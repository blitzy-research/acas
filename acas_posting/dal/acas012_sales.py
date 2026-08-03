"""`acas012` and its bridge `salesMT` - the `SALEDGER-REC` sales ledger.

The data-access module for the Sales entity, 37 columns, primary key `SALES-KEY`.

ELEVEN SIGNS ARE LOST HERE, AND THE LOSS IS REPRODUCED. A block of statistics and
date fields is declared signed `binary-long` in the copybook
[copybooks/wssl.cob:L45-L53], UNSIGNED at the bridge host variable
[common/salesMT.cbl:L305-L312] and unsigned at the column, so a negative value
loses its sign AT THE BRIDGE - before any SQL executes. This module performs the
bridge's conversion rather than writing the computed value and letting the
database complain, because the stored value is what a state comparison sees.

The monetary fields are signed at all three layers and pass through cleanly, so
the drift is specific rather than systemic and is handled field by field from the
generated dictionary.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Any, Final, cast

from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    acquire_cursor,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal import cursor_state as _cursor_state
from acas_posting.dal.cursor_state import (
    EXTRA_READ_ORDERS,
    SEQUENTIAL_READ_START,
    TABLE_OF_KEYNAMES,
    CursorOutcome,
    CursorSlot,
    CursorState,
    CursorStateTable,
    DatabaseCursor,
    ExtraReadOrder,
    KeyOfReference,
    OrderQuoting,
    SequentialReadStart,
    key_of_reference,
)
# `Mysql-1100-Db-Error` and its per-operation `We-Error` override are DELIBERATELY NOT
# IMPORTED, and the omission is recorded here because R-5 requires omissions to be
# visible rather than silent.
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    SqlState,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    log_cobol_stop,
    log_file_handler_record,
    log_handler_failure,
    sanitise_for_log,
    start_access_type_is_valid,
)
from acas_posting.dictionary import loader as _loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.sales_ledger import (
    BRIDGE_PROGRAM,
    COPYBOOK_FILE,
    COPYBOOK_RECORD,
    DICTIONARY_KEYS,
    ENTITY_FACADE,
    FILE_HANDLER,
    MYSQL_TABLE,
    WsSalesRecord,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#: ``Program-Id. acas012.`` [common/acas012.cbl:L12]; re-exported from the record module
#: so the handler name is stated once in the migration.
HANDLER: Final[str] = FILE_HANDLER

BRIDGE: Final[str] = BRIDGE_PROGRAM

TABLE_NAME: Final[str] = MYSQL_TABLE

FACADE: Final[str] = ENTITY_FACADE

RECORD_COPYBOOK: Final[str] = COPYBOOK_FILE
RECORD_GROUP: Final[str] = COPYBOOK_RECORD

PROG_NAME: Final[str] = "acas012 (3.3.00)"

BRIDGE_PROG_NAME: Final[str] = "SalesMT (3.3.00)"

BRIDGE_DIRECTIVE_LOCATOR: Final[str] = "[common/salesMT.cbl:L276-L279]"

HOST_VARIABLE_GROUP: Final[str] = "TD-SALEDGER-REC"
HOST_VARIABLE_GROUP_LOCATOR: Final[str] = "[common/salesMT.cbl:L283-L321]"

#: ``move 3 to WS-Log-System`` [common/acas012.cbl:L291].
LOG_SYSTEM: Final[LogSystem] = LogSystem.SL

#: ``move 11 to WS-Log-File-No`` [common/acas012.cbl:L292] - the number this handler
#: sets FIRST.
LOG_FILE_NO_COBOL: Final[int] = 11

#: ``move 21 to WS-Log-File-no. *> for FHlogger`` [common/acas012.cbl:L604], reached on
#: the RDB path only and overwriting the 11 above.
LOG_FILE_NO_RDB: Final[int] = 21

#: ``05 WS-File-Key pic x(64) value spaces`` [copybooks/wsfnctn.cob:L52].
WS_FILE_KEY_WIDTH: Final[int] = 64

WS_LOG_WHERE_WIDTH: Final[int] = 231

FLAT_FILE_DEFS_MEMBER: Final[str] = "file_12"

#: ``fd Sales-File. 01 Sales-Record.`` [copybooks/fdsl.cob] - field-for-field identical
#: to ``WS-Sales-Record``; both copybook headers state "rec size 300 bytes".
WS_SALES_RECORD_BYTES: Final[int] = 300
SALES_RECORD_BYTES: Final[int] = 300

WS_NO_PARAGRAPH_HANDLER: Final[Mapping[str, int]] = MappingProxyType(
    {
        "aa020-Process-Open": 201,
        "aa030-Process-Close": 202,
        "aa040-Process-Read-Next": 203,
        "aa050-Process-Read-Indexed": 204,
        "aa060-Process-Start": 205,
        "aa070-Process-Write": 206,
        "aa080-Process-Delete": 207,
        "aa090-Process-Rewrite": 208,
    }
)

WS_NO_PARAGRAPH_BRIDGE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed": 5,
        "ba050-Fetch": 6,
        "ba060-Process-Start": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
        "ba140-Process-Read-Next": 21,
        "ba141-Reread": 22,
    }
)

#: The nine ``File-Function`` codes ``evaluate File-Function`` accepts
#: [common/acas012.cbl:L336-L356], in the order the ``when`` clauses appear.
SUPPORTED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,
    FileFunction.CLOSE,
    FileFunction.READ_NEXT,
    FileFunction.READ_BY_NAME,
    FileFunction.READ_INDEXED,
    FileFunction.WRITE,
    FileFunction.RE_WRITE,
    FileFunction.DELETE,
    FileFunction.START,
)

#: The key guard [common/acas012.cbl:L296-L308]: each of these three functions is
#: refused with ``FS-Reply`` 99 when ``File-Key-No not = 1``, and the two ``WE-Error``
#: codes differ.
GUARDED_KEY_FUNCTIONS: Final[Mapping[FileFunction, WeError]] = MappingProxyType(
    {
        FileFunction.READ_INDEXED: WeError.FILE_KEY_NO_OUT_OF_RANGE,
        FileFunction.START: WeError.FILE_KEY_NO_OUT_OF_RANGE,
        FileFunction.DELETE: WeError.DELETE_KEY_OUT_OF_RANGE,
    }
)

ONLY_FILE_KEY_NO: Final[int] = 1

#: The eleven published Sales facade verbs and the ``(File-Function, Access-Type)`` pair
#: each sets [copybooks/Proc-ACAS-FH-Calls.cob:L652-L707].
FACADE_VERBS: Final[Mapping[str, tuple[FileFunction, AccessType | None]]] = (
    MappingProxyType(
        {
            "Sales-Open": (FileFunction.OPEN, AccessType.I_O),
            "Sales-Open-Input": (FileFunction.OPEN, AccessType.INPUT),
            "Sales-Open-Output": (FileFunction.OPEN, AccessType.OUTPUT),
            "Sales-Close": (FileFunction.CLOSE, None),
            "Sales-Delete": (FileFunction.DELETE, None),
            "Sales-Start": (FileFunction.START, None),
            "Sales-Read-Next": (FileFunction.READ_NEXT, None),
            "Sales-Read-Next-Sorted-By-Name": (FileFunction.READ_BY_NAME, None),
            "Sales-Read-Indexed": (FileFunction.READ_INDEXED, None),
            "Sales-Write": (FileFunction.WRITE, None),
            "Sales-Rewrite": (FileFunction.RE_WRITE, None),
        }
    )
)


_ENTRIES: Final[tuple[_loader.DictionaryEntry, ...]] = tuple(
    _loader.entries_for_table(TABLE_NAME)
)

ENTRIES: Final[Mapping[str, _loader.DictionaryEntry]] = MappingProxyType(
    {entry.column.name: entry for entry in _ENTRIES}
)

COLUMN_ORDER: Final[tuple[str, ...]] = tuple(ENTRIES)

#: ``PRIMARY KEY (`SALES-KEY`)`` [mysql/ACASDB.sql:L983], taken from the dictionary's
#: own table record rather than restated.
PRIMARY_KEY_COLUMN: Final[str] = _loader.table_for(TABLE_NAME).primary_key

RECORD_ATTRIBUTE_FOR_COLUMN: Final[Mapping[str, str]] = MappingProxyType(
    {
        key.split(".", 1)[1]: attribute
        for attribute, key in DICTIONARY_KEYS.items()
        if key.startswith(f"{TABLE_NAME}.")
    }
)

#: The copybook fields of ``WS-Sales-Record`` that reach neither a host variable nor a
#: column, each with why. Rule R-5.
OMITTED_COPYBOOK_FIELDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "sales_address.sales_addr1": (
            "inside the N-addrconcat group concatenation - moved as part of "
            "Sales-Address [common/salesMT.cbl:L1207] into one X(96) host "
            "variable [:L287] and one char(96) column; no column of its own "
            "[copybooks/wssl.cob:L19]"
        ),
        "sales_address.sales_addr2": (
            "inside the N-addrconcat group concatenation, as above "
            "[copybooks/wssl.cob:L20]"
        ),
        "filler_l40": (
            "filler pic xxx, three bytes of alignment padding with no host "
            "variable and no column [copybooks/wssl.cob:L40]"
        ),
        "quarters_view": (
            "filler redefines Quarters - the same storage as TURNOVER-Q1 "
            "through Q4 under a second name, correctly not duplicated as "
            "columns [copybooks/wssl.cob:L61]"
        ),
        "quarters_view.sturnover_q": (
            "STurnover-Q pic s9(8)v99 comp-3 occurs 4 - the subscripted view "
            "of the same four quarters [copybooks/wssl.cob:L62]"
        ),
        "filler_l68": (
            "filler pic x(5), the trailing five bytes that bring the record to "
            "its declared 300 [copybooks/wssl.cob:L68]"
        ),
    }
)

#: The three commented-out lines of ``copybooks/wssl.cob`` - a ``redefines`` of the key
#: into a six-element array plus a check digit. Never compiled, so never migrated.
COMMENTED_OUT_COPYBOOK_LINES: Final[str] = (
    "filler redefines WS-Sales-Key / Array-K pic x occurs 6 / Check-Digit "
    "pic 9 [copybooks/wssl.cob:L14-L16]"
)


def _columns_where(predicate: Any) -> tuple[str, ...]:
    """Select column names in ordinal order by a predicate on their entry.

    The one place this module turns dictionary metadata into a column set, so that every
    set below is demonstrably derived rather than typed out.

    Args:
        predicate: Called with each
            :class:`~acas_posting.dictionary.loader.DictionaryEntry` in ordinal order;
            truthy selects the column.

    Returns:
        The selected column names, in ``mysql/ACASDB.sql`` ordinal order.
    """
    return tuple(name for name, entry in ENTRIES.items() if predicate(entry))


#: bridge host variable is UNSIGNED - ``copybooks/wssl.cob:L43-L53`` against
#: ``common/salesMT.cbl:L302-L312``.
SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: (
        entry.copybook.signed and not entry.bridge_host_variable.signed
    )
)

MONEY_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: entry.copybook.signed and entry.bridge_host_variable.signed
)

UNLOADED_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: not (
        entry.bridge_host_variable.loaded_from_record
        or entry.bridge_host_variable.unloaded_to_record
    )
)

LOADED_COLUMNS: Final[tuple[str, ...]] = tuple(
    name for name in COLUMN_ORDER if name not in UNLOADED_COLUMNS
)

CHARACTER_COLUMNS: Final[tuple[str, ...]] = _columns_where(
    lambda entry: entry.bridge_host_variable.character_length is not None
)

NUMERIC_COLUMNS: Final[tuple[str, ...]] = tuple(
    name for name in COLUMN_ORDER if name not in CHARACTER_COLUMNS
)

# The dictionary is authoritative and this module is built on it, so the three facts it
# is built on are asserted at import time rather than assumed.
if len(COLUMN_ORDER) != 37:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        f"{TABLE_NAME} must have 37 columns [mysql/ACASDB.sql:L945-L985]; the "
        f"data dictionary reports {len(COLUMN_ORDER)}"
    )
if len(SIGN_LOSS_COLUMNS) != 11:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        "anomaly A-11 covers exactly 11 columns "
        "[copybooks/wssl.cob:L43-L53] -> [common/salesMT.cbl:L302-L312]; the "
        f"data dictionary reports {len(SIGN_LOSS_COLUMNS)}: "
        f"{SIGN_LOSS_COLUMNS}"
    )
if len(MONEY_COLUMNS) != 7:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        "exactly 7 columns are signed at all three layers "
        "[common/salesMT.cbl:L313-L319]; the data dictionary reports "
        f"{len(MONEY_COLUMNS)}: {MONEY_COLUMNS}"
    )


# Every one of the eleven A-11 columns must also carry the dictionary's own ambiguity
# tag Q-3, because Agent Action Plan 0.6.8 makes the stored value of a negative-through-
# unsigned a question the compiled oracle had to settle.
_A11_WITHOUT_Q3: Final[tuple[str, ...]] = tuple(
    name
    for name in SIGN_LOSS_COLUMNS
    if "Q-3" not in ENTRIES[name].ambiguity_refs
    or "A-11" not in ENTRIES[name].anomaly_refs
)
if _A11_WITHOUT_Q3:  # pragma: no cover - guards a frozen fact
    raise AssertionError(
        "every sign-loss column must carry both anomaly A-11 and ambiguity "
        f"Q-3 in the data dictionary; these do not: {_A11_WITHOUT_Q3}"
    )


def citations() -> tuple[str, ...]:
    """Publish the dictionary citation for all 37 columns, in ordinal order.

    Rule R-5 requires that every field cite its data-dictionary entry, and the agent
    brief directs that the citation come from
    :func:`acas_posting.dictionary.loader.cite` rather than being hand-written.

    Returns:
        One ``loader.cite`` line per column, in ``mysql/ACASDB.sql`` ordinal order.
            Deterministic: the same tuple in every process.
    """
    return tuple(_loader.cite(entry.key) for entry in _ENTRIES)


def drift_report() -> tuple[str, ...]:
    """Publish the copybook-to-bridge-to-column drift for all 37 columns.

    The full drift table of the module docstring, generated rather than transcribed, so
    it cannot fall out of step with the dictionary.

    Returns:
        One line per column, in ordinal order, naming the drift dimensions the
            dictionary reports and flagging the two anomaly sets by name.
    """
    lines: list[str] = []
    for entry in _ENTRIES:
        drift = _loader.drift_for(entry.key)
        dimensions = tuple(
            name
            for name in (
                "signedness",
                "usage",
                "digits",
                "scale",
                "character_length",
                "name",
            )
            if getattr(drift, name)
        )
        column = entry.column.name
        tags: list[str] = []
        if column in SIGN_LOSS_COLUMNS:
            tags.append("A-11 SIGN LOST AT THE BRIDGE")
        if column in MONEY_COLUMNS:
            tags.append("signed at all three layers; N-signdrop on render")
        if column in UNLOADED_COLUMNS:
            tags.append("N-2fields-lost: never loaded, never unloaded")
        lines.append(
            f"{entry.column.ordinal:2d} {column:<26} "
            f"{entry.copybook.name} {entry.copybook.picture or entry.copybook.usage}"
            f" -> {entry.bridge_host_variable.name} "
            f"{entry.bridge_host_variable.picture or ''}"
            f" -> {entry.column.sql_type}"
            f"  drift={','.join(dimensions) or 'none'}"
            + (f"  [{'; '.join(tags)}]" if tags else "")
        )
    return tuple(lines)


#: ``03 keyOfReference occurs 1 indexed by KOR-x1`` [common/salesMT.cbl:L233-L238]. ONE
#: key.
KEY_TABLE: Final[tuple[KeyOfReference, ...]] = TABLE_OF_KEYNAMES[TABLE_NAME]

PRIMARY_KEY_OF_REFERENCE: Final[KeyOfReference] = key_of_reference(
    TABLE_NAME, ONLY_FILE_KEY_NO
)

KEY_OFFSET: Final[int] = PRIMARY_KEY_OF_REFERENCE.kor_offset

KEY_LENGTH: Final[int] = PRIMARY_KEY_OF_REFERENCE.kor_length

#: ``KOR-Type`` as declared - carried, never acted on. See anomaly N-kortype.
KEY_TYPE: Final[str] = PRIMARY_KEY_OF_REFERENCE.kor_type

SEQUENTIAL_READ: Final[SequentialReadStart] = SEQUENTIAL_READ_START[TABLE_NAME]

#: ``ba140``'s read order - ``ORDER BY `SALES-NAME` ASC`` on a SECOND cursor
#: [common/salesMT.cbl:L1016-L1019], reached only by ``fn-Read-By-Name`` (31).
READ_BY_NAME_ORDER: Final[ExtraReadOrder] = EXTRA_READ_ORDERS[TABLE_NAME][
    FileFunction.READ_BY_NAME
]

READ_BY_NAME_LOW_KEY: Final[int] = 0

READ_BY_NAME_LOW_KEY_TEXT: Final[str] = "0000000"

#: ``05 MOST-Relation pic xxx. *> valid are >=, <=, <, >, =``
#: [common/salesMT.cbl:L248-L249]. Sourced from ``dal/cursor_state.py`` so the relation
#: vocabulary is stated once.
RELATION_FOR_ACCESS_TYPE: Final[Mapping[int, str]] = MappingProxyType(
    dict(_cursor_state.ACCESS_TYPE_TO_RELATION)
)

if READ_BY_NAME_ORDER.cursor_slot is not CursorSlot.SECONDARY:
    raise AssertionError(  # pragma: no cover - guards a frozen fact
        "fn-Read-By-Name must drive Most-Cursor-Set-2 "
        "[common/salesMT.cbl:L252-L254]; cursor_state reports "
        f"{READ_BY_NAME_ORDER.cursor_slot}"
    )


# `salesMT` receives no connection handle and no `System-Record`.


@dataclass(slots=True)
class BridgeSession:
    """The state ``salesMT`` keeps between calls.

    Attributes:
        system_record: The row ``ba012-Test-WS-Rec-Size-2`` read the credentials
            from [common/acas012.cbl:L637-L645]. The bridge itself never sees
            it; it is held here because
            :func:`~acas_posting.dal.connection.mysql_1000_open` owns the
            connect and takes the row. ``None`` until the handler has run once,
            which is the state in which the frozen ``RDB-Data`` block is still
            spaces and a connect would fail.
        connection: The live connection, or ``None`` before an open and after a
            close - the C interface's global connection id.
        cursors: ``DAL-Data``'s two cursor flags, ``Most-Cursor-Set`` and
            ``Most-Cursor-Set-2`` [common/salesMT.cbl:L250-L254], as the primary
            and secondary slots of one table. ONE table, because the frozen
            block is one block: freeing the primary must be visibly unable to
            reach the secondary, which is anomaly N-cursor2-leak.
        transport: How the connection may cross the network. Has no COBOL
            counterpart - transport policy is compiled into ``cobmysqlapi.c`` -
            and ``None``, the default, defers to the ONE policy the deployment
            installed with
            :func:`acas_posting.dal.connection.set_connection_policy`.
        allow_frozen_placeholder_credentials: Passed through to the open.
            ``copybooks/wssystem.cob:L138-L139`` still ships ``"ACAS-User"`` and
            ``"PaSsWoRd"``; ``None`` defers to that same policy, which reports
            the exposure and connects exactly as the compiled program does.
        open_access_type: The ``Access-Type`` the last successful open used, kept
            for diagnostics only. It changes no status and no statement.
    """

    system_record: SystemRecord | None = None
    connection: Any | None = None
    cursors: CursorStateTable = field(default_factory=CursorStateTable)
    transport: TransportSecurity | None = None
    allow_frozen_placeholder_credentials: bool | None = None
    open_access_type: int = 0

    def is_open(self) -> bool:
        """Report whether a connection is established.

        Returns:
            ``True`` when :attr:`connection` holds a live connection.
        """
        return self.connection is not None

    def require_connection(self) -> Any:
        """Return the live connection, or refuse.

        The bridge has no equivalent test: it calls ``MySQL_query`` on whatever the
        global connection id holds, and a closed one fails inside the C interface, which
        ``Mysql-1100-Db-Error`` then reports as ``(99, 911)`` [copybooks/mysql-
        procedures.cpy:L127-L128].

        Returns:
            The live connection.

        Raises:
            ConnectionError: If no open has succeeded, or a close has run.
        """
        if self.connection is None:
            raise ConnectionError(
                f"{BRIDGE} has no open connection: fn-open (File-Function 1) "
                f"must succeed before any other verb, exactly as "
                f"MYSQL-1000-OPEN must precede MySQL_query "
                f"[common/salesMT.cbl:L438]"
            )
        return self.connection


_SESSION: Final[BridgeSession] = BridgeSession()


def session() -> BridgeSession:
    """Return the module's single :class:`BridgeSession`.

    Returns:
        The process-global session - the Python counterpart of the C interface's global
            connection plus the bridge's ``DAL-Data`` block.
    """
    return _SESSION


def reset_session() -> None:
    """Discard every cursor and forget the connection, without closing it.

    Not a COBOL paragraph: it exists so a test or a harness scenario can start from the
    state a freshly loaded ``salesMT`` is in, which rule R-6's determinism requirement
    needs.
    """
    _SESSION.cursors.reset(TABLE_NAME)
    _SESSION.system_record = None
    _SESSION.connection = None
    _SESSION.open_access_type = 0
    #  NO RECORD. Resetting the module's session state is a test and harness
    #  affordance with no counterpart in the frozen bridge at all, so there is
    #  nothing to reproduce and nothing to report (rule R-4).


@contextmanager
def _bridge_cursor(connection: Any) -> Iterator[DatabaseCursor]:
    """Yield a cursor for a statement the callee issues, and close it.

    :func:`~acas_posting.dal.connection.execute_statement` executes the statement
    itself, which suits every statement this module builds. The three verbs delegated to
    :mod:`acas_posting.dal.cursor_state` build and issue their own, so they need the
    cursor rather than the result - and they get the same lifecycle.

    Args:
        connection: The live connection from :func:`BridgeSession.require_connection`.

    Yields:
        A cursor satisfying :class:`~acas_posting.dal.cursor_state.DatabaseCursor`.
    """
    cursor = acquire_cursor(connection)
    try:
        yield cursor
    finally:
        discard_unread = getattr(connection, "consume_results", None)
        if discard_unread is not None:
            try:
                discard_unread()
            except Exception:  # noqa: BLE001, S110 - cleanup must not mask
                #  SILENT. Discarding an unread result has no counterpart in the
                #  frozen bridge, and the only thing a record could carry is the
                #  driver's free text, which can name the account and echo a row
                #  key (CWE-532, CWE-117). See `dal/connection.py` for the same
                #  decision at the same kind of site.
                pass
        try:
            cursor.close()
        except Exception:  # noqa: BLE001, S110 - cleanup must not mask
            #  SILENT, for the same reason: no frozen counterpart, and nothing
            #  to report but driver text.
            pass


# These are the primitives that make the two sign-loss mechanisms reproducible.

MYSQL_EDIT_PICTURE: Final[str] = "-Z(18)9.9(9)"
MYSQL_EDIT_WIDTH: Final[int] = 30
MYSQL_EDIT_SIGN_POSITION: Final[int] = 1
MYSQL_EDIT_INTEGER_POSITIONS: Final[int] = 19
MYSQL_EDIT_POINT_POSITION: Final[int] = 21
MYSQL_EDIT_FRACTION_POSITIONS: Final[int] = 9

#: The 1-based position one past the last integer digit of the edit field - the end of
#: every integer window the generated SQL takes.
MYSQL_EDIT_INTEGER_END: Final[int] = 21

#: The six integer windows that actually appear in ``salesMT``, verified by enumerating
#: every ``WS-MYSQL-EDIT(n:m)`` in the file.
MYSQL_EDIT_WINDOWS_IN_USE: Final[tuple[str, ...]] = (
    "(11:10)",
    "(13:08)",
    "(16:05)",
    "(18:03)",
    "(19:02)",
    "(22:02)",
)


def _sign_loss_at_the_bridge(
    value: int,
    *,
    column: str,
) -> int:
    """**ANOMALY A-11.** Drop the sign of a signed binary field. THE ONE HELPER.

    Agent Action Plan 0.7.2 R-4 names this module as the reproduction site for this
    anomaly, and 0.6.2 states the requirement, verbatim: "the Python data-access layer
    must reproduce the bridge's conversion, NOT MERELY WRITE.

    Args:
        value: The record's value, an ``int`` because ``binary-short`` and ``binary-
            long`` are integers - see rule R-2 in the module docstring for why they are
            not ``Decimal``.
        column: The column being loaded. Must be one of :data:`SIGN_LOSS_COLUMNS`; the
            digit count comes from that column's host variable in the data dictionary,
            never from a literal.

    Returns:
        The value as the unsigned host variable holds it.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        ValueError: If ``column`` is not one of the eleven.
    """
    if column not in SIGN_LOSS_COLUMNS:
        raise ValueError(
            f"{column} is not one of the eleven anomaly A-11 columns "
            f"[copybooks/wssl.cob:L43-L53] -> "
            f"[common/salesMT.cbl:L302-L312]; applying the sign loss to it "
            f"would invent an anomaly the frozen bridge does not have. The "
            f"eleven are {SIGN_LOSS_COLUMNS}."
        )
    host_variable = ENTRIES[column].bridge_host_variable
    digits = host_variable.digits
    if digits is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{host_variable.name} declares no digit count in the data "
            f"dictionary [{host_variable.source}]"
        )
    # `MOVE` into an unsigned receiver.
    stored = abs(int(value)) % (10**digits)
    if stored != value:
        #  SILENT, AND THE ANOMALY IS THE SILENCE. The frozen bridge neither
        #  reports nor refuses the signed-to-unsigned narrowing
        #  [copybooks/wssl.cob:L43-L53] against [common/salesMT.cbl:L302-L312];
        #  the sign is simply gone before SQL executes. A record here would be a
        #  diagnostic the compiled program cannot produce (rule R-4), and the
        #  record this site used to emit interpolated the VALUE both before and
        #  after the narrowing - for this table a customer's turnover or credit
        #  figure (CWE-532). A-11 is documented in
        #  `docs/migration/anomaly-log.md`.
        pass
    return stored


def _store_into_unsigned_host_variable(
    value: Decimal | int,
    *,
    column: str,
) -> Decimal | int:
    """Store into an unsigned host variable whose copybook field is ALSO unsigned.

    There is no sign to lose here, and that is exactly why this is a SEPARATE function
    from :func:`_sign_loss_at_the_bridge`.

    Args:
        value: The record's value - ``int`` for the nine integer columns, a
            :class:`~decimal.Decimal` for ``SALES-DISCOUNT``.
        column: The column being loaded.

    Returns:
        The value as the host variable holds it.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        ValueError: If the host variable declares no digit count.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    scale = host_variable.scale or 0
    if scale == 0:
        digits = host_variable.digits
        if digits is None:  # pragma: no cover - guards a frozen fact
            raise ValueError(
                f"{host_variable.name} declares no digit count "
                f"[{host_variable.source}]"
            )
        return abs(int(value)) % (10**digits)
    integer_digits = host_variable.integer_digits
    if integer_digits is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{host_variable.name} declares no integer digit count "
            f"[{host_variable.source}]"
        )
    quantum = Decimal(1).scaleb(-scale)
    truncated = Decimal(value).quantize(quantum, rounding=ROUND_DOWN)
    limit = Decimal(10) ** integer_digits
    return (truncated.copy_abs() % limit).quantize(
        quantum, rounding=ROUND_DOWN
    )


