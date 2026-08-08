r"""`acas016` and its bridge `slinvoiceMT` - the Invoice entity, header AND lines.

One handler, two tables: `SAINVOICE-REC` for the invoice header and
`SAINV-LINES-REC` for its lines. The module boundary follows the HANDLER, so both
tables live here and the pairing the COBOL performs is preserved.

Beyond the twelve standard verbs this handler publishes extra read functions -
by name, by batch and by customer - which the frozen copybook declares as
additional function codes [copybooks/wsfnctn.cob:L102-L105]. They are reproduced
as published, including for callers that never use them.

Each write goes through the bridge's own host-variable record, whose load
paragraph initialises the group first, so an unset field becomes zero or space
rather than SQL NULL.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Any, Final

from acas_posting.dal.connection import (
    ConnectionPolicyError,
    TransportSecurity,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1980_close,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    TABLE_OF_KEYNAMES,
    TABLE_PRIMARY_KEYS,
    CursorSlot,
    CursorState,
    CursorStateTable,
    KeyOfReference,
    start_relation_for,
)
from acas_posting.dal.status import (
    DUPLICATE_KEY_ERRNOS,
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    SqlState,
    WeError,
    is_duplicate_key_bridge_level,
    log_cobol_stop,
    log_file_handler_record,
    mysql_1100_db_error,
    sanitise_for_log,
    start_access_type_is_valid,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess, LoggingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.sales_invoice import (
    BRIDGE,
    ENTITY_FACADE,
    HANDLER,
    HEADER_TABLE,
    LINES_TABLE,
    IhCustomer,
    IhFig,
    IhInvoiceHeader,
    IhOrderView,
    IhPrime,
    IhSubPrime,
    IlInvoiceLine,
    SihCustomer,
    SihFig,
    SihOrderView,
    SihPrime,
    SihSubPrime,
    SilInvoiceLine,
    SilKey,
    SInvoiceHeader,
    WsInvoiceKey,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

_LOG: Final[logging.Logger] = logging.getLogger(__name__)

__all__: Final[tuple[str, ...]] = (
    # Identity, taken from records.sales_invoice so the two never drift apart.
    "BRIDGE",
    "ENTITY_FACADE",
    "HANDLER",
    "HEADER_TABLE",
    "LINES_TABLE",
    "BRIDGE_PARAGRAPH_TRACE",
    "HANDLER_PARAGRAPH_TRACE",
    "WS_LOG_FILE_NO_FLAT",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "BRIDGE_BAD_FUNCTION_WE_ERROR",
    "BRIDGE_PROGRAM_ID",
    "BRIDGE_START_ACCESS_TYPE_RANGE",
    "HANDLER_BAD_FUNCTION_WE_ERROR",
    "HANDLER_START_ACCESS_TYPE_RANGE",
    "RG_FAMILY_DESCRIPTION",
    "RG_SECONDARY_KEY_RANGE_WE_ERROR",
    "RG_UNKNOWN_UNEXPECTED_WE_ERROR",
    "HEADER_COLUMNS",
    "HEADER_LOAD_SEQUENCE",
    "LINE_COLUMNS",
    "LINE_LOAD_SEQUENCE",
    "SIGN_LOSS_KEYS",
    "ColumnBinding",
    "HEADER_KEY_OF_REFERENCE",
    "LINE_KEY_OF_REFERENCE",
    "KEYS_OF_REFERENCE",
    "BridgeState",
    "InvoiceBuffer",
    "linkage_buffer_for",
    "publish_linkage_buffer",
    "reset_bridge_storage",
    "TdSainvLinesRec",
    "TdSainvoiceRec",
    "WsInvoiceLine",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "bc000_hv_load_rg1",
    "bc100_unload_hvs_rg1",
    "bc200_insert_rg1",
    "bc300_update_rg1",
    "ba010_initialise",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba042_fetch",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba085_process_delete_all",
    "ba090_process_rewrite",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "bc050_process_read_indexed",
    "bc051_fetch_rg1",
    "bc058_restore_pointers",
    "bc070_process_write",
    "bc080_process_delete",
    "bc085_process_delete_all",
    "bc090_process_rewrite",
    "bc998_free",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa045_eval_keys",
    "aa050_process_read_indexed",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_exit",
    "aa_main_exit",
    "aa_process_flat_file",
    "ba010_test_ws_rec_size_handler",
    "ba012_test_ws_rec_size_2_handler",
    "ba015_test_ends_handler",
    "ba_process_rdbms_handler",
    "ba_rdbms_exit_handler",
    "ca_exit_handler",
    "ca_process_logs_handler",
    "HEADER_KEY_COLUMN",
    "LINES_KEY_COLUMN",
    "READ_INDEXED_NO_ERRNO_WE_ERROR",
    "REWRITE_ROW_COUNT_WE_ERROR",
    "DELETE_FAILURE_WE_ERROR",
    "StatementOutcome",
    "SPINE",
    "ca_process_logs",
    "dispatch",
    "slinvoice_mt",
    "narrow_signed_host_variable",
    # The WS-MYSQL-EDIT rendering [common/slinvoiceMT.cbl:L271] - published because it
    # is the arbitrated resolution of Q-edit-mask-sign and Q-edit-mask-truncation and
    # the parity suite must be able to assert it.
    "EditMaskWindow",
    "MYSQL_EDIT_FRACTION_DIGITS",
    "MYSQL_EDIT_FRACTION_POSITION",
    "MYSQL_EDIT_INTEGER_POSITIONS",
    "MYSQL_EDIT_LOCATOR",
    "MYSQL_EDIT_PICTURE",
    "MYSQL_EDIT_POINT_POSITION",
    "MYSQL_EDIT_SIGN_POSITION",
    "MYSQL_EDIT_UNITS_POSITION",
    "MYSQL_EDIT_WIDTH",
    "MYSQL_EDIT_WINDOWS",
    "render_through_mysql_edit",
    "ws_mysql_edit",
)


# Log identity [common/acas016.cbl:L248-L249] and [common/acas016.cbl:L567]
# [common/acas016.cbl:L248] verbatim: move 3 to WS-Log-System. *> 1 = IRS, 2=GL, 3=SL,
# 4=PL, 5=Invoice used in FH logging N-logsystem5-meaning.
WS_LOG_SYSTEM: Final[int] = int(LogSystem.SL)

# N-log. The file number is set twice. [common/acas016.cbl:L249] verbatim: move 12 to
# WS-Log-File-No. *> RDB, File/Table then [common/acas016.cbl:L567], inside ba010-Test-
# WS-Rec-Size, verbatim: move 22 to WS-Log-File-no.
WS_LOG_FILE_NO_FLAT: Final[int] = 12
WS_LOG_FILE_NO_RDB: Final[int] = 22


# ws-No-Paragraph trace numbers N-noparagraph-collision. The handler's values are
# 201..208 and are IDENTICAL to acas013's and acas015's, so a log line is ambiguous
# without WS-Log-System.
HANDLER_PARAGRAPH_TRACE: Final[Mapping[str, int]] = MappingProxyType(
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

# The bridge keeps its own, entirely disjoint, numbering - 1..20 for the header and
# 51..58 for the Repeating Group.

# THE FOURTEEN EXIT TERMINATORS - mapped to `return`, not to a no-op function R-5
# requires every paragraph to map to a function.
BRIDGE_PARAGRAPH_TRACE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed-select": 5,
        "ba050-Process-Read-Indexed-fetch": 6,
        "ba060-Process-Start-header": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba085-Process-Delete-All": 15,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
        "bc050-Process-Read-Indexed": 51,
        "bc051-Fetch-RG1": 52,
        "bc070-Process-Write": 53,
        "bc080-Process-Delete": 54,
        "bc085-Process-Delete-All": 55,
        "bc090-Process-Rewrite": 56,
        "ba060-Process-Start-rg1": 57,
        "bc998-Free": 58,
    }
)


# ---------------------------------------------------------------------------
# Status vocabulary
# ---------------------------------------------------------------------------
# The two bad-function paragraphs return DIFFERENT We-Error values, and both are
# reachable, so both are named.
#  handler [common/acas016.cbl:L535-L536]:  move 999 to WE-Error / move 99 to fs-reply
#  bridge  [common/slinvoiceMT.cbl:L1414-L1415]: move 990 to WE-Error / move 99 to Fs-Reply
# Note the handler's 999 is the value the bridge's own documentation calls
# "Not used here - Yet" [common/slinvoiceMT.cbl:L185] - a further divergence
# between the two layers' vocabularies, recorded and not harmonised.
#: The bridge's PROGRAM-ID, as `call "slinvoiceMT"` names it
#: [common/acas016.cbl:L85]. `BRIDGE`, imported from
#: :mod:`acas_posting.records.sales_invoice`, is the bridge's FILE PATH and is what
#: a locator cites; a log record names the PROGRAM, so that every handler's records
#: carry the same kind of identifier.
BRIDGE_PROGRAM_ID: Final[str] = "slinvoiceMT"

HANDLER_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.NOT_USED)
BRIDGE_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

# The START Access-Type guards ALSO differ between the layers, and the handler's is the
# odd one out in two ways.
HANDLER_START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 9)
BRIDGE_START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 8)

#: ``989`` - set by ``ba050-Process-Read-Indexed`` when the fetch returns nothing AND
#: the driver reported no errno [common/slinvoiceMT.cbl:L930], as the else-arm of the
#: ``990`` case at [:L925].
READ_INDEXED_NO_ERRNO_WE_ERROR: Final[int] = 989

REWRITE_ROW_COUNT_WE_ERROR: Final[int] = 994

_OPEN_INPUT_FAILED_FS_REPLY: Final[int] = 35

#: The five function codes ``aa045-Eval-Keys`` sets a key for
#: [common/acas016.cbl:L400-L404]: read-indexed, write, re-write, delete and start.
_AA045_KEYED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
    }
)

DELETE_FAILURE_WE_ERROR: Final[int] = int(WeError.DELETE_SQLSTATE_NOT_00000)

# N-rg-status-codes. The 8nn family exists in NO single-table bridge; it belongs to
# slinvoiceMT and plinvoiceMT alone. Authoritative comment block
# [common/slinvoiceMT.cbl:L204-L207], verbatim.
RG_FAMILY_DESCRIPTION: Final[str] = "Processing on RG Table & rows"

RG_UNKNOWN_UNEXPECTED_WE_ERROR: Final[int] = 890

# 880 is DOCUMENTED AND NEVER ASSIGNED in this bridge. Verified by exhaustive search.
RG_SECONDARY_KEY_RANGE_WE_ERROR: Final[int] = 880

# Widths of the log fields, so every string this module writes truncates exactly as the
# COBOL MOVE would.
_WS_FILE_KEY_WIDTH: Final[int] = 64
_WS_LOG_WHERE_WIDTH: Final[int] = 231


HEADER_KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[HEADER_TABLE][0]
LINE_KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[LINES_TABLE][0]

# N-two-cursors. [common/slinvoiceMT.cbl:L329-L336], verbatim: 01 DAL-Data. 05 MOST-
# Relation pic xxx. *> valid are >=, <=, <, >, = 05 Most-Cursor-Set pic 9 value zero.
KEYS_OF_REFERENCE: Final[Mapping[int, KeyOfReference]] = MappingProxyType(
    {1: HEADER_KEY_OF_REFERENCE, 2: LINE_KEY_OF_REFERENCE}
)

#: ``SINVOICE-KEY`` - the header primary key [mysql/ACASDB.sql:L876], and the name the
#: bridge's first key of reference carries [common/slinvoiceMT.cbl:L297].
HEADER_KEY_COLUMN: Final[str] = TABLE_PRIMARY_KEYS[HEADER_TABLE]
#: ``IL-LINE-KEY`` - the lines primary key [mysql/ACASDB.sql:L825] and the second key of
#: reference [common/slinvoiceMT.cbl:L301]. Declared, yet unreachable through the
#: handler's guarded verbs: N-key2-unreachable.
LINES_KEY_COLUMN: Final[str] = TABLE_PRIMARY_KEYS[LINES_TABLE]

# TWO INDEPENDENT AUTHORITIES, CROSS-CHECKED AT IMPORT.
if HEADER_KEY_OF_REFERENCE.column_name != HEADER_KEY_COLUMN:  # pragma: no cover
    raise ImportError(
        "SAINVOICE-REC key of reference "
        f"{HEADER_KEY_OF_REFERENCE.column_name!r} "
        f"[common/slinvoiceMT.cbl:L297] disagrees with its DDL primary key "
        f"{HEADER_KEY_COLUMN!r} [mysql/ACASDB.sql:L876]"
    )
if LINE_KEY_OF_REFERENCE.column_name != LINES_KEY_COLUMN:  # pragma: no cover
    raise ImportError(
        "SAINV-LINES-REC key of reference "
        f"{LINE_KEY_OF_REFERENCE.column_name!r} "
        f"[common/slinvoiceMT.cbl:L301] disagrees with its DDL primary key "
        f"{LINES_KEY_COLUMN!r} [mysql/ACASDB.sql:L825]"
    )


# The entity-to-table spine, published for traceability (R-5) AAP section 0.2.1.1's
# spine table for this row, resolved to live values rather than restated in prose, so a
# reader - or a traceability generator - can obtain the mapping from the module itself.
SPINE: Final[Mapping[str, object]] = MappingProxyType(
    {
        "entity_facade": ENTITY_FACADE,
        "handler": HANDLER,
        "bridge": BRIDGE,
        "tables": (HEADER_TABLE, LINES_TABLE),
        "primary_keys": MappingProxyType(
            {HEADER_TABLE: HEADER_KEY_COLUMN, LINES_TABLE: LINES_KEY_COLUMN}
        ),
        "keys_of_reference": KEYS_OF_REFERENCE,
        "extra_function_codes": (int(FileFunction.READ_NEXT_HEADER),),
    }
)

_HEADER_SLOT: Final[CursorSlot] = HEADER_KEY_OF_REFERENCE.cursor_slot
_LINE_SLOT: Final[CursorSlot] = LINE_KEY_OF_REFERENCE.cursor_slot

# ba040-Process-Read-Next opens the sequential walk with a low key rather than a caller-
# supplied one. [common/slinvoiceMT.cbl:L646-L647], verbatim: '` >= "' ... '0000000000'.
_SEQUENTIAL_LOW_KEY: Final[str] = "0000000000"
_SEQUENTIAL_RELATION: Final[str] = ">="

# The six signed fields the bridge narrows to unsigned host variables. Sourced from the
# generated dictionary rather than transcribed.
SIGN_LOSS_KEYS: Final[tuple[str, ...]] = (
    f"{HEADER_TABLE}.IH-DAT",
    f"{HEADER_TABLE}.IH-DEDUCT-DAYS",
    f"{HEADER_TABLE}.IH-DAYS",
    f"{HEADER_TABLE}.IH-CR",
    f"{HEADER_TABLE}.IH-LINES",
    f"{LINES_TABLE}.IL-QTY",
)


# Column metadata, GENERATED from the data dictionary (rule R-5).
@dataclass(frozen=True, slots=True)
class ColumnBinding:
    """One column of one table, with everything needed to bind it and cite it.

    Rule R-5 requires every field to map to a data-dictionary entry, and AAP section
    0.8.1 makes the ordering a directive: *"Data dictionary first. ... every Python
    field definition cites its entry.
    """

    dictionary_key: str
    citation: str
    column_name: str
    quoted_column_name: str
    ordinal: int
    host_variable: str
    host_variable_suffix: str
    #: Python storage class: ``"STR"``, ``"INT"``, ``"DECIMAL"`` or ``"NONE"`` (group
    #: items). Never a float - rule R-2.
    storage: str
    scale: int
    character_length: int
    host_variable_digits: int
    host_variable_integer_digits: int
    column_unsigned: bool
    signed_source: bool
    sign_narrowed: bool
    load_source: str | None
    #: The bridge statement that unloads it back, or ``None`` when there is none - which
    #: is the whole of N-il-invoice-never-unloaded and N-header-key-not-unloaded.
    unload_source: str | None

    @property
    def unloaded(self) -> bool:
        """Whether the bridge ever copies this host variable back to the record."""
        return self.unload_source is not None


def _column_bindings(table: str) -> tuple[ColumnBinding, ...]:
    """Build the binding tuple for ``table`` in COLUMN-ORDINAL order.

    Determinism (rule R-6): the dictionary is a committed artefact and the ordinal is a
    fixed integer, so this tuple is byte-identical between processes. Nothing here reads
    a clock, a random source or the environment.
    """
    bindings: list[ColumnBinding] = []
    for entry in loader.entries_for_table(table):
        column = loader.column_for(entry.key)
        host_variable = loader.host_variable_for(entry.key)
        copybook_field = loader.copybook_field_for(entry.key)
        if column is None or host_variable is None:  # pragma: no cover - guard
            msg = (
                f"dictionary entry {entry.key!r} is missing its column or host "
                "variable; the generated dictionary is incomplete for "
                f"{table!r}"
            )
            raise loader.DictionaryLookupError(msg)
        drift = loader.drift_for(entry.key)
        bindings.append(
            ColumnBinding(
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                column_name=column.name,
                quoted_column_name=quote_identifier(column.name),
                ordinal=column.ordinal,
                host_variable=host_variable.name,
                host_variable_suffix=host_variable.hv_group_suffix,
                storage=str(entry.cobol_python_storage.value),
                scale=int(column.scale or 0),
                character_length=int(host_variable.character_length or 0),
                host_variable_digits=int(host_variable.digits or 0),
                host_variable_integer_digits=int(host_variable.integer_digits or 0),
                column_unsigned=bool(column.unsigned),
                signed_source=bool(
                    copybook_field.signed if copybook_field is not None else False
                ),
                sign_narrowed=bool(drift.signedness),
                load_source=host_variable.load_source,
                unload_source=host_variable.unload_source,
            )
        )
    return tuple(bindings)


def _load_sequence(bindings: Iterable[ColumnBinding]) -> tuple[ColumnBinding, ...]:
    """Order ``bindings`` by the bridge's LOAD-PARAGRAPH statement order.

    N-triple-order-mismatch. This is deliberately a SECOND, independent ordering, never
    derived from :func:`_column_bindings`. For the header the two differ at ``IH-
    LINES``.
    """

    def statement_line(binding: ColumnBinding) -> tuple[int, int]:
        source = binding.load_source
        if source is None:
            return (1, binding.ordinal)
        _, _, line_token = source.rpartition(":L")
        return (0, int(line_token)) if line_token.isdigit() else (1, binding.ordinal)

    return tuple(sorted(bindings, key=statement_line))


HEADER_COLUMNS: Final[tuple[ColumnBinding, ...]] = _column_bindings(HEADER_TABLE)

LINE_COLUMNS: Final[tuple[ColumnBinding, ...]] = _column_bindings(LINES_TABLE)

HEADER_LOAD_SEQUENCE: Final[tuple[ColumnBinding, ...]] = _load_sequence(HEADER_COLUMNS)

LINE_LOAD_SEQUENCE: Final[tuple[ColumnBinding, ...]] = _load_sequence(LINE_COLUMNS)

_HEADER_BY_COLUMN: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in HEADER_COLUMNS}
)
_LINE_BY_COLUMN: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in LINE_COLUMNS}
)


# Storage coercion - the bridge's MOVE semantics, reproduced field by field.
def narrow_signed_host_variable(binding: ColumnBinding, value: int) -> int:
    """Reproduce ``MOVE <signed source> TO <unsigned host variable>``.

    N-signloss, AAP anomaly A-11 family. Six of this bridge's 45 fields are declared
    SIGNED in the copybook and UNSIGNED in both the host variable and the column, so
    **the sign is lost at the bridge, before any SQL executes**.
    """
    magnitude = -value if value < 0 else value
    digits = binding.host_variable_digits
    if digits > 0:
        # COBOL truncates HIGH-order digits on a MOVE into a shorter numeric field.
        magnitude %= 10**digits
    return magnitude


def _initial_value(binding: ColumnBinding) -> str | int | Decimal:
    """The value ``INITIALIZE`` leaves in a host variable - zero or spaces.

    ``initialize TD-SAINVOICE-REC.`` [common/slinvoiceMT.cbl:L1453] and ``initialize TD-
    SAINV-LINES-REC.`` [common/slinvoiceMT.cbl:L2787] are the FIRST statements of their
    load paragraphs, so a field the load never touches still reaches SQL as zero or
    space - never ``NULL``. AAP section 0.6.2, verbatim.
    """
    if binding.storage == "DECIMAL":
        return Decimal(0).quantize(Decimal(1).scaleb(-binding.scale))
    if binding.storage == "INT":
        return 0
    return " " * binding.character_length


def _coerce_for_bind(binding: ColumnBinding, value: object) -> str | int | Decimal:
    """Coerce ``value`` into exactly what this column's host variable would hold.

    This is the ONE place a value crosses from the record area into the host variable,
    so it is the one place the drift is applied.
    """
    if binding.storage in {"STR", "NONE"}:
        text = "" if value is None else str(value)
        width = binding.character_length or len(text)
        return text[:width].ljust(width)

    if binding.storage == "INT":
        if isinstance(value, bool):  # pragma: no cover - defensive
            msg = (
                f"{binding.dictionary_key}: a boolean is not a COBOL numeric; "
                "the record layer must supply an int"
            )
            raise TypeError(msg)
        number = int(value) if value is not None else 0
        if binding.sign_narrowed:
            return narrow_signed_host_variable(binding, number)
        return number

    if binding.storage == "DECIMAL":
        amount = _as_decimal(binding, value)
        quantum = Decimal(1).scaleb(-binding.scale)
        quantized = amount.quantize(quantum, rounding=ROUND_DOWN)
        if binding.sign_narrowed and quantized < 0:
            return -quantized
        return quantized

    msg = (  # pragma: no cover - the dictionary has only four storage classes
        f"{binding.dictionary_key}: unsupported storage class "
        f"{binding.storage!r}"
    )
    raise loader.DictionaryNumericPolicyError(msg)


@dataclass(frozen=True, slots=True)
class EditMaskWindow:
    """One numeric column's FIXED substring of ``WS-MYSQL-EDIT``.

    The bridge never binds a numeric host variable. It ``MOVE``s the host variable into
    the single shared edit field ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)``
    [common/slinvoiceMT.cbl:L271] and then ``STRING``s a hard-coded substring of that
    field into the statement text.
    """

    host_variable: str
    integer_start: int
    integer_length: int
    decimal_start: int
    decimal_length: int
    render_locator: str


# N-edit-mask-sign / N-edit-mask-truncation - the two anomalies this mask creates.
# ARBITRATED AGAINST THE COMPILED ORACLE, not reasoned about.
MYSQL_EDIT_PICTURE: Final[str] = "-Z(18)9.9(9)"
MYSQL_EDIT_LOCATOR: Final[str] = "[common/slinvoiceMT.cbl:L271]"
MYSQL_EDIT_WIDTH: Final[int] = 30
MYSQL_EDIT_SIGN_POSITION: Final[int] = 1
MYSQL_EDIT_INTEGER_POSITIONS: Final[int] = 19
MYSQL_EDIT_UNITS_POSITION: Final[int] = 20
MYSQL_EDIT_POINT_POSITION: Final[int] = 21
MYSQL_EDIT_FRACTION_POSITION: Final[int] = 22
MYSQL_EDIT_FRACTION_DIGITS: Final[int] = 9

MYSQL_EDIT_WINDOWS: Final[Mapping[str, EditMaskWindow]] = MappingProxyType(
    {
        "IH-INVOICE": EditMaskWindow(
            "HV-IH-INVOICE", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L1569]"
        ),
        "IH-TEST": EditMaskWindow(
            "HV-IH-TEST", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1581]"
        ),
        "IH-DAT": EditMaskWindow(
            "HV-IH-DAT", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L1602]"
        ),
        "IH-TYPE": EditMaskWindow(
            "HV-IH-TYPE", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1623]"
        ),
        "IH-P-C": EditMaskWindow(
            "HV-IH-P-C", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1653]"
        ),
        "IH-NET": EditMaskWindow(
            "HV-IH-NET", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1670]"
        ),
        "IH-EXTRA": EditMaskWindow(
            "HV-IH-EXTRA", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1687]"
        ),
        "IH-CARRIAGE": EditMaskWindow(
            "HV-IH-CARRIAGE", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1704]"
        ),
        "IH-VAT": EditMaskWindow(
            "HV-IH-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1721]"
        ),
        "IH-DISCOUNT": EditMaskWindow(
            "HV-IH-DISCOUNT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1738]"
        ),
        "IH-E-VAT": EditMaskWindow(
            "HV-IH-E-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1755]"
        ),
        "IH-C-VAT": EditMaskWindow(
            "HV-IH-C-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L1772]"
        ),
        "IH-DEDUCT-DAYS": EditMaskWindow(
            "HV-IH-DEDUCT-DAYS", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1843]"
        ),
        "IH-DEDUCT-AMT": EditMaskWindow(
            "HV-IH-DEDUCT-AMT", 18, 3, 22, 2, "[common/slinvoiceMT.cbl:L1855]"
        ),
        "IH-DEDUCT-VAT": EditMaskWindow(
            "HV-IH-DEDUCT-VAT", 18, 3, 22, 2, "[common/slinvoiceMT.cbl:L1872]"
        ),
        "IH-DAYS": EditMaskWindow(
            "HV-IH-DAYS", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1889]"
        ),
        "IH-CR": EditMaskWindow(
            "HV-IH-CR", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L1901]"
        ),
        "IH-LINES": EditMaskWindow(
            "HV-IH-LINES", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L1913]"
        ),
        "IL-INVOICE": EditMaskWindow(
            "HV1-IL-INVOICE", 11, 10, 0, 0, "[common/slinvoiceMT.cbl:L2875]"
        ),
        "IL-LINE": EditMaskWindow(
            "HV1-IL-LINE", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L2887]"
        ),
        "IL-QTY": EditMaskWindow(
            "HV1-IL-QTY", 16, 5, 0, 0, "[common/slinvoiceMT.cbl:L2917]"
        ),
        "IL-NET": EditMaskWindow(
            "HV1-IL-NET", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L2947]"
        ),
        "IL-UNIT": EditMaskWindow(
            "HV1-IL-UNIT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L2964]"
        ),
        "IL-DISCOUNT": EditMaskWindow(
            "HV1-IL-DISCOUNT", 19, 2, 22, 2, "[common/slinvoiceMT.cbl:L2981]"
        ),
        "IL-VAT": EditMaskWindow(
            "HV1-IL-VAT", 14, 7, 22, 2, "[common/slinvoiceMT.cbl:L2998]"
        ),
        "IL-VAT-CODE": EditMaskWindow(
            "HV1-IL-VAT-CODE", 18, 3, 0, 0, "[common/slinvoiceMT.cbl:L3015]"
        ),
    }
)


def ws_mysql_edit(value: int | Decimal) -> str:
    """Return the 30 characters ``WS-MYSQL-EDIT`` holds after ``MOVE value``.

    Three COBOL behaviours are reproduced deliberately.
    """
    exact = value if isinstance(value, Decimal) else Decimal(int(value))
    negative = exact < 0
    magnitude = -exact if negative else exact
    magnitude = magnitude.quantize(
        Decimal(1).scaleb(-MYSQL_EDIT_FRACTION_DIGITS), rounding=ROUND_DOWN
    )

    integer_digits, _, fraction_digits = f"{magnitude:f}".partition(".")
    integer_digits = integer_digits[-MYSQL_EDIT_INTEGER_POSITIONS:]

    return (
        ("-" if negative else " ")
        + integer_digits.rjust(MYSQL_EDIT_INTEGER_POSITIONS)
        + "."
        + fraction_digits.ljust(MYSQL_EDIT_FRACTION_DIGITS, "0")
    )


def render_through_mysql_edit(
    binding: ColumnBinding, held: int | Decimal
) -> int | Decimal:
    """Return the value the bridge's ``STRING`` of the mask would put in the SQL.

    This is the second and final conversion a numeric column undergoes, after
    :func:`narrow_signed_host_variable` has modelled the ``MOVE`` into the host
    variable. It reproduces N-edit-mask-sign and N-edit-mask-truncation for every
    numeric column of both tables.
    """
    window = MYSQL_EDIT_WINDOWS[binding.column_name]
    mask = ws_mysql_edit(held)

    start = window.integer_start - 1
    integer_text = mask[start : start + window.integer_length].strip()
    if window.decimal_length == 0:
        return int(integer_text)

    fraction_start = window.decimal_start - 1
    fraction_text = mask[fraction_start : fraction_start + window.decimal_length]
    return Decimal(f"{integer_text}.{fraction_text}")


# The window census above is TRANSCRIBED from the 26 render sites so that each carries
# its own locator (rule R-4).
for _mask_table in (HEADER_TABLE, LINES_TABLE):
    for _mask_binding in _column_bindings(_mask_table):
        _numeric = _mask_binding.storage in {"INT", "DECIMAL"}
        _window = MYSQL_EDIT_WINDOWS.get(_mask_binding.column_name)
        if _numeric != (_window is not None):
            raise ImportError(
                f"{_mask_binding.dictionary_key}: storage "
                f"{_mask_binding.storage!r} and MYSQL_EDIT_WINDOWS disagree on "
                f"whether {_mask_binding.column_name!r} is rendered through "
                f"WS-MYSQL-EDIT {MYSQL_EDIT_LOCATOR}"
            )
        if _window is None:
            continue
        _expected_start = (
            MYSQL_EDIT_POINT_POSITION - _mask_binding.host_variable_integer_digits
        )
        if (
            _window.integer_start != _expected_start
            or _window.integer_length != _mask_binding.host_variable_integer_digits
        ):
            raise ImportError(
                f"{_mask_binding.dictionary_key}: window "
                f"({_window.integer_start}:{_window.integer_length}) from "
                f"{_window.render_locator} does not match the "
                f"{_mask_binding.host_variable_integer_digits} integer digits of "
                f"{_window.host_variable} - expected "
                f"({_expected_start}:{_mask_binding.host_variable_integer_digits})"
            )
        if (
            _window.integer_start + _window.integer_length - 1
            != MYSQL_EDIT_UNITS_POSITION
        ):
            raise ImportError(
                f"{_mask_binding.dictionary_key}: window from "
                f"{_window.render_locator} does not end at the units position "
                f"{MYSQL_EDIT_UNITS_POSITION} of {MYSQL_EDIT_PICTURE}"
            )
        if _window.decimal_length not in {0, _mask_binding.scale}:
            raise ImportError(
                f"{_mask_binding.dictionary_key}: fraction window "
                f"({_window.decimal_start}:{_window.decimal_length}) from "
                f"{_window.render_locator} does not match scale "
                f"{_mask_binding.scale}"
            )
del _mask_table, _mask_binding, _numeric, _window, _expected_start


def _render_for_bind(
    binding: ColumnBinding, held: str | int | Decimal
) -> str | int | Decimal:
    """Render a held host variable exactly as the generated statement does.

    The bridge builds its statement text one host variable at a time, and the rendering
    is per storage class.
    """
    if binding.storage in {"STR", "NONE"}:
        return str(held).rstrip()
    return render_through_mysql_edit(binding, held)


def _as_decimal(binding: ColumnBinding, value: object) -> Decimal:
    """Return ``value`` as a :class:`~decimal.Decimal`, refusing binary floats."""
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    msg = (
        f"{binding.dictionary_key}: {type(value).__name__} is not an exact "
        "numeric; accounting values must arrive as Decimal, int or str "
        "(rule R-2 forbids binary floating point in this layer)"
    )
    raise TypeError(msg)


def _truncate_move(text: str, width: int) -> str:
    """``MOVE`` a literal into a fixed ``PIC X(width)`` field, COBOL-style.

    Used for ``WS-File-Key`` (``pic x(64)`` [copybooks/wsfnctn.cob:L52]) and ``WS-Log-
    Where`` (``pic x(231)`` [copybooks/wsfnctn.cob:L53]). A COBOL ``MOVE`` into a
    shorter alphanumeric field truncates on the RIGHT and pads with spaces, and every
    ``STRING ...
    """
    return text[:width].rstrip()


# The two host-variable groups [common/slinvoiceMT.cbl:L381-L385], verbatim.
class _HostVariableGroup:
    """Shared behaviour of the two ``TD-`` groups: initialise, set, read, bind.

    Deliberately NOT a dataclass of 31 or 14 named attributes. Rule R-5 makes the
    generated dictionary the single source of truth for field metadata ("**Data
    dictionary first** ...
    """

    __slots__ = ("_bindings", "_by_column", "_group_name", "_values")

    def __init__(
        self,
        *,
        group_name: str,
        bindings: tuple[ColumnBinding, ...],
        by_column: Mapping[str, ColumnBinding],
    ) -> None:
        self._group_name = group_name
        self._bindings = bindings
        self._by_column = by_column
        self._values: dict[str, str | int | Decimal] = {}
        self.initialize()

    @property
    def group_name(self) -> str:
        """The COBOL group name, e.g. ``TD-SAINVOICE-REC``."""
        return self._group_name

    @property
    def bindings(self) -> tuple[ColumnBinding, ...]:
        """The group's columns in frozen ``CREATE TABLE`` ordinal order."""
        return self._bindings

    def initialize(self) -> None:
        """``INITIALIZE`` the whole group - zero or spaces, never ``NULL``."""
        self._values = {
            binding.column_name: _initial_value(binding) for binding in self._bindings
        }

    def move_in(self, column_name: str, value: object) -> None:
        """``MOVE value TO HV-<column>``, applying this field's drift."""
        binding = self._by_column[column_name]
        self._values[column_name] = _coerce_for_bind(binding, value)

    def __getitem__(self, column_name: str) -> str | int | Decimal:
        """Read a host variable back, as an unload ``MOVE`` would."""
        return self._values[column_name]

    def __contains__(self, column_name: object) -> bool:
        return column_name in self._values

    def as_parameters(self) -> tuple[str | int | Decimal, ...]:
        """Every host variable, in ordinal order, rendered and ready to bind.

        The tuple length always equals the table's column count, because
        :meth:`initialize` seeds every key. No element is ever ``None``, which is the
        ``NOT NULL`` invariant of AAP section 0.6.2 made mechanical.
        """
        return tuple(
            _render_for_bind(binding, self._values[binding.column_name])
            for binding in self._bindings
        )

    def render_one(self, column_name: str) -> str | int | Decimal:
        """One host variable, rendered exactly as :meth:`as_parameters` renders it.

        Used for the ``WHERE`` value of an UPDATE or DELETE, where the bridge binds the
        SAME field it also SETs - ``bb300-Update`` appends ``FUNCTION TRIM (WS-Where
        (1:J))`` [common/slinvoiceMT.cbl:L2336] over a clause built from the key host
        variable.
        """
        binding = self._by_column[column_name]
        return _render_for_bind(binding, self._values[column_name])

    def snapshot(self) -> Mapping[str, str | int | Decimal]:
        """A read-only view, for assertions and log records."""
        return MappingProxyType(dict(self._values))


class TdSainvoiceRec(_HostVariableGroup):
    """``01 TD-SAINVOICE-REC.`` [common/slinvoiceMT.cbl:L390-L421] - 31 HVs, ``HV`` prefix.
    """

    def __init__(self) -> None:
        super().__init__(
            group_name="TD-SAINVOICE-REC",
            bindings=HEADER_COLUMNS,
            by_column=_HEADER_BY_COLUMN,
        )


class TdSainvLinesRec(_HostVariableGroup):
    """``01 TD-SAINV-LINES-REC.`` [common/slinvoiceMT.cbl:L426-L440] - 14 HVs, ``HV1``
    prefix.
    """

    def __init__(self) -> None:
        super().__init__(
            group_name="TD-SAINV-LINES-REC",
            bindings=LINE_COLUMNS,
            by_column=_LINE_BY_COLUMN,
        )


@dataclass(slots=True)
class WsInvoiceLine:
    """``01 WS-Invoice-Line.`` [common/slinvoiceMT.cbl:L361-L377].

    That bare ``filler`` sits exactly where ``copybooks/slwsinv.cob:L97-L98`` declares
    ``sil-Back-Ordered`` - the field added on 03/03/24 to replace the old filler, ``*>
    value space, or B for a BO item.`` So the 2024 feature has NO host variable and NO
    column.
    """

    ws_sil_invoice: int = 0
    ws_sil_line: int = 0
    ws_sil_product: str = ""
    ws_sil_pa: str = ""
    ws_sil_qty: int = 0
    ws_sil_type: str = ""
    ws_sil_description: str = ""
    ws_sil_net: Decimal = Decimal("0.00")
    ws_sil_unit: Decimal = Decimal("0.00")
    ws_sil_discount: Decimal = Decimal("0.00")
    ws_sil_vat: Decimal = Decimal("0.00")
    ws_sil_vat_code: int = 0
    ws_sil_update: str = ""
    #: The bare ``filler pic x`` [:L377] standing where ``sil-Back-Ordered`` lives in
    #: the copybook. Declared so the omission is visible, never mapped.
    filler_80: str = " "

    @property
    def ws_sil_key(self) -> str:
        """``03 WS-Sil-Key.`` rendered as the 10 characters the PK column holds.

        ``move WS-Sil-Key to HV1-IL-LINE-KEY`` [common/slinvoiceMT.cbl:L2789] is a GROUP
        move, so the column receives the 8-digit invoice followed by the 2-digit line,
        zero-filled - exactly the ten bytes ``KeyOfReference(offset 1, length 10)``
        describes.
        """
        return f"{self.ws_sil_invoice:08d}{self.ws_sil_line:02d}"

    def ws_sil_analyised(self) -> bool:
        """``88 WS-Sil-Analyised value "Z".`` [common/slinvoiceMT.cbl:L376]."""
        return self.ws_sil_update == "Z"


def _new_header_record() -> SInvoiceHeader:
    """``initialize`` a header view - every field zero or space, nothing absent.

    COBOL's ``INITIALIZE`` sets numeric fields to zero and alphanumeric fields to spaces
    across the whole group, which is why every column of ``SAINVOICE-REC`` can be
    declared ``NOT NULL`` and why AAP section 0.6.2 requires the Python layer to
    *"default rather than omit"*.
    """
    return SInvoiceHeader(
        sih_prime=SihPrime(
            ws_invoice_key=WsInvoiceKey(sih_invoice=0, sih_test=0),
            sih_customer=SihCustomer(sih_nos=" " * 6, sih_check=0),
            sih_date=0,
            sih_order=" " * 10,
            # The redefinition of sih-order [copybooks/slwsinv.cob:L28-L38].
            filler_28=SihOrderView(
                sih_freq=" ",
                sih_repeat=0,
                filler_37=" " * 3,
                sih_last_date=0,
            ),
            sih_type=0,
            sih_ref=" " * 10,
        ),
        sih_sub_prime=SihSubPrime(
            sih_description=" " * 32,
            sih_fig=SihFig(
                sih_p_c=Decimal("0.00"),
                sih_net=Decimal("0.00"),
                sih_extra=Decimal("0.00"),
                sih_carriage=Decimal("0.00"),
                sih_vat=Decimal("0.00"),
                sih_discount=Decimal("0.00"),
                sih_e_vat=Decimal("0.00"),
                sih_c_vat=Decimal("0.00"),
            ),
            sih_status=" ",
            sih_status_p=" ",
            sih_status_l=" ",
            sih_status_c=" ",
            sih_status_a=" ",
            sih_status_i=" ",
            sih_lines=0,
            sih_deduct_days=0,
            sih_deduct_amt=Decimal("0.00"),
            sih_deduct_vat=Decimal("0.00"),
            sih_days=0,
            sih_cr=0,
            sih_day_book_flag=" ",
            sih_update=" ",
        ),
    )


def _new_line_record() -> SilInvoiceLine:
    """``initialize`` a line view - every field zero or space, nothing absent.

    N-back-ordered-dropped. ``sil_back_ordered`` IS initialised here, because
    ``copybooks/slwsinv.cob:L97-L98`` declares it (added 03/03/24, replacing an older
    filler) - but it has NO host variable and NO column.
    """
    return SilInvoiceLine(
        sil_key=SilKey(sil_invoice=0, sil_line=0),
        sil_product=" " * 13,
        sil_pa=" " * 2,
        sil_qty=0,
        sil_type=" ",
        sil_description=" " * 32,
        sil_net=Decimal("0.00"),
        sil_unit=Decimal("0.00"),
        sil_discount=Decimal("0.00"),
        sil_vat=Decimal("0.00"),
        sil_vat_code=0,
        sil_update=" ",
        # Declared, initialised, and never carried to any column.  See above.
        sil_back_ordered=" ",
    )


@dataclass(slots=True)
class InvoiceBuffer:
    """``WS-Invoice-Record`` - ONE record parameter for TWO tables.

    So the shared region is modelled ONCE, here, and the two views hold only their own
    remaining fields.
    """

    ws_sih_invoice: int = 0
    ws_sih_test: int = 0
    ws_invoice_record: SInvoiceHeader | None = None
    invoice_line: SilInvoiceLine | None = None
    # Mirrors of the bridge module's persistent state. They remain public for
    # compatibility with direct bridge callers, but a fresh linkage buffer no
    # longer owns or resets the bridge's connection/cursors.
    bridge_state: BridgeState = field(default_factory=lambda: BridgeState())
    connection: object = None

    @property
    def ws_invoice_key(self) -> str:
        """``03 WS-Invoice-Key.`` - the ten characters both PK columns hold."""
        return f"{self.ws_sih_invoice:08d}{self.ws_sih_test:02d}"

    def header_selected(self) -> bool:
        """Whether this buffer currently addresses the HEADER table."""
        return self.ws_sih_test == 0

    def select_header(self) -> SInvoiceHeader:
        """Address the header view, materialising it if the caller never set one.

        ``WS-Invoice-Record`` is 137 bytes of storage that always exists; the three
        redefinitions [copybooks/slwsinv2.cob:L27], [:L38], [:L91] are three ways of
        reading the SAME bytes, and an ``initialize`` leaves them zero and space rather
        than absent.
        """
        header = self.ws_invoice_record
        if header is None:
            header = _new_header_record()
            self.ws_invoice_record = header
        header.sih_prime.ws_invoice_key.sih_invoice = self.ws_sih_invoice
        header.sih_prime.ws_invoice_key.sih_test = self.ws_sih_test
        return header

    def select_line(self) -> SilInvoiceLine:
        """Address the line view, materialising it if the caller never set one.

        The counterpart of :meth:`select_header`, for the same reason.
        """
        line = self.invoice_line
        if line is None:
            line = _new_line_record()
            self.invoice_line = line
        line.sil_key.sil_invoice = self.ws_sih_invoice
        line.sil_key.sil_line = self.ws_sih_test
        return line

    def sync_key_into_views(self) -> None:
        """Propagate the shared ten bytes into whichever views are present.

        The COBOL needs no such step because the views literally overlay the same
        storage.
        """
        header = self.ws_invoice_record
        if header is not None:
            header.sih_prime.ws_invoice_key.sih_invoice = self.ws_sih_invoice
            header.sih_prime.ws_invoice_key.sih_test = self.ws_sih_test
        line = self.invoice_line
        if line is not None:
            line.sil_key.sil_invoice = self.ws_sih_invoice
            line.sil_key.sil_line = self.ws_sih_test

    def adopt_key_from_header(self) -> None:
        """Take the shared ten bytes FROM the header view."""
        header = self.ws_invoice_record
        if header is not None:
            key = header.sih_prime.ws_invoice_key
            self.ws_sih_invoice = key.sih_invoice
            self.ws_sih_test = key.sih_test

    def adopt_key_from_line(self) -> None:
        """Take the shared ten bytes FROM the line view."""
        line = self.invoice_line
        if line is not None:
            self.ws_sih_invoice = line.sil_key.sil_invoice
            self.ws_sih_test = line.sil_key.sil_line


@dataclass(slots=True)
class BridgeState:
    """The bridge's Working-Storage that survives between calls.

    Everything here is declared in ``slinvoiceMT``'s Working-Storage and is stateful
    ACROSS calls, which is why it lives in one object the caller keeps rather than in
    locals. There is no thread-safety machinery of any kind.
    """

    ws_last_read_invoice: int = 0
    ws_last_read_line: int = 40
    #: ``01 WS-Actual-Lines-In-Row pic 99 value zero.`` [:L288] - the header's own line
    #: count, cached by the unload so the line walk knows when to stop.
    ws_actual_lines_in_row: int = 0

    #: N-deadfields. ``01 WS-Body-Key pic x(9). *> Not used``
    #: [common/slinvoiceMT.cbl:L348]. Declared and never referenced anywhere in the
    #: bridge.
    ws_body_key: str = " " * 9

    most_relation: str = ""
    ws_where: str = ""
    ws_where_2: str = ""

    td_sainvoice_rec: TdSainvoiceRec = field(default_factory=TdSainvoiceRec)
    td_sainv_lines_rec: TdSainvLinesRec = field(default_factory=TdSainvLinesRec)

    ws_invoice_line: WsInvoiceLine = field(default_factory=WsInvoiceLine)

    #: N-two-cursors. ``Most-Cursor-Set`` [:L331] and ``Most-Cursor-Set-2`` [:L334] are
    #: TWO independent cursors with their own ``88`` pairs, and they are never
    #: collapsed.
    cursors: CursorStateTable = field(default_factory=CursorStateTable)

    save_result_rows: tuple[Mapping[str, Any], ...] = ()
    save_count_rows: int = 0
    save_result_rows_rg1: tuple[Mapping[str, Any], ...] = ()
    save_count_rows_rg1: int = 0

    def header_cursor(self) -> CursorState:
        """``Most-Cursor-Set`` - the ``SAINVOICE-REC`` cursor [:L331-L333]."""
        return self.cursors.state_for(HEADER_TABLE, _HEADER_SLOT)

    def line_cursor(self) -> CursorState:
        """``Most-Cursor-Set-2`` - the ``SAINV-LINES-REC`` cursor [:L334-L336]."""
        return self.cursors.state_for(LINES_TABLE, _LINE_SLOT)


_BRIDGE_STATE: BridgeState = BridgeState()
_BRIDGE_CONNECTION: object = None
_BRIDGE_TRANSPORT: TransportSecurity | None = None
_TRANSPORT_NOT_SUPPLIED: Final[object] = object()


def reset_bridge_storage(
    *,
    transport: TransportSecurity | None = None,
) -> None:
    """Discard acas016/slinvoiceMT working storage, as ending the run unit does."""
    global _BRIDGE_CONNECTION, _BRIDGE_STATE, _BRIDGE_TRANSPORT

    if _BRIDGE_CONNECTION is not None:
        mysql_1980_close(_BRIDGE_CONNECTION)  # type: ignore[arg-type]
    _BRIDGE_CONNECTION = None
    _BRIDGE_STATE = BridgeState()
    _BRIDGE_TRANSPORT = transport
    _LINKAGE_BUFFERS.clear()


_SIH_ORDER_WIDTH: Final[int] = int(
    loader.copybook_field_for("SAINVOICE-REC.IH-ORDER").character_length or 0
)
_SIH_FREQ_WIDTH: Final[int] = int(
    loader.copybook_field_for("SInvoice-Header.sih-Freq").character_length or 0
)
_SIH_REPEAT_DIGITS: Final[int] = int(
    loader.copybook_field_for("SInvoice-Header.sih-Repeat").digits or 0
)
_SIH_FILLER_37_WIDTH: Final[int] = int(
    loader.copybook_field_for("SInvoice-Header.filler#37").character_length or 0
)
_SIH_LAST_DATE_BYTES: Final[int] = 4
_SIH_LAST_DATE_MASK: Final[int] = (1 << (8 * _SIH_LAST_DATE_BYTES)) - 1

# The four members must tile the field they redefine exactly.
if (
    _SIH_FREQ_WIDTH + _SIH_REPEAT_DIGITS + _SIH_FILLER_37_WIDTH + _SIH_LAST_DATE_BYTES
) != _SIH_ORDER_WIDTH:
    _MSG: Final[str] = (
        "filler redefines sih-order [copybooks/slwsinv.cob:L28-L38] must tile "
        f"sih-order [:L27] exactly: {_SIH_FREQ_WIDTH} + {_SIH_REPEAT_DIGITS} + "
        f"{_SIH_FILLER_37_WIDTH} + {_SIH_LAST_DATE_BYTES} != {_SIH_ORDER_WIDTH}"
    )
    raise loader.DictionaryLookupError(_MSG)


def _order_overlay_is_blank(view: SihOrderView) -> bool:
    """Is the autogen overlay still at the state ``INITIALIZE`` leaves it in?

    The test is what makes correction C1 safe rather than sweeping.
    """
    return (
        view.sih_freq == " " * _SIH_FREQ_WIDTH
        and view.sih_repeat == 0
        and view.filler_37 == " " * _SIH_FILLER_37_WIDTH
        and view.sih_last_date == 0
    )


def _blank_order_overlay(view: SihOrderView) -> None:
    """Blank the overlay, because blanking ``sih-order`` blanks it in COBOL.

    ``initialize WS-Invoice-Record.`` [common/slinvoiceMT.cbl:L1496] is the PLAIN form,
    which does not descend into a FILLER item - but it does name ``sih-order``
    [copybooks/slwsinv.cob:L27], and the unnamed ``filler redefines sih-order`` [:L28]
    occupies exactly those bytes, so the compiled program blanks the overlay whether
    ``INITIALIZE`` walked into it or not.
    """
    view.sih_freq = " " * _SIH_FREQ_WIDTH
    view.sih_repeat = 0
    view.filler_37 = " " * _SIH_FILLER_37_WIDTH
    view.sih_last_date = 0


def _project_order_overlay_into_base(prime: SihPrime) -> None:
    """Make the overlay's bytes visible through ``sih-order``.

    * ``sih-Freq pic x`` [copybooks/slwsinv.cob:L29] - one character. * ``sih-Repeat pic
    99`` [:L36] - two ZONED digits, so the integer is rendered zero-padded; a
    ``DISPLAY`` field stores its digits as characters.

    Args:
        prime: ``02 sih-prime.`` [copybooks/slwsinv.cob:L19], mutated in place -
            ``sih_order`` is rewritten from ``filler_28`` when the latter carries
            anything.
    """
    view = prime.filler_28
    if _order_overlay_is_blank(view):
        return
    freq = view.sih_freq.ljust(_SIH_FREQ_WIDTH)[:_SIH_FREQ_WIDTH]
    # `pic 99` is DISPLAY: the digits ARE the bytes.
    repeat = f"{int(view.sih_repeat):0{_SIH_REPEAT_DIGITS}d}"[-_SIH_REPEAT_DIGITS:]
    filler = view.filler_37.ljust(_SIH_FILLER_37_WIDTH)[:_SIH_FILLER_37_WIDTH]
    # A `binary-long` field IS four bytes, so a value outside its range keeps only the
    # low four bytes rather than raising - `to_bytes` alone would raise `OverflowError`,
    # and this module's contract is that a verb returns a status pair and never
    # propagates an exception.
    stored = int(view.sih_last_date) & _SIH_LAST_DATE_MASK
    last_date = stored.to_bytes(_SIH_LAST_DATE_BYTES, "big", signed=False).decode(
        "latin-1"
    )
    prime.sih_order = f"{freq}{repeat}{filler}{last_date}"[:_SIH_ORDER_WIDTH]


def bb000_hv_load(state: BridgeState, buffer: InvoiceBuffer) -> None:
    """``bb000-HV-Load Section.`` [common/slinvoiceMT.cbl:L1445-L1486].

    N-punctuation. The punctuation is irregular: [:L1455], [:L1457] and [:L1458] each
    end with a period mid-block, then [:L1459] onward run unpunctuated to [:L1486] -
    four statement groups where one would do.
    """
    header = buffer.select_header()
    group = state.td_sainvoice_rec
    group.initialize()

    prime = header.sih_prime
    sub = header.sih_sub_prime
    fig = sub.sih_fig

    group.move_in("SINVOICE-KEY", buffer.ws_invoice_key)
    group.move_in("IH-INVOICE", prime.ws_invoice_key.sih_invoice)
    group.move_in("IH-TEST", prime.ws_invoice_key.sih_test)
    customer = prime.sih_customer
    group.move_in("IH-CUSTOMER", f"{customer.sih_nos:<6.6}{customer.sih_check:1d}")
    group.move_in("IH-DAT", prime.sih_date)
    _project_order_overlay_into_base(prime)
    group.move_in("IH-ORDER", prime.sih_order)
    group.move_in("IH-TYPE", prime.sih_type)
    group.move_in("IH-REF", prime.sih_ref)
    group.move_in("IH-DESCRIPTION", sub.sih_description)
    # L1465-L1472 the eight COMP-3 money fields.
    group.move_in("IH-P-C", fig.sih_p_c)
    group.move_in("IH-NET", fig.sih_net)
    group.move_in("IH-EXTRA", fig.sih_extra)
    group.move_in("IH-CARRIAGE", fig.sih_carriage)
    group.move_in("IH-VAT", fig.sih_vat)
    group.move_in("IH-DISCOUNT", fig.sih_discount)
    group.move_in("IH-E-VAT", fig.sih_e_vat)
    group.move_in("IH-C-VAT", fig.sih_c_vat)
    group.move_in("IH-STATUS", sub.sih_status)
    group.move_in("IH-STATUS-P", sub.sih_status_p)
    group.move_in("IH-STATUS-L", sub.sih_status_l)
    group.move_in("IH-STATUS-C", sub.sih_status_c)
    group.move_in("IH-STATUS-A", sub.sih_status_a)
    group.move_in("IH-STATUS-I", sub.sih_status_i)
    group.move_in("IH-LINES", sub.sih_lines)
    group.move_in("IH-DEDUCT-DAYS", sub.sih_deduct_days)
    group.move_in("IH-DEDUCT-AMT", sub.sih_deduct_amt)
    group.move_in("IH-DEDUCT-VAT", sub.sih_deduct_vat)
    group.move_in("IH-DAYS", sub.sih_days)
    group.move_in("IH-CR", sub.sih_cr)
    group.move_in("IH-DAY-BOOK-FLAG", sub.sih_day_book_flag)
    group.move_in("IH-UPDATE", sub.sih_update)


def bb100_unload_hvs(state: BridgeState, buffer: InvoiceBuffer) -> None:
    """``bb100-UnloadHVs Section.`` [common/slinvoiceMT.cbl:L1491-L1538].

    N-header-key-not-unloaded. ``HV-SINVOICE-KEY`` is loaded at [:L1455] and
    reconstructed only from its two components. The generated dictionary agrees:
    ``SAINVOICE-REC.SINVOICE-KEY`` has ``unloaded_to_record`` False and
    ``unload_source`` None. The asymmetry is preserved, not completed.
    """
    header = buffer.select_header()
    group = state.td_sainvoice_rec
    prime = header.sih_prime
    sub = header.sih_sub_prime
    fig = sub.sih_fig

    _initialize_header_record(header)

    prime.ws_invoice_key.sih_invoice = int(group["IH-INVOICE"])
    prime.ws_invoice_key.sih_test = int(group["IH-TEST"])
    customer_text = str(group["IH-CUSTOMER"]).ljust(7)[:7]
    prime.sih_customer.sih_nos = customer_text[:6]
    prime.sih_customer.sih_check = _digit_or_zero(customer_text[6:7])
    prime.sih_date = int(group["IH-DAT"])
    prime.sih_order = str(group["IH-ORDER"])
    prime.sih_type = int(group["IH-TYPE"])
    prime.sih_ref = str(group["IH-REF"])
    sub.sih_description = str(group["IH-DESCRIPTION"])
    fig.sih_p_c = _decimal_of(group["IH-P-C"])
    fig.sih_net = _decimal_of(group["IH-NET"])
    fig.sih_extra = _decimal_of(group["IH-EXTRA"])
    fig.sih_carriage = _decimal_of(group["IH-CARRIAGE"])
    fig.sih_vat = _decimal_of(group["IH-VAT"])
    fig.sih_discount = _decimal_of(group["IH-DISCOUNT"])
    fig.sih_e_vat = _decimal_of(group["IH-E-VAT"])
    fig.sih_c_vat = _decimal_of(group["IH-C-VAT"])
    sub.sih_status = str(group["IH-STATUS"])
    sub.sih_status_p = str(group["IH-STATUS-P"])
    sub.sih_status_l = str(group["IH-STATUS-L"])
    sub.sih_status_c = str(group["IH-STATUS-C"])
    sub.sih_status_a = str(group["IH-STATUS-A"])
    sub.sih_status_i = str(group["IH-STATUS-I"])
    sub.sih_lines = int(group["IH-LINES"])
    sub.sih_deduct_days = int(group["IH-DEDUCT-DAYS"])
    sub.sih_deduct_amt = _decimal_of(group["IH-DEDUCT-AMT"])
    sub.sih_deduct_vat = _decimal_of(group["IH-DEDUCT-VAT"])
    sub.sih_days = int(group["IH-DAYS"])
    sub.sih_cr = int(group["IH-CR"])
    sub.sih_day_book_flag = str(group["IH-DAY-BOOK-FLAG"])
    sub.sih_update = str(group["IH-UPDATE"])

    buffer.adopt_key_from_header()
    buffer.sync_key_into_views()

    # L1529-L1531, verbatim: *> THIS BLOCK SPECIAL FOR THIS DAL AS IT ALSO processes a
    # RG.
    state.ws_actual_lines_in_row = _move_to_actual_lines_in_row(int(group["IH-LINES"]))
    state.ws_last_read_invoice = int(group["IH-INVOICE"])
    # L1538 move HV-IH-TEST to WS-Last-Read-Line. *> should be zero N-lines-cursor-from-
    # ih-test.
    state.ws_last_read_line = int(group["IH-TEST"])


def _initialize_header_record(header: SInvoiceHeader) -> None:
    """``initialize WS-Invoice-Record.`` for the header view [:L1496]."""
    prime = header.sih_prime
    prime.ws_invoice_key.sih_invoice = 0
    prime.ws_invoice_key.sih_test = 0
    prime.sih_customer.sih_nos = " " * 6
    prime.sih_customer.sih_check = 0
    prime.sih_date = 0
    prime.sih_order = " " * 10
    _blank_order_overlay(prime.filler_28)
    prime.sih_type = 0
    prime.sih_ref = " " * 10
    sub = header.sih_sub_prime
    sub.sih_description = " " * 32
    zero_money = Decimal("0.00")
    fig = sub.sih_fig
    fig.sih_p_c = zero_money
    fig.sih_net = zero_money
    fig.sih_extra = zero_money
    fig.sih_carriage = zero_money
    fig.sih_vat = zero_money
    fig.sih_discount = zero_money
    fig.sih_e_vat = zero_money
    fig.sih_c_vat = zero_money
    sub.sih_status = " "
    sub.sih_status_p = " "
    sub.sih_status_l = " "
    sub.sih_status_c = " "
    sub.sih_status_a = " "
    sub.sih_status_i = " "
    sub.sih_lines = 0
    sub.sih_deduct_days = 0
    sub.sih_deduct_amt = zero_money
    sub.sih_deduct_vat = zero_money
    sub.sih_days = 0
    sub.sih_cr = 0
    sub.sih_day_book_flag = " "
    sub.sih_update = " "


def _initialize_line_record(line: SilInvoiceLine) -> None:
    """``initialize`` the line view IN PLACE - every field zero or space.

    The in-place counterpart of :func:`_new_line_record`, needed because the caller
    holds a reference to the view object.
    """
    line.sil_key.sil_invoice = 0
    line.sil_key.sil_line = 0
    line.sil_product = " " * 13
    line.sil_pa = " " * 2
    line.sil_qty = 0
    line.sil_type = " "
    line.sil_description = " " * 32
    zero_money = Decimal("0.00")
    line.sil_net = zero_money
    line.sil_unit = zero_money
    line.sil_discount = zero_money
    line.sil_vat = zero_money
    line.sil_vat_code = 0
    line.sil_update = " "
    # Declared, initialised, and never carried to any column - see `_new_line_record`'s
    # N-back-ordered-dropped note.
    line.sil_back_ordered = " "


def _initialise_ws_invoice_record(buffer: InvoiceBuffer) -> None:
    """``initialise WS-Invoice-Record.`` - the WHOLE 137-byte linkage area.

    - the ``STRING`` runs AFTER the ``INITIALIZE`` and reads ``WS-Invoice-Key``, so the
    logged text is the ten ZERO characters and not the key that was just searched for.

    Args:
        buffer: The linkage record area, mutated in place.
    """
    # The shared ten bytes first, so the two `select_*` calls below carry the cleared
    # key into whichever views the caller supplied.
    buffer.ws_sih_invoice = 0
    buffer.ws_sih_test = 0
    _initialize_header_record(buffer.select_header())
    _initialize_line_record(buffer.select_line())


def _digit_or_zero(text: str) -> int:
    """A single ``PIC 9`` read out of a group move, defaulting to zero.

    ``sih-check pic 9`` [copybooks/slwsinv.cob:L25] is the last byte of the 7-character
    ``IH-CUSTOMER`` column.
    """
    stripped = text.strip()
    return int(stripped) if stripped.isdigit() else 0


def _decimal_of(held: str | int | Decimal) -> Decimal:
    """Read a money host variable back as an exact ``Decimal`` (rule R-2)."""
    if isinstance(held, Decimal):
        return held
    return Decimal(str(held))


_ACTUAL_LINES_IN_ROW_DIGITS: Final[int] = 2


def _move_to_actual_lines_in_row(value: int) -> int:
    """``move HV-IH-LINES to WS-Actual-Lines-In-Row.`` [common/slinvoiceMT.cbl:L1533].

    COBOL discards HIGH-ORDER digits on a move into a shorter numeric item, so a header
    carrying 100 lines stores **zero** here, 123 stores 23, and 99 stores 99.

    Args:
        value: What the host variable holds - the ``IH-LINES`` column's value.

    Returns:
        The two digits the receiving field keeps.
    """
    magnitude = -value if value < 0 else value
    return magnitude % 10**_ACTUAL_LINES_IN_ROW_DIGITS


def _move_ws_invoice_record_to_ws_invoice_line(
    state: BridgeState, buffer: InvoiceBuffer
) -> None:
    """``move WS-Invoice-Record to WS-Invoice-Line.`` [:L2523] and [:L2726].

    The bridge stages line data through its own Working-Storage record rather than
    working from the shared buffer directly, and it does so with named ``MOVE``
    statements at exactly two sites: ``bc070-Process-Write``
    [common/slinvoiceMT.cbl:L2523] and ``bc090-Process-Rewrite`` [:L2726].
    """
    line_view = buffer.invoice_line
    staged = state.ws_invoice_line
    staged.ws_sil_invoice = buffer.ws_sih_invoice
    staged.ws_sil_line = buffer.ws_sih_test
    if line_view is None:
        # A caller that set only the key has still addressed a line.
        return
    staged.ws_sil_product = line_view.sil_product
    staged.ws_sil_pa = line_view.sil_pa
    staged.ws_sil_qty = line_view.sil_qty
    staged.ws_sil_type = line_view.sil_type
    staged.ws_sil_description = line_view.sil_description
    staged.ws_sil_net = line_view.sil_net
    staged.ws_sil_unit = line_view.sil_unit
    staged.ws_sil_discount = line_view.sil_discount
    staged.ws_sil_vat = line_view.sil_vat
    staged.ws_sil_vat_code = line_view.sil_vat_code
    staged.ws_sil_update = line_view.sil_update
    # N-back-ordered-dropped. sil_back_ordered lands on the bridge's bare `filler pic x`
    # [common/slinvoiceMT.cbl:L377] and goes no further: there is no HV1- host variable
    # and no IL-BACK-ORDERED column.
    staged.filler_80 = line_view.sil_back_ordered


def _move_ws_invoice_line_to_ws_invoice_record(
    state: BridgeState, buffer: InvoiceBuffer
) -> None:
    """``move WS-Invoice-Line to WS-Invoice-Record.`` [:L2499] and [:L2842].

    The reverse staging copy, at ``bc051-Fetch-RG1`` [common/slinvoiceMT.cbl:L2499] and
    at the very end of ``bc100-UnloadHVs-rg1`` [:L2842] - the line record is copied OVER
    the shared buffer after every unload, so the caller reads its line out of the same
    area a header would have arrived in.
    """
    staged = state.ws_invoice_line
    buffer.ws_sih_invoice = staged.ws_sil_invoice
    buffer.ws_sih_test = staged.ws_sil_line
    line_view = buffer.invoice_line
    if line_view is None:
        line_view = SilInvoiceLine(
            sil_key=_new_sil_key(staged.ws_sil_invoice, staged.ws_sil_line),
            sil_product=staged.ws_sil_product,
            sil_pa=staged.ws_sil_pa,
            sil_qty=staged.ws_sil_qty,
            sil_type=staged.ws_sil_type,
            sil_description=staged.ws_sil_description,
            sil_net=staged.ws_sil_net,
            sil_unit=staged.ws_sil_unit,
            sil_discount=staged.ws_sil_discount,
            sil_vat=staged.ws_sil_vat,
            sil_vat_code=staged.ws_sil_vat_code,
            sil_update=staged.ws_sil_update,
            sil_back_ordered=staged.filler_80,
        )
        buffer.invoice_line = line_view
        buffer.sync_key_into_views()
        return
    line_view.sil_key.sil_invoice = staged.ws_sil_invoice
    line_view.sil_key.sil_line = staged.ws_sil_line
    line_view.sil_product = staged.ws_sil_product
    line_view.sil_pa = staged.ws_sil_pa
    line_view.sil_qty = staged.ws_sil_qty
    line_view.sil_type = staged.ws_sil_type
    line_view.sil_description = staged.ws_sil_description
    line_view.sil_net = staged.ws_sil_net
    line_view.sil_unit = staged.ws_sil_unit
    line_view.sil_discount = staged.ws_sil_discount
    line_view.sil_vat = staged.ws_sil_vat
    line_view.sil_vat_code = staged.ws_sil_vat_code
    line_view.sil_update = staged.ws_sil_update
    # Still the bridge's `filler pic x` - never a column.
    line_view.sil_back_ordered = staged.filler_80
    buffer.sync_key_into_views()


def _new_sil_key(invoice: int, line: int) -> Any:
    """Build a ``sil-Key`` group [copybooks/slwsinv.cob:L82] for a fresh line view."""
    from acas_posting.records.sales_invoice import SilKey

    return SilKey(sil_invoice=invoice, sil_line=line)


def _initialise_ws_invoice_line(state: BridgeState) -> None:
    """``initialise WS-Invoice-Line`` [common/slinvoiceMT.cbl:L2501] and [:L2820].

    while [:L2820] and every other site in the bridge use ``initialize``. GnuCOBOL
    accepts both spellings, so the divergence is cosmetic - and it is recorded rather
    than normalised, because it is evidence of two editing sessions.
    """
    state.ws_invoice_line = WsInvoiceLine()


def bc000_hv_load_rg1(state: BridgeState) -> None:
    """``bc000-HV-Load-rg1 Section. *> Dry chk ?`` [common/slinvoiceMT.cbl:L2776-L2802].

    N-triple-key-materialisation. ``WS-Sil-Key`` - the 10-byte group - feeds ``HV1-IL-
    LINE-KEY`` at [:L2789] while its two components feed ``HV1-IL-INVOICE`` and
    ``HV1-IL-LINE`` separately, so the key is stored three times in one row here too.
    """
    group = state.td_sainv_lines_rec
    staged = state.ws_invoice_line

    group.initialize()

    group.move_in("IL-LINE-KEY", staged.ws_sil_key)
    group.move_in("IL-LINE", staged.ws_sil_line)
    # L2791 move WS-Sil-Invoice to HV1-IL-INVOICE N-il-invoice-never-unloaded starts
    # here: this host variable IS loaded, and bc100-UnloadHVs-rg1 [:L2822-L2834] never
    # reads it back.
    group.move_in("IL-INVOICE", staged.ws_sil_invoice)
    group.move_in("IL-PRODUCT", staged.ws_sil_product)
    group.move_in("IL-PA", staged.ws_sil_pa)
    group.move_in("IL-QTY", staged.ws_sil_qty)
    group.move_in("IL-TYPE", staged.ws_sil_type)
    group.move_in("IL-DESCRIPTION", staged.ws_sil_description)
    group.move_in("IL-NET", staged.ws_sil_net)
    group.move_in("IL-UNIT", staged.ws_sil_unit)
    group.move_in("IL-DISCOUNT", staged.ws_sil_discount)
    group.move_in("IL-VAT", staged.ws_sil_vat)
    group.move_in("IL-VAT-CODE", staged.ws_sil_vat_code)
    group.move_in("IL-UPDATE", staged.ws_sil_update)


def bc100_unload_hvs_rg1(state: BridgeState, buffer: InvoiceBuffer) -> None:
    """``bc100-UnloadHVs-rg1 Section. *> Dry chk ?`` [common/slinvoiceMT.cbl:L2810-L2842].

    module.** Count the moves: the load does FOURTEEN [:L2789-L2802], the unload does
    THIRTEEN [:L2822-L2834]. ``HV1-IL-INVOICE`` is loaded at [:L2791] and appears
    NOWHERE in the unload.
    """
    group = state.td_sainv_lines_rec

    _initialise_ws_invoice_line(state)
    staged = state.ws_invoice_line

    key_text = str(group["IL-LINE-KEY"]).strip().rjust(10, "0")[:10]
    staged.ws_sil_invoice = _digits_or_zero(key_text[:8])
    staged.ws_sil_line = _digits_or_zero(key_text[8:10])
    staged.ws_sil_line = int(group["IL-LINE"])
    staged.ws_sil_product = str(group["IL-PRODUCT"])
    staged.ws_sil_pa = str(group["IL-PA"])
    staged.ws_sil_qty = int(group["IL-QTY"])
    staged.ws_sil_type = str(group["IL-TYPE"])
    staged.ws_sil_description = str(group["IL-DESCRIPTION"])
    staged.ws_sil_net = _decimal_of(group["IL-NET"])
    staged.ws_sil_unit = _decimal_of(group["IL-UNIT"])
    staged.ws_sil_discount = _decimal_of(group["IL-DISCOUNT"])
    staged.ws_sil_vat = _decimal_of(group["IL-VAT"])
    staged.ws_sil_vat_code = int(group["IL-VAT-CODE"])
    staged.ws_sil_update = str(group["IL-UPDATE"])

    state.ws_last_read_line = int(group["IL-LINE"])

    _move_ws_invoice_line_to_ws_invoice_record(state, buffer)


def _digits_or_zero(text: str) -> int:
    """Read a fixed-width numeric slice of a group move, defaulting to zero.

    A ``PIC 9(n)`` region read out of a ten-byte group move can legitimately hold spaces
    before anything has been written to it, and COBOL reads that as zero rather than
    failing. Silent, because the COBOL is silent.
    """
    stripped = text.strip()
    return int(stripped) if stripped.isdigit() else 0


_HEADER_TABLE_SQL: Final[str] = quote_identifier(HEADER_TABLE)
_LINES_TABLE_SQL: Final[str] = quote_identifier(LINES_TABLE)

_HEADER_KEY_SQL: Final[str] = quote_identifier(HEADER_KEY_COLUMN)
_LINES_KEY_SQL: Final[str] = quote_identifier(LINES_KEY_COLUMN)


def _select_all(table_sql: str, where: str) -> str:
    """``SELECT * FROM <table> WHERE <where>;`` - the bridge's own shape.

    Verified at ``ba040-Process-Read-Next`` [common/slinvoiceMT.cbl:L660-L672],
    ``ba050`` [:L860], ``ba060`` header [:L1010] and RG1 [:L1080], and ``bc050``
    [:L2412].
    """
    return f"SELECT * FROM {table_sql} WHERE {where};"


def _delete_from(table_sql: str, where: str) -> str:
    """``DELETE FROM <table> WHERE <where>`` - with NO trailing semicolon.

    The bridge terminates its DELETE text with ``X"00"`` alone - ``ba080-Process-
    Delete`` [common/slinvoiceMT.cbl:L1216-L1222], ``ba085`` [:L1320], ``bc080``
    [:L2596] and ``bc085`` [:L2688] - while its SELECT, INSERT and UPDATE all carry
    ``";"`` before the null terminator.
    """
    return f"DELETE FROM {table_sql} WHERE {where}"


def _insert_statement(
    table_sql: str, bindings: tuple[ColumnBinding, ...]
) -> str:
    r"""``INSERT INTO <table> SET \`COL\`=%s, ... ;`` - the bridge's ``SET`` form.

    Every column is named - all 31 for the header, all 14 for the lines - because the
    group was ``INITIALIZE``d before the load and every column is ``NOT NULL`` with no
    ``DEFAULT``.
    """
    assignments = ", ".join(f"{b.quoted_column_name}=%s" for b in bindings)
    return f"INSERT INTO {table_sql} SET {assignments};"


def _update_statement(
    table_sql: str, bindings: tuple[ColumnBinding, ...], where: str
) -> str:
    r"""``UPDATE <table> SET \`COL\`=%s, ... WHERE <where>;``.

    ``bb300-Update`` [common/slinvoiceMT.cbl:L1949-L2356] and ``bc300-Update-rg1``
    [:L3042-L3236] emit the SAME column order as their INSERT counterparts - verified by
    extracting every ``'`COL`='`` literal from all four paragraphs - and then append ``"
    WHERE " FUNCTION TRIM (WS-Where (1:J)) ";"``.
    """
    assignments = ", ".join(f"{b.quoted_column_name}=%s" for b in bindings)
    return f"UPDATE {table_sql} SET {assignments} WHERE {where};"


_HEADER_INSERT_SQL: Final[str] = _insert_statement(_HEADER_TABLE_SQL, HEADER_COLUMNS)
#: ``bc200-Insert-rg1`` - 14 columns in ordinal order. Note the LOAD inverts INVOICE and
#: LINE [common/slinvoiceMT.cbl:L2790-L2791] but the STATEMENT does not.
_LINES_INSERT_SQL: Final[str] = _insert_statement(_LINES_TABLE_SQL, LINE_COLUMNS)


def _equality_where(key_sql: str) -> str:
    r"""``\`KeyName\`=%s`` - the exact-match clause.

    AAP section 0.1.1 on the START condition, quoted through
    :mod:`acas_posting.dal.cursor_state`: *"The START condition cannot be compounded"* -
    EXACTLY ONE predicate on EXACTLY ONE column, never an ``AND``.
    """
    return f"{key_sql}=%s"


def _start_where(key_sql: str, relation: str, *, quote_value: bool) -> str:
    r"""``\`KeyName\` <rel> %s ORDER BY \`KeyName\` ASC`` - the START clause.

    The header form ``[common/slinvoiceMT.cbl:L987-L1002]`` wraps the value in ``'"'``
    on both sides. The RG1 form ``[common/slinvoiceMT.cbl:L1061-L1072]`` is real and is
    reproduced through ``quote_value``.
    """
    del quote_value
    operator = relation.split(" ", 1)[0]
    # ' ASC' at [common/slinvoiceMT.cbl:L651] for ba040 carries no trailing spaces while
    # ' ASC ' at [:L999] and [:L1070] carries two.
    return f"{key_sql}{operator}%s ORDER BY {key_sql} ASC"


def _sequential_start_where(key_sql: str) -> str:
    r"""``\`KeyName\` >= %s ORDER BY \`KeyName\` ASC`` with the low key.

    ``acas_posting.dal.cursor_state.SEQUENTIAL_READ_START`` already records the relation
    and the low key for ``SAINVOICE-REC``, cited to [:L646] and [:L647], which is where
    they are taken from rather than retyped.
    """
    return f"{key_sql} {_SEQUENTIAL_RELATION} %s ORDER BY {key_sql} ASC"


def _delete_all_lines_where() -> str:
    """The clear-down clause for ``bc085`` - and it can never match a row.

    N-bc085-string-constant-predicate. The identifier is written ``"'IL-INVOICE'"`` -
    **single quotes, so a STRING LITERAL, not a backtick identifier**. The generated
    predicate is therefore ``'IL-INVOICE' = '00012345'``.
    """
    # '="' is 'delimited by size' [common/slinvoiceMT.cbl:L2669], so no spaces surround
    # the operator, and the closing '"' at [:L2671] closes the value - which is bound
    # here rather than interpolated.
    return "'IL-INVOICE'=%s"


@dataclass(frozen=True, slots=True)
class StatementOutcome:
    """The result of one bridge statement - a status PAIR, never an exception.

    That single comment is the contract for this whole module, and it is why nothing
    here raises: :func:`acas_posting.dal.status.raise_for_status` exists but is opt-in
    and is deliberately never called.
    """

    statement: str
    parameters: tuple[object, ...]
    fs_reply: int = int(FsReply.SUCCESS)
    we_error: int = int(WeError.SUCCESS)
    sql_err: str = ""
    sql_msg: str = ""
    sql_state: str = ""
    count_rows: int = 0
    #: Rows as POSITIONAL tuples, not mappings. This is deliberate and is the faithful
    #: shape.
    rows: tuple[tuple[object, ...], ...] = ()

    @property
    def succeeded(self) -> bool:
        """True when the COBOL would regard the call as clean."""
        return self.fs_reply == int(FsReply.SUCCESS)


def _run_command(
    connection: object,
    logging_data: LoggingData,
    statement: str,
    parameters: Sequence[object],
    *,
    fetch: bool,
    delete_we_error: int = int(WeError.SUCCESS),
) -> StatementOutcome:
    """``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` plus the errno check.

    Every bridge paragraph that touches the database follows one shape, verified
    identical at ``bb200-Insert`` [common/slinvoiceMT.cbl:L1930-L1946], ``bb300-Update``
    [:L2340-L2356], ``bc200-Insert-rg1`` [:L3023-L3039], ``bc300-Update-rg1``
    [:L3220-L3236] and every read paragraph.
    """
    bound = tuple(parameters)
    logging_data.ws_log_where = sanitise_for_log(statement)
    try:
        with execute_statement(connection, statement, bound) as cursor:  # type: ignore[arg-type]
            if fetch:
                # [common/slinvoiceMT.cbl:L668-L671]. The bridge materialises the whole
                # result set and then walks it.
                fetched = cursor.fetchall()
                rows = tuple(tuple(row) for row in (fetched or ()))
                return StatementOutcome(
                    statement=statement,
                    parameters=bound,
                    count_rows=len(rows),
                    rows=rows,
                )
            affected = cursor.rowcount
            return StatementOutcome(
                statement=statement,
                parameters=bound,
                count_rows=affected if affected and affected > 0 else 0,
            )
    except Exception as exc:  # noqa: BLE001 - the COBOL reports, it does not raise
        # 'call "MySQL_errno" using WS-MYSQL-Error-Number' and its siblings. The driver
        # surfaces the same three facts on its exception object.
        errno = getattr(exc, "errno", None)
        sql_state = getattr(exc, "sqlstate", None)
        message = getattr(exc, "msg", None) or str(exc)
        status = mysql_1100_db_error(
            errno="" if errno is None else str(errno),
            message=message,
            sql_state="" if sql_state is None else str(sql_state),
            command=statement,
            we_error=delete_we_error,
        )
        #  NO SECOND RECORD HERE.
        # :func:`acas_posting.dal.status.mysql_1100_db_error`, called on the line
        # above, IS the one operator record for a database failure - it is the
        # migration of `Mysql-1110-Report-Problem`
        # [copybooks/mysql-procedures.cpy:L130-L137], which the frozen bridge
        # reaches on every one - and it already carries the FS-Reply, the WE-Error,
        # the SQLSTATE, the errno and the stable category. Repeating them here made
        # one failure two records, so an operator counting failures counted twice
        # and a reader could not tell which record was authoritative.
        return StatementOutcome(
            statement=statement,
            parameters=bound,
            fs_reply=status.fs_reply,
            we_error=status.we_error,
            sql_err=status.sql_err[:SQL_ERR_WIDTH],
            sql_msg=status.sql_msg[:SQL_MSG_WIDTH],
            sql_state=status.sql_state[:SQL_STATE_WIDTH],
        )


def _apply_statement_status(ctx: "_BridgeContext", outcome: StatementOutcome) -> None:
    """Copy a statement's status pair onto ``File-Access`` and ``Logging-Data``.

    A CLEAN statement is not allowed to clear a status the caller already had, because
    ``ba010-Initialise`` deliberately does not clear ``We-Error`` or ``Fs-Reply``
    [common/slinvoiceMT.cbl:L502-L503]. So only a FAILING outcome writes here.
    """
    if outcome.fs_reply == int(FsReply.SUCCESS) and outcome.we_error == int(
        WeError.SUCCESS
    ):
        return
    ctx.file_access.fs_reply = outcome.fs_reply
    ctx.file_access.we_error = outcome.we_error
    logging_data = ctx.logging_data
    logging_data.sql_err = _truncate_move(outcome.sql_err, SQL_ERR_WIDTH)
    logging_data.sql_msg = _truncate_move(outcome.sql_msg, SQL_MSG_WIDTH)
    logging_data.sql_state = _truncate_move(outcome.sql_state, SQL_STATE_WIDTH)


def _fetch_into_group(
    group: _HostVariableGroup,
    bindings: tuple[ColumnBinding, ...],
    row: object,
) -> None:
    """Land one fetched row in its host-variable group, BY POSITION.

    This is ``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` followed by the host
    variables in order - 31 of them for the header [common/slinvoiceMT.cbl:L746-L780],
    14 for the lines [:L2476-L2491].
    """
    values = tuple(row) if isinstance(row, (tuple, list)) else ()
    for index, binding in enumerate(bindings):
        if index >= len(values):
            break
        group.move_in(binding.column_name, values[index])


def bb200_insert(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bb200-Insert Section.`` [common/slinvoiceMT.cbl:L1543]

    Writes the header row. All 31 columns are named, in TABLE ORDINAL order, because the
    group was ``INITIALIZE``d by :func:`bb000_hv_load` and every column is ``NOT NULL``
    with no ``DEFAULT`` - AAP section 0.6.2.
    """
    # NO 'move nn to ws-No-Paragraph' here. Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.
    parameters = state.td_sainvoice_rec.as_parameters()
    return _run_command(
        connection,
        logging_data,
        _HEADER_INSERT_SQL,
        parameters,
        fetch=False,
    )


def bb300_update(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bb300-Update Section.`` [common/slinvoiceMT.cbl:L1949]

    Rewrites the header row.
    """
    # NO 'move nn to ws-No-Paragraph' here. Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.
    where = _equality_where(_HEADER_KEY_SQL)
    statement = _update_statement(_HEADER_TABLE_SQL, HEADER_COLUMNS, where)
    parameters = (
        *state.td_sainvoice_rec.as_parameters(),
        # FUNCTION TRIM on the WHERE value.
        state.td_sainvoice_rec.render_one(HEADER_KEY_COLUMN),
    )
    return _run_command(connection, logging_data, statement, parameters, fetch=False)


def bc200_insert_rg1(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bc200-Insert-rg1 Section.`` [common/slinvoiceMT.cbl:L2849]

    Writes one line row. All 14 columns are named, in TABLE ORDINAL order - ``IL-
    INVOICE`` second, ``IL-LINE`` third - which is the opposite of the order
    :func:`bc000_hv_load_rg1` moves them in [common/slinvoiceMT.cbl:L2790-L2791].
    """
    # NO 'move nn to ws-No-Paragraph' here. Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.
    parameters = state.td_sainv_lines_rec.as_parameters()
    return _run_command(
        connection,
        logging_data,
        _LINES_INSERT_SQL,
        parameters,
        fetch=False,
    )


def bc300_update_rg1(
    connection: object, state: BridgeState, logging_data: LoggingData
) -> StatementOutcome:
    """``bc300-Update-rg1 Section.`` [common/slinvoiceMT.cbl:L3042]

    Rewrites one line row, same 14 columns in the same ordinal order as
    :func:`bc200_insert_rg1`, matched on ``IL-LINE-KEY``.
    """
    # NO 'move nn to ws-No-Paragraph' here. Verified by counting the moves in
    # [common/slinvoiceMT.cbl:L1543-L1948] (bb200), [:L1949-L2358] (bb300),
    # [:L2849-L3041] (bc200) and [:L3042-L3238] (bc300): ZERO in each.
    where = _equality_where(_LINES_KEY_SQL)
    statement = _update_statement(_LINES_TABLE_SQL, LINE_COLUMNS, where)
    parameters = (
        *state.td_sainv_lines_rec.as_parameters(),
        state.td_sainv_lines_rec.render_one(LINES_KEY_COLUMN),
    )
    return _run_command(connection, logging_data, statement, parameters, fetch=False)


@dataclass(slots=True)
class _BridgeContext:
    """What every bridge paragraph can see - the COBOL's shared storage.

    A COBOL paragraph reaches ``File-Access``, ``ACAS-DAL-Common-data`` and ``WS-
    Invoice-Record`` because they are Linkage, and reaches ``WS-Where``, the two host-
    variable groups and the cursor flags because they are Working-Storage.
    """

    connection: object
    file_access: FileAccess
    dal_common: AcasDalCommonData
    state: BridgeState
    buffer: InvoiceBuffer
    #: ``System-Record``. The bridge itself reads its credentials from the ``RDB-Data``
    #: block inside ``File-Access`` [copybooks/wsfnctn.cob:L56-L62], which is how
    #: ``ba020-Process-Open`` fills ``WS-MYSQL-BASE-NAME`` and its five siblings
    #: [common/slinvoiceMT.cbl:L574-L599].
    system_record: SystemRecord | None = None
    transport: TransportSecurity | None = None
    #: ``K``/``L`` - the key offset and length the current paragraph selected from
    #: ``KeyOfReference`` [common/slinvoiceMT.cbl:L305-L310]. Held on the context
    #: because the paragraphs genuinely share them.
    k: int = 1
    ell: int = 10
    k2: int = 1
    ell2: int = 10
    return_code: int = 0

    @property
    def logging_data(self) -> LoggingData:
        """``Logging-Data`` [copybooks/wsfnctn.cob:L44-L55], reached through File-Access.
        """
        return self.file_access.logging_data


def _key_of_reference(ctx: _BridgeContext, kor_x1: int) -> KeyOfReference:
    """``set KOR-x1 to n`` then ``move KOR-offset/KOR-length (KOR-x1) to K/L``.

    ``[common/slinvoiceMT.cbl:L296-L310]`` declares the two-entry table; every paragraph
    that builds a clause selects an entry and copies its offset and length.
    """
    # KOR-x1 is a COBOL INDEXED BY name, so it is 1-relative.
    entry = KEYS_OF_REFERENCE[kor_x1]
    if kor_x1 == 1:
        ctx.k, ctx.ell = entry.kor_offset, entry.kor_length
    else:
        # ba060 keeps the RG1 pair separately in K2/L2 [:L1057-L1058] because its header
        # block is still using K/L; every other rg1 paragraph reuses K/L.
        ctx.k2, ctx.ell2 = entry.kor_offset, entry.kor_length
        ctx.k, ctx.ell = entry.kor_offset, entry.kor_length
    return entry


def _record_key_slice(ctx: _BridgeContext, offset: int, length: int) -> str:
    """``WS-Invoice-Record (K:L)`` - a reference-modified slice of the buffer.

    Every clause value in this bridge is taken this way rather than from a named field,
    which is precisely why the union buffer works.
    """
    return ctx.buffer.ws_invoice_key[offset - 1 : offset - 1 + length]


def _move_to_ws_file_key(ctx: _BridgeContext, text: str) -> None:
    """``move <literal> to WS-File-Key`` - a MOVE into ``pic x(64)``.

    ``WS-File-Key`` is 64 characters [copybooks/wsfnctn.cob:L52], and a COBOL MOVE into
    an alphanumeric field left-justifies, pads with spaces and TRUNCATES anything
    longer.
    """
    ctx.logging_data.ws_file_key = _truncate_move(text, _WS_FILE_KEY_WIDTH)


def _move_to_ws_log_where(ctx: _BridgeContext, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - a MOVE into ``pic x(231)``."""
    ctx.logging_data.ws_log_where = _truncate_move(text, _WS_LOG_WHERE_WIDTH)


def ba010_initialise(ctx: _BridgeContext) -> None:
    """``ba010-Initialise.`` [common/slinvoiceMT.cbl:L498]

    N-noinit, SECOND INSTANCE. ``We-Error`` and ``Fs-Reply`` are commented OUT of the
    bridge's initialise, exactly as they are commented out of the handler's at
    [common/acas016.cbl:L287-L288].
    """
    logging_data = ctx.logging_data
    logging_data.sql_state = "0".ljust(SQL_STATE_WIDTH)
    # NOT cleared, deliberately: ctx.file_access.we_error and .fs_reply.
    # [common/slinvoiceMT.cbl:L502-L503] have them commented out. move spaces to WS-
    # MYSQL-Error-Message WS-MYSQL-Error-Number WS-Log-Where WS-File-Key SQL-Msg SQL-
    # Err. [:L505-L511].
    logging_data.ws_log_where = " " * _WS_LOG_WHERE_WIDTH
    logging_data.ws_file_key = " " * _WS_FILE_KEY_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = " " * SQL_ERR_WIDTH


def ba020_process_open(ctx: _BridgeContext) -> None:
    """``ba020-Process-Open.`` [common/slinvoiceMT.cbl:L568]

    The COBOL builds six null-terminated strings from ``DB-Schema``, ``DB-Host``, ``DB-
    UName``, ``DB-UPass``, ``DB-Port`` and ``DB-Socket``
    [common/slinvoiceMT.cbl:L574-L599] and then performs ``MYSQL-1000-OPEN THRU
    MYSQL-1090-EXIT``.
    """
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba020-Process-Open"]
    try:
        outcome = mysql_1000_open(
            ctx.system_record,
            ws_no_paragraph=logging_data.ws_no_paragraph,
            we_error=ctx.file_access.we_error,
            transport=ctx.transport,
            # slinvoiceMT keeps its own SQL state across CALLs. A live handle
            # owned by another bridge is not that state and must not be reused.
            reuse_process_connection=False,
        )
    except ConnectionPolicyError as refused:
        # A connection.py policy refusal. Rendered as the COBOL's failed-open status
        # rather than propagated, per [common/acas016.cbl:L627].
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = int(WeError.RDB_INIT_ERROR)
        logging_data.sql_err = " " * SQL_ERR_WIDTH
        logging_data.sql_msg = _truncate_move(
            sanitise_for_log(str(refused)), SQL_MSG_WIDTH
        )
        logging_data.sql_state = " " * SQL_STATE_WIDTH
        ctx.connection = None
        ba999_end(ctx)
        return
    outcome.apply_to_logging_data(logging_data)
    ctx.file_access.fs_reply = outcome.fs_reply
    ctx.file_access.we_error = outcome.we_error
    ctx.connection = outcome.connection
    if ctx.file_access.fs_reply != int(FsReply.SUCCESS):
        ba999_end(ctx)
        return
    _move_to_ws_file_key(ctx, "OPEN SL INVOICE")
    ctx.state.header_cursor().set_cursor_not_active()
    ba999_end(ctx)


def ba030_process_close(ctx: _BridgeContext) -> None:
    """``ba030-Process-Close.`` [common/slinvoiceMT.cbl:L610]

    Only the PRIMARY cursor is tested and freed. The RG1 cursor is not, because the
    paragraph that would free it - ``bc998-Free`` - is never called from anywhere; see
    :func:`bc998_free`. N-bc998-never-called.
    """
    logging_data = ctx.logging_data
    if ctx.state.header_cursor().cursor_active():
        ba998_free(ctx)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba030-Process-Close"]
    _move_to_ws_file_key(ctx, "CLOSE SL INVOICE")
    mysql_1980_close(ctx.connection)  # type: ignore[arg-type]
    ctx.connection = None
    ba999_end(ctx)


def ba040_process_read_next(ctx: _BridgeContext) -> None:
    """``ba040-Process-Read-Next.`` [common/slinvoiceMT.cbl:L624]

    Opens the walk ONLY when the cursor is not already active, then FALLS THROUGH into
    :func:`ba041_reread`.
    """
    logging_data = ctx.logging_data
    cursor = ctx.state.header_cursor()
    if cursor.cursor_not_active():
        entry = _key_of_reference(ctx, 1)
        where = _sequential_start_where(quote_identifier(entry.column_name))
        _move_to_ws_log_where(ctx, where)
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE[
            "ba040-Process-Read-Next"
        ]
        statement = _select_all(_HEADER_TABLE_SQL, where)
        outcome = _run_command(
            ctx.connection,
            logging_data,
            statement,
            (_SEQUENTIAL_LOW_KEY,),
            fetch=True,
        )
        _move_to_ws_file_key(ctx, _SEQUENTIAL_LOW_KEY)
        # TP-SAINVOICE-REC [common/slinvoiceMT.cbl:L669-L671]. The rows are POSITIONAL
        # tuples.
        stored = cursor.store_result(outcome.rows)  # type: ignore[arg-type]
        _apply_statement_status(ctx, outcome)
        if stored == 0:
            ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
            ctx.file_access.we_error = int(FsReply.END_OF_FILE)
            _move_to_ws_file_key(ctx, "No Data")
            ba999_end(ctx)
            return
        cursor.set_cursor_active()
        _move_to_ws_file_key(ctx, f"> 0 got cnt={stored} recs for INVOICE-REC Table")
        ba999_end(ctx)
    ba041_reread(ctx)


def ba041_reread(ctx: _BridgeContext) -> None:
    """``ba041-Reread.`` [common/slinvoiceMT.cbl:L706]"""
    logging_data = ctx.logging_data
    _move_to_ws_log_where(ctx, "")
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba041-Reread"]
    ctx.return_code = 0
    if ctx.state.ws_last_read_invoice == 0:
        ba042_fetch(ctx)
        return
    if ctx.file_access.file_function == int(FileFunction.READ_NEXT_HEADER):
        ba042_fetch(ctx)
        return
    if ctx.state.ws_last_read_line < ctx.state.ws_actual_lines_in_row:
        ctx.buffer.ws_sih_test = ctx.state.ws_last_read_line + 1
        ctx.buffer.ws_sih_invoice = ctx.state.ws_last_read_invoice
        ctx.buffer.sync_key_into_views()
        bc050_process_read_indexed(ctx)
        if ctx.file_access.fs_reply != int(FsReply.SUCCESS):
            _initialise_ws_invoice_record(ctx.buffer)
            _move_to_ws_file_key(ctx, f"{ctx.buffer.ws_invoice_key} Not Found")
            ba999_end(ctx)
            return
        ctx.state.ws_last_read_line = ctx.buffer.ws_sih_test
        ba999_end(ctx)
        return
    ba042_fetch(ctx)


def ba042_fetch(ctx: _BridgeContext) -> None:
    """``ba042-Fetch.`` [common/slinvoiceMT.cbl:L744]

    ``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` and then all 31 host variables
    BY POSITION [common/slinvoiceMT.cbl:L746-L780]. That operand list was extracted and
    diffed against the host-variable group declaration [:L391-L421]: IDENTICAL, and both
    equal the frozen column ordinal order.
    """
    logging_data = ctx.logging_data
    cursor = ctx.state.header_cursor()
    row = cursor.fetch_record()
    if row is None:
        ctx.return_code = -1
        ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
        ctx.file_access.we_error = int(FsReply.END_OF_FILE)
        _move_to_ws_file_key(ctx, "EOF")
        cursor.set_cursor_not_active()
        ba999_end(ctx)
        return
    if cursor.count_rows == 0:
        # initialize WS-Invoice-Record with filler [:L804] N-initialize: 'with filler'
        # HERE, plain at [:L1496]. Two semantics in one bridge.
        _initialise_ws_invoice_record(ctx.buffer)
        _move_to_ws_file_key(ctx, "EOF2")
        ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
        ctx.file_access.we_error = int(FsReply.END_OF_FILE)
        cursor.set_cursor_not_active()
        ba999_end(ctx)
        return
    if ctx.file_access.fs_reply == int(FsReply.END_OF_FILE):
        cursor.set_cursor_not_active()
        _move_to_ws_file_key(ctx, "EOF3")
        ba999_end(ctx)
        return
    _fetch_into_group(ctx.state.td_sainvoice_rec, HEADER_COLUMNS, row)
    bb100_unload_hvs(ctx.state, ctx.buffer)
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    ba999_end(ctx)


def ba050_process_read_indexed(ctx: _BridgeContext) -> None:
    """``ba050-Process-Read-Indexed.`` [common/slinvoiceMT.cbl:L824]

    ``WS-Sih-Test`` - the header record's own two-digit test field - is what decides
    WHICH TABLE is read. Non-zero means "this is a line".
    """
    logging_data = ctx.logging_data
    if ctx.buffer.ws_sih_test != 0:
        bc050_process_read_indexed(ctx)
        return
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE[
        "ba050-Process-Read-Indexed-select"
    ]
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_HEADER_TABLE_SQL, where),
        (key_value,),
        fetch=True,
    )
    cursor = ctx.state.header_cursor()
    stored = cursor.store_result(outcome.rows)  # type: ignore[arg-type]
    _apply_statement_status(ctx, outcome)
    if stored == 0:
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
        ctx.file_access.we_error = int(WeError.SUCCESS)
        ba998_free(ctx)
        return
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE[
        "ba050-Process-Read-Indexed-fetch"
    ]
    row = cursor.fetch_record()
    if row is None:
        if str(outcome.sql_err).strip() not in ("", "0"):
            ctx.file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
        else:
            ctx.file_access.we_error = READ_INDEXED_NO_ERRNO_WE_ERROR
            logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
            logging_data.sql_msg = " " * SQL_MSG_WIDTH
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
        _move_to_ws_file_key(ctx, "")
        ba998_free(ctx)
        return
    _fetch_into_group(ctx.state.td_sainvoice_rec, HEADER_COLUMNS, row)
    bb100_unload_hvs(ctx.state, ctx.buffer)
    # move HV-SINVOICE-KEY to WS-File-Key. [:L938] The header key host variable IS
    # read - but only for LOGGING.
    _move_to_ws_file_key(ctx, str(ctx.state.td_sainvoice_rec[HEADER_KEY_COLUMN]))
    ba999_end(ctx)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba998_free(ctx)


def ba060_process_start(ctx: _BridgeContext) -> None:
    """``ba060-Process-Start.`` [common/slinvoiceMT.cbl:L946]

    The bridge rejects anything outside 5..8, yet the ``evaluate`` immediately below
    still carries ``when 9 *> fn-not-greater-than`` [:L980-L981] - a branch the guard
    makes UNREACHABLE. Meanwhile the HANDLER's own START guard admits 5..9
    [common/acas016.cbl:L446-L454].
    """
    logging_data = ctx.logging_data
    access_type = ctx.file_access.access_type
    low, high = BRIDGE_START_ACCESS_TYPE_RANGE
    if access_type < low or access_type > high:
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        ba999_end(ctx)
        return
    if ctx.state.header_cursor().cursor_active():
        ba998_free(ctx)
    header_entry = _key_of_reference(ctx, 1)
    # The evaluate at [:L972-L983] maps Access-Type to a three-character MOST-Relation.
    # cursor_state owns that table, so it is called rather than retyped.
    relation = start_relation_for(access_type, padded=True)
    ctx.state.most_relation = relation
    header_where = _start_where(
        quote_identifier(header_entry.column_name), relation, quote_value=True
    )
    ctx.state.ws_where = header_where
    _move_to_ws_log_where(ctx, header_where)
    header_key = _record_key_slice(ctx, ctx.k, ctx.ell)
    _move_to_ws_file_key(ctx, header_key)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba060-Process-Start-header"]
    header_outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_HEADER_TABLE_SQL, header_where),
        (header_key,),
        fetch=True,
    )
    header_cursor = ctx.state.header_cursor()
    header_cursor.most_relation = relation
    header_rows = header_cursor.store_result(header_outcome.rows)  # type: ignore[arg-type]
    _apply_statement_status(ctx, header_outcome)
    if header_rows != 0:
        header_cursor.set_cursor_active()
        header_cursor.position_at(header_key)
    # NO 'else set Cursor-Not-Active' here. The header cursor is left as it was found
    # on an empty result. Asymmetric with the RG1 block below.
    if header_rows == 0:
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
        ctx.file_access.we_error = int(WeError.SUCCESS)
    else:
        ctx.file_access.fs_reply = int(FsReply.SUCCESS)
        ctx.file_access.we_error = int(WeError.SUCCESS)
        _move_to_ws_file_key(
            ctx, f"{relation}{header_key} got {header_rows} recs"
        )
    ba999_end(ctx)
    line_entry = _key_of_reference(ctx, 2)
    line_where = _start_where(
        quote_identifier(line_entry.column_name), relation, quote_value=False
    )
    ctx.state.ws_where_2 = line_where
    ctx.state.save_result_rows = header_cursor.stored_rows
    ctx.state.save_count_rows = header_rows
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba060-Process-Start-rg1"]
    line_key = _record_key_slice(ctx, ctx.k2, ctx.ell2)
    line_outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_LINES_TABLE_SQL, line_where),
        (_digits_or_zero(line_key),),
        fetch=True,
    )
    line_cursor = ctx.state.line_cursor()
    line_cursor.most_relation = relation
    line_rows = line_cursor.store_result(line_outcome.rows)  # type: ignore[arg-type]
    if line_rows != 0:
        line_cursor.set_cursor_active()
        line_cursor.position_at(line_key)
    else:
        line_cursor.set_cursor_not_active()
    _apply_statement_status(ctx, line_outcome)
    if line_rows == 0:
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
        ctx.file_access.we_error = int(WeError.SUCCESS)
    else:
        ctx.file_access.fs_reply = int(FsReply.SUCCESS)
        ctx.file_access.we_error = int(WeError.SUCCESS)
        _move_to_ws_file_key(
            ctx, f"{relation}{line_key} got {line_rows} recs RG1 (Lines)"
        )
    ctx.state.save_result_rows_rg1 = line_cursor.stored_rows
    ctx.state.save_count_rows_rg1 = line_rows
    header_cursor.store_result(ctx.state.save_result_rows)  # type: ignore[arg-type]
    ba999_end(ctx)


