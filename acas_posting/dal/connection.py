"""The relational connection: the native reimplementation of the handler open path.

Opens and holds the one connection every handler module shares, with its
credentials taken from the `RDB-Data` block of the file-access record
[copybooks/wsfnctn.cob:L56-L63] - schema, user, password, host, socket and port -
which is where the frozen tree puts them.

Three properties are reproduced rather than improved. Autocommit follows the
COBOL's per-statement behaviour, so a statement's effect is visible exactly when
it would have been. There is NO connection pool and no concurrency of any kind
(R-3): execution is strictly sequential, matching the single-threaded original.
And the driver's converters are pinned so a numeric column arrives as `Decimal`
or `int` and never as a binary float (R-2) - the frozen schema declares no
FLOAT, DOUBLE or REAL column, and nothing here may introduce one.

A credential value is never logged, echoed or included in an exception message;
only the name of a missing parameter is.
"""

from __future__ import annotations

import decimal
import ipaddress
import logging
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, NoReturn

import mysql.connector
from mysql.connector import FieldType, conversion
from mysql.connector.abstracts import (
    MySQLConnectionAbstract,
    MySQLCursorAbstract,
)
from mysql.connector.constants import ClientFlag

#  `redact_for_log` is deliberately NOT imported. It was, and every use of it in
#  this module was a driver message reaching a log record; redaction cannot make
#  that safe, because its rules recognise the connection-message shapes the client
#  library is known to produce and nothing else (CWE-117, CWE-532). The two
#  picture widths below replace the literal 5 that the one surviving record used,
#  so the fields are cut to the widths `copybooks/wsfnctn.cob:L49, :L51` declares
#  rather than to a number repeated here.
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_STATE_WIDTH,
    ConnectStep,
    DbErrorStatus,
    FsReply,
    WeError,
    db_error_log_category,
    mysql_1100_db_error,
    sanitise_for_log,
)
from acas_posting.records.file_access import LoggingData, RdbData
from acas_posting.records.system_record import (
    SystemRecord,
    carries_frozen_placeholder_rdbms_credentials,
)

__all__: Final[tuple[str, ...]] = (
    "CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT",
    "CONVERTER_PROBE_STATEMENT",
    "IDENTIFIER_QUOTE",
    "LOOPBACK_HOST_NAMES",
    "PINNED_CONVERTER_HOOKS",
    "REJECTED_CONVERTER_HOOKS",
    "SCHEMA_MAX_DECIMAL_PRECISION",
    "SCHEMA_MAX_DECIMAL_SCALE",
    "TRANSPORT_CATEGORIES",
    "AcasConverter",
    "BinaryFloatingPointError",
    "ConnectionPolicy",
    "ConnectionPolicyError",
    "ConverterPinningError",
    "FrozenPlaceholderCredentialsError",
    "InsecureTransportError",
    "OpenOutcome",
    "TransportSecurity",
    "acquire_cursor",
    #  ---- connection policy: REPORTING is on the parity path, REFUSING is not
    #  (M-06). `audit_connection_policy` returns concerns and `mysql_1000_open`
    #  logs them; `require_connection_policy` raises and nothing in the migrated
    #  cycle calls it.
    "audit_connection_policy",
    "require_connection_policy",
    "cobol_string_delimited_by_space",
    "connection_parameters",
    "connection_policy",
    "cursor_is_unavailable",
    "execute_statement",
    "load_rdb_data_once",
    "mysql_1000_open",
    "mysql_1090_exit",
    "mysql_1980_close",
    "mysql_1999_exit",
    "process_connection",
    "quote_identifier",
    "rdb_data_from_system_record",
    "rdb_data_is_loaded",
    "reset_connection_policy",
    "reset_process_connection",
    "reset_rdb_data_cache",
    "transport_category",
    "set_connection_policy",
    "transport_decimal_context",
)

#: Module logger. A library module attaches no handler and configures no root logger;
#: the application decides where diagnostics go.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


SCHEMA_MAX_DECIMAL_PRECISION: Final[int] = 14

SCHEMA_MAX_DECIMAL_SCALE: Final[int] = 2

IDENTIFIER_QUOTE: Final[str] = "`"

#: The driver field types the frozen schema can produce, mapped to the converter hook
#: that must be pinned for each. The hook names are not invented.
PINNED_CONVERTER_HOOKS: Final[Mapping[int, str]] = MappingProxyType(
    {
        FieldType.DECIMAL: "_decimal_to_python",
        FieldType.NEWDECIMAL: "_newdecimal_to_python",
        FieldType.TINY: "_tiny_to_python",
        FieldType.SHORT: "_short_to_python",
        FieldType.INT24: "_int24_to_python",
        FieldType.LONG: "_long_to_python",
        FieldType.LONGLONG: "_longlong_to_python",
        FieldType.STRING: "_string_to_python",
        FieldType.VAR_STRING: "_var_string_to_python",
    }
)

#: The two field types that must never arrive, and the hooks that refuse them.
REJECTED_CONVERTER_HOOKS: Final[Mapping[int, str]] = MappingProxyType(
    {
        FieldType.FLOAT: "_float_to_python",
        FieldType.DOUBLE: "_double_to_python",
    }
)

#: The connect-time probe. Three casts, chosen so the statement depends on no table and
#: therefore cannot be affected by - or affect - any seeded state.
CONVERTER_PROBE_STATEMENT: Final[str] = (
    "SELECT CAST('1.50' AS DECIMAL(10,2)), "
    "CAST(-42 AS SIGNED), "
    "CAST('AB' AS CHAR(4))"
)

#: The exact text the decimal probe value must render as. ``'1.50'`` and not ``'1.5'``.
CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT: Final[str] = "1.50"

#: Width of ``05 DB-Port pic x(5)`` [copybooks/wsfnctn.cob:L62].
_DB_PORT_WIDTH: Final[int] = 5

#: Width of ``Ws-Mysql-Port-Number pic x(4)`` [copybooks/mysql-variables.cpy:L91] - the
#: working-storage item the bridge STRINGs ``DB-Port`` into
#: [common/glpostingMT.cbl:L408].
_WS_MYSQL_PORT_WIDTH: Final[int] = 4

#: The three literal values the C interface reads as "no socket", tested with ``strcmp``
#: after it has trimmed the item.
_SOCKET_MEANS_NONE: Final[frozenset[str]] = frozenset({"0", "null", "NULL"})


class BinaryFloatingPointError(TypeError):
    """A binary floating-point value reached the transport boundary.

    Raised by :class:`AcasConverter` when a driver field type that produces a binary
    floating-point value is encountered.
    """


class ConverterPinningError(RuntimeError):
    """The pinned numeric converter is not in force on a live connection.

    * the connection is not using :class:`AcasConverter` at all - the
    ``converter_class`` argument was dropped or overridden; * a hook this module pins is
    no longer overridden, so the driver's default would serve that field type.
    """


