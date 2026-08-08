"""`acas008` and its bridge `slpostingMT` - the `PSIRSPOST-REC` transfer table.

The data-access module for the SPL-Posting entity: the transfer file `sl060` and
`pl060` write and `irs030` consumes. Three of its behaviours are defects that are
reproduced, not repaired.

FOUR PUBLISHED VERBS CAN NEVER SUCCEED. The handler rejects read-indexed,
rewrite, start and delete unconditionally at entry
[common/acas008.cbl:L299-L307], because the underlying file is sequential - yet
the facade publishes Rewrite anyway, so a caller invoking it always fails. The
guard is reproduced and returns the same status pair rather than performing an
update.

OPEN-OUTPUT MEANS A DELETE-ALL [common/acas008.cbl:L313-L319],
[common/acas008.cbl:L571-L574], which is how `irs030`'s end-of-job clear is
implemented [irs/irs030.cbl:L1720-L1724]. IT IS NOT A TRUNCATE, and this is the
one claim about this handler most likely to be got wrong: the bridge builds a
STRICT `<` predicate from the ten-character key text `9999999999`
[common/slpostingMT.cbl:L850-L891], while every key it stores is a group-move
image near 4.7e17 [common/slpostingMT.cbl:L1001] - so the clear is MEASURED to
remove no row this bridge ever wrote. The measured table for this handler and its
three siblings is the key-bound note under A-NEW-8 in
docs/migration/anomaly-log.md; `N-DELALLMUTATES` is registered there too.

The handler also labels its own log identity as the IRS subsystem
[common/acas008.cbl:L293-L294] although it serves the Sales and Purchase side;
the label is carried as written.
"""

from __future__ import annotations

import contextlib
import enum
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Final

from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    acquire_cursor,
    cobol_string_delimited_by_space,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    HANDLER_REJECTED_FUNCTIONS,
    SEQUENTIAL_READ_START,
    TABLE_OF_KEYNAMES,
    TABLE_PRIMARY_KEYS,
    CursorOutcome,
    CursorSlot,
    CursorStateTable,
    KeyOfReference,
)
from acas_posting.dal.cursor_state import key_of_reference as _key_of_reference
from acas_posting.dal.cursor_state import read_next as _cursor_read_next
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    DUPLICATE_KEY_ERRNOS,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess, LoggingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.spl_irs_posting import WsIrsPostingRecord, WsIrsPostKey
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "TABLE_NAME",
    "HANDLER_NAME",
    "BRIDGE_NAME",
    "ENTITY_FACADE",
    "PROG_NAME",
    "BRIDGE_PROG_NAME",
    "PRIMARY_KEY_COLUMN",
    "WS_LOG_SYSTEM",
    "WS_LOG_FILE_NO_COBOL",
    "WS_LOG_FILE_NO_RDB",
    "WS_RECORD_LENGTH",
    "FD_RECORD_LENGTH",
    "REJECTED_FUNCTIONS",
    "SUPPORTED_HANDLER_FUNCTIONS",
    "COERCED_FUNCTION",
    "BRIDGE_DISPATCH_FUNCTIONS",
    "ABSENT_PARAGRAPHS",
    "KEY_OF_REFERENCE",
    "KEY_METADATA_IS_UNREACHABLE",
    "SEQUENTIAL_READ",
    "COLUMNS",
    "COLUMNS_BY_ATTRIBUTE",
    "KEY_SUBFIELDS_WITHOUT_COLUMNS",
    "ColumnBinding",
    "Renderer",
    "HostVariables",
    "WorkingStorage",
    "BridgeVerbUnreachable",
    "CobolFlatFileNotMigrated",
    "cobol_group_image",
    "group_move_to_binary",
    "binary_move_to_group",
    "numeric_display_value",
    "ws_mysql_edit",
    "edit_slice",
    "function_trim",
    "function_trim_trailing",
    "render_column",
    "working_storage",
    "reset_working_storage",
    "dispatch",
    "aa_process_flat_file",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa070_process_write",
    "aa080_process_delete",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_main_exit",
    "aa_exit",
    "ba_process_rdbms",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba_rdbms_exit",
    "ca_process_logs",
    "ca_exit",
    "slposting_mt",
    "ba_acas_dal_process",
    "ba010_initialise",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba070_process_write",
    "ba085_process_delete_all",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba999_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


TABLE_NAME: Final[str] = "PSIRSPOST-REC"

HANDLER_NAME: Final[str] = "acas008"

BRIDGE_NAME: Final[str] = "slpostingMT"

ENTITY_FACADE: Final[str] = "SPL-Posting"

PROG_NAME: Final[str] = "acas008 (3.3.00)"

BRIDGE_PROG_NAME: Final[str] = "slpostingMT (3.3.00)"

#: ``PRIMARY KEY (`IRS-POST-KEY`)`` [mysql/ACASDB.sql:L377]. Read from ``cursor_state``
#: rather than restated, so one declaration serves both modules.
PRIMARY_KEY_COLUMN: Final[str] = TABLE_PRIMARY_KEYS[TABLE_NAME]

#: ``move 1 to WS-Log-System`` [common/acas008.cbl:L293]. Anomaly N-LOGSYSTEM: the value
#: is the IRS subsystem even though Sales and Purchase are the callers.
WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.IRS

#: ``move 15 to WS-Log-File-No`` [common/acas008.cbl:L294] - the Cobol-path value,
#: recorded because anomaly N-LOGFILE overwrites it.
WS_LOG_FILE_NO_COBOL: Final[int] = 15

#: ``move 25 to WS-Log-File-no`` [common/acas008.cbl:L522] - the RDB-path value that
#: replaces it. Anomaly N-LOGFILE. Note the ``-No`` / ``-no`` capitalisation change
#: between the two frozen statements.
WS_LOG_FILE_NO_RDB: Final[int] = 25

WS_RECORD_LENGTH: Final[int] = 84

#: ``function length(IRS-Posting-Record)`` [common/acas008.cbl:L530-L532] - the FD
#: record from ``copybooks/fdpost-irs.cob``, MEASURED at the same 84 bytes because it
#: declares the same fields. See ambiguity Q-2.
FD_RECORD_LENGTH: Final[int] = 84


# `ws-No-Paragraph` values [copybooks/wsfnctn.cob:L48] The handler numbers its
# paragraphs in the 200 range and the bridge in the 1..20 range.

_HANDLER_PARA_OPEN: Final[int] = 201
_HANDLER_PARA_CLOSE: Final[int] = 202
_HANDLER_PARA_READ_NEXT: Final[int] = 203
#: ``move 206 to WS-No-Paragraph`` [common/acas008.cbl:L469]. 204 and 205 are unused by
#: this handler, because read-indexed and start have no paragraph here (O-1).
_HANDLER_PARA_WRITE: Final[int] = 206
#: ``move 207 to WS-No-Paragraph`` [common/acas008.cbl:L478], in the unreachable delete
#: paragraph - anomaly N-DEADDELETE.
_HANDLER_PARA_DELETE: Final[int] = 207

_BRIDGE_PARA_OPEN: Final[int] = 1
_BRIDGE_PARA_CLOSE: Final[int] = 2
_BRIDGE_PARA_SELECT: Final[int] = 3
_BRIDGE_PARA_FETCH: Final[int] = 4
_BRIDGE_PARA_INSERT: Final[int] = 10
_BRIDGE_PARA_DELETE: Final[int] = 13
_BRIDGE_PARA_FREE: Final[int] = 20


#: ANOMALY A-6, as data.
REJECTED_FUNCTIONS: Final[Mapping[FileFunction, tuple[FsReply, WeError, str]]] = (
    HANDLER_REJECTED_FUNCTIONS[TABLE_NAME]
)

#: The four functions the handler honours [common/acas008.cbl:L354-L375]. In the order
#: of the frozen ``evaluate``'s ``when`` clauses, which here IS numeric. Function 6 is
#: absent deliberately.
SUPPORTED_HANDLER_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,
    FileFunction.CLOSE,
    FileFunction.READ_NEXT,
    FileFunction.WRITE,
)

#: The function ``Open`` plus ``Output`` is REPLACED BY, never merely followed by
#: [common/acas008.cbl:L316] and [:L573]. See the module docstring.
COERCED_FUNCTION: Final[FileFunction] = FileFunction.DELETE_ALL

#: What the BRIDGE's own dispatch accepts [common/slpostingMT.cbl:L345-L366].
BRIDGE_DISPATCH_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,
    FileFunction.CLOSE,
    FileFunction.READ_NEXT,
    FileFunction.WRITE,
    FileFunction.DELETE_ALL,
)

#: OMISSION O-1. Paragraphs present in every sibling handler and absent here, each
#: mapped to the reason the frozen source gives.
ABSENT_PARAGRAPHS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "aa050-Process-Read-Indexed": (
            "absent - fn-read-indexed (4) is refused at entry "
            "[common/acas008.cbl:L300]; the commented-out dispatch arm survives at "
            "[common/acas008.cbl:L362-L363]"
        ),
        "aa060-Process-Start": (
            "absent - fn-start (9) is refused at entry [common/acas008.cbl:L302]; "
            "commented-out dispatch arm at [common/acas008.cbl:L371-L372]"
        ),
        "aa090-Process-Rewrite": (
            "absent - fn-re-write (7) is refused at entry "
            "[common/acas008.cbl:L301]; commented-out dispatch arm at "
            "[common/acas008.cbl:L367-L368]"
        ),
        "aa041-Reread / aa051-Reread / aa047-Eval-Keys": (
            "absent - the handler holds no cursor of its own; the bridge owns "
            "positioning and its own ba041 is delegated to dal/cursor_state.py"
        ),
        "ba020-Process-DAL": (
            "absent - the bridge CALL is INLINE in ba015-Test-Ends "
            "[common/acas008.cbl:L583-L587]; no sibling handler does this"
        ),
    }
)


#: The bridge's ``Table-Of-Keynames`` for this table, transcribed EXACTLY as declared
#: [common/slpostingMT.scb:L213-L223]:: 01 Table-Of-Keynames. 03 filler pic x(30) value
#: "IRS-POST-KEY ".
KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[TABLE_NAME][0]

