r"""`acasirsub5` + `irsfinalMT` - the IRS Final-Accounts handler [`IRSFINAL-REC`].

The migration of the handler `common/acasirsub5.cbl` (534 lines) together with
its generated bridge `common/irsfinalMT.cbl` (727 lines), reimplemented as SQL
against the frozen three-column table `IRSFINAL-REC` [mysql/ACASDB.sql:L214].
Agent Action Plan section 0.4.1.5 names the pair and the target verbatim::

    | acas_posting/dal/acasirsub5_irs_final.py | CREATE |
    | common/acasirsub5.cbl + common/irsfinalMT.cbl | IRSFINAL-REC |

and section 0.2.1.1 gives the spine link: IRS final -> `acasirsub5` ->
`irsfinalMT` -> `IRSFINAL-REC` -> record copybook `copybooks/irswsfinal.cob`.
Section 0.3.1 states the boundary rule that puts a MODULE PER HANDLER rather
than per table here, verbatim: "Mirroring the handler boundary rather than the
table boundary keeps the Python module set in exact correspondence with the
COBOL programs that the traceability document must map, and preserves the
dispatch semantics rather than flattening them."

THREE THINGS TO KNOW BEFORE READING ANY CODE BELOW
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from acas_posting.dal.connection import (
    TransportSecurity,
    cobol_string_delimited_by_space,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1980_close,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    SEQUENTIAL_READ_START,
    CursorSlot,
    CursorState,
    CursorStateTable,
    DatabaseCursor,
    KeyOfReference,
    key_of_reference,
)
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    log_file_handler_record,
    mysql_1100_db_error,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.irs_final import Ar1View, Ar2View, IrsFinalRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

if TYPE_CHECKING:  # pragma: no cover - typing only, never a runtime dependency
    from mysql.connector.abstracts import MySQLConnectionAbstract


__all__: Final[tuple[str, ...]] = (
    "ARRAY_LENGTH",
    "BRIDGE_BAD_FUNCTION",
    "BRIDGE_DISPATCHED_FUNCTIONS",
    "COLUMNS",
    "DUP_KEY_SQLSTATE",
    "DUP_KEY_SQL_ERRORS",
    "FD_RECORD_BYTES",
    "FS_REPLY_DUPLICATE",
    "FS_REPLY_GENERAL",
    "HANDLER_BAD_FUNCTION",
    "HANDLER_DISPATCHED_FUNCTIONS",
    "KEY_COUNT",
    "PRIMARY_KEY",
    "PUBLISHED_FACADE_VERBS",
    "RECORD_SIZE_ERROR",
    "TABLE",
    "TRACE_DEAD_CLOSE",
    "TRACE_DEAD_OPEN",
    "TRACE_READ_NEXT",
    "TRACE_WRITE",
    "WE_ERROR_UNOBSERVABLE_REWRITE",
    "WS_LOG_FILE_NO_FLAT",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "WS_RECORD_BYTES",
    "acasirsub5_close",
    "acasirsub5_open",
    "acasirsub5_open_input",
    "acasirsub5_read_next",
    "acasirsub5_rewrite",
    "acasirsub5_write",
    "close",
    "dispatch",
    "insert_statement",
    "open_",
    "open_extend",
    "open_input",
    "open_output",
    "read_next",
    "reset",
    "rewrite",
    "select_statement",
    "select_where",
    "update_statement",
    "update_where",
    "write",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


TABLE: Final[str] = "IRSFINAL-REC"

#: `PRIMARY KEY (`IRS-FINAL-ACC-REC-KEY`)` [mysql/ACASDB.sql:L218]. THE COLUMN EXISTS IN
#: NO COPYBOOK - it is the `occurs` subscript, per the bridge's own `*> KEY = table
#: position` [common/irsfinalMT.cbl:L455].
PRIMARY_KEY: Final[str] = loader.table_for(TABLE).primary_key

KEY_COUNT: Final[int] = 1

#: The three columns in SCHEMA ORDINAL ORDER [mysql/ACASDB.sql:L215-L217], taken from
#: the generated dictionary rather than transcribed - which is what section 0.8.1's
#: "Data dictionary first" directive requires, and what catches the `IRS-` prefix the
#: bridge ADDS (anomaly A28) without anyone having to remember it.
COLUMNS: Final[tuple[str, ...]] = tuple(
    entry.column.name
    for entry in sorted(
        loader.entries_for_table(TABLE), key=lambda entry: entry.column.ordinal
    )
)

# THE RECORD LAYER'S OWN DESCRIPTORS - the ONLY source of widths and counts used here.
# The descriptor OBJECTS are consumed.

_AR1_DESCRIPTOR: Final = Ar1View.FIELDS[0]

_AR2_DESCRIPTOR: Final = Ar2View.FIELDS[0]

#: `03 ar3 pic x(5).` [copybooks/irswsfinal.cob:L68].
_AR3_DESCRIPTOR: Final = next(
    descriptor
    for descriptor in IrsFinalRecord.FIELDS
    if descriptor.name == "ar3"
)

#: `05 ar1 pic x(24) occurs 26.` [copybooks/irswsfinal.cob:L36] and `05 ar2 pic x occurs
#: 26.` [:L66]. ONE COBOL RECORD IS THIS MANY TABLE ROWS.
ARRAY_LENGTH: Final[int] = _AR1_DESCRIPTOR.occurs

WS_RECORD_BYTES: Final[int] = (
    _AR1_DESCRIPTOR.byte_length * _AR1_DESCRIPTOR.occurs
    + _AR2_DESCRIPTOR.byte_length * _AR2_DESCRIPTOR.occurs
    + _AR3_DESCRIPTOR.byte_length
)

#: `01 Record-5 pic x(655).` [common/acasirsub5.cbl:L104] - the flat, structureless FD
#: blob, and the `B` operand of the gate [:L372-L374].
FD_RECORD_BYTES: Final[int] = 655

if WS_RECORD_BYTES != FD_RECORD_BYTES:  # pragma: no cover - frozen sources agree
    # A CROSS-SOURCE CONSISTENCY CHECK ON FROZEN DECLARATIONS, not a validation of
    # accounting data - rule R-3 forbids the latter and says nothing about the former,
    # and section 0.4.1.6 asks the dictionary generator to do exactly this kind of
    # "present in one source and absent from another" flagging.
    raise ValueError(
        f"{TABLE}: [copybooks/irswsfinal.cob] sums to {WS_RECORD_BYTES} bytes "
        f"but [common/acasirsub5.cbl:L104] declares {FD_RECORD_BYTES}"
    )

WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.IRS

#: `move 14 to WS-Log-File-No` [common/acasirsub5.cbl:L159] - the flat-file identity,
#: and the ONLY UNCOLLIDED FILE NUMBER IN THE FOLDER.
WS_LOG_FILE_NO_FLAT: Final[int] = 14

#: `move 24 to WS-Log-File-no.
WS_LOG_FILE_NO_RDB: Final[int] = 24


TRACE_READ_NEXT: Final[int] = 203

TRACE_WRITE: Final[int] = 206

#: 201 and 202 survive ONLY inside the ~35 commented-out lines of `aa020-Process-
#: Open`/`aa030-Process-Close` [common/acasirsub5.cbl:L212-L246], so this handler uses
#: just TWO of the standard 201..208 band - the smallest set in the folder, matching
#: `acasirsub3`.
TRACE_DEAD_OPEN: Final[int] = 201
TRACE_DEAD_CLOSE: Final[int] = 202

_BRIDGE_TRACE_OPEN: Final[int] = 1
_BRIDGE_TRACE_CLOSE: Final[int] = 2
_BRIDGE_TRACE_SELECT: Final[int] = 3
_BRIDGE_TRACE_FETCH: Final[int] = 4
_BRIDGE_TRACE_INSERT: Final[int] = 10
_BRIDGE_TRACE_UPDATE: Final[int] = 17
_BRIDGE_TRACE_FREE: Final[int] = 20


DUP_KEY_SQL_ERRORS: Final[tuple[str, ...]] = ("1062", "1022")

DUP_KEY_SQLSTATE: Final[str] = "23000"

FS_REPLY_DUPLICATE: Final[FsReply] = FsReply.DUPLICATE_KEY

FS_REPLY_GENERAL: Final[FsReply] = FsReply.ERROR

#: `move 994 to WE-Error` [common/irsfinalMT.cbl:L563] - AND IT CAN NEVER BE SEEN.
WE_ERROR_UNOBSERVABLE_REWRITE: Final[int] = int(WeError.REWRITE_SQLSTATE_NOT_00000)

HANDLER_BAD_FUNCTION: Final[int] = int(WeError.NOT_USED)

#: `move 990 to WE-Error.` / `move 99 to Fs-Reply.` - the BRIDGE's bad-function pair
#: [common/irsfinalMT.cbl:L580-L581]. THE TWO DISAGREE, and the disagreement is not
#: reconciled.
BRIDGE_BAD_FUNCTION: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

RECORD_SIZE_ERROR: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)

HANDLER_DISPATCHED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,
    FileFunction.CLOSE,
    FileFunction.READ_NEXT,
    FileFunction.WRITE,
    FileFunction.RE_WRITE,
)

BRIDGE_DISPATCHED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    HANDLER_DISPATCHED_FUNCTIONS
)

PUBLISHED_FACADE_VERBS: Final[tuple[str, ...]] = (
    "acasirsub5-Open",
    "acasirsub5-Open-Input",
    "acasirsub5-Close",
    "acasirsub5-Read-Next",
    "acasirsub5-Write",
    "acasirsub5-ReWrite",
)


_AR1_WIDTH: Final[int] = _AR1_DESCRIPTOR.byte_length

_AR2_WIDTH: Final[int] = _AR2_DESCRIPTOR.byte_length

_AR3_WIDTH: Final[int] = _AR3_DESCRIPTOR.byte_length

#: What `initialize Final-Record with filler.` [common/irsfinalMT.cbl:L395] leaves in
#: each member.
_AR1_BLANK: Final[str] = " " * _AR1_WIDTH
_AR2_BLANK: Final[str] = " " * _AR2_WIDTH
_AR3_BLANK: Final[str] = " " * _AR3_WIDTH

if _AR2_DESCRIPTOR.occurs != ARRAY_LENGTH:  # pragma: no cover - frozen metadata
    # added validations of accounting data; this compares two FROZEN DECLARATIONS -
    # `occurs 26` at [copybooks/irswsfinal.cob:L36] and at [:L66] - against each other.
    raise ValueError(
        f"{TABLE}: the two occurs clauses of copybooks/irswsfinal.cob disagree "
        f"- ar1 declares {ARRAY_LENGTH} at L36 and ar2 declares "
        f"{_AR2_DESCRIPTOR.occurs} at L66; the bridge indexes both with one "
        f"subscript at [common/irsfinalMT.cbl:L455-L456]"
    )

if len(COLUMNS) != loader.table_for(TABLE).column_count:  # pragma: no cover
    raise ValueError(
        f"{TABLE}: the dictionary lists {len(COLUMNS)} column entries but "
        f"records a column count of {loader.table_for(TABLE).column_count} "
        f"from [mysql/ACASDB.sql:L214]"
    )


#: `01 DAL-Data.` with `05 MOST-Relation pic xxx.` and `05 Most-Cursor-Set pic 9 value
#: zero.` plus its two `88`-levels [common/irsfinalMT.cbl:L130-L134].
_CURSOR_STATES: Final[CursorStateTable] = CursorStateTable()

#: `03 ws-saved-fs-reply pic 99.` [common/irsfinalMT.cbl:L147]. ANOMALY A44 LIVES IN
#: THIS VARIABLE.
_WS_SAVED_FS_REPLY: int = 0

#: `77 A pic 9(4).` and `77 B pic 9(4).` [common/acasirsub5.cbl:L112-L115], whose own
#: comment reads `*> used in 1st test ONLY`, latched by `if A = zero` [:L368].
_RECORD_SIZE_A: int = 0
_RECORD_SIZE_B: int = 0


def reset(*, states: CursorStateTable | None = None) -> None:
    """Clear this module's persistent state, as a fresh run would find it.

    Two runs of one scenario inside ONE Python process must be independent - rule R-6
    requires them to be byte-identical - and any of the three surviving between them
    would let the second run inherit the first's state.

    Args:
        states: The cursor set to clear. The module's own set by default, which is the
            one every function here uses unless a caller supplies another.
    """
    global _WS_SAVED_FS_REPLY, _RECORD_SIZE_A, _RECORD_SIZE_B  # noqa: PLW0603
    (states if states is not None else _CURSOR_STATES).reset(TABLE)
    _WS_SAVED_FS_REPLY = 0
    _RECORD_SIZE_A = 0
    _RECORD_SIZE_B = 0


def _cursor_state(states: CursorStateTable | None) -> CursorState:
    """Resolve the `01 DAL-Data` block these verbs are to work through.

    Args:
        states: A caller-supplied cursor set, or ``None`` for the module's own.

    Returns:
        The one :class:`~acas_posting.dal.cursor_state.CursorState` for this table's
            single key of reference.
    """
    table = states if states is not None else _CURSOR_STATES
    return table.state_for(TABLE, CursorSlot.PRIMARY)


def select_where() -> str:
    """`ws-Where` for the sequential read [common/irsfinalMT.cbl:L335-L347].

    and its own echo comment [:L351] shows the intended result - though WITHOUT the
    backticks the code actually emits, which is a documentation/code mismatch worth
    noting rather than acting on.

    Returns:
        The predicate text, e.g. `` `IRS-FINAL-ACC-REC-KEY` > "000" ORDER BY `IRS-FINAL-
            ACC-REC-KEY` ASC ``.
    """
    key: KeyOfReference = key_of_reference(TABLE, 1)
    column = quote_identifier(cobol_string_delimited_by_space(key.key_name))
    start = SEQUENTIAL_READ_START[TABLE]
    relation = start.relation.token
    low_key = f'"{start.low_key}"'
    return f"{column} {relation} {low_key} ORDER BY {column} ASC"


def select_statement() -> str:
    """`SELECT * FROM ... WHERE ...` [common/irsfinalMT.cbl:L357-L362].

    NO `LIMIT` AND NO SECOND PREDICATE, because there is neither in the frozen text.

    Returns:
        The statement text, with no placeholder - the only value in it is the frozen
            low-key literal.
    """
    return f"SELECT * FROM {quote_identifier(TABLE)} WHERE {select_where()}"


def insert_statement() -> str:
    """`bb200-Insert` [common/irsfinalMT.cbl:L609-L657].

    ALL THREE COLUMNS ARE ALWAYS NAMED AND ALWAYS BOUND. None may be omitted and none
    may be `None`.

    Returns:
        The statement text with three placeholders, in schema ordinal order.
    """
    columns = ", ".join(f"{quote_identifier(name)}=%s" for name in COLUMNS)
    return f"INSERT INTO {quote_identifier(TABLE)} SET {columns}"


def update_where(ws_key: str) -> str:
    """`WS-Where` for the rewrite [common/irsfinalMT.cbl:L535-L546].

    `WS-Key` is `pic 99` [:L106], so `delimited by size` [:L542] emits it ZERO-PADDED -
    `"01"` through `"26"`. That is anomaly A36: the same key value reaches the `SET`
    clause UNPADDED, because there it comes through `TRIM(WS-MYSQL-EDIT(18:03))`.

    Args:
        ws_key: The `pic 99` rendering of the subscript, from :func:`_ws_key`.

    Returns:
        The predicate text, e.g. `` `IRS-FINAL-ACC-REC-KEY`="01" ``.
    """
    key: KeyOfReference = key_of_reference(TABLE, 1)
    column = quote_identifier(cobol_string_delimited_by_space(key.key_name))
    return f'{column}="{ws_key}"'


def update_statement() -> str:
    """`bb300-Update` [common/irsfinalMT.cbl:L662-L714].

    TWO ODDITIES, BOTH REPRODUCED. The `SET` clause INCLUDES THE PRIMARY KEY, so every
    row's key is updated to itself [:L677-L687]; and the key is rendered UNPADDED there
    and ZERO-PADDED in the `WHERE` - anomaly A36.

    Returns:
        The statement text with four placeholders: the three `SET` values in schema
            ordinal order, then the `WHERE` key.
    """
    columns = ", ".join(f"{quote_identifier(name)}=%s" for name in COLUMNS)
    key: KeyOfReference = key_of_reference(TABLE, 1)
    predicate = quote_identifier(cobol_string_delimited_by_space(key.key_name))
    return (
        f"UPDATE {quote_identifier(TABLE)} SET {columns} WHERE {predicate}=%s"
    )


def _ws_key(subscript: int) -> str:
    """`move A to WS-Key` where `WS-Key pic 99` [common/irsfinalMT.cbl:L106].

    Args:
        subscript: The 1-based `occurs` position, 1 through 26.

    Returns:
        The `pic 99` text, ``"01"`` through ``"26"``.
    """
    return f"{subscript:02d}"


def _insert_key_text(subscript: int) -> str:
    """`TRIM(WS-MYSQL-EDIT(18:03))` [common/irsfinalMT.cbl:L626-L628, :L679-L681].

    `WS-MYSQL-EDIT` is `PIC -Z(18)9.9(9)` [common/irsfinalMT.cbl:L105] - thirty
    characters: the sign
    at 1, eighteen zero-suppressed digit positions at 2 through 19, a mandatory
    digit at 20, the point at 21 and nine decimals at 22 through 30. The integer
    part is right-justified in 2..20, so positions 18, 19 and 20 hold the
    hundreds, tens and units. `FUNCTION TRIM` with no direction strips BOTH ends,
    so the Z-suppressed leading spaces vanish and the result is the plain,
    UNPADDED decimal of the subscript.

    Worked: 1 gives `"  1"` -> `"1"`; 10 gives `" 10"` -> `"10"`; 26 gives
    `" 26"` -> `"26"`. Three character positions is also the widest value this
    can carry, which matches `HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP` [:L172]
    and is far above the 26 the array can index.

    THE RESULT DIFFERS FROM :func:`_ws_key` FOR EVERY SUBSCRIPT BELOW TEN, and in
    the rewrite BOTH appear in the same statement - anomaly A36. The
    `tinyint(2) unsigned` column DOES hold what the `9(03)` host variable intended
    over the whole 1..26 domain - measured, ambiguity Q-16 resolved: `(2)` is a
    display width and the column holds 0..255.

    Args:
        subscript: The 1-based `occurs` position, 1 through 26.

    Returns:
        The trimmed edited text, ``"1"`` through ``"26"``.
    """
    return str(subscript)


def _trim_trailing(value: str) -> str:
    """`FUNCTION TRIM (<hv>, TRAILING)` [common/irsfinalMT.cbl:L638, :L647].

    TRAILING ONLY, so leading spaces are PRESERVED - a distinction that matters because
    `ar1` is a free-text 24-character slot and a caller may legitimately have indented
    its content.

    Args:
        value: The array entry, at its declared width.

    Returns:
        The entry with trailing spaces removed.
    """
    return value.rstrip(" ")


def _receive_alphanumeric(value: object, width: int) -> str:
    """Store a fetched column into a `pic x(n)` item, at that item's width.

    `move HV-IRS-AR1 to AR1 (HV-IRS-FINAL-ACC-REC-KEY)` [common/irsfinalMT.cbl:L455] is
    a same-width alphanumeric move in the frozen source, because the host variable and
    the array entry are both `x(24)`.

    Args:
        value: The column value as the pinned converter produced it.
        width: The receiving field's declared width, from its descriptor.

    Returns:
        Exactly ``width`` characters.
    """
    if value is None:
        text = ""
    elif isinstance(value, (bytes, bytearray)):
        text = bytes(value).decode("utf-8", errors="replace")
    else:
        text = str(value)
    return text[:width].ljust(width)


def _initialize_final_record(final: IrsFinalRecord) -> None:
    """`initialize Final-Record with filler.` [common/irsfinalMT.cbl:L395].

    The operand is THE WHOLE `01` GROUP, not one view, so every member is blanked: both
    `occurs` views, both enumerated groups, and `ar3`. `with filler` is what extends
    `initialize` to the two unnamed `redefines` groups [copybooks/irswsfinal.cob:L35,
    :L65].

    Args:
        final: The caller's `Final-Record`, mutated in place exactly as the COBOL
            mutates the linkage record.
    """
    final.ar1_view.ar1 = tuple(_AR1_BLANK for _ in range(ARRAY_LENGTH))
    final.ar2_view.ar2 = tuple(_AR2_BLANK for _ in range(ARRAY_LENGTH))
    for subscript in range(1, ARRAY_LENGTH + 1):
        # The enumerated fields occupy the SAME BYTES as the array views
        # [copybooks/irswsfinal.cob:L35-L36, :L65-L66], so `initialize` of the group
        # blanks them too.
        setattr(final.ar1_fields, f"ar1_{subscript}", _AR1_BLANK)
        setattr(final.ar2_fields, f"ar2_{subscript}", _AR2_BLANK)
    # `03 ar3 pic x(5).` [copybooks/irswsfinal.cob:L68] - blanked here and referenced
    # NOWHERE else in this module, because no column exists for it.
    final.ar3 = _AR3_BLANK


def _store_array_entry(final: IrsFinalRecord, key: int, ar1: str, ar2: str) -> None:
    """`move HV-IRS-AR1 to AR1 (key)` and its `ar2` twin [:L455-L456].

    ANOMALY A4 LIVES HERE: the subscript is THE DATABASE VALUE, not the loop counter.

    Args:
        final: The caller's `Final-Record`.
        key: The 1-based key value the row carried - NOT the loop counter.
        ar1: The `IRS-AR1` value, already at its receiving width.
        ar2: The `IRS-AR2` value, already at its receiving width.
    """
    index = key - 1
    entries_1 = list(final.ar1_view.ar1)
    entries_2 = list(final.ar2_view.ar2)
    entries_1[index] = ar1
    entries_2[index] = ar2
    final.ar1_view.ar1 = tuple(entries_1)
    final.ar2_view.ar2 = tuple(entries_2)
    setattr(final.ar1_fields, f"ar1_{key}", ar1)
    setattr(final.ar2_fields, f"ar2_{key}", ar2)


def _alias_enumerated_into_array(final: IrsFinalRecord) -> None:
    """Re-establish the `redefines` byte sharing before a host-variable load.

    * The ENUMERATED names are THE CALLER'S.

    Args:
        final: The caller's `Final-Record`, whose two views of each array are brought
            into the agreement the compiled program never has to arrange.
    """
    # A short view is fitted rather than rejected, so this helper cannot raise on a
    # record the caller built by hand.
    current_1 = (list(final.ar1_view.ar1) + [_AR1_BLANK] * ARRAY_LENGTH)[:ARRAY_LENGTH]
    current_2 = (list(final.ar2_view.ar2) + [_AR2_BLANK] * ARRAY_LENGTH)[:ARRAY_LENGTH]
    resolved_1: list[str] = []
    resolved_2: list[str] = []
    for subscript in range(1, ARRAY_LENGTH + 1):
        index = subscript - 1
        # `_receive_alphanumeric` is the module's own fit to a declared width, so a
        # caller's `ar1_1 = "Sales"` becomes the twenty-four bytes a COBOL `move` into
        # `pic x(24)` would have stored.
        enumerated_1 = _receive_alphanumeric(
            getattr(final.ar1_fields, f"ar1_{subscript}"), _AR1_WIDTH
        )
        enumerated_2 = _receive_alphanumeric(
            getattr(final.ar2_fields, f"ar2_{subscript}"), _AR2_WIDTH
        )
        resolved_1.append(
            enumerated_1 if enumerated_1 != _AR1_BLANK else current_1[index]
        )
        resolved_2.append(
            enumerated_2 if enumerated_2 != _AR2_BLANK else current_2[index]
        )
    final.ar1_view.ar1 = tuple(resolved_1)
    final.ar2_view.ar2 = tuple(resolved_2)
    for subscript in range(1, ARRAY_LENGTH + 1):
        setattr(final.ar1_fields, f"ar1_{subscript}", resolved_1[subscript - 1])
        setattr(final.ar2_fields, f"ar2_{subscript}", resolved_2[subscript - 1])


def _array_entry(final: IrsFinalRecord, subscript: int) -> tuple[str, str]:
    """`move AR1 (A) to HV-IRS-AR1` and its twin [:L484-L485, :L528-L529].

    THE ARRAY VIEWS ARE THE OPERANDS, and only they: the 52 enumerated names appear
    NOWHERE in `common/irsfinalMT.cbl`. In the compiled program that costs nothing,
    because `AR1 (A)` and `ar1-A` are one byte area [copybooks/irswsfinal.cob:L35-L36,
    :L65-L66].

    Args:
        final: The caller's `Final-Record`.
        subscript: The 1-based loop position, 1 through 26.

    Returns:
        The `(ar1, ar2)` pair at that position, untrimmed.
    """
    index = subscript - 1
    return final.ar1_view.ar1[index], final.ar2_view.ar2[index]


def _ba010_initialise(file_access: FileAccess) -> None:
    """`ba010-Initialise` [common/irsfinalMT.cbl:L222-L230].

    `We-Error` IS CLEARED AND `FS-Reply` IS NOT - so a caller's incoming `FS-Reply`
    survives into the verb, which is why the handler saves and restores the pair around
    its synthesised close rather than relying on the bridge.

    Args:
        file_access: The caller's block, mutated in place.
    """
    file_access.we_error = int(WeError.SUCCESS)
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    logging_data.ws_file_key = ""
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH


def _process_logs(
    dal_common: AcasDalCommonData, file_access: FileAccess, site: str
) -> None:
    """`perform Ca-Process-Logs` - as a log record, never as a `CALL`.

    Both `Ca-Process-Logs` paragraphs contain nothing but
    `call "fhlogger" using File-Access ACAS-DAL-Common-data`
    [common/acasirsub5.cbl:L528-L529, common/irsfinalMT.cbl:L722-L723], and
    `common/fhlogger.cbl` is out of scope per section 0.2.2, so rule R-1 forbids
    the call outright. The site therefore emits the record through
    :func:`acas_posting.dal.status.log_file_handler_record` - THE ONE ADAPTER every
    handler in this package shares, at one level, with one field set - and it changes
    no status, no control flow and no table.

    `WS-File-Key` is WITHHELD: on this table it is `IRS-FINAL-ACC-REC-KEY`, a
    business key, and the safe-event schema admits no record key (CWE-532). So are
    `WS-Log-Where` and `SQL-Msg`. The two testing switches are withheld too - they
    are configuration, not an event, and a record naming them said nothing an
    operator acts on. `Log-File-Rec-Written` IS now advanced, by one modulo a
    million, once per record.

    THIS FUNCTION IS THE BARE `perform`, WITH NO GATE, because the gate is not
    always there in the frozen source. EVERY ONE of the bridge's seven sites is
    wrapped in `if Testing-1` [common/irsfinalMT.cbl:L420-L422, :L430-L432,
    :L450-L452, :L457-L458, :L504-L505, :L566-L568, :L602-L604], and NOT ONE of
    the handler's seven is [common/acasirsub5.cbl:L428, :L436, :L445, :L452,
    :L456, :L478, :L502]. Use :func:`_process_logs_if_testing` for the former and
    this for the latter, so each call site says which the source said.

    ANOMALY A26: the handler's own paragraph is annotated
    `*> Not called on DAL access as it does it already` [common/acasirsub5.cbl:
    L525] and yet `ba015-Test-Ends` performs it SEVEN times, four of them in the
    read path alone.

    Args:
        dal_common: `ACAS-DAL-Common-data`, which the logger takes as its second
            argument [common/acasirsub5.cbl:L529] and reads `Testing-1` from.
        file_access: The block the logger would have read.
        site: Which frozen `perform` this is, for the log line.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program="irsfinalMT",
        paragraph=site,
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(file_access.file_function),
        access_type=int(file_access.access_type),
        fs_reply=int(file_access.fs_reply),
        we_error=int(file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=dal_common,
    )


