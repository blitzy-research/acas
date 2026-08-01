#!/usr/bin/env python3
"""Canonicalise a dump so that only REAL behavioural differences survive.

Stage 4 of the eight-stage parity protocol, and its counterpart after
stage 7. Agent Action Plan section 0.3.2 fixes the stage order - "seed,
run, dump, normalize, reset, run, dump, diff" - and this module is both
normalisations. Its whole mandate is one line of the plan's
transformation map, section 0.4.1.7: "Canonicalises fixed-char trailing
spaces, decimal scale rendering, and the two-digit versus four-digit date
text forms".

    [harness/docker-compose.yml:L44-L51]  the eight stages, in order
    [harness/docker-compose.yml:L269]     stage 4, the COBOL-side pass
    [harness/docker-compose.yml:L273]     stage 8's input, the Python pass

    stage 1  seed        harness/seed.sh          (COBOL *LD loaders)
    stage 2  run  COBOL  harness/run_cobol_scenario.sh
    stage 3  dump        harness/dump_tables.py   -> $ACAS_OUT/.../cobol
    stage 4  normalize   THIS MODULE              -> ....../cobol.norm
    stage 5  reset       harness/reset_db.sh      (+ re-seed)
    stage 6  run  Python harness/run_python_scenario.sh
    stage 7  dump        harness/dump_tables.py   -> $ACAS_OUT/.../python
    stage 4' normalize   THIS MODULE              -> ....../python.norm
    stage 8  diff        harness/diff_states.py   -> MUST be EMPTY

It reads one directory of `<TABLE>.json` files, as `dump_tables.py` wrote
them, and writes one directory of `<TABLE>.json` files with the same
shape and only the VALUES canonicalised. It opens no database link, needs
no driver, invokes no COBOL and imports nothing from the shipped Python
package.

THE ONE SENTENCE THAT DEFINES THIS MODULE - AND ITS HARD LIMIT
==============================================================
Agent Action Plan section 0.6.6, verbatim:

    "a non-empty diff is always a real behavioral difference and never an
    artefact of the comparison."

That sentence cuts BOTH ways, and the second direction is the trap.

  FORWARD.  Representation artefacts - driver formatting, character
  padding, decimal scale rendering - must be canonicalised away, or a
  FALSE failure appears and a correct migration looks broken.

  BACKWARD, AND EQUALLY BINDING.  This module must NEVER make two
  genuinely different stored values compare equal. A normaliser that
  "helpfully" folded `21/09/20` and `21/09/2025` into one token, or
  rounded `1234.5600` to `1234.56` because the column declares two
  places, or trimmed a value one side stored padded and the other stored
  short, would hide a REAL behavioural difference and silently defeat the
  whole engagement.

Every transformation here is therefore:

  1. ALLOW-LISTED BY COLUMN or driven by the column's DECLARED TYPE -
     never by a heuristic and never by what a value happens to look like.
  2. DERIVED FROM THE FROZEN SCHEMA `mysql/ACASDB.sql`, which is the
     specification rather than a view of it.
  3. IDEMPOTENT - normalising a normalised dump changes nothing.
  4. CITED, so a reader can go to the finding that motivates it (R-5).
  5. EXACTLY ONE OF THE THREE JOBS BELOW. There are THREE and there is no
     fourth. Not case folding, not whitespace collapsing inside a value,
     not NULL coalescing, not row re-ordering, not key remapping, not
     sign normalisation. Any fourth transformation is one more place a
     real difference could hide.

JOB 1 - TRAILING SPACES IN FIXED-WIDTH CHARACTER COLUMNS
========================================================
Applied to every column the frozen schema declares `char(n)`, for all n
including 1: the trailing ASCII space `U+0020` is removed and nothing
else is.

THE FINDING.  Agent Action Plan section 0.6.2's width drift, verified end
to end in this checkout:

    [copybooks/wsledger.cob:L27]  03  Ledger-Name pic x(24).        24
    [common/nominalMT.cbl:L299]   05  HV-LEDGER-NAME PIC X(32).     32
    [mysql/ACASDB.sql:L127]       `LEDGER-NAME` char(32) NOT NULL,  32

Section 0.6.2, verbatim: "The value is not corrupted, but the padding
differs, and padding is visible in a table dump - which is why the dump
normaliser must canonicalise fixed-character trailing spaces rather than
compare raw bytes."

THE FINDING BEYOND THE PLAN, and the reason this job is mandatory rather
than decorative: THE BRIDGE TRIMS TRAILING SPACES as it builds the SQL
text, so the COBOL side stores character columns TRIMMED while a Python
data-access layer writing the padded record field could store them
PADDED.

    [common/nominalMT.cbl:L1065-L1067]
        STRING '`LEDGER-NAME`="' INTO WS-MYSQL-COMMAND ...
        STRING FUNCTION TRIM (HV-LEDGER-NAME,TRAILING) ...

That is not one stray call. Measured in this checkout: 23 `FUNCTION TRIM`
sites in `common/nominalMT.cbl`, 29 in `common/glpostingMT.cbl`, 27 in
`common/irspostingMT.cbl`, 75 in `common/salesMT.cbl` and 339 in
`common/systemMT.cbl`. The bridge trims system-wide. Whether the
difference is even observable then depends on the server's
`PAD_CHAR_TO_FULL_LENGTH` mode, which `harness/Dockerfile.mariadb`
deliberately leaves unset for exactly this reason. Without job 1 that
purely representational difference would fail every scenario.

TRAILING ONLY, NEVER LEADING.  A COBOL alphanumeric `MOVE` is
left-justified with RIGHT padding, so a leading space is CONTENT, not
padding. A two-sided or leading-side removal would be a bug, and only the
ASCII space is removed - never a tab, a NUL, a carriage return, a newline
or any other Unicode whitespace, because any of those in a `char` column
is real content or a genuine defect worth seeing.

Scale of the job, measured: the schema declares 238 `char(...)` columns
and ZERO `varchar(...)`; 177 of the 238 are in scope.

JOB 2 - DECIMAL SCALE RENDERING
===============================
Applied to every column the frozen schema declares `decimal(p,s)`: the
value is parsed as an exact `decimal.Decimal` FROM ITS STRING and
re-rendered at exactly the column's declared scale `s`.

THE FINDING.  Agent Action Plan section 0.6.6: "canonicalise decimal
scale rendering so that a value stored at two decimal places compares
equal regardless of driver formatting."

THE SCALE IS NOT UNIFORMLY 2.  Measured over the frozen schema: 68 x
decimal(9,2), 57 x decimal(10,2), 17 x decimal(4,2), 12 x decimal(5,2),
4 x decimal(14,2), 2 x decimal(2,0), 2 x decimal(14,4) and one each of
decimal(6,2), decimal(5,0), decimal(11,4), decimal(11,2) and
decimal(10,4). In scope: 55 x decimal(10,2), 44 x decimal(9,2), 15 x
decimal(4,2), 8 x decimal(5,2), 4 x decimal(14,2), 1 x decimal(6,2) and
1 x decimal(5,0) - so a ZERO scale is in scope even though a `,4` scale
is not. The declared scale is always read from the schema; two places are
never assumed.

THE INFORMATION-LOSS GUARD.  If a value's own exponent implies MORE
decimal digits than the column declares, that is not a rendering
artefact - it means one side stored something the column cannot hold,
which is a REAL finding. `DecimalScaleError` is raised rather than
quantising it away, because quantising would be exactly the "make two
different values compare equal" failure the hard limit above forbids.
A value read back from a `DECIMAL(p,s)` column always has exponent `-s`,
so the guard should never fire - which is why its firing is worth an
error rather than a warning.

JOB 3 - THE TWO-DIGIT VERSUS FOUR-DIGIT DATE TEXT FORMS
=======================================================
Applied to FIVE allow-listed columns and to nothing else. It validates
the value against the canonical shape and re-renders it from its parsed
components; anything that does not match the shape is passed through
UNCHANGED and REPORTED.

THE FINDING.  Agent Action Plan section 0.6.6: "canonicalise the
two-digit versus four-digit date text forms that the schema stores side
by side."

    [mysql/ACASDB.sql:L158]   `POST-DAT` char(8)            date text
    [mysql/ACASDB.sql:L277]   `POST4-DAT` char(8)           date text
    [mysql/ACASDB.sql:L369]   `IRS-POST-DAT` char(8)        date text
    [mysql/ACASDB.sql:L981]   `SALES-STATS-DATE` char(4)    period text
    [mysql/ACASDB.sql:L1236]  `STATS-DATE-PERIOD` char(4)   period text

`char(8)` DOES NOT MEAN "DATE", and that is precisely why this job is an
explicit column allow-list and never a width or content heuristic. The
schema declares six `char(8)` columns; `PUITM5-REC`.`OI5-BATCH` and
`SAITM3-REC`.`OI3-BATCH` are BATCH REFERENCES, proven by the copybook -
[copybooks/slwsoi.cob:L16-L18] declares `03 OI-Batch comp.` over
`05 OI-B-Nos pic 9(5).` and `05 OI-B-Item pic 999.`, five digits plus
three - and the schema itself labels their component columns
`COMMENT 'Batch content'` [mysql/ACASDB.sql:L902-L903]. `char(4)` does
not mean "period" either: `PURCH-EXT`, `SALES-EXT` and `PASS-WORD` are
char(4) and are not periods. Every deliberate exclusion is listed in
`DATE_TEXT_EXCLUSIONS` below with its reason and locator (R-5).

ALMOST EVERY OTHER IN-SCOPE DATE IS A BINARY DAY-NUMBER INTEGER, not
text, and job 3 must not go near it: `SYSTEM-REC`.`RUN-DAT`,
`START-DAT`, `END-DAT`, `S-END-CYCLE-DAT`, `BL-END-CYCLE-DAT`,
`GLBATCH-REC`.`ENTERED` / `PROOFED` / `POSTED` / `STORED`, both
`IH-DAT`, `OI3-DAT`, `OI3-DATE-CLEARED`, `OI5-DAT`,
`OI5-DATE-CLEARED`, `SALES-CREATE-DAT` and `PURCH-CREATE-DAT`. They are
exact integers with nothing to canonicalise. `RUN-DAT`
[mysql/ACASDB.sql:L1199] is the `Run-Date binary-long` of
[copybooks/wssystem.cob:L67] - the pinned-clock observable, and
genuinely diff-visible.

THE EIGHT-CHARACTER LAYOUT, verified:

    [copybooks/wspost.cob:L18]  03  Post-Date pic x(8).

    [common/irspostingMT.cbl:L982-L987], with the maintainer's own
    comment at L978-L980 ("... and yes they all should be numeric as a
    date is present but JIC (just in case)."):
        if       Post-Date (1:2) numeric
                 move     Post-Date (1:2) to HV-POST4-DAY.
        if       Post-Date (4:2) numeric
                 move     Post-Date (4:2) to HV-POST4-MONTH.
        if       Post-Date (7:2) numeric
                 move     Post-Date (7:2) to HV-POST4-YEAR.

Slices at (1:2), (4:2) and (7:2) of an eight-character field put the
separators at 3 and 6: the layout is `NN/NN/NN`.

AN AMBIGUITY THIS MODULE DOES NOT RESOLVE - AND DOES NOT NEED TO.
The linkage date is `to-day pic x(10)` in DD/MM/CCYY form. A COBOL
alphanumeric `MOVE` from `x(10)` to `x(8)` is left-justified and
truncated on the right, which would yield DD/MM/CC - making (7:2) the
CENTURY. Two in-scope programs instead build the field with two partial
moves,

    [sales/sl060.cbl:L1071-L1072]  and  [purchase/pl060.cbl:L937-L938]
        move     u-date (1:6) to post-date (1:6).
        move     u-date (9:2) to post-date (7:2).

which takes `DD/MM/` verbatim and the LAST TWO digits of CCYY, making
(7:2) the YEAR. Rule R-6 governs: the question is arbitrated by running
the compiled oracle and the answer is recorded in
`docs/migration/ambiguity-resolutions.md`. NOTHING HERE DEPENDS ON THE
ANSWER, because job 3 never expands a two-digit component to four and
never contracts four to two. It canonicalises RENDERING and reports
everything else.

The evidence does settle one thing that matters here: `/` is the only
separator the in-scope write paths can produce, since `u-date (1:6)` is
copied verbatim. So `/` is the canonical separator, and a value carrying
`-`, `.` or `,` instead is REAL information - reported, never rewritten.
Widening the recogniser to fold those into `/` could collapse a genuine
divergence between the two sides, which the hard limit forbids.

The period columns are `pic 9(4)` in the copybooks -
[copybooks/wssystem.cob:L145] `05 Stats-Date-Period pic 9(4).` and
[copybooks/wssl.cob:L64] `03 Sales-Stats-Date pic 9(4).` - carried in
`PIC X(4)` host variables [common/systemMT.cbl:L373],
[common/salesMT.cbl:L320] and trimmed into the SQL
[common/systemMT.cbl:L2001-L2003]. Their canonical shape is therefore
exactly four ASCII digits.

Because both canonical shapes are EXACT, re-rendering a canonical value
reproduces it byte for byte. That fixed point is deliberate: any looser
recogniser would risk equating values that genuinely differ. Job 3's
real product is the REPORT it emits for everything that does not match,
so an operator takes the question to the oracle rather than to a
normaliser tweak.

WHAT JOB 3 MUST NOT DO - THE CHARSET CAVEAT STAYS
=================================================
[mysql/ACASDB.sql:L9-L11], verbatim:

    --  THERE IS NOT ANY DATA RECORDS PRESENT HERE --
    --   YOU MAY NEED TO CHANGE the defined Character set in all tables
    --   TO MATCH ANY OF YOUR REQUIREMENTS IF THEY DIFFER

The dump sets `SET NAMES utf8mb4` at [mysql/ACASDB.sql:L16] while all 33
tables declare `utf8mb3` / `utf8mb3_general_ci`. That inconsistency is
frozen specification. No value is ever re-encoded, transliterated,
Unicode-normalised or case-folded to "fix" it (R-4).

THE RULES CITED BELOW BY NUMBER
===============================
This project ships NO separate rules document - `review_rules` reports
"No user rules provided.", confirmed by a full read. The six binding
rules R-1 to R-6 are the Agent Action Plan's own, section 0.7.2, and each
section below names the one it satisfies. Where the plan is silent,
ordinary enterprise practice applies; nothing here is invented.

NUMERIC POLICY  (rule R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport. Agent
Action Plan section 0.5.1 extends the prohibition to this exact file,
naming the two dataframe and array libraries it excludes outright and
adding, verbatim: "This exclusion is absolute, including for the harness
dump comparison, which uses ordered row sequences rather than
dataframes." Neither library is imported here, for any reason, and
neither is in `requirements.txt`.

  * `Decimal` is only ever built FROM A STRING, so no value passes
    through a binary approximation on the way in.
  * A decimal value ARRIVES as a JSON string and LEAVES as a JSON
    string. JSON numbers are IEEE-754 doubles in every consumer, so
    writing a decimal as a JSON number would reintroduce binary floating
    point at the file boundary. Integers stay JSON integers, exact for
    every integer width the schema uses.
  * THE ACTIVE GUARD. A binary value for a `decimal` column raises
    `NumericPolicyError` naming the table, the column and the value. It
    is never coerced: a value like that means `dump_tables.py` was
    misconfigured, and quietly repairing it here would hide that bug.
    The same guard covers every other column class, so the policy is
    structural rather than incidental.
  * Only exact operations are used - `quantize` with an explicit
    rounding mode and an explicit `Context`, and `format(value, "f")`
    for rendering so exponent notation can never appear. There is no
    binary conversion, no `%` formatting of a binary number and no
    reliance on the caller's ambient decimal context.

The schema supports all of this: it declares ZERO `float`, `double` and
`real` columns. Its numeric census is 167 `decimal`, 151 `int`, 116
`tinyint`, 23 `mediumint`, 22 `smallint` and 3 `bigint`; in scope, 128
`decimal`, 65 `int`, 99 `tinyint`, 21 `mediumint`, 20 `smallint` and 3
`bigint`. 177 character columns plus 128 decimal plus 208 integer is the
513 in-scope columns exactly.

NO COBOL AT RUNTIME, AND NO COUPLING TO THE SHIPPED PACKAGE  (rule R-1)
=======================================================================
`harness/` is the compiled-COBOL oracle tree and a SIBLING of the shipped
Python package. Agent Action Plan section 0.3.1 annotates it "the
compiled oracle; NEVER on the package import path" and states the
guarantee that there is no import path from the shipped package to
`harness`. `pyproject.toml` makes that structural by excluding
`harness*` from the packaged distribution.

  * THERE IS NO `harness/__init__.py` AND THERE MUST NEVER BE ONE. This
    is a plain module invoked BY PATH, and it is on `sys.path` only for
    the duration of its own run.
  * The shipped package is NOT imported here, in any form - not its
    data-access layer, not its record layouts, not its dictionary
    loader - and neither is the generated data-dictionary JSON.
    Deriving field metadata from the migrated package would make the
    oracle depend on the very thing it exists to arbitrate, a
    circularity that destroys the comparison's independence. The frozen
    `mysql/ACASDB.sql` is parsed instead, which additionally means this
    module runs offline, in unit tests, with the Compose stack down and
    with the package not installed at all.
  * No COBOL is invoked, no `cobc` is shelled out to, no compiled module
    is loaded and no child process is started.
  * Imports are confined to the standard library, which is inside the
    permission Agent Action Plan section 0.4.3 grants `harness/*`. No
    database driver and no SQL toolkit is imported - none is needed,
    because this module is pure file-to-file. No JSON-schema validator
    library is imported either: none is in `requirements.txt`.

NO SCHEMA CHANGE, STRICTLY SEQUENTIAL  (rule R-3)
=================================================
Agent Action Plan section 0.2.2 forbids "new tables, columns, indexes,
constraints, views, triggers or DDL statements", and separately forbids
concurrency of every kind - threads, event loops, subprocess pools and
pooled database links are each named there - requiring instead that
execution be strictly sequential.

  * This module issues NO SQL AT ALL and opens no database link. It
    reads JSON files and the frozen schema text, and writes JSON files.
  * ONE table at a time, in a plain loop. There is no thread, no event
    loop, no process pool and no synchronisation primitive anywhere in
    this file.
  * It writes nothing under `$ACAS_REPO`, which the Compose file mounts
    read-only [harness/docker-compose.yml:L591] to keep the frozen
    artifact guarantee of section 0.8.1 structural. The frozen schema is
    READ here, never written.
  * It adds no validation of the DATA. The structural assertions check
    the DUMP SHAPE and the SCHEMA - keys, order, counts, types - never a
    row's business content.

ANOMALIES ARE REPRODUCED, NEVER REPAIRED  (rule R-4)
====================================================
Agent Action Plan section 0.8.2, preserving the user's own requirement:
"A defect reproduced is correct; a defect fixed is a failure."

The clearest case is the plan's anomaly 7. `IRSPOSTING-REC` carries three
columns that exist in NO copybook - `POST4-DAY`, `POST4-MONTH` and
`POST4-YEAR` - because the bridge derives them from two-character slices
of a date string under a guard [common/irspostingMT.cbl:L982-L987]. When
the guard does not hold the slices are simply not moved, so the
components keep the zero left by the group `INITIALIZE` while
`POST4-DAT` still holds the raw date text. The row is internally
inconsistent, and that is the specification: nothing here derives,
back-fills, cross-checks or repairs those three columns, and a
`POST4-DAT` of `21/09/25` beside three zero components survives
normalisation untouched.

Nor is any sign flipped, any leading zero in a numeric removed, any
charset harmonised, or any display-width quirk tidied - the
`int(1) unsigned` declaration of `BL-END-CYCLE-DAT`
[mysql/ACASDB.sql:L1270] is left exactly as the schema writes it.

DETERMINISM IS THE PRODUCT  (rule R-6)
======================================
Agent Action Plan section 0.8.5: "Two runs of the same scenario under the
same pinned clock produce byte-identical dumps, proven by
`tests/determinism/test_two_runs_byte_identical.py`."

NOT ONE BYTE OF NON-REPRODUCIBLE CONTENT MAY APPEAR IN A NORMALISED
FILE. There is no wall-clock reading, no host name, no process
identifier, no run identifier, no elapsed time, no absolute path, no
schema-file modification time and no tool version in the output; this
module reads no clock and no entropy source, and the only directory it
lists is sorted before use.

`normalize_dump` is a PURE function of `(dump, schema)`: it reads no
environment variable, opens no file, touches no global and depends on no
ambient decimal context, so it is deterministic and safely reusable.

Serialisation is pinned rather than left to a default, and matches
`dump_tables.py` byte for byte: `indent=2`, `ensure_ascii=True`,
`sort_keys=False`, `separators=(",", ": ")`, LF newlines, UTF-8, exactly
one trailing newline, and the five keys always in the same insertion
order. `ensure_ascii=True` is deliberate - it makes the bytes independent
of any locale or filesystem-encoding difference between the two runs, so
do not "improve" it. Each file is written to a temporary name in its own
directory and moved into place with `os.replace`, so
`harness/diff_states.py` can never read a partial file.

Only `<TABLE>.json` files are written into the destination directory - no
manifest, no log, no marker - because `dump_tables.py` records that
constraint for this module explicitly. Progress goes to stderr, and the
job 3 findings report goes OUTSIDE the compared trees.

THE PUBLIC API
==============
`tests/conftest.py` is specified to provide "the seed/dump/normalize/diff
helpers so that no test reimplements the comparison protocol" (Agent
Action Plan section 0.4.3), which means it imports this module and calls
these functions directly. They are a library first and a command second.

    load_schema              the column-type map, parsed from the frozen
                             `mysql/ACASDB.sql`
    schema_columns           one table's ordered column names
    column_type              one column's declared type
    canonicalise_char        job 1, on its own for testing
    canonicalise_decimal     job 2, on its own for testing
    canonicalise_date_text   job 3, on its own for testing
    normalize_dump           the pure, shape-preserving normalisation
    read_dump / write_dump   the JSON boundary, deterministic and atomic
    normalize_tree           one directory to another, sequentially
    render_report            the job 3 findings, deterministically
    default_schema_path      `$ACAS_REPO/mysql/ACASDB.sql`
    build_parser / main      the command line; `main` RETURNS a code

`main` returns an exit status and never calls `sys.exit`, so a caller can
drive it in-process. The module guard raises `SystemExit(main())`.

COMMAND LINE
============
Two flag spellings are accepted for the source and destination, because
this repository documents two and neither is a guess. The committed
Compose file publishes, verbatim:

    harness/normalize.py --in /out/cobol  --out /out/cobol.norm
    harness/normalize.py --in /out/python --out /out/python.norm

while the file specification for this module names `--src` and `--dst`
with a `.normalized` default suffix and the composed
`<out-dir>/<scenario>/<side>/` layout. `--in` and `--src` are the same
option; so are `--out` and `--dst`. Abbreviation is disabled, so `--out`
can never be confused with `--out-dir`.

EXIT CODES
==========
Deliberately the same 80+ band the sibling harness tools use, so an
operator reading a pipeline log sees one family.

    0   every requested table was normalised and written
    80  usage - bad or contradictory command line
    81  precondition - a missing directory, or an unreadable schema
    83  scope - an out-of-scope or unknown table was present
    84  drift - a structural assertion against the frozen schema failed
    85  numeric - the R-2 value guard tripped, or a NULL was present
    86  write - an output file could not be written

82 is database, and is deliberately never returned: this module opens no
database link.

FURTHER READING
===============
    mysql/ACASDB.sql             the frozen schema; the source of every
                                 column type this module applies
    harness/dump_tables.py       the dump contract this module consumes
    harness/diff_states.py       the comparison; empty is the pass
    harness/docker-compose.yml   the eight stages and the environment
    harness/reset_db.sh          the same invariants from the database
                                 side
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Mapping, MutableSequence, Sequence
from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Final

# ---------------------------------------------------------------------------
#  THE FROZEN-SCHEMA INVENTORY  (rule R-5)
#
#  One entry per in-scope table: its single-column primary key, its declared
#  column count and the `CREATE TABLE` line of mysql/ACASDB.sql it was read
#  from. The same twenty-two triples appear independently at
#  [harness/dump_tables.py:L479-L502] and [harness/reset_db.sh:L248-L271];
#  all three were verified against the schema, and `load_schema` re-checks
#  every count on every run so the map cannot silently drift.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TableSpec:
    """One in-scope table's frozen-schema facts.

    Attributes:
        primary_key: The single column the dump was ordered by. Agent
            Action Plan section 0.6.6 establishes that every in-scope
            table has exactly one, which is why the dump needs no
            tie-break and why this module must never re-order rows.
        column_count: The declared number of columns, asserted against
            the parsed schema. A cheap, strong tripwire on tampering.
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
# stray dump is refused with an explanation rather than with a not-found.
# Agent Action Plan section 0.2.2 enumerates them as "Eleven out-of-scope
# tables, all present in the frozen schema but never touched by the
# cycle". 22 + 11 = 33, the schema's full CREATE TABLE count. The same
# list is at [harness/dump_tables.py:L510-L525] and
# [harness/reset_db.sh:L276-L288].
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

