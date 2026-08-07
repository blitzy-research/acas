"""`acas019` and its bridge `otm3MT` - the `SAITM3-REC` sales open-item table.

The data-access module for the OTM3 entity: the sales ledger's unpaid-item
register, written and applied by `sl060` and cleared by `sl100`.

The date and batch columns are binary integers, so their values arrive as `int`
and their arithmetic truncates as integer arithmetic does - which is what makes
`sl100`'s payment-days figures reproducible
[sales/sl100.cbl:L503], [sales/sl100.cbl:L511].

Cursor positioning follows the bridge's declared key metadata, so a `START`
followed by `READ NEXT` walks the order the frozen program walked.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Callable, Final, Mapping, Protocol, Sequence

from acas_posting.dal.connection import (
    TransportSecurity,
    cobol_string_delimited_by_space,
    transport_category,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    EXTRA_READ_ORDERS,
    SEQUENTIAL_READ_START,
    TABLE_OF_KEYNAMES,
    CursorSlot,
    CursorState,
    CursorStateTable,
    KeyOfReference,
    OrderQuoting,
)
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    is_duplicate_key_bridge_level,
    log_cobol_stop,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
    sanitise_for_log,
    start_access_type_is_valid,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.otm3 import (
    Filler1,
    Filler2,
    Oi3Key,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OpenItemRecord3,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__ = (
    "dispatch",
    "otm3_mt",
    "ACCESS_TYPE_RELATION_ARMS",
    "BRIDGE_FUNCTIONS",
    "BRIDGE_PARAGRAPH_NUMBERS",
    "BRIDGE_PROGRAM_ID",
    "COLUMNS",
    "COLUMN_NAMES",
    "ColumnBinding",
    "FlatFileMedium",
    "HANDLER_FUNCTIONS",
    "HANDLER_PARAGRAPH_NUMBERS",
    "HANDLER_PROGRAM_ID",
    "KEY_OF_REFERENCE",
    "LOAD_SEQUENCE",
    "RECORD_LENGTH",
    "SIGN_LOSS_COLUMNS",
    "TABLE_NAME",
    "TdSaitm3Rec",
    "UNLOAD_SEQUENCE",
    "WRITE_ONLY_COLUMNS",
    "WS_LOG_FILE_NO_FLAT_FILE",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "WS_MYSQL_EDIT_PICTURE",
    "WsTempEd",
    "WsTempEdBatch",
    "WsTempEdKey",
    "ws_mysql_edit",
    "ba_acas_dal_process",
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
    "ba150_process_read_next",
    "ba151_reread",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba999_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "otm3mt_ca_process_logs",
    "otm3mt_ca_exit",
    "aa_process_flat_file",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_move_inv_data",
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
    "acas019_ca_process_logs",
    "acas019_ca_exit",
)

_LOG: Final = logging.getLogger(__name__)


HANDLER_PROGRAM_ID: Final = "acas019"
BRIDGE_PROGRAM_ID: Final = "otm3MT"
TABLE_NAME: Final = "SAITM3-REC"

RECORD_LENGTH: Final = 118

#: ``move 3 to WS-Log-System`` [common/acas019.cbl:L240].
WS_LOG_SYSTEM: Final = int(LogSystem.SL)

#: ``move 15 to WS-Log-File-No`` [common/acas019.cbl:L241] - the value on the flat-file
#: path, which never reaches ``ba010`` and so never sees the overwrite below.
WS_LOG_FILE_NO_FLAT_FILE: Final = 15

#: ``move 25 to WS-Log-File-no`` [common/acas019.cbl:L557] - anomaly N-log. The RDB path
#: reaches this through ``perform ba-Process-RDBMS``, which enters the section at
#: ``ba010-Test-WS-Rec-Size``.
WS_LOG_FILE_NO_RDB: Final = 25

#: ``WS-File-Key pic x(64)`` [copybooks/wsfnctn.cob:L52]. Every log string this module
#: builds is truncated into this width exactly as a COBOL ``MOVE`` would.
WS_FILE_KEY_WIDTH: Final = 64

WS_LOG_WHERE_WIDTH: Final = 231

#: ``77 Display-Blk pic x(75) value spaces.`` [common/acas019.cbl:L196] - the handler's
#: own screen buffer.
_DISPLAY_BLK_WIDTH: Final = 75

#: ``03 SL901 pic x(31) value "SL901 Note error and hit return".``
#: [common/acas019.cbl:L207]. Displayed at 2401 immediately before the dropped ``accept``
#: [:L581, :L585], so its own instruction no longer applies.
#:
#: DECLARED AND DELIBERATELY UNREFERENCED. The declaration is a fact about the frozen
#: ``Error-Messages`` group and R-5 keeps it verbatim, but the literal's whole text is the
#: acknowledgement half of the 904 diagnostic, and quoting an acknowledgement prompt in a
#: log line is still emitting it. Only ``_SL904``, which names the error, reaches a record.
_SL901: Final = "SL901 Note error and hit return"

#: ``03 SL904 pic x(32) value "SL904 Program Error: Temp rec = ".``
#: [common/acas019.cbl:L208], with the maintainer's own continuation comment on the next
#: line.
_SL904: Final = "SL904 Program Error: Temp rec = "

#: The handler's nine-code dispatch, in the SOURCE ORDER of the ``evaluate``
#: [common/acas019.cbl:L283-L302]. Code 6 is spare, and 32/33 are absent - see docstring
#: C1.
HANDLER_FUNCTIONS: Final = (
    int(FileFunction.OPEN),
    int(FileFunction.CLOSE),
    int(FileFunction.READ_NEXT),
    int(FileFunction.READ_INDEXED),
    int(FileFunction.WRITE),
    int(FileFunction.RE_WRITE),
    int(FileFunction.DELETE),
    int(FileFunction.START),
    # ANOMALY N-codes-32-33, THE HANDLER'S HALF: 32 and 33 are ABSENT here.
)

#: The bridge's eleven-code dispatch, in the source order of ITS ``evaluate``
#: [common/otm3MT.cbl:L406-L429]: the handler's nine, plus the two sorted reads that
#: [copybooks/wsfnctn.cob:L103-L104] declares for OTM3/OTM5.
BRIDGE_FUNCTIONS: Final = HANDLER_FUNCTIONS + (
    int(FileFunction.READ_BY_BATCH),
    int(FileFunction.READ_BY_CUST),
)

#: ``move NNN to WS-No-Paragraph`` in the handler's flat-file paragraphs. Anomaly
#: N-noparagraph-collision.
HANDLER_PARAGRAPH_NUMBERS: Final = MappingProxyType(
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

#: ``move N to ws-No-Paragraph`` in the bridge. Two collisions inside the bridge itself.
BRIDGE_PARAGRAPH_NUMBERS: Final = MappingProxyType(
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
        "ba140-Process-Read-Next": 21,
        "ba141-Reread": 22,
        "ba150-Process-Read-Next": 21,
        "ba151-Reread": 22,
        "ba998-Free": 20,
    }
)

#: The single key of reference, from the bridge's own metadata table
#: [common/otm3MT.scb:L249-L251] / [common/otm3MT.cbl:L248-L258]: ``OI3-KEY``, offset
#: 0001, length 0015, type ``'STR'``.
KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[TABLE_NAME][0]

#: ``evaluate Access-Type`` [common/otm3MT.cbl:L779-L787], transcribed. Arm 9 is
#: declared and unreachable, because the guard above it admits 5..8 only - anomaly
#: N-start-997-vs-998.
ACCESS_TYPE_RELATION_ARMS: Final = MappingProxyType(
    {
        int(AccessType.EQUAL_TO): "=  ",
        int(AccessType.LESS_THAN): "<  ",
        int(AccessType.GREATER_THAN): ">  ",
        int(AccessType.NOT_LESS_THAN): ">= ",
        int(AccessType.NOT_GREATER_THAN): "<= ",
    }
)

#: The relation and low key the sequential read positions with
#: [common/otm3MT.cbl:L504-L505], through the shared table so the two modules cannot
#: drift apart.
_SEQUENTIAL_START: Final = SEQUENTIAL_READ_START[TABLE_NAME]

#: The sorted-read metadata for codes 32 and 33 - slot, predicate presence and locator -
#: taken from the shared table.
_EXTRA_READS: Final = EXTRA_READ_ORDERS[TABLE_NAME]

#: The ORDER BY clauses of ``ba140`` and ``ba150``, transcribed CHARACTER FOR CHARACTER
#: from the frozen literals [common/otm3MT.cbl:L1000-L1007] and [:L1153-L1159] rather
#: than rebuilt from :data:`_EXTRA_READS`.
_SORTED_ORDER_BY_QUOTING: Final = OrderQuoting.STRING_CONSTANT
_SORTED_ORDER_BY_TEXT: Final = MappingProxyType(
    {
        int(FileFunction.READ_BY_BATCH): (
            " ORDER BY "
            "'OI3-INVOICE', 'OI3-DAT' ASC, "
            "'OI3-TYPE' DESC, "
            "'OI3-BATCH-ITEM', 'OI3-BATCH-NOS' ASC "
        ),
        int(FileFunction.READ_BY_CUST): (
            " ORDER BY "
            "'OI3-CUSTOMER', 'OI3-DAT', "
            "'OI3-INVOICE', 'OI3-TYPE' ASC "
        ),
    }
)

#: ``move "..." to WS-File-Key`` literals, transcribed. Reproduced verbatim because they
#: are the only trace the compiled system leaves of which path it took.
_FILE_KEY_OPEN: Final = "OPEN SL OTM3"
_FILE_KEY_CLOSE: Final = "CLOSE SL OTM3"
_FILE_KEY_NO_DATA: Final = "No Data"
_FILE_KEY_SORTED: Final = "Sorted"
_FILE_KEY_EOF: Final = "EOF"
_FILE_KEY_EOF2: Final = "EOF2"
_FILE_KEY_EOF3: Final = "EOF3"
_FILE_KEY_FLAT_EOF: Final = "EOF"
_FILE_KEY_FAILED_ACTION: Final = "Failed action"

# WS-MYSQL-EDIT - the edited picture through which EVERY number becomes SQL text. `01
# WS-MYSQL-EDIT PIC -Z(18)9.9(9).` [common/otm3MT.cbl:L226] Thirty character positions:
# pos 1 the sign.

WS_MYSQL_EDIT_PICTURE: Final = "-Z(18)9.9(9)"
_EDIT_LENGTH: Final = 30
_EDIT_INTEGER_FIRST_POSITION: Final = 2
_EDIT_INTEGER_LAST_POSITION: Final = 20
_EDIT_INTEGER_POSITIONS: Final = _EDIT_INTEGER_LAST_POSITION - _EDIT_INTEGER_FIRST_POSITION + 1
_EDIT_POINT_POSITION: Final = 21
_EDIT_DECIMAL_FIRST_POSITION: Final = 22
_EDIT_DECIMAL_POSITIONS: Final = 9


def ws_mysql_edit(value: Decimal | int) -> str:
    """Build the 30-character ``WS-MYSQL-EDIT`` image of ``value``.

    Reproduces ``move <numeric> to WS-MYSQL-EDIT`` for the picture at
    [common/otm3MT.cbl:L226]. The image is what the bridge then slices; see
    :func:`_edit_slice`.

    Args:
        value: A ``Decimal`` or ``int``. Never a binary floating-point value.

    Returns:
        Exactly ``_EDIT_LENGTH`` characters.
    """
    amount = value if isinstance(value, Decimal) else Decimal(int(value))
    if not amount.is_finite():
        # A non-finite value cannot arrive from the frozen schema or from the record
        # layer, both of which carry only fixed-point fields. Rather than raise - this
        # module never raises, per [common/acas019.cbl:L617] - the condition is logged
        # and rendered as zero, which is what an `initialize`d host variable holds.
        #  THE VALUE ITSELF IS NOT LOGGED. It is a monetary or quantity figure
        #  from a posting, which the safe-event schema forbids in a record
        #  (CWE-532); the table and the condition are what identify the fault, and
        #  the caller that produced it is named by the traceback of its own tests.
        #  This record is NOT a narration of frozen control flow - `ws_mysql_edit`
        #  has no such arm - it is a programming-error guard on an input rule R-2
        #  makes impossible, so it is kept at ERROR rather than removed.
        _LOG.error(
            "ws_mysql_edit received a non-finite value; rendering the zero image. "
            "No field of %s can hold one",
            TABLE_NAME,
        )
        amount = Decimal(0)

    # Split sign from digits through the value's own representation rather than by
    # negating it.
    sign, significand, exponent = amount.as_tuple()
    negative = sign == 1
    magnitude = "".join(str(digit) for digit in significand)

    if exponent >= 0:
        integer_digits = magnitude + "0" * int(exponent)
        fraction_digits = "0" * _EDIT_DECIMAL_POSITIONS
    else:
        # `-exponent` fractional digits are present.
        present = int(-exponent)
        padded = magnitude.rjust(present + 1, "0")
        integer_digits = padded[:-present]
        fraction_digits = (padded[-present:] + "0" * _EDIT_DECIMAL_POSITIONS)[
            :_EDIT_DECIMAL_POSITIONS
        ]

    # `Z(18)9`: right-justify in nineteen positions and let the padding BE the zero
    # suppression, because a suppressed leading zero is exactly a space.
    integer_image = integer_digits.lstrip("0") or "0"
    integer_image = integer_image[-_EDIT_INTEGER_POSITIONS:].rjust(
        _EDIT_INTEGER_POSITIONS
    )

    image = f"{'-' if negative else ' '}{integer_image}.{fraction_digits}"
    return image[:_EDIT_LENGTH]


def _edit_slice(image: str, start: int, length: int) -> str:
    """COBOL reference modification ``WS-MYSQL-EDIT(start:length)``, 1-based."""
    first = start - 1
    return image[first : first + length]


def _render_integer(value: int, digits: int) -> str:
    """Render an integer host variable as the bridge does: one slice, sign dropped.

    The window is derived from the host variable's own digit count rather than hard-
    coded, because the dictionary is the authority on that count (rule R-5).
    """
    start = _EDIT_INTEGER_LAST_POSITION - digits + 1
    return _edit_slice(ws_mysql_edit(value), start, digits).strip()


def _render_decimal(value: Decimal, integer_digits: int, scale: int) -> str:
    """Render a scaled host variable as the bridge does: two slices joined by a point.

    THE INTEGER SLICE IS TRIMMED AND THE FRACTION SLICE IS NOT. The integer window is
    derived exactly as in :func:`_render_integer`.
    """
    image = ws_mysql_edit(value)
    integer_part = _edit_slice(
        image, _EDIT_INTEGER_LAST_POSITION - integer_digits + 1, integer_digits
    ).strip()
    fraction_part = _edit_slice(image, _EDIT_DECIMAL_FIRST_POSITION, scale)
    return f"{integer_part}.{fraction_part}"


def _cobol_move_alphanumeric(value: str, width: int) -> str:
    """``MOVE`` of an alphanumeric item into ``PIC X(width)``."""
    return value[:width].ljust(width)


# The 28-column mapping, DERIVED from the committed data dictionary. AAP section 0.8.1:
# "Data dictionary first ... every Python field definition cites its entry.


@dataclass(frozen=True)
class ColumnBinding:
    """One column of ``SAITM3-REC``, with everything needed to render and place it.

    Every instance is built by :func:`_build_columns` from a single
    ``dictionary.loader`` entry, so each carries its dictionary key and citation and
    nothing about it is transcribed (rule R-5).
    """

    column_name: str
    ordinal: int
    dictionary_key: str
    citation: str
    quoted_column: str
    sql_type: str
    column_unsigned: bool
    is_primary_key: bool
    column_comment: str
    hv_name: str
    hv_attribute: str
    hv_picture: str
    hv_signed: bool
    hv_digits: int | None
    hv_integer_digits: int | None
    hv_scale: int | None
    hv_character_length: int | None
    copybook_field: str
    copybook_source: str
    signedness_drift: bool
    unloaded_to_record: bool
    derivation_kind: str
    derivation_expression: str
    load_source: str

    @property
    def is_character(self) -> bool:
        """True when the host variable is ``PIC X(n)`` and the value is text."""
        return self.hv_character_length is not None and self.hv_digits is None

    @property
    def is_scaled(self) -> bool:
        """True when the host variable carries a ``V9(n)`` fraction."""
        return self.hv_scale is not None and self.hv_scale > 0

    @property
    def is_derived(self) -> bool:
        """True for the two columns the bridge assembles rather than copies."""
        return self.derivation_kind != ""

    def initial_value(self) -> str | int | Decimal:
        """The value ``initialize TD-SAITM3-REC`` leaves in this host variable.

        [common/otm3MT.cbl:L1339] is the FIRST statement of the load, which is why every
        column of this table can be ``NOT NULL`` and why this module must default rather
        than omit - AAP section 0.6.2.
        """
        if self.is_character:
            return " " * int(self.hv_character_length or 0)
        if self.is_scaled:
            return Decimal(0).scaleb(0).quantize(
                Decimal(1).scaleb(-int(self.hv_scale or 0)), rounding=ROUND_DOWN
            )
        return 0

    def coerce(self, value: str | int | Decimal) -> str | int | Decimal:
        """Apply the ``MOVE`` into this host variable, receiving-field rules and all.

        1. Alphanumeric receivers pad or truncate on the right. This is where the ``OI-
        Description`` width drift 25 -> 32 materialises as seven trailing spaces
        (anomaly N-desc-width), and where ``OI-Type`` and ``OI-Status`` stop being
        numbers (anomaly N-numeric-to-char). 2.
        """
        if self.is_character:
            text = value if isinstance(value, str) else _display_digits(value, self)
            return _cobol_move_alphanumeric(text, int(self.hv_character_length or 0))

        if self.is_scaled:
            amount = value if isinstance(value, Decimal) else Decimal(int(value))
            amount = amount.quantize(
                Decimal(1).scaleb(-int(self.hv_scale or 0)), rounding=ROUND_DOWN
            )
            return _drop_sign_for_unsigned_receiver(amount, self)

        whole = int(value) if not isinstance(value, Decimal) else int(value.to_integral_value(rounding=ROUND_DOWN))
        return _drop_sign_for_unsigned_receiver(whole, self)

    def render(self, value: str | int | Decimal) -> str:
        """Render the host variable exactly as the bridge renders it into SQL text."""
        if self.is_character:
            text = value if isinstance(value, str) else str(value)
            return text.rstrip(" ")
        if self.is_scaled:
            amount = value if isinstance(value, Decimal) else Decimal(int(value))
            return _render_decimal(
                amount, int(self.hv_integer_digits or 0), int(self.hv_scale or 0)
            )
        whole = int(value) if not isinstance(value, Decimal) else int(value)
        return _render_integer(whole, int(self.hv_digits or 0))


def _display_digits(value: int | Decimal, binding: ColumnBinding) -> str:
    """Convert a binary or display-numeric COBOL value into the digit characters a ``PIC
    X(n)`` host variable receives.

    Anomaly N-binary-to-char and anomaly N-numeric-to-char both land here.
    """
    width = int(binding.hv_character_length or 0)
    whole = int(value)
    digits = "".join(character for character in str(whole) if character.isdigit())
    return digits.rjust(width, "0")[-width:] if width else digits


def _drop_sign_for_unsigned_receiver(
    value: int | Decimal, binding: ColumnBinding
) -> int | Decimal:
    """The single named helper for anomaly N-signloss."""
    if binding.hv_signed or value >= 0:
        return value
    #  NO RECORD HERE. The frozen `move` into an unsigned host variable
    #  [see `binding.load_source`] narrows in silence - it writes no status, sets no
    #  flag and displays nothing - so a record was invented (R-4), and the silence
    #  IS anomaly N-signloss as the register describes it. The record it replaced
    #  also interpolated the value being narrowed, which is a posted figure
    #  (CWE-532). The anomaly is documented in `ANOMALIES` below and in
    #  `docs/migration/anomaly-log.md`, where a reader can find it without an
    #  operator having to see it once per column per row.
    return 0 - value


def _load_line(binding: ColumnBinding) -> int:
    """The source line of this column's ``move`` inside ``bb000-HV-Load``.

    Each dictionary entry records its own load site, e.g. ``common/otm3MT.cbl:L1345``
    for the derived key.
    """
    _, _, line = binding.load_source.rpartition(":L")
    return int(line) if line.isdigit() else 1 << 30


def _build_columns() -> tuple[ColumnBinding, ...]:
    """Read the 28 columns of ``SAITM3-REC`` from the committed data dictionary."""
    bindings: list[ColumnBinding] = []
    for entry in loader.entries_for_table(TABLE_NAME):
        column = entry.column
        host_variable = entry.bridge_host_variable
        copybook_field = entry.copybook
        derivation = entry.derivation
        bindings.append(
            ColumnBinding(
                column_name=column.name,
                ordinal=int(column.ordinal),
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                quoted_column=quote_identifier(column.name),
                sql_type=column.sql_type,
                column_unsigned=bool(column.unsigned),
                is_primary_key=bool(column.is_primary_key),
                column_comment=column.comment or "",
                hv_name=host_variable.name,
                hv_attribute=host_variable.name.replace("-", "_").lower(),
                hv_picture=host_variable.picture or "",
                hv_signed=bool(host_variable.signed),
                hv_digits=host_variable.digits,
                hv_integer_digits=host_variable.integer_digits,
                hv_scale=host_variable.scale,
                hv_character_length=host_variable.character_length,
                copybook_field=copybook_field.name if copybook_field else "",
                # `CopybookField.source` is ALREADY a full `<path>:L<n>` locator - the
                # dictionary stores it that way, and `.file` is the same path without
                # the line.
                copybook_source=(
                    copybook_field.source if copybook_field is not None else ""
                ),
                signedness_drift=bool(loader.drift_for(entry.key).signedness),
                unloaded_to_record=bool(host_variable.unloaded_to_record),
                derivation_kind=(
                    str(derivation.kind.value) if derivation is not None else ""
                ),
                derivation_expression=(
                    derivation.expression if derivation is not None else ""
                ),
                load_source=host_variable.load_source or "",
            )
        )
    return tuple(bindings)


COLUMNS: Final[tuple[ColumnBinding, ...]] = _build_columns()

#: The column names, in the same order. Frozen so the statement text cannot vary between
#: processes (rule R-6).
COLUMN_NAMES: Final[tuple[str, ...]] = tuple(binding.column_name for binding in COLUMNS)

_COLUMN_BY_NAME: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in COLUMNS}
)

#: The four host variables anomaly N-signloss applies to, derived from the dictionary's
#: own signedness drift rather than listed by hand - ``OI3-DAT``, ``OI3-DEDUCT-DAYS``,
#: ``OI3-DAYS``, ``OI3-DATE-CLEARED``.
SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = tuple(
    binding.column_name for binding in COLUMNS if binding.signedness_drift
)

#: The two columns the bridge writes and never reads back - anomaly N-two-write-only-
#: columns.
WRITE_ONLY_COLUMNS: Final[tuple[str, ...]] = tuple(
    binding.column_name for binding in COLUMNS if not binding.unloaded_to_record
)

#: ``bb000-HV-Load``'s move order [common/otm3MT.cbl:L1341-L1374], derived by ordering
#: the columns on the load site each dictionary entry records for itself.
LOAD_SEQUENCE: Final[tuple[str, ...]] = tuple(
    binding.column_name
    for binding in sorted(
        COLUMNS, key=lambda item: (_load_line(item), item.ordinal)
    )
)

#: ``bb100-UnloadHVs``'s move order [common/otm3MT.cbl:L1386-L1413], TRANSCRIBED because
#: it is the one order the dictionary cannot supply - it records only WHETHER a column
#: is unloaded, not where.
UNLOAD_SEQUENCE: Final[tuple[str, ...]] = (
    "OI3-INVOICE",
    "OI3-CUSTOMER",
    "OI3-DAT",
    "OI3-BATCH-NOS",
    "OI3-BATCH-ITEM",
    "OI3-TYPE",
    "OI3-DESCRIPTION",
    "OI3-HOLD-FLAG",
    "OI3-UNAPL",
    "OI3-P-C",
    "OI3-NET",
    "OI3-EXTRA",
    "OI3-CARRIAGE",
    "OI3-VAT",
    "OI3-DISCOUNT",
    "OI3-E-VAT",
    "OI3-C-VAT",
    "OI3-PAID",
    "OI3-STATUS",
    "OI3-DEDUCT-DAYS",
    "OI3-DEDUCT-AMT",
    "OI3-DEDUCT-VAT",
    "OI3-DAYS",
    "OI3-CR",
    "OI3-APPLIED",
    "OI3-DATE-CLEARED",
)


def _verify_unload_sequence() -> None:
    """Cross-check the transcribed unload order against the dictionary's own flags.

    A disagreement is logged rather than raised. Raising here would make a diagnostic
    unable to be imported, and this module's contract is that it never raises
    [common/acas019.cbl:L617].
    """
    transcribed = set(UNLOAD_SEQUENCE)
    expected = {binding.column_name for binding in COLUMNS if binding.unloaded_to_record}
    if transcribed != expected or len(UNLOAD_SEQUENCE) != len(transcribed):
        _LOG.error(
            "UNLOAD_SEQUENCE disagrees with the data dictionary for %s: "
            "only-in-transcription=%s only-in-dictionary=%s duplicates=%d. "
            "The authority is [common/otm3MT.cbl:L1386-L1413]",
            TABLE_NAME,
            sorted(transcribed - expected),
            sorted(expected - transcribed),
            len(UNLOAD_SEQUENCE) - len(transcribed),
        )
    # The success arm emits NOTHING. A per-import summary of the column counts is a
    # restatement of the data dictionary, which is the authority for all of it and is
    # committed as an artifact; logging it made every import of this module write a
    # record no operator acts on. Only the DISAGREEMENT above is reportable.


_verify_unload_sequence()


# TD-SAITM3-REC - the bridge's host-variable group. `/MYSQL VAR\ ACASDB
# TABLE=SAITM3-REC,HV` [common/otm3MT.cbl:L293-L296] `01 TD-SAITM3-REC.`
# [common/otm3MT.cbl:L301-L329] The 28 host variables in DECLARATION order.


@dataclass
class TdSaitm3Rec:
    """The host-variable group, one attribute per column, in declaration order.

    Attribute names are the host-variable names lowercased with hyphens replaced, and
    :attr:`ColumnBinding.hv_attribute` is derived the same way from the dictionary, so
    the generic accessors below and these declarations cannot drift apart.
    """

    hv_oi3_key: str = " " * 15
    hv_oi3_customer: str = " " * 7
    hv_oi3_invoice: int = 0
    hv_oi3_dat: int = 0
    hv_oi3_batch: str = " " * 8
    hv_oi3_batch_nos: str = " " * 5
    hv_oi3_batch_item: str = " " * 3
    hv_oi3_type: str = " "
    hv_oi3_description: str = " " * 32
    hv_oi3_hold_flag: str = " "
    hv_oi3_unapl: str = " "
    hv_oi3_p_c: Decimal = Decimal("0.00")
    hv_oi3_net: Decimal = Decimal("0.00")
    hv_oi3_extra: Decimal = Decimal("0.00")
    hv_oi3_carriage: Decimal = Decimal("0.00")
    hv_oi3_vat: Decimal = Decimal("0.00")
    hv_oi3_discount: Decimal = Decimal("0.00")
    hv_oi3_e_vat: Decimal = Decimal("0.00")
    hv_oi3_c_vat: Decimal = Decimal("0.00")
    hv_oi3_paid: Decimal = Decimal("0.00")
    hv_oi3_status: str = " "
    hv_oi3_deduct_days: int = 0
    hv_oi3_deduct_amt: Decimal = Decimal("0.00")
    hv_oi3_deduct_vat: Decimal = Decimal("0.00")
    hv_oi3_days: int = 0
    hv_oi3_cr: int = 0
    hv_oi3_applied: str = " "
    hv_oi3_date_cleared: int = 0

    @classmethod
    def initialize(cls) -> TdSaitm3Rec:
        """``initialize TD-SAITM3-REC`` [common/otm3MT.cbl:L1339].

        The FIRST statement of the load, and the reason every column of this table can
        be declared ``NOT NULL``: an unset host variable holds zero or spaces, never a
        database null. Widths and scales come from the dictionary.
        """
        group = cls()
        for binding in COLUMNS:
            setattr(group, binding.hv_attribute, binding.initial_value())
        return group

    def value_of(self, binding: ColumnBinding) -> str | int | Decimal:
        """Read one host variable."""
        return getattr(self, binding.hv_attribute)

    def store(self, binding: ColumnBinding, value: str | int | Decimal) -> None:
        """``move <record field> to <host variable>`` - the MOVE, not an assignment.

        :meth:`ColumnBinding.coerce` applies the receiving-field rules, which is where
        anomaly N-signloss, anomaly N-binary-to-char and anomaly N-numeric-to-char all
        take effect.
        """
        setattr(self, binding.hv_attribute, binding.coerce(value))

    def rendered(self, binding: ColumnBinding) -> str:
        """The SQL text form of one host variable - see :meth:`ColumnBinding.render`."""
        return binding.render(self.value_of(binding))


# The staging records the two derived columns are assembled in.


@dataclass
class WsTempEdKey:
    """``WS-Temp-ED-Key`` - the 15-character primary key, assembled from two fields.

    Anomaly N-two-write-only-columns begins here.
    """

    ws_temp_ed_customer: str = " " * 7
    ws_temp_ed_invoice: int = 0

    @property
    def image(self) -> str:
        """The group's 15 bytes: ``x(7)`` then ``9(8)``, in DECLARATION order.

        ``move WS-Temp-Ed-Key to HV-OI3-KEY`` [common/otm3MT.cbl:L1345] - the statement
        with no terminating period between punctuated neighbours (anomaly
        N-punctuation).
        """
        customer = _cobol_move_alphanumeric(self.ws_temp_ed_customer, 7)
        invoice = str(int(self.ws_temp_ed_invoice)).rjust(8, "0")[-8:]
        return f"{customer}{invoice}"


@dataclass
class WsTempEdBatch:
    """``WS-Temp-ED-Batch`` and its ``pic 9(8)`` redefinition ``WS-Temp-ED-Batch9``.

    The second half of anomaly N-two-write-only-columns, and the whole of anomaly
    N-binary-to-char.
    """

    ws_temp_ed_batch_nos: int = 0
    ws_temp_ed_batch_item: int = 0

    @property
    def batch9(self) -> str:
        """``WS-Temp-ED-Batch9`` - the same 8 bytes read as one ``pic 9(8)``.

        ``move WS-Temp-ED-Batch9 to HV-OI3-BATCH`` [common/otm3MT.cbl:L1351].
        """
        nos = str(int(self.ws_temp_ed_batch_nos)).rjust(5, "0")[-5:]
        item = str(int(self.ws_temp_ed_batch_item)).rjust(3, "0")[-3:]
        return f"{nos}{item}"


@dataclass
class WsTempEd:
    """``WS-Temp-ED`` - the HANDLER's own logging-key builder, not the bridge's.

    Anomaly N-casing in its purest form: three casings of one name in three consecutive
    lines.
    """

    ws_temp_ed_1: str = " " * 7
    ws_temp_ed_2: int = 0

    @property
    def image(self) -> str:
        """The group's 15 bytes, in declaration order - customer then invoice."""
        customer = _cobol_move_alphanumeric(self.ws_temp_ed_1, 7)
        invoice = str(int(self.ws_temp_ed_2)).rjust(8, "0")[-8:]
        return f"{customer}{invoice}"