class AcasConverter(conversion.MySQLConverter):
    """The explicitly pinned type converter for every ACAS connection.

    Rule R-2, of this file, verbatim: "`acas_posting/dal/connection.py` additionally
    pins the converter explicitly rather than relying on the default." This class is
    that pinning.
    """


    def _decimal_to_python(
        self,
        value: bytes | bytearray | str,
        desc: Any = None,
    ) -> decimal.Decimal:
        """Return a ``DECIMAL`` column as an exact ``decimal.Decimal``.

        The server sends a decimal as its TEXT rendering, so the declared scale is
        present in the bytes and survives if - and only if - the ``Decimal`` is built
        from that text.

        Args:
            value: The column as the driver delivers it - ``bytes`` from the wire, or
                ``str`` if a caller has already decoded it.
            desc: The driver's column description tuple. Unused: the scale is carried in
                the value's own text, so nothing needs to be read from the description.

        Returns:
            The value as an exact ``decimal.Decimal`` at its declared scale.
        """
        del desc
        text = (
            value.decode(self.charset)
            if isinstance(value, (bytes, bytearray))
            else str(value)
        )
        return decimal.Decimal(text)

    #: `NEWDECIMAL` is what MariaDB 10.11.7 actually sends for a `decimal` column.
    _newdecimal_to_python = _decimal_to_python

    # Five widths, 208 in-scope columns, one behaviour.

    @staticmethod
    def _tiny_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``TINYINT`` column as ``int`` (99 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _short_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``SMALLINT`` column as ``int`` (20 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _int24_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``MEDIUMINT`` column as ``int`` (21 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _long_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return an ``INT`` column as ``int`` (65 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _longlong_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``BIGINT`` column as ``int`` (3 in-scope columns)."""
        del desc
        return int(value)

    # Serves the 177 in-scope `char(n)` columns, which the driver reports as STRING.
    # VAR_STRING is pinned alongside it: the schema holds zero `varchar` columns, but a
    # `CAST(...

    def _string_to_python(
        self,
        value: bytes | bytearray | str,
        dsc: Any = None,
    ) -> str:
        """Return a ``CHAR`` column as ``str``, padding intact.

        Args:
            value: The column as the driver delivers it.
            dsc: The driver's column description tuple.

        Returns:
            The value decoded with the connection's character set.
        """
        del dsc
        if isinstance(value, (bytes, bytearray)):
            return value.decode(self.charset)
        return str(value)

    _var_string_to_python = _string_to_python


    @staticmethod
    def _float_to_python(value: Any, desc: Any = None) -> NoReturn:
        """Refuse a ``FLOAT`` column - rule R-2.

        Raises:
            BinaryFloatingPointError: Always.
        """
        del value, desc
        raise BinaryFloatingPointError(
            "rule R-2 violated at the transport layer: a FLOAT value reached "
            "acas_posting.dal.connection. No accounting value may pass "
            "through a binary floating-point type at any point - not in "
            "computation, not in storage, not in transport. The frozen schema "
            "mysql/ACASDB.sql declares zero FLOAT, DOUBLE and REAL columns, "
            "so this value cannot have come from an in-scope column."
        )

    @staticmethod
    def _double_to_python(value: Any, desc: Any = None) -> NoReturn:
        """Refuse a ``DOUBLE`` column - rule R-2.

        Raises:
            BinaryFloatingPointError: Always. See :meth:`_float_to_python` for the
                reasoning; ``DOUBLE`` is the same fault with a wider mantissa.
        """
        del value, desc
        raise BinaryFloatingPointError(
            "rule R-2 violated at the transport layer: a DOUBLE value reached "
            "acas_posting.dal.connection. No accounting value may pass "
            "through a binary floating-point type at any point - not in "
            "computation, not in storage, not in transport. The frozen schema "
            "mysql/ACASDB.sql declares zero FLOAT, DOUBLE and REAL columns, "
            "so this value cannot have come from an in-scope column."
        )


def transport_decimal_context() -> decimal.Context:
    """Return the decimal context this transport layer is exact under.

    A DELIBERATE context rather than an implicit one, but a narrow one.

    Returns:
        A fresh :class:`decimal.Context`, safe for the caller to mutate. >>> ctx =
            transport_decimal_context() >>> ctx.prec 28 >>> ctx.create_decimal("1.50") +
            ctx.create_decimal("0.25") Decimal('1.75').
    """
    return decimal.Context(
        prec=SCHEMA_MAX_DECIMAL_PRECISION * 2,
        # No rounding mode is nominated as "the" mode, because this context must never
        # round.
        traps=[
            decimal.Inexact,
            decimal.Rounded,
            decimal.InvalidOperation,
            decimal.DivisionByZero,
            decimal.Overflow,
        ],
    )


def cobol_string_delimited_by_space(field: str) -> str:
    """Return a fixed-width field as the COBOL ``STRING`` verb sends it.

    ``delimited by space`` means the sending item contributes its characters UP TO the
    first space and stops. Two consequences follow, and both are reproduced here rather
    than approximated by a trailing-space strip.

    Args:
        field: The fixed-width, space-padded field value.

    Returns:
        The characters before the first space, or ``""`` if the field starts with one.
    """
    return field.partition(" ")[0]


def quote_identifier(name: str) -> str:
    """Return a table or column name wrapped in backticks, ready for SQL.

    Note the ``delimited by space`` on the name itself: a COBOL key name is a fixed-
    width, space-padded item, so the bridge quotes only its significant characters.

    Args:
        name: The identifier, optionally space-padded to a COBOL field width.

    Returns:
        The identifier enclosed in backticks.

    Raises:
        ValueError: If the identifier is empty once the ``delimited by space`` rule has
            been applied, or if it contains a NUL.
    """
    significant = cobol_string_delimited_by_space(name)
    if not significant:
        raise ValueError(
            "an ACAS identifier cannot be empty: every table and column name "
            "in mysql/ACASDB.sql is a non-empty upper-case, hyphenated name "
            f"(received {name!r})"
        )
    if "\x00" in significant:
        raise ValueError(
            "an ACAS identifier cannot contain a NUL: MySQL forbids it, and "
            "no name in mysql/ACASDB.sql carries one "
            f"(received {name!r})"
        )
    escaped = significant.replace(IDENTIFIER_QUOTE, IDENTIFIER_QUOTE * 2)
    return f"{IDENTIFIER_QUOTE}{escaped}{IDENTIFIER_QUOTE}"


def _pic_x(text: str, width: int) -> str:
    """Fit a value to an alphanumeric picture of ``width`` characters.

    COBOL ``MOVE`` into a ``pic x(n)`` item truncates on the right and pads on the right
    with spaces. Reproduced locally, mirroring the same private helper in
    ``dal/status.py``, because this module may not import ``cobol/move.py``.

    Args:
        text: The sending value.
        width: The receiving item's declared character count.

    Returns:
        Exactly ``width`` characters.
    """
    return text[:width].ljust(width)


def rdb_data_from_system_record(system_record: SystemRecord) -> RdbData:
    """Copy the connection parameters out of ``SYSTEM-REC`` into ``RDB-Data``.

    All six receiving items are declared ``value spaces``
    [copybooks/wsfnctn.cob:L57-L62], so THE FROZEN SOURCE CARRIES NO CREDENTIAL and
    every value a connection ever uses originates in the ``SYSTEM-REC`` row.

    Args:
        system_record: The ``SYSTEM-REC`` row the caller already holds. Read only; this
            function mutates nothing.

    Returns:
        A fresh :class:`~acas_posting.records.file_access.RdbData`. The class is
            IMPORTED from the record layer and never redeclared here - one record shape,
            one owner.
    """
    rdb_data = RdbData()

    # All six sending items are `05` items of `03 System-Data-Block.`
    # [copybooks/wssystem.cob:L52], so the record layer exposes them on
    # `SystemRecord.system_data_block` rather than on the record itself.
    system_data_block = system_record.system_data_block

    # The six moves, in the frozen source's own order.
    rdb_data.db_schema = _pic_x(system_data_block.rdbms_db_name, 12)
    rdb_data.db_uname = _pic_x(system_data_block.rdbms_user, 12)
    rdb_data.db_upass = _pic_x(system_data_block.rdbms_passwd, 12)
    rdb_data.db_port = _pic_x(system_data_block.rdbms_port, _DB_PORT_WIDTH)
    rdb_data.db_host = _pic_x(system_data_block.rdbms_host, 32)
    rdb_data.db_socket = _pic_x(system_data_block.rdbms_socket, 64)

    return rdb_data


_LOADED_RDB_DATA: RdbData | None = None


def load_rdb_data_once(system_record: SystemRecord) -> RdbData:
    """Load the connection parameters on the first call and never again.

    ``A`` is assigned a record length inside the guarded block before any later call can
    test it, and the ``end-if`` [common/acas008.cbl:L564] closes AFTER the six moves, so
    from the second call onward the ENTIRE block - the record-length check and the
    credential load together - is skipped for the remainder of the run.

    Args:
        system_record: The ``SYSTEM-REC`` row. CONSULTED ONLY ON THE FIRST CALL; ignored
            on every later call, exactly as the guard ignores it.

    Returns:
        The one :class:`~acas_posting.records.file_access.RdbData` for this run.
    """
    global _LOADED_RDB_DATA  # noqa: PLW0603 - the `A = zero` sentinel

    if _LOADED_RDB_DATA is None:
        _LOADED_RDB_DATA = rdb_data_from_system_record(system_record)
    # `end-if` [common/acas008.cbl:L564]. No else branch exists in the frozen
    # source and none is added: a later call simply proceeds with whatever the
    # block already holds.
    return _LOADED_RDB_DATA


def rdb_data_is_loaded() -> bool:
    """Report whether the first-call-only load has already happened.

    The observable form of the COBOL's ``A`` sentinel, published so that a test can
    assert anomaly A-1 rather than infer it.

    Returns:
        ``True`` once :func:`load_rdb_data_once` has run in this process, ``False``
            before that and after :func:`reset_rdb_data_cache`.
    """
    return _LOADED_RDB_DATA is not None


def reset_rdb_data_cache() -> None:
    """Clear the first-call-only load so the next call reloads.

    THERE IS NO COBOL COUNTERPART, and that is stated plainly rather than disguised:
    nothing in the frozen source clears ``A``. It does not need to, because a COBOL run
    is a process and the sentinel dies with it.
    """
    global _LOADED_RDB_DATA  # noqa: PLW0603 - the `A = zero` sentinel

    _LOADED_RDB_DATA = None


def _atoi(text: str) -> int:
    """Convert leading digits to an ``int`` the way C's ``atoi`` does.

    The C interface the bridges link converts the port with a bare ``port =
    atoi(xport)`` and then hands the result straight to ``mysql_real_connect``. ``atoi``
    HAS NO FAILURE MODE.

    Args:
        text: The port characters, already reduced by the ``delimited by space`` rule
            and narrowed to the working-storage item's width.

    Returns:
        The converted value, or 0 when no digits were found.
    """
    body = text.lstrip(" \t\n\r\v\f")
    sign = 1
    if body[:1] in {"+", "-"}:
        if body[0] == "-":
            sign = -1
        body = body[1:]
    digits = ""
    for character in body:
        if not character.isdigit() or not character.isascii():
            break
        digits += character
    if not digits:
        return 0
    return sign * int(digits)


# =============================================================================
#  THE TRANSPORT AND CREDENTIAL POLICY  (CWE-798, CWE-295, CWE-319)
# =============================================================================
#  This is the ONE place in the migrated cycle that reaches a real server, so it
#  is the one place where two properties of the frozen source stop being
#  harmless facts about a 1980s accounting package and become live exposures.
#
#  1. THE CREDENTIALS ARE SOURCE LITERALS. `05 RDBMS-User pic x(12) value
#     "ACAS-User"` and `05 RDBMS-Passwd pic x(12) value "PaSsWoRd"`
#     [copybooks/wssystem.cob:L138-L139], each annotated `*> change in setup` by
#     the maintainer. `acas_posting/records/system_record.py` declares them
#     byte-for-byte because `SYSTEM-REC` is a dumped table and its declared
#     defaults are diff-visible (rule R-4), and it publishes them so that this
#     module can RECOGNISE them.
#  2. THE TRANSPORT IS PLAINTEXT. The C interface the bridges link calls
#     `mysql_real_connect(&sql, host, user, passwd, db, port, socket, 0)` with a
#     literal zero client-flag word, so `CLIENT_SSL` is never negotiated and the
#     password crosses the wire in the clear. On a loopback socket that is of no
#     consequence; to a server on another host it is the whole credential and
#     every posted figure, unprotected and unauthenticated.
#
#  WHAT IS NOT DONE ABOUT IT, AND WHY
#  ----------------------------------
#  Reading a credential from the process environment, a dotenv file or a
#  parameter file is NOT an option here, however conventional it would be. Rule
#  R-6 makes two runs of the same scenario byte-identical, and an ambient input
#  is exactly what breaks that; rule R-3 forbids adding anything the frozen
#  source does not have. So the credential keeps arriving where the frozen source
#  puts it - in the `SYSTEM-REC` row this module is handed - and this module never
#  reads its surroundings. A grep of this file for `os.environ`, `getenv` or
#  `dotenv` returns nothing, and it must stay that way.
#
#  WHAT IS DONE INSTEAD: ONE POLICY BOUNDARY, DECLARED BY THE DEPLOYMENT
#  --------------------------------------------------------------------
#  ⭐ THE POLICY IS ONE OBJECT, SET ONCE, AND EVERY OPEN RESOLVES TO IT.
#  :class:`ConnectionPolicy` is the whole of it, :func:`set_connection_policy`
#  installs it and :func:`connection_policy` reads it back. When a caller opens
#  without a declaration of its own - `transport=None`, which is the default of
#  every handler in this package - :func:`mysql_1000_open` resolves the omission
#  FROM THAT ONE POLICY. So the twenty handler modules above this one need know
#  nothing about transport: whatever the deployment declared before the first
#  `fn-Open` is what every one of them gets, and there is exactly one place to
#  look to find out what that was.
#
#  ⛔ AND THE DEFAULT DOES NOT REFUSE, WHICH IS A DELIBERATE CORRECTION.
#  An earlier revision of this module failed CLOSED: a target that was neither a
#  loopback address nor a Unix socket was REFUSED unless the caller declared
#  `isolated_oracle=True`, and a row still carrying the shipped placeholders was
#  REFUSED unless the caller declared them intended. That was withdrawn, for two
#  reasons that agree:
#
#    * IT WAS A VALIDATION THE MIGRATED CYCLE DOES NOT HAVE. Rule R-3 forbids
#      adding one. `Mysql-1000-Open` calls `MySQL_real_connect` and reports what
#      the server says [copybooks/mysql-procedures.cpy:L72-L77]; it inspects
#      neither the host nor the credential, so a refusal before the connect call
#      is behaviour the compiled program cannot produce.
#    * IT BLOCKED THE DOCUMENTED CYCLE OUTRIGHT. The comparison database runs in
#      a container reached at a private, NON-loopback address
#      (`harness/docker-compose.yml`), so the fail-closed default refused every
#      posting run before a single figure was written - and it did so through a
#      declaration no entry point could make, since the policy was reachable only
#      as a keyword on individual handler calls. A guard that stops the cycle it
#      is guarding is not hardening.
#
#  WHAT REPLACES IT: SAY SO, LOUDLY, AND STILL PROCEED
#  --------------------------------------------------
#  Each exposure now produces a WARNING log record on the open that carries it,
#  and the connect proceeds. A log record is presentation: Agent Action Plan
#  section 0.3.4 requires that a diagnostic "must not alter control flow and must
#  not appear in any table dump", and neither of these does. Nothing is silently
#  reclassified - in particular a remote host is NEVER treated as an isolated
#  oracle by inference, it is simply reported as unprotected - and no message
#  names the host, the account or the schema, so the diagnostic itself leaks
#  nothing (CWE-532).
#
#  STRICTNESS REMAINS AVAILABLE, AS AN EXPLICIT DEPLOYMENT DECLARATION
#  ------------------------------------------------------------------
#  A deployment that wants the refusal back asks for it, at the boundary, in one
#  place, and gets it for every handler at once:
#
#    * `ConnectionPolicy(transport=TransportSecurity(ca_file=...))` turns on TLS
#      with certificate AND host-name verification, which is protection rather
#      than decoration (CWE-295);
#    * `ConnectionPolicy(require_encrypted_transport=True)` restores the refusal
#      of unprotected non-local targets (CWE-319);
#    * `ConnectionPolicy(require_declared_placeholder_credentials=True)` restores
#      the refusal of the shipped placeholder credentials (CWE-798).
#
#  Both refusals stay off unless asked for, so the shipped behaviour of the
#  migrated cycle is the compiled behaviour and the security surface is a
#  deployment choice - which is the only division that satisfies R-3 and CWE-319
#  at the same time.
#
#  WHY THIS CHANGES NO BEHAVIOUR THAT IS COMPARED
#  ---------------------------------------------
#  The two refusals that remain reachable are opt-in, and one further refusal is
#  not a policy at all: a client certificate supplied without its private key, or
#  a key without its certificate, cannot authenticate anything, and no legacy path
#  can produce that pair because the frozen C interface supplies no TLS material
#  whatsoever. Every refusal RAISES. None of them returns a COBOL status, and that
#  is deliberate: `(FS-Reply 99, We-Error 911)` is what the frozen paragraph
#  produces for a failed connect [copybooks/mysql-procedures.cpy:L127-L128], and
#  manufacturing that pair for a policy refusal would make a refusal
#  indistinguishable from a genuine connect failure - the caller would carry on
#  along the frozen error path as though the server had answered. Raising a type
#  no COBOL path can produce keeps the two apart. It is the same reasoning
#  `_assert_converter_pinned` is given (rule R-2): a broken migration guarantee
#  is not a state the frozen program can be in, so there is nothing to degrade
#  to.
#
#  And once a connection IS permitted, nothing here touches it. The six
#  `RDB-Data` items are marshalled exactly as before, the port still narrows
#  through `pic x(4)`, no value is validated, and the TLS arguments are
#  additional driver keywords that alter the wire and nothing above it. No stored
#  value, no status pair, no statement text and no table dump moves by a
#  character (rules R-3, R-4).
#
#  DETERMINISM. The policy is an explicit object installed by the caller, never
#  read from the process environment or any other ambient source by this module,
#  and :func:`_target_is_local` judges a host by what it says rather than by what
#  a name service would say about it. Two runs of one scenario therefore resolve
#  the same policy to the same verdict (rule R-6).
# =============================================================================

#: Host names that name the local machine, compared lower-case. Numeric loopback
#: addresses are NOT listed.
LOOPBACK_HOST_NAMES: Final[frozenset[str]] = frozenset(
    {"localhost", "localhost.localdomain"}
)


class ConnectionPolicyError(RuntimeError):
    """A connection was refused by this module's own policy, not by a server.

    Raised, never reported as a COBOL status, for the reason argued in the section
    comment above: a policy refusal must not be mistakable for the ``(99, 911)`` the
    frozen paragraph produces when a server declines.
    """


class FrozenPlaceholderCredentialsError(ConnectionPolicyError):
    """The `SYSTEM-REC` row still carries the maintainer's shipped credentials.

    `05 RDBMS-User pic x(12) value "ACAS-User"` and `05 RDBMS-Passwd pic x(12) value
    "PaSsWoRd"` [copybooks/wssystem.cob:L138-L139] are published in the frozen source
    and in this repository, so a connection authenticated by them is a connection anyone
    reading the source can make.
    """


class InsecureTransportError(ConnectionPolicyError):
    """A non-local connection would have crossed the network in the clear.

    Either supply a certificate authority in :class:`TransportSecurity` so the server is
    authenticated and the session encrypted, or declare ``isolated_oracle=True`` to
    state that the target is the parity harness on a private network with no TLS
    available.
    """


@dataclass(frozen=True, slots=True)
class TransportSecurity:
    """The caller's declaration about how the connection may cross the network.

    Frozen and slotted, like every other value object in this layer: a policy is
    a decision the caller has already taken, not something this module edits.

    An instance with every field at its default declares plaintext with no
    verification, which is exactly what the frozen C interface negotiates
    [copybooks/mysql-procedures.cpy:L72-L77]. It is NOT a refusal: what an
    unprotected non-local target leads to - a warning, or a refusal - belongs to
    :class:`ConnectionPolicy`, the one installed policy, and not to this object.
    A caller that passes nothing at all gets the installed policy's declaration
    rather than an instance of this class made up on the spot; see
    :func:`mysql_1000_open`.

    Attributes:
        ca_file: Path to the certificate authority bundle the server's certificate is
            verified against.
        certificate_file: Path to a client certificate, when the server requires one.
            Must be given together with ``key_file``.
        key_file: Path to the private key for ``certificate_file``.
        isolated_oracle: Declares that the target is the comparison harness on a private
            network whose server has no TLS configured at all - the situation the
            harness genuinely runs in - and that a plaintext connection to it is
            intended.
    """

    ca_file: str | None = None
    certificate_file: str | None = None
    key_file: str | None = None
    isolated_oracle: bool = False

    def __post_init__(self) -> None:
        """Reject half a client-certificate pair, at construction.

        ⭐ M-06.  THIS CHECK USED TO RUN ON THE PARITY PATH, inside
        `_require_permitted_connection` and therefore inside
        :func:`mysql_1000_open`. It has moved here because it is not a statement
        about the connection at all - it is an invariant of THIS PYTHON OBJECT,
        which has no frozen counterpart: the frozen `Mysql-1000-Open`
        [copybooks/mysql-procedures.cpy:L60-L128] passes no TLS material of any
        kind. A certificate without its key cannot authenticate anything, so an
        instance carrying one is malformed rather than insecure, and rejecting it
        where it is BUILT keeps the refusal off every path a posting program can
        reach: a default `TransportSecurity()` can never trip it.

        Raises:
            InsecureTransportError: One of ``certificate_file`` and ``key_file``
                was supplied without the other.
        """
        if bool(self.certificate_file) != bool(self.key_file):
            raise InsecureTransportError(
                "TransportSecurity needs certificate_file and key_file "
                "together: a client certificate cannot authenticate without "
                "its private key"
            )

    def verifies_the_server(self) -> bool:
        """Report whether this policy authenticates and encrypts the session.

        Returns:
            ``True`` when a certificate authority was supplied, which is the only
                configuration this module treats as protected.
        """
        return bool(self.ca_file)

    def driver_arguments(self) -> dict[str, Any]:
        """Render the policy as driver keyword arguments.

        Returns:
            The ``ssl_*`` keywords, or an empty mapping when no certificate
            authority was supplied. The empty case is deliberate: it leaves the
            connect call byte-for-byte as it was before this policy existed, so
            a permitted plaintext connection behaves exactly as the frozen C
            interface's does. The empty case is always permitted on the parity
            path (M-06); :func:`audit_connection_policy` reports it as a concern
            and :func:`require_connection_policy` is the separate opt-in gate that
            refuses it.
        """
        if not self.ca_file:
            return {}
        arguments: dict[str, Any] = {
            "ssl_ca": self.ca_file,
            # Both, always, and never one without the other.
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_disabled": False,
        }
        if self.certificate_file:
            arguments["ssl_cert"] = self.certificate_file
        if self.key_file:
            arguments["ssl_key"] = self.key_file
        return arguments


@dataclass(frozen=True, slots=True)
class ConnectionPolicy:
    """The ONE connection policy of the process, installed by the deployment.

    ⭐ THIS IS THE SINGLE BOUNDARY. Every handler in this package opens without a
    transport declaration of its own, and :func:`mysql_1000_open` resolves that
    omission here, so one installed policy governs all twenty of them. A handler
    that DOES pass a declaration still wins for its own call - the per-call
    keyword is the narrower statement - but no handler needs to, and none of them
    should invent one, because a policy declared privately in one handler is
    exactly the inconsistency this object exists to remove.

    NO COBOL COUNTERPART, AND NOTHING COMPARED MOVES BY A CHARACTER. The frozen
    C interface passes host, user, password, schema, port and socket and a literal
    zero client-flag word [copybooks/mysql-procedures.cpy:L72-L77]; it has no
    notion of transport security at all. This object decides which connections
    this module PERMITS and what it SAYS about them, never what is stored, which
    statement is issued or which status pair is produced (rules R-3, R-4).

    THE DEFAULT INSTANCE PERMITS EVERYTHING AND WARNS ABOUT WHAT IS EXPOSED,
    which is the disposition argued in the section comment above: the compiled
    program performs no such check, and the comparison database is reached at a
    private non-loopback container address, so a refusing default would block the
    migrated cycle rather than protect it. Both refusals are available, and both
    have to be asked for.

    Frozen and slotted, like :class:`TransportSecurity`: a policy is a decision
    the deployment has already taken, not something this module edits.

    Attributes:
        transport: The transport declaration every open that makes none of its
            own resolves to. ``None`` - the default - means plaintext, exactly as
            the frozen C interface connects. Supply
            ``TransportSecurity(ca_file=...)`` to encrypt and verify.
        require_encrypted_transport: ``True`` refuses a non-local target that is
            neither verified by a certificate authority nor declared an isolated
            oracle, raising :class:`InsecureTransportError` (CWE-319). ``False``
            - the default - reports the exposure as a warning and proceeds.
        require_declared_placeholder_credentials: ``True`` refuses a
            ``SYSTEM-REC`` row still carrying the maintainer's shipped
            ``"ACAS-User"`` / ``"PaSsWoRd"`` [copybooks/wssystem.cob:L138-L139]
            unless the opening call declares them intended, raising
            :class:`FrozenPlaceholderCredentialsError` (CWE-798). ``False`` - the
            default - reports the exposure as a warning and proceeds, which is
            what the compiled program does: it hands the row's values to the
            server and reports whatever the server says.
        allow_frozen_placeholder_credentials: ``True`` declares, once for the
            whole process, that the shipped placeholders are the intended
            credentials and the server is disposable. It silences the warning and
            satisfies ``require_declared_placeholder_credentials``. The harness
            declares this; a production deployment should not need to, because
            its row carries real credentials.
    """

    transport: TransportSecurity | None = None
    require_encrypted_transport: bool = False
    require_declared_placeholder_credentials: bool = False
    allow_frozen_placeholder_credentials: bool = False

    def declared_transport(self) -> TransportSecurity:
        """Return the transport declaration to apply when a caller made none.

        Returns:
            The installed :class:`TransportSecurity`, or one at its own defaults
            - plaintext, unverified - when the policy names none. Never ``None``,
            so callers have one type to reason about.
        """
        return TransportSecurity() if self.transport is None else self.transport


#: The installed policy. Module state, exactly as :data:`_PROCESS_CONNECTION` and
#: :data:`_LOADED_RDB_DATA` are, and for the same reason: the frozen system has
#: ONE connection, established once per run, so the policy governing it is
#: process-wide too. Rebound only by :func:`set_connection_policy` and
#: :func:`reset_connection_policy`; never mutated, because the object is frozen.
_CONNECTION_POLICY: ConnectionPolicy = ConnectionPolicy()


def set_connection_policy(policy: ConnectionPolicy) -> None:
    """Install the process connection policy. THE boundary, called once.

    Called by the deployment before the run's first ``fn-Open`` - in this package
    that is :mod:`acas_posting.cli.args`, on the one path all seven entry points
    funnel through - and by the comparison harness, which declares its private
    container network. Nothing below the entry points calls it: a handler or a
    program module that installed a policy would be declaring on behalf of a
    deployment it cannot see.

    Idempotent and order-independent in the only way that matters: the policy is
    consulted at every open rather than captured at the first one, so installing
    it before the first open and installing it again later differ only in which
    opens see it.

    Args:
        policy: The policy to install. Frozen, so the caller cannot change it
            afterwards by accident.

    Raises:
        TypeError: The argument is not a :class:`ConnectionPolicy`. A PROGRAMMER
            error, and refused rather than coerced so that a caller passing a
            bare :class:`TransportSecurity` finds out immediately.
    """
    global _CONNECTION_POLICY  # noqa: PLW0603 - the one installed policy

    if not isinstance(policy, ConnectionPolicy):
        raise TypeError(
            "set_connection_policy takes a ConnectionPolicy, not "
            f"{type(policy).__name__}"
        )
    _CONNECTION_POLICY = policy
    #  DEBUG, and it names no host, no account and no schema - the policy's own
    #  fields are paths and booleans, never a credential (CWE-532).
    _LOG.debug(
        "connection policy installed: transport=%r require_encrypted_transport=%s "
        "require_declared_placeholder_credentials=%s "
        "allow_frozen_placeholder_credentials=%s",
        policy.transport,
        policy.require_encrypted_transport,
        policy.require_declared_placeholder_credentials,
        policy.allow_frozen_placeholder_credentials,
    )


def connection_policy() -> ConnectionPolicy:
    """Return the installed process connection policy.

    Returns:
        The policy :func:`set_connection_policy` installed, or a
        :class:`ConnectionPolicy` at its defaults when none was installed.
    """
    return _CONNECTION_POLICY


def reset_connection_policy() -> None:
    """Restore the default policy, discarding whatever was installed.

    For a test or a harness step that must start from a known boundary, and the
    counterpart of :func:`reset_process_connection` and
    :func:`reset_rdb_data_cache`. Not part of any migrated path.
    """
    global _CONNECTION_POLICY  # noqa: PLW0603 - the one installed policy

    _CONNECTION_POLICY = ConnectionPolicy()


def _target_is_local(parameters: Mapping[str, Any]) -> bool:
    """Report whether the connect target is on this machine.

    A Unix socket cannot leave the machine, and a loopback address does not reach a
    network, so neither carries the password anywhere an eavesdropper can be. Everything
    else is treated as remote.

    Args:
        parameters: The driver keyword arguments :func:`connection_parameters` produced.
            Only ``unix_socket`` and ``host`` are consulted; the TLS keywords are
            ignored here.

    Returns:
        ``True`` for a socket, an absent host, a loopback host name or any loopback IP
            address.
    """
    if "unix_socket" in parameters:
        return True

    host = str(parameters.get("host", "")).strip()
    if not host:
        # A blank `DB-Host` omits the key, and the driver's own default is the loopback
        # address 127.0.0.1.
        return True
    if host.lower() in LOOPBACK_HOST_NAMES:
        return True

    try:
        # `strip("[]")` because a literal IPv6 address is conventionally bracketed in a
        # host field.
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


#: The stable transport tokens :func:`transport_category` can return.
#:
#: FIVE TOKENS, AND NOTHING ELSE MAY REACH A LOG RECORD ABOUT THE ENDPOINT. A
#: diagnostic that names the host, the schema, the account, the port or the
#: socket path hands an attacker the reconnaissance half of the work for free
#: (CWE-532), and it also makes two runs against two deployments produce
#: different text for the same event. Each token below answers the only question
#: an operator has - can the credentials and the posted figures be read off the
#: wire - and answers it identically on every deployment.
TRANSPORT_CATEGORIES: Final[tuple[str, ...]] = (
    "local-socket",
    "loopback-tcp",
    "tls-verified",
    "isolated-network",
    #  DECLARED AND UNDECLARED PLAINTEXT ARE NOT THE SAME EVENT, and one token
    #  for both would assert something no caller said. `isolated-network` is the
    #  harness's link, permitted BECAUSE `TransportSecurity(isolated_oracle=True)`
    #  declared the server private; `unverified` is the same wire with nobody
    #  having said so. `harness/dump_tables.py` draws the identical distinction
    #  under the identical two names, so a reader comparing the two sides of the
    #  comparison sees one vocabulary.
    "unverified",
)


def transport_category(
    parameters: Mapping[str, Any],
    security: TransportSecurity | None = None,
) -> str:
    """Classify a connect target into a stable token that is safe to log.

    Derived from the SHAPE of the target and from the caller's declared policy,
    never from the identity of either, so the result carries no host name, no
    schema, no account, no port and no path - and is identical for every
    connection of the same kind (CWE-532).

    NOT A POLICY DECISION. Whether a connection is PERMITTED is decided by
    ``_require_permitted_connection``, which reads the same two inputs and
    raises; this function only names what was decided, and is consulted by log
    sites and by nothing else.

    Args:
        parameters: the driver keyword arguments
            :func:`connection_parameters` produced. Only the presence of
            ``unix_socket`` and the shape of ``host`` are consulted.
        security: the caller's declaration, or ``None`` for the fail-closed
            default.

    Returns:
        One of :data:`TRANSPORT_CATEGORIES`. ``"local-socket"`` for a Unix
        socket, ``"loopback-tcp"`` for an address that does not reach a network,
        ``"tls-verified"`` when a certificate authority was supplied and so the
        server is authenticated and the session encrypted, and
        ``"isolated-network"`` for the harness's declared plaintext link to a
        private server, and ``"unverified"`` for the same unencrypted wire with
        NO declaration at all - which is reported and permitted, because the
        frozen open applies no such check, unless the installed policy asked for
        a refusal.

        >>> transport_category({"unix_socket": "/run/mysqld/mysqld.sock"})
        'local-socket'
        >>> transport_category({"host": "127.0.0.1"})
        'loopback-tcp'
        >>> transport_category({"host": "db.internal"},
        ...                    TransportSecurity(ca_file="/etc/ssl/ca.pem"))
        'tls-verified'
        >>> transport_category({"host": "db.internal"},
        ...                    TransportSecurity(isolated_oracle=True))
        'isolated-network'
        >>> transport_category({"host": "db.internal"})
        'unverified'
    """
    policy = security or TransportSecurity()
    if policy.verifies_the_server():
        return "tls-verified"
    if "unix_socket" in parameters:
        return "local-socket"
    if _target_is_local(parameters):
        return "loopback-tcp"
    #  NOTHING HERE INFERS THAT A REMOTE HOST IS PRIVATE. Only an explicit
    #  declaration can say that, which is why the undeclared case is named for
    #  what is known about it and not for what would be convenient to assume -
    #  the same rule `_require_permitted_connection`'s warning follows when it
    #  calls such a target UNPROTECTED.
    if policy.isolated_oracle:
        return "isolated-network"
    return "unverified"


def _require_permitted_connection(
    system_record: SystemRecord,
    parameters: Mapping[str, Any],
    transport: TransportSecurity,
    *,
    allow_frozen_placeholder_credentials: bool,
    policy: ConnectionPolicy,
) -> None:
    """Apply the one connection policy, in one place, before the connect call.

    The whole of the policy argued in the section comment above, applied
    immediately before the connect call and nowhere else. It REPORTS an exposure
    and permits the connection unless the installed policy asked for the refusal:
    the compiled program performs no such check, so refusing by default would be
    a validation the migrated cycle has not got (rule R-3).

    Args:
        system_record: The row the credentials came from.
        parameters: The driver keyword arguments, used to judge locality.
        transport: The transport declaration in force for this call - the
            caller's own if it made one, otherwise the installed policy's.
        allow_frozen_placeholder_credentials: The declaration in force for this
            call - the caller's own if it made one, otherwise the installed
            policy's.
        policy: The installed process policy, consulted for the two
            ``require_*`` switches and for nothing else.

    Raises:
        FrozenPlaceholderCredentialsError: The row still carries a shipped
            credential, no declaration was made, AND the installed policy sets
            ``require_declared_placeholder_credentials``.
        InsecureTransportError: A client certificate was supplied without its key
            or a key without its certificate, which cannot authenticate anything;
            or the target is not local, is neither verified nor declared an
            isolated oracle, AND the installed policy sets
            ``require_encrypted_transport``.
    """
    concerns: list[str] = []

    if (
        carries_frozen_placeholder_rdbms_credentials(system_record)
        and not allow_frozen_placeholder_credentials
    ):
        if policy.require_declared_placeholder_credentials:
            raise FrozenPlaceholderCredentialsError(
                "SYSTEM-REC still carries the placeholder RDBMS credentials "
                "declared at [copybooks/wssystem.cob:L138-L139] and the "
                "installed ConnectionPolicy requires an explicit declaration; "
                "supply real credentials in the row, or declare "
                "allow_frozen_placeholder_credentials=True for a disposable "
                "server"
            )
        #  REPORTED AND PERMITTED. The compiled system hands the row's values to
        #  the server and reports what the server says, so this must too. Named
        #  fields only: no host, no account, no password (CWE-532).
        _LOG.warning(
            "Mysql-1000-Open: SYSTEM-REC still carries the placeholder RDBMS "
            "credentials published at [copybooks/wssystem.cob:L138-L139]; the "
            "connection proceeds because the compiled program applies no such "
            "check (CWE-798). Install ConnectionPolicy("
            "require_declared_placeholder_credentials=True) to refuse instead"
        )

    #  NOT A POLICY, A CONTRADICTION, and it stays a refusal whatever the policy
    #  says. No legacy path can reach it: the frozen C interface supplies no TLS
    #  material at all [copybooks/mysql-procedures.cpy:L72-L77], so only a caller
    #  that half-configured this module's own addition can produce it.
    if bool(transport.certificate_file) != bool(transport.key_file):
        raise InsecureTransportError(
            "TransportSecurity needs certificate_file and key_file together: "
            "a client certificate cannot authenticate without its private key"
        )

    if _target_is_local(parameters):
        return tuple(concerns)

    if transport.verifies_the_server():
        return tuple(concerns)

    if transport.isolated_oracle:
        # Logged without the host, the account or the schema.
        _LOG.warning(
            "Mysql-1000-Open: plaintext transport to a non-local server "
            "permitted by an explicit isolated_oracle declaration; "
            "credentials and posted figures are unprotected on this connection"
        )
        return

    if policy.require_encrypted_transport:
        raise InsecureTransportError(
            "the connect target is not a loopback address or a Unix socket and "
            "the installed ConnectionPolicy requires an encrypted transport, so "
            "the credentials from [copybooks/wssystem.cob:L138-L139] and every "
            "posted figure would cross the network in the clear: supply "
            "TransportSecurity(ca_file=...) to verify and encrypt, or declare "
            "TransportSecurity(isolated_oracle=True) for the parity harness"
        )

    #  REPORTED AND PERMITTED, and the wording matters: the target is called
    #  UNPROTECTED, never "isolated". Nothing here infers that a remote host is
    #  private - that is a declaration only a caller can make - so no host is
    #  ever silently reclassified as safe.
    _LOG.warning(
        "Mysql-1000-Open: the connect target is neither a loopback address nor "
        "a Unix socket and the session is not encrypted, so the credentials "
        "from [copybooks/wssystem.cob:L138-L139] and every posted figure cross "
        "the network in the clear (CWE-319). The connection proceeds because "
        "the compiled program applies no such check; supply "
        "ConnectionPolicy(transport=TransportSecurity(ca_file=...)) to encrypt "
        "and verify, or ConnectionPolicy(require_encrypted_transport=True) to "
        "refuse instead"
    )
    return tuple(concerns)


def audit_connection_policy(
    system_record: SystemRecord,
    parameters: Mapping[str, Any],
    transport: TransportSecurity,
    *,
    allow_frozen_placeholder_credentials: bool,
) -> tuple[str, ...]:
    """Report the policy concerns about one connection. NEVER refuses.

    ⭐ M-06.  THIS IS THE WHOLE OF `_require_permitted_connection`, TURNED FROM
    REFUSALS INTO FINDINGS. That function ran on the parity path - it was called
    from :func:`mysql_1000_open`, which reproduces ``Mysql-1000-Open``
    [copybooks/mysql-procedures.cpy:L60-L128] - and it raised two exception types
    the frozen paragraph cannot produce. The frozen paragraph has exactly two
    outcomes: it connects, or it reports ``(FS-Reply 99, We-Error 911)``
    [copybooks/mysql-procedures.cpy:L127-L128]. It does not inspect whose
    credentials it was given and it does not care where the server is. So the
    refusals were dispositions absent from compiled behaviour, and rule R-3
    forbids adding one however well-motivated it is.

    The analysis was not wrong about the exposure, and none of it is discarded:

      * ``05 RDBMS-User pic x(12) value "ACAS-User"`` and
        ``05 RDBMS-Passwd pic x(12) value "PaSsWoRd"``
        [copybooks/wssystem.cob:L138-L139] are published in this repository, so a
        connection authenticated by them is one any reader of the source can make.
      * A plaintext connection to a non-local server puts those credentials and
        every posted figure on the wire in the clear.

    Both are now reported rather than enforced. :func:`mysql_1000_open` logs each
    concern at WARNING - a diagnostic with no database effect and no effect on
    control flow, which is Agent Action Plan section 0.3.4's first class - and
    :func:`require_connection_policy` is the explicitly separate deployment gate
    that still REFUSES for a caller that wants it to. Nothing in the migrated
    cycle calls that gate.

    NO CREDENTIAL, HOST, ACCOUNT OR SCHEMA APPEARS IN A MESSAGE (CWE-532). The
    concern says what is wrong and what declaration would settle it, never to whom
    the connection was about to be made.

    Args:
        system_record: The row the credentials came from.
        parameters: The driver keyword arguments, used to judge locality.
        transport: The caller's transport declaration.
        allow_frozen_placeholder_credentials: The caller's credential
            declaration. ``True`` suppresses the credential concern, because the
            caller has stated that the exposure is intended.

    Returns:
        One string per concern, or an empty tuple when there is none. An empty
        tuple does not promise the connection will succeed - only that these
        exposures are absent.
    """
    concerns: list[str] = []

    if (
        carries_frozen_placeholder_rdbms_credentials(system_record)
        and not allow_frozen_placeholder_credentials
    ):
        concerns.append(
            "SYSTEM-REC still carries the placeholder RDBMS credentials "
            "declared at [copybooks/wssystem.cob:L138-L139], which are "
            "published in this repository; supply real credentials in the row, "
            "or pass allow_frozen_placeholder_credentials=True to declare that "
            "this server is disposable"
        )

    if _target_is_local(parameters):
        return tuple(concerns)

    if transport.verifies_the_server():
        return tuple(concerns)

    concerns.append(
        "the connect target is not a loopback address or a Unix socket, so the "
        "credentials from [copybooks/wssystem.cob:L138-L139] and every posted "
        "figure cross the network in the clear"
        + (
            "; permitted by the caller's explicit isolated_oracle declaration"
            if transport.isolated_oracle
            else ": supply TransportSecurity(ca_file=...) to verify and encrypt, "
            "or declare TransportSecurity(isolated_oracle=True) for the parity "
            "harness"
        )
    )
    return tuple(concerns)


def require_connection_policy(
    system_record: SystemRecord,
    parameters: Mapping[str, Any],
    transport: TransportSecurity,
    *,
    allow_frozen_placeholder_credentials: bool = False,
) -> None:
    """Refuse a connection the caller has not declared safe. OFF the parity path.

    ⭐ M-06.  THE FAIL-CLOSED GATE, KEPT AND MADE OPT-IN. It is the same policy
    :func:`audit_connection_policy` reports, raised instead of returned, and it is
    published so that an orchestrator or a deployment script can still refuse
    before a run rather than merely be told. NOTHING IN `acas_posting` CALLS IT -
    verify with a grep - which is what makes it "outside the parity path"
    structurally rather than by convention. A posting program cannot be affected
    by a function it has no route to.

    :func:`mysql_1000_open` deliberately does NOT call this. Calling it there is
    what the finding was about: it put two exception types on a path whose frozen
    counterpart has only ``connect`` and ``(FS-Reply 99, We-Error 911)``
    [copybooks/mysql-procedures.cpy:L127-L128] between them.

    Args:
        system_record: The row the credentials came from.
        parameters: The driver keyword arguments :func:`connection_parameters`
            produced.
        transport: The caller's transport declaration.
        allow_frozen_placeholder_credentials: ``True`` declares that the shipped
            placeholder credentials are intended and the server disposable.

    Raises:
        FrozenPlaceholderCredentialsError: The row still carries a shipped
            credential and the caller did not declare that it intends to.
        InsecureTransportError: The target is not local, no certificate authority
            was supplied and no isolated-oracle declaration was made.
    """
    for concern in audit_connection_policy(
        system_record,
        parameters,
        transport,
        allow_frozen_placeholder_credentials=(
            allow_frozen_placeholder_credentials
        ),
    ):
        if concern.startswith("SYSTEM-REC still carries"):
            raise FrozenPlaceholderCredentialsError(concern)
        if "permitted by the caller's explicit isolated_oracle" in concern:
            # The caller declared this one; it is reported, not refused.
            continue
        raise InsecureTransportError(concern)


def connection_parameters(
    rdb_data: RdbData, *, transport: TransportSecurity | None = None
) -> dict[str, Any]:
    """Build the driver's keyword arguments from the ``RDB-Data`` block.

    Reproduces the bridge's own parameter marshalling
    [common/glpostingMT.cbl:L394-L416], which loads the six ``RDB-Data`` items into
    the six working-storage items ``MySQL_real_connect`` is called with. That
    call's argument list is host, USER, password, base, port, socket
    [copybooks/mysql-procedures.cpy:L72-L77], and its second argument is
    ``Ws-Mysql-Implementation`` - anomaly A-3, a variable whose name says nothing
    about the user name it carries [common/glpostingMT.cbl:L402-L404]:

    ============================= ================================ ==========
    ``RDB-Data`` item             COBOL working-storage item       Driver
    ============================= ================================ ==========
    ``DB-Host``     x(32)  [:L60] ``Ws-Mysql-Host-Name``    x(64)  ``host``
    ``DB-UName``    x(12)  [:L58] ``Ws-Mysql-Implementation`` x(64) ``user``
    ``DB-UPass``    x(12)  [:L59] ``Ws-Mysql-Password``     x(64)  ``password``
    ``DB-Schema``   x(12)  [:L57] ``Ws-Mysql-Base-Name``    x(64)  ``database``
    ``DB-Port``     x(5)   [:L62] ``Ws-Mysql-Port-Number``  x(4)   ``port``
    ``DB-Socket``   x(64)  [:L61] ``Ws-Mysql-Socket``       x(64)  ``unix_socket``
    ============================= ================================ ==========

    ``DB-Port`` IS A CHARACTER FIELD, declared ``pic x(5)``
    [copybooks/wsfnctn.cob:L62], and the item it is strung into is narrower still
    at ``pic x(4)`` [copybooks/mysql-variables.cpy:L91], so the port travels
    through the whole COBOL side as text. Two consequences are reproduced:

    * THE NARROWING IS OBSERVABLE. ``STRING`` stops when its receiving item is
      full, so a five-digit port loses its fifth character
      [common/glpostingMT.cbl:L410-L412] and no port above 9999 can be expressed -
      ``"13306"`` reaches the client library as 1330. A limitation of the frozen
      source, not a defect to repair (anomaly A-5).
    * THE CONVERSION CANNOT FAIL. The C interface converts with ``atoi`` and passes
      the result straight on, so a malformed port silently becomes a different port
      or the default. See :func:`_atoi`; NO PORT VALIDATION IS PERFORMED, because a
      new validation is forbidden by R-3 and a defect fixed is a failure under R-4
      (anomaly A-4).

    The widening from characters to the integer the driver wants happens HERE and
    nowhere else, because the C interface takes a numeric fifth argument
    [copybooks/mysql-procedures.cpy:L76] and the Python driver takes an ``int``.
    ``port`` is therefore ALWAYS present in the returned mapping, mirroring the C
    call, which always passes one: a blank ``DB-Port`` yields 0, precisely what the
    C passes and what the client library reads as "use your default port".

    A BLANK TEXT ITEM MEANS UNSET, and omitting its key is how that is expressed.
    The ``delimited by space`` clause on each of the six STRING statements makes an
    all-spaces item contribute nothing, so the C interface receives an empty string
    and its client library reads that as "no value supplied". Two of the six are
    ``value spaces`` in the maintainer's own defaults - ``RDBMS-Host`` and
    ``RDBMS-Socket`` [copybooks/wssystem.cob:L143-L144] - so this is the ordinary
    case, not an edge one. Supplying an empty string instead would ask the driver
    to connect to a host named "".

    THREE SOCKET VALUES ALSO MEAN "NO SOCKET". Before calling
    ``mysql_real_connect`` the C interface compares the socket item against
    ``"0"``, ``"null"`` and ``"NULL"`` and substitutes a null pointer, so those
    spellings behave exactly like a blank item. Reproduced via
    :data:`_SOCKET_MEANS_NONE` (anomaly A-6); without it a ``DB-Socket`` of ``"0"``
    would send the driver looking for a socket file named ``0``.

    THE TRANSPORT KEYWORDS ARE THE ONE ADDITION, AND THEY ARE OPT-IN. The frozen
    C interface passes a literal zero client-flag word, so it negotiates no TLS
    at all; when ``transport`` is omitted this function therefore returns
    precisely the six-item mapping it always did, and the connect call is
    byte-for-byte the frozen one. When a caller supplies a certificate authority,
    its ``ssl_*`` keywords are merged in. They affect the wire and nothing above
    it: no ``RDB-Data`` item is re-read, no value is validated and no stored
    value moves (rules R-3, R-4). A connection without them is always permitted on
    the parity path (M-06) - :func:`audit_connection_policy` reports it and
    :func:`require_connection_policy` is the separate opt-in gate that refuses it -
    and either way this function marshals, it does not judge.

    Args:
        rdb_data: The block :func:`load_rdb_data_once` produced.
        transport: The caller's transport declaration, or ``None`` for the frozen
            plaintext behaviour. See :class:`TransportSecurity`.

    Returns:
        The driver keyword arguments: the four text items that are set, plus ``port``
            always, plus the ``ssl_*`` keywords when ``transport`` authenticates the
            server.
    """
    # Each of the six values is extracted exactly as the bridge extracts it - up to the
    # first space - so that a blank item yields "" and an item with an embedded space is
    # truncated where the COBOL truncates it.
    host = cobol_string_delimited_by_space(rdb_data.db_host)
    user = cobol_string_delimited_by_space(rdb_data.db_uname)
    password = cobol_string_delimited_by_space(rdb_data.db_upass)
    database = cobol_string_delimited_by_space(rdb_data.db_schema)
    port_text = cobol_string_delimited_by_space(rdb_data.db_port)
    socket_path = cobol_string_delimited_by_space(rdb_data.db_socket)

    parameters: dict[str, Any] = {}
    if host:
        parameters["host"] = host
    if user:
        parameters["user"] = user
    if password:
        parameters["password"] = password
    if database:
        parameters["database"] = database
    if socket_path and socket_path not in _SOCKET_MEANS_NONE:
        parameters["unix_socket"] = socket_path

    # `pic x(5)` -> `pic x(4)` -> int, in that order, because that is the order the
    # frozen source performs it in.
    parameters["port"] = _atoi(port_text[:_WS_MYSQL_PORT_WIDTH])

    # Merged LAST and only when the caller declared a verifying policy, so that the six
    # frozen items are never displaced and the omitted-transport case returns exactly
    # what it returned before this policy existed.
    if transport is not None:
        parameters.update(transport.driver_arguments())

    return parameters


@dataclass(frozen=True, slots=True)
class OpenOutcome:
    """Everything ``Mysql-1000-Open`` leaves behind, success or failure.

    Frozen, because an outcome is a fact about something that already happened - the
    same reasoning ``dal/status.py`` gives for
    :class:`~acas_posting.dal.status.DbErrorStatus`.
    """

    connection: MySQLConnectionAbstract | None

    #: ``Fs-Reply`` [copybooks/wsfnctn.cob:L25]. ``FsReply.SUCCESS`` when all three
    #: steps completed, and ``FsReply.ERROR`` (99) otherwise - unconditionally, per
    #: anomaly A-2 [copybooks/mysql-procedures.cpy:L127].
    fs_reply: FsReply

    #: ``We-Error`` [copybooks/wsfnctn.cob:L23].
    we_error: int

    #: ``ws-No-Paragraph`` [copybooks/wsfnctn.cob:L48]. On failure, the
    #: :class:`~acas_posting.dal.status.ConnectStep` that failed - 101, 102 or 103. On
    #: success, the value the CALLER was carrying, undisturbed.
    ws_no_paragraph: int

    sql_err: str

    sql_msg: str

    sql_state: str

    @property
    def opened(self) -> bool:
        """Report whether the connection is usable.

        Returns:
            ``True`` only when a connection was produced AND the reply is zero. Both are
                required.
        """
        return self.connection is not None and self.fs_reply == FsReply.SUCCESS

    def apply_to_logging_data(self, logging_data: LoggingData) -> None:
        """Write the diagnostics into the caller's ``Logging-Data`` block.

        Reproduces what the COBOL leaves in the shared record: the three diagnostic text
        fields plus ``ws-No-Paragraph``.

        Args:
            logging_data: The block to update, owned by ``records/file_access.py``.
                Mutated in place, as a COBOL ``MOVE`` mutates a record.
        """
        logging_data.ws_no_paragraph = self.ws_no_paragraph
        logging_data.sql_err = self.sql_err
        logging_data.sql_msg = self.sql_msg
        logging_data.sql_state = self.sql_state


def _connect_step_for(errno: int) -> ConnectStep:
    """Decide which COBOL step a single driver failure is attributed to.

    WHY 103 IS UNREACHABLE IN THE FROZEN CALL SHAPE. Step 103 failed only when
    ``MySQL_selectdb`` was handed a DIFFERENT name from the one the connect had already
    selected. The bridge never does that.

    Args:
        errno: The driver's error number. Non-positive when the driver never reached a
            server.

    Returns:
        The :class:`~acas_posting.dal.status.ConnectStep` to report. >>>
            _connect_step_for(-1) <ConnectStep.INIT: 101> >>> _connect_step_for(2003)
            <ConnectStep.REAL_CONNECT: 102> >>> _connect_step_for(1049) # measured at
            102, never 103 <ConnectStep.REAL_CONNECT.
    """
    if errno <= 0:
        return ConnectStep.INIT
    return ConnectStep.REAL_CONNECT


def _db_error_status(
    *,
    errno: int,
    message: str,
    sql_state: str,
    we_error: int,
) -> DbErrorStatus:
    """Map one connect failure through ``Mysql-1100-Db-Error``.

    ``command`` is passed as empty on purpose. That argument feeds ONLY the duplicate-
    key test, which examines ``Ws-Mysql-Command (1:6)`` [copybooks/mysql-
    procedures.cpy:L100] and can fire only for error numbers 1062 and 1022 [:L99].

    Args:
        errno: The driver's error number.
        message: The driver's error message - the equivalent of ``Ws-Mysql-Error-
            Message`` [copybooks/mysql-variables.cpy:L86].
        sql_state: The driver's SQLSTATE - the equivalent of ``WS-Mysql-SqlState``
            [copybooks/mysql-variables.cpy:L85].
        we_error: The value ``We-Error`` already held.

    Returns:
        The status the error paragraph would have left behind.
    """
    return mysql_1100_db_error(
        # `call "MySQL_errno" using Ws-Mysql-Error-Number` [copybooks/mysql-
        # procedures.cpy:L97]. Text, because `Ws-Mysql-Error-Number` is `pic x(5)`
        # [copybooks/mysql-variables.cpy:L84] and the duplicate test compares it as
        # characters.
        errno=str(errno) if errno > 0 else "",
        message=message,
        sql_state=sql_state,
        command="",
        we_error=we_error,
    )


def _assert_converter_pinned(connection: MySQLConnectionAbstract) -> None:
    """Verify the pinned converter is really in force on a live connection.

    Rule R-2 names this file for pinning the converter "rather than relying on the
    default".

    Args:
        connection: A connection that has just been opened.

    Raises:
        ConverterPinningError: On any drift. The caller closes the connection before
            letting this leave :func:`mysql_1000_open`.
    """
    converter = getattr(connection, "converter", None)
    if not isinstance(converter, AcasConverter):
        raise ConverterPinningError(
            "rule R-2: the ACAS numeric converter is not in force - the "
            f"connection is using {type(converter).__name__!r}. Every "
            "connection must be opened with converter_class=AcasConverter so "
            "that no accounting value passes through a binary floating-point "
            "type in transport."
        )

    base = conversion.MySQLConverter
    for field_type, hook in (
        *PINNED_CONVERTER_HOOKS.items(),
        *REJECTED_CONVERTER_HOOKS.items(),
    ):
        if getattr(AcasConverter, hook) is getattr(base, hook):
            raise ConverterPinningError(
                f"rule R-2: converter hook {hook!r} for driver field type "
                f"{FieldType.get_info(field_type)!r} resolves to the driver's "
                "own implementation, so that type would be converted by the "
                "default this file exists to replace."
            )

    with execute_statement(connection, CONVERTER_PROBE_STATEMENT) as cursor:
        probe = cursor.fetchone()

    if probe is None or len(probe) != 3:
        raise ConverterPinningError(
            "rule R-2: the converter probe returned no row, so the pinning "
            f"could not be verified (statement: {CONVERTER_PROBE_STATEMENT})"
        )

    probed_decimal, probed_integer, probed_text = probe

    if not isinstance(probed_decimal, decimal.Decimal):
        raise ConverterPinningError(
            "rule R-2: a DECIMAL(10,2) column arrived as "
            f"{type(probed_decimal).__name__!r} instead of decimal.Decimal. "
            "No accounting value may pass through a binary floating-point "
            "type at any point - not in computation, not in storage, not in "
            "transport - and the 128 in-scope decimal columns all take this "
            "path."
        )
    if str(probed_decimal) != CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT:
        raise ConverterPinningError(
            "rule R-2: a DECIMAL(10,2) column lost its declared scale - "
            f"expected {CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT!r}, got "
            f"{str(probed_decimal)!r}. The scale is part of the stored value "
            "and the state diff compares it."
        )
    # The same fact stated as an exponent rather than as text, because the widest in-
    # scope scale is what a money column carries and a normalised value would silently
    # report a different one.
    if -probed_decimal.as_tuple().exponent != SCHEMA_MAX_DECIMAL_SCALE:
        raise ConverterPinningError(
            "rule R-2: a DECIMAL(10,2) column arrived at exponent "
            f"{probed_decimal.as_tuple().exponent} rather than at the "
            f"{SCHEMA_MAX_DECIMAL_SCALE} decimal places every in-scope money "
            "column declares."
        )
    # `isinstance(x, int)` would accept a bool, which is an int subclass and is not a
    # value any in-scope column can hold, so the type is checked exactly.
    if type(probed_integer) is not int:
        raise ConverterPinningError(
            "rule R-2: a signed integer column arrived as "
            f"{type(probed_integer).__name__!r} instead of int. The 208 "
            "in-scope integer columns carry the COBOL binary family, whose "
            "truncation on divide is integer truncation."
        )
    if type(probed_text) is not str:
        raise ConverterPinningError(
            "rule R-2 support: a character column arrived as "
            f"{type(probed_text).__name__!r} instead of str, so the 177 "
            "in-scope char columns would not compare as text in a state diff."
        )


_PROCESS_CONNECTION: MySQLConnectionAbstract | None = None


def process_connection() -> MySQLConnectionAbstract | None:
    """Report the one connection this process holds, without touching it.

    Returns:
        The one connection object, live or closed, or ``None`` before the first
            :func:`mysql_1000_open` of the process and after
            :func:`reset_process_connection`.
    """
    return _PROCESS_CONNECTION


def reset_process_connection() -> None:
    """Close the one connection and forget it, so the next open starts clean.

    THERE IS NO COBOL COUNTERPART, and that is stated plainly rather than disguised -
    the same position :func:`reset_rdb_data_cache` is in. Nothing in the frozen source
    discards the ``sql`` struct, because it does not need to.
    """
    global _PROCESS_CONNECTION  # noqa: PLW0603 - the `MYSQL sql` file-scope struct

    if _PROCESS_CONNECTION is not None:
        _close_quietly(_PROCESS_CONNECTION)
    _PROCESS_CONNECTION = None


def _close_quietly(connection: MySQLConnectionAbstract) -> None:
    """Close one connection the way ``MySQL_close`` closes: without reporting.

    Args:
        connection: The connection to close. Already-closed is fine - the driver
            tolerates it, and so does ``mysql_close`` on a struct whose session has
            gone.
    """
    try:
        connection.close()
    except Exception:  # noqa: BLE001, S110 - see the comment below
        # DISCARDED IN SILENCE, WHICH IS THE FROZEN BEHAVIOUR AND NOT AN OVERSIGHT.
        # `Mysql-1980-Close` calls `MySQL_close`, whose C signature is `void`
        # [copybooks/mysql-procedures.cpy:L142-L145]: it returns nothing, the
        # bridge tests nothing afterwards, and no status field is written. There is
        # no error path here to reproduce, so there is no diagnostic to emit -
        # inventing one would be a record the compiled program cannot produce
        # (rule R-4), and the only thing it could report is the driver's own free
        # text, which can name the account and can carry a line feed (CWE-117,
        # CWE-532). The exception is bound to no name so that nothing can leak
        # from it by accident.
        pass


def mysql_1000_open(
    system_record: SystemRecord,
    *,
    ws_no_paragraph: int = 0,
    we_error: int = WeError.SUCCESS,
    transport: TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool | None = None,
) -> OpenOutcome:
    """Open the connection, as ``Mysql-1000-Open`` does.

    Only the third arm omits the ``go to``, because it is already last.

    Args:
        system_record: The ``SYSTEM-REC`` row carrying the connection
            parameters. Consulted only on the first call of the run - anomaly
            A-1, see :func:`load_rdb_data_once`.
        ws_no_paragraph: The value the caller already has in
            ``ws-No-Paragraph``. Returned unchanged on success, exactly as the
            frozen paragraph leaves it; the bridge sets 1 before performing the
            paragraph [common/glpostingMT.cbl:L418].
        we_error: The value the caller already has in ``We-Error``. Returned
            unchanged on success, because the paragraph writes that field only
            on the error path.
        transport: How the connection may cross the network. ``None`` - the
            default, and what every handler in this package passes - resolves to
            the INSTALLED PROCESS POLICY, so the deployment's one declaration
            governs this open. Passing a declaration overrides the policy for
            this call only. See the policy section of this module.
        allow_frozen_placeholder_credentials: Declares that the caller knows the
            row may still carry `"ACAS-User"` and `"PaSsWoRd"`
            [copybooks/wssystem.cob:L138-L139] and that the target server is
            disposable. ``None`` - the default - resolves to the installed
            process policy; ``False`` states positively that no declaration is
            made, which is what a handler that has not been told anything means.

    Returns:
        An :class:`OpenOutcome`.

    Raises:
        FrozenPlaceholderCredentialsError: The row still carries a shipped
            credential, no declaration was made, and the installed policy
            requires one. Raised rather than reported as ``(99, 911)`` so that a
            policy refusal can never be mistaken for a server declining - see the
            policy section.
        InsecureTransportError: The transport declaration is internally
            inconsistent, or the connection would have crossed a network
            unprotected and the installed policy requires encryption. Raised for
            the same reason.
        ConverterPinningError: If the connection opened but the pinned
            converter is not in force. Not reported as a COBOL status,
            because it is not a condition the frozen program can be in: the
            migration's own transport guarantee has failed and rule R-2
            leaves nothing to degrade to. The connection is closed first.
    """
    global _PROCESS_CONNECTION  # noqa: PLW0603 - the `MYSQL sql` file-scope struct

    #  THE ONE BOUNDARY, RESOLVED HERE AND NOWHERE ELSE. An omitted declaration
    #  is not "the strictest thing this function can think of" - it is the policy
    #  the deployment installed, read at every open rather than captured at the
    #  first, so a policy installed before the run's first `fn-Open` governs all
    #  twenty handlers without any of them knowing it exists.
    policy = connection_policy()
    declared_transport = (
        policy.declared_transport() if transport is None else transport
    )
    declared_placeholder_credentials = (
        policy.allow_frozen_placeholder_credentials
        if allow_frozen_placeholder_credentials is None
        else bool(allow_frozen_placeholder_credentials)
    )

    rdb_data = load_rdb_data_once(system_record)
    parameters = connection_parameters(rdb_data, transport=declared_transport)

    # ⭐ M-06.  REPORTED, NOT REFUSED.  This used to call
    # `_require_permitted_connection`, which raised
    # `FrozenPlaceholderCredentialsError` or `InsecureTransportError` before the
    # connect. That put two dispositions on this path that its frozen counterpart
    # has not got: `Mysql-1000-Open` [copybooks/mysql-procedures.cpy:L60-L128]
    # either connects or reports `(FS-Reply 99, We-Error 911)`
    # [copybooks/mysql-procedures.cpy:L127-L128], and it inspects neither whose
    # credentials it was handed nor where the server is. Rule R-3 forbids adding a
    # disposition, so the policy became a WARNING here and a separately-named
    # opt-in gate, `require_connection_policy`, for a caller that wants to refuse.
    #
    # A LOG RECORD IS THE ONE THING THAT CHANGES NOTHING. Agent Action Plan
    # section 0.3.4's first class is exactly this: "diagnostic displays with no
    # database effect become log records ... They must not alter control flow and
    # must not appear in any table dump." So the exposure is still visible in a
    # run's output, while the connect, the status pair, the statement text and
    # every dumped column stay byte-for-byte as the frozen path leaves them.
    #
    # Evaluated on EVERY call, including the calls that re-use the one process
    # connection: the verdict is about THIS call's declaration and the policy in
    # force now, so it cannot be inherited from an earlier caller that happened
    # to declare something else.
    _require_permitted_connection(
        system_record,
        parameters,
        declared_transport,
        allow_frozen_placeholder_credentials=declared_placeholder_credentials,
        policy=policy,
    )

    # THE FULL ARGUMENT SET, ASSEMBLED ONCE AND USED ON EVERY OPEN, because that is what
    # the frozen source does.
    driver_arguments: dict[str, Any] = {
        **parameters,
        "autocommit": True,
        # RULE R-2, WHICH NAMES THIS FILE. The converter is pinned explicitly rather
        # than left to the driver's default.
        "converter_class": AcasConverter,
        "client_flags": [-ClientFlag.MULTI_STATEMENTS],
    }

    established = _PROCESS_CONNECTION
    try:
        if established is None:
            connection = mysql.connector.connect(**driver_arguments)
        else:
            established.connect(**driver_arguments)
            connection = established
    except mysql.connector.Error as error:
        errno = error.errno if isinstance(error.errno, int) else 0
        return _failed_open(
            step=_connect_step_for(errno),
            errno=errno,
            message=error.msg or str(error),
            sql_state=error.sqlstate or "",
            we_error=we_error,
        )

    _PROCESS_CONNECTION = connection

    # Checked on EVERY open, exactly as before this slot existed, so the number of probe
    # statements a run issues does not move.
    try:
        _assert_converter_pinned(connection)
    except BaseException:
        # The connection is unusable under rule R-2, so it is closed rather than leaked.
        # `Mysql-1980-Close` is used so the close path stays single-sourced.
        mysql_1980_close(connection)
        raise

    # A clean open: the paragraph wrote neither `Fs-Reply`, nor `We-Error`, nor `ws-No-
    # Paragraph`, so the caller's own values are handed straight back.
    return mysql_1090_exit(
        OpenOutcome(
            connection=connection,
            fs_reply=FsReply.SUCCESS,
            we_error=we_error,
            ws_no_paragraph=ws_no_paragraph,
            sql_err="",
            sql_msg="",
            sql_state="",
        )
    )


def _failed_open(
    *,
    step: ConnectStep,
    errno: int,
    message: str,
    sql_state: str,
    we_error: int,
) -> OpenOutcome:
    """Assemble the outcome of a failed connect, as the three arms do.

    The three failure arms of ``Mysql-1000-Open`` differ in ONE statement - the step
    code they stamp into ``ws-No-Paragraph`` [copybooks/mysql-procedures.cpy:L68, :L79,
    :L84] - and are otherwise identical.

    Args:
        step: Which of the three steps failed.
        errno: The driver's error number, or 0 if the driver never reached a server.
        message: The driver's error message.
        sql_state: The driver's SQLSTATE, or ``""`` if it reported none.
        we_error: The value ``We-Error`` already held.

    Returns:
        The failure :class:`OpenOutcome`, carrying no connection.
    """
    status = _db_error_status(
        errno=errno,
        message=message,
        sql_state=sql_state,
        we_error=we_error,
    )
    # The step code, its name and the two ACAS status values are this module's
    # own values and carry nothing sensitive. THE DRIVER'S MESSAGE DOES, AND IS
    # THEREFORE NOT LOGGED AT ALL: a failed connect is precisely the failure whose
    # message names the account and the host - "Access denied for user
    # 'ACAS-User'@'localhost' (using password: YES)" - and it can carry a carriage
    # return that forges a second log record. Redacting it was not enough, because
    # the rules of `redact_for_log` recognise the connection-message shapes the
    # client library is known to produce and cannot recognise text it has never
    # seen (CWE-117, CWE-532).
    #
    # WHAT REPLACES IT IS BETTER FOR AN OPERATOR, NOT WORSE. The stable
    # `db_error_log_category` token is derived from the error number and the
    # SQLSTATE alone, so `access-denied`, `unknown-database`, `connect-failed`,
    # `tls-failed` and `connection-lost` are each identical on every occurrence
    # and greppable as such - which the free text never was. The `OpenOutcome`
    # returned below still carries all three diagnostic fields exactly as the
    # driver produced them, so no status, no linkage field and no compared value
    # is affected.
    _LOG.error(
        "Mysql-1000-Open failed at step %d (%s): "
        "FS-Reply=%d WE-Error=%d SQLSTATE=%s errno=%s category=%s",
        int(step),
        step.name,
        int(status.fs_reply),
        int(status.we_error),
        sanitise_for_log(status.sql_state.strip(), limit=SQL_STATE_WIDTH),
        sanitise_for_log(str(errno).strip(), limit=SQL_ERR_WIDTH),
        db_error_log_category(errno, sql_state),
    )
    return mysql_1090_exit(
        OpenOutcome(
            connection=None,
            fs_reply=status.fs_reply,
            we_error=status.we_error,
            ws_no_paragraph=int(step),
            sql_err=status.sql_err,
            sql_msg=status.sql_msg,
            sql_state=status.sql_state,
        )
    )


def mysql_1090_exit(outcome: OpenOutcome) -> OpenOutcome:
    """The single convergence point of the open paragraph.

    ``Mysql-1090-Exit`` [copybooks/mysql-procedures.cpy:L87-L88] is a label followed by
    ``exit.`` and nothing else.

    Args:
        outcome: The outcome the arriving arm assembled.

    Returns:
        That same outcome, unchanged.
    """
    return outcome


def mysql_1980_close(connection: MySQLConnectionAbstract | None) -> None:
    """Close the connection, as ``Mysql-1980-Close`` does.

    NO COMMIT PRECEDES THE CLOSE, and none is added.

    Args:
        connection: The connection the calling paragraph believes it is closing, or
            ``None``. Not used to decide WHAT is closed - see above.
    """
    global _PROCESS_CONNECTION  # noqa: PLW0603 - the `MYSQL sql` file-scope struct

    if _PROCESS_CONNECTION is not None:
        _close_quietly(_PROCESS_CONNECTION)
    if connection is not None and connection is not _PROCESS_CONNECTION:
        # Not the process handle. No frozen counterpart exists, because no bridge can
        # hold a second connection.
        _close_quietly(connection)
    mysql_1999_exit()


def mysql_1999_exit() -> None:
    """The convergence point of the close block.

    ``Mysql-1999-Exit`` [copybooks/mysql-procedures.cpy:L267-L268] is, like
    ``Mysql-1090-Exit``, a label followed by ``exit.``. It is the named end of the range
    the bridge performs [common/glpostingMT.cbl:L443], and it is reproduced as a
    function for the same rule R-5 reason.
    """
    return


class _UnavailableCursor:
    """A cursor-shaped stand-in that reports the failure when a statement runs.

    The frozen bridges issue a statement with ONE foreign call - ``call "MySQL_query"
    using Ws-Mysql-Command`` [copybooks/mysql-procedures.cpy:L148, :L165] - and test ONE
    return code immediately afterwards [:L149, :L166].
    """

    __slots__ = ("_error",)

    #: A closed connection has no result set, so there is no row description to report.
    #: Present because callers read it defensively before fetching.
    description: Final[None] = None

    #: ``MySQL_affected_rows`` on a failed statement reports "unknown" rather than a
    #: count [copybooks/mysql-procedures.cpy:L178].
    rowcount: Final[int] = 0

    def __init__(self, error: BaseException) -> None:
        """Capture the failure to re-raise when a statement is attempted.

        Args:
            error: The exception ``connection.cursor()`` raised.
        """
        self._error = error

    def execute(
        self, operation: str, params: Sequence[Any] | None = None
    ) -> NoReturn:
        """Report the captured failure, as ``MySQL_query`` reports its own.

        Args:
            operation: The statement the caller meant to issue. Accepted so that the
                signature matches a real cursor's; never sent.
            params: The parameters the caller meant to bind. Likewise never sent.

        Raises:
            BaseException: The error ``connection.cursor()`` raised, unchanged, so the
                caller's own error mapping sees the driver's own errno, SQLSTATE and
                message rather than a substitute.
        """
        raise self._error

    def fetchone(self) -> NoReturn:
        """Report the captured failure.

        Unreachable through any handler, because :meth:`execute` raises first. Present
        so that a caller which fetches without executing cannot silently read ``None``
        from a dead session and take it for an empty result.

        Raises:
            BaseException: The error ``connection.cursor()`` raised.
        """
        raise self._error

    def fetchall(self) -> NoReturn:
        """Report the captured failure, for the reason :meth:`fetchone` gives.

        Raises:
            BaseException: The error ``connection.cursor()`` raised.
        """
        raise self._error

    def close(self) -> None:
        """Do nothing, because nothing was opened.

        Every caller closes its cursor in a ``finally``, so this must not raise - a
        raise from a ``finally`` would replace the caller's own status with a misleading
        exception, which is the same reasoning :func:`execute_statement` gives for
        swallowing a cursor-close failure.
        """
        return


def acquire_cursor(connection: MySQLConnectionAbstract) -> Any:
    """Obtain a cursor, or a stand-in that fails when the statement runs.

    The single cursor-acquisition point for the handler modules that issue their
    statement themselves rather than through :func:`execute_statement` - the positioning
    verbs, which need the cursor and the statement in the caller's hands.

    Args:
        connection: The connection :func:`mysql_1000_open` returned, live or not.

    Returns:
        The driver's cursor when one can be obtained.
    """
    try:
        return connection.cursor()
    except Exception as error:  # noqa: BLE001 - the bridge tests a code, not a type
        # NOT REPORTED HERE, AND NOT SWALLOWED EITHER. The frozen source has no
        # cursor-acquisition step to report: it goes straight to the statement and
        # tests the result [copybooks/mysql-procedures.cpy:L149, :L166], so this
        # refusal is visible to the compiled program only as a failed statement.
        # Carrying the driver's error into `_UnavailableCursor` reproduces exactly
        # that - the caller's existing failure arm raises it at `execute` and
        # produces the status - so the event is reported ONCE, by the layer that
        # turns it into an ACAS status pair. Logging it here as well produced two
        # records for one fault, and the only thing this layer could add to the
        # second was the driver's own free text.
        return _UnavailableCursor(error)


def cursor_is_unavailable(cursor: object) -> bool:
    """Report whether :func:`acquire_cursor` returned the stand-in.

    Args:
        cursor: Whatever :func:`acquire_cursor` returned.

    Returns:
        ``True`` when it is the stand-in, so the caller must use it once and discard it
            rather than retain it.
    """
    return isinstance(cursor, _UnavailableCursor)


@contextmanager
def execute_statement(
    connection: MySQLConnectionAbstract,
    statement: str,
    parameters: Sequence[Any] = (),
) -> Iterator[MySQLCursorAbstract]:
    """Execute exactly one statement and yield its cursor.

    The shared execution path for every handler module, corresponding to the frozen
    copybook's ``Mysql-1200-Select`` [copybooks/mysql-procedures.cpy: L147-L150] and
    ``Mysql-1210-Command`` [:L164-L178], both of which issue a single ``call
    "MySQL_query"`` and then test the return code.

    Args:
        connection: A connection from :func:`mysql_1000_open`, so the pinned converter
            applies to everything fetched through it.
        statement: One SQL statement, identifiers already backtick-quoted and values
            expressed as ``%s`` placeholders.
        parameters: The values to bind, in the statement's own order. Empty by default,
            for a statement that carries no placeholder.

    Yields:
        The cursor the statement was executed on, positioned before the first row.
            Closed when the block ends, whether or not it raised.
    """
    cursor = connection.cursor()
    try:
        # One `execute` per call, so one statement per call. The guarantee is structural
        # rather than a convention.
        cursor.execute(statement, tuple(parameters))
        yield cursor
    finally:
        # The cursor is closed on every path.
        discard_unread = getattr(connection, "consume_results", None)
        if discard_unread is not None:
            try:
                discard_unread()
            except mysql.connector.Error:  # noqa: S110 - see the comment below
                # DROPPED IN SILENCE. Discarding an unread result has no
                # counterpart in the frozen source at all - the bridge reads its
                # one row and moves on - so there is no frozen error path here to
                # reproduce and nothing to report (rule R-4). Raising from a
                # `finally` would replace the caller's own exception with a
                # misleading one, and the only thing a record could carry is the
                # driver's free text. The exception is bound to no name so nothing
                # can leak from it by accident.
                pass
        try:
            cursor.close()
        except mysql.connector.Error:  # noqa: S110 - see the comment below
            # Likewise. A cursor that will not close is not a condition the frozen
            # source has an error path for, and raising from a `finally` would hide
            # the caller's own failure. Whatever made the close fail will also have
            # made the statement fail, and THAT is reported - once - by
            # `dal/status.py`'s `mysql_1100_db_error`, with typed fields.
            pass
