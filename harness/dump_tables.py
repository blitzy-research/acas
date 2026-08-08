#!/usr/bin/env python3
# Executable in its own right: the canonical recipe in harness/docker-compose.yml
# names the three state tools by path, and without this line the kernel refuses
# the exec, bash treats the file as a shell script, and the plain-text lines of
# this docstring become commands -- one of which is a destructive reset.
"""Deterministic state capture: `SELECT * FROM <table> ORDER BY <primary key>`.

Stages 3 and 7 of the parity protocol. Writes one JSON file per table, holding
the rows exactly as the driver returned them, so that the comparison later
measures behaviour rather than transport.

The dump needs no tie-breaking, timestamp masking or surrogate-key remapping,
because every one of the 22 in-scope tables of `mysql/ACASDB.sql` has a
single-column primary key, no secondary index, no `TIMESTAMP` column and no
`AUTO_INCREMENT`. Ordering by that key is therefore a total order and two runs
of one scenario dump identically. Exactly one column-level default exists in
scope - `SYSTEM-REC`.`PASS-WORD` [mysql/ACASDB.sql:L1219] - and it is recorded
as a cited allowance in `KNOWN_COLUMN_DEFAULTS` rather than glossed over; it
changes nothing here, because a default applies only to an omitting `INSERT`
and this module issues `SELECT` only.

Numeric values are `decimal.Decimal` or `int` and are serialised as strings that
preserve the stored scale; a value that arrives as a float aborts the dump,
because no accounting figure may traverse binary floating point (R-2).

    stage  1  reset+seed  harness/reset_db.sh      (COBOL *LD loaders)
    stage  2  run  COBOL   harness/run_cobol_scenario.sh
    stage  3  dump         THIS MODULE              -> $ACAS_OUT/.../cobol
    stage  4  normalize    harness/normalize.py
    stage  5  reset+seed   harness/reset_db.sh      (the SAME command as 1)
    stage  6  run  Python  harness/run_python_scenario.sh
    stage  7  dump         THIS MODULE              -> $ACAS_OUT/.../python
    stage  8  normalize    harness/normalize.py
    stage  9  verify       both captures published
    stage 10  diff         harness/diff_states.py   -> MUST be EMPTY

Those ten stages are DEFINED IN ONE PLACE, [harness/normalize.py PARITY_STAGES], which
[harness/normalize.py] owns and publishes through `--print-stages`; the
listing above is a restatement of it and nothing else reads it. The Agent Action
Plan's eight logical stages (section 0.3.2) become these ten by making both
normalisations and the publication check explicit, so where older prose says
"stage 8" of the protocol it means today's stage 10. The canonical
one-command-per-stage recipe is published by the committed Compose file at
[harness/docker-compose.yml "STAGES."].

THE DUMP IS DELIBERATELY DUMB
=============================
Agent Action Plan section 0.6.6 establishes why one `ORDER BY` on one
column suffices: "All 22 in-scope tables have a single-column primary key
and zero secondary indexes, and none contains a `TIMESTAMP` column, an
`AUTO_INCREMENT` column, or a column-level `DEFAULT` ... Consequently the
dump is `SELECT * FROM <table> ORDER BY <primary key>` with no
tie-breaking logic, no timestamp masking and no surrogate-key remapping
needed." Each clause is checkable against `mysql/ACASDB.sql`, and
`assert_table_structure` re-checks it against `information_schema` on
every run rather than trusting it. So: no `ORDER BY` beyond the single
primary-key column, no secondary sort, no row-hash tie-break and no
client-side re-sorting - rows arrive primary-key-ordered from SQL and are
written in that order, untouched. No timestamp masking, there being zero
temporal columns in scope. No surrogate-key remapping, the schema's only
`AUTO_INCREMENT` column being `STOCKAUDIT-REC`.`AUDIT-ID`, out of scope.

The schema's only composite primary key, only `UNIQUE` constraint and
only `FOREIGN KEY` all belong to `PLPAY-RECrg01`, and its only secondary
indexes are three `KEY` clauses on `STOCK-REC` plus one on
`PLPAY-RECrg01`. Both tables are out of scope, which is why nothing in
scope needs special handling. `harness/reset_db.sh` asserts the same
invariant from the other side and says so at [harness/reset_db.sh ACAS_RESET_OUT_OF_SCOPE]
and [harness/reset_db.sh acas_expected_table_names].

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

Over all thirty-three tables and seven hundred and twenty columns,
`SYSTEM-REC`.`PASS-WORD` is the single column whose declaration carries a
`DEFAULT` clause. It changes nothing here: a column default applies only
to an `INSERT` that omits the column, and this module issues `SELECT`
only. Rather than drop the check or let it fail against the real schema,
`KNOWN_COLUMN_DEFAULTS` records this one default as a cited allowance and
`assert_table_structure` aborts on any OTHER column-level default. The
tripwire on frozen-schema tampering is kept; the false alarm is not.

FAITHFUL CAPTURE, NOT NORMALISATION
===================================
This module has zero canonicalisation jobs. `harness/normalize.py` has
exactly three: trailing spaces in fixed-width character columns, decimal
scale rendering, and the two-digit versus four-digit date text forms. The
split is deliberate and load-bearing. Agent Action Plan section 0.6.2's
width drift, traced end to end:

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
the difference is even retrievable then depends on the server's
`PAD_CHAR_TO_FULL_LENGTH` mode, which `harness/Dockerfile.mariadb`
deliberately leaves unset for exactly this reason. So: capture what the
driver returns, byte for byte, and let `normalize.py` canonicalise.
Trimming or padding here would hide a real behavioural difference behind
a helpful-looking transformation.

FACTS `harness/normalize.py` NEEDS, RECORDED SO THE PAIR AGREES
===============================================================
  * FIXED-WIDTH COLUMNS. The schema declares 238 `char(...)` columns and
    ZERO `varchar(...)`; 177 of those 238 are in scope. In-scope width
    census: 79 x char(1), 12 x char(2), 6 x char(3), 5 x char(4),
    3 x char(5), 2 x char(6), 6 x char(7), 5 x char(8), 10 x char(10),
    1 x char(11), 4 x char(12), 6 x char(13), 1 x char(14), 2 x char(15),
    1 x char(16), 1 x char(18), 12 x char(24), 5 x char(30),
    10 x char(32), 3 x char(48), 1 x char(64), 2 x char(96).
  * DECIMAL SCALE IS NOT UNIFORMLY 2. The schema carries 167 `DECIMAL`
    columns, 128 in scope, and the in-scope scales are 55 x decimal(10,2),
    44 x decimal(9,2), 15 x decimal(4,2), 8 x decimal(5,2),
    4 x decimal(14,2), 1 x decimal(6,2) and 1 x decimal(5,0). Out of
    scope there are also `,4` scales. NEVER hard-code two places.
  * `char(8)` DOES NOT MEAN "DATE". The in-scope char(8) columns are
    `GLPOSTING-REC`.`POST-DAT`, `IRSPOSTING-REC`.`POST4-DAT` and
    `PSIRSPOST-REC`.`IRS-POST-DAT`, which are date text - but ALSO
    `PUITM5-REC`.`OI5-BATCH` and `SAITM3-REC`.`OI3-BATCH`, which are
    batch references. Any date handling in `normalize.py` must be driven
    by an explicit COLUMN ALLOW-LIST, never by a width or content
    heuristic.
  * NO EXTRA FILES IN THE OUTPUT DIRECTORY. `normalize.py` is invoked as
    `--in /out/cobol --out /out/cobol.norm`
    [harness/docker-compose.yml "STAGES."], so it reads a directory. This
    module writes ONLY `<TABLE>.json` files there - no manifest, no log,
    no marker. Progress goes to stderr.

THE OUTPUT CONTRACT
===================
One file per table, named for the table exactly as the schema spells it,
hyphens included, for example `GLPOSTING-REC.json`. The object carries
five keys, in this insertion order and no others:

    {"table": "GLLEDGER-REC",
     "primary_key": "LEDGER-KEY",
     "columns": ["LEDGER-KEY", "LEDGER-TYPE", ... ],
     "row_count": 2,
     "rows": [[1, 1, "B", 1, "Sales Ledger Control", "1234.56", ... ],
              [2, 1, "B", 1, "VAT Control", "-99.99", ... ]]}

`columns` is in schema ordinal order, taken from the cursor description of
`SELECT *` and cross-checked against `information_schema`; it is never
sorted. `rows` is a list of lists in the order SQL returned them, which is
primary-key ascending, positionally aligned with `columns`; `row_count` is
derived and asserted equal to `len(rows)`. A `DECIMAL` becomes a canonical
JSON STRING with the column's declared scale intact, rendered with
`format(value, "f")` so exponent notation can never appear, and trailing
zeros are NOT stripped here; integers become JSON integers; `CHAR` becomes
a JSON string exactly as the driver returned it, unpadded and untrimmed.
NO other key - no timestamp, no server version, no connection detail, no
scenario name, no side, because the file's PATH carries the scenario and
the side.

TWO ACCEPTED OUTPUT LAYOUTS, BOTH FROM THIS REPOSITORY'S DOCUMENTATION
======================================================================
    <out-dir>/<scenario>/<side>/<TABLE>.json    --scenario NAME --side S
    <out>/<TABLE>.json                          --out DIR

The first is the layout this module's file specification defines, with
`side` one of `cobol` or `python`. The second is the invocation the
committed Compose file publishes verbatim as the canonical ten-stage
recipe, `harness/dump_tables.py --out /out/cobol`
[harness/docker-compose.yml "STAGES."]. Both are supported because both are
documented in this repository, and neither is a guess. `--out` names the
directory the `<TABLE>.json` files are written into directly; `--out-dir`
names the root under which `<scenario>/<side>/` is composed.

CONNECTION POLICY
=================
Credentials come from the environment `harness/docker-compose.yml` already
defines for the `gnucobol` service [harness/docker-compose.yml "ENVIRONMENT -- the canonical ACAS_* contract"]:
`ACAS_DB_HOST`, `ACAS_DB_PORT`, `ACAS_DB_NAME`, `ACAS_DB_USER`,
`ACAS_DB_PASSWORD` and `ACAS_DB_SOCKET` (declared, and legitimately
empty). They are never logged, never echoed, never persisted and never
allowed to influence a single output byte; `ConnectionSettings.__repr__`
redacts the password.

Widths are enforced because the COBOL side cannot carry more. The
`RDB-Data` group at [copybooks/wsfnctn.cob:L56-L62] declares
`DB-Schema pic x(12)`, `DB-UName pic x(12)`, `DB-UPass pic x(12)`,
`DB-Host pic x(32)`, `DB-Socket pic x(64)` and `DB-Port pic x(5)`. A
credential the bridge cannot hold would make the two sides connect as
different users, and two dumps taken as different users are not
comparable.

NO SESSION STATE IS SET. `harness/Dockerfile.mariadb` declares the
RUNTIME autocommit mode at SERVER level precisely so that every client
inherits the same value identically - the COBOL loaders, the bridges
through `cobmysqlapi.o`, the `mariadb` client in `seed.sh` and
`reset_db.sh`, and the Python driver here - and warns that a per-session
setting "would let one side of the diff differ from the other". The one
mode change anywhere in the harness is the seeding window `seed.sh` opens
around the frozen load programs and closes again, so a dump never runs
inside it. This module therefore sets no `autocommit`, no `sql_mode`, no
`charset`, no collation and no `PAD_CHAR_TO_FULL_LENGTH`: it reads the
server as configured. Being `SELECT`-only, the autocommit value cannot
affect its output either way. Under the declared runtime `autocommit=1`
each `SELECT` is its own read rather than one long snapshot, which is
equally deterministic here because execution is strictly sequential and
nothing writes to the schema while a dump is in progress - the run has
finished before the dump starts.
The connection is still released with a write-free `rollback()`, never
a commit, so the module cannot alter state even if the server were
reconfigured.

THE RULES CITED BELOW BY NUMBER
===============================
The six binding rules R-1 to R-6 are the Agent Action Plan's own, section 0.7.2,
and each section below names the one it satisfies. Where the plan is silent,
ordinary enterprise practice applies.

NUMERIC POLICY  (rule R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport. Agent Action
Plan section 0.5.1 extends the prohibition to this exact file: "No
`pandas` and no `numpy` - both compute in binary floating point by
default, which is prohibited outright for accounting computation. This
exclusion is absolute, including for the harness dump comparison, which
uses ordered row sequences rather than dataframes." So, structurally:

  * `pandas` and `numpy` are not imported here, for any reason. Neither is
    in `requirements.txt`, and `harness/Dockerfile.gnucobol` fails its own
    build if either is importable.
  * `float(...)` is never called on a database value, and no value is
    allowed to reach `float` by inference.
  * A `DECIMAL` is NEVER serialised as a JSON number, JSON numbers being
    IEEE-754 doubles in every consumer, so `"1234.56"` is written as text.
    Integers are written as JSON integers, exact for every integer width
    the schema uses - the widest in scope is `bigint(11)`, comfortably
    inside a 64-bit integer.
  * `render_value` DISPATCHES ON TYPE AND RAISES on anything unexpected
    rather than coercing it. A `float` raises `NumericPolicyError` naming
    the table, the column and the value; so does a non-finite `Decimal`; a
    `bool` raises too, because JSON `true` is not the integer the column
    holds. Silently rounding any of these would destroy the exactness the
    whole engagement rests on.
  * `assert_table_structure` additionally refuses a table carrying a
    `float`, `double` or `real` column, so the guard is structural as well
    as per value.

The schema supports all of this: it declares ZERO `FLOAT`, `DOUBLE` and
`REAL` columns. Its numeric census is 167 `DECIMAL`, 151 `INT`, 116
`TINYINT`, 23 `MEDIUMINT`, 22 `SMALLINT` and 3 `BIGINT`; in scope, 128
`DECIMAL`, 65 `INT`, 99 `TINYINT`, 21 `MEDIUMINT`, 20 `SMALLINT` and 3
`BIGINT`. The pinned driver `mysql-connector-python==26.7.0` maps
`DECIMAL` to `decimal.Decimal` with the declared scale intact -
`decimal(14,4)` arrives as `Decimal("0.0000")` - and every integer width
to `int`. `render_value` does not rely on that mapping: it asserts it per
value, so a driver change that broke it would raise rather than round.

NO COBOL AT RUNTIME, NO COUPLING TO THE SHIPPED PACKAGE  (rule R-1)
===================================================================
`harness/` is the compiled-COBOL oracle tree and a SIBLING of
`acas_posting/`. Agent Action Plan section 0.3.1 annotates it "the
compiled oracle; NEVER on the package import path" and states the
guarantee: "there is no import path from `acas_posting` to `harness`, and
the shipped artifact carries no COBOL, no `cobc` requirement and no
linkage to the bridge's C interface object."

  * THERE IS NO `harness/__init__.py` AND THERE MUST NEVER BE ONE. This is
    a plain module invoked BY PATH, on `sys.path` only for its own run.
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
    `dump_path`, `_ident` - are usable, and unit-testable, with no driver
    installed and no database reachable. `jsonschema` is not imported: it
    is not in `requirements.txt`.

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
    transaction-control statement it issues is a write-free `rollback()`,
    which releases any read-only transaction the server may have opened.
    It writes nothing either way, because this module only ever reads, and
    under the declared runtime `autocommit=1` there is usually no
    transaction open for it to release at all.
  * ONE connection, no pool. Tables are dumped one after another in a
    plain loop. There is no thread, no event loop, no process pool and no
    synchronisation primitive anywhere in this file.
  * It writes nothing under `$ACAS_REPO`, which the Compose file mounts
    read-only [harness/docker-compose.yml "/repo is READ-ONLY"] to keep the frozen
    artifact guarantee of section 0.8.1 structural.
  * It adds no validation of the DATA. The structural assertions check the
    SCHEMA - shape, keys, types - never a row's contents.

ANOMALIES ARE REPRODUCED, NEVER REPAIRED  (rule R-4)
====================================================
Agent Action Plan section 0.8.2, preserving the user's own requirement: "A
defect reproduced is correct; a defect fixed is a failure." For a dump
that means: DUMP WHAT IS THERE. The clearest case is the plan's anomaly A-7.
`IRSPOSTING-REC` carries three columns that exist in NO copybook -
`POST4-DAY`, `POST4-MONTH` and `POST4-YEAR` - because the bridge derives
them from two-character slices of a date string under a guard
[common/irspostingMT.cbl:L982-L987]. When the guard does not hold the
slices are simply not moved, so the components keep the zero left by the
group `INITIALIZE` while `POST4-DAT` still holds the raw date text. The
row is internally inconsistent, and that is the specification. Nothing
here derives, back-fills, cross-checks or "repairs" those three columns,
and nothing rounds, re-scales, trims, pads or reformats any other value.
`render_value` is a type dispatch, not a transformation.

TRACEABILITY  (rule R-5)
========================
Every table, primary key and column count in `IN_SCOPE` is traceable to
`mysql/ACASDB.sql` and carries the `CREATE TABLE` line it was read from.
The same twenty-two triples appear independently in
[harness/reset_db.sh ACAS_RESET_INSCOPE] and the same eleven out-of-scope names in
[harness/reset_db.sh ACAS_RESET_OUT_OF_SCOPE]; the two were checked against each other
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
`tests/determinism/test_two_runs_byte_identical.py`." That determinism
suite is written at a later boundary; the property it will assert is the
one this module is built to deliver.

NOT ONE BYTE OF NON-REPRODUCIBLE CONTENT MAY APPEAR IN A DUMP FILE. There
is no wall-clock timestamp, no hostname, no run identifier, no elapsed
time, no absolute path, no process id, no driver version, no server
version and no random ordering in the output - this module reads no clock,
no entropy source and no distribution metadata, and lists no directory.
Provenance, when wanted, belongs in a log outside the dump tree.

Serialisation is pinned rather than left to a default: `indent=2`,
`ensure_ascii=True`, `sort_keys=False`, `separators=(",", ": ")`, LF
newlines, UTF-8, exactly one trailing newline, and the five keys always in
the same insertion order. `ensure_ascii=True` is deliberate - it makes the
bytes independent of any locale or filesystem-encoding difference between
the two runs, so do not "improve" it. Each file is written to a temporary
name in its own directory and moved into place with `os.replace`, so a
partial write can never be compared.

THE PUBLIC API
==============
`tests/conftest.py` is specified to provide "the seed/dump/normalize/diff
helpers so that no test reimplements the comparison protocol" (Agent
Action Plan section 0.4.3), so it will import this module and call these
functions directly. They are a library first and a command second.

    connect                    context manager over one read-only
                               connection, from the ACAS_DB_* environment
    connection_settings        the resolved settings, password redacted
    dump_table                 the dump object for one table
    dump_tables                the dump objects for many, sequentially
    write_dump                 the deterministic serialiser, one file
    publish_dumps              the whole set, staged and committed with a
                               manifest written last
    build_manifest             the completeness manifest object
    write_manifest             its deterministic serialiser
    file_digest                the SHA-256 the manifest records
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
    0   every requested table was dumped, published and marked complete
    80  usage - bad or contradictory command line, or NO table selector
    81  precondition - environment or output directory
    82  database - unreachable, or credentials rejected
    83  scope - an out-of-scope or unknown table was requested
    84  drift - a structural assertion against the frozen schema failed
    85  numeric - the R-2 value guard tripped, or a NULL was fetched
    86  write - a file could not be written, or the output directory
        overlaps the read-only checkout in either direction
    87  timeout - a connect, read or write deadline expired

A table selector is REQUIRED, not optional, because evidence whose scope
is implicit is not evidence (rule R-6). The selector the protocol uses is
`--all-in-scope`, all 22 tables: both cycles perform the menu's own
`overrewrite.` [general/general.cbl:L656-L672], which rewrites SYSTEM-REC
under key 1, SYSDEFLT-REC under key 2 and SYSTOT-REC under key 4, so
those rows are comparable rather than a source of false failure.
`--scenario-file` narrows the capture to a scenario's declared effect and
is for debugging: a capture bounded by what a scenario EXPECTS to move
cannot show a difference in anything it did not expect to move.

Every network operation is bounded by a finite, configurable deadline, so
no stage of the protocol can hang: ACAS_DB_CONNECT_TIMEOUT,
ACAS_DB_READ_TIMEOUT and ACAS_DB_WRITE_TIMEOUT, none of which may be 0.

FURTHER READING
===============
Each path below is written in the house citation form, in brackets. That is
not decoration: a bare path at the start of a line is a runnable command to
any shell that ends up reading this file, and one of these is a destructive
reset. The shebang above is what stops that happening; the brackets are
what make it harmless if it ever does.

    [mysql/ACASDB.sql]            the frozen schema; the source of the
                                  table, key and column inventory
    [harness/normalize.py PARITY_STAGES]    the ten stages, in order, defined once
    [tests/conftest.py]           the composed protocol that drives them
    [harness/docker-compose.yml]  the per-stage commands and the environment
    [harness/reset_db.sh]         the same invariants, from the database
                                  side
    [harness/normalize.py]        the three canonicalisation jobs
    [harness/diff_states.py]      the comparison; empty is the pass

The migration anomaly log and the per-scenario diff evidence, both written
at a later boundary, are built from this pipeline's output.
"""

# Every fact this module encodes comes from the frozen schema mysql/ACASDB.sql, the
# maintainer's own one-way COBOL-to-MySQL bridge (common/*MT.scb and common/*MT.cbl) and
# the record copybooks under copybooks/.

from __future__ import annotations

import argparse
import difflib
import errno
import hashlib
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

# One entry per in-scope table: its single-column primary key, its declared column count
# and the `CREATE TABLE` line of mysql/ACASDB.sql it was read from.


@dataclass(frozen=True, slots=True)
class TableSpec:
    """One in-scope table's frozen-schema facts.

    Attributes:
        primary_key: The single column the dump orders by.
        column_count: The declared number of columns, asserted before any row is read. A
            cheap, strong tripwire on schema tampering.
        schema_line: The `CREATE TABLE` line in `mysql/ACASDB.sql`, so a reader can go
            straight to the declaration.
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

# The eleven tables the posting cycle never touches, listed by NAME so a wrong request
# is refused with an explanation rather than with a not-found.
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

# Deterministic iteration order for `--all-in-scope` and for the default selection: the
# table names, ascending.
IN_SCOPE_TABLES: Final[tuple[str, ...]] = tuple(sorted(IN_SCOPE))

# 513, the sum of the twenty-two declared column counts above, which is also the number
# of in-scope columns mysql/ACASDB.sql declares.
EXPECTED_TOTAL_COLUMNS: Final[int] = sum(
    spec.column_count for spec in IN_SCOPE.values()
)

# The two sides of the comparison. Two things record which side a capture is, and the
# distinction matters because only one of them can reach a verdict:
#   - the PATH composes it, as <out-dir>/<scenario>/<side>/, and
#   - the MANIFEST states it, because `side` is one of `MANIFEST_KEYS` and the run
#     attestation is matched against it (`read_run_attestation`).
# What carries no side at all is the per-table dump OBJECT: `DUMP_KEYS` is exactly
# table/primary_key/columns/row_count/rows, and those files are the only ones
# harness/diff_states.py compares. So recording the side in the manifest cannot
# influence a verdict, which is why it is safe to record it there and misleading to
# claim -- as it would be tempting to -- that
# nothing but the path knows it.
SIDES: Final[tuple[str, ...]] = ("cobol", "python")

#: The two members of `SIDES`, named so that a comparison against one of them
#: cannot be misspelled. `SIDE_PYTHON` in particular is compared against when
#: deciding whether a behavioural run status is admissible, and only that side
#: has one.
SIDE_COBOL: Final[str] = SIDES[0]
SIDE_PYTHON: Final[str] = SIDES[1]

# The dump object's key order. Fixed, and asserted by `write_dump` before anything is
# serialised (rule R-6).
DUMP_KEYS: Final[tuple[str, ...]] = (
    "table",
    "primary_key",
    "columns",
    "row_count",
    "rows",
)

# [mysql/ACASDB.sql:L1219] `PASS-WORD` char(4) NOT NULL DEFAULT '', Agent Action Plan
# section 0.6.6 says the in-scope tables carry none.
KNOWN_COLUMN_DEFAULTS: Final[Mapping[tuple[str, str], frozenset[str]]] = {
    ("SYSTEM-REC", "PASS-WORD"): frozenset({"''", ""}),
}

# Column types that would break the determinism argument of Agent Action Plan section
# 0.6.6 - a temporal type could carry a wall-clock value into a dump - or the numeric
# policy of rule R-2.
_FORBIDDEN_FLOAT_TYPES: Final[frozenset[str]] = frozenset(
    {"float", "double", "real"}
)
_FORBIDDEN_TEMPORAL_TYPES: Final[frozenset[str]] = frozenset(
    {"timestamp", "datetime", "date", "time", "year"}
)

# `information_schema.COLUMNS.EXTRA` substrings that would each defeat a clause of
# section 0.6.6.
_FORBIDDEN_EXTRA_MARKERS: Final[tuple[str, ...]] = (
    "auto_increment",
    "generated",
    "on update",
)

EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 80
EX_PRECONDITION: Final[int] = 81
EX_DATABASE: Final[int] = 82
EX_SCOPE: Final[int] = 83
EX_DRIFT: Final[int] = 84
EX_NUMERIC: Final[int] = 85
EX_WRITE: Final[int] = 86
# A deadline expired: the connection attempt, a socket read or a socket write did not
# finish inside its budget.
EX_TIMEOUT: Final[int] = 87

_ENV_HOST: Final[str] = "ACAS_DB_HOST"
_ENV_PORT: Final[str] = "ACAS_DB_PORT"
_ENV_NAME: Final[str] = "ACAS_DB_NAME"
_ENV_USER: Final[str] = "ACAS_DB_USER"
_ENV_PASSWORD: Final[str] = "ACAS_DB_PASSWORD"
_ENV_SOCKET: Final[str] = "ACAS_DB_SOCKET"
_ENV_OUT: Final[str] = "ACAS_OUT"

# TRANSPORT SECURITY (CWE-295, CWE-319).
_ENV_TLS_CA: Final[str] = "ACAS_DB_TLS_CA"
_ENV_TLS_CERT: Final[str] = "ACAS_DB_TLS_CERT"
_ENV_TLS_KEY: Final[str] = "ACAS_DB_TLS_KEY"
_ENV_ALLOW_PLAINTEXT: Final[str] = "ACAS_DB_ALLOW_PLAINTEXT"

# The spellings accepted as "yes" for `ACAS_DB_ALLOW_PLAINTEXT`. Deliberately a closed
# set.
_AFFIRMATIVE: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})

# Host names that name the local machine, compared lower-case. Numeric loopback
# addresses are NOT listed.
_LOOPBACK_HOST_NAMES: Final[frozenset[str]] = frozenset(
    {"localhost", "localhost.localdomain"}
)

_ENV_REPO: Final[str] = "ACAS_REPO"

# ---------------------------------------------------------------------------
#  DEADLINES
#
#  EVERY network operation this module performs is bounded. Without a
#  bound, a server that accepts a socket and then never answers - a
#  container still starting, a table held by a lock the seeding stage left
#  behind, a dropped route - leaves the dump stage blocked forever, and a
#  parity protocol whose stage 3 can hang has no failure mode an operator
#  can act on.
#
#  Three separate budgets, because they fail for three different reasons:
#    connect  the TCP handshake plus the server's greeting. Short: a
#             reachable MariaDB answers in milliseconds, and the readiness
#             wait belongs to [harness/reset_db.sh], not here.
#    read     how long ONE socket read may block. This is the per-query
#             deadline: `SELECT * FROM <table> ORDER BY <pk>` on the
#             largest in-scope table is a small query against a seeded
#             fixture, so a generous default still catches a hang.
#    write    how long ONE socket write may block. Only statement text
#             ever goes out, so this can be short.
#
#  The budgets are the driver's own socket options rather than a signal, an
#  alarm or a watchdog thread: rule R-3 forbids concurrency, and a thread
#  would be the wrong tool anyway - the driver already knows how to time a
#  socket out and to invalidate the connection when it does.
#
#  A server-side `MAX_EXECUTION_TIME` is deliberately NOT set: `connect`
#  states that no session variable is set, and honouring that keeps the
#  two sides of the comparison reading the server exactly as
#  harness/Dockerfile.mariadb configured it.
# ---------------------------------------------------------------------------
#: Stands in for a driver field the exception did not carry, or carried in a
#: shape that is not that field. Never the driver's own text.
_UNKNOWN_DRIVER_FIELD: Final[str] = "unknown"

#: SQLSTATE is five alphanumeric characters [copybooks/wsfnctn.cob:L51].
_SQLSTATE_WIDTH: Final[int] = 5

_ENV_CONNECT_TIMEOUT: Final[str] = "ACAS_DB_CONNECT_TIMEOUT"
_ENV_READ_TIMEOUT: Final[str] = "ACAS_DB_READ_TIMEOUT"
_ENV_WRITE_TIMEOUT: Final[str] = "ACAS_DB_WRITE_TIMEOUT"

_DEFAULT_CONNECT_TIMEOUT: Final[int] = 10
_DEFAULT_READ_TIMEOUT: Final[int] = 300
_DEFAULT_WRITE_TIMEOUT: Final[int] = 60

# An upper bound on a configured budget, so "one day" cannot be set by a typo and
# quietly reinstate the unbounded behaviour this replaces.
_MAX_TIMEOUT: Final[int] = 86_400

# Driver error numbers that mean a deadline expired rather than a request being refused.
_TIMEOUT_ERRNOS: Final[frozenset[int]] = frozenset({2003, 2006, 2013, 1969, 3024})

# Field widths from the `RDB-Data` group at [copybooks/wsfnctn.cob:L56-L62].
_RDB_WIDTHS: Final[Mapping[str, int]] = {
    _ENV_NAME: 12,
    _ENV_USER: 12,
    _ENV_PASSWORD: 12,
    _ENV_HOST: 32,
    _ENV_SOCKET: 64,
    _ENV_PORT: 5,
}

_SUGGESTION_LIMIT: Final[int] = 4

_STATEMENT_ECHO_LIMIT: Final[int] = 120

_DIGEST_BLOCK: Final[int] = 1 << 16

_SCENARIO_TABLE_KEYS: Final[tuple[str, ...]] = (
    "affected_tables",
    "affected-tables",
)


# Stderr, and never stdout, so nothing this module says can be mistaken for data.

# Set once by `main` from --quiet.
_QUIET: bool = False


def _progress(message: str) -> None:
    """Write one progress line to stderr, unless `--quiet` was given.

    Args:
        message: The line to write.
    """
    if _QUIET:
        return
    print(message, file=sys.stderr)


# ERRORS One root, so a caller can catch everything this module raises with a single
# clause, and one subclass per distinct cause so a caller that cares can tell them
# apart.


class DumpError(Exception):
    """Base class for every error this module raises."""


class UnknownTableError(DumpError, ValueError):
    """A requested name is not a table of the frozen schema at all."""


class TableNotInScopeError(DumpError, ValueError):
    """A requested table exists but the posting cycle never touches it.

    Agent Action Plan section 0.2.2 lists the eleven, and refusing them by name - rather
    than dumping them, or failing to find them - is what keeps a comparison bounded by
    the cycle actually being migrated.
    """


class SchemaDriftError(DumpError, RuntimeError):
    """The live schema does not match the frozen schema's declaration.

    Either `mysql/ACASDB.sql` was modified, which Agent Action Plan section 0.8.1 calls
    "a defect in the migration, regardless of how harmless it appears", or `IN_SCOPE` is
    wrong. Both stop the run.
    """


class NumericPolicyError(DumpError, TypeError):
    """A value would have to pass through binary floating point (rule R-2).

    Raised, never coerced. A `float` arriving here means the driver was configured
    wrongly, and silently rounding it would destroy the exactness the whole engagement
    rests on.
    """


class UnexpectedValueTypeError(DumpError, TypeError):
    """The driver returned a type no in-scope column can hold."""


class UnexpectedNullError(DumpError, ValueError):
    """A NULL was fetched from a schema that declares every column NOT NULL.

    Agent Action Plan section 0.6.2 explains why one cannot legitimately appear: each
    bridge load paragraph initialises the host-variable group first, "so unset fields
    become zero or space rather than SQL `NULL`".
    """


class ConnectionConfigError(DumpError, RuntimeError):
    """The ACAS_DB_* environment is missing, malformed or out of range."""


class InsecureTransportError(DumpError, RuntimeError):
    """A non-local connection would have crossed the network in the clear."""


class DriverUnavailableError(DumpError, RuntimeError):
    """The pinned database driver is not importable."""


class DumpWriteError(DumpError, OSError):
    """A dump file could not be written or moved into place."""


class DumpPathError(DumpError, ValueError):
    """The output directory is not somewhere this tool may write."""


class ManifestError(DumpError, ValueError):
    """A published tree's completeness manifest is missing or disagrees."""