# Deterministic iteration order for the default selection: the table
# names, ascending. Sorted ONCE here, never per run, and NEVER applied to
# rows - rows keep the primary-key order SQL returned them in (rule R-6).
IN_SCOPE_TABLES: Final[tuple[str, ...]] = tuple(sorted(IN_SCOPE))

# 513, verified by summing the twenty-two declared column counts and again
# by counting them in mysql/ACASDB.sql. Exposed so a test can assert the
# whole inventory in one line.
EXPECTED_TOTAL_COLUMNS: Final[int] = sum(
    spec.column_count for spec in IN_SCOPE.values()
)

# The frozen schema's full table count: 22 in scope plus 11 out of scope.
# `load_schema` aborts if the parsed file does not contain exactly this
# many `CREATE TABLE` statements, which is the tamper tripwire required by
# Agent Action Plan section 0.8.1.
EXPECTED_SCHEMA_TABLES: Final[int] = 33

# The two sides of the comparison. The path records which one a dump is,
# never the file's content.
SIDES: Final[tuple[str, ...]] = ("cobol", "python")

# The dump object's key order, identical to
# [harness/dump_tables.py:L544-L550]. Asserted on input AND on output: the
# key order is part of the byte-identical guarantee (rule R-6).
DUMP_KEYS: Final[tuple[str, ...]] = (
    "table",
    "primary_key",
    "columns",
    "row_count",
    "rows",
)


# ---------------------------------------------------------------------------
#  JOB 3's COLUMN ALLOW-LIST  (rule R-5)
#
#  FIVE columns, named explicitly. `char(8)` does not mean "date" and
#  `char(4)` does not mean "period", so this can never be a width or content
#  heuristic. Every deliberate exclusion is recorded below it with its
#  reason and locator, because an unexplained absence from an allow-list is
#  indistinguishable from an oversight.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DateTextSpec:
    """The canonical shape of one allow-listed date-text column.

    Attributes:
        form: `"date"` for the eight-character `NN/NN/NN` layout,
            `"period"` for the four-character all-digit layout.
        width: The `char(n)` width the frozen schema declares, asserted
            against the parsed schema so the pair cannot drift.
        schema_line: The declaring line of `mysql/ACASDB.sql`.
        copybook: The COBOL declaration the form was read from.
    """

    form: str
    width: int
    schema_line: int
    copybook: str


DATE_TEXT_COLUMNS: Final[Mapping[tuple[str, str], DateTextSpec]] = {
    # The GL posting date. [copybooks/wspost.cob:L18] declares
    # `03 Post-Date pic x(8).`; the bridge slices it at (1:2), (4:2) and
    # (7:2) [common/irspostingMT.cbl:L982-L987], which puts the
    # separators at 3 and 6.
    ("GLPOSTING-REC", "POST-DAT"): DateTextSpec(
        "date", 8, 158, "copybooks/wspost.cob:L18"
    ),
    # The internal IRS posting date - the same eight-character form, and
    # the field the three bridge-only components are derived from
    # (anomaly 7; the components are never repaired here).
    ("IRSPOSTING-REC", "POST4-DAT"): DateTextSpec(
        "date", 8, 277, "copybooks/irswspost.cob:L11"
    ),
    # The SL/PL-to-IRS transfer posting date.
    # [copybooks/wspost-irs.cob:L18] declares
    # `03 WS-IRS-Post-Date pic x(8).`
    ("PSIRSPOST-REC", "IRS-POST-DAT"): DateTextSpec(
        "date", 8, 369, "copybooks/wspost-irs.cob:L18"
    ),
    # The sales-ledger statistics period. [copybooks/wssl.cob:L64]
    # declares `03 Sales-Stats-Date pic 9(4).` - four DIGITS, carried in
    # a `PIC X(4)` host variable [common/salesMT.cbl:L320] and trimmed
    # into the SQL [common/salesMT.cbl:L1751-L1753].
    ("SALEDGER-REC", "SALES-STATS-DATE"): DateTextSpec(
        "period", 4, 981, "copybooks/wssl.cob:L64"
    ),
    # The system statistics period. [copybooks/wssystem.cob:L145]
    # declares `05 Stats-Date-Period pic 9(4).`, host variable at
    # [common/systemMT.cbl:L373], trimmed at
    # [common/systemMT.cbl:L2001-L2003].
    ("SYSTEM-REC", "STATS-DATE-PERIOD"): DateTextSpec(
        "period", 4, 1236, "copybooks/wssystem.cob:L145"
    ),
}

# DELIBERATE EXCLUSIONS. Every one of these has the width of an
# allow-listed column and is NOT a date or a period. They are named so
# that a reader can see the allow-list is complete by intent rather than
# by accident (rule R-5). Job 3 never touches them; job 1 still trims
# their trailing spaces, because they are `char` columns like any other.
DATE_TEXT_EXCLUSIONS: Final[Mapping[tuple[str, str], str]] = {
    ("PUITM5-REC", "OI5-BATCH"): (
        "char(8) [mysql/ACASDB.sql:L601] but a BATCH REFERENCE, not a "
        "date: [copybooks/slwsoi.cob:L16-L18] declares `03 OI-Batch "
        "comp.` over `05 OI-B-Nos pic 9(5).` and `05 OI-B-Item pic "
        "999.` - five digits plus three - and the schema labels its two "
        "component columns COMMENT 'Batch content' "
        "[mysql/ACASDB.sql:L602-L603]."
    ),
    ("SAITM3-REC", "OI3-BATCH"): (
        "char(8) [mysql/ACASDB.sql:L901] but a BATCH REFERENCE, not a "
        "date, by the same copybook declaration as OI5-BATCH; component "
        "columns labelled COMMENT 'Batch content' "
        "[mysql/ACASDB.sql:L902-L903]."
    ),
    ("PULEDGER-REC", "PURCH-EXT"): (
        "char(4) [mysql/ACASDB.sql:L653] but the supplier-key extension "
        "[copybooks/wspl.cob:L27] `03 Purch-Ext pic x(4).`, not a period."
    ),
    ("SALEDGER-REC", "SALES-EXT"): (
        "char(4) [mysql/ACASDB.sql:L950] but the customer-key extension "
        "[copybooks/wssl.cob:L22] `03 Sales-Ext pic x(4).`, not a period."
    ),
    ("SYSTEM-REC", "PASS-WORD"): (
        "char(4) [mysql/ACASDB.sql:L1219] but the system password "
        "[copybooks/wssystem.cob:L97] `05 Pass-Word pic x(4).`, not a "
        "period. It also carries the schema's ONLY column-level DEFAULT, "
        "recorded at [harness/dump_tables.py:L568-L570]."
    ),
    ("DELIVERY-REC", "DELIV-KEY"): (
        "char(8) [mysql/ACASDB.sql:L57] and the sixth char(8) column of "
        "the schema, but `DELIVERY-REC` is one of the eleven "
        "OUT-OF-SCOPE tables of Agent Action Plan section 0.2.2, so no "
        "dump of it ever reaches this module."
    ),
}