def _clear_sql_status(ctx: _BridgeContext) -> None:
    """``move zero to FS-Reply WE-Error SQL-State`` + ``spaces to SQL-Msg`` + ``zero to
    SQL-Err``.

    The five-move preamble the write-side paragraphs run before issuing their statement
    - ``ba070-Process-Write`` [common/slinvoiceMT.cbl:L1157-L1162] and ``bc070-Process-
    Write`` [:L2526-L2529]. Note this is the OPPOSITE of ``ba010-Initialise``, which
    deliberately leaves ``FS-Reply`` and ``WE-Error`` alone [:L502-L503].
    """
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data = ctx.logging_data
    logging_data.sql_state = "0".ljust(SQL_STATE_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)


def _duplicate_key_seen(outcome: StatementOutcome, sql_state: str) -> bool:
    """``if Sql-State = "23000" or SQL-Err (1:4) = "1062" or = "1022"``."""
    return is_duplicate_key_bridge_level(outcome.sql_err, sql_state) or (
        outcome.sql_err[:4].strip() in DUPLICATE_KEY_ERRNOS
    )


def ba070_process_write(ctx: _BridgeContext) -> None:
    """``ba070-Process-Write.`` [common/slinvoiceMT.cbl:L1145]"""
    logging_data = ctx.logging_data
    if ctx.buffer.ws_sih_test != 0:
        bc070_process_write(ctx)
        return
    bb000_hv_load(ctx.state, ctx.buffer)
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    _clear_sql_status(ctx)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba070-Process-Write"]
    outcome = bb200_insert(ctx.connection, ctx.state, logging_data)
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        logging_data.sql_state = _truncate_move(outcome.sql_state, SQL_STATE_WIDTH)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        if outcome.sql_err.strip() not in ("", "0"):
            if _duplicate_key_seen(outcome, outcome.sql_state):
                ctx.file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    ba999_end(ctx)


