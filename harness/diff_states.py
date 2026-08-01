#!/usr/bin/env python3
"""Compare two normalised dumps. AN EMPTY DIFF IS THE PASS CONDITION.

Stage 8 of the eight-stage parity protocol, and the last word in it.
Agent Action Plan section 0.3.2 fixes the stage order - "seed, run, dump,
normalize, reset, run, dump, diff" - and this module is the diff.

    stage 1  seed        harness/seed.sh              (COBOL *LD loaders)
    stage 2  run  COBOL  harness/run_cobol_scenario.sh
    stage 3  dump        harness/dump_tables.py   -> .../cobol
    stage 4  normalize   harness/normalize.py     -> .../cobol.norm
    stage 5  reset       harness/reset_db.sh          (+ re-seed)
    stage 6  run  Python harness/run_python_scenario.sh
    stage 7  dump        harness/dump_tables.py   -> .../python
    stage 8  normalize   harness/normalize.py     -> .../python.norm
    stage 8  diff        THIS MODULE              -> MUST be EMPTY

THIS MODULE IS THE ACCEPTANCE CRITERION
=======================================
Agent Action Plan section 0.8.5 states the criterion, verbatim:

    "Scenario state parity. For each scenario: seed identically through
    the maintainer's load programs, run the compiled cycle, dump the
    affected tables ordering-normalised, reset, run the Python cycle,
    dump again - and the diff must be empty. Section 0.6.6 establishes
    that the dump is deterministic by construction, so a non-empty diff
    is always a real behavioral difference and never an artefact of the
    comparison."

And section 0.1.1 makes the same sentence the operational definition of
the whole engagement, verbatim:

    "'exact' is defined operationally as the ordering-normalized diff of
    affected database tables after a Python run versus a COBOL run
    against an identical seed must be empty."

So this module is the judge. Its exit code is the verdict for every one
of the eight scenarios, and docs/migration/scenario-diff-evidence.md is
built from its output. It is written so that its verdict cannot be wrong
in either direction.

THE EXIT-CODE CONTRACT  (rule R-6, non-negotiable)
==================================================
    0   The two trees are IDENTICAL. stdout is EMPTY - not a banner, not
        a summary, not "no differences found". Zero bytes. Agent Action
        Plan section 0.8.5: "the diff must be empty."
    1   A REAL DIFFERENCE was found. A deterministic report goes to
        stdout, and to --out when one is given.
    2   The comparison COULD NOT BE PERFORMED - a missing tree, a missing
        table file, a malformed dump, a shape mismatch, a duplicate
        primary key, a float or a null in the input, a usage error.

Exit 2 is NEVER conflated with exit 0. An inability to compare is not a
pass, and treating it as one is the single most dangerous defect this
module could carry.

Nor is the exit status ever unconditional. Two frozen build scripts in
this repository end with a bare `exit 0` - [comp-all.sh:L45] and
[common/comp-common.sh:L59] - so their exit status is not a success
signal, which is why harness/build_oracle.sh has to scan their output for
errors instead. Those are defects the harness works AROUND (rule R-4, so
they are reproduced rather than repaired at the source); the shape is
deliberately not reproduced HERE, in the one module whose exit code is
the verdict.

The 80+ exit band the sibling harness modules use - harness/seed.sh,
harness/reset_db.sh, harness/dump_tables.py, harness/normalize.py all map
their failures onto EX_USAGE 80 and upwards - is deliberately NOT used
here. Those modules exit 0 for "I did my job"; this one exits 0 for "the
migration is exact", and exit 1 has to mean "difference found" rather
than an unrelated failure class. The file specification for this module
fixes 0/1/2, and that is what is implemented.

THE TWO WAYS THIS MODULE COULD BE WRONG
=======================================
A FALSE PASS is the worse of the two, because nothing downstream would
catch it: there is no correct answer other than what the compiled COBOL
produced, so a wrongly-empty diff certifies a broken migration. The
plausible routes to one are all closed explicitly:

  * a missing or unreadable tree           -> MissingTreeError,   exit 2
  * a missing table file on one side       -> a reported DIFFERENCE
  * both sides missing a requested table   -> MissingTableFileError, 2
  * an empty table selection               -> EmptyComparisonError, 2
  * a shape mismatch in a dump             -> DumpShapeError,     exit 2
  * comparing a tree with ITSELF           -> SameTreeError,      exit 2
  * a float or a null in a value           -> raised, never coerced, 2

A FALSE FAIL is less dangerous but would waste the oracle's time. Its two
plausible routes are also closed: rows are aligned BY PRIMARY KEY and
never by position, and the module refuses to compare raw dumps, because
raw dumps still carry the representation artefacts harness/normalize.py
exists to remove.

COMPARE THE `.normalized` TREES, NEVER THE RAW DUMPS
====================================================
Agent Action Plan section 0.6.2's width drift is the reason. The same
logical field is declared three different widths, and the bridge trims
trailing spaces as it builds its SQL text:

    [copybooks/wsledger.cob:L27]   03  Ledger-Name pic x(24).       24
    [common/nominalMT.cbl:L299]    HV-LEDGER-NAME PIC X(32).        32
    [mysql/ACASDB.sql:L127]        `LEDGER-NAME` char(32) NOT NULL, 32
    [common/nominalMT.cbl:L1065-L1067]
        STRING FUNCTION TRIM (HV-LEDGER-NAME,TRAILING) ...

So the COBOL side can store a character column trimmed while a Python
data-access layer writing padded values stores it padded. That is a
representation artefact, not a behavioural difference, and canonicalising
it is harness/normalize.py's first job. Comparing the raw dumps would
report it as a failure on almost every character column.

A directory is therefore accepted only when its name ends with one of the
two suffixes this repository documents:

    `.normalized`  harness/normalize.py's own default and its composed
                   layout [harness/normalize.py:L808, L3182]
    `.norm`        the suffix the committed canonical recipe passes
                   explicitly [harness/docker-compose.yml:L269, L273]

Anything else is refused with an explanation, unless --allow-raw is
given, which is a debugging escape and says so loudly on stderr.

BOUND THE COMPARISON BY THE SCENARIO, NEVER BY AN IGNORE-LIST
=============================================================
Agent Action Plan section 0.4.1.7 specifies that each
harness/scenarios/*.yaml carries "Seed data, inputs and the
affected-table list per scenario", and there is a concrete reason that
list matters. [general/general.cbl:L656-L691] rewrites SYSTEM-REC,
SYSDEFLT-REC and SYSTOT-REC to both the relational database and the
COBOL flat file when the operator leaves the menu with "X": System-Open,
then a key-1 rewrite of the system record, key 2 for the default record,
key 4 for WS-System-Record-4, then System-Close, and then the identical
three rewrites against the flat file. The Python command line has no menu
and performs no such rewrite. Comparing those tables in a scenario that
does not affect them would be a FALSE FAILURE.

harness/run_cobol_scenario.sh reaches the same conclusion from the other
end and names this module in doing so [L1336]: the comparison must be
bounded "by an explicit per-scenario list rather than by an ignore-list in
diff_states.py".

SYSTOT-REC is nevertheless genuinely in scope for the period-end
scenario - Agent Action Plan section 0.6.4 identifies nine period-total
write sites in the Sales and Purchase programs, "the sole writers of the
totals record". That overlap between "a table the menu shell rewrites"
and "a table the cycle legitimately writes" is real, and it belongs in
docs/migration/ambiguity-resolutions.md, arbitrated by the oracle. It
does NOT belong in a special case here.

ROW ALIGNMENT IS BY PRIMARY KEY
===============================
harness/normalize.py preserves the primary-key ordering it inherits from
`SELECT * ... ORDER BY <primary key>`, so positional alignment would
usually work - and would be catastrophic when it did not. One inserted or
deleted row would shift every later row by one and turn a single finding
into a cascade of hundreds of spurious column differences, in a
169-column table. Rows are therefore keyed on their primary-key VALUE,
and a key present on one side only is reported as such.

The direction is labelled, because the two directions are materially
different findings. "The Python run created a row the COBOL run did not"
is not the same evidence as the reverse, and the anomaly analysis depends
on telling them apart:

  * Anomaly #4, the half-posted double entry at
    [irs/irs030.cbl:L1635-L1652] - the debit is rewritten before the
    credit account is looked up, so a missing credit leaves an unbalanced
    debit and NO posting record - shows up as a one-sided missing row.
  * Anomaly #5, the lost update on the two VAT control accounts
    [irs/irs030.cbl:L1602, L1612, L1704-L1708] - pre-loop snapshots
    rewritten at end of job, discarding any in-loop rewrite - shows up as
    a single stale value.

VALUE COMPARISON IS EXACT, AND NOTHING ELSE
===========================================
Agent Action Plan section 0.1.1 requires "a behaviorally exact clone of
the compiled COBOL". A one-penny difference is a FAILURE, by design.
There is no tolerance, no epsilon, no math.isclose, no case-insensitive
compare, no whitespace-insensitive compare and no numeric coercion
anywhere in this file.

Decimal values arrive from harness/normalize.py as JSON STRINGS, already
rendered at their column's declared scale [harness/normalize.py, job 2].
They are compared AS STRINGS, which is both exact and scale-aware, and
which is why decimal.Decimal is not imported here: there is nothing to
compute. Integers arrive as JSON integers and are compared as integers.
Values of differing type are reported as a difference with both type
names, because that would mean the two dumps were produced by
inconsistent serialisation - a real defect, not something to smooth over.

THE MODULE IS NEUTRAL ABOUT WHETHER A VALUE "LOOKS WRONG"  (rule R-4)
=====================================================================
Agent Action Plan section 0.8.2, verbatim: "A defect reproduced is
correct; a defect fixed is a failure." This module reports DIFFERENCES,
never defects, and it makes no judgement beyond equality. There is no
ignore-list, no tolerance list, no "known difference" allowance and no
per-column special case of any kind.

The canonical case is anomaly #7. IRSPOSTING-REC carries three date
component columns, POST4-DAY, POST4-MONTH and POST4-YEAR, that exist in
no copybook: the bridge derives them from a date string under a guard
[common/irspostingMT.cbl:L982-L987], and when the guard fails they stay
ZERO while POST4-DAT still holds the date text. That row is internally
inconsistent, and it is CORRECT. If both sides produce it, this module
reports nothing. If only one side does, it reports a difference. It never
excuses it, and it never repairs it.

Two further shapes that are legitimate and must not be second-guessed:

  * PSIRSPOST-REC can legitimately end a scenario EMPTY. Opening the
    transfer file for output means DELETING EVERY ROW
    [common/acas008.cbl:L309-L319, L566-L574], which is how irs030's
    end-of-job clear works [irs/irs030.cbl:L1715-L1724]. Empty on both
    sides is a pass; empty on one side is a real failure.
  * SYSTEM-REC carries the two pinned, diff-visible observables. The
    controlled clock's binary run date, `05 Run-Date binary-long`
    [copybooks/wssystem.cob:L67], is column `RUN-DAT int(8) unsigned`
    [mysql/ACASDB.sql:L1199]; and the three-state IRS fan-out switch,
    `05 IRS-Instead pic x.` with `88 IRS-Used value "Y".` and
    `88 IRS-Both-Used value "B".` [copybooks/wssystem.cob:L179-L181], is
    column `IRS-INSTEAD char(1)` [mysql/ACASDB.sql:L1252] - space for
    General Ledger only, "Y" for IRS instead, "B" for IRS as well as.
    Agent Action Plan section 0.6.4 warns that "leaving it at a default
    would make the affected-table list ambiguous". A difference in
    either is a genuine failure, never something to excuse.

THE INPUT CONTRACT
==================
    $ACAS_OUT/<scenario>/cobol.normalized/<TABLE>.json    LEFT, the oracle
    $ACAS_OUT/<scenario>/python.normalized/<TABLE>.json   RIGHT, the migration
    $ACAS_OUT/<scenario>/diff.txt                         this module's output

A dump object carries exactly five keys, in this order and no others -
the layout fixed at [harness/dump_tables.py:L544-L550] and preserved
unchanged by [harness/normalize.py]:

    {
      "table": "GLLEDGER-REC",
      "primary_key": "LEDGER-KEY",
      "columns": ["LEDGER-KEY", ..., "LEDGER-BALANCE", ...],
      "row_count": 2,
      "rows": [[1, 1, "B", 1, "Sales Ledger Control", "1234.56", ...], ...]
    }

Every assertion below is checked before any comparison, and each failure
is exit 2 with the file and the failed assertion named:

  1. Both files parse as JSON objects carrying exactly the five keys, in
     order.
  2. `table` is a string, is one of the 22 in-scope tables, and equals
     the file's own name stem.
  3. `primary_key` is a string and is a member of `columns`; and the two
     sides agree on it, since it is the alignment column.
  4. `columns` is a list of unique, non-empty strings.
  5. `row_count` equals `len(rows)`, and every row has exactly
     `len(columns)` values.
  6. No value is a float and no value is null. Verified: ZERO of the 513
     in-scope columns is nullable, and the schema declares zero FLOAT,
     DOUBLE and REAL columns. Agent Action Plan section 0.6.2 explains
     the first: each bridge load paragraph initialises the host-variable
     group, "so unset fields become zero or space rather than SQL NULL".
     A null is genuinely new information - it is reported, never
     coalesced. A float would mean harness/dump_tables.py or
     harness/normalize.py had been reconfigured, and comparing floats
     here would launder that bug (rule R-2).
  7. No primary-key value appears twice. A PRIMARY KEY column cannot
     produce a duplicate, so one means the input is malformed.

The ONE cross-side check that is a DIFFERENCE rather than an error is the
column list. The file specification lists it among the pre-comparison
assertions and then says of it, in the same breath, "A column-set or
column-order difference is a structural failure, not a row difference:
report it as such and stop comparing that table's rows (there is no
meaningful positional alignment)" - and its validation step 12 requires
exit 1 for a column-order mismatch, "reported as a structural finding,
with row comparison skipped for that table". Validation wins the tie:
a column mismatch is reported at exit 1, rows are not compared for that
table, and `load_dump` deliberately does NOT check a dump's columns
against a hardcoded per-table list, which would have pre-empted that
finding with an exit 2.

THE REPORT
==========
One difference per line, two spaces between fields, self-describing, and
BYTE-DETERMINISTIC for a given pair of inputs: no timestamp, no host
name, no process id, no absolute path, no elapsed time, no tool version,
and no dependence on dictionary or filesystem iteration order.

    GLLEDGER-REC  row_count  cobol=12  python=11
    GLLEDGER-REC  missing_in_python  LEDGER-KEY=1204
    GLLEDGER-REC  LEDGER-KEY=1100  col[6] LEDGER-BALANCE
        cobol="1234.56"  python="1234.55"

(that last finding is ONE line in the real report; it is wrapped here
only to keep this docstring inside the file's 79-column margin)

The sides are labelled `cobol` and `python`, matching the directory
names, so the report says which one is the oracle. Values are rendered as
JSON, so a trailing space, a leading space and an empty string are all
visible. Column ordinals are 1-based, matching SQL's ORDINAL_POSITION -
SYSTEM-REC has 169 columns, and finding a difference by hand without an
ordinal is impractical, so the ordinal is evidence rather than decoration
(rule R-5).

Ordering, top to bottom, is fixed:

  1. Tables in the order the scenario's affected-table list gives them;
     with no list, in ASCII-sorted table-name order. Never in
     filesystem-iteration order.
  2. Within a table: the structural findings first - a one-sided table,
     a column mismatch, a row-count difference - then missing_in_python,
     then missing_in_cobol, then the value differences.
  3. Keys ascending: numeric keys numerically, character keys by ASCII.
  4. Within a key: columns in schema ordinal order, never alphabetical.

--max-differences caps the DETAIL lines per table so that a catastrophic
mismatch cannot produce an unusable megabyte. The structural headline is
never capped, the notice always carries the TRUE total, and truncation
NEVER changes the exit code.

THE RULES CITED BELOW BY NUMBER
===============================
This project ships NO separate rules document: `review_rules` reports
exactly "No user rules provided.", confirmed by a full read. The six
binding rules R-1 to R-6 are the Agent Action Plan's own, section 0.7.2.
Where the plan is silent, ordinary enterprise practice applies. Nothing
here is invented.

R-1  NO COBOL AT RUNTIME, AND NO COUPLING TO THE SHIPPED PACKAGE.
     `acas_posting` is never imported, in any form, and
     data_dictionary/*.json is never read: the judge cannot depend on the
     defendant, and this module must run with the migrated package not
     installed. No COBOL is invoked, no cobc is shelled out to, and no
     database connection is opened - this module is pure file-to-file, so
     it needs no driver at all. harness/ is a SIBLING of acas_posting/
     and has NO __init__.py, which is what makes "there is no import path
     from acas_posting to harness" (Agent Action Plan section 0.3.1) a
     structural fact; pyproject.toml packages `acas_posting*` and
     excludes `harness*` from the other side. Imports here are the
     standard library plus, lazily and only for a scenario file, PyYAML.
R-2  ZERO BINARY FLOATING POINT. No pandas and no numpy, for any reason;
     Agent Action Plan section 0.5.1 extends that prohibition to this
     exact file, verbatim: "This exclusion is absolute, including for the
     harness dump comparison, which uses ordered row sequences rather
     than dataframes." `float(...)` is never called; a float in an input
     is raised on, never compared; comparison is exact.
R-3  NO SCHEMA CHANGE, STRICTLY SEQUENTIAL. No SQL, no DDL, no
     connection. Tables are compared one after another in a plain loop -
     no thread, no event loop, no process pool. Nothing is written under
     $ACAS_REPO, which is mounted read-only and holds the frozen
     artifacts (Agent Action Plan section 0.8.1).
R-4  LEGACY ANOMALIES REPRODUCED, NEVER FIXED. See the neutrality section
     above. No ignore-list, no tolerance, no judgement.
R-5  FULL TRACEABILITY. Every reported difference names its table, its
     primary-key value, and its column by NAME and by ORDINAL, which is
     what makes docs/migration/scenario-diff-evidence.md and
     docs/migration/ambiguity-resolutions.md writable from this output.
R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER. This module is the
     arbitration. Its exit code is the verdict and its report is
     byte-deterministic.

THE VERIFIED INVENTORY
======================
The 22 in-scope tables, their column counts and their single-column
primary keys, re-verified against mysql/ACASDB.sql before this module was
written - 33 CREATE TABLE statements in the file, 22 in scope and 11 out,
513 in-scope columns in total, none of them nullable, and no FLOAT,
DOUBLE or REAL column anywhere. It matches Agent Action Plan section
0.6.6 exactly.

    table               cols  primary key             ACASDB.sql
    ANALYSIS-REC           4  PA-CODE                       L31
    GLBATCH-REC           21  BATCH-KEY                     L80
    GLLEDGER-REC          11  LEDGER-KEY                   L122
    GLPOSTING-REC         14  POST-RRN                     L154
    IRSDFLT-REC            4  DEF-REC-KEY                  L189
    IRSFINAL-REC           3  IRS-FINAL-ACC-REC-KEY        L214
    IRSNL-REC             15  KEY-1                        L238
    IRSPOSTING-REC        13  KEY-4                        L274
    PSIRSPOST-REC         10  IRS-POST-KEY                 L366
    PUINV-LINES-REC       14  IL-LINE-KEY                  L510
    PUINVOICE-REC         30  PINVOICE-KEY                 L545
    PUITM5-REC            29  OI5-KEY                      L596
    PULEDGER-REC          29  PURCH-KEY                    L646
    SAINV-LINES-REC       14  IL-LINE-KEY                  L809
    SAINVOICE-REC         31  SINVOICE-KEY                 L844
    SAITM3-REC            28  OI3-KEY                      L896
    SALEDGER-REC          37  SALES-KEY                    L945
    SYSDEFLT-REC           4  DEF-REC-KEY                 L1138
    SYSFINAL-REC           2  FINAL-ACC-REC-KEY           L1163
    SYSTEM-REC           169  SYSTEM-REC-KEY              L1186
    SYSTOT-REC            21  LEDGER-TOTALS-REC-KEY       L1376
    VALUEANAL-REC         10  VA-CODE                     L1418

The eleven out-of-scope tables are refused BY NAME with an explanation
rather than with a not-found, citing Agent Action Plan section 0.2.2:
DELIVERY-REC, PLPAY-REC, PLPAY-RECrg01, PUAUTOGEN-LINES-REC,
PUAUTOGEN-REC, PUDELINV-REC, SAAUTOGEN-LINES-REC, SAAUTOGEN-REC,
SADELINV-REC, STOCK-REC, STOCKAUDIT-REC.

INVOCATIONS
===========
Both forms this repository documents are supported, and neither is a
guess. The committed canonical eight-stage recipe passes the two
directories POSITIONALLY [harness/docker-compose.yml:L274]:

    harness/diff_states.py /out/cobol.norm /out/python.norm

The named form is equivalent and reads better in a test:

    harness/diff_states.py --cobol /out/cobol.norm --python /out/python.norm
    harness/diff_states.py --scenario clean_batch_gl --out-dir /out
    harness/diff_states.py ... --scenario-file harness/scenarios/x.yaml
    harness/diff_states.py ... --tables GLBATCH-REC,GLLEDGER-REC

USED AS A LIBRARY
=================
tests/conftest.py provides "the pinned-clock fixture and the seed/dump/
normalize/diff helpers so that no test reimplements the comparison
protocol" (Agent Action Plan section 0.4.3), so this module is both an
importable plain module and a runnable command line. `main` RETURNS its
exit code and never calls sys.exit. The question every one of the eight
tests/scenarios/test_*.py files asks is a single cheap call:

    from harness import diff_states
    diff = diff_states.diff_trees(cobol_dir, python_dir, tables)
    assert diff.is_empty, diff_states.render(diff)

That import works even though harness/ has no __init__.py and must never
gain one (rule R-1): harness/ resolves as an implicit namespace package
(PEP 420) whenever the repository root is on sys.path, which is what
pytest's rootdir insertion already provides. It is genuinely not a
regular package - `harness.__file__` is None - so no import path from
acas_posting to harness is created by it.

If a caller prefers to bypass sys.path entirely and load this file by
its path, the registration line below is MANDATORY, not decorative:

    name = "acas_diff_states"
    spec = importlib.util.spec_from_file_location(
        name, REPO / "harness" / "diff_states.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # REQUIRED before exec_module
    spec.loader.exec_module(module)

Omitting it raises `AttributeError: 'NoneType' object has no attribute
'__dict__'` from inside dataclasses. The cause is not local to this
module: `from __future__ import annotations` makes every field
annotation a string, and @dataclass resolves those strings through
`sys.modules[cls.__module__].__dict__` while deciding whether any of
them names dataclasses.KW_ONLY. A module that is being executed but is
not yet registered has no sys.modules entry for that lookup to find.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

# ---------------------------------------------------------------------------
#  THE FROZEN INVENTORY
#
#  Re-declared here rather than imported. harness/ has no __init__.py - by
#  design, rule R-1 - so there is no package path from this module to
#  harness/dump_tables.py or harness/normalize.py, and each of the three
#  carries its own copy of these facts. That is the established pattern in
#  this tree, and it is what lets any one of them be run or imported on
#  its own. Every entry was re-verified against mysql/ACASDB.sql, which
#  is read as specification and never modified.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TableSpec:
    """One in-scope table's frozen-schema facts.

    Attributes:
        primary_key: The single column rows are aligned on. Agent Action
            Plan section 0.6.6 establishes that every in-scope table has
            exactly one, which is why no compound key is modelled.
        column_count: The declared number of columns. Recorded for the
            error messages and for a one-line inventory assertion; a
            dump's own column list is never checked against it, because
            a column-count difference between the two SIDES is a
            reported structural finding rather than an error.
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