class DumpTimeoutError(DumpError, TimeoutError):
    """A connection, read or write deadline expired.

    Separated from `DumpError` proper so `main` can return `EX_TIMEOUT` rather than
    `EX_DATABASE`: "the server never answered" and "the server refused us" call for
    different operator action, and only the first can be cured by raising a budget.
    """


class ScenarioFileError(DumpError, ValueError):
    """A scenario definition does not carry a usable affected-table list."""


def _is_timeout(exc: BaseException) -> bool:
    """Report whether a driver exception means a deadline expired.

    Three independent signals are consulted, because no single one is reliable across
    the driver's own layers: a bare socket timeout arrives as `TimeoutError`; the
    connector wraps most of them in its own error class carrying an `errno`.

    Args:
        exc: The exception the driver raised.

    Returns:
        Whether it should be reported as a timeout rather than as a plain database
            failure.
    """
    if isinstance(exc, TimeoutError):
        return True
    # Named `code` and not `errno`, which is now an imported module.
    code = getattr(exc, "errno", None)
    if isinstance(code, int) and code in _TIMEOUT_ERRNOS:
        return True
    text = str(exc).lower()
    return "timed out" in text or "timeout" in text


def _driver_error_fields(exc: BaseException) -> tuple[str, str]:
    """Reduce a driver exception to two typed, console-safe fields.

    THE REASON THIS EXISTS. A driver message is arbitrary text the SERVER
    supplied. It routinely names the account and the host ("Access denied for
    user 'acas'@'db.internal'"), and on a statement failure it can quote the
    statement and its parameters - so putting one in a diagnostic discloses
    identity and business values (CWE-532) and lets a newline inside it forge a
    further log line (CWE-117). The errno and the SQLSTATE say which failure it
    was without any of that; they are the same two fields
    `acas_posting/dal/status.py` records for the same class of event.

    Args:
        exc: The exception the driver raised.

    Returns:
        The errno and the SQLSTATE, each rendered as a short token and each
        `"unknown"` when the driver did not supply it. Both are constrained to
        the characters they are documented to use, so neither can carry a
        control character into a log line however the driver behaved.

    Examples:
        >>> class _E(Exception):
        ...     errno = 1045
        ...     sqlstate = "28000"
        >>> _driver_error_fields(_E("Access denied for 'a'@'h'"))
        ('1045', '28000')
        >>> _driver_error_fields(Exception("no fields at all"))
        ('unknown', 'unknown')

        A driver whose fields are the WRONG SHAPE - a string where an integer
        belongs, and a forged log line where a five-character state belongs - is
        refused rather than rendered:

        >>> class _Forged(Exception):
        ...     errno = "1045; INFO harness: everything fine"
        ...     sqlstate = "28000\\nERROR harness: forged line"
        >>> _driver_error_fields(_Forged())
        ('unknown', 'unknown')
    """
    code = getattr(exc, "errno", None)
    rendered_errno = (
        str(code) if isinstance(code, int) and not isinstance(code, bool)
        else _UNKNOWN_DRIVER_FIELD
    )
    state = getattr(exc, "sqlstate", None)
    rendered_state = _UNKNOWN_DRIVER_FIELD
    if isinstance(state, str):
        candidate = state.strip()
        # SQLSTATE is five alphanumeric characters by definition. Anything
        # else is not a SQLSTATE, so it is not rendered as one.
        if len(candidate) == _SQLSTATE_WIDTH and candidate.isalnum():
            rendered_state = candidate
    return rendered_errno, rendered_state


# ---------------------------------------------------------------------------
#  IDENTIFIER SAFETY
#  EVERY identifier in this schema is HYPHENATED - `ANALYSIS-REC`,
#  `LEDGER-NAME`, `IRS-POST-KEY`, `POST4-DAT` - so every one must be
#  backtick-quoted in every statement. Unquoted, `SELECT * FROM
#  ANALYSIS-REC` parses as a subtraction and fails.
#  Only two identifiers are ever interpolated into SQL here: a table name
#  and its primary-key column. Both are resolved through the allow-list
#  below FIRST, so no caller-supplied text ever reaches a statement.
#  Everything else - schema name, table name in the information_schema
#  lookups - is passed as a bound parameter.


# The primary-key columns, collected once. Kept separate from the table
# names so that `_ident` cannot be talked into quoting an arbitrary column.
_ALLOWED_KEY_COLUMNS: Final[frozenset[str]] = frozenset(
    spec.primary_key for spec in IN_SCOPE.values()
)


def table_spec(table: str) -> TableSpec:
    """Return the frozen-schema facts for `table`, or refuse the name.

    Args:
        table: A table name, spelled exactly as `mysql/ACASDB.sql` spells it, hyphens
            included and case-sensitive.

    Returns:
        The `TableSpec` recorded for that table.

    Raises:
        TableNotInScopeError: `table` is one of the eleven the posting cycle never
            touches (Agent Action Plan section 0.2.2).
        UnknownTableError: `table` is not a table of the frozen schema, or is not a
            string. The message offers near-miss names.
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

    The allow-list is the twenty-two in-scope table names together with their primary-
    key columns - the only identifiers this module ever places in a statement.

    Args:
        name: The identifier to quote.

    Returns:
        The identifier wrapped in backticks, ready to interpolate.

    Raises:
        TableNotInScopeError: `name` is an out-of-scope table.
        UnknownTableError: `name` is not on the allow-list at all, or is not a string.
    """
    if not isinstance(name, str):
        raise UnknownTableError(
            f"an identifier must be a string; got {type(name).__name__}."
        )

    if name in IN_SCOPE or name in _ALLOWED_KEY_COLUMNS:
        return f"`{name}`"

    table_spec(name)
    raise UnknownTableError(  # pragma: no cover - unreachable by design
        f"{name!r} is not an identifier this module may place in a "
        f"statement."
    )


# THE CONNECTION (rules R-1, R-3, R-6) ONE connection, read-only, no pool, strictly
# sequential. No session state is set.

_REDACTED: Final[str] = "***redacted***"


@dataclass(frozen=True, slots=True)
class ConnectionSettings:
    """Where to connect, resolved from the environment.

    A value object, deliberately without a `dsn` or `url` accessor: a
    connection string is the classic way a password reaches a log file.
    `__repr__` and `__str__` carry NO endpoint identity, NO socket path, NO
    certificate or private-key path and no password - only the transport
    CATEGORY and the three deadlines - so the object is safe to interpolate
    into a diagnostic that reaches a collected container log (CWE-532). See
    `__repr__` for what was removed and why, and `transport_category` for the
    vocabulary that replaced it.

    Attributes:
        host: `ACAS_DB_HOST`; `mariadb` inside the Compose network.
        port: `ACAS_DB_PORT` as an integer; 3306 in the Compose service.
        database: `ACAS_DB_NAME`.
        user: `ACAS_DB_USER`.
        password: `ACAS_DB_PASSWORD`. Never logged, never persisted, never allowed to
            influence an output byte.
        socket: `ACAS_DB_SOCKET`, empty for TCP. The Compose service sets it empty
            explicitly harness/docker-compose.yml.
        tls_ca: `ACAS_DB_TLS_CA`, empty when none was named. Naming one turns on TLS
            with BOTH certificate and host-name verification.
        tls_cert: `ACAS_DB_TLS_CERT`, for a server that wants a client certificate. Must
            be given together with `tls_key`.
        tls_key: `ACAS_DB_TLS_KEY`, the private key for `tls_cert`.
        allow_plaintext: `ACAS_DB_ALLOW_PLAINTEXT`, the explicit declaration that a
            plaintext connection to a non-local server is intended because the target is
            the harness's private network.
        connect_timeout: Seconds the handshake may take.
        read_timeout: Seconds ONE socket read may block - the per-query deadline.
        write_timeout: Seconds ONE socket write may block.
    """

    host: str
    port: int
    database: str
    user: str
    password: str
    socket: str
    tls_ca: str = ""
    tls_cert: str = ""
    tls_key: str = ""
    allow_plaintext: bool = False
    connect_timeout: int = _DEFAULT_CONNECT_TIMEOUT
    read_timeout: int = _DEFAULT_READ_TIMEOUT
    write_timeout: int = _DEFAULT_WRITE_TIMEOUT

    def __repr__(self) -> str:
        """Return a representation carrying NO endpoint identity and NO paths.

        WHAT THIS DELIBERATELY OMITS, AND WHY. It renders none of the host, the
        port, the schema, the account, the socket path or the certificate and
        PRIVATE-KEY file paths, even though a file name is arguably not a secret.
        Two reasons, and the first is sufficient on its own:

        * An operator diagnostic in this harness reaches stderr, which the
          composed recipe collects as a container log. Endpoint identity and
          internal file-system paths in a collected log are exactly the
          disclosure CWE-532 describes: together they name the server, the
          account that reaches it and where its key material is kept.
        * A private-key PATH is a pointer at key material. Publishing where to
          look is a meaningful step towards it, whatever the file's own mode.

        What is left is `transport_category` - a token from a fixed vocabulary
        that answers the only question a diagnostic needs, "was this connection
        protected, and how" - and the three deadlines, which are settings this
        process chose rather than facts about the deployment.

        The password never appeared here and does not now; it is still shown as
        redacted so that a reader can see the object HAS one rather than wonder.
        """
        return (
            f"{type(self).__name__}("
            f"transport={self.transport_category()!r}, "
            f"password={_REDACTED!r}, "
            f"connect_timeout={self.connect_timeout!r}, "
            f"read_timeout={self.read_timeout!r}, "
            f"write_timeout={self.write_timeout!r})"
        )

    __str__ = __repr__

    def transport_category(self) -> str:
        """Return a stable token naming HOW this connection is protected.

        The harness counterpart of `acas_posting.dal.connection`'s
        `transport_category`, with the same vocabulary, so a reader comparing an
        `acas_posting` record with a harness diagnostic sees the same word for
        the same situation. Derived entirely from settings this object already
        holds; NOTHING is resolved, so two runs of one scenario always agree
        (rule R-6).

        Returns:
            One of five tokens, most protective first:

            * `local-socket` - a Unix socket, which cannot leave the machine.
            * `loopback-tcp` - a loopback address or an empty host.
            * `tls-verified` - a certificate authority was named, which turns on
              BOTH certificate and host-name verification.
            * `isolated-network` - plaintext to a non-local server, explicitly
              declared as the harness's private network.
            * `unverified` - plaintext to a non-local server with no
              declaration. `_require_permitted_transport` refuses to connect in
              this state, so it appears only in a message explaining the
              refusal.
        """
        if self.socket:
            return "local-socket"
        if self.target_is_local():
            return "loopback-tcp"
        if self.verifies_the_server():
            return "tls-verified"
        if self.allow_plaintext:
            return "isolated-network"
        return "unverified"

    def verifies_the_server(self) -> bool:
        """Report whether these settings authenticate and encrypt the session.

        Returns:
            `True` when a certificate authority was named, which is the only
                configuration this module treats as protected.
        """
        return bool(self.tls_ca)

    def target_is_local(self) -> bool:
        """Report whether the connect target is on this machine.

        A Unix socket cannot leave the machine and a loopback address does not reach a
        network, so neither carries the password anywhere an eavesdropper can be.

        Returns:
            `True` for a socket, an empty host, a loopback host name or any loopback IP
                address.
        """
        if self.socket:
            return True
        host = self.host.strip()
        if not host:
            return True
        if host.lower() in _LOOPBACK_HOST_NAMES:
            return True
        try:
            # `strip("[]")` because a literal IPv6 address is conventionally bracketed
            # in a host field.
            return ipaddress.ip_address(host.strip("[]")).is_loopback
        except ValueError:
            return False

    def driver_tls_arguments(self) -> dict[str, Any]:
        """Render the TLS settings as driver keyword arguments.

        Returns:
            The `ssl_*` keywords, or an empty mapping when no certificate authority was
                named.
        """
        if not self.tls_ca:
            return {}
        arguments: dict[str, Any] = {
            "ssl_ca": self.tls_ca,
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_disabled": False,
        }
        if self.tls_cert:
            arguments["ssl_cert"] = self.tls_cert
        if self.tls_key:
            arguments["ssl_key"] = self.tls_key
        return arguments


def _timeout_seconds(
    source: Mapping[str, str], name: str, default: int
) -> int:
    """Resolve one deadline from the environment.

    Args:
        source: The environment to read.
        name: The variable to read.
        default: The value to use when it is unset or empty.

    Returns:
        A positive, finite number of seconds.

    Raises:
        ConnectionConfigError: The value is not a positive integer, or it exceeds
            `_MAX_TIMEOUT`. ZERO IS REJECTED RATHER THAN TREATED AS "no limit".
    """
    text = (source.get(name) or "").strip()
    if not text:
        return default
    if not text.isdigit():
        raise ConnectionConfigError(
            f"{name} must be a positive whole number of seconds; got "
            f"{text!r}. Leave it unset for the default of {default}s."
        )
    value = int(text)
    if value < 1 or value > _MAX_TIMEOUT:
        raise ConnectionConfigError(
            f"{name} must be between 1 and {_MAX_TIMEOUT} seconds; got "
            f"{value}. Zero is not accepted: a deadline of zero would mean "
            f"'block forever' to the driver, and every network operation "
            f"this tool performs is bounded on purpose."
        )
    return value


def connection_settings(
    env: Mapping[str, str] | None = None,
) -> ConnectionSettings:
    """Resolve the ACAS_DB_* environment into connection settings.

    Args:
        env: The mapping to read; `os.environ` when omitted. Passing one explicitly is
            how a test drives this without touching the process environment.

    Returns:
        The resolved settings, with the password redacted in `repr`.

    Raises:
        ConnectionConfigError: A required variable is missing or empty, the port is not
            a positive integer, a value is wider than the `RDB-Data` field that must
            carry it [copybooks/wsfnctn.cob:L56-L62], or one of the three deadline
            variables is not a positive whole number of seconds.
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
            f'harness/docker-compose.yml defines all of them for the '
            f'gnucobol service under "ENVIRONMENT -- the canonical ACAS_* '
            f'contract", and harness/reset_db.sh requires the same five in '
            f"acas_assert_environment. {_ENV_SOCKET} may be empty, which means "
            f"connect over TCP."
        )

    #  THE RANGE IS THE FROZEN CARRIER'S, 1..9999, NOT THE TCP RANGE. The value
    #  travels through `LK-Port-Number pic x(4)`
    #  [common/acas-get-params.cbl:L158] and `01 Ws-Mysql-Port-Number pic x(4)`
    #  [copybooks/mysql-variables.cpy:L91], which every bridge STRINGs DB-Port
    #  into [common/glpostingMT.cbl:L410-L413]. Four characters. A five-digit
    #  port would therefore be DUMPED from the server this module reached while
    #  the compiled cycle wrote to the truncated one - 13306 against 1330 - and
    #  the resulting diff would be evidence about nothing. `pic x(5)`
    #  [copybooks/wssystem.cob:L142] is the STORED width, not the carrier.
    port_text = source[_ENV_PORT].strip()
    if not port_text.isdigit() or int(port_text) < 1 or int(port_text) > 9999:
        raise ConnectionConfigError(
            f"{_ENV_PORT} must be a decimal port number between 1 and "
            f"9999; got {port_text!r}. The frozen carrier holds four "
            f"characters - LK-Port-Number pic x(4) "
            f"[common/acas-get-params.cbl:L158] and Ws-Mysql-Port-Number "
            f"pic x(4) [copybooks/mysql-variables.cpy:L91] - so a wider value "
            f"would reach the compiled cycle truncated while this dump used "
            f"the whole of it. The Compose service sets "
            f'{_ENV_PORT}: "3306" itself; see harness/docker-compose.yml.'
        )

    settings = ConnectionSettings(
        host=source[_ENV_HOST].strip(),
        port=int(port_text),
        database=source[_ENV_NAME].strip(),
        user=source[_ENV_USER].strip(),
        password=source[_ENV_PASSWORD],
        socket=(source.get(_ENV_SOCKET) or "").strip(),
        tls_ca=(source.get(_ENV_TLS_CA) or "").strip(),
        tls_cert=(source.get(_ENV_TLS_CERT) or "").strip(),
        tls_key=(source.get(_ENV_TLS_KEY) or "").strip(),
        connect_timeout=_timeout_seconds(
            source, _ENV_CONNECT_TIMEOUT, _DEFAULT_CONNECT_TIMEOUT
        ),
        read_timeout=_timeout_seconds(
            source, _ENV_READ_TIMEOUT, _DEFAULT_READ_TIMEOUT
        ),
        write_timeout=_timeout_seconds(
            source, _ENV_WRITE_TIMEOUT, _DEFAULT_WRITE_TIMEOUT
        ),
        allow_plaintext=(
            (source.get(_ENV_ALLOW_PLAINTEXT) or "").strip().lower()
            in _AFFIRMATIVE
        ),
    )

    # The COBOL side cannot carry a wider value, so a wider one here would make the two
    # sides of the comparison connect differently - and two dumps taken as different
    # users are not comparable.
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


def _require_permitted_transport(settings: ConnectionSettings) -> None:
    """Refuse a connection the operator has not declared safe to make.

    Called BEFORE the connect call, so a refused connection is never attempted and no
    credential ever leaves the process.

    Args:
        settings: The resolved settings.

    Raises:
        InsecureTransportError: A client certificate was named without its key or the
            key without the certificate, which cannot authenticate anything.
    """
    if bool(settings.tls_cert) != bool(settings.tls_key):
        raise InsecureTransportError(
            f"{_ENV_TLS_CERT} and {_ENV_TLS_KEY} belong together: a client "
            f"certificate cannot authenticate without its private key. Set "
            f"both, or neither."
        )

    if settings.target_is_local() or settings.verifies_the_server():
        return

    if settings.allow_plaintext:
        # Named without the host, the account or the schema.
        _progress(
            f"harness/dump_tables.py: plaintext transport to a non-local "
            f"server permitted by {_ENV_ALLOW_PLAINTEXT}; the credentials "
            f"and every value read are unprotected on this connection"
        )
        return

    raise InsecureTransportError(
        f"the connect target is neither a loopback address nor a Unix "
        f"socket, so the credentials and every posted figure read would "
        f"cross the network in the clear. Set {_ENV_TLS_CA} to a "
        f"certificate authority bundle - which turns on TLS with both "
        f"certificate and host-name verification - or set "
        f"{_ENV_ALLOW_PLAINTEXT}=1 to declare that the target is the "
        f"harness's own private network, whose server has no TLS "
        f"configured. harness/docker-compose.yml runs exactly that private "
        f"network, so it is the declaration that belongs there."
    )


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

    The single connection policy for both the command line and any
    in-process caller, so the two cannot drift apart. No pool, no
    thread, no retry loop and no session state (rule R-3): the server is
    read as `harness/Dockerfile.mariadb` configured it.

    On exit the connection is released with `rollback()` and closed.
    `rollback` rather than `commit` because this module only ever reads:
    rolling back writes nothing, and it releases any read-only transaction
    the server may have opened. Being SELECT-only, there is never anything
    to discard, whichever autocommit mode the server serves.

    Args:
        settings: Where to connect. Resolved from `env` when omitted.
        env: The environment to resolve from.

    Yields:
        An open DB-API connection.

    Raises:
        ConnectionConfigError: The environment is unusable.
        InsecureTransportError: The connection would have crossed a network unprotected,
            or the certificate settings are inconsistent. Raised before the connect
            call.
        DriverUnavailableError: The pinned driver is not importable.
        DumpError: The server refused the connection. The message names the host, port,
            database and user - NEVER the password.
    """
    resolved = connection_settings(env) if settings is None else settings
    _require_permitted_transport(resolved)
    driver = _import_driver()

    # `raw=False` and `use_unicode=True` pin the driver's own conversion rather than
    # leaning on its defaults.
    connect_kwargs: dict[str, Any] = {
        "host": resolved.host,
        "port": resolved.port,
        "database": resolved.database,
        "user": resolved.user,
        "password": resolved.password,
        "raw": False,
        "use_unicode": True,
        "connect_timeout": resolved.connect_timeout,
        "read_timeout": resolved.read_timeout,
        "write_timeout": resolved.write_timeout,
    }
    if resolved.socket:
        connect_kwargs["unix_socket"] = resolved.socket

    # Merged last, and only when a certificate authority was named, so that the
    # plaintext case is byte-for-byte the call this module always made.
    connect_kwargs.update(resolved.driver_tls_arguments())

    try:
        connection = driver.connect(**connect_kwargs)
    except Exception as exc:  # driver-specific; re-raised as one of ours
        #  NEITHER MESSAGE NAMES THE ENDPOINT, THE ACCOUNT OR THE DRIVER'S OWN
        #  TEXT. Both are raised to be printed on stderr, which the composed
        #  recipe collects as a container log:
        #    * the account, host, port and schema together identify the server
        #      and who reaches it (CWE-532);
        #    * a driver message is arbitrary server-supplied text, so it can
        #      carry a statement fragment, a value, or a newline that forges a
        #      further log line (CWE-117 as well as CWE-532).
        #  `transport_category` and the driver's own errno and SQLSTATE say
        #  everything a diagnosis needs - which is also what
        #  `acas_posting/dal/status.py` records for the same class of failure -
        #  and the original exception is still CHAINED with `from exc`, so a
        #  traceback in an interactive session loses nothing.
        driver_errno, driver_sqlstate = _driver_error_fields(exc)
        if _is_timeout(exc):
            raise DumpTimeoutError(
                f"connecting to the ACAS database "
                f"(transport {resolved.transport_category()}) did not "
                f"complete within {resolved.connect_timeout}s "
                f"(errno {driver_errno}, sqlstate {driver_sqlstate}). The "
                f"server may still be starting - harness/Dockerfile.mariadb "
                f"declares a HEALTHCHECK and harness/reset_db.sh waits for "
                f"readiness, so run this stage after that wait. Raise "
                f"{_ENV_CONNECT_TIMEOUT} only if the server is genuinely "
                f"slower than that to greet a client."
            ) from exc
        raise DumpError(
            f"could not connect to the ACAS database (transport "
            f"{resolved.transport_category()}, errno {driver_errno}, "
            f"sqlstate {driver_sqlstate}). Check {_ENV_HOST}, {_ENV_PORT}, "
            f"{_ENV_NAME}, {_ENV_USER} and {_ENV_PASSWORD} against the "
            f"running service; they are deliberately not echoed here."
        ) from exc

    try:
        yield connection
    finally:
        # Release any read-only transaction, then close. Neither may mask the
        # error that brought us here, so neither is allowed to propagate - but
        # NEITHER IS SILENT EITHER. A rollback that fails means the session was
        # already lost, and a close that fails leaks a server-side session for
        # the life of the process; both change how a later stage behaves, and a
        # cleanup failure that leaves no trace is how that becomes a mystery.
        # Only the exception TYPE is reported: a driver message is arbitrary
        # server-supplied text (CWE-117, CWE-532), and the type is the whole of
        # what a diagnosis needs from a tidy-up path.
        try:
            connection.rollback()
        except Exception as rollback_error:  # noqa: BLE001 - never propagated
            _progress(
                f"harness/dump_tables.py: warning: the read-only transaction "
                f"could not be rolled back before closing "
                f"({type(rollback_error).__name__}); the session was most "
                f"likely already lost."
            )
        try:
            connection.close()
        except Exception as close_error:  # noqa: BLE001 - never propagated
            _progress(
                f"harness/dump_tables.py: warning: the connection could not "
                f"be closed ({type(close_error).__name__}); a server-side "
                f"session may remain until this process exits."
            )


def _schema_name(connection: Any) -> str:
    """Return the schema the connection is using.

    Asked of the server rather than taken from the settings, so the `information_schema`
    assertions are made against the schema the rows actually come from.

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

    Args:
        connection: An open DB-API connection.
        statement: A `SELECT`. Nothing else is ever passed.
        parameters: Bound parameters, in the driver's `%s` style.

    Returns:
        The rows, in the order the server returned them.

    Raises:
        DumpTimeoutError: The statement did not answer inside the read budget, or the
            statement text could not be sent inside the write budget.
    """
    cursor = connection.cursor()
    try:
        try:
            cursor.execute(statement, tuple(parameters))
            return list(cursor.fetchall())
        except Exception as exc:
            if _is_timeout(exc):
                #  THE DRIVER'S OWN TEXT IS NOT CARRIED. Its errno and SQLSTATE
                #  are, which say which failure this was without the arbitrary
                #  server-supplied string that could name the account, quote a
                #  value, or embed a newline that forges a further log line
                #  (CWE-117, CWE-532). The abridged STATEMENT stays: this
                #  module's statements are built from the frozen schema and the
                #  fixed table list, carry their operands as bound parameters
                #  rather than literals, and naming which query stalled is the
                #  whole diagnosis. The original exception is still chained.
                statement_errno, statement_state = _driver_error_fields(exc)
                raise DumpTimeoutError(
                    f"a deadline expired while running "
                    f"{_abridge_statement(statement)} (errno "
                    f"{statement_errno}, sqlstate {statement_state}). The "
                    f"socket budgets are {_ENV_READ_TIMEOUT} (how long one "
                    f"read may block) and {_ENV_WRITE_TIMEOUT}. A read that "
                    f"expires on a SELECT usually means the row is held by "
                    f"a lock an earlier stage left open - "
                    f"[common/glbatchLD.cbl:L9-L13] requires autocommit OFF "
                    f"for seeding, which harness/seed.sh scopes to a window "
                    f"around the frozen load programs - so check that the "
                    f"seed stage closed that window and released its locks "
                    f"before raising the budget."
                ) from exc
            raise
    finally:
        cursor.close()


