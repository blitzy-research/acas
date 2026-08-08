#!/usr/bin/env python3
# Executable in its own right: the canonical recipe in harness/docker-compose.yml
# names the three state tools by path, and without this line the kernel refuses
# the exec and bash falls back to interpreting the file as a shell script.
"""Compare two normalised dumps. AN EMPTY DIFF IS THE PASS CONDITION.

Stage 10 of the parity protocol, and the only arbiter in it. The stage list itself
lives in [harness/normalize.py PARITY_STAGES], which
[harness/normalize.py parity_stage_shell] reads and
`harness/normalize.py --print-stages' prints. It is the stage older prose in this
repository calls "stage 8", from the Agent Action Plan's eight logical stages
(section 0.3.2); the protocol makes both normalisations and the publication check
explicit, which is what turns eight into ten. Exit 0 with empty
output means the Python cycle reproduced the compiled COBOL exactly; exit 1 means
a real behavioural difference; exit 2 means the comparison could not be performed
at all, which is never weaker evidence than a difference - it is none.

Both trees must be normalised, and each must carry the `_manifest.json` its
producing stage wrote, so a truncated capture cannot masquerade as a small diff.
The table list comes from the scenario definition, because a comparison is
bounded by the scenario that produced it; `--all-tables` exists for debugging.

Rows are matched on the primary key and compared field by field. Numeric values
are compared as `decimal.Decimal` or `int`; a float anywhere aborts the
comparison rather than being coerced (R-2). Run `--help` for the options.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

# Re-declared here rather than imported.


@dataclass(frozen=True, slots=True)
class TableSpec:
    """One in-scope table's frozen-schema facts.

    Attributes:
        primary_key: The single column rows are aligned on.
        column_count: The declared number of columns. Recorded for the error messages
            and for a one-line inventory assertion.
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

# The eleven tables the posting cycle never touches, listed BY NAME so a wrong request
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

# The default table order.
IN_SCOPE_TABLES: Final[tuple[str, ...]] = tuple(sorted(IN_SCOPE))

# 513 and 33, both as mysql/ACASDB.sql declares them. Exposed so a test can assert the
# whole inventory in two lines.
EXPECTED_TOTAL_COLUMNS: Final[int] = sum(
    spec.column_count for spec in IN_SCOPE.values()
)
EXPECTED_SCHEMA_TABLES: Final[int] = len(IN_SCOPE) + len(OUT_OF_SCOPE)

SIDES: Final[tuple[str, ...]] = ("cobol", "python")

# The report's side labels. `cobol` and `python` rather than left and right, so the
# report says which side is the ORACLE.
LABEL_COBOL: Final[str] = SIDES[0]
LABEL_PYTHON: Final[str] = SIDES[1]

# A dump object's key order, fixed at harness/dump_tables.py and preserved unchanged by
# harness/normalize.py.
DUMP_KEYS: Final[tuple[str, ...]] = (
    "table",
    "primary_key",
    "columns",
    "row_count",
    "rows",
)

DUMP_SUFFIX: Final[str] = ".json"

# harness/dump_tables.py and harness/normalize.py both write through a temporary file
# named `.<stem>.json.tmp` in the target directory and then os.replace it into position,
# so a partial file can never be compared.
TEMP_PREFIX: Final[str] = "."

NORMALIZED_SUFFIXES: Final[tuple[str, ...]] = (".normalized", ".norm")
NORMALIZED_SUFFIX: Final[str] = NORMALIZED_SUFFIXES[0]

# Mirrored from [harness/dump_tables.py] and [harness/normalize.py] rather than
# imported, following the convention every constant this module already shares with its
# siblings follows - `DUMP_KEYS`, `IN_SCOPE_TABLES`, `SIDES`, `TEMP_PREFIX`.
MANIFEST_FILENAME: Final[str] = "_manifest.json"
# Version 2 added `attestation`, in step with harness/dump_tables.py and
# harness/normalize.py. A version-1 tree is REFUSED rather than read: the whole
# point of that key is that its absence cannot be mistaken for a claim of success,
# so tolerating a manifest written before it existed would defeat the check.
MANIFEST_VERSION: Final[int] = 3