# The eleven tables the posting cycle never touches, listed BY NAME so a
# wrong request is refused with an explanation rather than with a
# not-found. Agent Action Plan section 0.2.2 enumerates them. 22 + 11 =
# 33, the schema's full CREATE TABLE count. The same list appears at
# [harness/dump_tables.py:L510-L524] and [harness/reset_db.sh:L276-L288].
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

# The default table order: the names, ASCII-ascending. Sorted ONCE here,
# never per run, so the report's table order cannot depend on dictionary
# or filesystem iteration order (rule R-6).
IN_SCOPE_TABLES: Final[tuple[str, ...]] = tuple(sorted(IN_SCOPE))

# 513 and 33, both verified against mysql/ACASDB.sql. Exposed so a test
# can assert the whole inventory in two lines.
EXPECTED_TOTAL_COLUMNS: Final[int] = sum(
    spec.column_count for spec in IN_SCOPE.values()
)
EXPECTED_SCHEMA_TABLES: Final[int] = len(IN_SCOPE) + len(OUT_OF_SCOPE)

# The two sides of the comparison, in the order they are always named:
# the compiled COBOL oracle first, the migrated Python cycle second.
SIDES: Final[tuple[str, ...]] = ("cobol", "python")

# The report's side labels. `cobol` and `python` rather than left and
# right, so the report says which side is the ORACLE.
LABEL_COBOL: Final[str] = SIDES[0]
LABEL_PYTHON: Final[str] = SIDES[1]

# A dump object's key order, fixed at [harness/dump_tables.py:L544-L550]
# and preserved unchanged by harness/normalize.py. Checked exactly - not
# as a set - because the order is part of the byte-identical guarantee.
DUMP_KEYS: Final[tuple[str, ...]] = (
    "table",
    "primary_key",
    "columns",
    "row_count",
    "rows",
)

# One file per table: `<TABLE>.json`, the table spelled exactly as the
# frozen schema spells it, hyphens included
# [harness/dump_tables.py:L1667].
DUMP_SUFFIX: Final[str] = ".json"

# harness/dump_tables.py and harness/normalize.py both write through a
# temporary file named `.<stem>.json.tmp` in the target directory and
# then os.replace it into position, so a partial file can never be
# compared. Anything beginning with a dot is skipped when a tree is
# scanned, which covers those leftovers and any other hidden file.
TEMP_PREFIX: Final[str] = "."

# The two directory suffixes that mark a NORMALISED tree, both documented
# in this repository:
#   `.normalized`  harness/normalize.py's own default and the suffix its
#                  composed layout appends [harness/normalize.py:L808]
#   `.norm`        what the committed canonical recipe passes explicitly
#                  [harness/docker-compose.yml:L269, L273]
# The composed layout this module offers derives `.normalized`, matching
# harness/normalize.py's composed layout [harness/normalize.py:L3182].
NORMALIZED_SUFFIXES: Final[tuple[str, ...]] = (".normalized", ".norm")
NORMALIZED_SUFFIX: Final[str] = NORMALIZED_SUFFIXES[0]

# THE VERDICT (rule R-6). Three values, and no others.
#
#   0  identical           stdout is EMPTY
#   1  difference found    the report is on stdout
#   2  cannot compare      a diagnosis is on stderr
#
# Deliberately NOT the 80+ band the sibling harness modules use: they
# exit 0 for "I did my job", this one exits 0 for "the migration is
# exact", and 1 must mean "difference found".
EX_IDENTICAL: Final[int] = 0
EX_DIFFERENT: Final[int] = 1
EX_ERROR: Final[int] = 2

# How many DETAIL lines per table the report prints before truncating.
# The structural headline is never truncated, the notice always carries
# the true total, and truncation never changes the exit code.
DEFAULT_MAX_DIFFERENCES: Final[int] = 200