def _initialize_oi_header(*, with_filler: bool) -> OiHeader:
    """``initialize WS-OTM3-Record`` over the LINKAGE view, with or without ``FILLER``.

    Anomaly N-initialize, and a verified refinement of it. The bridge writes
    ``initialize WS-OTM3-Record with filler`` at three sites [common/otm3MT.cbl:L626,
    :L1123, :L1277] and the plain form at one [:L1384] - the widest such split in the
    checkout.
    """
    # NO RECORD HERE. `initialize` displays nothing, and the equivalence argument the
    # record used to carry is an argument about the SOURCE, which belongs in this
    # docstring - where it is - and not in a line emitted once per record initialised.
    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(oi_nos=" " * 6, oi_check=0),
            oi_invoice=0,
        ),
        filler_1=Filler1(
            oi_date=0,
            oi_batch=OiBatch(oi_b_nos=0, oi_b_item=0),
            oi_type=0,
            oi_description=" " * 25,
            oi_hold_flag=" ",
            oi_unapl=" ",
            filler_2=Filler2(
                oi_p_c=Decimal("0.00"),
                oi_net=Decimal("0.00"),
                # `OI-Approp redefines OI-Net` [copybooks/slwsoi.cob:L38-L39] - the same
                # bytes under a second name, which is why it has no column of its own
                # (anomaly N-oi-approp-redefine).
                oi_approp=Decimal("0.00"),
                oi_extra=Decimal("0.00"),
                oi_carriage=Decimal("0.00"),
                oi_vat=Decimal("0.00"),
                oi_discount=Decimal("0.00"),
                oi_e_vat=Decimal("0.00"),
                oi_c_vat=Decimal("0.00"),
                oi_paid=Decimal("0.00"),
            ),
            oi_status=0,
            oi_deduct_days=0,
            oi_deduct_amt=Decimal("0.00"),
            oi_deduct_vat=Decimal("0.00"),
            oi_days=0,
            oi_cr=0,
            oi_applied=" ",
            oi_date_cleared=0,
        ),
    )


def _copy_oi_header(source: OiHeader, target: OiHeader) -> None:
    """Overwrite ``target``'s fields from ``source`` - a group move between two OI-Headers.

    ``bb100-UnloadHVs`` writes into ``WS-OTM3-Record``, which is the LINKAGE item the
    CALLER owns [common/otm3MT.cbl:L611-L615] - the bridge does not return a record, it
    mutates the caller's.
    """
    target.oi_key.oi_customer.oi_nos = source.oi_key.oi_customer.oi_nos
    target.oi_key.oi_customer.oi_check = source.oi_key.oi_customer.oi_check
    target.oi_key.oi_invoice = source.oi_key.oi_invoice
    source_filler, target_filler = source.filler_1, target.filler_1
    target_filler.oi_date = source_filler.oi_date
    target_filler.oi_batch.oi_b_nos = source_filler.oi_batch.oi_b_nos
    target_filler.oi_batch.oi_b_item = source_filler.oi_batch.oi_b_item
    target_filler.oi_type = source_filler.oi_type
    target_filler.oi_description = source_filler.oi_description
    target_filler.oi_hold_flag = source_filler.oi_hold_flag
    target_filler.oi_unapl = source_filler.oi_unapl
    source_money, target_money = source_filler.filler_2, target_filler.filler_2
    target_money.oi_p_c = source_money.oi_p_c
    target_money.oi_net = source_money.oi_net
    target_money.oi_approp = source_money.oi_approp
    target_money.oi_extra = source_money.oi_extra
    target_money.oi_carriage = source_money.oi_carriage
    target_money.oi_vat = source_money.oi_vat
    target_money.oi_discount = source_money.oi_discount
    target_money.oi_e_vat = source_money.oi_e_vat
    target_money.oi_c_vat = source_money.oi_c_vat
    target_money.oi_paid = source_money.oi_paid
    target_filler.oi_status = source_filler.oi_status
    target_filler.oi_deduct_days = source_filler.oi_deduct_days
    target_filler.oi_deduct_amt = source_filler.oi_deduct_amt
    target_filler.oi_deduct_vat = source_filler.oi_deduct_vat
    target_filler.oi_days = source_filler.oi_days
    target_filler.oi_cr = source_filler.oi_cr
    target_filler.oi_applied = source_filler.oi_applied
    target_filler.oi_date_cleared = source_filler.oi_date_cleared


def _copy_open_item_record_3(
    source: OpenItemRecord3, target: OpenItemRecord3
) -> None:
    """Overwrite ``target``'s fields from ``source`` - a group move between two FILE views.
    """
    target.oi3_key.oi3_customer = source.oi3_key.oi3_customer
    target.oi3_key.oi3_invoice = source.oi3_key.oi3_invoice
    target.oi3_date = source.oi3_date
    target.filler_1 = source.filler_1


def _initialize_oi_header_in_place(record: OiHeader, *, with_filler: bool) -> None:
    """``initialize WS-OTM3-Record with filler`` applied to the CALLER's record.

    [common/otm3MT.cbl:L626, :L1123, :L1277] - the three ``with filler`` sites, all
    inside a reread's error branch. The linkage item belongs to the caller, so the
    initialise must land there rather than on a copy.
    """
    _copy_oi_header(_initialize_oi_header(with_filler=with_filler), record)


def _initialize_open_item_record_3(
    record: OpenItemRecord3, *, with_filler: bool
) -> OpenItemRecord3:
    """``initialize Open-Item-Record-3`` over the FILE view [common/acas019.cbl:L379].

    Here the ``FILLER`` phrase DOES change the outcome, because the file view declares
    an elementary ``filler pic x(99)`` [copybooks/slwsoi3.cob:L16] holding 99 of the 118
    bytes.
    """
    return OpenItemRecord3(
        oi3_key=Oi3Key(oi3_customer=" " * 7, oi3_invoice=0),
        oi3_date=0,
        filler_1=(" " * 99) if with_filler else record.filler_1,
    )


def _blank_open_item_record_3() -> OpenItemRecord3:
    """A file-view record with every byte at its initial value.

    Used only where the handler has no prior record to preserve, so the distinction
    :func:`_initialize_open_item_record_3` draws does not arise.
    """
    return OpenItemRecord3(
        oi3_key=Oi3Key(oi3_customer=" " * 7, oi3_invoice=0),
        oi3_date=0,
        filler_1=" " * 99,
    )


def _oi_key_image(record: OiHeader) -> str:
    """``WS-OTM3-Record (1:15)`` - the 15 bytes the bridge slices for every predicate.

    Every ``WS-Where`` the bridge builds takes the key straight out of the RECORD BUFFER
    rather than out of a host variable: ``WS-OTM3-Record (K:L)`` with ``K`` and ``L``
    taken from the key metadata table [common/otm3MT.cbl:L653-L654, :L662].
    """
    customer = _cobol_move_alphanumeric(record.oi_key.oi_customer.oi_nos, 6)
    check = str(int(record.oi_key.oi_customer.oi_check)).rjust(1, "0")[-1:]
    invoice = str(int(record.oi_key.oi_invoice)).rjust(8, "0")[-8:]
    return f"{customer}{check}{invoice}"


def _oi_customer_image(record: OiHeader) -> str:
    """``OI-Customer`` as the 7 bytes a group move transfers.

    ``move OI-Customer to HV-OI3-CUSTOMER`` [common/otm3MT.cbl:L1343] moves a GROUP to
    ``PIC X(7)``, so the transfer is byte-for-byte: ``OI-Nos`` ``x(6)`` followed by
    ``OI-Check`` ``9`` rendered as one digit character.
    """
    nos = _cobol_move_alphanumeric(record.oi_key.oi_customer.oi_nos, 6)
    check = str(int(record.oi_key.oi_customer.oi_check)).rjust(1, "0")[-1:]
    return f"{nos}{check}"


