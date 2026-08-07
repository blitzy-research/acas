#!/usr/bin/env python3
# Executable in its own right: the canonical recipe in harness/docker-compose.yml
# names the three state tools by path, and without this line the kernel refuses
# the exec and bash falls back to interpreting the file as a shell script.
"""Canonicalise a dump so that only REAL behavioural differences survive.

Stage 4 of the parity protocol. Reads the raw `<TABLE>.json` dumps
`harness/dump_tables.py` wrote and rewrites them into a `.normalized` tree,
leaving the source untouched.

Exactly three canonicalisations, each answering a difference that is
representational rather than behavioural:

* fixed-character columns are compared without trailing spaces, because the
  bridge widens some fields on the way to the column - a ledger name declared 24
  characters wide becomes a 32-character host variable and a 32-character column
  [common/nominalMT.cbl:L299], so the padding differs while the value does not.
  MEASURED CAVEAT, worth knowing before treating this job as load-bearing:
  through the driver this harness uses it rarely has anything to do, because
  MariaDB strips trailing spaces from a `char` column on READ unless
  `PAD_CHAR_TO_FULL_LENGTH` is set - a value stored as "Zed trailing  " already
  arrives as "Zed trailing", and "  " already arrives as "". So the padding
  difference the width drift produces is usually gone before the dump is written.
  The job is kept, and deliberately: the drift at Agent Action Plan section 0.6.2
  is real, that server behaviour is a setting rather than a guarantee (and
  [harness/Dockerfile.mariadb] declines to set the mode either way, because
  choosing it would make the server a party to the comparison), and a capture
  taken through any driver or server that DOES preserve padding must still
  compare equal. It is a guard that mostly finds nothing, which is not the same
  as a guard that does nothing;
* decimal columns are rendered at the scale the schema declares, so a value
  stored at two decimal places compares equal however a driver formatted it;
* date text is rendered in one form, because the schema stores two-digit and
  four-digit year spellings side by side.

The ten stages are defined in [harness/parity_stages.sh] and published by
[harness/run_parity.sh] through `--print-stages`; the Compose recipe restates
them at [harness/docker-compose.yml "STAGES."]. This module owns two of them:
stage 4 normalises the COBOL dump and stage 8 the Python dump. The AAP's eight
logical stages (section 0.3.2) map onto those ten by making both normalisations
and the publication check explicit rather than implied; "stage 8" in any older
prose means today's stage 10, the diff.

It reads one directory of `<TABLE>.json` files, as `dump_tables.py` wrote
them, and writes one directory of `<TABLE>.json` files with the same shape
and only the VALUES canonicalised. It opens no database link, needs no
driver, invokes no COBOL and imports nothing from the shipped Python
package.

THE ONE SENTENCE THAT DEFINES THIS MODULE - AND ITS HARD LIMIT
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping, MutableSequence, Sequence
from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Final

# One entry per in-scope table: its single-column primary key, its declared column count
# and the `CREATE TABLE` line of mysql/ACASDB.sql it was read from.


@dataclass(frozen=True, slots=True)
class TableSpec:
    """One in-scope table's frozen-schema facts.

    Attributes:
        primary_key: The single column the dump was ordered by.
        column_count: The declared number of columns, asserted against the parsed
            schema. A cheap, strong tripwire on tampering.
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

# The eleven tables the posting cycle never touches, listed by NAME so a stray dump is
# refused with an explanation rather than with a not-found.
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

# Deterministic iteration order for the default selection: the table names, ascending.
IN_SCOPE_TABLES: Final[tuple[str, ...]] = tuple(sorted(IN_SCOPE))

# 513, the sum of the twenty-two declared column counts above, which is also the number
# of in-scope columns mysql/ACASDB.sql declares.
EXPECTED_TOTAL_COLUMNS: Final[int] = sum(
    spec.column_count for spec in IN_SCOPE.values()
)

EXPECTED_SCHEMA_TABLES: Final[int] = 33

# The two sides of the comparison. Both the PATH and the MANIFEST record which side a
# capture is: the path composes <out-dir>/<scenario>/<side>/, and `side` is one of
# `MANIFEST_KEYS`, inherited here verbatim from the dump manifest along with the run
# attestation. What carries no side is the per-table dump OBJECT (`DUMP_KEYS`), and those
# are the only files harness/diff_states.py compares -- so the manifest's copy cannot
# influence a verdict. Stated in full because an earlier revision of this comment claimed
# the content never records it, which the manifest contradicts.
SIDES: Final[tuple[str, ...]] = ("cobol", "python")

# The dump object's key order, identical to harness/dump_tables.py. Asserted on input
# AND on output: the key order is part of the byte-identical guarantee (rule R-6).
DUMP_KEYS: Final[tuple[str, ...]] = (
    "table",
    "primary_key",
    "columns",
    "row_count",
    "rows",
)


# JOB 3's COLUMN ALLOW-LIST (rule R-5) FIVE columns, named explicitly.


@dataclass(frozen=True, slots=True)
class DateTextSpec:
    """The canonical shape of one allow-listed date-text column.

    Attributes:
        form: `"date"` for the eight-character `NN/NN/NN` layout, `"period"` for the
            four-character all-digit layout.
        width: The `char(n)` width the frozen schema declares, asserted against the
            parsed schema so the pair cannot drift.
        schema_line: The declaring line of `mysql/ACASDB.sql`.
        copybook: The COBOL declaration the form was read from.
    """

    form: str
    width: int
    schema_line: int
    copybook: str


DATE_TEXT_COLUMNS: Final[Mapping[tuple[str, str], DateTextSpec]] = {
    ("GLPOSTING-REC", "POST-DAT"): DateTextSpec(
        "date", 8, 158, "copybooks/wspost.cob:L18"
    ),
    # The internal IRS posting date - the same eight-character form, and the field the
    # three bridge-only components are derived from (anomaly 7.
    ("IRSPOSTING-REC", "POST4-DAT"): DateTextSpec(
        "date", 8, 277, "copybooks/irswspost.cob:L11"
    ),
    ("PSIRSPOST-REC", "IRS-POST-DAT"): DateTextSpec(
        "date", 8, 369, "copybooks/wspost-irs.cob:L18"
    ),
    ("SALEDGER-REC", "SALES-STATS-DATE"): DateTextSpec(
        "period", 4, 981, "copybooks/wssl.cob:L64"
    ),
    ("SYSTEM-REC", "STATS-DATE-PERIOD"): DateTextSpec(
        "period", 4, 1236, "copybooks/wssystem.cob:L145"
    ),
}

# DELIBERATE EXCLUSIONS. Every one of these has the width of an allow-listed column and
# is NOT a date or a period.
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
        "recorded by harness/dump_tables.py."
    ),
    ("DELIVERY-REC", "DELIV-KEY"): (
        "char(8) [mysql/ACASDB.sql:L57] and the sixth char(8) column of "
        "the schema, but `DELIVERY-REC` is one of the eleven "
        "OUT-OF-SCOPE tables of Agent Action Plan section 0.2.2, so no "
        "dump of it ever reaches this module."
    ),
}

# The canonical eight-character date-text shape: two digits, a solidus, two digits, a
# solidus, two digits.
_DATE_TEXT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\A(?P<first>[0-9]{2})/(?P<second>[0-9]{2})/(?P<third>[0-9]{2})\Z"
)

# The canonical four-character period shape: exactly four ASCII digits, because the
# copybooks declare `pic 9(4)`.
_PERIOD_TEXT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\A(?P<digits>[0-9]{4})\Z"
)

_DATE_TEXT_SEPARATOR: Final[str] = "/"

_FORM_DATE: Final[str] = "date"
_FORM_PERIOD: Final[str] = "period"


KIND_CHAR: Final[str] = "char"
KIND_DECIMAL: Final[str] = "decimal"
KIND_INTEGER: Final[str] = "integer"

# The integer widths the schema uses.
_INTEGER_TYPES: Final[frozenset[str]] = frozenset(
    {"tinyint", "smallint", "mediumint", "int", "integer", "bigint"}
)

# Declared types that would break either the numeric policy of rule R-2 or the
# determinism argument of Agent Action Plan section 0.6.6.
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


# The same 80+ band the sibling harness tools use harness/dump_tables.py, so one
# pipeline log reads as one family. 82 - database - is deliberately absent.

EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 80
EX_PRECONDITION: Final[int] = 81
EX_SCOPE: Final[int] = 83
EX_DRIFT: Final[int] = 84
EX_NUMERIC: Final[int] = 85
EX_WRITE: Final[int] = 86

_ENV_REPO: Final[str] = "ACAS_REPO"
_ENV_OUT: Final[str] = "ACAS_OUT"

# The frozen schema, relative to the read-only checkout. Read, never written (rule R-3).
_SCHEMA_RELPATH: Final[str] = "mysql/ACASDB.sql"

_NORMALIZED_SUFFIX: Final[str] = ".normalized"

# Where a defaulted findings report goes: alongside `$ACAS_OUT/reset/`, which
# harness/reset_db.sh documents as never being part of a comparison.
_REPORT_SUBDIR: Final[str] = "normalize"
_REPORT_FILENAME: Final[str] = "date-text-findings.txt"