def ba080_process_delete(ctx: _BridgeContext) -> None:
    """``ba080-Process-Delete.`` [common/slinvoiceMT.cbl:L1185]"""
    logging_data = ctx.logging_data
    if ctx.buffer.ws_sih_test != 0:
        bc080_process_delete(ctx)
        return
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    _move_to_ws_file_key(ctx, key_value)
    _move_to_ws_log_where(ctx, where)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba080-Process-Delete"]
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_HEADER_TABLE_SQL, where),
        (key_value,),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = DELETE_FAILURE_WE_ERROR
        ba999_end(ctx)
        return
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    ba999_end(ctx)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)


def ba085_process_delete_all(ctx: _BridgeContext) -> None:
    """``ba085-Process-Delete-ALL.`` [common/slinvoiceMT.cbl:L1254]

    - the FULL TEN-BYTE primary key, exact match.
    """
    logging_data = ctx.logging_data
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    _move_to_ws_log_where(ctx, where)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba085-Process-Delete-All"]
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_HEADER_TABLE_SQL, where),
        (key_value,),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    if outcome.count_rows <= 0:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = DELETE_FAILURE_WE_ERROR
        ba999_end(ctx)
        return
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba999_end(ctx)
    bc085_process_delete_all(ctx)


def ba090_process_rewrite(ctx: _BridgeContext) -> None:
    """``ba090-Process-Rewrite.`` [common/slinvoiceMT.cbl:L1354]

    Loads the host variables, builds the exact-key clause, performs ``bb300-Update``,
    and requires exactly one affected row - otherwise 99 and ``994`` [:L1399-L1400].
    """
    logging_data = ctx.logging_data
    if ctx.buffer.ws_sih_test != 0:
        bc090_process_rewrite(ctx)
        return
    bb000_hv_load(ctx.state, ctx.buffer)
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba090-Process-Rewrite"]
    entry = _key_of_reference(ctx, 1)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    outcome = bb300_update(ctx.connection, ctx.state, logging_data)
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = REWRITE_ROW_COUNT_WE_ERROR
        ba999_end(ctx)
        return
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    ba999_end(ctx)


