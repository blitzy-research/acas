"""`acas022` and its bridge `purchMT` - the `PULEDGER-REC` purchase ledger.

The data-access module for the Purch entity: one supplier account per row,
primary key `PURCH-KEY`.

TWELVE SIGNS ARE LOST HERE, AND THE LOSS IS REPRODUCED. The statistics and date
fields are declared signed in the copybook and UNSIGNED at both the bridge host
variable and the column, so a negative value loses its sign at the bridge, before
any SQL executes. This module performs that conversion rather than writing the
computed value and letting the database complain, because the stored value is what
a state comparison sees. The monetary fields are signed at all three layers and
pass through cleanly.

The by-name read path is the twin of the keyed one and differs from it in exactly
three respects, each reproduced - including the end-of-file behaviour that leaves
the cursor set, so a following read continues rather than restarting.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from decimal import ROUND_DOWN, Decimal
from typing import Final, Protocol, runtime_checkable

from acas_posting.dal.connection import (
    TransportSecurity,
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
    TABLE_PRIMARY_KEYS,
    CursorSlot,
    CursorState,
    CursorStateTable,
    ExtraReadOrder,
    KeyOfReference,
    MostRelation,
    key_of_reference,
)
from acas_posting.dal.status import (
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    log_cobol_stop,
    log_file_handler_record,
    mysql_1100_db_error,
    redact_for_log,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.purchase_ledger import (
    BRIDGE,
    COPYBOOK,
    HANDLER,
    TABLE,
    WsPurchRecord,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "BRIDGE",
    "BRIDGE_PARAGRAPH_NUMBERS",
    "BRIDGE_PROG_NAME",
    "CHARACTER_HOST_VARIABLE_WIDTHS",
    "COLUMN_ORDER",
    "COPYBOOK",
    "EDIT_PICTURE",
    "EDIT_WINDOWS",
    "HANDLER",
    "HANDLER_PARAGRAPH_NUMBERS",
    "HV_LOAD_ORDER",
    "HV_UNLOAD_ORDER",
    "KEY_OF_REFERENCE",
    "MONEY_COLUMNS",
    "NAME_ORDER",
    "OMITTED_COPYBOOK_FIELDS",
    "ONLY_KEY_NUMBER",
    "PRIMARY_KEY_COLUMN",
    "PROG_NAME",
    "SIGN_LOSS_COLUMNS",
    "SUPPORTED_FUNCTIONS",
    "TABLE",
    "WS_FILE_KEY_WIDTH",
    "WS_LOG_FILE_NO_COBOL",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "HostVariables",
    "PurchaseFile",
    "PurchaseFileNotSuppliedError",
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
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "ca_exit",
    "ca_process_logs",
    "dispatch",
    "purch_mt",
    "purchmt_ba010_initialise",
    "purchmt_ba020_process_open",
    "purchmt_ba030_process_close",
    "purchmt_ba040_process_read_next",
    "purchmt_ba041_reread",
    "purchmt_ba050_process_read_indexed",
    "purchmt_ba060_process_start",
    "purchmt_ba070_process_write",
    "purchmt_ba080_process_delete",
    "purchmt_ba090_process_rewrite",
    "purchmt_ba100_bad_function",
    "purchmt_ba140_process_read_next",
    "purchmt_ba141_reread",
    "purchmt_ba998_free",
    "purchmt_ba999_end",
    "purchmt_ba999_exit",
    "purchmt_ba_acas_dal_process",
    "purchmt_ca_exit",
    "purchmt_ca_process_logs",
    "reset_bridge_state",
)

_LOG: Final = logging.getLogger(__name__)


PROG_NAME: Final[str] = "acas022 (3.3.00)"

BRIDGE_PROG_NAME: Final[str] = "purchMT (3.3.00)"

#: ``move 4 to WS-Log-System`` [common/acas022.cbl:L293]. ANOMALY
#: ``N-logsystem5-meaning``.
WS_LOG_SYSTEM: Final[int] = int(LogSystem.PL)

#: ``move 11 to WS-Log-File-No`` [common/acas022.cbl:L294] - the Cobol-files value,
#: recorded but never reported by this module.
WS_LOG_FILE_NO_COBOL: Final[int] = 11

#: ``move 21 to WS-Log-File-no`` [common/acas022.cbl:L605] - the RDB value, which
#: overwrites the 11 above on the only path this module takes. ANOMALY ``N-log``.
WS_LOG_FILE_NO_RDB: Final[int] = 21

#: ``WS-File-Key pic x(64)`` [copybooks/wsfnctn.cob:L52]. Every log literal this module
#: writes is truncated to this width exactly as a COBOL ``MOVE`` would.
WS_FILE_KEY_WIDTH: Final[int] = 64

#: The handler's ``WS-No-Paragraph`` stamps, one per paragraph that sets one. ANOMALY
#: ``N-noparagraph-collision``: 201..208 is byte-for-byte the scheme used by
#: ``acas013``, ``acas015``, ``acas016`` and ``acas019`` as well.
HANDLER_PARAGRAPH_NUMBERS: Final[Mapping[str, int]] = {
    "aa020-Process-Open": 201,
    "aa030-Process-Close": 202,
    "aa040-Process-Read-Next": 203,
    "aa050-Process-Read-Indexed": 204,
    "aa060-Process-Start": 205,
    "aa070-Process-Write": 206,
    "aa080-Process-Delete": 207,
    "aa090-Process-Rewrite": 208,
}

#: The bridge's ``ws-No-Paragraph`` stamps.
BRIDGE_PARAGRAPH_NUMBERS: Final[Mapping[str, int]] = {
    "ba020-Process-Open": 1,
    "ba030-Process-Close": 2,
    "ba040-Process-Read-Next": 3,
    "ba041-Reread": 4,
    "ba050-Process-Read-Indexed-select": 5,
    "ba050-Process-Read-Indexed-fetch": 6,
    "ba060-Process-Start": 8,
    "ba070-Process-Write": 10,
    "ba080-Process-Delete": 13,
    "ba090-Process-Rewrite": 17,
    "ba998-Free": 19,
    "ba140-Process-Read-Next": 21,
    "ba141-Reread": 22,
}

#: The nine function codes the handler's ``evaluate`` admits
#: [common/acas022.cbl:L338-L358]. Codes 32, 33 and 34 are absent because this handler
#: does not dispatch them - see ``N-codes-32-33-dead``.
SUPPORTED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.OPEN),
        int(FileFunction.CLOSE),
        int(FileFunction.READ_NEXT),
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
        int(FileFunction.READ_BY_NAME),
    }
)

#: The verbs whose key guard runs before dispatch [common/acas022.cbl:L298-L312]. ``fn-
#: read-indexed`` and ``fn-start`` share the 998 arm; ``fn-delete`` has its own 996 arm.
_KEY_GUARD_998_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {int(FileFunction.READ_INDEXED), int(FileFunction.START)}
)
_KEY_GUARD_996_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {int(FileFunction.DELETE)}
)

#: The only key number either program admits, enforced by the guard above.
ONLY_KEY_NUMBER: Final[int] = 1


#: The ONE key of reference this table declares [common/purchMT.scb:L228-L230] and
#: [common/purchMT.cbl:L227-L237]: ``'PURCH-KEY'``, offset ``0001``, length ``0007``,
#: type ``'STR'``.
KEY_OF_REFERENCE: Final[KeyOfReference] = key_of_reference(TABLE, ONLY_KEY_NUMBER)

#: ``03 keyOfReference occurs 1`` [common/purchMT.cbl:L232] - the OCCURS count is 1, and
#: everything about ``File-Key-No`` follows from it.
if len(TABLE_OF_KEYNAMES[TABLE]) != ONLY_KEY_NUMBER:  # pragma: no cover
    raise LookupError(
        f"{TABLE} declares {len(TABLE_OF_KEYNAMES[TABLE])} keys of reference; "
        f"[common/purchMT.cbl:L232] declares `occurs 1`"
    )

PRIMARY_KEY_COLUMN: Final[str] = TABLE_PRIMARY_KEYS[TABLE]

#: ``ba040``'s hard-coded self-positioning relation and low key
#: [common/purchMT.cbl:L521-L522], held as data by ``dal/cursor_state.py`` so that the
#: per-bridge disagreement survives as data rather than as code.
_SEQUENTIAL_START: Final = SEQUENTIAL_READ_START[TABLE]

NAME_ORDER: Final[ExtraReadOrder] = EXTRA_READ_ORDERS[TABLE][
    FileFunction.READ_BY_NAME
]

#: ``ba140`` writes its low key UNQUOTED - ``"0000000"`` is a COBOL literal delimited by
#: ``"``, so the token that reaches the statement text is the bare ``0000000``
#: [common/purchMT.cbl:L1030].
_NAME_ORDER_LOW_KEY: Final[str] = "0000000"

#: ``01 DAL-Data.`` declares TWO cursor flags [common/purchMT.cbl:L244-L254].
_KEY_ORDER_SLOT: Final[CursorSlot] = CursorSlot.PRIMARY
_NAME_ORDER_SLOT: Final[CursorSlot] = CursorSlot.SECONDARY

#: ANOMALY ``N-single-result-pointer-two-cursors``. There are TWO cursor flags but only
#: ONE result pointer: ``01 TP-PULEDGER-REC USAGE POINTER`` [common/purchMT.cbl:L283].
_RESULT_POINTER: Final[CursorState] = CursorState(
    table_name=TABLE, slot=_KEY_ORDER_SLOT
)

#: The relation each ``Access-Type`` selects [common/purchMT.cbl:L800-L811].
_START_RELATIONS: Final[Mapping[int, str]] = {
    int(AccessType.EQUAL_TO): "=  ",
    int(AccessType.LESS_THAN): "<  ",
    int(AccessType.GREATER_THAN): ">  ",
    int(AccessType.NOT_LESS_THAN): ">= ",
    int(AccessType.NOT_GREATER_THAN): "<= ",
}


@dataclasses.dataclass(frozen=True, slots=True)
class _ColumnBinding:
    """One column's complete transfer contract, derived from the dictionary.

    Attributes:
        column: The MySQL column name, hyphens included.
        ordinal: Its 1-based position in ``mysql/ACASDB.sql``.
        attribute: The dotted path to the value on :class:`WsPurchRecord`.
        host_variable: The ``HV-`` name, which is also the attribute name on
            :class:`HostVariables` in lower case with hyphens as underscores.
        kind: ``"char"``, ``"int"`` or ``"decimal"`` - the host variable's own storage
            class, NOT the copybook's.
        digits: The host variable's total digit count; zero for character fields.
        scale: The host variable's fraction digit count.
        width: The host variable's character length; zero for numeric fields.
        signed: Whether the HOST VARIABLE is signed. Twelve of these are False where the
            copybook field is signed - that is ``N-signloss-twelve``.
        copybook_signed: Whether the COPYBOOK field is signed, so the loss is visible in
            the data rather than only in prose.
        copybook_usage: The copybook field's usage - ``ALPHANUMERIC``, ``DISPLAY``,
            ``COMP``, ``COMP-3``, ``BINARY-CHAR``, ``BINARY-LONG`` or ``GROUP``.
        copybook_digits: The copybook field's digit count, or zero where it has no
            picture clause.
        copybook_scale: The copybook field's fraction digits.
        copybook_width: The copybook field's character length, zero for numerics.
        edit_start: 1-based start of the window sliced out of ``WS-MYSQL-EDIT``; zero
            for character fields, which are trimmed instead.
        edit_length: That window's length.
        citation: ``loader.cite(key)`` - the copybook, bridge and column locators for
            this field, in one string.
        drift_details: ``loader.drift_for(key).details``, empty when the four views
            agree.
    """

    column: str
    ordinal: int
    attribute: str
    host_variable: str
    kind: str
    digits: int
    scale: int
    width: int
    signed: bool
    copybook_signed: bool
    copybook_usage: str
    copybook_digits: int
    copybook_scale: int
    copybook_width: int
    edit_start: int
    edit_length: int
    citation: str
    drift_details: str

    @property
    def field(self) -> str:
        """The :class:`HostVariables` attribute name for this column."""
        return self.host_variable.lower().replace("-", "_")

    @property
    def sign_lost_at_bridge(self) -> bool:
        """True when the copybook signs the field and the host variable does not.

        This is the predicate that selects the twelve fields of ``N-signloss-twelve`` -
        computed from the dictionary rather than from a hand-written list, so a
        dictionary regeneration cannot silently drop one.
        """
        return self.copybook_signed and not self.signed


#: Where each column's value comes from on :class:`WsPurchRecord`, and the edit window
#: the bridge slices for it.
_RECORD_ATTRIBUTES: Final[Mapping[str, str]] = {
    "PURCH-KEY": "ws_purch_key",
    "PURCH-STATUS": "purch_status",
    "PURCH-NOTES-TAG": "purch_notes_tag",
    "PURCH-NAME": "purch_name",
    "PURCH-ADDRESS": "purch_address",
    "PURCH-PHONE": "purch_phone",
    "PURCH-EXT": "purch_ext",
    "PURCH-FAX": "purch_fax",
    "PURCH-EMAIL": "purch_email",
    "PURCH-DISCOUNT": "purch_discount",
    "PURCH-CREDIT": "purch_credit",
    "PURCH-SORTCODE": "purch_sortcode",
    "PURCH-ACCOUNTNO": "purch_accountno",
    "PURCH-LIMIT": "purch_limit",
    "PURCH-ACTIVETY": "purch_activety",
    "PURCH-LAST-INV": "purch_last_inv",
    "PURCH-LAST-PAY": "purch_last_pay",
    "PURCH-AVERAGE": "purch_average",
    "PURCH-CREATE-DAT": "purch_create_date",
    "PURCH-PAY-ACTIVETY": "purch_pay_activety",
    "PURCH-PAY-AVERAGE": "purch_pay_average",
    "PURCH-PAY-WORST": "purch_pay_worst",
    "PURCH-CURRENT": "purch_current",
    "PURCH-LAST": "purch_last",
    "TURNOVER-Q1": "quarters.turnover_q1",
    "TURNOVER-Q2": "quarters.turnover_q2",
    "TURNOVER-Q3": "quarters.turnover_q3",
    "TURNOVER-Q4": "quarters.turnover_q4",
    "PURCH-UNAPPLIED": "purch_unapplied",
}

#: The five windows sliced out of ``WS-MYSQL-EDIT``, as ``(start, length)`` pairs keyed
#: by the host variable's declared integer-digit count.
_INTEGER_WINDOW_BY_DIGITS: Final[Mapping[int, tuple[int, int]]] = {
    2: (19, 2),
    3: (18, 3),
    8: (13, 8),
    10: (11, 10),
}

_FRACTION_WINDOW: Final[tuple[int, int]] = (22, 2)


def _dictionary_bindings() -> tuple[_ColumnBinding, ...]:
    """Build the 29 column bindings from ``loader``, in COLUMN-ORDINAL order.

    Rule R-5's field-level traceability is mechanised here rather than hand-maintained.

    Returns:
        The bindings, ordered by ``column.ordinal`` so that the tuple IS the table's
            column order and every later ordering can be derived from it.

    Raises:
        LookupError: If the dictionary does not describe exactly the 29 columns the
            frozen schema declares, or names one this module has no record attribute
            for.
    """
    entries = loader.entries_for_table(TABLE)
    if len(entries) != _EXPECTED_COLUMN_COUNT:
        raise LookupError(
            f"{TABLE} is declared with {_EXPECTED_COLUMN_COUNT} columns in "
            f"mysql/ACASDB.sql:L646-L677 but the data dictionary describes "
            f"{len(entries)}; regenerate data_dictionary/"
            f"acas_posting_dictionary.json before using this module."
        )
    bindings: list[_ColumnBinding] = []
    for entry in sorted(entries, key=lambda item: item.column.ordinal):
        column = entry.column.name
        attribute = _RECORD_ATTRIBUTES.get(column)
        if attribute is None:
            raise LookupError(
                f"the data dictionary names column {column} for {TABLE}, which "
                f"acas_posting/records/purchase_ledger.py does not carry; the "
                f"record module and copybooks/wspl.cob must be reconciled "
                f"before this module can transfer it."
            )
        host_variable = entry.bridge_host_variable
        drift = loader.drift_for(entry.key)
        if host_variable.usage == "ALPHANUMERIC":
            kind = "char"
            edit_start, edit_length = 0, 0
        elif host_variable.scale:
            kind = "decimal"
            edit_start, edit_length = _INTEGER_WINDOW_BY_DIGITS[
                host_variable.integer_digits
            ]
        else:
            kind = "int"
            edit_start, edit_length = _INTEGER_WINDOW_BY_DIGITS[
                host_variable.integer_digits
            ]
        copybook = entry.copybook
        bindings.append(
            _ColumnBinding(
                column=column,
                ordinal=entry.column.ordinal,
                attribute=attribute,
                host_variable=host_variable.name,
                kind=kind,
                digits=host_variable.digits or 0,
                scale=host_variable.scale or 0,
                width=host_variable.character_length or 0,
                signed=bool(host_variable.signed),
                copybook_signed=bool(copybook is not None and copybook.signed),
                copybook_usage=(
                    "GROUP" if copybook is None else str(copybook.usage)
                ),
                copybook_digits=(
                    0 if copybook is None else (copybook.digits or 0)
                ),
                copybook_scale=(
                    0 if copybook is None else (copybook.scale or 0)
                ),
                copybook_width=(
                    0 if copybook is None else (copybook.character_length or 0)
                ),
                edit_start=edit_start,
                edit_length=edit_length,
                citation=loader.cite(entry.key),
                drift_details=drift.details or "",
            )
        )
    return tuple(bindings)


#: The C storage width of the two picture-less binary usages the copybook declares.
_BINARY_STORAGE_BYTES: Final[Mapping[str, int]] = {
    "BINARY-CHAR": 1,
    "BINARY-SHORT": 2,
    "BINARY-LONG": 4,
    "BINARY-DOUBLE": 8,
}


_EXPECTED_COLUMN_COUNT: Final[int] = 29

_BINDINGS: Final[tuple[_ColumnBinding, ...]] = _dictionary_bindings()

COLUMN_ORDER: Final[tuple[str, ...]] = tuple(
    binding.column for binding in _BINDINGS
)

HV_LOAD_ORDER: Final[tuple[str, ...]] = COLUMN_ORDER

HV_UNLOAD_ORDER: Final[tuple[str, ...]] = COLUMN_ORDER

# THE SYMMETRY, CHECKED RATHER THAN ASSERTED IN PROSE.
if not (HV_LOAD_ORDER == HV_UNLOAD_ORDER == COLUMN_ORDER):  # pragma: no cover
    raise LookupError(
        "purchMT's load order [common/purchMT.cbl:L1212-L1240], unload order "
        "[common/purchMT.cbl:L1259-L1287] and column order "
        "[mysql/ACASDB.sql:L646-L677] must be the same list"
    )

#: The twelve columns of ``N-signloss-twelve``, selected by the dictionary's own
#: signedness drift rather than by a hand-written list: ``PURCH-CREDIT`` through
#: ``PURCH-PAY-WORST`` [copybooks/wspl.cob:L31-L42] -> [common/purchMT.cbl:L295-L306].
SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = tuple(
    binding.column for binding in _BINDINGS if binding.sign_lost_at_bridge
)

MONEY_COLUMNS: Final[tuple[str, ...]] = tuple(
    binding.column
    for binding in _BINDINGS
    if binding.kind == "decimal" and binding.signed
)

#: Every character column and the width its host variable declares, so that a value
#: shorter than the column is space-padded rather than sent short - the
#: ``initialize``-first invariant of section 3.16.
CHARACTER_HOST_VARIABLE_WIDTHS: Final[Mapping[str, int]] = {
    binding.column: binding.width
    for binding in _BINDINGS
    if binding.kind == "char"
}

#: The window each numeric column is rendered through, for the record and for tests.
#: Character columns are absent because they are trimmed, not windowed.
EDIT_WINDOWS: Final[Mapping[str, tuple[int, int]]] = {
    binding.column: (binding.edit_start, binding.edit_length)
    for binding in _BINDINGS
    if binding.kind != "char"
}

#: Copybook fields that reach the database NOWHERE, recorded as deliberate omissions per
#: rule R-5's "Deliberate omissions are recorded as omissions".
OMITTED_COPYBOOK_FIELDS: Final[Mapping[str, str]] = {
    "Purch-Addr1": (
        "flattened into PURCH-ADDRESS by the bridge "
        "[common/purchMT.cbl:L338]; no host variable, no column "
        "[copybooks/wspl.cob:L24]"
    ),
    "Purch-Addr2": (
        "flattened into PURCH-ADDRESS by the bridge "
        "[common/purchMT.cbl:L338]; no host variable, no column "
        "[copybooks/wspl.cob:L25]"
    ),
    "PTurnover-q": (
        "an OCCURS 4 redefinition of the four named quarters; the redefinition "
        "has no host variable and no column, and the bridge's own record buffer "
        "omits it entirely [copybooks/wspl.cob:L50-L51]"
    ),
    "Purch-Stats-Date": (
        "N-stats-date-write-nowhere: present in BOTH record layouts and stored "
        "nowhere - absent from the host-variable group "
        "[common/purchMT.cbl:L285-L313], the load "
        "[common/purchMT.cbl:L1211-L1240], the unload "
        "[common/purchMT.cbl:L1257-L1287] and the schema "
        "[mysql/ACASDB.sql:L646-L677], while being declared in BOTH record "
        "layouts [copybooks/wspl.cob:L53]"
    ),
    "filler": (
        "twelve bytes of record padding with no host variable and no column "
        "[copybooks/wspl.cob:L54]"
    ),
    "Array-k": (
        "N-dead-redefine: part of a key redefinition that is commented out in "
        "the frozen copybook and is not revived "
        "[copybooks/wspl.cob:L15-L17]"
    ),
    "Check-Digit": (
        "N-dead-redefine: the second half of the same commented-out key "
        "redefinition [copybooks/wspl.cob:L15-L17]"
    ),
}


EDIT_PICTURE: Final[str] = "-Z(18)9.9(9)"

#: Position 1 holds the sign.
_EDIT_SIGN_POSITION: Final[int] = 1

#: Positions 2..19 are the eighteen ``Z`` positions - zero-suppressed, so a leading zero
#: renders as a space.
_EDIT_SUPPRESSED_DIGITS: Final[int] = 18

#: Position 20 is the ``9`` - the units digit, never suppressed, which is why a value of
#: zero still renders as ``"0"`` in every window rather than as spaces.
_EDIT_INTEGER_DIGITS: Final[int] = _EDIT_SUPPRESSED_DIGITS + 1

#: Positions 22..30 are the nine fraction digits, never suppressed.
_EDIT_FRACTION_DIGITS: Final[int] = 9

_EDIT_WIDTH: Final[int] = 1 + _EDIT_INTEGER_DIGITS + 1 + _EDIT_FRACTION_DIGITS


def _ws_mysql_edit(value: Decimal | int) -> str:
    """Render one numeric host variable into the bridge's edited field.

    Reproduces ``MOVE HV-<name> TO WS-MYSQL-EDIT`` for the field declared at
    [common/purchMT.cbl:L215], from the picture clause rather than from a guess.

    Args:
        value: The host variable's value. An :class:`int` for the binary fields and a
            :class:`~decimal.Decimal` for the scaled ones; never a binary approximation
            of a real number.

    Returns:
        The thirty-character image, exactly as ``WS-MYSQL-EDIT`` would hold it.
    """
    magnitude = Decimal(value)
    negative = magnitude < 0
    if negative:
        # Negate rather than take a magnitude function, so that no banned numeric helper
        # is used and the operation stays exact.
        magnitude = -magnitude
    total_digits = _EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS
    units = int(
        magnitude.scaleb(_EDIT_FRACTION_DIGITS).to_integral_value(
            rounding=ROUND_DOWN
        )
    )
    digits = f"{units:0{total_digits}d}"[-total_digits:]
    integer_part = digits[:_EDIT_INTEGER_DIGITS]
    fraction_part = digits[_EDIT_INTEGER_DIGITS:]
    suppressed = integer_part[:_EDIT_SUPPRESSED_DIGITS].lstrip("0")
    return (
        ("-" if negative else " ")
        + suppressed.rjust(_EDIT_SUPPRESSED_DIGITS)
        + integer_part[_EDIT_SUPPRESSED_DIGITS]
        + "."
        + fraction_part
    )


def _edit_window(image: str, start: int, length: int) -> str:
    """Slice ``WS-MYSQL-EDIT(start:length)`` out of a rendered image.

    Args:
        image: A thirty-character image from :func:`_ws_mysql_edit`.
        start: The 1-based start position.
        length: The number of characters.

    Returns:
        The window's contents, spaces included.

    Raises:
        ValueError: If the window falls outside the field.
    """
    if start < 1 or length < 1 or start - 1 + length > _EDIT_WIDTH:
        raise ValueError(
            f"WS-MYSQL-EDIT({start}:{length}) falls outside the "
            f"{_EDIT_WIDTH}-character field declared as {EDIT_PICTURE} at "
            f"[common/purchMT.cbl:L215]"
        )
    return image[start - 1 : start - 1 + length]


def _trim(text: str) -> str:
    """``FUNCTION TRIM (x)`` - remove leading AND trailing spaces."""
    return text.strip(" ")


def _trim_trailing(text: str) -> str:
    """``FUNCTION TRIM (x, TRAILING)`` - remove trailing spaces only."""
    return text.rstrip(" ")


def _ws_file_key(text: str) -> str:
    """Fit one log literal into ``WS-File-Key pic x(64)``.

    [copybooks/wsfnctn.cob:L52] declares the field 64 characters wide, so a COBOL
    ``MOVE`` of a longer literal truncates on the right and a shorter one pads with
    spaces.

    Args:
        text: The literal the frozen source moves into the field.

    Returns:
        Exactly :data:`WS_FILE_KEY_WIDTH` characters.
    """
    return text[:WS_FILE_KEY_WIDTH].ljust(WS_FILE_KEY_WIDTH)


def _move_to_unsigned_host_variable(value: int, binding: _ColumnBinding) -> int:
    """Reproduce a signed binary field's ``MOVE`` into an UNSIGNED host variable.

    ANOMALY ``N-signloss-twelve``, the largest instance in the checkout and the purchase
    twin of Agent Action Plan anomaly #11.

    Args:
        value: The record field's value, signed as the copybook declares it.
        binding: The column's contract, whose ``digits`` is the host variable's declared
            width.

    Returns:
        The unsigned value the host variable would hold.
    """
    magnitude = -value if value < 0 else value
    if binding.signed:  # pragma: no cover - unreachable for this table
        # Every one of this table's binary host variables is declared unsigned within
        # the group at [common/purchMT.cbl:L285-L313]; only the eight scaled ones carry
        # an ``S``.
        raise ValueError(
            f"{binding.host_variable} is declared signed in the host-variable "
            f"group at [common/purchMT.cbl:L285-L313]; the unsigned narrowing "
            f"of anomaly N-signloss-twelve does not apply to it"
        )
    return magnitude % (10**binding.digits)


def _move_to_scaled_host_variable(
    value: Decimal, binding: _ColumnBinding
) -> Decimal:
    """Reproduce a packed-decimal field's ``MOVE`` into a ``COMP`` host variable.

    ANOMALY ``N-money-width-truncation``. The bridge's own hard-coded record buffer
    declares seven money fields ONE DIGIT WIDER than its own host variables.

    Args:
        value: The record field's value.
        binding: The column's contract, carrying the host variable's digits and scale.

    Returns:
        The value the host variable would hold.
    """
    negative = value < 0
    magnitude = -value if negative else value
    units = int(
        magnitude.scaleb(binding.scale).to_integral_value(rounding=ROUND_DOWN)
    )
    units %= 10**binding.digits
    held = Decimal(units).scaleb(-binding.scale)
    if negative and binding.signed:
        return -held
    return held


def _move_to_character_host_variable(
    value: str, binding: _ColumnBinding
) -> str:
    """Reproduce a ``MOVE`` into an alphanumeric host variable.

    A COBOL ``MOVE`` to ``PIC X(n)`` is left-justified, space-padded on the right and
    truncated on the right. The padding matters.

    Args:
        value: The record field's value.
        binding: The column's contract, carrying the declared width.

    Returns:
        Exactly ``binding.width`` characters.
    """
    return value[: binding.width].ljust(binding.width)


def _group_concatenation(purch: WsPurchRecord) -> str:
    """Flatten ``Purch-Address`` into the bridge's ``pic x(96)``.

    ANOMALY ``N-address-flattened``. The copybook declares a GROUP of two 48-character
    fields [copybooks/wspl.cob:L23-L25]; the bridge's own record buffer declares the
    flat ``pic x(96)`` [common/purchMT.cbl:L338] with irregular spacing that suggests it
    was hand-edited, and the host variable follows [common/purchMT.cbl:L289].

    Args:
        purch: The record whose address group is being flattened.

    Returns:
        Ninety-six characters: 48 of ``Purch-Addr1`` then 48 of ``Purch-Addr2``.
    """
    address = purch.purch_address
    return address.purch_addr1[:48].ljust(48) + address.purch_addr2[:48].ljust(
        48
    )


def _split_group_concatenation(purch: WsPurchRecord, value: str) -> None:
    """Unflatten ``HV-PURCH-ADDRESS`` back into the copybook's two fields.

    The reverse of :func:`_group_concatenation`, performed by ``move HV-PURCH-ADDRESS to
    PURCH-ADDRESS`` [common/purchMT.cbl:L1263]. In COBOL the group move writes 96 bytes
    across both children at once.

    Args:
        purch: The record to write into, mutated in place as the COBOL ``MOVE`` mutates
            the record area.
        value: The host variable's 96 characters.
    """
    padded = value[:96].ljust(96)
    purch.purch_address.purch_addr1 = padded[:48]
    purch.purch_address.purch_addr2 = padded[48:]


@dataclasses.dataclass(slots=True)
class HostVariables:
    """``01 TD-PULEDGER-REC`` [common/purchMT.cbl:L284-L313], field for field.

    CONSTRUCTING AN INSTANCE IS ``initialize TD-PULEDGER-REC``. Every default below is
    what ``INITIALIZE`` leaves in the field - spaces for alphanumeric, zero for numeric
    - and that statement is the FIRST statement of the load [common/purchMT.cbl:L1211].
    """

    hv_purch_key: str = " " * 7
    hv_purch_status: int = 0
    hv_purch_notes_tag: int = 0
    hv_purch_name: str = " " * 30
    hv_purch_address: str = " " * 96
    hv_purch_phone: str = " " * 13
    hv_purch_ext: str = " " * 4
    hv_purch_fax: str = " " * 13
    hv_purch_email: str = " " * 30
    hv_purch_discount: Decimal = Decimal("0.00")
    hv_purch_credit: int = 0
    hv_purch_sortcode: int = 0
    hv_purch_accountno: int = 0
    hv_purch_limit: int = 0
    hv_purch_activety: int = 0
    hv_purch_last_inv: int = 0
    hv_purch_last_pay: int = 0
    hv_purch_average: int = 0
    hv_purch_create_dat: int = 0
    hv_purch_pay_activety: int = 0
    hv_purch_pay_average: int = 0
    hv_purch_pay_worst: int = 0
    hv_purch_current: Decimal = Decimal("0.00")
    hv_purch_last: Decimal = Decimal("0.00")
    hv_turnover_q1: Decimal = Decimal("0.00")
    hv_turnover_q2: Decimal = Decimal("0.00")
    hv_turnover_q3: Decimal = Decimal("0.00")
    hv_turnover_q4: Decimal = Decimal("0.00")
    hv_purch_unapplied: Decimal = Decimal("0.00")

    def value_for(self, column: str) -> str | int | Decimal:
        """Read the host variable that feeds one column.

        Args:
            column: A column name from :data:`COLUMN_ORDER`.

        Returns:
            The host variable's current value.

        Raises:
            KeyError: If the column is not one of this table's 29.
        """
        return getattr(self, _BINDING_BY_COLUMN[column].field)

    def rendered_values(self) -> tuple[str, ...]:
        """Render all 29 host variables exactly as the bridge renders them.

        Returns:
            Twenty-nine strings, positionally aligned with :data:`COLUMN_ORDER`, each
                the exact text the bridge would have placed between its two ``"``
                delimiters.
        """
        rendered: list[str] = []
        for binding in _BINDINGS:
            value = getattr(self, binding.field)
            if binding.kind == "char":
                rendered.append(_trim_trailing(str(value)))
                continue
            image = _ws_mysql_edit(value)
            integer_text = _trim(
                _edit_window(image, binding.edit_start, binding.edit_length)
            )
            if binding.scale == 0:
                rendered.append(integer_text)
                continue
            # `STRING "." ... STRING WS-MYSQL-EDIT(22:02)` - the fraction window is NOT
            # trimmed [common/purchMT.cbl:L1404, L1565], so a value of 12.30 renders
            # "12" "." "30" and never "12.3".
            fraction_text = _edit_window(image, *_FRACTION_WINDOW)
            rendered.append(f"{integer_text}.{fraction_text}")
        return tuple(rendered)


_BINDING_BY_COLUMN: Final[Mapping[str, _ColumnBinding]] = {
    binding.column: binding for binding in _BINDINGS
}

#: The host-variable attribute names in column order, so that a fetch can be written as
#: one positional zip against the ``MySQL_fetch_record`` argument list.
_HV_FIELDS: Final[tuple[str, ...]] = tuple(
    binding.field for binding in _BINDINGS
)


def bb000_hv_load(purch: WsPurchRecord) -> HostVariables:
    """``bb000-HV-Load Section.`` [common/purchMT.cbl:L1203-L1246].

    *> Loading HVs implies a non-Fetch action. RGs are handled separately for *> all
    such actions so they must not be loaded here.

    Args:
        purch: The caller's record, read only. ``bb000`` never writes to it.

    Returns:
        The loaded host-variable group.
    """
    loaded = HostVariables()
    for binding in _BINDINGS:
        if binding.column == "PURCH-ADDRESS":
            setattr(
                loaded,
                binding.field,
                _move_to_character_host_variable(
                    _group_concatenation(purch), binding
                ),
            )
            continue
        value = _record_value(purch, binding)
        if binding.kind == "char":
            setattr(
                loaded,
                binding.field,
                _move_to_character_host_variable(str(value), binding),
            )
        elif binding.kind == "int":
            # ANOMALY N-signloss-twelve for twelve of these [copybooks/wspl.cob:L31-L42]
            # -> [common/purchMT.cbl:L295-L306].
            setattr(
                loaded,
                binding.field,
                _move_to_unsigned_host_variable(int(value), binding),
            )
        else:
            # ANOMALY N-money-width-truncation [common/purchMT.cbl:L356-L357] against
            # [common/purchMT.cbl:L307-L313].
            setattr(
                loaded,
                binding.field,
                _move_to_scaled_host_variable(Decimal(value), binding),
            )
    return loaded


def bb100_unload_hvs(
    host_variables: HostVariables, purch: WsPurchRecord
) -> None:
    """``bb100-UnloadHVs Section.`` [common/purchMT.cbl:L1248-L1290].

    *> Load the data buffer in the interface with data from the host *> variables. *>
    (init moved lower) *> *> NULL fields must not be returned in the buffer.

    Args:
        host_variables: The group a fetch has just filled.
        purch: The caller's record, MUTATED IN PLACE - a COBOL ``MOVE`` writes into the
            record area the caller passed, and every caller of this bridge holds a
            reference to that area.
    """
    _initialize_purch_rec(purch, with_filler=False)
    for binding in _BINDINGS:
        value = getattr(host_variables, binding.field)
        if binding.column == "PURCH-ADDRESS":
            _split_group_concatenation(purch, str(value))
            continue
        _set_record_value(purch, binding, value)
    _refresh_quarters_view(purch)


def _record_value(
    purch: WsPurchRecord, binding: _ColumnBinding
) -> str | int | Decimal:
    """Read the record field one column is loaded from.

    Resolves the dotted attribute paths of :data:`_RECORD_ATTRIBUTES`, which exist
    because the copybook groups ``Turnover-q1`` through ``Turnover-q4`` under
    ``Quarters`` [copybooks/wspl.cob:L45-L49] and the bridge does not.

    Args:
        purch: The record to read.
        binding: The column's contract.

    Returns:
        The field's value, in the copybook's own storage class.
    """
    target: object = purch
    for part in binding.attribute.split("."):
        target = getattr(target, part)
    return target  # type: ignore[return-value]


def _set_record_value(
    purch: WsPurchRecord,
    binding: _ColumnBinding,
    value: str | int | Decimal,
) -> None:
    """Write one host variable back into its record field.

    The receiving field's own storage class governs, not the host variable's.

    Args:
        purch: The record to write into, mutated in place.
        binding: The column's contract.
        value: The host variable's value.
    """
    parts = binding.attribute.split(".")
    target: object = purch
    for part in parts[:-1]:
        target = getattr(target, part)
    setattr(target, parts[-1], _move_to_record_field(value, binding))


def _move_to_record_field(
    value: str | int | Decimal, binding: _ColumnBinding
) -> str | int | Decimal:
    """Reproduce the unload direction's ``MOVE`` - host variable INTO the record.

    ``bb100-UnloadHVs`` [common/purchMT.cbl:L1259-L1287] is twenty-nine plain ``MOVE``
    statements, and a COBOL ``MOVE`` is governed by the RECEIVING field. That matters
    here because the drift recorded in the module docstring runs in both directions.

    Args:
        value: The host variable's value.
        binding: The column's contract, carrying the RECEIVING copybook field's usage,
            digits, scale, width and signedness.

    Returns:
        The value the copybook field would hold after the move.

    Raises:
        ValueError: If the column is the flattened address group, which has no single
            receiving field and is unloaded by :func:`_split_group_concatenation`
            instead, or if the dictionary reports a usage this table does not declare.
    """
    usage = binding.copybook_usage
    if usage == "ALPHANUMERIC":
        return str(value)[: binding.copybook_width].ljust(binding.copybook_width)
    if usage in _BINARY_STORAGE_BYTES:
        # `binary-char` [copybooks/wspl.cob:L31] and `binary-long`
        # [copybooks/wspl.cob:L32-L42] carry no picture clause, so the receiving
        # capacity is the storage width. GnuCOBOL wraps such a store in two's
        # complement.
        if binding.copybook_scale:  # pragma: no cover - no scaled binary here
            raise ValueError(
                f"{binding.column} is declared {usage} with a scale of "
                f"{binding.copybook_scale} at {binding.citation}; the "
                f"storage-width wrap models integer binary fields only"
            )
        modulus = 1 << (8 * _BINARY_STORAGE_BYTES[usage])
        wrapped = int(value) % modulus
        if wrapped >= modulus >> 1:
            wrapped -= modulus
        return wrapped
    if usage in ("DISPLAY", "COMP", "COMP-3"):
        return _store_into_picture_field(value, binding)
    # `03 Purch-Address.` [copybooks/wspl.cob:L23] is a GROUP.
    raise ValueError(
        f"{binding.column} has copybook usage {usage} at {binding.citation}; "
        f"it is not stored by a single MOVE"
    )


def _store_into_picture_field(
    value: str | int | Decimal, binding: _ColumnBinding
) -> int | Decimal:
    """Store a numeric value into a picture-declared receiving field.

    Covers the three picture-bearing usages this table's copybook declares - ``DISPLAY``
    [copybooks/wspl.cob:L18], ``COMP`` [copybooks/wspl.cob:L30] and ``COMP-3``
    [copybooks/wspl.cob:L43-L52].

    Args:
        value: The host variable's value.
        binding: The column's contract.

    Returns:
        An ``int`` for an unscaled field, a ``Decimal`` at the field's own scale for a
            scaled one. Never a binary approximation of either.
    """
    scale = binding.copybook_scale
    digits = binding.copybook_digits
    incoming = value if isinstance(value, Decimal) else Decimal(int(value))
    negative = incoming < 0
    magnitude = -incoming if negative else incoming
    units = int(magnitude.scaleb(scale).to_integral_value(rounding=ROUND_DOWN))
    units %= 10**digits
    if scale == 0:
        return -units if negative and binding.copybook_signed else units
    held = Decimal(units).scaleb(-scale)
    return -held if negative and binding.copybook_signed else held


#: The record fields the copybook declares as FILLER.
_RECORD_FILLER_FIELDS: Final[Mapping[str, str]] = {
    "filler_l54": "[copybooks/wspl.cob:L54]",
}

#: The record fields that REDEFINE earlier storage.
_RECORD_REDEFINING_FIELDS: Final[Mapping[str, str]] = {
    "quarters_view": "[copybooks/wspl.cob:L50-L51]",
}


def _initialize_purch_rec(purch: WsPurchRecord, *, with_filler: bool) -> None:
    """``initialize Purch-REC`` - with or without ``with filler``.

    Three sites in the frozen bridge initialise this record and they do NOT agree, which
    is why the form is a parameter rather than a constant.

    Args:
        purch: The record to initialise, MUTATED IN PLACE - COBOL initialises storage,
            it does not hand back a new record.
        with_filler: ``True`` for ``initialize ... with filler``, ``False`` for the
            plain form.
    """
    _initialize_group(purch, with_filler=with_filler)
    _refresh_quarters_view(purch)


def _initialize_group(group: object, *, with_filler: bool) -> None:
    """Initialise one record or subordinate group, honouring the FILLER rule.

    Recurses into subordinate groups - ``03 Purch-Address.`` [copybooks/wspl.cob:L23]
    and ``03 Quarters.`` [copybooks/wspl.cob:L45] - mutating each in place rather than
    rebinding it, because a COBOL ``INITIALIZE`` writes into the storage the caller
    already holds.

    Args:
        group: The record or group to initialise, mutated in place.
        with_filler: Whether FILLER items are included.

    Raises:
        ValueError: If a field declares neither a default nor a default factory, leaving
            no initialised value to restore.
    """
    for field_info in dataclasses.fields(group):  # type: ignore[arg-type]
        name = field_info.name
        if name in _RECORD_REDEFINING_FIELDS:
            continue
        if name in _RECORD_FILLER_FIELDS and not with_filler:
            continue
        current = getattr(group, name)
        if dataclasses.is_dataclass(current):
            _initialize_group(current, with_filler=with_filler)
            continue
        default = field_info.default
        if default is not dataclasses.MISSING:
            setattr(group, name, default)
            continue
        factory = field_info.default_factory
        if factory is not dataclasses.MISSING:
            setattr(group, name, factory())
            continue
        raise ValueError(  # pragma: no cover - every field declares one
            f"{type(group).__name__}.{name} declares no initialised value, so "
            f"`initialize` [common/purchMT.cbl:L1257] cannot be reproduced"
        )


def _refresh_quarters_view(purch: WsPurchRecord) -> None:
    """Restore the ``PTurnover-q ... occurs 4`` alias over the four quarters.

    ``03 filler redefines Quarters.`` with ``05 PTurnover-q pic s9(8)v99 comp-3 occurs
    4.`` [copybooks/wspl.cob:L50-L51] is a SECOND VIEW of the same storage, so in COBOL
    it needs no move of its own - writing ``Turnover-q1`` IS writing ``PTurnover-q
    (1)``.

    Args:
        purch: The record whose alias is restored, mutated in place.
    """
    quarters = purch.quarters
    purch.quarters_view.pturnover_q = (
        quarters.turnover_q1,
        quarters.turnover_q2,
        quarters.turnover_q3,
        quarters.turnover_q4,
    )


# `purchMT` keeps its connection handle and its two cursor flags in WORKING STORAGE, so
# they persist between calls and are shared by every caller of the bridge
# [common/purchMT.cbl:L244-L254], [copybooks/mysql-variables.cpy via
# common/purchMT.cbl:L279].

_CONNECTION: object | None = None

#: ``Most-Cursor-Set`` and ``Most-Cursor-Set-2`` [common/purchMT.cbl:L246-L254], the
#: bridge's TWO cursor slots.
_CURSORS: Final[CursorStateTable] = CursorStateTable()

#: ``77 A pic 9(4) value zero`` and ``77 B pic 9(4) value zero``
#: [common/acas022.cbl:L253-L254], carrying the maintainer's own instruction.
_WS_A: int = 0
_WS_B: int = 0


def reset_bridge_state() -> None:
    """Return both programs' working storage to its declared initial state.

    A freshly loaded COBOL program starts with ``A`` and ``B`` at zero
    [common/acas022.cbl:L253-L254], ``Cobol-File-Status`` at its declared ``value zero``
    [common/acas022.cbl:L256], both cursor flags at zero [common/purchMT.cbl:L246],
    [common/purchMT.cbl:L252] and no connection handle.
    """
    global _CONNECTION, _WS_A, _WS_B, _COBOL_FILE_STATUS
    if _CONNECTION is not None:
        mysql_1980_close(_CONNECTION)  # type: ignore[arg-type]
        mysql_1999_exit()
        _CONNECTION = None
    _CURSORS.reset(TABLE)
    _RESULT_POINTER.free_result()
    _RESULT_POINTER.set_cursor_not_active()
    _WS_A = 0
    _WS_B = 0
    _COBOL_FILE_STATUS = 0


@runtime_checkable
class PurchaseFile(Protocol):
    """The ISAM verbs ``acas022`` issues against ``fd Purchase-File``.

    ``acas022`` is a DUAL-PATH handler: when ``FS-Cobol-Files-Used``
    [copybooks/wssystem.cob:L113] holds, it drives an indexed file declared by ``copy
    "selpl.cob"`` and ``copy "fdpl.cob"`` [common/acas022.cbl:L239, :L244]; otherwise it
    hands the call to the bridge and returns [common/acas022.cbl:L316-L320].
    """

    @property
    def record(self) -> WsPurchRecord:
        """``01 Purch-Record`` [copybooks/fdpl.cob:L15] - the FD record area."""

    def open_input(self) -> int:
        """``open input Purchase-File`` [common/acas022.cbl:L367]."""

    def open_io(self) -> int:
        """``open i-o Purchase-File`` [common/acas022.cbl:L375, :L380]."""

    def open_output(self) -> int:
        """``open output Purchase-File`` [common/acas022.cbl:L378, :L384]."""

    def close(self) -> int:
        """``close Purchase-File`` [common/acas022.cbl:L370, :L377, :L405]."""

    def read_next(self) -> int:
        """``read Purchase-File next record`` [common/acas022.cbl:L431]."""

    def read_by_key(self) -> int:
        """``read Purchase-File key Purch-Key`` [common/acas022.cbl:L474]."""

    def start(self, access_type: int) -> int:
        """``start Purchase-File key <relation> Purch-Key``."""

    def write(self) -> int:
        """``write Purch-Record`` [common/acas022.cbl:L543]."""

    def rewrite(self) -> int:
        """``rewrite Purch-Record`` [common/acas022.cbl:L567]."""

    def delete(self) -> int:
        """``delete Purchase-File record`` [common/acas022.cbl:L555]."""


class PurchaseFileNotSuppliedError(TypeError):
    """Raised when the ISAM path is entered with no ``Purchase-File`` store.

    COBOL the file always exists, because ``fd Purchase-File`` [copybooks/fdpl.cob:L13]
    is part of the program.
    """


def _require_purchase_file(
    purchase_file: PurchaseFile | None, paragraph: str
) -> PurchaseFile:
    """Return the ISAM store, or explain precisely why there is none.

    Args:
        purchase_file: The store the caller supplied, if any.
        paragraph: The COBOL paragraph being reproduced, named in the message so a
            caller can see which verb it was about to issue.

    Returns:
        The store.

    Raises:
        PurchaseFileNotSuppliedError: If no store was supplied.
    """
    if purchase_file is None:
        raise PurchaseFileNotSuppliedError(
            f"{paragraph} drives `fd Purchase-File` [copybooks/fdpl.cob:L13], "
            f"but no store was supplied. `acas022` takes this path only when "
            f"FS-Cobol-Files-Used holds [copybooks/wssystem.cob:L113]; the "
            f"migrated cycle sets File-System-Used to 1 and takes the RDBMS "
            f"path at [common/acas022.cbl:L316-L320] instead"
        )
    return purchase_file


#: ``WS-Log-Where pic x(231)`` [copybooks/wsfnctn.cob:L53].
_WS_LOG_WHERE_WIDTH: Final[int] = 231

#: ``ws-temp-ed pic 9(10)`` [common/purchMT.scb:L219], the numeric edit field two
#: paragraphs route values through. Its digit count is what makes anomaly ``N-key-
#: through-numeric-edit`` observable.
_WS_TEMP_ED_DIGITS: Final[int] = 10

#: The quoted table name, built once.
_QUOTED_TABLE: Final[str] = quote_identifier(TABLE)

_QUOTED_KEY_COLUMN: Final[str] = quote_identifier(KEY_OF_REFERENCE.column_name)


def _purch_rec_key(purch: WsPurchRecord) -> str:
    """``Purch-REC (K:L)`` - the key sliced out of the bridge's record buffer.

    Args:
        purch: The record whose key field is sliced.

    Returns:
        Exactly :attr:`KeyOfReference.kor_length` characters.
    """
    width = KEY_OF_REFERENCE.kor_length
    return purch.ws_purch_key[:width].ljust(width)


def _where_on_primary_key(relation: str) -> str:
    """Build ``` `PURCH-KEY`<relation>%s ``` - the one-predicate WHERE clause.

    Reproduces the ``string`` at [common/purchMT.cbl:L918-L926] and its three siblings,
    with ONE substitution the migration is required to make: the key VALUE travels as a
    bound ``%s`` placeholder rather than being formatted into the text between two ``"``
    delimiters.

    Args:
        relation: The comparison, already in the bridge's spelling - ``"="`` for the
            three exact-match paragraphs, or one of the five
            :class:`~acas_posting.dal.cursor_state.MostRelation` tokens for a start.

    Returns:
        The clause text, with one placeholder.
    """
    return f"{_QUOTED_KEY_COLUMN}{relation}%s"


def _stored_rows(cursor: object) -> tuple[Mapping[str, object], ...]:
    """Materialise a result set, reproducing ``MYSQL-1220-STORE-RESULT``.

    ``ba040``, ``ba050``, ``ba060`` and ``ba140`` each issue ``PERFORM MYSQL-1220-STORE-
    RESULT THRU MYSQL-1239-EXIT`` immediately after the query [common/purchMT.cbl:L546,
    :L699, :L848, :L1053] and then ``MOVE WS-MYSQL-RESULT TO TP-PULEDGER-REC``, parking
    the WHOLE result in the bridge's own result pointer.

    Args:
        cursor: The cursor a statement has just been executed on.

    Returns:
        Every row, in the order the server returned them.
    """
    description = getattr(cursor, "description", None) or ()
    names = tuple(str(column[0]) for column in description)
    rows: list[Mapping[str, object]] = []
    fetch_one = getattr(cursor, "fetchone")
    while True:
        row = fetch_one()
        if row is None:
            break
        if isinstance(row, Mapping):
            rows.append(dict(row))
            continue
        rows.append(dict(zip(names, tuple(row), strict=False)))
    return tuple(rows)


def _log_where(file_access: FileAccess, clause: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where.`` "For test logging".

    Reproduced at [common/purchMT.cbl:L532, :L682, :L829, :L928, :L985, :L1039], and
    cleared at [common/purchMT.cbl:L584] and [common/purchMT.cbl:L1091]. Truncated to
    the receiving field's own 231 characters [copybooks/wsfnctn.cob:L53].

    Args:
        file_access: The block whose logging data is written.
        clause: The clause text, or the empty string for the ``move spaces`` form.
    """
    file_access.logging_data.ws_log_where = clause[:_WS_LOG_WHERE_WIDTH].ljust(
        _WS_LOG_WHERE_WIDTH
    )