# The defaulted report file is named for the source directory - so the two invocations
# the harness/docker-compose.yml "STAGES." recipe makes, stages 4 and 8, produce
# `cobol-date-text-findings.txt` and `python-date-text-findings.txt` rather than one
# overwriting the other, and both sides' questions reach the oracle.
_REPORT_LABEL_RE: Final[re.Pattern[str]] = re.compile(r"[0-9A-Za-z]+")
_REPORT_DEFAULT_LABEL: Final[str] = "dump"

# JSON serialisation, pinned to `dump_tables.py`'s parameters exactly
# harness/dump_tables.py so a normalised file differs from its input in VALUES only.
_JSON_INDENT: Final[int] = 2
_JSON_SEPARATORS: Final[tuple[str, str]] = (",", ": ")
_DUMP_SUFFIX: Final[str] = ".json"
_TEMP_PREFIX: Final[str] = "."
_TEMP_SUFFIX: Final[str] = ".json.tmp"

# The findings report is text, not JSON, so it stages under its own suffix.
_REPORT_TEMP_SUFFIX: Final[str] = ".txt.tmp"

# SECURE OUTPUT (CWE-59 symlink following, CWE-367 TOCTOU, CWE-312 cleartext storage,
# CWE-732 over-permissive files) A normalised dump holds exactly what the raw dump held
# - every value of every row of the accounting tables - with only the RENDERING
# canonicalised.

_OUTPUT_FILE_MODE: Final[int] = 0o600

_OUTPUT_DIR_MODE: Final[int] = 0o700

_OUTPUT_UMASK: Final[int] = 0o077

#: `O_NOFOLLOW` where the platform has it; 0 leaves the flag word unchanged rather than
#: making the module unimportable where it is absent.
_O_NOFOLLOW: Final[int] = getattr(os, "O_NOFOLLOW", 0)


def _write_text_securely(text: str, target: Path, staging: Path) -> None:
    """Write `text` to `target` atomically, privately, and without following.

    Args:
        text: The exact bytes-to-be, already assembled. Written in one call, so no
            reader observes a partial file.
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
            # NOT SWALLOWED SILENTLY. `EBADF` is the expected, uninteresting
            # case - the context manager above already closed the descriptor.
            # Anything else means the descriptor could not be released, which
            # is REPORTED: a cleanup failure that leaves no trace is how a
            # leaked descriptor or a full filesystem stays invisible. The
            # original failure still propagates, unchanged, from the `raise`
            # below.
            if close_error.errno != errno.EBADF:
                print(
                    f"harness/normalize.py: warning: could not close the "
                    f"staging descriptor for {staging} while handling an "
                    f"earlier failure: errno {close_error.errno} "
                    f"({os.strerror(close_error.errno or 0)})",
                    file=sys.stderr,
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

MANIFEST_FILENAME: Final[str] = "_manifest.json"
# Version 2 added `attestation`; version 3 added `provenance` and widened
# `attestation`, in step with harness/dump_tables.py. An older tree is refused rather
# than read: the point of these keys is that their absence cannot be mistaken for a
# claim, so silently tolerating a manifest that predates them would defeat them.
MANIFEST_VERSION: Final[int] = 3
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

# The attestation's keys, in the order harness/dump_tables.py writes them. This stage
# CARRIES the object through unread: what the run stage claimed is a fact about the
# run, not about the canonicalisation, so re-deriving or re-judging it here would let
# the two stages disagree about one run.
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

# =============================================================================
# PROVENANCE AND LINEAGE (findings F-34, F-36)
#
# The provenance block is CARRIED THROUGH from the raw manifest for the same reason the
# attestation is: what a capture was taken from is a fact about the capture, and
# re-deriving it here would let two stages disagree about one run.
#
# One field is NOT carried, and it is the point of this comment.
# `source_manifest_sha256' is the digest of the manifest THIS TREE WAS DERIVED FROM,
# and only this stage can know it. Without it there was NO LINEAGE AT ALL between a raw
# tree and its normalised form: this tool could be pointed at raw tree A and publish a
# normalised tree whose manifest inherited A's scenario, side and attestation, and
# nothing in the result recorded WHICH raw bytes it canonicalised. A re-run of the
# dump stage between the two normalisations, a hand edit of a dump, a --src pointing at
# the other side's tree -- each produced a normalised tree that looked exactly right
# and described a capture it was not made from.
#
# So the digest of the source manifest is recorded here and REQUIRED downstream:
# harness/diff_states.py refuses a normalised tree whose recorded lineage does not
# match the raw manifest beside it.
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
MANIFEST_STAGE_RAW: Final[str] = "raw"
MANIFEST_STAGE_NORMALIZED: Final[str] = "normalized"
SELECTOR_INHERITED: Final[str] = "inherited"
_PRODUCER: Final[str] = "harness/normalize.py"

# The reserved file-name namespace inside a published tree.
_RESERVED_PREFIX: Final[str] = "_"

_STAGING_SUFFIX: Final[str] = ".staging"
_DIGEST_BLOCK: Final[int] = 1 << 16

# An explicit arithmetic context for job 2, so a `quantize` here can never depend on the
# caller's ambient decimal settings.
_DECIMAL_CONTEXT: Final[Context] = Context(prec=60)

# Only the ASCII space is padding (job 1). Named so the intent cannot be widened by
# accident into a general whitespace removal.
_PAD_CHARACTER: Final[str] = " "


# stderr only, and never a byte of it inside a normalised file (rule R-6).
# `normalize_dump` never calls this.

_QUIET: bool = False


def _progress(message: str) -> None:
    """Write one progress line to stderr unless `--quiet` was given.

    Args:
        message: The line to write, without a trailing newline.
    """
    if not _QUIET:
        print(message, file=sys.stderr)


# ERRORS One class per failure mode, each mapped to exactly one exit code, so a caller
# driving `main` in process and a caller catching an exception see the same taxonomy.


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
    """A dump object does not have the shape `dump_tables.py` writes."""


class NumericPolicyError(NormalizeError, TypeError):
    """A value would have required binary floating point. Exit code 85.

    Rule R-2 forbids binary floating point outright, so the value is refused rather than
    coerced.
    """


class UnexpectedValueTypeError(NormalizeError, TypeError):
    """A value is of a type no in-scope column can hold. Exit code 85."""


class UnexpectedNullError(NormalizeError, ValueError):
    """A dump carries a JSON `null`. Exit code 85.

    Every column of the frozen schema is declared `NOT NULL`, and Agent Action Plan
    section 0.6.2 explains why: each bridge load paragraph initialises the host-variable
    group, "so unset fields become zero or space rather than SQL NULL".
    """


class DecimalScaleError(NormalizeError, ValueError):
    """A decimal value carries more decimal places than its column. 85.

    Job 2's information-loss guard. Quantising such a value away would make two
    genuinely different stored values compare equal, which the module docstring's hard
    limit forbids.
    """


class DumpReadError(NormalizeError, OSError):
    """A dump file could not be read or parsed as JSON. Exit code 81."""


class DumpWriteError(NormalizeError, OSError):
    """A normalised file could not be written or moved. Exit code 86."""


class ManifestError(NormalizeError, ValueError):
    """A tree's completeness manifest is missing, unreadable or disagrees.

    Distinct from `DumpReadError`.
    """


class OutputPathError(NormalizeError, ValueError):
    """The destination is not somewhere this tool may write."""


class ReportPathError(NormalizeError, ValueError):
    """The findings report would land inside a compared tree. Code 80."""


# `mysql/ACASDB.sql` is the source of truth, for three reasons that all matter.


@dataclass(frozen=True, slots=True)
class ColumnType:
    """One column's declared type, as `mysql/ACASDB.sql` writes it.

    Attributes:
        name: The column name, spelled exactly as the schema spells it, hyphens
            included.
        kind: `KIND_CHAR`, `KIND_DECIMAL` or `KIND_INTEGER`.
        sql_type: The declaration verbatim, for error messages - for example `char(32)`,
            `decimal(10,2)` or `int(8) unsigned`.
        width: The `char(n)` length, or `None` for the other kinds.
        precision: The `decimal(p,s)` precision, or `None`.
        scale: The `decimal(p,s)` scale, or `None`. Job 2 renders to exactly this many
            places and never assumes two.
        unsigned: Whether the declaration carries `unsigned`. Recorded for completeness;
            this module never alters a sign (rule R-4).
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


_CREATE_TABLE_RE: Final[re.Pattern[str]] = re.compile(
    r"\ACREATE\s+TABLE\s+`(?P<table>[^`]+)`\s*\(\s*\Z", re.IGNORECASE
)

_END_TABLE_RE: Final[re.Pattern[str]] = re.compile(r"\A\)[^;]*;\s*\Z")

# A column definition. Identifiers are BACKTICK-QUOTED and HYPHENATED, so the backticks
# are what is matched - a bare-word parser would split `LEDGER-NAME` into two tokens.
_COLUMN_RE: Final[re.Pattern[str]] = re.compile(
    r"\A\s+`(?P<name>[^`]+)`\s+(?P<declaration>.+?),\s*\Z"
)