# The canonical eight-character date-text shape: two digits, a solidus,
# two digits, a solidus, two digits. Anchored, ASCII-only, and NOT widened
# to accept `-`, `.` or `,` separators or non-padded components - see the
# module docstring's job 3 section for why widening it would risk
# equating values that genuinely differ.
_DATE_TEXT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\A(?P<first>[0-9]{2})/(?P<second>[0-9]{2})/(?P<third>[0-9]{2})\Z"
)

# The canonical four-character period shape: exactly four ASCII digits,
# because the copybooks declare `pic 9(4)`.
_PERIOD_TEXT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\A(?P<digits>[0-9]{4})\Z"
)

# The canonical separator, and the only one the in-scope write paths can
# produce: [sales/sl060.cbl:L1071] copies `u-date (1:6)` verbatim, which
# already carries it.
_DATE_TEXT_SEPARATOR: Final[str] = "/"

# The two forms `DateTextSpec.form` may take.
_FORM_DATE: Final[str] = "date"
_FORM_PERIOD: Final[str] = "period"


# ---------------------------------------------------------------------------
#  COLUMN CLASSES
#
#  Three, and they partition the frozen schema exactly: 238 `char`, 167
#  `decimal` and 315 integer-family columns, 720 in total, with zero
#  `varchar`, `float`, `double`, `real` or temporal columns anywhere.
# ---------------------------------------------------------------------------

KIND_CHAR: Final[str] = "char"
KIND_DECIMAL: Final[str] = "decimal"
KIND_INTEGER: Final[str] = "integer"

# The integer widths the schema uses. `bigint(11)` is the widest in scope
# and sits comfortably inside a 64-bit integer, so a JSON integer renders
# every one of them exactly.
_INTEGER_TYPES: Final[frozenset[str]] = frozenset(
    {"tinyint", "smallint", "mediumint", "int", "integer", "bigint"}
)

# Declared types that would break either the numeric policy of rule R-2 or
# the determinism argument of Agent Action Plan section 0.6.6. Verified
# absent from all 33 tables; asserted rather than trusted, because their
# appearance would mean the frozen schema had been modified.
_REFUSED_TYPES: Final[frozenset[str]] = frozenset(
    {
        "float",
        "double",
        "real",
        "varchar",
        "text",
        "blob",
        "timestamp",
        "datetime",
        "date",
        "time",
        "year",
        "json",
        "enum",
        "set",
        "bit",
        "binary",
        "varbinary",
        "numeric",
    }
)


# ---------------------------------------------------------------------------
#  EXIT CODES
#
#  The same 80+ band the sibling harness tools use
#  [harness/dump_tables.py:L598-L606], so one pipeline log reads as one
#  family. 82 - database - is deliberately absent: this module opens no
#  database link.
# ---------------------------------------------------------------------------

EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 80
EX_PRECONDITION: Final[int] = 81
EX_SCOPE: Final[int] = 83
EX_DRIFT: Final[int] = 84
EX_NUMERIC: Final[int] = 85
EX_WRITE: Final[int] = 86

# The environment variables this module consults, both defined by the
# Compose service [harness/docker-compose.yml:L686-L689]. Neither is read
# by `normalize_dump`, which is pure.
_ENV_REPO: Final[str] = "ACAS_REPO"
_ENV_OUT: Final[str] = "ACAS_OUT"

# The frozen schema, relative to the read-only checkout. Read, never
# written (rule R-3).
_SCHEMA_RELPATH: Final[str] = "mysql/ACASDB.sql"

# The destination suffix the file specification for this module defines.
# The committed Compose recipe passes `--out .../cobol.norm` explicitly
# [harness/docker-compose.yml:L269], so this default only applies when no
# destination is given at all.
_NORMALIZED_SUFFIX: Final[str] = ".normalized"

# Where a defaulted findings report goes: alongside `$ACAS_OUT/reset/`,
# which [harness/reset_db.sh:L150-L151] documents as never being part of a
# comparison. NEVER inside `$ACAS_OUT/<scenario>/`.
_REPORT_SUBDIR: Final[str] = "normalize"
_REPORT_FILENAME: Final[str] = "date-text-findings.txt"

# The defaulted report file is named for the source directory - so the
# recipe's two invocations [harness/docker-compose.yml:L269] and [L273]
# produce `cobol-date-text-findings.txt` and
# `python-date-text-findings.txt` rather than one overwriting the other,
# and both sides' questions reach the oracle. Runs of alphanumerics only,
# joined with a hyphen, so the name is deterministic and portable
# whatever the source directory was called.
_REPORT_LABEL_RE: Final[re.Pattern[str]] = re.compile(r"[0-9A-Za-z]+")
_REPORT_DEFAULT_LABEL: Final[str] = "dump"

# JSON serialisation, pinned to `dump_tables.py`'s parameters exactly
# [harness/dump_tables.py:L1663-L1673] so a normalised file differs from
# its input in VALUES only.
_JSON_INDENT: Final[int] = 2
_JSON_SEPARATORS: Final[tuple[str, str]] = (",", ": ")
_DUMP_SUFFIX: Final[str] = ".json"
_TEMP_PREFIX: Final[str] = "."
_TEMP_SUFFIX: Final[str] = ".json.tmp"

# An explicit arithmetic context for job 2, so a `quantize` here can never
# depend on the caller's ambient decimal settings. Purity and determinism
# both require that (rule R-6). The precision is far above anything the
# schema can hold - the widest declaration anywhere in the file is
# `decimal(14,4)`, fourteen digits - so `quantize` cannot fail for
# capacity reasons, and no rounding decision is ever delegated to the
# context: the rounding mode is passed at every call site.
_DECIMAL_CONTEXT: Final[Context] = Context(prec=60)

# Only the ASCII space is padding (job 1). Named so the intent cannot be
# widened by accident into a general whitespace removal.
_PAD_CHARACTER: Final[str] = " "


# ---------------------------------------------------------------------------
#  PROGRESS
#
#  stderr only, and never a byte of it inside a normalised file (rule R-6).
#  `normalize_dump` never calls this: it is pure, and a pure function does
#  not write to a stream.
# ---------------------------------------------------------------------------

_QUIET: bool = False


def _progress(message: str) -> None:
    """Write one progress line to stderr unless `--quiet` was given.

    Args:
        message: The line to write, without a trailing newline.
    """
    if not _QUIET:
        print(message, file=sys.stderr)


# ---------------------------------------------------------------------------
#  ERRORS
#
#  One class per failure mode, each mapped to exactly one exit code, so a
#  caller driving `main` in process and a caller catching an exception see
#  the same taxonomy. Every message names the table, the column and the
#  value where it can, and cites the locator a reader would need.
# ---------------------------------------------------------------------------


class NormalizeError(Exception):
    """Base class for every failure this module raises."""


class SchemaFileError(NormalizeError, OSError):
    """The frozen schema could not be read. Exit code 81."""


class SchemaParseError(NormalizeError, ValueError):
    """The frozen schema could not be parsed, or drifted. Exit code 84."""


class UnknownTableError(NormalizeError, ValueError):
    """A dump names a table the frozen schema does not define. Code 83."""


class TableNotInScopeError(NormalizeError, ValueError):
    """A dump names one of the eleven out-of-scope tables. Code 83."""


class DumpShapeError(NormalizeError, ValueError):
    """A dump object does not have the shape `dump_tables.py` writes.

    Exit code 84: a shape mismatch means either the frozen schema was
    modified or the dump is stale, and both are drift.
    """


class NumericPolicyError(NormalizeError, TypeError):
    """A value would have required binary floating point. Exit code 85.

    Rule R-2 forbids binary floating point outright, so the value is
    refused rather than coerced.
    """


class UnexpectedValueTypeError(NormalizeError, TypeError):
    """A value is of a type no in-scope column can hold. Exit code 85."""


class UnexpectedNullError(NormalizeError, ValueError):
    """A dump carries a JSON `null`. Exit code 85.

    Every column of the frozen schema is declared `NOT NULL`, and Agent
    Action Plan section 0.6.2 explains why: each bridge load paragraph
    initialises the host-variable group, "so unset fields become zero or
    space rather than SQL NULL". A null is genuinely new information, so
    it is reported loudly and never coalesced.
    """


class DecimalScaleError(NormalizeError, ValueError):
    """A decimal value carries more decimal places than its column. 85.

    Job 2's information-loss guard. Quantising such a value away would
    make two genuinely different stored values compare equal, which the
    module docstring's hard limit forbids.
    """


class DumpReadError(NormalizeError, OSError):
    """A dump file could not be read or parsed as JSON. Exit code 81."""


class DumpWriteError(NormalizeError, OSError):
    """A normalised file could not be written or moved. Exit code 86."""


class ReportPathError(NormalizeError, ValueError):
    """The findings report would land inside a compared tree. Code 80."""


# ---------------------------------------------------------------------------
#  THE COLUMN TYPE MAP, PARSED FROM THE FROZEN SCHEMA  (rules R-1, R-5)
#
#  `mysql/ACASDB.sql` is the source of truth, for three reasons that all
#  matter:
#
#    * NO DATABASE IS NEEDED, so this module runs offline, in unit tests,
#      with the Compose stack down.
#    * NO DEPENDENCE ON THE SHIPPED PACKAGE or on the generated
#      data-dictionary JSON, which preserves the oracle's independence from
#      the thing it exists to arbitrate (rule R-1).
#    * IT IS THE FROZEN ARTIFACT ITSELF, so the declared types are the
#      specification rather than a derived view of it.
#
#  The parser is strict and asserts its own results: exactly 33 tables, and
#  the declared column count of every one of the 22 in-scope tables. A
#  mismatch means the frozen schema was modified, which Agent Action Plan
#  section 0.8.1 calls "a defect in the migration, regardless of how
#  harmless it appears" - so it aborts and says so rather than adapting.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ColumnType:
    """One column's declared type, as `mysql/ACASDB.sql` writes it.

    Attributes:
        name: The column name, spelled exactly as the schema spells it,
            hyphens included.
        kind: `KIND_CHAR`, `KIND_DECIMAL` or `KIND_INTEGER`.
        sql_type: The declaration verbatim, for error messages - for
            example `char(32)`, `decimal(10,2)` or `int(8) unsigned`.
        width: The `char(n)` length, or `None` for the other kinds.
        precision: The `decimal(p,s)` precision, or `None`.
        scale: The `decimal(p,s)` scale, or `None`. Job 2 renders to
            exactly this many places and never assumes two.
        unsigned: Whether the declaration carries `unsigned`. Recorded
            for completeness; this module never alters a sign (rule R-4).
        line: The declaring line of `mysql/ACASDB.sql` (rule R-5).
    """

    name: str
    kind: str
    sql_type: str
    width: int | None
    precision: int | None
    scale: int | None
    unsigned: bool
    line: int


# `CREATE TABLE `NAME` (` - the only statement whose body is parsed. The
# frozen file writes one per table, always with the parenthesis on the
# same line.
_CREATE_TABLE_RE: Final[re.Pattern[str]] = re.compile(
    r"\ACREATE\s+TABLE\s+`(?P<table>[^`]+)`\s*\(\s*\Z", re.IGNORECASE
)

# The closing line of a table body, for example
# `) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;` and
# also the one that carries a TABLE-level COMMENT
# [mysql/ACASDB.sql:L195].
_END_TABLE_RE: Final[re.Pattern[str]] = re.compile(r"\A\)[^;]*;\s*\Z")

# A column definition. Identifiers are BACKTICK-QUOTED and HYPHENATED, so
# the backticks are what is matched - a bare-word parser would split
# `LEDGER-NAME` into two tokens. Every column line of the frozen file ends
# with a comma, because a `PRIMARY KEY` clause always follows.
_COLUMN_RE: Final[re.Pattern[str]] = re.compile(
    r"\A\s+`(?P<name>[^`]+)`\s+(?P<declaration>.+?),\s*\Z"
)

# The type at the head of a declaration, with its optional arguments and an
# optional `unsigned`. Anything after that - `NOT NULL`, `DEFAULT ''`
# [mysql/ACASDB.sql:L1219], `COMMENT '...'` - is deliberately ignored.
#
# NOTE ON COMMENTS: the file specification for this module states the
# `COMMENT` suffix is "verified present on exactly one column". The frozen
# artifact disagrees, and the frozen artifact wins: there are FOURTEEN
# column-level COMMENTs - [mysql/ACASDB.sql:L155] `POST-RRN`,
# L562-L567 and L575 on `SAINVOICE-REC`, L597, L602, L603 and L610 on
# `PUITM5-REC`, L902, L903 and L909 on `SAITM3-REC` - plus one TABLE-level
# COMMENT at L195. All fifteen are handled, none is a special case.
_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"\A(?P<type>[A-Za-z]+)"
    r"(?:\s*\((?P<arguments>[^)]*)\))?"
    r"(?P<tail>.*)\Z",
    re.DOTALL,
)

# The `PRIMARY KEY (`col`)` clause, used to cross-check `IN_SCOPE`.
_PRIMARY_KEY_RE: Final[re.Pattern[str]] = re.compile(
    r"\A\s+PRIMARY\s+KEY\s+\((?P<columns>[^)]*)\)", re.IGNORECASE
)

# Clauses inside a table body that are constraints rather than columns.
# Skipped by name. Measured over the frozen file: 33 `PRIMARY KEY`, 1
# `UNIQUE KEY`, 3 `KEY` and 1 `CONSTRAINT`, and every one of the five
# non-primary clauses belongs to an OUT-OF-SCOPE table.
_CONSTRAINT_RE: Final[re.Pattern[str]] = re.compile(
    r"\A\s+(PRIMARY\s+KEY|UNIQUE\s+KEY|FULLTEXT\s+KEY|SPATIAL\s+KEY"
    r"|FOREIGN\s+KEY|CONSTRAINT|KEY|INDEX|CHECK)\b",
    re.IGNORECASE,
)


def default_schema_path(env: Mapping[str, str] | None = None) -> Path:
    """Return the frozen schema's path, `$ACAS_REPO/mysql/ACASDB.sql`.

    Args:
        env: The environment to read `ACAS_REPO` from; `os.environ` when
            omitted. The Compose service sets it to `/repo`
            [harness/docker-compose.yml:L686], mounted read-only
            [harness/docker-compose.yml:L591].

    Returns:
        `$ACAS_REPO/mysql/ACASDB.sql` when `ACAS_REPO` is set and
        non-empty, otherwise the same relative path resolved against the
        directory that contains this file's parent - that is, the
        checkout this module was invoked from.
    """
    environment = os.environ if env is None else env
    root = environment.get(_ENV_REPO, "")
    if root:
        return Path(root) / _SCHEMA_RELPATH
    # `harness/normalize.py` -> `harness/` -> the checkout root.
    return Path(__file__).resolve().parent.parent / _SCHEMA_RELPATH