def _file_key(file_access: FileAccess, text: str) -> None:
    """``move <literal> to WS-File-Key`` - the 64-character log key.

    Every site's literal is reproduced verbatim, truncated and space-padded to ``pic
    x(64)`` [copybooks/wsfnctn.cob:L52] exactly as a COBOL ``MOVE`` to an alphanumeric
    field would.

    Args:
        file_access: The block whose logging data is written.
        text: The literal, or the empty string for the ``move spaces`` form.
    """
    file_access.logging_data.ws_file_key = _ws_file_key(text)


def _count_rows_file_key(count: int, suffix: str) -> str:
    """Build the counted log key of ``ba040`` and ``ba140``.

    ``move WS-MYSQL-Count-Rows to WS-Temp-Ed`` then ``string "> 0 got cnt=" WS-Temp-ED "
    recs"`` [common/purchMT.cbl:L571-L576].

    Args:
        count: ``WS-MYSQL-Count-Rows``.
        suffix: ``" recs"`` for ``ba040`` [common/purchMT.cbl:L574], or ``" recs in NAME
            order"`` for ``ba140`` [common/purchMT.cbl:L1081].

    Returns:
        The log key text, before the receiving field truncates it.
    """
    return f"> 0 got cnt={count % (10**_WS_TEMP_ED_DIGITS):010d}{suffix}"