# The report file name the composed layout writes:
# $ACAS_OUT/<scenario>/diff.txt.
DIFF_FILENAME: Final[str] = "diff.txt"

# The output root for the composed layout, and the read-only checkout
# nothing may be written into. The Compose service sets both
# [harness/docker-compose.yml].
_ENV_OUT: Final[str] = "ACAS_OUT"
_ENV_REPO: Final[str] = "ACAS_REPO"

# The scenario key this module reads. Agent Action Plan section 0.4.1.7
# specifies that each harness/scenarios/*.yaml carries "Seed data, inputs
# and the affected-table list per scenario"; these are the two spellings
# of that list - the underscored form and the hyphenated form the
# repository uses for every COBOL and SQL identifier. Both mean the same
# thing and only one may appear. Identical to
# [harness/dump_tables.py:L641-L644] and to the keys
# harness/run_cobol_scenario.sh reads [L1323-L1326].
_SCENARIO_TABLE_KEYS: Final[tuple[str, ...]] = (
    "affected_tables",
    "affected-tables",
)

# How many near-miss names an unknown-table message offers.
_SUGGESTION_LIMIT: Final[int] = 4

# The report's field separator. Two spaces, so a line stays greppable and
# a value containing a single space is still unambiguous.
_FIELD_GAP: Final[str] = "  "

# The prog name every diagnostic is prefixed with. A fixed string, not
# sys.argv[0]: an absolute path would make stderr depend on how the
# module was invoked (rule R-6).
_PROG: Final[str] = "harness/diff_states.py"


# ---------------------------------------------------------------------------
#  PROGRESS
#
#  STDERR ONLY, and never stdout. stdout carries the verdict and nothing
#  else: on a pass it must be zero bytes, so a single reassuring word
#  written there would break the contract. No line carries a clock
#  reading, a host name, a process id or an elapsed time (rule R-6).
# ---------------------------------------------------------------------------

# Set once by `main` from --quiet. A module-level flag rather than a
# parameter threaded through every function, because there is exactly one
# process and one run (rule R-3, strictly sequential).
_QUIET: bool = False


def _progress(message: str) -> None:
    """Write one progress line to stderr, unless `--quiet` was given.

    Args:
        message: The line to write.
    """
    if _QUIET:
        return
    print(message, file=sys.stderr)