#: True, and it is a statement about the COBOL rather than about this module.
KEY_METADATA_IS_UNREACHABLE: Final[bool] = True

SEQUENTIAL_READ: Final[Any] = SEQUENTIAL_READ_START[TABLE_NAME]


# COBOL language primitives Everything in this block reimplements a COBOL language rule
# rather than any accounting behaviour, and every one of them was MEASURED against the
# compiled oracle because the source alone could not settle it.

#: ``WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` [common/slpostingMT.cbl:L205], MEASURED at 30
#: characters.
_EDIT_WIDTH: Final[int] = 30
_EDIT_INTEGER_DIGITS: Final[int] = 19
_EDIT_DECIMAL_DIGITS: Final[int] = 9

_KEY_HOST_VARIABLE_BYTES: Final[int] = 8

_KEY_GROUP_LENGTH: Final[int] = 10

_KEY_SUBFIELD_LENGTH: Final[int] = 5

#: COBOL bytes are 8-bit and are not text.
_BYTE_CODEC: Final[str] = "latin-1"


def cobol_group_image(key: WsIrsPostKey) -> str:
    """Render ``WS-IRS-Post-Key`` to its ten-character COBOL byte image.

    A ``pic 9(5)`` item holds five digits and is unsigned, so a value that will not fit
    is reduced exactly as a COBOL MOVE reduces it.

    Args:
        key: The two-field key group.

    Returns:
        Exactly ten characters.
    """
    modulus = 10**_KEY_SUBFIELD_LENGTH
    batch = abs(int(key.ws_irs_batch)) % modulus
    number = abs(int(key.ws_irs_post_number)) % modulus
    return f"{batch:0{_KEY_SUBFIELD_LENGTH}d}{number:0{_KEY_SUBFIELD_LENGTH}d}"


def group_move_to_binary(image: str, size: int = _KEY_HOST_VARIABLE_BYTES) -> int:
    """``move <group> to <binary>`` - a RAW BYTE REINTERPRETATION, MEASURED.

    Reproduces ``move WS-IRS-Post-Key to HV-IRS-POST-KEY``
    [common/slpostingMT.cbl:L1001]. The sending operand is a GROUP item, so COBOL treats
    BOTH operands as alphanumeric and moves bytes without conversion: left-justified
    into the receiving item, truncated on the right when the sender is longer.

    Args:
        image: The sending group's byte image, as :func:`cobol_group_image` returns.
        size: The receiving binary item's width in bytes. Eight, measured.

    Returns:
        The receiving field's value.
    """
    raw = image.encode(_BYTE_CODEC)
    # Alphanumeric MOVE: left-justified, truncated on the right, SPACE-padded on the
    # right when the sender is shorter - never zero-padded.
    raw = raw[:size] if len(raw) >= size else raw + b" " * (size - len(raw))
    # `signed=True` is anomaly N-SIGNADDED: an unsigned group becomes a signed binary
    # [common/slpostingMT.cbl:L266] and then a `bigint(11)` that is NOT declared
    # `unsigned` [mysql/ACASDB.sql:L367].
    return int.from_bytes(raw, byteorder="big", signed=True)


def binary_move_to_group(
    value: int,
    size: int = _KEY_HOST_VARIABLE_BYTES,
    group_length: int = _KEY_GROUP_LENGTH,
) -> str:
    """``move <binary> to <group>`` - the reverse raw byte move, MEASURED.

    Reproduces ``move HV-IRS-POST-KEY to WS-IRS-Post-Key``
    [common/slpostingMT.cbl:L1029]. The RECEIVING operand is the group this time, so the
    move is alphanumeric again.

    Args:
        value: The binary host variable's value.
        size: Its width in bytes.
        group_length: The receiving group's length in characters.

    Returns:
        Exactly ``group_length`` characters, which may include non-printable bytes.

    Raises:
        OverflowError: If ``value`` does not fit the declared binary width. The frozen
            field is eight bytes, so a value outside that range cannot have come from
            it.
    """
    raw = int(value).to_bytes(size, byteorder="big", signed=True)
    raw = (
        raw[:group_length]
        if len(raw) >= group_length
        else raw + b" " * (group_length - len(raw))
    )
    return raw.decode(_BYTE_CODEC)


def numeric_display_value(image: str) -> int:
    """The value of a zoned-decimal ``pic 9(n)`` item, whatever bytes it holds.

    MEASURED. After the group move above, ``WS-IRS-Batch`` and ``WS-IRS-Post-
    Number`` contain arbitrary bytes rather than ASCII digits, yet the compiled program
    still yields a DEFINED value for them: the low nibble of each byte, folded left to
    right.

    Args:
        image: The field's byte image.

    Returns:
        The field's numeric value.
    """
    value = 0
    for character in image:
        value = value * 10 + (ord(character) & 0x0F)
    return value


def ws_mysql_edit(value: Decimal | int) -> str:
    """Render a host variable through ``WS-MYSQL-EDIT``, MEASURED.

    Reproduces ``move <host variable> to WS-MYSQL-EDIT``, which the generated
    ``bb200-Insert`` performs before every numeric column
    [common/slpostingMT.cbl:L1060-L1061, L1088-L1089, L1112-L1113, L1138-L1139,
    L1161-L1162]. The field is ``PIC -Z(18)9.9(9)`` [common/slpostingMT.cbl:L205]; its
    layout is documented at :data:`_EDIT_WIDTH`.

    Args:
        value: The host variable's value. ``Decimal`` for the two money columns and
            ``int`` for the key and the three integer columns.

    Returns:
        Exactly 30 characters.
    """
    if isinstance(value, Decimal):
        negative = value.is_signed() and value != 0
        # `copy_abs` is context-free, unlike `abs`, so a nineteen-digit value cannot be
        # rounded by the ambient precision on its way through here.
        magnitude_text = format(value.copy_abs(), "f")
    else:
        integer = int(value)
        negative = integer < 0
        magnitude_text = str(-integer if negative else integer)

    integer_text, _, fraction_text = magnitude_text.partition(".")

    integer_text = integer_text[-_EDIT_INTEGER_DIGITS:].rjust(
        _EDIT_INTEGER_DIGITS, "0"
    )
    fraction_text = fraction_text[:_EDIT_DECIMAL_DIGITS].ljust(
        _EDIT_DECIMAL_DIGITS, "0"
    )

    # `Z(18)` then `9`: suppress leading zeros over the first eighteen positions and
    # never over the nineteenth.
    rendered: list[str] = []
    suppressing = True
    last = _EDIT_INTEGER_DIGITS - 1
    for index, digit in enumerate(integer_text):
        if index == last:
            rendered.append(digit)
        elif suppressing and digit == "0":
            rendered.append(" ")
        else:
            suppressing = False
            rendered.append(digit)

    edit = f"{'-' if negative else ' '}{''.join(rendered)}.{fraction_text}"
    if len(edit) != _EDIT_WIDTH:  # pragma: no cover - guards the layout constants
        raise AssertionError(
            f"WS-MYSQL-EDIT must be {_EDIT_WIDTH} characters "
            f"[common/slpostingMT.cbl:L205]; built {len(edit)}"
        )
    return edit


def edit_slice(edit: str, start: int, length: int) -> str:
    """COBOL reference modification, ``edit(start:length)`` - ONE-BASED.

    Args:
        edit: The 30-character image from :func:`ws_mysql_edit`.
        start: The one-based start position, as written in the COBOL.
        length: The number of characters.

    Returns:
        The requested substring.
    """
    return edit[start - 1 : start - 1 + length]


def function_trim(text: str) -> str:
    """``FUNCTION TRIM (x)`` - remove leading AND trailing spaces.

    The bare form, with no ``LEADING``/``TRAILING`` keyword, is what the bridge applies
    to every ``WS-MYSQL-EDIT`` slice [common/slpostingMT.cbl:L1062, L1088, L1112, L1138,
    L1163], because those slices are space-padded on the LEFT by zero suppression.

    Args:
        text: The sending item.

    Returns:
        The trimmed value - the empty string when the input is all spaces, per
            MEASURED.
    """
    return text.strip(" ")


def function_trim_trailing(text: str) -> str:
    """``FUNCTION TRIM (x, TRAILING)`` - remove trailing spaces ONLY.

    an all-space field this returns a ZERO-LENGTH string, measured at length ``0`` for
    both ``X(2)`` and ``X(32)``. So an unset code is stored as ``''`` and not as two
    spaces.

    Args:
        text: The sending item.

    Returns:
        The trimmed value.
    """
    return text.rstrip(" ")


class Renderer(enum.Enum):
    """How ``bb200-Insert`` turns one host variable into one SQL value.

    Five forms, no more, and each is used by a fixed set of columns
    [common/slpostingMT.cbl:L1051-L1176].
    """

    EDIT_03_18 = "TRIM(WS-MYSQL-EDIT(03:18))"
    TRIM_TRAILING = "TRIM(hv,TRAILING)"
    EDIT_11_10 = "TRIM(WS-MYSQL-EDIT(11:10))"
    #: money columns. Assembles the decimal point by hand and never reads position 1, so
    #: THE SIGN IS LOST, MEASURED.
    EDIT_14_07_DOT_22_02 = 'TRIM(WS-MYSQL-EDIT(14:07)) "." WS-MYSQL-EDIT(22:02)'
    EDIT_18_03 = "TRIM(WS-MYSQL-EDIT(18:03))"