# The type at the head of a declaration, with its optional arguments and an optional
# `unsigned`.
_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"\A(?P<type>[A-Za-z]+)"
    r"(?:\s*\((?P<arguments>[^)]*)\))?"
    r"(?P<tail>.*)\Z",
    re.DOTALL,
)

_PRIMARY_KEY_RE: Final[re.Pattern[str]] = re.compile(
    r"\A\s+PRIMARY\s+KEY\s+\((?P<columns>[^)]*)\)", re.IGNORECASE
)

# Clauses inside a table body that are constraints rather than columns.
_CONSTRAINT_RE: Final[re.Pattern[str]] = re.compile(
    r"\A\s+(PRIMARY\s+KEY|UNIQUE\s+KEY|FULLTEXT\s+KEY|SPATIAL\s+KEY"
    r"|FOREIGN\s+KEY|CONSTRAINT|KEY|INDEX|CHECK)\b",
    re.IGNORECASE,
)


def default_schema_path(env: Mapping[str, str] | None = None) -> Path:
    """Return the frozen schema's path, `$ACAS_REPO/mysql/ACASDB.sql`.

    Args:
        env: The environment to read `ACAS_REPO` from; `os.environ` when omitted. The
            Compose service sets it to `/repo` harness/docker-compose.yml, mounted read-
            only harness/docker-compose.yml.

    Returns:
        `$ACAS_REPO/mysql/ACASDB.sql` when `ACAS_REPO` is set and non-empty, otherwise
            the same relative path resolved against the directory that contains this
            file's parent - that is, the checkout this module was invoked from.
    """
    environment = os.environ if env is None else env
    root = environment.get(_ENV_REPO, "")
    if root:
        return Path(root) / _SCHEMA_RELPATH
    return Path(__file__).resolve().parent.parent / _SCHEMA_RELPATH


def _parse_declaration(
    name: str, declaration: str, line: int
) -> ColumnType:
    """Turn one column declaration into a `ColumnType`.

    Args:
        name: The column name, without its backticks.
        declaration: Everything after the name, without the trailing comma - for example
            `char(32) NOT NULL` or `decimal(10,2) NOT NULL` or `mediumint(5) unsigned
            NOT NULL COMMENT 'Rel.
        line: The declaring line of `mysql/ACASDB.sql`.

    Returns:
        The parsed type.

    Raises:
        SchemaParseError: The declaration is unrecognisable, or names a type that would
            break rule R-2's numeric policy or Agent Action Plan section 0.6.6's
            determinism argument.
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
        # The parenthesised number on an integer type is MySQL's display width and has
        # no effect on the stored value.
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
        SchemaParseError: The arguments are missing or malformed.
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

    Args:
        schema_path: The schema to parse; `default_schema_path()` when omitted. A test
            may point this at a fixture.
        env: The environment used to resolve the default path.

    Returns:
        The column-type map, with 33 tables.

    Raises:
        SchemaFileError: The file could not be read.
        SchemaParseError: The file could not be parsed, does not contain exactly 33
            `CREATE TABLE` statements, or disagrees with `IN_SCOPE` on a column count, a
            primary key or an allow-listed column's declared width.
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
            f"Compose service mounts the checkout at /repo; see "
            f"harness/docker-compose.yml."
        ) from exc

    schema: dict[str, dict[str, ColumnType]] = {}
    primary_keys: dict[str, list[str]] = {}
    current: str | None = None

    for number, raw in enumerate(text.splitlines(), start=1):
        if current is None:
            # Outside a table body. Everything else in the file is ignored on purpose.
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
                f"independently by harness/dump_tables.py and "
                f"harness/reset_db.sh."
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


# The width drift, traced end to end in this checkout: [copybooks/wsledger.cob:L27] 03
# Ledger-Name pic x(24). 24 [common/nominalMT.cbl:L299] 05 HV-LEDGER-NAME PIC X(32).


def canonicalise_char(
    value: object,
    *,
    table: str,
    column: str,
    declared: ColumnType,
) -> str:
    """Job 1: remove trailing ASCII spaces from a fixed-width value.

    TRAILING ONLY, NEVER LEADING. A COBOL alphanumeric `MOVE` is left-justified with
    RIGHT padding, so a leading space is CONTENT.

    Args:
        value: The dumped value. Must be a `str`; a `char` column cannot legitimately
            dump anything else.
        table: The table it came from, for the error message.
        column: The column it came from, for the error message.
        declared: The column's declared type, asserted to be `char(n)` so a caller
            cannot apply job 1 to the wrong class of column.

    Returns:
        The value with its trailing ASCII spaces removed.

    Raises:
        UnexpectedValueTypeError: `value` is not a `str`.
        SchemaParseError: `declared` is not a `char(n)` column, which would mean the
            caller dispatched on something other than the declared type.
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
            f"harness/dump_tables.py renders character data "
            f"as a JSON string exactly as the driver returned it, so "
            f"anything else means the dump is not one this module can "
            f"compare."
        )
    return value.rstrip(_PAD_CHARACTER)


# Agent Action Plan section 0.6.6.

# A decimal literal, anchored.
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

    The value is parsed FROM ITS STRING into an exact `Decimal` - never through a binary
    approximation (rule R-2) - quantised to the declared scale under an explicit context
    and rounding mode, and rendered with `format(value, "f")` so exponent notation can
    never appear.

    Args:
        value: The dumped value. Must be a `str`, because harness/dump_tables.py renders
            every `DECIMAL` as a JSON string.
        table: The table it came from, for the error messages.
        column: The column it came from, for the error messages.
        declared: The column's declared type, which supplies the scale.

    Returns:
        The value rendered at exactly `declared.scale` places.

    Raises:
        NumericPolicyError: `value` is a binary floating-point number, or a `bool`, or
            an `int` - each of which means the dump serialised a decimal as a JSON
            number and so reintroduced binary floating point at the file boundary (rule
            R-2).
        UnexpectedValueTypeError: `value` is of some other type.
        DecimalScaleError: The information-loss guard tripped, or the string is not a
            finite decimal literal.
        SchemaParseError: `declared` is not a `decimal(p,s)` column.
    """
    if declared.kind != KIND_DECIMAL or declared.scale is None:
        raise SchemaParseError(
            f"job 2 applies only to decimal columns, but "
            f"`{table}`.`{column}` is declared {declared.sql_type} "
            f"[{_SCHEMA_RELPATH}:L{declared.line}]."
        )

    if isinstance(value, bool):
        raise NumericPolicyError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries the boolean {value!r}. No column of the "
            f"frozen schema can produce one."
        )

    # THE ACTIVE R-2 GUARD. A binary floating-point value here means `dump_tables.py`
    # was misconfigured, and quietly repairing it would hide that bug.
    if isinstance(value, float):
        raise NumericPolicyError(
            f"`{table}`.`{column}` is declared {declared.sql_type} but "
            f"the dump carries a binary floating-point value ({value!r}). "
            f"No accounting value may pass through binary floating point "
            f"at any point (rule R-2), and a JSON number IS an IEEE-754 "
            f"double in every consumer. "
            f"harness/dump_tables.py renders every DECIMAL "
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


# FIVE allow-listed columns, and nothing else.


@dataclass(frozen=True, slots=True)
class DateTextOutcome:
    """The result of one job 3 canonicalisation.

    Attributes:
        value: The canonical rendering when the value matched its shape,
            or the value UNCHANGED when it did not.
        reason: `None` when the value matched, otherwise the deterministic
            explanation that goes into the findings report.
        category: `None` when the value matched, otherwise one of the four
            `_CATEGORY_*` tokens - the console-safe half of `reason`, which for
            two of the categories quotes bytes of the value itself.
    """

    value: str
    reason: str | None
    category: str | None = None


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
        reason: Why it did not match its canonical shape. May quote bytes of
            `value`, so it belongs only in the 0600 report.
        category: The console-safe classification of `reason`, one of the four
            `_CATEGORY_*` tokens.
    """

    table: str
    column: str
    row_index: int
    value: str
    reason: str
    category: str = ""


