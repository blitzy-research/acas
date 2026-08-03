"""Deterministic state capture: `SELECT * FROM <table> ORDER BY <primary key>`.

Stages 3 and 7 of the parity protocol. Writes one JSON file per table, holding
the rows exactly as the driver returned them, so that the comparison later
measures behaviour rather than transport.

The dump needs no tie-breaking, timestamp masking or surrogate-key remapping,
because every one of the 22 in-scope tables of `mysql/ACASDB.sql` has a
single-column primary key, no secondary index, no `TIMESTAMP` column, no
`AUTO_INCREMENT` and no column default. Ordering by that key is therefore a
total order and two runs of one scenario dump identically.

Numeric values are `decimal.Decimal` or `int` and are serialised as strings that
preserve the stored scale; a value that arrives as a float aborts the dump,
because no accounting figure may traverse binary floating point (R-2).

    stage 1  seed        harness/seed.sh          (COBOL *LD loaders)
    stage 2  run  COBOL  harness/run_cobol_scenario.sh
    stage 3  dump        THIS MODULE              -> $ACAS_OUT/.../cobol
    stage 4  normalize   harness/normalize.py
    stage 5  reset       harness/reset_db.sh      (+ re-seed)
    stage 6  run  Python harness/run_python_scenario.sh
    stage 7  dump        THIS MODULE              -> $ACAS_OUT/.../python
    stage 8  diff        harness/diff_states.py   -> MUST be EMPTY

The same eight stages, and the canonical one-command-per-stage recipe,
are published by the committed Compose file at
[harness/docker-compose.yml:L16-L26] and
[harness/docker-compose.yml:L138-L157].

THE DUMP IS DELIBERATELY DUMB
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
import shutil
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

# The two sides of the comparison; the dump's path, never its content, records which one
# it is.
SIDES: Final[tuple[str, ...]] = ("cobol", "python")

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

        WHAT THIS DELIBERATELY OMITS, AND WHY. It used to render the host, the
        port, the schema, the account, the socket path and BOTH the certificate
        and PRIVATE-KEY file paths, on the argument that a file name is not a
        secret. Every one of those is now gone. Two reasons, and the first is
        sufficient on its own:

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
    rolling back writes nothing, and it releases the read-only transaction
    the server opens under the pinned `autocommit=0`. Being SELECT-only,
    there is never anything to discard.

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
                    f"for seeding, which the harness server pins - so check "
                    f"that the seed stage released its locks before raising "
                    f"the budget."
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
                f"side [L1878-L1891] - because the bridge writes zero or "
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
    one connection. No thread, no pool, no batching. Under the
    `autocommit=0` that `harness/Dockerfile.mariadb` pins at server level
    the tables are read inside one implicit read transaction, which is at
    least as consistent as reading each alone: the posting run has
    completed before the dump starts and nothing else writes to the
    schema, so no table can change between reads.

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
        _make_output_directory(target.parent)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the output directory {target.parent}: {exc}"
        ) from exc

    # Serialised in full before the file is opened, so the descriptor is held for as
    # short a time as possible and a serialisation failure cannot leave a staging file
    # behind at all.
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
            f"could not write the dump for table {dump['table']!r} to "
            f"{target}: {exc}"
        ) from exc

    return target


# The manifest's file name.
MANIFEST_FILENAME: Final[str] = "_manifest.json"

# Bumped only if the manifest's SHAPE changes.
MANIFEST_VERSION: Final[int] = 1

# The manifest's keys, in the order they are written. Fixed, like `DUMP_KEYS`, because
# the order is part of the byte-identical guarantee.
MANIFEST_KEYS: Final[tuple[str, ...]] = (
    "manifest_version",
    "producer",
    "stage",
    "scenario",
    "side",
    "selector",
    "table_count",
    "tables",
)

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


def build_manifest(
    entries: Sequence[tuple[str, int, str]],
    *,
    stage: str,
    producer: str = _PRODUCER,
    scenario: str | None = None,
    side: str | None = None,
    selector: str = SELECTOR_INHERITED,
) -> dict[str, Any]:
    """Assemble a completeness manifest.

    Args:
        entries: One `(table, row_count, digest)` triple per published file.
        stage: `MANIFEST_STAGE_RAW` or `MANIFEST_STAGE_NORMALIZED`.
        producer: The tool that wrote the tree.
        scenario: The scenario this tree belongs to, or None.
        side: `cobol` or `python`, or None.
        selector: How the table list was chosen.

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
    return {
        "manifest_version": MANIFEST_VERSION,
        "producer": producer,
        "stage": stage,
        "scenario": scenario,
        "side": side,
        "selector": selector,
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


# Bound the comparison by the SCENARIO's affected-table list, not by everything. The
# reason is a menu-shell side effect.


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
            f"canonical invocation passes a scenario definition path; see "
            f"harness/docker-compose.yml."
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

    Exactly one selector may be given.

    Args:
        tables: A comma-separated list of table names.
        scenario_file: A scenario definition to read the list from.
        all_in_scope: Dump all 22 explicitly.

    Returns:
        The table names, in the order to dump them.

    Raises:
        ValueError: More than one selector was given, or `tables` is empty or names a
            table twice.
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

    return IN_SCOPE_TABLES


_EPILOGUE: Final[str] = """\
layouts
  --scenario NAME --side {cobol|python} [--out-dir DIR]
      writes <DIR>/<NAME>/<side>/<TABLE>.json   (DIR defaults to $ACAS_OUT)
  --out DIR
      writes <DIR>/<TABLE>.json                 the form the canonical
      recipe in harness/docker-compose.yml uses

table selection is REQUIRED
  exactly one of --scenario-file, --tables or --all-in-scope. An
  unbounded run is refused: [general/general.cbl:L656-L691] rewrites
  SYSTEM-REC, SYSDEFLT-REC and SYSTOT-REC on menu exit and the Python
  cycle has no menu, so comparing them in a scenario that does not
  affect them is a FALSE FAILURE - and evidence whose scope is implicit
  is not evidence (rule R-6).

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
            "eight-stage recipe in harness/docker-compose.yml uses. "
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
            "read the affected-table list from a scenario definition file, "
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
            "scope of this dump is undefined. Bound it by the scenario:\n"
            "  --scenario-file <scenario>.yaml                     "
            "the protocol; the list comes from the scenario's "
            "affected_tables\n"
            "  --tables TABLE[,TABLE...]                           "
            "an explicit list, for narrowing one table by hand\n"
            "  --all-in-scope                                      "
            "all 22, a debugging aid and NOT scenario evidence\n"
            "An unbounded run is refused rather than defaulted because "
            "[general/general.cbl:L656-L691] rewrites SYSTEM-REC, "
            "SYSDEFLT-REC and SYSTOT-REC on menu exit and the Python cycle "
            "has no menu, so comparing them in a scenario that does not "
            "affect them produces a FALSE FAILURE - and because evidence "
            "whose scope is implicit is not evidence (rule R-6).",
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

    destination = dump_path(
        out, tables[0], scenario=scenario, side=side
    ).parent
    try:
        _assert_output_writable(destination, env)
    except DumpPathError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_WRITE

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
    """
    if arguments.scenario_file is not None:
        return SELECTOR_SCENARIO_FILE
    if arguments.tables is not None:
        return SELECTOR_TABLES
    if arguments.all_in_scope:
        return SELECTOR_ALL_IN_SCOPE
    return None


if __name__ == "__main__":
    raise SystemExit(main())