#: Which renderer each column uses, and the ``bb200-Insert`` lines that say so.
_RENDERER_BY_COLUMN: Final[Mapping[str, tuple[Renderer, str]]] = MappingProxyType(
    {
        "IRS-POST-KEY": (Renderer.EDIT_03_18, "[common/slpostingMT.cbl:L1058-L1064]"),
        "IRS-POST-CODE": (
            Renderer.TRIM_TRAILING,
            "[common/slpostingMT.cbl:L1070-L1075]",
        ),
        "IRS-POST-DAT": (
            Renderer.TRIM_TRAILING,
            "[common/slpostingMT.cbl:L1079-L1084]",
        ),
        "IRS-POST-DR": (Renderer.EDIT_11_10, "[common/slpostingMT.cbl:L1088-L1094]"),
        "IRS-POST-CR": (Renderer.EDIT_11_10, "[common/slpostingMT.cbl:L1100-L1106]"),
        "IRS-POST-AMOUNT": (
            Renderer.EDIT_14_07_DOT_22_02,
            "[common/slpostingMT.cbl:L1112-L1123]",
        ),
        "IRS-POST-LEGEND": (
            Renderer.TRIM_TRAILING,
            "[common/slpostingMT.cbl:L1129-L1134]",
        ),
        "IRS-VAT-AC-DEF": (
            Renderer.EDIT_18_03,
            "[common/slpostingMT.cbl:L1138-L1144]",
        ),
        "IRS-POST-VAT-SIDE": (
            Renderer.TRIM_TRAILING,
            "[common/slpostingMT.cbl:L1150-L1155]",
        ),
        "IRS-VAT-AMOUNT": (
            Renderer.EDIT_14_07_DOT_22_02,
            "[common/slpostingMT.cbl:L1159-L1170]",
        ),
    }
)


@dataclass(frozen=True)
class ColumnBinding:
    """One of the ten columns, with every fact about it traced to its source.

    Nothing here is transcribed by eye. Agent Action Plan section 0.8.1 makes that a
    directive rather than a preference - "**Data dictionary first.** ... every Python
    field definition cites its entry.
    """

    ordinal: int
    #: The MySQL column name. Contains a HYPHEN, like every identifier in this schema,
    #: so it is never emitted unquoted.
    column: str
    dictionary_key: str
    citation: str
    copybook_field: str
    record_attribute: str
    host_variable: str
    host_variable_attribute: str
    load_source: str
    unload_source: str
    renderer: Renderer
    renderer_source: str
    sql_type: str
    #: Whether the column is declared ``unsigned``. ``IRS-POST-KEY`` is the only integer
    #: key in the GL/SPL group that is NOT - anomaly N-SIGNADDED.
    unsigned: bool
    is_primary_key: bool
    #: The drift between the three layers, from ``loader.drift_for``.
    drift: Any


def _python_attribute(cobol_name: str) -> str:
    """The record/host-variable attribute name for a COBOL data name."""
    return cobol_name.lower().replace("-", "_")


def _build_columns() -> tuple[ColumnBinding, ...]:
    """Assemble :data:`COLUMNS` from the generated data dictionary, once, at import.

    Ordered by ``CREATE TABLE`` ordinal, which is the order the bridge loads, unloads
    and inserts in. Determinism is structural.
    """
    bindings: list[ColumnBinding] = []
    for entry in sorted(
        loader.entries_for_table(TABLE_NAME), key=lambda item: item.column.ordinal
    ):
        column = entry.column
        copybook = entry.copybook
        host_variable = entry.bridge_host_variable
        if copybook is None or host_variable is None:  # pragma: no cover
            raise AssertionError(
                f"{entry.key} is missing a copybook field or a bridge host variable; "
                f"the bridge is the authoritative mapping for this migration "
                f"[common/slpostingMT.cbl:L257-L259] and every column of "
                f"{TABLE_NAME} has both"
            )
        renderer, renderer_source = _RENDERER_BY_COLUMN[column.name]
        bindings.append(
            ColumnBinding(
                ordinal=column.ordinal,
                column=column.name,
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                copybook_field=copybook.name,
                record_attribute=_python_attribute(copybook.name),
                host_variable=host_variable.name,
                host_variable_attribute=_python_attribute(host_variable.name),
                load_source=host_variable.load_source,
                unload_source=host_variable.unload_source,
                renderer=renderer,
                renderer_source=renderer_source,
                sql_type=column.sql_type,
                unsigned=bool(column.unsigned),
                is_primary_key=bool(column.is_primary_key),
                drift=loader.drift_for(entry.key),
            )
        )
    if len(bindings) != len(_RENDERER_BY_COLUMN):  # pragma: no cover
        raise AssertionError(
            f"{TABLE_NAME} has exactly {len(_RENDERER_BY_COLUMN)} columns "
            f"[mysql/ACASDB.sql:L366-L378]; the dictionary yielded {len(bindings)}"
        )
    return tuple(bindings)


COLUMNS: Final[tuple[ColumnBinding, ...]] = _build_columns()

COLUMNS_BY_ATTRIBUTE: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.record_attribute: binding for binding in COLUMNS}
)

#: OMISSION - the two key subfields have NO column of their own.
KEY_SUBFIELDS_WITHOUT_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.cite(descriptor.dictionary_key)
    for descriptor in WsIrsPostKey.FIELDS
    if descriptor.dictionary_key is not None
)


def render_column(binding: ColumnBinding, value: Decimal | int | str) -> str:
    """Render one host-variable value exactly as ``bb200-Insert`` renders it.

    Reproduces the per-column blocks of [common/slpostingMT.cbl:L1051-L1176]. Each block
    emits ``'`COL`="'``, then the rendered text, then ``'"'`` - so EVERY VALUE REACHES
    MySQL AS A QUOTED STRING, including the numeric columns, and the server coerces it.

    Args:
        binding: The column, carrying its renderer and that renderer's locator.
        value: The host variable's value.

    Returns:
        The text the bridge would have placed between the two double quotes.

    Raises:
        TypeError: If the value's Python type cannot be the host variable's.
    """
    renderer = binding.renderer
    if renderer is Renderer.TRIM_TRAILING:
        if not isinstance(value, str):
            raise TypeError(
                f"{binding.host_variable} is a character host variable "
                f"{binding.load_source}; got {type(value).__name__}"
            )
        return function_trim_trailing(value)

    if isinstance(value, str):
        raise TypeError(
            f"{binding.host_variable} is a numeric host variable "
            f"{binding.load_source}; got str"
        )
    edit = ws_mysql_edit(value)
    if renderer is Renderer.EDIT_03_18:
        return function_trim(edit_slice(edit, 3, 18))
    if renderer is Renderer.EDIT_11_10:
        return function_trim(edit_slice(edit, 11, 10))
    if renderer is Renderer.EDIT_18_03:
        return function_trim(edit_slice(edit, 18, 3))
    # `Renderer.EDIT_14_07_DOT_22_02`: the decimal point is assembled by hand from three
    # separate `string` statements [common/slpostingMT.cbl:L1163-L1170], and position 1
    # - the sign - is never among them.
    return f"{function_trim(edit_slice(edit, 14, 7))}.{edit_slice(edit, 22, 2)}"


class CobolFlatFileNotMigrated(RuntimeError):
    """The Cobol flat-file leg of a handler paragraph, which has no target.

    OMISSION O-2, raised at exactly the statement that cannot be reproduced and nowhere
    else.
    """


class BridgeVerbUnreachable(RuntimeError):
    """A bridge paragraph that no compiled run can enter was asked for anyway.

    ``slpostingMT`` implements all nine verbs, but its ONLY caller refuses four of them
    before dispatching [common/acas008.cbl:L299-L307], so ``ba050-Process-Read-Indexed``
    [common/slpostingMT.cbl:L552], ``ba060-Process-Start`` [:L647], ``ba080-Process-
    Delete`` [:L771] and ``ba090-Process-Rewrite`` [:L916] are dead code in the shipped
    COBOL.
    """


@dataclass
class HostVariables:
    """``TD-PSIRSPOST-REC``, the bridge's host-variable group.

    Transcribed field for field from [common/slpostingMT.cbl:L264-L275], which the JC
    preSQL translator generated from the directive [common/slpostingMT.scb:L257-L260].
    The Agent Action Plan's preserved user requirement makes this group, not the
    copybook, the authority.
    """

    hv_irs_post_key: int = 0
    hv_irs_post_code: str = " " * 2
    hv_irs_post_dat: str = " " * 8
    hv_irs_post_dr: int = 0
    hv_irs_post_cr: int = 0
    hv_irs_post_amount: Decimal = Decimal("0.00")
    hv_irs_post_legend: str = " " * 32
    hv_irs_vat_ac_def: int = 0
    hv_irs_post_vat_side: str = " " * 2
    hv_irs_vat_amount: Decimal = Decimal("0.00")

    @classmethod
    def initialize(cls) -> HostVariables:
        """``initialize TD-PSIRSPOST-REC`` [common/slpostingMT.cbl:L1000].

        Returns a group in the state COBOL's ``INITIALIZE`` leaves: numeric items zero,
        alphanumeric items spaces. A fresh instance rather than an in-place reset,
        because the group is rebuilt from scratch on every load.
        """
        return cls()