def _abridge_statement(statement: str) -> str:
    """Return a statement shortened for a diagnostic.

    Args:
        statement: The SQL that was being run.

    Returns:
        The statement collapsed onto one line and capped, so a message stays readable.
    """
    collapsed = " ".join(statement.split())
    if len(collapsed) <= _STATEMENT_ECHO_LIMIT:
        return collapsed
    return collapsed[:_STATEMENT_ECHO_LIMIT] + "..."


# THE STRUCTURAL ASSERTIONS (rules R-2, R-5, R-6) Seven checks, all against
# information_schema, all cheap, run before a single row is read.

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
        The column names in `ORDINAL_POSITION` order - the order a `SELECT *` returns
            them in, and the order the dump records.

    Raises:
        TableNotInScopeError: `table` is out of scope.
        UnknownTableError: `table` is not a table of the frozen schema.
        SchemaDriftError: Any of the seven assertions failed. The message names the
            table and the specific expectation.
    """
    spec = table_spec(table)
    where = _schema_name(connection) if schema is None else schema

    columns = _query(connection, _COLUMN_QUERY, (where, table))

    if not columns:
        raise SchemaDriftError(
            f"table `{table}` is declared by mysql/ACASDB.sql at line "
            f"{spec.schema_line} but is not present in schema {where!r}. "
            f"Apply the frozen schema before dumping - "
            f"harness/reset_db.sh does that and re-seeds."
        )

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

        # 5a. No temporal column: one could carry a wall-clock value into a dump and
        # break the byte-identical guarantee (rule R-6).
        if kind in _FORBIDDEN_TEMPORAL_TYPES:
            raise SchemaDriftError(
                f"column `{table}`.`{column}` has temporal type {kind!r}. "
                f"Agent Action Plan section 0.6.6 records that no in-scope "
                f"table contains one, which is why the dump needs no "
                f"timestamp masking; a temporal column would make two runs "
                f"differ."
            )

        # 7. Every column NOT NULL. Agent Action Plan section 0.6.2.
        if str(is_nullable).upper() != "NO":
            raise SchemaDriftError(
                f"column `{table}`.`{column}` is nullable. Every column of "
                f"the frozen schema is declared NOT NULL - "
                f"harness/reset_db.sh asserts the same from the database "
                f"side in acas_verify_shapes - because the bridge writes zero or "
                f"space rather than NULL."
            )

        # 5b. AUTO_INCREMENT and generated columns.
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


# VALUE RENDERING (rules R-2 and R-4) A TYPE DISPATCH, NOT A TRANSFORMATION. Nothing
# here trims, pads, rounds, re-scales or reformats.

# The one encoding choice this module makes, and it is documented rather than implicit.
_BYTES_ENCODING: Final[str] = "utf-8"


# =============================================================================
# THE TWO COLUMNS WHOSE VALUE NEVER REACHES A CAPTURE  (rule R-3, CWE-532)
#
# A capture is `SELECT *' and a capture is EVIDENCE - it is written to $ACAS_OUT,
# read by a human after a failure and cited by docs/migration/scenario-diff-evidence.md.
# `SYSTEM-REC' carries `RDBMS-PASSWD char(12)' [copybooks/wssystem.cob:L139] and
# `PASS-WORD char(4)' [mysql/ACASDB.sql:L1219], so an unmodified capture of that table
# puts a database password and an application password into that evidence.
#
# Of the two ways to remove the leak, only one keeps the row. BOUNDING THE TABLE OUT
# of the comparison would take the row with it: 168 columns the two cycles genuinely
# write - the run date, the IRS posting allocator, the one-shot latches, `Date-Form' -
# would sit outside every diff, and a bound drawn that way cannot reveal a difference
# in what it excludes. REDACTING THE TWO COLUMNS' VALUES removes the leak and keeps the
# row: every other column of `SYSTEM-REC' is compared exactly as it is elsewhere.
#
# The redaction is applied in `render_value', the ONE funnel every captured cell
# passes through, and it is keyed by `(table, column)' constants - so it is applied
# identically on both sides of a comparison and cannot itself produce a difference.
#
# WHAT IT COSTS, STATED PLAINLY: the two credential columns are not compared by
# value, in the capture or in the digest `harness/dump_tables.py --table-digest' takes of it. That
# costs nothing measurable here - both sides of one run connect with the SAME
# credentials, which this module requires of them, and the builder fills those columns
# from the same environment for both legs, so they cannot carry a behavioural
# difference of the migrated cycle. Every other column of the row, and the row's
# presence and count, remain compared and fingerprinted.
# =============================================================================

#: `(table, column)` pairs whose value is replaced by `REDACTED_VALUE` in a capture.
#: Closed, small, and stated here rather than derived from a name pattern: a pattern
#: would silently start redacting a column that merely looked like a credential.
REDACTED_COLUMNS: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        ("SYSTEM-REC", "RDBMS-PASSWD"),
        ("SYSTEM-REC", "PASS-WORD"),
    }
)

#: What a redacted cell holds. A fixed, obviously-not-data string: a reader can see
#: that the column HAS a value rather than wonder whether the capture lost it, and the
#: same eight-character rendering appears on both sides.
REDACTED_VALUE: Final[str] = "***redacted***"


def render_value(value: object, *, table: str, column: str) -> str | int:
    """Render one fetched value for the dump, or refuse it.

    Args:
        value: The value the driver returned.
        table: The table it came from, for the error messages.
        column: The column it came from, for the error messages.

    Returns:
        `int` for every integer width the schema uses, or `str` for a `DECIMAL`
            (rendered with `format(value, "f")`, so the declared scale survives and
            exponent notation can never appear) and for character data (exactly as the
            driver returned it, unpadded and untrimmed).

    Raises:
        NumericPolicyError: `value` is a `float`, or a non-finite `Decimal`. Rule R-2
            forbids binary floating point outright, and this module raises rather than
            rounding.
        UnexpectedValueTypeError: `value` is a `bool`, undecodable bytes, or a type no
            in-scope column can hold.
        UnexpectedNullError: `value` is `None`, which a schema declaring every column
            NOT NULL cannot legitimately produce.
    """
    #  THE CREDENTIAL COLUMNS ARE RENDERED, NOT READ. First, before any type
    #  check, so that no code path below can put the value into a message either.
    if (table, column) in REDACTED_COLUMNS:
        return REDACTED_VALUE

    if isinstance(value, bool):
        raise UnexpectedValueTypeError(
            f"`{table}`.`{column}` returned a bool ({value!r}). The dump "
            f"records integers as JSON integers; a bool would serialise "
            f"as true/false and no longer match the stored value. No "
            f"in-scope column can produce one."
        )

    # THE R-2 GUARD. A float here means the driver was configured wrongly, and silently
    # rounding it would destroy the exactness the whole engagement rests on.
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
        # `format(v, "f")` and not `str(v)`: str would render Decimal("1E+2") in
        # exponent notation, which no consumer of this dump should have to parse.
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
        schema: The schema to assert against; asked of the server when omitted.

    Returns:
        The dump object: `table`, `primary_key`, `columns`, `row_count` and `rows`, in
            that insertion order and with no other key.

    Raises:
        TableNotInScopeError: `table` is out of scope.
        UnknownTableError: `table` is not a table of the frozen schema.
        SchemaDriftError: A structural assertion failed, or the columns a `SELECT *`
            returned disagree with `information_schema`.
        NumericPolicyError: The rule R-2 value guard tripped.
        UnexpectedValueTypeError: A value had a type no column can hold.
        UnexpectedNullError: A NULL was fetched.
        DumpTimeoutError: The read deadline expired mid-table.
    """
    spec = table_spec(table)
    declared = assert_table_structure(connection, table, schema=schema)

    statement = (
        f"SELECT * FROM {_ident(table)} ORDER BY {_ident(spec.primary_key)}"
    )

    cursor = connection.cursor()
    try:
        try:
            cursor.execute(statement)
            # `columns` comes from the cursor description, which is the table's declared
            # order, and is NEVER sorted.
            description = cursor.description or ()
            columns = tuple(str(field[0]) for field in description)
            fetched = list(cursor.fetchall())
        except Exception as exc:
            if _is_timeout(exc):
                # As at the statement site above: the typed fields, never the
                # driver's own text. The TABLE name is frozen public metadata -
                # every one of the 22 is in the committed
                # data_dictionary/acas_posting_dictionary.json.
                fetch_errno, fetch_state = _driver_error_fields(exc)
                raise DumpTimeoutError(
                    f"reading table {table!r} did not complete within the "
                    f"{_ENV_READ_TIMEOUT} budget (errno {fetch_errno}, "
                    f"sqlstate {fetch_state})"
                ) from exc
            raise
    finally:
        cursor.close()

    # The map cannot silently drift (rule R-5): what SELECT * returned is compared with
    # what information_schema declares, name for name and position for position.
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

    # `row_count` is a convenience for a human reading a diff. It is derived, so it is
    # asserted rather than assumed.
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
    one connection. No thread, no pool, no batching. Under the runtime
    `autocommit=1` that `harness/Dockerfile.mariadb` declares at server
    level each table is read on its own, which is as consistent here as one
    implicit read transaction would be: the posting run has completed
    before the dump starts and nothing else writes to the schema, so no
    table can change between reads.

    Args:
        connection: An open DB-API connection.
        tables: The tables to dump, in the order to dump them. Duplicates are refused
            rather than dumped twice.
        schema: The schema to assert against; resolved once when omitted.

    Returns:
        A mapping of table name to dump object, in the order dumped.

    Raises:
        UnknownTableError: A name is not a table of the frozen schema, or appears more
            than once.
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


# SERIALISATION (rule R-6) The bytes are the product.

_JSON_INDENT: Final[int] = 2
_JSON_SEPARATORS: Final[tuple[str, str]] = (",", ": ")

_DUMP_SUFFIX: Final[str] = ".json"

# The temporary name a dump is written under before `os.replace` moves it into place, so
# a partial write can never be compared.
_TEMP_PREFIX: Final[str] = "."
_TEMP_SUFFIX: Final[str] = ".json.tmp"

# SECURE OUTPUT (CWE-59 symlink following, CWE-367 TOCTOU, CWE-312 cleartext storage,
# CWE-732 over-permissive files) A dump file is not a log line.

_OUTPUT_FILE_MODE: Final[int] = 0o600

_OUTPUT_DIR_MODE: Final[int] = 0o700

#: The umask `main` installs, so that anything created by this process - the output
#: directories included - is private to its owner.
_OUTPUT_UMASK: Final[int] = 0o077

#: `O_NOFOLLOW` where the platform has it. Linux and every BSD do.
_O_NOFOLLOW: Final[int] = getattr(os, "O_NOFOLLOW", 0)