def ba100_bad_function(ctx: _BridgeContext) -> None:
    """``ba100-Bad-Function.`` [common/slinvoiceMT.cbl:L1412]

    The BRIDGE's bad-function pair is 990/99. The HANDLER's is 999/99
    [common/acas016.cbl:L535-L539]. Different codes for the same condition at the two
    layers; both reproduced, neither harmonised.
    """
    ctx.file_access.we_error = BRIDGE_BAD_FUNCTION_WE_ERROR
    ctx.file_access.fs_reply = int(FsReply.ERROR)
    ba999_end(ctx)


def ba998_free(ctx: _BridgeContext) -> None:
    """``ba998-Free.`` [common/slinvoiceMT.cbl:L1421]

    ONLY THE PRIMARY RESULT IS FREED. The lines result (``TP-SAINV-LINES-REC``) is
    freed only by ``bc998-Free``, which nothing calls - see :func:`bc998_free`.
    N-bc998-never-called.
    """
    ctx.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["ba998-Free"]
    cursor = ctx.state.header_cursor()
    cursor.free_result()
    cursor.set_cursor_not_active()


def ba999_end(ctx: _BridgeContext) -> None:
    """``ba999-end.`` [common/slinvoiceMT.cbl:L1433]

    ``Testing-1`` is the compile-time switch from [copybooks/Test-Data-Flags.cob],
    surfaced as
    :attr:`acas_posting.records.test_data_flags.AcasDalCommonData.sw_testing`. Logging
    is gated on it exactly as here, and :func:`ca_process_logs` explains why the DAL
    path must not log at all.
    """
    if ctx.dal_common.sw_testing != 0:
        ca_process_logs(ctx)