@dataclass
class WorkingStorage:
    """The two programs' WORKING-STORAGE, which persists between ``CALL``s.

    A COBOL sub-program's WORKING-STORAGE is static: it survives from one ``CALL`` to
    the next for the life of the run.
    """

    #: ``77 A pic 9(4) value zero`` [common/acas008.cbl:L253] - "A & B used in 1st test
    #: ONLY in ba-Process-RDBMS".
    a: int = 0
    #: ``77 B pic 9(4) value zero`` [common/acas008.cbl:L254]. The measured length of
    #: ``IRS-Posting-Record`` [:L530-L532], the FD side of the comparison. Never read as
    #: a gate.
    b: int = 0
    cobol_file_status: int = 0
    connection: Any = None
    system_record: SystemRecord | None = None
    transport: TransportSecurity | None = None
    #: Whether the caller has declared that the frozen placeholder credentials
    #: shipped in ``copybooks/wssystem.cob`` may be used against a disposable
    #: server. ``dal/connection.py`` refuses them otherwise.
    allow_frozen_placeholder_credentials: bool | None = None
    #: ``TD-PSIRSPOST-REC`` [common/slpostingMT.cbl:L265].
    host_variables: HostVariables = field(default_factory=HostVariables)
    #: ``01 DAL-Data`` - ``MOST-Relation`` and ``Most-Cursor-Set`` with its two
    #: condition names [common/slpostingMT.scb:L229-L233] - plus the stored result the
    #: ``/MYSQL SELECT\`` materialises.
    cursor_states: CursorStateTable = field(default_factory=CursorStateTable)

    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof value 1`` [common/acas008.cbl:L257].

        A condition-name predicate. Written inline rather than imported, because
        ``acas_posting.cobol`` is outside this module's dependency set.
        """
        return self.cobol_file_status == 1


_WORKING_STORAGE: WorkingStorage = WorkingStorage()


def working_storage() -> WorkingStorage:
    """The run's WORKING-STORAGE for this handler and its bridge.

    Returns:
        The single instance. Static for the life of the process, as COBOL's is for the
            life of the run.
    """
    return _WORKING_STORAGE


def reset_working_storage() -> None:
    """Discard the working storage, as ending the run and starting another would.

    Closes any live connection first, so that a reset cannot leak one. The cursor state
    goes with the instance, because :attr:`WorkingStorage.cursor_states` is private to
    it. Mirrors :func:`~acas_posting.dal.connection.reset_rdb_data_cache` and
    :func:`~acas_posting.dal.cursor_state.reset`, which exist for the same reason.
    """
    global _WORKING_STORAGE  # noqa: PLW0603 - the module-level singleton IS the model
    if _WORKING_STORAGE.connection is not None:
        mysql_1980_close(_WORKING_STORAGE.connection)
        mysql_1999_exit()
    _WORKING_STORAGE.cursor_states.reset(TABLE_NAME)
    _WORKING_STORAGE = WorkingStorage()


# Condition names `88`-level predicates for the levels this handler tests. Written
# inline with their copybook citations because `acas_posting.cobol.condition_names` is
# outside this module's permitted dependency set.


def _fs_cobol_files_used(system: SystemRecord) -> bool:
    """``88 FS-Cobol-Files-Used value zero`` [copybooks/wssystem.cob:L113]."""
    return system.system_data_block.rdbms_flat_statuses.file_system_used == 0


def _testing_1(dal_common: AcasDalCommonData) -> bool:
    """``88 Testing-1 value 1`` [copybooks/Test-Data-Flags.cob]."""
    return dal_common.sw_testing == 1


def _testing_2(dal_common: AcasDalCommonData) -> bool:
    """``88 Testing-2 value 1`` [copybooks/Test-Data-Flags.cob]."""
    return dal_common.sw_testing_2 == 1


# THE BRIDGE - slpostingMT Everything from here to `slposting_mt` reproduces
# `common/slpostingMT.cbl`, the program the JC preSQL translator generated from
# `common/slpostingMT.scb`.


def _move_to_ws_file_key(log: LoggingData, text: str) -> None:
    """``move <x> to WS-File-Key`` for the ``pic x(64)`` log field.

    The field is a diagnostic that only ``fhlogger`` reads; it reaches no table, so no
    scenario diff depends on it.
    """
    width = len(log.ws_file_key)
    log.ws_file_key = text[:width].ljust(width)


def _move_to_log_where(text: str) -> str:
    """``move WS-Where (1:J) to WS-Log-Where`` for the ``pic x(231)`` field.

    Returns:
        The value to store, truncated and space-padded to the declared width.
    """
    width = 231
    return text[:width].ljust(width)


def _fetch_record_into_host_variables(row: Mapping[str, object]) -> HostVariables:
    r"""``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT <ten host variables>``
    [common/slpostingMT.cbl:L503-L517].

    The expansion of ``/MYSQL FETCH\ TABLE=PSIRSPOST-REC``
    [common/slpostingMT.scb:L467-L469] names the ten host variables POSITIONALLY, in the
    order ``HV-IRS-POST-KEY`` through ``HV-IRS-VAT-AMOUNT``
    [common/slpostingMT.cbl:L505-L514] - which is column ordinal order, so the C routine
    fills variable *n* from column *n*.

    Args:
        row: one record of the stored result, keyed by column name.

    Returns:
        The ten host variables, filled.

    Raises:
        KeyError: if the row is missing a column.
    """
    hv = HostVariables.initialize()
    for binding in COLUMNS:
        value = row[binding.column]
        current = getattr(hv, binding.host_variable_attribute)
        if isinstance(current, str):
            width = len(current)
            text = "" if value is None else str(value)
            setattr(hv, binding.host_variable_attribute, text[:width].ljust(width))
        elif isinstance(current, Decimal):
            # `PIC S9(07)V9(02) COMP`.
            setattr(
                hv,
                binding.host_variable_attribute,
                Decimal(0) if value is None else Decimal(str(value)),
            )
        else:
            setattr(
                hv,
                binding.host_variable_attribute,
                0 if value is None else int(value),
            )
    return hv


def _clear_sql_fields(log: LoggingData) -> None:
    """``move spaces to ... SQL-Msg SQL-Err`` [common/slpostingMT.cbl:L330-L335].

    Note that ``SQL-Err`` receives SPACES here and ZERO - so ``"00000"`` - in
    ``ba070-Process-Write`` [common/slpostingMT.cbl:L752]. Two different clearings of
    the same ``pic x(5)`` field [copybooks/wsfnctn.cob:L49], preserved at each site.
    """
    log.sql_msg = " " * SQL_MSG_WIDTH
    log.sql_err = " " * SQL_ERR_WIDTH


def _record_driver_failure(error: BaseException, *, paragraph: int) -> None:
    """Report one driver failure - once, at ERROR, with typed fields only.

    The bridge's response to a failed statement is to call ``MySQL_error`` and store
    the server's text [common/slpostingMT.cbl:L758-L760]. NEITHER THAT TEXT NOR THE
    STATEMENT REACHES THIS RECORD. The text is built from material that can include
    the account, the host and key values from the data, and can carry a carriage
    return that forges a second record; the statement is worse, because for this
    table it names the IRS posting row and its amount (CWE-532, CWE-117). Redaction
    was applied to both and removed nothing that mattered: its rules recognise
    connection-message shapes, not a posted figure. What is reported instead is the
    driver's error number, its SQLSTATE and the stable category the two imply - which
    is identical for every occurrence of the same fault and therefore alertable.

    Nothing branches on the result: the status pair each caller reports is the one
    the frozen source dictates, chosen by the exception being caught at all and never
    by what it said.
    """
    log_handler_failure(
        _LOG,
        program=HANDLER_NAME + "/" + BRIDGE_NAME,
        paragraph="ws-No-Paragraph %d" % paragraph,
        fs_reply=int(FsReply.ERROR),
        we_error=int(WeError.RDB_INIT_ERROR),
        sql_err=str(getattr(error, "errno", "") or ""),
        sql_state=str(getattr(error, "sqlstate", "") or ""),
        detail="the statement failed at the driver",
    )


def _driver_error_fields(error: BaseException) -> tuple[str, str, str]:
    """The three values ``Mysql-1100-Db-Error`` reads out of a failed statement.

    ``call "MySQL_errno"`` [copybooks/mysql-procedures.cpy:L97], ``call "MySQL_error"``
    [:L107] and ``call "MySQL_sqlstate"`` [:L122]. Read by ``getattr`` rather than by
    catching a driver-specific class, which is the same choice ``dal/cursor_state.py``
    makes.

    Returns:
        ``(errno as text, message, SQLSTATE)``. Each is the empty string when the
            exception does not carry it, which is what a non-server failure looks like.
    """
    errno = getattr(error, "errno", None)
    message = getattr(error, "msg", None)
    sql_state = getattr(error, "sqlstate", None)
    return (
        str(errno) if isinstance(errno, int) and errno > 0 else "",
        str(message) if message else str(error),
        str(sql_state) if sql_state else "",
    )


def bb000_hv_load(irs_posting: WsIrsPostingRecord) -> HostVariables:
    """``bb000-HV-Load Section.`` [common/slpostingMT.cbl:L992].

    THREE WAYS THIS BRIDGE IS BETTER BEHAVED THAN ITS SIBLINGS, stated here so that
    nobody generalises from it.

    Args:
        irs_posting: the caller's ``WS-IRS-Posting-Record``. Read, never written.

    Returns:
        The loaded ``TD-PSIRSPOST-REC``.
    """
    hv = HostVariables.initialize()
    hv.hv_irs_post_key = group_move_to_binary(
        cobol_group_image(irs_posting.ws_irs_post_key)
    )
    hv.hv_irs_post_code = irs_posting.ws_irs_post_code
    hv.hv_irs_post_dat = irs_posting.ws_irs_post_date
    hv.hv_irs_post_dr = irs_posting.ws_irs_post_dr
    hv.hv_irs_post_cr = irs_posting.ws_irs_post_cr
    # `sign leading` zoned display [copybooks/wspost-irs.cob:L21] into binary
    # [common/slpostingMT.cbl:L271]. Both scales are two, so the value crosses HERE
    # unchanged, sign included.
    hv.hv_irs_post_amount = irs_posting.ws_irs_post_amount
    hv.hv_irs_post_legend = irs_posting.ws_irs_post_legend
    hv.hv_irs_vat_ac_def = irs_posting.ws_irs_vat_ac_def
    hv.hv_irs_post_vat_side = irs_posting.ws_irs_post_vat_side
    hv.hv_irs_vat_amount = irs_posting.ws_irs_vat_amount
    return hv


def bb100_unload_hvs(hv: HostVariables, irs_posting: WsIrsPostingRecord) -> None:
    """``bb100-UnloadHVs Section.`` [common/slpostingMT.cbl:L1018].

    ``initialize WS-IRS-Posting-Record`` [:L1027] - the PLAIN spelling. The ``with
    filler`` variant appears exactly once in the bridge, in ``ba041-Reread``'s zero-rows
    branch [:L534], and the two are NOT normalised to each other (N-INITIALIZE).

    Args:
        hv: the host-variable group a fetch has populated.
        irs_posting: the caller's record. MUTATED IN PLACE, because the COBOL writes
            straight into the linkage item.
    """
    irs_posting.ws_irs_post_key = WsIrsPostKey()
    irs_posting.ws_irs_post_code = " " * 2
    irs_posting.ws_irs_post_date = " " * 8
    irs_posting.ws_irs_post_dr = 0
    irs_posting.ws_irs_post_cr = 0
    irs_posting.ws_irs_post_amount = Decimal("0.00")
    irs_posting.ws_irs_post_legend = " " * 32
    irs_posting.ws_irs_vat_ac_def = 0
    irs_posting.ws_irs_post_vat_side = " " * 2
    irs_posting.ws_irs_vat_amount = Decimal("0.00")
    image = binary_move_to_group(hv.hv_irs_post_key)
    irs_posting.ws_irs_post_key = WsIrsPostKey(
        ws_irs_batch=numeric_display_value(image[:_KEY_SUBFIELD_LENGTH]),
        ws_irs_post_number=numeric_display_value(image[_KEY_SUBFIELD_LENGTH:]),
    )
    irs_posting.ws_irs_post_code = hv.hv_irs_post_code
    irs_posting.ws_irs_post_date = hv.hv_irs_post_dat
    irs_posting.ws_irs_post_dr = hv.hv_irs_post_dr
    irs_posting.ws_irs_post_cr = hv.hv_irs_post_cr
    irs_posting.ws_irs_post_amount = hv.hv_irs_post_amount
    irs_posting.ws_irs_post_legend = hv.hv_irs_post_legend
    irs_posting.ws_irs_vat_ac_def = hv.hv_irs_vat_ac_def
    irs_posting.ws_irs_post_vat_side = hv.hv_irs_post_vat_side
    irs_posting.ws_irs_vat_amount = hv.hv_irs_vat_amount


def _insert_statement(hv: HostVariables) -> tuple[str, tuple[str, ...]]:
    """Build the ``INSERT`` the translator generated, as text plus bound values.

    So the shape is MySQL's ``INSERT ... SET`` extension, all ten columns are named, the
    values are rendered to TEXT and quoted, and the whole thing ends in a semicolon.

    Args:
        hv: the loaded host-variable group.

    Returns:
        ``(statement, parameters)`` with one ``%s`` placeholder per column, in column
            ordinal order.
    """
    assignments: list[str] = []
    parameters: list[str] = []
    for binding in COLUMNS:
        assignments.append(f"{quote_identifier(binding.column)}=%s")
        parameters.append(
            render_column(binding, getattr(hv, binding.host_variable_attribute))
        )
    statement = (
        f"INSERT INTO {quote_identifier(TABLE_NAME)} SET "
        + ", ".join(assignments)
        + ";"
    )
    return (statement, tuple(parameters))


def bb200_insert(
    connection: Any,
    hv: HostVariables,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``bb200-Insert Section.`` [common/slpostingMT.cbl:L1043].

    :func:`~acas_posting.dal.status.mysql_1100_db_error` owns ``Mysql-1100-Db-Error``
    including its duplicate-key shortcut, which is where N-DUPKEY lives: a duplicate
    insert leaves ``We-Error`` at zero and ``SQL-State`` at spaces because the branch
    transfers out before either is set [copybooks/mysql-procedures.cpy:L99-L105].

    Args:
        connection: the live connection standing in for ``Ws-Mysql-Cid``.
        hv: the loaded host-variable group.
        file_access: the caller's block. ``WS-Count-Rows`` and, on failure, the four
            status fields are written into it.
        dal_common: the testing switches.
    """
    log = file_access.logging_data
    statement, parameters = _insert_statement(hv)
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = cursor.rowcount
    except Exception as error:  # any driver error takes this path - see below
        # `if Return-Code not = zero / perform Mysql-1100-Db-Error Thru
        #  Mysql-1190-Exit` [copybooks/mysql-procedures.cpy:L166-L177]. The bridge
        # branches on the query's return code alone and never on which error it was,
        # so catching `Exception` is the faithful width.
        _record_driver_failure(error, paragraph=_BRIDGE_PARA_INSERT)
        errno, message, sql_state = _driver_error_fields(error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            we_error=file_access.we_error,
        )
        file_access.fs_reply = int(status.fs_reply)
        file_access.we_error = int(status.we_error)
        log.sql_err = status.sql_err
        log.sql_msg = status.sql_msg
        log.sql_state = status.sql_state
        # `call "MySQL_affected_rows" using WS-Mysql-Count-Rows.` [:L178] - reached on
        # the failure path too, because it sits AFTER the `end-if`.
        log.ws_count_rows = 0
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
        return
    log.ws_count_rows = affected if affected > 0 else 0


def ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``ba-ACAS-DAL-Process section.`` [common/slpostingMT.cbl:L314].

    Control then FALLS THROUGH into ``ba010-Initialise`` - there is no ``go to`` and no
    ``perform``. Reproduced as a direct call.
    """
    ba010_initialise(file_access, dal_common, irs_posting)


def ba010_initialise(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``ba010-Initialise.`` [common/slpostingMT.cbl:L325].

    [common/slpostingMT.cbl:L327-L328]. So ``FS-Reply`` and ``We-Error`` carry into the
    bridge from whatever the caller last left there, and only the verbs that set them
    explicitly - write [:L750], delete-all's else-branch [:L910], bad-function
    [:L962-L963] - overwrite them.
    """
    log = file_access.logging_data
    # [common/slpostingMT.cbl:L327-L328] `move zero to We-Error Fs-Reply` IS COMMENTED
    # OUT. Deliberately not reproduced - see N-BRIDGENOCLEAR above. `move spaces to WS-
    # MYSQL-Error-Message WS-MYSQL-Error-Number WS-Log-Where WS-File-Key SQL-Msg SQL-
    # Err.` [common/slpostingMT.cbl:L330-L335].
    log.ws_log_where = " " * len(log.ws_log_where)
    log.ws_file_key = " " * len(log.ws_file_key)
    _clear_sql_fields(log)
    function = file_access.file_function
    if function == FileFunction.OPEN:
        ba020_process_open(file_access, dal_common)
        return
    if function == FileFunction.CLOSE:
        ba030_process_close(file_access, dal_common)
        return
    if function == FileFunction.READ_NEXT:
        ba040_process_read_next(file_access, dal_common, irs_posting)
        return
    if function == FileFunction.WRITE:
        ba070_process_write(file_access, dal_common, irs_posting)
        return
    if function == FileFunction.DELETE_ALL:
        ba085_process_delete_all(file_access, dal_common, irs_posting)
        return
    # `when 4 -> ba050 / when 7 -> ba090 / when 8 -> ba080 / when 9 -> ba060`
    # [common/slpostingMT.cbl:L352-L363].
    if function in REJECTED_FUNCTIONS:
        raise BridgeVerbUnreachable(
            f"{BRIDGE_NAME} was called with File-Function {int(function)}, which "
            f"{HANDLER_NAME} refuses at its own entry "
            f"[common/acas008.cbl:L299-L307]. The bridge paragraph for it is "
            f"unreachable in the compiled system and is deliberately not implemented."
        )
    ba100_bad_function(file_access, dal_common)


def ba020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba020-Process-Open.`` [common/slpostingMT.cbl:L368].

    Each is ``delimited by space`` with an appended ``X"00"``, because the C library
    wants NUL-terminated strings;
    :func:`~acas_posting.dal.connection.cobol_string_delimited_by_space` reproduces the
    truncation-at-first-space rule and the terminator is the C boundary's business, not
    this layer's.
    """
    ws = working_storage()
    log = file_access.logging_data
    rdb = file_access.rdb_data
    # The six `string ... delimited by space` moves [common/slpostingMT.cbl:L373-L396].
    for _field_name in ("db_schema", "db_host", "db_uname", "db_upass", "db_port",
                        "db_socket"):
        cobol_string_delimited_by_space(getattr(rdb, _field_name))
    log.ws_no_paragraph = _BRIDGE_PARA_OPEN
    system = ws.system_record
    if system is None:
        # The handler always loads the credentials before the first bridge call
        # [common/acas008.cbl:L554-L563], and `dispatch` reproduces that ordering, so
        # the compiled system cannot reach an open with no system record. Reported the
        # way the copybook reports a failed connect - `(99, 911)`
        # [copybooks/mysql-procedures.cpy:L127-L128] - rather than by raising, because
        # a status is what the caller is equipped to read.
        log_handler_failure(
            _LOG,
            program=HANDLER_NAME + "/" + BRIDGE_NAME,
            paragraph="ba020-Process-Open",
            locator="[common/acas008.cbl:L554-L563]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="open requested before the credentials were loaded",
        )
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.RDB_INIT_ERROR)
        ba999_end(file_access, dal_common)
        return
    outcome: OpenOutcome = mysql_1090_exit(
        mysql_1000_open(
            system,
            ws_no_paragraph=_BRIDGE_PARA_OPEN,
            we_error=file_access.we_error,
            transport=ws.transport,
            allow_frozen_placeholder_credentials=(
                ws.allow_frozen_placeholder_credentials
            ),
        )
    )
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    log.ws_no_paragraph = outcome.ws_no_paragraph
    log.sql_err = outcome.sql_err
    log.sql_msg = outcome.sql_msg
    log.sql_state = outcome.sql_state
    if file_access.fs_reply != int(FsReply.SUCCESS):
        ba999_end(file_access, dal_common)
        return
    ws.connection = outcome.connection
    _move_to_ws_file_key(log, "OPEN SLIRSPOSTING")
    ws.cursor_states.reset(TABLE_NAME)
    ba999_end(file_access, dal_common)


def ba030_process_close(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba030-Process-Close.`` [common/slpostingMT.cbl:L412].

    N-CLOSESILENT CLOSE WRITES NO STATUS AT ALL. There is no ``move zero to FS-Reply``,
    no ``move zero to WE-Error``, and ``MYSQL-1980-CLOSE`` sets neither.
    """
    ws = working_storage()
    log = file_access.logging_data
    if ws.cursor_states.state_for(TABLE_NAME, CursorSlot.PRIMARY).cursor_active():
        ba998_free(file_access)
    log.ws_no_paragraph = _BRIDGE_PARA_CLOSE
    _move_to_ws_file_key(log, "CLOSE SLIRSPOSTING")
    mysql_1980_close(ws.connection)
    mysql_1999_exit()
    ws.connection = None
    ba999_end(file_access, dal_common)


def ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``ba040-Process-Read-Next.`` [common/slpostingMT.cbl:L427] and ``ba041-Reread.``
    [:L492].

    The paragraph builds a positioning ``SELECT`` whose ``WHERE`` is the one predicate
    [common/slpostingMT.cbl:L436-L446], stores the result, and then ``ba041-Reread``
    fetches ONE row per call [:L492-L551]. On the first call it selects and fetches.
    """
    ws = working_storage()
    log = file_access.logging_data
    log.ws_no_paragraph = _BRIDGE_PARA_SELECT
    if ws.connection is None:
        # Unreachable through `acas008`, which opens before it reads. Reported as the
        # copybook reports a dead connection rather than raised, for the same reason
        # as in `ba020_process_open`.
        log_handler_failure(
            _LOG,
            program=HANDLER_NAME + "/" + BRIDGE_NAME,
            paragraph="ba040-Process-Read-Next",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="read-next requested with no open connection",
        )
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.RDB_INIT_ERROR)
        ba999_end(file_access, dal_common)
        return
    # A RAW cursor: the delegate issues the `execute` and stores the result itself.
    with contextlib.closing(acquire_cursor(ws.connection)) as cursor:  # type: ignore[arg-type]
        outcome: CursorOutcome = _cursor_read_next(
            cursor,
            TABLE_NAME,
            slot=CursorSlot.PRIMARY,
            states=ws.cursor_states,
            file_access=file_access,
        )
    # `perform bb100-UnloadHVs.` [common/slpostingMT.cbl:L546] and [:L641] - performed
    # ONLY on the delivering path.
    if outcome.row is not None:
        ws.host_variables = _fetch_record_into_host_variables(outcome.row)
        bb100_unload_hvs(ws.host_variables, irs_posting)
    ba999_end(file_access, dal_common)


def ba070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``ba070-Process-Write.`` [common/slpostingMT.cbl:L747].

    ``move zero to SQL-Err`` [:L752] puts ``"00000"`` into the ``pic x(5)`` field, where
    ``ba010-Initialise`` put SPACES [:L335]. Both are reproduced at their own site.
    """
    ws = working_storage()
    log = file_access.logging_data
    hv = bb000_hv_load(irs_posting)
    ws.host_variables = hv
    _move_to_ws_file_key(log, str(hv.hv_irs_post_key))
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    log.sql_msg = " " * SQL_MSG_WIDTH
    log.sql_err = "0" * SQL_ERR_WIDTH
    log.ws_no_paragraph = _BRIDGE_PARA_INSERT
    if ws.connection is None:
        log_handler_failure(
            _LOG,
            program=HANDLER_NAME + "/" + BRIDGE_NAME,
            paragraph="ba070-Process-Write",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="write requested with no open connection",
        )
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.RDB_INIT_ERROR)
        ba999_end(file_access, dal_common)
        return
    bb200_insert(ws.connection, hv, file_access, dal_common)
    if log.ws_count_rows != 1:
        # `call "MySQL_errno" using WS-MYSQL-Error-Number` [:L756] then `if WS-MYSQL-
        # Error-Number not = "0 "` [:L757].
        errno_text = log.sql_err.strip()
        if errno_text and errno_text.strip("0"):
            # `move WS-MYSQL-Error-Number to SQL-Err` [:L759] and `move WS-MYSQL-Error-
            # Message to SQL-Msg` [:L760] re-store what `Mysql-1100-Db-Error` already
            # stored; both are already in place.
            if log.sql_err[:4] in DUPLICATE_KEY_ERRNOS:
                file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
            else:
                file_access.fs_reply = int(FsReply.ERROR)
    ba999_end(file_access, dal_common)


def ba085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``ba085-Process-Delete-ALL.`` [common/slpostingMT.cbl:L827].

    FOUR ANOMALIES LIVE IN THOSE FORTY LINES, and all four are reproduced.

    THE PREDICATE IS BOUNDED, NOT A TRUNCATE. The sentinel this paragraph moves in
    renders as the ten-character key text ``9999999999``, and the ``WHERE`` clause is a
    STRICT ``<`` against it - so a row AT the bound survives the bound built from it,
    and a row above it survives too. Because a bridge-written key is a group-move image
    near 4.7e17 [common/slpostingMT.cbl:L1001], MEASURED: this delete removes nothing
    the bridge itself wrote. Registered as the key-bound note under A-NEW-8 in
    ``docs/migration/anomaly-log.md``, together with ``N-DELALLMUTATES`` below.
    """
    ws = working_storage()
    log = file_access.logging_data
    # `add 1 to WS-IRS-Post-Number` is COMMENTED OUT at [common/slpostingMT.cbl:L849]
    # and is deliberately not reproduced. `move 99999 to WS-IRS-Batch WS-IRS-Post-
    # Number.` [common/slpostingMT.cbl:L850-L851] - MUTATES THE CALLER'S RECORD
    # (N-DELALLMUTATES).
    irs_posting.ws_irs_post_key = WsIrsPostKey(
        ws_irs_batch=99999, ws_irs_post_number=99999
    )
    # `set KOR-x1 to File-Key-No / move KOR-offset (KOR-x1) to K / move KOR-length
    # (KOR-x1) to L` [common/slpostingMT.cbl:L853-L855].
    _key = _key_of_reference(TABLE_NAME, max(log.file_key_no, 1))
    _k, _length = _key.kor_offset, _key.kor_length
    del _k, _length
    bound_key = cobol_group_image(irs_posting.ws_irs_post_key)
    where = f"{quote_identifier(_key.column_name)}<%s"
    _move_to_ws_file_key(log, f"Deleting back from {bound_key}")
    log.ws_log_where = _move_to_log_where(f"{quote_identifier(_key.column_name)}<"
                                         f'"{bound_key}"')
    # `if Testing-2 display Display-Message-1 with erase eos`
    # [common/slpostingMT.cbl:L876-L878] - screen output with no database effect, so a
    # log record per Agent Action Plan section 0.3.4.
    if _testing_2(dal_common):
        #  THE CLAUSE IS NOT LOGGED. `WS-Where` is the composed SQL `WHERE` clause,
        #  which for this table names the IRS posting key (CWE-532). The frozen
        #  `display` writes it to a curses screen; a log record persists it. The
        #  `Testing-2` guard is kept so that the paragraph and its switch still exist
        #  for traceability - it simply has nothing left to write, and returns exactly
        #  as it did before.
        pass
    # `move 13 to ws-No-Paragraph.` [common/slpostingMT.cbl:L879]
    log.ws_no_paragraph = _BRIDGE_PARA_DELETE
    if ws.connection is None:
        log_handler_failure(
            _LOG,
            program=HANDLER_NAME + "/" + BRIDGE_NAME,
            paragraph="ba085-Process-Delete-All",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="delete-all requested with no open connection",
        )
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.RDB_INIT_ERROR)
        ba999_exit(file_access, dal_common)
        return
    # [common/slpostingMT.cbl:L885-L891]. Note there is NO trailing semicolon here,
    # where the generated INSERT has one [:L1173] - a generator inconsistency,
    # preserved.
    statement = f"DELETE FROM {quote_identifier(TABLE_NAME)} WHERE {where}"
    try:
        with execute_statement(connection=ws.connection, statement=statement,
                               parameters=(bound_key,)) as cursor:
            affected = cursor.rowcount
    except Exception as error:  # any driver error takes this path
        _record_driver_failure(error, paragraph=_BRIDGE_PARA_DELETE)
        errno, message, sql_state = _driver_error_fields(error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            we_error=file_access.we_error,
        )
        file_access.fs_reply = int(status.fs_reply)
        file_access.we_error = int(status.we_error)
        log.sql_err = status.sql_err
        log.sql_msg = status.sql_msg
        log.sql_state = status.sql_state
        log.ws_count_rows = 0
        affected = 0
    else:
        log.ws_count_rows = affected if affected > 0 else 0
    if log.ws_count_rows <= 0:
        errno_text = log.sql_err.strip()
        if errno_text and errno_text.strip("0"):
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
        ba999_exit(file_access, dal_common)
        return
    log.sql_msg = " " * SQL_MSG_WIDTH
    log.sql_err = "0" * SQL_ERR_WIDTH
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common)
    ba999_exit(file_access, dal_common)


def ba100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba100-Bad-Function.`` [common/slpostingMT.cbl:L958].

    CODES. The bridge uses ``990`` [:L962]; the handler's own ``aa100-Bad-Function``
    uses ``999`` [common/acas008.cbl:L491]. Same condition, two codes, and which one the
    caller sees depends on which program noticed.
    """
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    file_access.fs_reply = int(FsReply.ERROR)
    ba999_end(file_access, dal_common)


def ba998_free(file_access: FileAccess) -> None:
    """``ba998-Free.`` [common/slpostingMT.cbl:L970].

    IT HAS NO TERMINATING TRANSFER, so it FALLS THROUGH into ``ba999-End`` [:L982]
    whenever it is reached by a ``go to`` rather than a ``perform``.
    """
    file_access.logging_data.ws_no_paragraph = _BRIDGE_PARA_FREE
    working_storage().cursor_states.reset(TABLE_NAME)


def ba999_end(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """``ba999-End.`` [common/slpostingMT.cbl:L982].

    then FALLS THROUGH into ``ba999-Exit`` [:L989], reproduced as a direct call. The
    maintainer's heading is a question to himself: "Any Clean ups before quiting move
    data record ?????
    """
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common)
    ba999_exit(file_access, dal_common)