def _parse_declaration(
    name: str, declaration: str, line: int
) -> ColumnType:
    """Turn one column declaration into a `ColumnType`.

    Args:
        name: The column name, without its backticks.
        declaration: Everything after the name, without the trailing
            comma - for example `char(32) NOT NULL` or
            `decimal(10,2) NOT NULL` or
            `mediumint(5) unsigned NOT NULL COMMENT 'Rel. replacement'`.
        line: The declaring line of `mysql/ACASDB.sql`.

    Returns:
        The parsed type.

    Raises:
        SchemaParseError: The declaration is unrecognisable, or names a
            type that would break rule R-2's numeric policy or Agent
            Action Plan section 0.6.6's determinism argument.
    """
    match = _TYPE_RE.match(declaration.strip())
    if match is None:
        raise SchemaParseError(
            f"[{_SCHEMA_RELPATH}:L{line}] the declaration of column "
            f"`{name}` could not be parsed: {declaration!r}. Every column "
            f"of the frozen schema is `<type>[(<args>)] [unsigned] NOT "
            f"NULL [DEFAULT ...] [COMMENT ...]`."
        )

    sql_type_name = match.group("type").lower()
    arguments = match.group("arguments")
    tail = match.group("tail") or ""
    unsigned = re.search(r"\bunsigned\b", tail, re.IGNORECASE) is not None
    rendered = sql_type_name
    if arguments is not None:
        rendered = f"{sql_type_name}({arguments})"
    if unsigned:
        rendered = f"{rendered} unsigned"

    if sql_type_name in _REFUSED_TYPES:
        raise SchemaParseError(
            f"[{_SCHEMA_RELPATH}:L{line}] column `{name}` is declared "
            f"{rendered}, which the frozen schema does not contain. It "
            f"declares zero float, double, real, varchar and temporal "
            f"columns - verified over all 720 columns of all 33 tables - "
            f"so this reading means the frozen artifact was modified. "
            f"Agent Action Plan section 0.8.1: such a diff \"is a defect "
            f"in the migration, regardless of how harmless it appears\"."
        )

    if sql_type_name == KIND_CHAR:
        width = _parse_single_argument(name, rendered, arguments, line)
        return ColumnType(
            name=name,
            kind=KIND_CHAR,
            sql_type=rendered,
            width=width,
            precision=None,
            scale=None,
            unsigned=unsigned,
            line=line,
        )

    if sql_type_name == KIND_DECIMAL:
        precision, scale = _parse_decimal_arguments(
            name, rendered, arguments, line
        )
        return ColumnType(
            name=name,
            kind=KIND_DECIMAL,
            sql_type=rendered,
            width=None,
            precision=precision,
            scale=scale,
            unsigned=unsigned,
            line=line,
        )

    if sql_type_name in _INTEGER_TYPES:
        # The parenthesised number on an integer type is MySQL's display
        # width and has no effect on the stored value. It is not recorded
        # as a width, and it is never "fixed" - `BL-END-CYCLE-DAT` is
        # declared `int(1) unsigned` [mysql/ACASDB.sql:L1270] and stays
        # that way (rule R-4).
        return ColumnType(
            name=name,
            kind=KIND_INTEGER,
            sql_type=rendered,
            width=None,
            precision=None,
            scale=None,
            unsigned=unsigned,
            line=line,
        )

    raise SchemaParseError(
        f"[{_SCHEMA_RELPATH}:L{line}] column `{name}` is declared "
        f"{rendered}, which is neither char, decimal nor an integer "
        f"width. Those three classes partition the frozen schema exactly: "
        f"238 char, 167 decimal and 315 integer columns, 720 in total."
    )


def _parse_single_argument(
    name: str, rendered: str, arguments: str | None, line: int
) -> int:
    """Parse a `char(n)` length.

    Args:
        name: The column name, for the error message.
        rendered: The rendered declaration, for the error message.
        arguments: The text between the parentheses, or `None`.
        line: The declaring line, for the error message.

    Returns:
        The declared length.

    Raises:
        SchemaParseError: The length is missing or not a positive integer.
    """
    if arguments is None or not arguments.strip().isdigit():
        raise SchemaParseError(
            f"[{_SCHEMA_RELPATH}:L{line}] column `{name}` is declared "
            f"{rendered} without a usable length. Every one of the "
            f"schema's 238 char columns declares one, and there are zero "
            f"varchar columns."
        )
    width = int(arguments.strip())
    if width <= 0:
        raise SchemaParseError(
            f"[{_SCHEMA_RELPATH}:L{line}] column `{name}` is declared "
            f"{rendered}, a non-positive length."
        )
    return width


def _parse_decimal_arguments(
    name: str, rendered: str, arguments: str | None, line: int
) -> tuple[int, int]:
    """Parse a `decimal(p,s)` precision and scale.

    Args:
        name: The column name, for the error message.
        rendered: The rendered declaration, for the error message.
        arguments: The text between the parentheses, or `None`.
        line: The declaring line, for the error message.

    Returns:
        The precision and the scale.

    Raises:
        SchemaParseError: The arguments are missing or malformed. A
            decimal column with no declared scale would leave job 2 with
            nothing to render to, so it is refused rather than defaulted -
            defaulting to two places is exactly the mistake the scale
            census warns against.
    """
    parts = [part.strip() for part in (arguments or "").split(",")]
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise SchemaParseError(
            f"[{_SCHEMA_RELPATH}:L{line}] column `{name}` is declared "
            f"{rendered}, which does not carry a precision and a scale. "
            f"Job 2 renders to the DECLARED scale and never assumes two: "
            f"the schema's scales include 2, 4 and 0."
        )
    precision, scale = int(parts[0]), int(parts[1])
    if precision <= 0 or scale < 0 or scale > precision:
        raise SchemaParseError(
            f"[{_SCHEMA_RELPATH}:L{line}] column `{name}` is declared "
            f"{rendered}, whose precision and scale are not a usable "
            f"pair."
        )
    return precision, scale


def load_schema(
    schema_path: Path | str | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> dict[str, dict[str, ColumnType]]:
    """Parse the frozen schema into a column-type map.

    The map is `{table: {column: ColumnType}}`, and the inner mapping's
    insertion order IS the schema's ordinal column order - which is what
    `normalize_dump` compares a dump's `columns` list against.

    Args:
        schema_path: The schema to parse; `default_schema_path()` when
            omitted. A test may point this at a fixture.
        env: The environment used to resolve the default path.

    Returns:
        The column-type map, with 33 tables.

    Raises:
        SchemaFileError: The file could not be read.
        SchemaParseError: The file could not be parsed, does not contain
            exactly 33 `CREATE TABLE` statements, or disagrees with
            `IN_SCOPE` on a column count, a primary key or an
            allow-listed column's declared width. Every one of those
            means the frozen artifact was modified.
    """
    path = (
        default_schema_path(env)
        if schema_path is None
        else Path(schema_path)
    )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaFileError(
            f"could not read the frozen schema at {path}: {exc}. It is "
            f"read-only input; set {_ENV_REPO} or pass --schema. The "
            f"Compose service mounts the checkout at /repo "
            f"[harness/docker-compose.yml:L591]."
        ) from exc

    schema: dict[str, dict[str, ColumnType]] = {}
    primary_keys: dict[str, list[str]] = {}
    current: str | None = None

    for number, raw in enumerate(text.splitlines(), start=1):
        if current is None:
            # Outside a table body. Everything else in the file is
            # ignored on purpose: the 33 `DROP TABLE IF EXISTS`
            # statements, the 33 `LOCK TABLES` / `UNLOCK TABLES` pairs,
            # the `/*!40101 ... */` and `/*!40000 ALTER TABLE ... KEYS */`
            # version-guarded comments - 66 of which mention ALTER TABLE
            # while being pure comment, with zero real DDL among them -
            # and the `--` header. The file carries no CREATE DATABASE and
            # no USE statement, so none is looked for.
            match = _CREATE_TABLE_RE.match(raw)
            if match is not None:
                current = match.group("table")
                if current in schema:
                    raise SchemaParseError(
                        f"[{_SCHEMA_RELPATH}:L{number}] table "
                        f"`{current}` is declared twice."
                    )
                schema[current] = {}
            continue

        if _END_TABLE_RE.match(raw):
            current = None
            continue

        primary = _PRIMARY_KEY_RE.match(raw)
        if primary is not None:
            primary_keys[current] = [
                column.strip().strip("`")
                for column in primary.group("columns").split(",")
                if column.strip()
            ]
            continue

        if _CONSTRAINT_RE.match(raw):
            continue

        column = _COLUMN_RE.match(raw)
        if column is None:
            raise SchemaParseError(
                f"[{_SCHEMA_RELPATH}:L{number}] this line is inside the "
                f"body of `{current}` but is neither a backtick-quoted "
                f"column definition nor a recognised constraint clause: "
                f"{raw!r}."
            )
        name = column.group("name")
        if name in schema[current]:
            raise SchemaParseError(
                f"[{_SCHEMA_RELPATH}:L{number}] column `{name}` is "
                f"declared twice in `{current}`."
            )
        schema[current][name] = _parse_declaration(
            name, column.group("declaration"), number
        )

    if current is not None:
        raise SchemaParseError(
            f"[{_SCHEMA_RELPATH}] the body of table `{current}` is not "
            f"closed. The frozen file is a complete mysqldump; a "
            f"truncated reading means it was modified."
        )

    _assert_schema_inventory(schema, primary_keys, path)
    return schema


def _assert_schema_inventory(
    schema: Mapping[str, Mapping[str, ColumnType]],
    primary_keys: Mapping[str, Sequence[str]],
    path: Path,
) -> None:
    """Assert the parsed schema against the frozen inventory.

    Four assertions, each a tripwire on tampering with a frozen artifact
    (Agent Action Plan section 0.8.1): the table count, every in-scope
    table's presence and column count, every in-scope primary key, and
    every allow-listed date-text column's declared width.

    Args:
        schema: The parsed column-type map.
        primary_keys: The `PRIMARY KEY (...)` columns parsed per table.
        path: The file it came from, for the error messages.

    Raises:
        SchemaParseError: Any assertion failed.
    """
    if len(schema) != EXPECTED_SCHEMA_TABLES:
        raise SchemaParseError(
            f"{path} defines {len(schema)} table(s); the frozen schema "
            f"defines exactly {EXPECTED_SCHEMA_TABLES} - "
            f"{len(IN_SCOPE)} in scope for the posting cycle plus "
            f"{len(OUT_OF_SCOPE)} out of scope. A different count means "
            f"the frozen artifact was modified, which Agent Action Plan "
            f"section 0.8.1 calls a defect in the migration."
        )

    missing = sorted(set(IN_SCOPE) - set(schema))
    if missing:
        raise SchemaParseError(
            f"{path} is missing {len(missing)} in-scope table(s): "
            f"{', '.join(missing)}."
        )

    unexpected = sorted(set(schema) - set(IN_SCOPE) - OUT_OF_SCOPE)
    if unexpected:
        raise SchemaParseError(
            f"{path} defines {len(unexpected)} table(s) that are neither "
            f"in scope nor among the eleven out-of-scope tables of Agent "
            f"Action Plan section 0.2.2: {', '.join(unexpected)}."
        )

    total = 0
    for table in IN_SCOPE_TABLES:
        specification = IN_SCOPE[table]
        columns = schema[table]
        total += len(columns)
        if len(columns) != specification.column_count:
            raise SchemaParseError(
                f"[{_SCHEMA_RELPATH}:L{specification.schema_line}] table "
                f"`{table}` declares {len(columns)} column(s); the frozen "
                f"schema declares {specification.column_count}. The "
                f"twenty-two counts sum to "
                f"{EXPECTED_TOTAL_COLUMNS} and are asserted "
                f"independently at [harness/dump_tables.py:L479-L502] and "
                f"[harness/reset_db.sh:L248-L271]."
            )
        parsed_key = list(primary_keys.get(table, ()))
        if parsed_key != [specification.primary_key]:
            raise SchemaParseError(
                f"[{_SCHEMA_RELPATH}:L{specification.schema_line}] table "
                f"`{table}` declares PRIMARY KEY {parsed_key}; the "
                f"frozen schema declares "
                f"['{specification.primary_key}']. Agent Action Plan "
                f"section 0.6.6 establishes that every in-scope table has "
                f"a single-column primary key, which is why the dump "
                f"needs no tie-break and why this module must never "
                f"re-order rows."
            )
        if specification.primary_key not in columns:
            raise SchemaParseError(
                f"[{_SCHEMA_RELPATH}:L{specification.schema_line}] table "
                f"`{table}` does not declare its primary-key column "
                f"`{specification.primary_key}`."
            )

    if total != EXPECTED_TOTAL_COLUMNS:
        raise SchemaParseError(
            f"{path} declares {total} in-scope column(s); the frozen "
            f"schema declares exactly {EXPECTED_TOTAL_COLUMNS}."
        )

    for (table, column), specification in DATE_TEXT_COLUMNS.items():
        declared_type = schema[table].get(column)
        if declared_type is None:
            raise SchemaParseError(
                f"{path} does not declare `{table}`.`{column}`, which "
                f"job 3's allow-list names "
                f"[{_SCHEMA_RELPATH}:L{specification.schema_line}]."
            )
        if (
            declared_type.kind != KIND_CHAR
            or declared_type.width != specification.width
        ):
            raise SchemaParseError(
                f"[{_SCHEMA_RELPATH}:L{declared_type.line}] "
                f"`{table}`.`{column}` is declared "
                f"{declared_type.sql_type}; job 3's allow-list expects "
                f"char({specification.width}), read from "
                f"[{specification.copybook}]. A width change would mean "
                f"the canonical shape had moved."
            )


def schema_columns(
    schema: Mapping[str, Mapping[str, ColumnType]], table: str
) -> tuple[str, ...]:
    """Return one table's ordered column names.

    Args:
        schema: The parsed column-type map.
        table: The table name, spelled as the schema spells it.

    Returns:
        The column names in schema ordinal order.

    Raises:
        UnknownTableError: The schema does not define the table.
    """
    columns = schema.get(table)
    if columns is None:
        raise UnknownTableError(
            f"the frozen schema does not define a table named "
            f"{table!r}. It defines exactly "
            f"{EXPECTED_SCHEMA_TABLES} tables."
        )
    return tuple(columns)


def column_type(
    schema: Mapping[str, Mapping[str, ColumnType]],
    table: str,
    column: str,
) -> ColumnType:
    """Return one column's declared type.

    Args:
        schema: The parsed column-type map.
        table: The table name.
        column: The column name.

    Returns:
        The declared type.

    Raises:
        UnknownTableError: The schema does not define the table.
        SchemaParseError: The table does not declare the column.
    """
    columns = schema.get(table)
    if columns is None:
        raise UnknownTableError(
            f"the frozen schema does not define a table named "
            f"{table!r}."
        )
    declared = columns.get(column)
    if declared is None:
        raise SchemaParseError(
            f"the frozen schema does not declare `{table}`.`{column}`."
        )
    return declared


# ---------------------------------------------------------------------------
#  JOB 1 - TRAILING SPACES IN FIXED-WIDTH CHARACTER COLUMNS
#
#  The finding, verified end to end in this checkout:
#
#      [copybooks/wsledger.cob:L27]  03  Ledger-Name pic x(24).       24
#      [common/nominalMT.cbl:L299]   05  HV-LEDGER-NAME PIC X(32).    32
#      [mysql/ACASDB.sql:L127]       `LEDGER-NAME` char(32) NOT NULL, 32
#
#  and, decisively, THE BRIDGE TRIMS as it builds the SQL text:
#
#      [common/nominalMT.cbl:L1065-L1067]
#          STRING '`LEDGER-NAME`="' INTO WS-MYSQL-COMMAND ...
#          STRING FUNCTION TRIM (HV-LEDGER-NAME,TRAILING) ...
#
#  23 such sites in `common/nominalMT.cbl`, 29 in `common/glpostingMT.cbl`,
#  27 in `common/irspostingMT.cbl`, 75 in `common/salesMT.cbl`, 339 in
#  `common/systemMT.cbl`. So the COBOL side stores character columns
#  trimmed while a Python data-access layer writing the padded record field
#  could store them padded, and without this job that purely
#  representational difference would fail every scenario.
# ---------------------------------------------------------------------------


def canonicalise_char(
    value: object,
    *,
    table: str,
    column: str,
    declared: ColumnType,
) -> str:
    """Job 1: remove trailing ASCII spaces from a fixed-width value.

    TRAILING ONLY, NEVER LEADING. A COBOL alphanumeric `MOVE` is
    left-justified with RIGHT padding, so a leading space is CONTENT.
    And the ASCII space only - never a tab, a NUL, a carriage return, a
    newline or any other Unicode whitespace, because any of those in a
    `char` column is real content or a genuine defect worth seeing.

    Idempotent by construction: a value with no trailing space is
    returned unchanged.

    Args:
        value: The dumped value. Must be a `str`; a `char` column cannot
            legitimately dump anything else.
        table: The table it came from, for the error message.
        column: The column it came from, for the error message.
        declared: The column's declared type, asserted to be `char(n)` so
            a caller cannot apply job 1 to the wrong class of column.

    Returns:
        The value with its trailing ASCII spaces removed.

    Raises:
        UnexpectedValueTypeError: `value` is not a `str`.
        SchemaParseError: `declared` is not a `char(n)` column, which
            would mean the caller dispatched on something other than the
            declared type.
    """
    if declared.kind != KIND_CHAR:
        raise SchemaParseError(
            f"job 1 applies only to char columns, but "
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}]. Every "
            f"canonicalisation here is driven by the DECLARED type, never "
            f"by what a value looks like."
        )
    if not isinstance(value, str):
        raise UnexpectedValueTypeError(
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}] but the dump carries "
            f"{type(value).__name__} ({value!r}). "
            f"[harness/dump_tables.py:L1460-L1461] renders character data "
            f"as a JSON string exactly as the driver returned it, so "
            f"anything else means the dump is not one this module can "
            f"compare."
        )
    return value.rstrip(_PAD_CHARACTER)