def _through_ws_temp_ed(key_text: str) -> str:
    """``move HV-Purch-Key to ws-temp-ed`` - ANOMALY ``N-key-through-numeric-edit``.

    ``ba050`` alone routes the key through a NUMERIC field on its way to the log key:
    ``move HV-Purch-Key to ws-temp-ed.`` then ``move ws-temp-ed to WS-File-Key``
    [common/purchMT.cbl:L771-L772].

    Args:
        key_text: The seven-character key from the host variable.

    Returns:
        The ten-character image ``ws-temp-ed`` would hold.
    """
    return key_text.rjust(_WS_TEMP_ED_DIGITS, "0")[-_WS_TEMP_ED_DIGITS:]


#: The three fields ``call "MySQL_errno"``, ``call "MySQL_sqlstate"`` and ``call
#: "MySQL_error"`` return when the statement itself SUCCEEDED.
_ERRNO_SUCCESS: Final[str] = "0  "
_SQLSTATE_SUCCESS: Final[str] = "00000"


def _driver_error_fields(error: BaseException | None) -> tuple[str, str, str]:
    """Render the three client-library queries as ``(errno, sqlstate, message)``.

    Reproduces the inline triple every failure path of this bridge issues - ``call
    "MySQL_errno" using WS-MYSQL-Error-Number``, ``call "MySQL_sqlstate" using WS-MYSQL-
    SQLstate`` and, only when the first reports a real error, ``call "MySQL_error" using
    WS-MYSQL-Error-Message`` [common/purchMT.cbl:L557-L563].

    Args:
        error: The exception the driver raised, or ``None`` for a statement that
            succeeded and simply matched no row.

    Returns:
        ``(errno, sqlstate, message)`` - all three exactly as the host variables would
            hold them.
    """
    if error is None:
        return _ERRNO_SUCCESS, _SQLSTATE_SUCCESS, ""
    errno = str(getattr(error, "errno", "") or "").ljust(3)[:5]
    sqlstate = str(getattr(error, "sqlstate", "") or "").ljust(5)[:5]
    return errno, sqlstate, redact_for_log(str(error))