def ba999_exit(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """``ba999-Exit.`` [common/slpostingMT.cbl:L989].

    ``exit program.`` [:L990] - return to the ``CALL``ing handler with the linkage items
    as they now stand. Nothing is written and nothing is cleaned up.
    """
    del file_access, dal_common


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` in BOTH programs: [common/acas008.cbl:L595] and
    [common/slpostingMT.cbl:L1329].

    One function for both, because the two paragraphs are textually identical - a single
    ``call "fhlogger" using File-Access ACAS-DAL-Common-data``
    [common/acas008.cbl:L598-L599], [common/slpostingMT.cbl:L1332-L1333] - and
    duplicating it would suggest a difference that is not there.
    """
    if not _testing_1(dal_common):
        # Every call site tests `Testing-1` first, so this cannot normally be false.
        return
    log = file_access.logging_data
    #  THE ONE ADAPTER, carrying two of the frozen record's fields:
    #  `WS-File-Key` is the IRS posting key and `WS-Log-Where` is the `WHERE` clause
    #  built around it. `sanitise_for_log` escaped and bounded both and removed
    #  nothing (CWE-532).
    log_file_handler_record(
        _LOG,
        program=HANDLER_NAME,
        paragraph="Ca-Process-Logs",
        log_system=log.ws_log_system,
        log_file_no=log.ws_log_file_no,
        no_paragraph=log.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=log.sql_err,
        sql_state=log.sql_state,
        dal_common=dal_common,
    )
    #  `Log-File-Rec-Written` [copybooks/Test-Data-Flags.cob:L18] IS NOW ADVANCED BY
    #  THE ADAPTER ABOVE, not assigned 1 here. Assigning 1 was wrong twice over: the
    #  field is a COUNT of records written, so a second record must leave 2, and the
    #  field is `pic 9(6)`, so the count wraps at a million rather than pinning. The
    #  handler never reads it, but the caller keeps the block and can, so a pinned 1
    #  made the shared block diverge from what the frozen run would hold. The adapter
    #  applies `(n + 1) % 1_000_000` exactly once per emitted record.


def ca_exit() -> None:
    """``ca-Exit.`` [common/acas008.cbl:L601] and ``ca-Exit. exit.``
    [common/slpostingMT.cbl:L1335].
    """


def slposting_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``call "slpostingMT" using File-Access ACAS-DAL-Common-data WS-IRS-Posting-Record``
    [common/acas008.cbl:L583-L587].

    THE BRIDGE'S ENTRY POINT, in the bridge's THREE-parameter order - ``File-Access``
    FIRST, the record LAST - which is not the handler's five-parameter order and is not
    a subset of it.

    Args:
        file_access: the ``File-Access`` block. Read for ``File-Function``, ``Access-
            Type`` and ``RDB-Data``; written with the status, the paragraph number, the
            log key and the row count.
        dal_common: the two testing switches.
        irs_posting: ``WS-IRS-Posting-Record``. Read on a write, written on a successful
            read, and MUTATED on a delete-all (N-DELALLMUTATES).
    """
    ba_acas_dal_process(file_access, dal_common, irs_posting)


# THE HANDLER - acas008 Everything from here to `dispatch` reproduces
# `common/acas008.cbl`. The handler issues NO SQL.


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas008.cbl:L516].

    ``aa010-main`` set 15 [:L294] describing it as "Cobol/RDB, File/Table within sub
    System"; this paragraph replaces it with 25 the moment the RDB path is taken.
    """
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    system: SystemRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas008.cbl:L524].

    THE GATE IS THIS HANDLER'S OWN ``77 A`` [common/acas008.cbl:L253], NOT a shared
    flag.

    Args:
        system: the ``SYSTEM-REC`` row. RECORDED ON EVERY CALL, because it is a LINKAGE
            parameter the compiled handler always has [:L278].
        file_access: the caller's block. ``RDB-Data`` is populated, and on the
            unreachable 901 path the status pair is written.
        dal_common: the testing switches.

    Returns:
        ``True`` when control should continue into ``ba015-Test-Ends``; ``False`` when
            the 901 path took ``go to ba-rdbms-exit``.
    """
    ws = working_storage()
    log = file_access.logging_data
    # `System-Record` is a LINKAGE parameter [common/acas008.cbl:L278], so the compiled
    # handler has it in hand on EVERY call, not just the first.
    ws.system_record = system
    # `if A = zero` [common/acas008.cbl:L526] - "so it is being called first time". THIS
    # HANDLER'S OWN `77 A` [:L253], never the shared credential cache.
    if ws.a != 0:
        return True
    # `move function Length (WS-IRS-Posting-Record) to A`
    # [common/acas008.cbl:L527-L529]. This assignment is ALSO what closes the gate,
    # because the frozen source stores the length in the sentinel itself.
    a = WS_RECORD_LENGTH
    ws.a = a
    b = FD_RECORD_LENGTH
    ws.b = b
    if a < b:
        file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
        file_access.fs_reply = int(FsReply.ERROR)
    # `if WE-Error = 901` [common/acas008.cbl:L537].
    if file_access.we_error == int(WeError.RECORD_SIZE_MISMATCH):
        # `string IR902 A " < " "IRS-Posting-Rec = " B into Display-Blk` then two
        # `display`s [common/acas008.cbl:L538-L546] - presentation, so a log record.
        _LOG.error(
            "%s: IR902 Program Error: Temp rec = %d < IRS-Posting-Rec = %d "
            "[common/acas008.cbl:L533-L543]",
            HANDLER_NAME,
            a,
            b,
        )
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
        # `accept Accept-Reply at 2433` [common/acas008.cbl:L550] - a pause whose only
        # effect is to block a terminal, DROPPED per Agent Action Plan section 0.3.4.
        ba_rdbms_exit()
        return False
    # `move RDBMS-DB-Name to DB-Schema` ... `move RDBMS-Socket to DB-Socket`
    # [common/acas008.cbl:L558-L563], in the handler's order: Schema, UName, UPass,
    # Port, Host, Socket.
    file_access.rdb_data = load_rdb_data_once(system)
    del log
    return True


def ba015_test_ends(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``ba015-Test-Ends.`` [common/acas008.cbl:L566].

    The maintainer's own heading says why the ``if`` is here [:L568-L569]: "First check
    if there is an open output and if so we need to force a DELETE-ALL call to the
    DAL.".
    """
    if (
        file_access.file_function == FileFunction.OPEN
        and file_access.access_type == AccessType.OUTPUT
    ):
        file_access.file_function = int(COERCED_FUNCTION)
    slposting_mt(file_access, dal_common, irs_posting)
    ba_rdbms_exit()


def ba_process_rdbms(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    irs_posting: WsIrsPostingRecord,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas008.cbl:L508].

    ba010-Test-WS-Rec-Size [:L516] -> log file number 15 becomes 25 ba012-Test-WS-Rec-
    Size-2 [:L524] -> length guard + credential load ba015-Test-Ends [:L566] -> coercion
    2 + the INLINE bridge call ba-rdbms-exit [:L591] -> exit section.
    """
    ba010_test_ws_rec_size(file_access)
    if not ba012_test_ws_rec_size_2(system, file_access, dal_common):
        return
    ba015_test_ends(file_access, dal_common, irs_posting)


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit.`` [common/acas008.cbl:L591].

    ``exit section.`` [:L592] - leave ``ba-Process-RDBMS`` and return to whichever
    ``perform`` entered it. No effect of its own.
    """


def aa020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa020-Process-Open.`` [common/acas008.cbl:L380] - THE COBOL FLAT-FILE LEG.

    Reached only when ``FS-Cobol-Files-Used`` is true, because the RDB path leaves
    ``aa010-main`` at [:L318] or [:L326] and never reaches the dispatch at [:L354].
    """
    log = file_access.logging_data
    _move_to_ws_file_key(log, "")
    log.ws_no_paragraph = _HANDLER_PARA_OPEN
    if file_access.access_type == AccessType.EXTEND:
        # `move 997 to WE-Error` / `move 99 to FS-Reply` / `go to aa999-Main-Exit`
        # [common/acas008.cbl:L406-L408] - Class 3.
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(file_access, dal_common)
        return
    raise CobolFlatFileNotMigrated(
        f"{HANDLER_NAME} aa020-Process-Open [common/acas008.cbl:L380] reached the "
        f"Cobol flat-file leg with Access-Type {file_access.access_type}. "
        f"IRS-Post-File is an indexed store the migration does not have; the RDB path "
        f"leaves aa010-main at [common/acas008.cbl:L326] and never arrives here."
    )


def aa030_process_close(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa030-Process-Close.`` [common/acas008.cbl:L422] - THE COBOL FLAT-FILE LEG.

    THREE ANOMALIES SIT IN THOSE ELEVEN LINES, all beyond the ``close`` and therefore
    named here rather than executed - see OMISSION O-2.
    """
    log = file_access.logging_data
    log.ws_no_paragraph = _HANDLER_PARA_CLOSE
    _move_to_ws_file_key(log, "")
    del dal_common
    raise CobolFlatFileNotMigrated(
        f"{HANDLER_NAME} aa030-Process-Close [common/acas008.cbl:L422] reached the "
        f"Cobol flat-file leg. IRS-Post-File is an indexed store the migration does "
        f"not have; see this function's docstring for the eight statements that follow "
        f"the close and the three anomalies among them."
    )


def aa040_process_read_next(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas008.cbl:L435] - THE COBOL FLAT-FILE LEG.

    N-STOPRUN ``stop "Cobol File EOF"`` [:L448] HALTS THE RUN. Not a status, not a
    display - a ``STOP`` with a literal, which suspends the program and waits at the
    console. The maintainer knew it should be unreachable, twice.
    """
    log = file_access.logging_data
    ws = working_storage()
    log.ws_no_paragraph = _HANDLER_PARA_READ_NEXT
    if ws.cobol_file_eof():
        file_access.fs_reply = int(FsReply.END_OF_FILE)
        file_access.we_error = int(FsReply.END_OF_FILE)
        _clear_sql_fields(log)
        # `stop "Cobol File EOF"` [common/acas008.cbl:L448] - N-STOPRUN.
        raise CobolFlatFileNotMigrated(
            f"{HANDLER_NAME} aa040-Process-Read-Next reached "
            f"`stop \"Cobol File EOF\"` [common/acas008.cbl:L448], which the "
            f"maintainer marks 'should NOT occur' [:L441]. The Cobol flat-file leg has "
            f"no store in the migration, so Cobol-File-Status can only have been set "
            f"by a caller reaching into working storage."
        )
    del dal_common
    raise CobolFlatFileNotMigrated(
        f"{HANDLER_NAME} aa040-Process-Read-Next [common/acas008.cbl:L435] reached the "
        f"Cobol flat-file leg. IRS-Post-File is an indexed store the migration does "
        f"not have; the RDB read-next is `fn-read-next` through the bridge - see "
        f"ba040_process_read_next."
    )