def _oi3_key_image(record: OpenItemRecord3) -> str:
    """``Open-Item-Record-3``'s own 15-byte key: ``OI3-Customer`` ``x(7)`` + ``9(8)``.

    The file view collapses the caller's ``x(6)`` + ``9`` customer into a single
    ``x(7)`` [copybooks/slwsoi3.cob:L13], so the two 15-byte images coincide byte for
    byte while being described differently - which is what lets the handler move between
    the views.
    """
    customer = _cobol_move_alphanumeric(record.oi3_key.oi3_customer, 7)
    invoice = str(int(record.oi3_key.oi3_invoice)).rjust(8, "0")[-8:]
    return f"{customer}{invoice}"


def bb000_hv_load(record: OiHeader) -> tuple[TdSaitm3Rec, WsTempEdKey, WsTempEdBatch]:
    """``bb000-HV-Load`` - fill the host-variable group from the record.

    Transcribed statement for statement from [common/otm3MT.cbl:L1339-L1374]. The move
    ORDER is :data:`LOAD_SEQUENCE`, which the dictionary supplies from each column's own
    recorded load site.

    Returns:
        The loaded group and the two staging records, so a caller (or a test) can
            inspect the derivations that produced ``HV-OI3-KEY`` and ``HV-OI3-BATCH``.
    """
    # `initialize TD-SAITM3-REC.` [common/otm3MT.cbl:L1339] - FIRST, which is what makes
    # every column NOT NULL-able and why nothing is ever bound as a database null.
    group = TdSaitm3Rec.initialize()
    temp_key = WsTempEdKey()
    temp_batch = WsTempEdBatch()

    group.store(_COLUMN_BY_NAME["OI3-INVOICE"], record.oi_key.oi_invoice)
    temp_key.ws_temp_ed_invoice = int(record.oi_key.oi_invoice)

    customer_image = _oi_customer_image(record)
    group.store(_COLUMN_BY_NAME["OI3-CUSTOMER"], customer_image)
    temp_key.ws_temp_ed_customer = customer_image

    # [:L1345] `move WS-Temp-Ed-Key to HV-OI3-KEY` <- no terminating period THE FIRST
    # DERIVED COLUMN.
    group.store(_COLUMN_BY_NAME["OI3-KEY"], temp_key.image)

    # [:L1347-L1348] `move OI-B-Nos to HV-OI3-BATCH-NOS WS-Temp-ED-Batch-Nos.` A COMP
    # field into PIC X(5): anomaly N-binary-to-char.
    group.store(_COLUMN_BY_NAME["OI3-BATCH-NOS"], record.filler_1.oi_batch.oi_b_nos)
    temp_batch.ws_temp_ed_batch_nos = int(record.filler_1.oi_batch.oi_b_nos)

    group.store(_COLUMN_BY_NAME["OI3-BATCH-ITEM"], record.filler_1.oi_batch.oi_b_item)
    temp_batch.ws_temp_ed_batch_item = int(record.filler_1.oi_batch.oi_b_item)

    # [:L1351] `move WS-Temp-ED-Batch9 to HV-OI3-BATCH.` THE SECOND DERIVED COLUMN, read
    # through the `pic 9(8)` redefinition.
    group.store(_COLUMN_BY_NAME["OI3-BATCH"], temp_batch.batch9)

    # [:L1353] `move OI-Date to HV-OI3-DAT` - SEVENTH here, THIRD in the unload, and
    # renamed `Date` -> `DAT` on the way. Signed source, unsigned receiver.
    group.store(_COLUMN_BY_NAME["OI3-DAT"], record.filler_1.oi_date)

    # [:L1354] `move OI-Type to HV-OI3-TYPE` - `pic 9` into `PIC X(1)`, anomaly
    # N-numeric-to-char. The legend for the values is quoted in docstring PART 3.
    group.store(_COLUMN_BY_NAME["OI3-TYPE"], record.filler_1.oi_type)

    # [:L1355] `move OI-Description to HV-OI3-DESCRIPTION` - x(25) into X(32), which
    # pads with seven trailing spaces: anomaly N-desc-width.
    group.store(_COLUMN_BY_NAME["OI3-DESCRIPTION"], record.filler_1.oi_description)

    group.store(_COLUMN_BY_NAME["OI3-HOLD-FLAG"], record.filler_1.oi_hold_flag)
    group.store(_COLUMN_BY_NAME["OI3-UNAPL"], record.filler_1.oi_unapl)

    # [:L1358-L1366] the nine money fields, signed at all three layers. `OI-Approp` is
    # NOT among them - it redefines `OI-Net` and has no column
    # [copybooks/slwsoi.cob:L38-L39], anomaly N-oi-approp-redefine.
    money = record.filler_1.filler_2
    group.store(_COLUMN_BY_NAME["OI3-P-C"], money.oi_p_c)
    group.store(_COLUMN_BY_NAME["OI3-NET"], money.oi_net)
    group.store(_COLUMN_BY_NAME["OI3-EXTRA"], money.oi_extra)
    group.store(_COLUMN_BY_NAME["OI3-CARRIAGE"], money.oi_carriage)
    group.store(_COLUMN_BY_NAME["OI3-VAT"], money.oi_vat)
    group.store(_COLUMN_BY_NAME["OI3-DISCOUNT"], money.oi_discount)
    group.store(_COLUMN_BY_NAME["OI3-E-VAT"], money.oi_e_vat)
    group.store(_COLUMN_BY_NAME["OI3-C-VAT"], money.oi_c_vat)
    group.store(_COLUMN_BY_NAME["OI3-PAID"], money.oi_paid)

    # [:L1367] `pic 9` into `PIC X(1)` again - anomaly N-numeric-to-char. The `88`s over
    # this field, `S-Open` and `S-Closed`, live in `records/otm3.py`.
    group.store(_COLUMN_BY_NAME["OI3-STATUS"], record.filler_1.oi_status)

    # [:L1368] second site of anomaly N-signloss: `binary-Char` -> `9(03)`.
    group.store(_COLUMN_BY_NAME["OI3-DEDUCT-DAYS"], record.filler_1.oi_deduct_days)

    # [:L1369-L1370] signed at all three layers HERE, and unsigned at both in the
    # invoice bridge [common/slinvoiceMT.cbl:L415-L416] - anomaly N-deduct-sign-
    # divergence.
    group.store(_COLUMN_BY_NAME["OI3-DEDUCT-AMT"], record.filler_1.oi_deduct_amt)
    group.store(_COLUMN_BY_NAME["OI3-DEDUCT-VAT"], record.filler_1.oi_deduct_vat)

    # [:L1371] third site of anomaly N-signloss.
    group.store(_COLUMN_BY_NAME["OI3-DAYS"], record.filler_1.oi_days)

    # [:L1372] `HV-OI3-CR PIC S9(10) COMP` - SIGNED, unlike the invoice bridge's `HV-IH-
    # CR PIC 9(10) COMP` [common/slinvoiceMT.cbl:L418]. Anomaly N-oi3-cr-sign-survives.
    group.store(_COLUMN_BY_NAME["OI3-CR"], record.filler_1.oi_cr)

    # [:L1373-L1374] the last is the fourth site of anomaly N-signloss.
    group.store(_COLUMN_BY_NAME["OI3-APPLIED"], record.filler_1.oi_applied)
    group.store(_COLUMN_BY_NAME["OI3-DATE-CLEARED"], record.filler_1.oi_date_cleared)

    return group, temp_key, temp_batch


# bb100-UnloadHVs Section.


def _unload_customer(record: OiHeader, value: str | int | Decimal) -> None:
    """``move HV-OI3-CUSTOMER to OI-Customer`` [common/otm3MT.cbl:L1387].

    ``PIC X(7)`` into the GROUP, so the 7 bytes split back into ``OI-Nos`` ``x(6)`` and
    ``OI-Check`` ``9``.
    """
    text = _cobol_move_alphanumeric(str(value), 7)
    record.oi_key.oi_customer.oi_nos = text[:6]
    check = text[6:7].strip()
    record.oi_key.oi_customer.oi_check = int(check) if check.isdigit() else 0


def _unload_integer_from_character(value: str | int | Decimal) -> int:
    """``move <PIC X(n)> to <pic 9(n)>`` - an alphanumeric host variable into a numeric
    record field, which is the reverse of anomalies N-binary-to-char and N-numeric-to-
    char.

    COBOL reads the digit characters and treats spaces as zero. Non-numeric content in a
    column the bridge wrote is impossible, and is carried as zero rather than rejected.
    """
    text = str(value).strip()
    return int(text) if text.isdigit() else 0


def _unload_scaled(value: str | int | Decimal, scale: int) -> Decimal:
    """``move <COMP scaled HV> to <COMP-3 scaled record field>`` - same scale, no rounding.

    The receiving field's scale is 2 for every scaled field of this record, matching the
    host variable, so the truncation never actually discards a digit.
    """
    amount = value if isinstance(value, Decimal) else Decimal(str(value))
    return amount.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_DOWN)


#: One setter per unloaded column, keyed by column name, each citing its own ``move``.
_UNLOAD_SETTERS: Final[
    Mapping[str, Callable[[OiHeader, str | int | Decimal], None]]
] = MappingProxyType(
    {
        "OI3-INVOICE": lambda record, value: setattr(
            record.oi_key, "oi_invoice", int(value)
        ),
        "OI3-CUSTOMER": _unload_customer,
        "OI3-DAT": lambda record, value: setattr(
            record.filler_1, "oi_date", int(value)
        ),
        "OI3-BATCH-NOS": lambda record, value: setattr(
            record.filler_1.oi_batch, "oi_b_nos", _unload_integer_from_character(value)
        ),
        "OI3-BATCH-ITEM": lambda record, value: setattr(
            record.filler_1.oi_batch, "oi_b_item", _unload_integer_from_character(value)
        ),
        "OI3-TYPE": lambda record, value: setattr(
            record.filler_1, "oi_type", _unload_integer_from_character(value)
        ),
        # [:L1394] `move HV-OI3-DESCRIPTION to OI-Description` - X(32) into x(25), so
        # the width drift of anomaly N-desc-width truncates on the way BACK.
        "OI3-DESCRIPTION": lambda record, value: setattr(
            record.filler_1, "oi_description", _cobol_move_alphanumeric(str(value), 25)
        ),
        "OI3-HOLD-FLAG": lambda record, value: setattr(
            record.filler_1, "oi_hold_flag", _cobol_move_alphanumeric(str(value), 1)
        ),
        "OI3-UNAPL": lambda record, value: setattr(
            record.filler_1, "oi_unapl", _cobol_move_alphanumeric(str(value), 1)
        ),
        "OI3-P-C": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_p_c", _unload_scaled(value, 2)
        ),
        # `OI-Net` and `OI-Approp` are the SAME BYTES [copybooks/slwsoi.cob:L38-L39], so
        # the one move lands in both names. Anomaly N-oi-approp-redefine, from the read
        # side.
        "OI3-NET": lambda record, value: _unload_net_and_approp(record, value),
        "OI3-EXTRA": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_extra", _unload_scaled(value, 2)
        ),
        "OI3-CARRIAGE": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_carriage", _unload_scaled(value, 2)
        ),
        "OI3-VAT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_vat", _unload_scaled(value, 2)
        ),
        "OI3-DISCOUNT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_discount", _unload_scaled(value, 2)
        ),
        "OI3-E-VAT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_e_vat", _unload_scaled(value, 2)
        ),
        "OI3-C-VAT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_c_vat", _unload_scaled(value, 2)
        ),
        "OI3-PAID": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_paid", _unload_scaled(value, 2)
        ),
        "OI3-STATUS": lambda record, value: setattr(
            record.filler_1, "oi_status", _unload_integer_from_character(value)
        ),
        "OI3-DEDUCT-DAYS": lambda record, value: setattr(
            record.filler_1, "oi_deduct_days", int(value)
        ),
        "OI3-DEDUCT-AMT": lambda record, value: setattr(
            record.filler_1, "oi_deduct_amt", _unload_scaled(value, 2)
        ),
        "OI3-DEDUCT-VAT": lambda record, value: setattr(
            record.filler_1, "oi_deduct_vat", _unload_scaled(value, 2)
        ),
        "OI3-DAYS": lambda record, value: setattr(
            record.filler_1, "oi_days", int(value)
        ),
        "OI3-CR": lambda record, value: setattr(record.filler_1, "oi_cr", int(value)),
        "OI3-APPLIED": lambda record, value: setattr(
            record.filler_1, "oi_applied", _cobol_move_alphanumeric(str(value), 1)
        ),
        "OI3-DATE-CLEARED": lambda record, value: setattr(
            record.filler_1, "oi_date_cleared", int(value)
        ),
    }
)


def _unload_net_and_approp(record: OiHeader, value: str | int | Decimal) -> None:
    """``move HV-OI3-NET to OI-Net`` [common/otm3MT.cbl:L1398], both names at once.

    ``OI-Approp redefines OI-Net`` [copybooks/slwsoi.cob:L38-L39], so in COBOL there is
    one field with two names and the single move sets both views.
    """
    amount = _unload_scaled(value, 2)
    record.filler_1.filler_2.oi_net = amount
    record.filler_1.filler_2.oi_approp = amount


def bb100_unload_hvs(group: TdSaitm3Rec) -> OiHeader:
    """``bb100-UnloadHVs`` - build the record from the host-variable group.

    [common/otm3MT.cbl:L1384-L1413]. Twenty-six moves, in :data:`UNLOAD_SEQUENCE` order,
    which is neither the load order nor the column order (anomaly N-loadorder).
    """
    # `initialize WS-OTM3-Record.` [common/otm3MT.cbl:L1384] - the PLAIN form, against
    # `with filler` at the three other sites (anomaly N-initialize). Over this view the
    # two coincide; see `_initialize_oi_header`.
    record = _initialize_oi_header(with_filler=False)

    for column_name in UNLOAD_SEQUENCE:
        binding = _COLUMN_BY_NAME[column_name]
        _UNLOAD_SETTERS[column_name](record, group.value_of(binding))

    return record


# Working storage that OUTLIVES a single CALL. A COBOL sub-program's WORKING-STORAGE
# persists between CALLs unless the program is CANCELled, and both programs rely on
# that.


@dataclass
class _BridgeWorkingStorage:
    """``otm3MT``'s WORKING-STORAGE, less the presentation items (deviation D2)."""

    connection: object | None = None

    #: The three cursors of ``01 DAL-Data`` [common/otm3MT.cbl:L260-L270]: ``Most-
    #: Cursor-Set`` (PRIMARY, ``ba040``), ``Most-Cursor-Set-2`` (SECONDARY, ``ba140``,
    #: function 32) and ``Most-Cursor-Set-3`` (TERTIARY, ``ba150``, function 33).
    cursors: CursorStateTable = field(default_factory=CursorStateTable)

    #: ``MOST-Relation pic xxx`` [common/otm3MT.cbl:L261], set by ``ba060`` and read by
    #: the predicate it builds.
    most_relation: str = "   "

    #: The credentials carrier.
    system_record: SystemRecord | None = None

    #: ``WS-Temp-ED-Row pic 9(7)`` [common/otm3MT.cbl:L230] - anomaly N-deadfields. Used
    #: for nothing but rendering a row count into a log string.
    ws_temp_ed_row: int = 0

    #: ``WS-Body-Key pic x(9)`` [common/otm3MT.cbl:L280] - anomaly N-deadfields.
    ws_body_key: str = " " * 9

    #: ``A`` and ``B`` from the handler's record-size guard
    #: [common/acas019.cbl:L559-L570]. Zero means the paragraph has not run, the only
    #: thing the guard tests.
    ws_length_a: int = 0
    ws_length_b: int = 0

    #: The transport declaration handed to ``connection.py``, and it is ``None``:
    #: THIS HANDLER DECLARES NOTHING AND MUST NOT. There is no counterpart in the
    #: frozen bridge - ``call "MySQL_real_connect"`` [common/otm3MT.cbl:L459] passes
    #: host, user, password, schema, port and socket and NOTHING else, no
    #: certificate, no key, no verification mode - so the compiled system's
    #: transport is plaintext to whatever host the row names.
    #:
    #: ⭐ ``None`` MEANS "USE THE ONE INSTALLED POLICY", which
    #: ``connection.mysql_1000_open`` resolves from
    #: ``connection.connection_policy()``. An earlier revision defaulted this field
    #: to ``TransportSecurity(isolated_oracle=True)`` so that the container-hosted
    #: comparison database could be reached; that made THIS handler the only one of
    #: the twenty that declared a policy of its own, which is precisely the
    #: inconsistency the single boundary exists to remove - the same run would then
    #: have declared different things depending on which table it touched. The
    #: declaration now belongs to the deployment, is made once at the entry point,
    #: and reaches every handler identically.
    transport: TransportSecurity | None = None

    #: Whether the shipped placeholder credentials of
    #: [copybooks/wssystem.cob:L138-L139] may be used. ``None``, meaning THIS HANDLER
    #: DECLARES NOTHING: the compiled program connects with whatever the row holds and
    #: reports what the server says, so the decision belongs to the deployment's one
    #: installed ``ConnectionPolicy`` and not to any one table's working storage. Left
    #: as a slot rather than a constant so a disposable-server scenario can narrow it
    #: here if it ever needs to.
    allow_frozen_placeholder_credentials: bool | None = None


_BRIDGE: Final = _BridgeWorkingStorage()


def _reset_working_storage() -> None:
    """Return the module-level working storage to its ``VALUE`` clauses.

    Not a COBOL paragraph: the equivalent of ``CANCEL "otm3MT"``, which is how a COBOL
    caller discards a sub-program's working storage.
    """
    _BRIDGE.connection = None
    _BRIDGE.cursors = CursorStateTable()
    _BRIDGE.most_relation = "   "
    _BRIDGE.system_record = None
    _BRIDGE.ws_temp_ed_row = 0
    _BRIDGE.ws_body_key = " " * 9
    _BRIDGE.ws_length_a = 0
    _BRIDGE.ws_length_b = 0
    # The two security declarations are reset with everything else, and for two
    # reasons. Determinism (rule R-6): a declaration `dispatch` recorded for one
    # scenario must not survive into the next, or two runs of the same scenario
    # differ by whichever ran before them. And NON-INHERITANCE: a permissive
    # declaration is the one piece of state that must never be inherited by a
    # caller who did not ask for it.
    _BRIDGE.transport = None
    _BRIDGE.allow_frozen_placeholder_credentials = False


# File-Access accessors. Every status this module reports goes through these, so the
# `(FS-Reply, We-Error)` pair and the log fields are written in exactly one place each.


#: ``35`` - the ISAM "file not found" status the flat-file open path moves into ``FS-
#: Reply`` at [common/acas019.cbl:L313], and the ONE value this module produces that is
#: NOT a member of :class:`~acas_posting.dal.status.FsReply`.
FS_REPLY_FILE_NOT_FOUND: Final = 35


def _as_fs_reply(value: FsReply | int) -> FsReply | int:
    """Name a raw ``FS-Reply`` value where a name exists, and pass it through where none
    does.

    Returns the :class:`FsReply` member for the six mandated values so that logging and
    comparisons read as the vocabulary does, and the plain integer for
    :data:`FS_REPLY_FILE_NOT_FOUND`. Never raises.
    """
    if isinstance(value, FsReply):
        return value
    raw = int(value)
    try:
        return FsReply(raw)
    except ValueError:
        return raw