def _write_text_securely(text: str, target: Path, staging: Path) -> None:
    """Write `text` to `target` atomically, privately, and without following.

    Args:
        text: The exact bytes-to-be, already assembled. Encoded UTF-8 with LF newlines
            and written in one call, so no reader can observe a partial file.
        target: The final path.
        staging: The temporary name, which MUST be in the same directory as `target` for
            the replace to be atomic.

    Raises:
        OSError: The staging file could not be created, written or moved. The caller
            wraps this in its own error type.
        behind: the staging file is removed on every failure path.
    """
    staging.unlink(missing_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW
    descriptor = os.open(staging, flags, _OUTPUT_FILE_MODE)
    try:
        # Re-applied explicitly.
        os.fchmod(descriptor, _OUTPUT_FILE_MODE)
        with os.fdopen(
            descriptor, "w", encoding="utf-8", newline="\n"
        ) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError as close_error:
            # NOT SWALLOWED SILENTLY. `EBADF` is the expected, uninteresting
            # case - the context manager above already closed the descriptor.
            # Anything else means the descriptor could not be released, which is
            # REPORTED: a cleanup failure that leaves no trace is how a leaked
            # descriptor or a full filesystem stays invisible. The real failure
            # still propagates, unchanged, from the `raise` below.
            if close_error.errno != errno.EBADF:
                _progress(
                    f"harness/dump_tables.py: warning: could not close the "
                    f"staging descriptor for {staging} while handling an "
                    f"earlier failure: errno {close_error.errno} "
                    f"({os.strerror(close_error.errno or 0)})"
                )
        staging.unlink(missing_ok=True)
        raise
    os.replace(staging, target)


def _make_output_directory(directory: Path) -> None:
    """Create `directory` and its parents, private to their owner.

    Args:
        directory: The directory to create.

    Raises:
        OSError: The directory could not be created.
    """
    directory.mkdir(parents=True, exist_ok=True, mode=_OUTPUT_DIR_MODE)


def dump_path(
    out: Path | str,
    table: str,
    *,
    scenario: str | None = None,
    side: str | None = None,
) -> Path:
    """Build the path a table's dump is written to.

    Args:
        out: The output directory, or the root under which `<scenario>/<side>/` is
            composed.
        table: One of the 22 in-scope tables.
        scenario: The scenario name. Must be given with `side`.
        side: `cobol` or `python`. Must be given with `scenario`.

    Returns:
        The path, with no directory created.

    Raises:
        UnknownTableError: `table` is not a table of the frozen schema.
        TableNotInScopeError: `table` is out of scope.
        ValueError: `scenario` and `side` were not both given or both omitted, `side` is
            not one of `SIDES`, or `scenario` contains a path separator.
    """
    table_spec(table)

    if (scenario is None) != (side is None):
        raise ValueError(
            "scenario and side belong together: give both, for the "
            "<out-dir>/<scenario>/<side>/ layout, or neither, for the "
            "<out>/ layout harness/docker-compose.yml uses."
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


def serialise_dump(dump: Mapping[str, Any]) -> str:
    """Render one dump object as the exact text `write_dump` writes.

    THE ONE DEFINITION OF THE CANONICAL BYTES. Published because a second caller
    needs them: `harness/dump_tables.py --table-digest` takes the SHA-256 of a table's canonical
    dump as a state fingerprint, and a digest over text serialised any other way -
    a different indent, a sorted key order, a missing trailing newline - would not be
    a digest of what the dump stage produces, so the two records could not corroborate
    each other. Both sides of a parity run invoke that one producer, which is what
    makes two independently taken digests comparable at all (rule R-4: one definition,
    not two).

    The five keys in `DUMP_KEYS` order, `indent=2`, `ensure_ascii=True`,
    `sort_keys=False`, separators `(",", ": ")`, and exactly one trailing newline.

    Args:
        dump: A dump object, as `dump_table` returns.

    Returns:
        The canonical text, ending in exactly one LF.

    Raises:
        ValueError: `dump` does not carry exactly the five expected keys in the
            expected order, or `row_count` disagrees with `rows`.
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
    return (
        json.dumps(
            dump,
            indent=_JSON_INDENT,
            ensure_ascii=True,
            sort_keys=False,
            separators=_JSON_SEPARATORS,
        )
        + "\n"
    )


def write_dump(dump: Mapping[str, Any], path: Path | str) -> Path:
    """Serialise one dump object to `path`, deterministically and atomically.

    The five keys are written in `DUMP_KEYS` order, `indent=2`, `ensure_ascii=True`,
    `sort_keys=False`, separators `(",", ": ")`, LF newlines, UTF-8, and exactly one
    trailing newline.

    Args:
        dump: A dump object, as `dump_table` returns.
        path: Where to write it. Parent directories are created, mode 0700.

    Returns:
        The path written.

    Raises:
        ValueError: `dump` does not carry exactly the five expected keys in the expected
            order, or `row_count` disagrees with `rows`.
        DumpWriteError: The file could not be written or moved.
    """
    # Serialised in full before the file is opened, so the descriptor is held for as
    # short a time as possible and a serialisation failure cannot leave a staging file
    # behind at all. `serialise_dump` also performs the two shape checks, so this
    # function and `harness/dump_tables.py --table-digest` refuse exactly the same inputs.
    text = serialise_dump(dump)

    target = Path(path)
    try:
        _make_output_directory(target.parent)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the output directory {target.parent}: {exc}"
        ) from exc

    temporary = target.parent / f"{_TEMP_PREFIX}{target.stem}{_TEMP_SUFFIX}"
    try:
        _write_text_securely(text, target, temporary)
    except OSError as exc:
        raise DumpWriteError(
            f"could not write the dump for table {dump['table']!r} to "
            f"{target}: {exc}"
        ) from exc

    return target


# The manifest's file name.
MANIFEST_FILENAME: Final[str] = "_manifest.json"

# Bumped only if the manifest's SHAPE changes. Version 2 added `attestation`; version
# 3 added `provenance` and widened `attestation`. An older tree is
# refused rather than read, because the whole point of these keys is that their
# ABSENCE cannot be mistaken for a pass.
MANIFEST_VERSION: Final[int] = 3

# The manifest's keys, in the order they are written. Fixed, like `DUMP_KEYS`, because
# the order is part of the byte-identical guarantee.
MANIFEST_KEYS: Final[tuple[str, ...]] = (
    "manifest_version",
    "producer",
    "stage",
    "scenario",
    "side",
    "selector",
    "provenance",
    "attestation",
    "table_count",
    "tables",
)

# =============================================================================
# PROVENANCE -- WHAT THIS CAPTURE WAS TAKEN FROM
#
# A manifest recorded WHAT was captured -- the table names, their row counts, their
# digests -- and, from version 2, whether the run that produced them exited zero. It
# recorded nothing about the RUN ITSELF, and that gap is what let two artifacts that
# were never part of the same attempt be compared and reported identical:
#
#   * No run id, so stages 1-5 of one attempt and 6-10 of another produced a verdict
#     and nothing in the evidence said so.
#   * No hash of the scenario definition, so a definition EDITED between the two legs
#     -- a changed fan-out switch, a changed affected-table list -- was invisible: the
#     comparison would have been bounded by two different lists.
#   * No hash of the frozen schema, so `mysql/ACASDB.sql` changing under the protocol
#     -- which Agent Action Plan section 0.8.1 forbids outright -- left no trace.
#   * No toolchain identity, so a capture taken by a different interpreter, or by an
#     EDITED dump tool, looked exactly like one taken by this one.
#   * No record of the command, so nobody reading the evidence could reproduce it.
#   * No per-operation statuses, so a four-operation scenario's evidence said only
#     that the wrapper exited zero.
#   * No prior-stage identity, so `normalize.py` could normalise tree A and claim to
#     have normalised tree B (that field is filled in by that tool).
#
# Every one of those is a way for a verdict to be about something other than what it
# claims. So each is recorded, and `diff_states.py` requires the two sides to AGREE on
# the ones that must match.
#
# The keys are fixed and ordered for the same reason `MANIFEST_KEYS` is.
# =============================================================================
PROVENANCE_KEYS: Final[tuple[str, ...]] = (
    "run_id",
    "scenario_file",
    "scenario_file_sha256",
    "frozen_schema_sha256",
    "producer_sha256",
    "python_version",
    "command",
    "source_manifest_sha256",
)

# A lower-case hexadecimal SHA-256, and nothing else. Used wherever a digest is
# REQUIRED rather than merely recorded, so that an empty or truncated one is a refusal
# instead of a value that compares equal to another empty one.
_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"[0-9a-f]{64}")

# The frozen schema, relative to `$ACAS_REPO`. Hashed into every manifest so that a
# change to it -- forbidden by Agent Action Plan section 0.8.1 -- cannot pass unnoticed
# through a comparison.
FROZEN_SCHEMA_RELPATH: Final[str] = "mysql/ACASDB.sql"

# =============================================================================
# THE RUN ATTESTATION -- WHY A CAPTURE HAS TO CARRY ONE
#
# The protocol's stages were operator discipline and nothing more: each tool exited
# with its own status and no tool ever looked at what the stage before it had
# done. Run the protocol against a checkout with no fixtures and no compiled
# oracle and every stage still "worked" -- seed exited 75, the COBOL run exited
# 74, the Python run exited 69, and the dump, normalise and diff stages then
# exited 0 apiece and printed "identical - 3 table(s) compared, no difference".
# An empty diff is the ONE documented pass condition (AAP section 0.8.5), so the
# harness certified the migration exact having compared two empty captures.
#
# The fix is to make the capture carry a claim about the run it came from. Each
# runner writes `<side>.run-status' beside its log when it finishes, this module
# reads it and records what it found, `normalize.py' carries it through, and
# `diff_states.py' refuses a pair that does not attest a COMPARABLE run. Nothing
# here INFERS success: a missing file or an unreadable one produces
# `attested: false', which is the fail-closed direction.
#
# THE STATUS IS EVIDENCE METADATA, NOT A GATE ON ONE VALUE, and the distinction
# is what makes a real behavioural difference investigable. A non-zero runner
# status has two entirely different meanings:
#
#   * THE HARNESS FAILED. A missing fixture, an unreachable server, a module that
#     does not publish an option, an overrun deadline. The run measured nothing, so
#     its capture is not evidence and a verdict drawn on it would be fiction. These
#     stay `attested: false'.
#   * THE MIGRATED CYCLE BEHAVED DIFFERENTLY FROM WHAT THE SCENARIO DECLARES.
#     [harness/run_python_scenario.sh] exits EX_BEHAVIOUR (69) for exactly this,
#     and it exits it AFTER running every operation, taking every post-run
#     assertion and leaving the database in the state the run produced. That state
#     IS the finding. Refusing to compare it
#     withheld the one artifact that says WHICH tables, rows and columns differ,
#     precisely when a human most needs it.
#
# So the attestation carries `run_status' verbatim and a `disposition' naming which
# of the two it is, and `attested' is true for a run that COMPLETED, whether or not
# its behaviour matched. A comparable-but-not-clean capture is never mistaken for a
# clean one: the disposition travels with it into the manifest and
# `diff_states.py' prints it above its verdict.
#
# The file is TSV, one `key<TAB>value' per line, and only these keys are read:
#     scenario                 the scenario the run was for
#     side                     cobol | python
#     status                   the runner's own exit status, as an integer
#     seed_fingerprint_sha256  digest of the pre-run seed fingerprint, or empty
# Unknown keys are ignored, so a runner may record more without breaking this.
# =============================================================================
RUN_STATUS_DIRNAME: Final[str] = "run-logs"
RUN_STATUS_SUFFIX: Final[str] = ".run-status"

# The attestation's own keys, fixed for the same reason `MANIFEST_KEYS` is. Widened in
# manifest version 3: the run id so a capture names the
# attempt it belongs to, the wrapper status separately from the behavioural counts so a
# reader never has to infer which kind of outcome it is looking at, the EXACT seed
# identity so two seedings with the same shape and different values cannot compare
# equal, and the ordered per-operation dispositions so a four-operation scenario's
# evidence says what each of the four actually did.
ATTESTATION_KEYS: Final[tuple[str, ...]] = (
    "attested",
    "disposition",
    "source",
    "run_id",
    "run_status",
    "wrapper_status",
    "behavioural",
    "assert_failures",
    "seed_fingerprint_sha256",
    "seed_marker_sha256",
    "operations",
    "detail",
)

#: The three dispositions a capture's run can carry, and the only three. They are
#: fixed strings so a downstream check can compare them exactly, and they mirror the
#: vocabulary `tests/conftest.py` uses for the same three-way split.
#:
#: `CLEAN` and `BEHAVIOURAL` are both COMPARABLE - the run reached its end and left
#: the database in the state it produced. `HARNESS_FAULT` and `UNKNOWN` are not: the
#: first measured nothing, the second cannot say whether it did.
DISPOSITION_CLEAN: Final[str] = "clean"
DISPOSITION_BEHAVIOURAL: Final[str] = "behavioural-difference"
DISPOSITION_HARNESS_FAULT: Final[str] = "harness-fault"
DISPOSITION_UNKNOWN: Final[str] = "unknown"

#: The runner exit status that means "every operation ran and a disposition
#: contradicted the scenario's declaration" - `EX_BEHAVIOUR` in
#: [harness/run_python_scenario.sh]. It is the ONE non-zero status whose capture is
#: still evidence, because the run completed and the difference it found is the
#: thing under comparison. The oracle-side runner has no equivalent: its own band is
#: 70-79 and every member is a precondition or a drive fault
#: [harness/run_cobol_scenario.sh].
BEHAVIOURAL_RUN_STATUS: Final[int] = 69

#: The dispositions on whose capture a verdict may be rendered.
COMPARABLE_DISPOSITIONS: Final[frozenset[str]] = frozenset(
    {DISPOSITION_CLEAN, DISPOSITION_BEHAVIOURAL}
)

# THE RUN-STATUS RECORD'S EXACT KEY SET
#
# IGNORING any key this reader did not recognise -- "so a runner may record more
# without breaking this" -- is the tolerance that would be the defect: a key misspelled
# by a runner, `statuss' or `seed_marker_sha_256', would be silently absent rather than
# reported, and a REPEATED key would silently take its last value. Both turn a missing
# attestation into a passing one, which is the exact direction this machinery exists to
# make impossible.
#
# So the key set is exact. A key outside these three sets is a refusal; a key
# outside REPEATED that appears twice is a refusal.
RUN_STATUS_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "scenario",
        "side",
        "run_id",
        "status",
        "wrapper_status",
        "seed_fingerprint_sha256",
        "seed_marker_sha256",
        "operations",
    }
)

# Written by one runner and not the other, so their absence is not a fault: the Python
# side counts contradicted dispositions and failed assertions, and the oracle side has
# neither concept -- it publishes each operation's observed term code instead.
RUN_STATUS_OPTIONAL_KEYS: Final[frozenset[str]] = frozenset(
    {"behavioural", "assert_failures"}
)

# The one key that legitimately appears more than once: one record per declared
# operation, in declared order.
RUN_STATUS_REPEATED_KEYS: Final[frozenset[str]] = frozenset({"operation_status"})

# The sentinel both runners write for an operation that was declared and never driven.
# It is NOT a number precisely so that it cannot be read as a clean disposition.
OPERATION_NOT_RUN: Final[str] = "not-run"

# At most this many bytes are read from a run-status file. It holds four short
# lines; anything larger is not the file this module is looking for, and reading
# it whole would be an unbounded read of an operator-supplied path.
_RUN_STATUS_MAX_BYTES: Final[int] = 64 * 1024

# What this module writes into `stage`, and the selector vocabulary. Both are fixed
# strings so a downstream check can compare them exactly.
MANIFEST_STAGE_RAW: Final[str] = "raw"
MANIFEST_STAGE_NORMALIZED: Final[str] = "normalized"

SELECTOR_SCENARIO_FILE: Final[str] = "scenario-file"
SELECTOR_TABLES: Final[str] = "tables"
SELECTOR_ALL_IN_SCOPE: Final[str] = "all-in-scope"
SELECTOR_INHERITED: Final[str] = "inherited"

_PRODUCER: Final[str] = "harness/dump_tables.py"

# The staging directory's name, derived from the destination's.
_STAGING_SUFFIX: Final[str] = ".staging"


def file_digest(path: Path | str) -> str:
    """Return the lower-case hex SHA-256 of a file's bytes.

    Read in binary in fixed-size blocks, so the digest is of the bytes on disk exactly
    as the next stage will read them - not of a re-serialised object, which could differ
    in a way the digest was meant to detect.

    Args:
        path: The file to digest.

    Returns:
        The digest, 64 hexadecimal characters.

    Raises:
        DumpWriteError: The file could not be read back.
    """
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(_DIGEST_BLOCK), b""):
                digest.update(block)
    except OSError as exc:
        raise DumpWriteError(
            f"could not read back {path} to record its digest in the "
            f"completeness manifest: {exc}"
        ) from exc
    return digest.hexdigest()


def unattested(
    detail: str,
    *,
    disposition: str = DISPOSITION_UNKNOWN,
    source: str | None = None,
    run_status: int | None = None,
) -> dict[str, Any]:
    """Return an attestation that claims nothing, with the reason it claims nothing.

    Used wherever a run either could not be established or measured nothing.
    `attested` is False here in every case, and the `disposition` says which kind of
    nothing it was, so that `diff_states.py` can report the difference between "no
    record was found" and "the harness itself failed".

    Args:
        detail: Why no claim is made, in a form an operator can act on.
        disposition: One of the four fixed strings. `UNKNOWN` when no usable record
            was found at all; `HARNESS_FAULT` when a record was found and reports a
            status that means the run measured nothing.
        source: The record that was read, when there was one. Kept even for a
            refusal, because an operator's first question is which file said so.
        run_status: The status that was read, when there was one. Recorded verbatim
            rather than reduced to a boolean - it is the fastest route to the
            failing stage's own diagnosis.

    Returns:
        An attestation object, keys in `ATTESTATION_KEYS` order.
    """
    return {
        "attested": False,
        "disposition": disposition,
        "source": source,
        "run_id": None,
        "run_status": run_status,
        "wrapper_status": run_status,
        "behavioural": None,
        "assert_failures": None,
        "seed_fingerprint_sha256": None,
        "seed_marker_sha256": None,
        "operations": None,
        "detail": detail,
    }


def run_status_path(
    out_root: Path | str, scenario: str, side: str
) -> Path:
    """Return where the runner for `side` records the outcome of `scenario`.

    Both runners write beside their transcript, under `<out>/run-logs/<scenario>/`,
    which is deliberately OUTSIDE `<out>/<scenario>/` so that nothing they write can
    land in a compared tree.

    Args:
        out_root: `$ACAS_OUT`, or whatever `--out-dir` named.
        scenario: The scenario name.
        side: `cobol` or `python`.

    Returns:
        The path of the run-status file. It may not exist.
    """
    return (
        Path(out_root) / RUN_STATUS_DIRNAME / scenario / f"{side}{RUN_STATUS_SUFFIX}"
    )


def read_run_attestation(
    out_root: Path | str | None, scenario: str | None, side: str | None
) -> dict[str, Any]:
    """Read the run-status file this capture belongs to and judge it.

    `attested` is True only when a file exists, parses, names THIS scenario and side,
    and records a status whose run COMPLETED - status 0, or the one behavioural status
    `BEHAVIOURAL_RUN_STATUS`. Every other outcome is a refusal with a reason,
    including a file that is absent, which is the ordinary case when the dump is run
    out of order.

    THE STATUS IS RECORDED VERBATIM EITHER WAY, together with a `disposition` naming
    which of the three kinds of run it was. That is what lets a REAL behavioural
    difference be investigated: the runner exits 69 after running every operation and
    leaving the database in the state it produced, so that state is the finding, and
    withholding it from the differ withholds the only artifact that says which rows
    and columns differ.

    Args:
        out_root: The output root, or None for the `--out DIR` layout.
        scenario: The scenario name, or None.
        side: `cobol` or `python`, or None.

    Returns:
        An attestation object, keys in `ATTESTATION_KEYS` order. Never raises: a dump
            must still be publishable when the run stage left nothing behind, because
            the refusal has to travel WITH the capture rather than replace it.
    """
    if out_root is None or scenario is None or side is None:
        return unattested(
            "this dump was taken with --out, which names a directory outright and "
            "carries no scenario or side, so the run it belongs to cannot be "
            "identified. Use --scenario NAME --side SIDE for a capture that is "
            "meant to be compared."
        )

    path = run_status_path(out_root, scenario, side)
    try:
        if not path.is_file():
            return unattested(
                f"no run-status file at {path}, so nothing attests that the "
                f"{side} run of {scenario} completed. harness/"
                f"run_{'cobol' if side == 'cobol' else 'python'}_scenario.sh "
                f"writes it when it finishes; a dump taken before the run, or "
                f"after a run that was killed outright, has none."
            )
        with open(path, "rb") as handle:
            raw = handle.read(_RUN_STATUS_MAX_BYTES + 1)
    except OSError as exc:
        return unattested(f"could not read the run-status file {path}: {exc}")

    if len(raw) > _RUN_STATUS_MAX_BYTES:
        return unattested(
            f"the run-status file {path} is larger than "
            f"{_RUN_STATUS_MAX_BYTES} bytes, so it is not the four-line record "
            f"a runner writes."
        )

    # AN EXACT KEY SET, NOT A TOLERANT ONE
    fields: dict[str, str] = {}
    operations: list[dict[str, Any]] = []
    for line in raw.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        if "\t" not in line:
            return unattested(
                f"the run-status file {path} holds a line with no tab in it: "
                f"{line[:80]!r}. Every record is `key<TAB>value'."
            )
        key, _, value = line.partition("\t")
        key = key.strip()

        if key in RUN_STATUS_REPEATED_KEYS:
            parts = value.split("\t")
            if len(parts) != 3:
                return unattested(
                    f"the run-status file {path} holds an {key!r} record with "
                    f"{len(parts)} field(s); it must carry an index, an operation "
                    f"name and an observed status."
                )
            index_text, operation_name, observed = (part.strip() for part in parts)
            try:
                operation_index = int(index_text)
            except ValueError:
                return unattested(
                    f"the run-status file {path} holds an {key!r} record whose "
                    f"index {index_text!r} is not an integer."
                )
            operations.append(
                {
                    "index": operation_index,
                    "operation": operation_name,
                    "status": observed,
                }
            )
            continue

        if key not in RUN_STATUS_REQUIRED_KEYS and key not in RUN_STATUS_OPTIONAL_KEYS:
            return unattested(
                f"the run-status file {path} holds an unrecognised key {key!r}. "
                f"An unknown key must not be IGNORED, because a key misspelled by "
                f"a runner read as absent and a missing attestation read as a "
                f"passing one. The record's keys are now exact: required "
                f"{sorted(RUN_STATUS_REQUIRED_KEYS)}, optional "
                f"{sorted(RUN_STATUS_OPTIONAL_KEYS)}, repeated "
                f"{sorted(RUN_STATUS_REPEATED_KEYS)}."
            )
        if key in fields:
            return unattested(
                f"the run-status file {path} records {key!r} more than once. A "
                f"repeated key taken silently at its LAST value is a way "
                f"for a failed run to attest a successful one."
            )
        fields[key] = value.strip()

    missing = sorted(RUN_STATUS_REQUIRED_KEYS - fields.keys())
    if missing:
        return unattested(
            f"the run-status file {path} is missing required key(s) {missing}. A "
            f"record without them cannot establish which attempt, which seed or "
            f"which dispositions this capture belongs to."
        )

    recorded_scenario = fields["scenario"]
    recorded_side = fields["side"]
    if recorded_scenario != scenario or recorded_side != side:
        return unattested(
            f"the run-status file {path} names scenario "
            f"{recorded_scenario or '<absent>'!r} side "
            f"{recorded_side or '<absent>'!r}, and this dump is "
            f"{scenario!r}/{side!r}. It belongs to a different run, so it "
            f"attests nothing about this one."
        )

    def _as_int(key: str) -> int | None:
        text = fields.get(key, "")
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None

    status = _as_int("status")
    if status is None:
        return unattested(
            f"the run-status file {path} records status "
            f"{fields['status'] or '<empty>'!r}, which is not an integer.",
            source=str(path),
        )

    wrapper = _as_int("wrapper_status")
    if wrapper is None:
        return unattested(
            f"the run-status file {path} records wrapper_status "
            f"{fields['wrapper_status'] or '<empty>'!r}, which is not an integer.",
            source=str(path),
        )
    if status != wrapper:
        return unattested(
            f"the run-status file {path} records status {status} and "
            f"wrapper_status {wrapper}. They are the same fact under two names; two "
            f"values means the record was assembled from more than one run.",
            source=str(path),
            run_status=status,
        )

    if status == BEHAVIOURAL_RUN_STATUS and side == SIDE_PYTHON:
        # THE ONE NON-ZERO STATUS WHOSE CAPTURE IS STILL EVIDENCE. The runner
        # exits EX_BEHAVIOUR only after every operation has run, every post-run
        # assertion has been taken and the database holds whatever the run produced.
        # A disposition contradicting the scenario's declaration is a FINDING, and
        # the state diff is how a human sees what it consists of - so the capture is
        # attested as comparable and carries the status and the disposition with it.
        # It is scoped to the Python side because the oracle-side runner has no
        # equivalent: 69 is not in its band at all. `behavioural`, published as its
        # own count beside the status, is what lets a reader tell this from a
        # wrapper fault without knowing the runner's exit-code bands.
        #
        # WHAT MAKES THIS SAFE IS UPSTREAM, NOT HERE. This branch
        # attests a capture as comparable on the strength of one number, so it is
        # only as sound as the rule that produced the number. A rule of "any child
        # status but 2 is a disposition" would let an uncaught exception, a missing
        # interpreter, a signal or any arbitrary tool exit arrive here as 69 and be
        # attested as a measured semantic difference.
        # harness/run_python_scenario.sh now admits ONLY zero and the operation's own
        # frozen term codes -- see its `ACAS_PY_TERM_CODE_MAP' and
        # `acas_py_status_is_semantic' -- and exits EX_ASSERT for everything else, so
        # a 69 reaching this branch can only mean a term code that contradicted the
        # scenario. The fault statuses fall through to the refusal below.
        return {
            "attested": True,
            "disposition": DISPOSITION_BEHAVIOURAL,
            "source": str(path),
            "run_id": fields["run_id"] or None,
            "run_status": status,
            "wrapper_status": wrapper,
            "behavioural": _as_int("behavioural"),
            "assert_failures": _as_int("assert_failures"),
            "seed_fingerprint_sha256": fields["seed_fingerprint_sha256"] or None,
            "seed_marker_sha256": fields["seed_marker_sha256"] or None,
            "operations": _as_int("operations"),
            "detail": (
                f"the {side} run of {scenario} exited {status}: every operation "
                f"ran and at least one disposition contradicted the scenario's "
                f"declaration. The run COMPLETED, so this capture is the state it "
                f"produced and is comparable - but the verdict below describes a "
                f"run that already reported a behavioural difference, and must not "
                f"be read as a clean one. The runner's own log names which "
                f"operation and which status."
            ),
        }

    # ZERO WRAPPER HEALTH IS OTHERWISE REQUIRED. A non-zero status
    # means the stage could not verify its own preconditions, so it measured nothing.
    if status != 0:
        return unattested(
            f"the {side} run of {scenario} exited {status}, which is a harness "
            f"fault rather than a behavioural result: the run did not measure "
            f"behaviour, so its capture is not evidence. {path} records it. "
            f"Re-run the stage; a capture taken after a failed run cannot support "
            f"a verdict.",
            disposition=DISPOSITION_HARNESS_FAULT,
            source=str(path),
            run_status=status,
        )

    run_id = fields["run_id"]
    if not run_id:
        return unattested(
            f"the run-status file {path} carries an empty run_id, so this capture "
            f"cannot name the attempt it belongs to. Without it, artifacts of two "
            f"different attempts cannot be told apart at the comparison."
        )

    # THE EXACT SEED IDENTITY IS REQUIRED AND MUST BE A DIGEST
    seed_marker = fields["seed_marker_sha256"]
    if not _SHA256_RE.fullmatch(seed_marker):
        return unattested(
            f"the run-status file {path} carries seed_marker_sha256 "
            f"{seed_marker or '<empty>'!r}, which is not a SHA-256. That digest is "
            f"the EXACT identity of the seeded bytes -- harness/reset_db.sh publishes "
            f"it from the fixture marker harness/seed.sh stages -- and without it the "
            f"only thing binding the two legs is a list of ROW COUNTS, which two "
            f"seedings with the same shape and different values share."
        )

    declared = _as_int("operations")
    if declared is None or declared < 0:
        return unattested(
            f"the run-status file {path} records operations "
            f"{fields['operations'] or '<empty>'!r}, which is not a count."
        )
    if len(operations) != declared:
        return unattested(
            f"the run-status file {path} declares {declared} operation(s) and "
            f"carries {len(operations)} disposition record(s). A capture cannot "
            f"attest operations whose outcome was never recorded."
        )
    if [entry["index"] for entry in operations] != list(range(1, declared + 1)):
        return unattested(
            f"the run-status file {path} carries operation indices "
            f"{[entry['index'] for entry in operations]}, which are not 1..{declared} "
            f"in order. The ORDER is part of the scenario: a later operation reads "
            f"state an earlier one wrote."
        )

    # EVERY OPERATION MUST CARRY A REAL DISPOSITION. The
    # `not-run' sentinel is exactly what it says, and a capture cannot support a
    # verdict about an operation that never ran.
    for entry in operations:
        observed = str(entry["status"])
        if observed == OPERATION_NOT_RUN:
            return unattested(
                f"the run-status file {path} records operation "
                f"{entry['index']} ({entry['operation']!r}) as {OPERATION_NOT_RUN!r}: "
                f"it was declared and never driven. The database therefore does not "
                f"hold its effects, and a capture taken now is of a partial run."
            )
        try:
            numeric = int(observed)
        except ValueError:
            return unattested(
                f"the run-status file {path} records operation {entry['index']} "
                f"({entry['operation']!r}) with status {observed!r}, which is "
                f"neither an integer nor {OPERATION_NOT_RUN!r}."
            )
        if not 0 <= numeric <= 255:
            return unattested(
                f"the run-status file {path} records operation {entry['index']} "
                f"({entry['operation']!r}) with status {numeric}, outside the 0..255 "
                f"range a process status can hold."
            )
        entry["status"] = numeric

    return {
        "attested": True,
        "disposition": DISPOSITION_CLEAN,
        "source": str(path),
        "run_id": run_id,
        "run_status": 0,
        "wrapper_status": 0,
        "behavioural": _as_int("behavioural"),
        "assert_failures": _as_int("assert_failures"),
        "seed_fingerprint_sha256": fields["seed_fingerprint_sha256"] or None,
        "seed_marker_sha256": seed_marker,
        "operations": operations,
        "detail": None,
    }


def optional_file_digest(path: Path | str | None) -> str | None:
    """Return a file's SHA-256, or None when it cannot be taken.

    Provenance must never be the reason a capture cannot be published: a missing or
    unreadable input is recorded as `None`, and the tools that REQUIRE a particular
    field refuse there, where the claim is actually made.

    Args:
        path: The file, or None.

    Returns:
        The lower-case hex digest, or None.
    """
    if path is None:
        return None
    try:
        return file_digest(path)
    except (OSError, ValueError):
        return None


def build_provenance(
    *,
    run_id: str | None,
    scenario_file: Path | str | None,
    repository: Path | str | None,
    command: Sequence[str] | None,
    source_manifest_sha256: str | None = None,
    producer_path: Path | str | None = None,
) -> dict[str, Any]:
    """Assemble the provenance block: what this capture was taken FROM.

    Every field answers a way a verdict could otherwise be about something other than
    what it claims - see PROVENANCE_KEYS for the enumeration. Nothing here raises: a
    field that cannot be established is `None` and the tool that requires it refuses.

    Args:
        run_id: The attempt this capture belongs to, from `$ACAS_PARITY_RUN_ID` or the
            runner that published the run-status record.
        scenario_file: The scenario definition that bounded the comparison.
        repository: `$ACAS_REPO`, used only to locate the frozen schema.
        command: The argument vector that produced this capture.
        source_manifest_sha256: The digest of the manifest this tree was DERIVED from.
            None at the raw stage, which is derived from the database rather than from
            another tree; `normalize.py` fills it in.
        producer_path: The tool's own file, hashed so that an EDITED tool is
            distinguishable from this one. Defaults to this module.

    Returns:
        The provenance object, keys in `PROVENANCE_KEYS` order.
    """
    schema_path: Path | None = None
    if repository is not None:
        schema_path = Path(repository) / FROZEN_SCHEMA_RELPATH

    if producer_path is None:
        producer_path = Path(__file__).resolve()

    return {
        "run_id": run_id or None,
        "scenario_file": str(scenario_file) if scenario_file is not None else None,
        "scenario_file_sha256": optional_file_digest(scenario_file),
        "frozen_schema_sha256": optional_file_digest(schema_path),
        "producer_sha256": optional_file_digest(producer_path),
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        ),
        "command": list(command) if command is not None else None,
        "source_manifest_sha256": source_manifest_sha256,
    }


def build_manifest(
    entries: Sequence[tuple[str, int, str]],
    *,
    stage: str,
    producer: str = _PRODUCER,
    scenario: str | None = None,
    side: str | None = None,
    selector: str = SELECTOR_INHERITED,
    provenance: Mapping[str, Any] | None = None,
    attestation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a completeness manifest.

    Args:
        entries: One `(table, row_count, digest)` triple per published file.
        stage: `MANIFEST_STAGE_RAW` or `MANIFEST_STAGE_NORMALIZED`.
        producer: The tool that wrote the tree.
        scenario: The scenario this tree belongs to, or None.
        side: `cobol` or `python`, or None.
        selector: How the table list was chosen.
        provenance: What this capture was taken from, as `build_provenance` returns.
            Omitted means every field is None, which is recorded as such rather than
            left out - an absent field is a refusal downstream, and a missing KEY would
            be a shape change.
        attestation: What the run stage claimed, as `read_run_attestation` returns.
            Omitted means "no claim", which is recorded as such rather than left out.

    Returns:
        The manifest object, keys in `MANIFEST_KEYS` order.

    Raises:
        ValueError: `stage` is not one of the two, or a table appears twice.
    """
    if stage not in {MANIFEST_STAGE_RAW, MANIFEST_STAGE_NORMALIZED}:
        raise ValueError(
            f"stage must be {MANIFEST_STAGE_RAW!r} or "
            f"{MANIFEST_STAGE_NORMALIZED!r}; got {stage!r}."
        )
    ordered = sorted(entries, key=lambda entry: entry[0])
    seen: set[str] = set()
    tables: list[dict[str, Any]] = []
    for table, row_count, digest in ordered:
        if table in seen:
            raise ValueError(
                f"table {table!r} appears twice in a manifest; each table "
                f"is published to exactly one file."
            )
        seen.add(table)
        tables.append(
            {"table": table, "row_count": int(row_count), "sha256": digest}
        )
    if attestation is None:
        attestation = unattested(
            "no run attestation was supplied to build_manifest, so this tree "
            "makes no claim about the run it came from."
        )
    if provenance is None:
        provenance = build_provenance(
            run_id=None, scenario_file=None, repository=None, command=None
        )
    return {
        "manifest_version": MANIFEST_VERSION,
        "producer": producer,
        "stage": stage,
        "scenario": scenario,
        "side": side,
        "selector": selector,
        # Rebuilt key by key in PROVENANCE_KEYS order, for the same reason the
        # attestation is: a caller must not be able to introduce a key order that
        # breaks byte-identity.
        "provenance": {key: provenance.get(key) for key in PROVENANCE_KEYS},
        # Rebuilt key by key in ATTESTATION_KEYS order rather than passed through,
        # so a caller cannot introduce a key order that breaks byte-identity.
        "attestation": {key: attestation.get(key) for key in ATTESTATION_KEYS},
        "table_count": len(tables),
        "tables": tables,
    }


def write_manifest(manifest: Mapping[str, Any], path: Path | str) -> Path:
    """Serialise a manifest with the same byte discipline as a dump.

    Args:
        manifest: The manifest object, as `build_manifest` returns.
        path: Where to write it.

    Returns:
        The path written.

    Raises:
        ValueError: The keys are not exactly `MANIFEST_KEYS` in order.
        DumpWriteError: The file could not be written or moved.
    """
    keys = tuple(manifest.keys())
    if keys != MANIFEST_KEYS:
        raise ValueError(
            f"a manifest must carry exactly the keys {list(MANIFEST_KEYS)} "
            f"in that order; got {list(keys)}."
        )

    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the directory for the completeness manifest "
            f"{target}: {exc}"
        ) from exc

    temporary = target.parent / f"{_TEMP_PREFIX}{target.stem}{_TEMP_SUFFIX}"
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(
                manifest,
                handle,
                indent=_JSON_INDENT,
                ensure_ascii=True,
                sort_keys=False,
                separators=_JSON_SEPARATORS,
            )
            handle.write("\n")
        os.replace(temporary, target)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError as unlink_error:
            # NOT SWALLOWED SILENTLY. A surviving staging file sits inside the
            # published tree, where `discover_tables` skips it by its `_` prefix
            # rather than by knowing it is rubbish - so a leftover one is
            # invisible to the next stage while still occupying the directory.
            # Reported here; the real failure is still the `DumpWriteError`
            # raised below.
            _progress(
                f"harness/dump_tables.py: warning: the staging file "
                f"{temporary} could not be removed after the manifest write "
                f"failed: errno {unlink_error.errno} "
                f"({os.strerror(unlink_error.errno or 0)})"
            )
        raise DumpWriteError(
            f"could not write the completeness manifest {target}: {exc}"
        ) from exc

    return target


def publish_dumps(
    dumps: Mapping[str, Mapping[str, Any]],
    out: Path | str,
    *,
    scenario: str | None = None,
    side: str | None = None,
    selector: str = SELECTOR_INHERITED,
    provenance: Mapping[str, Any] | None = None,
    attestation: Mapping[str, Any] | None = None,
) -> tuple[Path, ...]:
    """Publish a whole set of dumps, staged, with a manifest written last.

    The destination is left in one of exactly two states: carrying this run's complete
    set plus its manifest, or carrying no manifest at all. It is never left holding a
    mixture of two runs.

    Args:
        dumps: A mapping of table name to dump object, as `dump_tables` returns. Every
            entry is written.
        out: The output directory, or the root for the composed layout.
        scenario: The scenario name, for the composed layout and for the manifest's
            identity.
        side: `cobol` or `python`.
        selector: How the table list was chosen, recorded in the manifest.
        provenance: What this capture was taken from, recorded verbatim in the manifest
            so a later stage can require the two sides to agree about it.
        attestation: What the run stage claimed, recorded verbatim in the manifest so
            that the refusal travels with the capture rather than replacing it.

    Returns:
        The published paths - the `<TABLE>.json` files in the order written, then the
            manifest last, which is also the order they reached the destination.

    Raises:
        ValueError: A dump object is malformed, or the layout arguments are
            inconsistent.
        DumpWriteError: A file could not be written, staged or published.
    """
    if not dumps:
        raise ValueError(
            "publish_dumps was given no dump to publish. A table with no "
            "rows still produces a dump object with row_count 0, so an "
            "empty mapping means the dump stage selected nothing - which "
            "must not be published as a complete tree."
        )

    # Derive the destination directory from the same helper the individual paths come
    # from, so the two can never disagree about the layout.
    first = next(iter(dumps))
    destination = dump_path(
        out, first, scenario=scenario, side=side
    ).parent
    staging = destination.parent / (
        f"{_TEMP_PREFIX}{destination.name}{_STAGING_SUFFIX}"
    )

    _reset_staging(staging)
    try:
        entries: list[tuple[str, int, str]] = []
        staged: list[Path] = []
        for table, dump in dumps.items():
            staged_path = write_dump(dump, staging / f"{table}{_DUMP_SUFFIX}")
            staged.append(staged_path)
            entries.append(
                (table, int(dump["row_count"]), file_digest(staged_path))
            )
        manifest = build_manifest(
            entries,
            stage=MANIFEST_STAGE_RAW,
            scenario=scenario,
            side=side,
            selector=selector,
            provenance=provenance,
            attestation=attestation,
        )
        staged_manifest = write_manifest(
            manifest, staging / MANIFEST_FILENAME
        )
        return _publish_staged(destination, staged, staged_manifest)
    finally:
        # Whatever happened, no staging directory is left behind. Removing it cannot
        # mask a failure.
        _remove_tree(staging)


def _reset_staging(staging: Path) -> None:
    """Create an empty staging directory, removing any predecessor.

    Args:
        staging: The staging directory.

    Raises:
        DumpWriteError: It could not be removed or created.
    """
    _remove_tree(staging, fatal=True)
    try:
        staging.mkdir(parents=True)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the staging directory {staging}: {exc}"
        ) from exc


def _remove_tree(path: Path, *, fatal: bool = False) -> None:
    """Remove a directory tree.

    Args:
        path: The directory to remove.
        fatal: Whether a failure is an error. False for the tidy-up in a `finally`,
            where a failure must not mask the real one.

    Raises:
        DumpWriteError: `fatal` and the tree could not be removed.
    """
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        if fatal:
            raise DumpWriteError(
                f"a previous run left the staging directory {path} behind "
                f"and it could not be removed: {exc}. Remove it by hand: a "
                f"stale staging directory must never be published."
            ) from exc


def _publish_staged(
    destination: Path,
    staged: Sequence[Path],
    staged_manifest: Path,
) -> tuple[Path, ...]:
    """Move a staged set into its destination, manifest last.

    Args:
        destination: Where the set is published.
        staged: The staged `<TABLE>.json` paths, already complete. The staging directory
            itself is not passed.
        staged_manifest: The staged manifest path.

    Returns:
        The published paths, the manifest last.

    Raises:
        DumpWriteError: The destination could not be prepared, or a move failed.
    """
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the output directory {destination}: {exc}"
        ) from exc

    existing_manifest = destination / MANIFEST_FILENAME
    try:
        existing_manifest.unlink(missing_ok=True)
    except OSError as exc:
        raise DumpWriteError(
            f"could not remove the previous completeness manifest "
            f"{existing_manifest} before republishing: {exc}. It is deleted "
            f"first on purpose, so that an interrupted publish leaves a "
            f"tree that declares itself unfinished rather than one that "
            f"mixes two runs."
        ) from exc

    # Every stale dump and every leftover temporary goes, so the destination cannot end
    # up holding a table this run did not write.
    for entry in sorted(destination.iterdir(), key=lambda item: item.name):
        if not entry.is_file():
            continue
        if not (
            entry.name.endswith(_DUMP_SUFFIX)
            or entry.name.endswith(_TEMP_SUFFIX)
        ):
            continue
        try:
            entry.unlink()
        except OSError as exc:
            raise DumpWriteError(
                f"could not remove the stale file {entry} from the output "
                f"directory: {exc}"
            ) from exc

    published: list[Path] = []
    for source in staged:
        target = destination / source.name
        try:
            os.replace(source, target)
        except OSError as exc:
            raise DumpWriteError(
                f"could not publish {source.name} into {destination}: "
                f"{exc}. The tree now carries no manifest, so the next "
                f"stage will refuse it rather than compare a partial set."
            ) from exc
        published.append(target)

    manifest_target = destination / MANIFEST_FILENAME
    try:
        os.replace(staged_manifest, manifest_target)
    except OSError as exc:
        raise DumpWriteError(
            f"could not publish the completeness manifest into "
            f"{destination}: {exc}. The set is present but unmarked, so it "
            f"will be refused - re-run this stage."
        ) from exc
    published.append(manifest_target)
    return tuple(published)


# THE COMPARISON IS BOUNDED BY THE 22 IN-SCOPE TABLES, NOT BY THE SCENARIO'S
# DECLARED EFFECT. `scenario_tables` below still reads `affected_tables`, because
# narrowing to one table is useful while debugging and because the runners assert
# the declared effect against that list - but it is not the evidence bound. A
# capture bounded by what a scenario EXPECTS to move cannot show a difference in
# anything it did not expect to move, and Agent Action Plan section 0.8.5 makes an
# empty diff the single pass condition, so the narrower bound would have let a
# scenario certify parity while a system row differed. Both cycles perform
# `overrewrite.` [general/general.cbl:L656-L672] - keys 1, 2 and 4, reproduced by
# `acas_posting/cli/args.py::overrewrite` - so SYSTEM-REC, SYSDEFLT-REC and
# SYSTOT-REC are comparable on both sides rather than a source of false failure.