def bc050_process_read_indexed(ctx: _BridgeContext) -> None:
    """``bc050-Process-Read-Indexed.`` [common/slinvoiceMT.cbl:L2381]

    THE POINTER SAVE/RESTORE IS THE WHOLE POINT. Because one MySQL result pointer is
    shared, reading a line row would destroy the header walk's position.
    """
    logging_data = ctx.logging_data
    header_cursor = ctx.state.header_cursor()
    ctx.state.save_result_rows = header_cursor.stored_rows
    ctx.state.save_count_rows = header_cursor.count_rows
    entry = _key_of_reference(ctx, 2)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc050-Process-Read-Indexed"]
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _select_all(_LINES_TABLE_SQL, where),
        (key_value,),
        fetch=True,
    )
    line_cursor = ctx.state.line_cursor()
    stored = line_cursor.store_result(outcome.rows)  # type: ignore[arg-type]
    _apply_statement_status(ctx, outcome)
    if stored == 0:
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
        ctx.file_access.we_error = RG_UNKNOWN_UNEXPECTED_WE_ERROR
        _move_to_ws_file_key(ctx, f"No RG1 Data for {key_value}")
        _initialise_ws_invoice_record(ctx.buffer)
        _initialise_ws_invoice_line(ctx.state)
        bc058_restore_pointers(ctx)
        return
    _move_to_ws_file_key(ctx, f"RG > 0 got cnt={stored} recs, KEY={key_value}")
    ba999_end(ctx)
    bc051_fetch_rg1(ctx)