# THE EXACT MANIFEST SHAPE THIS TOOL REQUIRES
#
# Checking only that a manifest parses, that its version matches and that its `tables`
# list agrees with the files beside it -- and reading every other key with `.get()` --
# would let a manifest MISSING a key this tool depends on, or carrying an extra one
# nobody wrote deliberately, reach the comparison and get a verdict. The keys read here
# are the ones that establish WHICH CAPTURE this is: the scenario, the side, the
# provenance and the attestation. A manifest that does not carry them is not a manifest
# of a capture this tool can render a verdict on, and reading it defensively is the
# wrong shape of defence: the right
# one is to require the shape and refuse anything else.
MANIFEST_REQUIRED_KEYS: Final[tuple[str, ...]] = (
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

# The provenance keys a verdict depends on, and what each one being unequal would mean.
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

# The provenance fields the TWO SIDES must agree on before a single row is compared.
#
#   run_id                one attempt. Unequal means stages of two different attempts
#                         were assembled into one verdict.
#   scenario_file_sha256  one definition. Unequal means the affected-table list that
#                         BOUNDS the comparison, or the fan-out switch that decides
#                         which tables a run touches, was edited between the two legs.
#   frozen_schema_sha256  one schema. Unequal means mysql/ACASDB.sql changed under the
#                         protocol, which Agent Action Plan section 0.8.1 forbids.
#
# `producer_sha256`, `python_version` and `command` are deliberately NOT required to
# match: the two sides are captured by the same tool but their commands differ by
# `--side`, and requiring the interpreter to match would refuse a legitimate comparison
# of captures taken minutes apart on a host that was patched in between. They are
# RECORDED so a reader can see them, which is what provenance is for.
PROVENANCE_MUST_MATCH: Final[tuple[str, ...]] = (
    "run_id",
    "scenario_file_sha256",
    "frozen_schema_sha256",
)

# THE DETERMINISM CONTRACT IS THE MIRROR IMAGE OF THE PARITY CONTRACT.
#
# tests/determinism/test_two_runs_byte_identical.py proves AAP section 0.8.5's fourth
# criterion -- "two runs of the same scenario under the same pinned clock produce
# byte-identical dumps" -- and that comparison is run A against run B of ONE side, not
# cobol against python. The parity requirements are therefore exactly wrong for it: the
# side must be the SAME rather than different, and the run ids must DIFFER rather than
# match, because two captures carrying ONE run id are the same capture read twice and
# would be identical by construction. Everything the two contracts share -- one
# scenario definition, one frozen schema, one seed -- is still required, so this mode
# is STRICTLY STRONGER than comparing the trees with no provenance check at all. It is
# never reachable from the command line: only an in-process caller can select it.
PROVENANCE_MUST_MATCH_SAME_SIDE: Final[tuple[str, ...]] = (
    "scenario_file_sha256",
    "frozen_schema_sha256",
)
PROVENANCE_MUST_DIFFER_SAME_SIDE: Final[tuple[str, ...]] = ("run_id",)

# The labels a same-side comparison reports with. `cobol'/`python' would be actively
# misleading in a determinism message, where BOTH trees are one side.
LABEL_RUN_A: Final[str] = "run A"
LABEL_RUN_B: Final[str] = "run B"

# The attestation keys this tool requires to be present on both sides.
ATTESTATION_REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "attested",
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

# The verdict manifest's own name and keys.
VERDICT_FILENAME: Final[str] = "verdict.json"
VERDICT_VERSION: Final[int] = 1
VERDICT_KEYS: Final[tuple[str, ...]] = (
    "verdict_version",
    "producer",
    "scenario",
    "outcome",
    "exit_code",
    "tables_compared",
    "tables_differing",
    "total_differences",
    "run_id",
    "seed_marker_sha256",
    "scenario_file_sha256",
    "frozen_schema_sha256",
    "cobol_manifest_sha256",
    "python_manifest_sha256",
    "report",
    "report_sha256",
)

OUTCOME_IDENTICAL: Final[str] = "identical"
OUTCOME_DIFFERENT: Final[str] = "different"

# A lower-case hexadecimal SHA-256 and nothing else, for the fields where a digest is
# REQUIRED rather than merely recorded.
_SHA256_PATTERN: Final[str] = r"[0-9a-f]{64}"
MANIFEST_STAGE_NORMALIZED: Final[str] = "normalized"

# The one disposition this module treats specially: a run that COMPLETED and reported
# a behavioural difference. Its capture is comparable -- the state it left is the
# finding -- and `assert_attested` announces it so the verdict cannot be read as a
# clean run's. Mirrored from [harness/dump_tables.py], following the same convention as
# the four constants above, rather than imported.
DISPOSITION_BEHAVIOURAL: Final[str] = "behavioural-difference"

# The reserved file-name namespace inside a published tree.
RESERVED_PREFIX: Final[str] = "_"

_DIGEST_BLOCK: Final[int] = 1 << 16

# THE VERDICT (rule R-6). Three values, and no others.
EX_IDENTICAL: Final[int] = 0
EX_DIFFERENT: Final[int] = 1
EX_ERROR: Final[int] = 2

# How many DETAIL lines per table the report prints before truncating.
DEFAULT_MAX_DIFFERENCES: Final[int] = 200

DIFF_FILENAME: Final[str] = "diff.txt"

_ENV_OUT: Final[str] = "ACAS_OUT"
_ENV_REPO: Final[str] = "ACAS_REPO"

_SCENARIO_TABLE_KEYS: Final[tuple[str, ...]] = (
    "affected_tables",
    "affected-tables",
)

_SUGGESTION_LIMIT: Final[int] = 4

# The report's field separator. Two spaces, so a line stays greppable and a value
# containing a single space is still unambiguous.
_FIELD_GAP: Final[str] = "  "

# The prog name every diagnostic is prefixed with. A fixed string, not sys.argv[0].
_PROG: Final[str] = "harness/diff_states.py"


# STDERR ONLY, and never stdout. stdout carries the verdict and nothing else.

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


def _warn(message: str) -> None:
    """Write one warning line to stderr. Never silenced by `--quiet`.

    Args:
        message: The line to write.
    """
    print(f"{_PROG}: warning: {message}", file=sys.stderr)


# One root, so a caller can catch everything this module raises with a single clause,
# and one subclass per distinct cause so a caller that cares can tell them apart.


class DiffStatesError(Exception):
    """Base class for every failure this module reports. Always exit 2."""


class MissingTreeError(DiffStatesError, OSError):
    """A tree to compare is absent, or is not a directory.

    The most dangerous input this module can be given, because the tempting response -
    "nothing to compare, so nothing differs" - is a FALSE PASS. It is exit 2.
    """


class RawTreeError(DiffStatesError, ValueError):
    """A directory is not a normalised tree and --allow-raw was not given.

    Comparing raw dumps would report harness/normalize.py's three representation
    artefacts as behavioural differences - the character padding of Agent Action Plan
    section 0.6.2 chief among them.
    """


class SameTreeError(DiffStatesError, ValueError):
    """Both sides name the same directory.

    A tree always equals itself, so the comparison would return empty whatever the
    migration did. That is a FALSE PASS, so it is refused.
    """


class EmptyComparisonError(DiffStatesError, ValueError):
    """There is no table to compare.

    Comparing nothing would return empty and read as a pass. Refused for the same reason
    as `SameTreeError`.
    """


class MissingTableFileError(DiffStatesError, OSError):
    """A requested table's dump is absent from BOTH trees.

    Absent from ONE tree is a reported DIFFERENCE, never an error - that asymmetry is
    exactly what a naive intersection would hide. Absent from both means the dumps were
    never taken.
    """


class DumpReadError(DiffStatesError, OSError):
    """A dump file could not be read, or is not a JSON object."""


class DumpShapeError(DiffStatesError, ValueError):
    """A dump object's shape is wrong."""


class NumericPolicyError(DiffStatesError, TypeError):
    """A value is a binary floating-point number (rule R-2).

    The frozen schema declares zero FLOAT, DOUBLE and REAL columns and both producers
    refuse to emit a float, so this is unreachable unless one of them was reconfigured.
    """


class UnexpectedValueTypeError(DiffStatesError, TypeError):
    """A value is of a type no in-scope column can hold."""


class UnexpectedNullError(DiffStatesError, ValueError):
    """A value is JSON null.

    Not one of the 513 in-scope columns is nullable. Agent Action Plan section 0.6.2
    explains why - each bridge load paragraph initialises the host-variable group, "so
    unset fields become zero or space rather than SQL NULL".
    """


class DuplicateKeyError(DiffStatesError, ValueError):
    """A primary-key value appears twice in one dump.

    A PRIMARY KEY column cannot produce a duplicate, so the input is malformed - and
    with a duplicate there is no unambiguous row to align against.
    """


class UnknownTableError(DiffStatesError, ValueError):
    """A name is not a table of the frozen schema at all."""


class TableNotInScopeError(DiffStatesError, ValueError):
    """A name is one of the eleven tables the posting cycle never touches."""


class ScenarioFileError(DiffStatesError, ValueError):
    """A scenario definition is missing, unreadable or unusable."""


class ManifestError(DiffStatesError, ValueError):
    """A tree does not declare itself complete, or the two disagree."""


class ReportPathError(DiffStatesError, ValueError):
    """The report would be written somewhere it must not be.

    Nothing may be written under `$ACAS_REPO`: it holds the frozen artifacts and is
    mounted read-only (rule R-3, Agent Action Plan section 0.8.1).
    """


def table_spec(table: str) -> TableSpec:
    """Look up an in-scope table's frozen-schema facts.

    Args:
        table: A table name, spelled exactly as `mysql/ACASDB.sql` spells it, hyphens
            included and upper case.

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

    # A near-miss list, so a typo or a case error is obvious at once. The comparison is
    # upper-cased for the SUGGESTION only.
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
        `<TABLE>.json`, matching harness/dump_tables.py and harness/normalize.py
            exactly.
    """
    return f"{table}{DUMP_SUFFIX}"


def is_normalized_tree(directory: Path | str) -> bool:
    """Report whether a directory NAME marks it as a normalised tree.

    The test is on the name, not on the contents.

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
        RawTreeError: Its name does not mark it as normalised and `allow_raw` is false.
    """
    if not directory.exists():
        raise MissingTreeError(
            f"the {label} tree {directory} does not exist. An absent tree "
            f"is NOT an empty diff: exit 2 says the comparison could not "
            f"be performed, and it is never reported as a pass. Run "
            f"stages 3 and 4 - harness/dump_tables.py then "
            f"harness/normalize.py - for the {label} side first; see "
            f"harness/docker-compose.yml."
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
        f"{' nor '.join(NORMALIZED_SUFFIXES)}. Stage 10 compares the "
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


# Every assertion here is about ONE file in isolation, and every one is exit 2: a
# malformed dump means the comparison could not be performed.


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
        The value unchanged - a `str` or an `int`. Nothing is converted, rounded,
            padded, trimmed or coerced.

    Raises:
        UnexpectedNullError: It is `None`.
        NumericPolicyError: It is a `float` (rule R-2).
        UnexpectedValueTypeError: It is a `bool`, a container, or any other type no in-
            scope column can hold.
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

    # bool BEFORE int, because bool is a subclass of int.
    if isinstance(value, bool):
        raise UnexpectedValueTypeError(
            f"{site} is the JSON boolean {json.dumps(value)}. A dump holds "
            f"JSON integers and JSON strings only, as "
            f"harness/dump_tables.py writes them; a boolean means the "
            f"file was not written by harness/normalize.py."
        )

    # THE RULE R-2 GUARD.
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
        where: The file path or the side name it came from, quoted in every message so a
            failure is traceable to its source.

    Raises:
        DumpShapeError: The keys, the columns, the primary key, the row count or a row's
            width is wrong.
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
            f"version, a scenario name or a side. The layout is fixed by "
            f"harness/dump_tables.py."
        )

    table = dump["table"]
    if not isinstance(table, str):
        raise DumpShapeError(
            f"{where}: `table` must be the table name as a string; got "
            f"{type(table).__name__} ({table!r})."
        )
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
        DumpReadError: It could not be read, is not valid UTF-8 JSON, or does not parse
            to a JSON object.
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

    Every failure is exit 2: a dump that cannot be trusted cannot produce a verdict.

    Args:
        path: The `<TABLE>.json` file to read.

    Returns:
        The parsed, asserted dump object. Nothing in it is altered.

    Raises:
        MissingTableFileError: The file does not exist.
        DumpReadError: It is unreadable or is not a JSON object.
        DumpShapeError: Its shape is wrong, including its name not matching the table it
            declares.
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

    # The file name and the declared table must agree, or a report would name a table
    # whose data came from somewhere else.
    stem = target.name.removesuffix(DUMP_SUFFIX)
    if stem != dump["table"]:
        raise DumpShapeError(
            f"{target}: the file is named for table {stem!r} but declares "
            f"{dump['table']!r}. Both producers name a dump "
            f"`<TABLE>{DUMP_SUFFIX}` for the table it holds, and a report "
            f"that named the "
            f"wrong table would be worthless as evidence."
        )
    return dump


# Values are rendered as JSON, which quotes strings and leaves integers bare. That is
# exactly the distinction the report needs.


def _render_value(value: str | int) -> str:
    """Render one value for the report.

    Args:
        value: A dumped value - a `str` or an `int`.

    Returns:
        `1234` for an integer, `"1234.56"` for a string. Quoting is what makes padding
            and emptiness visible.
    """
    return json.dumps(value, ensure_ascii=True)


def _key_sort_key(key: str | int) -> tuple[int, int, str]:
    """Build a total, deterministic sort key for a primary-key value.

    Numeric keys sort NUMERICALLY, so `2` comes before `10`; character keys sort by
    ASCII, which is what Python's own string ordering gives for the ASCII-only content a
    dump can hold.

    Args:
        key: The primary-key value.

    Returns:
        A tuple ordering integers first and numerically, then strings by code point.
    """
    if isinstance(key, int):
        return (0, key, "")
    return (1, 0, key)


# Frozen dataclasses, so a diff cannot be edited after the fact, and every collection
# inside one is a tuple in its final report order - sorted once, at construction.


@dataclass(frozen=True, slots=True)
class ValueDifference:
    """One column of one row differing between the two sides.

    Attributes:
        column: The column name.
        ordinal: Its 1-based position in the table's column list, which is the schema's
            ORDINAL_POSITION. SYSTEM-REC has 169 columns.
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

        A type mismatch is a difference in its own right: it would mean the two dumps
        were produced by inconsistent serialisation, which is a real defect rather than
        something to smooth over.
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

    A one-sided table is expressed by `in_cobol` or `in_python` being false; that is a
    DIFFERENCE, never a reason to skip the table.

    Attributes:
        table: The in-scope table name.
        primary_key: The column rows were aligned on.
        in_cobol: Whether the oracle side had a dump for this table.
        in_python: Whether the migrated side had one.
        cobol_columns: The oracle's column list, in its own order.
        python_columns: The migrated side's column list.
        cobol_row_count: The oracle's row count.
        python_row_count: The migrated side's row count.
        missing_in_python: Primary keys the oracle produced and the migrated cycle did
            not, ascending.
        missing_in_cobol: Primary keys the migrated cycle produced and the oracle did
            not, ascending. Reported separately from the above because the two
            directions are materially different findings.
        value_differences: Rows present on both sides that differ in at least one
            column, ascending by key.
        rows_compared: Whether the rows were compared at all.
        cobol_key_types: The distinct Python type names of the oracle's primary-key
            values, ascending.
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
        """Whether the two column lists disagree in names, order or count."""
        if self.table_missing:
            return False
        return self.cobol_columns != self.python_columns

    @property
    def row_count_differs(self) -> bool:
        """Whether the two row counts disagree."""
        if self.table_missing:
            return False
        return self.cobol_row_count != self.python_row_count

    @property
    def key_types_differ(self) -> bool:
        """Whether the two sides serialised the ALIGNMENT COLUMN differently.

        A type mismatch in an ordinary column is reported per row with both type names.
        A type mismatch in the primary key cannot be, because rows are aligned on that
        column's VALUE and `1` is not `"1"`.
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
        tables: One entry per compared table, in the report's table order - the
            scenario's affected-table order when one was given, ASCII-sorted otherwise.
        cobol_dir: The oracle tree that was compared, for the operator's benefit. Never
            rendered into the report - an absolute path would break byte-determinism
            (rule R-6).
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
        """THE PASS CONDITION. True when the two trees are identical."""
        return self.total_differences == 0

    def __bool__(self) -> bool:
        """Whether anything differs, so `if diff:` reads naturally."""
        return not self.is_empty


# Pure: no I/O, no clock, no environment, no mutation of its arguments. Exact: `==`
# after a type check, and nothing else.


def _key_type_names(rows_by_key: Mapping[str | int, Any]) -> tuple[str, ...]:
    """Name the distinct Python types of a side's primary-key values.

    Args:
        rows_by_key: The side's rows, keyed by primary-key value.

    Returns:
        The distinct type names, ascending, so the comparison against the other side is
            deterministic. Empty when the side has no rows.
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
        DumpShapeError: Either object is malformed, they are for different tables, or
            they disagree on the primary key - the alignment column, so a disagreement
            there leaves no meaningful way to compare.
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

    # positional, so there is no meaningful alignment left to make.
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
        # Columns in SCHEMA ORDINAL ORDER, never alphabetical, so a reader can walk the
        # report against the CREATE TABLE statement.
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
            # EXACT, and nothing else.
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


# One table at a time, plain loop, fixed order: no thread, no event loop, no process
# pool, no synchronisation primitive.


def discover_tables(directory: Path | str) -> tuple[str, ...]:
    """List the tables a tree holds dumps for.

    Args:
        directory: A normalised tree.

    Returns:
        The table names, ASCII-ascending - sorted once, so the report's order can never
            depend on filesystem iteration order (rule R-6).

    Raises:
        MissingTreeError: The directory does not exist or is not a directory.
        UnknownTableError: It holds a `<NAME>.json` file whose name is not a table of
            the frozen schema.
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
        # Both producers write through `.<stem>.json.tmp` and then os.replace, so a dot-
        # prefixed name is a leftover from a failed write and never a dump.
        if name.startswith(TEMP_PREFIX):
            continue
        # Skip the reserved `_*` namespace, which is where the completeness manifest
        # lives.
        if name.startswith(RESERVED_PREFIX):
            continue
        if not name.endswith(DUMP_SUFFIX):
            continue
        if not entry.is_file():
            continue
        table = name[: -len(DUMP_SUFFIX)]
        # Raises rather than ignoring.
        table_spec(table)
        names.append(table)
    return tuple(sorted(names))


def _file_digest(path: Path) -> str:
    """Return the lower-case hex SHA-256 of a file's bytes.

    Args:
        path: The file to digest.

    Returns:
        The digest, 64 hexadecimal characters.

    Raises:
        ManifestError: The file could not be read back for checking.
    """
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(_DIGEST_BLOCK), b""):
                digest.update(block)
    except OSError as exc:
        raise ManifestError(
            f"could not read {path} to check it against the digest its "
            f"completeness manifest records: {exc}"
        ) from exc
    return digest.hexdigest()


def _manifest_fingerprint(directory: Path | str) -> str:
    """Return the SHA-256 of a tree's completeness manifest, for the summary.

    THE REASON THIS EXISTS (rule R-6). The manifest is what lets this
    module claim both trees were captured whole, so the claim is only as good as
    the reader's ability to check that the manifest quoted in the evidence is the
    manifest that was actually read. A digest binds the two; a file name does
    not.

    Args:
        directory: The published tree.

    Returns:
        The lower-case hex digest, or a short reason in its place. NEVER raises:
        a summary line is a diagnostic, and a digest that cannot be taken must
        not turn a completed comparison into an error. The manifest itself was
        already read and verified by `_verified_manifest` before this is called,
        so the failure cases here are narrow.
    """
    path = Path(directory) / MANIFEST_FILENAME
    try:
        return _file_digest(path)
    except ManifestError:
        return "unreadable"


def read_manifest(directory: Path | str) -> dict[str, Any] | None:
    """Read a tree's completeness manifest, if it has one.

    Args:
        directory: The published tree.

    Returns:
        The manifest object, or None when the tree carries none - which means the stage
            that wrote it did not finish.

    Raises:
        ManifestError: The manifest is present but unreadable, is not valid JSON, is not
            an object, or declares a version this tool does not understand.
    """
    path = Path(directory) / MANIFEST_FILENAME
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(
            f"could not read the completeness manifest {path}: {exc}"
        ) from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"the completeness manifest {path} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise ManifestError(
            f"the completeness manifest {path} must be a JSON object; got "
            f"{type(document).__name__}."
        )
    version = document.get("manifest_version")
    if version != MANIFEST_VERSION:
        raise ManifestError(
            f"the completeness manifest {path} declares manifest_version "
            f"{version!r}, and this tool understands {MANIFEST_VERSION}."
        )
    return document