#: The status range that raises the COBOL ``INVALID KEY`` condition.
_INVALID_KEY_STATUS_RANGE: Final = range(21, 25)


def _invalid_key_condition(status: FsReply | int) -> bool:
    """Would this file status raise ``INVALID KEY`` on an indexed file?

    ONE - every verb sets ``FS-Reply`` whether or not its conditional phrase fires,
    which is why ``aa020`` can write ``open input`` and then simply ask ``if Fs-Reply
    not = zero`` [common/acas019.cbl:L311-L312] with no status clause of its own.
    """
    return int(status) in _INVALID_KEY_STATUS_RANGE


def _write_status(
    file_access: FileAccess, fs_reply: FsReply | int, we_error: WeError | int
) -> tuple[int, int]:
    """``move <n> to fs-reply`` / ``move <n> to WE-Error`` - and return the pair.

    ``We-Error`` is ``pic 999`` and ``Fs-Reply`` is ``pic 99``
    [copybooks/wsfnctn.cob:L23-L38], so both are unsigned display integers.
    """
    reply = _as_fs_reply(fs_reply)
    file_access.fs_reply = int(reply)
    file_access.we_error = int(we_error)
    return reply, int(we_error)


def _write_file_key(file_access: FileAccess, text: str) -> None:
    """``move <literal or field> to WS-File-Key`` - truncated into ``pic x(64)``.

    [copybooks/wsfnctn.cob:L52]. A COBOL ``MOVE`` truncates on the right and pads with
    spaces, and both happen here so the logged key is byte-comparable with the compiled
    system's.
    """
    file_access.logging_data.ws_file_key = _cobol_move_alphanumeric(
        text, WS_FILE_KEY_WIDTH
    )


def _write_log_where(file_access: FileAccess, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - truncated into ``pic x(231)``.

    [copybooks/wsfnctn.cob:L53]. ``J`` is the STRING pointer AFTER the transfer, so the
    slice carries one trailing space beyond the text - anomaly N-string-pointer-overrun,
    reproduced by :func:`_ws_where_1_to_j`.
    """
    file_access.logging_data.ws_log_where = _cobol_move_alphanumeric(
        text, WS_LOG_WHERE_WIDTH
    )


def _write_sql_fields(
    file_access: FileAccess,
    *,
    sql_err: str | None = None,
    sql_msg: str | None = None,
    sql_state: str | None = None,
) -> None:
    """Write the three diagnostic fields, each truncated into its declared width.

    ``SQL-Err``, ``SQL-Msg`` and ``SQL-State`` [copybooks/wsfnctn.cob:L44-L56]; the
    widths come from ``dal/status.py`` so every handler module truncates identically.
    Messages are passed through :func:`sanitise_for_log` first, because a driver message
    can quote the statement and a statement can quote a value.
    """
    logging_data = file_access.logging_data
    if sql_err is not None:
        logging_data.sql_err = _cobol_move_alphanumeric(sql_err, SQL_ERR_WIDTH)
    if sql_msg is not None:
        logging_data.sql_msg = _cobol_move_alphanumeric(
            sanitise_for_log(sql_msg, limit=SQL_MSG_WIDTH), SQL_MSG_WIDTH
        )
    if sql_state is not None:
        logging_data.sql_state = _cobol_move_alphanumeric(sql_state, SQL_STATE_WIDTH)


def _testing_1(dal_common: AcasDalCommonData) -> bool:
    """``Testing-1`` - ``SW-Testing = 1`` [copybooks/Test-Data-Flags.cob:L10-L16].

    Gates ``perform Ca-Process-Logs`` in both programs. Note anomaly N-nolog-on-dal: the
    handler's own logging paragraph carries ``*> Not called on DAL access as it does it
    already`` on its label line [common/acas019.cbl:L623].
    """
    return int(dal_common.sw_testing) == 1


def _testing_2(dal_common: AcasDalCommonData) -> bool:
    """``Testing-2`` - ``SW-Testing-2 = 1`` [copybooks/Test-Data-Flags.cob:L13-L16]."""
    return int(dal_common.sw_testing_2) == 1


# WS-Where and the statement text.


def _quoted_key_name() -> str:
    """``"`" KeyName (KOR-x1) delimited by space "`"`` - the key column, backtick-quoted.

    ``KeyName`` is ``pic x(30)`` and holds ``'OI3-KEY '`` [common/otm3MT.cbl:L249], so
    ``delimited by space`` is what reduces it to ``OI3-KEY``. Every identifier in this
    module goes through :func:`connection.quote_identifier`, without exception.
    """
    return quote_identifier(cobol_string_delimited_by_space(KEY_OF_REFERENCE.key_name))


_QUOTED_TABLE: Final = quote_identifier(TABLE_NAME)


def _ws_where_1_to_j(text: str) -> str:
    """``WS-Where (1:J)`` - the built text PLUS the one character the pointer overran.

    ``move 1 to J`` then ``STRING ...
    """
    return f"{text} "


def _key_predicate() -> str:
    """``` `OI3-KEY`="<record(1:15)>" ``` with the value bound - deviation D1."""
    return f"{_quoted_key_name()}=%s"


def _sequential_predicate() -> str:
    """``` `OI3-KEY` >= "000000000000000" ORDER BY `OI3-KEY` ASC ``` - ``ba040``'s SELECT.

    [common/otm3MT.cbl:L500-L513]. The relation and the low key come from
    ``cursor_state.SEQUENTIAL_READ_START`` so the two modules cannot drift; the literal
    spacing - ``" >= "`` with a space each side, against ``ba060``'s space-delimited
    relation with none - is transcribed.
    """
    key = _quoted_key_name()
    return (
        f"{key} {_SEQUENTIAL_START.relation.padded.strip()} "
        f'"{_SEQUENTIAL_START.low_key}"'
        f" ORDER BY {key} ASC"
    )


def _start_predicate(relation: str) -> str:
    """``ba060``'s predicate: relation from ``MOST-Relation``, then ORDER BY, then ASC.

    [common/otm3MT.cbl:L789-L802]. Three details are transcribed rather than tidied:
    ``MOST-relation delimited by space`` drops the padding so there is NO space between
    the column and the operator; the opening ``'"'`` follows immediately.
    """
    key = _quoted_key_name()
    operator = cobol_string_delimited_by_space(relation)
    return f"{key}{operator}%s ORDER BY {key} ASC  "


def _select_statement(predicate_1_to_j: str) -> str:
    """``SELECT * FROM `SAITM3-REC` WHERE <WS-Where (1:J)>;``"""
    return f"SELECT * FROM {_QUOTED_TABLE} WHERE {predicate_1_to_j};"


def _delete_statement(predicate_1_to_j: str) -> str:
    """``DELETE FROM `SAITM3-REC` WHERE <WS-Where (1:J)>`` - and NO semicolon.

    [common/otm3MT.cbl:L919-L925]. The INSERT [:L1788] and the UPDATE [:L2175] both end
    with ``";"``; this one ends with ``X"00"`` alone. Reproduced as written.
    """
    return f"DELETE FROM {_QUOTED_TABLE} WHERE {predicate_1_to_j}"


def _insert_statement() -> str:
    """``INSERT INTO `SAITM3-REC` SET `col`=%s, ... ;`` - ALL TWENTY-EIGHT columns.

    [common/otm3MT.cbl:L1426-L1789]. Column order is :data:`COLUMNS`, i.e.
    """
    assignments = ", ".join(f"{binding.quoted_column}=%s" for binding in COLUMNS)
    return f"INSERT INTO {_QUOTED_TABLE} SET {assignments};"


def _update_statement(predicate_trimmed: str) -> str:
    """``UPDATE `SAITM3-REC` SET <all 28> WHERE <TRIM(WS-Where (1:J))>;``

    [common/otm3MT.cbl:L1807-L2176]. THE PRIMARY KEY IS AMONG THE COLUMNS SET:
    ``OI3-KEY`` is assigned first [:L1815-L1818] and is also the whole of the predicate,
    so the statement sets the key to the value it is selected by. Harmless, and
    reproduced.
    """
    assignments = ", ".join(f"{binding.quoted_column}=%s" for binding in COLUMNS)
    return (
        f"UPDATE {_QUOTED_TABLE} SET {assignments} WHERE {predicate_trimmed};"
    )


def _insert_parameters(group: TdSaitm3Rec) -> tuple[str, ...]:
    """The 28 rendered values, in :data:`COLUMNS` order, to bind to the INSERT or UPDATE.

    Every value is the RENDERED TEXT, never the raw ``Decimal`` or ``int``: docstring C6
    establishes that the render is where the sign is dropped, so binding the numeric
    value would store something the compiled system never stored.
    """
    return tuple(group.rendered(binding) for binding in COLUMNS)


# The `mysql-procedures.cpy` primitives, at the level this bridge uses them. `COPY
# "mysql-procedures.cpy".` sits inside the bridge at [common/otm3MT.cbl:L1303], between
# `ba100-Bad-Function` and `ba998-Free`.


@dataclass(frozen=True)
class _CommandResult:
    """What a statement leaves behind for the calling paragraph to test.

    ``WS-MYSQL-Count-Rows`` is the field every paragraph branches on, and its meaning
    depends on the statement: affected rows after a command, stored rows after a store.
    """

    count_rows: int
    errno: str
    message: str
    sql_state: str
    rows: tuple[Mapping[str, object], ...] = ()

    @property
    def driver_reported_error(self) -> bool:
        """``if WS-MYSQL-Error-Number not = "0 "`` - the test, spelled once."""
        return self.errno != _ERRNO_CLEAN


#: ``WS-MYSQL-Error-Number`` when nothing went wrong. The paragraphs compare against the
#: literal ``"0 "``, so the clean value is a zero in a three-character field.
_ERRNO_CLEAN: Final = "0  "


def _materialise_rows(cursor: object) -> tuple[Mapping[str, object], ...]:
    """``MYSQL-1220-STORE-RESULT`` - pull EVERY qualifying row to the client.

    [copybooks/mysql-procedures.cpy:L187-L192] as performed at [common/otm3MT.cbl:L527,
    :L684, :L817, :L1020, :L1173]. The whole result is stored and ``MySQL_num_rows``
    counts THAT.
    """
    description = getattr(cursor, "description", None) or ()
    names = tuple(str(column[0]) for column in description)
    rows: list[Mapping[str, object]] = []
    fetchone = getattr(cursor, "fetchone")
    while True:
        row = fetchone()
        if row is None:
            return tuple(rows)
        if isinstance(row, Mapping):
            rows.append(MappingProxyType(dict(row)))
        else:
            rows.append(MappingProxyType(dict(zip(names, tuple(row)))))


def _mysql_1210_command(
    context: _BridgeContext,
    statement: str,
    parameters: Sequence[object] = (),
    *,
    store_result: bool = False,
) -> _CommandResult:
    """Issue one statement. Never raises; a driver failure becomes a status.

    Reproduces ``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``, optionally followed
    by ``PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT`` when the statement is a
    SELECT - which is exactly the pairing the frozen source uses.
    """
    connection = _BRIDGE.connection
    if connection is None:
        # `Ws-Mysql-Cid` is zero because no `ba020-Process-Open` has succeeded. The frozen
        # bridge would pass a null handle to the interface object and the query would fail,
        # which is the `Mysql-1100-Db-Error` path - so that is the status reported here,
        # with the RDB initialisation error the copybook itself uses.
        # ONE ERROR, through the shared reporter, so that every failure in every
        # handler renders with the same fields in the same order. The statement's
        # leading verb is no longer interpolated: it is the first token of the SQL
        # this module built, and the safe-event schema admits no SQL fragment at all
        # (CWE-532). The paragraph name identifies the site without it.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="_mysql_command",
            locator="[common/otm3MT.cbl:L458-L468]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="a statement was issued with no open connection; "
            "ba020-Process-Open has not succeeded",
        )
        status = mysql_1100_db_error(
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message="no open connection",
            sql_state="",
            command=statement,
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        return _CommandResult(
            count_rows=0,
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message="no open connection",
            sql_state="",
        )

    try:
        with execute_statement(connection, statement, tuple(parameters)) as cursor:
            if store_result:
                rows = _materialise_rows(cursor)
                return _CommandResult(
                    count_rows=len(rows),
                    errno=_ERRNO_CLEAN,
                    message="",
                    sql_state="",
                    rows=rows,
                )
            affected = int(getattr(cursor, "rowcount", 0) or 0)
            return _CommandResult(
                count_rows=max(affected, 0),
                errno=_ERRNO_CLEAN,
                message="",
                sql_state="",
            )
    except Exception as error:  # noqa: BLE001 - see below
        # EVERY driver failure takes this path, deliberately.
        errno = str(getattr(error, "errno", "") or "").strip() or "1"
        sql_state = str(getattr(error, "sqlstate", "") or "")
        message = str(getattr(error, "msg", None) or error)
        status = mysql_1100_db_error(
            errno=errno, message=message, sql_state=sql_state, command=statement
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        #  THE DRIVER'S TEXT IS NOT LOGGED. For this table it renders the whole
        #  statement and its bound values - the customer number, the invoice number
        #  and the deduction amounts - and `sanitise_for_log` escaped it rather than
        #  removing any of it (CWE-117 addressed, CWE-532 not). What remains is the
        #  errno, the SQLSTATE and the stable category derived from them, which is
        #  what an operator acts on.
        #  ONE ERROR, not two: `mysql_1100_db_error` above is the migration of
        #  `Mysql-1110-Report-Problem` [copybooks/mysql-procedures.cpy:L130-L137] and
        #  has already emitted the operator record. This site adds the paragraph
        #  identity the shared reporter cannot know, at the same level, and `message`
        #  is still RETURNED because `SQL-Msg` is a status field the paragraphs read.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="_mysql_command",
            locator="[copybooks/mysql-procedures.cpy:L127-L128]",
            sql_err=errno,
            sql_state=sql_state,
            detail="the statement failed; the calling paragraph's own row-count "
            "test then overwrites the (99, 911) pair, as the frozen bridge does",
        )
        return _CommandResult(
            count_rows=0,
            errno=errno,
            message=message,
            sql_state=sql_state,
        )


def _mysql_fetch_record(group: TdSaitm3Rec, row: Mapping[str, object]) -> None:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT HV-OI3-KEY ...``

    ALL TWENTY-EIGHT are fetched, including ``HV-OI3-KEY`` and ``HV-OI3-BATCH``: the two
    write-only columns ARE read into their host variables here and are then simply not
    unloaded into the record (anomaly N-two-write-only-columns). The asymmetry is in
    ``bb100-UnloadHVs``, not in the fetch.
    """
    for binding in COLUMNS:
        if binding.column_name in row:
            group.store(binding, row[binding.column_name])  # type: ignore[arg-type]
        else:
            # A column absent from the result is not a condition the frozen source has a
            # path for - `SELECT *` always returns all of them.
            _LOG.error(
                "%s: column %s absent from the result of a SELECT *; the host variable "
                "keeps its initialised value [%s]",
                BRIDGE_PROGRAM_ID,
                binding.column_name,
                binding.citation,
            )


@dataclass
class _BridgeContext:
    """``otm3MT``'s LINKAGE plus the per-CALL scratch its paragraphs share."""

    file_access: FileAccess
    dal_common: AcasDalCommonData
    record: OiHeader
    group: TdSaitm3Rec = field(default_factory=TdSaitm3Rec.initialize)
    ws_where: str = ""
    count_rows: int = 0
    return_code: int = 0
    fs_reply: int = FsReply.SUCCESS
    we_error: int = 0

    def status(self, fs_reply: FsReply | int, we_error: WeError | int) -> None:
        """Write a status pair into ``File-Access`` and remember it for the return."""
        self.fs_reply, self.we_error = _write_status(
            self.file_access, fs_reply, we_error
        )

    def slot_state(self, slot: CursorSlot) -> CursorState:
        """One of the three cursors of ``01 DAL-Data`` - docstring C5."""
        return _BRIDGE.cursors.state_for(TABLE_NAME, slot)


# The flat-file medium - deviation D3. `select Open-Item-File-3 assign ...


class FlatFileMedium(Protocol):
    """The six ISAM verbs ``acas019``'s flat-file paragraphs issue.

    Each method returns the ``FS-Reply`` the ``status fs-Reply`` clause of
    [copybooks/slseloi3.cob] would have written - ``0`` for success, ``23`` for a not-
    found key, ``35`` for a missing file, and so on.
    """

    def open_file(self, mode: str) -> FsReply:
        """``open input | i-o | output | extend Open-Item-File-3`` - ``aa020``."""

    def close_file(self) -> FsReply:
        """``close Open-Item-File-3`` - ``aa030``."""

    def read_next(self) -> tuple[FsReply, OpenItemRecord3 | None]:
        """``read Open-Item-File-3 next record at end ...`` - ``aa040``."""

    def read_indexed(self, key: str) -> tuple[FsReply, OpenItemRecord3 | None]:
        """``read Open-Item-File-3 key OI3-Key invalid key ...`` - ``aa050``."""

    def start(self, key: str, relation: str) -> FsReply:
        """``start Open-Item-File-3 key <rel> OI3-Key invalid key ...`` - ``aa060``."""

    def write(self, record: OpenItemRecord3) -> FsReply:
        """``write Open-Item-Record-3 invalid key ...`` - ``aa070``."""

    def delete(self, record: OpenItemRecord3) -> FsReply:
        """``delete Open-Item-File-3 record invalid key ...`` - ``aa080``."""

    def rewrite(self, record: OpenItemRecord3) -> FsReply:
        """``rewrite Open-Item-Record-3 invalid key ...`` - ``aa090``."""


class _AbsentFlatFileMedium:
    """The default medium: no ISAM store is present, so every verb fails.

    ``FsReply.ERROR`` (99) is returned rather than a made-up file status, and the handler's
    OWN branches then decide the outcome - ``aa020``'s ``if Fs-Reply not = zero`` becomes
    ``move 35 to fs-Reply``, ``aa050``'s ``invalid key`` phrase becomes ``move 21 to
    we-error fs-reply``, and so on. No status is invented by this module.

    Every call is reported ONCE, AT ERROR, through the shared reporter, because on the
    DAL path it cannot happen: per C2 ``acas019`` leaves for ``ba-Process-RDBMS`` before
    the dispatch, so reaching here in a migrated run means ``FS-Cobol-Files-Used`` was
    true, which no in-scope scenario sets. A verb that returns 99 to its caller is a
    FAILURE, and reporting it at WARNING put it below the level an operator watches.
    """

    def _absent(self, verb: str) -> FsReply:
        """Report the attempt and return 99, the one status this class ever produces."""
        log_handler_failure(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="_AbsentFlatFileMedium.%s" % verb,
            locator="[copybooks/slseloi3.cob]",
            fs_reply=int(FsReply.ERROR),
            detail="a flat-file verb was requested but no ISAM medium is present; "
            "the paragraph's own branch interprets the 99 (deviation D3)",
        )
        return FsReply.ERROR

    def open_file(self, mode: str) -> FsReply:
        """No file to open, so ``aa020``'s ``if Fs-Reply not = zero`` [:L312] decides.
        """
        return self._absent(f"open {mode}")

    def close_file(self) -> FsReply:
        """No file to close; ``aa030`` [:L349] does not test the reply."""
        return self._absent("close")

    def read_next(self) -> tuple[FsReply, OpenItemRecord3 | None]:
        """No record, so ``aa040`` takes its ``at end`` branch [:L375-L381]."""
        return self._absent("read next"), None

    def read_indexed(self, key: str) -> tuple[FsReply, OpenItemRecord3 | None]:
        """No record, so ``aa050`` reports ``21`` in both fields [:L422]."""
        return self._absent("read indexed"), None

    def start(self, key: str, relation: str) -> FsReply:
        """No cursor to position, so ``aa060``'s ``invalid key`` phrase decides."""
        return self._absent(f"start {relation}")

    def write(self, record: OpenItemRecord3) -> FsReply:
        """99 is outside the '2x' class, so ``aa070``'s phrase does NOT fire [:L495]."""
        return self._absent("write")

    def delete(self, record: OpenItemRecord3) -> FsReply:
        """99 is outside the '2x' class, so ``aa080``'s phrase does NOT fire [:L506]."""
        return self._absent("delete")

    def rewrite(self, record: OpenItemRecord3) -> FsReply:
        """99 is outside the '2x' class, so ``aa090``'s phrase does NOT fire [:L518]."""
        return self._absent("rewrite")


_FLAT_FILE_MEDIUM_ABSENT: Final[FlatFileMedium] = _AbsentFlatFileMedium()  # type: ignore[assignment]


# The cross-view group moves - deviation D4. `move Open-Item-Record-3 to WS-OTM3-Record`
# and its inverse are group moves between two arrangements of the same 118 bytes (C3).


def _move_file_record_to_linkage(
    file_record: OpenItemRecord3, linkage: OiHeader
) -> None:
    """``move Open-Item-Record-3 to WS-OTM3-Record`` - [common/acas019.cbl:L385, :L422].

    The FILE view's ``OI3-Key`` is one 15-character group; the LINKAGE view splits the
    same 15 bytes into ``OI-Customer`` (7, itself ``OI-Nos`` 6 plus ``OI-Check`` 1) and
    ``OI-Invoice`` (``pic 9(8)``).
    """
    key_image = _oi3_key_image(file_record)
    customer = _cobol_move_alphanumeric(key_image[:7], 7)
    linkage.oi_key.oi_customer.oi_nos = customer[:6]
    linkage.oi_key.oi_customer.oi_check = _character_digit(customer[6:7])
    linkage.oi_key.oi_invoice = _numeric_digits(key_image[7:15], "OI-Invoice")
    linkage.filler_1.oi_date = file_record.oi3_date


def _move_linkage_to_file_record(
    linkage: OiHeader, file_record: OpenItemRecord3
) -> None:
    """``move WS-OTM3-Record to Open-Item-Record-3`` - [:L491, :L502, :L514].

    The inverse of the above, and the first statement of ``aa070``, ``aa080`` and
    ``aa090`` alike.
    """
    key_image = _oi_key_image(linkage)
    file_record.oi3_key.oi3_customer = key_image[:7]
    file_record.oi3_key.oi3_invoice = _numeric_digits(key_image[7:15], "OI3-Invoice")
    file_record.oi3_date = linkage.filler_1.oi_date


def _character_digit(text: str) -> int:
    """``OI-Check pic 9`` receiving one character of a group move.

    A space or any other non-digit in that byte is what ``move spaces to OI3-Key``
    [common/acas019.cbl:L368] deliberately puts there - anomaly N-spaces-into-numeric -
    so it is taken as zero here rather than treated as an error.
    """
    stripped = text.strip()
    return int(stripped) if stripped.isdigit() else 0


def _numeric_digits(text: str, field_name: str) -> int:
    """Digits of a group move into a ``pic 9(n)`` receiver, spaces included.

    Anomaly N-spaces-into-numeric puts spaces into exactly such a field, and the
    compiled program carries them without complaint until something reads the field as a
    number.
    """
    stripped = text.strip()
    if stripped.isdigit():
        return int(stripped)
    if stripped:
        #  THE BYTES THEMSELVES ARE NOT LOGGED. They are whatever a group move
        #  put into the field, which on this record is part of a customer number or
        #  an invoice number - a business key even when it is malformed (CWE-532).
        #  The FIELD NAME is a record-layout identifier and is enough to locate it.
        _LOG.warning(
            "%s: %s received non-numeric bytes from a group move; taken as zero "
            "(anomaly N-spaces-into-numeric [common/acas019.cbl:L368])",
            HANDLER_PROGRAM_ID,
            field_name,
        )
    return 0


def ba_acas_dal_process(context: _BridgeContext) -> None:
    """``ba-ACAS-DAL-Process section.`` - [common/otm3MT.cbl:L370-L382].

    Not one of those six statements has a database effect, and the three fields they
    compute are read only by ``display ... at`` positions.
    """
    # NO RECORD HERE. Six statements were dropped and not one of them displays
    # anything, so announcing the drop is announcing an omission - which belongs in
    # this docstring and in `docs/migration/traceability.md`, where it is, and not in a
    # line emitted on every relational call.
    return None


def ba010_initialise(context: _BridgeContext) -> tuple[int, int]:
    """``ba010-Initialise.`` - [common/otm3MT.cbl:L384-L429]. Clear, then dispatch.

    ``We-Error`` and ``Fs-Reply`` ARRIVE FROM THE CALLER AND ARE NOT RESET. This is the
    bridge's own deliberate non-initialisation, and it is the second one in the call
    chain: the handler has an identical pair commented out at
    [common/acas019.cbl:L279-L280].
    """
    context.file_access.logging_data.sql_state = _cobol_move_alphanumeric(
        "0", SQL_STATE_WIDTH
    )
    # `We-Error` and `Fs-Reply` are NOT cleared: [:L386-L387] are commented out. The
    # caller's values stand. Anomaly N-initialise-partial.
    context.fs_reply = _as_fs_reply(context.file_access.fs_reply)
    context.we_error = int(context.file_access.we_error)
    _write_log_where(context.file_access, "")
    _write_file_key(context.file_access, "")
    context.file_access.logging_data.sql_msg = " " * SQL_MSG_WIDTH
    context.file_access.logging_data.sql_err = " " * SQL_ERR_WIDTH

    function = int(context.file_access.file_function)
    if function == int(FileFunction.OPEN):
        return ba020_process_open(context)
    if function == int(FileFunction.CLOSE):
        return ba030_process_close(context)
    if function == int(FileFunction.READ_NEXT):
        return ba040_process_read_next(context)
    if function == int(FileFunction.READ_INDEXED):
        return ba050_process_read_indexed(context)
    if function == int(FileFunction.WRITE):
        return ba070_process_write(context)
    if function == int(FileFunction.RE_WRITE):
        return ba090_process_rewrite(context)
    if function == int(FileFunction.DELETE):
        return ba080_process_delete(context)
    if function == int(FileFunction.START):
        return ba060_process_start(context)
    if function == int(FileFunction.READ_BY_BATCH):
        return ba140_process_read_next(context)
    if function == int(FileFunction.READ_BY_CUST):
        return ba150_process_read_next(context)
    return ba100_bad_function(context)


def ba020_process_open(context: _BridgeContext) -> tuple[int, int]:
    """``ba020-Process-Open.`` - [common/otm3MT.cbl:L430-L472]. Connect, then flag.

    Six ``string`` statements marshal the credentials, each one
    ``delimited by space`` followed by a ``X"00"`` terminator
    [common/otm3MT.cbl:L434-L457], in this order: schema, host, user, password, port,
    socket. ``connection.mysql_1000_open`` performs the identical marshalling from the
    identical six fields - the AAP forbids duplicating its credential load - so this
    paragraph reads them and hands them over rather than re-marshalling them into a
    connect call of its own. Only the transport CLASS is recorded; see the comment at the
    record itself.

    Then::

        move     1 to ws-No-Paragraph.                    [:L458]
        PERFORM  MYSQL-1000-OPEN  THRU MYSQL-1090-EXIT.   [:L459]
        if       fs-reply not = zero  go to ba999-end.    [:L460-L461]
        move    "OPEN SL OTM3" to WS-File-Key             [:L466]
        set     Cursor-Not-Active to true                 [:L467]
        go      to ba999-end.                             [:L468]

    ⭐ THE OPEN MODE IS NEVER CONSULTED. ``Access-Type`` distinguishes input, i-o, output
    and extend for the flat-file handler, and this paragraph reads none of them: a
    connection is a connection. That is the mechanism behind anomaly N-noopenoutput - an
    Open+Output through the DAL path is a plain connect and DELETES NOTHING, unlike
    ``acas008``, which coerces the function to delete-all [common/acas008.cbl:L313-L319].

    ⭐ ONLY THE PRIMARY CURSOR IS FLAGGED INACTIVE at [:L467]. ``Most-Cursor-Set-2`` and
    ``Most-Cursor-Set-3`` keep whatever they held across the CALL, so an open following a
    sorted read leaves that sorted cursor believing it is still active - the same
    one-of-three asymmetry as anomaly N-ba998-frees-primary-only, at the other end of the
    connection's life.

    Transfers: ``go to ba999-end`` twice, both Class 3.
    """
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba020-Process-Open"
    ]

    rdb = context.file_access.rdb_data
    #  THE ENDPOINT IS CLASSIFIED, NOT NAMED. This record used to carry the schema,
    #  the host, the port and the socket path. Withholding the user and the password was
    #  not enough: the four that remained are the deployment's own identity, they differ
    #  between every environment - so two runs of the same scenario could not produce the
    #  same line - and they are exactly what an attacker reading a log wants (CWE-532).
    #  `transport_category` answers the one question a record has to answer about a
    #  connect target, whether the credentials and the posted figures can be read off the
    #  wire, with one of five fixed tokens.
    _LOG.debug(
        "%s: ba020 connect [common/otm3MT.cbl:L434-L457] transport=%s",
        BRIDGE_PROGRAM_ID,
        transport_category(
            {
                "host": cobol_string_delimited_by_space(rdb.db_host),
                "unix_socket": cobol_string_delimited_by_space(rdb.db_socket),
            }
            if cobol_string_delimited_by_space(rdb.db_socket)
            else {"host": cobol_string_delimited_by_space(rdb.db_host)},
            _BRIDGE.transport,
        ),
    )

    system_record = _BRIDGE.system_record
    if system_record is None:
        # `Ws-Mysql-Cid` would be passed to `MySQL_real_connect` with blank credentials
        # and the connect would fail, which is the `Mysql-1100-Db-Error` path: (99, 911).
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="ba020-Process-Open",
            locator="[common/acas019.cbl:L586-L598]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="no system record in working storage: the handler's ba012 has "
            "not run, so DB-Schema and its five companions are unset",
        )
        status = mysql_1100_db_error(
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message="credentials not loaded",
            sql_state="",
            command="MySQL_real_connect",
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        context.status(status.fs_reply, status.we_error)
        return ba999_end(context)

    try:
        # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT` [:L459]. The credential load,
        # the three-step error ladder and the (99, 911) on failure all live in
        # `dal/connection.py`.
        outcome = mysql_1090_exit(
            mysql_1000_open(
                system_record,
                ws_no_paragraph=BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"],
                transport=_BRIDGE.transport,
                allow_frozen_placeholder_credentials=(
                    _BRIDGE.allow_frozen_placeholder_credentials
                ),
            )
        )
    except Exception as error:  # noqa: BLE001 - the never-raises contract, [:L617]
        # `connection.py`'s policy layer refuses a placeholder credential or an
        # unprotected non-local target by raising. The frozen program has no such notion,
        # and its only failure outcome for an open is the one below, so the refusal is
        # reported as that outcome rather than escaping this module.
        #  THE REFUSAL'S OWN TEXT IS NOT LOGGED. `connection.py` raises with a
        #  message that names the target it refused and, for a placeholder credential,
        #  the credential's own value; `sanitise_for_log` escaped it and removed none
        #  of it (CWE-532). The exception TYPE names the reason without naming the
        #  deployment, and the policy layer has already reported its own refusal once.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="ba020-Process-Open",
            locator="[common/otm3MT.cbl:L459-L461]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="the connect was refused by the connection policy layer (%s); "
            "reported as the frozen open-failure outcome rather than raised, per "
            "the never-raises contract" % type(error).__name__,
        )
        status = mysql_1100_db_error(
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message=str(error),
            sql_state="",
            command="MySQL_real_connect",
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        context.status(status.fs_reply, status.we_error)
        return ba999_end(context)

    outcome.apply_to_logging_data(context.file_access.logging_data)
    context.status(outcome.fs_reply, outcome.we_error)
    if int(outcome.fs_reply) != 0:
        return ba999_end(context)

    _BRIDGE.connection = outcome.connection
    _write_file_key(context.file_access, _FILE_KEY_OPEN)
    context.slot_state(CursorSlot.PRIMARY).set_cursor_not_active()
    return ba999_end(context)


def ba030_process_close(context: _BridgeContext) -> tuple[int, int]:
    """``ba030-Process-Close.`` - [common/otm3MT.cbl:L474-L486]. Free, then disconnect.

    ⭐ THE ``perform`` AT [:L476] IS NOT A ``go to``, AND THE DIFFERENCE IS LOAD-BEARING.
    """
    # `if Cursor-Active perform ba998-Free.` [:L475-L476]. PERFORM, so the fall-through
    # into `ba999-end` does NOT happen here.
    if context.slot_state(CursorSlot.PRIMARY).cursor_active():
        ba998_free(context)

    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba030-Process-Close"
    ]
    _write_file_key(context.file_access, _FILE_KEY_CLOSE)
    mysql_1980_close(_BRIDGE.connection)  # type: ignore[arg-type]
    mysql_1999_exit()
    _BRIDGE.connection = None
    return ba999_end(context)