def bc051_fetch_rg1(ctx: _BridgeContext) -> None:
    """``bc051-Fetch-RG1.`` [common/slinvoiceMT.cbl:L2466]

    The ``move 23 to FS-Reply`` in the else-arm is UNCONDITIONALLY OVERWRITTEN two
    statements later by ``move zero to FS-Reply WE-Error``. A caller can therefore never
    observe the 23 this paragraph sets: an exhausted line cursor reports SUCCESS.
    """
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc051-Fetch-RG1"]
    line_cursor = ctx.state.line_cursor()
    row = line_cursor.fetch_record()
    if row is not None and line_cursor.count_rows > 0:
        _fetch_into_group(ctx.state.td_sainv_lines_rec, LINE_COLUMNS, row)
        # perform bc100-UnloadHVs-rg1 [:L2498] (which itself ends with 'move WS-Invoice-
        # Line to WS-Invoice-Record' at [:L2842], so the [:L2499] move is the same
        # transfer restated).
        bc100_unload_hvs_rg1(ctx.state, ctx.buffer)
        _move_ws_invoice_line_to_ws_invoice_record(ctx.state, ctx.buffer)
    else:
        # initialise WS-Invoice-Line WS-Invoice-Record [:L2501-L2502] The REVERSE order
        # of [:L2452-L2453] - staging record first here - and the order is kept because
        # the source keeps it.
        _initialise_ws_invoice_line(ctx.state)
        _initialise_ws_invoice_record(ctx.buffer)
        ctx.file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
    _move_to_ws_file_key(ctx, _record_key_slice(ctx, ctx.k, ctx.ell))
    # move zero to FS-Reply WE-Error. [:L2507] THIS DESTROYS THE 23 SET ABOVE.
    # Unconditional, two lines after it was set. N-fetch-rg1-status-erased. Do NOT guard
    # this.
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    bc058_restore_pointers(ctx)


def bc058_restore_pointers(ctx: _BridgeContext) -> None:
    """``bc058-Restore-Pointers.`` [common/slinvoiceMT.cbl:L2509]

    Puts the header walk's position back so that a caller alternating header and line
    reads keeps its place. The restore is the reason :func:`ba041_reread` can read a
    line and then still fetch the next header.
    """
    header_cursor = ctx.state.header_cursor()
    fetched_before = header_cursor.fetched_count
    header_cursor.store_result(ctx.state.save_result_rows)  # type: ignore[arg-type]
    header_cursor.fetched_count = fetched_before
    ba999_end(ctx)


def bc070_process_write(ctx: _BridgeContext) -> None:
    """``bc070-Process-Write.`` [common/slinvoiceMT.cbl:L2519]

    ``*> Same as WS-Sil-Key`` at [:L2525] asserts by COMMENT that the invoice key and
    the line key are the same ten bytes. Nothing in the code checks it.
    """
    logging_data = ctx.logging_data
    _move_ws_invoice_record_to_ws_invoice_line(ctx.state, ctx.buffer)
    bc000_hv_load_rg1(ctx.state)
    _move_to_ws_file_key(ctx, ctx.buffer.ws_invoice_key)
    _clear_sql_status(ctx)
    logging_data.sql_state = " " * SQL_STATE_WIDTH
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc070-Process-Write"]
    outcome = bc200_insert_rg1(ctx.connection, ctx.state, logging_data)
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        if outcome.sql_err.strip() not in ("", "0") or outcome.sql_state.startswith(
            str(SqlState.DUPLICATE_KEY)
        ):
            if _duplicate_key_seen(outcome, outcome.sql_state):
                ctx.file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
            else:
                ctx.file_access.fs_reply = int(FsReply.ERROR)
        _move_to_ws_file_key(
            ctx,
            "Cant Re|WriteRG1 Data on "
            f"{_record_key_slice(ctx, ctx.k, ctx.ell)} RG="
            f"{ctx.state.ws_invoice_line.ws_sil_line:02d}",
        )
    ba999_end(ctx)


def bc080_process_delete(ctx: _BridgeContext) -> None:
    """``bc080-Process-Delete.`` [common/slinvoiceMT.cbl:L2563]

    The comment claims "Delete all rows (9<=) for key" while the clause it builds is an
    exact single-key match [:L2573-L2581] and the paragraph is named ``-Delete``, not
    ``-Delete-All``. ``(9<=)`` refers to nothing in the code.
    """
    logging_data = ctx.logging_data
    entry = _key_of_reference(ctx, 2)
    where = _equality_where(quote_identifier(entry.column_name))
    key_value = _record_key_slice(ctx, ctx.k, ctx.ell)
    _move_to_ws_file_key(ctx, key_value)
    _move_to_ws_log_where(ctx, where)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc080-Process-Delete"]
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_LINES_TABLE_SQL, where),
        (key_value,),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    if outcome.count_rows <= 0:
        _apply_statement_status(ctx, outcome)
        _move_to_ws_file_key(
            ctx,
            f"Delete for {key_value} only found (rg01) {outcome.count_rows} Rows",
        )
        # go to ba999-End [:L2622] NO 'move 99 to fs-reply' and NO 'move 995 to WE-
        # Error' on this arm, unlike ba080/ba085/bc085. The miss is silent.
        ba999_end(ctx)
        return
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba999_end(ctx)


def bc085_process_delete_all(ctx: _BridgeContext) -> None:
    """``bc085-Process-Delete-ALL.`` [common/slinvoiceMT.cbl:L2632]

    Header comment, verbatim: ``*> THIS IS NON STANDARD - NEEDED (sl940) - Coded/
    D.Tested.`` So the maintainer believed it tested.
    """
    logging_data = ctx.logging_data
    # set KOR-x1 to 2 [:L2655] - selected, then NOT USED, because the clause hard-codes
    # its predicate instead.
    _key_of_reference(ctx, 2)
    where = _delete_all_lines_where()
    _move_to_ws_file_key(ctx, "")
    _move_to_ws_log_where(ctx, where)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc085-Process-Delete-All"]
    # WS-Sih-Invoice is the bound value [:L2670] - the HEADER's invoice number, rendered
    # as the eight-digit text the STRING would have produced.
    outcome = _run_command(
        ctx.connection,
        logging_data,
        _delete_from(_LINES_TABLE_SQL, where),
        (f"{ctx.buffer.ws_sih_invoice:08d}",),
        fetch=False,
        delete_we_error=DELETE_FAILURE_WE_ERROR,
    )
    if outcome.count_rows <= 0:
        _apply_statement_status(ctx, outcome)
        # The 99/995 pair sits INSIDE the errno test [:L2705-L2712], so it fires only on
        # a genuine driver error - never on the always-empty delete.
        if outcome.sql_err.strip() not in ("", "0"):
            ctx.file_access.fs_reply = int(FsReply.ERROR)
            ctx.file_access.we_error = DELETE_FAILURE_WE_ERROR
        ba999_end(ctx)
        return
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ba999_end(ctx)


def bc090_process_rewrite(ctx: _BridgeContext) -> None:
    """``bc090-Process-Rewrite section.`` [common/slinvoiceMT.cbl:L2723]"""
    logging_data = ctx.logging_data
    _move_ws_invoice_record_to_ws_invoice_line(ctx.state, ctx.buffer)
    bc000_hv_load_rg1(ctx.state)
    _move_to_ws_file_key(ctx, ctx.state.ws_invoice_line.ws_sil_key)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc090-Process-Rewrite"]
    entry = _key_of_reference(ctx, 2)
    where = _equality_where(quote_identifier(entry.column_name))
    _move_to_ws_log_where(ctx, where)
    outcome = bc300_update_rg1(ctx.connection, ctx.state, logging_data)
    if outcome.count_rows != 1:
        _apply_statement_status(ctx, outcome)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        ctx.file_access.we_error = REWRITE_ROW_COUNT_WE_ERROR
        ba999_end(ctx)
        return
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0".ljust(SQL_ERR_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    ba999_end(ctx)


def bc998_free(ctx: _BridgeContext) -> None:
    """``bc998-Free.`` [common/slinvoiceMT.cbl:L3239] - AND NOTHING EVER CALLS IT.

    N-bc998-never-called. Searching the whole 3259-line bridge for ``bc998`` returns
    exactly ONE hit: its own label at [common/slinvoiceMT.cbl:L3239]. No ``perform``, no
    ``go to``, from any paragraph. Consequences, all reproduced.
    """
    ctx.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_TRACE["bc998-Free"]
    cursor = ctx.state.line_cursor()
    cursor.free_result()
    cursor.set_cursor_not_active()


def ca_process_logs(ctx: _BridgeContext) -> None:
    """``Ca-Process-Logs.`` [common/slinvoiceMT.cbl:L3251]

    ``fhlogger`` is ``common/fhlogger.cbl``, which AAP section 0.2.2 lists as OUT OF
    SCOPE. So the call is not reproduced as a call.
    """
    logging_data = ctx.logging_data
    #  ONE ADAPTER FOR ALL SEVENTEEN HANDLER MODULES, at one level, with one field set.
    # `WS-File-Key` is WITHHELD - for this table it is the invoice number, a
    # business key - and so is `WS-Log-Where`, which this bridge fills with the
    # WHOLE STATEMENT [see `_run_statement`], making it the single most exposing
    # field in the module (CWE-532). `sanitise_for_log` escaped both and removed
    # neither. The adapter also advances `Log-File-Rec-Written` modulo one million,
    # the range of the frozen `pic 9(6)` [copybooks/Test-Data-Flags.cob:L18], which
    # this paragraph did not advance at all.
    log_file_handler_record(
        _LOG,
        program=BRIDGE_PROGRAM_ID,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(ctx.file_access.file_function),
        access_type=int(ctx.file_access.access_type),
        fs_reply=int(ctx.file_access.fs_reply),
        we_error=int(ctx.file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=ctx.dal_common,
    )


def slinvoice_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    invoice: InvoiceBuffer,
    *,
    connection: object = None,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
) -> FileAccess:
    """``call "slinvoiceMT" using ...`` - the bridge, entered as the handler enters it.

    THIS FUNCTION *IS* ``ba-ACAS-DAL-Process section.``
    ``[common/slinvoiceMT.cbl:L483]`` - the bridge's single entry section, the one a
    ``CALL "slinvoiceMT"`` actually lands in.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L22-L41], carrying the
            function code, the access type, the status pair and ``Logging-Data``.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob], whose
            ``sw-testing`` gates logging exactly as ``Testing-1`` does.
        invoice: ``WS-Invoice-Record`` - the ONE union buffer serving BOTH tables.
        connection: The live connection, or ``None`` to reuse this bridge's
            persistent handle.
        system_record: ``System-Record``, needed only by function 1.
        transport: A per-call declaration, or ``None`` to use the declaration
            installed on this bridge by :func:`dispatch`.

    Returns:
        The same ``file_access`` object, mutated - which is what a COBOL ``CALL BY
            REFERENCE`` does.
    """
    global _BRIDGE_CONNECTION

    state = _BRIDGE_STATE
    resolved_connection = (
        _BRIDGE_CONNECTION if connection is None else connection
    )
    resolved_transport = _BRIDGE_TRANSPORT if transport is None else transport
    ctx = _BridgeContext(
        connection=resolved_connection,
        file_access=file_access,
        dal_common=dal_common,
        state=state,
        buffer=invoice,
        system_record=system_record,
        transport=resolved_transport,
    )
    ba010_initialise(ctx)
    function_code = file_access.file_function
    if function_code == int(FileFunction.OPEN):
        ba020_process_open(ctx)
    elif function_code == int(FileFunction.CLOSE):
        ba030_process_close(ctx)
    elif function_code in (
        int(FileFunction.READ_NEXT),
        int(FileFunction.READ_NEXT_HEADER),
    ):
        ba040_process_read_next(ctx)
    elif function_code == int(FileFunction.READ_INDEXED):
        ba050_process_read_indexed(ctx)
    elif function_code == int(FileFunction.WRITE):
        ba070_process_write(ctx)
    elif function_code == int(FileFunction.DELETE_ALL):
        # *> option 6 is a special to cleardown all LINE data for 1 invoice
        # [common/slinvoiceMT.cbl:L529-L532]. THE BRIDGE HONOURS 6.
        ba085_process_delete_all(ctx)
    elif function_code == int(FileFunction.RE_WRITE):
        ba090_process_rewrite(ctx)
    elif function_code == int(FileFunction.DELETE):
        ba080_process_delete(ctx)
    elif function_code == int(FileFunction.START):
        ba060_process_start(ctx)
    else:
        ba100_bad_function(ctx)
    # The bridge owns this state across CALLs. Mirror it onto the linkage buffer
    # for compatibility, but never make a fresh buffer the owner of the handle.
    _BRIDGE_CONNECTION = ctx.connection
    invoice.bridge_state = state
    invoice.connection = ctx.connection
    return file_access


# The handler: acas016 'aa-Process-Flat-File Section.' [common/acas016.cbl:L242] and
# everything under it.


def _isam_file_available(_ctx: "_HandlerContext") -> bool:
    """Whether ``Invoice-File`` - the ISAM file - can be opened. Always ``False``.

    ``Invoice-File`` is the indexed (ISAM) file declared in the handler's own ``FILE-
    CONTROL``. This migration has ONE store, the frozen MySQL schema, and AAP section
    0.2.2 forbids adding another.
    """
    return False


@dataclass(slots=True)
class _HandlerContext:
    """What every ``acas016`` paragraph can see - the handler's five linkage items."""

    system_record: SystemRecord
    invoice: InvoiceBuffer
    file_access: FileAccess
    file_defs: FileDefs
    dal_common: AcasDalCommonData
    cobol_file_status: int = 0

    @property
    def logging_data(self) -> LoggingData:
        """``Logging-Data``, reached through ``File-Access``."""
        return self.file_access.logging_data

    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof`` - the condition name tested at [common/acas016.cbl:L373].
        """
        return self.cobol_file_status != 0


def _handler_file_key(ctx: _HandlerContext, text: str) -> None:
    """``move <x> to WS-File-Key`` at handler level - ``pic x(64)``, truncating."""
    ctx.logging_data.ws_file_key = _truncate_move(text, _WS_FILE_KEY_WIDTH)


def aa010_main(ctx: _HandlerContext) -> None:
    """``aa010-main.`` [common/acas016.cbl:L244]"""
    logging_data = ctx.logging_data
    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT


def aa020_process_open(ctx: _HandlerContext) -> None:
    """``aa020-Process-Open.`` [common/acas016.cbl:L316]

    ISAM path. Four access types, tested as a nest of ``if/else`` rather than an
    ``evaluate`` [:L320-L345].
    """
    logging_data = ctx.logging_data
    _handler_file_key(ctx, "")
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa020-Process-Open"]
    access_type = ctx.file_access.access_type
    if access_type == int(AccessType.INPUT):
        if not _isam_file_available(ctx):
            ctx.file_access.fs_reply = _OPEN_INPUT_FAILED_FS_REPLY
            aa999_main_exit(ctx)
            return
    elif access_type == int(AccessType.I_O):
        # The close/open-output/close/open-i-o recovery [:L331-L335].
        pass
    elif access_type == int(AccessType.OUTPUT):
        pass
    elif access_type == int(AccessType.EXTEND):
        # *> Must not be used for ISAM files: 997 / 99   [:L341-L343]
        ctx.file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        ctx.file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(ctx)
        return
    ctx.cobol_file_status = 0
    _handler_file_key(ctx, "OPEN SL INVOICE File")
    if ctx.file_access.fs_reply != int(FsReply.SUCCESS):
        ctx.file_access.we_error = HANDLER_BAD_FUNCTION_WE_ERROR
    aa999_main_exit(ctx)


def aa030_process_close(ctx: _HandlerContext) -> None:
    """``aa030-Process-Close.`` [common/acas016.cbl:L354]

    It performs ``aa999-main-exit`` (which itself logs when ``Testing-1``), then ZEROES
    ``File-Function`` and ``Access-Type`` and logs AGAIN unconditionally - the second
    call being what closes the log file. Every other paragraph reaches ``aa999-main-
    exit`` once and stops.
    """
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa030-Process-Close"]
    _handler_file_key(ctx, "")
    ctx.cobol_file_status = 0
    _handler_file_key(ctx, "CLOSE SL INVOICE File")
    aa999_main_exit(ctx)
    ctx.file_access.file_function = 0
    ctx.file_access.access_type = 0
    ca_process_logs_handler(ctx)


def aa040_process_read_next(ctx: _HandlerContext) -> None:
    """``aa040-Process-Read-Next.`` [common/acas016.cbl:L367]

    ``stop "Cobol File EOF"`` halts the run and waits for the operator. Its comment is
    UPPER-CASED here (``*> FOR TESTING ONLY``) where ``common/acas015.cbl:L424`` writes
    the same thing in lower case.
    """
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa040-Process-Read-Next"]
    if ctx.cobol_file_eof():
        ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
        ctx.file_access.we_error = int(FsReply.END_OF_FILE)
        ctx.invoice.ws_sih_invoice = 0
        ctx.invoice.ws_sih_test = 0
        logging_data.sql_err = " " * SQL_ERR_WIDTH
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        # stop "Cobol File EOF"  *> FOR TESTING ONLY   [:L379]
        # DELIBERATELY NOT REPRODUCED as a pause.  The transfer below IS reproduced.
        #  ONE ERROR, THROUGH THE ONE REPORTER. `STOP` with a literal DISPLAYS
        #  that literal and then waits, so the display is a record and the wait is
        #  the omission. DEBUG was the wrong level and, worse, a DIFFERENT level
        #  from the same statement's record in every sibling handler - WARNING in
        #  acas006 and acas007, INFO in acas012, ERROR in acas019 - so one event
        #  appeared as four and, at DEBUG, usually as none. A production `stop` that
        #  would hang an unattended batch run is exactly what an operator must see.
        log_cobol_stop(
            _LOG,
            program=HANDLER,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas016.cbl:L379]",
        )
        aa999_main_exit(ctx)
        return
    # read Invoice-File next record at end ... [:L383-L390] - ISAM verb, omitted.
    ctx.file_access.we_error = int(FsReply.END_OF_FILE)
    ctx.file_access.fs_reply = int(FsReply.END_OF_FILE)
    ctx.cobol_file_status = 1
    # initialize Invoice-Record [:L387] The handler's own ISAM record area is the SAME
    # linkage record the bridge sees, so the whole of it clears - key included.
    _initialise_ws_invoice_record(ctx.invoice)
    _handler_file_key(ctx, "EOF")
    aa999_main_exit(ctx)


def aa045_eval_keys(ctx: _HandlerContext) -> None:
    """``aa045-Eval-Keys.`` [common/acas016.cbl:L398]

    AND NOTE WHICH FUNCTIONS ARE ABSENT: 3 and 34. A read-next therefore leaves ``WS-
    File-Key`` at whatever the previous call put there, until the paragraph body
    overwrites it. Reproduced by simply not listing them.
    """
    logging_data = ctx.logging_data
    del logging_data
    function_code = ctx.file_access.file_function
    if function_code in _AA045_KEYED_FUNCTIONS:
        if ctx.logging_data.file_key_no == 1:
            _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
        else:
            _handler_file_key(ctx, "")
    else:
        _handler_file_key(ctx, "")


def aa050_process_read_indexed(ctx: _HandlerContext) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas016.cbl:L416]

    The trailing 998 at [:L437] carries the comment ``*> file seeks key type out of
    range but should never get here 998`` - the author knew the guard at [:L256] had
    already rejected key numbers other than 1, so this is defence in depth against his
    own dispatch.
    """
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa050-Process-Read-Indexed"]
    aa045_eval_keys(ctx)
    ctx.cobol_file_status = 0
    if logging_data.file_key_no == 1:
        if not _isam_file_available(ctx):
            ctx.file_access.we_error = int(FsReply.INVALID_KEY_ON_START)
            ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
        if ctx.file_access.fs_reply == int(FsReply.SUCCESS):
            _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
        else:
            _initialise_ws_invoice_record(ctx.invoice)
            _handler_file_key(
                ctx,
                f"Failed action in read-indexed for {ctx.invoice.ws_invoice_key}",
            )
        aa999_main_exit(ctx)
        return
    # move 998 to WE-Error  *> ... but should never get here   [:L437-L438]
    ctx.file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
    ctx.file_access.fs_reply = int(FsReply.ERROR)
    aa999_main_exit(ctx)


def aa060_process_start(ctx: _HandlerContext) -> None:
    """``aa060-Process-Start.`` [common/acas016.cbl:L442]

    AND THIS GUARD SETS ``WE-Error`` WITHOUT SETTING ``FS-Reply``. Compare the key
    guard at [:L256-L259], which sets both 998 AND ``fs-reply`` 99.
    """
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa060-Process-Start"]
    aa045_eval_keys(ctx)
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ctx.cobol_file_status = 0
    low, high = HANDLER_START_ACCESS_TYPE_RANGE
    access_type = ctx.file_access.access_type
    if access_type < low or access_type > high:
        ctx.file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        aa999_main_exit(ctx)
        return
    if logging_data.file_key_no == 1 and start_access_type_is_valid(access_type):
        if not _isam_file_available(ctx):
            ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
            aa999_main_exit(ctx)
            return
    if logging_data.file_key_no == 1:
        _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa070_process_write(ctx: _HandlerContext) -> None:
    """``aa070-Process-Write.`` [common/acas016.cbl:L500]"""
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa070-Process-Write"]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ctx.cobol_file_status = 0
    if not _isam_file_available(ctx):
        ctx.file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa080_process_delete(ctx: _HandlerContext) -> None:
    """``aa080-Process-Delete.`` [common/acas016.cbl:L511]"""
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa080-Process-Delete"]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ctx.cobol_file_status = 0
    if not _isam_file_available(ctx):
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa090_process_rewrite(ctx: _HandlerContext) -> None:
    """``aa090-Process-Rewrite.`` [common/acas016.cbl:L522]"""
    logging_data = ctx.logging_data
    logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_TRACE["aa090-Process-Rewrite"]
    ctx.file_access.fs_reply = int(FsReply.SUCCESS)
    ctx.file_access.we_error = int(WeError.SUCCESS)
    ctx.cobol_file_status = 0
    if not _isam_file_available(ctx):
        ctx.file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    _handler_file_key(ctx, ctx.invoice.ws_invoice_key)
    aa999_main_exit(ctx)


def aa100_bad_function(ctx: _HandlerContext) -> None:
    """``aa100-Bad-Function.`` [common/acas016.cbl:L534]

    N-delete-all-bad-function. FUNCTION CODE 6 ARRIVES HERE. The dispatch's ``when
    other`` comment claims ``*> 6 is spare / unused`` [common/acas016.cbl:L309], yet
    ``fn-Delete-All value 6`` exists [copybooks/wsfnctn.cob:L94] and the facade
    publishes ``Invoice-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L911].
    """
    ctx.file_access.we_error = HANDLER_BAD_FUNCTION_WE_ERROR
    ctx.file_access.fs_reply = int(FsReply.ERROR)
    aa999_main_exit(ctx)


def aa999_main_exit(ctx: _HandlerContext) -> None:
    """``aa999-main-exit.`` [common/acas016.cbl:L541]"""
    if ctx.dal_common.sw_testing != 0:
        ca_process_logs_handler(ctx)
    aa_main_exit(ctx)


def aa_main_exit(ctx: _HandlerContext) -> None:
    """``aa-main-exit.`` [common/acas016.cbl:L546]

    A label with a comment and no statements - it exists only to be a ``go to`` target
    and to fall through to ``aa-Exit``.
    """
    aa_exit(ctx)


def aa_exit(ctx: _HandlerContext) -> None:
    """``aa-Exit.`` [common/acas016.cbl:L550]"""
    del ctx