def _verify_tree(directory: Path, label: str) -> dict[str, Any]:
    """Assert one tree declares itself complete and matches its declaration.

    Args:
        directory: The normalised tree.
        label: `cobol` or `python`, for the message.

    Returns:
        The verified manifest.

    Raises:
        ManifestError: The tree carries no manifest, over-declares, holds a file whose
            digest has changed, or holds an undeclared dump.
        TableNotInScopeError: It holds a `<NAME>.json` for one of the eleven
            out-of-scope tables. Raised from `discover_tables` rather than from the
            manifest read, and NAMED here because a caller that catches only
            `ManifestError` lets it escape - which is exactly how it once reached a
            caller as an unhandled traceback and exit 1.
        UnknownTableError: It holds a `<NAME>.json` whose name is not a table of the
            frozen schema at all. Same origin, same reason for naming it.
    """
    manifest = read_manifest(directory)
    if manifest is None:
        raise ManifestError(
            f"the {label} tree {directory} carries no "
            f"{MANIFEST_FILENAME}, so it does not declare itself complete. "
            f"harness/normalize.py writes that file LAST, so its absence "
            f"means the normalise stage did not finish for this side. "
            f"COMPARING AN UNMARKED TREE IS THE ONE THING THIS TOOL MUST "
            f"NOT DO: two partial captures can produce an EMPTY diff over "
            f"the tables that happen to be in both, and an empty diff is "
            f"the pass condition (Agent Action Plan section 0.8.5). Re-run "
            f"the dump and normalise stages for this side. "
            f"--allow-unmanifested waives the check and forfeits the claim "
            f"that the verdict is evidence (rule R-6)."
        )

    # THE EXACT SHAPE, NOT A DEFENSIVE READ. See
    # MANIFEST_REQUIRED_KEYS: every key below establishes WHICH capture this is, and a
    # manifest missing one is not a manifest this tool can render a verdict on.
    missing_keys = [key for key in MANIFEST_REQUIRED_KEYS if key not in manifest]
    if missing_keys:
        raise ManifestError(
            f"the manifest in the {label} tree {directory} is missing "
            f"{missing_keys}. This tool requires the exact shape "
            f"{list(MANIFEST_REQUIRED_KEYS)}: every one of those keys establishes "
            f"which capture the verdict would be about, and reading them defensively "
            f"is how a verdict came to be rendered on a capture that could not say "
            f"which run, which seed or which scenario definition it came from. "
            f"Re-run the dump and normalise stages; they write the current shape."
        )
    extra_keys = sorted(set(manifest) - set(MANIFEST_REQUIRED_KEYS))
    if extra_keys:
        raise ManifestError(
            f"the manifest in the {label} tree {directory} carries unrecognised "
            f"key(s) {extra_keys}. The shape is fixed and its key ORDER is part of "
            f"the byte-identical guarantee, so an added key means the tree was "
            f"written by something other than harness/normalize.py -- or edited "
            f"afterwards, which a verdict must never be rendered on."
        )

    provenance = manifest.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ManifestError(
            f"the manifest in the {label} tree {directory} carries no provenance "
            f"block, so the capture cannot say which attempt, which scenario "
            f"definition or which frozen schema it was taken under."
        )
    provenance_missing = [key for key in PROVENANCE_KEYS if key not in provenance]
    if provenance_missing:
        raise ManifestError(
            f"the provenance block in the {label} tree {directory} is missing "
            f"{provenance_missing}. Every field is either a fact a verdict depends "
            f"on or a fact a reader needs to reproduce it."
        )

    attestation_block = manifest.get("attestation")
    if not isinstance(attestation_block, Mapping):
        raise ManifestError(
            f"the manifest in the {label} tree {directory} carries no attestation "
            f"block, so nothing says the {label} cycle ever ran for this scenario."
        )
    attestation_missing = [
        key for key in ATTESTATION_REQUIRED_KEYS if key not in attestation_block
    ]
    if attestation_missing:
        raise ManifestError(
            f"the attestation block in the {label} tree {directory} is missing "
            f"{attestation_missing}."
        )

    stage = manifest.get("stage")
    if stage != MANIFEST_STAGE_NORMALIZED:
        raise ManifestError(
            f"the {label} tree {directory} declares stage {stage!r}, not "
            f"{MANIFEST_STAGE_NORMALIZED!r}. This stage compares NORMALISED "
            f"trees: a raw dump still carries char padding, unnormalised "
            f"decimal scales and both date-text forms, so comparing one "
            f"would report differences the normaliser exists to remove. Run "
            f"harness/normalize.py on it first."
        )

    declared = manifest.get("tables")
    if not isinstance(declared, list):
        raise ManifestError(
            f"the manifest in the {label} tree {directory} has no usable "
            f"`tables` list."
        )
    named: list[str] = []
    for entry in declared:
        if not isinstance(entry, dict) or not isinstance(
            entry.get("table"), str
        ):
            raise ManifestError(
                f"the manifest in the {label} tree {directory} has a "
                f"malformed entry in its `tables` list: {entry!r}."
            )
        table = entry["table"]
        named.append(table)
        member = directory / f"{table}{DUMP_SUFFIX}"
        if not member.is_file():
            raise ManifestError(
                f"the manifest in the {label} tree {directory} names table "
                f"{table!r} but {member.name} is not there. The tree is "
                f"incomplete, so no verdict can be rendered from it."
            )
        recorded = entry.get("sha256")
        if isinstance(recorded, str) and recorded:
            actual = _file_digest(member)
            if actual != recorded:
                raise ManifestError(
                    f"{member} does not match the digest its manifest "
                    f"records ({actual} rather than {recorded}), so the "
                    f"file changed after the tree was published. A verdict "
                    f"must be rendered on one capture, not a patched one."
                )

    present = set(discover_tables(directory))
    undeclared = sorted(present - set(named))
    if undeclared:
        raise ManifestError(
            f"the {label} tree {directory} holds dump(s) its manifest does "
            f"not name: {', '.join(undeclared)}. A published tree is purged "
            f"of stale files before the new set is moved in, so an "
            f"undeclared dump is a table left over from an earlier run - "
            f"comparing it would mix two captures."
        )
    return manifest