def _capture_driver_error(context: _BridgeContext, result: _CommandResult) -> None:
    """``call "MySQL_errno" ... "MySQL_sqlstate" ... "MySQL_error"`` - the shared ladder.
    """
    _write_sql_fields(
        context.file_access,
        sql_state=result.sql_state,
        sql_err=result.errno if result.driver_reported_error else None,
        sql_msg=result.message if result.driver_reported_error else None,
    )


def ba040_process_read_next(context: _BridgeContext) -> tuple[int, int]:
    """``ba040-Process-Read-Next.`` - [common/otm3MT.cbl:L488-L562]. SELECT, then fetch.

    ⭐ ``K`` AND ``L`` ARE COMPUTED AND NEVER USED. The predicate embeds a LITERAL low
    key, not a slice of the record, so the offset and length fetched at [:L495-L496] are
    dead here.
    """
    primary = context.slot_state(CursorSlot.PRIMARY)
    if primary.cursor_not_active():
        # `set KOR-x1 to 1` / `move KOR-offset (KOR-x1) to K` / `... to L` [:L494-L496].
        # Fetched exactly as the COBOL does, and - uniquely among the paragraphs that
        # fetch them - never used, because the predicate embeds a literal low key.
        # NO RECORD HERE. Three frozen `move`s that display nothing, whose whole
        # interest is that the values go unused - a fact about the SOURCE, recorded in
        # the comment above and in `docs/migration/anomaly-log.md`, not an event.
        # `KEY_OF_REFERENCE.kor_offset` and `.kor_length` are the two values the
        # frozen `move`s copy; nothing binds them here because nothing reads them.
        # `move spaces to WS-Where` / `move 1 to J` / the STRING [:L497-L513].
        context.ws_where = _ws_where_1_to_j(_sequential_predicate())
        _write_log_where(context.file_access, context.ws_where)
        context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            "ba040-Process-Read-Next"
        ]

        statement = _select_statement(context.ws_where)
        result = _mysql_1210_command(context, statement, store_result=True)
        context.count_rows = result.count_rows
        _write_file_key(context.file_access, _SEQUENTIAL_START.low_key)
        if _testing_2(context.dal_common):
            #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
            #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
            #  customer and invoice key as a literal - or the statement itself. Both are
            #  forbidden in a record by the safe-event schema (CWE-532), and
            #  `sanitise_for_log` escaped them rather than removing them. This was a
            #  developer's trace read at the terminal beside the running program; nothing
            #  acts on it operationally. `WS-Where` is still BUILT and still stored in
            #  `Logging-Data`, because the bridge's own statements read it (R-3).
            pass

        if result.count_rows == 0:
            _capture_driver_error(context, result)
            context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
            _write_file_key(context.file_access, _FILE_KEY_NO_DATA)
            return ba999_end(context)

        primary.store_result(result.rows)
        primary.set_cursor_active()
        _BRIDGE.ws_temp_ed_row = result.count_rows
        # `string "> 0 got cnt=" WS-Temp-ED-Row " recs for INVOICE-RECORD Table"`
        # [:L551-L556].
        _write_file_key(
            context.file_access,
            f"> 0 got cnt={_BRIDGE.ws_temp_ed_row:07d}"
            " recs for INVOICE-RECORD Table",
        )
        ba999_end(context)

    return ba041_reread(context)


def _fetch_one_row(
    context: _BridgeContext,
    state: CursorState,
    *,
    paragraph: str,
    slot_locator: str,
) -> tuple[int, int]:
    """The body shared, statement for statement, by ``ba041``, ``ba141`` and ``ba151``.

    ⭐ THREE END-OF-FILE PATHS, THREE DIFFERENT ``WS-File-Key`` VALUES, ONE STATUS PAIR.
    ``"EOF"`` is the real one; ``"EOF2"`` is guarded by ``*> no data but should not
    happen here`` [:L615]; ``"EOF3"`` by ``*> should not happen as tested prior``
    [:L635].
    """
    _write_log_where(context.file_access, "")
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        paragraph
    ]
    context.return_code = 0

    row = state.fetch_record()
    if row is None:
        context.return_code = -1
    else:
        _mysql_fetch_record(context.group, row)
        context.count_rows = 1

    if context.return_code == -1:                                # [:L607]
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))  # [:L608-L609]
        _write_file_key(context.file_access, _FILE_KEY_EOF)       # [:L610]
        state.set_cursor_not_active()                             # [:L611] - see locator
        # NO RECORD HERE. `set Cursor-Not-Active to true` displays nothing, and which
        # of the three flags each paragraph clears is documented in this function's own
        # docstring - the place a reader looks for it.
        return ba999_end(context)                                # [:L612] - Class 3

    if context.count_rows == 0:
        result = _CommandResult(
            count_rows=0, errno=_ERRNO_CLEAN, message="", sql_state=""
        )
        _capture_driver_error(context, result)
        if result.driver_reported_error:
            _initialize_oi_header_in_place(context.record, with_filler=True)
            _write_file_key(context.file_access, _FILE_KEY_EOF2)
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
        state.set_cursor_not_active()
        return ba999_end(context)

    if int(context.fs_reply) == int(FsReply.END_OF_FILE):
        state.set_cursor_not_active()
        _write_file_key(context.file_access, _FILE_KEY_EOF3)
        return ba999_end(context)

    # `perform bb100-UnloadHVs.` [:L641]. The 26 moves; `HV-OI3-KEY` and `HV-OI3-BATCH`
    # are NOT among them - anomaly N-two-write-only-columns.
    unloaded = bb100_unload_hvs(context.group)
    _copy_oi_header(unloaded, context.record)
    # `move HV-OI3-KEY to WS-File-Key.` [:L642]. THE HOST VARIABLE, not the record: the
    # derived key that was never unloaded is nonetheless what gets logged.
    _write_file_key(
        context.file_access, str(context.group.hv_oi3_key)
    )
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    return ba999_end(context)


def ba041_reread(context: _BridgeContext) -> tuple[int, int]:
    """``ba041-Reread.`` - [common/otm3MT.cbl:L563-L644]. Fetch one row, primary cursor.

    Entered by fall-through from ``ba040-Process-Read-Next``, never by a ``go to``.
    Stamps ``ws-No-Paragraph`` 4 and clears ``Most-Cursor-Set``.
    """
    return _fetch_one_row(
        context,
        context.slot_state(CursorSlot.PRIMARY),
        paragraph="ba041-Reread",
        slot_locator="[common/otm3MT.cbl:L611] Most-Cursor-Set",
    )