def _process_logs_if_testing(
    dal_common: AcasDalCommonData, file_access: FileAccess, site: str
) -> None:
    """`if Testing-1 / perform Ca-Process-Logs / end-if` - the gated form.

    Args:
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` is `Testing-1`.
        file_access: The block the logger would have read.
        site: Which frozen `perform` this is, for the log line.
    """
    if dal_common.sw_testing == 1:
        _process_logs(dal_common, file_access, site)


def _column_names(cursor: DatabaseCursor) -> tuple[str, ...]:
    """The result's column names, from the cursor's own metadata.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The names in result order, or an empty tuple when the driver published no
            description.
    """
    description = cursor.description
    if not description:
        return ()
    return tuple(str(column[0]) for column in description)


def _fetch_one_row(cursor: DatabaseCursor) -> Mapping[str, object] | None:
    """`CALL "MySQL_fetch_record"` [common/irsfinalMT.cbl:L404-L411].

    The frozen call hands the three host variables straight back from the result row.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The next row, or ``None`` at `return-code = -1` [:L415].
    """
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row
    names = _column_names(cursor)
    if not names:
        return MappingProxyType({str(index): value for index, value in enumerate(row)})
    return MappingProxyType(dict(zip(names, row, strict=False)))


def _store_result(cursor: DatabaseCursor) -> tuple[Mapping[str, object], ...]:
    """`PERFORM MYSQL-1220-STORE-RESULT` [common/irsfinalMT.cbl:L364].

    Args:
        cursor: The cursor the `SELECT` was issued on.

    Returns:
        Every row, keyed by column name, in the order the single `ORDER BY` term
            returned them.
    """
    rows: list[Mapping[str, object]] = []
    while True:
        row = _fetch_one_row(cursor)
        if row is None:
            return tuple(rows)
        rows.append(row)