def verify_trees(
    left_dir: Path | str,
    right_dir: Path | str,
    require_identity: bool = True,
    *,
    same_side: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Assert both trees are complete and belong to the SAME run.

    dump and normalise stages record the scenario they were run for, so two trees whose
    manifests name different scenarios are not two sides of one comparison - they are
    two unrelated runs, and a clean diff between them says nothing whatever about the
    migration.

    Args:
        left_dir: The COBOL oracle's normalised tree.
        right_dir: The Python cycle's normalised tree.
        require_identity: Passed to `assert_same_provenance`; False under
            `--allow-unattested`, which permits an unidentified pair but never a
            mismatched one.
        same_side: Select the DETERMINISM contract instead of the parity one - two
            captures of the SAME side taken by two DIFFERENT runs. See
            PROVENANCE_MUST_MATCH_SAME_SIDE. Keyword-only and not reachable from the
            command line, so the default path is unchanged.

    Returns:
        The two verified manifests, left then right.

    Raises:
        ManifestError: Either tree is incomplete, or the two disagree about which
            scenario they belong to.
        MissingTreeError: Either directory is absent or is not a directory.
        TableNotInScopeError: Either tree holds a dump for one of the eleven
            out-of-scope tables.
        UnknownTableError: Either tree holds a dump whose name is not a table of the
            frozen schema.
        DiffStatesError: The root class of all four above. A command-line caller
            should catch THIS and report exit 2 - every failure this module raises is
            a "cannot compare", never a difference, and enumerating subclasses is how
            the discovery-time refusals once escaped as a traceback.
    """
    left_label = LABEL_RUN_A if same_side else LABEL_COBOL
    right_label = LABEL_RUN_B if same_side else LABEL_PYTHON
    left_manifest = _verify_tree(Path(left_dir), left_label)
    right_manifest = _verify_tree(Path(right_dir), right_label)

    left_scenario = left_manifest.get("scenario")
    right_scenario = right_manifest.get("scenario")
    if left_scenario != right_scenario:
        raise ManifestError(
            f"the two trees belong to different scenarios: the "
            f"{LABEL_COBOL} tree {left_dir} declares "
            f"{left_scenario!r} and the {LABEL_PYTHON} tree {right_dir} "
            f"declares {right_scenario!r}. They are not two sides of one "
            f"comparison, so no verdict can be rendered: a clean diff "
            f"between two unrelated runs says nothing about the migration."
        )

    # THE SIDES MUST BE THE SIDES THEY CLAIM TO BE. Two captures both labelled
    # `cobol' would compare a tree against itself and be identical by construction.
    left_side = left_manifest.get("side")
    right_side = right_manifest.get("side")
    if same_side:
        # The determinism obligation: ONE side, captured twice. The sides must be
        # EQUAL, and must still be a side this project knows -- a pair of captures
        # both labelled with something else is not a determinism pair either.
        if left_side != right_side or left_side not in SIDES:
            raise ManifestError(
                f"a same-side comparison needs two captures of ONE known side: "
                f"{left_dir} declares side {left_side!r} and {right_dir} declares "
                f"{right_side!r}, and the sides this project captures are "
                f"{', '.join(repr(side) for side in SIDES)}. Two captures of "
                f"DIFFERENT sides are a parity comparison, which is this tool's "
                f"default mode and enforces the opposite requirement."
            )
    elif left_side != LABEL_COBOL or right_side != LABEL_PYTHON:
        raise ManifestError(
            f"the two trees do not name the two sides of one comparison: "
            f"{left_dir} declares side {left_side!r} and {right_dir} declares "
            f"{right_side!r}, and this tool compares {LABEL_COBOL!r} against "
            f"{LABEL_PYTHON!r}. Two captures of one side are identical by "
            f"construction and would report a pass having compared nothing. "
            f"A determinism pair is compared with same_side=True, which requires "
            f"the run ids to DIFFER instead."
        )

    assert_same_provenance(
        left_manifest,
        right_manifest,
        left_dir,
        right_dir,
        require_identity=require_identity,
        same_side=same_side,
    )
    return left_manifest, right_manifest


def assert_same_provenance(
    left_manifest: Mapping[str, Any],
    right_manifest: Mapping[str, Any],
    left_dir: Path | str,
    right_dir: Path | str,
    require_identity: bool = True,
    *,
    same_side: bool = False,
) -> None:
    """Refuse two captures that were not taken under the same conditions.

    Three provenance fields and one attestation field must be equal before a single row
    is compared. See PROVENANCE_MUST_MATCH for what each inequality would mean, and
    below for why the seed identity is the most important of the four.

    Args:
        left_manifest: The COBOL side's verified manifest.
        right_manifest: The Python side's verified manifest.
        left_dir: Where the COBOL tree is, for the message.
        right_dir: Where the Python tree is, for the message.
        require_identity: Whether a run identity and a seed identity must be PRESENT.
            `--allow-unattested` sets this False, because a capture whose run stage
            published nothing cannot carry either by construction and refusing it here
            would make that waiver unusable. EQUALITY is still enforced whenever both
            sides carry a value: the waiver permits an unidentified pair, never a
            MISMATCHED one, so two captures of different runs are refused either way.
        same_side: Apply the determinism contract instead of the parity one:
            `run_id` must DIFFER rather than match, and the remaining shared fields
            must still be equal. See PROVENANCE_MUST_MATCH_SAME_SIDE.

    Raises:
        ManifestError: A required field is absent, the two sides disagree about one
            that must match, or they agree about one that must differ.
    """
    left_prov = left_manifest["provenance"]
    right_prov = right_manifest["provenance"]
    left_label = LABEL_RUN_A if same_side else LABEL_COBOL
    right_label = LABEL_RUN_B if same_side else LABEL_PYTHON
    must_match = (
        PROVENANCE_MUST_MATCH_SAME_SIDE if same_side else PROVENANCE_MUST_MATCH
    )

    # THE ROOT CAUSE IS REPORTED, NOT THE SYMPTOM.
    #
    # An absent run identity is almost never a defect in the dump stage; it is what an
    # absent RUN looks like by the time it reaches here, because a capture whose run
    # stage published nothing -- or published a failure -- carries no identity to
    # record. Reporting "the provenance field 'run_id' is empty" would send a reader to
    # the dump stage; reporting that the capture does not attest a run, and the status
    # it recorded, sends them to the run stage where the cause actually is.
    #
    # Enforcement is unchanged either way: both conditions refuse. Only the diagnosis
    # is ordered, and only when the attestation explains the emptiness.
    if require_identity:
        for label, manifest, directory in (
            (left_label, left_manifest, left_dir),
            (right_label, right_manifest, right_dir),
        ):
            attestation = manifest.get("attestation")
            if not isinstance(attestation, Mapping):
                continue
            if attestation.get("attested") is True:
                continue
            if manifest["provenance"].get("run_id"):
                # It does not attest, but it does carry an identity - so the identity
                # gate has nothing to complain about and assert_attested owns the
                # refusal. Left to it, with its waiver intact.
                continue
            detail = attestation.get("detail") or "no reason was recorded"
            recorded = attestation.get("run_status")
            raise ManifestError(
                f"the {label} capture in {directory} does not ATTEST a run, and so "
                f"carries no run identity for a verdict to cite: {detail} "
                f"(recorded run status {recorded!r}). Two captures taken after runs "
                f"that never happened are trivially equal, and equality is the pass "
                f"condition -- which is why this is refused here rather than compared. "
                f"Run the ten stages in order with one run id bound through all of "
                f"them: export ACAS_PARITY_RUN_ID before stage 1 (README section 8), "
                f"or let tests/conftest.py bind it for the composed protocol."
            )

    for key in must_match:
        left_value = left_prov.get(key)
        right_value = right_prov.get(key)
        if (not left_value or not right_value) and require_identity:
            whose = (
                "both sides"
                if not left_value and not right_value
                else (str(left_dir) if not left_value else str(right_dir))
            )
            raise ManifestError(
                f"the provenance field {key!r} is empty on {whose}. It is required: a "
                f"verdict that cannot state it is a verdict about an unidentified pair "
                f"of captures. Re-run the protocol from stage 1 with ACAS_PARITY_RUN_ID "
                f"bound through every stage (README section 8)."
            )
        if not left_value or not right_value:
            # The identity requirement was waived, so an empty field is accepted and
            # there is nothing to compare it against.
            continue
        if left_value != right_value:
            raise ManifestError(
                f"the two captures disagree about {key!r}: {left_dir} records "
                f"{left_value!r} and {right_dir} records {right_value!r}. They were "
                f"not taken under the same conditions, so no verdict can be rendered "
                f"on them -- an empty diff between two captures of different runs, "
                f"different scenario definitions or different schemas says nothing "
                f"about the migration."
            )

    # THE FIELDS A DETERMINISM PAIR MUST DISAGREE ABOUT.
    #
    # Two captures carrying ONE run id are one capture read twice, and a tree always
    # equals itself -- the same false pass the identical-directory guard refuses, just
    # arriving by a different route. So the determinism mode requires the run ids to
    # DIFFER, which is a check the parity mode has no use for and which no earlier
    # version of this tool performed at all.
    if same_side:
        for key in PROVENANCE_MUST_DIFFER_SAME_SIDE:
            left_value = left_prov.get(key)
            right_value = right_prov.get(key)
            if require_identity and (not left_value or not right_value):
                whose = (
                    "both sides"
                    if not left_value and not right_value
                    else (str(left_dir) if not left_value else str(right_dir))
                )
                raise ManifestError(
                    f"the provenance field {key!r} is empty on {whose}, so this pair "
                    f"cannot be shown to be two DIFFERENT runs. A determinism verdict "
                    f"on two captures that might be one run is not a verdict. Bind one "
                    f"run id per run and re-run the protocol."
                )
            if left_value and right_value and left_value == right_value:
                raise ManifestError(
                    f"the two captures carry the SAME {key!r}, {left_value!r}: "
                    f"{left_dir} and {right_dir} are two readings of ONE run, not two "
                    f"runs. A capture always equals itself, so comparing them would "
                    f"report byte-identical dumps whatever the migrated cycle did -- a "
                    f"FALSE PASS for the determinism obligation. Run the cycle twice, "
                    f"binding a DIFFERENT run id to each."
                )

    # THE EXACT SEED IDENTITY
    #
    # This is the field that makes the pass condition mean what it claims. The
    # comparison's whole premise is that both cycles started from BYTE-FOR-BYTE the
    # same state -- and until now the only thing binding them was a list of TABLE ROW
    # COUNTS, which two seedings with the same shape and DIFFERENT VALUES share. Two
    # legs could start from different money and the protocol would report that their
    # starting states matched. harness/seed.sh stages a marker carrying a SHA-256 per
    # seeded file, harness/reset_db.sh publishes that marker's digest, both runners
    # record it, and here it must be present, a real digest, and EQUAL.
    left_seed = left_manifest["attestation"].get("seed_marker_sha256")
    right_seed = right_manifest["attestation"].get("seed_marker_sha256")
    for label, directory, value in (
        (left_label, left_dir, left_seed),
        (right_label, right_dir, right_seed),
    ):
        if not isinstance(value, str) or not re.fullmatch(_SHA256_PATTERN, value):
            if not require_identity:
                # Waived by --allow-unattested for the reason in the docstring. The
                # equality check below still runs, so two DIFFERENT markers are refused
                # even under the waiver.
                continue
            raise ManifestError(
                f"the {label} capture in {directory} carries seed_marker_sha256 "
                f"{value!r}, which is not a SHA-256. That digest is the EXACT identity "
                f"of the bytes the run was seeded from. Without it the only thing "
                f"binding the two legs to one starting state is a list of row counts, "
                f"and two seedings with the same shape and different values share "
                f"those. Run the protocol through harness/reset_db.sh, which publishes "
                f"the identity from the fixture marker harness/seed.sh stages."
            )
    if left_seed != right_seed:
        raise ManifestError(
            f"the two cycles were seeded from DIFFERENT fixtures: the "
            f"{left_label} capture records {left_seed} and the {right_label} "
            f"capture records {right_seed}. The comparison's entire premise is that "
            f"both started from byte-for-byte the same state, so this is refused here "
            f"rather than surfacing at the diff, where it would look exactly like an "
            f"accounting difference. Reset and re-seed both legs from one fixture."
        )


def assert_attested(
    manifests: tuple[Mapping[str, Any], Mapping[str, Any]],
) -> None:
    """Refuse a pair of trees whose run stages did not attest success.

    THE DEFECT THIS CLOSES. The protocol's stages were operator discipline: every tool
    reported its own status and no tool looked at the one before it. Against a checkout
    with no fixtures and no compiled oracle the seed exited 75, the COBOL run 74 and the
    Python run 69 -- and the dump, normalise and comparison stages then exited 0 apiece
    and printed "identical, no difference". An empty diff is the ONE documented pass
    condition (AAP section 0.8.5), so the harness certified the migration exact having
    compared two empty captures. Both manifests were COMPLETE, so the existing
    partial-capture defence could not engage: the trees were not partial, the RUNS were
    absent.

    So each capture now carries what its run stage claimed, and this is where the claim
    is enforced. Nothing is inferred: a missing run-status file, one belonging to
    another scenario, or a status that means the harness itself failed all arrive here
    as `attested: false` with the reason recorded, and all three are refused.

    WHAT IS *NOT* REFUSED, AND WHY THAT MATTERS MOST. A run that COMPLETED and found
    a behavioural difference - `harness/run_python_scenario.sh` exiting 69 after every
    operation ran and every post-run assertion was taken - is attested as COMPARABLE.
    Refusing it along with the harness faults would be perverse: the one situation in
    which a human most needs to know which tables, rows
    and columns differ is exactly the situation in which the differ declined to say. The
    state that run left IS the finding. So it is compared, and its disposition is
    ANNOUNCED here so that the verdict which follows cannot be mistaken for a clean
    run's.

    Args:
        manifests: The verified COBOL and Python manifests, in that order.

    Raises:
        ManifestError: Either side's run did not complete.
    """
    for label, manifest in zip((LABEL_COBOL, LABEL_PYTHON), manifests):
        attestation = manifest.get("attestation")
        if not isinstance(attestation, Mapping):
            raise ManifestError(
                f"the {label} tree's {MANIFEST_FILENAME} carries no run "
                f"attestation, so nothing says the {label} cycle ever ran for "
                f"this scenario. Re-run the dump stage: harness/dump_tables.py "
                f"records what the run stage claimed. "
                f"--allow-unattested waives this and forfeits the claim that "
                f"the verdict is evidence (rule R-6)."
            )
        if attestation.get("attested") is True:
            # A comparable-but-not-clean run is announced, every time, before any
            # verdict is printed. Silence here would let an empty diff read as
            # unqualified parity for a run that had already reported otherwise.
            if attestation.get("disposition") == DISPOSITION_BEHAVIOURAL:
                status = attestation.get("run_status")
                detail = attestation.get("detail") or "no reason was recorded."
                print(
                    f"{_PROG}: NOTE - the {label} run exited {status} and reported a "
                    f"BEHAVIOURAL DIFFERENCE. Its capture is compared because the run "
                    f"completed and the state it left is the finding, but the verdict "
                    f"below is NOT the verdict of a clean run. {detail}",
                    file=sys.stderr,
                )
            continue
        detail = attestation.get("detail") or "no reason was recorded."
        raise ManifestError(
            f"the {label} tree does not attest a COMPLETED run, so NO VERDICT "
            f"CAN BE RENDERED ON IT: {detail} "
            f"This is refused rather than reported as a pass because an empty "
            f"diff is the only pass condition the protocol has (Agent Action "
            f"Plan section 0.8.5), and two captures taken after failed runs "
            f"produce exactly that. Run the ten stages in order and stop at the "
            f"first failure. "
            f"--allow-unattested waives this and forfeits the claim that the "
            f"verdict is evidence (rule R-6)."
        )


def assert_not_all_empty(
    manifests: tuple[Mapping[str, Any], Mapping[str, Any]],
    *,
    expect_empty: bool,
) -> None:
    """Refuse a comparison in which every table is empty on BOTH sides.

    A comparison of nothing against nothing is trivially equal, and equality is the
    pass condition. This is the same failure as an unattested capture arriving by a
    different route -- a database that was never seeded, a seed whose rows were
    discarded, a scenario pointed at the wrong schema -- and it is refused for the same
    reason.

    An individual empty table is perfectly ordinary and is NOT refused: an empty
    `GLPOSTING-REC` may be exactly what a rejected batch should leave behind. What is
    refused is a comparison in which nothing anywhere holds a row, unless the scenario
    itself declares that expectation.

    Args:
        manifests: The verified COBOL and Python manifests, in that order.
        expect_empty: The scenario declared `expect_empty_state: true`, so an all-empty
            capture is its stated outcome and is compared rather than refused.

    Raises:
        ManifestError: Both sides are wholly empty and the scenario did not declare it.
    """
    totals: list[int] = []
    for manifest in manifests:
        declared = manifest.get("tables")
        total = 0
        if isinstance(declared, list):
            for entry in declared:
                if isinstance(entry, Mapping):
                    count = entry.get("row_count")
                    if isinstance(count, int):
                        total += count
        totals.append(total)

    if any(total > 0 for total in totals):
        return
    if expect_empty:
        _progress(
            f"{_PROG}: every table is empty on both sides, and the scenario "
            f"declares expect_empty_state, so the comparison proceeds on that "
            f"declaration."
        )
        return

    raise ManifestError(
        f"every table is EMPTY on both sides -- {totals[0]} row(s) in the "
        f"{LABEL_COBOL} capture and {totals[1]} in the {LABEL_PYTHON} one -- so "
        f"there is nothing to compare and equality here means nothing was "
        f"measured. Refused rather than reported as a pass: an empty diff is "
        f"the only pass condition the protocol has (Agent Action Plan section "
        f"0.8.5). The usual causes are a database that was never seeded, a seed "
        f"whose rows were discarded before they were committed, or a run that "
        f"never reached the tables at all. Check the seed stage first: "
        f"harness/seed.sh measures its own result and exits 76 rather than "
        f"reporting a seed that is not there. If an all-empty state really is "
        f"this scenario's expected outcome, declare it in the scenario file "
        f"with `expect_empty_state: true' so the claim is on the record."
    )


def manifest_tables(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the table names a manifest declares, in its own order.

    Args:
        manifest: A verified manifest.

    Returns:
        The declared table names.
    """
    declared = manifest.get("tables")
    if not isinstance(declared, list):
        return ()
    return tuple(
        entry["table"]
        for entry in declared
        if isinstance(entry, dict) and isinstance(entry.get("table"), str)
    )


def diff_trees(
    left_dir: Path | str,
    right_dir: Path | str,
    tables: Sequence[str] | None = None,
    *,
    allow_raw: bool = False,
    same_side: bool = False,
) -> TreeDiff:
    """Compare two normalised trees, table by table, sequentially.

    Args:
        left_dir: The COBOL oracle's normalised tree - the specification side, reported
            as `cobol`.
        right_dir: The migrated Python cycle's normalised tree, reported as `python`.
        tables: The tables to compare, in the order to report them - normally the
            scenario's affected-table list.
        allow_raw: Permit comparing directories whose names do not mark them as
            normalised.
        same_side: Report the two trees as `run A'/`run B' rather than
            `cobol'/`python'. The determinism obligation compares one side twice; see
            PROVENANCE_MUST_MATCH_SAME_SIDE. This flag affects the LABELS only - the
            row-by-row comparison is byte-for-byte identical in both modes, and no
            tolerance, ignore-list or coalescing exists in either.

    Returns:
        A `TreeDiff`. `is_empty` is the pass condition.

    Raises:
        MissingTreeError: Either directory is absent or is not a directory.
        SameTreeError: Both sides name the same directory, which would always compare
            equal and so would be a false pass.
        RawTreeError: A directory is not a normalised tree and `allow_raw` is false.
        EmptyComparisonError: There is no table to compare.
        MissingTableFileError: A requested table's dump is absent from one or both
            trees. Absence is a reported difference only for a table that was DISCOVERED
            rather than requested.
        UnknownTableError: A requested or discovered name is not a table of the frozen
            schema.
        TableNotInScopeError: A requested or discovered name is out of scope.
        DumpReadError: A dump is unreadable or is not a JSON object.
        DumpShapeError: A dump's shape is wrong, or the two sides disagree on the
            alignment column.
        DuplicateKeyError: A primary-key value appears twice in a dump.
        UnexpectedNullError: A value is null.
        NumericPolicyError: A value is a float (rule R-2).
        UnexpectedValueTypeError: A value is of an impossible type.
    """
    left = Path(left_dir)
    right = Path(right_dir)

    # COMPARING A TREE WITH ITSELF ALWAYS PASSES, whatever the migration did, so it is
    # refused rather than answered.
    if left.resolve() == right.resolve():
        raise SameTreeError(
            f"both sides name the same directory, {left}. A tree always "
            f"equals itself, so the comparison would report an empty diff "
            f"whatever the migration produced - a FALSE PASS. Pass the "
            f"{LABEL_COBOL} tree and the {LABEL_PYTHON} tree, for example "
            f"`$ACAS_OUT/<scenario>/{LABEL_COBOL}{NORMALIZED_SUFFIX}` and "
            f"`$ACAS_OUT/<scenario>/{LABEL_PYTHON}{NORMALIZED_SUFFIX}`."
        )

    _assert_tree(
        left, LABEL_RUN_A if same_side else LABEL_COBOL, allow_raw=allow_raw
    )
    _assert_tree(
        right, LABEL_RUN_B if same_side else LABEL_PYTHON, allow_raw=allow_raw
    )

    discovered = tables is None

    if discovered:
        # The UNION, not the intersection.
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
            "trees hold will be compared. A scenario comparison should name "
            "its scope explicitly: --all-in-scope is the protocol, all 22 "
            "in-scope tables whatever the two captures happen to contain, "
            "and --scenario-file or --tables narrow it for debugging. A "
            "union depends on how the captures were taken, so its verdict "
            "is not evidence (rule R-6)."
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
            # harness/dump_tables.py writes a file for every table it is asked to dump
            # whatever the row count - an empty table still gets `"row_count".
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
            # A ONE-SIDED DISCOVERED TABLE IS A DIFFERENCE, never a skip: a naive
            # intersection would have hidden it.
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
            "it affects, and harness/run_cobol_scenario.sh says the same: "
            "the comparison must be bounded by an explicit "
            "per-scenario list."
        )
    return tuple(selected)