# ---------------------------------------------------------------------------
#  JOB 2 - DECIMAL SCALE RENDERING
#
#  Agent Action Plan section 0.6.6: "canonicalise decimal scale rendering
#  so that a value stored at two decimal places compares equal regardless
#  of driver formatting."
#
#  THE SCALE IS NEVER ASSUMED. Measured over the frozen schema: 68 x
#  decimal(9,2), 57 x decimal(10,2), 17 x decimal(4,2), 12 x decimal(5,2),
#  4 x decimal(14,2), 2 x decimal(2,0), 2 x decimal(14,4) and one each of
#  decimal(6,2), decimal(5,0), decimal(11,4), decimal(11,2) and
#  decimal(10,4). In scope a ZERO scale occurs - `decimal(5,0)` - even
#  though a `,4` scale does not.
# ---------------------------------------------------------------------------

# A decimal literal, anchored. It accepts what `format(Decimal, "f")`
# produces and what a driver or a hand-written fixture might legitimately
# carry - including exponent notation, so `1E+2` renders as `100.00` - and
# refuses everything else: surrounding whitespace, thousands separators,
# `NaN`, `Infinity`, and the empty string. Refusing rather than tolerating
# keeps the guard loud: a decimal column cannot produce any of those, so
# their appearance is information, not noise.
_DECIMAL_LITERAL_RE: Final[re.Pattern[str]] = re.compile(
    r"\A[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z"
)


def canonicalise_decimal(
    value: object,
    *,
    table: str,
    column: str,
    declared: ColumnType,
) -> str:
    """Job 2: re-render a decimal at its column's declared scale.

    The value is parsed FROM ITS STRING into an exact `Decimal` - never
    through a binary approximation (rule R-2) - quantised to the declared
    scale under an explicit context and rounding mode, and rendered with
    `format(value, "f")` so exponent notation can never appear.

    The sign is preserved exactly as it arrives, including on a zero:
    MySQL `DECIMAL` has no signed zero, so a `-0.00` from either side is
    itself informative and is never quietly flipped (rule R-4).

    THE INFORMATION-LOSS GUARD. If the value's own exponent implies more
    decimal places than the column declares, `DecimalScaleError` is
    raised rather than quantising it away. That is not a rendering
    artefact: it means one side stored something the column cannot hold,
    which is a REAL finding, and rounding it away would make two
    genuinely different values compare equal. A value read back from a
    `DECIMAL(p,s)` column always has exponent `-s`, so the guard should
    never fire - which is why its firing is an error and not a warning.

    A value with FEWER decimal places than the column declares is exactly
    the artefact this job exists for, and is padded out to the declared
    scale.

    Idempotent by construction: the output always has exponent `-s`, so a
    second pass quantises it to itself.

    Args:
        value: The dumped value. Must be a `str`, because
            [harness/dump_tables.py:L1446-L1458] renders every `DECIMAL`
            as a JSON string.
        table: The table it came from, for the error messages.
        column: The column it came from, for the error messages.
        declared: The column's declared type, which supplies the scale.

    Returns:
        The value rendered at exactly `declared.scale` places.

    Raises:
        NumericPolicyError: `value` is a binary floating-point number, or
            a `bool`, or an `int` - each of which means the dump
            serialised a decimal as a JSON number and so reintroduced
            binary floating point at the file boundary (rule R-2).
        UnexpectedValueTypeError: `value` is of some other type.
        DecimalScaleError: The information-loss guard tripped, or the
            string is not a finite decimal literal.
        SchemaParseError: `declared` is not a `decimal(p,s)` column.
    """
    if declared.kind != KIND_DECIMAL or declared.scale is None:
        raise SchemaParseError(
            f"job 2 applies only to decimal columns, but "
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}]."
        )

    # bool BEFORE the numeric checks: `bool` is a subclass of `int`, and
    # JSON `true` is not a decimal.
    if isinstance(value, bool):
        raise NumericPolicyError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries the boolean {value!r}. No column of the "
            f"frozen schema can produce one."
        )

    # THE ACTIVE R-2 GUARD. A binary floating-point value here means
    # `dump_tables.py` was misconfigured, and quietly repairing it would
    # hide that bug. Nothing is coerced.
    if isinstance(value, float):
        raise NumericPolicyError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries a binary floating-point value ({value!r}). "
            f"No accounting value may pass through binary floating point "
            f"at any point (rule R-2), and a JSON number IS an IEEE-754 "
            f"double in every consumer. "
            f"[harness/dump_tables.py:L1446-L1458] renders every DECIMAL "
            f"as a JSON string for exactly this reason, so this dump is "
            f"broken. It is refused, not converted."
        )

    if isinstance(value, int):
        raise NumericPolicyError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries the JSON number {value!r}. A DECIMAL must "
            f"cross the file boundary as a JSON STRING (rule R-2): a JSON "
            f"number is an IEEE-754 double in every consumer, so writing "
            f"one would silently reintroduce binary floating point. "
            f"Accepting it here would hide that."
        )

    if not isinstance(value, str):
        raise UnexpectedValueTypeError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries {type(value).__name__} ({value!r})."
        )

    if _DECIMAL_LITERAL_RE.match(value) is None:
        raise DecimalScaleError(
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}] but the dump carries "
            f"{value!r}, which is not a finite decimal literal. A "
            f"DECIMAL column cannot produce surrounding whitespace, a "
            f"thousands separator, NaN, infinity or an empty string, so "
            f"the value is reported rather than repaired."
        )

    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:  # pragma: no cover - regex precedes it
        raise DecimalScaleError(
            f"`{table}`.`{column}` carries {value!r}, which is not a "
            f"decimal literal."
        ) from exc

    if not parsed.is_finite():  # pragma: no cover - regex precedes it
        raise DecimalScaleError(
            f"`{table}`.`{column}` carries the non-finite value "
            f"{value!r}. A DECIMAL column cannot hold NaN or infinity, "
            f"and neither has a faithful rendering."
        )

    exponent = parsed.as_tuple().exponent
    # `exponent` is an int for every finite Decimal; the special string
    # forms belong to NaN and infinity, which `is_finite` already refused.
    places = -int(exponent) if int(exponent) < 0 else 0
    if places > declared.scale:
        raise DecimalScaleError(
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}] - scale "
            f"{declared.scale} - but the dump carries {value!r}, which "
            f"has {places} decimal place(s). Quantising it would DESTROY "
            f"information and could make two genuinely different stored "
            f"values compare equal, which is the failure Agent Action "
            f"Plan section 0.6.6 forbids: \"a non-empty diff is always a "
            f"real behavioral difference and never an artefact of the "
            f"comparison\". A value read back from a "
            f"DECIMAL({declared.precision},{declared.scale}) column "
            f"always has exponent "
            f"-{declared.scale}, so this means one side stored something "
            f"the column cannot hold. It is reported, not rounded."
        )

    quantum = Decimal(1).scaleb(-declared.scale, _DECIMAL_CONTEXT)
    canonical = parsed.quantize(
        quantum, rounding=ROUND_HALF_UP, context=_DECIMAL_CONTEXT
    )
    return format(canonical, "f")


# ---------------------------------------------------------------------------
#  JOB 3 - THE TWO-DIGIT VERSUS FOUR-DIGIT DATE TEXT FORMS
#
#  FIVE allow-listed columns, and nothing else. RENDERING ONLY: a value
#  that matches the canonical shape is re-rendered from its parsed
#  components, and a value that does not is passed through UNCHANGED and
#  REPORTED. A two-digit component is never expanded to four and four is
#  never contracted to two, because either would invent or destroy
#  information and could make a genuine divergence between the two sides
#  compare equal.
#
#  The DD/MM/CC-versus-DD/MM/YY question the eight-character form raises is
#  arbitrated by the compiled oracle under rule R-6 and recorded in
#  `docs/migration/ambiguity-resolutions.md`. Nothing here depends on the
#  answer - see the module docstring's job 3 section.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DateTextOutcome:
    """The result of one job 3 canonicalisation.

    Attributes:
        value: The canonical rendering when the value matched its shape,
            or the value UNCHANGED when it did not.
        reason: `None` when the value matched, otherwise the deterministic
            explanation that goes into the findings report.
    """

    value: str
    reason: str | None


@dataclass(frozen=True, slots=True)
class DateTextFinding:
    """One reported date-text deviation.

    Attributes:
        table: The table the value came from.
        column: The allow-listed column.
        row_index: The zero-based position of the row within `rows`, in
            the primary-key order the dump preserved.
        value: The value as it arrived at job 3 - that is, after job 1
            removed trailing spaces - and as it was written out
            unchanged.
        reason: Why it did not match its canonical shape.
    """

    table: str
    column: str
    row_index: int
    value: str
    reason: str


def canonicalise_date_text(
    value: object,
    *,
    table: str,
    column: str,
    specification: DateTextSpec,
) -> DateTextOutcome:
    """Job 3: canonicalise the RENDERING of one allow-listed date text.

    Two canonical shapes, both exact:

        `date`    `NN/NN/NN` - two digits, a solidus, two digits, a
                  solidus, two digits. The layout the bridge slices at
                  (1:2), (4:2) and (7:2)
                  [common/irspostingMT.cbl:L982-L987] over the
                  `pic x(8)` field [copybooks/wspost.cob:L18].
        `period`  `NNNN` - exactly four ASCII digits, because the
                  copybooks declare `pic 9(4)`
                  [copybooks/wssystem.cob:L145],
                  [copybooks/wssl.cob:L64].

    A matching value is rebuilt from its parsed components with the
    canonical separator and zero-padded two-digit fields, which
    reproduces it byte for byte. That fixed point is deliberate: a looser
    recogniser - one that folded `-`, `.` or `,` separators into `/`, or
    accepted unpadded components - could equate values that genuinely
    differ, and [sales/sl060.cbl:L1071] shows `/` is the only separator
    the in-scope write paths can produce.

    Anything that does not match is returned UNCHANGED with a reason, so
    the operator takes the question to the compiled oracle (rule R-6)
    rather than to a normaliser tweak.

    Idempotent by construction: a canonical value re-renders to itself and
    a non-canonical value is passed through untouched.

    Args:
        value: The dumped value, after job 1. Must be a `str`.
        table: The table it came from.
        column: The allow-listed column it came from.
        specification: The column's entry from `DATE_TEXT_COLUMNS`.

    Returns:
        The outcome: the canonical rendering and `None`, or the unchanged
        value and the reason it was not canonical.

    Raises:
        UnexpectedValueTypeError: `value` is not a `str`.
        SchemaParseError: `specification.form` is neither `date` nor
            `period`.
    """
    if not isinstance(value, str):
        raise UnexpectedValueTypeError(
            f"`{table}`.`{column}` is an allow-listed date-text column "
            f"[{_SCHEMA_RELPATH}:L{specification.schema_line}] but the "
            f"dump carries {type(value).__name__} ({value!r})."
        )

    if specification.form == _FORM_DATE:
        match = _DATE_TEXT_PATTERN.match(value)
        if match is None:
            return DateTextOutcome(value, _date_text_reason(value))
        # Rebuilt from the parsed components rather than returned as
        # found, so the canonical separator and the two-digit component
        # rendering are asserted by construction.
        return DateTextOutcome(
            _DATE_TEXT_SEPARATOR.join(
                (
                    match.group("first"),
                    match.group("second"),
                    match.group("third"),
                )
            ),
            None,
        )

    if specification.form == _FORM_PERIOD:
        match = _PERIOD_TEXT_PATTERN.match(value)
        if match is None:
            return DateTextOutcome(value, _period_text_reason(value))
        return DateTextOutcome(match.group("digits"), None)

    raise SchemaParseError(
        f"`{table}`.`{column}` carries the unknown date-text form "
        f"{specification.form!r}. The two forms are "
        f"{_FORM_DATE!r} and {_FORM_PERIOD!r}."
    )


def _date_text_reason(value: str) -> str:
    """Explain why an eight-character date text is not canonical.

    The explanation is a function of the value alone, so the findings
    report is deterministic (rule R-6).

    Args:
        value: The non-canonical value, after job 1.

    Returns:
        The reason, naming the specific deviation.
    """
    if not value:
        return (
            "empty after job 1 removed trailing spaces, so the stored "
            "value was all spaces; the canonical form is NN/NN/NN "
            "[copybooks/wspost.cob:L18]"
        )
    if len(value) != 8:
        return (
            f"{len(value)} character(s), not the 8 of the canonical "
            f"NN/NN/NN form. NEITHER EXPANDED NOR CONTRACTED: the "
            f"two-digit versus four-digit component question is "
            f"arbitrated by the compiled oracle (rule R-6) and recorded "
            f"in docs/migration/ambiguity-resolutions.md, never by this "
            f"normaliser"
        )
    separators = (value[2], value[5])
    if separators != (_DATE_TEXT_SEPARATOR, _DATE_TEXT_SEPARATOR):
        return (
            f"separators {separators!r} at positions 3 and 6 rather than "
            f"{_DATE_TEXT_SEPARATOR!r}. Left as found: "
            f"[sales/sl060.cbl:L1071] copies `u-date (1:6)` verbatim, so "
            f"a different separator is real information rather than a "
            f"rendering artefact"
        )
    return (
        "non-numeric or non-zero-padded component(s); the canonical form "
        "is NN/NN/NN, matching the (1:2), (4:2) and (7:2) slices of "
        "[common/irspostingMT.cbl:L982-L987]"
    )