# ---------------------------------------------------------------------------
#  THE SHARED SCENARIO PARSER IS RESOLVED BY PATH, NOT BY NAME.
#
#  `harness/normalize.py` is a SIBLING FILE, not an installed package, so a bare
#  `import normalize` resolves only when this directory already sits on `sys.path`.
#  That holds when this module is run as a script from `harness/` and does NOT hold
#  when a test loads it by path, which made the import ORDER-DEPENDENT: it resolved if
#  some other harness module had inserted the directory first and failed otherwise.
#  The failure was then reported as "PyYAML is not importable" - a different fault with
#  a different remedy - so the refusal that should have followed was never produced.
#  Measured symptom: `tests/scenarios/` run on its own failed twelve tests while the
#  full suite passed, because in the full suite an earlier module did the insert.
#
#  Resolved from this module's OWN location, so it behaves identically however the
#  module was loaded and depends on nothing else having run first. `sys.path` is
#  deliberately left alone: making one import succeed by mutating the interpreter's
#  global search path is what allowed the order dependency to hide, and this module is
#  imported into test processes where a shadowing entry would be a real hazard.
# ---------------------------------------------------------------------------
def _load_scenario_yaml_module() -> Any:
    """Load the sibling module that owns the shared scenario parser, by path.

    The parser lives in `harness/normalize.py`: it was
    `harness/scenario_yaml.py`, which is not one of the harness paths the Agent Action
    Plan section 0.3.1 inventory names, and the canonicalisation module is where the
    other definitions every consumer must agree on already live.

    REGISTERED IN `sys.modules` BEFORE EXECUTION, and removed again if execution
    fails. Not optional: the module declares `@dataclass` classes with `slots=True`,
    which rebuilds each class and makes `dataclasses` look the defining module up by
    name - so an unregistered module fails with an `AttributeError` raised from inside
    the standard library, naming neither this call nor the real cause.

    Returns:
        The executed module, whose `load_scenario_yaml` rejects a duplicate key instead
            of applying last-one-wins.

    Raises:
        ImportError: The sibling file is absent or cannot be executed - which includes
            PyYAML being unavailable, since the loader types it builds subclass PyYAML's.
            The message names which of the two it was, so the caller's refusal can say
            what is actually missing.
    """
    import importlib.util  # noqa: PLC0415 - lazy, alongside the import it performs

    sibling = Path(__file__).resolve().parent / "normalize.py"
    if not sibling.is_file():
        raise ImportError(
            f"the shared duplicate-rejecting scenario parser is absent: {sibling}"
        )
    module_name = "acas_harness_normalize_scenario_parser"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_name, sibling)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"the shared scenario parser is not loadable: {sibling}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def scenario_tables(path: Path | str) -> tuple[str, ...]:
    """Read a scenario's affected-table list.

    Args:
        path: The scenario definition to read.

    Returns:
        The table names, in the order the scenario lists them.

    Raises:
        ScenarioFileError: The file is missing, unreadable, not a mapping, carries
            neither key or both, or the list is empty or holds something that is not a
            table name.
        TableNotInScopeError: The list names an out-of-scope table.
        UnknownTableError: The list names something that is not a table.
    """
    try:
        import yaml  # noqa: PLC0415 - lazy, so the module imports without it

        #  THE SHARED DUPLICATE-REJECTING LOADER.
        #  `yaml.safe_load` applies last-one-wins to a repeated key, silently. A
        #  scenario definition carries the destructive answers, the fan-out switch
        #  that decides which tables a run touches and the comparison bound, so a
        #  shadowed key means two consumers read two different files. Imported
        #  lazily, and by sibling name, so this module still imports on a host
        #  without PyYAML.
        parser_module = _load_scenario_yaml_module()
    except ImportError as exc:
        raise ScenarioFileError(
            f"the shared scenario parser could not be loaded, so a scenario "
            f"definition cannot be read: {exc}. The two possible causes have "
            f"different remedies, which is why this message names the one that "
            f"applied: harness/normalize.py is the shared "
            f"duplicate-rejecting loader, and requirements.txt pins "
            f"PyYAML==6.0.3. Pass --tables instead to name the tables directly."
        ) from exc

    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScenarioFileError(
            f"could not read the scenario definition {source}: {exc}. The "
            f"canonical invocation passes a scenario definition path; see "
            f"harness/docker-compose.yml."
        ) from exc

    try:
        document = parser_module.load_scenario_yaml(text)
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

    SELECTION AND PROVENANCE ARE TWO DIFFERENT USES OF `--scenario-file`, and
    conflating them broke the protocol outright. `--scenario-file` originally had one
    job: read the declared `affected_tables` and dump those. When the comparison bound
    became all 22 in-scope tables, stages 3 and 7 switched to `--all-in-scope` - and
    because the two options were refused together as "alternative ways of choosing the
    same list", the dumps stopped naming the scenario definition at all. That emptied
    `scenario_file_sha256`, which `harness/diff_states.py`'s `PROVENANCE_MUST_MATCH`
    requires to be present and equal on both sides, so stage 10 refused every run with
    "the provenance field 'scenario_file_sha256' is empty on both sides". The
    authoritative driver could not complete a single scenario.

    So `--scenario-file` now SELECTS only when no other selector is given, and is
    otherwise recorded as provenance beside the capture. `--all-in-scope` and
    `--tables` remain mutually exclusive, because those two really are alternative
    ways of choosing one list.

    Args:
        tables: A comma-separated list of table names.
        scenario_file: A scenario definition. Selects its declared `affected_tables`
            when it is the only selector; otherwise provenance only.
        all_in_scope: Dump all 22 explicitly.

    Returns:
        The table names, in the order to dump them.

    Raises:
        ValueError: Both real selectors were given, or `tables` is empty or names a
            table twice.
        ScenarioFileError: The scenario definition is unusable.
        TableNotInScopeError: A named table is out of scope.
        UnknownTableError: A named table is not a table of the schema.
    """
    chosen = [
        name
        for name, given in (
            ("--tables", tables is not None),
            ("--all-in-scope", bool(all_in_scope)),
        )
        if given
    ]
    if len(chosen) > 1:
        raise ValueError(
            f"{' and '.join(chosen)} were both given; they are alternative "
            f"ways of choosing the same list, so use exactly one."
        )

    if scenario_file is not None and not chosen:
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

    return IN_SCOPE_TABLES


_EPILOGUE: Final[str] = """\
modes
  --table-digest [--] TABLE [TABLE ...]
  --table-digest --scenario-file <scenario>.yaml
      THE CANONICAL STATE FINGERPRINT, not a dump: one
      `<TABLE><TAB><row count><TAB><sha256>' line per table on stdout,
      taken over this module's own canonical dump text so both sides of
      the comparison digest with one implementation. Its exit statuses
      are 0, 1 (a table could not be read; the record is still complete),
      2 (usage) and 3 (environment) - deliberately NOT the 8x band below,
      because both runners already map those three codes. Writes no file
      and needs no --out.

layouts
  --scenario NAME --side {cobol|python} [--out-dir DIR]
      writes <DIR>/<NAME>/<side>/<TABLE>.json   (DIR defaults to $ACAS_OUT)
  --out DIR
      writes <DIR>/<TABLE>.json                 the form the canonical
      recipe in harness/docker-compose.yml uses

table selection is REQUIRED
  exactly one of --all-in-scope, --scenario-file or --tables. An
  unbounded run is refused because evidence whose scope is implicit is
  not evidence (rule R-6). --all-in-scope, all 22 tables, is THE
  PROTOCOL: `overrewrite.` [general/general.cbl:L656-L672] rewrites
  SYSTEM-REC under key 1, SYSDEFLT-REC under key 2 and SYSTOT-REC under
  key 4, and acas_posting/cli/args.py::overrewrite reproduces it, so a
  capture that omitted those rows could report an empty diff while the
  run date, the allocators, the flags, the defaults or the period totals
  differed. --scenario-file narrows to a scenario's declared effect and
  is for debugging.

what is written
  <TABLE>.json  one per selected table
  _manifest.json  the completeness manifest, written LAST. The whole set
  is staged beside the destination and published together, so the
  destination carries either this run's complete set with its manifest or
  no manifest at all - never a mixture of two runs. Downstream stages
  require the manifest.

environment
  ACAS_DB_HOST  ACAS_DB_PORT  ACAS_DB_NAME  ACAS_DB_USER  ACAS_DB_PASSWORD
  must be set and non-empty; ACAS_DB_SOCKET may be empty, meaning TCP.
  ACAS_OUT supplies the default for --out-dir. ACAS_REPO, when set, is the
  read-only checkout: the dump tree may neither lie inside it nor contain
  it. Credentials are never logged and never reach a dump file. The COBOL
  side cannot carry a database name, user or password longer than 12
  characters, nor a host longer than 32 [copybooks/wsfnctn.cob:L56-L62].

deadlines - every network operation is bounded, none may be 0
  ACAS_DB_CONNECT_TIMEOUT  seconds for the handshake      (default 10)
  ACAS_DB_READ_TIMEOUT     seconds one read may block     (default 300)
  ACAS_DB_WRITE_TIMEOUT    seconds one write may block    (default 60)

exit codes
  0 dumped   80 usage   81 precondition   82 database
  83 scope    84 schema drift             85 numeric   86 write
  87 timeout - a deadline expired; the server never answered

this tool issues SELECT only, on one connection, sequentially, and writes
no byte of non-reproducible content: two runs against the same state
produce byte-identical files, manifest included.
"""


# ======================================================================================
#  THE CANONICAL STATE FINGERPRINT  -  `--table-digest'
#
#  WHY IT IS HERE. Both run stages of the parity protocol record what state they were
#  handed and what state they left, and they once recorded a ROW COUNT. A row count
#  cannot tell two different starting states apart: swap one balance, alter one status
#  byte, load a different fixture of the same shape, and the counts agree while the
#  states do not - and then every downstream difference, or its ABSENCE, belongs to the
#  seed rather than to either cycle. That is the most expensive failure a parity harness
#  has, because an empty diff over two differently-seeded databases looks exactly like
#  parity. So each side records, per bounded table:
#
#      <TABLE><TAB><row count><TAB><sha256 of the canonical dump>
#
#  and a table that cannot be read at all carries a single HYPHEN in both value fields -
#  a hyphen and never a zero, because "this table could not be read" is a different fact
#  from "this table is empty" and the far side must be able to tell them apart.
#
#  THE DIGEST IS TAKEN OVER THIS MODULE'S OWN CANONICAL TEXT, through `serialise_dump`,
#  and that is the whole design: it covers every bounded table and every row, at each
#  column's declared scale, in primary-key order - the same bytes the dump stage writes
#  and the normalise stage compares; it inherits for free every invariant the dump path
#  already enforces, the single-column primary-key ordering, the structural assertion
#  against `information_schema`, the rule R-2 float refusal and the null refusal; and
#  BOTH SIDES COMPUTE IT WITH THIS ONE PROGRAM, because two digests are comparable only
#  if one implementation produced them. A digest taken by the mysql client on one side
#  and by the driver on the other would differ on formatting alone and would report a
#  starting-state disagreement on every single run.
#
#  WHY IT IS A MODE OF THIS FILE RATHER THAN A FILE OF ITS OWN. It was
#  `harness/table_digest.py`, which is not one of the harness paths the Agent Action Plan
#  section 0.3.1 inventory names - and it existed only to call THIS
#  module's `serialise_dump`, `scenario_tables`, `IN_SCOPE`, `connection_settings`,
#  `connect` and `dump_table`. To reach them it loaded this file BY PATH through
#  `importlib`, registering it in `sys.modules` under a second name, so a fingerprint and
#  the dump it digests ran against two separately-executed copies of the same code. As a
#  mode there is one copy, one set of constants and no loader.
#
#  WHAT IT IS NOT. It is not a stage of the protocol and it writes nothing into a
#  compared tree: the runners put its output under `run-logs/`, outside every tree the
#  comparison reads, so a fingerprint can never be diffed as though it were posted data
#  (rule R-6). It issues `SELECT` only and emits no DDL (rule R-3), and it reaches no
#  COBOL (rule R-1).
#
#  USAGE, and the flag is pre-scanned out of `argv` before the dump parser runs, so a
#  bare table list is a positional list exactly as it always was:
#
#      harness/dump_tables.py --table-digest -- TABLE [TABLE ...]
#      harness/dump_tables.py --table-digest --scenario-file harness/scenarios/x.yaml
#
#  EXIT STATUS - ITS OWN BAND, AND DELIBERATELY NOT THE 8x BAND THE DUMP MODE USES,
#  because both runners already map these three codes and a fingerprint failure is not a
#  dump failure:
#      0  every requested table was digested
#      1  at least one table could not be read; its line carries the hyphen markers and
#         the reason is on stderr. The record is still complete and still comparable, so
#         the caller decides what an unreadable table means to it
#      2  the command line was wrong - a table that is not one of the 22 in scope, or
#         neither a table list nor a scenario file
#      3  the environment or the server is unusable, so no record could be taken at all
# ======================================================================================

#: How this mode names itself in a diagnosis, so an operator reading merged stderr can
#: tell a fingerprint refusal from a dump refusal at a glance.
DIGEST_PROG: Final[str] = "harness/dump_tables.py --table-digest"

#: The flag that selects this mode. Pre-scanned out of `argv` by `main` before the dump
#: parser runs, because the dump parser declares no positional and a bare table list is
#: how both runners have always passed one.
DIGEST_MODE_FLAG: Final[str] = "--table-digest"

#: The three fingerprint statuses that are not "everything worked". Small integers on
#: purpose: both runners test for exactly 1 and treat anything else as fatal.
DIGEST_EX_UNREADABLE: Final[int] = 1
DIGEST_EX_USAGE: Final[int] = 2
DIGEST_EX_ENVIRONMENT: Final[int] = 3

#: What a value field holds when the table could not be read. Both runners and
#: `tests/conftest.py` spell the unreadable case this way.
DIGEST_UNREADABLE: Final[str] = "-"


def _extract_mode(argv: Sequence[str], flag: str) -> tuple[bool, list[str]]:
    """Split one mode flag out of an argument vector, if it is there.

    Pre-scanned rather than declared on the dump parser for one concrete reason: the
    dump parser has NO positional argument, so `--table-digest -- GLBATCH-REC` would
    fail its parse with "unrecognized arguments" before any dispatch could happen. Both
    runners pass their bounded table list positionally, and that call shape is part of
    the fingerprint contract - the ORDER of the tables is compared byte for byte - so it
    is the dispatch that adapts, not the callers. `--make-fixtures` takes a positional
    scenario path for the same reason and is handled the same way.

    Scanning STOPS at a bare `--`, because everything after it is a positional by
    definition: a table could not be spelt `--table-digest`, but reading one as a mode
    flag would be wrong in principle and this costs one comparison to get right.

    Args:
        argv: The argument vector, without the program name.
        flag: The mode flag to look for - `DIGEST_MODE_FLAG` or `FIXTURE_MODE_FLAG`.

    Returns:
        Whether the mode was requested, and the vector with the first occurrence of the
            flag removed.
    """
    remaining: list[str] = []
    requested = False
    for index, token in enumerate(argv):
        if token == "--":
            remaining.extend(argv[index:])
            break
        if token == flag and not requested:
            requested = True
            continue
        remaining.append(token)
    return requested, remaining


#: The parameter row the menu exit persists on every route. Every scenario declares it,
#: so a scenario-file table list already covers it; it is appended only on the fallback
#: path where one does not - see `_resolve_digest_tables`. It is dumped like any other table,
#: with its two credential cells withheld by this module's dump mode, and digested here
#: as well, because a digest compares even those two. Named here once, and spelled the
#: same way in
#: `harness/run_cobol_scenario.sh`, `harness/run_python_scenario.sh` and
#: `tests/conftest.py`.
PARAMETER_TABLE: Final[str] = "SYSTEM-REC"


def digest_of(dump: Mapping[str, Any]) -> str:
    """Return the SHA-256 of one table's canonical dump text.

    Args:
        dump: A dump object, as `dump_table` returns.

    Returns:
        The digest, 64 lower-case hexadecimal characters.

    Raises:
        ValueError: The dump object's shape is wrong - raised by `serialise_dump`,
            which is the one definition of that check.
    """
    return hashlib.sha256(serialise_dump(dump).encode("utf-8")).hexdigest()


def _resolve_digest_tables(
    named: Sequence[str], scenario_file: str | None
) -> tuple[str, ...]:
    """Resolve the table list, from an explicit list or a scenario file - never both.

    Args:
        named: Table names given on the command line.
        scenario_file: A scenario definition whose `affected_tables` bounds the record.

    Returns:
        The tables, in the order the caller asked for them - which for a scenario file
        is the scenario's own DECLARED order, with `SYSTEM-REC` appended only when that
        order omits it, because the order is part of the fingerprint contract: the two
        sides compare these records byte for byte. An explicit list is taken exactly as
        given, so a caller that wants only some of them can say so.

    Raises:
        SystemExit: With `DIGEST_EX_USAGE`, when neither or both were given, or when a name is
            not one of the 22 tables in scope.
    """
    if bool(named) == bool(scenario_file):
        raise SystemExit(
            _digest_fail(
                "give either a table list or --scenario-file, and exactly one of "
                "them. They are alternative ways of choosing the same list IN THIS "
                "MODE, because a fingerprint record has no provenance field to put a "
                "scenario file in. Note that the DUMP mode of this same module is "
                "DIFFERENT: it accepts --scenario-file alongside a selector and "
                "records it as provenance (scenario_file_sha256), refusing only "
                "--tables with --all-in-scope.",
                DIGEST_EX_USAGE,
            )
        )
    if named:
        tables = tuple(named)
    else:
        #  THE SCENARIO-FILE FORM APPENDS THE MENU-PERSISTED PARAMETER ROW, because
        #  that is the order both run stages record. `overrewrite' rewrites SYSTEM-REC
        #  key 1 on all four subsystems - [general/general.cbl:L656-L672],
        #  [sales/sales.cbl:L628-L641], [purchase/purchase.cbl:L621-L634],
        #  [irs/irs.cbl:L759-L774] - and the migrated command line reproduces that
        #  paragraph, so both cycles write the row on every route. No scenario DUMPS
        #  it: the row carries `RDBMS-PASSWD char(12)'
        #  [copybooks/wssystem.cob:L139] and a dump is `SELECT *', and counting it in
        #  a scenario's declared table effect would tie that claim to fields no
        #  scenario reasons about -- `Date-Form', another of its columns
        #  [copybooks/wssystem.cob:L127], among them. A digest carries no value, so
        #  the row can be bounded here and nowhere else. Appended rather than sorted
        #  in, so the scenario's declared order is left exactly as written and the two
        #  sides' records stay byte-comparable.
        declared = tuple(scenario_tables(scenario_file))
        tables = (
            declared
            if PARAMETER_TABLE in declared
            else (*declared, PARAMETER_TABLE)
        )
    for table in tables:
        if table not in IN_SCOPE:
            raise SystemExit(
                _digest_fail(
                    f"{table!r} is not one of the {len(IN_SCOPE)} "
                    f"in-scope tables this module declares. The inventory has "
                    f"exactly one definition in this repository.",
                    DIGEST_EX_USAGE,
                )
            )
    return tables


def _digest_fail(message: str, status: int) -> int:
    """Report `message` on stderr and return `status`, for a `SystemExit`.

    Args:
        message: The diagnosis.
        status: One of the three `DIGEST_EX_*` codes.

    Returns:
        `status`, so a caller can write `return _digest_fail(...)`.
    """
    sys.stderr.write(f"{DIGEST_PROG}: {message}\n")
    return status


def table_digest_main(argv: Sequence[str] | None = None) -> int:
    """Print one `<TABLE>\\t<count>\\t<digest>` line per requested table.

    RETURNS an exit code and never calls `sys.exit`, so a caller can drive it in
    process - the contract the three state tools beside it already carry.

    Args:
        argv: The argument vector, `sys.argv[1:]` when omitted.

    Returns:
        0, `DIGEST_EX_UNREADABLE`, `DIGEST_EX_USAGE` or `DIGEST_EX_ENVIRONMENT`, as the
            section comment above records.
    """
    parser = argparse.ArgumentParser(
        prog=DIGEST_PROG,
        description=(
            "One canonical state digest per table, for the pre-run and post-run "
            "fingerprints both run stages record."
        ),
    )
    parser.add_argument(
        "tables",
        nargs="*",
        metavar="TABLE",
        help="the tables to digest, in the order to record them",
    )
    parser.add_argument(
        "--scenario-file",
        default=None,
        help=(
            "a scenario definition whose affected_tables list bounds the record, "
            "read in the scenario's own declared order, with SYSTEM-REC - the parameter "
            "row the menu exit persists - appended if that list omits it"
        ),
    )
    try:
        namespace = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exit_request:
        # argparse's own usage failure is DIGEST_EX_USAGE by construction; returned rather
        # than allowed to escape, so this function keeps its no-`sys.exit` contract.
        return int(exit_request.code or DIGEST_EX_USAGE)

    try:
        tables = _resolve_digest_tables(
            namespace.tables, namespace.scenario_file
        )
    except SystemExit as exit_request:
        return int(exit_request.code or DIGEST_EX_USAGE)
    except ScenarioFileError as exc:
        return _digest_fail(str(exc), DIGEST_EX_USAGE)

    try:
        settings = connection_settings(os.environ)
    except ConnectionConfigError as exc:
        return _digest_fail(str(exc), DIGEST_EX_ENVIRONMENT)

    status = 0
    lines: list[str] = []
    try:
        with connect(settings) as connection:
            for table in tables:
                try:
                    dump = dump_table(connection, table)
                except DumpError as exc:
                    # A table that cannot be read is REPORTED, not fatal: the record
                    # stays complete and comparable, and the far side can tell an
                    # unreadable table from an empty one. The reason goes to stderr,
                    # never into the record.
                    lines.append(f"{table}\t{DIGEST_UNREADABLE}\t{DIGEST_UNREADABLE}")
                    sys.stderr.write(
                        f"{DIGEST_PROG}: {table} could not be digested: "
                        f"{type(exc).__name__}: {exc}\n"
                    )
                    status = DIGEST_EX_UNREADABLE
                    continue
                lines.append(
                    f"{table}\t{int(dump['row_count'])}\t"
                    f"{digest_of(dump)}"
                )
    except (
        ConnectionConfigError,
        InsecureTransportError,
        DriverUnavailableError,
        DumpTimeoutError,
        DumpError,
        OSError,
    ) as exc:
        return _digest_fail(f"{type(exc).__name__}: {exc}", DIGEST_EX_ENVIRONMENT)

    # One write, so a partial record cannot reach a caller that reads line by line.
    sys.stdout.write("".join(f"{line}\n" for line in lines))
    return status


# ======================================================================================
#  THE FIXTURE BUILDER  -  `--make-fixtures'
#
#  Materialise a scenario's declared flat seed files, non-interactively.
#
#  WHY IT EXISTS. Each scenario declares the flat files it seeds from and the checkout
#  ships none of them, so without this mode harness/seed.sh refuses with its fixture exit
#  code and the protocol cannot reach stage 1. The frozen loaders read those files.
#
#  WHY THE FILES CANNOT SIMPLY BE COMMITTED. Fifteen of the seventeen distinct seed files
#  are ORGANIZATION INDEXED or RELATIVE: an indexed file under GnuCOBOL is a Berkeley DB
#  database whose on-disk form depends on the library version the image was built with,
#  and a relative file is a fixed-length record image with an implementation-defined
#  layout. Committing either would commit an opaque, version-specific binary and tie the
#  repository to one build of one library. So the RECORDS are declared as reviewable text
#  in each scenario file and the FILES are built here.
#
#  HOW A FILE IS BUILT, AND WHY THIS WAY. Nothing about a record's layout is
#  reimplemented. For every file except `system.dat' the frozen loaders reach the flat
#  file through a numbered handler with `File-System-Used' set to zero
#  [common/glbatchLD.cbl:L295-L304], so the handler owns the SELECT, the FD, the key and
#  the write. This mode therefore generates a driver program that CALLS THAT SAME
#  HANDLER, and builds the driver's data division out of THE HANDLER'S OWN LINKAGE COPY
#  BLOCK, read from the frozen source at build time. The record name, its layout, every
#  picture clause and every `REPLACING' the handler applies are consequently identical by
#  construction rather than by transcription - there is no table of record names here to
#  fall out of date, and no packed-decimal layout is computed in Python. COBOL's own MOVE
#  performs every store, so the store semantics are the frozen ones (rule R-2: no value
#  is rendered to bytes by Python).
#
#  `system.dat' is the one exception, and the frozen code is the reason: every loader
#  reads it DIRECTLY through [copybooks/selsys.cob] - ORGANIZATION RELATIVE, relative key
#  `rrn' - and [copybooks/fdsys.cob], not through a handler [common/glbatchLD.cbl:L129],
#  [common/glbatchLD.cbl:L136]. Its writer therefore copies that select and that FD, and
#  still writes not one byte of layout of its own.
#
#  WHAT IS NEVER TAKEN FROM THE SCENARIO FILE. The system record carries the database
#  account the loaders authenticate with - `RDBMS-DB-Name', `RDBMS-User' and
#  `RDBMS-Passwd' at [copybooks/wssystem.cob:L137-L139], moved into `DB-Schema',
#  `DB-UName' and `DB-UPass' by every handler's RDB path (for example
#  [common/acas000.cbl:L558]). Those three are filled from the ENVIRONMENT, never from
#  the committed YAML, and a scenario that tries to declare them is refused. A credential
#  in a committed scenario file would be a credential in the repository.
#
#  WHY IT IS A MODE OF THIS FILE RATHER THAN A FILE OF ITS OWN. A twelfth harness file
#  would be outside the Agent Action Plan section 0.3.1 inventory, and this module is
#  already the harness's authority on what a record looks like and how a declared value
#  takes its external form - `table_spec`, `render_value`, `serialise_dump`,
#  `scenario_tables` and the in-scope inventory all live here. A fixture is the same
#  question in the other direction: the external form a declared value must take on the
#  way IN. This module also already owns the by-path route to the shared scenario loader,
#  so folding the builder in leaves one route to the parser rather than two.
#
#  WHAT THIS MODE DOES NOT DO. It does not touch the database, issues no SQL and needs no
#  server. It writes only inside the directory it is given, never into $ACAS_REPO. It does
#  not run the loaders - that is harness/seed.sh - and it does not decide whether a
#  scenario's data is *right*, only that every declared file was written and reads back
#  through the frozen FD.
#
#  USAGE
#      harness/dump_tables.py --make-fixtures <scenario>.yaml --out DIR
#      harness/dump_tables.py --make-fixtures <scenario>.yaml --list-fields ALL
#
#  EXIT STATUS - ITS OWN BAND, a third one, distinct from the dump band (8x) and the
#  fingerprint band (1-3), because harness/seed.sh maps these codes:
#      0   every declared file was built and read back
#      64  usage error
#      65  a precondition failed - missing cobc, unwritable output, absent copybook
#      66  the scenario file is missing, unreadable or malformed
#      67  a declared field does not exist in the record, or its value is unusable
#      68  cobc rejected a generated program
#      69  a generated program failed at run time, or the read-back did not agree
# ======================================================================================

#: How this mode names itself in a diagnosis and in its own `--help`.
FIXTURE_PROG: Final[str] = "harness/dump_tables.py --make-fixtures"

#: The flag that selects this mode, pre-scanned out of `argv` by `main` for the reason
#: `_extract_mode` records: the mode takes a positional the dump parser does not declare.
FIXTURE_MODE_FLAG: Final[str] = "--make-fixtures"

#: What a `SystemExit` carrying no code means when it escapes the fixture builder. It
#: cannot happen through `fixture_fail`, which always passes one, but `argparse` raises
#: `SystemExit(None)` for `--help`, and reporting that as 0 is correct.
FIXTURE_EX_OK_FALLBACK: Final[int] = 0

FIXTURE_EX_USAGE: Final[int] = 64
FIXTURE_EX_PRECONDITION: Final[int] = 65
FIXTURE_EX_SCENARIO: Final[int] = 66
FIXTURE_EX_DECLARATION: Final[int] = 67
FIXTURE_EX_COMPILE: Final[int] = 68
FIXTURE_EX_RUNTIME: Final[int] = 69

# Every file a scenario may declare, mapped to what the FROZEN code says about it.
#
#   handler   the numbered handler the loaders reach the file through, or None for the
#             one file they open themselves
#   defs      the File-Defs field the handler's SELECT assigns to, so the driver can
#             put the absolute path there. The names come from [copybooks/wsnames.cob]
#             and the per-file copybooks it includes, e.g. [copybooks/file07.cob]
#   loader    the load program [common/masterLD.sh] pairs the file with, recorded so a
#             reader of a generated program can find the frozen consumer
#
# The list is closed on purpose: a scenario naming a file that is not here is refused,
# because the twenty in-scope loaders are the only consumers the protocol has.
SEED_FILES: Final[dict[str, dict[str, str | None]]] = {
    "system.dat": {"handler": None, "defs": "file-0", "loader": "systemLD"},
    "ledger.dat": {"handler": "acas005", "defs": "file-5", "loader": "nominalLD"},
    "posting.dat": {"handler": "acas006", "defs": "file-6", "loader": "glpostingLD"},
    "batch.dat": {"handler": "acas007", "defs": "file-7", "loader": "glbatchLD"},
    "postings2irs.dat": {
        "handler": "acas008",
        "defs": "file-8",
        "loader": "slpostingLD",
    },
    "salesled.dat": {"handler": "acas012", "defs": "file-12", "loader": "salesLD"},
    "value.dat": {"handler": "acas013", "defs": "file-13", "loader": "valueLD"},
    "analysis.dat": {"handler": "acas015", "defs": "file-15", "loader": "analLD"},
    "invoice.dat": {"handler": "acas016", "defs": "file-16", "loader": "slinvoiceLD"},
    "openitm3.dat": {"handler": "acas019", "defs": "file-19", "loader": "otm3LD"},
    "purchled.dat": {"handler": "acas022", "defs": "file-22", "loader": "purchLD"},
    # THE ONE FILE WHOSE LAYOUT IS NOT READ FROM ITS HANDLER'S LINKAGE, and the reason
    # is a real divergence in the frozen tree rather than a convenience. acas026 copies
    # [copybooks/plwspinv.cob], whose 100-byte header is the record it lists in USING
    # [common/acas026.cbl:L227-L231] but whose LINE view is a SEPARATE 01 carrying an
    # OCCURS 40 table [copybooks/plwspinv.cob:L65-L66] that the USING clause does not
    # mention -- so through that copybook a line row cannot be named at all. The
    # posting program itself copies `plwspinv2.cob` directly [purchase/pl055.cbl:L135]
    # instead, where the SAME 100 bytes carry a header view
    # [copybooks/plwspinv2.cob:L21] and a line view [copybooks/plwspinv2.cob:L56] as
    # REDEFINES, and where the base record is already named WS-PInvoice-Record -- the
    # very name acas026 uses, so no REPLACING is needed and the two are compatible at
    # the linkage boundary by construction. pl055 distinguishes the two row kinds by
    # item number exactly as its Sales counterpart does, branching to header analysis
    # on zero [purchase/pl055.cbl:L310-L311]. The Agent Action Plan names both members
    # of this pair for the same reason (section 0.4.1.3).
    # THE VIEW THE FROZEN PROGRAM READS THROUGH IS THEREFORE THE VIEW THE DATA MUST
    # SATISFY, and the record-name check in read_layout is what proves the substitution
    # is storage-compatible rather than merely plausible.
    "pinvoice.dat": {
        "handler": "acas026",
        "defs": "file-26",
        "loader": "plinvoiceLD",
        "layout": "plwspinv2.cob",
    },
    "openitm5.dat": {"handler": "acas029", "defs": "file-29", "loader": "otm5LD"},
    "irsacnts.dat": {
        "handler": "acasirsub1",
        "defs": "file-34",
        "loader": "irsnominalLD",
    },
    # SINGLE-RECORD HANDLER. acasirsub3 opens, reads or writes ONE record and closes
    # on every call [common/acasirsub3.cbl:L259-L310], [common/acasirsub3.cbl:L312-L338],
    # treating open and close as no-ops [common/acasirsub3.cbl:L199-L208] because "IRS
    # only does a read or write and not a direct open or close"
    # [common/acasirsub3.cbl:L168-L178]. Two consequences the builder MUST honour: a
    # second declared record would silently replace the first, because each write
    # re-opens OUTPUT and truncates; and a read-back loop would never terminate,
    # because EOF is never reported.
    "irsdflt.dat": {
        "handler": "acasirsub3",
        "defs": "file-35",
        "loader": "irsdfltLD",
        "single_record": True,
    },
    "irspost.dat": {
        "handler": "acasirsub4",
        "defs": "file-36",
        "loader": "irspostingLD",
    },
    # SINGLE-RECORD HANDLER, for the same reason: acasirsub5 is the final-accounts
    # twin of acasirsub3 and the latter's own header names them together as the two
    # modules that behave this way [common/acasirsub3.cbl:L168-L172].
    "irsfinal.dat": {
        "handler": "acasirsub5",
        "defs": "file-37",
        "loader": "irsfinalLD",
        "single_record": True,
    },
}