def _move_sql_state(file_access: FileAccess, sqlstate: str) -> None:
    """``move WS-MYSQL-SqlState to SQL-State`` - unconditional at all seven sites.

    Every zero-row and every failure path moves the client's SQL state across BEFORE
    testing the error number [common/purchMT.cbl:L559, :L637, :L752, :L894, :L949,
    :L995, :L1066], so the state is reported even on the paths that decide the statement
    did not really fail.

    Args:
        file_access: The block whose logging data is written.
        sqlstate: The five-character state.
    """
    file_access.logging_data.sql_state = sqlstate[:5].ljust(5)


def _move_sql_error(
    file_access: FileAccess, errno: str, message: str
) -> None:
    """``move WS-MYSQL-Error-Number to SQL-Err`` and the message to ``SQL-Msg``.

    Args:
        file_access: The block whose logging data is written.
        errno: The client's error number.
        message: The client's message, already redacted.
    """
    logging_data = file_access.logging_data
    logging_data.sql_err = errno[:5].ljust(5)
    logging_data.sql_msg = message[:512].ljust(512)


def _clear_sql_error(file_access: FileAccess) -> None:
    """``move spaces to SQL-Msg`` and ``move zero to SQL-Err``.

    The success-path clear of ``ba080`` [common/purchMT.cbl:L959-L960], ``ba090``
    [common/purchMT.cbl:L1006-L1007] and ``ba070``'s entry
    [common/purchMT.cbl:L887-L888].

    Args:
        file_access: The block whose logging data is written.
    """
    logging_data = file_access.logging_data
    logging_data.sql_err = "0".ljust(5)
    logging_data.sql_msg = " " * 512


def _status(file_access: FileAccess, fs_reply: int, we_error: int) -> None:
    """Write the status pair every paragraph reports through.

    Args:
        file_access: The block whose status pair is written.
        fs_reply: The value the frozen source moves to ``FS-Reply``.
        we_error: The value the frozen source moves to ``WE-Error``.
    """
    file_access.fs_reply = int(fs_reply) % 100
    file_access.we_error = int(we_error) % 1000


def _stamp(file_access: FileAccess, paragraph: int) -> None:
    """``move <n> to ws-No-Paragraph`` - the per-paragraph trace number.

    Args:
        file_access: The block whose logging data is written.
        paragraph: The number the frozen source moves.
    """
    file_access.logging_data.ws_no_paragraph = int(paragraph) % 1000


def _trace(message: str, *arguments: object) -> None:
    """``display Display-Message-1 with erase eos`` - gated on ``Testing-2``.

    Agent Action Plan section 0.3.4 settles the treatment: "Diagnostic displays with no
    database effect become log records at a severity matching the original's intent.

     THE EIGHT CALL SITES ARE PRESERVED AND THIS FUNCTION EMITS NOTHING.
    Every one of them passes the assembled ``WHERE`` clause or the whole statement -
    for this table a predicate carrying ``PURCH-KEY``, the supplier code, as a
    literal, and an INSERT or UPDATE naming every one of the twenty-nine columns and
    its value. The safe-event schema in :mod:`acas_posting.dal.status` admits no SQL
    text and no record key (CWE-532), and no redaction can help: escaping a
    statement's control characters leaves the statement.

    The function, its eight call sites and the ``Testing-2`` guard around each are
    all kept, so a reader following the frozen source still finds every ``display``
    and finds what it now does. The clause itself is still BUILT and still stored in
    ``WS-Log-Where``, because the bridge's own statements read it - the disposition
    is unchanged (R-3). Nothing acts on this trace operationally: it was a
    developer's own, read at the terminal beside the running program, and the frozen
    copybook leaves its switch at zero.

     THE EIGHT CALL SITES ARE PRESERVED AND THIS FUNCTION EMITS NOTHING.
    Every one of them passes the assembled ``WHERE`` clause or the whole statement -
    for this table a predicate carrying ``PURCH-KEY``, the supplier code, as a
    literal, and an INSERT or UPDATE naming every one of the twenty-nine columns and
    its value. The safe-event schema in :mod:`acas_posting.dal.status` admits no SQL
    text and no record key (CWE-532), and no redaction can help: escaping a
    statement's control characters leaves the statement.

    The function, its eight call sites and the ``Testing-2`` guard around each are
    all kept, so a reader following the frozen source still finds every ``display``
    and finds what it now does. The clause itself is still BUILT and still stored in
    ``WS-Log-Where``, because the bridge's own statements read it - the disposition
    is unchanged (R-3). Nothing acts on this trace operationally: it was a
    developer's own, read at the terminal beside the running program, and the frozen
    copybook leaves its switch at zero.

    Args:
        message: A printf-style template, retained so every call site still records
            which paragraph displayed what.
        *arguments: Its arguments, evaluated by the caller and then discarded here -
            no argument is rendered, so nothing can leak by accident.
    """
    del message, arguments


# THE BRIDGE PROGRAM - `purchMT` `PROCEDURE DIVISION using File-Access ACAS-DAL-Common-
# data Purch-Rec.` [common/purchMT.cbl:L385-L387] - THREE parameters, in that order,
# with the third annotated by the maintainer as "Ws record".


def purchmt_ba010_initialise(file_access: FileAccess) -> None:
    """``ba010-Initialise.`` [common/purchMT.cbl:L403-L445].

    ANOMALY ``N-bridge-clears-sqlstate``. The bridge clears all three SQL fields
    including ``SQL-State``; its own caller ``acas022`` clears only TWO, ``move spaces
    to SQL-Err SQL-Msg.`` [common/acas022.cbl:L336].

    Args:
        file_access: The block whose logging data is cleared.
    """
    logging_data = file_access.logging_data
    # `move spaces to ... WS-Log-Where ...
    _log_where(file_access, "")
    _file_key(file_access, "")
    logging_data.sql_msg = " " * 512
    logging_data.sql_err = " " * 5
    logging_data.sql_state = " " * 5


def purchmt_ba020_process_open(
    file_access: FileAccess,
    *,
    system_record: SystemRecord | None,
    transport: TransportSecurity | None,
) -> None:
    """``ba020-Process-Open.`` [common/purchMT.cbl:L447-L489].

    Six ``string`` statements copy the connection settings out of ``RDB-Data``, each
    ``delimited by space`` and each terminated with an explicit ``X"00"`` for the C
    interface [common/purchMT.cbl:L452-L475] - schema, host, user, password, port and
    socket, in that order.

    Args:
        file_access: The block whose status and logging data are written.
        system_record: The record the handler loaded ``RDB-Data`` from at
            [common/acas022.cbl:L641-L646]. When ``None`` it is reconstructed from
            ``RDB-Data`` itself, because the bridge holds nothing else.
        transport: The transport-security policy for the driver, passed straight through
            to the shared open.
    """
    global _CONNECTION
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"])
    source = (
        system_record
        if system_record is not None
        else _system_record_from_rdb_data(file_access)
    )
    outcome = mysql_1090_exit(
        mysql_1000_open(
            source,
            ws_no_paragraph=file_access.logging_data.ws_no_paragraph,
            we_error=file_access.we_error,
            transport=transport,
        )
    )
    _status(file_access, outcome.fs_reply, outcome.we_error)
    _stamp(file_access, outcome.ws_no_paragraph)
    logging_data = file_access.logging_data
    logging_data.sql_err = outcome.sql_err[:5].ljust(5)
    logging_data.sql_msg = outcome.sql_msg[:512].ljust(512)
    logging_data.sql_state = outcome.sql_state[:5].ljust(5)
    if file_access.fs_reply != int(FsReply.SUCCESS):
        _CONNECTION = outcome.connection
        return
    _CONNECTION = outcome.connection
    _file_key(file_access, "OPEN PULedger")
    # `move zero to Most-Cursor-Set` [common/purchMT.cbl:L488] - SLOT 1 ONLY. ANOMALY
    # N-open-resets-slot-1-only: slot 2 is untouched here.
    _CURSORS.state_for(TABLE, _KEY_ORDER_SLOT).set_cursor_not_active()


def _system_record_from_rdb_data(file_access: FileAccess) -> SystemRecord:
    """Rebuild the six connection settings a system record carries.

    :func:`~acas_posting.dal.connection.mysql_1000_open` takes the system record, so
    this inverts those six moves - a lossless round trip, because they are the only six
    fields the open reads.

    Args:
        file_access: The block carrying ``RDB-Data``.

    Returns:
        A system record carrying those six settings and nothing else.
    """
    rdb_data = file_access.rdb_data
    rebuilt = SystemRecord()
    block = rebuilt.system_data_block
    block.rdbms_db_name = rdb_data.db_schema
    block.rdbms_user = rdb_data.db_uname
    block.rdbms_passwd = rdb_data.db_upass
    block.rdbms_port = rdb_data.db_port
    block.rdbms_host = rdb_data.db_host
    block.rdbms_socket = rdb_data.db_socket
    return rebuilt


def purchmt_ba030_process_close(file_access: FileAccess) -> None:
    """``ba030-Process-Close.`` [common/purchMT.cbl:L491-L503].

    Note the ORDER: the free comes BEFORE the stamp, so a close that frees a cursor
    reports paragraph 19 from inside ``ba998-Free`` [common/purchMT.cbl:L1182] and then
    overwrites it with 2. Reproduced as written.

    Args:
        file_access: The block whose status and logging data are written.
    """
    global _CONNECTION
    if _CURSORS.state_for(TABLE, _KEY_ORDER_SLOT).cursor_active():
        # `perform ba998-Free.` [common/purchMT.cbl:L493] - a PERFORM, so control
        # returns here rather than falling into `ba999-end`.
        purchmt_ba998_free(file_access)
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba030-Process-Close"])
    _file_key(file_access, "CLOSE PULedger")
    mysql_1980_close(_CONNECTION)  # type: ignore[arg-type]
    mysql_1999_exit()
    _CONNECTION = None


def _host_variables_from_row(row: Mapping[str, object]) -> HostVariables:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT`` and its 29 arguments.

    A missing column is not a case the fetch has.

    Args:
        row: One row, keyed by column name.

    Returns:
        The host-variable group the fetch would have filled.
    """
    fetched = HostVariables()
    for binding in _BINDINGS:
        if binding.column not in row:
            continue
        value = row[binding.column]
        if binding.kind == "char":
            setattr(
                fetched,
                binding.field,
                _move_to_character_host_variable(
                    "" if value is None else str(value), binding
                ),
            )
            continue
        if value is None:
            continue
        if binding.kind == "int":
            setattr(
                fetched,
                binding.field,
                _move_to_unsigned_host_variable(int(value), binding),  # type: ignore[arg-type]
            )
            continue
        setattr(
            fetched,
            binding.field,
            _move_to_scaled_host_variable(
                value if isinstance(value, Decimal) else Decimal(str(value)),
                binding,
            ),
        )
    return fetched


def purchmt_ba040_process_read_next(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    connection: object,
) -> None:
    """``ba040-Process-Read-Next.`` [common/purchMT.cbl:L505-L578].

    So the whole body is wrapped in ``if Cursor-Not-Active`` [common/purchMT.cbl:L511]
    and the paragraph FALLS THROUGH into ``ba041`` whether or not it ran - which is why
    a read with a live cursor issues no statement at all.

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record. Untouched here; ``ba041`` writes it.
        dal_common: The logging switches [copybooks/Test-Data-Flags.cob].
        connection: The open handle the statement is issued on.
    """
    state = _CURSORS.state_for(TABLE, _KEY_ORDER_SLOT)
    if state.cursor_not_active():
        relation = _SEQUENTIAL_START.relation.padded.strip()
        clause = (
            f"{_QUOTED_KEY_COLUMN} {relation} %s"
            f" ORDER BY {_QUOTED_KEY_COLUMN} ASC"
        )
        _log_where(file_access, clause)
        _stamp(
            file_access, BRIDGE_PARAGRAPH_NUMBERS["ba040-Process-Read-Next"]
        )
        statement = (
            f"SELECT * FROM {_QUOTED_TABLE} WHERE {clause};"
        )
        _RESULT_POINTER.most_relation = _SEQUENTIAL_START.relation
        rows, error = _mysql_1210_command_then_store(
            connection, statement, (_SEQUENTIAL_START.low_key,), file_access
        )
        count = _RESULT_POINTER.store_result(rows)
        _file_key(file_access, _SEQUENTIAL_START.low_key)
        if dal_common.sw_testing_2 == 1:
            _trace("purchMT ba040: %s", clause)
        if count == 0:
            errno, sqlstate, message = _driver_error_fields(error)
            _move_sql_state(file_access, sqlstate)
            if errno != _ERRNO_SUCCESS:
                _move_sql_error(file_access, errno, message)
            fs_reply, we_error = end_of_file_status()
            _status(file_access, fs_reply, we_error)
            _file_key(file_access, "No Data")
            return
        state.set_cursor_active()
        _file_key(file_access, _count_rows_file_key(count, " recs"))
        purchmt_ba999_end(file_access, dal_common)
    purchmt_ba041_reread(file_access, purch, dal_common)


def purchmt_ba041_reread(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba041-Reread.`` [common/purchMT.cbl:L580-L660].

    "If here cursor is set (even from start), so get the next row"
    [common/purchMT.cbl:L582]. THE PARAGRAPH ISSUES NO STATEMENT.

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record, written by the unload on the success path and wiped
            on the ``"EOF2"`` path.
        dal_common: The logging switches, unused on this path and accepted so that every
            paragraph of the bridge takes the same shape.
    """
    state = _CURSORS.state_for(TABLE, _KEY_ORDER_SLOT)
    # `move spaces to WS-Log-Where.` [common/purchMT.cbl:L584] - the fetch has no clause
    # of its own, so the previous paragraph's is cleared rather than left to be logged
    # twice.
    _log_where(file_access, "")
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba041-Reread"])
    row = _RESULT_POINTER.fetch_record()
    if row is None:
        fs_reply, we_error = end_of_file_status()
        _status(file_access, fs_reply, we_error)
        _file_key(file_access, "EOF")
        state.set_cursor_not_active()
        return
    if _RESULT_POINTER.count_rows == 0:  # pragma: no cover - a row implies a count
        # [common/purchMT.cbl:L634-L648]. Unreachable while a row was returned, and
        # reproduced because the frozen source tests it in this order.
        errno, sqlstate, message = _driver_error_fields(None)
        _move_sql_state(file_access, sqlstate)
        if errno != _ERRNO_SUCCESS:
            _move_sql_error(file_access, errno, message)
            _initialize_purch_rec(purch, with_filler=True)
            _file_key(file_access, "EOF2")
        fs_reply, we_error = end_of_file_status()
        _status(file_access, fs_reply, we_error)
        state.set_cursor_not_active()
        return
    if file_access.fs_reply == int(FsReply.END_OF_FILE):
        # ANOMALY N-sticky-eof [common/purchMT.cbl:L651-L655]. The row just fetched is
        # discarded and the cursor deactivated.
        state.set_cursor_not_active()
        _file_key(file_access, "EOF3")
        return
    bb100_unload_hvs(_host_variables_from_row(row), purch)
    _file_key(file_access, str(row.get(KEY_OF_REFERENCE.column_name, "")))
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)