@dataclass(frozen=True, slots=True)
class _CommandOutcome:
    """What one `Mysql-1210-Command` leaves behind for its caller to read.

    Attributes:
        count_rows: `WS-MYSQL-Count-Rows` - `MySQL_affected_rows` for the two command
            paragraphs [copybooks/mysql-procedures.cpy:L178], or `MySQL_num_rows` over
            the stored result for the select [copybooks/mysql-procedures.cpy:L191-L192].
        status: What `Mysql-1100-Db-Error` produced, or ``None`` when the statement
            carried no driver failure.
        errno: `WS-MYSQL-Error-Number`, as `call "MySQL_errno"` would return it.
        message: `WS-MYSQL-Error-Message`, as `call "MySQL_error"` would.
        sql_state: `WS-MYSQL-SQLstate`, as `call "MySQL_sqlstate"` would.
    """

    count_rows: int
    status: DbErrorStatus | None
    errno: str
    message: str
    sql_state: str


def _apply_driver_status(file_access: FileAccess, status: DbErrorStatus) -> None:
    """Store what `Mysql-1100-Db-Error Thru Mysql-1190-Exit` moved into place.

    fs-Reply` then `go to Mysql-1190-Exit` [copybooks/mysql-procedures.cpy:L103-L104]
    jumps past `call "MySQL_error"` [:L107], past `call "MySQL_sqlstate"` and `move ...
    to SQL-State` [:L122-L123], and past `move 911 to We-Error` [:L128].

    Args:
        file_access: The caller's block, mutated in place.
        status: The paragraph's result.
    """
    file_access.fs_reply = int(status.fs_reply)
    file_access.we_error = int(status.we_error)
    logging_data = file_access.logging_data
    if status.sql_err:
        logging_data.sql_err = status.sql_err[:SQL_ERR_WIDTH].ljust(SQL_ERR_WIDTH)
    if status.sql_msg:
        logging_data.sql_msg = status.sql_msg[:SQL_MSG_WIDTH].ljust(SQL_MSG_WIDTH)
    if status.sql_state:
        logging_data.sql_state = status.sql_state[:SQL_STATE_WIDTH].ljust(
            SQL_STATE_WIDTH
        )