def ba050_process_read_indexed(context: _BridgeContext) -> tuple[int, int]:
    """``ba050-Process-Read-Indexed.`` - [common/otm3MT.cbl:L646-L755]. One row, by key.

    ⭐⭐ ANOMALY N-read-indexed-23: THE KEY-NOT-FOUND STATUS IS ``23``, NOT ``21``, AND
    THE TWO BRIDGES DISAGREE. This one writes ``move 23 to fs-Reply`` with the comment
    ``*> could also be 21 or 14``.
    """
    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]
    context.ws_where = _ws_where_1_to_j(_key_predicate())
    _write_log_where(context.file_access, context.ws_where)      # [:L666]
    if _testing_2(context.dal_common):                           # [:L667-L668] - D2
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba050-Process-Read-Indexed"
    ]

    statement = _select_statement(context.ws_where)
    result = _mysql_1210_command(context, statement, (key_value,), store_result=True)
    context.count_rows = result.count_rows

    if result.count_rows == 0:
        # ANOMALY N-read-indexed-23: 23 here, 21 in `glpostingMT` [:L682].
        context.status(FsReply.KEY_NOT_FOUND, int(WeError.SUCCESS))
        ba998_free(context)
        return ba999_end(context)

    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba050-Fetch"
    ]
    row = result.rows[0] if result.rows else None
    if row is None:
        context.count_rows = 0
    else:
        _mysql_fetch_record(context.group, row)

    if context.count_rows <= 0:
        _write_sql_fields(context.file_access, sql_state=result.sql_state)
        if result.driver_reported_error:
            context.we_error = int(WeError.UNKNOWN_UNEXPECTED)
            _write_sql_fields(
                context.file_access, sql_err=result.errno, sql_msg=result.message
            )
        else:
            context.we_error = int(WeError.READ_INDEXED_UNEXPECTED)
            _write_sql_fields(context.file_access, sql_err="0", sql_msg="")
        context.status(FsReply.KEY_NOT_FOUND, context.we_error)
        _write_file_key(context.file_access, "")
        ba998_free(context)
        return ba999_end(context)

    unloaded = bb100_unload_hvs(context.group)
    _copy_oi_header(unloaded, context.record)
    # `move HV-OI3-KEY to WS-File-Key.` [:L751] - the host variable, never unloaded into
    # the record (anomaly N-two-write-only-columns) yet logged from here.
    _write_file_key(context.file_access, str(context.group.hv_oi3_key))
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    ba998_free(context)
    return ba999_end(context)


def ba060_process_start(context: _BridgeContext) -> tuple[int, int]:
    """``ba060-Process-Start.`` - [common/otm3MT.cbl:L756-L861]. Position, do not fetch.

    ⭐⭐ ANOMALY N-start-997-vs-998: THE HANDLER AND THE BRIDGE DISAGREE ON THE SAME
    GUARD. ``if access-type < 5 or > 8`` appears in both, and the handler moves 998
    [common/acas019.cbl:L437-L448] while the bridge moves 997 [:L762].
    """
    access_type = int(context.file_access.access_type)
    # `if access-type < 5 or > 8` [:L760], with the inline comment `*> not using not <
    # or not >`. The bounds are NOT restated here.
    if not start_access_type_is_valid(access_type):
        context.status(FsReply.ERROR, int(WeError.ACCESS_TYPE_WRONG))  # 997 [:L761-L762]
        # ONE ERROR, through the shared reporter. A refusal that returns 99 to the
        # caller is a FAILURE, and WARNING put it below the level an operator watches.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="ba060-Process-Start",
            locator="[common/otm3MT.cbl:L760-L763]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="Access-Type rejected with We-Error 997; the HANDLER rejects the "
            "identical range with 998 [common/acas019.cbl:L437-L448] - anomaly "
            "N-start-997-vs-998",
        )
        return ba999_end(context)

    if context.slot_state(CursorSlot.PRIMARY).cursor_active():
        ba998_free(context)

    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]
    context.most_relation = ACCESS_TYPE_RELATION_ARMS.get(access_type, "   ")
    _BRIDGE.most_relation = context.most_relation
    context.ws_where = _ws_where_1_to_j(_start_predicate(context.most_relation))
    _write_log_where(context.file_access, context.ws_where)      # [:L803]
    _write_file_key(context.file_access, key_value)              # [:L804]
    if _testing_2(context.dal_common):                           # [:L805-L807] - D2
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba060-Process-Start"
    ]

    statement = _select_statement(context.ws_where)
    result = _mysql_1210_command(context, statement, (key_value,), store_result=True)
    context.count_rows = result.count_rows

    primary = context.slot_state(CursorSlot.PRIMARY)
    if result.count_rows != 0:
        primary.store_result(result.rows)
        primary.position_at(key_value)
        primary.set_cursor_active()

    if result.count_rows == 0:
        _capture_driver_error(context, result)
        context.status(FsReply.INVALID_KEY_ON_START, int(WeError.SUCCESS))
    else:
        context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
        _BRIDGE.ws_temp_ed_row = result.count_rows
        # `string MOST-relation WS-OTM3-Record (K:L) " got " WS-Temp-ED-Row " recs"`
        # [:L839-L845].
        _write_file_key(
            context.file_access,
            f"{context.most_relation}{key_value}"
            f" got {_BRIDGE.ws_temp_ed_row:07d} recs",
        )
    return ba999_end(context)


def ba070_process_write(context: _BridgeContext) -> tuple[int, int]:
    """``ba070-Process-Write.`` - [common/otm3MT.cbl:L862-L889]. Load, insert, classify.

    ⭐ ``WE-Error`` IS NEVER SET ON THE FAILURE PATH. It was zeroed at [:L866] and the
    failure branch moves 99 into ``fs-reply`` alone, so a failed insert reports ``(99,
    0)`` - a hard error with no error code.
    """
    group, _key_staging, _batch_staging = bb000_hv_load(context.record)
    context.group = group
    _write_file_key(context.file_access, _oi_key_image(context.record))
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    _write_sql_fields(
        context.file_access, sql_state="0", sql_msg="", sql_err="0"
    )
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba070-Process-Write"
    ]

    result = bb200_insert(context)
    context.count_rows = result.count_rows
    if result.count_rows != 1:
        _write_sql_fields(context.file_access, sql_state=result.sql_state)
        context.status(FsReply.ERROR, context.we_error)
        if result.driver_reported_error:
            _write_sql_fields(
                context.file_access, sql_err=result.errno, sql_msg=result.message
            )
            if is_duplicate_key_bridge_level(
                context.file_access.logging_data.sql_err,
                context.file_access.logging_data.sql_state,
            ):
                context.status(FsReply.DUPLICATE_KEY, context.we_error)
    return ba999_end(context)


def ba080_process_delete(context: _BridgeContext) -> tuple[int, int]:
    """``ba080-Process-Delete.`` - [common/otm3MT.cbl:L890-L943]. One row, by key.

    both end ``";" X"00"``; this one ends ``X"00"`` alone [:L923]. Harmless to a single-
    statement protocol, and reproduced because the statement text is what ``WS-Log-
    Where``'s companion records.
    """
    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]
    context.ws_where = _ws_where_1_to_j(_key_predicate())        # [:L894-L907]
    _write_file_key(context.file_access, key_value)              # [:L908]
    _write_log_where(context.file_access, context.ws_where)      # [:L909]
    if _testing_2(context.dal_common):                           # [:L910-L912] - D2
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba080-Process-Delete"
    ]

    # `DELETE FROM `SAITM3-REC` WHERE <slice>` - no semicolon [:L917-L923]. Note there
    # is no `MYSQL-1220-STORE-RESULT` here.
    statement = _delete_statement(context.ws_where)
    result = _mysql_1210_command(context, statement, (key_value,))
    context.count_rows = result.count_rows

    if result.count_rows != 1:
        _capture_driver_error(context, result)
        context.status(FsReply.ERROR, int(WeError.DELETE_SQLSTATE_NOT_00000))
        return ba999_end(context)

    _write_sql_fields(context.file_access, sql_msg="", sql_err="0")
    return ba999_end(context)


def ba090_process_rewrite(context: _BridgeContext) -> tuple[int, int]:
    """``ba090-Process-Rewrite.`` - [common/otm3MT.cbl:L944-L988]. Load, update, classify.

    ⭐ ANOMALY N-punctuation, on the procedural side. [:L946] and [:L947] are indented
    FOUR spaces where every neighbouring statement uses five, so the two lines sit one
    column left of the block they belong to. Cosmetic, recorded, not normalised.
    """
    group, _key_staging, _batch_staging = bb000_hv_load(context.record)
    context.group = group
    # [:L946-L947] - the two four-space-indented statements (anomaly N-punctuation).
    _write_file_key(context.file_access, _oi_key_image(context.record))
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba090-Process-Rewrite"
    ]

    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]
    context.ws_where = _ws_where_1_to_j(_key_predicate())
    _write_log_where(context.file_access, context.ws_where)

    result = bb300_update(context, key_value)
    context.count_rows = result.count_rows
    if _testing_2(context.dal_common):                           # [:L967-L969] - AFTER
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass

    if result.count_rows != 1:
        _capture_driver_error(context, result)
        context.status(FsReply.ERROR, int(WeError.REWRITE_SQLSTATE_NOT_00000))
        return ba999_end(context)

    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    _write_sql_fields(context.file_access, sql_err="0", sql_msg="")
    return ba999_end(context)


def _sorted_read_next(
    context: _BridgeContext,
    *,
    function: FileFunction,
    slot: CursorSlot,
    paragraph: str,
    reread: Callable[[_BridgeContext], tuple[int, int]],
    file_key_suffix: str,
) -> tuple[int, int]:
    """The body ``ba140`` and ``ba150`` share, statement for statement.

    ⭐⭐ ANOMALY N-sorted-order-is-a-syntax-error. THREE INDEPENDENT DEFECTS COMPOUND
    HERE.
    """
    state = context.slot_state(slot)
    if state.cursor_not_active():                                # [:L995]
        # `set KOR-x1 to 1` / offset / length [:L996-L998] - computed, then unused.
        # NO RECORD HERE, for the reason `ba040` gives: three `move`s that display
        # nothing and whose values go unused. `_EXTRA_READS` still carries this
        # paragraph's `source_locator` for the traceability tables.
        # `move spaces to WS-Where` / `move 1 to J` / the STRING [:L999-L1008]. The whole
        # of `WS-Where` is the ORDER BY - `_EXTRA_READS[function].predicate_present` is
        # False, which is the shared table's own record of the same fact.
        context.ws_where = _ws_where_1_to_j(_SORTED_ORDER_BY_TEXT[int(function)])
        _write_log_where(context.file_access, context.ws_where)
        context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            paragraph
        ]

        # The SELECT template emits " WHERE " with no predicate - defect 1 above.
        statement = _select_statement(context.ws_where)
        result = _mysql_1210_command(context, statement, store_result=True)
        context.count_rows = result.count_rows
        _write_file_key(context.file_access, _FILE_KEY_SORTED)    # [:L1023]
        if _testing_2(context.dal_common):                       # [:L1024-L1026] - D2
            #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
            #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
            #  customer and invoice key as a literal - or the statement itself. Both are
            #  forbidden in a record by the safe-event schema (CWE-532), and
            #  `sanitise_for_log` escaped them rather than removing them. This was a
            #  developer's trace read at the terminal beside the running program; nothing
            #  acts on it operationally. `WS-Where` is still BUILT and still stored in
            #  `Logging-Data`, because the bridge's own statements read it (R-3).
            pass

        if result.count_rows == 0:
            _capture_driver_error(context, result)
            context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
            _write_file_key(context.file_access, _FILE_KEY_NO_DATA)
            return ba999_end(context)

        state.store_result(result.rows)
        state.set_cursor_active()
        _BRIDGE.ws_temp_ed_row = result.count_rows
        _write_file_key(
            context.file_access,
            f"> 0 got cnt={_BRIDGE.ws_temp_ed_row:07d}{file_key_suffix}",
        )
        ba999_end(context)

    return reread(context)


def ba140_process_read_next(context: _BridgeContext) -> tuple[int, int]:
    """``ba140-Process-Read-Next.`` - [common/otm3MT.cbl:L989-L1061]. Function 32.

    The code orders by invoice and date first, then type descending, then batch item and
    batch nos [:L1002-L1007]. A second false comment, the same family as anomaly
    N-false-occurs-comment. Recorded; the CODE's order is what is reproduced.
    """
    return _sorted_read_next(
        context,
        function=FileFunction.READ_BY_BATCH,
        slot=CursorSlot.SECONDARY,
        paragraph="ba140-Process-Read-Next",
        reread=ba141_reread,
        file_key_suffix=" recs in sorted order",
    )


def ba141_reread(context: _BridgeContext) -> tuple[int, int]:
    """``ba141-Reread.`` - [common/otm3MT.cbl:L1062-L1142]. Fetch one row, cursor 2.

    Identical to ``ba041-Reread`` apart from ``ws-No-Paragraph`` 22, the cursor flag
    ``Most-Cursor-Set-2``, and ``move HV-OI3-Key to WS-File-Key`` at [:L1139] - which
    spells the host variable ``HV-OI3-Key`` where ``ba041`` spells it ``HV-OI3-KEY``
    [:L642]. Anomaly N-casing, third instance in this program.
    """
    return _fetch_one_row(
        context,
        context.slot_state(CursorSlot.SECONDARY),
        paragraph="ba141-Reread",
        slot_locator="[common/otm3MT.cbl:L1111] Most-Cursor-Set-2",
    )


def ba150_process_read_next(context: _BridgeContext) -> tuple[int, int]:
    """``ba150-Process-Read-Next.`` - [common/otm3MT.cbl:L1143-L1215]. Function 33.

    ``fn-Read-By-Cust``, declared at [copybooks/wsfnctn.cob:L104] with the note ``*>
    09/02/17 for OTM3 (sl110, 120, 190)`` - three report programs, all of them out of
    scope for this migration [AAP section 0.2.2], which is why nothing in the migrated
    cycle issues this function.
    """
    return _sorted_read_next(
        context,
        function=FileFunction.READ_BY_CUST,
        slot=CursorSlot.TERTIARY,
        paragraph="ba150-Process-Read-Next",
        reread=ba151_reread,
        # `" recs in sorted order"` [:L1203] - the same suffix as `ba140`, so the log
        # line cannot distinguish the two either. Third collision in the pair.
        file_key_suffix=" recs in sorted order",
    )


def ba151_reread(context: _BridgeContext) -> tuple[int, int]:
    """``ba151-Reread.`` - [common/otm3MT.cbl:L1216-L1296]. Fetch one row, cursor 3."""
    return _fetch_one_row(
        context,
        context.slot_state(CursorSlot.TERTIARY),
        paragraph="ba151-Reread",
        slot_locator="[common/otm3MT.cbl:L1265] Most-Cursor-Set-3",
    )


def ba100_bad_function(context: _BridgeContext) -> tuple[int, int]:
    """``ba100-Bad-Function.`` - [common/otm3MT.cbl:L1297-L1302].

    ::

    *> Houston; We have a problem                                [:L1299]
        move     990 to WE-Error.                                [:L1300]
        move     99 to Fs-Reply.                                 [:L1301]
        go       to ba999-end.                                   [:L1302]

    ⭐ THE BRIDGE SAYS 990 AND THE HANDLER SAYS 999 FOR THE SAME CONDITION. ``acas019``'s
    ``aa100-Bad-Function`` moves 999 [common/acas019.cbl:L528] - and carries the identical
    "Houston" comment. So an unrecognised function code reports ``(99, 999)`` on the
    flat-file path and ``(99, 990)`` on the DAL path. ``dal/status.py`` publishes 990 as
    ``UNKNOWN_UNEXPECTED`` and 999 as ``NOT_USED``; each side keeps its own.

    ⭐ 992 - ``INVALID_FUNCTION`` - is what the vocabulary reserves for exactly this, and
    NEITHER program uses it. Recorded; not substituted.

    ⭐ ``ba100`` IS REACHED ONE WAY ONLY here, from ``when other``. The handler reaches its
    equivalent TWO ways - ``when other`` and an unconditional fall-through at
    [common/acas019.cbl:L305] - see :func:`aa100_bad_function`.

    Transfers: ``go to ba999-end``, Class 3.
    """
    # ONE ERROR, through the shared reporter. `File-Function` is an operation code
    # from the frozen vocabulary [copybooks/wsfnctn.cob:L88-L118], not business data, so
    # it stays - the reporter renders it as its own field.
    log_handler_failure(
        _LOG,
        program=BRIDGE_PROGRAM_ID,
        paragraph="ba100-Bad-Function",
        locator="[common/otm3MT.cbl:L1300]",
        fs_reply=int(FsReply.ERROR),
        we_error=int(WeError.UNKNOWN_UNEXPECTED),
        detail="File-Function %d is not one this bridge implements; the bridge "
        "reports We-Error 990 where the handler reports 999 "
        "[common/acas019.cbl:L528]" % int(context.file_access.file_function),
    )
    context.status(FsReply.ERROR, int(WeError.UNKNOWN_UNEXPECTED))
    return ba999_end(context)


def ba998_free(context: _BridgeContext) -> None:
    """``ba998-Free.`` - [common/otm3MT.cbl:L1309-L1319]. Release the result set.

    ⭐⭐ ANOMALY N-ba998-frees-primary-only. THE PARAGRAPH ALWAYS CLEARS ``Most-Cursor-
    Set``, THE PRIMARY FLAG - never ``-2``, never ``-3``.
    """
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba998-Free"
    ]
    for slot in (CursorSlot.PRIMARY, CursorSlot.SECONDARY, CursorSlot.TERTIARY):
        context.slot_state(slot).free_result()
    context.slot_state(CursorSlot.PRIMARY).set_cursor_not_active()


def ba999_end(context: _BridgeContext) -> tuple[int, int]:
    """``ba999-end.`` - [common/otm3MT.cbl:L1321-L1326], then ``ba999-exit``.

    ⭐ THE BRIDGE DOES LOG, AND THE HANDLER DOES NOT - on the DAL path. ``acas019``'s
    ``Ca-Process-Logs`` carries its comment on the label line itself: ``*> Not called on
    DAL access as it does it already`` [common/acas019.cbl:L623]. Anomaly N-nolog-on-
    dal.
    """
    if _testing_1(context.dal_common):
        otm3mt_ca_process_logs(context)
    return ba999_exit(context)


def ba999_exit(context: _BridgeContext) -> tuple[int, int]:
    """``ba999-exit. exit program.`` - [common/otm3MT.cbl:L1328-L1329].

    The return to the caller. ``File-Access`` already carries the status pair - every
    paragraph wrote it before transferring here - so the pair is returned as a
    convenience and NOT as the authoritative channel.
    """
    return context.fs_reply, context.we_error