# system.dat IS FOUR DIFFERENT RECORDS IN ONE RELATIVE FILE, and this is the single
# most surprising fact about the seed contract. [copybooks/selsys.cob] declares it
# ORGANIZATION RELATIVE with relative key `rrn', and the four system loaders each read
# a DIFFERENT relative record out of it, each through its own copybook:
#   rrn 1  systemLD [common/systemLD.cbl:L227]  wssystem.cob  System-Record    -> SYSTEM-REC
#   rrn 2  dfltLD   [common/dfltLD.cbl:L221]    wsdflt.cob    Default-Record   -> SYSDEFLT-REC
#   rrn 3  finalLD  [common/finalLD.cbl:L221]   wsfinal.cob   Final-Record     -> SYSFINAL-REC
#   rrn 4  sys4LD   [common/sys4LD.cbl:L226]    wssys4.cob    System-Record-4  -> SYSTOT-REC
# The frozen handler agrees: acas000 dispatches by moving File-Key-No straight into rrn
# [common/acas000.cbl:L461], [common/acas000.cbl:L473], [common/acas000.cbl:L481], and
# rejects a key outside 1 to 5 [common/acas000.cbl:L335].
# ALL FOUR ARE 1024 BYTES, each copybook saying so in its own header, which is why they
# can share one relative file at all.
# CONSEQUENCE, AND THE REASON THIS TOOL REFUSES A PARTIAL DECLARATION: masterLD runs all
# four loaders unconditionally [common/masterLD.sh:L50-L88], so a system.dat carrying
# only the parameter record would leave three of them reading a relative slot that was
# never written -- and the last of the four is tested against zero rather than 63
# [common/masterLD.sh:L83-L86], so that failure ABORTS the seed. A scenario therefore
# states all four, and states them explicitly even when three are all-zero, because an
# undefined pre-state is a difference waiting to happen.
SYSTEM_RELATIVE_RECORDS: Final[dict[str, tuple[str, str, str]]] = {
    "1": ("wssystem.cob", "System-Record", "SYSTEM-REC via systemLD"),
    "2": ("wsdflt.cob", "Default-Record", "SYSDEFLT-REC via dfltLD"),
    "3": ("wsfinal.cob", "Final-Record", "SYSFINAL-REC via finalLD"),
    "4": ("wssys4.cob", "System-Record-4", "SYSTOT-REC via sys4LD"),
}

# The six system-record connection fields filled from the environment and refused in a
# scenario. The widths are the actual declarations in wssystem.cob rather than the
# narrower x(12) RDB-Data fields used after the frozen handler copies them.
CONNECTION_FIELD_BINDINGS: Final[tuple[tuple[str, str, int, bool], ...]] = (
    ("RDBMS-DB-Name", "ACAS_DB_NAME", 12, True),
    ("RDBMS-User", "ACAS_DB_USER", 12, True),
    ("RDBMS-Passwd", "ACAS_DB_PASSWORD", 12, True),
    ("RDBMS-Host", "ACAS_DB_HOST", 32, True),
    ("RDBMS-Port", "ACAS_DB_PORT", 5, True),
    # An empty socket is the frozen TCP-only declaration and is therefore valid.
    ("RDBMS-Socket", "ACAS_DB_SOCKET", 64, False),
)
CREDENTIAL_FIELDS: Final[tuple[str, ...]] = tuple(
    field for field, _environment, _width, _required in CONNECTION_FIELD_BINDINGS
)

# A COBOL data name, as this tool is willing to emit it. Deliberately narrow in its
# CHARACTER SET -- the name is interpolated into generated source, so anything that
# could carry a statement separator, a quote or a period is refused rather than escaped
# -- but not in its length: the frozen copybooks contain names longer than the 30
# characters COBOL-85 allowed, `System-Record-Version-Secondary' at
# [copybooks/wssystem.cob:L54] being 31, and a limit that refused a name the frozen
# code declares would be this tool disagreeing with the specification.
NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z][A-Za-z0-9-]{0,62}$")

# A value this tool will emit as a NUMERIC literal. Everything else becomes an
# alphanumeric literal, and the choice is checked against the field's own picture so a
# mismatch is a refusal rather than a silently wrong store.
NUMERIC_RE: Final[re.Pattern[str]] = re.compile(r"^[+-]?[0-9]+(\.[0-9]+)?$")


def fixture_fail(code: int, headline: str, *detail: str) -> "NoReturn":  # type: ignore[name-defined]
    """Report and stop. One shape for every refusal, as the shell scripts have."""
    sys.stderr.write(f"{FIXTURE_PROG}: {headline}\n")
    for line in detail:
        sys.stderr.write(f"    {line}\n")
    raise SystemExit(code)


# =============================================================================
# READING THE FROZEN SOURCES.  Read-only, every one of them, and never modified.
# =============================================================================
def handler_linkage_copies(repo: Path, handler: str) -> list[str]:
    """The copy statements a handler's LINKAGE SECTION contains, in order.

    This is what makes the generated driver agree with the handler about the record:
    the same five copy statements, with the same REPLACING clauses, produce the same
    names and the same layout. Comments are dropped and continuation lines are joined,
    because a copy statement in this codebase routinely spans several lines.
    """
    source = repo / "common" / f"{handler}.cbl"
    if not source.is_file():
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"the frozen handler {source} is not in the checkout.",
            "It supplies the record layout the generated writer uses, so nothing can",
            "be built without it.",
        )
    text = source.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    start = lowered.find("linkage section")
    if start < 0:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"{source} has no LINKAGE SECTION, so its record layout cannot be read.",
        )
    end = lowered.find("procedure division", start)
    if end < 0:
        end = len(text)

    statements: list[str] = []
    buffer: str | None = None
    for raw in text[start:end].splitlines():
        line = raw.strip()
        if not line or line.startswith("*>"):
            continue
        if buffer is None:
            if not line.lower().startswith("copy "):
                continue
            buffer = line
        else:
            buffer = f"{buffer} {line}"
        if buffer.rstrip().endswith("."):
            # A trailing inline comment is legal after the period and is dropped.
            statements.append(re.sub(r"\s+", " ", buffer).strip())
            buffer = None
    if not statements:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"{source} declares no copybook in its LINKAGE SECTION.",
        )
    return statements


def copybook_of(statement: str) -> str:
    """The copybook a copy statement names."""
    match = re.match(r'copy\s+"([^"]+)"', statement, re.IGNORECASE)
    if match is None:
        fixture_fail(FIXTURE_EX_PRECONDITION, f"could not read a copybook name from: {statement}")
    return match.group(1)


def replacements_of(statement: str) -> dict[str, str]:
    """The REPLACING pairs a copy statement applies, lowercased on the left.

    Needed because a declared field name has to be matched against the record as the
    HANDLER sees it: acas013 renames `VA-Code' to `WS-VA-Code'
    [common/acas013.cbl], and a scenario declaring either spelling must resolve.
    """
    match = re.search(r"\breplacing\b(.*)$", statement, re.IGNORECASE | re.DOTALL)
    if match is None:
        return {}
    body = match.group(1).rstrip(". ")
    tokens = [t for t in re.split(r"\s+", body.strip()) if t]
    pairs: dict[str, str] = {}
    index = 0
    while index + 2 < len(tokens) + 1:
        if index + 2 >= len(tokens) + 1:
            break
        if index + 2 > len(tokens):
            break
        left, by, right = tokens[index], tokens[index + 1], tokens[index + 2]
        if by.lower() != "by":
            break
        pairs[left.lower()] = right
        index += 3
    return pairs


class Layout:
    """The elementary fields of one record copybook, and what each will accept.

    Only what a MOVE needs is read: the name, whether the picture is numeric or
    alphanumeric, and whether the item is a group, a REDEFINES or an OCCURS. Nothing
    here computes an offset or a byte width - COBOL does the storing.
    """

    def __init__(self) -> None:
        self.numeric: dict[str, str] = {}
        self.alphanumeric: dict[str, str] = {}
        self.groups: set[str] = set()
        self.excluded: dict[str, str] = {}
        # Character width of every elementary field held in DISPLAY, which is the only
        # kind a `raw' declaration can address. A COMP-3 or binary field has no
        # character view to write bytes into, so it is deliberately absent here.
        self.display_width: dict[str, int] = {}
        # The 01-level group each field actually descends from, which is NOT always the
        # record the handler is called with. Several in-scope copybooks describe one
        # buffer through more than one 01-level view: the invoice record is declared
        # once and then REDEFINED twice, as a header at
        # [copybooks/slwsinv2.cob:L38] and as a line at [copybooks/slwsinv2.cob:L92],
        # so `ih-net' and `il-net' are subordinate to those views and NOT to the base
        # record. Qualifying them with the base record does not compile, which is how
        # this was found. The views share storage, so a MOVE through the right
        # qualifier lands in the same bytes the handler is handed.
        self.root: dict[str, str] = {}
        # Fields that live inside an OCCURS and therefore REQUIRE a subscript, mapped
        # to (table name, bound). Some in-scope records are nothing but a table: the
        # IRS defaults record is a single `Def-Group occurs 33'
        # [copybooks/irswsdflt.cob:L8-L12] and the posting section indexes entries 31
        # and 32 of it by name [irs/irs030.cbl:L871], so a tool that could not address
        # a table entry could not seed the IRS scenario at all.
        self.subscripted: dict[str, tuple[str, int]] = {}

    def qualifier(self, name: str, fallback: str) -> str:
        """The 01-level group a MOVE to this field must be qualified with."""
        return self.root.get(name.lower(), fallback)

    def raw_target(self, name: str) -> tuple[str, int]:
        """Return (declared name, character width) for a field a `raw' value may set.

        Refuses anything a byte-exact store would be meaningless on, so the escape
        hatch cannot quietly do the wrong thing.
        """
        kind, declared = self.classify(name)
        width = self.display_width.get(name.lower())
        if width is None:
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"{declared} is not held in DISPLAY, so a raw value cannot be stored "
                "in it.",
                "A COMP-3 or binary field has no character view; declare the value as "
                "ordinary text and let COBOL's own MOVE perform the store.",
            )
        if kind == "alphanumeric":
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"{declared} is already an alphanumeric field, so raw adds nothing.",
                "Declare the value as ordinary text.",
            )
        return declared, width

    def classify(self, name: str) -> tuple[str, str]:
        """Return ("numeric"|"alphanumeric", the name as declared)."""
        key = name.lower()
        if key in self.numeric:
            return "numeric", self.numeric[key]
        if key in self.alphanumeric:
            return "alphanumeric", self.alphanumeric[key]
        if key in self.excluded:
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"the field {name} cannot be set by this tool: {self.excluded[key]}",
                "Declare an elementary field that is neither a REDEFINES nor a table.",
            )
        if key in self.groups:
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"{name} is a group item, and a group cannot be given a value here.",
                "Declare its elementary members instead.",
            )
        fixture_fail(
            FIXTURE_EX_DECLARATION,
            f"the record has no field named {name}.",
            "Field names are spelled exactly as the frozen copybook spells them.",
        )


# The usages that make an item numeric even with no PICTURE of its own. All of them
# occur in the in-scope record copybooks: `Run-Date binary-long'
# [copybooks/wssystem.cob:L67] and the seven `binary-long' statistics fields
# [copybooks/wssl.cob:L46-L52] are the ones a scenario is most likely to declare.
_NUMERIC_USAGE: Final[re.Pattern[str]] = re.compile(
    r"\b(binary-char|binary-short|binary-long|binary-double|binary"
    r"|comp-1|comp-2|comp-3|comp-4|comp-5|comp|computational[0-9-]*"
    r"|packed-decimal|index)\b"
)


def _display_width(picture: str) -> int:
    """Character width of a DISPLAY picture, or zero if it cannot be read.

    Only the symbols the in-scope copybooks actually use are counted. `V' and `P' are
    implied positions that occupy no byte, and an `S' occupies none either, because
    none of these copybooks writes SIGN IS SEPARATE -- the sign rides in the final
    digit, which is exactly why a signed DISPLAY field is the same width as its
    unsigned twin.
    """
    expanded = re.sub(
        r"([9xaz])\((\d+)\)",
        lambda m: m.group(1) * int(m.group(2)),
        picture.lower(),
    )
    if re.search(r"[^9xazsvp]", expanded):
        return 0
    return sum(1 for character in expanded if character in "9xaz")


def _replace_tokens(text: str, replacements: dict[str, str]) -> str:
    """Apply COPY REPLACING to a whole declaration, token by whole token.

    Whole-token only, which matters here: `Invoice-Nos' is a replacement operand and
    `WS-Invoice-Nos' contains it, so a substring rewrite would corrupt names the
    compiler leaves alone.
    """
    if not replacements:
        return text

    def swap(match: re.Match[str]) -> str:
        return replacements.get(match.group(0).lower(), match.group(0))

    return re.sub(r"[A-Za-z][A-Za-z0-9-]*", swap, text)


def _copybook_declarations(
    repo: Path, copybooks: list[str], replacements: dict[str, str]
) -> list[tuple[int, str, str]]:
    """Every data declaration of one or more copybooks, in source order.

    Returns (level, name-as-the-handler-sees-it, the rest of the declaration). A
    copybook may itself COPY another -- `fdsys.cob' copies `wssystem.cob' -- and the
    include is expanded IN PLACE, because level numbers only mean anything in order.
    """
    declarations: list[tuple[int, str, str]] = []
    seen: set[str] = set()

    def expand(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        path = repo / "copybooks" / name
        if not path.is_file():
            fixture_fail(FIXTURE_EX_PRECONDITION, f"the frozen copybook {path} is not in the checkout.")
        # A declaration may span lines; join to the terminating period first, so a
        # picture or usage clause on a continuation line is still seen.
        joined: list[str] = []
        buffer = ""
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("*>"):
                continue
            # Strip a trailing inline comment; it can carry stray punctuation.
            line = re.sub(r"\*>.*$", "", line).strip()
            if not line:
                continue
            buffer = f"{buffer} {line}".strip() if buffer else line
            if buffer.endswith("."):
                joined.append(buffer)
                buffer = ""
        if buffer:
            joined.append(buffer)
        for statement in joined:
            nested = re.match(r'copy\s+"([^"]+)"', statement, re.IGNORECASE)
            if nested is not None:
                expand(nested.group(1))
                continue
            match = re.match(
                r"^(\d\d)\s+([A-Za-z][A-Za-z0-9-]*)\b(.*)$", statement
            )
            if match is None:
                continue
            level_text, field, rest = match.groups()
            level = int(level_text)
            # An 88 is a condition name, not a field, and a 66 renames one.
            if level in (66, 88):
                continue
            # COPY REPLACING SUBSTITUTES THE TOKEN EVERYWHERE, not only where a name is
            # declared -- so it also rewrites the operand of a REDEFINES. Applying it to
            # the declared name alone was a real bug: acas016 renames `Invoice-Record'
            # [common/acas016.cbl:L220-L223], which makes
            # [copybooks/slwsinv2.cob:L38] read `Invoice-Header redefines
            # WS-Invoice-Record' in the compiler's eyes, and a reader that left the
            # operand un-renamed concluded the header view was a DETACHED buffer and
            # refused every `ih-' field. The rest of the declaration is rewritten here
            # for the same reason the compiler rewrites it.
            declarations.append(
                (
                    level,
                    replacements.get(field.lower(), field),
                    _replace_tokens(rest, replacements),
                )
            )

    for entry in copybooks:
        expand(entry)
    return declarations


def read_layout(
    repo: Path,
    copybooks: list[str],
    replacements: dict[str, str],
    *,
    record: str | None = None,
) -> Layout:
    """Classify every field of a record: elementary numeric, elementary text, or not
    settable.

    GROUP OR ELEMENTARY IS DECIDED BY THE LEVEL NUMBERS, not by whether a PICTURE is
    present. Both readings are needed and only one is right: `03 Amounts comp-3.'
    [copybooks/wsbatch.cob] is a GROUP that carries a usage clause and no picture,
    while `05 Run-Date binary-long.' [copybooks/wssystem.cob:L67] is ELEMENTARY with
    no picture either. An item is a group exactly when the declaration that follows it
    has a HIGHER level number.
    """
    layout = Layout()
    declarations = _copybook_declarations(repo, copybooks, replacements)
    root = ""
    # 01-level groups that describe the SAME BYTES the handler is handed: the record
    # itself, plus anything that REDEFINES it directly or transitively. Anything else
    # at 01 level is a SEPARATE BUFFER, and a MOVE into it would be silently discarded
    # -- see the class comment on Layout.root, and note the case that forced this:
    # [copybooks/plwspinv.cob:L65] declares `Pinvoice-Bodies' as an independent 01 that
    # acas026 carries in LINKAGE but does NOT list in its USING clause
    # [common/acas026.cbl:L227-L231], so its `il-' fields reach no file at all.
    attached: set[str] = set()
    detached: set[str] = set()
    # (level, the innermost OCCURS in effect for anything subordinate, as
    # (table name, bound), or None when there is none)
    stack: list[tuple[int, tuple[str, int] | None]] = []
    for index, (level, field, rest) in enumerate(declarations):
        key = field.lower()
        body = rest.lower()
        while stack and stack[-1][0] >= level:
            stack.pop()
        under_occurs = stack[-1][1] if stack else None
        if level == 1:
            root = field
            target = re.search(r"\bredefines\s+([A-Za-z][A-Za-z0-9-]*)", body)
            if not attached and target is None:
                # The first 01 of a record copybook IS the record.
                attached.add(key)
            elif target is not None and target.group(1).lower() in attached:
                attached.add(key)
            else:
                detached.add(key)
        elif root:
            layout.root[key] = root
        is_group = (
            index + 1 < len(declarations) and declarations[index + 1][0] > level
        )
        occurs = re.search(r"\boccurs\s+(\d+)", body)
        if is_group:
            layout.groups.add(key)
            own = (field, int(occurs.group(1))) if occurs is not None else None
            stack.append((level, own or under_occurs))
            continue
        if root.lower() in detached:
            layout.excluded[key] = (
                f"it belongs to {root}, which is a SEPARATE 01-level buffer and not "
                "the record the handler writes, so a value here would be discarded"
            )
            continue
        if "redefines" in body:
            layout.excluded[key] = "it REDEFINES another field"
            continue
        if occurs is not None:
            layout.excluded[key] = (
                "it is itself a table (OCCURS), so declare the elementary members of "
                "its entries rather than the table"
            )
            continue
        if under_occurs is not None:
            # Settable, but ONLY through the subscripted form. Recorded rather than
            # excluded, because refusing it would make the IRS defaults unseedable.
            layout.subscripted[key] = under_occurs
        if field.lower() == "filler":
            continue
        picture = re.search(r"\bpic(?:ture)?\s+(?:is\s+)?([^\s.]+)", body)
        if picture is not None:
            text = picture.group(1)
            if re.search(r"[9szvp]", text):
                layout.numeric[key] = field
            else:
                layout.alphanumeric[key] = field
            if not _NUMERIC_USAGE.search(body):
                width = _display_width(text)
                if width:
                    layout.display_width[key] = width
            continue
        if _NUMERIC_USAGE.search(body):
            layout.numeric[key] = field
            continue
        layout.excluded[key] = (
            "it declares neither a picture nor a numeric usage, so this tool cannot "
            "tell what a value for it would mean"
        )
    # Turn the "first 01 is the record" reading into a CHECK rather than a belief. If a
    # copybook ever ordered its views differently, the attached/detached split above
    # would be inverted and values would be silently discarded, which is the one
    # failure mode this tool must never have.
    if record is not None and record.lower() not in attached:
        fixture_fail(
            FIXTURE_EX_DECLARATION,
            f"{record} is the record {copybooks[0]} is used as, but it is not the "
            "first 01-level group of that copybook nor a REDEFINES of it.",
            "This tool decides which 01-level views share the handler's bytes from",
            "that relationship, so it refuses rather than guess.",
        )
    return layout


# =============================================================================
# GENERATING A WRITER
# =============================================================================
def refuse_unplaceable_text(text: str, *, what: str, code: int) -> None:
    """Refuse text that cannot be placed inside a generated COBOL literal.

    ONE RULE, STATED ONCE. Everything this tool interpolates into generated source
    -- a declared VALUE, a declared raw byte image, an output path -- is going into
    source that is then COMPILED AND RUN, so all of it has to survive the same two
    hazards, and until now each site spelled the rule for itself:

      * a double quote CLOSES the literal, and whatever follows it becomes generated
        COBOL rather than data. That is arbitrary statements from an input;
      * any control character ends or corrupts the line. A newline is the obvious one
        and was the only one three of the four sites checked, but a carriage return
        does it too, and NUL and DEL make the emitted source undiagnosable.

    Neither is escaped. There is no escaping that makes arbitrary text safe inside a
    fixed-format-descended literal, and an escape that half-works is worse than a
    refusal because it fails silently at compile time instead of loudly here.

    Args:
        text: The text about to be interpolated.
        what: What it is, for the diagnosis.
        code: The exit status to fail with -- declaration inputs and command-line
            inputs are different faults and get different statuses.
    """
    if '"' in text:
        fixture_fail(
            code,
            f"{what} contains a double quote: {text!r}.",
            "It is interpolated into a COBOL alphanumeric literal in source this tool",
            "compiles and runs, so a quote would close the literal and leave the",
            "remainder as generated COBOL. It is refused rather than escaped.",
        )
    for index, character in enumerate(text):
        if ord(character) < 0x20 or ord(character) == 0x7F:
            fixture_fail(
                code,
                f"{what} contains a control character (0x{ord(character):02X}) at "
                f"offset {index}: {text!r}.",
                "It is interpolated into generated COBOL source, where a line break",
                "ends the line and starts another one, and where a NUL or a DEL makes",
                "the emitted source undiagnosable. Refused rather than escaped.",
            )


def cobol_literal(kind: str, value: str, field: str) -> str:
    """A COBOL literal for a declared text value, checked against the field's kind."""
    if kind == "numeric":
        if not NUMERIC_RE.match(value):
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"{field} is a numeric field and {value!r} is not a number.",
                "Declare digits, with an optional sign and an optional decimal point.",
            )
        # Emitted verbatim: COBOL aligns it on the receiving field's implied decimal
        # point and truncates toward zero, which is the frozen store semantics.
        return value
    refuse_unplaceable_text(
        value, what=f"the value for {field}", code=FIXTURE_EX_DECLARATION
    )
    return f'"{value}"'


#: The longest path this tool will interpolate into a generated COBOL literal.
#: A COBOL alphanumeric literal has a maximum length and a source line has a fixed
#: area; a path long enough to need continuation would produce source that either
#: does not compile or -- worse -- compiles with the tail silently dropped, so it is
#: refused. The frozen file-name field it is moved into is itself bounded:
#: `wsnames.cob' declares each as `pic x(n)', so a path past that is not usable by
#: the loaders either.
COBOL_PATH_LITERAL_MAX: Final[int] = 160


def cobol_path_literal(path: str, *, what: str) -> str:
    """Return `path` as a COBOL alphanumeric literal, or refuse it.

    EVERY PATH THIS TOOL PUTS INTO GENERATED COBOL COMES THROUGH HERE. The output
    directory arrives on the command line, each seed file's path is derived from it,
    and the result is interpolated into four `move "<path>" to <field>.' statements
    and two comment lines of source that is then COMPILED AND RUN. Declared VALUES
    were already held to this standard; the paths were the gap, and they are the input
    an operator supplies directly.
    The quote-and-control-character rule itself lives in `refuse_unplaceable_text' so
    that this function and the two declared-value paths cannot drift apart -- they
    previously spelled it three different ways, and only this one covered a carriage
    return, a NUL or a DEL. What this function adds on top of the shared rule is the
    LENGTH budget, which applies to a path (it is derived, and can be arbitrarily
    long) but not to a declared raw value (it must equal its field's width exactly).
    A comment line is checked by the same rule: `*>' cannot execute anything, but a
    newline inside one still ends the comment and hands the remainder to the compiler.

    Args:
        path: The path to interpolate.
        what: What it is, for the diagnosis - e.g. `the --out directory`.

    Returns:
        The path unchanged, once it has been shown to be placeable. It is returned
        WITHOUT quotes because the two call sites need different framing -- a `move'
        statement supplies its own pair, a `*>' comment wants none -- and because a
        caller that forgets the quotes generates COBOL that fails to compile, which
        is a loud failure rather than a silent one.
    """
    if not path:
        fixture_fail(FIXTURE_EX_PRECONDITION, f"{what} is empty, and it has to name a file.")
    # The shared rule -- the same one every declared VALUE and raw byte image is held
    # to -- under the command-line status, because a path is what the operator typed.
    refuse_unplaceable_text(path, what=what, code=FIXTURE_EX_PRECONDITION)
    if len(path) > COBOL_PATH_LITERAL_MAX:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"{what} is {len(path)} characters, past the "
            f"{COBOL_PATH_LITERAL_MAX} this tool will place in a COBOL literal.",
            "A longer literal would need continuation, and source that needs it",
            "either fails to compile or compiles with the tail dropped. Choose a",
            "shorter --out directory.",
        )
    return path


def moves_for(
    layout: Layout, record: str, fields: dict[str, str], *, where: str
) -> list[str]:
    """The MOVE statements one declared record needs, in declaration order."""
    lines: list[str] = []
    for name, value in fields.items():
        if not isinstance(name, str) or not NAME_RE.match(name):
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"{name!r} in {where} is not a plain COBOL data name.",
                "It is interpolated into generated source, so it is refused.",
            )
        if isinstance(value, list):
            lines.extend(
                table_moves_for(layout, record, name, value, where=where)
            )
            continue
        if name.lower() in layout.subscripted:
            table, bound = layout.subscripted[name.lower()]
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"{name} in {where} is inside the table {table} (OCCURS {bound}), so "
                "it needs a subscript and a bare value cannot say which entry.",
                "Declare a list of entries instead, each an `at' and a `value':",
                f"  {name}:",
                '    - at: "31"',
                '      value: "..."',
            )
        if isinstance(value, dict):
            lines.append(raw_move_for(layout, record, name, value, where=where))
            continue
        if not isinstance(value, str):
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"the value for {name} in {where} must be a quoted string.",
                "Every value is declared as text so that YAML cannot parse a money",
                "figure into a binary float (R-2). Quote it.",
            )
        kind, declared = layout.classify(name)
        literal = cobol_literal(kind, value, declared)
        owner = layout.qualifier(name, record)
        lines.append(f"     move     {literal} to {declared} in {owner}")
    return lines