def _issue_command(
    connection: MySQLConnectionAbstract,
    statement: str,
    parameters: Sequence[object],
    *,
    we_error: int,
) -> _CommandOutcome:
    """`PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`.

    ANOMALY A39 - THERE IS NO RETRY AND THERE CAN BE NONE. The whole retry arm of that
    `if`, including `perform Mysql-1300-DB-Error`, the `WE-Error = 910` test and the `go
    to Mysql-1210-Command` re-issue, IS COMMENTED OUT [copybooks/mysql-
    procedures.cpy:L167-L175].

    Args:
        connection: A connection from `mysql_1000_open`.
        statement: One statement, identifiers already quoted, values as `%s`.
        parameters: The values to bind, in the statement's own order.
        we_error: The caller's `We-Error` as it stands NOW, so the duplicate arm can
            pass it straight through instead of zeroing it.

    Returns:
        The `WS-MYSQL-Count-Rows` reading, the driver paragraph's status, and the raw
            three fields the bridge's own `MySQL_errno` / `MySQL_error` /
            `MySQL_sqlstate` calls would have fetched.
    """
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = cursor.rowcount
    except Exception as error:  # noqa: BLE001 - any driver failure takes this arm
        errno, message, sql_state = _driver_failure_fields(error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            # The duplicate-key arm returns this untouched rather than 911
            # [copybooks/mysql-procedures.cpy:L99-L105 vs :L128].
            we_error=we_error,
        )
        #  NO SECOND RECORD HERE. `mysql_1100_db_error`, called on the line
        #  above, IS the one operator record for a database failure - it is the
        #  migration of `Mysql-1110-Report-Problem`
        #  [copybooks/mysql-procedures.cpy:L130-L137], which the frozen bridge reaches
        #  on every one - and it already carries the status pair, the SQLSTATE, the
        #  errno and the stable category. Repeating them made one failure two records,
        #  and this one also interpolated the driver's message, which for this table
        #  renders the statement and its bound key (CWE-532); `redact_for_log` escaped
        #  it and removed none of it. `message` is still RETURNED, because `SQL-Msg` is
        #  a status field the paragraphs read.
        # A40: affected rows is still read, and a failed statement affected none.
        return _CommandOutcome(
            count_rows=0,
            status=status,
            errno=errno,
            message=message,
            sql_state=sql_state,
        )
    return _CommandOutcome(
        count_rows=0 if affected is None or affected < 0 else int(affected),
        status=None,
        errno="",
        message="",
        sql_state="",
    )


def _driver_failure_fields(error: BaseException) -> tuple[str, str, str]:
    """Split a driver exception into the three values the frozen calls fetch.

    `call "MySQL_errno"`, `call "MySQL_error"` and `call "MySQL_sqlstate"` fetch a
    number, a message and a five-character SQLSTATE [common/irsfinalMT.cbl:L438-L448,
    :L488-L494, :L555-L561].

    Args:
        error: The exception the driver raised.

    Returns:
        `(errno, message, sqlstate)`, each already a string.
    """
    errno = getattr(error, "errno", None)
    sql_state = getattr(error, "sqlstate", None)
    message = getattr(error, "msg", None)
    return (
        "" if errno is None else str(errno),
        str(error) if message is None else str(message),
        "" if sql_state is None else str(sql_state),
    )


def _issue_select(
    connection: MySQLConnectionAbstract,
    statement: str,
    state: CursorState,
    *,
    we_error: int,
) -> _CommandOutcome:
    """The select pair: `MYSQL-1210-COMMAND` then `MYSQL-1220-STORE-RESULT`.

    THE COUNT COMES FROM `MySQL_num_rows`, NOT FROM AFFECTED ROWS. `Mysql-1220-Store-
    Result` materialises the whole result on the client and then overwrites `WS-MYSQL-
    Count-Rows` with its size [copybooks/mysql-procedures.cpy:L187-L192], so the
    affected-rows reading the command paragraph left there [:L178] is discarded.

    Args:
        connection: A connection from `mysql_1000_open`.
        statement: The select, with the frozen low-key literal already in it.
        state: The cursor state that will hold the materialised result.
        we_error: The caller's `We-Error` as it stands now.

    Returns:
        The stored-result count and, on a driver failure, everything the bridge's own
            re-fetch would have read.
    """
    try:
        with execute_statement(connection, statement, ()) as cursor:
            rows = _store_result(cursor)
    except Exception as error:  # noqa: BLE001 - any driver failure takes this arm
        errno, message, sql_state = _driver_failure_fields(error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            # The duplicate-key arm returns this untouched rather than 911
            # [copybooks/mysql-procedures.cpy:L99-L105 vs :L128].
            we_error=we_error,
        )
        state.store_result(())
        #  NO SECOND RECORD HERE, for the reason the command path gives above:
        #  `mysql_1100_db_error` has already emitted the one operator record, and the
        #  driver's message is not safe to log.
        return _CommandOutcome(
            count_rows=0,
            status=status,
            errno=errno,
            message=message,
            sql_state=sql_state,
        )
    return _CommandOutcome(
        count_rows=state.store_result(rows),
        status=None,
        errno="",
        message="",
        sql_state="",
    )