def _period_text_reason(value: str) -> str:
    """Explain why a four-character period text is not canonical.

    Args:
        value: The non-canonical value, after job 1.

    Returns:
        The reason, naming the specific deviation.
    """
    if not value:
        return (
            "empty after job 1 removed trailing spaces, so the stored "
            "value was all spaces; the canonical form is four digits "
            "[copybooks/wssystem.cob:L145]"
        )
    if len(value) != 4:
        return (
            f"{len(value)} character(s), not the 4 digits the copybooks "
            f"declare as `pic 9(4)`. NOT zero-padded and NOT truncated "
            f"here: either would invent or destroy information"
        )
    return (
        "non-numeric character(s); the copybooks declare the period "
        "`pic 9(4)` [copybooks/wssystem.cob:L145], "
        "[copybooks/wssl.cob:L64]"
    )


# ---------------------------------------------------------------------------
#  THE STRUCTURAL ASSERTIONS
#
#  Cheap, and they protect every diff. They validate the DUMP SHAPE and the
#  SCHEMA - never a row's business content, which rule R-3 forbids adding
#  validation to. Each one has a specific failure it catches:
#
#    * a stale dump, taken before the schema was re-applied
#    * a dump of an out-of-scope table, which would widen the comparison
#      beyond Agent Action Plan section 0.2.2's boundary
#    * a dump whose decimal values crossed the file boundary as JSON
#      numbers, reintroducing binary floating point (rule R-2)
#    * a JSON null, which a schema declaring every column NOT NULL cannot
#      legitimately produce
# ---------------------------------------------------------------------------


def _assert_dump_keys(dump: Mapping[str, Any], where: str) -> None:
    """Assert a dump object carries exactly the five keys, in order.

    Args:
        dump: The object to check.
        where: `"input"` or `"output"`, for the error message.

    Raises:
        DumpShapeError: The keys are wrong, missing, extra or reordered.
    """
    keys = tuple(dump.keys())
    if keys != DUMP_KEYS:
        raise DumpShapeError(
            f"the {where} dump object must carry exactly the keys "
            f"{list(DUMP_KEYS)} in that order; got {list(keys)}. The key "
            f"order is part of the byte-identical guarantee (rule R-6), "
            f"and no other key may appear - not a timestamp, a server "
            f"version, a scenario name or a side. The layout is fixed at "
            f"[harness/dump_tables.py:L544-L550]."
        )


def _assert_table_in_scope(table: object) -> str:
    """Assert a dump's table name is one of the twenty-two in scope.

    Args:
        table: The `table` value from the dump object.

    Returns:
        The table name.

    Raises:
        DumpShapeError: `table` is not a string.
        TableNotInScopeError: It is one of the eleven out-of-scope tables.
        UnknownTableError: It is not a table of the frozen schema at all.
    """
    if not isinstance(table, str):
        raise DumpShapeError(
            f"a dump's `table` must be the table name as a string; got "
            f"{type(table).__name__} ({table!r})."
        )
    if table in IN_SCOPE:
        return table
    if table in OUT_OF_SCOPE:
        raise TableNotInScopeError(
            f"`{table}` is one of the eleven tables the posting cycle "
            f"never touches, listed as out of scope by Agent Action Plan "
            f"section 0.2.2: {', '.join(sorted(OUT_OF_SCOPE))}. Comparing "
            f"it would widen the comparison beyond the migration's "
            f"boundary, so its dump is refused rather than normalised."
        )
    raise UnknownTableError(
        f"`{table}` is not a table of the frozen schema. It defines "
        f"exactly {EXPECTED_SCHEMA_TABLES} tables: the "
        f"{len(IN_SCOPE)} in scope for the posting cycle - "
        f"{', '.join(IN_SCOPE_TABLES)} - plus {len(OUT_OF_SCOPE)} out of "
        f"scope."
    )


def _assert_columns(
    table: str,
    columns: object,
    schema: Mapping[str, Mapping[str, ColumnType]],
) -> tuple[str, ...]:
    """Assert a dump's column list matches the frozen schema exactly.

    Same names, same order, same count. A mismatch means either the
    frozen schema was modified or the dump is stale, and both are drift
    rather than a difference worth diffing.

    Args:
        table: The in-scope table.
        columns: The `columns` value from the dump object.
        schema: The parsed column-type map.

    Returns:
        The column names.

    Raises:
        DumpShapeError: `columns` is not a list of strings, or does not
            match the schema.
    """
    if isinstance(columns, str) or not isinstance(columns, Sequence):
        raise DumpShapeError(
            f"`{table}`: a dump's `columns` must be a list of column "
            f"names; got {type(columns).__name__} ({columns!r})."
        )
    dumped = tuple(columns)
    for name in dumped:
        if not isinstance(name, str):
            raise DumpShapeError(
                f"`{table}`: every entry of `columns` must be a column "
                f"name as a string; got {type(name).__name__} "
                f"({name!r})."
            )
    declared = schema_columns(schema, table)
    if dumped != declared:
        specification = IN_SCOPE[table]
        raise DumpShapeError(
            f"`{table}`: the dump lists {len(dumped)} column(s) but the "
            f"frozen schema declares {len(declared)} "
            f"[{_SCHEMA_RELPATH}:L{specification.schema_line}], or the "
            f"order differs. The dump must carry the schema's ordinal "
            f"order exactly, because rows are positional. First "
            f"disagreement: {_first_difference(dumped, declared)}. Either "
            f"the dump is stale - taken before "
            f"harness/reset_db.sh re-applied the schema - or the frozen "
            f"artifact was modified, which Agent Action Plan section "
            f"0.8.1 calls a defect in the migration."
        )
    return dumped


def _first_difference(
    dumped: Sequence[str], declared: Sequence[str]
) -> str:
    """Describe the first position at which two column lists differ.

    Args:
        dumped: The dump's column list.
        declared: The frozen schema's column list.

    Returns:
        A short, deterministic description naming the position and both
        readings.
    """
    for index, (left, right) in enumerate(zip(dumped, declared)):
        if left != right:
            return (
                f"position {index} carries {left!r} but the schema "
                f"declares {right!r}"
            )
    if len(dumped) < len(declared):
        return (
            f"the dump stops after {len(dumped)} column(s); the schema "
            f"continues with {declared[len(dumped)]!r}"
        )
    if len(dumped) > len(declared):
        return (
            f"the schema stops after {len(declared)} column(s); the dump "
            f"continues with {dumped[len(declared)]!r}"
        )
    return "no positional difference, which means the counts agree"


def _assert_rows(
    table: str, dump: Mapping[str, Any], columns: Sequence[str], where: str
) -> tuple[Sequence[Any], ...]:
    """Assert a dump's row block is well formed.

    Args:
        table: The in-scope table.
        dump: The dump object.
        columns: Its column list, already validated.
        where: `"input"` or `"output"`, for the error messages.

    Returns:
        The rows, unchanged and in the order they arrived.

    Raises:
        DumpShapeError: `rows` is not a list of equal-length lists, or
            `row_count` disagrees with it.
    """
    rows = dump["rows"]
    if isinstance(rows, str) or not isinstance(rows, Sequence):
        raise DumpShapeError(
            f"`{table}`: the {where} dump's `rows` must be a list of "
            f"rows; got {type(rows).__name__}."
        )
    count = dump["row_count"]
    if isinstance(count, bool) or not isinstance(count, int):
        raise DumpShapeError(
            f"`{table}`: the {where} dump's `row_count` must be an "
            f"integer; got {type(count).__name__} ({count!r})."
        )
    if count != len(rows):
        raise DumpShapeError(
            f"`{table}`: the {where} dump's `row_count` is {count} but it "
            f"carries {len(rows)} row(s)."
        )
    for index, row in enumerate(rows):
        if isinstance(row, str) or not isinstance(row, Sequence):
            raise DumpShapeError(
                f"`{table}` row {index}: a row must be a list of values "
                f"positionally aligned with `columns`; got "
                f"{type(row).__name__}."
            )
        if len(row) != len(columns):
            raise DumpShapeError(
                f"`{table}` row {index}: {len(row)} value(s) against "
                f"{len(columns)} column(s). Rows are positional, so a "
                f"length mismatch makes every value in the row "
                f"unattributable."
            )
    return tuple(rows)


def _canonicalise_integer(
    value: object,
    *,
    table: str,
    column: str,
    declared: ColumnType,
) -> int:
    """Return an integer value unchanged, having refused anything else.

    THIS IS NOT A FOURTH JOB. An exact integer has no rendering to
    canonicalise: `[harness/dump_tables.py:L1443-L1444]` writes it as a
    JSON integer and a JSON integer is exact for every width the schema
    uses, the widest in scope being `bigint(11)`. The binary day-number
    dates in particular - `RUN-DAT` [mysql/ACASDB.sql:L1199],
    `ENTERED` / `PROOFED` / `POSTED` / `STORED`, both `IH-DAT`,
    `OI3-DAT`, `OI5-DAT`, `SALES-CREATE-DAT`, `PURCH-CREATE-DAT` and the
    rest - pass through here untouched, which is why job 3 never sees
    them.

    Args:
        value: The dumped value.
        table: The table it came from.
        column: The column it came from.
        declared: The column's declared type.

    Returns:
        The value, unchanged.

    Raises:
        NumericPolicyError: `value` is a binary floating-point number or a
            `bool` (rule R-2).
        UnexpectedValueTypeError: `value` is of some other type.
        SchemaParseError: `declared` is not an integer column.
    """
    if declared.kind != KIND_INTEGER:
        raise SchemaParseError(
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}], not an integer "
            f"width."
        )
    if isinstance(value, bool):
        raise NumericPolicyError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries the boolean {value!r}. JSON true/false is "
            f"not the integer the column holds, and no column of the "
            f"frozen schema can produce one."
        )
    if isinstance(value, float):
        raise NumericPolicyError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries a binary floating-point value ({value!r}). "
            f"Rule R-2 forbids binary floating point outright; the value "
            f"is refused, not converted."
        )
    if not isinstance(value, int):
        raise UnexpectedValueTypeError(
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}] but the dump carries "
            f"{type(value).__name__} ({value!r}). "
            f"[harness/dump_tables.py:L1443-L1444] writes every integer "
            f"width as a JSON integer."
        )
    return value


def _canonicalise_value(
    value: object,
    *,
    table: str,
    column: str,
    declared: ColumnType,
    row_index: int,
    findings: MutableSequence[DateTextFinding] | None,
) -> str | int:
    """Apply the jobs that the column's DECLARED type calls for.

    The dispatch is on the declared type and on the job 3 allow-list, and
    on nothing else - never on what the value looks like. There are
    exactly three transformations, and a value receives at most two of
    them: an allow-listed date-text column is a `char` column, so job 1
    removes its trailing spaces before job 3 examines its shape.

    Args:
        value: The dumped value.
        table: The in-scope table.
        column: The column name.
        declared: The column's declared type.
        row_index: The row's zero-based position, for a finding.
        findings: Where job 3's findings are appended, or `None` to
            discard them. `normalize_dump` stays pure either way: the
            collector is the caller's own, and nothing is read back from
            it.

    Returns:
        The canonical value.

    Raises:
        UnexpectedNullError: `value` is `None`.
        NumericPolicyError: Rule R-2's guard tripped.
        UnexpectedValueTypeError: The value's type does not match the
            column's class.
        DecimalScaleError: Job 2's information-loss guard tripped.
        SchemaParseError: The declared type is not one of the three
            classes.
    """
    if value is None:
        raise UnexpectedNullError(
            f"`{table}`.`{column}` row {row_index} is JSON null, but "
            f"every column of the frozen schema is declared NOT NULL. "
            f"Agent Action Plan section 0.6.2 explains why: each bridge "
            f"load paragraph initialises the host-variable group, \"so "
            f"unset fields become zero or space rather than SQL NULL\". A "
            f"null is genuinely new information, so it is reported loudly "
            f"and NEVER coalesced to zero, to a space or to an empty "
            f"string."
        )

    if declared.kind == KIND_CHAR:
        trimmed = canonicalise_char(
            value, table=table, column=column, declared=declared
        )
        specification = DATE_TEXT_COLUMNS.get((table, column))
        if specification is None:
            # Not allow-listed for job 3. `OI5-BATCH`, `OI3-BATCH`,
            # `PURCH-EXT`, `SALES-EXT` and `PASS-WORD` reach exactly here,
            # each for the reason recorded in `DATE_TEXT_EXCLUSIONS`.
            return trimmed
        outcome = canonicalise_date_text(
            trimmed,
            table=table,
            column=column,
            specification=specification,
        )
        if outcome.reason is not None and findings is not None:
            findings.append(
                DateTextFinding(
                    table=table,
                    column=column,
                    row_index=row_index,
                    value=outcome.value,
                    reason=outcome.reason,
                )
            )
        return outcome.value

    if declared.kind == KIND_DECIMAL:
        return canonicalise_decimal(
            value, table=table, column=column, declared=declared
        )

    if declared.kind == KIND_INTEGER:
        return _canonicalise_integer(
            value, table=table, column=column, declared=declared
        )

    raise SchemaParseError(
        f"`{table}`.`{column}` is declared {declared.sql_type} "
        f"[{_SCHEMA_RELPATH}:L{declared.line}], whose class "
        f"{declared.kind!r} is not one of {KIND_CHAR!r}, "
        f"{KIND_DECIMAL!r} or {KIND_INTEGER!r}."
    )