def connection_accepts_for(
    layout: Layout, record: str, bindings: dict[str, str]
) -> list[str]:
    """The six connection fields, accepted from the environment at RUN time.

    WHY `ACCEPT ... FROM ENVIRONMENT` AND NOT `MOVE "..."`. The
    values reach the same fields with the same bytes either way, but a `MOVE` puts
    them in the GENERATED SOURCE, where a kept build directory or an echoed compiler
    diagnostic publishes the database account. `ACCEPT` names the variable and reads
    it when the writer runs, so the source is credential-free and can be kept,
    listed or attached to a bug report without redaction.

    The statement form is the literal-name one - `accept <item> from environment
    "NAME"` - which GnuCOBOL 3.2 accepts directly. Every field is preceded by
    `initialize <record>`, so a variable that is absent or empty leaves the field at
    spaces, which is exactly what an empty `RDBMS-Socket` means
    [copybooks/wssystem.cob:L137-L144] and what the frozen TCP-only declaration
    carries.

    Args:
        layout: the parameter record's layout, for the declared spelling and owner
            of each field.
        record: the record the fields belong to, for qualification.
        bindings: field name to environment variable name, as
            `credentials_from_env` returned it - so the names emitted are the ones
            whose presence and width that function has already checked, and there is
            no second list to drift.

    Returns:
        One `accept` line per connection field, in declaration order.
    """
    lines: list[str] = []
    for field, _environment, _width, _required in CONNECTION_FIELD_BINDINGS:
        environment = bindings[field]
        _kind, declared = layout.classify(field)
        owner = layout.qualifier(field, record)
        lines.append(
            f"     accept   {declared} in {owner} from environment "
            f'"{environment}"'
        )
    return lines


def table_moves_for(
    layout: Layout,
    record: str,
    name: str,
    entries: list,
    *,
    where: str,
) -> list[str]:
    """The MOVEs for a table field declared as a list of `at'/`value' entries.

    THE SUBSCRIPT IS EMITTED UNQUALIFIED, which is the shape the frozen code itself
    uses -- `def-acs (31)' at [irs/irs030.cbl:L871] and `def-codes (w)' at
    [irs/irs030.cbl:L794] -- and is unambiguous here because a generated driver copies
    one record layout and the four shared copybooks, none of which repeats these names.
    The index is BOUNDS-CHECKED against the OCCURS clause, because writing past a table
    is the one mistake a fixture can make that no read-back would reveal.
    """
    key = name.lower()
    if key not in layout.subscripted:
        _kind, declared = layout.classify(name)
        fixture_fail(
            FIXTURE_EX_DECLARATION,
            f"{declared} in {where} is not inside a table, so a list of entries is "
            "not what it takes.",
            "Declare a single quoted value.",
        )
    table, bound = layout.subscripted[key]
    kind, declared = layout.classify(name)
    lines: list[str] = []
    seen: set[int] = set()
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or "at" not in entry:
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"entry {position} of {declared} in {where} must be a mapping with an "
                "`at' and a `value'.",
            )
        extra = set(entry) - {"at", "value", "raw"}
        if extra or not ({"value", "raw"} & set(entry)):
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"entry {position} of {declared} in {where} must hold `at' and exactly "
                f"one of `value' or `raw'. It holds: {sorted(entry)}.",
            )
        index_text = entry["at"]
        if not isinstance(index_text, str) or not index_text.isdigit():
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"the `at' of entry {position} of {declared} in {where} must be a "
                "quoted whole number.",
            )
        index = int(index_text)
        if index < 1 or index > bound:
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"entry {position} of {declared} in {where} addresses {index}, and "
                f"{table} holds entries 1 to {bound} [OCCURS {bound}].",
                "Writing past a table is the one fixture mistake a read-back would not",
                "reveal, so it is refused here.",
            )
        if index in seen:
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"{declared} in {where} declares entry {index} more than once, so one "
                "of the two would silently win.",
            )
        seen.add(index)
        if "raw" in entry:
            width = layout.display_width.get(key)
            text = entry["raw"]
            if width is None or kind == "alphanumeric":
                fixture_fail(
                    FIXTURE_EX_DECLARATION,
                    f"a raw value is not available for {declared}: it is either not "
                    "held in DISPLAY or already alphanumeric.",
                )
            if not isinstance(text, str) or len(text) != width:
                fixture_fail(
                    FIXTURE_EX_DECLARATION,
                    f"the raw value for {declared} entry {index} must be a quoted "
                    f"string of exactly {width} character(s).",
                )
            refuse_unplaceable_text(
                text,
                what=f"the raw value for {declared} entry {index}",
                code=FIXTURE_EX_DECLARATION,
            )
            lines.append(
                f'     move     "{text}" to {declared} ({index}) (1:{width})'
            )
            continue
        value = entry["value"]
        if not isinstance(value, str):
            fixture_fail(
                FIXTURE_EX_DECLARATION,
                f"the value of entry {index} of {declared} in {where} must be a quoted "
                "string (rule R-2).",
            )
        literal = cobol_literal(kind, value, declared)
        lines.append(f"     move     {literal} to {declared} ({index})")
    return lines


def raw_move_for(
    layout: Layout,
    record: str,
    name: str,
    value: dict,
    *,
    where: str,
) -> str:
    """The MOVE for a `{raw: "..."}' declaration: bytes stored verbatim.

    WHY THIS EXISTS AT ALL, AND WHY IT IS OPT-IN. Some frozen guards can only be
    reached by a field holding something its own picture does not describe. The one
    this harness needs is `if post-batch not numeric' [general/gl072.cbl:L291-L292],
    which tests a work-file field written from `Batch pic 9(5)'
    [copybooks/wspost.cob:L15]: an ordinary MOVE of digits can never make it true, so
    a scenario that means to exercise that skip has to be able to say so. Removing the
    data an anomaly needs is forbidden (rule R-4), and quietly coercing it would be
    the same removal wearing a different hat.
    Storing bytes into a numeric-display item is done by reference modification, which
    yields an alphanumeric receiving item and therefore performs no numeric
    conversion. That it does so in this compiler, and that the guard becomes reachable
    as a result, was MEASURED against GnuCOBOL 3.2 rather than assumed.
    The form is a one-key mapping so that it can never be mistaken for data: an
    ordinary value is a plain string, and a value that bypasses the field's own
    picture has to be written as one deliberately.
    """
    if set(value) != {"raw"}:
        fixture_fail(
            FIXTURE_EX_DECLARATION,
            f"the value for {name} in {where} is a mapping, so it must hold exactly "
            f"one key, raw. It holds: {sorted(value) or 'nothing'}.",
        )
    text = value["raw"]
    if not isinstance(text, str):
        fixture_fail(
            FIXTURE_EX_DECLARATION,
            f"the raw value for {name} in {where} must be a quoted string.",
        )
    refuse_unplaceable_text(
        text, what=f"the raw value for {name} in {where}", code=FIXTURE_EX_DECLARATION
    )
    declared, width = layout.raw_target(name)
    if len(text) != width:
        fixture_fail(
            FIXTURE_EX_DECLARATION,
            f"the raw value for {declared} in {where} is {len(text)} character(s) and "
            f"the field holds exactly {width}.",
            "A raw value is stored byte for byte, so it is neither padded nor",
            "truncated: state all of it or none of it.",
        )
    owner = layout.qualifier(name, record)
    return f'     move     "{text}" to {declared} in {owner} (1:{width})'


def writer_via_handler(
    *,
    handler: str,
    record: str,
    defs_field: str,
    linkage: list[str],
    path: str,
    records: list[list[str]],
) -> str:
    """A driver that writes one flat file by calling its frozen handler.

    The shape is the loaders' own: set File-System-Used to zero so the handler takes
    its Cobol-file path [common/glbatchLD.cbl:L295-L304], open output, write each
    record, close. Every status is checked, because a handler reports through
    `fs-reply' and never through a process status.
    """
    body: list[str] = []
    for index, moves in enumerate(records, start=1):
        body.append(f"*>   record {index}")
        body.append(f"     initialize {record}")
        body.extend(moves)
        body.append(f'     move     {index} to WS-Fixture-Seq')
        body.append("     perform  fx-write")
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfx.",
            "*>",
            "*>  GENERATED by harness/dump_tables.py --make-fixtures. Not committed, not frozen, and",
            "*>  never edited by hand: rebuild it by re-running the builder.",
            "*>",
            f'*>  Writes {cobol_path_literal(path, what="the seed file path")}',
            f"*>  through the frozen handler {handler}, whose own LINKAGE copy block is",
            "*>  reproduced verbatim below so that the record name and every picture",
            "*>  clause are the handler's, not this generator's.",
            "*>",
            "       environment division.",
            "       configuration section.",
            "       data division.",
            "       working-storage section.",
            "*>",
            "*>  The frozen handler's own linkage declarations, in its own order.",
            *(f" {statement}" for statement in linkage),
            "*>",
            " 01  WS-Fixture-Seq        pic 9(4) value zero.",
            " 01  WS-Fixture-Written    pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            "*>",
            "*>  Zero means: take the Cobol flat-file path, not the RDB path. The RDB",
            "*>  path would need the generated bridge programs and a live server, and a",
            "*>  fixture builder has no business touching either.",
            "*>",
            "     move     zero to File-System-Used",
            "                      FA-File-System-Used.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     set      fn-open to true.",
            "     set      fn-output to true.",
            f'     perform  fx-call.',
            "     if       fs-reply not = zero",
            '              display "acasfx: open output failed, fs-reply = "',
            "                      fs-reply \" we-error = \" we-error",
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "*>",
            *body,
            "*>",
            "     set      fn-close to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfx: close failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            '     display  "acasfx: wrote " WS-Fixture-Written " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "*>",
            " fx-write.",
            "     set      fn-write to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfx: write failed on record "',
            "                      WS-Fixture-Seq \" fs-reply = \" fs-reply",
            "                      \" we-error = \" we-error",
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "     add      1 to WS-Fixture-Written.",
            "*>",
            " fx-call.",
            f'     call     "{handler}" using System-Record',
            f"                              {record}",
            "                              File-Access",
            "                              File-Defs",
            "                              ACAS-DAL-Common-data.",
            "",
        ]
    )


def writer_for_system(
    *, defs_field: str, path: str, records: dict[str, list[str]]
) -> str:
    """A writer for `system.dat', which every loader opens itself.

    [copybooks/selsys.cob] declares it ORGANIZATION RELATIVE with relative key `rrn'
    and [copybooks/fdsys.cob] gives it the system record, so the select and the FD are
    copied here exactly as the loaders copy them
    [common/glbatchLD.cbl:L129], [common/glbatchLD.cbl:L136]. `System-Record' comes
    from the FD, so it is deliberately NOT also declared in working storage.
    """
    body: list[str] = []
    for key in sorted(SYSTEM_RELATIVE_RECORDS):
        _copybook, record, purpose = SYSTEM_RELATIVE_RECORDS[key]
        body.append(f"*>   relative record {key} -- {record} -- {purpose}")
        body.append(f"     initialize {record}")
        body.extend(records.get(key, []))
        if record != "System-Record":
            # Records 2, 3 and 4 are built in working storage and then copied into the
            # FD record, because the FD declares only the parameter record
            # [copybooks/fdsys.cob:L10-L12] while all four share its 1024 bytes.
            body.append(f"     move     {record} to System-Record")
        body.append(f"     move     {key} to rrn")
        body.append("     perform  fx-write")
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfxsys.",
            "*>",
            "*>  GENERATED by harness/dump_tables.py --make-fixtures. Not committed, not frozen.",
            "*>",
            f'*>  Writes {cobol_path_literal(path, what="the seed file path")} '
            "using the frozen select and FD every loader uses for it.",
            "*>",
            "       environment division.",
            "       configuration section.",
            "       input-output section.",
            "       file-control.",
            ' copy "selsys.cob".',
            "       data division.",
            "       file section.",
            ' copy "fdsys.cob".',
            "       working-storage section.",
            ' copy "wsfnctn.cob".',
            ' copy "wsnames.cob".',
            *(
                f' copy "{SYSTEM_RELATIVE_RECORDS[key][0]}".'
                for key in sorted(SYSTEM_RELATIVE_RECORDS)
                if SYSTEM_RELATIVE_RECORDS[key][1] != "System-Record"
            ),
            " 01  WS-Fixture-Seq        pic 9(4) value zero.",
            " 01  WS-Fixture-Written    pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     open     output system-file.",
            "     if       fs-reply not = zero",
            '              display "acasfxsys: open output failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            *body,
            "     close    system-file.",
            "     if       fs-reply not = zero",
            '              display "acasfxsys: close failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            '     display  "acasfxsys: wrote " WS-Fixture-Written " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "*>",
            " fx-write.",
            "     move     rrn to WS-Fixture-Seq.",
            "     write    System-Record invalid key",
            '              display "acasfxsys: write failed at rrn " WS-Fixture-Seq',
            "                      \" fs-reply = \" fs-reply",
            "              move 69 to return-code",
            "              stop run",
            "     end-write.",
            "     add      1 to WS-Fixture-Written.",
            "",
        ]
    )


def reader_via_handler(
    *,
    handler: str,
    record: str,
    defs_field: str,
    linkage: list[str],
    path: str,
    single: bool = False,
) -> str:
    """A reader that proves the file loads through the SAME frozen handler.

    This is the read-back check, and it is the only assurance that matters: a file the
    handler cannot open and walk is not a fixture, whatever it looks like on disk. The
    count it prints is compared with the count the writer reported.

    `single' SUPPRESSES THE LOOP, and it is not an optimisation -- it is required for
    correctness on two of the seventeen handlers. acasirsub3 and acasirsub5 are
    SINGLE-RECORD handlers: their own comments say IRS "only does a read or write and
    not a direct open or close" [common/acasirsub3.cbl:L168-L178], their EVALUATE turns
    function 1 and function 2 into no-ops returning zero
    [common/acasirsub3.cbl:L199-L208], and the read path OPENS, reads one record and
    CLOSES on every single call, logging itself as "Open Dflt, Read, Close on 1"
    [common/acasirsub3.cbl:L259-L310]. It therefore NEVER REPORTS EOF, and a
    read-until-ten loop against it spins forever -- which is exactly how this was
    found, as a silent twelve-minute hang with no output at all.
    """
    loop = (
        [
            "     set      fn-read-next to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfxrd: single read failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "     add      1 to WS-Fixture-Read.",
        ]
        if single
        else [
            " fx-010-loop.",
            "     set      fn-read-next to true.",
            "     perform  fx-call.",
            "     if       fs-reply = 10",
            "              go to fx-020-end",
            "     end-if.",
            "     if       fs-reply not = zero",
            '              display "acasfxrd: read next failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "     add      1 to WS-Fixture-Read.",
            "     go       to fx-010-loop.",
        ]
    )
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfxrd.",
            "*>  GENERATED by harness/dump_tables.py --make-fixtures. Read-back proof only.",
            "       environment division.",
            "       configuration section.",
            "       data division.",
            "       working-storage section.",
            *(f" {statement}" for statement in linkage),
            " 01  WS-Fixture-Read       pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            "     move     zero to File-System-Used",
            "                      FA-File-System-Used.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     set      fn-open to true.",
            "     set      fn-input to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfxrd: open input failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            *loop,
            " fx-020-end.",
            "     set      fn-close to true.",
            "     perform  fx-call.",
            '     display  "acasfxrd: read " WS-Fixture-Read " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "*>",
            " fx-call.",
            f'     call     "{handler}" using System-Record',
            f"                              {record}",
            "                              File-Access",
            "                              File-Defs",
            "                              ACAS-DAL-Common-data.",
            "",
        ]
    )


def reader_for_system(*, defs_field: str, path: str) -> str:
    """The read-back proof for `system.dat', through its frozen select and FD."""
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfxsysrd.",
            "*>  GENERATED by harness/dump_tables.py --make-fixtures. Read-back proof only.",
            "       environment division.",
            "       configuration section.",
            "       input-output section.",
            "       file-control.",
            ' copy "selsys.cob".',
            "       data division.",
            "       file section.",
            ' copy "fdsys.cob".',
            "       working-storage section.",
            ' copy "wsfnctn.cob".',
            ' copy "wsnames.cob".',
            " 01  WS-Fixture-Read       pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     open     input system-file.",
            "     if       fs-reply not = zero",
            '              display "acasfxsysrd: open input failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            # EACH SLOT IS READ BY NUMBER, not walked. A sequential walk would report
            # a count without proving WHICH relative records exist, and the whole
            # point of this file is that four specific slots must be readable because
            # four different loaders each go straight to one of them.
            *(
                line
                for key in sorted(SYSTEM_RELATIVE_RECORDS)
                for line in (
                    f"     move     {key} to rrn.",
                    "     read     system-file invalid key",
                    f'              display "acasfxsysrd: relative record {key} '
                    f'({SYSTEM_RELATIVE_RECORDS[key][2]}) is missing"',
                    "              move 69 to return-code",
                    "              stop run",
                    "     end-read.",
                    "     add      1 to WS-Fixture-Read.",
                )
            ),
            " fx-020-end.",
            "     close    system-file.",
            '     display  "acasfxsysrd: read " WS-Fixture-Read " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "",
        ]
    )


# =============================================================================
# BUILDING
# =============================================================================
def run_fixture_program(
    argv: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 600
) -> subprocess.CompletedProcess[str]:
    """Run one bounded external command and return it, output captured.

    stdin is DEVNULL on purpose. Several frozen handlers reach an `accept' on an error
    path -- [common/acasirsub3.cbl:L400] is one -- and a fixture build must fail rather
    than wait for a keypress that will never come.
    """
    return subprocess.run(  # noqa: S603 - argv is built here, never from a string
        argv,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
    )


def compile_and_run(
    *,
    label: str,
    source: str,
    work: Path,
    repo: Path,
    env: dict[str, str],
    modules: Path | None,
) -> str:
    """Compile one generated program with cobc, run it, and return its output."""
    stem = f"acasfx_{label}"
    program = work / f"{stem}.cbl"
    program.write_text(source, encoding="utf-8")
    binary = work / stem
    argv = [
        "cobc",
        "-x",
        "-free",
        "-o",
        str(binary),
        f"-I{repo / 'copybooks'}",
        "-fmissing-statement=ok",
        str(program),
    ]
    compiled = run_fixture_program(argv, cwd=work, env=env)
    if compiled.returncode != 0:
        fixture_fail(
            FIXTURE_EX_COMPILE,
            f"cobc rejected the generated program for {label} (status {compiled.returncode}).",
            f"source: {program}",
            *(compiled.stderr or compiled.stdout or "").splitlines()[:20],
        )
    child = dict(env)
    if modules is not None:
        existing = child.get("COB_LIBRARY_PATH", "")
        child["COB_LIBRARY_PATH"] = (
            f"{modules}:{existing}" if existing else str(modules)
        )
    # A GENERATED PROGRAM GETS A SHORT LEASH, DELIBERATELY. It writes or reads a
    # handful of records and nothing else, so anything past a minute is a hang and not
    # slow progress -- and a hang here is the worst failure this tool can have, because
    # it produces no output at all to diagnose from. The read-back of the IRS defaults
    # was exactly that until the single-record property of acasirsub3 was found; this
    # bound is what turns the next such surprise into a report instead of a stall.
    try:
        executed = run_fixture_program([str(binary)], cwd=work, env=child, timeout=60)
    except subprocess.TimeoutExpired:
        fixture_fail(
            FIXTURE_EX_RUNTIME,
            f"the generated program for {label} did not finish within 60 seconds.",
            "It writes or reads only a few records, so this is a hang rather than slow",
            "progress. The likeliest causes, both properties of the frozen handler:",
            "  - the handler never reports EOF, so the read-back loop cannot end. Two",
            "    of the seventeen behave this way and are marked single_record above.",
            "  - the handler reached an interactive `accept' on an error path. stdin is",
            "    /dev/null here, so it cannot be satisfied and must not be waited on.",
            f"source: {program}",
        )
    if executed.returncode != 0:
        fixture_fail(
            FIXTURE_EX_RUNTIME,
            f"the generated program for {label} failed (status {executed.returncode}).",
            *(executed.stdout or "").splitlines()[:12],
            *(executed.stderr or "").splitlines()[:12],
        )
    return executed.stdout


def system_blocks(document: dict) -> dict[str, dict]:
    """The four relative records a scenario declares for `system.dat'.

    The declaration is a mapping keyed by RELATIVE RECORD NUMBER, quoted, mirroring the
    frozen dispatch that moves File-Key-No straight into rrn
    [common/acas000.cbl:L461]. All four keys are REQUIRED -- see the comment on
    SYSTEM_RELATIVE_RECORDS for why a partial declaration aborts the seed rather than
    degrading -- and a slot with nothing to pin is declared as an empty mapping, which
    writes an INITIALIZEd record. Empty is a statement about the pre-state; ABSENT is a
    slot no loader can read.
    """
    block = document.get("seed_records")
    if not isinstance(block, dict) or "system.dat" not in block:
        fixture_fail(
            FIXTURE_EX_SCENARIO,
            "the scenario declares no seed_records for system.dat.",
            "All four system loaders read it, unconditionally and first",
            "[common/masterLD.sh:L50-L88], and it carries the run date, the fan-out",
            "switch and the database account, so it cannot be defaulted.",
        )
    declared = block["system.dat"]
    if not isinstance(declared, dict):
        fixture_fail(
            FIXTURE_EX_SCENARIO,
            "seed_records[system.dat] must be a mapping keyed by relative record "
            "number, because that one file holds FOUR different records.",
            "The four keys and what each becomes:",
            *(
                f'  "{key}": {SYSTEM_RELATIVE_RECORDS[key][1]:16} -> '
                f"{SYSTEM_RELATIVE_RECORDS[key][2]}"
                for key in sorted(SYSTEM_RELATIVE_RECORDS)
            ),
            "A slot with nothing to pin is declared as {} and is written INITIALIZEd.",
        )
    unknown = sorted(set(map(str, declared)) - set(SYSTEM_RELATIVE_RECORDS))
    if unknown:
        fixture_fail(
            FIXTURE_EX_SCENARIO,
            f"seed_records[system.dat] declares relative record(s) {unknown}, and the "
            "frozen loaders read only 1, 2, 3 and 4.",
            "acas000 rejects a key outside that range itself",
            "[common/acas000.cbl:L335].",
        )
    resolved: dict[str, dict] = {}
    for key in sorted(SYSTEM_RELATIVE_RECORDS):
        if key not in {str(k) for k in declared}:
            _copybook, record, purpose = SYSTEM_RELATIVE_RECORDS[key]
            fixture_fail(
                FIXTURE_EX_SCENARIO,
                f'seed_records[system.dat] does not declare relative record "{key}" '
                f"({record}, {purpose}).",
                "All four are required. masterLD runs all four loaders",
                "unconditionally, and the last is tested against zero rather than 63",
                "[common/masterLD.sh:L83-L86], so an unwritten slot ABORTS the seed.",
                'Declare it as {} if there is nothing to pin in it.',
            )
        value = next(v for k, v in declared.items() if str(k) == key)
        if value is None:
            value = {}
        if isinstance(value, list):
            if len(value) > 1:
                fixture_fail(
                    FIXTURE_EX_SCENARIO,
                    f'seed_records[system.dat]["{key}"] holds {len(value)} records and '
                    "a relative slot holds exactly one.",
                )
            value = value[0] if value else {}
        if not isinstance(value, dict):
            fixture_fail(
                FIXTURE_EX_SCENARIO,
                f'seed_records[system.dat]["{key}"] must be a mapping of field names '
                "to quoted values, or {} for an INITIALIZEd record.",
            )
        resolved[key] = value
    return resolved


def declared_records(document: dict, name: str) -> list[dict[str, str]]:
    """The records a scenario declares for one file, or an empty list."""
    block = document.get("seed_records")
    if block is None:
        return []
    if not isinstance(block, dict):
        fixture_fail(
            FIXTURE_EX_SCENARIO,
            "seed_records must be a mapping of file name to a list of records.",
        )
    records = block.get(name, [])
    if records is None:
        records = []
    if not isinstance(records, list):
        fixture_fail(FIXTURE_EX_SCENARIO, f"seed_records[{name}] must be a list of records.")
    for entry in records:
        if not isinstance(entry, dict):
            fixture_fail(
                FIXTURE_EX_SCENARIO,
                f"every record in seed_records[{name}] must be a mapping of field to value.",
            )
    return records


def credentials_from_env() -> dict[str, str]:
    """Validate all six connection fields and return the ENVIRONMENT NAME of each.

    THE VALUES ARE VALIDATED HERE AND EMITTED NOWHERE. Returning them would put a
    `move '<password>' to RDBMS-Passwd' into the generated COBOL, so a build kept for
    diagnosis, or a compiler diagnostic echoing the offending line, would publish the
    database account. The generated writer performs `accept RDBMS-Passwd from
    environment "ACAS_DB_PASSWORD"' instead, which reaches the same field with the same
    bytes at RUN time and leaves nothing in the source.

    The width and presence checks stay HERE rather than moving into the generated
    program, because a refusal a human can read beats a truncation a COBOL move
    performs silently - and `pic x(12)` is what the frozen loader passes on
    [copybooks/wssystem.cob:L137-L144].

    Returns:
        The field name mapped to the ENVIRONMENT VARIABLE NAME it is accepted from -
        never to its value.
    """
    values: dict[str, str] = {}
    for field, environment, width, required in CONNECTION_FIELD_BINDINGS:
        raw_value = os.environ.get(environment) or ""
        value = raw_value if field == "RDBMS-Passwd" else raw_value.strip()
        if required and not value:
            fixture_fail(
                FIXTURE_EX_PRECONDITION,
                f"{field} has no value: {environment} does not supply it.",
                "The system record carries all six connection parameters used by",
                "the frozen loaders [copybooks/wssystem.cob:L137-L144], and they",
                "come from the environment so no deployment value is committed.",
            )
        if len(value) > width:
            fixture_fail(
                FIXTURE_EX_PRECONDITION,
                f"{field} is {len(value)} characters long; the field is pic x({width}).",
                "A longer value is silently truncated before the frozen loader",
                "connects [copybooks/wssystem.cob:L137-L144].",
            )
        values[field] = environment
    return values


def build_one(
    *,
    name: str,
    document: dict,
    out: Path,
    work: Path,
    repo: Path,
    env: dict[str, str],
    modules: Path | None,
    verbose: bool,
) -> int:
    """Build one declared flat file and prove it reads back. Returns the row count."""
    spec = SEED_FILES[name]
    handler = spec["handler"]
    defs_field = spec["defs"]
    assert isinstance(defs_field, str)
    target = out / name
    # system.dat is declared by RELATIVE RECORD NUMBER rather than as a list, because
    # that one file holds four different records -- see SYSTEM_RELATIVE_RECORDS -- so
    # its own reader validates the shape and the generic list reader is not used.
    records = [] if name == "system.dat" else declared_records(document, name)

    if name == "system.dat":
        #  Validated here, emitted nowhere: the return value is the map of field to
        #  ENVIRONMENT VARIABLE NAME, and the check that each is present and fits its
        #  `pic x(n)` happens on this call.
        forced = credentials_from_env()
        declared_blocks = system_blocks(document)
        rendered: dict[str, list[str]] = {}
        for key in sorted(SYSTEM_RELATIVE_RECORDS):
            copybook, record, purpose = SYSTEM_RELATIVE_RECORDS[key]
            layout = read_layout(repo, [copybook], {}, record=record)
            fields = dict(declared_blocks[key])
            if key == "1":
                for reserved in CREDENTIAL_FIELDS:
                    if any(k.lower() == reserved.lower() for k in fields):
                        fixture_fail(
                            FIXTURE_EX_SCENARIO,
                            f"the scenario declares {reserved}, which is refused.",
                            "The six connection fields are filled from the environment",
                            "so no credential or deployment endpoint is committed to",
                            "the repository.",
                        )
            elif any(k.lower() in {f.lower() for f in CREDENTIAL_FIELDS} for k in fields):
                fixture_fail(
                    FIXTURE_EX_SCENARIO,
                    f"relative record {key} declares a credential field, which is "
                    "refused. Only the parameter record carries the database account.",
                )
            rendered[key] = moves_for(
                layout,
                record,
                fields,
                where=f"seed_records[system.dat][{key}] ({purpose})",
            )
            if key == "1":
                #  APPENDED AFTER THE DECLARED MOVES, so an `initialize' followed by
                #  the scenario's own fields is followed by the environment's six -
                #  the same order the old literal MOVEs occupied, with no value in
                #  the source. `forced` holds the VARIABLE NAMES and
                #  has already refused an absent or over-wide value.
                rendered[key].extend(
                    connection_accepts_for(layout, record, forced)
                )
        records = [fields for fields in declared_blocks.values() if fields]
        source = writer_for_system(
            defs_field=defs_field, path=str(target), records=rendered
        )
        wrote = compile_and_run(
            label="system_w",
            source=source,
            work=work,
            repo=repo,
            env=env,
            modules=None,
        )
        read = compile_and_run(
            label="system_r",
            source=reader_for_system(defs_field=defs_field, path=str(target)),
            work=work,
            repo=repo,
            env=env,
            modules=None,
        )
    else:
        assert isinstance(handler, str)
        linkage = handler_linkage_copies(repo, handler)
        record_copy = linkage[0]
        record_name = record_name_of(repo, handler)
        override = spec.get("layout")
        if override:
            # The substitution has to reach the GENERATED SOURCE too, not just the
            # field classification: the driver's data division is built from these copy
            # statements, so a name classified from one copybook and declared from
            # another would not compile. Replacing the record copybook -- the first
            # statement -- and leaving the other four exactly as the handler writes
            # them is what keeps the driver and the handler agreeing about everything
            # else. No REPLACING is needed because the substituted copybook already
            # names the record as the handler's USING clause names it, and
            # read_layout's record check is what proves that.
            linkage = [f'copy "{override}".'] + linkage[1:]
            record_copy = linkage[0]
        layout = read_layout(
            repo,
            [copybook_of(record_copy)],
            replacements_of(record_copy),
            record=record_name,
        )
        single = bool(spec.get("single_record"))
        if single and len(records) > 1:
            fixture_fail(
                FIXTURE_EX_SCENARIO,
                f"{name} declares {len(records)} records and {handler} holds exactly "
                "one.",
                "That handler re-opens the file for OUTPUT on every write",
                f"[common/{handler}.cbl], so a second record would silently REPLACE",
                "the first and the fixture would not be what the scenario says it is.",
                "Declare a single record.",
            )
        rendered = [
            moves_for(
                layout,
                record_name,
                fields,
                where=f"seed_records[{name}][{index}]",
            )
            for index, fields in enumerate(records, start=1)
        ]
        source = writer_via_handler(
            handler=handler,
            record=record_name,
            defs_field=defs_field,
            linkage=linkage,
            path=str(target),
            records=rendered,
        )
        wrote = compile_and_run(
            label=f"{handler}_w",
            source=source,
            work=work,
            repo=repo,
            env=env,
            modules=modules,
        )
        read = compile_and_run(
            label=f"{handler}_r",
            source=reader_via_handler(
                handler=handler,
                record=record_name,
                defs_field=defs_field,
                linkage=linkage,
                path=str(target),
                single=single,
            ),
            work=work,
            repo=repo,
            env=env,
            modules=modules,
        )

    written = count_in(wrote)
    reread = count_in(read)
    if not target.exists():
        fixture_fail(
            FIXTURE_EX_RUNTIME,
            f"{name} was reported written but is not on disk at {target}.",
        )
    if written != reread:
        fixture_fail(
            FIXTURE_EX_RUNTIME,
            f"{name} was written with {written} record(s) but reads back as {reread}.",
            "A fixture that does not read back through the frozen handler is not a",
            "fixture, whatever it looks like on disk.",
        )
    if verbose:
        sys.stdout.write(
            f"    {name:<18} {written:>4} record(s)  read back {reread:>4}  "
            f"{target.stat().st_size:>9} bytes\n"
        )
    return written