def aa_process_flat_file(ctx: _HandlerContext) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas016.cbl:L242]

    The section that owns ``aa010-main`` through ``aa-Exit``. Entering the section means
    entering its first paragraph, so this is :func:`aa010_main` followed by the guards
    and the function ``evaluate`` - all of which :func:`dispatch` performs in the
    COBOL's order.
    """
    aa010_main(ctx)


def ca_process_logs_handler(ctx: _HandlerContext) -> None:
    """``Ca-Process-Logs.`` [common/acas016.cbl:L633] - the HANDLER's copy.

    So on the RDB path this must NOT run - the bridge has already logged, and calling it
    again would double every log record.
    """
    logging_data = ctx.logging_data
    #  THE SAME ONE ADAPTER the bridge's copy uses, so that the two paragraphs
    # that share a name render identically and differ only in the program they
    # name. `WS-File-Key` - the invoice number - is withheld (CWE-532), and
    # `Log-File-Rec-Written` is advanced modulo one million.
    log_file_handler_record(
        _LOG,
        program=HANDLER,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(ctx.file_access.file_function),
        access_type=int(ctx.file_access.access_type),
        fs_reply=int(ctx.file_access.fs_reply),
        we_error=int(ctx.file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=ctx.dal_common,
    )


def ca_exit_handler(ctx: _HandlerContext) -> None:
    """``ca-Exit.`` [common/acas016.cbl:L639] - ``exit.`` A bare paragraph exit."""
    del ctx


# acas016's OWN 'ba' section - the RDBMS branch N-paragraph-name-collision.


def ba010_test_ws_rec_size_handler(ctx: _HandlerContext) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas016.cbl:L561]

    The paragraph then FALLS THROUGH into ``ba012-Test-WS-Rec-Size-2`` [:L569] with no
    transfer of control. THE FALL-THROUGH IS DRIVEN BY
    :func:`ba_process_rdbms_handler`, NOT BY THIS FUNCTION, because COBOL's two PERFORM
    forms differ and both are used against this section.
    """
    ctx.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2_handler(ctx: _HandlerContext) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas016.cbl:L569]

    The first-call-only record-length guard and credential load. ``if A = zero`` [:L571]
    makes the whole block run ONCE per program activation, with the comment at [:L563]
    insisting ``(So do NOT use var A & B again)``.

    Returns:
        ``True`` when the paragraph took ``go to ba-rdbms-exit`` [:L596], so the section
            driver must NOT fall through into ``ba015-Test-Ends``; ``False`` on the
            normal path.
    """
    # if A = zero *> so it is being called first time [:L571] move function Length (WS-
    # Invoice-Record) to A [:L572-L574] move function length (Invoice-Record) to B
    # [:L575-L577] if A < B -> 901 / 99 [:L578-L581] DELIBERATE OMISSION, RECORDED
    # (R-5).
    ctx.file_access.rdb_data = load_rdb_data_once(ctx.system_record)
    return False


def ba015_test_ends_handler(ctx: _HandlerContext) -> None:
    """``ba015-Test-Ends.`` [common/acas016.cbl:L611]"""
    # call "slinvoiceMT" using File-Access ACAS-DAL-Common-data WS-Invoice-Record THE
    # PARAMETER ORDER IS THE BRIDGE'S, NOT THE HANDLER'S. The handler was entered with
    # System-Record first and File-Access third.
    slinvoice_mt(
        ctx.file_access,
        ctx.dal_common,
        ctx.invoice,
        connection=ctx.invoice.connection,
        system_record=ctx.system_record,
        transport=_BRIDGE_TRANSPORT,
    )


def ba_rdbms_exit_handler(ctx: _HandlerContext) -> None:
    """``ba-rdbms-exit.`` [common/acas016.cbl:L629]"""
    del ctx


def ba_process_rdbms_handler(ctx: _HandlerContext) -> None:
    """``ba-Process-RDBMS section.`` [common/acas016.cbl:L553]

    Entering the section enters its first paragraph, ``ba010-Test-WS-Rec-Size``, and the
    remaining paragraphs run by fall-through until ``ba-rdbms-exit``'s ``exit section``.
    """
    ba010_test_ws_rec_size_handler(ctx)
    jumped_to_exit = ba012_test_ws_rec_size_2_handler(ctx)
    if jumped_to_exit:
        ba_rdbms_exit_handler(ctx)
        return
    ba015_test_ends_handler(ctx)
    ba_rdbms_exit_handler(ctx)


def dispatch(
    system: SystemRecord,
    invoice: InvoiceBuffer,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None | object = _TRANSPORT_NOT_SUPPLIED,
) -> FileAccess:
    """``call "acas016" using ...`` - the handler, entered as its callers enter it.

    ONE RECORD PARAMETER FOR TWO TABLES. ``WS-Invoice-Record`` is a UNION buffer with
    three redefining views [copybooks/slwsinv2.cob:L27], [:L38], [:L91], and the
    function code together with ``WS-Sih-Test`` decides which table is touched.

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob], whose ``RDBMS-Flat-
            Statuses`` selects the ISAM or the RDB path and whose ``RDBMS-*`` fields
            carry the credentials.
        invoice: ``WS-Invoice-Record`` - the ONE union buffer for BOTH tables.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L22-L41].
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Carried because the linkage
            carries it; the RDB path does not read it, which is itself recorded as a
            deliberate omission.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob].
        transport: The caller's keyword-only transport declaration. Omission
            preserves the bridge's current declaration; explicit ``None`` clears it.

    Returns:
        The same ``file_access``, mutated - a COBOL ``CALL BY REFERENCE``.
    """
    global _BRIDGE_TRANSPORT

    if transport is not _TRANSPORT_NOT_SUPPLIED:
        if transport is not None and not isinstance(transport, TransportSecurity):
            raise TypeError("transport must be TransportSecurity or None")
        _BRIDGE_TRANSPORT = transport

    ctx = _HandlerContext(
        system_record=system,
        invoice=invoice,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=dal_common,
    )
    logging_data = ctx.logging_data
    aa010_main(ctx)
    function_code = file_access.file_function
    # evaluate File-Function when 4 *> fn-read-indexed when 9 *> fn-start if File-Key-No
    # not = 1.
    if function_code in (int(FileFunction.READ_INDEXED), int(FileFunction.START)):
        if logging_data.file_key_no != 1:
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(ctx)
            return file_access
    elif function_code == int(FileFunction.DELETE):
        if logging_data.file_key_no != 1:
            file_access.we_error = int(WeError.DELETE_KEY_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(ctx)
            return file_access
    # Verified absent from the whole file. Opening for output here is a PLAIN open and
    # clears NEITHER table.
    flat_statuses = system.system_data_block.rdbms_flat_statuses
    if not _fs_cobol_files_used(flat_statuses):
        source_statuses = flat_statuses
        target_statuses = file_access.fa_rdbms_flat_statuses
        target_statuses.fa_file_system_used = source_statuses.file_system_used
        target_statuses.fa_file_duplicates_in_use = (
            source_statuses.file_duplicates_in_use
        )
        ba_process_rdbms_handler(ctx)
        # go to AA-Main-Exit - Class 3.
        aa_main_exit(ctx)
        return file_access
    # *> Test Rec lengths first. [:L277] A PARAGRAPH PERFORM, NOT A SECTION PERFORM.
    # It runs ba012's body ALONE and returns.
    if ba012_test_ws_rec_size_2_handler(ctx):
        aa999_main_exit(ctx)
        return file_access
    # [common/acas016.cbl:L287-L288], VERBATIM (the second line's leading space is the
    # maintainer's, not a transcription slip - L287 opens its comment in column 1 and
    # L288 in column 2, so even the commented-out block is misaligned).
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH
    if function_code == int(FileFunction.OPEN):
        aa020_process_open(ctx)
    elif function_code == int(FileFunction.CLOSE):
        aa030_process_close(ctx)
    elif function_code in (
        int(FileFunction.READ_NEXT),
        int(FileFunction.READ_NEXT_HEADER),
    ):
        aa040_process_read_next(ctx)
    elif function_code == int(FileFunction.READ_INDEXED):
        aa050_process_read_indexed(ctx)
    elif function_code == int(FileFunction.WRITE):
        aa070_process_write(ctx)
    elif function_code == int(FileFunction.RE_WRITE):
        aa090_process_rewrite(ctx)
    elif function_code == int(FileFunction.DELETE):
        aa080_process_delete(ctx)
    elif function_code == int(FileFunction.START):
        aa060_process_start(ctx)
    else:
        # when other *> 6 is spare / unused [common/acas016.cbl:L309-L310] N-delete-
        # all-bad-function, AND THE TWO LAYERS DISAGREE. Verified.
        aa100_bad_function(ctx)
        return file_access
    # *> Should never get here but in case :( go to aa100-Bad-Function.
    return file_access


# The linkage projection - `copy "slwsinv2.cob" replacing Invoice-Record by WS-Invoice-
# Record` [common/acas016.cbl:L218-L221] WHY THIS EXISTS AT ALL.


def _projected_record_views(record: object) -> tuple[object, object] | None:
    """Return ``(header, line)`` if ``record`` is a caller's own record area.

    The area is recognised STRUCTURALLY, by the four names the copybook gives it -
    ``Invoice-Nos``, ``Item-Nos`` and the two redefining views - because the callers are
    ``programs/*`` modules this layer may not import.
    """
    if isinstance(record, InvoiceBuffer):
        return None
    for attribute in ("invoice_nos", "item_nos", "invoice_header", "invoice_line"):
        if not hasattr(record, attribute):
            return None
    return getattr(record, "invoice_header"), getattr(record, "invoice_line")


def linkage_buffer_for(record: object) -> InvoiceBuffer:
    """Adopt the caller's record area as this handler's ``WS-Invoice-Record``.

    THE BUFFER IS THE SAME ONE ON EVERY CALL for a given record area, and it has to
    be.

    Args:
        record: The second operand of the ``CALL`` - either a caller's record area or an
            :class:`InvoiceBuffer` the caller manages itself.

    Returns:
        The buffer to pass to :func:`dispatch`.
    """
    if isinstance(record, InvoiceBuffer):
        return record
    views = _projected_record_views(record)
    if views is None:
        raise TypeError(
            "acas016 takes WS-Invoice-Record [common/acas016.cbl:L218-L221] - "
            "either an InvoiceBuffer or a record area exposing invoice_nos, "
            f"item_nos, invoice_header and invoice_line; got {type(record).__name__}"
        )
    identity = id(record)
    held = _LINKAGE_BUFFERS.get(identity)
    if held is None or held[0] is not record:
        held = (record, InvoiceBuffer())
        _LINKAGE_BUFFERS[identity] = held
    buffer = held[1]
    _load_buffer_from_record(record, buffer)
    return buffer


def publish_linkage_buffer(buffer: InvoiceBuffer, record: object) -> None:
    """Copy the buffer back over the caller's record area, after the ``CALL``.

    ``File-Access`` is not the only thing a COBOL ``CALL`` passes by reference - the
    record area is passed the same way, so whatever the handler and the bridge left in
    ``WS-Invoice-Record`` is what the caller reads next.

    Args:
        buffer: The buffer :func:`dispatch` was given.
        record: The caller's record area, mutated in place. An :class:`InvoiceBuffer` is
            its own area and is left alone.
    """
    if isinstance(record, InvoiceBuffer):
        return
    if _projected_record_views(record) is None:
        return
    _store_record_from_buffer(buffer, record)


#: The buffer each caller record area is walked through, keyed by the area's identity
#: and holding the area itself so the key stays valid.
_LINKAGE_BUFFERS: Final[dict[int, tuple[object, InvoiceBuffer]]] = {}


def _load_buffer_from_record(record: object, buffer: InvoiceBuffer) -> None:
    """The `ih-`/`il-` area into the `sih-`/`sil-` buffer - a rename, field for field.
    """
    header_view = getattr(record, "invoice_header")
    generic_invoice = int(getattr(record, "invoice_nos"))
    generic_test = int(getattr(record, "item_nos"))
    if header_view is not None and not generic_invoice and not generic_test:
        generic_invoice = int(header_view.ih_prime.ih_invoice)
        generic_test = int(header_view.ih_prime.ih_test)
    buffer.ws_sih_invoice = generic_invoice
    buffer.ws_sih_test = generic_test
    if header_view is not None:
        target = buffer.select_header()
        source_prime = header_view.ih_prime
        target_prime = target.sih_prime
        target_prime.sih_customer.sih_nos = source_prime.ih_customer.ih_nos
        target_prime.sih_customer.sih_check = source_prime.ih_customer.ih_check
        target_prime.sih_date = source_prime.ih_date
        target_prime.sih_order = source_prime.ih_order
        # `filler redefines sih-order` [copybooks/slwsinv.cob:L28] against `filler
        # redefines ih-order` [copybooks/slwsinv2.cob:L47] - the same overlay, carried
        # across so a stale one cannot survive a projection.
        source_overlay = source_prime.filler_47
        target_overlay = target_prime.filler_28
        target_overlay.sih_freq = source_overlay.ih_freq
        target_overlay.sih_repeat = source_overlay.ih_repeat
        target_overlay.filler_37 = source_overlay.filler_56
        target_overlay.sih_last_date = source_overlay.ih_last_date
        target_prime.sih_type = source_prime.ih_type
        target_prime.sih_ref = source_prime.ih_ref
        source_sub = header_view.ih_sub_prime
        target_sub = target.sih_sub_prime
        target_sub.sih_description = source_sub.ih_description
        source_fig = source_sub.ih_fig
        target_fig = target_sub.sih_fig
        target_fig.sih_p_c = source_fig.ih_p_c
        target_fig.sih_net = source_fig.ih_net
        target_fig.sih_extra = source_fig.ih_extra
        target_fig.sih_carriage = source_fig.ih_carriage
        target_fig.sih_vat = source_fig.ih_vat
        target_fig.sih_discount = source_fig.ih_discount
        target_fig.sih_e_vat = source_fig.ih_e_vat
        target_fig.sih_c_vat = source_fig.ih_c_vat
        target_sub.sih_status = source_sub.ih_status
        target_sub.sih_status_p = source_sub.ih_status_p
        target_sub.sih_status_l = source_sub.ih_status_l
        target_sub.sih_status_c = source_sub.ih_status_c
        target_sub.sih_status_a = source_sub.ih_status_a
        target_sub.sih_status_i = source_sub.ih_status_i
        target_sub.sih_lines = source_sub.ih_lines
        target_sub.sih_deduct_days = source_sub.ih_deduct_days
        target_sub.sih_deduct_amt = source_sub.ih_deduct_amt
        target_sub.sih_deduct_vat = source_sub.ih_deduct_vat
        target_sub.sih_days = source_sub.ih_days
        target_sub.sih_cr = source_sub.ih_cr
        target_sub.sih_day_book_flag = source_sub.ih_day_book_flag
        target_sub.sih_update = source_sub.ih_update
    line_view = getattr(record, "invoice_line")
    if line_view is not None:
        line = buffer.select_line()
        line.sil_product = line_view.il_product
        line.sil_pa = line_view.il_pa
        line.sil_qty = line_view.il_qty
        line.sil_type = line_view.il_type
        line.sil_description = line_view.il_description
        line.sil_net = line_view.il_net
        line.sil_unit = line_view.il_unit
        line.sil_discount = line_view.il_discount
        line.sil_vat = line_view.il_vat
        line.sil_vat_code = line_view.il_vat_code
        line.sil_update = line_view.il_update
        line.sil_back_ordered = line_view.il_back_ordered
    buffer.sync_key_into_views()


def _new_caller_header_view() -> IhInvoiceHeader:
    """``01 Invoice-Header redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L38].

    The caller's own view of the shared area, at its ``INITIALIZE`` values. Needed
    because a Python record area can hold ``None`` where COBOL storage always exists.
    """
    return IhInvoiceHeader(
        ih_prime=IhPrime(
            ih_invoice=0,
            ih_test=0,
            ih_customer=IhCustomer(ih_nos=" " * 6, ih_check=0),
            ih_date=0,
            ih_order=" " * 10,
            filler_47=IhOrderView(
                ih_freq=" ", ih_repeat=0, filler_56=" " * 3, ih_last_date=0
            ),
            ih_type=0,
            ih_ref=" " * 10,
        ),
        ih_sub_prime=IhSubPrime(
            ih_description=" " * 32,
            ih_fig=IhFig(
                ih_p_c=Decimal("0.00"),
                ih_net=Decimal("0.00"),
                ih_extra=Decimal("0.00"),
                ih_carriage=Decimal("0.00"),
                ih_vat=Decimal("0.00"),
                ih_discount=Decimal("0.00"),
                ih_e_vat=Decimal("0.00"),
                ih_c_vat=Decimal("0.00"),
            ),
            ih_status=" ",
            ih_status_p=" ",
            ih_status_l=" ",
            ih_status_c=" ",
            ih_status_a=" ",
            ih_status_i=" ",
            ih_lines=0,
            ih_deduct_days=0,
            ih_deduct_amt=Decimal("0.00"),
            ih_deduct_vat=Decimal("0.00"),
            ih_days=0,
            ih_cr=0,
            ih_day_book_flag=" ",
            ih_update=" ",
        ),
    )


def _new_caller_line_view() -> IlInvoiceLine:
    """``01 Invoice-Line redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L91]."""
    return IlInvoiceLine(
        il_invoice=0,
        il_line=0,
        il_product=" " * 13,
        il_pa=" " * 2,
        il_qty=0,
        il_type=" ",
        il_description=" " * 32,
        il_net=Decimal("0.00"),
        il_unit=Decimal("0.00"),
        il_discount=Decimal("0.00"),
        il_vat=Decimal("0.00"),
        il_vat_code=0,
        il_update=" ",
        il_back_ordered=" ",
    )


def _store_record_from_buffer(buffer: InvoiceBuffer, record: object) -> None:
    """The `sih-`/`sil-` buffer back into the `ih-`/`il-` area - the same rename."""
    setattr(record, "invoice_nos", buffer.ws_sih_invoice)
    setattr(record, "item_nos", buffer.ws_sih_test)
    header_view = getattr(record, "invoice_header")
    source = buffer.ws_invoice_record
    if header_view is None and source is not None:
        # COBOL storage always exists, so a caller that arrived with no view object gets
        # one rather than an exception. See `_new_caller_header_view`.
        header_view = _new_caller_header_view()
        setattr(record, "invoice_header", header_view)
    if header_view is not None and source is not None:
        source_prime = source.sih_prime
        target_prime = header_view.ih_prime
        target_prime.ih_invoice = buffer.ws_sih_invoice
        target_prime.ih_test = buffer.ws_sih_test
        target_prime.ih_customer.ih_nos = source_prime.sih_customer.sih_nos
        target_prime.ih_customer.ih_check = source_prime.sih_customer.sih_check
        target_prime.ih_date = source_prime.sih_date
        target_prime.ih_order = source_prime.sih_order
        source_overlay = source_prime.filler_28
        target_overlay = target_prime.filler_47
        target_overlay.ih_freq = source_overlay.sih_freq
        target_overlay.ih_repeat = source_overlay.sih_repeat
        target_overlay.filler_56 = source_overlay.filler_37
        target_overlay.ih_last_date = source_overlay.sih_last_date
        target_prime.ih_type = source_prime.sih_type
        target_prime.ih_ref = source_prime.sih_ref
        source_sub = source.sih_sub_prime
        target_sub = header_view.ih_sub_prime
        target_sub.ih_description = source_sub.sih_description
        source_fig = source_sub.sih_fig
        target_fig = target_sub.ih_fig
        target_fig.ih_p_c = source_fig.sih_p_c
        target_fig.ih_net = source_fig.sih_net
        target_fig.ih_extra = source_fig.sih_extra
        target_fig.ih_carriage = source_fig.sih_carriage
        target_fig.ih_vat = source_fig.sih_vat
        target_fig.ih_discount = source_fig.sih_discount
        target_fig.ih_e_vat = source_fig.sih_e_vat
        target_fig.ih_c_vat = source_fig.sih_c_vat
        target_sub.ih_status = source_sub.sih_status
        target_sub.ih_status_p = source_sub.sih_status_p
        target_sub.ih_status_l = source_sub.sih_status_l
        target_sub.ih_status_c = source_sub.sih_status_c
        target_sub.ih_status_a = source_sub.sih_status_a
        target_sub.ih_status_i = source_sub.sih_status_i
        target_sub.ih_lines = source_sub.sih_lines
        target_sub.ih_deduct_days = source_sub.sih_deduct_days
        target_sub.ih_deduct_amt = source_sub.sih_deduct_amt
        target_sub.ih_deduct_vat = source_sub.sih_deduct_vat
        target_sub.ih_days = source_sub.sih_days
        target_sub.ih_cr = source_sub.sih_cr
        target_sub.ih_day_book_flag = source_sub.sih_day_book_flag
        target_sub.ih_update = source_sub.sih_update
    line_view = getattr(record, "invoice_line")
    line = buffer.invoice_line
    if line_view is None and line is not None:
        line_view = _new_caller_line_view()
        setattr(record, "invoice_line", line_view)
    if line_view is not None and line is not None:
        line_view.il_invoice = buffer.ws_sih_invoice
        line_view.il_line = buffer.ws_sih_test
        line_view.il_product = line.sil_product
        line_view.il_pa = line.sil_pa
        line_view.il_qty = line.sil_qty
        line_view.il_type = line.sil_type
        line_view.il_description = line.sil_description
        line_view.il_net = line.sil_net
        line_view.il_unit = line.sil_unit
        line_view.il_discount = line.sil_discount
        line_view.il_vat = line.sil_vat
        line_view.il_vat_code = line.sil_vat_code
        line_view.il_update = line.sil_update
        line_view.il_back_ordered = line.sil_back_ordered


def _fs_cobol_files_used(flat_statuses: object) -> bool:
    """``88 FS-Cobol-Files-Used value zero.`` [copybooks/wssystem.cob:L113]

    The single condition name that chooses between the ISAM path and the RDB path.
    ``File-System-Used`` zero means COBOL files.
    """
    file_system_used = getattr(flat_statuses, "file_system_used", None)
    if file_system_used is None:
        return False
    return int(file_system_used) == 0