def _store_into_signed_host_variable(
    value: Decimal,
    *,
    column: str,
) -> Decimal:
    """Store into a host variable that is SIGNED, like its copybook field.

    The seven money fields of :data:`MONEY_COLUMNS`: ``s9(8)v99 comp-3`` ->
    ``S9(08)V9(02) COMP`` [common/salesMT.cbl:L313-L319] -> signed ``decimal(10,2)``.
    **The sign survives this step**, which is Agent Action Plan 0.6.2's evidence that
    the drift is "specific rather than systemic".

    Args:
        value: The record's value as a :class:`~decimal.Decimal`.
        column: The column being loaded.

    Returns:
        The value as the signed host variable holds it, at the host variable's own
            scale.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    scale = host_variable.scale or 0
    integer_digits = host_variable.integer_digits
    if integer_digits is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{host_variable.name} declares no integer digit count "
            f"[{host_variable.source}]"
        )
    quantum = Decimal(1).scaleb(-scale)
    truncated = Decimal(value).quantize(quantum, rounding=ROUND_DOWN)
    limit = Decimal(10) ** integer_digits
    if truncated.copy_abs() >= limit:
        # High-order truncation, sign preserved - the receiver is signed.
        sign = -1 if truncated < 0 else 1
        truncated = (truncated.copy_abs() % limit).copy_sign(Decimal(sign))
        truncated = truncated.quantize(quantum, rounding=ROUND_DOWN)
    return truncated


def _store_into_character_host_variable(text: str, *, column: str) -> str:
    """Store into an alphanumeric host variable - ``PIC X(n)``.

    Args:
        text: The record's value.
        column: The column being loaded.

    Returns:
        Exactly ``character_length`` characters.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    width = ENTRIES[column].bridge_host_variable.character_length
    if width is None:  # pragma: no cover - guards a frozen fact
        raise ValueError(
            f"{ENTRIES[column].bridge_host_variable.name} declares no "
            f"character length [{ENTRIES[column].bridge_host_variable.source}]"
        )
    return str(text)[:width].ljust(width)


def _ws_mysql_edit(value: Decimal | int) -> str:
    """Render a host variable into ``WS-MYSQL-EDIT``, character for character.

    position 1 sign: '-' when negative, ' ' otherwise positions 2..19 eighteen Z,
    leading zeros suppressed to spaces position 20 a 9, so the units digit always shows
    position 21 '.' positions 22..30 nine fraction digits, zero filled.

    Args:
        value: The host variable's value - :class:`int` for a ``COMP`` integer,
            :class:`~decimal.Decimal` for a scaled one. Never a ``float`` (rule R-2).

    Returns:
        Exactly :data:`MYSQL_EDIT_WIDTH` characters.
    """
    amount = Decimal(value)
    sign_character = "-" if amount < 0 else " "
    magnitude = amount.copy_abs()
    # Nine fraction positions: truncate rather than round, then split. Using Decimal
    # shifting keeps every digit exact; no float appears anywhere.
    scaled = magnitude.quantize(
        Decimal(1).scaleb(-MYSQL_EDIT_FRACTION_POSITIONS),
        rounding=ROUND_DOWN,
    )
    digits = format(scaled, "f")
    if "." in digits:
        integer_text, fraction_text = digits.split(".", 1)
    else:  # pragma: no cover - quantize always yields a point at scale 9
        integer_text, fraction_text = digits, ""
    fraction_text = fraction_text[:MYSQL_EDIT_FRACTION_POSITIONS].ljust(
        MYSQL_EDIT_FRACTION_POSITIONS, "0"
    )
    # `Z` suppression: leading zeros become spaces, but the final `9` at position 20
    # always prints, so a zero value shows a single '0' there.
    integer_text = integer_text.lstrip("0") or "0"
    integer_text = integer_text[-MYSQL_EDIT_INTEGER_POSITIONS:].rjust(
        MYSQL_EDIT_INTEGER_POSITIONS
    )
    return f"{sign_character}{integer_text}.{fraction_text}"


def _render_numeric_for_sql(value: Decimal | int, *, column: str) -> str:
    r"""Render a numeric host variable exactly as the generated SQL renders it.

    The window is not hard-coded here. Every one of the five integer windows in use ends
    at edit-field position 20, so the window is exactly ``(21 - integer_digits :
    integer_digits)`` - which the data dictionary supplies per host variable.

    Args:
        value: The host variable's value.
        column: The column being rendered.

    Returns:
        The literal text the bridge would have placed between the double quotes of
            ``\`COLUMN\`="..."``.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        ValueError: If the column is alphanumeric - those go through
            :func:`_render_character_for_sql`.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    integer_digits = host_variable.integer_digits
    if integer_digits is None:
        raise ValueError(
            f"{host_variable.name} is not a numeric host variable "
            f"[{host_variable.source}]; alphanumeric host variables are "
            f"rendered by FUNCTION TRIM (HV-xxx,TRAILING)"
        )
    edit = _ws_mysql_edit(value)
    window_start = MYSQL_EDIT_INTEGER_END - integer_digits
    integer_text = edit[window_start - 1 : MYSQL_EDIT_INTEGER_END - 1].strip()
    scale = host_variable.scale or 0
    if scale == 0:
        return integer_text
    fraction_start = MYSQL_EDIT_POINT_POSITION + 1
    fraction_text = edit[fraction_start - 1 : fraction_start - 1 + scale]
    return f"{integer_text}.{fraction_text}"


def _render_character_for_sql(text: str, *, column: str) -> str:
    """Render an alphanumeric host variable as the generated SQL renders it.

    [common/salesMT.cbl:L1314] - TRAILING only, so trailing spaces are stripped and any
    LEADING space survives into the stored value.

    Args:
        text: The host variable's value.
        column: The column being rendered - used only for the log record, since the
            rendering itself is width-independent.

    Returns:
        The literal text, right-trimmed.
    """
    rendered = str(text).rstrip(" ")
    if column in UNLOADED_COLUMNS and rendered == "":
        #  SILENT. That `bb000-HV-Load` never loads these two columns
        #  [common/salesMT.cbl:L1204-L1239] is a property of the frozen bridge,
        #  reproduced by not loading them; the bridge announces it nowhere, so
        #  neither does this (rule R-4). N-2fields-lost is documented in
        #  `docs/migration/anomaly-log.md`.
        pass
    return rendered


# [common/salesMT.cbl:L283-L321] Thirty-seven host variables, each with the picture the
# bridge declares.

#: Column name -> the bridge's own host-variable name, from the dictionary. This is
#: where the N-nametrunc anomaly shows.
HOST_VARIABLE_NAMES: Final[Mapping[str, str]] = MappingProxyType(
    {name: entry.bridge_host_variable.name for name, entry in ENTRIES.items()}
)


def _initial_host_variable_value(column: str) -> Decimal | int | str:
    """The value ``initialize TD-SALEDGER-REC`` leaves in one host variable.

    ``initialize`` sets every alphanumeric item to SPACES and every numeric item to
    ZERO, and it is the FIRST statement of ``bb000-HV-Load`` [common/salesMT.cbl:L1204].
    Agent Action Plan 0.6.2 draws the consequence, verbatim.

    Args:
        column: The column whose host variable is being initialised.

    Returns:
        Spaces at the declared width for an alphanumeric host variable, integer zero for
            an unscaled numeric one, and ``Decimal`` zero at the declared scale for a
            scaled one.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    host_variable = ENTRIES[column].bridge_host_variable
    width = host_variable.character_length
    if width is not None:
        return " " * width
    scale = host_variable.scale or 0
    if scale == 0:
        return 0
    return Decimal(0).quantize(Decimal(1).scaleb(-scale))