def normalize_dump(
    dump: Mapping[str, Any],
    schema: Mapping[str, Mapping[str, ColumnType]],
    *,
    findings: MutableSequence[DateTextFinding] | None = None,
) -> dict[str, Any]:
    """Canonicalise one dump object. Pure, and shape-preserving.

    THE SHAPE IS PRESERVED EXACTLY: the same five keys in the same order,
    the same `table` and `primary_key`, the same `columns` list in the
    same order, the same `row_count`, and the same rows IN THE SAME ORDER.
    Only the VALUES inside `rows` are canonicalised. Rows are never
    re-ordered - they arrive primary-key-ordered from SQL and Agent Action
    Plan section 0.6.6 records that the dump is
    `SELECT * FROM <table> ORDER BY <primary key>` "with no tie-breaking
    logic" - and no column is added, removed or moved, and no metadata key
    is introduced.

    The function reads no environment variable, opens no file, touches no
    global and depends on no ambient decimal context, so it is
    deterministic given `(dump, schema)` and safely reusable. The input
    object is not mutated.

    Args:
        dump: A dump object as `harness/dump_tables.py` writes it.
        schema: The parsed column-type map from `load_schema`.
        findings: An optional collector for job 3's findings, appended to
            in row order and then column order. `None` discards them.

    Returns:
        A new dump object with canonical values.

    Raises:
        DumpShapeError: The dump does not have the shape
            `harness/dump_tables.py` writes, or disagrees with the frozen
            schema on the column list.
        TableNotInScopeError: The dump is of an out-of-scope table.
        UnknownTableError: The dump names a table the schema does not
            define.
        UnexpectedNullError: A value is JSON null.
        NumericPolicyError: Rule R-2's guard tripped on a value.
        UnexpectedValueTypeError: A value's type does not match its
            column's class.
        DecimalScaleError: Job 2's information-loss guard tripped.
        SchemaParseError: A declared type is unusable.
    """
    _assert_dump_keys(dump, "input")
    table = _assert_table_in_scope(dump["table"])
    columns = _assert_columns(table, dump["columns"], schema)

    specification = IN_SCOPE[table]
    primary_key = dump["primary_key"]
    if primary_key != specification.primary_key:
        raise DumpShapeError(
            f"`{table}`: the dump names {primary_key!r} as its primary "
            f"key; the frozen schema declares "
            f"`{specification.primary_key}` "
            f"[{_SCHEMA_RELPATH}:L{specification.schema_line}]. The key "
            f"is what the dump's row order came from, so a disagreement "
            f"means the two sides were not ordered alike."
        )
    if specification.primary_key not in columns:
        raise DumpShapeError(
            f"`{table}`: the primary key `{specification.primary_key}` is "
            f"not among the dump's columns."
        )

    rows = _assert_rows(table, dump, columns, "input")
    declared_types = [
        column_type(schema, table, column) for column in columns
    ]

    canonical_rows: list[list[str | int]] = []
    for row_index, row in enumerate(rows):
        canonical_rows.append(
            [
                _canonicalise_value(
                    value,
                    table=table,
                    column=column,
                    declared=declared,
                    row_index=row_index,
                    findings=findings,
                )
                # `strict=True` states the invariant `_assert_rows`
                # already enforced: rows are POSITIONAL, so a length
                # mismatch would silently mis-attribute every value
                # after it rather than fail.
                for value, column, declared in zip(
                    row, columns, declared_types, strict=True
                )
            ]
        )

    # Rebuilt in `DUMP_KEYS` order rather than copied, so the key order is
    # asserted by construction as well as by `_assert_dump_keys` below.
    normalized: dict[str, Any] = {
        "table": table,
        "primary_key": specification.primary_key,
        "columns": list(columns),
        "row_count": len(canonical_rows),
        "rows": canonical_rows,
    }

    # The output invariants, re-asserted. Cheap, and they turn any future
    # mistake in the code above into a loud failure rather than a silent
    # one that a diff would blame on the migration.
    _assert_dump_keys(normalized, "output")
    _assert_rows(table, normalized, columns, "output")
    if normalized["row_count"] != dump["row_count"]:
        raise DumpShapeError(
            f"`{table}`: normalisation changed the row count from "
            f"{dump['row_count']} to {normalized['row_count']}. It must "
            f"change values only."
        )
    if tuple(normalized["columns"]) != tuple(columns):
        raise DumpShapeError(
            f"`{table}`: normalisation changed the column list. It must "
            f"change values only."
        )

    return normalized


# ---------------------------------------------------------------------------
#  THE JSON BOUNDARY
#
#  Deterministic and atomic, with `harness/dump_tables.py`'s serialisation
#  parameters pinned rather than defaulted, so a normalised file differs
#  from its input in VALUES ONLY:
#
#      indent=2, ensure_ascii=True, sort_keys=False,
#      separators=(",", ": "), LF newlines, UTF-8, one trailing newline
#
#  `ensure_ascii=True` is deliberate: it makes the bytes independent of any
#  locale or filesystem-encoding difference between the two runs, which is
#  what `tests/determinism/test_two_runs_byte_identical.py` rests on. Do not
#  "improve" it to False.
#
#  Each file is written under a temporary name IN ITS OWN DIRECTORY and
#  moved into place with `os.replace`, which is what makes the move atomic,
#  so `harness/diff_states.py` can never read a partial file.
# ---------------------------------------------------------------------------


def dump_filename(table: str) -> str:
    """Return the file name a table's dump is stored under.

    Args:
        table: The table name, spelled exactly as the frozen schema
            spells it, hyphens included.

    Returns:
        `<TABLE>.json`, matching
        [harness/dump_tables.py:L1667] exactly.
    """
    return f"{table}{_DUMP_SUFFIX}"


def read_dump(path: Path | str) -> dict[str, Any]:
    """Read one dump file.

    Args:
        path: The `<TABLE>.json` file to read.

    Returns:
        The parsed dump object. Its shape is NOT validated here;
        `normalize_dump` does that, so a caller reading a file and a
        caller holding an object in memory go through the same
        assertions.

    Raises:
        DumpReadError: The file could not be read, is not valid UTF-8
            JSON, or does not parse to a JSON object.
    """
    target = Path(path)
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise DumpReadError(
            f"could not read the dump {target}: {exc}"
        ) from exc
    try:
        parsed = json.loads(text)
    except ValueError as exc:
        raise DumpReadError(
            f"{target} is not valid JSON: {exc}. It should be a dump "
            f"written by harness/dump_tables.py."
        ) from exc
    if not isinstance(parsed, dict):
        raise DumpReadError(
            f"{target} parses to {type(parsed).__name__}, not a JSON "
            f"object. A dump is an object with the five keys "
            f"{list(DUMP_KEYS)}."
        )
    return parsed


def write_dump(dump: Mapping[str, Any], path: Path | str) -> Path:
    """Serialise one dump object, deterministically and atomically.

    Args:
        dump: A normalised dump object, as `normalize_dump` returns.
        path: Where to write it. Parent directories are created.

    Returns:
        The path written.

    Raises:
        DumpShapeError: `dump` does not carry exactly the five keys in
            order, or `row_count` disagrees with `rows`.
        DumpWriteError: The file could not be written or moved.
    """
    _assert_dump_keys(dump, "output")
    if dump["row_count"] != len(dump["rows"]):
        raise DumpShapeError(
            f"row_count {dump['row_count']!r} does not equal the "
            f"{len(dump['rows'])} row(s) of table {dump['table']!r}."
        )

    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the output directory {target.parent}: "
            f"{exc}"
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
            # `json.dump` writes no trailing newline. Exactly one is
            # added, so every file ends the same way.
            handle.write("\n")
        os.replace(temporary, target)
    except OSError as exc:
        # Leave nothing half-written behind for diff_states.py to read.
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            # Best effort only; the real failure is re-raised below and
            # must not be masked by a cleanup failure.
            pass
        raise DumpWriteError(
            f"could not write the normalised dump for table "
            f"{dump['table']!r} to {target}: {exc}"
        ) from exc

    return target


# ---------------------------------------------------------------------------
#  ONE DIRECTORY TO ANOTHER, SEQUENTIALLY  (rule R-3)
#
#  One table at a time, in a plain loop, in ascending table-name order.
#  There is no thread, no event loop, no process pool and no
#  synchronisation primitive anywhere in this file.
#
#  ONLY `<TABLE>.json` FILES ARE WRITTEN into the destination - no
#  manifest, no log, no marker - because `harness/dump_tables.py` records
#  that constraint for this module explicitly: normalize.py "reads a
#  directory", so anything else left there would be taken for a dump.
# ---------------------------------------------------------------------------


def discover_tables(src_dir: Path | str) -> tuple[str, ...]:
    """List the tables a source directory holds dumps for.

    Args:
        src_dir: The directory `harness/dump_tables.py` wrote into.

    Returns:
        The table names, ASCENDING - sorted once, deterministically, so
        two runs process the same tables in the same order (rule R-6).

    Raises:
        DumpReadError: The directory does not exist, or is not a
            directory.
    """
    source = Path(src_dir)
    if not source.is_dir():
        raise DumpReadError(
            f"{source} is not a directory. It should be the directory "
            f"harness/dump_tables.py wrote its <TABLE>.json files into, "
            f"for example $ACAS_OUT/<scenario>/cobol."
        )
    names: list[str] = []
    for entry in source.iterdir():
        name = entry.name
        # Skip the temporary files write_dump may have left behind after a
        # failure - they end `.json.tmp`, not `.json` - and skip any other
        # hidden file, which pathlib's glob would otherwise match.
        if name.startswith(_TEMP_PREFIX):
            continue
        if not name.endswith(_DUMP_SUFFIX):
            continue
        if not entry.is_file():
            continue
        names.append(name[: -len(_DUMP_SUFFIX)])
    return tuple(sorted(names))


def _is_same_directory(left: Path, right: Path) -> bool:
    """Report whether two paths name the same directory.

    `Path.resolve` is non-strict, so it normalises `..` segments and
    symlinks for paths that do not exist yet - which the destination
    usually does not on a first run.

    Args:
        left: The first path.
        right: The second path.

    Returns:
        Whether they resolve to the same location.
    """
    return left.resolve() == right.resolve()


def normalize_tree(
    src_dir: Path | str,
    dst_dir: Path | str,
    schema: Mapping[str, Mapping[str, ColumnType]],
    *,
    tables: Sequence[str] | None = None,
    findings: MutableSequence[DateTextFinding] | None = None,
) -> list[str]:
    """Normalise every dump in one directory into another.

    Args:
        src_dir: The directory of `<TABLE>.json` dumps to read.
        dst_dir: The directory to write the normalised dumps into. It is
            created if it does not exist. It must not be the source.
        schema: The parsed column-type map from `load_schema`.
        tables: An optional explicit table list; every entry must have a
            dump in `src_dir`. `None` normalises every dump present.
        findings: An optional collector for job 3's findings.

    Returns:
        The table names normalised, in the order processed - ascending.

    Raises:
        DumpReadError: The source is missing, a requested dump is absent,
            or a file could not be read.
        DumpShapeError: A dump does not have the expected shape, or its
            file name disagrees with its `table` key.
        TableNotInScopeError: A dump is of an out-of-scope table.
        UnknownTableError: A dump names an unknown table.
        UnexpectedNullError: A dump carries a JSON null.
        NumericPolicyError: Rule R-2's guard tripped.
        UnexpectedValueTypeError: A value's type is wrong for its column.
        DecimalScaleError: Job 2's information-loss guard tripped.
        DumpWriteError: An output file could not be written.
        ValueError: The source and the destination are the same
            directory, which would overwrite the dumps being compared.
    """
    source = Path(src_dir)
    destination = Path(dst_dir)

    if _is_same_directory(source, destination):
        raise ValueError(
            f"the source and the destination are the same directory "
            f"({source}). Normalising in place would overwrite the dump "
            f"harness/dump_tables.py produced, and the comparison needs "
            f"both the raw dump and the normalised one."
        )

    available = discover_tables(source)

    if tables is None:
        selected: tuple[str, ...] = available
    else:
        selected = tuple(tables)
        missing = [
            table for table in selected if table not in set(available)
        ]
        if missing:
            raise DumpReadError(
                f"{source} holds no dump for {', '.join(missing)}. It "
                f"holds {len(available)} dump(s)"
                + (f": {', '.join(available)}." if available else ".")
            )

    normalized: list[str] = []
    for table in selected:
        source_path = source / dump_filename(table)
        dump = read_dump(source_path)
        named = dump.get("table")
        if named != table:
            raise DumpShapeError(
                f"{source_path} is named for table {table!r} but its "
                f"`table` key says {named!r}. The file name and the key "
                f"must agree, or a dump would be normalised - and later "
                f"compared - under the wrong schema."
            )
        canonical = normalize_dump(dump, schema, findings=findings)
        target = write_dump(canonical, destination / dump_filename(table))
        normalized.append(table)
        _progress(
            f"  {table:<24} {canonical['row_count']:>7} row(s)  "
            f"{len(canonical['columns']):>3} column(s)  -> {target}"
        )

    return normalized


# ---------------------------------------------------------------------------
#  THE JOB 3 FINDINGS REPORT  (rule R-6)
#
#  Loud, deterministic, and OUTSIDE the compared trees. It never lands in
#  the destination directory and never under `$ACAS_OUT/<scenario>/`,
#  following the convention `harness/reset_db.sh` states at
#  [harness/reset_db.sh:L150-L151]: its run log goes to `$ACAS_OUT/reset/`,
#  "which is never part of a comparison".
#
#  Its purpose is to send an operator to the ORACLE. A date-text form this
#  module does not recognise is a question about what the compiled
#  program actually stores, and rule R-6 says the compiled program answers
#  it - not a tweak to this normaliser.
# ---------------------------------------------------------------------------

_REPORT_HEADER: Final[str] = """\
harness/normalize.py - job 3 date-text findings

Every value listed below was passed through UNCHANGED. None was expanded
from two digits to four, contracted from four to two, re-separated or
re-padded: doing any of that could make a genuine divergence between the
two sides compare equal, which Agent Action Plan section 0.6.6 forbids -
"a non-empty diff is always a real behavioral difference and never an
artefact of the comparison".

A finding is a QUESTION FOR THE COMPILED ORACLE (rule R-6), not a defect
in this tool and not a reason to widen its recogniser. Record the answer
in docs/migration/ambiguity-resolutions.md.

The canonical shapes, and where they come from:
  NN/NN/NN  the eight-character date text. [copybooks/wspost.cob:L18]
            declares `03 Post-Date pic x(8).` and
            [common/irspostingMT.cbl:L982-L987] slices it at (1:2), (4:2)
            and (7:2), which puts the separators at 3 and 6.
  NNNN      the four-character period. [copybooks/wssystem.cob:L145] and
            [copybooks/wssl.cob:L64] declare it `pic 9(4)`.

The five allow-listed columns, and no others:
  GLPOSTING-REC.POST-DAT          char(8)  [mysql/ACASDB.sql:L158]
  IRSPOSTING-REC.POST4-DAT        char(8)  [mysql/ACASDB.sql:L277]
  PSIRSPOST-REC.IRS-POST-DAT      char(8)  [mysql/ACASDB.sql:L369]
  SALEDGER-REC.SALES-STATS-DATE   char(4)  [mysql/ACASDB.sql:L981]
  SYSTEM-REC.STATS-DATE-PERIOD    char(4)  [mysql/ACASDB.sql:L1236]
"""