def _issue_query(
    connection: object,
    statement: str,
    parameters: Sequence[object],
) -> tuple[tuple[Mapping[str, object], ...], BaseException | None]:
    """``PERFORM MYSQL-1210-COMMAND`` then ``MYSQL-1220-STORE-RESULT``.

    One statement, one materialised result, and the driver's failure captured rather
    than raised - because every one of this bridge's paragraphs decides for itself what
    a failure means, and several decide it means nothing. The broad ``except``
    reproduces that.

    Args:
        connection: The open handle.
        statement: One statement, identifiers quoted and values as ``%s``.
        parameters: The values to bind, in the statement's order.

    Returns:
        ``(rows, error)`` - the materialised result and the exception, if any. A failure
            yields no rows, which is what makes every caller's ``WS-MYSQL-Count-Rows``
            test fire.
    """
    try:
        with execute_statement(connection, statement, parameters) as cursor:  # type: ignore[arg-type]
            return _stored_rows(cursor), None
    except Exception as error:
        return (), error


def _issue_command(
    connection: object,
    statement: str,
    parameters: Sequence[object],
) -> tuple[int, BaseException | None]:
    """``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` for a non-query.

    Args:
        connection: The open handle.
        statement: One statement, identifiers quoted and values as ``%s``.
        parameters: The values to bind, in the statement's order.

    Returns:
        ``(affected rows, error)``. A failure yields a count of zero, so the ``not = 1``
            test fires exactly as it does in the frozen source.
    """
    try:
        with execute_statement(connection, statement, parameters) as cursor:  # type: ignore[arg-type]
            affected = getattr(cursor, "rowcount", 0)
            return (0 if affected is None or affected < 0 else int(affected)), None
    except Exception as error:
        return 0, error


def _mysql_1100_db_error(
    file_access: FileAccess, error: BaseException, statement: str
) -> None:
    """``Mysql-1100-Db-Error`` [copybooks/mysql-procedures.cpy:L96-L128].

    The shared failure paragraph that every statement in this bridge reaches through
    :func:`_mysql_1210_command`.

    Args:
        file_access: The block whose status pair and diagnostic fields are written,
            mutated in place as the COBOL ``MOVE`` statements do.
        error: The driver failure standing in for the three foreign calls
            ``MySQL_errno``, ``MySQL_error`` and ``MySQL_sqlstate``.
        statement: The statement text that failed. The duplicate test reads its first
            six characters only.
    """
    errno, sqlstate, message = _driver_error_fields(error)
    outcome = mysql_1100_db_error(
        errno=errno,
        message=message,
        sql_state=sqlstate,
        command=statement,
        we_error=int(file_access.we_error),
    )
    _status(file_access, int(outcome.fs_reply), int(outcome.we_error))
    outcome.apply_to_logging_data(file_access.logging_data)


def _mysql_1210_command(
    connection: object,
    statement: str,
    parameters: Sequence[object],
    file_access: FileAccess,
) -> tuple[int, BaseException | None]:
    """``Mysql-1210-Command`` thru ``Mysql-1219-Exit``.

    ANOMALY ``N-select-through-command``.

    Args:
        connection: The open handle.
        statement: The assembled statement, identifiers already quoted.
        parameters: The values bound in place of the text the COBOL embeds.
        file_access: The block the failure path writes to.

    Returns:
        The affected-row count and the driver failure, if there was one.
    """
    affected, error = _issue_command(connection, statement, parameters)
    if error is not None:
        _mysql_1100_db_error(file_access, error, statement)
    return affected, error


def _mysql_1210_command_then_store(
    connection: object,
    statement: str,
    parameters: Sequence[object],
    file_access: FileAccess,
) -> tuple[tuple[Mapping[str, object], ...], BaseException | None]:
    """``MYSQL-1210-COMMAND`` followed by ``MYSQL-1220-STORE-RESULT``.

    The pair every read paragraph in this bridge performs back to back
    [common/purchMT.cbl:L545-L546, :L698-L699, :L847-L848, :L1052-L1053].

    Args:
        connection: The open handle.
        statement: The assembled statement, identifiers already quoted.
        parameters: The values bound in place of the text the COBOL embeds.
        file_access: The block the failure path writes to.

    Returns:
        The materialised rows and the driver failure, if there was one.
    """
    rows, error = _issue_query(connection, statement, parameters)
    if error is not None:
        _mysql_1100_db_error(file_access, error, statement)
    return rows, error


def purchmt_ba050_process_read_indexed(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    connection: object,
) -> None:
    """``ba050-Process-Read-Indexed.`` [common/purchMT.cbl:L662-L774].

    * ``move 23 to fs-Reply`` with ``move zero to WE-Error``
    [common/purchMT.cbl:L703-L706], carrying the maintainer's own note that it "could
    also be 21 or 14". ANOMALY ``N-readindexed-23``.

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record; its key field supplies the predicate and the unload
            writes the rest of it back.
        dal_common: The logging switches.
        connection: The open handle.
    """
    key_value = _purch_rec_key(purch)
    clause = _where_on_primary_key("=")
    _log_where(file_access, clause)
    if dal_common.sw_testing_2 == 1:
        _trace("purchMT ba050: %s", clause)
    _stamp(
        file_access,
        BRIDGE_PARAGRAPH_NUMBERS["ba050-Process-Read-Indexed-select"],
    )
    statement = f"SELECT * FROM {_QUOTED_TABLE} WHERE {clause};"
    rows, error = _mysql_1210_command_then_store(
        connection, statement, (key_value,), file_access
    )
    count = _RESULT_POINTER.store_result(rows)
    if count == 0:
        # [common/purchMT.cbl:L703-L707].
        _status(file_access, FsReply.KEY_NOT_FOUND, WeError.SUCCESS)
        purchmt_ba998_free(file_access)
        return
    _stamp(
        file_access,
        BRIDGE_PARAGRAPH_NUMBERS["ba050-Process-Read-Indexed-fetch"],
    )
    row = _RESULT_POINTER.fetch_record()
    if row is None or _RESULT_POINTER.count_rows <= 0:
        errno, sqlstate, message = _driver_error_fields(error)
        _move_sql_state(file_access, sqlstate)
        if errno != _ERRNO_SUCCESS:
            _status(file_access, FsReply.KEY_NOT_FOUND, WeError.UNKNOWN_UNEXPECTED)
            _move_sql_error(file_access, errno, message)
            _file_key(file_access, "")
        else:
            _status(
                file_access,
                FsReply.KEY_NOT_FOUND,
                WeError.READ_INDEXED_UNEXPECTED,
            )
            _clear_sql_error(file_access)
            _file_key(file_access, "")
        purchmt_ba998_free(file_access)
        return
    bb100_unload_hvs(_host_variables_from_row(row), purch)
    # ANOMALY N-key-through-numeric-edit [common/purchMT.cbl:L771-L772].
    _file_key(
        file_access,
        _through_ws_temp_ed(str(row.get(KEY_OF_REFERENCE.column_name, ""))),
    )
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    purchmt_ba998_free(file_access)


def purchmt_ba060_process_start(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    connection: object,
) -> None:
    """``ba060-Process-Start.`` [common/purchMT.cbl:L776-L879].

    ANOMALY ``N-start-guard-998-vs-997``. The handler's own flat-file start rejects the
    identical condition with 998 and leaves ``FS-Reply`` untouched
    [common/acas022.cbl:L500-L502]; the bridge uses 997 and sets both. Two different
    reports for one input error, in one handler.

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record; its key field supplies the predicate.
        dal_common: The logging switches.
        connection: The open handle.
    """
    access_type = int(file_access.access_type)
    if (
        access_type < int(AccessType.EQUAL_TO)
        or access_type > int(AccessType.NOT_LESS_THAN)
    ):
        # [common/purchMT.cbl:L780-L784]. ANOMALY N-start-guard-998-vs-997.
        _status(file_access, FsReply.ERROR, WeError.ACCESS_TYPE_WRONG)
        return
    if _CURSORS.state_for(TABLE, _KEY_ORDER_SLOT).cursor_active():
        purchmt_ba998_free(file_access)
    relation = MostRelation.for_access_type(access_type)
    _RESULT_POINTER.most_relation = relation
    key_value = _purch_rec_key(purch)
    clause = (
        f"{_QUOTED_KEY_COLUMN}{relation.padded.strip()}%s"
        f" ORDER BY {_QUOTED_KEY_COLUMN} ASC  "
    )
    _log_where(file_access, clause)
    _file_key(file_access, key_value)
    if dal_common.sw_testing_2 == 1:
        _trace("purchMT ba060: %s", clause)
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba060-Process-Start"])
    statement = f"SELECT * FROM {_QUOTED_TABLE} WHERE {clause};"
    rows, error = _mysql_1210_command_then_store(
        connection, statement, (key_value,), file_access
    )
    count = _RESULT_POINTER.store_result(rows)
    slot = _CURSORS.state_for(TABLE, _KEY_ORDER_SLOT)
    if count != 0:
        slot.set_cursor_active()
    if count == 0:
        errno, sqlstate, message = _driver_error_fields(error)
        _move_sql_state(file_access, sqlstate)
        if errno != _ERRNO_SUCCESS:
            _move_sql_error(file_access, errno, message)
            _status(file_access, FsReply.INVALID_KEY_ON_START, WeError.SUCCESS)
            return
        # ANOMALY N-start-silent-noop: no status is written on this path at all. Control
        # reaches `go to ba999-end` [common/purchMT.cbl:L879] with the caller's incoming
        # pair intact.
        return
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    _file_key(
        file_access,
        f"{relation.padded}{key_value} got ="
        f"{count % (10**_WS_TEMP_ED_DIGITS):010d} recs",
    )


def purchmt_ba070_process_write(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    connection: object,
) -> None:
    """``ba070-Process-Write.`` [common/purchMT.cbl:L883-L908].

    The duplicate-key test is the three-way one [common/purchMT.cbl:L899-L901] - error
    1062, error 1022, or SQL state ``23000`` - which is exactly what
    :func:`~acas_posting.dal.status.is_duplicate_key_bridge_level` implements. A
    duplicate reports 22.

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record, read into the host variables.
        dal_common: The logging switches.
        connection: The open handle.
    """
    host_variables = bb000_hv_load(purch)
    _file_key(file_access, _purch_rec_key(purch))
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    _clear_sql_error(file_access)
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba070-Process-Write"])
    affected, error = bb200_insert(
        host_variables, file_access, dal_common, connection=connection
    )
    if affected != 1:
        errno, sqlstate, message = _driver_error_fields(error)
        _move_sql_state(file_access, sqlstate)
        if errno != _ERRNO_SUCCESS:
            _move_sql_error(file_access, errno, message)
            if is_duplicate_key_bridge_level(
                file_access.logging_data.sql_err,
                file_access.logging_data.sql_state,
            ):
                file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
            else:
                file_access.fs_reply = int(FsReply.ERROR)
        # ANOMALY N-write-masked-failure: when the client reports no error the `if`
        # above does nothing, and the zero set on entry stands.


def purchmt_ba080_process_delete(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    connection: object,
) -> None:
    """``ba080-Process-Delete.`` [common/purchMT.cbl:L910-L963].

    Every other statement in this bridge appends ``";" X"00"`` [common/purchMT.cbl:L544,
    :L697, :L846, :L1051] and the two builders do the same. This one appends only the
    null terminator. Reproduced.

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record; its key field supplies the predicate.
        dal_common: The logging switches.
        connection: The open handle.
    """
    key_value = _purch_rec_key(purch)
    clause = _where_on_primary_key("=")
    _file_key(file_access, key_value)
    _log_where(file_access, clause)
    if dal_common.sw_testing_2 == 1:
        _trace("purchMT ba080: %s", clause)
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba080-Process-Delete"])
    # No terminating `;` - ANOMALY N-delete-no-semicolon.
    statement = f"DELETE FROM {_QUOTED_TABLE} WHERE {clause}"
    affected, error = _mysql_1210_command(
        connection, statement, (key_value,), file_access
    )
    if affected != 1:
        errno, sqlstate, message = _driver_error_fields(error)
        _move_sql_state(file_access, sqlstate)
        if errno != _ERRNO_SUCCESS:
            _move_sql_error(file_access, errno, message)
            _status(
                file_access, FsReply.ERROR, WeError.DELETE_SQLSTATE_NOT_00000
            )
        # `go to ba999-End` [common/purchMT.cbl:L957] - Class 2.
        return
    _clear_sql_error(file_access)
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)


def purchmt_ba090_process_rewrite(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    connection: object,
) -> None:
    """``ba090-Process-Rewrite.`` [common/purchMT.cbl:L965-L1008].

    ANOMALY ``N-rewrite-no-entry-clear``. Unlike the write, which zeroes the status pair
    and the SQL pair on entry [common/purchMT.cbl:L886-L888], this paragraph clears
    NOTHING before issuing the update [common/purchMT.cbl:L967-L986]. The clear happens
    only on the success path [common/purchMT.cbl:L1005-L1007].

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record, read into the host variables.
        dal_common: The logging switches.
        connection: The open handle.
    """
    host_variables = bb000_hv_load(purch)
    key_value = _purch_rec_key(purch)
    _file_key(file_access, key_value)
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba090-Process-Rewrite"])
    clause = _where_on_primary_key("=")
    _log_where(file_access, clause)
    affected, error = bb300_update(
        host_variables,
        clause,
        key_value,
        file_access,
        dal_common,
        connection=connection,
    )
    if dal_common.sw_testing_2 == 1:
        _trace("purchMT ba090: %s", clause)
    if affected != 1:
        errno, sqlstate, message = _driver_error_fields(error)
        _move_sql_state(file_access, sqlstate)
        if errno != _ERRNO_SUCCESS:
            _move_sql_error(file_access, errno, message)
            _status(
                file_access, FsReply.ERROR, WeError.REWRITE_SQLSTATE_NOT_00000
            )
        return
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    _clear_sql_error(file_access)


def purchmt_ba140_process_read_next(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    connection: object,
) -> None:
    """``ba140-Process-Read-Next.`` [common/purchMT.cbl:L1010-L1085].

    ANOMALY ``N-lowkey-quoting-split``. ``ba040`` writes its low key as ``'"0000000"'``
    and so lands ``"0000000"`` WITH quotes in the statement [common/purchMT.cbl:L522];
    this paragraph writes ``"0000000"``, a COBOL literal, and so lands the bare token
    ``0000000`` [common/purchMT.cbl:L1029].

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record, filled by the fetch that follows.
        dal_common: The logging switches.
        connection: The open handle.
    """
    state = _CURSORS.state_for(TABLE, _NAME_ORDER_SLOT)
    if state.cursor_not_active():
        # `set KOR-x1 to 1` then the offset and length moves
        # [common/purchMT.cbl:L1019-L1021].
        order_term = NAME_ORDER.order_terms[0]
        clause = (
            f"{_QUOTED_KEY_COLUMN} >= {_NAME_ORDER_LOW_KEY}"
            f" ORDER BY {quote_identifier(order_term.column_name)}"
            f" {order_term.direction}"
        )
        _log_where(file_access, clause)
        _stamp(
            file_access, BRIDGE_PARAGRAPH_NUMBERS["ba140-Process-Read-Next"]
        )
        statement = f"SELECT * FROM {_QUOTED_TABLE} WHERE {clause};"
        # No value is bound: the low key is a frozen literal, inlined so that N-lowkey-
        # quoting-split survives - see :data:`_NAME_ORDER_LOW_KEY`.
        rows, error = _mysql_1210_command_then_store(
            connection, statement, (), file_access
        )
        count = _RESULT_POINTER.store_result(rows)
        _file_key(file_access, _NAME_ORDER_LOW_KEY)
        if dal_common.sw_testing_2 == 1:
            _trace("purchMT ba140: %s", clause)
        if count == 0:
            errno, sqlstate, message = _driver_error_fields(error)
            _move_sql_state(file_access, sqlstate)
            if errno != _ERRNO_SUCCESS:
                _move_sql_error(file_access, errno, message)
            fs_reply, we_error = end_of_file_status()
            _status(file_access, fs_reply, we_error)
            _file_key(file_access, "No Data")
            purchmt_ba999_end(file_access, dal_common)
            return
        state.set_cursor_active()
        _file_key(
            file_access, _count_rows_file_key(count, " recs in NAME order")
        )
        purchmt_ba999_end(file_access, dal_common)
    purchmt_ba141_reread(file_access, purch, dal_common)