def bb200_insert(context: _BridgeContext) -> _CommandResult:
    """``bb200-Insert Section.`` - [common/otm3MT.cbl:L1418-L1798].

    ⭐ EVERY COLUMN IS NAMED ON EVERY INSERT - never a subset. Combined with ``initialize
    TD-SAITM3-REC`` at the head of the load, that is what lets every column of this
    table be declared ``NOT NULL``.
    """
    statement = _insert_statement()
    parameters = _insert_parameters(context.group)
    # Belt and braces on the NOT NULL invariant: 28 parameters, none of them None.
    if len(parameters) != len(COLUMNS) or any(
        parameter is None for parameter in parameters
    ):  # pragma: no cover - unreachable while `initialize` runs first
        # KEPT, and kept at ERROR. This is not a narration of frozen control flow -
        # the bridge has no such arm - it is a programming-error guard on an invariant
        # the schema imposes, and the two numbers it reports are COUNTS, which the
        # safe-event schema admits. No parameter VALUE is named.
        _LOG.error(
            "%s: bb200-Insert built %d parameters for %d columns; every column of "
            "SAITM3-REC is NOT NULL [mysql/ACASDB.sql:L896-L926]",
            BRIDGE_PROGRAM_ID,
            len(parameters),
            len(COLUMNS),
        )
    return _mysql_1210_command(context, statement, parameters)


def bb300_update(context: _BridgeContext, key_value: str) -> _CommandResult:
    """``bb300-Update Section.`` - [common/otm3MT.cbl:L1799-L2180].

    the key is also the entire predicate, so the statement assigns ``OI3-KEY`` the value
    it selects by. Reproduced.
    """
    statement = _update_statement(context.ws_where.strip())
    parameters = _insert_parameters(context.group) + (key_value,)
    return _mysql_1210_command(context, statement, parameters)


def otm3mt_ca_process_logs(context: _BridgeContext) -> None:
    """``Ca-Process-Logs.`` in ``otm3MT`` - [common/otm3MT.cbl:L2184-L2188].

    ``fhlogger`` [common/fhlogger.cbl] is out of scope [AAP section 0.2.2, "Non-posting
    utilities"], so the record it would append is emitted through
    :func:`acas_posting.dal.status.log_file_handler_record`, THE ONE ADAPTER every handler
    in this package shares. It has no database effect - AAP section 0.3.4's first rule - so
    it becomes a log record and alters no control flow.

    TWO FIELDS ARE WITHHELD. ``WS-File-Key`` is the customer-and-invoice key and
    ``WS-Log-Where`` is a SQL predicate carrying that key as a literal; both are CWE-532 in
    a log and neither is needed to act on a failure.

    ⭐ THE HANDLER HAS A PARAGRAPH OF THE SAME NAME [common/acas019.cbl:L623] which is NOT
    called on this path, per the comment on its own label line. So one CALL produces one
    log record, from here. Anomaly N-nolog-on-dal.
    """
    logging_data = context.file_access.logging_data
    #  `Log-File-Rec-Written` IS NOW ADVANCED, NOT PINNED. Assigning 1 was wrong
    #  twice over: the field is `pic 9(6)` [copybooks/Test-Data-Flags.cob:L20], so it
    #  counts to 999999 and wraps, and it lives in `ACAS-DAL-Common-data`, which the
    #  CALLER owns and carries across calls - so pinning it to 1 discarded every count
    #  the rest of the cycle had accumulated. The adapter advances it by one, modulo one
    #  million, once per record it emits.
    log_file_handler_record(
        _LOG,
        program=BRIDGE_PROGRAM_ID,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(context.file_access.file_function),
        access_type=int(context.file_access.access_type),
        fs_reply=int(context.file_access.fs_reply),
        we_error=int(context.file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=context.dal_common,
    )
    otm3mt_ca_exit(context)


def otm3mt_ca_exit(context: _BridgeContext) -> None:
    """``ca-Exit. exit.`` in ``otm3MT`` - [common/otm3MT.cbl:L2190].

    A bare ``exit``, which in COBOL is a no-operation that gives the paragraph a name to
    end at. Reproduced as a named function so the paragraph inventory is complete.
    """


def otm3_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    otm3: OiHeader,
) -> tuple[int, int]:
    """``call "otm3MT" using File-Access, ACAS-DAL-Common-data, WS-OTM3-Record``.

    Note the order: ``File-Access`` FIRST here, where the handler's own linkage puts
    ``System-Record`` first and ``File-Access`` third [common/acas019.cbl:L225-L231].

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L64], carrying the
            requested ``File-Function`` and ``Access-Type`` in, and the status, the
            diagnostics and the logging fields out.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob:L10-L16],
            whose two switches gate the logging (``Testing-1``) and the diagnostic
            display (``Testing-2``, deviation D2).
        otm3: ``WS-OTM3-Record`` as the bridge declares it - the FULL field layout,
            because [common/otm3MT.cbl:L345-L346] renames ``OI-Header`` to that name.

    Returns:
        The ``(FS-Reply, We-Error)`` pair, which is also in ``file_access``.
    """
    context = _BridgeContext(
        file_access=file_access, dal_common=dal_common, record=otm3
    )
    ba_acas_dal_process(context)
    return ba010_initialise(context)


# THE HANDLER - acas019 `aa-Process-Flat-File Section.` [common/acas019.cbl:L234]
# through `ca-Exit. exit.` [:L629]. One function per paragraph, in source order.


@dataclass
class _HandlerContext:
    """``acas019``'s five linkage items plus the per-CALL scratch its paragraphs share.
    """

    system: SystemRecord
    record: OiHeader
    file_access: FileAccess
    file_defs: FileDefs
    dal_common: AcasDalCommonData
    medium: FlatFileMedium = _FLAT_FILE_MEDIUM_ABSENT
    file_record: OpenItemRecord3 = field(default_factory=_blank_open_item_record_3)
    ws_temp_ed: WsTempEd = field(default_factory=WsTempEd)
    cobol_file_status: int = 0
    cobol_file_eof: bool = False
    fs_reply: int = FsReply.SUCCESS
    we_error: int = 0

    def status(self, fs_reply: FsReply | int, we_error: WeError | int) -> None:
        """Write a status pair into ``File-Access`` and remember it for the return."""
        self.fs_reply, self.we_error = _write_status(
            self.file_access, fs_reply, we_error
        )

    def read_status(self) -> None:
        """Re-read the pair from ``File-Access`` after something else wrote it."""
        self.fs_reply = _as_fs_reply(self.file_access.fs_reply)
        self.we_error = int(self.file_access.we_error)


def aa_process_flat_file(context: _HandlerContext) -> tuple[int, int]:
    """``aa-Process-Flat-File Section.`` - [common/acas019.cbl:L234]. A bare section head.

    The section header carries no statements of its own; ``aa010-main`` at [:L236] is
    its first paragraph and runs immediately.
    """
    return aa010_main(context)


def aa010_main(context: _HandlerContext) -> tuple[int, int]:
    """``aa010-main.`` - [common/acas019.cbl:L236-L305]. Log identity, guard, branch,
    dispatch.

    ⭐ ANOMALY N-logsystem5-meaning: the legend on [:L240] says ``5=Invoice``, matching
    ``acas016:L248``, while ``acas013:L298`` and ``acas015:L291`` both say ``5=Stock``
    for the same code. Four handlers, two legends, one vocabulary.
    """
    logging_data = context.file_access.logging_data
    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT_FILE

    # TWO - the key guard [:L245-L259], which governs BOTH paths because it is above the
    # branch. A rejection returns immediately.
    guarded = _aa010_key_guard(context)
    if guarded is not None:
        return guarded

    if not _fs_cobol_files_used(context.system):
        source = context.system.system_data_block.rdbms_flat_statuses
        target = context.file_access.fa_rdbms_flat_statuses
        target.fa_file_system_used = source.file_system_used
        target.fa_file_duplicates_in_use = source.file_duplicates_in_use
        ba_process_rdbms(context)
        return aa_main_exit(context)

    # FOUR - flat-file path only from here. `perform ba012-Test-WS-Rec-Size-2.` [:L271]
    # names a PARAGRAPH, so the range is that paragraph ALONE.
    ba012_test_ws_rec_size_2(context)
    context.read_status()
    _write_sql_fields(context.file_access, sql_err="", sql_msg="", sql_state="")

    function = int(context.file_access.file_function)
    if function == int(FileFunction.OPEN):
        return aa020_process_open(context)
    if function == int(FileFunction.CLOSE):
        return aa030_process_close(context)
    if function == int(FileFunction.READ_NEXT):
        return aa040_process_read_next(context)
    if function == int(FileFunction.READ_INDEXED):
        return aa050_process_read_indexed(context)
    if function == int(FileFunction.WRITE):
        return aa070_process_write(context)
    if function == int(FileFunction.RE_WRITE):
        return aa090_process_rewrite(context)
    if function == int(FileFunction.DELETE):
        return aa080_process_delete(context)
    if function == int(FileFunction.START):
        return aa060_process_start(context)
    # `when other go to aa100-Bad-Function` [:L300-L301] - `*> 6 is spare / unused`.
    # Codes 32 and 33 land here too.
    return aa100_bad_function(context)


def _aa010_key_guard(context: _HandlerContext) -> tuple[int, int] | None:
    """``evaluate File-Function`` at [common/acas019.cbl:L245-L259] - the key guard,
    VERBATIM::

    ⭐ ANOMALY N-996-comment: the comment beside the 996 is a VERBATIM COPY of the one
    beside the 998, ending in the wrong number's worth of alignment - ``*> file seeks
    key type out of range 996``.

    Returns:
        The status pair if the guard rejected, or ``None`` to continue.
    """
    function = int(context.file_access.file_function)
    key_number = int(context.file_access.logging_data.file_key_no)

    if function in (int(FileFunction.READ_INDEXED), int(FileFunction.START)):
        if key_number != 1:
            context.status(
                FsReply.ERROR, int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            )                                                    # 998 [:L249-L250]
            # ONE ERROR, through the shared reporter: the guard returns 99 to the
            # caller, so it is a failure and WARNING was below the level an operator
            # watches. `File-Key-No` and `File-Function` are operation codes from the
            # frozen vocabulary [copybooks/wsfnctn.cob:L88-L118], not business data.
            log_handler_failure(
                _LOG,
                program=HANDLER_PROGRAM_ID,
                paragraph="aa000-Main-Process key guard",
                locator="[common/acas019.cbl:L248-L251]",
                fs_reply=int(FsReply.ERROR),
                we_error=int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
                detail="File-Key-No %d rejected for File-Function %d; SAITM3-REC "
                "declares exactly one key [common/otm3MT.scb:L249-L251]"
                % (key_number, function),
            )
            return aa999_main_exit(context)
    elif function == int(FileFunction.DELETE):
        if key_number != 1:
            context.status(
                FsReply.ERROR, int(WeError.DELETE_KEY_OUT_OF_RANGE)
            )                                                    # 996 [:L255-L256]
            # ONE ERROR, as above - the delete arm has its own code, 996.
            log_handler_failure(
                _LOG,
                program=HANDLER_PROGRAM_ID,
                paragraph="aa000-Main-Process key guard",
                locator="[common/acas019.cbl:L254-L257]",
                fs_reply=int(FsReply.ERROR),
                we_error=int(WeError.DELETE_KEY_OUT_OF_RANGE),
                detail="File-Key-No %d rejected for delete; the comment beside the "
                "frozen code is a verbatim copy of the 998 comment at [:L249] - "
                "anomaly N-996-comment" % key_number,
            )
            return aa999_main_exit(context)
    return None