def _warn(message: str) -> None:
    """Write one warning line to stderr. Never silenced by `--quiet`.

    A warning marks a departure from the protocol - comparing raw trees,
    or comparing without a scenario's affected-table list - and a
    departure from the protocol must always be visible.

    Args:
        message: The line to write.
    """
    print(f"{_PROG}: warning: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
#  ERRORS - EVERY ONE OF THEM IS EXIT 2
#
#  One root, so a caller can catch everything this module raises with a
#  single clause, and one subclass per distinct cause so a caller that
#  cares can tell them apart. Each also subclasses the builtin a reader
#  would expect, which is the convention the sibling modules follow
#  [harness/dump_tables.py:L688-L750], [harness/normalize.py:L880-L948].
#
#  EVERY error here means "the comparison could not be performed", which
#  is exit 2 and NEVER exit 0. That distinction is the whole reason exit 2
#  exists: an inability to compare is not a pass.
# ---------------------------------------------------------------------------


class DiffStatesError(Exception):
    """Base class for every failure this module reports. Always exit 2."""


class MissingTreeError(DiffStatesError, OSError):
    """A tree to compare is absent, or is not a directory.

    The most dangerous input this module can be given, because the
    tempting response - "nothing to compare, so nothing differs" - is a
    FALSE PASS. It is exit 2.
    """


class RawTreeError(DiffStatesError, ValueError):
    """A directory is not a normalised tree and --allow-raw was not given.

    Comparing raw dumps would report harness/normalize.py's three
    representation artefacts as behavioural differences - the character
    padding of Agent Action Plan section 0.6.2 chief among them.
    """


class SameTreeError(DiffStatesError, ValueError):
    """Both sides name the same directory.

    A tree always equals itself, so the comparison would return empty
    whatever the migration did. That is a FALSE PASS, so it is refused.
    """


class EmptyComparisonError(DiffStatesError, ValueError):
    """There is no table to compare.

    Comparing nothing would return empty and read as a pass. Refused for
    the same reason as `SameTreeError`.
    """


class MissingTableFileError(DiffStatesError, OSError):
    """A requested table's dump is absent from BOTH trees.

    Absent from ONE tree is a reported DIFFERENCE, never an error - that
    asymmetry is exactly what a naive intersection would hide. Absent
    from both means the dumps were never taken.
    """


class DumpReadError(DiffStatesError, OSError):
    """A dump file could not be read, or is not a JSON object."""


class DumpShapeError(DiffStatesError, ValueError):
    """A dump object's shape is wrong.

    Wrong keys, a wrong key order, a `row_count` that disagrees with the
    rows, a ragged row, a primary key that is not one of the columns, or
    the two sides disagreeing on the alignment column.
    """


class NumericPolicyError(DiffStatesError, TypeError):
    """A value is a binary floating-point number (rule R-2).

    The frozen schema declares zero FLOAT, DOUBLE and REAL columns and
    both producers refuse to emit a float, so this is unreachable unless
    one of them was reconfigured. Comparing floats here would silently
    launder that bug, so it is raised on instead - and never coerced.
    """


class UnexpectedValueTypeError(DiffStatesError, TypeError):
    """A value is of a type no in-scope column can hold.

    A dump holds only JSON strings and JSON integers. A bool, a list, an
    object or a number with a fractional part means the file was not
    written by harness/normalize.py.
    """


class UnexpectedNullError(DiffStatesError, ValueError):
    """A value is JSON null.

    Verified: not one of the 513 in-scope columns is nullable. Agent
    Action Plan section 0.6.2 explains why - each bridge load paragraph
    initialises the host-variable group, "so unset fields become zero or
    space rather than SQL NULL". A null is genuinely new information, so
    it is reported and NEVER coalesced to zero, to a space or to an
    empty string.
    """


class DuplicateKeyError(DiffStatesError, ValueError):
    """A primary-key value appears twice in one dump.

    A PRIMARY KEY column cannot produce a duplicate, so the input is
    malformed - and with a duplicate there is no unambiguous row to
    align against.
    """


class UnknownTableError(DiffStatesError, ValueError):
    """A name is not a table of the frozen schema at all."""


class TableNotInScopeError(DiffStatesError, ValueError):
    """A name is one of the eleven tables the posting cycle never touches."""


class ScenarioFileError(DiffStatesError, ValueError):
    """A scenario definition is missing, unreadable or unusable."""


class ReportPathError(DiffStatesError, ValueError):
    """The report would be written somewhere it must not be.

    Nothing may be written under `$ACAS_REPO`: it holds the frozen
    artifacts and is mounted read-only (rule R-3, Agent Action Plan
    section 0.8.1).
    """


# ---------------------------------------------------------------------------
#  TABLE NAMES
# ---------------------------------------------------------------------------


def table_spec(table: str) -> TableSpec:
    """Look up an in-scope table's frozen-schema facts.

    Args:
        table: A table name, spelled exactly as `mysql/ACASDB.sql` spells
            it, hyphens included and upper case.

    Returns:
        Its `TableSpec`.

    Raises:
        TableNotInScopeError: It is one of the eleven out-of-scope tables.
        UnknownTableError: It is not a table of the frozen schema.
    """
    specification = IN_SCOPE.get(table)
    if specification is not None:
        return specification

    if table in OUT_OF_SCOPE:
        raise TableNotInScopeError(
            f"`{table}` is one of the {len(OUT_OF_SCOPE)} tables the "
            f"posting cycle never touches, listed as out of scope by "
            f"Agent Action Plan section 0.2.2: "
            f"{', '.join(sorted(OUT_OF_SCOPE))}. Comparing it would widen "
            f"the comparison beyond the migration's boundary, so it is "
            f"refused rather than compared."
        )

    # A near-miss list, so a typo or a case error is obvious at once. The
    # comparison is upper-cased for the SUGGESTION only; the name itself
    # is matched exactly, because the schema's spelling is the contract.
    wanted = table.upper().replace("_", "-")
    close = [name for name in IN_SCOPE_TABLES if name.upper() == wanted]
    if not close:
        close = [
            name
            for name in IN_SCOPE_TABLES
            if wanted and (wanted in name.upper() or name.upper() in wanted)
        ]
    hint = ""
    if close:
        hint = f" Did you mean {', '.join(close[:_SUGGESTION_LIMIT])}?"

    raise UnknownTableError(
        f"`{table}` is not a table of the frozen schema. "
        f"mysql/ACASDB.sql defines exactly {EXPECTED_SCHEMA_TABLES} "
        f"tables: the {len(IN_SCOPE)} in scope for the posting cycle - "
        f"{', '.join(IN_SCOPE_TABLES)} - plus {len(OUT_OF_SCOPE)} out of "
        f"scope.{hint}"
    )


def dump_filename(table: str) -> str:
    """Return the file name a table's dump is stored under.

    Args:
        table: The table name.

    Returns:
        `<TABLE>.json`, matching [harness/dump_tables.py:L1667] and
        [harness/normalize.py:L2534-L2545] exactly.
    """
    return f"{table}{DUMP_SUFFIX}"


# ---------------------------------------------------------------------------
#  IS THIS A NORMALISED TREE?
#
#  The second most likely cause of a FALSE FAIL, after positional row
#  alignment: comparing the raw dumps instead of the normalised ones.
# ---------------------------------------------------------------------------


def is_normalized_tree(directory: Path | str) -> bool:
    """Report whether a directory NAME marks it as a normalised tree.

    The test is on the name, not on the contents: a normalised dump is
    byte-comparable with a raw one - harness/normalize.py preserves the
    shape exactly and changes only values - so there is nothing inside a
    file that could distinguish the two. The name is the only signal, and
    both producers of that name are committed in this repository.

    Args:
        directory: The directory to test.

    Returns:
        Whether its name ends with `.normalized` or `.norm`.
    """
    name = Path(directory).name
    return any(name.endswith(suffix) for suffix in NORMALIZED_SUFFIXES)


def _assert_tree(
    directory: Path, label: str, *, allow_raw: bool
) -> None:
    """Assert a directory is a usable normalised tree.

    Args:
        directory: The directory to check.
        label: `cobol` or `python`, for the messages.
        allow_raw: Skip the normalised-name requirement, loudly.

    Raises:
        MissingTreeError: It does not exist, or is not a directory.
        RawTreeError: Its name does not mark it as normalised and
            `allow_raw` is false.
    """
    if not directory.exists():
        raise MissingTreeError(
            f"the {label} tree {directory} does not exist. An absent tree "
            f"is NOT an empty diff: exit 2 says the comparison could not "
            f"be performed, and it is never reported as a pass. Run "
            f"stages 3 and 4 - harness/dump_tables.py then "
            f"harness/normalize.py - for the {label} side first "
            f"[harness/docker-compose.yml:L268-L273]."
        )
    if not directory.is_dir():
        raise MissingTreeError(
            f"the {label} tree {directory} is not a directory. It should "
            f"be the directory harness/normalize.py wrote its "
            f"<TABLE>.json files into, for example "
            f"$ACAS_OUT/<scenario>/{label}{NORMALIZED_SUFFIX}."
        )

    if is_normalized_tree(directory):
        return

    if allow_raw:
        _warn(
            f"--allow-raw: comparing {directory}, whose name does not end "
            f"with {' or '.join(NORMALIZED_SUFFIXES)}, so it is probably a "
            f"RAW dump tree. Raw dumps still carry the three "
            f"representation artefacts harness/normalize.py removes - "
            f"character padding above all, because the bridge trims "
            f"trailing spaces as it builds its SQL "
            f"[common/nominalMT.cbl:L1065-L1067] while a Python write may "
            f"not - so differences reported from here may be artefacts "
            f"rather than behaviour. This is a debugging mode; a verdict "
            f"taken from it is not evidence."
        )
        return

    raise RawTreeError(
        f"the {label} tree {directory} does not look like a normalised "
        f"tree: its name ends with neither "
        f"{' nor '.join(NORMALIZED_SUFFIXES)}. Stage 8 compares the "
        f"NORMALISED dumps, because a raw dump still carries the "
        f"representation artefacts harness/normalize.py exists to remove "
        f"- character padding above all (Agent Action Plan section 0.6.2: "
        f"`Ledger-Name pic x(24)` [copybooks/wsledger.cob:L27] becomes "
        f"`HV-LEDGER-NAME PIC X(32)` [common/nominalMT.cbl:L299] and "
        f"`char(32)` [mysql/ACASDB.sql:L127], and the bridge TRIMS "
        f"trailing spaces [common/nominalMT.cbl:L1065-L1067]) - so a "
        f"comparison here would report artefacts as behaviour. Run "
        f"harness/normalize.py first and compare its output, for example "
        f"`--in {directory} --out {directory}{NORMALIZED_SUFFIX}`; or pass "
        f"--allow-raw if you are debugging and accept that the verdict is "
        f"not evidence."
    )


# ---------------------------------------------------------------------------
#  LOADING AND ASSERTING ONE DUMP
#
#  Every assertion here is about ONE file in isolation - its shape, its
#  types, its internal consistency. Every one of them is exit 2, because
#  a malformed dump means the comparison could not be performed.
#
#  What is deliberately NOT asserted here is anything CROSS-SIDE. In
#  particular a dump's `columns` list is never checked against a
#  hardcoded per-table column list: the file specification's validation
#  step 12 requires a column-order mismatch between the two sides to be
#  reported as a STRUCTURAL DIFFERENCE at exit 1, with that table's rows
#  left uncompared, and an assertion here would have pre-empted that
#  finding with an exit 2.
#
#  `_assert_dump` is pure, so a caller holding an object in memory and a
#  caller reading a file go through exactly the same checks - the split
#  harness/normalize.py makes for the same reason [L2555-L2558]. That
#  matters for the rule R-2 float guard in particular: it has to fire on
#  a hand-built dict passed straight to `diff_table` by a test, not only
#  on a file.
# ---------------------------------------------------------------------------


def _assert_value(
    value: object, *, where: str, table: str, column: str, row_index: int
) -> str | int:
    """Assert one dumped value is a comparable scalar, and return it.

    Args:
        value: The value as JSON parsed it.
        where: The file or side the value came from, for the message.
        table: The table, for the message.
        column: The column, for the message.
        row_index: The row's zero-based position, for the message.

    Returns:
        The value unchanged - a `str` or an `int`. Nothing is converted,
        rounded, padded, trimmed or coerced.

    Raises:
        UnexpectedNullError: It is `None`.
        NumericPolicyError: It is a `float` (rule R-2).
        UnexpectedValueTypeError: It is a `bool`, a container, or any
            other type no in-scope column can hold.
    """
    site = f"{where}: `{table}`.`{column}` row {row_index}"

    if value is None:
        raise UnexpectedNullError(
            f"{site} is JSON null, but every column of the frozen schema "
            f"is declared NOT NULL - verified: none of the "
            f"{EXPECTED_TOTAL_COLUMNS} in-scope columns is nullable. "
            f"Agent Action Plan section 0.6.2 explains why: each bridge "
            f"load paragraph initialises the host-variable group, \"so "
            f"unset fields become zero or space rather than SQL NULL\". A "
            f"null is genuinely new information, so it is reported here "
            f"and NEVER coalesced to zero, to a space or to an empty "
            f"string."
        )

    # bool BEFORE int, because bool is a subclass of int. JSON true is not
    # the integer a tinyint column holds, and no in-scope column can
    # produce one.
    if isinstance(value, bool):
        raise UnexpectedValueTypeError(
            f"{site} is the JSON boolean {json.dumps(value)}. A dump holds "
            f"JSON integers and JSON strings only "
            f"[harness/dump_tables.py:L1392-L1461]; a boolean means the "
            f"file was not written by harness/normalize.py."
        )

    # THE RULE R-2 GUARD. A float here would mean
    # harness/dump_tables.py or harness/normalize.py had its type
    # conversion overridden - the schema declares zero FLOAT, DOUBLE and
    # REAL columns and both producers raise rather than emit one. It is
    # NOT compared, because comparing floats here would launder the bug,
    # and it is NOT converted, because a conversion would decide by
    # itself what the value was meant to be.
    if isinstance(value, float):
        raise NumericPolicyError(
            f"{site} is the binary floating-point value {value!r}. No "
            f"accounting value may pass through binary floating point at "
            f"any point (rule R-2); Agent Action Plan section 0.5.1 "
            f"extends that prohibition to this comparison explicitly. A "
            f"DECIMAL reaches a dump as a JSON STRING rendered at the "
            f"column's declared scale, so a JSON number with a fractional "
            f"part means harness/dump_tables.py or harness/normalize.py "
            f"is broken. Nothing is coerced here, and the comparison is "
            f"refused rather than made approximate."
        )

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        return value

    raise UnexpectedValueTypeError(
        f"{site} is {type(value).__name__} ({value!r}), which no in-scope "
        f"column can hold. A dump holds JSON integers - for TINYINT, "
        f"SMALLINT, MEDIUMINT, INT and BIGINT - and JSON strings, for "
        f"CHAR and for DECIMAL rendered at its declared scale."
    )


def _assert_dump(dump: Mapping[str, Any], where: str) -> None:
    """Assert one dump object is well formed. Pure: no I/O, no mutation.

    Args:
        dump: The parsed dump object.
        where: The file path or the side name it came from, quoted in
            every message so a failure is traceable to its source.

    Raises:
        DumpShapeError: The keys, the columns, the primary key, the row
            count or a row's width is wrong.
        TableNotInScopeError: Its table is out of scope.
        UnknownTableError: Its table is not a table of the schema.
        DuplicateKeyError: A primary-key value appears twice.
        UnexpectedNullError: A value is null.
        NumericPolicyError: A value is a float (rule R-2).
        UnexpectedValueTypeError: A value is of an impossible type.
    """
    keys = tuple(dump.keys())
    if keys != DUMP_KEYS:
        raise DumpShapeError(
            f"{where}: a dump object must carry exactly the keys "
            f"{list(DUMP_KEYS)} in that order; got {list(keys)}. The key "
            f"order is part of the byte-identical guarantee (rule R-6) "
            f"and no other key may appear - not a timestamp, a server "
            f"version, a scenario name or a side. The layout is fixed at "
            f"[harness/dump_tables.py:L544-L550]."
        )

    table = dump["table"]
    if not isinstance(table, str):
        raise DumpShapeError(
            f"{where}: `table` must be the table name as a string; got "
            f"{type(table).__name__} ({table!r})."
        )
    # Raises TableNotInScopeError or UnknownTableError, both exit 2.
    table_spec(table)

    columns = dump["columns"]
    if isinstance(columns, str) or not isinstance(columns, Sequence):
        raise DumpShapeError(
            f"{where}: `{table}`: `columns` must be a list of column "
            f"names; got {type(columns).__name__} ({columns!r})."
        )
    seen: set[str] = set()
    for position, name in enumerate(columns, start=1):
        if not isinstance(name, str):
            raise DumpShapeError(
                f"{where}: `{table}`: every entry of `columns` must be a "
                f"column name as a string; position {position} is "
                f"{type(name).__name__} ({name!r})."
            )
        if not name:
            raise DumpShapeError(
                f"{where}: `{table}`: `columns` position {position} is "
                f"the empty string. Every column of the frozen schema is "
                f"named."
            )
        if name in seen:
            raise DumpShapeError(
                f"{where}: `{table}`: `columns` names {name!r} more than "
                f"once. Rows are positional, so a repeated column name "
                f"would make a reported difference ambiguous."
            )
        seen.add(name)

    primary_key = dump["primary_key"]
    if not isinstance(primary_key, str):
        raise DumpShapeError(
            f"{where}: `{table}`: `primary_key` must be the column name "
            f"as a string; got {type(primary_key).__name__} "
            f"({primary_key!r})."
        )
    if primary_key not in seen:
        raise DumpShapeError(
            f"{where}: `{table}`: `primary_key` is {primary_key!r}, which "
            f"is not one of the {len(seen)} columns the dump lists. Rows "
            f"are aligned on the primary-key VALUE, so the key must be a "
            f"column that is present. The frozen schema declares "
            f"`{IN_SCOPE[table].primary_key}` "
            f"[mysql/ACASDB.sql:L{IN_SCOPE[table].schema_line}]."
        )

    rows = dump["rows"]
    if isinstance(rows, str) or not isinstance(rows, Sequence):
        raise DumpShapeError(
            f"{where}: `{table}`: `rows` must be a list of rows; got "
            f"{type(rows).__name__} ({rows!r})."
        )
    row_count = dump["row_count"]
    if isinstance(row_count, bool) or not isinstance(row_count, int):
        raise DumpShapeError(
            f"{where}: `{table}`: `row_count` must be an integer; got "
            f"{type(row_count).__name__} ({row_count!r})."
        )
    if row_count != len(rows):
        raise DumpShapeError(
            f"{where}: `{table}`: `row_count` is {row_count} but the dump "
            f"carries {len(rows)} row(s). One of the two is wrong, so the "
            f"file cannot be trusted to be complete."
        )

    width = len(columns)
    key_index = list(columns).index(primary_key)
    keys_seen: dict[str | int, int] = {}
    for row_index, row in enumerate(rows):
        if isinstance(row, str) or not isinstance(row, Sequence):
            raise DumpShapeError(
                f"{where}: `{table}`: row {row_index} is "
                f"{type(row).__name__} ({row!r}); every row must be a "
                f"list of values positionally aligned with `columns`."
            )
        if len(row) != width:
            raise DumpShapeError(
                f"{where}: `{table}`: row {row_index} carries "
                f"{len(row)} value(s) but the dump lists {width} "
                f"column(s). Rows are positional, so a ragged row has no "
                f"meaningful alignment with the column list."
            )
        for position, value in enumerate(row):
            _assert_value(
                value,
                where=where,
                table=table,
                column=str(columns[position]),
                row_index=row_index,
            )

        key = row[key_index]
        # A str|int by construction: _assert_value has just accepted
        # every value in this row, and it admits nothing else.
        if key in keys_seen:
            raise DuplicateKeyError(
                f"{where}: `{table}`: the primary-key value "
                f"{_render_value(key)} appears in row {keys_seen[key]} "
                f"and again in row {row_index}. `{primary_key}` is a "
                f"PRIMARY KEY column "
                f"[mysql/ACASDB.sql:L{IN_SCOPE[table].schema_line}], so a "
                f"duplicate is impossible from the database and means the "
                f"dump is malformed. Rows are aligned on that value, so "
                f"there would be no unambiguous row to compare against."
            )
        keys_seen[key] = row_index


def read_dump(path: Path | str) -> dict[str, Any]:
    """Read one dump file, without asserting its shape.

    Args:
        path: The `<TABLE>.json` file to read.

    Returns:
        The parsed dump object.

    Raises:
        MissingTableFileError: The file does not exist.
        DumpReadError: It could not be read, is not valid UTF-8 JSON, or
            does not parse to a JSON object.
    """
    target = Path(path)
    if not target.exists():
        raise MissingTableFileError(
            f"the dump {target} does not exist. A missing file is NOT an "
            f"empty diff."
        )
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise DumpReadError(
            f"could not read the dump {target}: {exc}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise DumpReadError(
            f"the dump {target} is not valid UTF-8: {exc}. "
            f"harness/dump_tables.py and harness/normalize.py both write "
            f"UTF-8 with ensure_ascii=True, so every byte of a dump is "
            f"ASCII."
        ) from exc
    try:
        parsed = json.loads(text)
    except ValueError as exc:
        raise DumpReadError(
            f"{target} is not valid JSON: {exc}. It should be a dump "
            f"written by harness/dump_tables.py and canonicalised by "
            f"harness/normalize.py."
        ) from exc
    if not isinstance(parsed, dict):
        raise DumpReadError(
            f"{target} parses to {type(parsed).__name__}, not a JSON "
            f"object. A dump is an object carrying the five keys "
            f"{list(DUMP_KEYS)}."
        )
    return parsed


def load_dump(path: Path | str) -> dict[str, Any]:
    """Read one dump file and assert it is well formed.

    Every failure is exit 2: a dump that cannot be trusted cannot produce
    a verdict.

    Args:
        path: The `<TABLE>.json` file to read.

    Returns:
        The parsed, asserted dump object. Nothing in it is altered.

    Raises:
        MissingTableFileError: The file does not exist.
        DumpReadError: It is unreadable or is not a JSON object.
        DumpShapeError: Its shape is wrong, including its name not
            matching the table it declares.
        TableNotInScopeError: Its table is out of scope.
        UnknownTableError: Its table is not a table of the schema.
        DuplicateKeyError: A primary-key value appears twice.
        UnexpectedNullError: A value is null.
        NumericPolicyError: A value is a float (rule R-2).
        UnexpectedValueTypeError: A value is of an impossible type.
    """
    target = Path(path)
    dump = read_dump(target)
    _assert_dump(dump, str(target))

    # The file name and the declared table must agree, or a report would
    # name a table whose data came from somewhere else.
    stem = target.name.removesuffix(DUMP_SUFFIX)
    if stem != dump["table"]:
        raise DumpShapeError(
            f"{target}: the file is named for table {stem!r} but declares "
            f"{dump['table']!r}. Both producers name a dump "
            f"`<TABLE>{DUMP_SUFFIX}` for the table it holds "
            f"[harness/dump_tables.py:L1667], and a report that named the "
            f"wrong table would be worthless as evidence."
        )
    return dump


# ---------------------------------------------------------------------------
#  RENDERING ONE VALUE, AND ORDERING KEYS
#
#  Values are rendered as JSON, which quotes strings and leaves integers
#  bare. That is exactly the distinction the report needs: a trailing
#  space, a leading space and the empty string are all visible, and `1`
#  can never be mistaken for `"1"`. ensure_ascii=True keeps the report
#  byte-identical whatever the locale (rule R-6).
# ---------------------------------------------------------------------------


def _render_value(value: str | int) -> str:
    """Render one value for the report.

    Args:
        value: A dumped value - a `str` or an `int`.

    Returns:
        `1234` for an integer, `"1234.56"` for a string. Quoting is what
        makes padding and emptiness visible.
    """
    return json.dumps(value, ensure_ascii=True)


def _key_sort_key(key: str | int) -> tuple[int, int, str]:
    """Build a total, deterministic sort key for a primary-key value.

    Numeric keys sort NUMERICALLY, so `2` comes before `10`; character
    keys sort by ASCII, which is what Python's own string ordering gives
    for the ASCII-only content a dump can hold. Integers sort before
    strings, so that a dump whose key column was serialised
    inconsistently still produces a stable, reproducible order rather
    than a TypeError.

    Args:
        key: The primary-key value.

    Returns:
        A tuple ordering integers first and numerically, then strings by
        code point.
    """
    if isinstance(key, int):
        return (0, key, "")
    return (1, 0, key)


# ---------------------------------------------------------------------------
#  THE DIFFERENCE MODEL
#
#  Frozen dataclasses, so a diff cannot be edited after the fact, and
#  every collection inside one is a tuple in its final report order -
#  sorted once, at construction. `is_empty` is the single cheap question
#  the eight tests/scenarios/test_*.py files ask, and `__bool__` is its
#  inverse so `if diff:` reads as "if anything differs".
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ValueDifference:
    """One column of one row differing between the two sides.

    Attributes:
        column: The column name.
        ordinal: Its 1-based position in the table's column list, which
            is the schema's ORDINAL_POSITION. SYSTEM-REC has 169
            columns; without an ordinal a reader cannot find the
            difference by hand (rule R-5).
        cobol: The value the compiled oracle produced.
        python: The value the migrated cycle produced.
    """

    column: str
    ordinal: int
    cobol: str | int
    python: str | int

    @property
    def type_mismatch(self) -> bool:
        """Whether the two values are of different Python types.

        A type mismatch is a difference in its own right: it would mean
        the two dumps were produced by inconsistent serialisation, which
        is a real defect rather than something to smooth over.
        """
        return type(self.cobol) is not type(self.python)


@dataclass(frozen=True, slots=True)
class RowDifference:
    """One row, identified by its primary key, differing in some columns.

    Attributes:
        key: The primary-key value the two rows were aligned on.
        values: The differing columns, in schema ordinal order.
    """

    key: str | int
    values: tuple[ValueDifference, ...]


@dataclass(frozen=True, slots=True)
class TableDiff:
    """Everything that differs for one table.

    A one-sided table is expressed by `in_cobol` or `in_python` being
    false; that is a DIFFERENCE, never a reason to skip the table.

    Attributes:
        table: The in-scope table name.
        primary_key: The column rows were aligned on.
        in_cobol: Whether the oracle side had a dump for this table.
        in_python: Whether the migrated side had one.
        cobol_columns: The oracle's column list, in its own order.
        python_columns: The migrated side's column list.
        cobol_row_count: The oracle's row count.
        python_row_count: The migrated side's row count.
        missing_in_python: Primary keys the oracle produced and the
            migrated cycle did not, ascending.
        missing_in_cobol: Primary keys the migrated cycle produced and
            the oracle did not, ascending. Reported separately from the
            above because the two directions are materially different
            findings.
        value_differences: Rows present on both sides that differ in at
            least one column, ascending by key.
        rows_compared: Whether the rows were compared at all. False when
            the column lists disagree, because rows are positional and
            there is then no meaningful alignment, and false when a
            table is one-sided.
        cobol_key_types: The distinct Python type names of the oracle's
            primary-key values, ascending. Recorded so that a
            serialisation difference IN THE ALIGNMENT COLUMN can be named
            rather than merely implied - see `key_types_differ`.
        python_key_types: The same for the migrated side.
    """

    table: str
    primary_key: str
    in_cobol: bool = True
    in_python: bool = True
    cobol_columns: tuple[str, ...] = ()
    python_columns: tuple[str, ...] = ()
    cobol_row_count: int = 0
    python_row_count: int = 0
    missing_in_python: tuple[str | int, ...] = ()
    missing_in_cobol: tuple[str | int, ...] = ()
    value_differences: tuple[RowDifference, ...] = ()
    rows_compared: bool = True
    cobol_key_types: tuple[str, ...] = ()
    python_key_types: tuple[str, ...] = ()

    @property
    def table_missing(self) -> bool:
        """Whether the table's dump was absent from one of the trees."""
        return not (self.in_cobol and self.in_python)

    @property
    def columns_differ(self) -> bool:
        """Whether the two column lists disagree in names, order or count.

        Only meaningful when both sides were present; a one-sided table
        has nothing to compare its columns with.
        """
        if self.table_missing:
            return False
        return self.cobol_columns != self.python_columns

    @property
    def row_count_differs(self) -> bool:
        """Whether the two row counts disagree.

        Reported once per table as a headline, in addition to the
        key-level detail that explains it.
        """
        if self.table_missing:
            return False
        return self.cobol_row_count != self.python_row_count

    @property
    def key_types_differ(self) -> bool:
        """Whether the two sides serialised the ALIGNMENT COLUMN differently.

        A type mismatch in an ordinary column is reported per row with
        both type names. A type mismatch in the primary key cannot be,
        because rows are aligned on that column's VALUE and `1` is not
        `"1"`: the two rows land under different keys and are correctly
        reported as one-sided. Coercing them together to pair them would
        be exactly the numeric coercion rule R-2 forbids.

        So this flag names the cause instead. It is purely diagnostic and
        purely additive: it never pairs a row, never suppresses a
        one-sided finding, and cannot turn an empty diff into a non-empty
        one - if the key types differ then no key is shared, so any row
        at all already produced a one-sided finding, and if neither side
        has a row then both type sets are empty and equal.
        """
        if self.table_missing or not self.rows_compared:
            return False
        if not self.cobol_key_types or not self.python_key_types:
            return False
        return self.cobol_key_types != self.python_key_types

    @property
    def value_difference_count(self) -> int:
        """The number of individual differing column values."""
        return sum(len(row.values) for row in self.value_differences)

    @property
    def detail_count(self) -> int:
        """The number of key-level findings, which is what truncation caps."""
        return (
            len(self.missing_in_python)
            + len(self.missing_in_cobol)
            + self.value_difference_count
        )

    @property
    def total_differences(self) -> int:
        """Every finding for this table, structural and detailed alike."""
        structural = (
            int(self.table_missing)
            + int(self.columns_differ)
            + int(self.row_count_differs)
            + int(self.key_types_differ)
        )
        return structural + self.detail_count

    @property
    def is_empty(self) -> bool:
        """Whether the two sides agree completely for this table."""
        return self.total_differences == 0

    def __bool__(self) -> bool:
        """Whether anything differs, so `if table_diff:` reads naturally."""
        return not self.is_empty


@dataclass(frozen=True, slots=True)
class TreeDiff:
    """Everything that differs between two normalised trees.

    Attributes:
        tables: One entry per compared table, in the report's table
            order - the scenario's affected-table order when one was
            given, ASCII-sorted otherwise. Tables that agree are kept in
            the sequence, so a caller can see what WAS compared; they
            simply contribute nothing to the report.
        cobol_dir: The oracle tree that was compared, for the operator's
            benefit. Never rendered into the report - an absolute path
            would break byte-determinism (rule R-6).
        python_dir: The migrated-cycle tree that was compared.
    """

    tables: tuple[TableDiff, ...]
    cobol_dir: Path | None = None
    python_dir: Path | None = None

    @property
    def differing(self) -> tuple[TableDiff, ...]:
        """Only the tables that differ, in report order."""
        return tuple(table for table in self.tables if not table.is_empty)

    @property
    def total_differences(self) -> int:
        """Every finding across every table."""
        return sum(table.total_differences for table in self.tables)

    @property
    def is_empty(self) -> bool:
        """THE PASS CONDITION. True when the two trees are identical.

        Agent Action Plan section 0.8.5: "the diff must be empty". This
        is the single question the eight scenario tests ask, and the
        single question `main` turns into an exit code.
        """
        return self.total_differences == 0

    def __bool__(self) -> bool:
        """Whether anything differs, so `if diff:` reads naturally."""
        return not self.is_empty


# ---------------------------------------------------------------------------
#  COMPARING ONE TABLE
#
#  Pure: no I/O, no clock, no environment, no mutation of its arguments.
#  Exact: `==` after a type check, and nothing else. There is no
#  tolerance, no epsilon, no case-insensitive compare, no
#  whitespace-insensitive compare and no numeric coercion, because Agent
#  Action Plan section 0.1.1 requires "a behaviorally exact clone" and a
#  tolerance would defeat the entire engagement (rule R-2).
#
#  harness/normalize.py has already canonicalised the three
#  representation artefacts - trailing spaces in character columns,
#  decimal scale rendering, and the two-digit versus four-digit date text
#  forms. ANYTHING LEFT IS REAL.
# ---------------------------------------------------------------------------


def _key_type_names(rows_by_key: Mapping[str | int, Any]) -> tuple[str, ...]:
    """Name the distinct Python types of a side's primary-key values.

    Args:
        rows_by_key: The side's rows, keyed by primary-key value.

    Returns:
        The distinct type names, ascending, so the comparison against the
        other side is deterministic. Empty when the side has no rows.
    """
    return tuple(sorted({type(key).__name__ for key in rows_by_key}))


def diff_table(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> TableDiff:
    """Compare two dump objects for the same table.

    Args:
        left: The COBOL oracle's dump - the specification side.
        right: The migrated Python cycle's dump.

    Returns:
        A `TableDiff`. It is empty, and falsy, when the two agree.

    Raises:
        DumpShapeError: Either object is malformed, they are for
            different tables, or they disagree on the primary key - the
            alignment column, so a disagreement there leaves no
            meaningful way to compare.
        TableNotInScopeError: Either table is out of scope.
        UnknownTableError: Either table is not a table of the schema.
        DuplicateKeyError: A primary-key value appears twice.
        UnexpectedNullError: A value is null.
        NumericPolicyError: A value is a float (rule R-2).
        UnexpectedValueTypeError: A value is of an impossible type.
    """
    _assert_dump(left, LABEL_COBOL)
    _assert_dump(right, LABEL_PYTHON)

    table = left["table"]
    if table != right["table"]:
        raise DumpShapeError(
            f"the two dumps are for different tables: {LABEL_COBOL} says "
            f"{table!r} and {LABEL_PYTHON} says {right['table']!r}. Only "
            f"the same table on both sides can be compared."
        )

    primary_key = left["primary_key"]
    if primary_key != right["primary_key"]:
        raise DumpShapeError(
            f"`{table}`: the two dumps disagree on the primary key - "
            f"{LABEL_COBOL} says {primary_key!r} and {LABEL_PYTHON} says "
            f"{right['primary_key']!r}. Rows are aligned on that column's "
            f"VALUE, so there is no meaningful alignment to make. The "
            f"frozen schema declares `{IN_SCOPE[table].primary_key}` "
            f"[mysql/ACASDB.sql:L{IN_SCOPE[table].schema_line}]; both "
            f"dumps should carry it, since both come from "
            f"harness/dump_tables.py."
        )

    cobol_columns = tuple(str(name) for name in left["columns"])
    python_columns = tuple(str(name) for name in right["columns"])
    cobol_rows: Sequence[Sequence[str | int]] = left["rows"]
    python_rows: Sequence[Sequence[str | int]] = right["rows"]

    # A COLUMN-SET OR COLUMN-ORDER DIFFERENCE IS STRUCTURAL. Rows are
    # positional, so there is no meaningful alignment left to make: the
    # finding is reported and this table's rows are NOT compared, which is
    # what the file specification's validation step 12 requires. Comparing
    # them anyway would emit a cascade of spurious differences that told a
    # reader nothing.
    if cobol_columns != python_columns:
        return TableDiff(
            table=table,
            primary_key=primary_key,
            cobol_columns=cobol_columns,
            python_columns=python_columns,
            cobol_row_count=len(cobol_rows),
            python_row_count=len(python_rows),
            rows_compared=False,
        )

    columns = cobol_columns
    key_index = columns.index(primary_key)

    # ROWS ARE ALIGNED ON THE PRIMARY-KEY VALUE, NEVER ON POSITION.
    # harness/normalize.py preserves the primary-key ordering it inherits
    # from `ORDER BY <primary key>`, so position would usually work - and
    # would be catastrophic when it did not, turning one inserted row into
    # a cascade of hundreds of spurious column differences. Duplicate keys
    # were already refused by `_assert_dump`, so each dictionary below has
    # exactly one row per key.
    cobol_by_key: dict[str | int, Sequence[str | int]] = {
        row[key_index]: row for row in cobol_rows
    }
    python_by_key: dict[str | int, Sequence[str | int]] = {
        row[key_index]: row for row in python_rows
    }

    missing_in_python = tuple(
        sorted(
            (key for key in cobol_by_key if key not in python_by_key),
            key=_key_sort_key,
        )
    )
    missing_in_cobol = tuple(
        sorted(
            (key for key in python_by_key if key not in cobol_by_key),
            key=_key_sort_key,
        )
    )

    shared = sorted(
        (key for key in cobol_by_key if key in python_by_key),
        key=_key_sort_key,
    )

    differences: list[RowDifference] = []
    for key in shared:
        cobol_row = cobol_by_key[key]
        python_row = python_by_key[key]
        # Columns in SCHEMA ORDINAL ORDER, never alphabetical, so a reader
        # can walk the report against the CREATE TABLE statement.
        values = tuple(
            ValueDifference(
                column=columns[position],
                ordinal=position + 1,
                cobol=cobol_value,
                python=python_value,
            )
            for position, (cobol_value, python_value) in enumerate(
                zip(cobol_row, python_row, strict=True)
            )
            # EXACT, and nothing else. A type mismatch fails this test as
            # surely as a value mismatch, and is reported with both type
            # names rather than coerced away.
            if type(cobol_value) is not type(python_value)
            or cobol_value != python_value
        )
        if values:
            differences.append(RowDifference(key=key, values=values))

    return TableDiff(
        table=table,
        primary_key=primary_key,
        cobol_columns=columns,
        python_columns=columns,
        cobol_row_count=len(cobol_rows),
        python_row_count=len(python_rows),
        missing_in_python=missing_in_python,
        missing_in_cobol=missing_in_cobol,
        value_differences=tuple(differences),
        cobol_key_types=_key_type_names(cobol_by_key),
        python_key_types=_key_type_names(python_by_key),
    )


# ---------------------------------------------------------------------------
#  COMPARING TWO TREES, SEQUENTIALLY  (rule R-3)
#
#  One table at a time, in a plain loop, in a fixed order. There is no
#  thread, no event loop, no process pool and no synchronisation primitive
#  anywhere in this file.
#
#  A TABLE PRESENT IN ONE TREE AND ABSENT FROM THE OTHER IS NEVER SKIPPED.
#  What it IS depends on who chose the table, and the two cases are
#  genuinely different:
#
#    * DISCOVERED, because no selection was given, so the union of the two
#      trees was taken: a one-sided table is a reported DIFFERENCE, exit 1.
#      That asymmetry is precisely what a naive intersection would hide.
#    * REQUESTED, by --tables or by a scenario's affected-table list: a
#      one-sided table is exit 2. The caller asserted that the scenario
#      affects that table, and harness/dump_tables.py writes a file for
#      every table it is asked to dump whatever its row count - an empty
#      table still gets `"row_count": 0` - so a MISSING FILE can never be
#      produced by a behavioural difference. It means one side's dump or
#      normalise stage did not run for that table, which is a harness
#      malfunction and not something to render a verdict on.
#
#  Neither case can ever be a false pass, which is what matters. The row
#  level is where a behavioural asymmetry actually shows up: anomaly #4's
#  half-posted double entry [irs/irs030.cbl:L1635-L1652] leaves an
#  unbalanced debit and NO posting record, which surfaces as a one-sided
#  ROW, reported as missing_in_python or missing_in_cobol.
# ---------------------------------------------------------------------------


def discover_tables(directory: Path | str) -> tuple[str, ...]:
    """List the tables a tree holds dumps for.

    Args:
        directory: A normalised tree.

    Returns:
        The table names, ASCII-ascending - sorted once, so the report's
        order can never depend on filesystem iteration order (rule R-6).

    Raises:
        MissingTreeError: The directory does not exist or is not a
            directory.
        UnknownTableError: It holds a `<NAME>.json` file whose name is
            not a table of the frozen schema.
        TableNotInScopeError: It holds a dump for an out-of-scope table.
    """
    source = Path(directory)
    if not source.is_dir():
        raise MissingTreeError(
            f"{source} is not a directory. It should be the directory "
            f"harness/normalize.py wrote its <TABLE>.json files into, for "
            f"example $ACAS_OUT/<scenario>/{LABEL_COBOL}"
            f"{NORMALIZED_SUFFIX}."
        )

    names: list[str] = []
    for entry in sorted(source.iterdir(), key=lambda item: item.name):
        name = entry.name
        # Both producers write through `.<stem>.json.tmp` and then
        # os.replace, so a dot-prefixed name is a leftover from a failed
        # write and never a dump. Skipped rather than compared.
        if name.startswith(TEMP_PREFIX):
            continue
        if not name.endswith(DUMP_SUFFIX):
            continue
        if not entry.is_file():
            continue
        table = name[: -len(DUMP_SUFFIX)]
        # Raises rather than ignoring: harness/normalize.py writes ONLY
        # `<TABLE>.json` files for in-scope tables into its destination,
        # so anything else there means the tree is not what it claims to
        # be, and silently ignoring a file in a tree being judged would
        # be exactly the wrong instinct.
        table_spec(table)
        names.append(table)
    return tuple(sorted(names))


def diff_trees(
    left_dir: Path | str,
    right_dir: Path | str,
    tables: Sequence[str] | None = None,
    *,
    allow_raw: bool = False,
) -> TreeDiff:
    """Compare two normalised trees, table by table, sequentially.

    Args:
        left_dir: The COBOL oracle's normalised tree - the specification
            side, reported as `cobol`.
        right_dir: The migrated Python cycle's normalised tree, reported
            as `python`.
        tables: The tables to compare, in the order to report them -
            normally the scenario's affected-table list. When omitted,
            the UNION of the tables the two trees hold is compared, in
            ASCII order, and a table present in only one of them is
            reported as a difference. When given, every named table must
            be present in BOTH trees, since a dump file exists for every
            table that was dumped whatever its row count.
        allow_raw: Permit comparing directories whose names do not mark
            them as normalised. A debugging escape; it warns loudly.

    Returns:
        A `TreeDiff`. `is_empty` is the pass condition.

    Raises:
        MissingTreeError: Either directory is absent or is not a
            directory.
        SameTreeError: Both sides name the same directory, which would
            always compare equal and so would be a false pass.
        RawTreeError: A directory is not a normalised tree and
            `allow_raw` is false.
        EmptyComparisonError: There is no table to compare.
        MissingTableFileError: A requested table's dump is absent from
            one or both trees. Absence is a reported difference only for
            a table that was DISCOVERED rather than requested.
        UnknownTableError: A requested or discovered name is not a table
            of the frozen schema.
        TableNotInScopeError: A requested or discovered name is out of
            scope.
        DumpReadError: A dump is unreadable or is not a JSON object.
        DumpShapeError: A dump's shape is wrong, or the two sides
            disagree on the alignment column.
        DuplicateKeyError: A primary-key value appears twice in a dump.
        UnexpectedNullError: A value is null.
        NumericPolicyError: A value is a float (rule R-2).
        UnexpectedValueTypeError: A value is of an impossible type.
    """
    left = Path(left_dir)
    right = Path(right_dir)

    # COMPARING A TREE WITH ITSELF ALWAYS PASSES, whatever the migration
    # did, so it is refused rather than answered. `resolve` is non-strict
    # and normalises `..` and symlinks, the same test
    # harness/normalize.py makes for the same reason [L2700-L2714].
    if left.resolve() == right.resolve():
        raise SameTreeError(
            f"both sides name the same directory, {left}. A tree always "
            f"equals itself, so the comparison would report an empty diff "
            f"whatever the migration produced - a FALSE PASS. Pass the "
            f"{LABEL_COBOL} tree and the {LABEL_PYTHON} tree, for example "
            f"`$ACAS_OUT/<scenario>/{LABEL_COBOL}{NORMALIZED_SUFFIX}` and "
            f"`$ACAS_OUT/<scenario>/{LABEL_PYTHON}{NORMALIZED_SUFFIX}`."
        )

    _assert_tree(left, LABEL_COBOL, allow_raw=allow_raw)
    _assert_tree(right, LABEL_PYTHON, allow_raw=allow_raw)

    # Which of the two one-sided-table dispositions applies is decided
    # here, once, by who chose the tables.
    discovered = tables is None

    if discovered:
        # The UNION, not the intersection: an intersection would silently
        # drop a table one side produced and the other did not, which is
        # a difference and one of the more diagnostic ones.
        selected = tuple(
            sorted(set(discover_tables(left)) | set(discover_tables(right)))
        )
        if not selected:
            raise EmptyComparisonError(
                f"neither {left} nor {right} holds a single "
                f"`<TABLE>{DUMP_SUFFIX}` file, so there is nothing to "
                f"compare. An empty comparison is NOT an empty diff: it "
                f"would read as a pass while proving nothing. Run stages "
                f"3 and 4 - harness/dump_tables.py then "
                f"harness/normalize.py - for both sides first."
            )
        _warn(
            "no table selection given, so the union of the tables the two "
            "trees hold will be compared. A scenario comparison should be "
            "bounded by its affected-table list (--scenario-file or "
            "--tables): [general/general.cbl:L656-L691] rewrites "
            "SYSTEM-REC, SYSDEFLT-REC and SYSTOT-REC when the operator "
            "leaves the menu with \"X\", and the Python cycle has no menu, "
            "so an unbounded comparison can fail on a menu-shell side "
            "effect the migration does not reproduce."
        )
    else:
        selected = _validate_table_selection(tables)

    results: list[TableDiff] = []
    for table in selected:
        filename = dump_filename(table)
        left_path = left / filename
        right_path = right / filename
        in_cobol = left_path.is_file()
        in_python = right_path.is_file()

        if not in_cobol and not in_python:
            raise MissingTableFileError(
                f"`{table}` was requested but neither {left_path} nor "
                f"{right_path} exists, so there is nothing to compare for "
                f"it. That is exit 2 and never a pass. Run stages 3 and 4 "
                f"- harness/dump_tables.py then harness/normalize.py - for "
                f"both sides, or drop `{table}` from the selection if the "
                f"scenario does not affect it."
            )

        if (not in_cobol or not in_python) and not discovered:
            # AN EXPLICITLY REQUESTED TABLE MUST BE PRESENT ON BOTH SIDES.
            # harness/dump_tables.py writes a file for every table it is
            # asked to dump whatever the row count - an empty table still
            # gets `"row_count": 0` - so a missing FILE cannot have been
            # produced by a behavioural difference. It means one side's
            # dump or normalise stage did not cover this table, and a
            # verdict rendered on half a comparison would be worthless.
            missing_side = LABEL_PYTHON if in_cobol else LABEL_COBOL
            missing_path = right_path if in_cobol else left_path
            raise MissingTableFileError(
                f"`{table}` was requested but its dump is absent from the "
                f"{missing_side} tree ({missing_path}). A dump file exists "
                f"for every table that was dumped, whatever its row count "
                f"- an empty table still gets \"row_count\": 0 - so a "
                f"missing file is a stage that did not run, not a "
                f"behavioural difference. Dump and normalise the SAME "
                f"table selection on both sides; comparing half a "
                f"selection would produce a verdict that proves nothing."
            )

        specification = IN_SCOPE[table]
        if not in_cobol or not in_python:
            # A ONE-SIDED DISCOVERED TABLE IS A DIFFERENCE, never a skip:
            # a naive intersection would have hidden it. The present side
            # is still loaded and asserted, so a malformed dump is still
            # reported as such, and so the row count can be quoted.
            present = left_path if in_cobol else right_path
            dump = load_dump(present)
            row_count = int(dump["row_count"])
            columns = tuple(str(name) for name in dump["columns"])
            results.append(
                TableDiff(
                    table=table,
                    primary_key=specification.primary_key,
                    in_cobol=in_cobol,
                    in_python=in_python,
                    cobol_columns=columns if in_cobol else (),
                    python_columns=columns if in_python else (),
                    cobol_row_count=row_count if in_cobol else 0,
                    python_row_count=row_count if in_python else 0,
                    rows_compared=False,
                )
            )
            continue

        results.append(diff_table(load_dump(left_path), load_dump(right_path)))

    return TreeDiff(tables=tuple(results), cobol_dir=left, python_dir=right)


def _validate_table_selection(tables: Sequence[str]) -> tuple[str, ...]:
    """Validate an explicit table selection, preserving its order.

    Args:
        tables: The requested table names, in the order to report them.

    Returns:
        The names, order preserved.

    Raises:
        EmptyComparisonError: The selection is empty.
        DumpShapeError: An entry is not a string.
        UnknownTableError: An entry is not a table of the schema.
        TableNotInScopeError: An entry is out of scope.
        ValueError: An entry appears twice.
    """
    selected: list[str] = []
    for entry in tables:
        if not isinstance(entry, str):
            raise DumpShapeError(
                f"a table selection must hold table names as strings; got "
                f"{type(entry).__name__} ({entry!r})."
            )
        table_spec(entry)
        if entry in selected:
            raise ValueError(
                f"the table selection names {entry!r} more than once. Each "
                f"table is compared once, and repeating it would repeat "
                f"its findings in the report."
            )
        selected.append(entry)

    if not selected:
        raise EmptyComparisonError(
            "the table selection is empty, so there is nothing to "
            "compare. An empty comparison is NOT an empty diff: it would "
            "read as a pass while proving nothing. Agent Action Plan "
            "section 0.4.1.7 requires each scenario to declare the tables "
            "it affects, and harness/run_cobol_scenario.sh:L1329-L1336 "
            "says the same: the comparison must be bounded by an explicit "
            "per-scenario list."
        )
    return tuple(selected)


# ---------------------------------------------------------------------------
#  THE SCENARIO'S AFFECTED-TABLE LIST
#
#  Bounding the comparison by the SCENARIO is the protocol, and the
#  alternative - an ignore-list here - is forbidden by rule R-4. Both
#  spellings of the key are accepted, matching
#  [harness/dump_tables.py:L641-L644] and the keys
#  harness/run_cobol_scenario.sh reads [L1323-L1326], so one scenario file
#  serves every stage.
# ---------------------------------------------------------------------------


def scenario_tables(path: Path | str) -> tuple[str, ...]:
    """Read a scenario's affected-table list, in the order it declares it.

    Only that one list is read: no seed data is interpreted and no input
    is validated, because interpreting a scenario's declared contents
    would be exactly the added validation rule R-3 forbids.

    Args:
        path: The scenario definition to read.

    Returns:
        The table names, in the scenario's own order - which becomes the
        report's table order.

    Raises:
        ScenarioFileError: PyYAML is unavailable, or the file is missing,
            unreadable, not a mapping, carries neither key or both, or
            its list is empty or holds something that is not a table
            name.
        UnknownTableError: The list names something that is not a table.
        TableNotInScopeError: The list names an out-of-scope table.
    """
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML is pinned
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
            f"the scenario definition {source} must be a mapping at the "
            f"top level; got {type(document).__name__}."
        )

    present = [key for key in _SCENARIO_TABLE_KEYS if key in document]
    if not present:
        raise ScenarioFileError(
            f"the scenario definition {source} carries no affected-table "
            f"list. Add one under {_SCENARIO_TABLE_KEYS[0]} (or "
            f"{_SCENARIO_TABLE_KEYS[1]}) naming the tables the scenario "
            f"affects, as Agent Action Plan section 0.4.1.7 specifies. It "
            f"is required, not optional: bounding the comparison by the "
            f"scenario is what keeps the menu-exit rewrite at "
            f"[general/general.cbl:L656-L691] from failing an otherwise "
            f"correct run."
        )
    if len(present) > 1:
        raise ScenarioFileError(
            f"the scenario definition {source} carries both {present[0]} "
            f"and {present[1]}. They mean the same thing, so exactly one "
            f"must be used."
        )

    declared = document[present[0]]
    if isinstance(declared, str) or not isinstance(declared, Sequence):
        raise ScenarioFileError(
            f"{present[0]} in {source} must be a list of table names; got "
            f"{type(declared).__name__}."
        )

    names: list[str] = []
    for entry in declared:
        if not isinstance(entry, str):
            raise ScenarioFileError(
                f"{present[0]} in {source} contains "
                f"{type(entry).__name__} ({entry!r}); every entry must be "
                f"a table name."
            )
        table_spec(entry)
        if entry in names:
            raise ScenarioFileError(
                f"{present[0]} in {source} names table {entry!r} more than "
                f"once."
            )
        names.append(entry)

    if not names:
        raise ScenarioFileError(
            f"{present[0]} in {source} is empty. A scenario that affects "
            f"no table has nothing to compare, and an empty comparison "
            f"would read as a pass while proving nothing; name at least "
            f"one table."
        )
    return tuple(names)


def resolve_tables(
    *,
    tables: str | None = None,
    scenario_file: Path | str | None = None,
) -> tuple[str, ...] | None:
    """Resolve the command line's table selectors into a table list.

    Args:
        tables: A comma-separated list of table names.
        scenario_file: A scenario definition to read the list from.

    Returns:
        The table names in the order to report them, or `None` when
        neither selector was given - which asks `diff_trees` for the
        union of what the two trees hold.

    Raises:
        ValueError: Both selectors were given, or `tables` is empty or
            names a table twice.
        ScenarioFileError: The scenario definition is unusable.
        UnknownTableError: A named table is not a table of the schema.
        TableNotInScopeError: A named table is out of scope.
    """
    if tables is not None and scenario_file is not None:
        raise ValueError(
            "--tables and --scenario-file were both given; they are "
            "alternative ways of naming the same list, so use exactly "
            "one. --scenario-file is the protocol; --tables is for "
            "narrowing a single table by hand."
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
        return _validate_table_selection(names)

    return None


# ---------------------------------------------------------------------------
#  THE REPORT
#
#  BYTE-DETERMINISTIC for a given pair of inputs (rule R-6). No timestamp,
#  no host name, no process id, no absolute path, no elapsed time, no tool
#  version, and no dependence on dictionary or filesystem iteration order:
#  every collection was sorted once at construction, and the table order
#  is the caller's or ASCII.
#
#  EVIDENCE-GRADE (rule R-5). docs/migration/scenario-diff-evidence.md is
#  built from this output, so every line names its table, its
#  primary-key value where it has one, and its column by NAME and by
#  1-based ORDINAL.
# ---------------------------------------------------------------------------

# The report's finding labels. Fixed strings, so the report is greppable
# and a downstream document can quote them. `missing_in_python` and
# `missing_in_cobol` are deliberately DIFFERENT words rather than one word
# with a direction argument: "the Python run created a row the COBOL run
# did not" is a materially different finding from the reverse.
_F_TABLE_MISSING_PYTHON: Final[str] = "missing_table_in_python"
_F_TABLE_MISSING_COBOL: Final[str] = "missing_table_in_cobol"
_F_COLUMNS: Final[str] = "columns"
_F_COLUMNS_SKIPPED: Final[str] = "columns_mismatch_rows_not_compared"
_F_ROW_COUNT: Final[str] = "row_count"
_F_MISSING_PYTHON: Final[str] = "missing_in_python"
_F_MISSING_COBOL: Final[str] = "missing_in_cobol"
_F_TYPE_MISMATCH: Final[str] = "type_mismatch"
_F_KEY_TYPE_MISMATCH: Final[str] = "key_type_mismatch"
_F_TRUNCATED: Final[str] = "truncated"


def _join(*fields: str) -> str:
    """Join report fields with the fixed separator.

    Args:
        fields: The fields, already rendered.

    Returns:
        One report line, without its newline.
    """
    return _FIELD_GAP.join(fields)


def _first_column_difference(
    cobol: Sequence[str], python: Sequence[str]
) -> str:
    """Describe the first position at which two column lists differ.

    Naming the first disagreement keeps a 169-column mismatch to one
    readable line instead of two lists of 169 names.

    Args:
        cobol: The oracle's column list.
        python: The migrated side's column list.

    Returns:
        A rendered description, or the empty string when the lists are
        equal.
    """
    for position in range(max(len(cobol), len(python))):
        left = cobol[position] if position < len(cobol) else None
        right = python[position] if position < len(python) else None
        if left == right:
            continue
        return _join(
            f"first_difference=col[{position + 1}]",
            f"{LABEL_COBOL}="
            + (_render_value(left) if left is not None else "<absent>"),
            f"{LABEL_PYTHON}="
            + (_render_value(right) if right is not None else "<absent>"),
        )
    return ""


def _render_value_difference(
    table: str, primary_key: str, key: str | int, value: ValueDifference
) -> str:
    """Render one differing column value as one report line.

    Args:
        table: The table.
        primary_key: The alignment column's name.
        key: The row's primary-key value.
        value: The difference.

    Returns:
        One report line, without its newline.
    """
    cobol = f"{LABEL_COBOL}={_render_value(value.cobol)}"
    python = f"{LABEL_PYTHON}={_render_value(value.python)}"
    if value.type_mismatch:
        # Both types named, because a type mismatch means the two dumps
        # were produced by inconsistent serialisation - a real defect, not
        # a rendering quirk.
        cobol = f"{cobol} ({type(value.cobol).__name__})"
        python = f"{python} ({type(value.python).__name__})"
        return _join(
            table,
            f"{primary_key}={_render_value(key)}",
            f"col[{value.ordinal}] {value.column}",
            _F_TYPE_MISMATCH,
            cobol,
            python,
        )
    return _join(
        table,
        f"{primary_key}={_render_value(key)}",
        f"col[{value.ordinal}] {value.column}",
        cobol,
        python,
    )


def render_table(
    diff: TableDiff, *, max_differences: int = DEFAULT_MAX_DIFFERENCES
) -> tuple[str, ...]:
    """Render one table's findings as report lines.

    The order is fixed: the structural findings first - a one-sided
    table, a column mismatch, a row-count difference - then
    `missing_in_python`, then `missing_in_cobol`, then the value
    differences. Keys ascend; columns follow schema ordinal order.

    Args:
        diff: The table's findings.
        max_differences: How many DETAIL lines to print before
            truncating. The structural headline is never truncated, and
            truncation never changes the exit code.

    Returns:
        The lines, without newlines. Empty when the table agrees.
    """
    if diff.is_empty:
        return ()

    table = diff.table
    lines: list[str] = []

    # 1. STRUCTURAL FINDINGS. Never truncated: at most three lines, and
    #    they are the headline a reader needs before any detail.
    if not diff.in_python:
        lines.append(
            _join(
                table,
                _F_TABLE_MISSING_PYTHON,
                f"{LABEL_COBOL}_rows={diff.cobol_row_count}",
            )
        )
    if not diff.in_cobol:
        lines.append(
            _join(
                table,
                _F_TABLE_MISSING_COBOL,
                f"{LABEL_PYTHON}_rows={diff.python_row_count}",
            )
        )
    if diff.columns_differ:
        detail = _first_column_difference(
            diff.cobol_columns, diff.python_columns
        )
        lines.append(
            _join(
                table,
                _F_COLUMNS,
                f"{LABEL_COBOL}={len(diff.cobol_columns)}",
                f"{LABEL_PYTHON}={len(diff.python_columns)}",
                detail,
            ).rstrip()
        )
        lines.append(
            _join(
                table,
                _F_COLUMNS_SKIPPED,
                "rows are positional, so there is no meaningful alignment",
            )
        )
    if diff.row_count_differs:
        lines.append(
            _join(
                table,
                _F_ROW_COUNT,
                f"{LABEL_COBOL}={diff.cobol_row_count}",
                f"{LABEL_PYTHON}={diff.python_row_count}",
            )
        )
    if diff.key_types_differ:
        # The alignment column itself was serialised differently, so no
        # key could be shared and every row below is reported one-sided.
        # Naming both types here is what makes that legible; the rows are
        # still NOT paired, because pairing them would be coercion.
        lines.append(
            _join(
                table,
                _F_KEY_TYPE_MISMATCH,
                diff.primary_key,
                f"{LABEL_COBOL}={','.join(diff.cobol_key_types)}",
                f"{LABEL_PYTHON}={','.join(diff.python_key_types)}",
            )
        )

    # 2. DETAIL FINDINGS, capped. The cap exists so that a catastrophic
    #    mismatch cannot produce an unusable megabyte; the notice always
    #    carries the TRUE total, and the exit code is unaffected.
    budget = max(max_differences, 0)
    shown = 0
    key_label = f"{diff.primary_key}="

    for key in diff.missing_in_python:
        if shown >= budget:
            break
        lines.append(
            _join(
                table,
                _F_MISSING_PYTHON,
                f"{key_label}{_render_value(key)}",
            )
        )
        shown += 1

    for key in diff.missing_in_cobol:
        if shown >= budget:
            break
        lines.append(
            _join(
                table,
                _F_MISSING_COBOL,
                f"{key_label}{_render_value(key)}",
            )
        )
        shown += 1

    for row in diff.value_differences:
        if shown >= budget:
            break
        for value in row.values:
            if shown >= budget:
                break
            lines.append(
                _render_value_difference(
                    table, diff.primary_key, row.key, value
                )
            )
            shown += 1

    if shown < diff.detail_count:
        lines.append(
            _join(
                table,
                _F_TRUNCATED,
                f"shown={shown}",
                f"total={diff.detail_count}",
                "raise --max-differences to see them all",
            )
        )

    return tuple(lines)


def render(
    diff: TreeDiff, *, max_differences: int = DEFAULT_MAX_DIFFERENCES
) -> str:
    """Render a whole comparison as the deterministic report.

    Args:
        diff: The comparison.
        max_differences: How many detail lines per table to print before
            truncating.

    Returns:
        THE EMPTY STRING when the two trees are identical - Agent Action
        Plan section 0.8.5: "the diff must be empty", so the pass case is
        zero bytes, not a banner. Otherwise the report, one finding per
        line, each line terminated with a single LF.
    """
    lines: list[str] = []
    for table in diff.tables:
        lines.extend(
            render_table(table, max_differences=max_differences)
        )
    if not lines:
        return ""
    return "".join(f"{line}\n" for line in lines)


# ---------------------------------------------------------------------------
#  WRITING THE REPORT TO A FILE
#
#  The composed layout writes $ACAS_OUT/<scenario>/diff.txt, which is the
#  path the file specification for this module names and the path
#  docs/migration/scenario-diff-evidence.md cites.
#
#  ON A PASS A ZERO-BYTE FILE IS WRITTEN. That is a deliberate choice
#  between the two the specification offers, and it is documented here and
#  in the CLI epilogue so that tests/scenarios/* can assert it: the
#  evidence document needs to distinguish "compared, and identical" from
#  "never compared", and an existing empty file says the first while an
#  absent file says nothing at all.
# ---------------------------------------------------------------------------

# The temporary name the report is written under before os.replace moves
# it into place, in the SAME directory as its target so the replace is
# atomic. Matches the convention of both producers
# [harness/dump_tables.py:L1672-L1673].
_TEMP_SUFFIX: Final[str] = ".txt.tmp"


def _assert_writable(target: Path, env: Mapping[str, str]) -> None:
    """Assert the report may be written where it was asked to go.

    Args:
        target: The report path.
        env: The environment, for `$ACAS_REPO`.

    Raises:
        ReportPathError: It would land inside the read-only checkout.
    """
    repository = env.get(_ENV_REPO)
    if not repository:
        return
    root = Path(repository).resolve()
    resolved = target.resolve()
    if resolved == root or root in resolved.parents:
        raise ReportPathError(
            f"the report {target} would be written inside the checkout "
            f"{root} (${_ENV_REPO}). Nothing may be written there: it "
            f"holds the frozen COBOL, the bridges and mysql/ACASDB.sql, it "
            f"is mounted read-only, and Agent Action Plan section 0.8.1 "
            f"calls any diff touching those paths \"a defect in the "
            f"migration, regardless of how harmless it appears\". Write it "
            f"under ${_ENV_OUT} instead, for example "
            f"${_ENV_OUT}/<scenario>/{DIFF_FILENAME}."
        )


def write_report(report: str, path: Path | str) -> Path:
    """Write the report to a file, atomically.

    Args:
        report: The rendered report; the empty string on a pass.
        path: Where to write it. Parent directories are created.

    Returns:
        The path written.

    Raises:
        ReportPathError: The file could not be written.
    """
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ReportPathError(
            f"could not create the directory for the report {target}: "
            f"{exc}"
        ) from exc

    temporary = target.parent / f"{TEMP_PREFIX}{target.stem}{_TEMP_SUFFIX}"
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            # `report` already ends with a newline when it is non-empty,
            # and is empty on a pass - so a passing run leaves a zero-byte
            # file rather than a file containing a bare newline.
            handle.write(report)
        os.replace(temporary, target)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            # Best effort only. The real failure is raised below and must
            # not be masked by a failure to tidy up.
            pass
        raise ReportPathError(
            f"could not write the report to {target}: {exc}"
        ) from exc
    return target


# ---------------------------------------------------------------------------
#  THE COMMAND LINE
#
#  Every diagnostic goes to STDERR. stdout carries the verdict and nothing
#  else, so that a passing run leaves stdout at zero bytes.
#
#  `main` RETURNS an exit code and never calls sys.exit, so tests/
#  conftest.py can drive it in process and inspect the code - including
#  argparse's own usage failures, which are caught and mapped to exit 2
#  rather than allowed to escape as SystemExit.
# ---------------------------------------------------------------------------

_EPILOGUE: Final[str] = f"""\
the two trees
  positionally, the form the canonical recipe uses
  [harness/docker-compose.yml:L274]:
      {_PROG} /out/{LABEL_COBOL}.norm /out/{LABEL_PYTHON}.norm
  by name:
      {_PROG} --{LABEL_COBOL} DIR --{LABEL_PYTHON} DIR
  composed from the scenario, deriving both trees and the report path:
      {_PROG} --scenario NAME [--out-dir DIR]
      reads  DIR/NAME/{LABEL_COBOL}{NORMALIZED_SUFFIX}/<TABLE>.json
             DIR/NAME/{LABEL_PYTHON}{NORMALIZED_SUFFIX}/<TABLE>.json
      writes DIR/NAME/{DIFF_FILENAME}   (DIR defaults to ${_ENV_OUT})

which tables
  --scenario-file FILE   the scenario's affected-table list, in its order.
                         This is the protocol: bounding the comparison by
                         the scenario is what keeps the menu-exit rewrite
                         at [general/general.cbl:L656-L691] from failing an
                         otherwise correct run. There is deliberately NO
                         ignore-list in this tool (rule R-4).
  --tables A,B           an explicit list, in the order given.
  neither                the union of what the two trees hold, ASCII
                         order, with a warning. A table present in only
                         one tree is a DIFFERENCE, never a skip.

exit codes
  0  identical           stdout is EMPTY - that is the pass condition
  1  difference found    the report is on stdout
  2  cannot compare      a diagnosis is on stderr; NEVER reported as 0

with --out, a passing run writes a ZERO-BYTE file, so the evidence can
distinguish "compared, and identical" from "never compared".

the comparison is EXACT: no tolerance, no epsilon, no case- or
whitespace-insensitive compare, no numeric coercion, and no ignore-list.
harness/normalize.py has already canonicalised character padding, decimal
scale and date text, so anything left is a real behavioural difference.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    `allow_abbrev=False`, so `--out` and `--out-dir` can never be confused
    with one another and no abbreviation of any option is silently
    accepted.

    Returns:
        The parser.
    """
    parser = argparse.ArgumentParser(
        prog=_PROG,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Compare two normalised ACAS table-state dumps. An EMPTY diff "
            "is the pass condition: exit 0 with empty stdout means the "
            "Python cycle reproduced the compiled COBOL exactly, exit 1 "
            "means a real behavioural difference, exit 2 means the "
            "comparison could not be performed. Stage 8 of the eight-stage "
            "parity protocol."
        ),
        epilog=_EPILOGUE,
    )

    parser.add_argument(
        "trees",
        nargs="*",
        metavar="DIR",
        help=(
            f"the two normalised trees, {LABEL_COBOL} first then "
            f"{LABEL_PYTHON} - the positional form the canonical recipe "
            f"uses [harness/docker-compose.yml:L274]. Equivalent to "
            f"--{LABEL_COBOL}/--{LABEL_PYTHON}."
        ),
    )
    parser.add_argument(
        "--left",
        f"--{LABEL_COBOL}",
        dest="left",
        metavar="DIR",
        help=(
            "the COBOL oracle's normalised tree - the specification side, "
            "reported as `cobol`."
        ),
    )
    parser.add_argument(
        "--right",
        f"--{LABEL_PYTHON}",
        dest="right",
        metavar="DIR",
        help=(
            "the migrated Python cycle's normalised tree, reported as "
            "`python`."
        ),
    )
    parser.add_argument(
        "--scenario",
        metavar="NAME",
        help=(
            "derive both trees and the default report path from the "
            "canonical layout <out-dir>/<scenario>/<side>"
            f"{NORMALIZED_SUFFIX}/."
        ),
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        help=(
            f"the root the composed layout is built under; defaults to "
            f"${_ENV_OUT}."
        ),
    )
    parser.add_argument(
        "--scenario-file",
        metavar="FILE",
        help=(
            "read the affected-table list from a scenario definition, and "
            "report the tables in the order it declares them. Mutually "
            "exclusive with --tables."
        ),
    )
    parser.add_argument(
        "--tables",
        metavar="A,B",
        help=(
            "compare exactly these tables, in this order. Mutually "
            "exclusive with --scenario-file."
        ),
    )
    parser.add_argument(
        "--out",
        metavar="FILE",
        help=(
            f"also write the report to a file. Defaults to "
            f"<out-dir>/<scenario>/{DIFF_FILENAME} when --scenario is "
            f"used. A passing run writes a zero-byte file."
        ),
    )
    parser.add_argument(
        "--max-differences",
        metavar="N",
        type=int,
        default=DEFAULT_MAX_DIFFERENCES,
        help=(
            f"how many detail lines per table to print before truncating "
            f"(default {DEFAULT_MAX_DIFFERENCES}). The structural "
            f"headline is never truncated, the notice always carries the "
            f"true total, and truncation never changes the exit code."
        ),
    )
    parser.add_argument(
        "--allow-raw",
        action="store_true",
        help=(
            "DEBUGGING ONLY: permit comparing trees whose names do not end "
            f"with {' or '.join(NORMALIZED_SUFFIXES)}. Raw dumps still "
            "carry the representation artefacts harness/normalize.py "
            "removes, so a verdict taken this way is not evidence."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help=(
            "silence progress on stderr. Warnings, diagnoses, the report "
            "and the exit code are unaffected."
        ),
    )
    return parser


def _resolve_trees(
    arguments: argparse.Namespace, env: Mapping[str, str]
) -> tuple[Path, Path, str | None, Path | None]:
    """Work out which two directories to compare, and where to report.

    Args:
        arguments: The parsed command line.
        env: The environment, for `$ACAS_OUT`.

    Returns:
        The `cobol` tree, the `python` tree, the scenario name when the
        composed layout was used, and the report path when one was asked
        for or implied.

    Raises:
        ValueError: The forms were mixed, or one of them is incomplete.
    """
    positional = list(arguments.trees)
    named = arguments.left is not None or arguments.right is not None
    composed = arguments.scenario is not None

    chosen = [
        label
        for label, given in (
            ("two positional directories", bool(positional)),
            (f"--{LABEL_COBOL}/--{LABEL_PYTHON}", named),
            ("--scenario", composed),
        )
        if given
    ]
    if len(chosen) > 1:
        raise ValueError(
            f"{' and '.join(chosen)} were given; they are alternative ways "
            f"of naming the same two directories, so use exactly one."
        )
    if not chosen:
        raise ValueError(
            f"no trees to compare. Give them positionally - "
            f"`{_PROG} /out/{LABEL_COBOL}.norm /out/{LABEL_PYTHON}.norm`, "
            f"the form [harness/docker-compose.yml:L274] uses - or by name "
            f"with --{LABEL_COBOL} and --{LABEL_PYTHON}, or let "
            f"--scenario NAME derive both from the canonical layout."
        )

    if arguments.out_dir is not None and not composed:
        raise ValueError(
            "--out-dir builds the composed layout "
            "<out-dir>/<scenario>/<side>"
            f"{NORMALIZED_SUFFIX}/, so it needs --scenario. To name the "
            "report file directly, use --out."
        )

    report = Path(arguments.out) if arguments.out is not None else None

    if positional:
        if len(positional) != 2:
            raise ValueError(
                f"exactly two directories are needed, the {LABEL_COBOL} "
                f"tree then the {LABEL_PYTHON} tree; got "
                f"{len(positional)}. The canonical form is "
                f"`{_PROG} /out/{LABEL_COBOL}.norm "
                f"/out/{LABEL_PYTHON}.norm` "
                f"[harness/docker-compose.yml:L274]."
            )
        return Path(positional[0]), Path(positional[1]), None, report

    if named:
        if arguments.left is None or arguments.right is None:
            missing = (
                f"--{LABEL_COBOL}" if arguments.left is None
                else f"--{LABEL_PYTHON}"
            )
            raise ValueError(
                f"{missing} is missing. Both trees are needed: the "
                f"{LABEL_COBOL} side is the oracle and the {LABEL_PYTHON} "
                f"side is the migration, and the report says which is "
                f"which."
            )
        return Path(arguments.left), Path(arguments.right), None, report

    scenario = arguments.scenario
    if not scenario or scenario in {".", ".."} or (set(scenario) & set("/\\")):
        raise ValueError(
            f"--scenario must be a plain directory name, not a path; got "
            f"{scenario!r}. It names a scenario such as clean_batch_gl."
        )
    root = arguments.out_dir or env.get(_ENV_OUT)
    if not root:
        raise ValueError(
            f"neither --out-dir nor ${_ENV_OUT} is set, so the output root "
            f"is unknown and the composed layout cannot be built. The "
            f"Compose service sets {_ENV_OUT}: /out. Alternatively name "
            f"the two trees directly."
        )
    base = Path(root) / scenario
    if report is None:
        report = base / DIFF_FILENAME
    return (
        base / f"{LABEL_COBOL}{NORMALIZED_SUFFIX}",
        base / f"{LABEL_PYTHON}{NORMALIZED_SUFFIX}",
        scenario,
        report,
    )


def _describe_missing_tree(directory: Path) -> str:
    """Suggest the sibling tree an operator probably meant.

    The two normalised suffixes both occur in this repository - the
    composed layout appends `.normalized`, the committed recipe passes
    `.norm` - so a missing directory is most often the other spelling.
    Naming it turns an exit 2 into an obvious fix, without this module
    ever guessing which tree to compare (rule R-6: the verdict must never
    be ambiguous about what was compared).

    Args:
        directory: The directory that was not there.

    Returns:
        A sentence naming the sibling that does exist, or the empty
        string.
    """
    name = directory.name
    for suffix in NORMALIZED_SUFFIXES:
        if not name.endswith(suffix):
            continue
        stem = name[: -len(suffix)]
        for alternative in NORMALIZED_SUFFIXES:
            if alternative == suffix:
                continue
            sibling = directory.with_name(f"{stem}{alternative}")
            if sibling.is_dir():
                return (
                    f" {sibling} does exist: harness/normalize.py's "
                    f"composed layout writes `{NORMALIZED_SUFFIXES[0]}` "
                    f"while the recipe at "
                    f"[harness/docker-compose.yml:L269] passes "
                    f"`{NORMALIZED_SUFFIXES[1]}` explicitly. Name the two "
                    f"trees directly rather than using --scenario, so it "
                    f"is unambiguous which pair was compared."
                )
    return ""


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the verdict as an exit code.

    Never calls `sys.exit`, so tests/conftest.py can drive it in process
    and inspect the code - argparse's own usage failures included, which
    are caught and mapped to exit 2 rather than allowed to escape.

    Args:
        argv: The arguments; `sys.argv[1:]` when omitted.

    Returns:
        `EX_IDENTICAL` (0) when the two trees are identical, and stdout is
        left EMPTY; `EX_DIFFERENT` (1) when a real difference was found,
        with the report on stdout; `EX_ERROR` (2) when the comparison
        could not be performed, with a diagnosis on stderr.
    """
    global _QUIET

    parser = build_parser()
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 for --help and 2 for a usage error. Both are
        # returned rather than propagated, and a usage error is exit 2 -
        # "the comparison could not be performed" - never exit 0.
        code = exc.code
        if code is None or code == 0:
            return EX_IDENTICAL
        return EX_ERROR

    _QUIET = bool(arguments.quiet)
    env: Mapping[str, str] = os.environ

    if arguments.max_differences < 1:
        print(
            f"{_PROG}: --max-differences must be at least 1; got "
            f"{arguments.max_differences}. It caps the DETAIL lines per "
            f"table so a catastrophic mismatch cannot produce an unusable "
            f"report; the structural headline is never capped and the "
            f"exit code is never affected.",
            file=sys.stderr,
        )
        return EX_ERROR

    try:
        left, right, scenario, report_path = _resolve_trees(arguments, env)
    except ValueError as exc:
        print(f"{_PROG}: {exc}", file=sys.stderr)
        return EX_ERROR

    try:
        tables = resolve_tables(
            tables=arguments.tables,
            scenario_file=arguments.scenario_file,
        )
    except (DiffStatesError, ValueError) as exc:
        print(f"{_PROG}: {exc}", file=sys.stderr)
        return EX_ERROR

    if report_path is not None:
        try:
            _assert_writable(report_path, env)
        except ReportPathError as exc:
            print(f"{_PROG}: {exc}", file=sys.stderr)
            return EX_ERROR

    _progress(
        f"{_PROG}: comparing "
        + (
            f"{len(tables)} table(s)"
            if tables is not None
            else "every table the two trees hold"
        )
        + (f" for scenario {scenario}" if scenario else "")
    )

    try:
        diff = diff_trees(
            left, right, tables, allow_raw=bool(arguments.allow_raw)
        )
    except MissingTreeError as exc:
        # The most dangerous input this module can be given, so the
        # message says outright that it is not a pass.
        print(f"{_PROG}: {exc}{_describe_missing_tree(left)}", file=sys.stderr)
        return EX_ERROR
    except (DiffStatesError, ValueError) as exc:
        print(f"{_PROG}: {exc}", file=sys.stderr)
        return EX_ERROR

    report = render(diff, max_differences=arguments.max_differences)

    if report_path is not None:
        try:
            write_report(report, report_path)
        except ReportPathError as exc:
            print(f"{_PROG}: {exc}", file=sys.stderr)
            return EX_ERROR

    if diff.is_empty:
        # THE PASS CONDITION. Not one byte on stdout: Agent Action Plan
        # section 0.8.5 says "the diff must be empty", and a banner here
        # would make an empty diff indistinguishable from a small one to
        # anything reading stdout.
        _progress(
            f"{_PROG}: identical - {len(diff.tables)} table(s) compared, "
            f"no difference"
        )
        return EX_IDENTICAL

    sys.stdout.write(report)
    _progress(
        f"{_PROG}: {diff.total_differences} difference(s) across "
        f"{len(diff.differing)} of {len(diff.tables)} table(s). A "
        f"non-empty diff is a real behavioural difference, never an "
        f"artefact of the comparison (Agent Action Plan section 0.6.6): "
        f"interrogate the compiled oracle, and record the resolution in "
        f"docs/migration/ambiguity-resolutions.md."
    )
    return EX_DIFFERENT


if __name__ == "__main__":
    raise SystemExit(main())