def purchmt_ba141_reread(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba141-Reread.`` [common/purchMT.cbl:L1087-L1167].

    "If here cursor is set (even from start), so get the next row"
    [common/purchMT.cbl:L1089]. The name-ordered twin of
    :func:`purchmt_ba041_reread`, and identical to it in every respect except three,
    each of which is reproduced.

    Args:
        file_access: The block whose status and logging data are written.
        purch: The caller's record; the unload writes into it on success only.
        dal_common: The logging switches.
    """
    _log_where(file_access, "")
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba141-Reread"])
    state = _CURSORS.state_for(TABLE, _NAME_ORDER_SLOT)
    row = _RESULT_POINTER.fetch_record()
    if row is None:
        fs_reply, we_error = end_of_file_status()
        _status(file_access, fs_reply, we_error)
        _file_key(file_access, "EOF")
        state.set_cursor_not_active()
        purchmt_ba999_end(file_access, dal_common)
        return
    if _RESULT_POINTER.count_rows == 0:  # pragma: no cover - a row implies rows
        _initialize_purch_rec(purch, with_filler=True)
        _file_key(file_access, "EOF2")
        fs_reply, we_error = end_of_file_status()
        _status(file_access, fs_reply, we_error)
        state.set_cursor_not_active()
        purchmt_ba999_end(file_access, dal_common)
        return
    if int(file_access.fs_reply) == int(FsReply.END_OF_FILE):
        # ANOMALY N-sticky-eof [common/purchMT.cbl:L1158-L1162].
        state.set_cursor_not_active()
        _file_key(file_access, "EOF3")
        purchmt_ba999_end(file_access, dal_common)
        return
    bb100_unload_hvs(_host_variables_from_row(row), purch)
    _file_key(file_access, str(row.get(KEY_OF_REFERENCE.column_name, "")))
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    purchmt_ba999_end(file_access, dal_common)


def purchmt_ba100_bad_function(file_access: FileAccess) -> None:
    """``ba100-Bad-Function.`` [common/purchMT.cbl:L1169-L1175].

    ANOMALY ``N-badfunction-990-vs-999``. The bridge reports ``(99, 990)``; the
    handler's own ``aa100-Bad-Function`` reports ``(99, 999)`` for the identical
    condition [common/acas022.cbl:L576-L577]. One handler, one invalid function code,
    two different ``We-Error`` values, decided by which store is configured. Neither is
    reconciled.

    Args:
        file_access: The block whose status pair is written.
    """
    _status(file_access, FsReply.ERROR, WeError.UNKNOWN_UNEXPECTED)


def purchmt_ba998_free(file_access: FileAccess) -> None:
    """``ba998-Free.`` [common/purchMT.cbl:L1181-L1191].

    "Free the results memory / Only used for read-indexed as we do not know when an app
    has finished with a cursor" [common/purchMT.cbl:L1183-L1186] - the maintainer's own
    statement of why the read-indexed path frees and the walks do not.

    Args:
        file_access: The block whose paragraph stamp is written.
    """
    _stamp(file_access, BRIDGE_PARAGRAPH_NUMBERS["ba998-Free"])
    _RESULT_POINTER.free_result()
    _CURSORS.state_for(TABLE, _KEY_ORDER_SLOT).set_cursor_not_active()


def purchmt_ba999_end(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba999-end.`` [common/purchMT.cbl:L1193-L1198].

    ANOMALY ``N-bridge-logs-handler-does-not``. The handler's own ``Ca-Process-Logs``
    carries the comment "Not called on DAL access as it does it already" on its label
    line [common/acas022.cbl:L671], and this is what it means.

    Args:
        file_access: The block passed to the logger.
        dal_common: Carries ``SW-Testing``, whose ``88 Testing-1 value 1``
            [copybooks/Test-Data-Flags.cob:L11] gates the call. The frozen copybook
            declares it ``value 1``, so logging is ON as shipped.
    """
    # `if Testing-1` [common/purchMT.cbl:L1195]. The Python record exposes no condition-
    # name predicate, so the 88 is tested inline [copybooks/Test-Data-
    # Flags.cob:L10-L11].
    if dal_common.sw_testing == 1:
        purchmt_ca_process_logs(file_access, dal_common)


def purchmt_ba999_exit() -> None:
    """``ba999-exit.`` [common/purchMT.cbl:L1200-L1201].

    ``exit program.`` - the bridge's return to its caller. Modelled as a named no-op so
    that the paragraph-to-function mapping rule R-5 requires has an entry for it, and so
    that a reader following the frozen listing finds every label.
    """
    return


def bb200_insert(
    host_variables: HostVariables,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    connection: object,
) -> tuple[int, BaseException | None]:
    """``bb200-Insert Section.`` [common/purchMT.cbl:L1292-L1680].

    Assembles ``INSERT INTO `PULEDGER-REC` SET `` [common/purchMT.cbl:L1302-L1303]
    followed by all TWENTY-NINE columns in table ordinal order, each rendered through
    the edit field and its declared window, separated by ``', '``
    [common/purchMT.cbl:L1313], and terminated with ``";" X"00"``
    [common/purchMT.cbl:L1671-L1673].

    Args:
        host_variables: The loaded ``TD-PULEDGER-REC`` group.
        file_access: The block the shared failure paragraph writes to.
        dal_common: The logging switches.
        connection: The open handle.

    Returns:
        The affected-row count and the driver failure, if any. The caller's ``not = 1``
            test decides what the status becomes; see
            :func:`purchmt_ba070_process_write` and anomaly ``N-write-masked-failure``.
    """
    assignments = ", ".join(
        f"{quote_identifier(column)}=%s" for column in COLUMN_ORDER
    )
    statement = f"INSERT INTO {_QUOTED_TABLE} SET {assignments};"
    values = host_variables.rendered_values()
    if len(values) != len(COLUMN_ORDER):  # pragma: no cover - guarded on import
        raise AssertionError(
            f"{BRIDGE} bb200-Insert renders {len(values)} values for "
            f"{len(COLUMN_ORDER)} columns"
        )
    if dal_common.sw_testing_2 == 1:
        _trace("purchMT bb200: %s", statement)
    return _mysql_1210_command(connection, statement, values, file_access)


def bb300_update(
    host_variables: HostVariables,
    clause: str,
    key_value: str,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    connection: object,
) -> tuple[int, BaseException | None]:
    """``bb300-Update Section.`` [common/purchMT.cbl:L1682-L2074].

    ANOMALY ``N-update-key-trim-split``. The clause reaches the statement through
    ``FUNCTION TRIM (WS-Where (1:J))`` [common/purchMT.cbl:L2064] while ``ba090`` placed
    the very same text into ``WS-Log-Where`` untrimmed [common/purchMT.cbl:L985].

    Args:
        host_variables: The loaded ``TD-PULEDGER-REC`` group.
        clause: The predicate ``ba090`` assembled, untrimmed.
        key_value: The value bound into that predicate.
        file_access: The block the shared failure paragraph writes to.
        dal_common: The logging switches.
        connection: The open handle.

    Returns:
        The affected-row count and the driver failure, if any.
    """
    assignments = ", ".join(
        f"{quote_identifier(column)}=%s" for column in COLUMN_ORDER
    )
    statement = (
        f"UPDATE {_QUOTED_TABLE} SET {assignments} WHERE {clause.strip()};"
    )
    values = host_variables.rendered_values()
    if len(values) != len(COLUMN_ORDER):  # pragma: no cover - guarded on import
        raise AssertionError(
            f"{BRIDGE} bb300-Update renders {len(values)} values for "
            f"{len(COLUMN_ORDER)} columns"
        )
    if dal_common.sw_testing_2 == 1:
        _trace("purchMT bb300: %s", statement)
    return _mysql_1210_command(
        connection, statement, (*values, key_value), file_access
    )


def purchmt_ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` [common/purchMT.cbl:L2076-L2080].

    The bridge's logging paragraph, whose COBOL body is
    ``call "fhlogger" using File-Access ACAS-DAL-Common-data``
    [common/purchMT.cbl:L2079-L2080]. ``fhlogger`` is a COBOL program and rule
    R-1 forbids calling it, so the record it would have written is emitted
    natively instead: the same eleven ``Logging-Data`` fields plus the status
    pair, at debug level, reaching no table.

    AAP section 0.1.1 places this transformation explicitly - diagnostics with no
    database effect become log lines - and section 0.2.2 puts ``common/fhlogger``
    ``.cbl`` out of scope, so there is nothing to reimplement beyond the record
    itself. It is emitted through
    :func:`acas_posting.dal.status.log_file_handler_record`, THE ONE ADAPTER every
    handler in this package shares, so the single legacy log this cycle produces
    reads the same whichever table wrote it.

    THREE FIELDS ARE WITHHELD. ``WS-File-Key`` is ``PURCH-KEY``, the supplier
    code; ``WS-Log-Where`` is a predicate carrying it as a literal; ``SQL-Msg`` is
    driver free text. All three are CWE-532 in a log and none is needed to act on a
    failure, and ``redact_for_log`` was escaping the first two rather than removing
    them.

    ``Log-File-Rec-Written`` IS NOW ADVANCED, by the adapter, modulo one
    million - the range of the frozen ``pic 9(6)``
    [copybooks/Test-Data-Flags.cob:L20]. Leaving it alone was wrong: the counter
    lives in ``ACAS-DAL-Common-data``, which the CALLER owns and carries across
    calls, so it is not the COBOL program's private state but part of the linkage
    this module is reproducing.

    Args:
        file_access: The block whose fields make up the record.
        dal_common: Carried for signature fidelity with the COBOL parameter list; the
            switch that gated this call was already tested by :func:`purchmt_ba999_end`.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program=BRIDGE_PROG_NAME,
        paragraph="Ca-Process-Logs",
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


def purchmt_ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    purch: WsPurchRecord,
    *,
    system_record: SystemRecord | None,
    transport: TransportSecurity | None,
) -> None:
    """``ba-ACAS-DAL-Process section.`` [common/purchMT.cbl:L389-L445].

    The bridge's only section entry.

    Args:
        file_access: The block carrying the function code, the access type and every
            status and diagnostic field.
        dal_common: The logging switches.
        purch: The caller's record.
        system_record: Supplies the credentials on the open path only.
        transport: The transport policy for the open path only.
    """
    purchmt_ba010_initialise(file_access)
    function = int(file_access.file_function)
    if function == int(FileFunction.OPEN):
        purchmt_ba020_process_open(
            file_access, system_record=system_record, transport=transport
        )
        return
    if function == int(FileFunction.CLOSE):
        purchmt_ba030_process_close(file_access)
        return
    # `01 WS-MYSQL-CONNECTION` is the bridge's own working storage, and the bridge
    # reaches its statement sites with whatever that field holds - it never tests it.
    connection = _CONNECTION
    if function == int(FileFunction.READ_NEXT):
        purchmt_ba040_process_read_next(
            file_access, purch, dal_common, connection
        )
        return
    if function == int(FileFunction.READ_INDEXED):
        purchmt_ba050_process_read_indexed(
            file_access, purch, dal_common, connection
        )
        return
    if function == int(FileFunction.WRITE):
        purchmt_ba070_process_write(
            file_access, purch, dal_common, connection
        )
        purchmt_ba999_end(file_access, dal_common)
        return
    if function == int(FileFunction.RE_WRITE):
        purchmt_ba090_process_rewrite(
            file_access, purch, dal_common, connection
        )
        purchmt_ba999_end(file_access, dal_common)
        return
    if function == int(FileFunction.DELETE):
        purchmt_ba080_process_delete(
            file_access, purch, dal_common, connection
        )
        purchmt_ba999_end(file_access, dal_common)
        return
    if function == int(FileFunction.START):
        purchmt_ba060_process_start(
            file_access, purch, dal_common, connection
        )
        purchmt_ba999_end(file_access, dal_common)
        return
    if function == int(FileFunction.READ_BY_NAME):
        # ANOMALY N-31-two-meanings [common/purchMT.cbl:L441-L442]. The bridge gives
        # code 31 its own name-ordered paragraph where the handler folds it into an
        # ordinary read-next.
        purchmt_ba140_process_read_next(
            file_access, purch, dal_common, connection
        )
        return
    # `when other` [common/purchMT.cbl:L443-L444]. Codes 6, 13, 15, 32, 33 and 34 all
    # land here.
    purchmt_ba100_bad_function(file_access)
    purchmt_ba999_end(file_access, dal_common)


def purch_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    purch: WsPurchRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
) -> tuple[int, int]:
    """``call "purchMT" using File-Access ACAS-DAL-Common-data WS-Purch-Record``.

    That block names the schema and the table, and declares that the group which follows
    is the host-variable group for it.

    Args:
        file_access: The ``File-Access`` block. Read for ``File-Function``, ``Access-
            Type`` and ``File-Key-No``; written with the status pair and the whole
            ``Logging-Data`` sub-block.
        dal_common: ``ACAS-DAL-Common-data``, carrying the two testing switches.
        purch: The caller's record, read on the write and rewrite paths and written on
            the read paths.
        system_record: The system record whose ``RDBMS`` fields supply the credentials.
            Consulted on the open path only.
        transport: The transport policy handed to
            :func:`~acas_posting.dal.connection.mysql_1000_open`. Consulted on the open
            path only.

    Returns:
        The ``(Fs-Reply, We-Error)`` pair, as a convenience for callers that prefer a
            return value to reading the record back.
    """
    purchmt_ba_acas_dal_process(
        file_access,
        dal_common,
        purch,
        system_record=system_record,
        transport=transport,
    )
    purchmt_ba999_exit()
    return int(file_access.fs_reply), int(file_access.we_error)


def purchmt_ca_exit() -> None:
    """``ca-Exit.`` [common/purchMT.cbl:L2082].

    Written on one line as ``ca-Exit. exit.`` - a plain ``exit``, not ``exit section``,
    exactly as the handler's own ``ca-Exit`` is [common/acas022.cbl:L677]. Both are
    modelled as named no-ops so that R-5's paragraph-to-function mapping is complete.
    """
    return


# The handler - `acas022`, the ISAM half. `aa-Process-Flat-File Section.`
# [common/acas022.cbl:L287] onwards. Every paragraph below is the flat-file path,
# reached only when `FS-Cobol-Files-Used` holds [common/acas022.cbl:L316].

_COBOL_FILE_STATUS: int = 0

_COBOL_FILE_EOF: Final[int] = 1

_PL905: Final[str] = "PL905 Program Error: Temp rec = "
_PL901: Final[str] = "PL901 Note error and hit return"

#: The two function codes the key guard's FIRST arm covers - ``when 4`` and ``when 9``
#: share one body and one 998 [common/acas022.cbl:L299-L305].
_KEY_GUARDED_READ_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {int(FileFunction.READ_INDEXED), int(FileFunction.START)}
)

#: ``when 3`` and ``when 31`` [common/acas022.cbl:L343-L345]. ANOMALY ``N-read-by-name-
#: is-read-next``: 31 falls through into 3 on the ISAM path and is served by the
#: ordinary read-next paragraph.
_AA_READ_NEXT_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {int(FileFunction.READ_NEXT), int(FileFunction.READ_BY_NAME)}
)

#: The five function arms of ``aa045-Eval-Keys`` [common/acas022.cbl:L450-L454].
_AA045_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
        int(FileFunction.DELETE),
        int(FileFunction.START),
    }
)

#: The four relations ``aa060-Process-Start`` has a longhand block for, in the frozen
#: order [common/acas022.cbl:L507-L534].
_AA060_RELATIONS: Final[tuple[int, ...]] = (
    int(AccessType.EQUAL_TO),
    int(AccessType.LESS_THAN),
    int(AccessType.GREATER_THAN),
    int(AccessType.NOT_LESS_THAN),
)

#: ``03 Purch-Address.`` with ``05 Purch-Addr1 pic x(48)`` and ``05 Purch-Addr2 pic
#: x(48)`` [copybooks/wspl.cob:L23-L25].
_ADDRESS_GROUP_BYTES: Final[int] = 96

#: ``Purch-Stats-Date pic 9(4)`` [copybooks/wspl.cob:L53] plus ``filler pic x(12)``
#: [copybooks/wspl.cob:L54].
_TRAILING_UNMAPPED_BYTES: Final[int] = 4 + 12


def _cobol_storage_bytes(binding: _ColumnBinding) -> int:
    """The bytes one copybook field occupies, by its declared usage.

    Needed by :func:`ba012_test_ws_rec_size_2`, whose guard compares ``function Length``
    of two records [common/acas022.cbl:L610-L615].

    Args:
        binding: The column binding carrying the copybook's usage, digit count and
            character length.

    Returns:
        The field's storage size in bytes.

    Raises:
        ValueError: If the usage is one this table does not declare. The frozen copybook
            declares exactly seven, so this cannot fire for ``PULEDGER-REC``.
    """
    usage = binding.copybook_usage
    if usage == "GROUP":
        return _ADDRESS_GROUP_BYTES
    if usage == "ALPHANUMERIC":
        return binding.copybook_width
    if usage == "DISPLAY":
        return binding.copybook_digits
    if usage in _BINARY_STORAGE_BYTES:
        return _BINARY_STORAGE_BYTES[usage]
    if usage == "COMP-3":
        return (binding.copybook_digits + 2) // 2
    if usage == "COMP":
        for digits, width in ((4, 2), (9, 4), (18, 8)):
            if binding.copybook_digits <= digits:
                return width
    raise ValueError(
        f"{COPYBOOK} declares no field of usage {usage!r}; "
        f"{binding.column} cannot be sized"
    )


#: ``function Length (WS-Purch-Record)`` and ``function length (Purch-Record)``
#: [common/acas022.cbl:L610-L615] - ONE value, because the two records are IDENTICAL.
#: Verified field by field.
_RECORD_DECLARED_LENGTH: Final[int] = (
    sum(_cobol_storage_bytes(binding) for binding in _BINDINGS)
    + _TRAILING_UNMAPPED_BYTES
)


def _reset_cobol_file_status(file_access: FileAccess) -> None:
    """``move zero to Cobol-File-Status``.

    Args:
        file_access: Accepted so that every paragraph's helper calls read alike.
    """
    global _COBOL_FILE_STATUS
    _COBOL_FILE_STATUS = 0
    del file_access


def _set_cobol_file_eof(file_access: FileAccess) -> None:
    """``set Cobol-File-EoF to true`` AND ``move 1 to Cobol-File-Status``.

    [common/acas022.cbl:L433-L434]. The frozen source does BOTH, the second under the
    comment "JIC above dont work :)" - a condition-name ``SET`` and a literal ``MOVE``
    of the value that condition name tests for, one after the other.

    Args:
        file_access: Accepted for call-site symmetry; see
            :func:`_reset_cobol_file_status`.
    """
    global _COBOL_FILE_STATUS
    _COBOL_FILE_STATUS = _COBOL_FILE_EOF
    del file_access


def _cobol_file_eof() -> bool:
    """``if Cobol-File-Eof`` [common/acas022.cbl:L421].

    Returns:
        Whether the handler's own end-of-file flag is set.
    """
    return _COBOL_FILE_STATUS == _COBOL_FILE_EOF


def _copy_purch_record(source: WsPurchRecord, target: WsPurchRecord) -> None:
    """``move Purch-Record to WS-Purch-Record`` and its three reverses.

    Args:
        source: The sending record.
        target: The receiving record, mutated in place - the COBOL ``MOVE`` writes into
            storage the caller already holds.
    """
    for field in dataclasses.fields(source):
        value = getattr(source, field.name)
        if dataclasses.is_dataclass(value):
            nested = getattr(target, field.name)
            for sub in dataclasses.fields(value):
                setattr(nested, sub.name, getattr(value, sub.name))
            continue
        setattr(target, field.name, value)
    _refresh_quarters_view(target)


def _move_spaces_to_purch_record(record: WsPurchRecord) -> None:
    """``move spaces to Purch-Record`` [common/acas022.cbl:L435, :L481].

    ANOMALY ``N-spaces-into-record``, reproduced literally.

    Args:
        record: The record to space-fill, mutated in place.
    """
    for binding in _BINDINGS:
        if binding.column == "PURCH-ADDRESS":
            _split_group_concatenation(record, " " * _ADDRESS_GROUP_BYTES)
            continue
        if binding.copybook_usage == "ALPHANUMERIC":
            _set_record_value(
                record, binding, " " * _cobol_storage_bytes(binding)
            )
            continue
        _set_record_value(record, binding, _space_bytes_as_number(binding))
    record.purch_stats_date = int(
        _space_bytes_as_number(_STATS_DATE_BINDING)
    )
    record.filler_l54 = " " * len(record.filler_l54)
    _refresh_quarters_view(record)


def _space_bytes_as_number(binding: _ColumnBinding) -> int | Decimal:
    """What a field full of ``0x20`` bytes decodes to, in that field's usage.

    Supports :func:`_move_spaces_to_purch_record`, which reproduces the group ``MOVE
    SPACES`` at [common/acas022.cbl:L435] rather than the ``initialize`` a sibling
    handler uses [common/acas019.cbl:L379].

    Args:
        binding: The field being space-filled.

    Returns:
        The decoded value, as an ``int`` for integer usages and a ``Decimal`` for scaled
            ones. Never a binary floating-point value (rule R-2).
    """
    usage = binding.copybook_usage
    if usage in _BINARY_STORAGE_BYTES:
        width = _BINARY_STORAGE_BYTES[usage]
        return int.from_bytes(
            b"\x20" * width, "big", signed=binding.copybook_signed
        )
    if usage == "DISPLAY":
        return 0
    if usage == "COMP":
        width = _cobol_storage_bytes(binding)
        raw = int.from_bytes(
            b"\x20" * width, "big", signed=binding.copybook_signed
        )
        return _scaled_from_raw(raw, binding)
    if usage == "COMP-3":
        digits = "".join("20" for _ in range(_cobol_storage_bytes(binding)))
        return _scaled_from_raw(
            int(digits[: binding.copybook_digits] or "0"), binding
        )
    raise ValueError(
        f"{binding.column} has usage {binding.copybook_usage!r}, which "
        f"MOVE SPACES cannot be modelled for"
    )


def _scaled_from_raw(raw: int, binding: _ColumnBinding) -> Decimal:
    """Place an implied decimal point in a raw integer, as ``V`` does.

    Args:
        raw: The integer the field's bytes decode to.
        binding: The field, carrying its scale.

    Returns:
        The value with the copybook's implied decimal point applied, exact.
    """
    if binding.copybook_scale == 0:
        return Decimal(raw)
    return Decimal(raw).scaleb(-binding.copybook_scale)


#: ``Purch-Stats-Date pic 9(4)`` [copybooks/wspl.cob:L53], the folder's only WRITE-
#: NOWHERE field.
_STATS_DATE_BINDING: Final[_ColumnBinding] = _ColumnBinding(
    column="PURCH-STATS-DATE",
    ordinal=0,
    attribute="purch_stats_date",
    host_variable="",
    kind="int",
    digits=4,
    scale=0,
    width=0,
    signed=False,
    copybook_signed=False,
    copybook_usage="DISPLAY",
    copybook_digits=4,
    copybook_scale=0,
    copybook_width=0,
    edit_start=0,
    edit_length=0,
    citation="[copybooks/wspl.cob:L53] - no host variable, no column",
    drift_details=(
        "declared in copybooks/wspl.cob:L53 and in the bridge's own record "
        "copy, absent from common/purchMT.cbl:L285-L313, from the load at "
        ":L1212-L1250, from the unload at :L1258-L1288 and from "
        "mysql/ACASDB.sql:L646-L677 - the folder's only write-nowhere field"
    ),
)


def _copy_rdbms_flat_statuses(
    system: SystemRecord, file_access: FileAccess
) -> None:
    """``move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses``.

    [common/acas022.cbl:L317], carrying the maintainer's own doubt on the same line:
    "needed for DAL? not JC/dbpre versions".

    Args:
        system: The source block, ``05 RDBMS-Flat-Statuses`` inside the system data
            block.
        file_access: The destination block.
    """
    source = system.system_data_block.rdbms_flat_statuses
    destination = file_access.fa_rdbms_flat_statuses
    destination.fa_file_system_used = int(source.file_system_used) % 10
    destination.fa_file_duplicates_in_use = (
        int(source.file_duplicates_in_use) % 10
    )


def aa020_process_open(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa020-Process-Open.`` [common/acas022.cbl:L363-L400].

    ``fn-input`` [common/acas022.cbl:L366-L372] reports ``35`` on failure - "file not
    found" - and then CLOSES the file it just failed to open [common/acas022.cbl:L370].
    ANOMALY ``N-close-after-failed-open``.

    Args:
        file_access: The block whose status, ``Cobol-File-Status`` stand-in and log key
            are written.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _file_key(file_access, "")
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa020-Process-Open"])
    access_type = int(file_access.access_type)
    if access_type == int(AccessType.INPUT):
        file_access.fs_reply = purchase_file.open_input() % 100
        if int(file_access.fs_reply) != 0:
            file_access.fs_reply = 35
            # ANOMALY N-close-after-failed-open [common/acas022.cbl:L370]; the status is
            # discarded.
            purchase_file.close()
            aa999_main_exit(file_access, dal_common)
            return
    elif access_type == int(AccessType.I_O):
        file_access.fs_reply = purchase_file.open_io() % 100
        if int(file_access.fs_reply) != 0:
            purchase_file.close()
            purchase_file.open_output()
            purchase_file.close()
            file_access.fs_reply = purchase_file.open_io() % 100
    elif access_type == int(AccessType.OUTPUT):
        file_access.fs_reply = purchase_file.open_output() % 100
    elif access_type == int(AccessType.EXTEND):
        _status(file_access, FsReply.ERROR, WeError.ACCESS_TYPE_WRONG)
        aa999_main_exit(file_access, dal_common)
        return
    # `move zeros to FS-Reply WE-Error.` is COMMENTED OUT at [common/acas022.cbl:L395],
    # dated 27/07/16 - a deliberate non-initialisation, left alone.
    _reset_cobol_file_status(file_access)
    _file_key(file_access, "OPEN Purchase Ledger File")
    if int(file_access.fs_reply) != 0:
        # ANOMALY N-open-999-vs-35-asymmetry [common/acas022.cbl:L398-L399].
        file_access.we_error = int(WeError.NOT_USED)
    aa999_main_exit(file_access, dal_common)


def aa030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa030-Process-Close.`` [common/acas022.cbl:L402-L413].

    ``aa999-main-exit`` is itself ``if Testing-1 perform Ca-Process-Logs``
    [common/acas022.cbl:L580-L582], so the close writes a log record through the switch
    and then writes a SECOND one UNCONDITIONALLY, with ``File-Function`` and ``Access-
    Type`` zeroed - the "close log file" sentinel the logger reads.

    Args:
        file_access: The block whose status and log key are written, and whose ``File-
            Function`` and ``Access-Type`` this paragraph ZEROES.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa030-Process-Close"])
    _file_key(file_access, "")
    file_access.fs_reply = purchase_file.close() % 100
    # `move zeros to FS-Reply WE-Error.` commented out at [common/acas022.cbl:L406] -
    # the same deliberate non-initialisation.
    _reset_cobol_file_status(file_access)
    _file_key(file_access, "CLOSE Purchase Ledger File")
    aa999_main_exit(file_access, dal_common)
    file_access.file_function = 0
    file_access.access_type = 0
    ca_process_logs(file_access, dal_common)
    aa_main_exit()


def aa040_process_read_next(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas022.cbl:L415-L445].

    The paragraph function code 3 reaches - AND function code 31, because the
    handler's dispatch folds ``when 31`` into ``when 3``
    [common/acas022.cbl:L343-L345]. On the ISAM path there is therefore no
    name-ordered read at all, no different key and no different call; anomaly
    ``N-31-two-meanings`` is the fact that the BRIDGE does have one
    [common/purchMT.cbl:L441-L442]. Both halves are reproduced, each in its own
    place, and neither is made to agree with the other.

    ANOMALY ``N-stop``. The end-of-file pre-test carries a bare
    ``stop "Cobol File EOF"`` annotated "for testing"
    [common/acas022.cbl:L427] - a debugging statement that halts the run in
    shipped source, left inside a branch that also sets a clean end-of-file
    status. It is SPLIT, per AAP section 0.3.4: the DISPLAY half becomes one record
    at ERROR through :func:`acas_posting.dal.status.log_cobol_stop`, identical in
    wording and level to every sibling handler's, and the HALT half is deliberately
    omitted - a pause has no database effect, and reproducing it would make the
    migrated cycle unrunnable. The branch's status, log key and control transfer are
    all preserved, and the omission is recorded here and in
    ``docs/migration/anomaly-log.md``.

    ANOMALY ``N-spaces-into-key`` [common/acas022.cbl:L424]. The pre-test moves
    SPACES into ``Purch-Key``, the ISAM record's ``pic x(7)`` key. Spaces, not
    zeros - and the low key every other part of the system uses is ``"0000000"``.
    Reproduced literally.

    ANOMALY ``N-spaces-into-record`` [common/acas022.cbl:L435]. At end of file the
    paragraph does ``move spaces to Purch-Record``, where the sibling handler in
    the same position does ``initialize``
    [common/acas019.cbl:L379]. ``INITIALIZE`` sets numeric fields to zero and
    alphanumeric fields to spaces; ``MOVE SPACES`` writes the space character over
    the whole record, INCLUDING the ``binary-char``, ``binary-long`` and
    ``comp-3`` fields, whose bytes then decode to whatever the space bit pattern
    means in that usage. Reproduced literally rather than corrected.

    ANOMALY ``N-double-zero`` [common/acas022.cbl:L443]. The success path zeroes
    BOTH ``FS-Reply`` and ``WE-Error`` where the sibling zeroes only ``WE-Error``
    [common/acas019.cbl:L387].

    ANOMALY ``N-no-aa041``. There is no ``aa041-*`` paragraph in this handler at
    all - the log key is built by a direct move of the record key
    [common/acas022.cbl:L442] - even though its own SALES mirror ``acas012`` has
    an ``aa041-Reread``. No such function is added here for symmetry.

    Args:
        file_access: The block whose status and log key are written.
        purch: The caller's record, filled on success.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa040-Process-Read-Next"])
    if _cobol_file_eof():
        # `if Cobol-File-Eof` [common/acas022.cbl:L421-L428].
        _status(file_access, FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
        purchase_file.record.ws_purch_key = " " * KEY_OF_REFERENCE.kor_length
        file_access.logging_data.sql_err = " " * 5
        file_access.logging_data.sql_msg = " " * 512
        # `stop "Cobol File EOF"` [common/acas022.cbl:L427] - N-stop.
        #  ONE ERROR, THROUGH THE ONE REPORTER, at the SAME LEVEL and in the
        #  same words as every sibling handler that carries this statement. `STOP`
        #  with a literal DISPLAYS the literal and then waits, so the display is a
        #  record and only the WAIT is the omission. Emitting nothing here, while
        #  acas006 and acas007 logged it at WARNING, acas012 at INFO, acas016 at
        #  DEBUG and acas019 at ERROR, meant one event had five different renderings
        #  and, in this module, none at all.
        log_cobol_stop(
            _LOG,
            program=PROG_NAME,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas022.cbl:L427]",
        )
        aa999_main_exit(file_access, dal_common)  # Class 3.
        return
    # `read Purchase-File next record` [common/acas022.cbl:L431].
    file_access.fs_reply = purchase_file.read_next() % 100
    if int(file_access.fs_reply) != 0:
        _status(file_access, FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
        _set_cobol_file_eof(file_access)
        _move_spaces_to_purch_record(purchase_file.record)
        _file_key(file_access, "EOF")
        aa999_main_exit(file_access, dal_common)
        return
    if int(file_access.fs_reply) != 0:
        # `if FS-Reply not = zero go to aa999-main-exit.` [common/acas022.cbl:L439-L440]
        # - unreachable in practice, because the `at end` branch above is the only thing
        # that sets it non-zero and it jumps out.
        aa999_main_exit(file_access, dal_common)
        return
    _copy_purch_record(purchase_file.record, purch)
    _file_key(file_access, purch.ws_purch_key)
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    aa999_main_exit(file_access, dal_common)


def aa045_eval_keys(
    file_access: FileAccess,
    purch: WsPurchRecord,
    purchase_file: PurchaseFile,
) -> None:
    """``aa045-Eval-Keys.`` [common/acas022.cbl:L446-L464].

    *> The next block will never get executed unless performed so is it needed ?

    Args:
        file_access: The block whose log key is written.
        purch: The caller's record, supplying the key.
        purchase_file: The ISAM store, whose record's own key field is the SECOND
            destination of the ``when 1`` move.
    """
    function = int(file_access.file_function)
    if function in _AA045_FUNCTIONS:
        if int(file_access.logging_data.file_key_no) == ONLY_KEY_NUMBER:
            _file_key(file_access, purch.ws_purch_key)
            purchase_file.record.ws_purch_key = _purch_rec_key(purch)
        else:
            # `when other move spaces to WS-File-Key` [common/acas022.cbl:L459-L460].
            _file_key(file_access, "")
        return
    _file_key(file_access, "")


def aa050_process_read_indexed(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas022.cbl:L466-L487].

    ANOMALY ``N-readindexed-23``, the handler half. Not found reports ``21`` in BOTH
    fields here [common/acas022.cbl:L475] where the bridge reports ``23`` with ``We-
    Error`` zeroed [common/purchMT.cbl:L703-L705], under the bridge maintainer's own
    note that it "could also be 21 or 14".

    Args:
        file_access: The block whose status and log key are written.
        purch: The caller's record, filled on success and SPACE-FILLED on a miss.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa050-Process-Read-Indexed"])
    aa045_eval_keys(file_access, purch, purchase_file)
    _reset_cobol_file_status(file_access)
    if int(file_access.logging_data.file_key_no) == ONLY_KEY_NUMBER:
        status = purchase_file.read_by_key(
            _purch_rec_key(purchase_file.record)
        )
        if status != 0:
            _status(file_access, FsReply.INVALID_KEY_ON_START, 21)
        else:
            file_access.fs_reply = 0
        if int(file_access.fs_reply) == 0:
            _copy_purch_record(purchase_file.record, purch)
            _file_key(file_access, _purch_rec_key(purchase_file.record))
        else:
            _move_spaces_to_purch_record(purch)
        aa999_main_exit(file_access, dal_common)
        return
    # Unreachable [common/acas022.cbl:L485-L487]; preserved.
    _status(file_access, FsReply.ERROR, WeError.FILE_KEY_NO_OUT_OF_RANGE)
    aa999_main_exit(file_access, dal_common)


def aa060_process_start(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa060-Process-Start.`` [common/acas022.cbl:L489-L535].

    "Check for Param error 1st on start WARNING Not logging starts"
    [common/acas022.cbl:L491] - and the warning is accurate: this paragraph is the only
    one in the handler that never writes a diagnostic of its own beyond the key.

    Args:
        file_access: The block whose status and log key are written.
        purch: The caller's record, supplying the key.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa060-Process-Start"])
    # `move zeros to fs-reply WE-Error.` [common/acas022.cbl:L494-L495] - BEFORE the
    # guard, which is what makes N-start-guard-leaves-fs-reply-zero possible.
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    _reset_cobol_file_status(file_access)
    _file_key(file_access, purch.ws_purch_key)
    purchase_file.record.ws_purch_key = _purch_rec_key(purch)
    access_type = int(file_access.access_type)
    if (
        access_type < int(AccessType.EQUAL_TO)
        or access_type > int(AccessType.NOT_LESS_THAN)
    ):
        # `move 998 to WE-Error` ONLY [common/acas022.cbl:L500-L502]. Fs-Reply stays at
        # the zero set above - N-start-guard-leaves-fs-reply- zero.
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        aa999_main_exit(file_access, dal_common)
        return
    key_number = int(file_access.logging_data.file_key_no)
    for relation in _AA060_RELATIONS:
        if key_number == ONLY_KEY_NUMBER and access_type == relation:
            if purchase_file.start(relation) != 0:
                file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
            aa999_main_exit(file_access, dal_common)
            return
    aa999_main_exit(file_access, dal_common)


def aa070_process_write(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa070-Process-Write.`` [common/acas022.cbl:L537-L546].

    ``move WS-Purch-Record to Purch-Record`` [common/acas022.cbl:L539] then the write.
    The two layouts are field-for-field identical - verified by comparing
    ``copybooks/wspl.cob`` against ``copybooks/fdpl.cob`` picture clause by picture
    clause - so this move is a straight copy and not a reinterpretation.

    Args:
        file_access: The block whose status and log key are written.
        purch: The caller's record, copied into the file's record area.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa070-Process-Write"])
    _copy_purch_record(purch, purchase_file.record)
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    _reset_cobol_file_status(file_access)
    _file_key(file_access, _purch_rec_key(purchase_file.record))
    if purchase_file.write() != 0:
        file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    aa999_main_exit(file_access, dal_common)


def aa080_process_delete(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa080-Process-Delete.`` [common/acas022.cbl:L548-L558].

    ANOMALY ``N-delete-copies-whole-record``. The paragraph copies the ENTIRE caller
    record into the file's record area [common/acas022.cbl:L550] before deleting by key.

    Args:
        file_access: The block whose status and log key are written.
        purch: The caller's record, supplying the key - and, needlessly, the rest.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa080-Process-Delete"])
    _copy_purch_record(purch, purchase_file.record)
    purchase_file.record.ws_purch_key = _purch_rec_key(purch)
    _file_key(file_access, purch.ws_purch_key)
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    _reset_cobol_file_status(file_access)
    if purchase_file.delete() != 0:
        file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    aa999_main_exit(file_access, dal_common)


def aa090_process_rewrite(
    file_access: FileAccess,
    purch: WsPurchRecord,
    dal_common: AcasDalCommonData,
    purchase_file: PurchaseFile,
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas022.cbl:L560-L570].

    ``invalid key move 21 to FS-Reply`` [common/acas022.cbl:L568], against the bridge's
    ``(99, 994)`` [common/purchMT.cbl:L1000-L1001].

    Args:
        file_access: The block whose status and log key are written.
        purch: The caller's record, copied into the file's record area.
        dal_common: The logging switches.
        purchase_file: The caller's ISAM store.
    """
    _stamp(file_access, HANDLER_PARAGRAPH_NUMBERS["aa090-Process-Rewrite"])
    _copy_purch_record(purch, purchase_file.record)
    _file_key(file_access, _purch_rec_key(purchase_file.record))
    _status(file_access, FsReply.SUCCESS, WeError.SUCCESS)
    _reset_cobol_file_status(file_access)
    if purchase_file.rewrite() != 0:
        file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
    aa999_main_exit(file_access, dal_common)


def aa100_bad_function(file_access: FileAccess) -> None:
    """``aa100-Bad-Function.`` [common/acas022.cbl:L572-L577].

    ANOMALY ``N-badfunction-990-vs-999``. ``(99, 999)`` here
    [common/acas022.cbl:L576-L577] against the bridge's ``(99, 990)``
    [common/purchMT.cbl:L1173-L1174], and note ``We-Error`` is assigned first in both,
    with 999 documented as "not used" and 990 as "unknown/unexpected".

    Args:
        file_access: The block whose status pair is written.
    """
    _status(file_access, FsReply.ERROR, WeError.NOT_USED)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit.`` [common/acas022.cbl:L579-L582].

    Args:
        file_access: The block passed to the logger.
        dal_common: Carries ``SW-Testing``; its ``88 Testing-1 value 1``
            [copybooks/Test-Data-Flags.cob:L11] gates the call.
    """
    if dal_common.sw_testing == 1:
        ca_process_logs(file_access, dal_common)


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas022.cbl:L584-L586].

    An empty label carrying only the comment "Now have processed cobol flat file, so .."
    and falling through into ``aa-Exit``.
    """
    return


def aa_exit() -> None:
    """``aa-Exit.`` [common/acas022.cbl:L588-L589]."""
    return


def ba_process_rdbms(
    system: SystemRecord,
    purch: WsPurchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas022.cbl:L591-L668].

    Args:
        system: The system record, whose ``RDBMS`` fields the credential load reads on
            the first call only.
        purch: The caller's record, handed to the bridge.
        file_access: The ``File-Access`` block.
        file_defs: The file-name block. Carried for linkage fidelity; the RDB path
            addresses a TABLE and never a file name, so nothing here reads it.
        dal_common: The logging switches.
        transport: The transport policy for the open path.
    """
    ba010_test_ws_rec_size(file_access)
    if not ba012_test_ws_rec_size_2(system, purch, file_access, dal_common):
        ba_rdbms_exit()
        return
    ba015_test_ends(
        purch, file_access, dal_common, system=system, transport=transport
    )
    ba_rdbms_exit()


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas022.cbl:L599-L605].

    ANOMALY ``N-log``. ``aa010-main`` set ``WS-Log-File-No`` to 11
    [common/acas022.cbl:L294]; this overwrites it with 21 - and it is reached ONLY on
    the RDB path, because ``aa010-main`` performs ``ba012-Test-WS-Rec-Size-2`` DIRECTLY
    when it wants the record-length guard alone [common/acas022.cbl:L324], skipping this
    paragraph.

    Args:
        file_access: The block whose ``WS-Log-File-No`` is overwritten.
    """
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    purch: WsPurchRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas022.cbl:L607-L647].

    One first-call-only block doing two unrelated jobs - the record-length guard and the
    credential load - which is exactly why ANOMALY ``A-1``, reproduced by
    :func:`~acas_posting.dal.connection.load_rdb_data_once`, makes the credentials unre-
    readable for the rest of the run.

    Args:
        system: The system record supplying the credentials on the first call.
        purch: The caller's record, one side of the length comparison.
        file_access: The block whose status pair and ``RDB-Data`` are written.
        dal_common: The logging switches.

    Returns:
        ``True`` to continue into ``ba015-Test-Ends``, ``False`` to take the ``go to ba-
            rdbms-exit`` the 901 branch takes. Always ``True`` in practice, because the
            comparison cannot fail.
    """
    global _WS_A, _WS_B
    if _WS_A != 0:
        # Second and later calls skip EVERYTHING, credential load included - anomaly A-1
        # [common/acas022.cbl:L609, :L647].
        return True
    # `move function Length (WS-Purch-Record) to A` and the same for `Purch-Record`
    # [common/acas022.cbl:L610-L615].
    _WS_A = _RECORD_DECLARED_LENGTH
    _WS_B = _RECORD_DECLARED_LENGTH
    if _WS_A < _WS_B:  # pragma: no cover - N-901-unreachable, verified dead
        _status(file_access, FsReply.ERROR, WeError.RECORD_SIZE_MISMATCH)
    if int(file_access.we_error) == int(
        WeError.RECORD_SIZE_MISMATCH
    ):  # pragma: no cover - unreachable with the frozen copybooks
        # The panel [common/acas022.cbl:L620-L635] splits THREE ways, not two:
        #   * the `display` of the assembled `PL905` diagnostic is the substance, so
        #     ONE record at ERROR - a programming error the caller must stop for.
        #   * the `display PL901` is "PL901 Note error and hit return"
        #     [common/acas022.cbl:L262] - the acknowledgement half, paired with the
        #     `accept` below it. AAP section 0.3.4 drops an acknowledgement pause
        #     ENTIRELY, and quoting its text in a log line is still emitting it, to a
        #     destination where no operator can answer it.
        #   * the `go to ba-rdbms-exit` is CONTROL, preserved as `return False`.
        _LOG.error(
            "%s %s%d < Purch-Rec = %d",
            PROG_NAME,
            _PL905,
            _WS_A,
            _WS_B,
        )
        if dal_common.sw_testing == 1:
            ca_process_logs(file_access, dal_common)
        return False
    # The six credential moves [common/acas022.cbl:L641-L646], in the frozen order.
    file_access.rdb_data = load_rdb_data_once(system)
    # The record is untouched by this paragraph; the parameter is present because the
    # COBOL reads its length.
    del purch
    return True


def ba015_test_ends(
    purch: WsPurchRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    system: SystemRecord,
    transport: TransportSecurity | None,
) -> None:
    """``ba015-Test-Ends.`` [common/acas022.cbl:L649-L665].

    ANOMALY ``N-cdftodo``. Four comment lines above the call record an unfinished design
    decision [common/acas022.cbl:L652-L657].

    Args:
        purch: The caller's record, passed straight through.
        file_access: The ``File-Access`` block, passed straight through.
        dal_common: ``ACAS-DAL-Common-data``, passed straight through.
        system: Supplies the credentials to the bridge's open path.
        transport: The transport policy for that open path.
    """
    purch_mt(
        file_access,
        dal_common,
        purch,
        system_record=system,
        transport=transport,
    )


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit.`` [common/acas022.cbl:L667-L668].

    ``exit section.`` - and note it IS ``exit section`` here, where ``ca-Exit`` two
    paragraphs later is a plain ``exit`` [common/acas022.cbl:L677]. Preserved as a
    distinction rather than normalised.
    """
    return


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` [common/acas022.cbl:L671-L675].

    which is the handler's own statement of anomaly ``N-bridge-logs-handler-does-not``
    and its handler-side half ``N-nolog-on-dal``: on the RDB path the bridge logs and
    the handler must not.

    Args:
        file_access: The block whose fields make up the record.
        dal_common: Carried for signature fidelity with the COBOL parameter list.
    """
    logging_data = file_access.logging_data
    #  THE SAME ONE ADAPTER the bridge's like-named paragraph uses, so the two
    # render identically and differ only in the program they name. `WS-File-Key` -
    # the supplier code - is withheld (CWE-532), and `Log-File-Rec-Written` is
    # advanced modulo one million rather than left alone.
    log_file_handler_record(
        _LOG,
        program=PROG_NAME,
        paragraph="Ca-Process-Logs",
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
    # Falls through into ca-Exit.


def ca_exit() -> None:
    """``ca-Exit.`` [common/acas022.cbl:L677]."""
    return


def aa_process_flat_file(
    system: SystemRecord,
    purch: WsPurchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    purchase_file: PurchaseFile | None,
    transport: TransportSecurity | None,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas022.cbl:L287].

    The handler's only section header.

    Args:
        system: The ``SYSTEM-REC`` row.
        purch: The caller's record.
        file_access: The ``File-Access`` block.
        file_defs: The file-name block.
        dal_common: The logging switches.
        purchase_file: The ISAM store, when the flat-file path is selected.
        transport: The transport policy for the RDB open path.
    """
    aa010_main(
        system,
        purch,
        file_access,
        file_defs,
        dal_common,
        purchase_file=purchase_file,
        transport=transport,
    )


def aa010_main(
    system: SystemRecord,
    purch: WsPurchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    purchase_file: PurchaseFile | None,
    transport: TransportSecurity | None,
) -> None:
    """``aa010-main.`` [common/acas022.cbl:L289-L361].

    1. The log identity [common/acas022.cbl:L293-L294] - ``WS-Log-System = 4``, the only
    handler in the folder that uses 4, and ``WS-Log-File-No = 11``. ANOMALY
    ``N-logsystem5-meaning``.

    Args:
        system: The ``SYSTEM-REC`` row; its ``File-System-Used`` field chooses the store
            and its ``RDBMS`` fields supply the credentials.
        purch: The caller's record.
        file_access: The ``File-Access`` block.
        file_defs: The file-name block, carried for linkage fidelity.
        dal_common: The logging switches.
        purchase_file: The ISAM store, required only on the flat-file path.
        transport: The transport policy for the RDB open path.

    Raises:
        PurchaseFileNotSuppliedError: If the flat-file path is selected and no store was
            supplied. Not a COBOL condition - see that class.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_system = int(WS_LOG_SYSTEM)
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_COBOL
    function = int(file_access.file_function)
    key_number = int(logging_data.file_key_no)
    # The key guard [common/acas022.cbl:L298-L312].
    if function in _KEY_GUARDED_READ_FUNCTIONS:
        if key_number != ONLY_KEY_NUMBER:
            _status(
                file_access, FsReply.ERROR, WeError.FILE_KEY_NO_OUT_OF_RANGE
            )
            aa999_main_exit(file_access, dal_common)
            return
    elif function == int(FileFunction.DELETE):
        # `when 8` [common/acas022.cbl:L306-L311], with N-guard-extra-comment and
        # N-996-comment.
        if key_number != ONLY_KEY_NUMBER:
            _status(
                file_access, FsReply.ERROR, WeError.DELETE_KEY_OUT_OF_RANGE
            )
            aa999_main_exit(file_access, dal_common)
            return
    if int(system.system_data_block.rdbms_flat_statuses.file_system_used) != 0:
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses`
        # [common/acas022.cbl:L317], commented "needed for DAL? not JC/dbpre versions" -
        # copied because the frozen source copies it, whatever the doubt.
        _copy_rdbms_flat_statuses(system, file_access)
        ba_process_rdbms(
            system,
            purch,
            file_access,
            file_defs,
            dal_common,
            transport=transport,
        )
        aa_main_exit()
        return
    # `perform ba012-Test-WS-Rec-Size-2.` [common/acas022.cbl:L324] - DIRECT, so ba010's
    # `move 21` never runs and this path keeps log file 11.
    if not ba012_test_ws_rec_size_2(system, purch, file_access, dal_common):
        # The dead 901 branch's transfer, preserved.
        return
    # [common/acas022.cbl:L334-L335] are COMMENTED OUT; the status pair is NOT zeroed
    # here. `move spaces to SQL-Err SQL-Msg.` [common/acas022.cbl:L336] - TWO fields.
    # N-sqlstate-not-cleared: SQL-State is deliberately left alone.
    logging_data.sql_err = " " * 5
    logging_data.sql_msg = " " * 512
    store = _require_purchase_file(purchase_file, "aa010-main")
    if function == int(FileFunction.OPEN):
        aa020_process_open(file_access, dal_common, store)
        return
    if function == int(FileFunction.CLOSE):
        aa030_process_close(file_access, dal_common, store)
        return
    if function in _AA_READ_NEXT_FUNCTIONS:
        # `when 3 / when 31` [common/acas022.cbl:L343-L345]. ANOMALY N-read-by-name-is-
        # read-next.
        aa040_process_read_next(file_access, purch, dal_common, store)
        return
    if function == int(FileFunction.READ_INDEXED):
        aa050_process_read_indexed(file_access, purch, dal_common, store)
        return
    if function == int(FileFunction.WRITE):
        aa070_process_write(file_access, purch, dal_common, store)
        return
    if function == int(FileFunction.RE_WRITE):
        aa090_process_rewrite(file_access, purch, dal_common, store)
        return
    if function == int(FileFunction.DELETE):
        aa080_process_delete(file_access, purch, dal_common, store)
        return
    if function == int(FileFunction.START):
        aa060_process_start(file_access, purch, dal_common, store)
        return
    aa100_bad_function(file_access)
    aa999_main_exit(file_access, dal_common)


def dispatch(
    system: SystemRecord,
    purch: WsPurchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    purchase_file: PurchaseFile | None = None,
    transport: TransportSecurity | None = None,
) -> tuple[int, int]:
    """``call "acas022" using ...`` - the file handler for the Purchase ledger.

    WHICH STORE SERVES THE REQUEST is decided by one digit of the system record, ``File-
    System-Used`` [copybooks/wssystem.cob:L112], whose condition names are ``FS-Cobol-
    Files-Used value zero`` and ``FS-MySql-Used value 1``
    [copybooks/wssystem.cob:L113-L114]. Zero takes the ISAM paragraphs, one takes the
    bridge.

    Args:
        system: ``System-Record``. Chooses the store, and supplies the RDB credentials
            on the first call of the run.
        purch: ``WS-Purch-Record``, the caller's copy of the row. Read by the write,
            rewrite, delete and start paths; written by the read paths.
        file_access: ``File-Access``. Carries the function code, the access type and the
            key number in, and the status pair plus the whole ``Logging-Data`` sub-block
            out.
        file_defs: ``File-Defs``. Carried for linkage fidelity - the ISAM path takes its
            file from ``purchase_file`` and the RDB path addresses a table, so no path
            reads it.
        dal_common: ``ACAS-DAL-Common-data``, carrying ``SW-Testing`` and ``SW-
            Testing-2``.
        purchase_file: The ISAM store.
        transport: Keyword-only transport policy handed to the bridge's open path;
            likewise not a COBOL parameter.

    Returns:
        The ``(Fs-Reply, We-Error)`` pair. ``file_access`` is authoritative and is what
            a COBOL caller inspects; the tuple is a convenience.

    Raises:
        PurchaseFileNotSuppliedError: Only when the flat-file path is selected and no
            store was supplied.
    """
    aa_process_flat_file(
        system,
        purch,
        file_access,
        file_defs,
        dal_common,
        purchase_file=purchase_file,
        transport=transport,
    )
    aa_exit()
    return int(file_access.fs_reply), int(file_access.we_error)