def canonicalise_date_text(
    value: object,
    *,
    table: str,
    column: str,
    specification: DateTextSpec,
) -> DateTextOutcome:
    """Job 3: canonicalise the RENDERING of one allow-listed date text.

    `date` `NN/NN/NN` - two digits, a solidus, two digits, a solidus, two digits. The
    layout the bridge slices at (1:2), (4:2) and (7:2)
    [common/irspostingMT.cbl:L982-L987] over the `pic x(8)` field
    [copybooks/wspost.cob:L18].

    Args:
        value: The dumped value, after job 1. Must be a `str`.
        table: The table it came from.
        column: The allow-listed column it came from.
        specification: The column's entry from `DATE_TEXT_COLUMNS`.

    Returns:
        The outcome: the canonical rendering and `None`, or the unchanged value and the
            reason it was not canonical.

    Raises:
        UnexpectedValueTypeError: `value` is not a `str`.
        SchemaParseError: `specification.form` is neither `date` nor `period`.
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
            return DateTextOutcome(
                value, _date_text_reason(value), _date_text_category(value)
            )
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
            return DateTextOutcome(
                value, _period_text_reason(value), _period_text_category(value)
            )
        return DateTextOutcome(match.group("digits"), None)

    raise SchemaParseError(
        f"`{table}`.`{column}` carries the unknown date-text form "
        f"{specification.form!r}. The two forms are "
        f"{_FORM_DATE!r} and {_FORM_PERIOD!r}."
    )


#  THE REASON CATEGORIES. A fixed four-token vocabulary, and the ONLY part of a
#  finding's explanation that may reach a console: two of the four full reasons
#  below quote bytes of the value itself - the separator characters and, by way
#  of the length, its shape - which is live accounting data and belongs in the
#  0600 report alone. `summarise_findings` carries the CATEGORY; `render_report`
#  carries the reason. The classifier is the single place the branch lives, and
#  each reason function dispatches on its result, so the two cannot drift apart.
_CATEGORY_EMPTY: Final[str] = "empty-after-job-1"
_CATEGORY_LENGTH: Final[str] = "wrong-length"
_CATEGORY_SEPARATOR: Final[str] = "unexpected-separator"
_CATEGORY_COMPONENT: Final[str] = "non-canonical-component"


def _date_text_category(value: str) -> str:
    """Classify why an eight-character date text is not canonical.

    Args:
        value: The non-canonical value, after job 1.

    Returns:
        One of the four `_CATEGORY_*` tokens. Carries no byte of `value`, so it
        is safe on a console.
    """
    if not value:
        return _CATEGORY_EMPTY
    if len(value) != 8:
        return _CATEGORY_LENGTH
    if (value[2], value[5]) != (
        _DATE_TEXT_SEPARATOR,
        _DATE_TEXT_SEPARATOR,
    ):
        return _CATEGORY_SEPARATOR
    return _CATEGORY_COMPONENT


def _period_text_category(value: str) -> str:
    """Classify why a four-character period text is not canonical.

    Args:
        value: The non-canonical value, after job 1.

    Returns:
        One of the four `_CATEGORY_*` tokens. Carries no byte of `value`.
    """
    if not value:
        return _CATEGORY_EMPTY
    if len(value) != 4:
        return _CATEGORY_LENGTH
    return _CATEGORY_COMPONENT


def _date_text_reason(value: str) -> str:
    """Explain why an eight-character date text is not canonical.

    The explanation is a function of the value alone, so the findings
    report is deterministic (rule R-6). IT QUOTES THE VALUE for two of the
    four categories, which is why it goes only into the 0600 report file.

    Args:
        value: The non-canonical value, after job 1.

    Returns:
        The reason, naming the specific deviation.
    """
    category = _date_text_category(value)
    if category == _CATEGORY_EMPTY:
        return (
            "empty after job 1 removed trailing spaces, so the stored "
            "value was all spaces; the canonical form is NN/NN/NN "
            "[copybooks/wspost.cob:L18]"
        )
    if category == _CATEGORY_LENGTH:
        return (
            f"{len(value)} character(s), not the 8 of the canonical "
            f"NN/NN/NN form. NEITHER EXPANDED NOR CONTRACTED: the "
            f"two-digit versus four-digit component question is "
            f"arbitrated by the compiled oracle (rule R-6) and recorded in "
            f"the migration's ambiguity register, never by this "
            f"normaliser"
        )
    if category == _CATEGORY_SEPARATOR:
        return (
            f"separators {(value[2], value[5])!r} at positions 3 and 6 "
            f"rather than {_DATE_TEXT_SEPARATOR!r}. Left as found: "
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
    category = _period_text_category(value)
    if category == _CATEGORY_EMPTY:
        return (
            "empty after job 1 removed trailing spaces, so the stored "
            "value was all spaces; the canonical form is four digits "
            "[copybooks/wssystem.cob:L145]"
        )
    if category == _CATEGORY_LENGTH:
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


# Cheap, and they protect every diff.


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
            f"harness/dump_tables.py."
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

    Same names, same order, same count. A mismatch means either the frozen schema was
    modified or the dump is stale, and both are drift rather than a difference worth
    diffing.

    Args:
        table: The in-scope table.
        columns: The `columns` value from the dump object.
        schema: The parsed column-type map.

    Returns:
        The column names.

    Raises:
        DumpShapeError: `columns` is not a list of strings, or does not match the
            schema.
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
        A short, deterministic description naming the position and both readings.
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
        DumpShapeError: `rows` is not a list of equal-length lists, or `row_count`
            disagrees with it.
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

    THIS IS NOT A FOURTH JOB. An exact integer has no rendering to canonicalise:
    `harness/dump_tables.py` writes it as a JSON integer and a JSON integer is exact for
    every width the schema uses, the widest in scope being `bigint(11)`.

    Args:
        value: The dumped value.
        table: The table it came from.
        column: The column it came from.
        declared: The column's declared type.

    Returns:
        The value, unchanged.

    Raises:
        NumericPolicyError: `value` is a binary floating-point number or a `bool` (rule
            R-2).
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
            f"harness/dump_tables.py writes every integer "
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

    The dispatch is on the declared type and on the job 3 allow-list, and on nothing
    else - never on what the value looks like. There are exactly three transformations,
    and a value receives at most two of them.

    Args:
        value: The dumped value.
        table: The in-scope table.
        column: The column name.
        declared: The column's declared type.
        row_index: The row's zero-based position, for a finding.
        findings: Where job 3's findings are appended, or `None` to discard them.
            `normalize_dump` stays pure either way.

    Returns:
        The canonical value.

    Raises:
        UnexpectedNullError: `value` is `None`.
        NumericPolicyError: Rule R-2's guard tripped.
        UnexpectedValueTypeError: The value's type does not match the column's class.
        DecimalScaleError: Job 2's information-loss guard tripped.
        SchemaParseError: The declared type is not one of the three classes.
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
                    category=outcome.category or "",
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

    THE SHAPE IS PRESERVED EXACTLY: the same five keys in the same order, the same
    `table` and `primary_key`, the same `columns` list in the same order, the same
    `row_count`, and the same rows IN THE SAME ORDER.

    Args:
        dump: A dump object as `harness/dump_tables.py` writes it.
        schema: The parsed column-type map from `load_schema`.
        findings: An optional collector for job 3's findings, appended to in row order
            and then column order.

    Returns:
        A new dump object with canonical values.

    Raises:
        DumpShapeError: The dump does not have the shape `harness/dump_tables.py`
            writes, or disagrees with the frozen schema on the column list.
        TableNotInScopeError: The dump is of an out-of-scope table.
        UnknownTableError: The dump names a table the schema does not define.
        UnexpectedNullError: A value is JSON null.
        NumericPolicyError: Rule R-2's guard tripped on a value.
        UnexpectedValueTypeError: A value's type does not match its column's class.
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
                # `strict=True` states the invariant `_assert_rows` already enforced:
                # rows are POSITIONAL, so a length mismatch would silently mis-attribute
                # every value after it rather than fail.
                for value, column, declared in zip(
                    row, columns, declared_types, strict=True
                )
            ]
        )

    # Rebuilt in `DUMP_KEYS` order rather than copied, so the key order is asserted by
    # construction as well as by `_assert_dump_keys` below.
    normalized: dict[str, Any] = {
        "table": table,
        "primary_key": specification.primary_key,
        "columns": list(columns),
        "row_count": len(canonical_rows),
        "rows": canonical_rows,
    }

    # The output invariants, re-asserted.
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


# Deterministic and atomic, with `harness/dump_tables.py`'s serialisation parameters
# pinned rather than defaulted, so a normalised file differs from its input in VALUES
# ONLY.


def dump_filename(table: str) -> str:
    """Return the file name a table's dump is stored under.

    Args:
        table: The table name, spelled exactly as the frozen schema spells it, hyphens
            included.

    Returns:
        `<TABLE>.json`, matching harness/dump_tables.py exactly.
    """
    return f"{table}{_DUMP_SUFFIX}"


def read_dump(path: Path | str) -> dict[str, Any]:
    """Read one dump file.

    Args:
        path: The `<TABLE>.json` file to read.

    Returns:
        The parsed dump object. Its shape is NOT validated here.

    Raises:
        DumpReadError: The file could not be read, is not valid UTF-8 JSON, or does not
            parse to a JSON object.
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

    The file is created mode 0600 through a descriptor opened `O_EXCL` and `O_NOFOLLOW`,
    because a normalised dump carries every value of every row of the accounting tables.
    See the SECURE OUTPUT commentary above `_write_text_securely`.

    Args:
        dump: A normalised dump object, as `normalize_dump` returns.
        path: Where to write it. Parent directories are created, mode 0700.

    Returns:
        The path written.

    Raises:
        DumpShapeError: `dump` does not carry exactly the five keys in order, or
            `row_count` disagrees with `rows`.
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
        _make_output_directory(target.parent)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the output directory {target.parent}: "
            f"{exc}"
        ) from exc

    # Serialised in full before the file is opened, so the descriptor is held briefly
    # and a serialisation failure cannot leave a staging file behind at all.
    text = json.dumps(
        dump,
        indent=_JSON_INDENT,
        ensure_ascii=True,
        sort_keys=False,
        separators=_JSON_SEPARATORS,
    )
    text += "\n"

    temporary = target.parent / f"{_TEMP_PREFIX}{target.stem}{_TEMP_SUFFIX}"
    try:
        _write_text_securely(text, target, temporary)
    except OSError as exc:
        raise DumpWriteError(
            f"could not write the normalised dump for table "
            f"{dump['table']!r} to {target}: {exc}"
        ) from exc

    return target