def read_next(
    connection: MySQLConnectionAbstract,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
    *,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`ba040-Process-Read-Next` [common/irsfinalMT.cbl:L317-L466].

    THE RETURNED STATUS IS ALMOST ALWAYS `(0, 0)`, AND THAT IS THE POINT. [:L465] is
    `move zero to fs-reply WE-Error.` with NO GUARD (anomaly A32), and it sits after the
    loop on the path every in-loop exit takes. So.

    Args:
        connection: A connection the caller has already opened, because the frozen
            bridge holds it in working storage across its three calls.
        file_access: `File-Access` [common/irsfinalMT.cbl:L207], mutated in place.
        dal_common: `ACAS-DAL-Common-data` [:L208]; `sw_testing` gates logging.
        final: `Final-Record` [:L209] - blanked, then filled by key.
        states: The cursor-state table to use. Defaults to this module's own, which
            keeps `read_next` deterministic across runs.

    Returns:
        The `(FS-Reply, We-Error)` pair as it stands at `ba999-exit`.
    """
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data
    state = _cursor_state(states)

    if state.cursor_not_active():
        key: KeyOfReference = key_of_reference(TABLE, 1)
        # `move KOR-offset (KOR-x1) to K` / `move KOR-length (KOR-x1) to L` [:L330-L331]
        # - ANOMALY A23: both are moved and then NEVER READ.
        _dead_kor_offset, _dead_kor_length = key.kor_offset, key.kor_length
        logging_data.ws_log_where = select_where()
        logging_data.ws_no_paragraph = _BRIDGE_TRACE_SELECT
        outcome = _issue_select(
            connection, select_statement(), state, we_error=file_access.we_error
        )
        if outcome.status is not None:
            _apply_driver_status(file_access, outcome.status)
        logging_data.ws_file_key = "000"
        if outcome.count_rows == 0:
            return _ba040_no_data(file_access, dal_common, state, outcome)
        state.set_cursor_active()

    logging_data.ws_log_where = ""
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_FETCH
    # `initialize Final-Record with filler.` [:L395] - the WHOLE group, `ar3` included,
    # and outside the cursor guard (A37).
    _initialize_final_record(final)

    # `perform varying A from 1 by 1 until A > 26` [:L396-L397].
    for subscript in range(1, ARRAY_LENGTH + 1):
        row = state.fetch_record()

        # `if return-code = -1 or A > 26 or = zero` [:L415-L416]. ANOMALY A42: inside a
        # 1..26 loop the second and third disjuncts are unreachable.
        if row is None or subscript > ARRAY_LENGTH or subscript == 0:
            # `move 10 to fs-Reply WE-Error` [:L417] - one statement, both fields, which
            # is what `end_of_file_status` exists to reproduce.
            fs_reply, we_error = end_of_file_status()
            file_access.fs_reply = int(fs_reply)
            file_access.we_error = we_error
            logging_data.ws_file_key = "EOF"
            state.set_cursor_not_active()
            # [:L420-L422] `if Testing-1 perform Ca-Process-Logs` - "do for each row".
            # This log record is the only place the `(10, 10)` survives, because [:L465]
            # erases it.
            _process_logs_if_testing(dal_common, file_access, "ba040/EOF")
            break

        key_value = _read_key(row)

        # `if HV-IRS-FINAL-ACC-REC-KEY = zero or > 26` [:L426].
        if key_value == 0 or key_value > ARRAY_LENGTH:
            logging_data.ws_file_key = "EOF3"
            # `move HV-IRS-FINAL-ACC-REC-KEY to WE-Error` [:L428] - ANOMALY A5: THE
            # OFFENDING KEY VALUE BECOMES THE ERROR CODE, and `FS-Reply` is NOT set.
            file_access.we_error = key_value
            state.set_cursor_not_active()
            _process_logs_if_testing(dal_common, file_access, "ba040/EOF3")
            break

        logging_data.ws_file_key = _insert_key_text(key_value)

        # `if WS-MYSQL-Count-Rows = zero` [:L437]. ANOMALY A43.
        if state.count_rows == 0:
            if _errno_is_set(outcome_errno := _last_errno(file_access)):
                fs_reply, we_error = end_of_file_status()
                file_access.fs_reply = int(fs_reply)
                file_access.we_error = we_error
                logging_data.sql_err = outcome_errno[:SQL_ERR_WIDTH].ljust(
                    SQL_ERR_WIDTH
                )
                logging_data.ws_file_key = "EOF2"
            # `call "MySQL_sqlstate"` then `move ... to SQL-State` [:L447-L448] -
            # OUTSIDE the errno arm, so the SQLSTATE is stored either way.
            state.set_cursor_not_active()
            _process_logs_if_testing(dal_common, file_access, "ba040/EOF2")
            break

        _store_array_entry(
            final,
            key_value,
            _receive_alphanumeric(row.get(COLUMNS[1]), _AR1_WIDTH),
            _receive_alphanumeric(row.get(COLUMNS[2]), _AR2_WIDTH),
        )

        # [:L457-L461] `if Testing-1 / perform Ca-Process-Logs / move zeros to FS-Reply
        # SQL-Err / move spaces to SQL-Msg`. ANOMALY A33.
        if dal_common.sw_testing == 1:
            _process_logs(dal_common, file_access, "ba040/row")
            file_access.fs_reply = int(FsReply.SUCCESS)
            logging_data.sql_err = "0" * SQL_ERR_WIDTH
            logging_data.sql_msg = " " * SQL_MSG_WIDTH

    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    return FsReply.SUCCESS, int(WeError.SUCCESS)


def _ba040_no_data(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    state: CursorState,
    outcome: _CommandOutcome,
) -> tuple[FsReply, int]:
    """The empty-table arm of the read [common/irsfinalMT.cbl:L374-L387].

    THIS IS THE ONLY FAILURE A CALLER OF THE READ CAN SEE. `go to ba998-Free` leaves by
    way of `ba998-Free` [:L588-L598] and `ba999-end` [:L600], so the unconditional reset
    at [:L465] is never executed and the `(10, 10)` survives.

    Args:
        file_access: The caller's block, mutated in place.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.
        state: The cursor state, freed here.
        outcome: What the select left in the `WS-MYSQL-*` fields.

    Returns:
        `(10, 10)` - the end-of-file pair, unerased.
    """
    logging_data = file_access.logging_data
    # `call "MySQL_errno"` [:L375] then `if ... not = "0 "` [:L376]. ANOMALY A20.
    if _errno_is_set(outcome.errno):
        logging_data.sql_err = outcome.errno[:SQL_ERR_WIDTH].ljust(SQL_ERR_WIDTH)
        logging_data.sql_msg = outcome.message[:SQL_MSG_WIDTH].ljust(SQL_MSG_WIDTH)
    logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
        SQL_STATE_WIDTH
    )
    # `move 10 to fs-reply` [:L383] and `move 10 to WE-Error` [:L384] - TWO separate
    # statements here where [:L417] uses one. ANOMALY A35.
    fs_reply, we_error = end_of_file_status()
    file_access.fs_reply = int(fs_reply)
    file_access.we_error = we_error
    logging_data.ws_file_key = "No Data"
    _ba998_free(file_access, dal_common, state)
    return fs_reply, we_error


def _ba998_free(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    state: CursorState,
) -> None:
    """`ba998-Free` and the fall-through into `ba999-end` [:L588-L604].

    Reached only by `go to ba998-Free`, which in this bridge means only the empty-table
    arm of the read. The three fan-out verbs all leave by `go to ba999-exit` instead and
    so skip the log below - anomaly A38.

    Args:
        file_access: The caller's block; only `ws_no_paragraph` changes.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.
        state: The cursor state to free.
    """
    file_access.logging_data.ws_no_paragraph = _BRIDGE_TRACE_FREE
    state.free()
    _process_logs_if_testing(dal_common, file_access, "ba999-end")


def _errno_is_set(errno: str) -> bool:
    """`if WS-MYSQL-Error-Number not = "0 "` - on the trimmed value.

    ANOMALY A20: the frozen source spells the literal with THREE trailing spaces at
    [common/irsfinalMT.cbl:L376] and [:L491] and with FOUR at [:L558].

    Args:
        errno: The `MySQL_errno` reading.

    Returns:
        Whether the errno arm is taken.
    """
    trimmed = errno.strip()
    return bool(trimmed.lstrip("0"))


def _last_errno(file_access: FileAccess) -> str:
    """`call "MySQL_errno" using WS-MYSQL-Error-Number` [:L438].

    The in-loop count-zero arm re-fetches the errno, and since no statement has been
    issued since the select, the value it gets is the select's.

    Args:
        file_access: The caller's block.

    Returns:
        The errno as `SQL-Err` currently holds it, trimmed of its padding.
    """
    return file_access.logging_data.sql_err.strip()


def _read_key(row: Mapping[str, object]) -> int:
    """The `HV-IRS-FINAL-ACC-REC-KEY` a fetched row carries [:L406].

    BINARY item, so it is a Python `int` and never a `Decimal` - there is no scale to
    preserve and rule R-2 forbids a float.

    Args:
        row: One fetched row, keyed by column name.

    Returns:
        The key value as the host variable would hold it.
    """
    value = row.get(COLUMNS[0])
    if isinstance(value, int):
        return value
    if value is None:
        # `initialize`d host variables read zero; the guard at [:L426] then takes the `=
        # zero` arm, which is exactly what the frozen code would do.
        return 0
    return int(str(value).strip() or "0")


def write(
    connection: MySQLConnectionAbstract,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
) -> tuple[FsReply, int]:
    """`ba070-Process-Write` [common/irsfinalMT.cbl:L468-L517].

    so ALL 26 ROWS ARE ALWAYS WRITTEN, blank ones included, and this table is DENSE
    after any write - anomaly A7. A scenario diff that expects only the populated rows
    will fail, and correctly so.

    Args:
        connection: A connection the caller has already opened.
        file_access: `File-Access` [:L207], mutated in place.
        dal_common: `ACAS-DAL-Common-data` [:L208]; `sw_testing` gates logging.
        final: `Final-Record` [:L209] - read through its `occurs` views.

    Returns:
        The `(FS-Reply, We-Error)` pair as it stands at `ba999-Exit`.
    """
    global _WS_SAVED_FS_REPLY  # noqa: PLW0603 - A44: the frozen field is program state
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data

    # `move zero to WS-Mysql-Time-Step WS-SQL-Retry.` [:L469-L470] - ANOMALY A39.

    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0" * SQL_ERR_WIDTH
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_INSERT

    statement = insert_statement()
    _alias_enumerated_into_array(final)
    for subscript in range(1, ARRAY_LENGTH + 1):
        # [:L477-L480] The blank-slot skip, COMMENTED OUT - anomaly A7. Nothing is
        # skipped and nothing may be.
        key_text = _insert_key_text(subscript)
        ws_key = _ws_key(subscript)
        logging_data.ws_file_key = ws_key
        # `move AR1 (A) to HV-IRS-AR1` / `move AR2 (A) to HV-IRS-AR2` [:L484-L485] - THE
        # `occurs` VIEWS, indexed by the LOOP COUNTER here, unlike the read which
        # indexes by the returned key (anomaly A4).
        ar1, ar2 = _array_entry(final, subscript)
        outcome = _issue_command(
            connection,
            statement,
            # `TRIM(HV-IRS-AR1,TRAILING)` and its twin [:L638, :L647]: trailing only, so
            # leading spaces survive and an all-spaces slot becomes the empty string -
            # never `None`.
            (key_text, _trim_trailing(ar1), _trim_trailing(ar2)),
            we_error=file_access.we_error,
        )
        if outcome.status is not None:
            _apply_driver_status(file_access, outcome.status)

        if outcome.count_rows != 1:
            # `call "MySQL_errno"` [:L488], then `call "MySQL_sqlstate"` and `move WS-
            # MYSQL-SqlState to SQL-State` [:L489-L490] - the SQLSTATE store is
            # UNCONDITIONAL inside this arm, BEFORE the errno test.
            logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
                SQL_STATE_WIDTH
            )
            # `if WS-MYSQL-Error-Number not = "0 " *> 14/12/16` [:L491] - THREE trailing
            # spaces here, FOUR in the rewrite [:L558]. Anomaly A20.
            if _errno_is_set(outcome.errno):
                logging_data.sql_err = outcome.errno[:SQL_ERR_WIDTH].ljust(
                    SQL_ERR_WIDTH
                )
                logging_data.sql_msg = outcome.message[:SQL_MSG_WIDTH].ljust(
                    SQL_MSG_WIDTH
                )
                if is_duplicate_key_bridge_level(
                    logging_data.sql_err, logging_data.sql_state
                ):
                    file_access.fs_reply = int(FS_REPLY_DUPLICATE)
                else:
                    file_access.fs_reply = int(FS_REPLY_GENERAL)

        if dal_common.sw_testing == 1:
            _process_logs(dal_common, file_access, "ba070/row")
            # [:L506-L507] `*> move zeros to FS-Reply SQL-Err` and `*> move spaces to
            # SQL-Msg` - ANOMALY A31.

        # `if fs-reply not = zero` [:L509] - THE SQUASH, anomaly A6.
        if file_access.fs_reply != int(FsReply.SUCCESS):
            _WS_SAVED_FS_REPLY = file_access.fs_reply
            file_access.fs_reply = int(FsReply.SUCCESS)

    # `if ws-saved-fs-reply not = zero *> restore last error` [:L514-L515]. A44.
    if _WS_SAVED_FS_REPLY != int(FsReply.SUCCESS):
        file_access.fs_reply = _WS_SAVED_FS_REPLY

    # `go to ba999-Exit.` [:L517] - jumping past `ba999-end`'s own logging hook
    # [:L600-L604], anomaly A38.
    return FsReply(file_access.fs_reply), file_access.we_error


def rewrite(
    connection: MySQLConnectionAbstract,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
) -> tuple[FsReply, int]:
    """`ba090-Process-Rewrite` [common/irsfinalMT.cbl:L519-L574].

    So the `move 99 to fs-reply` at [:L562] and the `move 994 to WE-Error` at [:L563]
    are set and then ERASED, on every iteration and finally after the loop.

    Args:
        connection: A connection the caller has already opened.
        file_access: `File-Access` [:L207], mutated in place.
        dal_common: `ACAS-DAL-Common-data` [:L208]; `sw_testing` gates logging.
        final: `Final-Record` [:L209] - read through its `occurs` views.

    Returns:
        Always `(0, 0)`. See above; this is not an oversight in the translation.
    """
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data

    # `move zero to WS-Mysql-Time-Step WS-SQL-Retry.` [:L521-L522] - anomaly A39 again;
    # the ladder is unreachable, so this is modelled as nothing.
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_UPDATE

    statement = update_statement()
    _alias_enumerated_into_array(final)
    for subscript in range(1, ARRAY_LENGTH + 1):
        ws_key = _ws_key(subscript)
        # `move WS-Key to WS-File-Key HV-IRS-FINAL-ACC-REC-KEY` [:L526-L527] - ONE move,
        # TWO receivers, and the second of them is then rendered UNPADDED by
        # `bb300-Update`'s edited slice [:L679-L681] while the `WHERE` below renders
        # `WS-Key` ZERO-PADDED.
        logging_data.ws_file_key = ws_key
        key_text = _insert_key_text(subscript)
        ar1, ar2 = _array_entry(final, subscript)

        key: KeyOfReference = key_of_reference(TABLE, 1)
        # `move KOR-offset (KOR-x1) to K` / `move KOR-length (KOR-x1) to L` [:L532-L533]
        # - ANOMALY A23, moved and never read.
        _dead_kor_offset, _dead_kor_length = key.kor_offset, key.kor_length
        # `move WS-Where (1:J) to WS-Log-Where *> For test logging` [:L547].
        logging_data.ws_log_where = update_where(ws_key)

        outcome = _issue_command(
            connection,
            statement,
            (key_text, _trim_trailing(ar1), _trim_trailing(ar2), ws_key),
            # As in the write loop.
            we_error=file_access.we_error,
        )
        if outcome.status is not None:
            _apply_driver_status(file_access, outcome.status)

        # [:L550-L552] `if Testing-2 / display Display-Message-1 with erase eos` -
        # ANOMALY A21: `Testing-2` where every other test in both files uses
        # `Testing-1`.

        if outcome.count_rows != 1:
            logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
                SQL_STATE_WIDTH
            )
            # `if WS-MYSQL-Error-Number not = "0 "` [:L558] - FOUR trailing spaces,
            # against THREE in the write [:L491]. Anomaly A20.
            if _errno_is_set(outcome.errno):
                # `call "MySQL_error"` [:L559], `move ... to SQL-Err` [:L560], `move ...
                # to SQL-Msg` [:L561]. NOTE.
                logging_data.sql_err = outcome.errno[:SQL_ERR_WIDTH].ljust(
                    SQL_ERR_WIDTH
                )
                logging_data.sql_msg = outcome.message[:SQL_MSG_WIDTH].ljust(
                    SQL_MSG_WIDTH
                )
                # `move 99 to fs-reply` [:L562] and `move 994 to WE-Error` [:L563]. BOTH
                # ARE ERASED BELOW.
                file_access.fs_reply = int(FS_REPLY_GENERAL)
                file_access.we_error = WE_ERROR_UNOBSERVABLE_REWRITE

        if dal_common.sw_testing == 1:
            _process_logs(dal_common, file_access, "ba090/row")

    # three statements and none may be added.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0" * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    # `go to ba999-exit.` [:L574] - past `ba999-end`'s log, anomaly A38.
    return FsReply.SUCCESS, int(WeError.SUCCESS)


_CONNECTION: MySQLConnectionAbstract | None = None


def _ba020_process_open(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`ba020-Process-Open` [common/irsfinalMT.cbl:L254-L300].

    `move zero to Most-Cursor-Set` [:L299] IS WHY THE HANDLER'S TRIPLE HIDES ANOMALY
    A37: every synthesised open resets the cursor, so the stale-cursor path is reachable
    only by calling the published read verb twice.

    Args:
        system: `System-Record`, from which the credentials resolve.
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`, unused by the frozen paragraph and carried
            only so the caller's argument list stays uniform.
        transport: The transport policy `dal/connection.py` requires.
        states: The cursor set whose `Most-Cursor-Set` [:L299] this open clears.

    Returns:
        The `(FS-Reply, We-Error)` pair this paragraph leaves behind.
    """
    global _CONNECTION  # noqa: PLW0603 - the bridge holds this in working storage
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_OPEN
    outcome = mysql_1000_open(
        system,
        ws_no_paragraph=_BRIDGE_TRACE_OPEN,
        we_error=file_access.we_error,
        transport=transport,
    )
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    if outcome.sql_err:
        logging_data.sql_err = outcome.sql_err[:SQL_ERR_WIDTH].ljust(SQL_ERR_WIDTH)
    if outcome.sql_msg:
        logging_data.sql_msg = outcome.sql_msg[:SQL_MSG_WIDTH].ljust(SQL_MSG_WIDTH)
    if outcome.sql_state:
        logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
            SQL_STATE_WIDTH
        )
    if file_access.fs_reply != int(FsReply.SUCCESS):
        _CONNECTION = None
        _process_logs_if_testing(dal_common, file_access, "ba999-end/open-failed")
        return FsReply(file_access.fs_reply), file_access.we_error
    _CONNECTION = outcome.connection
    logging_data.ws_file_key = "OPEN IRS FINAL"
    # `move zero to Most-Cursor-Set` [:L299] - on THE CALLER'S cursor set, not
    # unconditionally on this module's own, so a caller working through its own set gets
    # the reset the frozen program gives it.
    _cursor_state(states).set_cursor_not_active()
    _process_logs_if_testing(dal_common, file_access, "ba999-end/open")
    return FsReply.SUCCESS, int(WeError.SUCCESS)