# Bounding the comparison by the SCENARIO is the protocol, and the alternative - an
# ignore-list here - is forbidden by rule R-4.


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


def scenario_expects_empty_state(path: Path | str | None) -> bool:
    """Report whether a scenario declares that an all-empty end state is its outcome.

    One optional boolean, `expect_empty_state`, read with the same discipline as the
    affected-table list: nothing else in the scenario is interpreted, and the key's
    ABSENCE means False, so no existing scenario changes behaviour by omitting it.

    It exists so that the all-empty refusal in `assert_not_all_empty` can be answered by
    a scenario rather than by a command-line flag: a flag would be a per-invocation
    decision an operator makes under pressure, while the scenario file is committed
    evidence of what the run was expected to leave behind.

    Args:
        path: The scenario definition, or None when the tables were named directly.

    Returns:
        Whether the scenario declares the expectation.

    Raises:
        ScenarioFileError: The file cannot be read as a YAML mapping, or the key is
            present with something other than a boolean.
    """
    if path is None:
        return False
    try:
        import yaml

        #  THE SHARED DUPLICATE-REJECTING LOADER.
        #  `yaml.safe_load` applies last-one-wins to a repeated key, silently, and a
        #  scenario definition carries the destructive answers, the fan-out switch
        #  that decides which tables a run touches and the comparison bound. Imported
        #  lazily, by sibling name, so this module still imports without PyYAML.
        parser_module = _load_scenario_yaml_module()
    except ImportError as exc:
        raise ScenarioFileError(
            f"the shared scenario parser could not be loaded, so a scenario "
            f"definition cannot be read: {exc}. harness/normalize.py is "
            f"the shared duplicate-rejecting loader and requirements.txt pins "
            f"PyYAML==6.0.3; the message above names which of the two was "
            f"missing, because they have different remedies."
        ) from exc

    source = Path(path)
    try:
        document = parser_module.load_scenario_yaml(
            source.read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise ScenarioFileError(
            f"could not read the scenario definition {source}: {exc}"
        ) from exc
    except yaml.YAMLError as exc:
        raise ScenarioFileError(
            f"the scenario definition {source} is not valid YAML: {exc}"
        ) from exc

    if not isinstance(document, Mapping):
        raise ScenarioFileError(
            f"the scenario definition {source} must be a mapping at the top "
            f"level; got {type(document).__name__}."
        )
    if "expect_empty_state" not in document:
        return False
    value = document["expect_empty_state"]
    if not isinstance(value, bool):
        raise ScenarioFileError(
            f"expect_empty_state in {source} must be true or false; got "
            f"{value!r}. It declares that this scenario is expected to leave "
            f"every affected table empty, which suspends the all-empty "
            f"refusal, so it is not inferred from a truthy value."
        )
    return value


def scenario_tables(path: Path | str) -> tuple[str, ...]:
    """Read a scenario's affected-table list, in the order it declares it.

    Only that one list is read: no seed data is interpreted and no input is validated,
    because interpreting a scenario's declared contents would be exactly the added
    validation rule R-3 forbids.

    Args:
        path: The scenario definition to read.

    Returns:
        The table names, in the scenario's own order - which becomes the report's table
            order.

    Raises:
        ScenarioFileError: The shared scenario parser is unloadable, or the file is
            missing, unreadable,
            not a mapping, carries neither key or both, or its list is empty or holds
            something that is not a table name.
        UnknownTableError: The list names something that is not a table.
        TableNotInScopeError: The list names an out-of-scope table.
    """
    try:
        import yaml

        #  THE SHARED DUPLICATE-REJECTING LOADER.
        #  `yaml.safe_load` applies last-one-wins to a repeated key, silently, and a
        #  scenario definition carries the destructive answers, the fan-out switch
        #  that decides which tables a run touches and the comparison bound. Imported
        #  lazily, by sibling name, so this module still imports without PyYAML.
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
        The table names in the order to report them, or `None` when neither selector was
            given - which asks `diff_trees` for the union of what the two trees hold.

    Raises:
        ValueError: Both selectors were given, or `tables` is empty or names a table
            twice.
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


# BYTE-DETERMINISTIC for a given pair of inputs (rule R-6).

# The report's finding labels. Fixed strings, so the report is greppable and a
# downstream document can quote them.
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

    Args:
        cobol: The oracle's column list.
        python: The migrated side's column list.

    Returns:
        A rendered description, or the empty string when the lists are equal.
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

    CARRIES ACCOUNTING VALUES, DELIBERATELY. This line and the primary keys
    `render_table` emits below it are the whole point of the report: an
    operator cannot interrogate the compiled oracle about a difference
    without seeing the two figures (rule R-6), and
    docs/migration/scenario-diff-evidence.md cites this file as the mandated
    evidence (Agent Action Plan section 0.8.5). Censoring it here would
    destroy the deliverable.

    The disclosure risk is handled at the two places it actually exists,
    NOT here - see THE OPERATOR SUMMARY above `summarise`:

    * the report FILE is created 0600, staged `O_EXCL | O_NOFOLLOW` and
      replaced atomically by `write_report`, in a directory this module
      creates 0700;
    * STDOUT - a collected container log in the composed recipe - gets
      `summarise`'s value-free rendering INSTEAD, on every path and with no
      flag to override it. A run given no `--out` writes the values to a
      private fallback file rather than to stdout.

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
        # Both types named, because a type mismatch means the two dumps were produced by
        # inconsistent serialisation - a real defect, not a rendering quirk.
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

    Args:
        diff: The table's findings.
        max_differences: How many DETAIL lines to print before truncating. The
            structural headline is never truncated, and truncation never changes the
            exit code.

    Returns:
        The lines, without newlines. Empty when the table agrees.
    """
    if diff.is_empty:
        return ()

    table = diff.table
    lines: list[str] = []

    # 1. STRUCTURAL FINDINGS. Never truncated: at most three lines, and they are the
    # headline a reader needs before any detail.
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
        # The alignment column itself was serialised differently, so no key could be
        # shared and every row below is reported one-sided.
        lines.append(
            _join(
                table,
                _F_KEY_TYPE_MISMATCH,
                diff.primary_key,
                f"{LABEL_COBOL}={','.join(diff.cobol_key_types)}",
                f"{LABEL_PYTHON}={','.join(diff.python_key_types)}",
            )
        )

    # 2. DETAIL FINDINGS, capped. The cap exists so that a catastrophic mismatch cannot
    # produce an unusable megabyte.
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
        max_differences: How many detail lines per table to print before truncating.

    Returns:
        THE EMPTY STRING when the two trees are identical - Agent Action Plan section
            0.8.5.
    """
    lines: list[str] = []
    for table in diff.tables:
        lines.extend(
            render_table(table, max_differences=max_differences)
        )
    if not lines:
        return ""
    return "".join(f"{line}\n" for line in lines)


# The composed layout writes $ACAS_OUT/<scenario>/diff.txt, which is the path the file
# specification for this module names and the path the per-scenario diff evidence will
# cite.

# The temporary name the report is written under before os.replace moves it into place,
# in the SAME directory as its target so the replace is atomic.
_TEMP_SUFFIX: Final[str] = ".txt.tmp"


_OUTPUT_FILE_MODE: Final[int] = 0o600

_OUTPUT_DIR_MODE: Final[int] = 0o700

_OUTPUT_UMASK: Final[int] = 0o077

#: `O_NOFOLLOW` where the platform has it; 0 leaves the flag word unchanged rather than
#: making the module unimportable where it is absent.
_O_NOFOLLOW: Final[int] = getattr(os, "O_NOFOLLOW", 0)


def _write_text_securely(text: str, target: Path, staging: Path) -> None:
    """Write `text` to `target` atomically, privately, and without following.

    Args:
        text: The exact bytes-to-be. May be EMPTY, which is the pass case and must
            produce a zero-byte file rather than no file.
        target: The final path. Replaced atomically. `os.replace` does not follow a
            symlink at this name either.
        staging: The temporary name, which MUST share `target`'s directory for the
            replace to be atomic.

    Raises:
        OSError: The staging file could not be created, written or moved.
    """
    staging.unlink(missing_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW
    descriptor = os.open(staging, flags, _OUTPUT_FILE_MODE)
    try:
        # Re-applied explicitly, because the mode passed to `os.open` is masked by the
        # process umask. `fchmod` on the open descriptor cannot be redirected to another
        # file.
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
            # NOT SWALLOWED SILENTLY. The expected case is `EBADF`: the
            # context manager above already closed the descriptor, which is
            # ordinary and says nothing. Anything else means the descriptor
            # could not be released, so it is REPORTED - a cleanup failure
            # that leaves no trace is how a leaked descriptor or a full
            # filesystem stays invisible. The original failure is still the
            # one that propagates, because it is re-raised below unchanged.
            if close_error.errno != errno.EBADF:
                _warn(
                    f"could not close the staging descriptor for {staging} "
                    f"while handling an earlier failure: errno "
                    f"{close_error.errno} "
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


def invalidate_report(target: Path) -> None:
    """Remove any report already at `target`, before comparing anything.

    So the accepted output is invalidated the moment the path is known and before a
    single dump is read. Afterwards there are exactly three states, and each says only
    what is true.

    Args:
        target: The report path this run will write.

    Raises:
        ReportPathError: An existing report could not be removed. Fatal rather than
            ignored.
    """
    try:
        target.unlink(missing_ok=True)
    except OSError as exc:
        raise ReportPathError(
            f"could not remove the previous report {target} before "
            f"comparing: {exc}. It has to go first: a passing run leaves a "
            f"ZERO-BYTE file, so a stale one surviving an error path would "
            f"be indistinguishable from proof that this run passed - and the "
            f"migration's scenario diff evidence is built from that file."
        ) from exc


def _fallback_report_path() -> Path:
    """Return a private path to hold the report when none was asked for.

    THE REASON THIS EXISTS. A non-empty diff's detail is live accounting data:
    every differing value beside its primary key. It belongs in a 0600 file and
    never on stdout, which in the composed recipe is a collected container log.
    Before this helper, a run given no `--out` put the whole report on stdout
    instead - the same content this module protects with `O_EXCL`, `O_NOFOLLOW`
    and mode 0600 when it goes to a file. That inconsistency was the leak; a
    private file that always exists removes it.

    `tempfile.mkdtemp` is used rather than a path derived from the compared
    trees, for two reasons: the trees are normalized captures that nothing
    should write into, and `mkdtemp` creates the directory 0700 by construction
    with a name no other process can have predicted, so there is no window in
    which the report is readable by anyone else.

    Returns:
        A path inside a fresh private directory, named exactly as the composed
        layout names its report so a reader recognises it.

    Raises:
        ReportPathError: No private directory could be created, which leaves
            the values with nowhere safe to go. The caller then prints the
            value-free summary with no pointer and reports this on stderr; it
            does NOT fall back to stdout.
    """
    try:
        directory = Path(tempfile.mkdtemp(prefix="acas-diff-"))
    except OSError as exc:
        raise ReportPathError(
            f"could not create a private directory to hold the differing "
            f"values: {exc}"
        ) from exc
    return directory / DIFF_FILENAME


def write_report(report: str, path: Path | str) -> Path:
    """Write the report to a file, atomically and privately.

    The file is created mode 0600 through a descriptor opened `O_EXCL` and `O_NOFOLLOW`.
    See the SECURE OUTPUT commentary above `_write_text_securely`.

    Args:
        report: The rendered report; the empty string on a pass.
        path: Where to write it. Parent directories are created, mode 0700.

    Returns:
        The path written.

    Raises:
        ReportPathError: The file could not be written.
    """
    target = Path(path)
    try:
        _make_output_directory(target.parent)
    except OSError as exc:
        raise ReportPathError(
            f"could not create the directory for the report {target}: "
            f"{exc}"
        ) from exc

    temporary = target.parent / f"{TEMP_PREFIX}{target.stem}{_TEMP_SUFFIX}"
    try:
        # `report` already ends with a newline when it is non-empty, and is empty on a
        # pass - so a passing run leaves a zero-byte file rather than a file containing
        # a bare newline.
        _write_text_securely(report, target, temporary)
    except OSError as exc:
        raise ReportPathError(
            f"could not write the report to {target}: {exc}"
        ) from exc
    return target


# The temporary name the verdict manifest is staged under, in the SAME directory as its
# target so the replace is atomic. Distinct from `_TEMP_SUFFIX` because the two files are
# published side by side and a shared staging name would let one clobber the other's.
_VERDICT_TEMP_SUFFIX: Final[str] = ".json.tmp"


def verdict_path_for(report_path: Path | None) -> Path | None:
    """Return where this run's verdict manifest belongs.

    The verdict sits beside the report, so the composed layout publishes
    `$ACAS_OUT/<scenario>/diff.txt` and `$ACAS_OUT/<scenario>/verdict.json` together and
    a reader who has one can always find the other.

    Args:
        report_path: Where the report will be written, or None when no `--out` was
            given and the values will go to a private fallback directory instead.

    Returns:
        The verdict path, or None when there is no report directory to put it in.
    """
    if report_path is None:
        return None
    return Path(report_path).parent / VERDICT_FILENAME


def invalidate_verdict(target: Path) -> None:
    """Remove any verdict manifest already at `target`, before comparing anything.

    THE REASON THIS EXISTS (rule R-6). The verdict manifest is the
    machine-readable claim that a scenario reached parity, and
    `docs/migration/scenario-diff-evidence.md` cites one per scenario. A stale manifest surviving an error path
    would therefore let a run that never reached the comparison inherit the previous
    run's verdict - which is the exact failure the manifest exists to prevent. It goes
    first, before a single dump is read, exactly as the report does.

    Args:
        target: The verdict path this run will write.

    Raises:
        ReportPathError: An existing manifest could not be removed. Fatal rather
            than ignored, for the reason above.
    """
    try:
        target.unlink(missing_ok=True)
    except OSError as exc:
        raise ReportPathError(
            f"could not remove the previous verdict manifest {target} before "
            f"comparing: {exc}. It has to go first: this file IS the published claim that a scenario may be reported IDENTICAL, so a stale one surviving an error path would let this run inherit the previous run's verdict."
        ) from exc


def _provenance_field(
    manifest: Mapping[str, Any] | None, key: str
) -> Any:
    """Return one field of a verified manifest's provenance block, or None.

    Args:
        manifest: A verified manifest, or None under `--allow-unmanifested`.
        key: The provenance key to read.

    Returns:
        The recorded value, or None when there is no manifest or no such key. None
        is meaningful in the published verdict: it says this comparison carried no
        provenance, which is what stops a reader claiming parity from
        it.
    """
    if manifest is None:
        return None
    provenance = manifest.get("provenance")
    if not isinstance(provenance, Mapping):
        return None
    value = provenance.get(key)
    return value if value != "" else None


def _attestation_field(
    manifest: Mapping[str, Any] | None, key: str
) -> Any:
    """Return one field of a verified manifest's attestation block, or None.

    Args:
        manifest: A verified manifest, or None under `--allow-unmanifested`.
        key: The attestation key to read.

    Returns:
        The recorded value, or None when there is no manifest or no such key.
    """
    if manifest is None:
        return None
    attestation = manifest.get("attestation")
    if not isinstance(attestation, Mapping):
        return None
    value = attestation.get(key)
    return value if value != "" else None


def build_verdict(
    diff: TreeDiff,
    *,
    outcome: str,
    exit_code: int,
    scenario: str | None,
    manifests: tuple[Mapping[str, Any], Mapping[str, Any]] | None,
    left: Path,
    right: Path,
    report_path: Path | None,
    report_digest: str | None,
) -> dict[str, Any]:
    """Build the machine-readable verdict manifest for a completed comparison.

    THE REASON THIS EXISTS. Before this, a pass was signalled only by
    exit status 0 and a zero-byte `diff.txt`, and nothing downstream could tell a run
    that compared twenty-two tables and found no difference from a run whose
    `diff.txt` happened to be absent or empty for some other reason. The verdict
    manifest states the outcome explicitly, names how much was compared, and carries
    the provenance the two sides agreed on - so the scenario
    tests and the migration's diff evidence read a claim rather than infer one.

    It is published on BOTH outcomes. A `different` verdict is evidence too: it is
    what an ambiguity resolution cites when the compiled oracle is interrogated
    (Agent Action Plan section 0.6.6).

    Args:
        diff: The completed comparison.
        outcome: `OUTCOME_IDENTICAL` or `OUTCOME_DIFFERENT`.
        exit_code: The status this run will exit with, recorded so the artifact and
            the process agree.
        scenario: The scenario name, from the manifests or `--scenario`.
        manifests: The two verified manifests, COBOL first, or None under
            `--allow-unmanifested`.
        left: The COBOL tree, for its manifest digest.
        right: The Python tree, for its manifest digest.
        report_path: Where the report was written, or None.
        report_digest: The report's SHA-256, or None when it could not be taken.

    Returns:
        A dict whose keys are exactly `VERDICT_KEYS`, in that order.
    """
    cobol_manifest = manifests[0] if manifests is not None else None
    python_manifest = manifests[1] if manifests is not None else None

    # `--cobol`/`--python` name the two trees directly and carry no scenario, but the
    # manifests always record one and `verify_trees` has already refused a pair that
    # disagrees about it. So the artifact names the scenario either way.
    if not scenario and cobol_manifest is not None:
        recorded_scenario = cobol_manifest.get("scenario")
        if isinstance(recorded_scenario, str) and recorded_scenario:
            scenario = recorded_scenario

    # `verify_trees` has already refused any comparison whose two sides disagree on
    # run id, scenario-file digest, frozen-schema digest or seed marker, so reading them
    # from the COBOL side alone records the value BOTH
    # sides carry rather than picking one of two.
    recorded: dict[str, Any] = {
        "verdict_version": VERDICT_VERSION,
        "producer": _PROG,
        "scenario": scenario or None,
        "outcome": outcome,
        "exit_code": exit_code,
        "tables_compared": len(diff.tables),
        "tables_differing": len(diff.differing),
        "total_differences": diff.total_differences,
        "run_id": _provenance_field(cobol_manifest, "run_id"),
        "seed_marker_sha256": _attestation_field(
            cobol_manifest, "seed_marker_sha256"
        ),
        "scenario_file_sha256": _provenance_field(
            cobol_manifest, "scenario_file_sha256"
        ),
        "frozen_schema_sha256": _provenance_field(
            cobol_manifest, "frozen_schema_sha256"
        ),
        "cobol_manifest_sha256": (
            _manifest_fingerprint(left) if cobol_manifest is not None else None
        ),
        "python_manifest_sha256": (
            _manifest_fingerprint(right) if python_manifest is not None else None
        ),
        "report": str(report_path) if report_path is not None else None,
        "report_sha256": report_digest,
    }

    # Rebuilt key by key in the declared order rather than returned as assembled, so
    # the published artifact's shape is the constant and cannot drift from it.
    verdict = {key: recorded[key] for key in VERDICT_KEYS}
    unexpected = set(recorded) - set(VERDICT_KEYS)
    if unexpected:  # pragma: no cover - a coding error, not an input
        raise DiffStatesError(
            f"the verdict manifest was built with {len(unexpected)} key(s) "
            f"{VERDICT_KEYS} does not declare: "
            f"{', '.join(sorted(unexpected))}"
        )
    return verdict


def write_verdict(verdict: Mapping[str, Any], path: Path | str) -> Path:
    """Write the verdict manifest, atomically and privately.

    Args:
        verdict: The manifest, as built by `build_verdict`.
        path: Where to write it. Parent directories are created, mode 0700.

    Returns:
        The path written.

    Raises:
        ReportPathError: The file could not be written.
    """
    target = Path(path)
    try:
        _make_output_directory(target.parent)
    except OSError as exc:
        raise ReportPathError(
            f"could not create the directory for the verdict manifest "
            f"{target}: {exc}"
        ) from exc

    # `sort_keys` is deliberately OFF: `VERDICT_KEYS` order is the published order,
    # and it groups the outcome, the counts and the provenance rather than
    # alphabetising them apart.
    text = json.dumps(dict(verdict), indent=2, sort_keys=False) + "\n"
    temporary = target.parent / f"{TEMP_PREFIX}{target.stem}{_VERDICT_TEMP_SUFFIX}"
    try:
        _write_text_securely(text, target, temporary)
    except OSError as exc:
        raise ReportPathError(
            f"could not write the verdict manifest to {target}: {exc}"
        ) from exc
    return target


def _report_digest_or_none(report_path: Path | None) -> str | None:
    """Return the report file's SHA-256, or None when it cannot be taken.

    Args:
        report_path: The report written, or None when there is none.

    Returns:
        The digest, or None. NEVER raises: the digest binds the summary's pointer
        and the verdict manifest's `report_sha256` to the report's bytes, and a
        digest that cannot be taken must not turn a completed comparison into an
        error. The failure is reported on stderr instead.
    """
    if report_path is None:
        return None
    try:
        return _file_digest(report_path)
    except ManifestError as exc:
        # The file is there but could not be read back, so the pointer cannot be
        # bound to its bytes. Reported, not fatal: the verdict does not depend on
        # the digest.
        _warn(str(exc))
        return None


def publish_verdict(
    diff: TreeDiff,
    *,
    outcome: str,
    exit_code: int,
    scenario: str | None,
    manifests: tuple[Mapping[str, Any], Mapping[str, Any]] | None,
    left: Path,
    right: Path,
    report_path: Path | None,
    report_digest: str | None,
) -> Path | None:
    """Build and publish the verdict manifest, reporting rather than raising.

    A comparison that completed has already produced its finding, and the exit
    status carries it. A verdict manifest that cannot be written must therefore be
    REPORTED loudly - no parity may be claimed without
    it, which is the intended consequence - but must not turn a completed
    comparison into `EX_ERROR`, because that would lose the finding itself.

    Args:
        diff: The completed comparison.
        outcome: `OUTCOME_IDENTICAL` or `OUTCOME_DIFFERENT`.
        exit_code: The status this run will exit with.
        scenario: The scenario name.
        manifests: The two verified manifests, or None.
        left: The COBOL tree.
        right: The Python tree.
        report_path: Where the report was written, or None.
        report_digest: The report's SHA-256, or None.

    Returns:
        The path published, or None when there was nowhere to put it or it could
        not be written.
    """
    target = verdict_path_for(report_path)
    if target is None:
        _warn(
            f"no verdict manifest was published: no --out was given, so there "
            f"is no output directory to put {VERDICT_FILENAME} in. "
            f"No parity may be reported from this run."
        )
        return None
    try:
        verdict = build_verdict(
            diff,
            outcome=outcome,
            exit_code=exit_code,
            scenario=scenario,
            manifests=manifests,
            left=left,
            right=right,
            report_path=report_path,
            report_digest=report_digest,
        )
        written = write_verdict(verdict, target)
    except (ReportPathError, DiffStatesError) as exc:
        _warn(
            f"{exc}. The comparison itself COMPLETED and its exit status is "
            f"unaffected, but with no {VERDICT_FILENAME} this run cannot be "
            f"reported as protocol evidence."
        )
        return None
    _progress(f"{_PROG}: verdict {outcome} published to {written}")
    return written


_SUMMARY_HEADER: Final[str] = "difference(s) found; values withheld from"


def summarise(
    diff: TreeDiff,
    *,
    report_path: Path | None,
    report_digest: str | None = None,
) -> str:
    """Render a value-free summary of a comparison, for stdout.

    Carries no accounting value of any kind: no primary key, no column
    content, no side-by-side figure. Only table names, column names,
    finding kinds and counts, all of which are frozen public metadata.

    THIS IS THE ONLY THING STDOUT EVER CARRIES for a non-empty diff. See THE
    OPERATOR SUMMARY block above: the values live in the 0600 report file on
    every path, including the one where no `--out` was given.

    Args:
        diff: The finished comparison. Read only; nothing branches on the
            result of this function.
        report_path: Where the full report was written, or None when it could
            not be written at all.
        report_digest: The report file's SHA-256, which binds the pointer to
            the bytes a reader will open (rule R-6). None when there is no
            file, or when it could not be read back.

    Returns:
        The summary, one line per differing table plus a header and a pointer, each line
            terminated with a single LF.
    """
    if diff.is_empty:
        return ""

    lines: list[str] = []
    for table in diff.differing:
        parts: list[str] = []
        if not table.in_python:
            parts.append(
                f"{_F_TABLE_MISSING_PYTHON} "
                f"{LABEL_COBOL}_rows={table.cobol_row_count}"
            )
        if not table.in_cobol:
            parts.append(
                f"{_F_TABLE_MISSING_COBOL} "
                f"{LABEL_PYTHON}_rows={table.python_row_count}"
            )
        if table.columns_differ:
            parts.append(
                f"{_F_COLUMNS}="
                f"{len(table.cobol_columns)}/{len(table.python_columns)}"
            )
            parts.append(_F_COLUMNS_SKIPPED)
        if table.row_count_differs:
            parts.append(
                f"{_F_ROW_COUNT}="
                f"{table.cobol_row_count}/{table.python_row_count}"
            )
        if table.key_types_differ:
            parts.append(
                f"{_F_KEY_TYPE_MISMATCH}="
                f"{','.join(table.cobol_key_types)}/"
                f"{','.join(table.python_key_types)}"
            )
        if table.missing_in_python:
            parts.append(
                f"{_F_MISSING_PYTHON}={len(table.missing_in_python)}"
            )
        if table.missing_in_cobol:
            parts.append(
                f"{_F_MISSING_COBOL}={len(table.missing_in_cobol)}"
            )
        if table.value_differences:
            # The COLUMN names, de-duplicated and in first-seen order - the single most
            # useful pointer into the protected file, and frozen schema metadata rather
            # than data.
            columns: list[str] = []
            for row in table.value_differences:
                for value in row.values:
                    label = f"col[{value.ordinal}] {value.column}"
                    if label not in columns:
                        columns.append(label)
            parts.append(
                f"differing_rows={len(table.value_differences)}"
            )
            parts.append(f"columns={'; '.join(columns)}")
        lines.append(_join(table.table, *parts))

    if report_path is None:
        # The fallback ALSO failed - see main. The finding below is intact;
        # only the values are gone, and stderr says why.
        pointer = (
            "the differing values could NOT be preserved: see the error on "
            "stderr. Re-run with --out FILE pointing somewhere writable."
        )
    elif report_digest is None:
        pointer = f"the differing values are in {report_path} (mode 0600)"
    else:
        # THE POINTER IS BOUND TO THE BYTES (rule R-6's requirement
        # applied to this artifact as well as to the manifests).
        pointer = (
            f"the differing values are in {report_path} (mode 0600, "
            f"sha256={report_digest})"
        )
    header = _join(
        f"{diff.total_differences} {_SUMMARY_HEADER} stdout",
        f"tables={len(diff.differing)}/{len(diff.tables)}",
        pointer,
    )
    return "".join(f"{line}\n" for line in (header, *lines))


# Every diagnostic goes to STDERR. stdout carries the verdict and nothing else, so that
# a passing run leaves stdout at zero bytes.

_EPILOGUE: Final[str] = f"""\
the two trees
  positionally, the form the recipe in harness/docker-compose.yml uses:
      {_PROG} /out/{LABEL_COBOL}.norm /out/{LABEL_PYTHON}.norm
  by name:
      {_PROG} --{LABEL_COBOL} DIR --{LABEL_PYTHON} DIR
  composed from the scenario, deriving both trees and the report path:
      {_PROG} --scenario NAME [--out-dir DIR]
      reads  DIR/NAME/{LABEL_COBOL}{NORMALIZED_SUFFIX}/<TABLE>.json
             DIR/NAME/{LABEL_PYTHON}{NORMALIZED_SUFFIX}/<TABLE>.json
      writes DIR/NAME/{DIFF_FILENAME}   (DIR defaults to ${_ENV_OUT})

which tables - a selector is REQUIRED
  --scenario-file FILE   the scenario's affected-table list, in its order.
                         This is the protocol: bounding the comparison by
                         the scenario is what keeps the menu-exit rewrite
                         at [general/general.cbl:L656-L691] from failing an
                         otherwise correct run. There is deliberately NO
                         ignore-list in this tool (rule R-4).
  --tables A,B           an explicit list, in the order given.
  --all-tables           the union of what the two trees hold, ASCII
                         order. A table present in only one tree is a
                         DIFFERENCE, never a skip. A DEBUGGING AID.
  none of the three      REFUSED: a verdict whose scope is implicit is not
                         evidence (rule R-6).

both trees must declare themselves complete
  each must carry {MANIFEST_FILENAME}, which
  [harness/normalize.py] writes LAST, and the two must name the SAME
  scenario. Every
  declared table must be present with the digest the manifest records, and
  no undeclared dump may be there. This is not bookkeeping: two PARTIAL
  captures can produce an EMPTY diff over the tables that happen to be in
  both, and an empty diff is the pass condition. Every requested table must
  also appear in both manifests, so a dump bounded by one list and a
  comparison bounded by another is reported rather than discovered as a
  missing file. --allow-unmanifested waives all of it and forfeits the
  claim that the verdict is evidence.

both captures must attest a successful run, and both must not be empty
  a manifest carries the run attestation [harness/dump_tables.py] read
  from the runner's own status record, and a capture that does not attest
  status 0 is REFUSED. So is a comparison in which every table is empty
  on BOTH sides. Neither refusal is fussiness: with no fixtures and no
  compiled oracle the seed, the COBOL run and the Python run all exit
  non-zero and the dump, normalise and comparison stages then exit 0
  apiece and report "identical" -- a pass certified over two empty
  captures. An individual empty table is ordinary and is never refused;
  a scenario whose expected end state really is all-empty declares
  `expect_empty_state: true' and is compared on that declaration.
  --allow-unattested waives both and forfeits the same claim.
  The ten stages are driven in order -- by hand as README section 8
  sets out, or composed by [tests/conftest.py] -- and stopped at the
  first non-zero, which is the reason neither refusal should ever fire
  in a protocol run.

exit codes
  0  identical           stdout is EMPTY - that is the pass condition
  1  difference found    a value-free summary is on stdout, naming the
                         0600 report file that holds the values and its
                         SHA-256; no value ever reaches stdout
  2  cannot compare      a diagnosis is on stderr; NEVER reported as 0

with --out, a passing run writes a ZERO-BYTE file, so the evidence can
distinguish "compared, and identical" from "never compared". Any report
already at that path is DELETED before the comparison begins, so a stale
zero-byte file from an earlier passing run cannot survive an error path
and be read as proof that this run passed. Afterwards: empty means
compared and identical, non-empty means differences, ABSENT means no
comparison was completed.

the comparison is EXACT: no tolerance, no epsilon, no case- or
whitespace-insensitive compare, no numeric coercion, and no ignore-list.
By this point [harness/normalize.py] has canonicalised character padding,
decimal scale and date text, so anything left is a real behavioural
difference.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    `allow_abbrev=False`, so `--out` and `--out-dir` can never be confused with one
    another and no abbreviation of any option is silently accepted.

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
            "comparison could not be performed. Stage 10 of the ten-stage "
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
            f"in harness/docker-compose.yml uses. Equivalent to "
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
        "--all-in-scope",
        action="store_true",
        help=(
            "THE PROTOCOL. Compare all 22 in-scope tables, whatever the "
            "scenario declares it affects. May be combined with "
            "--scenario-file, which then supplies only the declared-effect "
            "gate; it is mutually exclusive with --tables. Both cycles "
            "perform the menu's own `overrewrite.` "
            "[general/general.cbl:L656-L672] - SYSTEM-REC under key 1, "
            "SYSDEFLT-REC under key 2, SYSTOT-REC under key 4, reproduced by "
            "acas_posting/cli/args.py::overrewrite - so those rows are "
            "comparable rather than a source of false failure, and a "
            "comparison that omitted them could report an empty diff while "
            "the run date, the allocators, the flags, the defaults or the "
            "period totals differed."
        ),
    )
    parser.add_argument(
        "--scenario-file",
        metavar="FILE",
        help=(
            "the scenario definition. Read for the declared-effect gate that "
            "refuses an all-empty comparison, and - unless --all-in-scope is "
            "also given - NARROWS the comparison to its affected_tables, in "
            "the order it declares them. Narrowing is for debugging: a "
            "comparison bounded by what a scenario EXPECTS to move cannot show "
            "a difference in anything it did not expect to move. Mutually "
            "exclusive with --tables."
        ),
    )
    parser.add_argument(
        "--tables",
        metavar="A,B",
        help=(
            "compare exactly these tables, in this order. For narrowing one "
            "table by hand. Mutually exclusive with --scenario-file and "
            "--all-in-scope."
        ),
    )
    parser.add_argument(
        "--all-tables",
        action="store_true",
        help=(
            "compare the UNION of what the two trees hold instead of a "
            "declared list. A DEBUGGING AID, NOT THE PROTOCOL: it reports "
            "whatever the two captures happen to share, so its scope depends "
            "on how they were taken. Use --all-in-scope, which names the 22 "
            "tables explicitly whatever the captures contain."
        ),
    )
    parser.add_argument(
        "--allow-unattested",
        action="store_true",
        help=(
            "compare captures whose run stage did not attest success. NOT THE "
            "PROTOCOL: harness/dump_tables.py records what the run stage "
            "claimed, and a capture taken after a failed run supports no "
            "verdict -- two such captures produce an EMPTY diff, which is the "
            "pass condition. This flag also waives the refusal of a comparison "
            "in which every table is empty on both sides. Use only when "
            "inspecting a broken run by hand, and do not present the verdict as "
            "evidence (rule R-6)."
        ),
    )
    parser.add_argument(
        "--allow-unmanifested",
        action="store_true",
        help=(
            "compare trees that carry no "
            + MANIFEST_FILENAME
            + ". NOT THE PROTOCOL: that file is written last by the stage "
            "that publishes a tree, so its absence means the stage did not "
            "finish - and two partial captures can produce an EMPTY diff, "
            "which is the pass condition. Use only for a tree assembled by "
            "hand, and do not present the verdict as evidence (rule R-6)."
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
    #  THERE IS DELIBERATELY NO `--stdout-detail` FLAG, AND ADDING ONE WOULD
    #  UNDO THIS MODULE'S PROTECTION. Its effect would be to put every differing
    #  value - live accounting data, each beside its primary key - onto stdout,
    #  which the composed recipe collects as a container log. That is the same
    #  content this module otherwise protects with `O_EXCL`, `O_NOFOLLOW` and
    #  mode 0600, so such a flag would make the protection optional. There is no path
    #  and no option that puts a value on stdout: the detail always goes to a
    #  0600 file - `--out FILE` when one is named, a private fallback
    #  directory otherwise - and stdout always carries the value-free summary
    #  plus that file's path and SHA-256. Nothing in the repository passed the
    #  flag, so no recipe changes with it.
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
        The `cobol` tree, the `python` tree, the scenario name when the composed layout
            was used, and the report path when one was asked for or implied.

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
            f"the form harness/docker-compose.yml uses - or by name "
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
                f"/out/{LABEL_PYTHON}.norm`, the form "
                f"harness/docker-compose.yml uses."
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

    The two normalised suffixes both occur in this repository - the composed layout
    appends `.normalized`, the committed recipe passes `.norm` - so a missing directory
    is most often the other spelling.

    Args:
        directory: The directory that was not there.

    Returns:
        A sentence naming the sibling that does exist, or the empty string.
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
                    f"while the recipe in "
                    f"harness/docker-compose.yml passes "
                    f"`{NORMALIZED_SUFFIXES[1]}` explicitly. Name the two "
                    f"trees directly rather than using --scenario, so it "
                    f"is unambiguous which pair was compared."
                )
    return ""


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the verdict as an exit code.

    Never calls `sys.exit`, so a test fixture can drive it in process and inspect the
    code - argparse's own usage failures included, which are caught and mapped to exit 2
    rather than allowed to escape.

    Args:
        argv: The arguments.

    Returns:
        `EX_IDENTICAL` (0) when the two trees are identical, and stdout is
        left EMPTY; `EX_DIFFERENT` (1) when a real difference was found, with
        a value-free summary on stdout naming the 0600 file that holds the
        values; `EX_ERROR` (2) when the comparison could not be performed,
        with a diagnosis on stderr.
    """
    global _QUIET

    parser = build_parser()
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 for --help and 2 for a usage error.
        code = exc.code
        if code is None or code == 0:
            return EX_IDENTICAL
        return EX_ERROR

    _QUIET = bool(arguments.quiet)
    env: Mapping[str, str] = os.environ

    # Tightened HERE and not at import time.
    os.umask(_OUTPUT_UMASK)

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

    if arguments.all_in_scope and arguments.tables is not None:
        print(
            f"{_PROG}: --all-in-scope and --tables were both given; they are "
            f"alternative ways of naming the scope, so use exactly one. "
            f"--all-in-scope is the protocol; --tables is for narrowing one "
            f"table by hand.",
            file=sys.stderr,
        )
        return EX_ERROR

    if (
        arguments.tables is None
        and arguments.scenario_file is None
        and not arguments.all_tables
        and not arguments.all_in_scope
    ):
        # REFUSED, not defaulted to the union.
        print(
            f"{_PROG}: no table selector was given, so the scope of this "
            f"comparison is undefined. Choose one:\n"
            f"  --all-in-scope                                     "
            f"THE PROTOCOL; all {len(IN_SCOPE)} in-scope tables\n"
            f"  --scenario-file <scenario>.yaml                    "
            f"narrow to the scenario's affected_tables, for debugging\n"
            f"  --tables A,B                                       "
            f"an explicit list, for narrowing by hand\n"
            f"  --all-tables                                       "
            f"the union of both trees, a debugging aid and NOT evidence\n"
            f"An unbounded comparison is refused rather than defaulted "
            f"because a verdict whose scope is implicit is not evidence "
            f"(rule R-6). Use --all-in-scope for evidence: `overrewrite.` "
            f"[general/general.cbl:L656-L672] rewrites SYSTEM-REC, "
            f"SYSDEFLT-REC and SYSTOT-REC, both cycles perform it, and a "
            f"comparison that omitted those rows could report an empty diff "
            f"while they differed.",
            file=sys.stderr,
        )
        return EX_ERROR

    try:
        #  --all-in-scope OUTRANKS the scenario's own list, which is then read
        #  only for the declared-effect gate below. This is what makes the
        #  verdict cover every table the cycle can persist rather than only the
        #  ones the scenario expected to move.
        tables = (
            IN_SCOPE_TABLES
            if arguments.all_in_scope
            else resolve_tables(
                tables=arguments.tables,
                scenario_file=arguments.scenario_file,
            )
        )
    except (DiffStatesError, ValueError) as exc:
        print(f"{_PROG}: {exc}", file=sys.stderr)
        return EX_ERROR

    if report_path is not None:
        try:
            _assert_writable(report_path, env)
            # INVALIDATE THE ACCEPTED OUTPUT NOW, before a dump is read. Both
            # artifacts: a stale verdict manifest is the more dangerous of the two,
            # because it IS this run's published parity claim
            #.
            invalidate_report(report_path)
            stale_verdict = verdict_path_for(report_path)
            if stale_verdict is not None:
                invalidate_verdict(stale_verdict)
        except ReportPathError as exc:
            print(f"{_PROG}: {exc}", file=sys.stderr)
            return EX_ERROR

    manifests: tuple[dict[str, Any], dict[str, Any]] | None = None
    if arguments.allow_unmanifested:
        _progress(
            f"{_PROG}: --allow-unmanifested - neither tree is being checked "
            f"for a {MANIFEST_FILENAME}, so an incomplete capture could be "
            f"compared and two partial captures can produce an EMPTY diff. "
            f"The verdict below is NOT protocol evidence (rule R-6)."
        )
    else:
        try:
            # --allow-unattested reaches the identity gate too: a capture whose run
            # stage published nothing carries no run id and no seed marker by
            # construction, so enforcing their PRESENCE here would make that waiver
            # unusable. Their EQUALITY is still enforced.
            manifests = verify_trees(
                left,
                right,
                require_identity=not bool(arguments.allow_unattested),
            )
        except MissingTreeError as exc:
            print(
                f"{_PROG}: {exc}{_describe_missing_tree(left)}",
                file=sys.stderr,
            )
            return EX_ERROR
        #  EVERY REFUSAL FROM THE VERIFICATION STAGE IS EXIT 2, WITHOUT EXCEPTION.
        #
        #  `DiffStatesError` and not `ManifestError`, and the difference is the whole
        #  point: verification does not only read the two manifests, it also DISCOVERS
        #  what each tree holds, and `discover_tables` refuses an unexpected
        #  `<NAME>.json` through `table_spec` - `TableNotInScopeError` for one of the
        #  eleven out-of-scope tables, `UnknownTableError` for a name that is not a
        #  table of the frozen schema at all. Neither is a `ManifestError`, so with
        #  only that clause here both escaped `main` as an unhandled traceback and the
        #  interpreter exited 1 -- the ONE status this tool reserves for "the two states
        #  really differ" (`EX_DIFFERENT`). A corrupt or mixed artifact tree would then
        #  have been reported to any caller keying on the status as a parity FAILURE,
        #  which is a finding about the migration rather than about the evidence, and a
        #  traceback naming internal paths and line numbers is not a diagnosis an
        #  operator can act on.
        #
        #  `DiffStatesError` is this module's documented root - "Base class for every
        #  failure this module reports. Always exit 2" - so catching it here makes the
        #  code match the contract for every present and future sibling instead of for
        #  an enumerated two. The message is the exception's own, which already names
        #  the offending table and says why it is refused.
        except DiffStatesError as exc:
            print(f"{_PROG}: {exc}", file=sys.stderr)
            return EX_ERROR

        # A requested table that neither side ever captured is a harness malfunction,
        # not a difference - and it must not be discovered halfway through as a missing
        # file.
        if tables is not None:
            declared = set(manifest_tables(manifests[0])) & set(
                manifest_tables(manifests[1])
            )
            absent = [table for table in tables if table not in declared]
            if absent:
                print(
                    f"{_PROG}: {len(absent)} requested table(s) were never "
                    f"captured on both sides: {', '.join(absent)}. The two "
                    f"manifests declare "
                    f"{len(manifest_tables(manifests[0]))} and "
                    f"{len(manifest_tables(manifests[1]))} table(s) "
                    f"respectively. harness/dump_tables.py writes a file "
                    f"for every table it is asked to dump whatever its row "
                    f"count - an empty table still gets \"row_count\": 0 - "
                    f"so a table absent from a manifest was never "
                    f"requested of the dump stage, which means the dump and "
                    f"the comparison were bounded by different lists. Pass "
                    f"the SAME --scenario-file to both stages.",
                    file=sys.stderr,
                )
                return EX_ERROR

        # THE TWO GATES THAT MAKE THE PASS CONDITION MEAN SOMETHING. Both run only
        # when the manifests were verified, because both read them.
        if arguments.allow_unattested:
            _progress(
                f"{_PROG}: --allow-unattested - neither capture is being "
                f"checked against its run status and an all-empty comparison "
                f"is permitted, so a verdict can be produced from runs that "
                f"never happened. The verdict below is NOT protocol evidence "
                f"(rule R-6)."
            )
        else:
            try:
                assert_attested(manifests)
                assert_not_all_empty(
                    manifests,
                    expect_empty=scenario_expects_empty_state(
                        arguments.scenario_file
                    ),
                )
            except ManifestError as exc:
                print(f"{_PROG}: {exc}", file=sys.stderr)
                return EX_ERROR
            except ScenarioFileError as exc:
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
        + (
            f" (manifests agree on scenario "
            f"{manifests[0].get('scenario')!r}, selector "
            f"{manifests[0].get('selector')!r}; "
            f"{LABEL_COBOL} {MANIFEST_FILENAME} "
            f"sha256={_manifest_fingerprint(left)}, "
            f"{LABEL_PYTHON} {MANIFEST_FILENAME} "
            f"sha256={_manifest_fingerprint(right)})"
            if manifests is not None
            else ""
        )
    )

    try:
        diff = diff_trees(
            left, right, tables, allow_raw=bool(arguments.allow_raw)
        )
    except MissingTreeError as exc:
        # The most dangerous input this module can be given, so the message says
        # outright that it is not a pass.
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
        # THE PASS CONDITION. Not one byte on stdout.
        #
        # The verdict manifest is published HERE and not merely implied by the exit
        # status. A zero-byte diff.txt and status 0 cannot be told
        # apart from a run whose report was never written, so the pass states itself:
        # how many tables were compared, the run id both sides carried, and the seed
        # identity they were both seeded from.
        publish_verdict(
            diff,
            outcome=OUTCOME_IDENTICAL,
            exit_code=EX_IDENTICAL,
            scenario=scenario,
            manifests=manifests,
            left=left,
            right=right,
            report_path=report_path,
            report_digest=_report_digest_or_none(report_path),
        )
        _progress(
            f"{_PROG}: identical - {len(diff.tables)} table(s) compared, "
            f"no difference"
        )
        return EX_IDENTICAL

    # THE ONE PLACE THE VALUES ARE WITHHELD, and they are withheld on EVERY
    # path. See THE OPERATOR SUMMARY above `summarise`: the report file keeps
    # every value and is 0600, while stdout - a collected container log in the
    # composed recipe - gets a value-free summary naming the tables, kinds,
    # counts and columns, the report path, and the report's SHA-256. There is
    # no flag that puts a value on stdout and no path on which one appears.
    # The exit code below is identical in every case.
    if report_path is None:
        # No `--out` was given, so the values have nowhere to go yet. They
        # do NOT go to stdout: a private file is created for them instead.
        try:
            report_path = _fallback_report_path()
            write_report(report, report_path)
        except ReportPathError as exc:
            # The values are lost, the FINDING is not. Say so plainly and
            # keep going: the summary below still names every differing
            # table, kind, column and count, and the verdict is unchanged.
            print(f"{_PROG}: {exc}", file=sys.stderr)
            report_path = None

    report_digest = _report_digest_or_none(report_path)

    # Published on the DIFFERENT outcome too. A difference is
    # evidence: it is what an ambiguity resolution cites when the compiled oracle is
    # interrogated, so it gets the same machine-readable artifact the pass gets.
    publish_verdict(
        diff,
        outcome=OUTCOME_DIFFERENT,
        exit_code=EX_DIFFERENT,
        scenario=scenario,
        manifests=manifests,
        left=left,
        right=right,
        report_path=report_path,
        report_digest=report_digest,
    )

    sys.stdout.write(
        summarise(diff, report_path=report_path, report_digest=report_digest)
    )
    _progress(
        f"{_PROG}: {diff.total_differences} difference(s) across "
        f"{len(diff.differing)} of {len(diff.tables)} table(s). A "
        f"non-empty diff is a real behavioural difference, never an "
        f"artefact of the comparison (Agent Action Plan section 0.6.6): "
        f"interrogate the compiled oracle, and record the resolution in "
        f"the migration's ambiguity register."
    )
    return EX_DIFFERENT


if __name__ == "__main__":
    raise SystemExit(main())