# One table at a time, in a plain loop, in ascending table-name order.


def file_digest(path: Path | str) -> str:
    """Return the lower-case hex SHA-256 of a file's bytes.

    Args:
        path: The file to digest.

    Returns:
        The digest, 64 hexadecimal characters.

    Raises:
        DumpReadError: The file could not be read.
    """
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(_DIGEST_BLOCK), b""):
                digest.update(block)
    except OSError as exc:
        raise DumpReadError(
            f"could not read {path} to check its digest: {exc}"
        ) from exc
    return digest.hexdigest()


def read_manifest(directory: Path | str) -> dict[str, Any] | None:
    """Read a tree's completeness manifest, if it has one.

    Args:
        directory: The published tree.

    Returns:
        The manifest object, or None when the tree carries none - which means the stage
            that wrote it did not finish.

    Raises:
        ManifestError: The manifest is present but unreadable, is not valid JSON, is not
            a mapping, or declares a version this module does not understand.
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
            f"the completeness manifest {path} declares "
            f"manifest_version {version!r}, and this tool understands "
            f"{MANIFEST_VERSION}. Refusing rather than guessing: a "
            f"manifest half-understood would let an incomplete tree pass "
            f"for a complete one."
        )
    return document


def assert_tree_complete(
    directory: Path | str, *, description: str = "the source tree"
) -> dict[str, Any]:
    """Assert a tree declares itself complete and matches its declaration.

    All four checks matter, and each catches a different way a tree can be a lie: no
    manifest means the producing stage never committed; a missing file means the
    manifest over-declares.

    Args:
        directory: The published tree to check.
        description: How to refer to it in a message.

    Returns:
        The verified manifest.

    Raises:
        ManifestError: The tree carries no manifest, names a table whose file is absent,
            records a digest that does not match the file on disk, or holds a
            `<TABLE>.json` the manifest does not name.
    """
    source = Path(directory)
    manifest = read_manifest(source)
    if manifest is None:
        raise ManifestError(
            f"{description} {source} carries no {MANIFEST_FILENAME}, so it "
            f"does not declare itself complete. The manifest is written "
            f"LAST by the stage that publishes a tree, so its absence "
            f"means that stage did not finish - the set may be missing "
            f"tables, and normalising it would carry a partial capture "
            f"into the comparison, where it could pass. Re-run the "
            f"producing stage. If the tree was assembled by hand, pass "
            f"--allow-unmanifested to proceed without this check and be "
            f"aware that the result is not protocol evidence (rule R-6)."
        )

    declared = manifest.get("tables")
    if not isinstance(declared, list):
        raise ManifestError(
            f"the manifest in {source} has no usable `tables` list."
        )
    named: list[str] = []
    for entry in declared:
        if not isinstance(entry, dict) or not isinstance(
            entry.get("table"), str
        ):
            raise ManifestError(
                f"the manifest in {source} has a malformed entry in its "
                f"`tables` list: {entry!r}."
            )
        table = entry["table"]
        named.append(table)
        member = source / dump_filename(table)
        if not member.is_file():
            raise ManifestError(
                f"the manifest in {source} names table {table!r} but "
                f"{member.name} is not there. The tree is incomplete."
            )
        recorded = entry.get("sha256")
        if isinstance(recorded, str) and recorded:
            actual = file_digest(member)
            if actual != recorded:
                raise ManifestError(
                    f"{member} does not match the digest its manifest "
                    f"records ({actual} rather than {recorded}), so the "
                    f"file changed after the tree was published. The "
                    f"comparison must be made against one capture, not a "
                    f"patched one."
                )

    present = set(_scan_dump_names(source))
    undeclared = sorted(present - set(named))
    if undeclared:
        raise ManifestError(
            f"{source} holds dump(s) its manifest does not name: "
            f"{', '.join(undeclared)}. A published tree is purged of stale "
            f"files before the new set is moved in, so an undeclared dump "
            f"is a table left over from an earlier run - comparing it "
            f"would mix two captures."
        )
    return manifest


def _scan_dump_names(source: Path) -> tuple[str, ...]:
    """Return the table names a directory holds `<TABLE>.json` files for.

    The single place the file-name filter lives, so `discover_tables` and
    `assert_tree_complete` cannot disagree about what counts as a dump.

    Args:
        source: The directory to scan.

    Returns:
        The names, ascending.
    """
    names: list[str] = []
    for entry in source.iterdir():
        name = entry.name
        if name.startswith(_TEMP_PREFIX):
            continue
        if name.startswith(_RESERVED_PREFIX):
            continue
        if not name.endswith(_DUMP_SUFFIX):
            continue
        if not entry.is_file():
            continue
        names.append(name[: -len(_DUMP_SUFFIX)])
    return tuple(sorted(names))


def discover_tables(src_dir: Path | str) -> tuple[str, ...]:
    """List the tables a source directory holds dumps for.

    Args:
        src_dir: The directory `harness/dump_tables.py` wrote into.

    Returns:
        The table names, ASCENDING - sorted once, deterministically, so two runs process
            the same tables in the same order (rule R-6).

    Raises:
        DumpReadError: The directory does not exist, or is not a directory.
    """
    source = Path(src_dir)
    if not source.is_dir():
        raise DumpReadError(
            f"{source} is not a directory. It should be the directory "
            f"harness/dump_tables.py wrote its <TABLE>.json files into, "
            f"for example $ACAS_OUT/<scenario>/cobol."
        )
    return _scan_dump_names(source)


def write_manifest(manifest: Mapping[str, Any], path: Path | str) -> Path:
    """Serialise a manifest with the same byte discipline as a dump.

    Args:
        manifest: The manifest object.
        path: Where to write it.

    Returns:
        The path written.

    Raises:
        DumpShapeError: The keys are not exactly `MANIFEST_KEYS` in order.
        DumpWriteError: The file could not be written or moved.
    """
    keys = tuple(manifest.keys())
    if keys != MANIFEST_KEYS:
        raise DumpShapeError(
            f"a manifest must carry exactly the keys "
            f"{list(MANIFEST_KEYS)} in that order; got {list(keys)}."
        )

    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the directory for the completeness "
            f"manifest {target}: {exc}"
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
            # NOT SWALLOWED SILENTLY. The staging file surviving matters: it
            # sits in the published tree, and `discover_tables` excludes it by
            # its `_` prefix rather than by knowing it is rubbish, so a leftover
            # one is invisible to the next stage while still occupying the
            # directory. Reported here; the real failure is still the
            # `DumpWriteError` raised below.
            print(
                f"harness/normalize.py: warning: the staging file "
                f"{temporary} could not be removed after the manifest write "
                f"failed: errno {unlink_error.errno} "
                f"({os.strerror(unlink_error.errno or 0)})",
                file=sys.stderr,
            )
        raise DumpWriteError(
            f"could not write the completeness manifest {target}: {exc}"
        ) from exc

    return target


def build_manifest(
    entries: Sequence[tuple[str, int, str]],
    *,
    scenario: str | None = None,
    side: str | None = None,
    selector: str = SELECTOR_INHERITED,
    provenance: Mapping[str, Any] | None = None,
    attestation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble this stage's completeness manifest.

    Args:
        entries: One `(table, row_count, digest)` triple per file written. Sorted here,
            so the manifest never depends on processing order.
        scenario: The scenario, INHERITED from the source tree's manifest so the two
            stages of one run cannot claim different identities.
        side: `cobol` or `python`, likewise inherited.
        selector: How the table list was originally chosen, likewise inherited - which
            is what lets the comparison stage report the scope the evidence actually
            has.
        attestation: What the RUN stage claimed, inherited verbatim. None becomes a
            recorded refusal rather than an omitted key, so a tree normalised from a
            waived or absent source manifest cannot pass for an attested one.

    Returns:
        The manifest object, keys in `MANIFEST_KEYS` order.

    Raises:
        DumpShapeError: A table appears twice.
    """
    ordered = sorted(entries, key=lambda entry: entry[0])
    seen: set[str] = set()
    tables: list[dict[str, Any]] = []
    for table, row_count, digest in ordered:
        if table in seen:
            raise DumpShapeError(
                f"table {table!r} appears twice in a manifest; each table "
                f"is written to exactly one file."
            )
        seen.add(table)
        tables.append(
            {"table": table, "row_count": int(row_count), "sha256": digest}
        )
    if not isinstance(attestation, Mapping):
        attestation = {
            key: None for key in ATTESTATION_KEYS
        } | {
            "attested": False,
            # `unknown` rather than a fault: nothing here has seen a status, so
            # nothing here can say which kind of nothing it was. The vocabulary is
            # harness/dump_tables.py's, and every other key stays at the `None` the
            # comprehension above set, so the object carries the full key set.
            "disposition": "unknown",
            "detail": (
                "the raw tree carried no usable run attestation, so this "
                "normalised tree makes no claim about the run it came from."
            ),
        }
    if not isinstance(provenance, Mapping):
        provenance = {key: None for key in PROVENANCE_KEYS}
    return {
        "manifest_version": MANIFEST_VERSION,
        "producer": _PRODUCER,
        "stage": MANIFEST_STAGE_NORMALIZED,
        "scenario": scenario,
        "side": side,
        "selector": selector,
        # Rebuilt key by key in PROVENANCE_KEYS order, so an inherited object with its
        # keys in another order cannot change these bytes.
        "provenance": {key: provenance.get(key) for key in PROVENANCE_KEYS},
        # Rebuilt key by key in ATTESTATION_KEYS order, so an inherited object with
        # its keys in another order cannot change these bytes.
        "attestation": {key: attestation.get(key) for key in ATTESTATION_KEYS},
        "table_count": len(tables),
        "tables": tables,
    }