def _ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`ba030-Process-Close` [common/irsfinalMT.cbl:L302-L315].

    NO COMMIT PRECEDES IT, and none is added: `dal/connection.py` records that a commit
    here would suppress the partial state section 0.6.5 requires.

    Args:
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.
        states: The cursor set to free from.

    Returns:
        `(0, 0)` - this paragraph sets no status of its own.
    """
    global _CONNECTION  # noqa: PLW0603 - the bridge holds this in working storage
    _ba010_initialise(file_access)
    state = _cursor_state(states)
    if state.cursor_active():
        _ba998_free(file_access, dal_common, state)
    file_access.logging_data.ws_no_paragraph = _BRIDGE_TRACE_CLOSE
    file_access.logging_data.ws_file_key = "CLOSE IRS FINAL"
    mysql_1980_close(_CONNECTION)
    _CONNECTION = None
    _process_logs_if_testing(dal_common, file_access, "ba999-end/close")
    return FsReply(file_access.fs_reply), file_access.we_error


def _ba100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> tuple[FsReply, int]:
    """`ba100-Bad-Function` [common/irsfinalMT.cbl:L576-L582].

    [common/acasirsub5.cbl:L331-L332, :L508-L509]. Four handler/bridge pairs in this
    folder disagree the same way - `acas029`/`otm5MT`, `acasirsub3`/`irsdfltMT`,
    `acasirsub4`/`irspostingMT` and this one - so it is a folder-wide pattern rather
    than a local slip, and neither side is reconciled to the other.

    Args:
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.

    Returns:
        `(99, 990)`.
    """
    file_access.we_error = BRIDGE_BAD_FUNCTION
    file_access.fs_reply = int(FS_REPLY_GENERAL)
    # `go to ba999-end.` [:L582] - unlike the three fan-out verbs, this one DOES reach
    # the end-of-call log (anomaly A38 is about the verbs, not this).
    _process_logs_if_testing(dal_common, file_access, "ba999-end/bad-function")
    return FS_REPLY_GENERAL, BRIDGE_BAD_FUNCTION


def _ba020_call_dal(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`ba020-Call-DAL` [common/acasirsub5.cbl:L512-L517] and the bridge's dispatch
    [common/irsfinalMT.cbl:L239-L252].

    THREE OF THE HANDLER'S FIVE PARAMETERS CROSS, with a blank line before the third
    [:L515] - the family's layout habit. `System-Record` and `File-Defs` do NOT cross.

    Args:
        system: `System-Record` - not passed to the bridge, but needed by the open arm
            because that is where `dal/connection.py` reads the credentials the frozen
            bridge reads from `RDB-Data`.
        file_access: `File-Access` [common/irsfinalMT.cbl:L207].
        dal_common: `ACAS-DAL-Common-data` [:L208].
        final: `Final-Record` [:L209].
        transport: The transport policy for the open arm.
        states: The cursor set the read arm works through.

    Returns:
        The `(FS-Reply, We-Error)` pair the bridge leaves behind.
    """
    function = file_access.file_function
    if function == int(FileFunction.OPEN):
        return _ba020_process_open(
            system, file_access, dal_common, transport=transport, states=states
        )
    if function == int(FileFunction.CLOSE):
        return _ba030_process_close(file_access, dal_common, states=states)
    if function == int(FileFunction.READ_NEXT):
        return _bridge_read_next(file_access, dal_common, final, states=states)
    if function == int(FileFunction.WRITE):
        return _bridge_write(file_access, dal_common, final)
    if function == int(FileFunction.RE_WRITE):
        return _bridge_rewrite(file_access, dal_common, final)
    return _ba100_bad_function(file_access, dal_common)