@dataclass(slots=True)
class HostVariables:
    """``01 TD-SALEDGER-REC`` [common/salesMT.cbl:L283-L321].

    The bridge's own working copy of a row, between the record layout and the SQL text.

    Attributes:
        values: Column name -> the host variable's value. Keyed by column rather than by
            host-variable name so that the column order of :data:`COLUMN_ORDER` drives
            every traversal.
    """

    values: dict[str, Decimal | int | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Fill the group at construction, as loading the program does.

        A COBOL ``01`` group in WORKING-STORAGE with no ``VALUE`` clause is zero- or
        space-filled when the program is loaded, so the group is never readable-but-
        unset.
        """
        if not self.values:
            self.initialize()

    def initialize(self) -> None:
        """``initialize TD-SALEDGER-REC`` [common/salesMT.cbl:L1204].

        Every host variable to zero or spaces. Run first by :func:`bb000_hv_load`, which
        is why the two columns of :data:`UNLOADED_COLUMNS` reach every ``INSERT`` and
        ``UPDATE`` as the empty string - anomaly N-2fields-lost.
        """
        self.values = {
            column: _initial_host_variable_value(column)
            for column in COLUMN_ORDER
        }

    def __getitem__(self, column: str) -> Decimal | int | str:
        """Read one host variable.

        Args:
            column: The column whose host variable is wanted.

        Returns:
            The host variable's current value.

        Raises:
            KeyError: If the group has not been initialised, or ``column`` is not a
                ``SALEDGER-REC`` column.
        """
        return self.values[column]

    def __setitem__(self, column: str, value: Decimal | int | str) -> None:
        """Write one host variable, without conversion.

        Used by the fetch path, which receives values already shaped by the pinned
        driver converter. The LOAD path goes through :func:`_move_to_host_variable`
        instead, because that is where the picture-clause conversions - and anomaly A-11
        - live.

        Args:
            column: The column whose host variable is being written.
            value: The value to store.

        Raises:
            KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        """
        if column not in ENTRIES:
            raise KeyError(
                f"{column} is not a {TABLE_NAME} column "
                f"[mysql/ACASDB.sql:L945-L985]"
            )
        self.values[column] = value


def _record_value(sales: WsSalesRecord, column: str) -> Any:
    """Read the record field that feeds one column, by its dictionary path.

    The attribute path comes from
    :data:`~acas_posting.records.sales_ledger.DICTIONARY_KEYS` through
    :data:`RECORD_ATTRIBUTE_FOR_COLUMN`, so a column reaches its field without this
    module naming the field.

    Args:
        sales: The ``WS-Sales-Record`` linkage record.
        column: The column whose feeding field is wanted.

    Returns:
        The field's value, with the address group already concatenated.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        AttributeError: If the record does not carry the dictionary's attribute path -
            which would mean the record module and the dictionary have drifted apart.
    """
    path = RECORD_ATTRIBUTE_FOR_COLUMN[column]
    value: Any = sales
    for part in path.split("."):
        value = getattr(value, part)
    if ENTRIES[column].copybook.is_group:
        return "".join(
            str(getattr(value, member.name)).ljust(48)
            for member in value.__dataclass_fields__.values()
        )
    return value


def _assign_record_value(sales: WsSalesRecord, column: str, value: Any) -> None:
    """Write the record field that one column unloads into, by its dictionary path.

    The inverse of :func:`_record_value`. ``SALES-ADDRESS`` is again the special case.

    Args:
        sales: The ``WS-Sales-Record`` linkage record.
        column: The column being unloaded.
        value: The host variable's value.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
        AttributeError: If the record does not carry the dictionary's attribute path.
    """
    path = RECORD_ATTRIBUTE_FOR_COLUMN[column]
    parts = path.split(".")
    target: Any = sales
    for part in parts[:-1]:
        target = getattr(target, part)
    if ENTRIES[column].copybook.is_group:
        group = getattr(target, parts[-1])
        text = str(value)
        offset = 0
        for member in group.__dataclass_fields__.values():
            setattr(group, member.name, text[offset : offset + 48].ljust(48))
            offset += 48
        return
    setattr(target, parts[-1], value)


def _move_to_host_variable(
    host_variables: HostVariables,
    sales: WsSalesRecord,
    column: str,
) -> None:
    """One ``move <record field> to HV-<column>`` of ``bb000-HV-Load``.

    The single dispatch point for every picture-clause conversion this module performs,
    and therefore the single place anomaly A-11 can happen. The four branches are
    mutually exclusive and are chosen from the data dictionary, not from the column's
    name.

    Args:
        host_variables: The group being loaded.
        sales: The ``WS-Sales-Record`` linkage record.
        column: The column being loaded.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    value = _record_value(sales, column)
    if column in SIGN_LOSS_COLUMNS:
        # ANOMALY A-11 - the sign is lost HERE, before any SQL is built.
        # [copybooks/wssl.cob:L43-L53] -> [common/salesMT.cbl:L302-L312].
        host_variables.values[column] = _sign_loss_at_the_bridge(
            int(value), column=column
        )
        return
    if column in MONEY_COLUMNS:
        # Signed at all three layers [common/salesMT.cbl:L313-L319]; the sign is kept
        # here and dropped later by the rendering - anomaly N-signdrop.
        host_variables.values[column] = _store_into_signed_host_variable(
            Decimal(value), column=column
        )
        return
    if column in CHARACTER_COLUMNS:
        host_variables.values[column] = _store_into_character_host_variable(
            str(value), column=column
        )
        return
    host_variables.values[column] = _store_into_unsigned_host_variable(
        value, column=column
    )


def bb000_hv_load(
    sales: WsSalesRecord,
    host_variables: HostVariables | None = None,
) -> HostVariables:
    """``bb000-HV-Load Section.`` [common/salesMT.cbl:L1196-L1245].

    Load the record into the host-variable group, ready for an ``INSERT`` or an
    ``UPDATE``. Performed from ``ba070-Process-Write`` [:L869] and ``ba090-Process-
    Rewrite`` [:L952], and from nowhere else - the maintainer's own closing comment says
    why [:L1241-L1242].

    Args:
        sales: The ``WS-Sales-Record`` linkage record to load from.
        host_variables: The group to load into. A fresh one when omitted, which is the
            normal case.

    Returns:
        The loaded group.
    """
    group = HostVariables() if host_variables is None else host_variables
    # `initialize TD-SALEDGER-REC.` [common/salesMT.cbl:L1204] - FIRST, which is what
    # makes N-2fields-lost store the empty string rather than NULL.
    group.initialize()
    for column in LOADED_COLUMNS:
        _move_to_host_variable(group, sales, column)
    return group


def bb100_unload_hvs(
    host_variables: HostVariables,
    sales: WsSalesRecord,
) -> WsSalesRecord:
    """``bb100-UnloadHVs Section.`` [common/salesMT.cbl:L1247-L1295].

    ``initialize WS-Sales-Record.`` [:L1256] first - a PLAIN ``initialize``, where the
    two error paths of the two rereads use ``initialize WS-Sales-Record WITH FILLER``
    [:L619, :L1142]. Two initialisation semantics in one bridge, the ``with filler``
    form appearing twice: anomaly N-initialize.

    Args:
        host_variables: The group a fetch has just filled.
        sales: The ``WS-Sales-Record`` linkage record to unload into. Mutated in place,
            as a COBOL ``MOVE`` into a linkage item is.

    Returns:
        The same record, for convenience.
    """
    # `initialize WS-Sales-Record.` [common/salesMT.cbl:L1256] - PLAIN, not `with
    # filler`. Anomaly N-initialize: the two sibling sites differ.
    _initialize_sales_record(sales, with_filler=False)
    for column in LOADED_COLUMNS:
        _assign_record_value(
            sales, column, _unload_host_variable(host_variables, column)
        )
    return sales


def _unload_host_variable(
    host_variables: HostVariables,
    column: str,
) -> Any:
    """Shape one host variable for the record field it unloads into.

    Two details matter. First, the eleven A-11 fields come back through a ``PIC 9(nn)
    COMP`` host variable and an ``unsigned`` column, so they can only ever be non-
    negative on this path.

    Args:
        host_variables: The group a fetch filled.
        column: The column being unloaded.

    Returns:
        The value shaped for the record field.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    value = host_variables[column]
    storage = ENTRIES[column].cobol_python_storage
    if storage is _loader.CobolPythonStorage.INT:
        return int(value)
    if storage is _loader.CobolPythonStorage.DECIMAL:
        scale = ENTRIES[column].copybook.scale or 0
        return Decimal(value).quantize(
            Decimal(1).scaleb(-scale), rounding=ROUND_DOWN
        )
    return str(value)


def _initialize_sales_record(
    sales: WsSalesRecord,
    *,
    with_filler: bool,
) -> None:
    """``initialize WS-Sales-Record`` - both forms. **ANOMALY N-initialize.**

    Three ``FILLER`` items are affected: ``filler pic xxx`` [copybooks/wssl.cob:L40],
    the ``filler redefines Quarters`` view [:L61] and ``filler pic x(5)`` [:L68]. The
    first and third are the record's alignment and tail padding.

    Args:
        sales: The record to initialise, mutated in place.
        with_filler: ``True`` for the ``with filler`` form.
    """
    for attribute, key in DICTIONARY_KEYS.items():
        if "." in attribute:
            continue
        entry_is_filler = key.rsplit(".", 1)[-1].startswith("filler#")
        if entry_is_filler and not with_filler:
            continue
        _initialize_attribute(sales, attribute, with_filler=with_filler)


def _initialize_attribute(
    owner: Any,
    attribute: str,
    *,
    with_filler: bool,
) -> None:
    """Set one attribute to its ``initialize`` value, recursing into groups.

    Args:
        owner: The record or, on a recursive call, the nested group that carries
            ``attribute``.
        attribute: The attribute to initialise.
        with_filler: Passed down so a nested group's members follow the same rule as the
            top level.
    """
    current = getattr(owner, attribute)
    if isinstance(current, str):
        setattr(owner, attribute, " " * len(current))
        return
    if isinstance(current, int) and not isinstance(current, bool):
        setattr(owner, attribute, 0)
        return
    if isinstance(current, Decimal):
        setattr(owner, attribute, Decimal(0).quantize(current))
        return
    if isinstance(current, tuple):
        setattr(
            owner,
            attribute,
            tuple(Decimal(0).quantize(item) for item in current),
        )
        return
    for member in getattr(current, "__dataclass_fields__", {}):
        _initialize_attribute(current, member, with_filler=with_filler)


# Rule R-3 permits SELECT, INSERT, UPDATE and DELETE and nothing else; there is no DDL
# here and no statement for any other table.


def _log_key(text: object) -> str:
    """``move <something> to WS-File-Key`` - truncated to the declared width.

    ``05 WS-File-Key pic x(64) value spaces`` [copybooks/wsfnctn.cob:L52], so a ``MOVE``
    of anything longer truncates on the right. Reproduced so that the log record carries
    what the frozen program's log record would carry, and no more.

    Args:
        text: Whatever the frozen source moves into the field.

    Returns:
        The field's contents: at most :data:`WS_FILE_KEY_WIDTH` characters, rendered
            through :func:`~acas_posting.dal.status.sanitise_for_log` so a control
            character in driver-supplied text cannot forge a log record.
    """
    return sanitise_for_log(
        str(text)[:WS_FILE_KEY_WIDTH], limit=WS_FILE_KEY_WIDTH
    )


def _log_where(text: object) -> str:
    """``move WS-Where (1:J) to WS-Log-Where`` - the test-logging copy.

    Args:
        text: The predicate the verb built.

    Returns:
        The field's contents: at most :data:`WS_LOG_WHERE_WIDTH` characters, rendered
            through :func:`~acas_posting.dal.status.sanitise_for_log`.
    """
    return sanitise_for_log(
        str(text)[:WS_LOG_WHERE_WIDTH], limit=WS_LOG_WHERE_WIDTH
    )


def _set_paragraph(file_access: FileAccess, number: int) -> None:
    """``move NNN to ws-No-Paragraph`` - and the field is the CALLER's.

    ``05 ws-No-Paragraph pic 999`` is declared inside ``03 Logging-Data`` inside ``01
    File-Access`` [copybooks/wsfnctn.cob:L22, L44-L48], and ``File-Access`` is a LINKAGE
    item in both the handler [common/acas012.cbl:L276-L282] and the bridge
    [common/salesMT.cbl:L336-L339]. So neither program owns the storage.

    Args:
        file_access: The caller's ``File-Access`` block.
        number: The paragraph number the frozen source moves in.
    """
    file_access.logging_data.ws_no_paragraph = abs(int(number)) % 1000


def _record_key(sales: WsSalesRecord) -> str:
    """``WS-Sales-Record (K:L)`` - the key as a substring of the WHOLE record.

    ``set KOR-x1 to 1`` / ``move KOR-offset (KOR-x1) to K`` / ``move KOR-length (KOR-x1)
    to L`` and then ``WS-Sales-Record (K:L)`` [common/salesMT.cbl:L645-L646 with :L657,
    :L780-L781 with :L806, :L898-L899 with :L907, :L956-L957]. The bridge does NOT read
    the named ``WS-Sales-Key`` field.

    Args:
        sales: The ``WS-Sales-Record`` linkage record.

    Returns:
        Exactly :data:`KEY_LENGTH` characters.
    """
    storage = str(sales.ws_sales_key).ljust(KEY_OFFSET - 1 + KEY_LENGTH)
    return storage[KEY_OFFSET - 1 : KEY_OFFSET - 1 + KEY_LENGTH]


def _quoted_columns() -> tuple[str, ...]:
    """Every column name, backtick-quoted, in ordinal order.

    Thirty-seven hyphenated identifiers, each of which is a MySQL syntax error unquoted.
    Built from :data:`COLUMN_ORDER`, which comes from the dictionary, so the list is
    never typed out.

    Returns:
        The quoted names, in ``mysql/ACASDB.sql`` ordinal order.
    """
    return tuple(quote_identifier(name) for name in COLUMN_ORDER)


QUOTED_TABLE: Final[str] = quote_identifier(TABLE_NAME)

QUOTED_KEY_COLUMN: Final[str] = quote_identifier(
    PRIMARY_KEY_OF_REFERENCE.column_name
)


def _rendered_parameters(
    host_variables: HostVariables,
) -> tuple[str, ...]:
    """Render all thirty-seven host variables into their SQL literals.

    The values ``bb200-Insert`` and ``bb300-Update`` place between the double quotes, in
    ordinal order. **All thirty-seven, always** - Agent Action Plan 0.6.2.

    Args:
        host_variables: The loaded group.

    Returns:
        Thirty-seven strings, in :data:`COLUMN_ORDER`.
    """
    rendered: list[str] = []
    for column in COLUMN_ORDER:
        value = host_variables[column]
        if column in CHARACTER_COLUMNS:
            rendered.append(_render_character_for_sql(str(value), column=column))
        else:
            # N-signdrop lives in here: the sign in edit-field position 1 is never
            # emitted [common/salesMT.cbl:L1636-L1642].
            rendered.append(
                _render_numeric_for_sql(
                    value if isinstance(value, (Decimal, int)) else Decimal(0),
                    column=column,
                )
            )
    return tuple(rendered)


def bb200_insert(
    connection: Any,
    host_variables: HostVariables,
) -> int:
    """``bb200-Insert Section.`` [common/salesMT.cbl:L1297-L1775].

    The ``X"00"`` terminator has no Python counterpart - it terminates a C string for
    ``cobmysqlapi.c`` - and is recorded as an omission.

    Args:
        connection: The live connection.
        host_variables: The group :func:`bb000_hv_load` filled.

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the affected-row count ``ba070-Process-Write`` tests
            against 1 [:L879].

    Raises:
        Exception: Whatever the driver raises. ``ba070-Process-Write`` translates it,
            because that is where the frozen source tests the outcome.
    """
    assignments = ", ".join(
        f"{quoted}=%s" for quoted in _quoted_columns()
    )
    statement = f"INSERT INTO {QUOTED_TABLE} SET {assignments};"
    parameters = _rendered_parameters(host_variables)
    with execute_statement(connection, statement, parameters) as cursor:
        rowcount = int(getattr(cursor, "rowcount", 0) or 0)
    #  NO PER-STATEMENT SUCCESS RECORD. `bb200-Insert` displays nothing, and a
    #  trace of every inserted row would be the highest-volume record in the
    #  cycle for no diagnostic gain (rule R-4). The count is returned to the
    #  caller, which is where the frozen bridge leaves it.
    return rowcount


def bb300_update(
    connection: Any,
    host_variables: HostVariables,
    where_key: str,
) -> int:
    """``bb300-Update Section.`` [common/salesMT.cbl:L1777-L2259].

    first assignment [:L1791-L1796] as well as the whole of the predicate, so a rewrite
    re-asserts the key it is keyed on.

    Args:
        connection: The live connection.
        host_variables: The group :func:`bb000_hv_load` filled.
        where_key: The key value for the predicate - ``WS-Sales-Record (K:L)`` as
            ``ba090`` built it [:L956-L965].

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the affected-row count ``ba090-Process-Rewrite`` tests
            against 1 [:L975].

    Raises:
        Exception: Whatever the driver raises; ``ba090-Process-Rewrite`` translates it.
    """
    assignments = ", ".join(
        f"{quoted}=%s" for quoted in _quoted_columns()
    )
    statement = (
        f"UPDATE {QUOTED_TABLE} SET {assignments} "
        f"WHERE {QUOTED_KEY_COLUMN}=%s;"
    )
    parameters = (*_rendered_parameters(host_variables), where_key)
    with execute_statement(connection, statement, parameters) as cursor:
        rowcount = int(getattr(cursor, "rowcount", 0) or 0)
    #  NO PER-STATEMENT SUCCESS RECORD - see `bb200_insert` above.
    return rowcount


def _row_into_host_variables(
    row: Mapping[str, object],
    host_variables: HostVariables,
) -> HostVariables:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` + all 37 host variables.

    The fetch call names every one of the thirty-seven host variables as an argument -
    [common/salesMT.cbl:L563-L599] in ``ba041-Reread``, [:L693-L729] in ``ba050-Process-
    Read-Indexed`` and [:L1086-L1122] in ``ba141-Reread``.

    Args:
        row: One stored row, keyed by column name.
        host_variables: The group to fill.

    Returns:
        The same group, filled.

    Raises:
        KeyError: If the row is missing a ``SALEDGER-REC`` column - which would mean the
            ``SELECT *`` did not come from the frozen table.
    """
    for column in COLUMN_ORDER:
        value = row[column]
        host_variable = ENTRIES[column].bridge_host_variable
        width = host_variable.character_length
        if width is not None:
            host_variables[column] = str(value).ljust(width)[:width]
            continue
        scale = host_variable.scale or 0
        if scale == 0:
            host_variables[column] = int(value)  # type: ignore[arg-type]
            continue
        host_variables[column] = Decimal(str(value)).quantize(
            Decimal(1).scaleb(-scale), rounding=ROUND_DOWN
        )
    return host_variables


# 8. `salesMT` - THE BRIDGE PROGRAM ONE FUNCTION PER PARAGRAPH, in the frozen program's
# own order, each carrying its locator (rule R-5).


@dataclass(slots=True)
class BridgeWorkingStorage:
    """``salesMT``'s WORKING-STORAGE, which is static across calls.

    Attributes:
        host_variables: ``01 TD-SALEDGER-REC`` [common/salesMT.cbl:L284-L321]. Static,
            so a value survives from one call to the next until the next ``initialize``.
        stored_rows_pointer: ``01 TP-SALEDGER-REC USAGE POINTER``
            [common/salesMT.cbl:L283] - the result-set handle ``MOVE WS-MYSQL-RESULT TO
            TP-SALEDGER-REC`` saves and ``MOVE TP-SALEDGER-REC TO WS-MYSQL-RESULT``
            restores.
        ws_where: ``WS-Where`` - the predicate under construction.
        j: ``J`` - ``WITH POINTER J``'s value, so ``WS-Where (1:J)`` is the predicate's
            used length.
        k: ``K`` - ``KOR-offset``, copied per verb.
        l: ``L`` - ``KOR-length``, copied per verb.
        most_relation: ``MOST-Relation pic xxx`` - the START comparison.
        ws_mysql_count_rows: ``WS-MYSQL-Count-Rows`` - what ``MySQL_num_rows`` or the
            affected-row count left.
        ws_mysql_error_number: ``WS-MYSQL-Error-Number pic x(4)`` - what ``MySQL_errno``
            left.
        ws_mysql_error_message: ``WS-MYSQL-Error-Message`` - ``MySQL_error``.
        ws_mysql_sqlstate: ``WS-MYSQL-SQLstate`` - ``MySQL_sqlstate``.
        return_code: ``RETURN-CODE``, which ``MySQL_fetch_record`` sets to -1 at end of
            result [common/salesMT.cbl:L604].
        ws_temp_ed: ``WS-Temp-Ed`` - the edited count the log strings embed.
    """

    host_variables: HostVariables = field(default_factory=HostVariables)
    stored_rows_pointer: CursorState | None = None
    ws_where: str = ""
    j: int = 1
    k: int = 0
    l: int = 0
    most_relation: str = "   "
    ws_mysql_count_rows: int = 0
    ws_mysql_error_number: str = "0  "
    ws_mysql_error_message: str = ""
    ws_mysql_sqlstate: str = ""
    return_code: int = 0
    ws_temp_ed: str = ""


_WORKING_STORAGE: Final[BridgeWorkingStorage] = BridgeWorkingStorage()


def working_storage() -> BridgeWorkingStorage:
    """Return the bridge's single :class:`BridgeWorkingStorage`.

    Returns:
        The static working storage, so a test can inspect ``WS-Where``, ``ws-No-
            Paragraph`` or the host variables the last call left - which is what the
            frozen program's screen displays exist to show.
    """
    return _WORKING_STORAGE


def reset_working_storage() -> None:
    """Return the bridge's working storage to its ``VALUE`` clauses.

    Not a COBOL paragraph - a freshly loaded program simply starts this way. It exists
    so that rule R-6's determinism requirement can be met by a caller that runs the same
    scenario twice in one process.
    """
    _WORKING_STORAGE.host_variables.initialize()
    _WORKING_STORAGE.stored_rows_pointer = None
    _WORKING_STORAGE.ws_where = ""
    _WORKING_STORAGE.j = 1
    _WORKING_STORAGE.k = 0
    _WORKING_STORAGE.l = 0
    _WORKING_STORAGE.most_relation = "   "
    _WORKING_STORAGE.ws_mysql_count_rows = 0
    _WORKING_STORAGE.ws_mysql_error_number = "0  "
    _WORKING_STORAGE.ws_mysql_error_message = ""
    _WORKING_STORAGE.ws_mysql_sqlstate = ""
    _WORKING_STORAGE.return_code = 0
    _WORKING_STORAGE.ws_temp_ed = ""


NO_DRIVER_ERROR: Final[str] = "0  "


def _driver_error_fields(error: BaseException) -> tuple[str, str, str]:
    """The three C calls the bridge makes after a failed statement.

    ``call "MySQL_errno" using WS-MYSQL-Error-Number``, ``call "MySQL_sqlstate" using
    WS-MYSQL-SQLstate`` and ``call "MySQL_error" using WS-MYSQL-Error-Message`` - three
    separate interrogations of the same connection, e.g. [common/salesMT.cbl:L876-L884].

    Args:
        error: What the driver raised.

    Returns:
        ``(errno, sqlstate, message)`` - errno space-padded to the width of
            :data:`NO_DRIVER_ERROR` so a comparison against it behaves as the COBOL's
            does, and the message sanitised for logging.
    """
    errno = getattr(error, "errno", None)
    sqlstate = getattr(error, "sqlstate", None) or ""
    message = getattr(error, "msg", None)
    if message is None:
        message = str(error)
    errno_text = (
        "0" if errno is None else str(errno)
    ).ljust(len(NO_DRIVER_ERROR))[:4]
    return (
        errno_text,
        str(sqlstate)[:SQL_STATE_WIDTH],
        sanitise_for_log(str(message), limit=SQL_MSG_WIDTH),
    )


def _column_names(cursor: DatabaseCursor) -> tuple[str, ...]:
    """The result's column names, or ``()`` when the driver gave no metadata.

    Args:
        cursor: The cursor a ``SELECT`` was issued on.

    Returns:
        The names in the result's own order.
    """
    description = getattr(cursor, "description", None)
    if not description:
        return ()
    return tuple(str(column[0]) for column in description)


def _fetch_one_row(cursor: DatabaseCursor) -> Mapping[str, object] | None:
    """``CALL "MySQL_fetch_record"`` - one row, keyed by column name.

    THE FROZEN CALL IS POSITIONAL. It names all thirty-seven host variables as arguments
    [common/salesMT.cbl:L563-L599] and the C interface copies result field *n* into
    argument *n*; there is no name matching anywhere in it.

    Args:
        cursor: The cursor the ``SELECT`` was issued on.

    Returns:
        The row keyed by column name, or ``None`` at end of result.

    Raises:
        ValueError: If the row has a different number of fields from the frozen table's
            column count.
    """
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row
    names = _column_names(cursor) or COLUMN_ORDER
    if len(row) != len(names):
        raise ValueError(
            f"{BRIDGE}: a row of {len(row)} field(s) cannot fill "
            f"{len(names)} host variable(s); the frozen "
            f"`{TABLE_NAME}` has {len(COLUMN_ORDER)} columns "
            f"[common/salesMT.cbl:L563-L599]"
        )
    return MappingProxyType(dict(zip(names, row, strict=True)))


def _store_result(cursor: DatabaseCursor) -> tuple[Mapping[str, object], ...]:
    """``PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT``.

    ``mysql_store_result`` pulls every qualifying row to the client [copybooks/mysql-
    procedures.cpy:L187-L192] before ``MySQL_num_rows`` counts it, which is why ``WS-
    MYSQL-Count-Rows`` is meaningful the instant the ``SELECT`` returns and why a
    subsequent statement on the same connection cannot disturb the walk.

    Args:
        cursor: The cursor the ``SELECT`` was issued on.

    Returns:
        Every row, in the order the statement returned them.
    """
    rows: list[Mapping[str, object]] = []
    while True:
        row = _fetch_one_row(cursor)
        if row is None:
            return tuple(rows)
        rows.append(row)


def _primary(session_state: BridgeSession) -> CursorState:
    """``Most-Cursor-Set`` - the primary cursor flag and its stored rows.

    Args:
        session_state: The session holding ``DAL-Data``.

    Returns:
        The primary slot's state.
    """
    return session_state.cursors.state_for(TABLE_NAME, CursorSlot.PRIMARY)


def _secondary(session_state: BridgeSession) -> CursorState:
    """``Most-Cursor-Set-2`` - the by-name cursor flag and its stored rows.

    Args:
        session_state: The session holding ``DAL-Data``.

    Returns:
        The secondary slot's state.
    """
    return session_state.cursors.state_for(TABLE_NAME, CursorSlot.SECONDARY)


def ca_process_logs(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``Ca-Process-Logs.`` [common/salesMT.cbl:L2261-L2265].

    are recorded as omissions. It reads ``function Current-Date``
    [common/fhlogger.cbl:L219] - a clock read, which rule R-6 bars from this module and
    which is safe to drop precisely because the value reaches only the log file.

    Args:
        file_access: The block the record is built from.
        dal_common: The block carrying the testing switches and the counter.
    """
    logging_data = file_access.logging_data
    #  THE ONE ADAPTER, and three fields fewer than this record used to carry -
    #  none of them redacted or even escaped before. `WS-File-Key` is the
    #  SALES-KEY of the customer row, `WS-Log-Where` is the `WHERE` clause built
    #  around it, and `SQL-Msg` is the driver's free text, which can name the
    #  account and can carry a carriage return that forges a second record
    #  (CWE-532, CWE-117). The adapter reports the closed-vocabulary fields plus
    #  the stable error category, and advances `Log-File-Rec-Written` modulo one
    #  million exactly once per record.
    log_file_handler_record(
        _LOG,
        program=HANDLER,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=str(logging_data.sql_err),
        sql_state=str(logging_data.sql_state),
        dal_common=dal_common,
    )
    # `add 1 to Log-File-Rec-Written.` [common/fhlogger.cbl:L249] IS THE ADAPTER'S
    # JOB and is done exactly once, inside it, immediately before the record is
    # emitted. It was done a SECOND time here, so one record advanced the counter by
    # two and every downstream reading of `Log-File-Rec-Written` was wrong by the
    # number of records written - which is precisely the incoherence OBS-010 names.
    # The field is `pic 9(6)` [copybooks/Test-Data-Flags.cob:L20], so the adapter
    # wraps it at a million.


def ba999_end(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba999-end.`` [common/salesMT.cbl:L1186-L1191].

    Args:
        file_access: The block the log record is built from.
        dal_common: The block carrying ``SW-Testing``.
    """
    if int(dal_common.sw_testing) == TESTING_1_VALUE:
        ca_process_logs(file_access, dal_common)


def ba999_exit() -> None:
    """``ba999-exit.`` [common/salesMT.cbl:L1193-L1194].

    ``exit program.`` - control returns to ``acas012``. Nothing else happens
    here, and in particular NOTHING IS CLEANED UP: the connection, the cursors
    and every host variable survive the return, which is what makes
    ``ba041-Reread`` able to continue a walk a previous call began.
    """
    #  NO RECORD. `exit program` [common/salesMT.cbl:L1195] displays nothing;
    #  that the connection and cursors survive the return is a fact about the
    #  frozen working storage, recorded in this function's docstring where a
    #  reader will find it rather than in a run's log stream (rule R-4).


def ba998_free(file_access: FileAccess, session_state: BridgeSession) -> None:
    """``ba998-Free.`` [common/salesMT.cbl:L1174-L1186].

    result and clears ONE flag: ``Cursor-Not-Active`` is ``88 Cursor-Not-Active`` over
    ``Most-Cursor-Set`` [common/salesMT.cbl:L246], the PRIMARY.

    Args:
        file_access: The caller's block, stamped with paragraph 20.
        session_state: The session holding both cursor slots.
    """
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba998-Free"])
    _primary(session_state).free()
    _WORKING_STORAGE.stored_rows_pointer = None
    #  SILENT. That `ba998-Free` releases the PRIMARY result only and leaves
    #  `Most-Cursor-Set-2` untouched is anomaly N-cursor2-leak, and the frozen
    #  paragraph announces it nowhere [common/salesMT.cbl:L1184]. Reproduced by
    #  freeing one and not the other; documented in
    #  `docs/migration/anomaly-log.md` (rule R-4).


def ba100_bad_function(file_access: FileAccess) -> None:
    """``ba100-Bad-Function.`` [common/salesMT.cbl:L1162-L1171].

    unsupported function as ``(99, 990)`` - ``WeError.UNKNOWN_UNEXPECTED``, whose
    documented meaning is "Unknown/unexpected" - while its own HANDLER reports the same
    condition as ``(99, 999)`` [common/acas012.cbl:L573-L575], and ``dal/status.py``
    carries a third code, ``992`` ``INVALID_FUNCTION``, that neither uses.

    Args:
        file_access: The block to write the status pair into.
    """
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    file_access.fs_reply = int(FsReply.ERROR)


def ba020_process_open(
    file_access: FileAccess,
    session_state: BridgeSession,
) -> None:
    """``ba020-Process-Open.`` [common/salesMT.cbl:L416-L458].

    The six ``STRING``s, the connect and its status are all
    :func:`~acas_posting.dal.connection.mysql_1000_open`'s.

    Args:
        file_access: The caller's block; the status and log fields are written into it.
        session_state: The session to store the connection on.
    """
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba020-Process-Open"])
    system_record = session_state.system_record
    if system_record is None:
        # The frozen program cannot reach this state: `ba012-Test-WS-Rec-Size-2` always
        # runs before the bridge is called.
        _LOG.error(
            "%s open attempted with no system record: the credentials come "
            "from ba012-Test-WS-Rec-Size-2 [common/acas012.cbl:L637-L645]",
            BRIDGE,
        )
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.RDB_INIT_ERROR)
        file_access.logging_data.ws_file_key = _log_key("OPEN SALEDGER")
        return

    # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.` [common/salesMT.cbl:L446] is a
    # paragraph RANGE, not a single paragraph. Under the Agent Action Plan's
    # transformation rule 3 (§0.4.2) a `PERFORM ...
    outcome: OpenOutcome = mysql_1090_exit(
        mysql_1000_open(
            system_record,
            transport=session_state.transport,
            allow_frozen_placeholder_credentials=(
                session_state.allow_frozen_placeholder_credentials
            ),
        )
    )
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    if outcome.connection is None:
        # `if fs-reply not = zero go to ba999-end.` [common/salesMT.cbl:L447-L448] Class
        # 3 - the section exits, and `WS-File-Key` is NOT written, so the log record
        # carries whatever the previous call left in it.
        _LOG.warning(
            "%s open failed with (%s, %s) [common/salesMT.cbl:L447-L448]",
            BRIDGE,
            outcome.fs_reply,
            outcome.we_error,
        )
        return

    session_state.connection = outcome.connection
    session_state.open_access_type = int(file_access.access_type)
    file_access.logging_data.ws_file_key = _log_key("OPEN SALEDGER")
    _primary(session_state).free()
    _WORKING_STORAGE.stored_rows_pointer = None


def ba030_process_close(
    file_access: FileAccess,
    session_state: BridgeSession,
) -> None:
    """``ba030-Process-Close.`` [common/salesMT.cbl:L460-L472].

    The order matters and is preserved: the cursor is freed BEFORE the paragraph number
    and the log key are set, and the connection is closed last.

    Args:
        file_access: The caller's block.
        session_state: The session whose connection is closed.
    """
    if _primary(session_state).cursor_active():
        ba998_free(file_access, session_state)

    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba030-Process-Close"])
    file_access.logging_data.ws_file_key = _log_key("CLOSE SALEDGER")

    connection = session_state.connection
    if connection is None:
        # `MYSQL-1980-CLOSE` calls `MySQL_close` on the global connection id
        # whatever it holds [copybooks/mysql-procedures.cpy]. With no connection
        # there is nothing to close and no status is written, which is what the
        # frozen paragraph does: it tests nothing after the close.
        #  SILENT, as the frozen paragraph is: it tests nothing after the close
        #  [common/salesMT.cbl:L468], so there is nothing to do and no status to
        #  write, and a record saying so would be an invented event (rule R-4).
        pass
        return
    mysql_1980_close(connection)
    mysql_1999_exit()
    session_state.connection = None
    session_state.open_access_type = 0


def ba010_initialise(
    file_access: FileAccess,
) -> FileFunction | None:
    """``ba010-Initialise.`` [common/salesMT.cbl:L372-L414].

    ABOVE, AND THEY STAY COMMENTED OUT.** [common/salesMT.cbl:L380-L382] would have
    zeroed both status fields on entry to every call.

    Args:
        file_access: The caller's block whose diagnostic fields are cleared.

    Returns:
        The function to dispatch, or ``None`` when the ``evaluate``'s ``when other`` arm
            is taken - ``go to ba100-Bad-Function`` [common/salesMT.cbl:L413], whose
            ``*> 6 is spare / unused`` comment names the gap.
    """
    # The two commented-out `move zero` statements are NOT reproduced - see the
    # docstring. [common/salesMT.cbl:L380-L382].
    _WORKING_STORAGE.ws_mysql_error_message = ""
    _WORKING_STORAGE.ws_mysql_error_number = "    "
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    logging_data.ws_file_key = ""
    logging_data.sql_msg = ""
    logging_data.sql_err = ""
    logging_data.sql_state = ""

    requested = int(file_access.file_function)
    for supported in SUPPORTED_FUNCTIONS:
        if requested == int(supported):
            return supported
    return None


WS_TEMP_ED_DIGITS: Final[int] = 10


def _move_count_to_ws_temp_ed(count: int) -> str:
    """``move WS-MYSQL-Count-Rows to WS-Temp-Ed``.

    Args:
        count: ``WS-MYSQL-Count-Rows``.

    Returns:
        Exactly :data:`WS_TEMP_ED_DIGITS` digit characters.
    """
    return f"{abs(int(count)):0{WS_TEMP_ED_DIGITS}d}"[-WS_TEMP_ED_DIGITS:]


def _move_alphanumeric_to_ws_temp_ed(text: str) -> str:
    """``move HV-Sales-Key to ws-temp-ed`` - **ANOMALY N-tempedkey**.

    while ``ba041-Reread`` [:L633] and ``ba141-Reread`` [:L1158] move ``HV-Sales-Key``
    STRAIGHT into ``WS-File-Key``.

    Args:
        text: The sending alphanumeric field, ``HV-SALES-KEY PIC X(7)``.

    Returns:
        Exactly :data:`WS_TEMP_ED_DIGITS` digit characters.
    """
    body = text.lstrip(" ")
    if body[:1] in {"+", "-"}:
        body = body[1:]
    digits: list[str] = []
    for position, character in enumerate(body):
        if character.isdigit():
            digits.append(character)
            continue
        if character == " ":
            continue
        if any(rest.isdigit() for rest in body[position:]):
            digits = []
        break
    value = int("".join(digits)) if digits else 0
    return _move_count_to_ws_temp_ed(value)


def _select_rows(
    connection: Any,
    statement: str,
    parameters: Sequence[object],
) -> tuple[Mapping[str, object], ...]:
    """``PERFORM MYSQL-1210-COMMAND`` then ``PERFORM MYSQL-1220-STORE-RESULT``.

    Args:
        connection: The live connection.
        statement: The assembled statement, identifiers already quoted.
        parameters: The values for its placeholders.

    Returns:
        Every qualifying row, in the order the statement returned them.

    Raises:
        Exception: Whatever the driver raises. Each caller translates it the way its own
            paragraph does, which is not the same way in every paragraph.
    """
    with execute_statement(connection, statement, parameters) as cursor:
        return _store_result(cursor)


def _sequential_where() -> str:
    """``ba040``'s predicate: the key at or after the lowest possible value.

    The relation and the low key are the bridge's own hard-coded literals, taken from
    :data:`SEQUENTIAL_READ` so the vocabulary is stated once. The low key travels as a
    bound value rather than being formatted in, which is what
    :func:`~acas_posting.dal.connection.execute_statement` requires.

    Returns:
        The predicate, with one ``%s`` placeholder for the low key.
    """
    return (
        f"{QUOTED_KEY_COLUMN} {SEQUENTIAL_READ.relation.token} %s "
        f"ORDER BY {QUOTED_KEY_COLUMN} ASC"
    )


def _by_name_where() -> str:
    """``ba140``'s predicate: the same key range, ordered by name instead.

    low key as the COBOL literal ``'"0000000"'`` [:L491], with the SQL double quotes
    inside the COBOL literal, so MySQL receives a string.

    Returns:
        The predicate, with one ``%s`` placeholder for the low key.

    Raises:
        ValueError: If the declared ordering names no term, which would mean the frozen
            ``ORDER BY`` had been misread.
    """
    if not READ_BY_NAME_ORDER.order_terms:
        raise ValueError(
            f"{BRIDGE} declares no ORDER BY term for fn-Read-By-Name "
            f"{READ_BY_NAME_ORDER.source_locator}"
        )
    ordering: list[str] = []
    for term in READ_BY_NAME_ORDER.order_terms:
        if term.quoting is OrderQuoting.IDENTIFIER:
            rendered = quote_identifier(term.column_name)
        else:
            # A single-quoted term is a STRING CONSTANT and orders nothing. This bridge
            # does not declare one.
            rendered = f"'{term.column_name}'"
        ordering.append(f"{rendered} {term.direction}")
    return (
        f"{QUOTED_KEY_COLUMN} {SEQUENTIAL_READ.relation.token} %s "
        f"ORDER BY {', '.join(ordering)}"
    )


def _indexed_where() -> str:
    """``ba050``/``ba080``/``ba090``'s predicate: the key, exactly.

    Returns:
        The predicate, with one ``%s`` placeholder for the key.
    """
    return f"{QUOTED_KEY_COLUMN}=%s"


def _start_where(relation_token: str) -> str:
    """``ba060``'s predicate: the key under the caller's relation, then ordered.

    The frozen ``STRING`` ends with ``' ASC '`` - TWO trailing spaces where ``ba040``
    has none [:L497 versus :L811] - which reaches MySQL as harmless whitespace and is
    preserved here so the assembled text matches.

    Args:
        relation_token: ``MOST-Relation`` trimmed, one of ``=``, ``<``, ``>``, ``>=``,
            ``<=``.

    Returns:
        The predicate, with one ``%s`` placeholder for the key.
    """
    return (
        f"{QUOTED_KEY_COLUMN} {relation_token} %s "
        f"ORDER BY {QUOTED_KEY_COLUMN} ASC  "
    )


def _record_diagnostics(
    file_access: FileAccess,
    errno: str,
    sqlstate: str,
    message: str,
) -> None:
    """The three-move block every failure path in this bridge writes.

    ``move WS-MYSQL-Error-Number to SQL-Err``, ``move WS-MYSQL-Error-Message to SQL-
    Msg`` and ``move WS-MYSQL-SqlState to SQL-State`` - e.g.
    [common/salesMT.cbl:L879-L884]. Each field is truncated to its own declared width
    [copybooks/wsfnctn.cob:L49-L51], because a ``MOVE`` into a shorter ``PIC X(n)``
    truncates on the right.

    Args:
        file_access: The caller's block.
        errno: ``WS-MYSQL-Error-Number``.
        sqlstate: ``WS-MYSQL-SQLstate``.
        message: ``WS-MYSQL-Error-Message``.
    """
    logging_data = file_access.logging_data
    logging_data.sql_err = errno[:SQL_ERR_WIDTH]
    logging_data.sql_msg = message[:SQL_MSG_WIDTH]
    logging_data.sql_state = sqlstate[:SQL_STATE_WIDTH]


def ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba040-Process-Read-Next.`` [common/salesMT.cbl:L474-L547].

    The SELECT stage of a sequential read, guarded by ``if Cursor-Not-Active`` so that
    it runs ONCE per walk.

    Args:
        file_access: The caller's block; the outcome is applied to it.
        dal_common: Needed because this paragraph performs ``ba999-End`` itself.
        sales: The record the fetch fills.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome of the whole verb, SELECT stage and fetch together.
    """
    state = _primary(session_state)
    logging_data = file_access.logging_data

    if not state.cursor_not_active():
        # The guard did not fire, so the SELECT stage is skipped entirely and the verb
        # is just a fetch from the stored result. Class 2's mirror.
        return ba041_reread(file_access, sales, session_state)

    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    _WORKING_STORAGE.ws_where = _sequential_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba040-Process-Read-Next"])

    statement = (
        f"SELECT * FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where};"
    )
    parameters: tuple[object, ...] = (SEQUENTIAL_READ.low_key,)

    try:
        rows = _select_rows(session_state.require_connection(), statement, parameters)
    except Exception as error:  # noqa: BLE001 - every failure takes one path
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        #  ONE ERROR. A driver failure DOES have an authoritative counterpart -
        #  `Mysql-1110-Report-Problem` [copybooks/mysql-procedures.cpy:L130-L137]
        #  displays on every one of them - so it is reported, once, at the level
        #  a failure deserves. The MASKING is preserved exactly: the status pair
        #  this paragraph returns is still end of file per
        #  [common/salesMT.cbl:L534-L535], and the record says so.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba040-Process-Read-Next",
            locator="[common/salesMT.cbl:L534-L535]",
            fs_reply=int(FsReply.END_OF_FILE),
            we_error=int(file_access.we_error),
            sql_err=str(errno),
            sql_state=str(sqlstate),
            detail="the sequential read failed at the driver and is MASKED as "
            "end of file",
        )
        _record_diagnostics(file_access, errno, sqlstate, message)
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=sqlstate or str(SqlState.NO_DATA),
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    logging_data.ws_file_key = _log_key(SEQUENTIAL_READ.low_key)
    _WORKING_STORAGE.ws_mysql_count_rows = state.store_result(rows)
    _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
    _WORKING_STORAGE.ws_mysql_sqlstate = ""
    _WORKING_STORAGE.ws_mysql_error_message = ""

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        state.set_cursor_not_active()
        logging_data.sql_state = ""
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    state.key_of_reference = PRIMARY_KEY_OF_REFERENCE
    state.most_relation = SEQUENTIAL_READ.relation
    state.set_cursor_active()
    _WORKING_STORAGE.stored_rows_pointer = state
    _WORKING_STORAGE.ws_temp_ed = _move_count_to_ws_temp_ed(
        _WORKING_STORAGE.ws_mysql_count_rows
    )
    logging_data.ws_file_key = _log_key(
        f"> 0 got cnt={_WORKING_STORAGE.ws_temp_ed} recs"
    )
    ba999_end(file_access, dal_common)

    return ba041_reread(file_access, sales, session_state)


def ba041_reread(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba041-Reread.`` [common/salesMT.cbl:L549-L637].

    The fetch stage of a sequential read: it advances the stored result and unloads one
    row into the caller's record.

    Args:
        file_access: The caller's block.
        sales: The record the unload fills.
        session_state: The session holding the cursors.

    Returns:
        The outcome, with :attr:`CursorOutcome.row` set on the success path.
    """
    state = _primary(session_state)
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba041-Reread"])
    _WORKING_STORAGE.return_code = 0

    row = state.fetch_record()
    if row is None:
        _WORKING_STORAGE.return_code = -1
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            _initialize_sales_record(sales, with_filler=True)
            logging_data.ws_file_key = _log_key("EOF2")
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    if int(file_access.fs_reply) == int(FsReply.END_OF_FILE):
        # `if fs-reply = 10` [:L628-L632] - the CALLER's sticky end of file. ANOMALY
        # N-eof3-stale.
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=FsReply.END_OF_FILE,
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF3"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    _row_into_host_variables(row, _WORKING_STORAGE.host_variables)
    bb100_unload_hvs(_WORKING_STORAGE.host_variables, sales)
    state.position_at(row[PRIMARY_KEY_COLUMN])
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement="",
        parameters=(),
        file_key=_log_key(_WORKING_STORAGE.host_variables[PRIMARY_KEY_COLUMN]),
    )
    outcome.apply_to(file_access)
    logging_data.ws_log_where = ""
    return outcome


def ba050_process_read_indexed(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba050-Process-Read-Indexed.`` [common/salesMT.cbl:L639-L759].

    One row by exact key. SELECT, test, fetch, unload - and then ``go to ba998-Free`` on
    EVERY path, so a read-indexed always destroys the PRIMARY cursor and therefore any
    sequential walk in progress.

    Args:
        file_access: The caller's block.
        sales: The record the unload fills.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome. The cursor is freed before returning on every path.
    """
    state = _primary(session_state)
    logging_data = file_access.logging_data

    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    key_value = _record_key(sales)
    _WORKING_STORAGE.ws_where = _indexed_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba050-Process-Read-Indexed"])

    statement = (
        f"SELECT * FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where};"
    )
    parameters: tuple[object, ...] = (key_value,)

    try:
        rows = _select_rows(session_state.require_connection(), statement, parameters)
    except Exception as error:  # noqa: BLE001 - one path, per the docstring
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        # The zero-count test below does not consult errno, so a failed statement
        # reports `(23, 0)` with NO diagnostic: `SQL-Err`, `SQL-Msg` and
        # `SQL-State` are left as `ba010-Initialise` cleared them. The failure is
        # logged here so it is at least visible, which changes no status.
        #  ONE ERROR, for the same reason as `ba040-Process-Read-Next` above.
        #  `SQL-Err` and `SQL-State` are still left as `ba010-Initialise` cleared
        #  them - the frozen source writes no diagnostic into the record - and
        #  the returned status is still "not found"; only the log record is new,
        #  and it changes neither.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba050-Process-Read-Indexed",
            locator="[common/salesMT.cbl:L680-L684]",
            fs_reply=int(file_access.fs_reply),
            we_error=int(file_access.we_error),
            sql_err=str(errno),
            sql_state=str(sqlstate),
            detail="the indexed read failed at the driver and is MASKED as not "
            "found, with no diagnostic written into the record",
        )
        rows = ()

    if not rows:
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        outcome = CursorOutcome(
            fs_reply=FsReply.KEY_NOT_FOUND,
            we_error=int(WeError.SUCCESS),
            row=None,
            statement=statement,
            parameters=parameters,
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        ba998_free(file_access, session_state)
        return outcome

    _WORKING_STORAGE.ws_mysql_count_rows = state.store_result(rows)
    _WORKING_STORAGE.stored_rows_pointer = state
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba050-Fetch"])
    row = state.fetch_record()

    if row is None or _WORKING_STORAGE.ws_mysql_count_rows <= 0:
        # [:L734-L753]. Unreachable, and reproduced - see the docstring.
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            we_error = int(WeError.UNKNOWN_UNEXPECTED)
        else:
            logging_data.sql_err = "0"
            logging_data.sql_msg = ""
            we_error = int(WeError.READ_INDEXED_UNEXPECTED)
        outcome = CursorOutcome(
            fs_reply=FsReply.KEY_NOT_FOUND,
            we_error=we_error,
            row=None,
            statement=statement,
            parameters=parameters,
        )
        outcome.apply_to(file_access)
        logging_data.ws_file_key = ""
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        ba998_free(file_access, session_state)
        return outcome

    # `perform bb100-UnloadHVs` [:L754], then the key through `ws-temp-ed` [:L756-L757]
    # - anomaly N-tempedkey - and `move zero to FS-Reply WE-Error`.
    _row_into_host_variables(row, _WORKING_STORAGE.host_variables)
    bb100_unload_hvs(_WORKING_STORAGE.host_variables, sales)
    _WORKING_STORAGE.ws_temp_ed = _move_alphanumeric_to_ws_temp_ed(
        str(_WORKING_STORAGE.host_variables[PRIMARY_KEY_COLUMN])
    )
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement=statement,
        parameters=parameters,
        file_key=_log_key(_WORKING_STORAGE.ws_temp_ed),
    )
    outcome.apply_to(file_access)
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    ba998_free(file_access, session_state)
    return outcome


def ba060_process_start(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba060-Process-Start.`` [common/salesMT.cbl:L761-L865].

    Position the PRIMARY cursor and deliver nothing; the caller follows with a read-
    next. The cursor mechanics are DELEGATED to
    :func:`~acas_posting.dal.cursor_state.start`, which reproduces this paragraph step
    for step, and this function contributes only the parts that are specific to
    ``salesMT``.

    Args:
        file_access: The caller's block, whose ``Access-Type`` carries the relation and
            to which the outcome is applied.
        sales: The record whose leading ``KEY_LENGTH`` characters are the key.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome. :attr:`CursorOutcome.row` is always ``None``.
    """
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba060-Process-Start"])
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    access_type = int(file_access.access_type)
    key_value = _record_key(sales)
    logging_data = file_access.logging_data

    # `move spaces to MOST-Relation.` [common/salesMT.cbl:L810] then the evaluate.
    _WORKING_STORAGE.most_relation = RELATION_FOR_ACCESS_TYPE.get(
        access_type, "   "
    )
    if not start_access_type_is_valid(access_type):
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            row=None,
            statement="",
            parameters=(),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba060-Process-Start",
            locator="[common/salesMT.cbl:L765]",
            fs_reply=int(file_access.fs_reply),
            we_error=int(file_access.we_error),
            detail="Access-Type %d rejected; the guard admits 5..8 only, so 9 "
            "is dead code (anomaly N-accesstype9)" % int(access_type),
        )
        return outcome

    _WORKING_STORAGE.ws_where = _start_where(
        _WORKING_STORAGE.most_relation.strip()
    )
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_file_key = _log_key(key_value)

    connection = session_state.require_connection()
    with _bridge_cursor(connection) as cursor:
        outcome = _cursor_state.start(
            cursor,
            TABLE_NAME,
            key_value,
            access_type,
            key_number=ONLY_FILE_KEY_NO,
            slot=CursorSlot.PRIMARY,
            states=session_state.cursors,
            file_access=file_access,
        )

    state = _primary(session_state)
    _WORKING_STORAGE.stored_rows_pointer = state if state.cursor_active() else None
    # `CursorState.count_rows` is a PROPERTY, not a method: reading it is the `move WS-
    # Mysql-Count-Rows` equivalent, mirroring the bridge's `MySQL-Count-Rows` host field
    # rather than re-counting the result set.
    _WORKING_STORAGE.ws_mysql_count_rows = state.count_rows
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        # Either `(21, 0)` from the driver-error branch or, on the anomaly N-start-stale
        # path, nothing at all.
        return outcome

    _WORKING_STORAGE.ws_temp_ed = _move_count_to_ws_temp_ed(
        _WORKING_STORAGE.ws_mysql_count_rows
    )
    logging_data.ws_file_key = _log_key(
        f"{_WORKING_STORAGE.most_relation}{key_value} got "
        f"={_WORKING_STORAGE.ws_temp_ed} recs"
    )
    return outcome


def ba070_process_write(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba070-Process-Write.`` [common/salesMT.cbl:L868-L893].

    Note that ``SQL-State`` is cleared with ``move ZERO``, not ``move spaces``, even
    though it is ``pic x(5)`` [copybooks/wsfnctn.cob:L51] - so it becomes ``"0000
    "``-shaped zero fill rather than blanks.

    Args:
        file_access: The caller's block.
        sales: The record to insert.
        session_state: The session holding the connection.

    Returns:
        The outcome, whose row is ``None``: a write returns no record.
    """
    logging_data = file_access.logging_data
    # `perform bb000-HV-Load.` [:L869] - where anomaly A-11's sign loss happens.
    bb000_hv_load(sales, _WORKING_STORAGE.host_variables)
    logging_data.ws_file_key = _log_key(sales.ws_sales_key)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_state = "0".rjust(SQL_STATE_WIDTH, "0")
    logging_data.sql_msg = ""
    logging_data.sql_err = "0".rjust(SQL_ERR_WIDTH, "0")
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba070-Process-Write"])

    try:
        _WORKING_STORAGE.ws_mysql_count_rows = bb200_insert(
            session_state.require_connection(), _WORKING_STORAGE.host_variables
        )
        _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
        _WORKING_STORAGE.ws_mysql_sqlstate = ""
        _WORKING_STORAGE.ws_mysql_error_message = ""
    except Exception as error:  # noqa: BLE001 - classified below, as the COBOL does
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message

    if _WORKING_STORAGE.ws_mysql_count_rows != 1:
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            duplicate = is_duplicate_key_bridge_level(
                logging_data.sql_err, logging_data.sql_state
            )
            file_access.fs_reply = int(
                FsReply.DUPLICATE_KEY if duplicate else FsReply.ERROR
            )
            # `We-Error` is deliberately NOT written here - see the docstring.
            #  NO SECOND RECORD. `_report_driver_failure` below is the one
            #  reporter for this fault; that `We-Error` is deliberately not
            #  written [common/salesMT.cbl:L884-L890] is stated in this
            #  function's docstring, which is where a reader looks for it.
    return CursorOutcome(
        fs_reply=FsReply(int(file_access.fs_reply)),
        we_error=int(file_access.we_error),
        row=None,
        statement="",
        parameters=(),
        status_written=False,
    )


def ba080_process_delete(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba080-Process-Delete.`` [common/salesMT.cbl:L895-L948].

    [:L921-L929] - the ``";"`` that ``bb200-Insert`` [:L1766] and ``bb300-Update``
    [:L2252] both write is absent here. Reproduced: the statement this module builds for
    a delete ends with the predicate.

    Args:
        file_access: The caller's block.
        sales: The record whose key selects the row.
        session_state: The session holding the connection.

    Returns:
        The outcome, whose row is ``None``.
    """
    logging_data = file_access.logging_data
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    key_value = _record_key(sales)
    _WORKING_STORAGE.ws_where = _indexed_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_file_key = _log_key(key_value)
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba080-Process-Delete"])

    statement = (
        f"DELETE FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where}"
    )
    parameters: tuple[object, ...] = (key_value,)

    try:
        with execute_statement(
            session_state.require_connection(), statement, parameters
        ) as cursor:
            _WORKING_STORAGE.ws_mysql_count_rows = int(
                getattr(cursor, "rowcount", 0) or 0
            )
        _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
        _WORKING_STORAGE.ws_mysql_sqlstate = ""
        _WORKING_STORAGE.ws_mysql_error_message = ""
    except Exception as error:  # noqa: BLE001 - classified below
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message

    if _WORKING_STORAGE.ws_mysql_count_rows != 1:
        status_written = False
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
            status_written = True
        else:
            #  SILENT, AND THAT IS ANOMALY N-delete-stale. With no driver error
            #  the inner test is false, so NEITHER status field is written
            #  [common/salesMT.cbl:L931-L942] and the caller keeps whatever the
            #  previous operation left. The frozen bridge displays nothing on
            #  this path, so neither does this (rule R-4).
            pass
        # `go to ba999-End` - Class 3, jumping past the `move zero` below.
        return CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement=statement,
            parameters=parameters,
            status_written=status_written,
        )

    logging_data.sql_msg = ""
    logging_data.sql_err = "0".rjust(SQL_ERR_WIDTH, "0")
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    return CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=None,
        statement=statement,
        parameters=parameters,
        status_written=False,
    )