def _is_same_directory(left: Path, right: Path) -> bool:
    """Report whether two paths name the same directory.

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
    require_manifest: bool = True,
) -> list[str]:
    """Normalise every dump in one directory into another, as a set.

    THE DESTINATION IS PUBLISHED AS A SET, NOT FILE BY FILE. Every file is written into
    a fresh staging directory beside the destination.

    Args:
        src_dir: The directory of `<TABLE>.json` dumps to read.
        dst_dir: The directory to write the normalised dumps into. It is created if it
            does not exist. It must not be the source.
        schema: The parsed column-type map from `load_schema`.
        tables: An optional explicit table list; every entry must have a dump in
            `src_dir`. `None` normalises every dump present.
        findings: An optional collector for job 3's findings.
        require_manifest: Whether the source must declare itself complete. True is the
            protocol. False is the hand-assembled-tree escape hatch, and a tree
            normalised that way is not evidence.

    Returns:
        The table names normalised, in the order processed - ascending.

    Raises:
        ManifestError: `require_manifest` and the source does not declare itself
            complete, or its declaration does not match its contents.
        DumpReadError: The source is missing, a requested dump is absent, or a file
            could not be read.
        DumpShapeError: A dump does not have the expected shape, or its file name
            disagrees with its `table` key.
        TableNotInScopeError: A dump is of an out-of-scope table.
        UnknownTableError: A dump names an unknown table.
        UnexpectedNullError: A dump carries a JSON null.
        NumericPolicyError: Rule R-2's guard tripped.
        UnexpectedValueTypeError: A value's type is wrong for its column.
        DecimalScaleError: Job 2's information-loss guard tripped.
        DumpWriteError: An output file could not be written.
        ValueError: The source and the destination are the same directory, which would
            overwrite the dumps being compared.
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

    source_manifest: Mapping[str, Any] | None = None
    # ⭐ THE LINEAGE DIGEST IS TAKEN FROM THE BYTES ON DISK (finding F-36), not from a
    # re-serialisation of the parsed object, so it identifies exactly what this stage
    # read and exactly what harness/diff_states.py will re-hash to check it.
    source_manifest_digest: str | None = None
    if require_manifest:
        source_manifest = assert_tree_complete(source)
        try:
            source_manifest_digest = file_digest(source / MANIFEST_FILENAME)
        except (OSError, ValueError) as exc:
            raise ManifestError(
                f"the source manifest {source / MANIFEST_FILENAME} could not be "
                f"hashed: {exc}. Its digest is the lineage this normalised tree "
                f"records, and without it the result cannot say which raw capture it "
                f"was made from."
            ) from exc
    else:
        _progress(
            f"harness/normalize.py: --allow-unmanifested - {source} is "
            f"being normalised without checking that it declares itself "
            f"complete. The result is NOT protocol evidence (rule R-6)."
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

    if not selected:
        return []

    staging = destination.parent / (
        f"{_TEMP_PREFIX}{destination.name}{_STAGING_SUFFIX}"
    )
    _reset_staging(staging)
    try:
        normalized: list[str] = []
        entries: list[tuple[str, int, str]] = []
        staged: list[Path] = []
        for table in selected:
            source_path = source / dump_filename(table)
            dump = read_dump(source_path)
            named = dump.get("table")
            if named != table:
                raise DumpShapeError(
                    f"{source_path} is named for table {table!r} but its "
                    f"`table` key says {named!r}. The file name and the "
                    f"key must agree, or a dump would be normalised - and "
                    f"later compared - under the wrong schema."
                )
            canonical = normalize_dump(dump, schema, findings=findings)
            staged_path = write_dump(
                canonical, staging / dump_filename(table)
            )
            staged.append(staged_path)
            entries.append(
                (
                    table,
                    int(canonical["row_count"]),
                    file_digest(staged_path),
                )
            )
            normalized.append(table)
            _progress(
                f"  {table:<24} {canonical['row_count']:>7} row(s)  "
                f"{len(canonical['columns']):>3} column(s)  canonicalised"
            )

        # ⭐ THE INPUT MUST STILL BE THE INPUT (finding F-36).
        #
        # The lineage digest was taken before a single dump was read. Everything since
        # then - discovering the tables, reading each one, canonicalising it, staging it
        # - has been reading files out of the source tree, and stage 3 can republish
        # that tree while this stage is walking it. If it did, this normalisation is a
        # MIXTURE of two captures: some tables from the capture whose manifest was read
        # and some from the one that replaced it. A mixture is indistinguishable from a
        # clean capture afterwards, and it can produce an empty diff.
        #
        # So the manifest is re-hashed here, after all the reading and before anything
        # is published, and a change is refused. This is the check that makes
        # `source_manifest_sha256` a verified fact rather than a value this stage
        # asserted about itself.
        if require_manifest and source_manifest_digest is not None:
            try:
                recheck = file_digest(source / MANIFEST_FILENAME)
            except (OSError, ValueError) as exc:
                raise ManifestError(
                    f"the source manifest {source / MANIFEST_FILENAME} could not be "
                    f"re-read after this stage finished reading the dumps: {exc}. It "
                    f"is re-hashed to prove the raw capture did not change while it "
                    f"was being normalised, and a result that cannot prove that is "
                    f"not evidence (rule R-6)."
                ) from exc
            if recheck != source_manifest_digest:
                raise ManifestError(
                    f"the raw capture {source} CHANGED while it was being "
                    f"normalised: its {MANIFEST_FILENAME} hashed "
                    f"{source_manifest_digest} when this stage began and {recheck} "
                    f"now. The tables read since then may come from two different "
                    f"captures, and a normalised tree mixing two captures is "
                    f"indistinguishable from a clean one afterwards - it can produce "
                    f"an EMPTY DIFF, which is the pass condition. Nothing is "
                    f"published. Re-run the dump stage for this side and normalise "
                    f"again, with no other stage writing into {source}."
                )

        # Identity is INHERITED from the source's manifest, never invented here.
        manifest = build_manifest(
            entries,
            scenario=_inherit(source_manifest, "scenario"),
            side=_inherit(source_manifest, "side"),
            selector=_inherit(source_manifest, "selector")
            or SELECTOR_INHERITED,
            provenance=_inherit_provenance(
                source_manifest, source_manifest_sha256=source_manifest_digest
            ),
            attestation=_inherit_attestation(source_manifest),
        )
        staged_manifest = write_manifest(
            manifest, staging / MANIFEST_FILENAME
        )
        _publish_staged(destination, staged, staged_manifest)
        return normalized
    finally:
        _remove_tree(staging)


def _inherit(manifest: Mapping[str, Any] | None, key: str) -> str | None:
    """Return one identity field from a source manifest.

    Args:
        manifest: The source tree's manifest, or None when the check was waived with
            --allow-unmanifested.
        key: The field to read.

    Returns:
        The value when it is a non-empty string, otherwise None - so a malformed or
            absent field becomes an honest "unknown" rather than a fabricated identity.
    """
    if manifest is None:
        return None
    value = manifest.get(key)
    return value if isinstance(value, str) and value else None


def _inherit_provenance(
    manifest: Mapping[str, Any] | None,
    *,
    source_manifest_sha256: str | None,
) -> Mapping[str, Any] | None:
    """Return the source's provenance with THIS stage's lineage stamped into it.

    Every field is carried through unchanged except `source_manifest_sha256`, which only
    this stage can know: it is the digest of the manifest the normalised tree was
    DERIVED from. See PROVENANCE KEYS above for why its absence made a normalised tree
    unattributable (finding F-36).

    Args:
        manifest: The source tree's manifest, or None when the check was waived with
            --allow-unmanifested.
        source_manifest_sha256: The digest of that manifest's bytes, or None when there
            was no manifest to hash - which yields a tree with no lineage, and
            harness/diff_states.py refuses one.

    Returns:
        The provenance object to publish, or None when the source carried none.
    """
    if manifest is None:
        return {
            key: None for key in PROVENANCE_KEYS
        } | {"source_manifest_sha256": source_manifest_sha256}
    value = manifest.get("provenance")
    carried = dict(value) if isinstance(value, Mapping) else {
        key: None for key in PROVENANCE_KEYS
    }
    carried["source_manifest_sha256"] = source_manifest_sha256
    return carried


def _inherit_attestation(
    manifest: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Return the run attestation a source manifest carries, unjudged.

    Args:
        manifest: The source tree's manifest, or None when the check was waived with
            --allow-unmanifested.

    Returns:
        The attestation object when the source carried one, otherwise None - which
            `build_manifest` turns into an explicit refusal. A waived source manifest
            therefore cannot yield an attested normalised tree, which is the direction
            that fails closed.
    """
    if manifest is None:
        return None
    value = manifest.get("attestation")
    return value if isinstance(value, Mapping) else None


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
            f"first on purpose, so an interrupted publish leaves a tree "
            f"that declares itself unfinished rather than one mixing two "
            f"runs."
        ) from exc

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
    for source_path in staged:
        target = destination / source_path.name
        try:
            os.replace(source_path, target)
        except OSError as exc:
            raise DumpWriteError(
                f"could not publish {source_path.name} into "
                f"{destination}: {exc}. The tree now carries no manifest, "
                f"so the comparison stage will refuse it rather than "
                f"compare a partial set."
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


# THE JOB 3 FINDINGS REPORT (rule R-6) Loud, deterministic, and OUTSIDE the compared
# trees.

_REPORT_HEADER: Final[str] = """\
job 3 date-text findings, from [harness/normalize.py]

Every value listed below was passed through UNCHANGED. None was expanded
from two digits to four, contracted from four to two, re-separated or
re-padded: doing any of that could make a genuine divergence between the
two sides compare equal, which Agent Action Plan section 0.6.6 forbids -
"a non-empty diff is always a real behavioral difference and never an
artefact of the comparison".

A finding is a QUESTION FOR THE COMPILED ORACLE (rule R-6), not a defect
in this tool and not a reason to widen its recogniser. Record the answer
in the migration's ambiguity register.

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


def summarise_findings(
    findings: Sequence[DateTextFinding],
    *,
    report_path: Path | None,
    report_digest: str | None = None,
) -> str:
    """Render a VALUE-FREE summary of the job 3 findings, for stderr.

    THE REASON THIS EXISTS. `render_report` quotes every unrecognised value
    verbatim - that is its whole point, because an operator has to take the
    exact bytes to the compiled oracle (rule R-6) - so the report carries live
    accounting data and is written 0600 through `_write_text_securely`. Printing
    those same bytes to stderr, which the composed recipe collects as a container
    log, treated the identical content as public in one channel and private in
    the other. This summary is what stderr gets instead: the counts, the TABLE
    and COLUMN names, the four-token reason CATEGORY, the report's path and its
    SHA-256 - all of which are frozen public metadata or a fixed vocabulary,
    since every table and column name is already in the committed
    `data_dictionary/acas_posting_dictionary.json`. The full `reason` is NOT on
    stderr: for two of the four categories it quotes bytes of the value.

    Args:
        findings: The findings collected during normalisation.
        report_path: Where the full report was written, or None when it could
            not be written at all.
        report_digest: The report file's SHA-256, which binds the pointer to the
            bytes a reader will open (rule R-6). None when there is no file or
            it could not be read back.

    Returns:
        The summary, ending in a newline; the EMPTY STRING when there are no
        findings, so a clean run stays silent exactly as before.
    """
    if not findings:
        return ""

    #: table -> column -> CATEGORY -> count. The category and not the reason:
    #: two of the four full reasons quote bytes of the value - the separator
    #: characters, and the length - and this line is a console line. Deterministic:
    #: `sorted` at every level, so the same findings always render to the same
    #: bytes.
    grouped: dict[str, dict[str, dict[str, int]]] = {}
    for finding in findings:
        by_column = grouped.setdefault(finding.table, {})
        by_category = by_column.setdefault(finding.column, {})
        key = finding.category or _CATEGORY_COMPONENT
        by_category[key] = by_category.get(key, 0) + 1

    lines: list[str] = [
        f"harness/normalize.py: {len(findings)} job 3 finding(s); the "
        f"unrecognised values are withheld from stderr"
    ]
    for table in sorted(grouped):
        for column in sorted(grouped[table]):
            categories = grouped[table][column]
            detail = "; ".join(
                f"{category} x{categories[category]}"
                for category in sorted(categories)
            )
            lines.append(f"  {table}.{column}  {detail}")

    if report_path is None:
        lines.append(
            "  the values could NOT be preserved: see the error above. "
            "Re-run with --report PATH pointing somewhere writable."
        )
    elif report_digest is None:
        lines.append(f"  the values are in {report_path} (mode 0600)")
    else:
        lines.append(
            f"  the values are in {report_path} (mode 0600, "
            f"sha256={report_digest})"
        )
    lines.append(
        "  a date-text form this module does not recognise is a question "
        "for the compiled oracle (rule R-6)."
    )
    return "".join(f"{line}\n" for line in lines)


def _fallback_report_path(source: Path) -> Path:
    """Return a private path to hold the findings report when none was asked for.

    The counterpart of `harness/diff_states.py`'s helper of the same name, and
    for the same reason: the report quotes live accounting data, so it belongs in
    a 0600 file on EVERY path rather than on stderr when no `--report` was given.
    `tempfile.mkdtemp` creates its directory 0700 by construction with a name no
    other process could have predicted.

    Args:
        source: The source directory, used only to name the file so that the two
            sides of a comparison are distinguishable.

    Returns:
        A path inside a fresh private directory.

    Raises:
        OSError: No private directory could be created. The caller then prints
            the value-free summary with no pointer; it does NOT fall back to
            printing the values.
    """
    directory = Path(tempfile.mkdtemp(prefix="acas-normalize-"))
    return directory / f"{_report_label(source)}-{_REPORT_FILENAME}"


def _report_digest(path: Path) -> str | None:
    """Return the lower-case hex SHA-256 of a written report, or None.

    Args:
        path: The report file.

    Returns:
        The digest, or None when the file could not be read back - which is
        reported by the caller and is never fatal, because no verdict depends
        on it.
    """
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(_DIGEST_BLOCK), b""):
                digest.update(block)
    except OSError:
        return None
    return digest.hexdigest()


def render_report(
    findings: Sequence[DateTextFinding],
    *,
    source: str | None = None,
) -> str:
    """Render the job 3 findings as deterministic text.

    Grouped by table, then column, then row index, all ascending, so the same findings
    always render to the same bytes. The text carries no wall-clock reading, no host
    name, no process identifier and no tool version.

    Args:
        findings: The findings collected during normalisation.
        source: The source directory as it was given on the command line, recorded so an
            operator can tell which side a report is for.

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


# Two flag spellings for the source and the destination, because this repository
# documents two and neither is a guess.

_EPILOGUE: Final[str] = """\
layouts
  --src DIR [--dst DIR]        (--in / --out are the same two options)
      reads DIR/<TABLE>.json, writes DIR.normalized/<TABLE>.json unless
      --dst is given. The committed ten-stage recipe passes both:
      `--in /out/cobol --out /out/cobol.norm`   (harness/docker-compose.yml)
  --scenario NAME --side {cobol|python} [--out-dir DIR]
      reads  <DIR>/<NAME>/<side>/<TABLE>.json
      writes <DIR>/<NAME>/<side>.normalized/<TABLE>.json
      (DIR defaults to $ACAS_OUT)

the three canonicalisation jobs, and there is no fourth
  1  trailing ASCII spaces in char(n) columns - trailing only, never
     leading, because a COBOL alphanumeric MOVE pads on the RIGHT. The
     bridge itself trims: [common/nominalMT.cbl:L1065-L1067].
     Through this harness's driver this job usually finds NOTHING to do:
     MariaDB strips trailing spaces from a char column on read unless
     PAD_CHAR_TO_FULL_LENGTH is set, and the harness server deliberately
     does not set that mode either way. Kept regardless -- the width
     drift it answers is real (AAP 0.6.2), the server behaviour is a
     setting rather than a guarantee, and a capture taken through a
     driver or server that DOES preserve padding must still compare
     equal. A guard that mostly finds nothing is not a guard that does
     nothing.
  the manifest's attestation is CARRIED, never re-judged: what the run
     stage claimed is a fact about the run, and harness/diff_states.py
     enforces it.
  2  decimal(p,s) values re-rendered at the DECLARED scale. Never two by
     assumption - the schema's scales include 2, 4 and 0. A value with
     more places than its column declares is an ERROR, not something to
     round away.
  3  the five allow-listed date-text columns, RENDERING ONLY. A
     two-digit component is never expanded to four and four is never
     contracted to two; anything that does not match its canonical shape
     is passed through unchanged and REPORTED for the oracle to settle.

the set is the unit, not the file
  the source must carry _manifest.json, written last by the stage that
  published it; a tree without one did not finish and is REFUSED, because
  normalising a partial capture carries it into a comparison that can
  pass. --allow-unmanifested waives the check for a hand-assembled tree
  and forfeits the claim that the result is evidence.
  the destination is published the same way: staged beside it, stale
  dumps purged, files renamed in, _manifest.json renamed in LAST. So it
  holds either this run's complete set or no manifest - never a mixture.
  the manifest's scenario, side, selector and run attestation are all
  INHERITED from the source's, so the two stages of one run cannot claim
  different identities -- and a tree normalised from a waived or absent
  source manifest inherits NO attestation, which is the direction that
  fails closed at the comparison stage.

environment
  ACAS_REPO supplies the default --schema, $ACAS_REPO/mysql/ACASDB.sql.
            It is also the tree the destination may neither lie inside
            nor contain: publishing purges its destination, so a
            destination containing the checkout would delete out of it.
  ACAS_OUT  supplies the default --out-dir and the default --report
            directory, $ACAS_OUT/normalize/. Nothing is ever written
            under ACAS_REPO: harness/docker-compose.yml mounts it
            read-only.

exit codes
  0 normalised   80 usage        81 precondition   83 scope
  84 drift       85 numeric      86 write
  81 also covers a source tree that does not declare itself complete.
  86 also covers a destination overlapping the read-only checkout.
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
            "four-digit date text forms. Stages 4 and 8 of the ten-stage "
            "parity protocol - the COBOL dump and the Python dump respectively."
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
            "and is the spelling the recipe in harness/docker-compose.yml "
            "uses."
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
            "--scenario. It selects the <scenario>/<side>/ path and is also "
            "carried through into the normalised manifest, inherited verbatim "
            "from the raw one; the manifests themselves are never compared, so "
            "recording it cannot affect a verdict."
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
            "overwrite one another. The file is mode 0600 because it quotes "
            "the unrecognised values verbatim; when neither this option nor "
            "$ACAS_OUT is set the report is written to a private temporary "
            "directory instead, never to stderr. STDERR always gets a "
            "value-free summary naming the tables, columns, reasons, counts, "
            "the report path and its SHA-256."
        ),
    )
    parser.add_argument(
        "--allow-unmanifested",
        action="store_true",
        help=(
            "normalise a source tree that carries no "
            + MANIFEST_FILENAME
            + ". NOT THE PROTOCOL: the manifest is written last by the "
            "stage that publishes a tree, so its absence means that stage "
            "did not finish and the set may be missing tables. Use this "
            "only for a tree assembled by hand, and do not present the "
            "result as scenario evidence (rule R-6)."
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
        The source, the destination, and the scenario name when the composed layout was
            used (`None` otherwise).

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
                f"either `--src DIR [--dst DIR]`, as harness/docker-compose.yml "
                f"does, or `--scenario NAME "
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
            f"is unknown. The Compose service sets {_ENV_OUT}: /out itself; see "
            f"harness/docker-compose.yml."
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
        The report path, or `None` when no root is derivable and none was requested - in
            which case the findings still go to stderr.

    Raises:
        ReportPathError: The requested path lies inside the source, the destination, or
            the scenario's own directory.
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

    Runs of ASCII alphanumerics from the directory's own name, joined with a hyphen:
    `/out/cobol` gives `cobol` and `/out/clean_batch_gl/python` gives `python`, so the
    recipe's two invocations harness/docker-compose.yml, harness/docker-compose.yml
    write two reports rather than one overwriting the other.

    Args:
        source: The source directory. It need not exist; `Path.resolve` is non-strict
            and only normalises the path.

    Returns:
        The label, or `_REPORT_DEFAULT_LABEL` when the name yields none - which happens
            only for a filesystem root.
    """
    parts = _REPORT_LABEL_RE.findall(source.resolve().name)
    if not parts:
        return _REPORT_DEFAULT_LABEL
    return "-".join(parts)


def _assert_output_writable(
    destination: Path, env: Mapping[str, str]
) -> None:
    """Assert the normalised tree may be written where it was asked to go.

    Inside-out - the destination lies at or under the checkout - is the obvious one.

    Args:
        destination: The directory the normalised dumps land in.
        env: The environment, for `$ACAS_REPO`.

    Raises:
        OutputPathError: The destination overlaps the read-only checkout in either
            direction.
    """
    repository = env.get(_ENV_REPO)
    if not repository:
        return
    root = Path(repository).resolve()
    resolved = destination.resolve()

    if resolved == root or root in resolved.parents:
        raise OutputPathError(
            f"the normalised tree {destination} resolves to {resolved}, "
            f"which is inside the read-only checkout {root} "
            f"(${_ENV_REPO}). Nothing may be written there: it holds the "
            f"frozen COBOL, the bridges and mysql/ACASDB.sql - which this "
            f"tool READS from that tree - and Agent Action Plan section "
            f"0.8.1 calls any diff touching those paths \"a defect in the "
            f"migration, regardless of how harmless it appears\". Write "
            f"under ${_ENV_OUT} instead."
        )

    if resolved in root.parents:
        raise OutputPathError(
            f"the normalised tree {destination} resolves to {resolved}, "
            f"which CONTAINS the read-only checkout {root} (${_ENV_REPO}). "
            f"Publishing a tree removes every stale *.json from its "
            f"destination first, so a destination that contains the "
            f"checkout would delete files out of it. Name the leaf "
            f"directory the normalised dumps belong in, for example "
            f"${_ENV_OUT}/<scenario>/cobol{_NORMALIZED_SUFFIX}."
        )


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
                f"DIRECTORY, so any other file there would be taken for a "
                f"dump. Put the report outside, as harness/reset_db.sh puts "
                f"its log in $ACAS_OUT/reset/."
            )
    if scenario is not None:
        scenario_directory = destination.parent.resolve()
        if _is_inside(resolved, scenario_directory):
            raise ReportPathError(
                f"the findings report {candidate} would land inside the "
                f"scenario directory {destination.parent}. Nothing that "
                f"can vary between the two sides may appear there: the "
                f"determinism check compares that tree byte for byte "
                f"(rule R-6)."
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
        # Reuses the same scope gate the dumps go through, so a typo and a deliberately
        # out-of-scope request are refused the same way.
        _assert_table_in_scope(name)
    # De-duplicated, and ascending, so the run order does not depend on how the operator
    # happened to type the list (rule R-6).
    return tuple(sorted(set(named)))


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return an exit code.

    Never calls `sys.exit`, so a test can drive it in process and inspect the code.

    Args:
        argv: The arguments.

    Returns:
        `EX_OK` on success, or one of `EX_USAGE`, `EX_PRECONDITION`, `EX_SCOPE`,
            `EX_DRIFT`, `EX_NUMERIC`, `EX_WRITE`.
    """
    global _QUIET

    parser = build_parser()
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 for --help and 2 for a usage error.
        code = exc.code
        if code is None or code == 0:
            return EX_OK
        return EX_USAGE

    _QUIET = bool(arguments.quiet)
    env: Mapping[str, str] = os.environ

    # Tightened HERE and not at import time.
    os.umask(_OUTPUT_UMASK)

    try:
        source, destination, scenario = _resolve_directories(
            arguments, env
        )
    except ValueError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_USAGE

    try:
        _assert_output_writable(destination, env)
    except OutputPathError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_WRITE

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
            require_manifest=not arguments.allow_unmanifested,
        )
    except ManifestError as exc:
        print(f"harness/normalize.py: {exc}", file=sys.stderr)
        return EX_PRECONDITION
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

    #  THE VALUES GO TO A FILE, NEVER TO STDERR - on every path, and there is no
    #  option that changes it. `render_report` quotes each unrecognised value
    #  verbatim, which is what an operator needs in order to take the exact bytes
    #  to the compiled oracle (rule R-6), so the report carries live accounting
    #  data and is written 0600 through `_write_text_securely` - staged
    #  `O_EXCL | O_NOFOLLOW` and replaced atomically. Printing the same bytes to
    #  stderr, which the composed recipe collects as a container log, treated
    #  identical content as private in one channel and public in the other; that
    #  inconsistency was the disclosure. `summarise_findings` is what stderr gets
    #  instead, and it is loud enough to serve the reason the print existed: an
    #  operator who never opens the file still sees every table, column, reason
    #  and count, plus where the values are and the digest that proves the file
    #  they open is the file this run wrote.
    #
    #  WHEN NO `--report` AND NO $ACAS_OUT WAS GIVEN, a private file is still
    #  written - `_fallback_report_path` creates a 0700 directory for it - so the
    #  values are never lost and never printed. If even that fails, the summary
    #  says so and the findings themselves are still fully described.
    if findings and report_path is None:
        try:
            report_path = _fallback_report_path(source)
        except OSError as exc:
            print(
                f"harness/normalize.py: neither --report nor {_ENV_OUT} is "
                f"set and no private directory could be created for the "
                f"findings report, so the unrecognised values cannot be "
                f"preserved: {exc}",
                file=sys.stderr,
            )
            exit_code = EX_WRITE

    if report_path is not None:
        try:
            _make_output_directory(report_path.parent)
            staging = (
                report_path.parent
                / f"{_TEMP_PREFIX}{report_path.stem}{_REPORT_TEMP_SUFFIX}"
            )
            _write_text_securely(report, report_path, staging)
        except OSError as exc:
            print(
                f"harness/normalize.py: could not write the findings "
                f"report to {report_path}: {exc}",
                file=sys.stderr,
            )
            exit_code = EX_WRITE
            report_path = None
        else:
            _progress(
                f"harness/normalize.py: {len(findings)} job 3 finding(s) "
                f"recorded in {report_path}"
            )

    if findings:
        print(
            summarise_findings(
                findings,
                report_path=report_path,
                report_digest=(
                    _report_digest(report_path)
                    if report_path is not None
                    else None
                ),
            ),
            end="",
            file=sys.stderr,
        )

    _progress(
        f"harness/normalize.py: normalised {len(normalized)} table(s) "
        f"into {destination}"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