def _require_connection(file_access: FileAccess) -> MySQLConnectionAbstract:
    """The connection the bridge's working storage is holding.

    `ba040`, `ba070` and `ba090` all issue statements on the handle `ba020-Process-Open`
    established, and the frozen program simply uses it: if no open preceded,
    `MySQL_query` is called on a null handle.

    Args:
        file_access: The caller's block, named in the message so the failing operation
            is identifiable.

    Returns:
        The open connection.

    Raises:
        RuntimeError: If no open preceded this verb.
    """
    if _CONNECTION is None:
        raise RuntimeError(
            f"{TABLE}: file-function {file_access.file_function} was reached with "
            "no connection open; ba020-Process-Open "
            "[common/irsfinalMT.cbl:L254-L300] must run first"
        )
    return _CONNECTION


def _bridge_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
    *,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`when 3 / go to ba040-Process-Read-Next` [common/irsfinalMT.cbl:L244-L245].

    Args:
        file_access: `File-Access`.
        dal_common: `ACAS-DAL-Common-data`.
        final: `Final-Record`.
        states: The cursor set to work through.

    Returns:
        What :func:`read_next` returns.
    """
    return read_next(
        _require_connection(file_access), file_access, dal_common, final, states=states
    )


def _bridge_write(
    file_access: FileAccess, dal_common: AcasDalCommonData, final: IrsFinalRecord
) -> tuple[FsReply, int]:
    """`when 5 / go to ba070-Process-Write` [common/irsfinalMT.cbl:L246-L247].

    Args:
        file_access: `File-Access`.
        dal_common: `ACAS-DAL-Common-data`.
        final: `Final-Record`.

    Returns:
        What :func:`write` returns.
    """
    return write(_require_connection(file_access), file_access, dal_common, final)


def _bridge_rewrite(
    file_access: FileAccess, dal_common: AcasDalCommonData, final: IrsFinalRecord
) -> tuple[FsReply, int]:
    """`when 7 / go to ba090-Process-Rewrite` [common/irsfinalMT.cbl:L248-L249].

    Args:
        file_access: `File-Access`.
        dal_common: `ACAS-DAL-Common-data`.
        final: `Final-Record`.

    Returns:
        What :func:`rewrite` returns - always `(0, 0)`, per anomaly A1.
    """
    return rewrite(_require_connection(file_access), file_access, dal_common, final)


def _record_size_gate(
    system: SystemRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> tuple[FsReply, int] | None:
    """`ba012-Test-WS-Rec-Size-2` [common/acasirsub5.cbl:L366-L406].

    A ONCE-ONLY LATCH, and its own comment says so: `*> Test on very first call only (So
    do NOT use var A & B again)` [:L360], with `77 A pic 9(4) value zero.

    Args:
        system: `System-Record`, the source of the six credential fields.
        file_access: `File-Access`; `RDB-Data` is populated here.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log at
            [common/acasirsub5.cbl:L389-L391].

    Returns:
        ``None`` when the gate passes - the caller continues to `ba015-Test-Ends`.
    """
    global _RECORD_SIZE_A, _RECORD_SIZE_B  # noqa: PLW0603 - frozen `77` latch
    if _RECORD_SIZE_A != 0:
        return None

    _RECORD_SIZE_A = WS_RECORD_BYTES
    _RECORD_SIZE_B = FD_RECORD_BYTES

    if _RECORD_SIZE_A < _RECORD_SIZE_B:
        file_access.we_error = RECORD_SIZE_ERROR
        file_access.fs_reply = int(FS_REPLY_GENERAL)

    # `if WE-Error = 901` [:L379] - a second test on the value the first arm just set,
    # rather than an `else`, so a caller arriving with 901 already in `We-Error` would
    # take this arm too.
    if file_access.we_error == RECORD_SIZE_ERROR:
        # `string IR902 ... A ... " < " ... "IRS-Final-Rec = " ...
        _LOG.error(
            "acasirsub5: IR902 Program Error: Temp rec = %s < IRS-Final-Rec = %s",
            _RECORD_SIZE_A,
            _RECORD_SIZE_B,
        )
        _process_logs_if_testing(dal_common, file_access, "ba012/rec-size")
        # `go to ba-rdbms-exit` [:L393] - Class 3, and THE BRIDGE IS NEVER CALLED.
        return FS_REPLY_GENERAL, RECORD_SIZE_ERROR

    # [:L400-L405] The six credential moves, in the handler's own order.
    rdb = load_rdb_data_once(system)
    rdb_data = file_access.rdb_data
    rdb_data.db_schema = rdb.db_schema
    rdb_data.db_uname = rdb.db_uname
    rdb_data.db_upass = rdb.db_upass
    rdb_data.db_port = rdb.db_port
    rdb_data.db_host = rdb.db_host
    rdb_data.db_socket = rdb.db_socket
    return None