def aa070_process_write(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa070-Process-Write.`` [common/acas008.cbl:L468] - THE COBOL FLAT-FILE LEG."""
    log = file_access.logging_data
    ws = working_storage()
    log.ws_no_paragraph = _HANDLER_PARA_WRITE
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ws.cobol_file_status = 0
    del dal_common
    raise CobolFlatFileNotMigrated(
        f"{HANDLER_NAME} aa070-Process-Write [common/acas008.cbl:L468] reached the "
        f"Cobol flat-file leg. IRS-Post-File is an indexed store the migration does "
        f"not have; the RDB write is `fn-write` through the bridge - see "
        f"ba070_process_write."
    )


def aa080_process_delete(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa080-Process-Delete.`` [common/acas008.cbl:L477] - UNREACHABLE DEAD CODE.

    and it can never run, for TWO independent reasons.
    """
    log = file_access.logging_data
    ws = working_storage()
    log.ws_no_paragraph = _HANDLER_PARA_DELETE
    # `move WS-IRS-Post-Key to IRS-Post-Key.` [common/acas008.cbl:L479] - no FD record
    # to move into; part of O-2. `move WS-IRS-Post-Key to WS-File-Key.`
    # [common/acas008.cbl:L480].
    _move_to_ws_file_key(log, "")
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ws.cobol_file_status = 0
    del dal_common
    raise CobolFlatFileNotMigrated(
        f"{HANDLER_NAME} aa080-Process-Delete [common/acas008.cbl:L477] is dead code "
        f"in the frozen handler: the entry guard refuses File-Function 8 at "
        f"[common/acas008.cbl:L303] and the dispatch that would reach it is commented "
        f"out at [common/acas008.cbl:L369-L370]. It is reproduced as unreachable "
        f"rather than deleted (anomaly N-DEADDELETE)."
    )


def aa100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa100-Bad-Function.`` [common/acas008.cbl:L489].

    N-BADFUNCCODES the handler reports ``999``
    (:data:`~acas_posting.dal.status.WeError.NOT_USED`) where the bridge reports ``990``
    (``UNKNOWN_UNEXPECTED``) for the same condition [common/slpostingMT.cbl:L962]. Both
    preserved.
    """
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit.`` [common/acas008.cbl:L496].

    then FALLS THROUGH into ``aa-main-exit`` [:L501], reproduced as a direct call.
    """
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common)
    aa_main_exit()


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas008.cbl:L501].

    An EMPTY paragraph - its only content is the maintainer's comment "Now have
    processed cobol flat file, so .." [:L503], a sentence he never finished. It falls
    through into ``aa-Exit`` [:L505].
    """
    aa_exit()


def aa_exit() -> None:
    """``aa-Exit.`` [common/acas008.cbl:L505].

    The paragraph is EMPTY apart from that verb, so this function is empty too; the
    actual return of control is the Python ``return`` at the call site.
    """


def aa010_main(
    system: SystemRecord,
    irs_posting: WsIrsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa010-main.`` [common/acas008.cbl:L289] - THE WHOLE OF THE HANDLER'S LOGIC.

    Reproduced statement for statement in the COBOL's order. The order is the point: the
    guard runs before the coercion, the coercion before the store decision, and the
    store decision before the record-length check.
    """
    log = file_access.logging_data
    # `move 1 to WS-Log-System.` [common/acas008.cbl:L293]. N-LOGSYSTEM.
    log.ws_log_system = int(WS_LOG_SYSTEM)
    log.ws_log_file_no = WS_LOG_FILE_NO_COBOL
    # `REJECTED_FUNCTIONS` is keyed by `FileFunction`, an `IntEnum`, so a plain `File-
    # Function` value keys it directly - which is what the COBOL `evaluate` does with
    # the numeric literals 4, 7, 9 and 8.
    rejected = REJECTED_FUNCTIONS.get(file_access.file_function)
    if rejected is not None:
        fs_reply, we_error, locator = rejected
        file_access.we_error = int(we_error)
        file_access.fs_reply = int(fs_reply)
        #  ONE ERROR. This is the guard behind anomaly ``A-6`` of
        #  [docs/migration/anomaly-log.md] - the handler refuses
        #  read-indexed, rewrite, start and delete unconditionally because its store
        #  is sequential - and `FS-Reply` 99 goes back to the caller, so it is a
        #  failure. Reporting it at DEBUG made a published facade verb that can NEVER
        #  succeed invisible at the level an operator watches.
        log_handler_failure(
            _LOG,
            program=HANDLER_NAME,
            paragraph="aa000-Main-Process entry guard",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="File-Function %d refused: the store is sequential (anomaly A-6)"
            % int(file_access.file_function),
        )
        aa999_main_exit(file_access, dal_common)
        return
    if (
        file_access.file_function == FileFunction.OPEN
        and file_access.access_type == AccessType.OUTPUT
        and not _fs_cobol_files_used(system)
    ):
        # `set fn-delete-all to true` [common/acas008.cbl:L316] - BEFORE the perform, so
        # the bridge sees 6 and is entered exactly ONCE.
        file_access.file_function = int(COERCED_FUNCTION)
        ba_process_rdbms(system, file_access, dal_common, irs_posting)
        # `go to AA-Main-Exit` [common/acas008.cbl:L318] - Class 3, and note it lands at
        # `aa-main-exit` and NOT at `aa999-main-exit`, so the handler's own log is
        # skipped.
        aa_main_exit()
        return
    if not _fs_cobol_files_used(system):
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = (
            system.system_data_block.rdbms_flat_statuses.file_system_used
        )
        ba_process_rdbms(system, file_access, dal_common, irs_posting)
        aa_main_exit()
        return
    if (
        file_access.file_function == FileFunction.DELETE_ALL
        and _fs_cobol_files_used(system)
    ):
        file_access.file_function = int(FileFunction.OPEN)
        file_access.access_type = int(AccessType.OUTPUT)
    ba012_test_ws_rec_size_2(system, file_access, dal_common)
    # `move zero to WE-Error FS-Reply` is COMMENTED OUT at
    # [common/acas008.cbl:L350-L351] and is deliberately not reproduced.
    _clear_sql_fields(log)
    log.sql_state = " " * SQL_STATE_WIDTH
    del file_defs
    function = file_access.file_function
    if function == FileFunction.OPEN:
        aa020_process_open(file_access, dal_common)
        return
    if function == FileFunction.CLOSE:
        aa030_process_close(file_access, dal_common)
        return
    if function == FileFunction.READ_NEXT:
        aa040_process_read_next(file_access, dal_common)
        return
    if function == FileFunction.WRITE:
        aa070_process_write(file_access, dal_common)
        return
    # `when other / go to aa100-Bad-Function` [common/acas008.cbl:L373-L374] - Class 4.
    # The unconditional `go to aa100-Bad-Function` at [:L378] is unreachable after this
    # and is reproduced as unreachable.
    aa100_bad_function(file_access, dal_common)


def aa_process_flat_file(
    system: SystemRecord,
    irs_posting: WsIrsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas008.cbl:L287].

    The handler's only section, and the ``PROCEDURE DIVISION``'s first, so entering the
    program enters it. It contains no statements of its own: control begins at
    ``aa010-main`` [:L289], reproduced as a direct call.
    """
    aa010_main(system, irs_posting, file_access, file_defs, dal_common)


def dispatch(
    system: SystemRecord,
    irs_posting: WsIrsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool | None = None,
) -> None:
    """``call "acas008" using System-Record WS-IRS-Posting-Record File-Access File-Defs
    ACAS-DAL-Common-data`` [common/acas008.cbl:L278-L285].

    REACHED FROM BOTH FACADE CONVENTIONS, which is unique to this entity.
    ``copybooks/Proc-ACAS-FH-Calls.cob`` publishes twelve ``SPL-Posting-*`` verbs
    [:L482-L538] and dispatches through [:L59-L65]; ``Proc-ZZ100-ACAS-IRS-Calls.cob``
    publishes seven ``acas008-*`` verbs [:L130-L163] and calls at [:L34-L43].

    Args:
        system: the ``SYSTEM-REC`` row. Read for ``File-System-Used``
            [copybooks/wssystem.cob:L111-L116] and, on the first call only, for the six
            connection parameters [common/acas008.cbl:L558-L563].
        irs_posting: ``WS-IRS-Posting-Record`` [copybooks/wspost-irs.cob:L13-L25]. Read
            on a write, written on a successful read-next, and MUTATED on a delete-all
            (N-DELALLMUTATES).
        file_access: the ``File-Access`` block [copybooks/wsfnctn.cob:L22-L80]. Carries
            the request in and the status, the log fields and the row count out.
        file_defs: the file and work-file names [copybooks/wsnames.cob]. TAKEN AND NOT
            READ, exactly as the handler takes and does not read it.
        dal_common: the two testing switches [copybooks/Test-Data-Flags.cob].
        transport: how the connection may cross the network. NOT a COBOL parameter -
            in the compiled system the C interface connects to whatever the credentials
            name, with no transport policy at all. ``None`` - the default - defers to
            the ONE policy the deployment installed with
            :func:`acas_posting.dal.connection.set_connection_policy`, so this handler
            declares nothing of its own. Keyword-only, so the five positional
            parameters remain exactly the COBOL's.
        allow_frozen_placeholder_credentials: whether the frozen placeholder
            credentials in ``copybooks/wssystem.cob`` may be used. Also not a COBOL
            parameter, and ``None`` defers to that same policy for the same reason.

    Raises:
        CobolFlatFileNotMigrated: when ``File-System-Used`` selects the Cobol flat-file
            store, which the migration does not have. Never on the RDB path.
        BridgeVerbUnreachable: never from here - the entry guard is why the state cannot
            arise.
    """
    ws = working_storage()
    ws.transport = transport
    ws.allow_frozen_placeholder_credentials = allow_frozen_placeholder_credentials
    aa_process_flat_file(system, irs_posting, file_access, file_defs, dal_common)