def ba090_process_rewrite(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba090-Process-Rewrite.`` [common/salesMT.cbl:L950-L993].

    On failure: ``(99, 994)``, but ONLY when the driver reported an error [:L977-L989].

    Args:
        file_access: The caller's block.
        sales: The record to write.
        session_state: The session holding the connection.

    Returns:
        The outcome, whose row is ``None``.
    """
    logging_data = file_access.logging_data
    bb000_hv_load(sales, _WORKING_STORAGE.host_variables)
    logging_data.ws_file_key = _log_key(sales.ws_sales_key)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba090-Process-Rewrite"])
    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    key_value = _record_key(sales)
    _WORKING_STORAGE.ws_where = _indexed_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)

    try:
        _WORKING_STORAGE.ws_mysql_count_rows = bb300_update(
            session_state.require_connection(),
            _WORKING_STORAGE.host_variables,
            key_value,
        )
        _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
        _WORKING_STORAGE.ws_mysql_sqlstate = ""
        _WORKING_STORAGE.ws_mysql_error_message = ""
    except Exception as error:  # noqa: BLE001 - classified below
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message

    statement_note = f"UPDATE {TABLE_NAME} WHERE {_WORKING_STORAGE.ws_where}"

    if _WORKING_STORAGE.ws_mysql_count_rows != 1:
        status_written = False
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)
            status_written = True
        else:
            #  SILENT, for the same reason as `ba080-Process-Delete` above
            #  [common/salesMT.cbl:L977-L990] (rule R-4).
            pass
        return CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement=statement_note,
            parameters=(key_value,),
            status_written=status_written,
        )

    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0".rjust(SQL_ERR_WIDTH, "0")
    logging_data.sql_msg = ""
    return CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=None,
        statement=statement_note,
        parameters=(key_value,),
        status_written=False,
    )


def ba140_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba140-Process-Read-Next.`` [common/salesMT.cbl:L995-L1070].

    and it is a copy of ``ba040`` with four differences, every one of which is
    preserved.

    Args:
        file_access: The caller's block.
        dal_common: Needed because this paragraph performs ``ba999-End`` itself.
        sales: The record the fetch fills.
        session_state: The session holding the connection and the cursors.

    Returns:
        The outcome of the whole verb.
    """
    state = _secondary(session_state)
    logging_data = file_access.logging_data

    if not state.cursor_not_active():
        return ba141_reread(file_access, sales, session_state)

    _WORKING_STORAGE.k = KEY_OFFSET
    _WORKING_STORAGE.l = KEY_LENGTH
    _WORKING_STORAGE.ws_where = _by_name_where()
    _WORKING_STORAGE.j = len(_WORKING_STORAGE.ws_where) + 1
    logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba140-Process-Read-Next"])

    statement = (
        f"SELECT * FROM {QUOTED_TABLE} WHERE {_WORKING_STORAGE.ws_where};"
    )
    # An `int`, not a `str` - anomaly N-lowkey-quoting.
    parameters: tuple[object, ...] = (READ_BY_NAME_LOW_KEY,)

    try:
        rows = _select_rows(session_state.require_connection(), statement, parameters)
    except Exception as error:  # noqa: BLE001 - masked as end of file, per ba040
        errno, sqlstate, message = _driver_error_fields(error)
        _WORKING_STORAGE.ws_mysql_error_number = errno
        _WORKING_STORAGE.ws_mysql_sqlstate = sqlstate
        _WORKING_STORAGE.ws_mysql_error_message = message
        _WORKING_STORAGE.ws_mysql_count_rows = 0
        #  ONE ERROR - see `ba040-Process-Read-Next`. The masking to end of file
        #  per [common/salesMT.cbl:L1057-L1058] is unchanged.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba140-Process-Read-Next",
            locator="[common/salesMT.cbl:L1057-L1058]",
            fs_reply=int(FsReply.END_OF_FILE),
            we_error=int(file_access.we_error),
            sql_err=str(errno),
            sql_state=str(sqlstate),
            detail="the second sequential read failed at the driver and is "
            "MASKED as end of file",
        )
        _record_diagnostics(file_access, errno, sqlstate, message)
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=sqlstate or str(SqlState.NO_DATA),
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    logging_data.ws_file_key = _log_key(READ_BY_NAME_LOW_KEY_TEXT)
    _WORKING_STORAGE.ws_mysql_count_rows = state.store_result(rows)
    _WORKING_STORAGE.ws_mysql_error_number = NO_DRIVER_ERROR
    _WORKING_STORAGE.ws_mysql_sqlstate = ""
    _WORKING_STORAGE.ws_mysql_error_message = ""

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        state.set_cursor_not_active()
        logging_data.sql_state = ""
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=_log_key("No Data"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = _log_where(_WORKING_STORAGE.ws_where)
        return outcome

    state.key_of_reference = PRIMARY_KEY_OF_REFERENCE
    state.most_relation = SEQUENTIAL_READ.relation
    state.set_cursor_active()
    _WORKING_STORAGE.ws_temp_ed = _move_count_to_ws_temp_ed(
        _WORKING_STORAGE.ws_mysql_count_rows
    )
    logging_data.ws_file_key = _log_key(
        f"> 0 got cnt={_WORKING_STORAGE.ws_temp_ed} recs in NAME order"
    )
    ba999_end(file_access, dal_common)

    return ba141_reread(file_access, sales, session_state)


def ba141_reread(
    file_access: FileAccess,
    sales: WsSalesRecord,
    session_state: BridgeSession,
) -> CursorOutcome:
    """``ba141-Reread.`` [common/salesMT.cbl:L1072-L1161].

    Args:
        file_access: The caller's block.
        sales: The record the unload fills.
        session_state: The session holding the cursors.

    Returns:
        The outcome, with :attr:`CursorOutcome.row` set on the success path.
    """
    state = _secondary(session_state)
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    _set_paragraph(file_access, WS_NO_PARAGRAPH_BRIDGE["ba141-Reread"])
    _WORKING_STORAGE.return_code = 0

    row = state.fetch_record()
    if row is None:
        _WORKING_STORAGE.return_code = -1
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    if _WORKING_STORAGE.ws_mysql_count_rows == 0:
        if _WORKING_STORAGE.ws_mysql_error_number != NO_DRIVER_ERROR:
            _record_diagnostics(
                file_access,
                _WORKING_STORAGE.ws_mysql_error_number,
                _WORKING_STORAGE.ws_mysql_sqlstate,
                _WORKING_STORAGE.ws_mysql_error_message,
            )
            _initialize_sales_record(sales, with_filler=True)
            logging_data.ws_file_key = _log_key("EOF2")
        end_fs_reply, end_we_error = end_of_file_status()
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement="",
            parameters=(),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    # `if fs-reply = 10 / set Cursor-Not-Active-2 to true / move "EOF3" to WS-File-Key /
    # go to ba999-End` [common/salesMT.cbl:L1151-L1155] - the by-name twin of the
    # primary-path block at [:L628-L632], differing only in setting `Cursor-Not-
    # Active-2` rather than `Cursor-Not-Active`.
    if int(file_access.fs_reply) == int(FsReply.END_OF_FILE):
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=FsReply.END_OF_FILE,
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            file_key=_log_key("EOF3"),
        )
        outcome.apply_to(file_access)
        logging_data.ws_log_where = ""
        return outcome

    _row_into_host_variables(row, _WORKING_STORAGE.host_variables)
    bb100_unload_hvs(_WORKING_STORAGE.host_variables, sales)
    state.position_at(row[PRIMARY_KEY_COLUMN])
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement="",
        parameters=(),
        file_key=_log_key(_WORKING_STORAGE.host_variables[PRIMARY_KEY_COLUMN]),
    )
    outcome.apply_to(file_access)
    logging_data.ws_log_where = ""
    return outcome


def sales_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
) -> CursorOutcome:
    """``PROCEDURE DIVISION using ...`` [common/salesMT.cbl:L354-L356].

    record or the file definitions the handler is given - which is why the credentials
    must already be in ``RDB-Data`` inside ``File-Access`` before the open, and why
    :class:`BridgeSession` carries the system record separately.

    Args:
        file_access: ``File-Access``, carrying ``File-Function``, ``Access-Type``, the
            two status fields, ``RDB-Data`` and ``Logging-Data``.
        dal_common: ``ACAS-DAL-Common-data`` - the testing switches and the log record
            counter.
        sales: ``WS-Sales-Record`` - read on a write or rewrite, written on a read.

    Returns:
        The outcome, already applied to ``file_access``.
    """
    session_state = session()
    requested = ba010_initialise(file_access)

    if requested is None:
        ba100_bad_function(file_access)
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.UNKNOWN_UNEXPECTED),
            row=None,
            statement="",
            parameters=(),
        )
        ba999_end(file_access, dal_common)
        ba999_exit()
        return outcome

    if requested is FileFunction.OPEN:
        ba020_process_open(file_access, session_state)
        outcome = CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            status_written=False,
        )
    elif requested is FileFunction.CLOSE:
        ba030_process_close(file_access, session_state)
        outcome = CursorOutcome(
            fs_reply=FsReply(int(file_access.fs_reply)),
            we_error=int(file_access.we_error),
            row=None,
            statement="",
            parameters=(),
            status_written=False,
        )
    elif requested is FileFunction.READ_NEXT:
        outcome = ba040_process_read_next(
            file_access, dal_common, sales, session_state
        )
    elif requested is FileFunction.READ_INDEXED:
        outcome = ba050_process_read_indexed(file_access, sales, session_state)
    elif requested is FileFunction.WRITE:
        outcome = ba070_process_write(file_access, sales, session_state)
    elif requested is FileFunction.RE_WRITE:
        outcome = ba090_process_rewrite(file_access, sales, session_state)
    elif requested is FileFunction.DELETE:
        outcome = ba080_process_delete(file_access, sales, session_state)
    elif requested is FileFunction.START:
        outcome = ba060_process_start(file_access, sales, session_state)
    else:
        # `when 31 go to ba140-Process-Read-Next` [:L407-L408].
        outcome = ba140_process_read_next(
            file_access, dal_common, sales, session_state
        )

    ba999_end(file_access, dal_common)
    ba999_exit()
    return outcome


#: Whether an indexed-file store backs the flat-file half of this handler. Permanently
#: ``False``.
FLAT_FILE_STORE_MIGRATED: Final[bool] = False

HANDLER_PROG_NAME: Final[str] = "acas012 (3.3.00)"

SL901: Final[str] = "SL901 Note error and hit return"

SL905: Final[str] = "SL905 Program Error: Temp rec = "

DISPLAY_BLK_WIDTH: Final[int] = 75

#: ``77 A pic 9(4) value zero`` / ``77 B pic 9(4) value zero``
#: [common/acas012.cbl:L251-L252], with the maintainer's own warning.
LENGTH_VARIABLE_DIGITS: Final[int] = 4

FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35

COBOL_FILE_STATUS_EOF: Final[int] = 1

TESTING_1_VALUE: Final[int] = 1


class FlatFileStoreNotMigrated(RuntimeError):
    """An ISAM verb on ``Sales-File`` was reached, and there is no ISAM store.

    Raised by :func:`_isam_verb` at the eight points in the flat-file half of
    ``acas012`` where the frozen program issues a COBOL file verb against ``Sales-File``
    [copybooks/selsl.cob, copybooks/fdsl.cob].

    Attributes:
        verb: The COBOL verb the frozen program issues, quoted.
        paragraph: The paragraph it is issued from.
        locator: The ``[path:Lnnn]`` citation for that statement.
    """

    def __init__(self, verb: str, paragraph: str, locator: str) -> None:
        """Build the refusal with its three coordinates.

        Args:
            verb: The COBOL statement, e.g. ``"read Sales-File next record"``.
            paragraph: The frozen paragraph name, e.g. ``"aa041-Reread"``.
            locator: The ``[common/acas012.cbl:Lnnn]`` citation.
        """
        self.verb: Final[str] = verb
        self.paragraph: Final[str] = paragraph
        self.locator: Final[str] = locator
        super().__init__(
            f"{verb!r} in {paragraph} {locator} operates on the indexed file "
            "Sales-File (salesled.dat), which this migration does not "
            "implement: the Sales entity is mapped onto the MySQL table "
            f"{TABLE_NAME} for the whole of acas_posting (Agent Action Plan "
            "sections 0.2.1.1 and 0.2.2). Everything the paragraph does around "
            "the verb has already been applied to File-Access. Set "
            "File-System-Used to 1 (FS-RDBMS-Used) so acas012.dispatch takes "
            "the ba-Process-RDBMS branch [common/acas012.cbl:L316-L321]."
        )


def _isam_verb(verb: str, paragraph: str, locator: str) -> None:
    """Stand at an ISAM verb and refuse it, loudly and with citations.

    The single point through which every one of the eight COBOL file verbs in the flat-
    file half passes.

    Args:
        verb: The COBOL statement being refused.
        paragraph: The paragraph issuing it.
        locator: Its ``[path:Lnnn]`` citation.

    Raises:
        FlatFileStoreNotMigrated: Always. The function has no success path;
            :data:`FLAT_FILE_STORE_MIGRATED` is a compile-time ``False``.
    """
    _LOG.error(
        "acas012 flat-file path reached %s in %s %s with no indexed store "
        "available; File-System-Used must be 1 for the migrated system",
        verb,
        paragraph,
        locator,
    )
    raise FlatFileStoreNotMigrated(
        verb=verb, paragraph=paragraph, locator=locator
    )


@dataclass
class HandlerWorkingStorage:
    """``working-storage section`` of ``acas012`` [common/acas012.cbl:L245-L261] plus its
    ``file section`` [:L241-L243].

    Attributes:
        fd_record: ``fd Sales-File. 01 Sales-Record.`` [copybooks/fdsl.cob] - the FD
            record area, field-for-field identical to ``WS-Sales-Record``.
        cobol_file_status: ``77 Cobol-File-Status pic 9 value zero`` [:L254].
        a: ``77 A pic 9(4) value zero`` [:L251] - the length of ``WS-Sales-Record``, and
            the first-call sentinel.
        b: ``77 B pic 9(4) value zero`` [:L252] - the length of ``Sales-Record``.
        display_blk: ``77 Display-Blk pic x(75) value spaces`` [:L253].
    """

    fd_record: WsSalesRecord = field(default_factory=WsSalesRecord)
    cobol_file_status: int = 0
    a: int = 0
    b: int = 0
    display_blk: str = " " * DISPLAY_BLK_WIDTH

    @property
    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof value 1`` [common/acas012.cbl:L255].

        Returns:
            ``True`` when ``Cobol-File-Status`` holds :data:`COBOL_FILE_STATUS_EOF`.
        """
        return int(self.cobol_file_status) == COBOL_FILE_STATUS_EOF

    def set_cobol_file_eof(self) -> None:
        """``set Cobol-File-EoF to true`` [common/acas012.cbl:L432]."""
        self.cobol_file_status = COBOL_FILE_STATUS_EOF


_HANDLER_STORAGE: HandlerWorkingStorage = HandlerWorkingStorage()


def handler_storage() -> HandlerWorkingStorage:
    """Return the loaded ``acas012`` program's WORKING-STORAGE.

    Returns:
        The single module-level :class:`HandlerWorkingStorage`.
    """
    return _HANDLER_STORAGE


def reset_handler_storage() -> None:
    """Reload ``acas012``, restoring every VALUE clause.

    Equivalent to ``cancel "acas012"`` followed by a fresh ``CALL``.
    """
    _HANDLER_STORAGE.fd_record = WsSalesRecord()
    _HANDLER_STORAGE.cobol_file_status = 0
    _HANDLER_STORAGE.a = 0
    _HANDLER_STORAGE.b = 0
    _HANDLER_STORAGE.display_blk = " " * DISPLAY_BLK_WIDTH


def _fs_reply_of(value: int) -> FsReply:
    """Present a raw ``FS-Reply pic 99`` value as the enum where it names one.

    ``03 Fs-Reply pic 99`` [copybooks/wsfnctn.cob:L25] holds any two-digit value, and
    the flat-file half writes one - 35, the open-input failure at
    [common/acas012.cbl:L368] - that :class:`~acas_posting.dal.status.FsReply` does not
    name.

    Args:
        value: Whatever ``File-Access.fs_reply`` holds.

    Returns:
        The matching :class:`~acas_posting.dal.status.FsReply` member, or the integer
            itself when no member has that value.
    """
    try:
        return FsReply(int(value))
    except ValueError:
        # `FsReply` is an `IntEnum`, so an `int` is interchangeable with a member
        # everywhere `CursorOutcome` uses the field. Preserving 35 exactly matters more
        # than the annotation.
        return cast(FsReply, int(value))


def _outcome_from_file_access(file_access: FileAccess) -> CursorOutcome:
    r"""Photograph the caller's block after a flat-file verb has written it.

    The flat-file half has no SQL and no row, so the returned outcome carries only the
    status pair, and ``status_written`` is ``False`` because the paragraphs have already
    written ``File-Access`` directly - exactly as the frozen program's ``MOVE``\ s do,
    through the linkage.

    Args:
        file_access: The caller's ``File-Access`` block, already written.

    Returns:
        A :class:`~acas_posting.dal.cursor_state.CursorOutcome` mirroring ``FS-Reply``,
            ``WE-Error``, ``SQL-State`` and ``WS-File-Key``.
    """
    return CursorOutcome(
        fs_reply=_fs_reply_of(file_access.fs_reply),
        we_error=int(file_access.we_error),
        row=None,
        statement="",
        parameters=(),
        status_written=False,
        sql_state=str(file_access.logging_data.sql_state),
        file_key=str(file_access.logging_data.ws_file_key),
    )


def _move_record(source: WsSalesRecord, destination: WsSalesRecord) -> None:
    """``move Sales-Record to WS-Sales-Record`` and its inverse - a group MOVE.

    ``01 Sales-Record`` [copybooks/fdsl.cob] and ``01 WS-Sales-Record``
    [copybooks/wssl.cob] are field-for-field identical: same order, same picture
    clauses, same ``USAGE``, same ``REDEFINES``, same three ``FILLER`` items, both
    documented as "rec size 300 bytes".

    Args:
        source: The area being read.
        destination: The area being written, mutated in place so the caller's own object
            identity survives - a COBOL ``MOVE`` never rebinds a linkage item.
    """
    for declared in dataclass_fields(source):
        setattr(
            destination, declared.name, deepcopy(getattr(source, declared.name))
        )


def aa020_process_open(
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa020-Process-Open.`` [common/acas012.cbl:L361-L398].

    aa020-Process-Open. *> move spaces to WS-File-Key. *> for logging move "OPEN Sales
    Ledger File" to WS-File-Key move 201 to WS-No-Paragraph.

    Args:
        file_access: ``File-Access``. ``Access-Type`` selects the branch; ``Fs-Reply``
            is both the FILE STATUS field and the reported status.
        file_defs: ``File-Defs``, whose ``file-12`` names the file the SELECT assigns
            [copybooks/selsl.cob, copybooks/file12.cob]. Read for the log record.
        dal_common: ``ACAS-DAL-Common-data`` - carried so the paragraph's exit can log.

    Raises:
        FlatFileStoreNotMigrated: On ``fn-input``, ``fn-i-o`` or ``fn-output``, at the
            ``open`` itself. Every write the paragraph performs before that point has
            already been applied.
    """
    storage = handler_storage()
    file_access.logging_data.ws_file_key = _log_key("OPEN Sales Ledger File")
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa020-Process-Open"])

    access_type = int(file_access.access_type)
    flat_file_name = str(file_defs.file_defs_a.file_12).rstrip()

    if access_type == AccessType.INPUT:
        _isam_verb(
            f"open input Sales-File ({flat_file_name})",
            "aa020-Process-Open",
            "[common/acas012.cbl:L366]",
        )
    elif access_type == AccessType.I_O:
        # `open i-o Sales-File` [:L374], then anomaly N-open-createdance.
        _isam_verb(
            f"open i-o Sales-File ({flat_file_name})",
            "aa020-Process-Open",
            "[common/acas012.cbl:L374]",
        )
    elif access_type == AccessType.OUTPUT:
        _isam_verb(
            f"open output Sales-File ({flat_file_name})",
            "aa020-Process-Open",
            "[common/acas012.cbl:L383]",
        )
    elif access_type == AccessType.EXTEND:
        # `if fn-extend` [:L385] - the `open extend` is commented out [:L386] and
        # replaced by a status decision. Reproduced whole; no file is touched.
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        _LOG.warning(
            "aa020-Process-Open refused fn-extend with (99, 997): "
            "'Must not be used for ISAM files' "
            "[common/acas012.cbl:L385-L389]"
        )
        aa999_main_exit(file_access, dal_common)
        return
    else:
        # ANOMALY N-open-nothing: no branch matched, nothing was opened, and `FS-Reply`
        # was never written [:L390-L393].
        _LOG.error(
            "aa020-Process-Open matched no branch for Access-Type %d: nothing "
            "was opened and FS-Reply was not written (anomaly N-open-nothing) "
            "[common/acas012.cbl:L390-L393]",
            access_type,
        )

    # `move zero to Cobol-File-Status` [:L395]. Unreachable for 1/2/3 because the `open`
    # above raises, and skipped for 4 because that branch returned.
    storage.cobol_file_status = 0
    # `if fs-reply not = zero move 999 to WE-Error.` [:L396-L397].
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.we_error = int(WeError.NOT_USED)
    aa999_main_exit(file_access, dal_common)


def aa030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    r"""``aa030-Process-Close.`` [common/acas012.cbl:L400-L411].

    paragraph in the program that ``perform``\ s ``aa999-main-exit`` [:L407] instead of
    ``go``\ ing to it, so control comes back; it then zeroes ``File-Function`` and
    ``Access-Type`` [:L408-L409] and logs a SECOND time [:L410].

    Args:
        file_access: ``File-Access``. ``File-Function`` and ``Access-Type`` are both
            zeroed before the second log record.
        dal_common: ``ACAS-DAL-Common-data`` - both log records go through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``close`` [:L403]. Paragraph 202 and the
            blanked ``WS-File-Key`` have already been written, matching the frozen
            program's state at that instant exactly.
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa030-Process-Close"])
    file_access.logging_data.ws_file_key = _log_key("")
    _isam_verb(
        "close Sales-File",
        "aa030-Process-Close",
        "[common/acas012.cbl:L403]",
    )
    # Everything below reproduces the rest of the paragraph. Unreachable while
    # FLAT_FILE_STORE_MIGRATED is False, and retained because rule R-5 requires the
    # paragraph, not a fragment of it.
    storage.cobol_file_status = 0
    file_access.logging_data.ws_file_key = _log_key("CLOSE Sales Ledger File")
    aa999_main_exit(file_access, dal_common)
    file_access.file_function = 0
    file_access.access_type = 0
    ca_process_logs_acas012(file_access, dal_common)
    # `go to aa-main-exit.` [:L411] - Class 3, and it SKIPS `aa999-main-exit`, which is
    # why there are exactly two records and not three.
    aa_main_exit()


def aa040_process_read_next(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> bool:
    """``aa040-Process-Read-Next.`` [common/acas012.cbl:L413-L427].

    Reached by BOTH ``when 3`` and ``when 31`` [:L341-L343] - anomaly N-when31.

    Args:
        file_access: ``File-Access``. ``FS-Reply``, ``WE-Error``, ``SQL-Err`` and ``SQL-
            Msg`` are written on the end-of-file branch.
        sales: ``WS-Sales-Record`` - only ``WS-Sales-Key`` is blanked.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Returns:
        ``True`` when the end-of-file branch transferred to ``aa999-main-exit`` [:L426]
            and the request is finished; ``False`` when the paragraph fell off its end
            into ``aa041-Reread`` [:L429].
    """
    storage = handler_storage()
    _set_paragraph(
        file_access, WS_NO_PARAGRAPH_HANDLER["aa040-Process-Read-Next"]
    )
    if not storage.cobol_file_eof:
        return False

    # `move 10 to FS-Reply WE-Error` [:L420-L421] - the one status pair the frozen
    # sources write into BOTH fields, which is why `end_of_file_status()` returns both
    # halves.
    file_access.fs_reply, file_access.we_error = end_of_file_status()
    _assign_record_value(
        sales,
        PRIMARY_KEY_COLUMN,
        _store_into_character_host_variable("", column=PRIMARY_KEY_COLUMN),
    )
    file_access.logging_data.sql_err = " " * SQL_ERR_WIDTH
    file_access.logging_data.sql_msg = " " * SQL_MSG_WIDTH
    # `stop "Cobol File EOF"  *> for testing` [:L425] - anomaly N-stopliteral.
    #  ONE ERROR, THROUGH THE ONE REPORTER, at the SAME LEVEL as every other
    #  handler that carries this stop. Reporting it at INFO here, WARNING in
    #  acas006 and acas007, DEBUG in acas016 and ERROR in acas019 made the same
    #  event unfindable. The keystroke wait is omitted per Agent Action Plan
    #  section 0.3.4; the transfer that follows is preserved by the caller.
    log_cobol_stop(
        _LOG,
        program=HANDLER,
        paragraph="aa040-Process-Read-Next",
        literal="Cobol File EOF",
        locator="[common/acas012.cbl:L425]",
    )
    aa999_main_exit(file_access, dal_common)
    return True


def aa041_reread(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa041-Reread.`` [common/acas012.cbl:L429-L443].

    declares ``aa041-Reread`` only [common/acas012.cbl:L429]; the siblings declare
    ``aa041-Reread`` AND ``aa051-Reread`` [common/acas006.cbl:L436,
    common/acas006.cbl:L461] and [common/acas007.cbl:L430, common/acas007.cbl:L451], the
    second serving their read-indexed path. Here ``aa050-Process-Read-Indexed`` reads
    inline instead [common/acas012.cbl:L465-L486]. Recorded as anomaly N-onereread.

    Args:
        file_access: ``File-Access``. ``FS-Reply`` is the FILE STATUS field the ``read``
            itself writes [copybooks/selsl.cob].
        sales: ``WS-Sales-Record`` - the whole record is replaced from the FD area on
            success, or initialized on end of file.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``read ... next record`` [:L430], the
            paragraph's first statement.
    """
    storage = handler_storage()
    _isam_verb(
        "read Sales-File next record",
        "aa041-Reread",
        "[common/acas012.cbl:L430]",
    )
    if int(file_access.fs_reply) == int(FsReply.END_OF_FILE):
        file_access.fs_reply, file_access.we_error = end_of_file_status()
        storage.set_cobol_file_eof()
        storage.cobol_file_status = COBOL_FILE_STATUS_EOF
        _initialize_sales_record(sales, with_filler=False)
        file_access.logging_data.ws_file_key = _log_key("EOF")
        aa999_main_exit(file_access, dal_common)
        return
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        aa999_main_exit(file_access, dal_common)
        return
    _move_record(storage.fd_record, sales)
    # `move Sales-Key to WS-File-Key.` [:L441] - the FD record's key, not the linkage
    # record's. See :func:`_move_record` on why both are the same class.
    file_access.logging_data.ws_file_key = _log_key(
        _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
    )
    # `move zeros to WE-Error.` [:L442] - WE-Error only; anomaly N-reread-noreply.
    file_access.we_error = int(WeError.SUCCESS)
    aa999_main_exit(file_access, dal_common)


def aa045_eval_keys(file_access: FileAccess, sales: WsSalesRecord) -> None:
    """``aa045-Eval-Keys.`` [common/acas012.cbl:L447-L463].

    *> The next block will never get executed unless performed so is it *> needed ?
    aa045-Eval-Keys.

    Args:
        file_access: ``File-Access``. ``File-Function`` and ``File-Key-No`` select the
            arm; ``WS-File-Key`` receives the result.
        sales: ``WS-Sales-Record`` - ``WS-Sales-Key`` is the source.
    """
    storage = handler_storage()
    function = int(file_access.file_function)
    if function in _AA045_KEYED_FUNCTIONS:
        if int(file_access.logging_data.file_key_no) == ONLY_FILE_KEY_NO:
            key_text = str(_record_value(sales, PRIMARY_KEY_COLUMN))
            file_access.logging_data.ws_file_key = _log_key(key_text)
            _assign_record_value(
                storage.fd_record,
                PRIMARY_KEY_COLUMN,
                _store_into_character_host_variable(
                    key_text, column=PRIMARY_KEY_COLUMN
                ),
            )
        else:
            file_access.logging_data.ws_file_key = _log_key("")
    else:
        file_access.logging_data.ws_file_key = _log_key("")


#: The five ``when`` values ``aa045-Eval-Keys`` treats as keyed
#: [common/acas012.cbl:L449-L453]. Four of them are unreachable, because only
#: ``aa050-Process-Read-Indexed`` performs the paragraph [:L470] - anomaly N-evalkeys-
#: dead.
_AA045_KEYED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
    }
)


# `move spaces to WS-Sales-Record` - ANOMALY N-spacesrecord, MEASURED `aa050-Process-
# Read-Indexed` answers a failed indexed read by moving SPACES over the whole record
# [common/acas012.cbl:L480].

#: ``move spaces`` over a binary field of W bytes, as an unsigned big-endian integer of
#: 0x20 repeated W times.
SPACE_FILLED_BINARY_BY_WIDTH: Final[Mapping[int, int]] = MappingProxyType(
    {
        1: 32,
        2: 8224,
        4: 538976288,
        8: 2314885530818453536,
    }
)

BINARY_WIDTH_BY_DIGITS: Final[tuple[tuple[int, int], ...]] = (
    (2, 1),
    (4, 2),
    (9, 4),
    (18, 8),
)

#: The byte width of each ``USAGE`` that declares its own size rather than deriving one
#: from a picture clause.
BINARY_WIDTH_BY_USAGE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "BINARY-CHAR": 1,
        "BINARY-SHORT": 2,
        "BINARY-LONG": 4,
        "COMP-5": 8,
        "POINTER": 8,
    }
)


def _space_filled_binary_width(digits: int) -> int:
    """The byte width of a ``COMP`` field of ``digits`` declared digits.

    Args:
        digits: The picture clause's total digit count.

    Returns:
        The field's width in bytes.
    """
    for upper, width in BINARY_WIDTH_BY_DIGITS:
        if digits <= upper:
            return width
    return 8


def _space_filled_value(column: str) -> Decimal | int | str:
    """What one field of ``SALEDGER-REC`` holds after ``move spaces``.

    Drives entirely off the field's dictionary entry - its ``USAGE``, digit count and
    scale - so the answer for each of the thirty-seven columns is derived from the same
    authority every other conversion in this module uses, rather than from a hand-
    written table of thirty-seven values.

    Args:
        column: The column whose feeding field is being space-filled.

    Returns:
        For a character field, spaces at its declared width.

    Raises:
        KeyError: If ``column`` is not a ``SALEDGER-REC`` column.
    """
    entry = ENTRIES[column]
    copybook = entry.copybook
    if column in CHARACTER_COLUMNS or copybook.is_group:
        return _store_into_character_host_variable("", column=column)

    digits = int(copybook.digits or 0)
    scale = int(copybook.scale or 0)
    usage = getattr(copybook.usage, "value", str(copybook.usage)).upper()

    if usage == "COMP-3":
        width = (digits + 2) // 2
        used = ("20" * width)[-(digits + 1) :] if digits else ""
        unscaled = int(used[:digits]) if digits else 0
    elif usage in BINARY_WIDTH_BY_USAGE:
        unscaled = SPACE_FILLED_BINARY_BY_WIDTH[BINARY_WIDTH_BY_USAGE[usage]]
    elif usage == "COMP":
        unscaled = SPACE_FILLED_BINARY_BY_WIDTH[
            _space_filled_binary_width(digits)
        ]
    else:
        return " " * digits

    if scale:
        return Decimal(unscaled).scaleb(-scale)
    return unscaled


#: Every column's value after ``move spaces to WS-Sales-Record``, resolved once at
#: import so the result is a constant a test can assert against and two processes agree
#: on byte for byte.
SPACE_FILLED_RECORD: Final[Mapping[str, Decimal | int | str]] = (
    MappingProxyType({column: _space_filled_value(column) for column in COLUMN_ORDER})
)


def _move_spaces_to_sales_record(sales: WsSalesRecord) -> None:
    """``move spaces to WS-Sales-Record`` [common/acas012.cbl:L480].

    above for the measured values.

    Args:
        sales: ``WS-Sales-Record``, mutated in place. Only the thirty-seven dictionary-
            mapped fields are written.
    """
    for column, value in SPACE_FILLED_RECORD.items():
        _assign_record_value(sales, column, value)
    _LOG.warning(
        "aa050-Process-Read-Indexed moved SPACES over WS-Sales-Record: the "
        "twenty-three numeric fields now hold space BYTES read as data "
        "(anomaly N-spacesrecord) [common/acas012.cbl:L480]"
    )


def aa050_process_read_indexed(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas012.cbl:L465-L486].

    The ONLY paragraph that performs ``aa045-Eval-Keys`` [:L470], and it does so because
    that paragraph moves the key into the FD record's ``Sales-Key`` - the field this
    ``read`` searches on.

    Args:
        file_access: ``File-Access``. ``File-Key-No`` selects the branch; ``Fs-Reply``
            is the FILE STATUS field the ``read`` writes.
        sales: ``WS-Sales-Record`` - replaced from the FD area on success, or space-
            filled on failure.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``read ... key`` [:L473], after paragraph 204,
            the key move and the status clear have been applied.
    """
    storage = handler_storage()
    _set_paragraph(
        file_access, WS_NO_PARAGRAPH_HANDLER["aa050-Process-Read-Indexed"]
    )
    aa045_eval_keys(file_access, sales)
    storage.cobol_file_status = 0
    if int(file_access.logging_data.file_key_no) == ONLY_FILE_KEY_NO:
        _isam_verb(
            "read Sales-File key Sales-Key",
            "aa050-Process-Read-Indexed",
            "[common/acas012.cbl:L473]",
        )
        if int(file_access.fs_reply) == int(FsReply.SUCCESS):
            _move_record(storage.fd_record, sales)
            file_access.logging_data.ws_file_key = _log_key(
                _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
            )
        else:
            _move_spaces_to_sales_record(sales)
        aa999_main_exit(file_access, dal_common)
        return
    # `move 998 to WE-Error / move 99 to fs-reply` [:L484-L485], the frozen comment
    # conceding `*> but should never get here`.
    file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
    file_access.fs_reply = int(FsReply.ERROR)
    _LOG.error(
        "aa050-Process-Read-Indexed reached its 'should never get here' branch "
        "with File-Key-No = %s; reporting (99, 998) "
        "[common/acas012.cbl:L484-L486]",
        file_access.logging_data.file_key_no,
    )
    aa999_main_exit(file_access, dal_common)


def aa060_process_start(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa060-Process-Start.`` [common/acas012.cbl:L488-L534].

    moves 998 into ``WE-Error`` and NOTHING into ``FS-Reply`` [:L499-L502], and ``FS-
    Reply`` was zeroed four lines earlier [:L493-L494].

    Args:
        file_access: ``File-Access``. ``Access-Type`` chooses the relation; ``Fs-Reply``
            is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - ``WS-Sales-Key`` is copied to both ``WS-File-Key``
            and the FD record's key.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At whichever of the four ``start`` verbs the relation
            selects [:L508, :L515, :L522, :L529].
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa060-Process-Start"])
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    storage.cobol_file_status = 0
    key_text = str(_record_value(sales, PRIMARY_KEY_COLUMN))
    file_access.logging_data.ws_file_key = _log_key(key_text)
    _assign_record_value(
        storage.fd_record,
        PRIMARY_KEY_COLUMN,
        _store_into_character_host_variable(key_text, column=PRIMARY_KEY_COLUMN),
    )
    access_type = int(file_access.access_type)
    if not start_access_type_is_valid(access_type):
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        _LOG.error(
            "aa060-Process-Start refused Access-Type %d with WE-Error 998 and "
            "FS-Reply left at zero (anomaly N-start998-noreply) "
            "[common/acas012.cbl:L499-L502]",
            access_type,
        )
        aa999_main_exit(file_access, dal_common)
        return

    keyed = int(file_access.logging_data.file_key_no) == ONLY_FILE_KEY_NO
    for expected, relation, locator in _AA060_START_BLOCKS:
        if keyed and access_type == expected:
            _isam_verb(
                f"start Sales-File key {relation} Sales-Key",
                "aa060-Process-Start",
                locator,
            )
            # `invalid key move 21 to Fs-Reply / go to aa999-main-exit` [:L509-L510] -
            # note FS-Reply only.
            if int(file_access.fs_reply) != int(FsReply.SUCCESS):
                file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
                aa999_main_exit(file_access, dal_common)
                return
    if not keyed:
        _LOG.error(
            "aa060-Process-Start fell past all four start blocks with "
            "File-Key-No = %s: nothing was started and the paragraph reports "
            "(0, 0) (anomaly N-start-nokey) [common/acas012.cbl:L506-L534]",
            file_access.logging_data.file_key_no,
        )
    aa999_main_exit(file_access, dal_common)


#: The four ``start`` blocks of ``aa060-Process-Start``, in the frozen source order
#: [common/acas012.cbl:L506-L533]: ``fn-equal-to``, ``fn-less-than``, ``fn-greater-
#: than``, ``fn-not-less-than``.
_AA060_START_BLOCKS: Final[tuple[tuple[int, str, str], ...]] = (
    (int(AccessType.EQUAL_TO), "=", "[common/acas012.cbl:L508]"),
    (int(AccessType.LESS_THAN), "<", "[common/acas012.cbl:L515]"),
    (int(AccessType.GREATER_THAN), ">", "[common/acas012.cbl:L522]"),
    (int(AccessType.NOT_LESS_THAN), "not <", "[common/acas012.cbl:L529]"),
)


def aa070_process_write(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa070-Process-Write.`` [common/acas012.cbl:L537-L546].

    The log tag is taken from ``Sales-Key`` [:L542] - the FD record's key, which the
    whole-record move on the line above has just filled from ``WS-Sales-Key``. So the
    tag is the key being written, arrived at indirectly.

    Args:
        file_access: ``File-Access``. ``Fs-Reply`` is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - copied wholesale into the FD area.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``write`` [:L543]. The record move, the status
            clear and the log tag have all been applied first.
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa070-Process-Write"])
    _move_record(sales, storage.fd_record)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    storage.cobol_file_status = 0
    file_access.logging_data.ws_file_key = _log_key(
        _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
    )
    _isam_verb(
        "write Sales-Record",
        "aa070-Process-Write",
        "[common/acas012.cbl:L543]",
    )
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        # FS-Reply only; WE-Error keeps its zero - anomaly N-write-noweerror.
        file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    aa999_main_exit(file_access, dal_common)


def aa080_process_delete(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa080-Process-Delete.`` [common/acas012.cbl:L548-L557].

    ``21`` goes into ``FS-Reply`` only [:L555], leaving ``WE-Error`` at the zero from
    [:L552] - the same asymmetry as ``aa070``. The bridge's own delete is worse.

    Args:
        file_access: ``File-Access``. ``Fs-Reply`` is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - only ``WS-Sales-Key`` is read.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``delete`` [:L554].
    """
    storage = handler_storage()
    _set_paragraph(file_access, WS_NO_PARAGRAPH_HANDLER["aa080-Process-Delete"])
    key_text = str(_record_value(sales, PRIMARY_KEY_COLUMN))
    _assign_record_value(
        storage.fd_record,
        PRIMARY_KEY_COLUMN,
        _store_into_character_host_variable(key_text, column=PRIMARY_KEY_COLUMN),
    )
    file_access.logging_data.ws_file_key = _log_key(key_text)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    storage.cobol_file_status = 0
    _isam_verb(
        "delete Sales-File record",
        "aa080-Process-Delete",
        "[common/acas012.cbl:L554]",
    )
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    aa999_main_exit(file_access, dal_common)