def _read_triple(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`if fn-read-next` inside `ba015-Test-Ends` [common/acasirsub5.cbl:L432-L458].

    THE CLOSE'S OWN STATUS IS DISCARDED. [:L443-L444] save the READ's pair before the
    close runs and [:L453-L454] put it back afterwards, so whatever `ba030-Process-
    Close` and `MYSQL-1980-CLOSE` leave in `FS-Reply`/`WE-Error` is overwritten and can
    never be observed.

    Args:
        system: `System-Record` - needed by the open arm alone.
        final: `Final-Record`, reassembled in place by the read arm.
        file_access: `File-Access`; `File-Function`, `Access-Type` and both status
            fields are mutated in place exactly as the `set`/`move` verbs do.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy for the synthesised open.
        states: The cursor set to work through.

    Returns:
        The `(FS-Reply, We-Error)` pair. On either bail-out it is the failing call's own
            pair; otherwise it is the READ's pair, restored across the close.
    """
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.INPUT)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    _process_logs(dal_common, file_access, "ba015/read-open")
    # `if Fs-Reply not = zero or WE-Error not = zero / go to ba-rdbms-Exit`
    # [:L437-L439]. ANOMALY A10: NO CLOSE.
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    file_access.file_function = int(FileFunction.READ_NEXT)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `move FS-Reply to WS-Save-FS-Reply *> save the statuses` [:L443] and `move WE-
    # Error to WS-Save-WE-Error` [:L444].
    ws_save_fs_reply = file_access.fs_reply
    ws_save_we_error = file_access.we_error
    _process_logs(dal_common, file_access, "ba015/read-verb")
    # `if FS-Reply not = zero or WE-Error not = zero / go to ba-RDBMS-Exit`
    # [:L446-L448]. ANOMALY A10 again.
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    file_access.file_function = int(FileFunction.CLOSE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    _process_logs(dal_common, file_access, "ba015/read-close")
    file_access.fs_reply = ws_save_fs_reply
    file_access.we_error = ws_save_we_error
    # `move "Open, Read, Close" to WS-File-key` [:L455]. `WS-File-Key pic x(64)`
    # [copybooks/wsfnctn.cob:L52], so the literal is space-padded on the move.
    file_access.logging_data.ws_file_key = "Open, Read, Close"
    _process_logs(dal_common, file_access, "ba015/read-done")
    return FsReply(file_access.fs_reply), file_access.we_error


def _write_triple(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int] | None:
    """`if fn-Write` inside `ba015-Test-Ends` [common/acasirsub5.cbl:L459-L483].

    ANOMALY A2 - ONE `end-if.` CLOSES TWO NESTED `if`s [:L483]. The outer `if fn-Write`
    [:L459] has no terminator of its own; the period on the inner `end-if` ends the
    whole sentence and closes both. So.

    Args:
        system: `System-Record` - needed by the open arm alone.
        final: `Final-Record`, the source of the twenty-six rows.
        file_access: `File-Access`, mutated in place. On the fall-through path it is
            left with `File-Function` = `fn-Re-write` and a zeroed status pair, exactly
            as [:L479-L480] leaves it.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy for the synthesised open.
        states: The cursor set to work through.

    Returns:
        The `(FS-Reply, We-Error)` pair when the open failed [:L465] or when the write
            succeeded [:L482].
    """
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.I_O)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `if Fs-Reply not = zero or WE-Error not = zero / go to ba-rdbms-Exit` [:L463-L465]
    # - the ONE path in this arm that skips the close (anomaly A10).
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    file_access.file_function = int(FileFunction.WRITE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    ws_save_fs_reply = file_access.fs_reply
    ws_save_we_error = file_access.we_error
    file_access.file_function = int(FileFunction.CLOSE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    file_access.fs_reply = ws_save_fs_reply
    file_access.we_error = ws_save_we_error

    if file_access.fs_reply != 0 or file_access.we_error != 0:
        file_access.logging_data.ws_file_key = "Open, Write failed, Close"
        # `perform Ca-Process-Logs *> temp only during testing` [:L478] - UNGATED, and
        # the ONLY log record this arm ever emits.
        _process_logs(dal_common, file_access, "ba015/write-failed")
        file_access.file_function = int(FileFunction.RE_WRITE)
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        return None

    # `else / go to ba-RDBMS-Exit` [:L481-L482] - the write succeeded. ANOMALY A47: AND
    # THAT IS ALL THE `else` DOES. No `move ...
    return FsReply(file_access.fs_reply), file_access.we_error


def _rewrite_triple(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`if fn-Re-write` inside `ba015-Test-Ends` [common/acasirsub5.cbl:L485-L504].

    REACHED TWO WAYS: from a caller that asked for function 7, and from the write arm's
    fall-through (anomalies A1 and A2, see :func:`_write_triple`).

    Args:
        system: `System-Record` - needed by the open arm alone.
        final: `Final-Record`, the source of the twenty-six `UPDATE`s.
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy for the synthesised open.
        states: The cursor set to work through.

    Returns:
        The `(FS-Reply, We-Error)` pair - `(0, 0)` on every path that reaches the
            rewrite verb, per anomaly A1, and the open's own pair on the bail-out.
    """
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.I_O)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    # `set fn-Re-write to true` [:L493] then `perform ba020-Call-DAL *> write` [:L494] -
    # ANOMALY A46, the comment says write on the rewrite path.
    file_access.file_function = int(FileFunction.RE_WRITE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    ws_save_fs_reply = file_access.fs_reply
    ws_save_we_error = file_access.we_error
    file_access.file_function = int(FileFunction.CLOSE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `move WS-Save-FS-Reply to FS-Reply *> restore them` [:L499-L500].
    file_access.fs_reply = ws_save_fs_reply
    file_access.we_error = ws_save_we_error
    file_access.logging_data.ws_file_key = "Open, Rewrite, Close"
    _process_logs(dal_common, file_access, "ba015/rewrite-done")
    return FsReply(file_access.fs_reply), file_access.we_error


def dispatch(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`call "acasirsub5"` - the handler entry [common/acasirsub5.cbl:L143-L149].

    PARAMETER ORDER PRESERVED EXACTLY, per the section 0.4.3 contract. The blank lines
    at [:L144] and [:L146] are the family's layout habit. The facade calls it as `call
    "acasirsub5" using WS-System-Record Final-Record File-Access File-Defs ACAS-DAL-
    Common-data` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L84-L89].

    Args:
        system: `System-Record` [:L143].
        final: `Final-Record` [:L145].
        file_access: `File-Access` [:L147] - carries the function code, the access type,
            `RDB-Data` and `Logging-Data`, all mutated in place.
        file_defs: `File-Defs` [:L148]. The frozen handler copies `wsnames.cob` for its
            flat-file paths [:L135] and the RDB path uses none of them.
        dal_common: `ACAS-DAL-Common-data` [:L149].
        transport: The transport policy `dal/connection.py` requires of every open.
        states: The cursor set to work through. Keyword-only, and defaulted to this
            module's own so two runs are byte-identical (rule R-6).

    Returns:
        The `(FS-Reply, We-Error)` pair, with no recovery applied.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_system = int(WS_LOG_SYSTEM)
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT
    logging_data.file_key_no = KEY_COUNT

    # `if not FS-Cobol-Files-Used / move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses /
    # perform ba-Process-RDBMS *> Can't hurt / go to AA-Main-Exit` [:L172-L176].
    file_access.fa_rdbms_flat_statuses.fa_file_system_used = (
        system.system_data_block.rdbms_flat_statuses.file_system_used
    )
    file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = (
        system.system_data_block.rdbms_flat_statuses.file_duplicates_in_use
    )

    # `ba010-Test-WS-Rec-Size.` [:L358] contains ONLY `move 24 to WS-Log-File-no.
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    refused = _record_size_gate(system, file_access, dal_common)
    if refused is not None:
        return refused

    function = file_access.file_function

    # `if fn-open *> Open ignore` [:L421-L424]. ANOMALY A15's RDB half: no logging, no
    # bridge call, no state change beyond the status pair.
    if function == int(FileFunction.OPEN):
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        return FsReply.SUCCESS, int(WeError.SUCCESS)

    if function == int(FileFunction.CLOSE):
        # `move zero to File-Function Access-Type` [:L426-L427] - the handler ZEROES THE
        # FUNCTION CODE IT WAS DISPATCHED ON, and `Access-Type` with it, so a caller
        # inspecting the block afterwards finds neither.
        file_access.file_function = 0
        file_access.access_type = 0
        _process_logs(dal_common, file_access, "ba015/close-ignored")
        return FsReply(file_access.fs_reply), file_access.we_error

    if function == int(FileFunction.READ_NEXT):
        return _read_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )

    if function == int(FileFunction.WRITE):
        outcome = _write_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )
        if outcome is not None:
            return outcome
        # and `move zero to fs-reply we-error *> clear if used in write` have already
        # run inside `_write_triple`.
        return _rewrite_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )

    # `if fn-Re-write` [:L485-L504] - reachable both from a caller asking for it and
    # from the fall-through above. ANOMALY A16's RDB half.
    if function == int(FileFunction.RE_WRITE):
        return _rewrite_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )

    # `*> In case of bad call action that was missed.` [:L506], then `move 999 to WE-
    # Error.` [:L508] and `move 99 to FS-Reply.` [:L509]. ANOMALY A19.
    file_access.we_error = HANDLER_BAD_FUNCTION
    file_access.fs_reply = int(FS_REPLY_GENERAL)
    return FS_REPLY_GENERAL, HANDLER_BAD_FUNCTION


def open_(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Open` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287-L291].

    A NO-OP THAT ALWAYS SUCCEEDS. `ba015-Test-Ends` tests `if fn-open` first and answers
    `move zero to FS-Reply WE-Error / go to ba-RDBMS-Exit`
    [common/acasirsub5.cbl:L421-L424] without examining the access type, without calling
    the bridge and without touching the database.

    Args:
        system: `WS-System-Record` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L84].
        final: `Final-Record` [:L85].
        file_access: `File-Access` [:L86].
        file_defs: `File-Defs` [:L87].
        dal_common: `ACAS-DAL-Common-data` [:L88].
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)` unless the record-size gate refuses first, which returns `(99,
            901)` [common/acasirsub5.cbl:L376-L377].
    """
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.I_O)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def open_input(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Open-Input` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L293-L297].

    The second and last of the two open forms the frozen IRS facade publishes for this
    handler, and the only difference from :func:`open_` is the access type - which
    `ba015-Test-Ends` never reads [common/acasirsub5.cbl:L421-L424].

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)`, or the record-size gate's `(99, 901)`.
    """
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.INPUT)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def open_output(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """The `-Open-Output` verb of the twelve-verb facade vocabulary.

    NO FROZEN PARAGRAPH PUBLISHES THIS FOR THIS HANDLER. The IRS convention publishes
    exactly six verbs for `acasirsub5` - Open, Open-Input, Close, Read-Next, Write and
    ReWrite [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287, :L293, :L299, :L304, :L309,
    :L314], and :data:`PUBLISHED_FACADE_VERBS` is that list.

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)`, or the record-size gate's `(99, 901)`. Never a row count,
            because nothing is written and nothing is removed.
    """
    # `set fn-open to true` with `set fn-output to true`, the form the twelve-verb
    # vocabulary would use.
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.OUTPUT)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def open_extend(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """The `-Open-Extend` verb of the twelve-verb facade vocabulary.

    As with :func:`open_output`, NO FROZEN PARAGRAPH PUBLISHES THIS FOR THIS HANDLER;
    see :data:`PUBLISHED_FACADE_VERBS` for the six that are published. Vocabulary
    completeness only, and the same ignored no-op, because `ba015-Test-Ends` answers
    every `fn-open` identically without reading the access type
    [common/acasirsub5.cbl:L421-L424].

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)`, or the record-size gate's `(99, 901)`.
    """
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.EXTEND)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def close(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Close` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L299-L302].

    NO ERROR CHECK ON THIS VERB. Only the two open forms perform `irsub5-Check-4-Errors`
    [:L291, :L297].

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`; `File-Function` and `Access-Type` are both zeroed in
            it before this returns.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Whatever `(FS-Reply, We-Error)` the caller arrived with - NOT `(0, 0)`.
    """
    file_access.access_type = 0
    file_access.file_function = int(FileFunction.CLOSE)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


#: `acasirsub5-Open` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287]. THE SAME
#: IMPLEMENTATION UNDER THE FROZEN PARAGRAPH NAME, per section 0.3.3's "Facade with dual
#: aliasing".
acasirsub5_open = open_

acasirsub5_open_input = open_input

acasirsub5_close = close


def acasirsub5_read_next(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Read-Next` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L304-L307].

    THIS IS NOT :func:`read_next`. That function is the BRIDGE's `ba040-Process-Read-
    Next` [common/irsfinalMT.cbl:L317-L466] and takes an already-open connection; this
    one is the FACADE VERB, takes the handler's five-parameter linkage, and reaches
    `ba040` only through the synthesised open-read-close triple inside `ba015-Test-Ends`
    [common/acasirsub5.cbl:L432-L458].

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`, reassembled in place.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        The read's own `(FS-Reply, We-Error)` pair, restored across the close.
    """
    # `move zero to Access-Type` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L305] - and
    # then `ba015-Test-Ends` immediately sets it to `fn-Input`
    # [common/acasirsub5.cbl:L434], so the clearing is undone at once.
    file_access.access_type = 0
    file_access.file_function = int(FileFunction.READ_NEXT)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def acasirsub5_write(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Write` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L309-L312].

    ONE LOGICAL WRITE IS TWENTY-SIX `INSERT`s, keyed by the `occurs` subscript
    [common/irsfinalMT.cbl:L481], with NO blank-slot skip - the skip is commented out
    [:L477-L480] - so the table holds exactly twenty-six rows afterwards, blank entries
    persisted as spaces.

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`, the source of the twenty-six rows.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        `(0, 0)` on success AND on failure, per anomalies A1 and A2.
    """
    file_access.access_type = 0
    file_access.file_function = int(FileFunction.WRITE)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def acasirsub5_rewrite(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-ReWrite` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L314-L317].

    IT CANNOT REPORT A FAILURE EITHER, and for a different reason than the write.

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`, the source of the twenty-six `UPDATE`s.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        `(0, 0)` on every path that reaches the rewrite verb, per anomaly A1; otherwise
            the synthesised open's failure [common/acasirsub5.cbl:L489-L491] or the
            gate's `(99, 901)`.
    """
    file_access.access_type = 0
    file_access.file_function = int(FileFunction.RE_WRITE)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )
