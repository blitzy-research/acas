"""`acas005` and its bridge `nominalMT` - the `GLLEDGER-REC` nominal ledger.

The data-access module for the GL-Nominal entity: it owns all SQL for the nominal
ledger table and publishes only the COBOL verb vocabulary.

Its `READ NEXT` ordering is load-bearing. `gl072` locates the account for each
posting with a SEQUENTIAL read [general/gl072.cbl:L408], guarded at L407, so this
module must walk the table in key order; a different order misposts silently.

The spine it serves, from Agent Action Plan 0.2.1.1::

    entity GL-Nominal -> handler acas005 -> bridge nominalMT
      -> table GLLEDGER-REC  [mysql/ACASDB.sql:L122-L135]   11 columns, PK LEDGER-KEY
      -> copybook copybooks/wsledger.cob
      -> record class WsLedgerRecord in acas_posting/records/gl_ledger.py

It owns no business logic. Every accounting decision belongs to the program
modules; this module moves records between :class:`WsLedgerRecord` and the
frozen table and reports the ``(FS-Reply, We-Error)`` pair the compiled system
would have left in the caller's ``File-Access`` block.

THE HEADLINE RISK is that this is the sequentially-read table: `gl072` locates a
posting's nominal account by walking, not by key, so the ordering contract that
makes it land correctly is stated in full at :func:`read_next`.
"""

from __future__ import annotations

import decimal
import enum
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Final

from acas_posting.dal import cursor_state
from acas_posting.dal.connection import (
    TransportSecurity,
    acquire_cursor,
    cobol_string_delimited_by_space,
    cursor_is_unavailable,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
    transport_category,
    transport_decimal_context,
)
from acas_posting.dal.cursor_state import (
    CursorOutcome,
    CursorSlot,
    CursorStateTable,
    DatabaseCursor,
    KeyOfReference,
    key_of_reference,
)
from acas_posting.dal.status import (
    START_ACCESS_TYPE_RANGE,
    AccessType,
    AcasFileHandlerError,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
)

# DELIBERATE OMISSION, recorded as an omission per rule R-5.
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_ledger import (
    WsLedgerKey,
    WsLedgerKey9,
    WsLedgerNosParts,
    WsLedgerRecord,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "BRIDGE_NAME",
    "BRIDGE_PARAGRAPH_NUMBERS",
    "COLUMN_BINDINGS",
    "COLUMN_BINDINGS_BY_NAME",
    "COLUMN_NAMES",
    "DELETE_STATEMENT",
    "DISPATCH_ORDER",
    "ENTITY_FACADE",
    "FILE_KEY_NO",
    "FILE_KEY_TAGS",
    "FLAT_FILE_STATUSES",
    "HANDLER_NAME",
    "HV_LOAD_ORDER",
    "HV_UNLOAD_ORDER",
    "INSERT_STATEMENT",
    "KEY_GUARDED_FUNCTIONS",
    "KEY_OF_REFERENCE",
    "LEDGER_RECORD_LENGTH",
    "SET_CLAUSE",
    "TABLE_NAME",
    "UPDATE_STATEMENT",
    "WS_FILE_KEY_WIDTH",
    "WS_LEDGER_RECORD_LENGTH",
    "WS_LOG_FILE_NO_COBOL",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "WS_MYSQL_EDIT_WIDTH",
    "BridgeSession",
    "CobolFileAccessNotMigratedError",
    "ColumnBinding",
    "CommandOutcome",
    "HandlerParagraph",
    "LedgerKeyView",
    "TdGlledgerRec",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_reread",
    "aa047_eval_keys",
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
    "align_ledger_key_views",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba020_process_dal",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba090_process_rewrite",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "bridge_character_literal",
    "bridge_money_literal",
    "ca_exit",
    "ca_process_logs",
    "dispatch",
    "nominal_mt",
    "ws_ledger_key_bytes",
    "ws_mysql_edit",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#: The MySQL table, spelled as `mysql/ACASDB.sql:L122` spells it. Every identifier in
#: this module contains a HYPHEN, so every one is routed through `quote_identifier`.
TABLE_NAME: Final[str] = "GLLEDGER-REC"

BRIDGE_NAME: Final[str] = "nominalMT"

HANDLER_NAME: Final[str] = "acas005"

ENTITY_FACADE: Final[str] = "GL-Nominal"

#: `move 1 to File-Key-No.` - the facade's dispatch paragraph sets it before every
#: `CALL` [copybooks/Proc-ACAS-FH-Calls.cob:L35-L41], and the key guard below rejects
#: anything else.
FILE_KEY_NO: Final[int] = 1

WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.GL

#: `move 11 to WS-Log-File-No.` [common/acas005.cbl:L284] - written on entry and
#: therefore the value a Cobol-files run ends on. ANOMALY N-LOG.
WS_LOG_FILE_NO_COBOL: Final[int] = 11

#: `move 21 to WS-Log-File-no.` [common/acas005.cbl:L600] - the first act of the RDB
#: section, overwriting the 11 above.
WS_LOG_FILE_NO_RDB: Final[int] = 21

#: `05 WS-File-Key pic x(64) value spaces.` [copybooks/wsfnctn.cob:L52], whose own
#: comment records the widening: "increased to 64-- 30/12/16".
WS_FILE_KEY_WIDTH: Final[int] = 64


class HandlerParagraph(enum.IntEnum):
    """`WS-No-Paragraph` values the HANDLER writes, one per ISAM verb.

    `03 ws-No-Paragraph pic 999.` [copybooks/wsfnctn.cob:L47]. The handler stamps one of
    these before each flat-file verb so that a log line can be traced back to a
    paragraph.
    """

    OPEN = 201

    CLOSE = 202

    READ_NEXT = 203

    READ_INDEXED = 204

    START = 205

    WRITE = 206

    DELETE = 207

    RE_WRITE = 208


#: The BRIDGE's own `ws-No-Paragraph` stamps, keyed by the paragraph that writes each
#: one.
BRIDGE_PARAGRAPH_NUMBERS: Final[Mapping[str, tuple[int, ...]]] = MappingProxyType(
    {
        "ba020-Process-Open": (1,),
        "ba030-Process-Close": (2,),
        "ba040-Process-Read-Next": (3,),
        "ba041-Reread": (4,),
        "ba050-Process-Read-Indexed": (5, 6),
        # `move 8 to ws-No-Paragraph` [common/nominalMT.cbl:L748].
        "ba060-Process-Start": (8,),
        "ba070-Process-Write": (10,),
        "ba080-Process-Delete": (13,),
        "ba090-Process-Rewrite": (17,),
        "ba998-Free": (20,),
    }
)


#: Every literal this module can write into `WS-File-Key`, keyed by the paragraph and
#: exit that writes it, transcribed CHARACTER FOR CHARACTER from the frozen source.
FILE_KEY_TAGS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "handler-open": "OPEN GL NL File",
        "handler-close": "CLOSE GL NL File",
        "handler-eof": "EOF",
        "bridge-open": "OPEN GL LEDGER (RDB)",
        "bridge-close": "CLOSE GL LEDGER (RDB)",
        "bridge-position": "> 00000000",
        "bridge-no-data": "No Data",
        "bridge-eof": "EOF",
        "bridge-eof2": "EOF2",
        "bridge-eof3": "EOF3",
    }
)


#: The `File-Key-No` guard, transcribed from [common/acas005.cbl:L288-L302].
KEY_GUARDED_FUNCTIONS: Final[Mapping[FileFunction, tuple[FsReply, WeError, str]]] = (
    MappingProxyType(
        {
            FileFunction.READ_INDEXED: (
                FsReply.ERROR,
                WeError.FILE_KEY_NO_OUT_OF_RANGE,
                "[common/acas005.cbl:L289-L295]",
            ),
            FileFunction.START: (
                FsReply.ERROR,
                WeError.FILE_KEY_NO_OUT_OF_RANGE,
                "[common/acas005.cbl:L290-L295]",
            ),
            FileFunction.DELETE: (
                FsReply.ERROR,
                # 996, not 998 - the one place the two codes differ, and the one whose
                # comment was copy-pasted from 998. ANOMALY N-996-COMMENT.
                WeError.DELETE_KEY_OUT_OF_RANGE,
                "[common/acas005.cbl:L296-L301]",
            ),
        }
    )
)

#: The single key of reference, resolved from the shared transcription in
#: :mod:`acas_posting.dal.cursor_state` rather than restated here, so that the offset
#: and length cannot drift between the two modules.
KEY_OF_REFERENCE: Final[KeyOfReference] = key_of_reference(TABLE_NAME, FILE_KEY_NO)


@dataclass(frozen=True, slots=True)
class ColumnBinding:
    """One column of ``GLLEDGER-REC``, bound to its record field and host variable.

    Built ONLY from ``loader.entries_for_table("GLLEDGER-REC")`` - never from a picture
    clause read by eye. Agent Action Plan 0.8.1 makes that ordering a directive rather
    than a preference, and Agent Action Plan 0.8.2 records why the bridge is the
    authority.
    """

    #: `ordinal` of the column in `mysql/ACASDB.sql`, one-based.
    ordinal: int

    column_name: str

    #: The dictionary key, `GLLEDGER-REC.<COLUMN>`, so every binding can be taken back
    #: to its entry with `loader.get_entry` (rule R-5).
    dictionary_key: str

    hv_name: str

    hv_attribute: str

    #: The host variable's PICTURE, e.g. `S9(08)V9(02)`.
    hv_picture: str

    hv_usage: str

    hv_digits: int | None

    hv_scale: int | None

    #: Whether the host variable carries a sign.
    hv_signed: bool

    #: Character length of the host variable, `None` for the numeric ones. This is the
    #: 32 of ANOMALY A-12 for `HV-LEDGER-NAME` [common/nominalMT.cbl:L299] against the
    #: copybook's 24 [copybooks/wsledger.cob:L27].
    hv_character_length: int | None

    copybook_name: str

    #: Dotted attribute path from a :class:`WsLedgerRecord` to the field this column is
    #: loaded from and unloaded to, e.g. `quarters.ledger_q1`.
    record_attribute: str

    copybook_locator: str

    hv_locator: str

    column_locator: str

    #: `[common/nominalMT.cbl:L<n>]` for the `bb000-HV-Load` move that fills the host
    #: variable. These are what make ANOMALY N-LOADORDER visible.
    load_locator: str

    unload_locator: str

    #: `INT`, `STR` or `DECIMAL`, from the dictionary's own `cobol_python_storage`.
    #: Never inferred and never `float` - R-2 forbids binary floating point in any
    #: accounting path.
    python_storage: str

    #: Whether the column is `NOT NULL` in the frozen schema.
    not_null: bool

    primary_key: bool

    #: The dictionary's own anomaly tags for this column.
    anomaly_refs: tuple[str, ...]

    def cite(self) -> str:
        """Return the dictionary citation for this column, for logs and evidence.

        Delegates to :func:`loader.cite` so the wording is the dictionary's and cannot
        drift from it (rule R-5).
        """
        return loader.cite(self.dictionary_key)


#: The column count `mysql/ACASDB.sql:L122-L135` declares, and the count Agent Action
#: Plan 0.6.6 records for this table.
_DECLARED_COLUMN_COUNT: Final[int] = 11

#: Copybook field name -> dotted attribute path on :class:`WsLedgerRecord`.
_RECORD_ATTRIBUTE_BY_COPYBOOK_FIELD: Final[Mapping[str, str]] = MappingProxyType(
    {
        "WS-Ledger-Key9": "ws_ledger_key9.ws_ledger_key9",
        "Ledger-Type": "ledger_type",
        "Ledger-Place": "ledger_place",
        "Ledger-Level": "ledger_level",
        "Ledger-Name": "ledger_name",
        "Ledger-Balance": "ledger_balance",
        "Ledger-Last": "ledger_last",
        "Ledger-Q1": "quarters.ledger_q1",
        "Ledger-Q2": "quarters.ledger_q2",
        "Ledger-Q3": "quarters.ledger_q3",
        "Ledger-Q4": "quarters.ledger_q4",
    }
)


def _column_bindings() -> tuple[ColumnBinding, ...]:
    """Build the eleven bindings from the data dictionary, in column order.

    Runs ONCE at import.

    Returns:
        The eleven bindings, ordinal 1 through 11.

    Raises:
        ValueError: If the dictionary does not describe exactly the eleven columns
            `mysql/ACASDB.sql:L122-L135` declares, or describes them with ordinals other
            than 1..11.
    """
    entries = sorted(loader.entries_for_table(TABLE_NAME), key=lambda e: e.column.ordinal)
    bindings: list[ColumnBinding] = []
    for entry in entries:
        column = entry.column
        host_variable = entry.bridge_host_variable
        copybook = entry.copybook
        bindings.append(
            ColumnBinding(
                ordinal=column.ordinal,
                column_name=column.name,
                dictionary_key=entry.key,
                hv_name=host_variable.name,
                # `HV-LEDGER-KEY` -> `hv_ledger_key`. One mechanical rule, so a reader
                # can map either way without a second table.
                hv_attribute=host_variable.name.lower().replace("-", "_"),
                hv_picture=host_variable.picture,
                hv_usage=str(host_variable.usage),
                hv_digits=host_variable.digits,
                hv_scale=host_variable.scale,
                hv_signed=host_variable.signed,
                hv_character_length=host_variable.character_length,
                copybook_name=copybook.name,
                record_attribute=_RECORD_ATTRIBUTE_BY_COPYBOOK_FIELD[copybook.name],
                copybook_locator=f"[{copybook.source}]",
                hv_locator=f"[{host_variable.source}]",
                column_locator=f"[{column.source}]",
                load_locator=f"[{host_variable.load_source}]",
                unload_locator=f"[{host_variable.unload_source}]",
                python_storage=str(entry.cobol_python_storage),
                not_null=not column.nullable,
                primary_key=column.is_primary_key,
                anomaly_refs=tuple(entry.anomaly_refs),
            )
        )
    expected_ordinals = tuple(range(1, len(bindings) + 1))
    if tuple(b.ordinal for b in bindings) != expected_ordinals:
        raise ValueError(
            f"{TABLE_NAME} column ordinals are not contiguous from 1: "
            f"{tuple(b.ordinal for b in bindings)}"
        )
    if len(bindings) != _DECLARED_COLUMN_COUNT:
        raise ValueError(
            f"{TABLE_NAME} is declared with {_DECLARED_COLUMN_COUNT} columns at "
            f"[mysql/ACASDB.sql:L122-L135]; the dictionary describes "
            f"{len(bindings)}"
        )
    return tuple(bindings)


COLUMN_BINDINGS: Final[tuple[ColumnBinding, ...]] = _column_bindings()

#: Just the names, same order.
COLUMN_NAMES: Final[tuple[str, ...]] = tuple(b.column_name for b in COLUMN_BINDINGS)

COLUMN_BINDINGS_BY_NAME: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in COLUMN_BINDINGS}
)


#: `01 WS-MYSQL-EDIT PIC -Z(18)9.9(9).` [common/nominalMT.cbl:L232]. Thirty character
#: positions, laid out as:: pos 1 `-` the SIGN.
WS_MYSQL_EDIT_WIDTH: Final[int] = 30

_EDIT_INTEGER_DIGITS: Final[int] = 19

_EDIT_DECIMAL_DIGITS: Final[int] = 9

#: `WS-MYSQL-EDIT(13:08)` - the money reference modifier [common/nominalMT.cbl:L1078].
#: One-based start, length.
_EDIT_MONEY_INTEGER_SLICE: Final[tuple[int, int]] = (13, 8)

_EDIT_MONEY_DECIMAL_SLICE: Final[tuple[int, int]] = (22, 2)

_EDIT_KEY_SLICE: Final[tuple[int, int]] = (11, 10)

_EDIT_SMALL_INT_SLICE: Final[tuple[int, int]] = (18, 3)


def ws_mysql_edit(value: Decimal | int) -> str:
    """Render ``value`` as ``MOVE <value> TO WS-MYSQL-EDIT`` renders it.

    Reproduces the numeric-edited ``MOVE`` the bridge performs before every numeric
    literal it embeds, e.g. ``MOVE HV-LEDGER-BALANCE TO WS-MYSQL-EDIT``
    [common/nominalMT.cbl:L1076]. The receiving field is ``PIC -Z(18)9.9(9)``
    [common/nominalMT.cbl:L232], so the rules are.

    Args:
        value: The host variable's value. ``Decimal`` for the money host variables,
            ``int`` for the three integer ones.

    Returns:
        Exactly :data:`WS_MYSQL_EDIT_WIDTH` characters.
    """
    # `decimal.localcontext` with the transport context keeps this arithmetic inside the
    # precision `connection.py` pins for everything crossing the boundary, so an unusual
    # ambient context cannot change a stored penny.
    with decimal.localcontext(transport_decimal_context()):
        amount = Decimal(value) if isinstance(value, int) else Decimal(value)
        negative = amount < 0
        magnitude = -amount if negative else amount
        scaled = magnitude.scaleb(_EDIT_DECIMAL_DIGITS)
        units = int(scaled.to_integral_value(rounding=decimal.ROUND_DOWN))
        digits = str(units).rjust(_EDIT_INTEGER_DIGITS + _EDIT_DECIMAL_DIGITS, "0")
        integer_part = digits[:_EDIT_INTEGER_DIGITS]
        decimal_part = digits[_EDIT_INTEGER_DIGITS:]
    # Z-suppression: positions 2..19 show a space in place of a leading zero, position
    # 20 always shows its digit.
    suppressible, units_digit = integer_part[:-1], integer_part[-1]
    stripped = suppressible.lstrip("0")
    suppressed = stripped.rjust(len(suppressible), " ")
    sign = "-" if negative else " "
    return f"{sign}{suppressed}{units_digit}.{decimal_part}"


def _reference_modifier(edited: str, start: int, length: int) -> str:
    """Return ``edited(start:length)`` with COBOL's one-based indexing.

    Args:
        edited: The thirty-character edited field.
        start: One-based first character position.
        length: Number of characters.

    Returns:
        The ``length`` characters beginning at ``start``.
    """
    return edited[start - 1 : start - 1 + length]


def bridge_money_literal(value: Decimal) -> Decimal:
    """Return the money value the bridge's SQL literal actually DENOTES.

    ``(13:08)`` is positions 13..20 and ``(22:02)`` is positions 22..23. The SIGN LIVES
    AT POSITION ONE and is in neither slice, so it is never copied into the statement.

    Args:
        value: The host variable's value, already stored into ``S9(08)V9(02)`` by
            :func:`bb000_hv_load`.

    Returns:
        The non-negative two-decimal-place value the bridge's literal denotes.
    """
    edited = ws_mysql_edit(value)
    integer_text = _reference_modifier(edited, *_EDIT_MONEY_INTEGER_SLICE).strip()
    decimal_text = _reference_modifier(edited, *_EDIT_MONEY_DECIMAL_SLICE)
    # `FUNCTION TRIM` on an all-space slice yields the empty string, which the bridge
    # would concatenate as nothing at all.
    return Decimal(f"{integer_text or '0'}.{decimal_text}")


def _bridge_integer_literal(value: int, slice_spec: tuple[int, int]) -> int:
    """Return the integer a bridge numeric literal denotes, via the edit mask.

    The integer columns take the same route as the money ones - ``FUNCTION TRIM (WS-
    MYSQL-EDIT(11:10))`` [common/nominalMT.cbl:L1022-L1026] - and are put through it
    here rather than bound directly, so that the ONE transformation the bridge applies
    is the one this module applies.

    Args:
        value: The host variable's value.
        slice_spec: :data:`_EDIT_KEY_SLICE` or :data:`_EDIT_SMALL_INT_SLICE`.

    Returns:
        The integer the literal denotes.
    """
    edited = ws_mysql_edit(value)
    text = _reference_modifier(edited, *slice_spec).strip()
    return int(text or "0")


#: The record-layer descriptors for the eleven column-mapped copybook fields, keyed by
#: dictionary key.
_COPYBOOK_DESCRIPTORS: Final[Mapping[str, Any]] = MappingProxyType(
    {descriptor.dictionary_key: descriptor for descriptor in WsLedgerRecord.COLUMN_MAPPED_FIELDS}
)


def _locator_line(locator: str) -> int:
    """Return the line number out of a ``[file:Lnnn]`` locator.

    Used only to ORDER the load and unload sequences by the line the frozen bridge
    performs each move on, so :data:`HV_LOAD_ORDER` and :data:`HV_UNLOAD_ORDER` are
    derived from the dictionary rather than typed out - which is how ANOMALY N-LOADORDER
    stays visible even if someone later re-reads the bridge and disagrees with this
    module's prose.

    Args:
        locator: A locator of the form ``[common/nominalMT.cbl:L965]``.

    Returns:
        The integer line number, e.g. ``965``.

    Raises:
        ValueError: If the locator has no ``:L<digits>`` part. A build error, not run-
            time validation: every input is a committed artifact.
    """
    _, _, tail = locator.rpartition(":L")
    digits = tail.rstrip("]")
    if not digits.isdigit():
        raise ValueError(f"locator {locator!r} has no ':L<line>' part")
    return int(digits)


#: The eleven columns in the order ``bb000-HV-Load`` MOVES THEM
#: [common/nominalMT.cbl:L962-L972], derived by sorting the bindings on their load
#: locator. ANOMALY N-LOADORDER - REPRODUCED, NOT FIXED.
HV_LOAD_ORDER: Final[tuple[str, ...]] = tuple(
    binding.column_name
    for binding in sorted(COLUMN_BINDINGS, key=lambda b: _locator_line(b.load_locator))
)

#: The eleven columns in the order ``bb100-UnloadHVs`` MOVES THEM
#: [common/nominalMT.cbl:L990-L1000].
HV_UNLOAD_ORDER: Final[tuple[str, ...]] = tuple(
    binding.column_name
    for binding in sorted(COLUMN_BINDINGS, key=lambda b: _locator_line(b.unload_locator))
)


@dataclass(slots=True)
class TdGlledgerRec:
    """``01 TD-GLLEDGER-REC.`` [common/nominalMT.cbl:L294-L305].

    This group is the MIDDLE of the three-layer mapping, and it is the layer the Agent
    Action Plan makes authoritative.
    """

    #: ``HV-LEDGER-KEY PIC 9(10) COMP`` [common/nominalMT.cbl:L295]. Unsigned, so it
    #: cannot carry the sign loss that N-SIGNLOSS inflicts on the money.
    hv_ledger_key: int = 0

    hv_ledger_type: int = 0

    hv_ledger_place: str = " "

    hv_ledger_level: int = 0

    #: ``HV-LEDGER-NAME PIC X(32)`` [common/nominalMT.cbl:L299]. THIRTY-TWO, not the
    #: copybook's twenty-four [copybooks/wsledger.cob:L27] - ANOMALY A-12.
    hv_ledger_name: str = " " * 32

    hv_ledger_balance: Decimal = Decimal("0.00")

    hv_ledger_last: Decimal = Decimal("0.00")

    hv_ledger_q1: Decimal = Decimal("0.00")

    hv_ledger_q2: Decimal = Decimal("0.00")

    hv_ledger_q3: Decimal = Decimal("0.00")

    hv_ledger_q4: Decimal = Decimal("0.00")

    def initialize(self) -> None:
        """``INITIALIZE TD-GLLEDGER-REC.`` [common/nominalMT.cbl:L961].

        The FIRST statement of ``bb000-HV-Load``, and the reason every column of the
        frozen schema can be ``NOT NULL``. Agent Action Plan 0.6.2, on the convention
        every bridge follows.
        """
        self.hv_ledger_key = 0
        self.hv_ledger_type = 0
        self.hv_ledger_place = " "
        self.hv_ledger_level = 0
        self.hv_ledger_name = " " * 32
        self.hv_ledger_balance = Decimal("0.00")
        self.hv_ledger_last = Decimal("0.00")
        self.hv_ledger_q1 = Decimal("0.00")
        self.hv_ledger_q2 = Decimal("0.00")
        self.hv_ledger_q3 = Decimal("0.00")
        self.hv_ledger_q4 = Decimal("0.00")


class LedgerKeyView(enum.Enum):
    """Which declaration of the shared eight key characters was written last.

    This enum names the direction an alignment travels, because the two in-scope
    directions have DIFFERENT writers.
    """

    GROUP = "GROUP"

    REDEFINES = "REDEFINES"


#: Decimal scale factor between ``WS-Ledger-Nos`` and the whole eight-digit key.
_LEDGER_PC_SCALE: Final[int] = 100

_LEDGER_S_SCALE: Final[int] = 100

_LEDGER_KEY_WIDTH: Final[int] = 8


def align_ledger_key_views(
    record: WsLedgerRecord, *, source: LedgerKeyView = LedgerKeyView.GROUP
) -> None:
    """Make every view of the shared eight key characters agree.

    ANOMALY N-REDEFINES-ALIAS - the emulation of REDEFINES storage sharing that
    :class:`LedgerKeyView` documents. Mutates ``record`` in place, as the COBOL ``MOVE``
    it stands for does.

    Args:
        record: The ``WS-Ledger-Record`` whose key views are to be aligned.
        source: Which view was written last. Defaults to :attr:`LedgerKeyView.GROUP`
            because every in-scope caller writes the group view.
    """
    key = record.ws_ledger_key
    if source is LedgerKeyView.GROUP:
        nos = WsLedgerKey.WS_LEDGER_NOS.store(key.ws_ledger_nos)
        key.ws_ledger_nos = nos
        parts = key.ws_ledger_nos_parts
        parts.ledger_n = WsLedgerNosParts.LEDGER_N.store(nos // _LEDGER_S_SCALE)
        parts.ledger_s = WsLedgerNosParts.LEDGER_S.store(nos % _LEDGER_S_SCALE)
        key.ledger_pc = WsLedgerKey.LEDGER_PC.store(key.ledger_pc)
        record.ws_ledger_key9.ws_ledger_key9 = WsLedgerKey9.WS_LEDGER_KEY9.store(
            nos * _LEDGER_PC_SCALE + key.ledger_pc
        )
        return
    key9 = WsLedgerKey9.WS_LEDGER_KEY9.store(record.ws_ledger_key9.ws_ledger_key9)
    record.ws_ledger_key9.ws_ledger_key9 = key9
    nos = WsLedgerKey.WS_LEDGER_NOS.store(key9 // _LEDGER_PC_SCALE)
    key.ws_ledger_nos = nos
    key.ledger_pc = WsLedgerKey.LEDGER_PC.store(key9 % _LEDGER_PC_SCALE)
    parts = key.ws_ledger_nos_parts
    parts.ledger_n = WsLedgerNosParts.LEDGER_N.store(nos // _LEDGER_S_SCALE)
    parts.ledger_s = WsLedgerNosParts.LEDGER_S.store(nos % _LEDGER_S_SCALE)


def ws_ledger_key_bytes(
    record: WsLedgerRecord, *, source: LedgerKeyView = LedgerKeyView.GROUP
) -> str:
    """Return the eight characters of ``WS-Ledger-Record(1:8)``.

    Every ``WHERE`` clause the bridge builds keys off this reference modifier, e.g.
    ``WS-Ledger-Record(1:8)`` at [common/nominalMT.cbl:L621] on the read-indexed path
    and [:L829] on the delete path.

    Args:
        record: The ``WS-Ledger-Record`` to take the key from.
        source: Which view was written last, passed through to
            :func:`align_ledger_key_views`.

    Returns:
        Exactly eight decimal digits, zero-padded on the left.
    """
    align_ledger_key_views(record, source=source)
    return f"{record.ws_ledger_key9.ws_ledger_key9:0{_LEDGER_KEY_WIDTH}d}"


def _align_quarter_views(record: WsLedgerRecord) -> None:
    """Refresh ``Ledger-Q occurs 4`` from the four named quarter fields.

    Note the bridge correctly emits NO column for ``Ledger-Q``: it is the same storage
    as ``Q1``..``Q4``, so a column would double-count it. That omission is deliberate
    and is recorded as such in this module's docstring (rule R-5).

    Args:
        record: The ``WS-Ledger-Record`` whose quarter views are to be aligned.
    """
    quarters = record.quarters
    record.quarters_table.ledger_q = (
        quarters.ledger_q1,
        quarters.ledger_q2,
        quarters.ledger_q3,
        quarters.ledger_q4,
    )


def _store_hv(binding: ColumnBinding, value: object) -> int | str | Decimal:
    """Perform the COBOL ``MOVE`` into ``binding``'s host variable.

    The receiving field's geometry comes ENTIRELY from the data dictionary - the
    picture, digits, scale, sign and character length recorded for the bridge's own
    declaration - never from a width read off the source by eye.

    Args:
        binding: The column whose host variable receives the value.
        value: The value moved from the copybook field.

    Returns:
        The value as the host variable would hold it.

    Raises:
        ValueError: If the dictionary describes a storage class this table does not use.
            A build error: the eleven columns are ``INT``, ``STR`` and ``DECIMAL`` only.
    """
    storage = binding.python_storage
    if storage == "STR":
        # Alphanumeric MOVE: left-justify, space-pad, truncate right.
        # [copybooks/wsledger.cob:L27] -> [common/nominalMT.cbl:L299]: 24 -> 32 keeps
        # the value and appends eight spaces.
        width = binding.hv_character_length
        if width is None:
            raise ValueError(f"{binding.hv_name} is STR storage with no character length")
        text = "" if value is None else str(value)
        return text[:width].ljust(width)
    if storage == "INT":
        digits = binding.hv_digits
        if digits is None:
            raise ValueError(f"{binding.hv_name} is INT storage with no digit count")
        number = int(value)  # type: ignore[arg-type]
        truncated = abs(number) % (10**digits)
        return truncated if not binding.hv_signed else truncated * (1 if number >= 0 else -1)
    if storage == "DECIMAL":
        digits, scale = binding.hv_digits, binding.hv_scale
        if digits is None or scale is None:
            raise ValueError(f"{binding.hv_name} is DECIMAL storage with no digits or scale")
        with decimal.localcontext(transport_decimal_context()):
            amount = Decimal(value)  # type: ignore[arg-type]
            # Excess decimals are discarded toward zero - never rounded.
            quantised = amount.quantize(Decimal(1).scaleb(-scale), rounding=decimal.ROUND_DOWN)
            # High-order truncation: keep the low `digits` digits of the scaled integer,
            # preserving the sign if the field is signed.
            units = int(quantised.scaleb(scale))
            kept = abs(units) % (10**digits)
            if binding.hv_signed and units < 0:
                kept = -kept
            return Decimal(kept).scaleb(-scale)
    raise ValueError(f"{binding.column_name} has unsupported storage {storage!r}")


def bridge_character_literal(value: str) -> str:
    """Return the character value the bridge's SQL literal DENOTES.

    Reproduces ``FUNCTION TRIM (HV-LEDGER-NAME,TRAILING)`` [common/nominalMT.cbl:L1067]
    on the ``INSERT`` path and [:L1245] on the ``UPDATE`` path, and the same form for
    ``HV-LEDGER-PLACE`` at [:L1046] and.

    Args:
        value: The host variable's character content.

    Returns:
        The value with trailing spaces removed and leading spaces intact.
    """
    return value.rstrip(" ")


def bb000_hv_load(
    ledger: WsLedgerRecord,
    host_variables: TdGlledgerRec | None = None,
    *,
    key_view: LedgerKeyView = LedgerKeyView.GROUP,
) -> TdGlledgerRec:
    """``bb000-HV-Load Section.`` [common/nominalMT.cbl:L953], body [:L961-L972].

    The maintainer's closing note, verbatim [common/nominalMT.cbl:L974-L975]: "Loading
    HVs implies a non-Fetch action. RGs are handled separately for all such actions so
    they must not be loaded here.".

    Args:
        ledger: The ``WS-Ledger-Record`` to load from.
        host_variables: The group to fill. A new one is built when omitted.
        key_view: Which key view the caller wrote last, passed through to
            :func:`align_ledger_key_views`. Defaults to :attr:`LedgerKeyView.GROUP`
            because every in-scope caller writes the group view, e.g.
            [general/gl072.cbl:L405].

    Returns:
        The filled host-variable group.
    """
    group = TdGlledgerRec() if host_variables is None else host_variables
    # `initialize TD-GLLEDGER-REC.` [common/nominalMT.cbl:L961] - FIRST, and the reason
    # no bind is ever NULL. Agent Action Plan 0.6.2.
    group.initialize()
    # `move WS-Ledger-Key9 to HV-LEDGER-KEY` [:L962] reads the REDEFINES view, so the
    # shared storage must be coherent first; in COBOL it always is.
    align_ledger_key_views(ledger, source=key_view)
    for column_name in HV_LOAD_ORDER:
        binding = COLUMN_BINDINGS_BY_NAME[column_name]
        setattr(group, binding.hv_attribute, _store_hv(binding, _record_value(ledger, binding)))
    return group


def _record_value(ledger: WsLedgerRecord, binding: ColumnBinding) -> object:
    """Read ``binding``'s copybook field out of ``ledger``.

    Walks the dotted :attr:`ColumnBinding.record_attribute` path, which exists because
    two of the eleven fields are not top-level attributes: the key is reached through a
    REDEFINES [copybooks/wsledger.cob:L21-L22] and the quarters sit inside a group
    [:L30-L34].

    Args:
        ledger: The record to read from.
        binding: The column whose copybook field is wanted.

    Returns:
        The field's current value.
    """
    target: object = ledger
    for attribute in binding.record_attribute.split("."):
        target = getattr(target, attribute)
    return target


def _set_record_value(ledger: WsLedgerRecord, binding: ColumnBinding, value: object) -> None:
    """Write ``value`` into ``binding``'s copybook field on ``ledger``.

    The inverse of :func:`_record_value`, and the point at which the value passes
    through the RECORD LAYER's descriptor - so it lands truncated to the COPYBOOK's
    declared width, which is what makes ANOMALY A-12 truncate on the read path.

    Args:
        ledger: The record to write into.
        binding: The column whose copybook field receives the value.
        value: The value moved from the host variable.
    """
    path = binding.record_attribute.split(".")
    target: object = ledger
    for attribute in path[:-1]:
        target = getattr(target, attribute)
    descriptor = _COPYBOOK_DESCRIPTORS[binding.dictionary_key]
    setattr(target, path[-1], descriptor.store(value))


def _initialize_ws_ledger_record(ledger: WsLedgerRecord) -> None:
    """``initialize WS-Ledger-Record.`` [common/nominalMT.cbl:L989].

    The first statement of ``bb100-UnloadHVs``, and it does NOT do what a reader might
    assume. Settled against the compiled oracle, which rule R-6 makes the tie-breaker.

    Args:
        ledger: The record to initialize in place.
    """
    key = ledger.ws_ledger_key
    key.ws_ledger_nos = 0
    key.ledger_pc = 0
    key.ws_ledger_nos_parts.ledger_n = 0
    key.ws_ledger_nos_parts.ledger_s = 0
    ledger.ws_ledger_key9.ws_ledger_key9 = 0
    ledger.ledger_type = 0
    ledger.ledger_place = " "
    ledger.ledger_level = 0
    ledger.ledger_name = " " * 24
    ledger.ledger_balance = Decimal("0.00")
    ledger.ledger_last = Decimal("0.00")
    quarters = ledger.quarters
    quarters.ledger_q1 = Decimal("0.00")
    quarters.ledger_q2 = Decimal("0.00")
    quarters.ledger_q3 = Decimal("0.00")
    quarters.ledger_q4 = Decimal("0.00")
    _align_quarter_views(ledger)
    # `filler pic x(5)` [copybooks/wsledger.cob:L26] and `filler pic x(50)` [:L37] are
    # DELIBERATELY NOT reset - see the docstring's oracle evidence.


def bb100_unload_hvs(host_variables: TdGlledgerRec, ledger: WsLedgerRecord) -> None:
    """``bb100-UnloadHVs Section.`` [common/nominalMT.cbl:L980], body [:L989-L1000].

    The maintainer's note on why no indicator variables are needed, verbatim
    [common/nominalMT.cbl:L986-L987]: "NULL fields must not be returned in the buffer.
    SQL filters each column to ensure it has a proper value. This saves using indicator
    variables.".

    Args:
        host_variables: The group just filled by a fetch.
        ledger: The ``WS-Ledger-Record`` to unload into, mutated in place exactly as the
            COBOL ``MOVE`` statements mutate working storage.
    """
    _initialize_ws_ledger_record(ledger)
    for column_name in HV_UNLOAD_ORDER:
        binding = COLUMN_BINDINGS_BY_NAME[column_name]
        _set_record_value(ledger, binding, getattr(host_variables, binding.hv_attribute))
    # [:L990] wrote the redefinition; bring the group view and the inner `Ledger-n` /
    # `Ledger-s` pair up with it. ANOMALY N-REDEFINES-ALIAS.
    align_ledger_key_views(ledger, source=LedgerKeyView.REDEFINES)
    _align_quarter_views(ledger)


class CobolFileAccessNotMigratedError(AcasFileHandlerError):
    """Raised when a caller asks for the ISAM path, which is NOT migrated.

    Only the RDBMS path is in scope. Agent Action Plan 0.2.1.1 puts the twenty ``*MT``
    bridge pairs and the seventeen handlers in scope as the specification for SQL
    against the frozen schema, and 0.2.2 admits no indexed-file store.
    """

    def __init__(self, file_function: int, *, access_type: int = 0) -> None:
        """Build the error for a specific verb.

        Args:
            file_function: The ``File-Function`` the caller asked for.
            access_type: The ``Access-Type`` the caller asked for, when relevant.
        """
        super().__init__(
            FsReply.ERROR,
            WeError.RECORD_SIZE_MISMATCH,
            operation=(
                f"File-Function {file_function} Access-Type {access_type} on the "
                f"Cobol indexed-file path of {HANDLER_NAME}, which is not migrated "
                f"[common/acas005.cbl:L277]"
            ),
            table=TABLE_NAME,
        )
        #: The verb asked for, kept so a caller can report it.
        self.file_function = file_function
        self.access_type = access_type


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    """The result of one SQL command, in the bridge's own terms.

    Carries the ``(FS-Reply, We-Error)`` pair the bridge would leave behind plus the row
    count it read, and - critically - WHETHER IT WROTE THE PAIR AT ALL.
    """

    fs_reply: int

    we_error: int

    count_rows: int

    statement: str

    parameters: tuple[object, ...]

    sql_state: str = ""

    sql_err: str = ""

    sql_msg: str = ""

    #: Whether ``FS-Reply`` and ``We-Error`` were actually SET. FIXED.
    status_written: bool = True

    def apply_to(self, file_access: FileAccess) -> None:
        """Write this outcome into ``File-Access``, honouring :attr:`status_written`.

        When :attr:`status_written` is false NEITHER ``fs_reply`` NOR ``we_error`` is
        copied, which is precisely the silent behaviour of N-REWRITE-SILENT and
        N-DELETE-SILENT.

        Args:
            file_access: The block to update in place.
        """
        if self.status_written:
            file_access.fs_reply = self.fs_reply
            file_access.we_error = self.we_error
        logging_data = file_access.logging_data
        logging_data.sql_err = self.sql_err
        logging_data.sql_msg = self.sql_msg
        logging_data.sql_state = self.sql_state
        logging_data.ws_count_rows = self.count_rows


def _mysql_1210_command(
    connection: object,
    statement: str,
    parameters: Sequence[object],
    *,
    we_error: int = WeError.SUCCESS,
    file_function: int = 0,
) -> CommandOutcome:
    """``Mysql-1210-Command.`` [copybooks/mysql-procedures.cpy:L164-L178].

    Two details of that order are load-bearing and are reproduced exactly.

    Args:
        connection: The open connection.
        statement: The statement, identifiers already quoted by
            :func:`quote_identifier`, values as ``%s``.
        parameters: The values to bind, in placeholder order.
        we_error: The ``We-Error`` to carry into the error handler, matching the value
            the calling paragraph had set.
        file_function: The ``File-Function`` in play, so
            :func:`status.override_we_error_for_operation`-style per-verb codes can be
            applied by the caller.

    Returns:
        The outcome, with ``count_rows`` filled whether or not the command failed.
    """
    bound = tuple(parameters)
    #  THE STATEMENT IS NOT LOGGED, AND REDACTING IT WOULD NOT HELP: what leaks is
    #  not an identity shape the redaction rules recognise
    #  but the statement itself: an `UPDATE ... SET` over `GLLEDGER-REC` names every
    #  column of the nominal ledger row, and a `WHERE` clause names the account
    #  being posted to (CWE-532). The bound parameters are not logged for the same
    #  reason. A failed statement is reported once, with typed fields, by
    #  `dal/status.py`'s `mysql_1100_db_error`, which is enough to identify the
    #  fault; the statement text belongs to a debugger, not to an operator log.
    try:
        with execute_statement(connection, statement, bound) as cursor:  # type: ignore[arg-type]
            # `MySQL_affected_rows` [copybooks/mysql-procedures.cpy:L178] - read
            # unconditionally, and read here because the cursor owns it.
            count_rows = int(getattr(cursor, "rowcount", 0) or 0)
    except Exception as error:  # noqa: BLE001 - the bridge tests a return code, not a type
        errno = str(getattr(error, "errno", "") or "")
        sql_state = str(getattr(error, "sqlstate", "") or "")
        message = str(getattr(error, "msg", None) or error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            we_error=we_error,
        )
        return CommandOutcome(
            fs_reply=status.fs_reply,
            we_error=status.we_error,
            count_rows=0,
            statement=statement,
            parameters=bound,
            sql_state=status.sql_state,
            sql_err=status.sql_err,
            sql_msg=status.sql_msg,
        )
    return CommandOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=WeError.SUCCESS,
        count_rows=count_rows,
        statement=statement,
        parameters=bound,
    )


def _bind_value(binding: ColumnBinding, host_variables: TdGlledgerRec) -> object:
    """Return the value ``binding``'s SQL literal denotes, ready to bind.

    Routes every column through the transformation the bridge applies when it builds the
    literal, so what is bound is what the frozen statement would have said.

    Args:
        binding: The column being bound.
        host_variables: The loaded host-variable group.

    Returns:
        The value to bind - ``int``, ``str`` or :class:`~decimal.Decimal`, never
            ``None`` and never a binary float.
    """
    value = getattr(host_variables, binding.hv_attribute)
    if binding.python_storage == "DECIMAL":
        return bridge_money_literal(value)
    if binding.python_storage == "INT":
        return _bridge_integer_literal(
            value,
            _EDIT_KEY_SLICE if binding.primary_key else _EDIT_SMALL_INT_SLICE,
        )
    return bridge_character_literal(value)


#: The ``WHERE`` clause every keyed statement in this bridge uses, built once.
_WHERE_BY_KEY: Final[str] = f"{quote_identifier(KEY_OF_REFERENCE.column_name)} = %s"


def _set_clause() -> str:
    """Build the ``SET`` list shared by ``bb200-Insert`` and ``bb300-Update``.

    Every identifier goes through :func:`quote_identifier`. That is not optional
    styling.

    Returns:
        The ``SET`` list, e.g. ``` `LEDGER-KEY` = %s, `LEDGER-TYPE` = %s, ... ```.
    """
    return ", ".join(
        f"{quote_identifier(binding.column_name)} = %s" for binding in COLUMN_BINDINGS
    )


#: The ``SET`` list, built once at import so two processes agree on it byte for byte -
#: the determinism rule R-6 asks for, and cheap to assert in a test.
SET_CLAUSE: Final[str] = _set_clause()

#: ``INSERT INTO `GLLEDGER-REC` SET ...`` [common/nominalMT.cbl:L1015-L1017]. MySQL's
#: ``INSERT ... SET`` form, not ``INSERT ... VALUES`` - the bridge's own choice,
#: preserved.
INSERT_STATEMENT: Final[str] = (
    f"INSERT INTO {quote_identifier(TABLE_NAME)} SET {SET_CLAUSE};"
)

#: ``UPDATE `GLLEDGER-REC` SET ... WHERE ...`` [common/nominalMT.cbl:L1194-L1196, The
#: ``SET`` list is the SAME eleven columns, INCLUDING THE PRIMARY KEY, which the
#: statement then also matches on.
UPDATE_STATEMENT: Final[str] = (
    f"UPDATE {quote_identifier(TABLE_NAME)} SET {SET_CLAUSE} WHERE {_WHERE_BY_KEY};"
)

#: ``DELETE FROM `GLLEDGER-REC` WHERE ...`` [common/nominalMT.cbl:L843-L849]. NOTE THE
#: ABSENCE OF A TRAILING SEMICOLON.
DELETE_STATEMENT: Final[str] = f"DELETE FROM {quote_identifier(TABLE_NAME)} WHERE {_WHERE_BY_KEY}"


def bb200_insert(
    connection: object, host_variables: TdGlledgerRec, *, we_error: int = WeError.SUCCESS
) -> CommandOutcome:
    """``bb200-Insert Section.`` [common/nominalMT.cbl:L1005-L1178].

    Values are bound in TABLE-ORDINAL order, which is the order the bridge emits
    [:L1044], ``LEDGER-LEVEL`` [:L1053], ``LEDGER-NAME`` [:L1065], ``LEDGER-BALANCE``
    [:L1074], ``LEDGER-LAST``, then ``LEDGER-Q1`` through ``LEDGER-Q4`` [:L1162]. Note
    this is NOT the order ``bb000-HV-Load`` filled the group in.

    Args:
        connection: The open connection.
        host_variables: The group filled by :func:`bb000_hv_load`.
        we_error: The ``We-Error`` in force, carried into the error handler.

    Returns:
        The command outcome. ``count_rows`` is 1 on a successful single-row insert.
    """
    parameters = tuple(_bind_value(binding, host_variables) for binding in COLUMN_BINDINGS)
    return _mysql_1210_command(
        connection,
        INSERT_STATEMENT,
        parameters,
        we_error=we_error,
        file_function=FileFunction.WRITE,
    )


def bb300_update(
    connection: object,
    host_variables: TdGlledgerRec,
    key_value: str,
    *,
    we_error: int = WeError.SUCCESS,
) -> CommandOutcome:
    """``bb300-Update Section.`` [common/nominalMT.cbl:L1184-L1362].

    Args:
        connection: The open connection.
        host_variables: The group filled by :func:`bb000_hv_load` at
            [common/nominalMT.cbl:L877].
        key_value: The eight-character key from :func:`ws_ledger_key_bytes`, which is
            what ``ba090-Process-Rewrite`` puts in ``WS-Where``.
        we_error: The ``We-Error`` in force, carried into the error handler.

    Returns:
        The command outcome.
    """
    parameters = (
        *(_bind_value(binding, host_variables) for binding in COLUMN_BINDINGS),
        key_value,
    )
    return _mysql_1210_command(
        connection,
        UPDATE_STATEMENT,
        parameters,
        we_error=we_error,
        file_function=FileFunction.RE_WRITE,
    )


@dataclass(slots=True)
class BridgeSession:
    """The bridge's WORKING STORAGE, which persists between calls.

    Modelled as an explicit object with a module-level default rather than as bare
    module globals, which is the pattern :mod:`acas_posting.dal.cursor_state` sets for
    its own ``states``.
    """

    connection: object | None = None

    cursor: DatabaseCursor | None = None

    host_variables: TdGlledgerRec = field(default_factory=TdGlledgerRec)

    #: The ``Most-Cursor-Set`` state, delegated to :mod:`acas_posting.dal.cursor_state`
    #: so the ``START`` / ``READ NEXT`` protocol lives in one place across all twenty
    #: handlers.
    cursor_states: CursorStateTable = field(default_factory=CursorStateTable)

    ws_no_paragraph: int = 0

    #: ``WS-Where`` as last built, kept because the bridge copies it to ``WS-Log-Where``
    #: for test logging [common/nominalMT.cbl:L481].
    ws_where: str = ""

    dal_common: AcasDalCommonData | None = None

    #: The system record the handler passed down, needed by
    #: :func:`connection.mysql_1000_open`. PLUMBING NOTE, not a behaviour change.
    system_record: SystemRecord | None = None

    #: The transport policy handed to :func:`connection.mysql_1000_open`.
    transport: TransportSecurity | None = None


_SESSION: Final[BridgeSession] = BridgeSession()


def _resolve_session(session: BridgeSession | None) -> BridgeSession:
    """Return ``session``, or the module-level default when it is ``None``.

    Args:
        session: A caller-supplied session, or ``None``.

    Returns:
        The session to use.
    """
    return _SESSION if session is None else session


def _set_file_key(file_access: FileAccess, text: str) -> None:
    """``move <literal> to WS-File-Key`` - the bridge's log tag.

    ``WS-File-Key pic x(64)`` [copybooks/wsfnctn.cob:L52], widened by the maintainer
    with the note "increased to 64-- 30/12/16". A COBOL ``MOVE`` into it left-justifies,
    pads with spaces and truncates on the right, so that is what happens here -
    :data:`WS_FILE_KEY_WIDTH` characters, always.

    Args:
        file_access: The block whose ``Logging-Data`` receives the tag.
        text: The literal or built string being moved.
    """
    file_access.logging_data.ws_file_key = text[:WS_FILE_KEY_WIDTH].ljust(WS_FILE_KEY_WIDTH)


def _display_message_1(file_access: FileAccess, dal_common: AcasDalCommonData | None) -> None:
    """``if Testing-2 display Display-Message-1 with erase eos end-if``.

    Per Agent Action Plan 0.3.4 a "diagnostic display with no database effect becomes a
    log record at a severity matching the original's intent" and "must not alter control
    flow and must not appear in any table dump".

    Args:
        file_access: The block whose ``WS-Log-Where`` carries the clause.
        dal_common: The switch block. ``None`` means no block was passed, in which case
            ``Testing-2`` cannot be true.
    """
    if dal_common is None or dal_common.sw_testing_2 != _TESTING_2:
        return
    # `03 from WS-Where (1:J) pic x(69)` [common/nominalMT.cbl:L324] - the reference
    # modifier takes the clause's used length and the picture then truncates to 69.
    #
    # THE CLAUSE ITSELF IS NOT LOGGED, WHICH IS WHY THIS FUNCTION NOW ONLY GUARDS.
    # `WS-Where` holds the composed SQL `WHERE` clause, with the key value the
    # bridge built it around - an account number, in this table (CWE-532). The
    # frozen `display` writes it to a curses screen that no operator log persists;
    # a log record persists, is aggregated, and is read by people who have no
    # business seeing which account was touched. The guard is kept in place, with
    # its `Testing-2` predicate intact, so that the paragraph still exists for
    # traceability and so that the switch still means what it means - it simply has
    # nothing left to write. Nothing about control flow or status changes: this
    # function returned `None` before and returns `None` now.


_DISPLAY_WHERE_WIDTH: Final[int] = 69


def _set_log_where(file_access: FileAccess, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - for test logging.

    Args:
        file_access: The block whose ``Logging-Data`` receives the clause.
        text: The ``WHERE`` clause as built.
    """
    file_access.logging_data.ws_log_where = text[:231].ljust(231)


def ba020_process_open(
    file_access: FileAccess, *, session: BridgeSession | None = None
) -> None:
    """``ba020-Process-Open.`` [common/nominalMT.cbl:L391-L432].

    The string order is the frozen order - Schema, Host, UName, UPass, Port, Socket
    [:L395-L418] - which is NOT the order the handler loaded ``RDB-Data`` in
    [common/acas005.cbl:L637-L642], where it is Schema, UName, UPass, Port, Host,
    Socket.

    Args:
        file_access: The block supplying ``RDB-Data`` and receiving the status.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"][0]
    rdb_data = file_access.rdb_data
    _LOG.debug(
        "%s connect: transport=%s",
        BRIDGE_NAME,
        transport_category(
            {
                "host": cobol_string_delimited_by_space(rdb_data.db_host),
                "unix_socket": cobol_string_delimited_by_space(
                    rdb_data.db_socket
                ),
            }
            if cobol_string_delimited_by_space(rdb_data.db_socket)
            else {"host": cobol_string_delimited_by_space(rdb_data.db_host)}
        ),
    )
    if state.system_record is None:
        raise CobolFileAccessNotMigratedError(FileFunction.OPEN, access_type=AccessType.INPUT)
    outcome = mysql_1090_exit(
        mysql_1000_open(
            state.system_record,
            ws_no_paragraph=state.ws_no_paragraph,
            we_error=file_access.we_error,
            # The policy from working storage - see `BridgeSession.transport`.
            transport=state.transport,
        )
    )
    file_access.fs_reply = outcome.fs_reply
    file_access.we_error = outcome.we_error
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = outcome.ws_no_paragraph
    logging_data.sql_err = outcome.sql_err
    logging_data.sql_msg = outcome.sql_msg
    logging_data.sql_state = outcome.sql_state
    if outcome.fs_reply != FsReply.SUCCESS:
        ba999_end(file_access, session=state)
        return
    state.connection = outcome.connection
    state.cursor = None
    _set_file_key(file_access, FILE_KEY_TAGS["bridge-open"])
    state.cursor_states.reset(TABLE_NAME)
    ba999_end(file_access, session=state)


def ba030_process_close(
    file_access: FileAccess, *, session: BridgeSession | None = None
) -> None:
    """``ba030-Process-Close.`` [common/nominalMT.cbl:L435-L448].

    Args:
        file_access: The block receiving the status.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    if state.cursor_states.state_for(TABLE_NAME, CursorSlot.PRIMARY).cursor_active():
        ba998_free(session=state)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba030-Process-Close"][0]
    _set_file_key(file_access, FILE_KEY_TAGS["bridge-close"])
    if state.cursor is not None:
        state.cursor.close()  # type: ignore[attr-defined]
        state.cursor = None
    mysql_1980_close(state.connection)  # type: ignore[arg-type]
    mysql_1999_exit()
    state.connection = None
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    ba999_end(file_access, session=state)


def _require_cursor(state: BridgeSession) -> DatabaseCursor:
    """Return the session's cursor, creating it on first use.

    The bridge holds ONE result pointer, ``TP-GLLEDGER-REC USAGE POINTER``
    [common/nominalMT.cbl:L293], so this holds one cursor. It is created lazily because
    ``ba020-Process-Open`` connects without positioning anything - ``move zero to Most-
    Cursor-Set`` [:L432] - and destroyed by :func:`ba030_process_close`.

    Args:
        state: The bridge working storage.

    Returns:
        The cursor for the ISAM emulation to walk.

    Raises:
        AcasFileHandlerError: If no connection is open. The bridge would have failed
            inside ``MySQL_query`` with a null handle.
    """
    if state.connection is None:
        raise AcasFileHandlerError(
            FsReply.ERROR,
            WeError.UNKNOWN_UNEXPECTED,
            operation=f"{BRIDGE_NAME} used before ba020-Process-Open",
            table=TABLE_NAME,
        )
    if state.cursor is None:
        cursor = acquire_cursor(state.connection)  # type: ignore[arg-type]
        if cursor_is_unavailable(cursor):
            return cursor  # type: ignore[return-value]
        state.cursor = cursor  # type: ignore[assignment]
    return state.cursor


def ba040_process_read_next(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CursorOutcome:
    """``ba040-Process-Read-Next.`` [common/nominalMT.cbl:L450-L523].

    Agent Action Plan 0.6.4, verbatim: "The sort feeds a sequential read. ``gl072``
    locates the nominal-ledger account for each posting with a sequential read-next
    rather than an indexed read [general/gl072.cbl:L408]. It finds the correct
    account only because ``gl071`` has already emitted the transaction stream in
    nominal-key order. Any change in sort stability or key composition produces
    SILENT MISPOSTING - no error, no diagnostic, wrong balances."

    The plan's citation is off by a few lines: the sequential read is the guarded
    ``if read-ledger not = "R" / perform GL-Nominal-Read-Next`` at
    ``[general/gl072.cbl:L407-L408]``, and ``[general/gl072.cbl:L408]`` is the
    ``move zero to tot-dr tot-cr`` after it. The requirement is unchanged.

    So the ordering below is a CORRECTNESS REQUIREMENT, not a convenience. It is
    ``ORDER BY `LEDGER-KEY` ASC``, one term, no tie-breaker, no ``LIMIT``, from the
    key of reference [common/nominalMT.cbl:L466-L470] - and the self-positioning
    relation is ``>`` with a low key of ``"00000000"`` [:L466-L467], carrying the
    maintainer's own note "26/12/16 NOT '='". Agent Action Plan 0.8.4 forbids the
    obvious optimisation by name: the migration "must not 'optimise' the sequential
    nominal read into an indexed one, even though that would obviously be faster ...
    Any performance work is therefore out of scope by construction, not merely
    unrequested."

    All of that - the positioning statement, the stored-result snapshot, the
    one-row-per-call fetch and the ``FS-Reply`` protocol - is implemented by
    :func:`cursor_state.read_next`, driven from
    :data:`cursor_state.SEQUENTIAL_READ_START` and
    :data:`cursor_state.TABLE_OF_KEYNAMES` so that the per-bridge relation survives
    as DATA rather than as a copy of this prose. This paragraph supplies the table
    and the record, and unloads the row.

    STRUCTURE. ``ba040`` and ``ba041`` are two stages of ONE verb: the
    ``if Cursor-Not-Active`` block [:L454-L522] positions, ends with
    ``perform ba999-End`` to log [:L521], and then FALLS THROUGH the ``end-if``
    into ``ba041-Reread``. The empty-table branch inside it instead does
    ``go to ba999-End`` [:L512] and does not fall through.

    * GO TO CLASS 3 (section exit) at [:L512] - the empty-table branch returns
      ``(10, 10)`` with the tag ``"No Data"``.
    * GO TO CLASS 4 (sibling re-dispatch) is the FALL-THROUGH at [:L522] into
      ``ba041-Reread``, expressed here as the explicit call to :func:`ba041_reread`
      that :func:`cursor_state.read_next` performs internally.

    Args:
        file_access: The block supplying the caller's ``FS-Reply`` - which matters,
            because end of file is STICKY on this path - and receiving the status.
        ledger: The record to unload a fetched row into.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The cursor outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba040-Process-Read-Next"][0]
    _set_log_where(file_access, "")
    _display_message_1(file_access, state.dal_common)
    outcome = cursor_state.read_next(
        _require_cursor(state),
        TABLE_NAME,
        slot=CursorSlot.PRIMARY,
        states=state.cursor_states,
        file_access=file_access,
    )
    state.ws_where = outcome.statement
    _set_file_key(file_access, outcome.file_key)
    if outcome.row is not None:
        ba041_reread(outcome, ledger, file_access, session=state)
    ba999_end(file_access, session=state)
    return outcome


def ba041_reread(
    outcome: CursorOutcome,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    *,
    session: BridgeSession | None = None,
) -> None:
    """``ba041-Reread.`` [common/nominalMT.cbl:L525-L592].

    The eleven host variables are fetched in COLUMN order [:L540-L551], which is why the
    fetch is driven from :data:`COLUMN_BINDINGS` and not from :data:`HV_LOAD_ORDER`.

    Args:
        outcome: The outcome from :func:`cursor_state.read_next`, carrying the row.
        ledger: The record to unload into.
        file_access: The block receiving the log tag and status.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba041-Reread"][0]
    if outcome.row is None:
        return
    _fetch_into_host_variables(outcome.row, state.host_variables)
    bb100_unload_hvs(state.host_variables, ledger)
    _set_file_key(file_access, str(state.host_variables.hv_ledger_key))


def _fetch_into_host_variables(
    row: Mapping[str, object], host_variables: TdGlledgerRec
) -> None:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT HV-...`` - the fetch.

    Reproduces the eleven-argument fetch at [common/nominalMT.cbl:L540-L551] on the
    read-next path and [:L645-L656] on the read-indexed path. The arguments are in
    COLUMN order in both, so the loop walks :data:`COLUMN_BINDINGS`.

    Args:
        row: The fetched row, keyed by column name.
        host_variables: The group to fill in place.
    """
    for binding in COLUMN_BINDINGS:
        value = row.get(binding.column_name)
        if value is None:
            # The buffer never holds NULL - see the maintainer's note above.
            value = 0 if binding.python_storage != "STR" else ""
        setattr(host_variables, binding.hv_attribute, _store_hv(binding, value))


def ba050_process_read_indexed(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CursorOutcome:
    """``ba050-Process-Read-Indexed.`` [common/nominalMT.cbl:L594-L687].

    * the miss branch is ``move 21 to fs-Reply`` with ``move zero to WE-Error``
    [:L635-L637] - and that second statement is a DIVERGENCE FROM ``glpostingMT``, whose
    equivalent [common/glpostingMT.cbl:L633-L636] does NOT clear ``We-Error``.

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key and receiving the row.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The cursor outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba050-Process-Read-Indexed"][0]
    key_value = ws_ledger_key_bytes(ledger)
    outcome = cursor_state.read_indexed(
        _require_cursor(state),
        TABLE_NAME,
        key_value,
        key_number=FILE_KEY_NO,
        slot=CursorSlot.PRIMARY,
        states=state.cursor_states,
        file_access=file_access,
    )
    state.ws_where = outcome.statement
    _set_log_where(file_access, outcome.statement)
    _display_message_1(file_access, state.dal_common)
    if outcome.row is not None:
        _fetch_into_host_variables(outcome.row, state.host_variables)
        bb100_unload_hvs(state.host_variables, ledger)
        _set_file_key(file_access, str(state.host_variables.hv_ledger_key))
    elif outcome.fs_reply == FsReply.INVALID_KEY_ON_START:
        file_access.we_error = WeError.SUCCESS
    # ANOMALY N-NOTFOUND-DEAD - REPRODUCTION SITE. The frozen paragraph's `WS-MYSQL-
    # Count-Rows not > zero` branch [common/nominalMT.cbl:L661-L681], with its 990/"Not
    # found 1" and 989/"Not found 2" arms, is UNREACHABLE.
    ba998_free(session=state)
    ba999_end(file_access, session=state)
    return outcome


def ba060_process_start(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CursorOutcome:
    """``ba060-Process-Start.`` [common/nominalMT.cbl:L689-L789].

    Read that range carefully: ``< 5 or > 8`` REJECTS ACCESS TYPE 9.

    Args:
        file_access: The block supplying ``Access-Type`` and receiving the status.
        ledger: The record supplying the key.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The cursor outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba060-Process-Start"][0]
    key_value = ws_ledger_key_bytes(ledger)
    outcome = cursor_state.start(
        _require_cursor(state),
        TABLE_NAME,
        key_value,
        file_access.access_type,
        key_number=FILE_KEY_NO,
        slot=CursorSlot.PRIMARY,
        states=state.cursor_states,
        file_access=file_access,
    )
    state.ws_where = outcome.statement
    _set_log_where(file_access, outcome.statement)
    # ANOMALY N-START-SILENT - REPRODUCTION SITE. No status is written on the no-rows-
    # without-errno path.
    _display_message_1(file_access, state.dal_common)
    # `move WS-Ledger-Key to WS-File-Key.` [:L744] - note the maintainer's own
    # commented-out alternative on the same line, `WS-Ledger-Record (K:L)`, which would
    # have been the same eight characters by a different route.
    _set_file_key(file_access, outcome.file_key or key_value)
    ba999_end(file_access, session=state)
    return outcome


def ba070_process_write(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CommandOutcome:
    """``ba070-Process-Write.`` [common/nominalMT.cbl:L793-L818].

    ordering choice is why write does NOT suffer ANOMALY N-REWRITE-SILENT or N-DELETE-
    SILENT.

    Args:
        file_access: The block receiving the status.
        ledger: The record to insert.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The command outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    bb000_hv_load(ledger, state.host_variables)
    _set_file_key(file_access, ws_ledger_key_bytes(ledger))
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba070-Process-Write"][0]
    outcome = bb200_insert(state.connection, state.host_variables, we_error=WeError.SUCCESS)
    if outcome.count_rows != 1:
        outcome.apply_to(file_access)
    else:
        file_access.logging_data.ws_count_rows = outcome.count_rows
    ba999_end(file_access, session=state)
    return outcome


def ba080_process_delete(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CommandOutcome:
    """``ba080-Process-Delete.`` [common/nominalMT.cbl:L820-L873].

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The command outcome, already applied to ``file_access`` - honouring
            ``status_written``.
    """
    state = _resolve_session(session)
    key_value = ws_ledger_key_bytes(ledger)
    _set_file_key(file_access, key_value)
    _set_log_where(file_access, DELETE_STATEMENT)
    _display_message_1(file_access, state.dal_common)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba080-Process-Delete"][0]
    outcome = _mysql_1210_command(
        state.connection,
        DELETE_STATEMENT,
        (key_value,),
        we_error=file_access.we_error,
        file_function=FileFunction.DELETE,
    )
    if outcome.count_rows != 1:
        if outcome.sql_err:
            outcome = replace(
                outcome, fs_reply=FsReply.ERROR, we_error=WeError.DELETE_KEY_OUT_OF_RANGE
            )
        else:
            # ANOMALY N-DELETE-SILENT: the branch jumps to ba999-End [:L868], PAST `move
            # zero to FS-Reply WE-Error` [:L872]. Nothing is written.
            outcome = replace(outcome, status_written=False)
    else:
        outcome = replace(
            outcome,
            fs_reply=FsReply.SUCCESS,
            we_error=WeError.SUCCESS,
            sql_err="",
            sql_msg="",
            sql_state="",
        )
    outcome.apply_to(file_access)
    ba999_end(file_access, session=state)
    return outcome


def ba090_process_rewrite(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CommandOutcome:
    """``ba090-Process-Rewrite.`` [common/nominalMT.cbl:L876-L916].

    ANOMALY N-REWRITE-SILENT - REPRODUCED, NOT FIXED. Identical in shape to N-DELETE-
    SILENT [:L901-L913]: the ``go to ba999-End`` at [:L912] sits inside the ``WS-MYSQL-
    COUNT-ROWS not = 1`` branch and jumps past ``move zero to FS-Reply WE-Error`` at
    [:L914].

    Args:
        file_access: The block receiving the status.
        ledger: The record to write, and the source of the key.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The command outcome, already applied to ``file_access`` - honouring
            ``status_written``.
    """
    state = _resolve_session(session)
    bb000_hv_load(ledger, state.host_variables)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba090-Process-Rewrite"][0]
    key_value = ws_ledger_key_bytes(ledger)
    _set_log_where(file_access, UPDATE_STATEMENT)
    _display_message_1(file_access, state.dal_common)
    outcome = bb300_update(
        state.connection, state.host_variables, key_value, we_error=file_access.we_error
    )
    if outcome.count_rows != 1:
        if outcome.sql_err:
            outcome = replace(outcome, fs_reply=FsReply.ERROR, we_error=994)
        else:
            # ANOMALY N-REWRITE-SILENT: `go to ba999-End` [:L912] jumps past `move zero
            # to FS-Reply WE-Error` [:L914]. Nothing is written.
            outcome = replace(outcome, status_written=False)
    else:
        outcome = replace(
            outcome,
            fs_reply=FsReply.SUCCESS,
            we_error=WeError.SUCCESS,
            sql_err="",
            sql_msg="",
            sql_state="",
        )
    outcome.apply_to(file_access)
    ba999_end(file_access, session=state)
    return outcome


def ba100_bad_function(
    file_access: FileAccess, *, session: BridgeSession | None = None
) -> None:
    """``ba100-Bad-Function.`` [common/nominalMT.cbl:L919-L923].

    ``We-Error`` FIRST, then ``FS-Reply`` - the reverse of the handler's own
    ``aa100-Bad-Function``, which writes ``FS-Reply`` first
    [common/acas005.cbl:L569-L570]. Statement order is preserved in both because rule
    R-6 asks for the COBOL's order, even where the result is identical.

    Args:
        file_access: The block receiving ``(99, 990)``.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    file_access.we_error = WeError.UNKNOWN_UNEXPECTED
    file_access.fs_reply = FsReply.ERROR
    ba999_end(file_access, session=state)


def ba998_free(*, session: BridgeSession | None = None) -> None:
    """``ba998-Free.`` [common/nominalMT.cbl:L931-L941].

    It has NO ``GO TO``: it falls straight into ``ba999-end`` [:L943], which is why
    every ``go to ba998-Free`` in the bridge also produces a log record.

    Args:
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba998-Free"][0]
    state.cursor_states.state_for(TABLE_NAME, CursorSlot.PRIMARY).free()


def ba999_end(file_access: FileAccess, *, session: BridgeSession | None = None) -> None:
    """``ba999-end.`` [common/nominalMT.cbl:L943-L948].

    Args:
        file_access: The block whose ``Logging-Data`` is written out.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    file_access.logging_data.ws_no_paragraph = state.ws_no_paragraph
    # `if Testing-1 perform Ca-Process-Logs.` [:L946-L947]. `ACAS-DAL-Common-data` is
    # the bridge's own second parameter [common/acas005.cbl:L664], so the switch is
    # reachable here.
    dal_common = state.dal_common
    if dal_common is not None and dal_common.sw_testing == _TESTING_1:
        ca_process_logs(file_access, dal_common)


#: ``88 Testing-1 value 1.`` [copybooks/Test-Data-Flags.cob:L11]. The switch's declared
#: ``VALUE`` is 1, so DAL logging is ON by default.
_TESTING_1: Final[int] = 1

_TESTING_2: Final[int] = 1


def ca_process_logs(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """``Ca-Process-Logs.`` [common/nominalMT.cbl:L1367-L1372] and
    [common/acas005.cbl:L675-L680].

    Both the bridge and the handler have a paragraph of this name and both do the
    same one thing::

        call     "fhlogger" using File-Access
                                 ACAS-DAL-Common-data.

    ``fhlogger`` is a separate COBOL program [common/fhlogger.cbl] that appends a
    line to a log file, and Agent Action Plan 0.2.2 puts it OUT OF SCOPE by name
    among the "Non-posting utilities". Rule R-1 forbids calling it in any case: "The
    Python implementation must not execute, embed, or shell out to the COBOL
    programs."

    So the CALL becomes a log record on this module's own logger, carrying the same
    fields the logger would have written - the paragraph number, the file key, the
    where-clause and the SQL diagnostics. It has NO database effect and NO effect on
    control flow, which is the treatment Agent Action Plan 0.3.4 prescribes for
    output that does not reach a table.

    ``Log-File-Rec-Written`` [copybooks/Test-Data-Flags.cob:L18] is advanced, because
    the counter lives in ``ACAS-DAL-Common-data`` - shared with the handler, per its
    comment "in both acas0nn and a DAL" - and a caller can read it. It is plain
    accounting of records written, not a clock or a random source, so it does not
    disturb the determinism rule R-6 requires. IT IS ADVANCED MODULO ONE MILLION,
    which this module used not to do: the field is ``pic 9(6)``, so it wraps rather
    than growing, and an unbounded Python integer diverged from the frozen value the
    moment a run wrote a millionth record.

    ONE ADAPTER FOR ALL SEVENTEEN HANDLER MODULES. The record is composed by
    :func:`acas_posting.dal.status.log_file_handler_record`, so this handler's field
    set, level and counter arithmetic are identical to every other handler's rather
    than a local reading of the same one-line paragraph. Three fields are withheld
    and the withholding is the point: ``WS-File-Key`` is the nominal-ledger ACCOUNT
    NUMBER, ``WS-Log-Where`` is the composed ``WHERE`` clause it was built into, and
    ``SQL-Msg`` is the driver's free text. ``redact_for_log`` was applied to all three
    and could not help - its rules recognise connection-message shapes, not account
    numbers - so they are not reported at all (CWE-532). ``WS-Count-Rows`` goes with
    them: it belongs to ``Delete-All`` reporting rather than to the trace.

    Args:
        file_access: The block whose ``Logging-Data`` is written out.
        dal_common: The switch block, whose counter is advanced.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program=HANDLER_NAME,
        paragraph="ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=dal_common,
    )


def ca_exit() -> None:
    """``ca-Exit.`` [common/acas005.cbl:L681-L682].

    Kept as a function because rule R-5 asks that every paragraph reproduced have a
    correspondingly named counterpart, so a reader walking the COBOL finds one here too.
    It performs nothing because the COBOL performs nothing.
    """


def nominal_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    ledger: WsLedgerRecord,
    *,
    system_record: SystemRecord | None = None,
    session: BridgeSession | None = None,
) -> None:
    """``call "nominalMT" using File-Access ACAS-DAL-Common-data WS-Ledger-Record``.

    THREE parameters, and ``File-Access`` FIRST - not the five-parameter, ``System-
    Record``-first shape of the handler :func:`dispatch`. Rule R-5 asks for both
    signatures to be published precisely so the difference is visible.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L22-L41], supplying ``File-
            Function``, ``Access-Type`` and ``RDB-Data``, and receiving ``FS-Reply``,
            ``We-Error`` and all ``Logging-Data``.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob:L6], the
            testing switches and the log-record counter.
        ledger: ``WS-Ledger-Record`` [copybooks/wsledger.cob:L12], the record buffer -
            read on write and re-write, written on the two read paths.
        system_record: Carried for :func:`connection.mysql_1000_open`; see the plumbing
            note on :attr:`BridgeSession.system_record`. Not a fourth COBOL parameter.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.dal_common = dal_common
    if system_record is not None:
        state.system_record = system_record
    function = file_access.file_function
    if function == FileFunction.OPEN:
        ba020_process_open(file_access, session=state)
    elif function == FileFunction.CLOSE:
        ba030_process_close(file_access, session=state)
    elif function == FileFunction.READ_NEXT:
        ba040_process_read_next(file_access, ledger, session=state)
    elif function == FileFunction.READ_INDEXED:
        ba050_process_read_indexed(file_access, ledger, session=state)
    elif function == FileFunction.WRITE:
        ba070_process_write(file_access, ledger, session=state)
    elif function == FileFunction.RE_WRITE:
        ba090_process_rewrite(file_access, ledger, session=state)
    elif function == FileFunction.DELETE:
        ba080_process_delete(file_access, ledger, session=state)
    elif function == FileFunction.START:
        ba060_process_start(file_access, ledger, session=state)
    else:
        # `when other go to ba100-Bad-Function` [:L387-L388], and the unconditional `go
        # to ba100-Bad-Function` that follows the `end-evaluate` [:L388] as the "should
        # never get here but in case" guard.
        ba100_bad_function(file_access, session=state)


def ba020_process_dal(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    ledger: WsLedgerRecord,
    *,
    system_record: SystemRecord | None = None,
    session: BridgeSession | None = None,
) -> None:
    """``ba020-Process-DAL.`` [common/acas005.cbl:L662-L669].

    The HANDLER's paragraph that issues the bridge ``CALL``.

    Args:
        file_access: ``File-Access``, passed through first.
        dal_common: ``ACAS-DAL-Common-data``, passed through second.
        ledger: ``WS-Ledger-Record``, passed through third.
        system_record: Carried for the connection open; see
            :attr:`BridgeSession.system_record`.
        session: The bridge working storage; the module default when ``None``.
    """
    nominal_mt(
        file_access, dal_common, ledger, system_record=system_record, session=session
    )


def _ws_ledger_record_length() -> int:
    """Return ``function Length (WS-Ledger-Record)`` [common/acas005.cbl:L605-L607].

    Summed from the record layer's own descriptors rather than written out as a literal:
    every storage-allocating elementary field contributes its width, and groups and
    REDEFINES views contribute nothing because they allocate no storage of their own.

    Returns:
        The record length in bytes.
    """
    total = 0
    for descriptor in WsLedgerRecord.FIELDS:
        parent = descriptor.parent_group
        if descriptor.is_group or descriptor.redefines:
            continue
        if parent and str(parent).lower().startswith("filler"):
            continue
        total += descriptor.byte_length * (descriptor.occurs or 1)
    return total


#: ``function Length (WS-Ledger-Record)`` - the ``A`` of the record-length guard,
#: computed once. 126 bytes [copybooks/wsledger.cob:L10].
WS_LEDGER_RECORD_LENGTH: Final[int] = _ws_ledger_record_length()

#: ``function length (Ledger-Record)`` - the ``B`` of the guard.
LEDGER_RECORD_LENGTH: Final[int] = WS_LEDGER_RECORD_LENGTH


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas005.cbl:L594-L600].

    ANOMALY N-LOG - REPRODUCED. ``WS-Log-File-No`` was set to 11 on entry to the program
    [common/acas005.cbl:L284], with the comment "Cobol/RDB, File/Table within sub
    System"; the moment the RDB path is entered it becomes 21.

    Args:
        file_access: The block whose ``Logging-Data`` receives the file number.
    """
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    file_access: FileAccess,
    system_record: SystemRecord,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas005.cbl:L602-L643].

    Two jobs inside ONE first-call-only guard, ``if A = zero`` [:L604], whose ``end-if``
    closes after BOTH [:L643].

    Args:
        file_access: The block receiving ``RDB-Data`` and, on refusal, ``(99, 901)``.
        system_record: The source of the six connection parameters.
        dal_common: The switch block; ``Testing-1`` gates the log on the refusal path
            [:L626-L628].

    Returns:
        ``True`` to continue to the bridge, ``False`` when the record-length guard fired
            and the section must exit.
    """
    if WS_LEDGER_RECORD_LENGTH < LEDGER_RECORD_LENGTH:
        file_access.we_error = WeError.RECORD_SIZE_MISMATCH
        file_access.fs_reply = FsReply.ERROR
        _LOG.error(
            "GL902 Program Error: Temp rec = %s < NL-Rec = %s - programming "
            "error, the caller must stop [common/acas005.cbl:L609]",
            WS_LEDGER_RECORD_LENGTH,
            LEDGER_RECORD_LENGTH,
        )
        if dal_common.sw_testing == _TESTING_1:
            ca_process_logs(file_access, dal_common)
        # `accept Accept-Reply at 2433` [:L630] - DROPPED, per AAP 0.3.4. `go to ba-
        # rdbms-exit` [:L631] - PRESERVED, as the False below.
        return False
    file_access.rdb_data = load_rdb_data_once(system_record)
    return True


def ba015_test_ends(file_access: FileAccess) -> None:
    """``ba015-Test-Ends.`` [common/acas005.cbl:L644-L660].

    In ``acas008`` the identical block is LIVE, and there ``Open-Output`` really does
    mean DELETE EVERY ROW [common/acas008.cbl:L313-L319, :L571-L574].

    Args:
        file_access: Unused. Taken so the call sequence in :func:`ba_process_rdbms`
            reads as the COBOL's does, one call per paragraph in source order.
    """


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit.`` [common/acas005.cbl:L671-L672].

    ``exit section.`` - the RDB section's single exit. Reproduced as a named no-op for
    the same reason as :func:`ca_exit`: rule R-5 asks that every paragraph have a
    counterpart, and the ``return`` in each caller IS the section exit.
    """


def ba_process_rdbms(
    file_access: FileAccess,
    system_record: SystemRecord,
    dal_common: AcasDalCommonData,
    ledger: WsLedgerRecord,
    *,
    session: BridgeSession | None = None,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas005.cbl:L586-L672].

    ba010-Test-WS-Rec-Size set the RDB log file number [:L594] ba012-Test-WS-Rec-Size-2
    length guard + first-call credentials [:L602] ba015-Test-Ends entirely commented out
    [:L644] ba020-Process-DAL call "nominalMT" [:L662] ba-rdbms-exit exit section
    [:L671].

    Args:
        file_access: ``File-Access``, carrying the verb and receiving the status.
        system_record: ``System-Record``, the source of the connection parameters.
        dal_common: ``ACAS-DAL-Common-data``, the switches and the log counter.
        ledger: ``WS-Ledger-Record``, the record buffer.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.system_record = system_record
    state.dal_common = dal_common
    # ANOMALY N-SECTION-CASE - REPRODUCTION SITE (second of the pair). This function is
    # the section header spelled lower-case `ba-Process-RDBMS section.`
    # [common/acas005.cbl:L586], against the capitalised `aa-Process-Flat-File Section.`
    # [common/acas005.cbl:L277].
    ba010_test_ws_rec_size(file_access)
    if not ba012_test_ws_rec_size_2(file_access, system_record, dal_common):
        ba_rdbms_exit()
        return
    ba015_test_ends(file_access)
    ba020_process_dal(
        file_access, dal_common, ledger, system_record=system_record, session=state
    )
    ba_rdbms_exit()


#: ``move 255 to WE-Error`` - the code the flat-file paragraphs pair with ``FS-Reply``
#: 21 on an invalid key [common/acas005.cbl:L478, :L503, :L510, :L517, :L524].
_WE_ERROR_INVALID_KEY: Final[int] = 255

_FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35


#: THE STATUS DISPOSITIONS OF THE UNMIGRATED ISAM BRANCHES, recorded as data.
FLAT_FILE_STATUSES: Final[Mapping[str, tuple[tuple[str, int | None, int | None, str], ...]]] = (
    MappingProxyType(
        {
            "aa020-Process-Open": (
                (
                    "fn-input, open failed",
                    _FS_REPLY_OPEN_INPUT_FAILED,
                    None,
                    "[common/acas005.cbl:L371]",
                ),
                (
                    "fn-extend, always refused",
                    FsReply.ERROR,
                    WeError.ACCESS_TYPE_WRONG,
                    "[common/acas005.cbl:L390-L391]",
                ),
                (
                    "common tail, any non-zero fs-reply",
                    None,
                    WeError.NOT_USED,
                    "[common/acas005.cbl:L397-L399]",
                ),
            ),
            "aa040-Process-Read-Next": (
                (
                    "already at end of file",
                    FsReply.END_OF_FILE,
                    int(FsReply.END_OF_FILE),
                    "[common/acas005.cbl:L424-L425]",
                ),
            ),
            "aa041-Reread": (
                (
                    "at end",
                    FsReply.END_OF_FILE,
                    int(FsReply.END_OF_FILE),
                    "[common/acas005.cbl:L435]",
                ),
                (
                    "success, We-Error only",
                    None,
                    WeError.SUCCESS,
                    "[common/acas005.cbl:L446]",
                ),
            ),
            "aa050-Process-Read-Indexed": (
                (
                    "invalid key",
                    FsReply.INVALID_KEY_ON_START,
                    _WE_ERROR_INVALID_KEY,
                    "[common/acas005.cbl:L477-L478]",
                ),
            ),
            "aa060-Process-Start": (
                (
                    "access-type < 5 or > 8, FS-Reply UNTOUCHED",
                    None,
                    WeError.FILE_KEY_NO_OUT_OF_RANGE,
                    "[common/acas005.cbl:L496]",
                ),
                (
                    "invalid key, all four relations",
                    FsReply.INVALID_KEY_ON_START,
                    _WE_ERROR_INVALID_KEY,
                    "[common/acas005.cbl:L502-L503, :L509-L510, :L516-L517, :L523-L524]",
                ),
            ),
            "aa070-Process-Write": (
                (
                    "invalid key, We-Error UNTOUCHED",
                    FsReply.DUPLICATE_KEY,
                    None,
                    "[common/acas005.cbl:L541]",
                ),
            ),
            "aa080-Process-Delete": (
                (
                    # `move 21 to FS-Reply` [:L553] - the DELETE uses 21 where the WRITE
                    # four paragraphs above uses 22. Both are reproduced.
                    "invalid key, We-Error UNTOUCHED",
                    FsReply.INVALID_KEY_ON_START,
                    None,
                    "[common/acas005.cbl:L553]",
                ),
            ),
            "aa090-Process-Rewrite": (
                (
                    "NO invalid-key clause exists, so nothing is written",
                    None,
                    None,
                    "[common/acas005.cbl:L563]",
                ),
            ),
        }
    )
)


def aa020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData | None = None
) -> None:
    """``aa020-Process-Open.`` [common/acas005.cbl:L365-L400].

    if fn-extend *> Must not be used for ISAM files *> open extend Ledger-File move 997
    to WE-Error [:L390] move 99 to FS-Reply [:L391] go to aa999-main-exit [:L392] end-
    if.

    Args:
        file_access: The block supplying ``Access-Type`` and receiving the status.
        dal_common: The handler's fifth linkage parameter, forwarded to
            :func:`aa999_main_exit` for the ``Testing-1`` log gate.

    Raises:
        CobolFileAccessNotMigratedError: For ``fn-input``, ``fn-i-o`` and ``fn-output``,
            which need an ISAM engine this package does not ship.
    """
    _set_file_key(file_access, "")
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.OPEN
    access_type = file_access.access_type
    if access_type == AccessType.EXTEND:
        file_access.we_error = WeError.ACCESS_TYPE_WRONG
        file_access.fs_reply = FsReply.ERROR
        aa999_main_exit(file_access, dal_common)
        return
    raise CobolFileAccessNotMigratedError(FileFunction.OPEN, access_type=access_type)


def aa030_process_close(file_access: FileAccess) -> None:
    """``aa030-Process-Close.`` [common/acas005.cbl:L402-L412].

    The double log is deliberate: [:L409] is a ``PERFORM``, so it logs the close and
    RETURNS, and then the verb and access type are zeroed and it logs AGAIN.

    Args:
        file_access: The block receiving the tag and the log records.

    Raises:
        CobolFileAccessNotMigratedError: The ``close`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.CLOSE
    _set_file_key(file_access, "")
    raise CobolFileAccessNotMigratedError(FileFunction.CLOSE)


def aa040_process_read_next(file_access: FileAccess) -> None:
    """``aa040-Process-Read-Next.`` [common/acas005.cbl:L415-L430].

    The positioning guard for the flat-file read, whose own header says it "is
    processed after Start code as its really Start/Read next at point aa041"
    [:L419-L420]::

        move     203 to WS-No-Paragraph.                               [:L422]
        if       Cobol-File-Eof          *> This block should NOT occur [:L423]
                 move 10 to FS-Reply WE-Error                          [:L424-L425]
                 move spaces to WS-Ledger-Key SQL-Err SQL-Msg          [:L426-L428]
                 stop "Cobol File EOF"                                 [:L429]
                 go to aa999-main-exit                                 [:L430]
        end-if.

    Two things to note. The guard's own comment says it "should NOT occur", and the
    ``stop`` literal carries "for testing because it should not have got here !!" -
    a ``STOP`` with a literal HALTS THE RUN until the operator acknowledges, which is
    a behaviour no batch migration can keep; it has no database effect, so per Agent
    Action Plan 0.3.4 it becomes a log record while the control transfer that follows
    it is preserved. And ``move spaces to WS-Ledger-Key`` writes SPACES into a
    ``9(6)``/``9(2)`` numeric group, leaving it non-numeric - which is exactly the
    condition ``gl072`` silently skips on [general/gl072.cbl:L291-L292] - the
    statement the anomaly register cites as [general/gl072.cbl:L289-L290], which in
    the frozen checkout is the ``go to end-run`` of the at-end clause.

    Falls through into :func:`aa041_reread` when not at end of file.

    * GO TO CLASS 3 at [:L430].

    Args:
        file_access: The block receiving the status.

    Raises:
        CobolFileAccessNotMigratedError: The read is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.READ_NEXT
    raise CobolFileAccessNotMigratedError(FileFunction.READ_NEXT)


def aa041_reread(file_access: FileAccess) -> None:
    """``aa041-Reread.`` [common/acas005.cbl:L433-L448].

    Note the ``initialize WS-Ledger-Record`` at [:L438] is the PLAIN form, so it leaves
    the 55 filler bytes alone - see :func:`_initialize_ws_ledger_record` for the oracle
    evidence. The bridge's own EOF2 branch uses ``WITH FILLER`` instead
    [common/nominalMT.cbl:L575].

    Args:
        file_access: The block receiving the status.

    Raises:
        CobolFileAccessNotMigratedError: The read is an ISAM verb.
    """
    raise CobolFileAccessNotMigratedError(FileFunction.READ_NEXT)


def aa047_eval_keys(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa047-Eval-Keys.`` [common/acas005.cbl:L451-L466].

    Its heading, verbatim [:L449]: "The next block will never get executed unless
    performed". That is accurate rather than an admission of dead code.

    Args:
        file_access: The block whose ``WS-File-Key`` is set.
        ledger: The record supplying ``WS-Ledger-Key``.
    """
    function = file_access.file_function
    guarded = (
        FileFunction.READ_INDEXED,
        FileFunction.WRITE,
        FileFunction.RE_WRITE,
        FileFunction.DELETE,
        FileFunction.START,
    )
    if function in guarded:
        if file_access.logging_data.file_key_no == FILE_KEY_NO:
            _set_file_key(file_access, ws_ledger_key_bytes(ledger))
        else:
            _set_file_key(file_access, "")
        return
    _set_file_key(file_access, "")


def aa050_process_read_indexed(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas005.cbl:L469-L483].

    Note the commented-out ``*> we-error`` fragment on [:L477] and the odd indentation
    of the ``move 255`` on [:L478] - the maintainer added the second statement later.

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key.

    Raises:
        CobolFileAccessNotMigratedError: The read is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.READ_INDEXED
    aa047_eval_keys(file_access, ledger)
    raise CobolFileAccessNotMigratedError(FileFunction.READ_INDEXED)


def aa060_process_start(
    file_access: FileAccess,
    ledger: WsLedgerRecord,
    dal_common: AcasDalCommonData | None = None,
) -> None:
    """``aa060-Process-Start.`` [common/acas005.cbl:L485-L531].

    Two facts about it are easy to get wrong and both are reproduced.

    Args:
        file_access: The block supplying ``Access-Type`` and receiving the status.
        ledger: The record supplying the key.
        dal_common: The handler's fifth linkage parameter, forwarded to
            :func:`aa999_main_exit` for the ``Testing-1`` log gate.

    Raises:
        CobolFileAccessNotMigratedError: When the access type passes the guard, since
            the ``start`` itself is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.START
    aa047_eval_keys(file_access, ledger)
    # `move zeros to fs-reply WE-Error.` [:L492-L493] - BEFORE the guard, which is what
    # makes the guard's disposition (0, 998).
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    low, high = START_ACCESS_TYPE_RANGE
    if file_access.access_type < low or file_access.access_type > high:
        # `move 998 to WE-Error` [:L496] - and FS-Reply deliberately NOT touched.
        file_access.we_error = WeError.FILE_KEY_NO_OUT_OF_RANGE
        aa999_main_exit(file_access, dal_common)
        return
    raise CobolFileAccessNotMigratedError(
        FileFunction.START, access_type=file_access.access_type
    )


def aa070_process_write(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa070-Process-Write.`` [common/acas005.cbl:L534-L544].

    Note ``WS-File-Key`` is set TWICE, from two different sources - the FD ``Ledger-
    Key`` before the write and the working-storage ``WS-Ledger-Key`` after - so the tag
    that reaches the log is always the second.

    Args:
        file_access: The block receiving the status.
        ledger: The record to write.

    Raises:
        CobolFileAccessNotMigratedError: The ``write`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.WRITE
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    _set_file_key(file_access, ws_ledger_key_bytes(ledger))
    raise CobolFileAccessNotMigratedError(FileFunction.WRITE)


def aa080_process_delete(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa080-Process-Delete.`` [common/acas005.cbl:L546-L555].

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key.

    Raises:
        CobolFileAccessNotMigratedError: The ``delete`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.DELETE
    _set_file_key(file_access, ws_ledger_key_bytes(ledger))
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    raise CobolFileAccessNotMigratedError(FileFunction.DELETE)


def aa090_process_rewrite(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa090-Process-Rewrite.`` [common/acas005.cbl:L557-L565].

    THE ``rewrite`` HAS NO ``invalid key`` CLAUSE - alone among the four write verbs in
    this handler.

    Args:
        file_access: The block receiving the status.
        ledger: The record to re-write.

    Raises:
        CobolFileAccessNotMigratedError: The ``rewrite`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.RE_WRITE
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    raise CobolFileAccessNotMigratedError(FileFunction.RE_WRITE)


def aa100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData | None = None
) -> None:
    """``aa100-Bad-Function.`` [common/acas005.cbl:L567-L572].

    ``999`` - NOT the ``990`` its counterpart ``ba100-Bad-Function`` uses
    [common/nominalMT.cbl:L922].

    Args:
        file_access: The block receiving ``(99, 999)``.
        dal_common: The handler's fifth linkage parameter, forwarded to
            :func:`aa999_main_exit` for the ``Testing-1`` log gate.
    """
    file_access.we_error = WeError.NOT_USED
    file_access.fs_reply = FsReply.ERROR
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData | None = None
) -> None:
    """``aa999-main-exit.`` [common/acas005.cbl:L574-L577].

    Args:
        file_access: The block whose ``Logging-Data`` is written out.
        dal_common: The handler's FIFTH linkage parameter [common/acas005.cbl:L274],
            supplying ``SW-Testing``. ``None`` means the caller passed no block, in
            which case ``Testing-1`` cannot be true and nothing is logged.
    """
    if dal_common is not None and dal_common.sw_testing == _TESTING_1:
        ca_process_logs(file_access, dal_common)


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas005.cbl:L579-L582].

    Reproduced as a named no-op because rule R-5 asks for one function per paragraph,
    and because it IS a real branch target - ``aa010-main`` jumps to it on the RDB path
    [common/acas005.cbl:L319] and ``aa030-Process-Close`` on the close path.
    """


def aa_exit() -> None:
    """``aa-Exit.`` [common/acas005.cbl:L583-L584].

    ``exit program.`` - the return to the caller of ``acas005``. The ``return`` at the
    end of :func:`dispatch` IS this statement; the function exists so a reader following
    the COBOL finds it.
    """


#: The dispatch table of ``aa010-main``'s ``evaluate File-Function``
#: [common/acas005.cbl:L340-L361], IN THE FROZEN SOURCE'S OWN ARM ORDER.
DISPATCH_ORDER: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,
    FileFunction.CLOSE,
    FileFunction.READ_NEXT,
    FileFunction.READ_INDEXED,
    FileFunction.WRITE,
    FileFunction.RE_WRITE,
    FileFunction.DELETE,
    FileFunction.START,
)


def aa_process_flat_file(
    system: SystemRecord,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas005.cbl:L277].

    The FIRST section of the procedure division, so entering the program enters this
    section, which falls straight into :func:`aa010_main` at [common/acas005.cbl:L279].

    Args:
        system: ``System-Record`` [common/acas005.cbl:L268].
        ledger: ``WS-Ledger-Record`` [common/acas005.cbl:L270].
        file_access: ``File-Access`` [common/acas005.cbl:L272].
        file_defs: ``File-Defs`` [common/acas005.cbl:L273].
        dal_common: ``ACAS-DAL-Common-data`` [common/acas005.cbl:L274].
    """
    # ANOMALY N-SECTION-CASE - REPRODUCTION SITE.
    aa010_main(system, ledger, file_access, file_defs, dal_common)


def aa010_main(
    system: SystemRecord,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa010-main.`` [common/acas005.cbl:L279-L363].

    The handler's body, in the frozen source's statement order. Every step below is the
    COBOL's, in the COBOL's sequence, and the sequence matters because two of the steps
    are SKIPPED on the RDB path by an early jump.

    Args:
        system: ``System-Record`` [:L268] - the connection parameters.
        ledger: ``WS-Ledger-Record`` [:L270] - the record being read or written.
        file_access: ``File-Access`` [:L272] - the verb in, the status out.
        file_defs: ``File-Defs`` [:L273] - the file-name block.
        dal_common: ``ACAS-DAL-Common-data`` [:L274] - the testing switches.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_system = WS_LOG_SYSTEM
    # ANOMALY N-LOG, first half. `move 11 to WS-Log-File-No.` [common/acas005.cbl:L284].
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_COBOL

    # THE KEY GUARD [common/acas005.cbl:L288-L302]. Covers read-indexed (4), start (9)
    # and delete (8) - NOT write (5) and NOT re-write (7).
    guard = KEY_GUARDED_FUNCTIONS.get(file_access.file_function)
    if guard is not None and logging_data.file_key_no != FILE_KEY_NO:
        fs_reply, we_error, locator = guard
        # The COBOL writes We-Error FIRST then fs-reply, at all three sites - `move 998
        # to WE-Error` / `move 99 to fs-reply` [:L292-L293] and `move 996 to WE-Error` /
        # `move 99 to fs-reply` [:L298-L299].
        file_access.we_error = we_error
        file_access.fs_reply = fs_reply
        log_handler_failure(
            _LOG,
            program=HANDLER_NAME,
            paragraph="aa000-Main-Process key guard",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="File-Key-No %d is not %d for %s"
            % (
                logging_data.file_key_no,
                FILE_KEY_NO,
                FileFunction(file_access.file_function).name,
            ),
        )
        aa999_main_exit(file_access, dal_common)
        return

    # ANOMALY N-DEADCODE. The open-output-becomes-delete-all coercion sits here in
    # `acas008` and is LIVE there [common/acas008.cbl:L313-L319].

    if not _is_cobol_files_used(system):
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses.` [:L317], under the
        # maintainer's note "needed for DAL? not JC/dbpre versions" - so he was not
        # certain it was needed either.
        source = system.system_data_block.rdbms_flat_statuses
        target = file_access.fa_rdbms_flat_statuses
        target.fa_file_system_used = source.file_system_used
        target.fa_file_duplicates_in_use = source.file_duplicates_in_use
        ba_process_rdbms(file_access, system, dal_common, ledger)
        aa_main_exit()
        return

    # `perform ba012-Test-WS-Rec-Size-2.` [:L327]. Cobol path only. Shared with the RDB
    # path's own caller [:L602].
    if not ba012_test_ws_rec_size_2(file_access, system, dal_common):
        # The record-length guard inside `ba012` ends `go to ba-rdbms-exit` [:L621]
        # having written (99, 901); on this path that lands back here. GO TO CLASS 3.
        aa999_main_exit(file_access, dal_common)
        return

    # `move spaces to SQL-Err SQL-Msg SQL-State.` [:L339]. COBOL PATH ONLY - see the
    # docstring.
    logging_data.sql_err = ""
    logging_data.sql_msg = ""
    logging_data.sql_state = ""

    function = file_access.file_function
    for arm in DISPATCH_ORDER:
        if function != arm:
            continue
        if arm == FileFunction.OPEN:
            aa020_process_open(file_access, dal_common)
        elif arm == FileFunction.CLOSE:
            aa030_process_close(file_access)
            aa_main_exit()
        elif arm == FileFunction.READ_NEXT:
            aa040_process_read_next(file_access)
        elif arm == FileFunction.READ_INDEXED:
            aa050_process_read_indexed(file_access, ledger)
        elif arm == FileFunction.WRITE:
            aa070_process_write(file_access, ledger)
        elif arm == FileFunction.RE_WRITE:
            aa090_process_rewrite(file_access, ledger)
        elif arm == FileFunction.DELETE:
            aa080_process_delete(file_access, ledger)
        else:
            aa060_process_start(file_access, ledger, dal_common)
        return

    aa100_bad_function(file_access, dal_common)
    # `go to aa100-Bad-Function.` [:L363] - the unconditional fall-through under "Should
    # never get here but in case :(" [:L362].
    return


#: ``88 FS-Cobol-Files-Used value zero.`` [copybooks/wssystem.cob:L113]. ZERO, NOT ONE -
#: and the RDBMS is the ``1`` [copybooks/wssystem.cob:L116].
_FS_COBOL_FILES_USED: Final[int] = 0


def _is_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - the store selector [copybooks/wssystem.cob:L111-L118].

    * IT LIVES IN ``System-Record``, NOT in ``File-Access``. ``File-Access`` has a
    SEPARATE copy, ``FA-RDBMS-Flat-Statuses`` [copybooks/wsfnctn.cob:L72-L82], annotated
    "Comes from System-Record via acas0nn" - and it is THIS handler that does the
    copying, at [common/acas005.cbl:L317].

    Args:
        system: ``System-Record`` - the handler's FIRST linkage parameter
            [common/acas005.cbl:L268].

    Returns:
        ``True`` when the run is using GnuCOBOL indexed files, ``False`` when it is
            using the RDBMS.
    """
    # `03 System-Data-Block.` [copybooks/wssystem.cob:L52] encloses the `05` group
    # [:L111], so the group name is part of the path - `System-Record` is 169 columns
    # across seven such blocks and the record module keeps every one of them.
    return (
        system.system_data_block.rdbms_flat_statuses.file_system_used
        == _FS_COBOL_FILES_USED
    )


def dispatch(
    system: SystemRecord,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``call "acas005" using ...`` - THE HANDLER ENTRY POINT.

    THIS IS THE CANONICAL FIVE-PARAMETER HANDLER SHAPE. Sixteen sibling handlers share
    it; ``acas005`` is simply the one that carries no per-table peculiarity in its
    linkage, which is why it is the reference.

    Args:
        system: ``System-Record`` - supplies ``RDB-Data``'s credentials by way of
            :func:`connection.load_rdb_data_once`.
        ledger: ``WS-Ledger-Record`` - the record read into or written from. Mutated in
            place on every read, exactly as the COBOL's linkage is.
        file_access: ``File-Access`` - carries ``File-Function`` and ``Access-Type`` in,
            and ``FS-Reply``, ``We-Error`` and the whole of ``Logging-Data`` out.
            Mutated in place.
        file_defs: ``File-Defs`` - accepted to honour the linkage and never read.
        dal_common: ``ACAS-DAL-Common-data`` - ``SW-Testing`` and ``SW-Testing-2``, the
            two logging switches.

    Raises:
        CobolFileAccessNotMigratedError: When ``RDB-Data`` selects GnuCOBOL indexed
            files rather than the RDBMS and the verb needs a real ISAM engine. Rule R-1
            forbids this package from carrying one.
        AcasFileHandlerError: Propagated from the bridge for a database failure the
            frozen source reports through ``FS-Reply``/``We-Error``.
    """
    aa_process_flat_file(system, ledger, file_access, file_defs, dal_common)
    aa_exit()