def record_name_of(repo: Path, handler: str) -> str:
    """The record name a handler's PROCEDURE DIVISION USING list puts second.

    Read from the frozen source rather than tabulated here, for the same reason the
    linkage block is: a name this generator held its own copy of could drift.
    """
    text = (repo / "common" / f"{handler}.cbl").read_text(
        encoding="utf-8", errors="replace"
    )
    match = re.search(r"procedure\s+division\s+using(.*?)\.", text, re.IGNORECASE | re.DOTALL)
    if match is None:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"{handler} has no PROCEDURE DIVISION USING list, so its record name "
            f"cannot be read.",
        )
    words = [w for w in re.split(r"\s+", match.group(1).strip()) if w]
    if len(words) < 2:
        fixture_fail(FIXTURE_EX_PRECONDITION, f"{handler}'s USING list is shorter than expected.")
    return words[1]


def count_in(output: str) -> int:
    """The record count a generated program reported."""
    match = re.search(r"(?:wrote|read)\s+(\d+)\s+record", output)
    if match is None:
        fixture_fail(
            FIXTURE_EX_RUNTIME,
            "a generated program did not report a record count.",
            *output.splitlines()[:10],
        )
    return int(match.group(1))


def report_fields(repo: Path, name: str) -> None:
    """Print the settable fields of one seed file's record.

    Read from the SAME frozen definitions the writer is generated from -- the
    handler's own LINKAGE copy block, with the handler's own REPLACING clauses applied
    -- so what this prints and what a build will accept cannot disagree.
    """
    spec = SEED_FILES[name]
    handler = spec["handler"]
    if handler is None:
        copybooks, replacements, record = ["fdsys.cob"], {}, "System-Record"
        origin = "[copybooks/fdsys.cob], opened directly by the loaders"
    else:
        statements = handler_linkage_copies(repo, handler)
        copybooks = [copybook_of(statement) for statement in statements]
        replacements = {}
        for statement in statements:
            replacements.update(replacements_of(statement))
        record = record_name_of(repo, handler)
        origin = f"[common/{handler}.cbl] LINKAGE SECTION: " + ", ".join(copybooks)
        override = spec.get("layout")
        if override:
            copybooks, replacements = [str(override)], {}
            origin = (
                f"[copybooks/{override}], the view the POSTING PROGRAM reads through; "
                f"see the SEED_FILES note for {name}"
            )
    layout = read_layout(repo, copybooks[:1], replacements, record=record)
    sys.stdout.write(f"\n{name} -> {record}\n  from {origin}\n")
    if replacements:
        pairs = ", ".join(f"{a} -> {b}" for a, b in sorted(replacements.items()))
        sys.stdout.write(f"  REPLACING {pairs}\n")
    for kind, table in (("numeric", layout.numeric), ("text", layout.alphanumeric)):
        for key in sorted(table):
            declared = table[key]
            width = layout.display_width.get(key)
            shape = f"DISPLAY({width})" if width else "COMP/COMP-3/binary"
            note = ""
            if key in layout.subscripted:
                owner, bound = layout.subscripted[key]
                note = f"   <- needs at: 1..{bound} in {owner}"
            sys.stdout.write(f"    {kind:8} {shape:18} {declared}{note}\n")
    for key in sorted(layout.excluded):
        sys.stdout.write(f"    -        NOT SETTABLE       {key}: {layout.excluded[key]}\n")


#: The marker a `--work` directory must carry when it is not the default
#: `<out>/.build`. Written by this tool for a directory that is empty,
#: and required thereafter, so a work root cannot be a path that happens to exist.
WORK_ROOT_MARKER: Final[str] = ".acas-harness-work-root"


def assert_work_directory(
    work: Path, *, repo: Path, out: Path, explicit: bool
) -> None:
    """Refuse a work directory that could overwrite something that matters.

    WHY THIS EXISTS. `--work` was accepted unchecked, and this tool
    WRITES GENERATED COBOL into it and compiles there. Pointed at the checkout it
    would create programs inside frozen specification directories; pointed at a
    populated directory it would litter, and `harness/seed.sh --build-fixtures` removes the
    default one recursively. Two directions of containment are checked, because both
    are wrong: the work directory must not be inside the checkout, AND the checkout
    must not be inside the work directory.

    THE DEFAULT IS EXEMPT FROM THE MARKER, NOT FROM THE CONTAINMENT. `<out>/.build`
    is created by this tool underneath a directory `harness/seed.sh --build-fixtures` has already
    claimed, so requiring a second marker there would be ceremony; an explicitly
    named root has no such provenance and must carry one.

    Args:
        work: The resolved work directory, already created.
        repo: The frozen checkout.
        out: The resolved output directory.
        explicit: True when `--work` named it, False for the default.

    Raises:
        SystemExit: Through `fail`, with `FIXTURE_EX_PRECONDITION`.
    """
    resolved = work.resolve()

    if resolved == repo or str(resolved).startswith(f"{repo}{os.sep}"):
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"the work directory {resolved} is inside the frozen checkout {repo}.",
            "This tool writes generated COBOL there and compiles it; the checkout is",
            "read-only specification and nothing here may write to it (R-3).",
        )
    if str(repo).startswith(f"{resolved}{os.sep}"):
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"the frozen checkout {repo} is inside the work directory {resolved}.",
            "A work root above the checkout puts the specification inside a directory",
            "this tool and harness/seed.sh --build-fixtures treat as disposable.",
        )
    if resolved == Path(resolved.anchor) or len(resolved.parts) <= 2:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"refusing {resolved} as a work directory: it is a filesystem or",
            "top-level directory. Name a directory created for the purpose.",
        )
    home = Path.home()
    if resolved == home:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"refusing the home directory {resolved} as a work directory.",
        )

    if not explicit:
        #  The default `<out>/.build`, underneath a root harness/seed.sh --build-fixtures claimed.
        return

    if resolved == out or str(resolved).startswith(f"{out}{os.sep}"):
        #  Inside the fixture root this run is publishing into: same provenance as
        #  the default, so the marker is not demanded.
        return

    marker = resolved / WORK_ROOT_MARKER
    if marker.is_file():
        return

    existing = [entry for entry in resolved.iterdir()]
    if existing:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"refusing {resolved} as a work directory: it holds content this tool",
            "did not create and carries no harness marker.",
            f"  first entry found: {existing[0]}",
            f"  expected marker  : {marker}",
            "Generated programs are written and compiled here, so a directory whose",
            "provenance cannot be established is not used. Point --work at an empty",
            "directory, or create the marker deliberately.",
        )
    try:
        marker.write_text(
            "# harness/dump_tables.py --make-fixtures work root.\n"
            "# Generated COBOL is written and compiled here; delete this file to\n"
            "# revoke that.\n",
            encoding="utf-8",
        )
        marker.chmod(0o600)
    except OSError as exc:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"could not claim the work directory by writing {marker}: {exc}",
        )


def make_fixtures_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=FIXTURE_PROG,
        description=(
            "Build the flat seed files a scenario declares, from the records it "
            "declares, using the frozen handlers and copybooks."
        ),
        epilog=(
            "The records live in the scenario file under seed_records, as text, so "
            "that no money figure is ever parsed by YAML into a binary float. The "
            "six RDBMS connection fields of the system record are filled from the "
            "environment and refused in the scenario file."
        ),
    )
    parser.add_argument("scenario", help="path of the scenario YAML")
    parser.add_argument(
        "--list-fields",
        metavar="SEED-FILE",
        default=None,
        help="do not build anything; report the settable fields of one seed file's "
        "record, spelled exactly as the frozen copybook spells them, with the "
        "handler and copybook they were read from. Pass ALL for every declared "
        "file. This exists so that a scenario's seed_records are transcribed from "
        "the frozen definitions BY THIS TOOL rather than by eye.",
    )
    parser.add_argument(
        "--out",
        required=False,
        help="directory the flat files are written into. Created if absent, and "
        "CLEARED of any file this builder would write, so a stale fixture from an "
        "earlier build cannot be seeded by mistake.",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("ACAS_REPO", "/repo"),
        help="the frozen checkout (default $ACAS_REPO, or /repo)",
    )
    parser.add_argument(
        "--modules",
        default=os.environ.get("ACAS_BUILD", "/build"),
        help="the build tree whose common/ holds the compiled handlers "
        "(default $ACAS_BUILD, or /build)",
    )
    parser.add_argument(
        "--work",
        default=None,
        help="where the generated programs are compiled (default <out>/.build). A "
        "directory OUTSIDE the checkout, with the checkout not inside it, and - "
        "unless it is under --out - either empty or carrying the "
        f"{WORK_ROOT_MARKER} marker this tool writes for an empty one.",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="report only failures"
    )
    args = parser.parse_args(argv)

    # The same discipline the five shell scripts of this harness set for themselves.
    # It has to be set before any directory or file is created, and it propagates to
    # the compiler and to the generated writer programs, which are the processes that
    # actually create the flat files.
    os.umask(0o077)

    scenario = Path(args.scenario)
    if not scenario.is_file():
        fixture_fail(FIXTURE_EX_SCENARIO, f"the scenario file does not exist: {scenario}")
    import yaml  # noqa: PLC0415 - lazy, so this module imports without it

    try:
        #  THE SHARED DUPLICATE-REJECTING LOADER: a shadowed
        #  `seed_records` or `seed_files` key would build a fixture from data the
        #  definition does not appear to declare. Resolved BY PATH through the loader
        #  this module already uses for `scenario_tables`, so there is one route to the
        #  parser and no `sys.path` mutation.
        document = _load_scenario_yaml_module().load_scenario_yaml(
            scenario.read_text(encoding="utf-8")
        )
    except (OSError, yaml.YAMLError) as exc:
        fixture_fail(FIXTURE_EX_SCENARIO, f"{scenario} could not be parsed: {exc}")
    if not isinstance(document, dict):
        fixture_fail(FIXTURE_EX_SCENARIO, f"{scenario} does not hold a YAML mapping at the top level.")

    declared = document.get("seed_files") or document.get("seed-files")
    if not isinstance(declared, list) or not declared:
        fixture_fail(
            FIXTURE_EX_SCENARIO,
            f"{scenario} declares no seed_files, so there is nothing to build.",
        )
    unknown = [n for n in declared if n not in SEED_FILES]
    if unknown:
        fixture_fail(
            FIXTURE_EX_SCENARIO,
            f"the scenario declares seed file(s) this builder does not know: {unknown}",
            "The known set is exactly the files the twenty in-scope loaders read:",
            ", ".join(sorted(SEED_FILES)),
        )

    repo = Path(args.repo).resolve()
    if not (repo / "copybooks").is_dir():
        fixture_fail(FIXTURE_EX_PRECONDITION, f"{repo} does not look like the checkout: no copybooks/")

    if args.list_fields is not None:
        wanted = (
            list(declared)
            if args.list_fields.upper() == "ALL"
            else [args.list_fields]
        )
        for name in wanted:
            if name not in SEED_FILES:
                fixture_fail(FIXTURE_EX_USAGE, f"{name} is not one of the seed files this tool knows.")
            report_fields(repo, name)
        return EX_OK

    if args.out is None:
        parser.error("--out is required unless --list-fields is given")
    out = Path(args.out)
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fixture_fail(FIXTURE_EX_PRECONDITION, f"the output directory could not be created: {exc}")
    resolved_out = out.resolve()
    if resolved_out == repo or str(resolved_out).startswith(f"{repo}{os.sep}"):
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            f"the output directory {resolved_out} is inside the frozen checkout.",
            "The checkout is read-only specification and nothing here may write to it.",
        )

    # CHECKED HERE AS WELL AS AT EVERY INTERPOLATION SITE, and the difference is
    # which failure the operator gets. Each seed file's path is derived from this
    # directory and lands in a COBOL literal in source this tool compiles and runs, so
    # `cobol_path_literal' refuses a quote, a control character or an over-long path
    # at each site. That refusal names a generated line; this one names `--out', which
    # is what the operator actually typed. The longest file name adds to the length,
    # so the budget is measured against the worst case rather than the directory.
    longest = max(len(name) for name in SEED_FILES)
    cobol_path_literal(
        f"{resolved_out}{os.sep}{'x' * longest}",
        what="the --out directory, plus the longest seed file name it will hold,",
    )

    if shutil.which("cobc") is None:
        fixture_fail(
            FIXTURE_EX_PRECONDITION,
            "cobc is not on the PATH.",
            "Fifteen of the seventeen seed files are ORGANIZATION INDEXED or RELATIVE,",
            "so GnuCOBOL itself has to write them. Run this inside the harness image.",
        )

    work = Path(args.work) if args.work else resolved_out / ".build"
    try:
        work.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fixture_fail(FIXTURE_EX_PRECONDITION, f"the work directory could not be created: {exc}")
    assert_work_directory(work, repo=repo, out=resolved_out, explicit=bool(args.work))

    modules_dir: Path | None = None
    candidate = Path(args.modules) / "common"
    if candidate.is_dir():
        modules_dir = candidate

    env = dict(os.environ)
    env.setdefault("COB_EXIT_WAIT", "off")
    # An indexed file GnuCOBOL creates alongside a stale one of a different shape is a
    # confusing failure, so anything this build would write is removed first.
    for name in declared:
        for stale in resolved_out.glob(f"{name}*"):
            if stale.is_file():
                stale.unlink()

    if not args.quiet:
        sys.stdout.write(
            f"harness/dump_tables.py --make-fixtures: building {len(declared)} file(s) for "
            f"{document.get('name', scenario.stem)} into {resolved_out}\n"
        )
    total = 0
    for name in declared:
        total += build_one(
            name=name,
            document=document,
            out=resolved_out,
            work=work,
            repo=repo,
            env=env,
            modules=modules_dir,
            verbose=not args.quiet,
        )
    if not args.quiet:
        sys.stdout.write(
            f"{FIXTURE_PROG}: built {len(declared)} file(s), {total} record(s) in "
            f"total, every one read back through the frozen definitions\n"
        )
    return EX_OK


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    `allow_abbrev=False` so that `--out` and `--out-dir` can never be confused with one
    another, and so no abbreviation of any option is silently accepted.

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
            "Stages 3 and 7 of the ten-stage parity protocol."
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
            "--scenario. It selects the <scenario>/<side>/ path AND is recorded "
            "in the manifest, where the run attestation is matched against it; "
            "the manifests themselves are never compared, so recording it "
            "cannot affect a verdict."
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
            "ten-stage recipe in harness/docker-compose.yml uses. "
            "Cannot be combined with --scenario, --side or --out-dir."
        ),
    )

    #  THE MUTUALLY EXCLUSIVE GROUP HOLDS THE TWO REAL SELECTORS ONLY.
    #  `--scenario-file` is deliberately NOT here too: that would make it impossible to name the
    #  scenario definition alongside the protocol's own `--all-in-scope` bound - and
    #  the definition's digest is a provenance field harness/diff_states.py REQUIRES
    #  on both sides. See `resolve_tables` for the whole of that story.
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--tables",
        metavar="TABLE[,TABLE...]",
        help=(
            "the explicit table list, comma separated, spelled exactly as "
            "mysql/ACASDB.sql spells it, hyphens included."
        ),
    )
    parser.add_argument(
        "--scenario-file",
        metavar="PATH",
        help=(
            "the scenario definition this capture belongs to. ALWAYS recorded "
            "as provenance -- its sha256 becomes scenario_file_sha256, which "
            "harness/diff_states.py requires to be present and equal on both "
            "sides before it compares a single row, because the definition "
            "carries the fan-out switch that decides which tables a run "
            "touches. It additionally SELECTS the declared affected_tables "
            "when no other selector is given, which NARROWS the capture and is "
            "useful while debugging one table but is NOT the protocol: a "
            "capture bounded by the declared effect cannot show a difference "
            "in a table the scenario did not expect to move. Pass it together "
            "with --all-in-scope for evidence -- the bound is then all 22 and "
            "the definition is still named."
        ),
    )
    selection.add_argument(
        "--all-in-scope",
        action="store_true",
        help=(
            "THE PROTOCOL. Dumps all 22 in-scope tables, whatever the "
            "scenario declares it affects. Both cycles now perform the menu's "
            "own persistence - `overrewrite.` [general/general.cbl:L656-L672] "
            "rewrites SYSTEM-REC under key 1, SYSDEFLT-REC under key 2 and "
            "SYSTOT-REC under key 4, and acas_posting/cli/args.py::overrewrite "
            "reproduces it - so those rows are comparable rather than a source "
            "of false failure, and a capture that omitted them could report an "
            "empty diff while the run date, the allocators, the flags, the "
            "defaults or the period totals differed."
        ),
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the per-table progress notes on stderr.",
    )

    return parser


def _assert_output_writable(
    destination: Path, env: Mapping[str, str]
) -> None:
    """Assert the dump tree may be written where it was asked to go.

    Inside-out - the destination lies at or under the checkout - is the obvious one.

    Args:
        destination: The directory the `<TABLE>.json` files land in.
        env: The environment, for `$ACAS_REPO`.

    Raises:
        DumpPathError: The destination overlaps the read-only checkout in either
            direction.
    """
    repository = env.get(_ENV_REPO)
    if not repository:
        return
    root = Path(repository).resolve()
    resolved = destination.resolve()

    if resolved == root or root in resolved.parents:
        raise DumpPathError(
            f"the dump tree {destination} resolves to {resolved}, which is "
            f"inside the read-only checkout {root} (${_ENV_REPO}). Nothing "
            f"may be written there: it holds the frozen COBOL, the bridges "
            f"and mysql/ACASDB.sql, and Agent Action Plan section 0.8.1 "
            f"calls any diff touching those paths \"a defect in the "
            f"migration, regardless of how harmless it appears\". Write "
            f"under ${_ENV_OUT} instead."
        )

    if resolved in root.parents:
        raise DumpPathError(
            f"the dump tree {destination} resolves to {resolved}, which "
            f"CONTAINS the read-only checkout {root} (${_ENV_REPO}). "
            f"Publishing a tree removes every stale *.json from its "
            f"destination first, so a destination that contains the "
            f"checkout would delete files out of it. Name the leaf "
            f"directory the dumps belong in, for example "
            f"${_ENV_OUT}/<scenario>/cobol."
        )


def _resolve_output(
    arguments: argparse.Namespace,
    env: Mapping[str, str],
) -> tuple[Path, str | None, str | None]:
    """Work out where the dumps go.

    Args:
        arguments: The parsed command line.
        env: The environment, for `$ACAS_OUT`.

    Returns:
        The output root, the scenario name and the side. The last two are `None` for the
            `--out DIR` layout.

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
                f"`--out DIR`, as harness/docker-compose.yml does, or "
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
            f"unknown. The Compose service sets {_ENV_OUT}: /out itself; see "
            f"harness/docker-compose.yml."
        )
    return Path(root), arguments.scenario, arguments.side


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return an exit code.

    Never calls `sys.exit`, so a test can drive it in process and inspect the code.

    Args:
        argv: The arguments.

    Returns:
        `EX_OK` on success, or one of `EX_USAGE`, `EX_PRECONDITION`, `EX_DATABASE`,
            `EX_SCOPE`, `EX_DRIFT`, `EX_NUMERIC`, `EX_WRITE`, `EX_TIMEOUT`.
    """
    global _QUIET

    #  THE FINGERPRINT MODE IS DISPATCHED BEFORE THE DUMP PARSER EXISTS. It has its own
    #  parser, its own three-code status band and its own positional table list, and it
    #  resolves no output directory - see `_extract_digest_mode` for why the flag is
    #  pre-scanned rather than declared.
    raw = list(sys.argv[1:] if argv is None else argv)
    requested_digest, remaining = _extract_mode(raw, DIGEST_MODE_FLAG)
    if requested_digest:
        return table_digest_main(remaining)

    #  THE FIXTURE BUILDER IS DISPATCHED THE SAME WAY, and its refusals raise
    #  `SystemExit` from `fixture_fail` - the one refusal shape it has always had, and
    #  the shape its tests assert. Converted to a return value here so that this
    #  function keeps its own no-`sys.exit` contract for an in-process caller.
    requested_fixtures, remaining = _extract_mode(raw, FIXTURE_MODE_FLAG)
    if requested_fixtures:
        try:
            return make_fixtures_main(remaining)
        except SystemExit as request:
            return int(request.code or FIXTURE_EX_OK_FALLBACK)

    parser = build_parser()
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 for --help and --version and 2 for a usage error.
        code = exc.code
        if code is None or code == 0:
            return EX_OK
        return EX_USAGE

    _QUIET = bool(arguments.quiet)
    env: Mapping[str, str] = os.environ

    # Tightened HERE and not at import time.
    os.umask(_OUTPUT_UMASK)

    try:
        out, scenario, side = _resolve_output(arguments, env)
    except ValueError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_USAGE

    selector = _selector_name(arguments)
    if selector is None:
        # REFUSED, not warned about.
        print(
            "harness/dump_tables.py: no table selector was given, so the "
            "scope of this dump is undefined. Choose one:\n"
            "  --all-in-scope                                      "
            "THE PROTOCOL; all 22 in-scope tables\n"
            "  --scenario-file <scenario>.yaml                     "
            "narrow to the scenario's declared affected_tables, for "
            "debugging\n"
            "  --tables TABLE[,TABLE...]                           "
            "an explicit list, for narrowing one table by hand\n"
            "An unbounded run is refused rather than defaulted because "
            "evidence whose scope is implicit is not evidence (rule R-6). "
            "Use --all-in-scope for evidence: `overrewrite.` "
            "[general/general.cbl:L656-L672] rewrites SYSTEM-REC under key 1, "
            "SYSDEFLT-REC under key 2 and SYSTOT-REC under key 4, and "
            "acas_posting/cli/args.py::overrewrite reproduces it, so a capture "
            "that omitted those rows could report an empty diff while the run "
            "date, the allocators, the flags, the defaults or the period "
            "totals differed.",
            file=sys.stderr,
        )
        return EX_USAGE

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

    try:
        destination = dump_path(
            out, tables[0], scenario=scenario, side=side
        ).parent
    except ValueError as exc:
        # The layout rules live in `dump_path`, and this is the one call that reaches
        # them from outside the guarded block above. Left uncaught it escaped as a
        # traceback with status 1 -- outside this tool's documented codes, and printing
        # internal file and line detail -- for an input the sibling tools refuse
        # cleanly. It is a usage error, and it says so.
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_USAGE
    try:
        _assert_output_writable(destination, env)
    except DumpPathError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_WRITE

    # WHAT THE RUN STAGE CLAIMED, read BEFORE the database is touched so that the
    # answer is on the record whether or not the dump goes on to succeed. A refusal is
    # not fatal here: it is recorded in the manifest and `diff_states.py` enforces it,
    # because the operator dumping a failed run needs the capture to inspect and only
    # the VERDICT has to fail closed.
    attestation = read_run_attestation(
        out if (scenario is not None and side is not None) else None,
        scenario,
        side,
    )

    # PROVENANCE, ASSEMBLED HERE AND CARRIED THROUGH EVERY STAGE.
    # The run id comes from the attestation when the runner published one -- so the
    # capture names the attempt whose run it actually attests -- and from the
    # environment otherwise, which is the case for a dump taken by hand.
    provenance = build_provenance(
        run_id=attestation.get("run_id") or env.get("ACAS_PARITY_RUN_ID") or None,
        scenario_file=arguments.scenario_file,
        repository=env.get(_ENV_REPO),
        command=list(argv if argv is not None else sys.argv[1:]),
    )
    _progress(
        "harness/dump_tables.py: provenance - run id "
        f"{provenance['run_id'] or '<none>'}, scenario file digest "
        f"{(provenance['scenario_file_sha256'] or '<none>')[:16]}, frozen schema "
        f"digest {(provenance['frozen_schema_sha256'] or '<none>')[:16]}"
    )
    if attestation["attested"]:
        _progress(
            f"harness/dump_tables.py: run attestation OK - "
            f"{attestation['source']} records status 0 for {side}/{scenario}"
        )
    else:
        _progress(
            f"harness/dump_tables.py: NOT ATTESTED - {attestation['detail']} "
            f"The capture is still written, and it carries that refusal: "
            f"harness/diff_states.py will not render a verdict on it without "
            f"--allow-unattested."
        )

    try:
        settings = connection_settings(env)
    except ConnectionConfigError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_PRECONDITION

    _progress(
        f"harness/dump_tables.py: SELECT * ORDER BY primary key for "
        f"{len(tables)} table(s) over a "
        f"{settings.transport_category()} connection"
    )

    try:
        with connect(settings) as connection:
            schema = _schema_name(connection)
            # EVERY table is captured before ANY of it is published.
            captured: dict[str, Mapping[str, Any]] = {}
            total_rows = 0
            for table in tables:
                dump = dump_table(connection, table, schema=schema)
                captured[table] = dump
                total_rows += int(dump["row_count"])
                _progress(
                    f"  {table:<24} {dump['row_count']:>7} row(s)  "
                    f"{len(dump['columns']):>3} column(s)  captured"
                )
            written = list(
                publish_dumps(
                    captured,
                    out,
                    scenario=scenario,
                    side=side,
                    selector=selector,
                    provenance=provenance,
                    attestation=attestation,
                )
            )
    except DumpTimeoutError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_TIMEOUT
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
    except (DumpWriteError, DumpPathError) as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_WRITE
    except ValueError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_USAGE
    except DumpError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_DATABASE

    _progress(
        f"harness/dump_tables.py: published {len(tables)} table(s), "
        f"{total_rows} row(s) in total, into {destination} - "
        f"{len(written)} file(s) including {MANIFEST_FILENAME}, which is "
        f"written last and is what marks the set complete"
    )
    return EX_OK


def _selector_name(arguments: argparse.Namespace) -> str | None:
    """Name which table selector the command line used.

    Args:
        arguments: The parsed command line.

    Returns:
        The selector's manifest vocabulary word, or None when no selector was given at
            all - which `main` refuses.

    The order matches `resolve_tables`: a real selector wins, and `--scenario-file`
    names the selector only when it was the one that chose the list. Recording
    `scenario-file` for a capture actually bounded by all 22 tables would misdescribe
    the capture's scope, which is the one thing the manifest exists to state.
    """
    if arguments.tables is not None:
        return SELECTOR_TABLES
    if arguments.all_in_scope:
        return SELECTOR_ALL_IN_SCOPE
    if arguments.scenario_file is not None:
        return SELECTOR_SCENARIO_FILE
    return None


if __name__ == "__main__":
    raise SystemExit(main())