def aa090_process_rewrite(
    file_access: FileAccess,
    sales: WsSalesRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas012.cbl:L559-L569].

    clears the status pair BEFORE taking the log tag [:L540-L542]; rewrite takes the tag
    FIRST and clears afterwards [:L563-L564].

    Args:
        file_access: ``File-Access``. ``Fs-Reply`` is the FILE STATUS field.
        sales: ``WS-Sales-Record`` - copied wholesale into the FD area.
        dal_common: ``ACAS-DAL-Common-data`` - the exit logs through it.

    Raises:
        FlatFileStoreNotMigrated: At the ``rewrite`` [:L566].
    """
    storage = handler_storage()
    _set_paragraph(
        file_access, WS_NO_PARAGRAPH_HANDLER["aa090-Process-Rewrite"]
    )
    _move_record(sales, storage.fd_record)
    file_access.logging_data.ws_file_key = _log_key(
        _record_value(storage.fd_record, PRIMARY_KEY_COLUMN)
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    storage.cobol_file_status = 0
    _isam_verb(
        "rewrite Sales-Record",
        "aa090-Process-Rewrite",
        "[common/acas012.cbl:L566]",
    )
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    aa999_main_exit(file_access, dal_common)


def aa100_bad_function(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa100-Bad-Function.`` [common/acas012.cbl:L571-L576].

    Reached from TWO places in ``aa010-main``.

    Args:
        file_access: ``File-Access``, receiving ``(99, 999)``.
        dal_common: ``ACAS-DAL-Common-data`` - the fall-through logs through it.
    """
    _LOG.error(
        "aa100-Bad-Function: File-Function %s is not one of the nine acas012 "
        "supports; reporting (99, 999) [common/acas012.cbl:L571-L576]",
        file_access.file_function,
    )
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa999-main-exit.`` [common/acas012.cbl:L578-L581].

    ``AA-Main-Exit`` [:L318], not to this paragraph, so the handler writes no log record
    of its own when the bridge did the work - which is exactly what the frozen comment
    on ``Ca-Process-Logs`` claims.

    Args:
        file_access: ``File-Access`` - the log record's whole content.
        dal_common: ``ACAS-DAL-Common-data`` - carries ``SW-Testing`` and the record
            counter.
    """
    if int(dal_common.sw_testing) == TESTING_1_VALUE:
        ca_process_logs_acas012(file_access, dal_common)


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas012.cbl:L583].

    statements at all: the three lines under its label are comments, and the next label
    is ``aa-Exit`` [:L587].
    """
    return


def aa_exit() -> None:
    """``aa-Exit.`` [common/acas012.cbl:L587-L588].

    ``exit program`` returns to the caller with the linkage records as they stand -
    which is the whole output protocol of this handler, since every status, every log
    field and the record itself live in the caller's storage.
    """
    return


# 9.2 `ba-Process-RDBMS section.` [common/acas012.cbl:L590] - the live half *> Here we
# call the relevent RDBMS module for this table * *> which will include processing any
# other joined tables as needed * Four paragraphs, and control simply falls through
# them.


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas012.cbl:L598-L604].

    ``aa010-main`` moved 11 in [:L292]; this moves 21 [:L604]. So a log record written
    on the RDB path carries 21 and one written on the flat-file path carries 11 -
    anomaly N-log.

    Args:
        file_access: ``File-Access`` - ``WS-Log-File-No`` is in its ``Logging-Data``, so
            this writes the caller's block.
    """
    file_access.logging_data.ws_log_file_no = LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas012.cbl:L606-L646].

    ``function Length`` of a group returns its size in bytes, and ``WS-Sales-Record``
    [copybooks/wssl.cob] and ``Sales-Record`` [copybooks/fdsl.cob] are field-for-field
    identical - both copybook headers state "rec size 300 bytes" and both carry the same
    three ``FILLER`` items, the same ``REDEFINES`` and the same ``USAGE`` on every
    field.

    Args:
        system: ``System-Record``, the first linkage parameter. Read only inside the
            first-call block, exactly as the frozen program reads it.
        file_access: ``File-Access``. ``RDB-Data`` receives the credentials and the
            status pair receives 901/99 on the dead branch.
        dal_common: ``ACAS-DAL-Common-data`` - the 901 branch logs through it.

    Returns:
        ``True`` when the frozen program would ``go to ba-rdbms-exit`` [:L633],
            abandoning the request; ``False`` when it falls through to ``ba015-Test-
            Ends``.
    """
    storage = handler_storage()
    if storage.a != 0:
        return False

    storage.a = WS_SALES_RECORD_BYTES % (10**LENGTH_VARIABLE_DIGITS)
    storage.b = SALES_RECORD_BYTES % (10**LENGTH_VARIABLE_DIGITS)
    if storage.a < storage.b:  # pragma: no cover - N-recsize-unreachable
        file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
        file_access.fs_reply = int(FsReply.ERROR)
    if int(file_access.we_error) == int(
        WeError.RECORD_SIZE_MISMATCH
    ):  # pragma: no cover - N-recsize-unreachable
        storage.display_blk = (
            f"{SL905}"
            f"{storage.a:0{LENGTH_VARIABLE_DIGITS}d}"
            " < "
            "Sales-Rec = "
            f"{storage.b:0{LENGTH_VARIABLE_DIGITS}d}"
        )[:DISPLAY_BLK_WIDTH].ljust(DISPLAY_BLK_WIDTH)
        _LOG.error(
            "ba012-Test-WS-Rec-Size-2 record length mismatch: %s "
            "[common/acas012.cbl:L615-L628] - the caller must stop",
            storage.display_blk.rstrip(),
        )
        if int(dal_common.sw_testing) == TESTING_1_VALUE:
            ca_process_logs_acas012(file_access, dal_common)
        return True

    # The six credential moves [:L640-L645], in the frozen order: schema, user,
    # password, PORT, host, socket.
    loaded = load_rdb_data_once(system)
    rdb_data = file_access.rdb_data
    rdb_data.db_schema = loaded.db_schema
    rdb_data.db_uname = loaded.db_uname
    rdb_data.db_upass = loaded.db_upass
    rdb_data.db_port = loaded.db_port
    rdb_data.db_host = loaded.db_host
    rdb_data.db_socket = loaded.db_socket
    session().system_record = system
    return False


def ba015_test_ends(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    sales: WsSalesRecord,
) -> CursorOutcome:
    """``ba015-Test-Ends.`` [common/acas012.cbl:L648-L662].

    The whole of the RDB half's work, in one ``CALL``. Three parameters, in this order -
    the bridge gets neither ``System-Record`` nor ``File-Defs``, which is why
    :func:`ba012_test_ws_rec_size_2` has to hand the system record over separately.

    Args:
        file_access: ``File-Access`` - first parameter of the ``CALL``.
        dal_common: ``ACAS-DAL-Common-data`` - second parameter.
        sales: ``WS-Sales-Record`` - third parameter.

    Returns:
        The bridge's outcome, already applied to ``file_access``.
    """
    return sales_mt(file_access, dal_common, sales)


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit.`` [common/acas012.cbl:L666-L667].

    The section's single exit, and the target of the 901 branch's ``go to`` [:L633].
    """
    return


def ca_process_logs_acas012(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``Ca-Process-Logs.`` [common/acas012.cbl:L670-L676].

    PARAGRAPH OF THE SAME NAME.** ``Ca-Process-Logs`` exists in both
    ``common/acas012.cbl`` [common/acas012.cbl:L670] and ``common/salesMT.cbl``
    [common/salesMT.cbl:L2261], which is legal because they are separate programs.

    Args:
        file_access: The block the log record is built from.
        dal_common: The block carrying ``SW-Testing`` and ``Log-File-Rec-Written``.
    """
    # `call "fhlogger" using File-Access ACAS-DAL-Common-data.` [:L673-L674]. Identical
    # arguments to the bridge's call, so the same reproduction serves.
    ca_process_logs(file_access, dal_common)


def ba_process_rdbms(
    system: SystemRecord,
    sales: WsSalesRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> CursorOutcome:
    """``ba-Process-RDBMS section.`` [common/acas012.cbl:L590-L667].

    Args:
        system: ``System-Record`` - reaches ``ba012`` only.
        sales: ``WS-Sales-Record`` - reaches the bridge.
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.

    Returns:
        The bridge's outcome, or - on the unreachable 901 branch - a photograph of the
            block the 901 branch left behind, since no bridge call was made.
    """
    ba010_test_ws_rec_size(file_access)
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        # `go to ba-rdbms-exit` [:L633] - the bridge is never called.
        ba_rdbms_exit()
        return _outcome_from_file_access(file_access)
    outcome = ba015_test_ends(file_access, dal_common, sales)
    ba_rdbms_exit()
    return outcome


def aa010_main(
    system: SystemRecord,
    sales: WsSalesRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> CursorOutcome:
    """``aa010-main.`` [common/acas012.cbl:L287-L359] - the whole dispatcher.

    Seven steps, in the frozen order, every one of them reproduced.

    Args:
        system: ``System-Record`` - first linkage parameter [:L276].
        sales: ``WS-Sales-Record`` - second [:L277].
        file_access: ``File-Access`` - third [:L278].
        file_defs: ``File-Defs`` - fourth [:L279].
        dal_common: ``ACAS-DAL-Common-data`` - fifth [:L280].

    Returns:
        A :class:`~acas_posting.dal.cursor_state.CursorOutcome`. The AUTHORITATIVE
            channel is ``file_access``, which every paragraph has already written
            through the linkage exactly as the frozen program does.

    Raises:
        FlatFileStoreNotMigrated: If the flat-file half is entered and reaches an ISAM
            verb - see :class:`FlatFileStoreNotMigrated`.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_system = int(LOG_SYSTEM)
    logging_data.ws_log_file_no = LOG_FILE_NO_COBOL

    function = int(file_access.file_function)
    # exactly one `when` arm, so the mapping is equivalent to the `evaluate`; the frozen
    # arm order is 4/9 then 8, which `GUARDED_KEY_FUNCTIONS` preserves.
    guarded = GUARDED_KEY_FUNCTIONS.get(cast(FileFunction, function))
    if guarded is not None and (
        int(logging_data.file_key_no) != ONLY_FILE_KEY_NO
    ):
        file_access.we_error = int(guarded)
        file_access.fs_reply = int(FsReply.ERROR)
        _LOG.error(
            "acas012 key guard refused File-Function %d with File-Key-No %s: "
            "(99, %d) [common/acas012.cbl:L296-L308]",
            function,
            logging_data.file_key_no,
            int(guarded),
        )
        aa999_main_exit(file_access, dal_common)
        aa_main_exit()
        return _outcome_from_file_access(file_access)

    flat_statuses = system.system_data_block.rdbms_flat_statuses
    if int(flat_statuses.file_system_used) != FS_COBOL_FILES_USED:
        fa_statuses = file_access.fa_rdbms_flat_statuses
        fa_statuses.fa_file_system_used = int(flat_statuses.file_system_used)
        fa_statuses.fa_file_duplicates_in_use = int(
            flat_statuses.file_duplicates_in_use
        )
        outcome = ba_process_rdbms(system, sales, file_access, dal_common)
        # `go to AA-Main-Exit` [:L319] - Class 3, and it SKIPS `aa999-main-exit`, so the
        # handler writes no log record of its own.
        aa_main_exit()
        return outcome

    _LOG.warning(
        "acas012 entered its flat-file half: File-System-Used is %s "
        "(FS-Cobol-Files-Used) and this migration maps Sales onto %s "
        "[common/acas012.cbl:L316]",
        flat_statuses.file_system_used,
        TABLE_NAME,
    )
    # OTHER section; anomaly N-performrange.
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        ba_rdbms_exit()
        aa_main_exit()
        return _outcome_from_file_access(file_access)

    # is deliberately NOT cleared - anomaly N-nostatusclear [:L332-L333].
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH

    # EVERY `when` arm is a `go to`, not a `perform`, so control NEVER returns to this
    # paragraph once a verb has been entered.
    transferred = True
    if function == FileFunction.OPEN:
        aa020_process_open(file_access, file_defs, dal_common)
    elif function == FileFunction.CLOSE:
        aa030_process_close(file_access, dal_common)
    elif function in _AA040_SHARED_FUNCTIONS:
        # `when 3 / when 31 go to aa040-Process-Read-Next` [:L341-L343] - one branch for
        # two codes, anomaly N-when31 - Class 4.
        if not aa040_process_read_next(file_access, sales, dal_common):
            # `aa040` fell off its end into `aa041-Reread` [:L429] - Class 2's mirror
            # image: no transfer, so the next paragraph simply runs.
            aa041_reread(file_access, sales, dal_common)
    elif function == FileFunction.READ_INDEXED:
        aa050_process_read_indexed(file_access, sales, dal_common)
    elif function == FileFunction.WRITE:
        aa070_process_write(file_access, sales, dal_common)
    elif function == FileFunction.RE_WRITE:
        aa090_process_rewrite(file_access, sales, dal_common)
    elif function == FileFunction.DELETE:
        aa080_process_delete(file_access, sales, dal_common)
    elif function == FileFunction.START:
        aa060_process_start(file_access, sales, dal_common)
    elif function not in _SUPPORTED_FUNCTION_CODES:
        aa100_bad_function(file_access, dal_common)
    else:  # pragma: no cover - guards the frozen `when` list against drift
        # A code that `SUPPORTED_FUNCTIONS` claims is handled but that no arm above
        # matched. Impossible while the two agree.
        transferred = False

    # `go to aa100-Bad-Function.` [:L358-L359] - Class 4, UNCONDITIONAL in the frozen
    # source and unreachable there for the reason above: every arm has already left the
    # program.
    if not transferred:
        _LOG.error(
            "acas012 reached the unconditional go to aa100-Bad-Function after "
            "the evaluate for File-Function %d - 'Should never get here but in "
            "case :(' [common/acas012.cbl:L358-L359]",
            function,
        )
        aa100_bad_function(file_access, dal_common)

    aa_main_exit()
    return _outcome_from_file_access(file_access)


FS_COBOL_FILES_USED: Final[int] = 0

#: :data:`SUPPORTED_FUNCTIONS` as plain ``int``, for the step-7 guard in
#: :func:`aa010_main`.
_SUPPORTED_FUNCTION_CODES: Final[frozenset[int]] = frozenset(
    int(code) for code in SUPPORTED_FUNCTIONS
)

#: The two ``File-Function`` codes that share ``aa040-Process-Read-Next``
#: [common/acas012.cbl:L341-L343] - anomaly N-when31. The bridge does NOT share them.
_AA040_SHARED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {int(FileFunction.READ_NEXT), int(FileFunction.READ_BY_NAME)}
)


def dispatch(
    system: SystemRecord,
    sales: WsSalesRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> CursorOutcome:
    """``Procedure Division Using ...`` [common/acas012.cbl:L276-L282].

    Note that the LINKAGE SECTION's ``copy`` order [:L264-L274] is different - ``wssl``,
    ``wssystem``, ``wsfnctn``, ``wsnames``, ``Test-Data-Flags`` - so a reader working
    from the copybook list would get the first two parameters the wrong way round.

    Args:
        system: ``System-Record``. Its ``RDBMS-Flat-Statuses`` chooses the half of the
            program that runs, and its six ``RDBMS-*`` fields supply the connection
            parameters.
        sales: ``WS-Sales-Record``. Read by write, re-write, delete and start; written
            by every read.
        file_access: ``File-Access``. Carries the request in (``File-Function``,
            ``Access-Type``, ``File-Key-No``) and the whole response out (``FS-Reply``,
            ``WE-Error``, ``Logging-Data``, ``RDB-Data``).
        file_defs: ``File-Defs``. Only the flat-file half consults it, for ``file-12``
            [copybooks/file12.cob].
        dal_common: ``ACAS-DAL-Common-data``. ``SW-Testing`` gates every log record and
            ``Log-File-Rec-Written`` counts them.

    Returns:
        A :class:`~acas_posting.dal.cursor_state.CursorOutcome` mirroring what was
            written into ``file_access``. Provided because a Python caller expects a
            return value.

    Raises:
        FlatFileStoreNotMigrated: Only from the flat-file half, and only when ``File-
            System-Used`` is 0. See :class:`FlatFileStoreNotMigrated`.
    """
    outcome = aa010_main(system, sales, file_access, file_defs, dal_common)
    aa_exit()
    return outcome


__all__ = (
    "dispatch",
    "sales_mt",
    "ENTITY_FACADE",
    "FILE_HANDLER",
    "BRIDGE_PROGRAM",
    "MYSQL_TABLE",
    "TABLE_NAME",
    "COPYBOOK_FILE",
    "COPYBOOK_RECORD",
    "HANDLER_PROG_NAME",
    "BRIDGE_DIRECTIVE_LOCATOR",
    "HOST_VARIABLE_GROUP",
    "HOST_VARIABLE_GROUP_LOCATOR",
    "LOG_SYSTEM",
    "LOG_FILE_NO_COBOL",
    "LOG_FILE_NO_RDB",
    "ENTRIES",
    "COLUMN_ORDER",
    "PRIMARY_KEY_COLUMN",
    "RECORD_ATTRIBUTE_FOR_COLUMN",
    "CHARACTER_COLUMNS",
    "SIGN_LOSS_COLUMNS",
    "MONEY_COLUMNS",
    "citations",
    "drift_report",
    "KEY_TABLE",
    "PRIMARY_KEY_OF_REFERENCE",
    "KEY_OFFSET",
    "KEY_LENGTH",
    "KEY_TYPE",
    "READ_BY_NAME_LOW_KEY",
    "READ_BY_NAME_LOW_KEY_TEXT",
    "SUPPORTED_FUNCTIONS",
    "GUARDED_KEY_FUNCTIONS",
    "ONLY_FILE_KEY_NO",
    "FACADE_VERBS",
    "WS_NO_PARAGRAPH_HANDLER",
    "WS_NO_PARAGRAPH_BRIDGE",
    "FS_COBOL_FILES_USED",
    "FS_REPLY_OPEN_INPUT_FAILED",
    "TESTING_1_VALUE",
    "COBOL_FILE_STATUS_EOF",
    "BridgeSession",
    "session",
    "reset_session",
    "BridgeWorkingStorage",
    "working_storage",
    "reset_working_storage",
    "HandlerWorkingStorage",
    "handler_storage",
    "reset_handler_storage",
    "HostVariables",
    "HOST_VARIABLE_NAMES",
    "FLAT_FILE_STORE_MIGRATED",
    "FlatFileStoreNotMigrated",
    "SPACE_FILLED_RECORD",
    "SPACE_FILLED_BINARY_BY_WIDTH",
    "BINARY_WIDTH_BY_DIGITS",
    "BINARY_WIDTH_BY_USAGE",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_reread",
    "aa045_eval_keys",
    "aa050_process_read_indexed",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_main_exit",
    "aa_exit",
    "ba_process_rdbms",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba_rdbms_exit",
    "ca_process_logs_acas012",
    "ba010_initialise",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba090_process_rewrite",
    "ba140_process_read_next",
    "ba141_reread",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba999_exit",
    "ca_process_logs",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
)