def render_report(
    findings: Sequence[DateTextFinding],
    *,
    source: str | None = None,
) -> str:
    """Render the job 3 findings as deterministic text.

    Grouped by table, then column, then row index, all ascending, so the
    same findings always render to the same bytes. The text carries no
    wall-clock reading, no host name, no process identifier and no tool
    version.

    Args:
        findings: The findings collected during normalisation.
        source: The source directory as it was given on the command line,
            recorded so an operator can tell which side a report is for.
            Omitted entirely when `None`.

    Returns:
        The report text, ending in a newline.
    """
    lines: list[str] = [_REPORT_HEADER]
    if source is not None:
        lines.append(f"source: {source}")
        lines.append("")

    if not findings:
        lines.append(
            "No findings: every value in every allow-listed date-text "
            "column matched its canonical shape."
        )
        lines.append("")
        return "\n".join(lines)

    ordered = sorted(
        findings,
        key=lambda finding: (
            finding.table,
            finding.column,
            finding.row_index,
        ),
    )
    lines.append(f"{len(ordered)} finding(s).")
    lines.append("")

    current: tuple[str, str] | None = None
    for finding in ordered:
        heading = (finding.table, finding.column)
        if heading != current:
            current = heading
            total = sum(
                1
                for candidate in ordered
                if (candidate.table, candidate.column) == heading
            )
            lines.append(
                f"{finding.table}.{finding.column}  -  {total} finding(s)"
            )
        lines.append(
            f"  row {finding.row_index}: {finding.value!r} - "
            f"{finding.reason}"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
#  THE COMMAND LINE
#
#  Two flag spellings for the source and the destination, because this
#  repository documents two and neither is a guess:
#
#    * the committed Compose recipe, verbatim
#      [harness/docker-compose.yml:L269] and [L273]:
#          harness/normalize.py --in /out/cobol  --out /out/cobol.norm
#          harness/normalize.py --in /out/python --out /out/python.norm
#    * the file specification for this module, which names `--src` and
#      `--dst` with a `.normalized` default suffix, plus the composed
#      `<out-dir>/<scenario>/<side>/` layout.
#
#  `--in` and `--src` are one option; so are `--out` and `--dst`.
#  `allow_abbrev=False` so `--out` can never be confused with `--out-dir`
#  and so no abbreviation of any option is silently accepted.
# ---------------------------------------------------------------------------

_EPILOGUE: Final[str] = """\
layouts
  --src DIR [--dst DIR]        (--in / --out are the same two options)
      reads DIR/<TABLE>.json, writes DIR.normalized/<TABLE>.json unless
      --dst is given. The committed eight-stage recipe passes both:
      `--in /out/cobol --out /out/cobol.norm`
      [harness/docker-compose.yml:L269]
  --scenario NAME --side {cobol|python} [--out-dir DIR]
      reads  <DIR>/<NAME>/<side>/<TABLE>.json
      writes <DIR>/<NAME>/<side>.normalized/<TABLE>.json
      (DIR defaults to $ACAS_OUT)

the three canonicalisation jobs, and there is no fourth
  1  trailing ASCII spaces in char(n) columns - trailing only, never
     leading, because a COBOL alphanumeric MOVE pads on the RIGHT. The
     bridge itself trims: [common/nominalMT.cbl:L1065-L1067].
  2  decimal(p,s) values re-rendered at the DECLARED scale. Never two by
     assumption - the schema's scales include 2, 4 and 0. A value with
     more places than its column declares is an ERROR, not something to
     round away.
  3  the five allow-listed date-text columns, RENDERING ONLY. A
     two-digit component is never expanded to four and four is never
     contracted to two; anything that does not match its canonical shape
     is passed through unchanged and REPORTED for the oracle to settle.

environment
  ACAS_REPO supplies the default --schema, $ACAS_REPO/mysql/ACASDB.sql.
  ACAS_OUT  supplies the default --out-dir and the default --report
            directory, $ACAS_OUT/normalize/. Nothing is ever written
            under ACAS_REPO: it is mounted read-only
            [harness/docker-compose.yml:L591].

exit codes
  0 normalised   80 usage        81 precondition   83 scope
  84 drift       85 numeric      86 write
  82 is database and is never returned: no database link is opened.

this tool reads and writes JSON files only. It issues no SQL, needs no
driver, invokes no COBOL, imports nothing from the shipped package, runs
strictly sequentially, and writes no byte of non-reproducible content:
two runs over the same input produce byte-identical output.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        The parser, with abbreviation disabled.
    """
    parser = argparse.ArgumentParser(
        prog="harness/normalize.py",
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Canonicalise a table-state dump so that only real "
            "behavioural differences survive: fixed-char trailing "
            "spaces, decimal scale rendering, and the two-digit versus "
            "four-digit date text forms. Stage 4 of the eight-stage "
            "parity protocol."
        ),
        epilog=_EPILOGUE,
    )

    parser.add_argument(
        "--src",
        "--in",
        dest="src",
        metavar="DIR",
        help=(
            "the directory of <TABLE>.json dumps to read, as "
            "harness/dump_tables.py wrote them. --in is the same option, "
            "and is the spelling the committed Compose recipe uses "
            "[harness/docker-compose.yml:L269]."
        ),
    )
    parser.add_argument(
        "--dst",
        "--out",
        dest="dst",
        metavar="DIR",
        help=(
            "the directory to write the normalised dumps into; defaults "
            "to the source with '"
            + _NORMALIZED_SUFFIX
            + "' appended. --out is the same option."
        ),
    )
    parser.add_argument(
        "--scenario",
        metavar="NAME",
        help=(
            "the scenario name, used only to build the paths "
            "<out-dir>/<scenario>/<side>/ and "
            "<out-dir>/<scenario>/<side>"
            + _NORMALIZED_SUFFIX
            + "/. Requires --side."
        ),
    )
    parser.add_argument(
        "--side",
        choices=SIDES,
        help=(
            "which side of the comparison this dump represents. Requires "
            "--scenario. The side is recorded in the PATH, never in a "
            "file."
        ),
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        help=(
            "the root under which <scenario>/<side>/ is composed; "
            "defaults to $ACAS_OUT."
        ),
    )
    parser.add_argument(
        "--schema",
        metavar="PATH",
        help=(
            "the frozen schema to read column types from; defaults to "
            "$ACAS_REPO/mysql/ACASDB.sql. Read, never written."
        ),
    )
    parser.add_argument(
        "--tables",
        metavar="TABLE[,TABLE...]",
        help=(
            "restrict to these tables, comma separated, spelled exactly "
            "as mysql/ACASDB.sql spells them, hyphens included. The "
            "default is every dump present in the source."
        ),
    )
    parser.add_argument(
        "--report",
        metavar="PATH",
        help=(
            "where the job 3 findings report is written. It must lie "
            "OUTSIDE the source and the destination, because only "
            "<TABLE>.json files may appear there; defaults to "
            "$ACAS_OUT/"
            + _REPORT_SUBDIR
            + "/<source>-"
            + _REPORT_FILENAME
            + ", named for the source directory so the two sides do not "
            "overwrite one another. Findings always go to stderr as well."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the per-table progress notes on stderr.",
    )

    return parser


def _resolve_directories(
    arguments: argparse.Namespace, env: Mapping[str, str]
) -> tuple[Path, Path, str | None]:
    """Work out which directory is read and which is written.

    Args:
        arguments: The parsed command line.
        env: The environment, for `$ACAS_OUT`.

    Returns:
        The source, the destination, and the scenario name when the
        composed layout was used (`None` otherwise). The scenario name is
        needed only to keep the findings report out of the scenario's own
        directory.

    Raises:
        ValueError: The layout arguments are contradictory or incomplete.
    """
    composed = arguments.scenario is not None or arguments.side is not None

    if arguments.src is not None:
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
                f"--src/--in names the source directory outright, so it "
                f"cannot be combined with {' or '.join(conflicting)}. Use "
                f"either `--src DIR [--dst DIR]` "
                f"[harness/docker-compose.yml:L269] or `--scenario NAME "
                f"--side SIDE [--out-dir DIR]`."
            )
        source = Path(arguments.src)
        if arguments.dst is not None:
            return source, Path(arguments.dst), None
        return (
            source,
            source.with_name(source.name + _NORMALIZED_SUFFIX),
            None,
        )

    if not composed:
        raise ValueError(
            "give either `--src DIR [--dst DIR]` - `--in` and `--out` are "
            "the same two options - or `--scenario NAME --side "
            f"{{{'|'.join(SIDES)}}}` for the "
            "<out-dir>/<scenario>/<side>/ layout."
        )

    if arguments.scenario is None or arguments.side is None:
        raise ValueError(
            "--scenario and --side belong together: give both for the "
            "<out-dir>/<scenario>/<side>/ layout, or neither and use "
            "--src instead."
        )

    scenario = arguments.scenario
    if not scenario or scenario in {".", ".."} or (
        set(scenario) & set("/\\")
    ):
        raise ValueError(
            f"--scenario must be a plain directory name, not a path; got "
            f"{scenario!r}. It names a scenario such as clean_batch_gl."
        )

    root = arguments.out_dir
    if root is None:
        root = env.get(_ENV_OUT)
    if not root:
        raise ValueError(
            f"neither --out-dir nor {_ENV_OUT} is set, so the output root "
            f"is unknown. The Compose service sets {_ENV_OUT}: /out "
            f"[harness/docker-compose.yml:L689]."
        )
    if arguments.dst is not None:
        raise ValueError(
            "--dst/--out cannot be combined with --scenario and --side: "
            "the composed layout derives both directories from "
            "--out-dir, the scenario and the side."
        )

    base = Path(root) / scenario
    return (
        base / arguments.side,
        base / (arguments.side + _NORMALIZED_SUFFIX),
        scenario,
    )


def _resolve_report_path(
    requested: str | None,
    *,
    source: Path,
    destination: Path,
    scenario: str | None,
    env: Mapping[str, str],
) -> Path | None:
    """Work out where the findings report goes, or that it goes nowhere.

    Args:
        requested: The `--report` value, or `None`.
        source: The source directory.
        destination: The destination directory.
        scenario: The scenario name for the composed layout, or `None`.
        env: The environment, for `$ACAS_OUT`.

    Returns:
        The report path, or `None` when no root is derivable and none was
        requested - in which case the findings still go to stderr. The
        defaulted name carries the source directory's label, so the
        recipe's two invocations do not overwrite one another.

    Raises:
        ReportPathError: The requested path lies inside the source, the
            destination, or the scenario's own directory. Only
            `<TABLE>.json` files may appear in a compared tree, and
            nothing that varies between the two sides may appear under
            `$ACAS_OUT/<scenario>/`, which the determinism test compares.
    """
    if requested is not None:
        candidate = Path(requested)
        _assert_report_outside(candidate, source, destination, scenario)
        return candidate

    root = env.get(_ENV_OUT)
    if not root:
        return None
    candidate = (
        Path(root)
        / _REPORT_SUBDIR
        / f"{_report_label(source)}-{_REPORT_FILENAME}"
    )
    _assert_report_outside(candidate, source, destination, scenario)
    return candidate


def _report_label(source: Path) -> str:
    """Derive a portable file-name label from a source directory.

    Runs of ASCII alphanumerics from the directory's own name, joined with
    a hyphen: `/out/cobol` gives `cobol` and `/out/clean_batch_gl/python`
    gives `python`, so the recipe's two invocations
    [harness/docker-compose.yml:L269], [harness/docker-compose.yml:L273]
    write two reports rather than one overwriting the other.

    Args:
        source: The source directory. It need not exist; `Path.resolve`
            is non-strict and only normalises the path.

    Returns:
        The label, or `_REPORT_DEFAULT_LABEL` when the name yields none -
        which happens only for a filesystem root.
    """
    parts = _REPORT_LABEL_RE.findall(source.resolve().name)
    if not parts:
        return _REPORT_DEFAULT_LABEL
    return "-".join(parts)


def _assert_report_outside(
    candidate: Path,
    source: Path,
    destination: Path,
    scenario: str | None,
) -> None:
    """Assert a report path is not inside a compared tree.

    Args:
        candidate: The report path.
        source: The source directory.
        destination: The destination directory.
        scenario: The scenario name for the composed layout, or `None`.

    Raises:
        ReportPathError: It is inside one of them.
    """
    resolved = candidate.resolve()
    for directory, description in (
        (source, "the source directory"),
        (destination, "the destination directory"),
    ):
        if _is_inside(resolved, directory.resolve()):
            raise ReportPathError(
                f"the findings report {candidate} would land inside "
                f"{description} ({directory}). Only <TABLE>.json files "
                f"may appear there - harness/normalize.py is invoked on a "
                f"DIRECTORY [harness/docker-compose.yml:L269], so any "
                f"other file there would be taken for a dump. Put the "
                f"report outside, as harness/reset_db.sh puts its log in "
                f"$ACAS_OUT/reset/ [harness/reset_db.sh:L150-L151]."
            )
    if scenario is not None:
        scenario_directory = destination.parent.resolve()
        if _is_inside(resolved, scenario_directory):
            raise ReportPathError(
                f"the findings report {candidate} would land inside the "
                f"scenario directory {destination.parent}. Nothing that "
                f"can vary between the two sides may appear there: "
                f"tests/determinism/test_two_runs_byte_identical.py "
                f"compares that tree byte for byte (rule R-6)."
            )


def _is_inside(candidate: Path, directory: Path) -> bool:
    """Report whether a resolved path lies at or under a directory.

    Args:
        candidate: The resolved path to test.
        directory: The resolved directory.

    Returns:
        Whether `candidate` is `directory` itself or beneath it.
    """
    return candidate == directory or directory in candidate.parents


def _parse_table_selection(
    selection: str | None, source: Path
) -> tuple[str, ...] | None:
    """Parse and validate the `--tables` value.

    Args:
        selection: The comma-separated value, or `None`.
        source: The source directory, for the error message.

    Returns:
        The requested table names, or `None` for "every dump present".

    Raises:
        ValueError: The value is empty or malformed.
        TableNotInScopeError: A named table is out of scope.
        UnknownTableError: A named table is not in the frozen schema.
    """
    if selection is None:
        return None
    names = [part.strip() for part in selection.split(",")]
    named = [name for name in names if name]
    if not named:
        raise ValueError(
            f"--tables was given but names no table. Spell each name "
            f"exactly as {_SCHEMA_RELPATH} spells it, hyphens included, "
            f"and separate them with commas; omit --tables to normalise "
            f"every dump in {source}."
        )
    for name in named:
        # Reuses the same scope gate the dumps go through, so a typo and a
        # deliberately out-of-scope request are refused the same way.
        _assert_table_in_scope(name)
    # De-duplicated, and ascending, so the run order does not depend on
    # how the operator happened to type the list (rule R-6).
    return tuple(sorted(set(named)))


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
        `EX_SCOPE`, `EX_DRIFT`, `EX_NUMERIC`, `EX_WRITE`.
    """
    global _QUIET

    parser = build_parser()
    arguments = parser.parse_args(argv)
    _QUIET = bool(arguments.quiet)
    env: Mapping[str, str] = os.environ

    try:
        source, destination, scenario = _resolve_directories(
            arguments, env
        )
    except ValueError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_USAGE

    try:
        report_path = _resolve_report_path(
            arguments.report,
            source=source,
            destination=destination,
            scenario=scenario,
            env=env,
        )
    except ReportPathError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_USAGE

    try:
        selection = _parse_table_selection(arguments.tables, source)
    except (TableNotInScopeError, UnknownTableError) as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_SCOPE
    except ValueError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_USAGE

    try:
        schema = load_schema(arguments.schema, env=env)
    except SchemaFileError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_PRECONDITION
    except SchemaParseError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_DRIFT

    _progress(
        f"harness/normalize.py: canonicalising {source} -> {destination}"
    )

    findings: list[DateTextFinding] = []
    try:
        normalized = normalize_tree(
            source,
            destination,
            schema,
            tables=selection,
            findings=findings,
        )
    except (TableNotInScopeError, UnknownTableError) as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_SCOPE
    except (DumpShapeError, SchemaParseError) as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_DRIFT
    except (
        NumericPolicyError,
        UnexpectedValueTypeError,
        UnexpectedNullError,
        DecimalScaleError,
    ) as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_NUMERIC
    except DumpWriteError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_WRITE
    except DumpReadError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_PRECONDITION
    except ValueError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_USAGE

    if not normalized:
        print(
            f"harness/normalize.py: {source} holds no <TABLE>.json dump "
            f"to normalise. harness/dump_tables.py writes one file per "
            f"table; an empty source means the dump stage did not run, "
            f"not that the tables were empty - a table with no rows still "
            f"produces a file with \"row_count\": 0.",
            file=sys.stderr,
        )
        return EX_PRECONDITION

    exit_code = EX_OK
    report = render_report(findings, source=str(source))
    if findings:
        # Loud on stderr as well as in the file: a date-text form this
        # module does not recognise is a question for the compiled oracle
        # (rule R-6), and an operator who never opens the file must still
        # see it.
        print(report, file=sys.stderr)
    if report_path is not None:
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open(
                "w", encoding="utf-8", newline="\n"
            ) as handle:
                handle.write(report)
        except OSError as exc:
            print(
                f"harness/normalize.py: could not write the findings "
                f"report to {report_path}: {exc}",
                file=sys.stderr,
            )
            exit_code = EX_WRITE
        else:
            _progress(
                f"harness/normalize.py: {len(findings)} job 3 finding(s) "
                f"recorded in {report_path}"
            )
    elif findings:
        print(
            f"harness/normalize.py: no report file was written because "
            f"neither --report nor {_ENV_OUT} is set. The findings above "
            f"are the whole record.",
            file=sys.stderr,
        )

    _progress(
        f"harness/normalize.py: normalised {len(normalized)} table(s) "
        f"into {destination}"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