def _fs_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - the condition name the RDB branch tests at [:L262].

    The predicate lives here rather than in ``acas_posting.cobol.condition_names``
    because AAP section 0.4.3's import table does not permit ``dal/*`` to import
    ``cobol/*``.
    """
    return int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0


def aa020_process_open(context: _HandlerContext) -> tuple[int, int]:
    """``aa020-Process-Open.`` - [common/acas019.cbl:L307-L344]. Four modes, four shapes.

    move spaces to WS-File-Key. *> for logging [:L308] move 201 to WS-No-Paragraph.
    """
    _write_file_key(context.file_access, "")
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa020-Process-Open"
    ]

    access_type = int(context.file_access.access_type)
    if access_type == int(AccessType.INPUT):
        reply = context.medium.open_file("input")
        context.status(reply, context.we_error)
        if int(reply) != 0:
            # `move 35 to fs-Reply` BEFORE the close, so the close's status is invisible.
            context.status(35, context.we_error)
            context.medium.close_file()
            return aa999_main_exit(context)
    elif access_type == int(AccessType.I_O):
        reply = context.medium.open_file("i-o")
        context.status(reply, context.we_error)
        if int(reply) != 0:
            context.medium.close_file()
            context.medium.open_file("output")
            context.medium.close_file()
            context.medium.open_file("i-o")
    elif access_type == int(AccessType.OUTPUT):
        # A PLAIN OPEN. Anomaly N-noopenoutput: nothing is deleted, unlike `acas008`
        # [common/acas008.cbl:L313-L319].
        reply = context.medium.open_file("output")
        context.status(reply, context.we_error)
    elif access_type == int(AccessType.EXTEND):                    # `fn-extend` [:L330]
        # `open extend` is commented out at [:L331]; the rejection is the arm.
        context.status(FsReply.ERROR, int(WeError.ACCESS_TYPE_WRONG))  # [:L332-L333]
        # ONE ERROR, through the shared reporter. A published verb that can never
        # succeed is exactly what an operator must be able to find - the same reasoning
        # that took anomaly A6's refusal in `acas008` off DEBUG.
        log_handler_failure(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="aa020-Process-Open",
            locator="[common/acas019.cbl:L330-L334]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="fn-extend refused: 'Must not be used for ISAM files'; the "
            "`open extend` itself is commented out in the frozen source",
        )
        return aa999_main_exit(context)

    # [:L339] is COMMENTED OUT, dated 27/07/16 16:30 - anomaly N-initialize.
    context.cobol_file_status = 0
    _write_file_key(context.file_access, "OPEN SL OTM3 File")
    if int(context.fs_reply) != 0:
        context.status(context.fs_reply, int(WeError.NOT_USED))
    return aa999_main_exit(context)


def aa030_process_close(context: _HandlerContext) -> tuple[int, int]:
    """``aa030-Process-Close.`` - [common/acas019.cbl:L346-L357]. Close, log, and leave
    low.

    aa999-main-exit`` at [:L353] logs the close itself.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa030-Process-Close"
    ]
    _write_file_key(context.file_access, "")
    reply = context.medium.close_file()
    context.status(reply, context.we_error)
    # [:L350] is COMMENTED OUT - anomaly N-initialize, fourth site.
    context.cobol_file_status = 0
    _write_file_key(context.file_access, "CLOSE SL OTM3 File")
    aa999_main_exit(context)
    context.file_access.file_function = 0
    context.file_access.access_type = 0
    acas019_ca_process_logs(context)
    return aa_main_exit(context)


def aa040_process_read_next(context: _HandlerContext) -> tuple[int, int]:
    """``aa040-Process-Read-Next.`` - [common/acas019.cbl:L359-L388]. Sequential, with a
    STOP.

    ⭐⭐ ANOMALY N-stop: ``stop "Cobol File EOF"`` at [:L371] HALTS THE PROGRAM AND WAITS
    FOR THE OPERATOR, on the second read past end of file. Its own comment says ``*> for
    testing`` and it was never removed.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa040-Process-Read-Next"
    ]

    if context.cobol_file_eof:
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
        # `move spaces to OI3-Key` [:L368] - anomaly N-spaces-into-numeric. The FILE
        # view's key group takes spaces, `PIC 9(8)` half included.
        context.file_record.oi3_key.oi3_customer = " " * 7
        context.file_record.oi3_key.oi3_invoice = _numeric_digits(
            " " * 8, "OI3-Invoice"
        )
        _write_sql_fields(context.file_access, sql_err="", sql_msg="")
        # `stop "Cobol File EOF"` [:L371] - anomaly N-stop, recorded as an omission. The
        # operator pause is NOT reproduced; the diagnostic becomes a log record and the
        # transfer below is preserved.
        #  ONE ERROR, THROUGH THE ONE REPORTER, worded and levelled identically
        #  to every sibling handler's record for the same statement. ERROR was already
        #  the right level here - a production `stop` that hangs an unattended batch run
        #  is exactly what an operator must see - but acas006 and acas007 logged it at
        #  WARNING, acas012 at INFO and acas016 at DEBUG, so one event read as four.
        log_cobol_stop(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas019.cbl:L371]",
        )
        return aa999_main_exit(context)

    reply, read_record = context.medium.read_next()
    if read_record is None:
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
        context.cobol_file_eof = True
        context.cobol_file_status = 1
        _initialize_open_item_record_3(context.file_record, with_filler=False)
        _write_file_key(context.file_access, _FILE_KEY_FLAT_EOF)
        return aa999_main_exit(context)

    context.status(reply, context.we_error)
    if int(context.fs_reply) != 0:
        return aa999_main_exit(context)

    _copy_open_item_record_3(read_record, context.file_record)
    _move_file_record_to_linkage(context.file_record, context.record)
    aa041_move_inv_data(context)
    context.status(context.fs_reply, int(WeError.SUCCESS))
    return aa999_main_exit(context)


def aa041_move_inv_data(context: _HandlerContext) -> None:
    """``aa041-Move-Inv-Data.`` - [common/acas019.cbl:L390-L393]. The logging key,
    VERBATIM::

    ⭐⭐ ANOMALY N-aa041-move-inv-data: THIS PARAGRAPH NAME EXISTS IN NO OTHER HANDLER.
    """
    context.ws_temp_ed.ws_temp_ed_2 = int(context.file_record.oi3_key.oi3_invoice)
    context.ws_temp_ed.ws_temp_ed_1 = _cobol_move_alphanumeric(
        str(context.file_record.oi3_key.oi3_customer), 7
    )
    _write_file_key(context.file_access, context.ws_temp_ed.image)


def aa045_eval_keys(context: _HandlerContext) -> None:
    """``aa045-Eval-Keys.`` - [common/acas019.cbl:L395-L413], VERBATIM::

    *> The next block will never get executed unless performed so is it needed ? [:L395]
    aa045-Eval-Keys.
    """
    function = int(context.file_access.file_function)
    if function in (
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
    ):
        if int(context.file_access.logging_data.file_key_no) == 1:
            _move_linkage_to_file_record(context.record, context.file_record)
            aa041_move_inv_data(context)
        else:
            _write_file_key(context.file_access, "")
    else:
        _write_file_key(context.file_access, "")


def aa050_process_read_indexed(context: _HandlerContext) -> tuple[int, int]:
    """``aa050-Process-Read-Indexed.`` - [common/acas019.cbl:L415-L435].

    move 204 to WS-No-Paragraph. [:L417] perform aa045-Eval-keys. [:L418] move zero to
    Cobol-File-Status.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa050-Process-Read-Indexed"
    ]
    aa045_eval_keys(context)
    context.cobol_file_status = 0

    if int(context.file_access.logging_data.file_key_no) == 1:
        key_value = _oi3_key_image(context.file_record)
        reply, read_record = context.medium.read_indexed(key_value)
        context.status(reply, context.we_error)
        if _invalid_key_condition(reply) or read_record is None:
            context.status(FsReply.INVALID_KEY_ON_START, 21)

        if int(context.fs_reply) == 0:
            _copy_open_item_record_3(read_record, context.file_record)  # type: ignore[arg-type]
            _move_file_record_to_linkage(context.file_record, context.record)
            aa041_move_inv_data(context)
        else:
            _initialize_oi_header_in_place(context.record, with_filler=False)
            _write_file_key(context.file_access, _FILE_KEY_FAILED_ACTION)
        return aa999_main_exit(context)

    # UNREACHABLE behind the guard at [:L245-L259] - `*> should never get here` [:L434].
    context.status(FsReply.ERROR, int(WeError.FILE_KEY_NO_OUT_OF_RANGE))
    return aa999_main_exit(context)


def aa060_process_start(context: _HandlerContext) -> tuple[int, int]:
    """``aa060-Process-Start.`` - [common/acas019.cbl:L437-L487]. FOUR separate START
    blocks.

    move 205 to WS-No-Paragraph. [:L441] perform aa045-Eval-keys. [:L442] move zeros to
    fs-reply WE-Error. [:L443-L444] move zero to Cobol-File-Status.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa060-Process-Start"
    ]
    aa045_eval_keys(context)
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    context.cobol_file_status = 0

    access_type = int(context.file_access.access_type)
    if not start_access_type_is_valid(access_type):
        context.status(context.fs_reply, int(WeError.FILE_KEY_NO_OUT_OF_RANGE))  # [:L448]
        # ONE ERROR, through the shared reporter - the refusal returns a failing
        # status to the caller, so WARNING was the wrong level, and it is now the same
        # level as the BRIDGE's record for the identical test.
        log_handler_failure(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="aa060-Process-Start",
            locator="[common/acas019.cbl:L447-L449]",
            fs_reply=int(context.fs_reply),
            we_error=int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
            detail="Access-Type %d rejected with We-Error 998; the BRIDGE rejects the "
            "identical range with 997 [common/otm3MT.cbl:L760-L762] - anomaly "
            "N-start-997-vs-998" % access_type,
        )
        return aa999_main_exit(context)

    _move_linkage_to_file_record(context.record, context.file_record)
    key_value = _oi3_key_image(context.file_record)
    key_number = int(context.file_access.logging_data.file_key_no)

    for relation, relation_access_type, block_locator in (
        ("=", int(AccessType.EQUAL_TO), "[common/acas019.cbl:L455-L461]"),
        ("<", int(AccessType.LESS_THAN), "[common/acas019.cbl:L462-L468]"),
        (">", int(AccessType.GREATER_THAN), "[common/acas019.cbl:L469-L475]"),
        ("not <", int(AccessType.NOT_LESS_THAN), "[common/acas019.cbl:L476-L482]"),
    ):
        if key_number == 1 and access_type == relation_access_type:
            reply = context.medium.start(key_value, relation)
            # `status fs-Reply` [copybooks/slseloi3.cob:L5] - the START's status lands
            # first, so a failure outside the '2x' class reaches the caller as itself.
            context.status(reply, context.we_error)
            if _invalid_key_condition(reply):
                context.status(FsReply.INVALID_KEY_ON_START, context.we_error)
                # NO RECORD HERE. `invalid key move 21 to Fs-Reply` displays nothing,
                # and an `invalid key` on a START is an ORDINARY outcome every caller
                # branches on - the same reasoning that took the equivalent record out
                # of `dal/cursor_state.py`. The status pair IS the report, and it
                # reaches the caller unchanged.
                return aa999_main_exit(context)                    # Class 3
            # On success control FALLS THROUGH; every later block's `and fn-<other>` is
            # false, so no second START is issued.

    if key_number == 1:
        aa041_move_inv_data(context)
    else:
        # UNREACHABLE - `*> changed for acas019 others ?` [:L485], `*> should never get
        # here` [:L487].
        context.status(FsReply.ERROR, int(WeError.FILE_KEY_NO_OUT_OF_RANGE))
    return aa999_main_exit(context)


def aa070_process_write(context: _HandlerContext) -> tuple[int, int]:
    """``aa070-Process-Write.`` - [common/acas019.cbl:L490-L498].

    ⭐ 22 IS DUPLICATE-KEY, and it is the ONLY status this paragraph can report besides
    zero: an ISAM ``write``'s ``invalid key`` on a keyed file means the key already
    exists.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa070-Process-Write"
    ]
    _move_linkage_to_file_record(context.record, context.file_record)
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    context.cobol_file_status = 0
    reply = context.medium.write(context.file_record)
    context.status(reply, context.we_error)
    if _invalid_key_condition(reply):
        # `invalid key move 22 to FS-Reply` [:L496] - the phrase NORMALISES the whole
        # '2x' class to 22; `WE-Error` is untouched.
        context.status(FsReply.DUPLICATE_KEY, context.we_error)
    aa041_move_inv_data(context)
    return aa999_main_exit(context)


def aa080_process_delete(context: _HandlerContext) -> tuple[int, int]:
    """``aa080-Process-Delete.`` - [common/acas019.cbl:L500-L509].

    ⭐ 21 HERE AND 22 IN ``aa070``, for the mirror-image condition. A write fails because
    the key EXISTS and reports duplicate-key; a delete fails because the key does NOT
    exist and reports invalid-key-on-start. Both leave ``WE-Error`` at zero.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa080-Process-Delete"
    ]
    _move_linkage_to_file_record(context.record, context.file_record)
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    context.cobol_file_status = 0
    reply = context.medium.delete(context.file_record)
    context.status(reply, context.we_error)
    if _invalid_key_condition(reply):
        context.status(FsReply.INVALID_KEY_ON_START, context.we_error)
    aa041_move_inv_data(context)
    return aa999_main_exit(context)


def aa090_process_rewrite(context: _HandlerContext) -> tuple[int, int]:
    """``aa090-Process-Rewrite.`` - [common/acas019.cbl:L511-L521].

    ⭐ ANOMALY N-punctuation, THE HANDLER'S INSTANCE: ``end-rewrite`` at [:L520] has NO
    TERMINATING PERIOD, where ``aa070``'s ``end-write.`` [:L496] and ``aa080``'s ``end-
    delete.`` [:L507] both do.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa090-Process-Rewrite"
    ]
    _move_linkage_to_file_record(context.record, context.file_record)
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))
    context.cobol_file_status = 0
    reply = context.medium.rewrite(context.file_record)
    context.status(reply, context.we_error)
    if _invalid_key_condition(reply):
        context.status(FsReply.INVALID_KEY_ON_START, context.we_error)
    # [:L520] `end-rewrite` carries NO period - anomaly N-punctuation.
    aa041_move_inv_data(context)
    return aa999_main_exit(context)


def aa100_bad_function(context: _HandlerContext) -> tuple[int, int]:
    """``aa100-Bad-Function.`` - [common/acas019.cbl:L524-L529].

    ⭐ 999 HERE, 990 IN THE BRIDGE for the identical condition [common/otm3MT.cbl:L1300]
    - and both programs carry the SAME "Houston" comment, so the divergence is a copy
    that was edited on one side only.
    """
    # ONE ERROR, through the shared reporter, matching the bridge's own record for
    # its equivalent paragraph.
    log_handler_failure(
        _LOG,
        program=HANDLER_PROGRAM_ID,
        paragraph="aa100-Bad-Function",
        locator="[common/acas019.cbl:L528]",
        fs_reply=int(FsReply.ERROR),
        we_error=int(WeError.NOT_USED),
        detail="File-Function %d is not one this handler implements; the handler "
        "reports We-Error 999 where the bridge reports 990 "
        "[common/otm3MT.cbl:L1300]" % int(context.file_access.file_function),
    )
    context.status(FsReply.ERROR, int(WeError.NOT_USED))
    return aa999_main_exit(context)


def aa999_main_exit(context: _HandlerContext) -> tuple[int, int]:
    """``aa999-main-exit.`` - [common/acas019.cbl:L531-L534].

    ⭐ THIS IS THE FLAT-FILE PATH'S LOGGING POINT, and it is NOT reached on the DAL path
    - the RDB branch leaves for ``AA-Main-Exit`` at [:L265], which is BELOW this
    paragraph. Anomaly N-nolog-on-dal.
    """
    if _testing_1(context.dal_common):
        acas019_ca_process_logs(context)
    return aa_main_exit(context)


def aa_main_exit(context: _HandlerContext) -> tuple[int, int]:
    """``aa-main-exit.`` - [common/acas019.cbl:L536-L538]. A label with no statements.
    """
    return aa_exit(context)


def aa_exit(context: _HandlerContext) -> tuple[int, int]:
    """``aa-Exit. exit program.`` - [common/acas019.cbl:L540-L541].

    The return to the caller. ``File-Access`` already carries the status pair, so the
    returned tuple is a convenience and not the authoritative channel - the COBOL
    communicates through linkage, and so does this module.
    """
    return context.fs_reply, context.we_error


def ba_process_rdbms(context: _HandlerContext) -> None:
    """``ba-Process-RDBMS section.`` - [common/acas019.cbl:L543-L549]. A bare section head.

    ⭐ THE SECTION IS ENTERED AT ``ba010-Test-WS-Rec-Size``, NOT AT ``ba012``, AND THE
    DIFFERENCE IS THE LOG FILE NUMBER.
    """
    ba010_test_ws_rec_size(context)
    if ba012_test_ws_rec_size_2(context):
        ba_rdbms_exit(context)
        return
    ba015_test_ends(context)
    ba_rdbms_exit(context)


def ba010_test_ws_rec_size(context: _HandlerContext) -> None:
    """``ba010-Test-WS-Rec-Size.`` - [common/acas019.cbl:L551-L557]. ONE statement.

    ⭐ THE PARAGRAPH IS NAMED FOR WORK IT DOES NOT DO. Its three comment lines describe
    the record-size test, and the test itself is in ``ba012-Test-WS-Rec-Size-2`` below.
    All this paragraph does is renumber the log file.
    """
    context.file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(context: _HandlerContext) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` - [common/acas019.cbl:L559-L599]. Guard and
    credentials.

    ``end-if.`` at [:L599] closes the outer ``if`` opened at [:L561], and the six moves
    at [:L593-L598] sit at the same indentation as the two nested ``if``s above them.

    Returns:
        ``True`` when the paragraph took ``go to ba-rdbms-exit`` at [:L586], so that
            :func:`ba_process_rdbms` can skip the rest of the section - AAP section
            0.4.2 Class 2.
    """
    if _BRIDGE.ws_length_a == 0:
        _BRIDGE.ws_length_a = RECORD_LENGTH
        _BRIDGE.ws_length_b = RECORD_LENGTH
        if _BRIDGE.ws_length_a < _BRIDGE.ws_length_b:
            context.status(FsReply.ERROR, int(WeError.RECORD_SIZE_MISMATCH))

        # [:L572] tests `WE-Error = 901`, NOT the comparison above - anomaly
        # N-stale-901. A caller that arrived holding 901 takes this branch with sizes
        # that agree.
        if int(context.file_access.we_error) == int(WeError.RECORD_SIZE_MISMATCH):
            # `move spaces to Display-Blk` then the STRING into it [:L573-L579].
            display_blk = _cobol_move_alphanumeric(
                f"{_SL904}{_BRIDGE.ws_length_a:04d} < "
                f"OTM3-Record = {_BRIDGE.ws_length_b:04d}",
                _DISPLAY_BLK_WIDTH,
            )
            _LOG.error(
                "%s: %s [common/acas019.cbl:L580]",
                HANDLER_PROGRAM_ID,
                display_blk.rstrip(),
            )
            if int(context.dal_common.sw_testing) == 1:
                acas019_ca_process_logs(context)
            # `accept Accept-Reply at 2433` [:L585] - DROPPED, deviation D2. `go to ba-
            # rdbms-exit` [:L586] - PRESERVED, Class 2, reported to the caller.
            return True

        # The six credential moves [:L593-L598], INSIDE the guard, so once per process.
        rdb = load_rdb_data_once(context.system)
        target = context.file_access.rdb_data
        target.db_schema = rdb.db_schema
        target.db_uname = rdb.db_uname
        target.db_upass = rdb.db_upass
        target.db_port = rdb.db_port
        target.db_host = rdb.db_host
        target.db_socket = rdb.db_socket
        # The bridge's `ba020` reads the six `DB-*` fields.
        _BRIDGE.system_record = context.system

    # `end-if.` [:L599] - no transfer, so the section falls into `ba015-Test-Ends`.
    return False


def ba015_test_ends(context: _HandlerContext) -> None:
    """``ba015-Test-Ends.`` - [common/acas019.cbl:L601-L617]. The bridge CALL, inline.

    ⭐ ANOMALY N-nobadal: THERE IS NO ``ba020-*`` PARAGRAPH IN THIS HANDLER. The bridge
    CALL is inline here, which is the ``acas008``/``acas015``/``acas016`` shape;
    ``acas005``/``acas006``/``acas007``/``acas012`` route it through a separate
    paragraph. Reproduced by NOT creating a ``ba020_process_dal`` function.
    """
    otm3_mt(context.file_access, context.dal_common, context.record)
    context.read_status()


def ba_rdbms_exit(context: _HandlerContext) -> None:
    """``ba-rdbms-exit. exit section.`` - [common/acas019.cbl:L619-L620].

    The section's exit. Two callers: the record-size guard transfers here at [:L581], and
    ``ba015-Test-Ends`` falls into it. ``exit section`` returns to the ``perform
    ba-Process-RDBMS`` at [:L264], after which ``aa010-main`` transfers to ``AA-Main-Exit``.

    ⭐ IT DOES NOT LOG. ``Ca-Process-Logs`` is BELOW it at [:L623] and is reached only by an
    explicit ``perform`` - which nothing on this path issues. Anomaly N-nolog-on-dal: the
    bridge's ``ba999-end`` already logged.

     AND NEITHER DOES THIS FUNCTION. ``exit section`` is one statement that writes
    nothing and displays nothing, so the position trace this paragraph used to emit was
    invented (R-4) - and it contradicted the docstring immediately above it, which says
    the paragraph does not log. The status pair it announced is the caller's to read from
    ``File-Access``, which is where the section leaves it.
    """
    del context


def acas019_ca_process_logs(context: _HandlerContext) -> None:
    """``Ca-Process-Logs.`` in ``acas019`` - [common/acas019.cbl:L623-L627], VERBATIM::

    ⭐⭐ ANOMALY N-nolog-on-dal, STATED BY THE MAINTAINER ON THE LABEL LINE ITSELF. The
    comment is not above the paragraph, it is ON it: ``*> Not called on DAL access as it
    does it already``. So this paragraph runs on the FLAT-FILE path only, from
    ``aa999-main-exit`` [:L533] and from ``aa030``'s second, deliberate call [:L356]. On the
    DAL path the bridge's ``ba999-end`` logs instead [common/otm3MT.cbl:L1323-L1324], which
    is why one CALL yields exactly one record.

    ⭐ THE NAME IS QUALIFIED BY PROGRAM only because ``otm3MT`` declares a paragraph of the
    same name - see :func:`otm3mt_ca_process_logs` for the reasoning. Two names in each
    program are qualified; every other paragraph keeps its own.

    ``fhlogger`` is out of scope [AAP section 0.2.2], so the record is emitted through
    :func:`acas_posting.dal.status.log_file_handler_record`, THE SAME ONE ADAPTER the
    bridge's like-named paragraph uses, so that the two render identically and differ only
    in the program they name. No database effect, no control-flow effect.

    ``WS-File-Key`` is WITHHELD: on this record it is the customer-and-invoice key
    (CWE-532). ``Log-File-Rec-Written`` is ADVANCED modulo one million rather than pinned
    to 1 - see :func:`otm3mt_ca_process_logs` for why pinning it was wrong twice over.
    """
    logging_data = context.file_access.logging_data
    log_file_handler_record(
        _LOG,
        program=HANDLER_PROGRAM_ID,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(context.file_access.file_function),
        access_type=int(context.file_access.access_type),
        fs_reply=int(context.file_access.fs_reply),
        we_error=int(context.file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=context.dal_common,
    )
    acas019_ca_exit(context)


def acas019_ca_exit(context: _HandlerContext) -> None:
    """``ca-Exit. exit.`` in ``acas019`` - [common/acas019.cbl:L629-L630].

    A bare ``exit`` - a no-operation giving the paragraph a name to end at, and the last
    paragraph of the program. Reproduced as a named function so the inventory is
    complete.
    """


def dispatch(
    system: SystemRecord,
    otm3: OiHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool | None = None,
) -> tuple[int, int]:
    """``call "acas019" using System-Record, WS-OTM3-Record, File-Access, File-Defs, ACAS-
    DAL-Common-data``.

    WHAT HAPPENS, in the COBOL's order: the log identity, then the key guard, then the
    RDB branch - and on the DAL path THAT IS ALL, because [:L262-L266] leaves for ``AA-
    Main-Exit`` before the function dispatch is reached (docstring C2).

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob], read for ``RDBMS-Flat-
            Statuses`` at [:L262-L263] and for the six credential fields at
            [:L586-L591].
        otm3: ``WS-OTM3-Record``. The handler's LINKAGE declares it by
            ``copy "slwsoi.cob" replacing OI-Header by WS-OTM3-Record`` [:L215] - the SAME
            declaration the bridge uses [common/otm3MT.cbl:L345-L346], which is docstring
            C3's correction to the agent prompt. MUTATED IN PLACE by a successful read.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L64], carrying the request
            in and the status, diagnostics, logging fields and ``RDB-Data`` out.
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Held because the linkage declares
            it; this handler names no field of it, because the RDB path addresses a table
            rather than a file and the flat-file path's ``select`` resolves its own name
            [copybooks/slseloi3.cob]. Recorded as a linkage item consumed by neither path.
        dal_common: ``ACAS-DAL-Common-data``
            [copybooks/Test-Data-Flags.cob:L10-L16] - ``Testing-1`` gates the logging and
            ``Testing-2`` the diagnostics (deviation D2).
        transport: The caller's transport declaration, forwarded to the open. KEYWORD-ONLY
            and NOT part of the frozen five-parameter linkage, for the reason
            ``acas006_gl_posting.dispatch`` gives for the identical parameter: the bridge
            reaches the server through ``RDB-Data`` and a C interface that has no transport
            policy at all [common/otm3MT.cbl:L459], so there is no COBOL operand this could
            correspond to. ``None`` - the default - leaves the working-storage declaration
            alone, and that declaration is itself ``None``, which
            ``connection._require_permitted_connection`` resolves FAIL-CLOSED. Pass
            ``TransportSecurity(isolated_oracle=True)`` to declare the parity harness, or
            ``TransportSecurity(ca_file=...)`` to verify and encrypt. It changes no status,
            no statement and no write order.
        allow_frozen_placeholder_credentials: Whether the shipped placeholders of
            [copybooks/wssystem.cob:L138-L139] may authenticate. Keyword-only for the same
            reason, and ``None`` likewise leaves the working-storage declaration - itself
            ``False`` - alone.

    Returns:
        The ``(FS-Reply, We-Error)`` pair, which is also in ``file_access``.
    """
    # The two keyword-only declarations are recorded in working storage BEFORE the
    # dispatch, because `ba020-Process-Open` reads them from there - it is reached
    # through the nine-arm `evaluate` and cannot take arguments of its own. `None`
    # means "the caller stated nothing", which leaves the INSTALLED PROCESS POLICY
    # in force rather than overwriting it with a permissive one.
    if transport is not None:
        _BRIDGE.transport = transport
    if allow_frozen_placeholder_credentials is not None:
        _BRIDGE.allow_frozen_placeholder_credentials = (
            allow_frozen_placeholder_credentials
        )

    context = _HandlerContext(
        system=system,
        record=otm3,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=dal_common,
    )
    # `File-Defs` is a linkage item this handler never reads a field of. It is part of
    # the contract because the frozen `PROCEDURE DIVISION USING` list names it
    # [common/acas019.cbl:L225-L231], and the parameter above records that; NO RECORD IS
    # EMITTED to prove it. The frozen dispatch displays nothing, so a per-CALL trace was
    # invented (R-4) - and it would have been the highest-volume record in the module,
    # one per handler call, with `file-defs delimiter` carrying a fragment of the
    # deployment's own filesystem convention.
    return aa_process_flat_file(context)
