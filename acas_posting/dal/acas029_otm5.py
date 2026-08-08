"""`acas029` and its bridge `otm5MT` - the `PUITM5-REC` purchase open-item table.

The data-access module for the OTM5 entity: the purchase ledger's unpaid-item
register, written and applied by `pl060` and cleared by `pl100`.

The date and batch columns are binary integers, so their values arrive as `int`
and truncate as integer arithmetic does, which is what makes `pl100`'s
payment-days figures reproducible
[purchase/pl100.cbl:L498], [purchase/pl100.cbl:L502].

A verb that arrives with a key number this table does not declare is refused
rather than guessed at, because guessing would silently read a different index
than the frozen program read.
"""

from __future__ import annotations

import decimal
import logging
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Final

from acas_posting.dal.connection import (
    MySQLConnectionAbstract,
    TransportSecurity,
    acquire_cursor,
    execute_statement,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    EXTRA_READ_ORDERS,
    CursorSlot,
    CursorStateTable,
    DatabaseCursor,
    KeyOfReference,
    OrderQuoting,
    key_of_reference,
    read_indexed as _cursor_read_indexed,
    read_next as _cursor_read_next,
    start as _cursor_start,
)
from acas_posting.dal.status import (
    AccessType,
    AcasFileHandlerError,
    FileFunction,
    FsReply,
    LogSystem,
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    WeError,
    db_error_log_category,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
    redact_for_log,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefsA
from acas_posting.records.otm5 import (
    Filler1,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OiSupplier,
    descriptors_of,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# Every value below is READ from the generated data dictionary rather than typed,
# because Agent Action Plan section 0.8.1 makes "data dictionary first" a directive and
# rule R-5 requires each field to cite its entry.
_TABLE_ENTRY: Final = loader.table_for("PUITM5-REC")

TABLE: Final[str] = _TABLE_ENTRY.name

BRIDGE: Final[str] = _TABLE_ENTRY.bridge

HANDLER: Final[str] = _TABLE_ENTRY.handler

#: The facade name the entity is published under [copybooks/Proc-ACAS-FH-Calls.cob].
#: ``dal/facade.py`` owns the vocabulary.
ENTITY_FACADE: Final[str] = _TABLE_ENTRY.entity_facade

PRIMARY_KEY: Final[str] = _TABLE_ENTRY.primary_key

RECORD_COPYBOOKS: Final[tuple[str, ...]] = _TABLE_ENTRY.copybooks

RECORD_LENGTH: Final[int] = 113

# ``'00010015'`` - offset 1, length 15 [common/otm5MT.cbl:L252].
_KEY: Final[KeyOfReference] = key_of_reference(TABLE, 1)

KEY_OFFSET: Final[int] = _KEY.kor_offset

KEY_LENGTH: Final[int] = _KEY.kor_length

KEY_COUNT: Final[int] = 1

KEY_TYPE: Final[str] = _KEY.kor_type

#: ``move 4 to WS-Log-System`` [common/acas029.cbl:L234] - the Purchase subsystem.
WS_LOG_SYSTEM: Final[int] = int(LogSystem.PL)

WS_LOG_FILE_NO_FLAT: Final[int] = 15

#: ``move 25 to WS-Log-File-no`` [common/acas029.cbl:L551] - the RDB value. The bump
#: from 15 to 25 happens inside ``ba010-Test-WS-Rec-Size``, which is never
#: ``perform``ed.
WS_LOG_FILE_NO_RDB: Final[int] = 25

_ENTRIES: Final[tuple[Any, ...]] = tuple(
    sorted(
        loader.entries_for_table(TABLE),
        key=lambda entry: loader.column_for(entry.key).ordinal,
    )
)

COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name for entry in _ENTRIES
)

#: Dictionary key per column, e.g. ``OI5-NET`` -> ``PUITM5-REC.OI5-NET``.
DICTIONARY_KEYS: Final[Mapping[str, str]] = {
    loader.column_for(entry.key).name: entry.key for entry in _ENTRIES
}

# ANOMALY A1 - the headline defect, derived rather than asserted.
WRITE_ONLY_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if not loader.host_variable_for(entry.key).unloaded_to_record
)

#: The 27 columns ``bb100-UnloadHVs`` does move back [common/otm5MT.cbl:L1394-L1422], in
#: COLUMN order. Its length is the arithmetic statement of anomaly A1: 29 loaded, 27
#: unloaded.
UNLOADED_COLUMNS: Final[tuple[str, ...]] = tuple(
    name for name in COLUMNS if name not in WRITE_ONLY_COLUMNS
)

# ANOMALY A4 - four fields signed in the copybook, unsigned at the host variable and
# unsigned in the column, so the sign is lost AT THE BRIDGE, before any SQL executes.
SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.drift_for(entry.key).signedness
)

CHARACTER_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "CHAR"
)

#: ``decimal`` columns - eleven: nine ``decimal(9,2)`` money fields plus the two
#: ``decimal(5,2)`` deduction fields. All eleven are :class:`decimal.Decimal` end to end
#: (rule R-2).
DECIMAL_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "DECIMAL"
)

#: ``int`` and ``tinyint`` columns - six of them.
INTEGER_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value in ("INT", "TINYINT")
)

#: Declared scale per ``decimal`` column, from the frozen DDL. Two everywhere here, but
#: read rather than assumed.
DECIMAL_SCALES: Final[Mapping[str, int]] = {
    name: int(loader.column_for(DICTIONARY_KEYS[name]).scale or 0)
    for name in DECIMAL_COLUMNS
}

CHARACTER_WIDTHS: Final[Mapping[str, int]] = {
    name: int(loader.column_for(DICTIONARY_KEYS[name]).display_width or 0)
    for name in CHARACTER_COLUMNS
}

#: True where the column is declared ``unsigned``. Consulted only for the record, never
#: as a validation.
COLUMN_IS_UNSIGNED: Final[Mapping[str, bool]] = {
    loader.column_for(entry.key).name: bool(loader.column_for(entry.key).unsigned)
    for entry in _ENTRIES
}


# ``WS-No-Paragraph`` is the field the logger reports the failing paragraph through
# [copybooks/wsfnctn.cob:L48].

#: ``acas029``'s 201..208 mapping, one per verb, each cited at its own line.
HANDLER_TRACE_NUMBERS: Final[Mapping[FileFunction, int]] = {
    FileFunction.OPEN: 201,
    FileFunction.CLOSE: 202,
    FileFunction.READ_NEXT: 203,
    FileFunction.READ_INDEXED: 204,
    FileFunction.START: 205,
    FileFunction.WRITE: 206,
    FileFunction.DELETE: 207,
    FileFunction.RE_WRITE: 208,
}

#: ``otm5MT``'s own small numbers, which the RDB path actually reports because the
#: bridge overwrites the handler's value.
BRIDGE_TRACE_NUMBERS: Final[Mapping[str, tuple[int, ...]]] = {
    "ba020-Process-Open": (1,),
    "ba030-Process-Close": (2,),
    "ba040-Process-Read-Next": (3, 4),
    "ba050-Process-Read-Indexed": (5, 6),
    "ba060-Process-Start": (8,),
    "ba070-Process-Write": (10,),
    "ba080-Process-Delete": (13,),
    "ba090-Process-Rewrite": (17,),
    "ba140-Process-Read-Next": (21, 22),
    "ba150-Process-Read-Next": (21, 22),
    "ba998-Free": (20,),
}


# ANOMALY A13 - ``move 35 to fs-Reply`` [common/acas029.cbl:L307] is a status value
# OUTSIDE the set ``dal/status.py`` declares from the frozen documentation, ``{0, 10,
# 21, 22, 23, 99}``.
FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35

# ANOMALY A12 - the handler and the bridge DISAGREE on the bad-function code.
# ``aa100-Bad-Function`` sets ``999`` [common/acas029.cbl:L522] while ``ba100-Bad-
# Function`` sets ``990`` [common/otm5MT.cbl:L1308].
HANDLER_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.NOT_USED)

BRIDGE_BAD_FUNCTION_WE_ERROR: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

# ANOMALY A18 - the key-number guard splits 996 from 998 under the SAME copy-pasted
# comment text, "file seeks key type out of range".
KEY_GUARD_WE_ERROR_READ_START: Final[int] = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)

KEY_GUARD_WE_ERROR_DELETE: Final[int] = int(WeError.DELETE_KEY_OUT_OF_RANGE)

# ANOMALY A19 - ``fn-read-next`` is NOT key-guarded, even though a read-next after a
# ``START`` uses the key.
KEY_GUARDED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.READ_INDEXED,
    FileFunction.START,
    FileFunction.DELETE,
)

# ANOMALY A14 - ``fn-extend`` has its ``open extend`` COMMENTED OUT, annotated "Must not
# be used for ISAM files" [common/acas029.cbl:L325], and returns ``997``/``99`` instead
# [common/acas029.cbl:L326-L327].
OPEN_EXTEND_WE_ERROR: Final[int] = int(WeError.ACCESS_TYPE_WRONG)

# ANOMALY A33 - the record-size FATAL. ``if A < B`` sets ``901``/``99`` and aborts the
# bridge call outright [common/acas029.cbl:L562-L564, L580]. WE-Error for the record-
# size mismatch [common/acas029.cbl:L563].
RECORD_SIZE_WE_ERROR: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)


#: ``05 WS-File-Key pic x(64) value spaces.`` [copybooks/wsfnctn.cob:L52].
WS_FILE_KEY_WIDTH: Final[int] = 64

WS_LOG_WHERE_WIDTH: Final[int] = 231

DELETE_ROWCOUNT_WE_ERROR: Final[int] = int(WeError.DELETE_SQLSTATE_NOT_00000)

REWRITE_ROWCOUNT_WE_ERROR: Final[int] = int(WeError.REWRITE_SQLSTATE_NOT_00000)

READ_INDEXED_DRIVER_WE_ERROR: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

READ_INDEXED_EMPTY_WE_ERROR: Final[int] = int(WeError.READ_INDEXED_UNEXPECTED)

READ_INDEXED_MISS_FS_REPLY: Final[FsReply] = FsReply.KEY_NOT_FOUND

# ANOMALY A11 - three distinct end-of-file markers written into the logging key field,
# all returning ``(10, 10)``.
EOF_FILE_KEYS: Final[tuple[str, str, str]] = ("EOF", "EOF2", "EOF3")

#: ``move "No Data" to WS-File-Key`` when the read-next SELECT itself returns nothing
#: [common/otm5MT.cbl:L553] - distinct from ``"EOF"``, which means the walk ran out.
NO_DATA_FILE_KEY: Final[str] = "No Data"

SEQUENTIAL_LOW_KEY: Final[str] = "0" * KEY_LENGTH

# ANOMALY A22 / A23 - the sales-terminology leaks.
OPEN_FILE_KEY: Final[str] = "OPEN PL OTM5"

CLOSE_FILE_KEY: Final[str] = "CLOSE PL OTM5"

#: The handler's own, misspelled, flat-file equivalents [common/acas029.cbl:L335, L346].
#: Recorded, never written.
HANDLER_OPEN_FILE_KEY: Final[str] = "OPEN SL OTM5 File"
HANDLER_CLOSE_FILE_KEY: Final[str] = "CLOSE SL OTM5 File"

# ANOMALY A9 - THREE cursors are declared for a single-key table with no repeating
# group.
CURSOR_SLOT: Final[CursorSlot] = CursorSlot.PRIMARY

SORTED_CURSOR_SLOTS: Final[Mapping[FileFunction, CursorSlot]] = {
    FileFunction.READ_BY_BATCH: CursorSlot.SECONDARY,
    FileFunction.READ_BY_CUST: CursorSlot.TERTIARY,
}

#: Nothing. Every slot the frozen bridge declares is now driven by the verb that
#: declares it, which is what correction C3 changed.
UNREACHED_CURSOR_SLOTS: Final[tuple[CursorSlot, ...]] = ()

# ``copybooks/wsfnctn.cob`` declares two extended function codes for this entity
# [copybooks/wsfnctn.cob:L103-L104]: 88 fn-Read-By-Batch value 32. *> 08/02/17 for
# OTM3/5 (sl095/pl095) 88 fn-Read-By-Cust value 33.
_EXTRA_READS: Final = EXTRA_READ_ORDERS[TABLE]

#: How the frozen bridge quotes its ordering terms, recorded against the shared
#: vocabulary so the intent is unambiguous rather than implied by the text below.
_SORTED_ORDER_BY_QUOTING: Final[OrderQuoting] = OrderQuoting.STRING_CONSTANT

#: The two ``ORDER BY`` clauses, transcribed CHARACTER FOR CHARACTER from the frozen
#: ``STRING`` literals rather than rebuilt from :data:`_EXTRA_READS`. Two reasons, both
#: fidelity.
_SORTED_ORDER_BY_TEXT: Final[Mapping[FileFunction, str]] = {
    # [common/otm5MT.cbl:L1009-L1013].
    FileFunction.READ_BY_BATCH: (
        " ORDER BY "
        "'OI5-INVOICE', 'OI5-DAT' ASC, "
        "'OI5-TYPE' DESC, "
        "'OI5-BATCH-ITEM', 'OI5-BATCH-NOS' ASC "
    ),
    FileFunction.READ_BY_CUST: (
        " ORDER BY "
        "'OI5-SUPPLIER', 'OI5-DAT', "
        "'OI5-INVOICE', 'OI5-TYPE' ASC "
    ),
}

#: ``move "Sorted" to WS-File-Key`` - written by BOTH sorted reads while their SELECT is
#: in flight [common/otm5MT.cbl:L1036, L1191], so the log tag cannot tell the by-batch
#: read from the by-customer one.
SORTED_FILE_KEY: Final[str] = "Sorted"

#: The tail of the success message both sorted reads compose, ``string "> 0 got cnt="
#: WS-Temp-ED-Row " recs in sorted order"`` [common/otm5MT.cbl:L1061, L1216].
SORTED_FILE_KEY_SUFFIX: Final[str] = " recs in sorted order"

_TEMP_ED_ROW_DIGITS: Final[int] = 7

# The shared positioning table and this module must agree on which slot each sorted read
# drives, because the table's ``owning_handlers`` names this handler and a silent
# disagreement would leave one of the two walks writing into the other's cursor.
for _sorted_function, _sorted_slot in SORTED_CURSOR_SLOTS.items():
    if _EXTRA_READS[_sorted_function].cursor_slot is not _sorted_slot:
        raise ValueError(
            f"{BRIDGE} {_sorted_function.name} drives "
            f"{_EXTRA_READS[_sorted_function].cursor_slot} in cursor_state but "
            f"{_sorted_slot} here "
            f"{_EXTRA_READS[_sorted_function].source_locator}"
        )
    if HANDLER not in _EXTRA_READS[_sorted_function].owning_handlers:
        raise ValueError(
            f"{HANDLER} is not recorded as an owner of "
            f"{_sorted_function.name} "
            f"{_EXTRA_READS[_sorted_function].source_locator}"
        )
del _sorted_function, _sorted_slot

StatusPair = tuple[FsReply, int]

_SUCCESS: Final[StatusPair] = (FsReply.SUCCESS, int(WeError.SUCCESS))


# Agent Action Plan section 0.3.3 has the arithmetic and MOVE layers take "a descriptor
# and a value", so storage semantics are data-driven.
_HEADER_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiHeader)
_KEY_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiKey)
_BATCH_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiBatch)
_SUPPLIER_FIELDS: Final[Mapping[str, Any]] = descriptors_of(OiSupplier)
_MONEY_FIELDS: Final[Mapping[str, Any]] = descriptors_of(Filler1)

# The frozen bridge holds its MySQL connection in the C interface's process state.
_CONNECTION: MySQLConnectionAbstract | None = None

# One cursor-state table, holding the single slot this handler's path uses - see
# anomalies A9 and A10 above.
_STATES: Final[CursorStateTable] = CursorStateTable()

# ``77 A pic 9(4) value zero`` / ``77 B pic 9(4) value zero``
# [common/acas029.cbl:L188-L189], annotated "A & B used in 1st test ONLY / in ba-
# Process-RDBMS".
_A: int = 0
_B: int = 0

# ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9).`` [common/otm5MT.cbl:L227]. Thirty characters,
# laid out as.
_EDIT_WIDTH: Final[int] = 30
_EDIT_INTEGER_DIGITS: Final[int] = 19
_EDIT_FRACTION_DIGITS: Final[int] = 9

_EDIT_CONTEXT: Final[decimal.Context] = decimal.Context(
    prec=_EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS + 2,
    rounding=decimal.ROUND_DOWN,
)
"""An exact-decimal context wide enough for the whole edit field.

Precision covers every digit position the field can hold, so no rendering can lose a
digit to the context.

Every ``decimal`` operation in this rendering path runs inside a copy of this context -
the two derived constants immediately below, and the whole body of :func:`mysql_edit` -
rather than in whatever context the importing application happens to be carrying.
``quantize``, ``scaleb``, ``**``, ``*`` and unary minus are all CONTEXT operations, so
without this the thirty-character image would be a property of the caller's ambient
precision instead of the picture at [common/otm5MT.cbl:L227], and two processes would
not agree on it (rule R-2). The sibling handler states the identical policy at
``acas_posting/dal/acasirsub4_irs_posting.py _EDIT_FRACTION_DIGITS``.
"""

with decimal.localcontext(_EDIT_CONTEXT):
    _EDIT_FRACTION_QUANTUM: Final[decimal.Decimal] = decimal.Decimal(1).scaleb(
        -_EDIT_FRACTION_DIGITS
    )
    _EDIT_TEN_POWER_FRACTION: Final[decimal.Decimal] = decimal.Decimal(10) ** (
        _EDIT_FRACTION_DIGITS
    )

_WINDOW_INTEGER_10: Final[slice] = slice(10, 20)
_WINDOW_INTEGER_07: Final[slice] = slice(13, 20)
_WINDOW_INTEGER_03: Final[slice] = slice(17, 20)
_WINDOW_FRACTION_02: Final[slice] = slice(21, 23)


def mysql_edit(value: decimal.Decimal | int) -> str:
    """Render one numeric host variable through ``WS-MYSQL-EDIT``.

    Reproduces ``MOVE HV-... TO WS-MYSQL-EDIT`` against the edited picture at
    [common/otm5MT.cbl:L227]. The result is always thirty characters, so the four
    reference-modification windows the statement builders slice out land on exactly the
    positions the frozen source intends.

    Args:
        value: the host variable's value. An ``int`` for the six integer columns, a
            ``Decimal`` for the eleven decimal columns.

    Returns:
        The thirty-character edited image, sign in position one.
    """
    # `_EDIT_CONTEXT`, not the ambient context. `quantize` in particular does not merely
    # round under a narrowed precision - it REFUSES, raising `InvalidOperation`, when the
    # result would need more digits than `prec` allows. Measured: with the ambient
    # precision at nine digits this function raised rather than rendering
    # `decimal(9,2)`. The sibling handler wraps its own renderer the same way at
    # `acas_posting/dal/acasirsub4_irs_posting.py _EDIT_CONTEXT`.
    with decimal.localcontext(_EDIT_CONTEXT):
        quantised = decimal.Decimal(value).quantize(
            _EDIT_FRACTION_QUANTUM, rounding=decimal.ROUND_DOWN
        )
        negative = quantised < 0
        # Unary minus rather than the absolute-value builtin: rule R-2 bars that builtin
        # on a monetary value, and unary minus on a ``Decimal`` is exact inside a context
        # wide enough to hold the operand, which `_EDIT_CONTEXT` is by construction.
        magnitude = -quantised if negative else quantised
        scaled = int(
            (magnitude * _EDIT_TEN_POWER_FRACTION).to_integral_value(
                rounding=decimal.ROUND_DOWN
            )
        )
    digits = str(scaled).rjust(_EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS, "0")
    # A value wider than the picture loses its high-order digits, which is what a COBOL
    # store does and what rule R-3 requires be preserved.
    digits = digits[-(_EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS) :]
    integer_digits = digits[:_EDIT_INTEGER_DIGITS]
    fraction_digits = digits[_EDIT_INTEGER_DIGITS :]
    suppressed = integer_digits[:-1].lstrip("0").rjust(_EDIT_INTEGER_DIGITS - 1)
    edited = (
        ("-" if negative else " ")
        + suppressed
        + integer_digits[-1]
        + "."
        + fraction_digits
    )
    if len(edited) != _EDIT_WIDTH:  # pragma: no cover - arithmetic invariant
        raise AssertionError(
            f"WS-MYSQL-EDIT must render {_EDIT_WIDTH} characters, got "
            f"{len(edited)}; see [common/otm5MT.cbl:L227]"
        )
    return edited


def render_integer_column(value: int) -> str:
    """Render an ``int`` column exactly as the statement builders do.

    ANOMALY A35 - THE SIGN IS DROPPED. The window starts at position 11 and the sign
    lives at position 1, so a negative ``OI5-CR`` renders as its MAGNITUDE and MySQL
    stores a positive value into a signed ``int(8)`` column.
    """
    return mysql_edit(value)[_WINDOW_INTEGER_10].strip()


def render_tinyint_column(value: int) -> str:
    """Render a ``tinyint`` column: ``FUNCTION TRIM (WS-MYSQL-EDIT(18:03))``.

    Used for ``OI5-DEDUCT-DAYS`` [common/otm5MT.cbl:L1723] and ``OI5-DAYS``, which carry
    no fraction. Anomaly A35 applies here too, though anomaly A4 has already reduced
    both to a magnitude at the host variable.
    """
    return mysql_edit(value)[_WINDOW_INTEGER_03].strip()


def render_money_column(value: decimal.Decimal) -> str:
    """Render a ``decimal(9,2)`` column, the nine money fields.

    ``FUNCTION TRIM (WS-MYSQL-EDIT(14:07))`` then a literal ``"."`` then ``WS-MYSQL-
    EDIT(22:02)`` - untrimmed, because it is exactly two digits
    [common/otm5MT.cbl:L1558-L1567]. Anomaly A35: the sign is dropped, so ``-123.45``
    renders ``123.45``. Measured on GnuCOBOL 3.2.0.
    """
    edited = mysql_edit(value)
    return (
        edited[_WINDOW_INTEGER_07].strip() + "." + edited[_WINDOW_FRACTION_02]
    )


def render_deduction_column(value: decimal.Decimal) -> str:
    """Render a ``decimal(5,2)`` column, the two deduction fields.

    ``FUNCTION TRIM (WS-MYSQL-EDIT(18:03))`` then ``"."`` then ``WS-MYSQL-EDIT(22:02)``
    [common/otm5MT.cbl:L1730-L1741]. The integer window is three characters wide rather
    than seven, matching ``s999v99`` [copybooks/plwsoi.cob:L57-L58]. Anomaly A35.
    """
    edited = mysql_edit(value)
    return (
        edited[_WINDOW_INTEGER_03].strip() + "." + edited[_WINDOW_FRACTION_02]
    )


def render_character_column(value: str) -> str:
    """Render a ``char`` column: ``FUNCTION TRIM (HV-..., TRAILING)``.

    For example [common/otm5MT.cbl:L1443] for ``OI5-KEY``, and identically for all
    twelve character columns.
    """
    return value.rstrip(" ")


# ``01 WS-TEMP-ED-Key.`` / ``03 WS-Temp-Ed-Customer.`` / ``05 WS-Temp-Ed-Supplier pic
# x(7).`` / ``03 WS-Temp-Ed-Invoice pic 9(8).`` [common/otm5MT.cbl:L233-L236], and ``01
# WS-Temp-ED-Batch.`` / ``03 WS-Temp-ED-Batch-Nos pic 9(5).`` / ``03 WS-Temp-ED-Batch-
# Item pic 999.`` / ``01 WS-Temp-ED-Batch9 redefines WS-Temp-ED-Batch pic 9(8).``
# [common/otm5MT.cbl:L238-L242].

# Widths taken from the descriptors rather than typed, so the composition cannot drift
# from the record layout.
_SUPPLIER_WIDTH: Final[int] = (
    int(_SUPPLIER_FIELDS["oi_nos"].character_length)
    + int(_SUPPLIER_FIELDS["oi_check"].digits)
)
_INVOICE_DIGITS: Final[int] = int(_KEY_FIELDS["oi_invoice"].digits)
_INVOICE_MODULUS: Final[int] = 10 ** _INVOICE_DIGITS
_BATCH_NOS_DIGITS: Final[int] = int(_BATCH_FIELDS["oi_b_nos"].digits)
_BATCH_NOS_MODULUS: Final[int] = 10 ** _BATCH_NOS_DIGITS
_BATCH_ITEM_DIGITS: Final[int] = int(_BATCH_FIELDS["oi_b_item"].digits)
_BATCH_ITEM_MODULUS: Final[int] = 10 ** _BATCH_ITEM_DIGITS


def supplier_characters(supplier: OiSupplier) -> str:
    """Render ``OI-Supplier`` as the seven characters the bridge copies.

    Args:
        supplier: the record's ``OI-Supplier`` group.

    Returns:
        Exactly seven characters, each child stored through its own descriptor so the
            widths are the frozen ones rather than assumed.
    """
    nos = str(_SUPPLIER_FIELDS["oi_nos"].store(supplier.oi_nos))
    check = int(_SUPPLIER_FIELDS["oi_check"].store(supplier.oi_check))
    # ``OI-Check`` is ``Pic 9`` - a single zoned digit - so the modulus is the field's
    # own width rather than a bound this module invents.
    return f"{nos}{check % 10:01d}"


def compose_key(supplier: str, invoice: int) -> str:
    """Compose ``HV-OI5-KEY`` - ANOMALY A3, the key built by concatenation.

    ANOMALY A25 - that last statement has NO TERMINATING PERIOD, so it runs on into the
    following moves as a single sentence. Harmless in GnuCOBOL, and the same punctuation
    defect class as [common/glpostingMT.cbl:L1059]. Not corrected.

    Args:
        supplier: the seven characters of ``OI-Supplier``.
        invoice: ``OI-Invoice``, a ``Pic 9(8)`` unsigned integer.

    Returns:
        Fifteen characters: seven of supplier followed by eight zero-padded invoice
            digits.
    """
    staged_supplier = f"{supplier:<{_SUPPLIER_WIDTH}.{_SUPPLIER_WIDTH}}"
    staged_invoice = int(_KEY_FIELDS["oi_invoice"].store(invoice))
    return f"{staged_supplier}{staged_invoice % _INVOICE_MODULUS:0{_INVOICE_DIGITS}d}"


def compose_batch(b_nos: int, b_item: int) -> str:
    """Compose ``HV-OI5-BATCH`` - ANOMALY A2, binary in, DIGITS out.

    ``WS-Temp-ED-Batch-Nos`` is ``pic 9(5)`` and ``WS-Temp-ED-Batch-Item`` is ``pic
    999`` [common/otm5MT.cbl:L239-L240], both DISPLAY, so the two moves perform a
    numeric conversion to zoned decimal.

    Args:
        b_nos: ``OI-B-Nos``, ``Pic 9(5) Comp``.
        b_item: ``OI-B-Item``, ``Pic 999 Comp``.

    Returns:
        Eight characters: five zero-padded batch-number digits followed by three zero-
            padded item digits.
    """
    nos = int(_BATCH_FIELDS["oi_b_nos"].store(b_nos))
    item = int(_BATCH_FIELDS["oi_b_item"].store(b_item))
    return (
        f"{nos % _BATCH_NOS_MODULUS:0{_BATCH_NOS_DIGITS}d}"
        f"{item % _BATCH_ITEM_MODULUS:0{_BATCH_ITEM_DIGITS}d}"
    )


def _zoned_integer(text: str, *, column: str) -> int:
    """Read a ``char`` column back into a numeric field.

    Reproduces the alphanumeric-to-numeric ``MOVE`` the unload paragraph performs four
    times - ``move HV-OI5-BATCH-NOS to OI-B-Nos`` [common/otm5MT.cbl:L1398], ``HV-
    OI5-BATCH-ITEM to OI-B-Item`` [common/otm5MT.cbl:L1399], ``HV-OI5-TYPE to OI-Type``
    [common/otm5MT.cbl:L1401] and ``HV-OI5-STATUS to OI-Status``
    [common/otm5MT.cbl:L1415]. Anomalies A5 and A6.

    Args:
        text: the column value as retrieved.
        column: the column name, for the diagnostic only.

    Returns:
        The unsigned integer the sending characters denote, before the receiving field's
            own truncation is applied by the caller.
    """
    body = text.lstrip()
    # Rule 2 - one leading sign only; the receivers are all unsigned, so the sign is
    # consumed and discarded [copybooks/plwsoi.cob:L21-L23, L53].
    if body[:1] in {"+", "-"}:
        body = body[1:]
    integer_digits: list[str] = []
    seen_decimal_point = False
    for character in body:
        if character.isdigit():
            if not seen_decimal_point:
                integer_digits.append(character)
        elif character in {" ", ","}:
            continue
        elif character == "." and not seen_decimal_point:
            seen_decimal_point = True
        else:
            _LOG.debug(
                "%s.%s carried a byte the alphanumeric-to-numeric MOVE "
                "rejects; the whole conversion yields zero, as measured on "
                "GnuCOBOL 3.2.0",
                TABLE,
                column,
            )
            return 0
    return int("".join(integer_digits)) if integer_digits else 0


# INITIALIZE - the NOT NULL invariant Every bridge load paragraph INITIALIZEs its host-
# variable group BEFORE loading, and this one is no exception: ``initialize TD-
# PUITM5-REC.`` [common/otm5MT.cbl:L1346].


def blank_host_variables() -> dict[str, str | int | decimal.Decimal]:
    """Reproduce ``initialize TD-PUITM5-REC`` [common/otm5MT.cbl:L1346].

    COBOL's ``INITIALIZE`` sets numeric fields to zero and alphanumeric fields to
    spaces.

    Returns:
        A fresh mutable mapping keyed by column name, one entry per column of
            :data:`COLUMNS`, with a zero or space-filled value of the right Python
            storage class.
    """
    host_variables: dict[str, str | int | decimal.Decimal] = {}
    for column in COLUMNS:
        if column in CHARACTER_WIDTHS:
            host_variables[column] = " " * CHARACTER_WIDTHS[column]
        elif column in DECIMAL_SCALES:
            # Numeric host variable with a scale -> zero at that scale, so the value
            # renders as "0.00" rather than "0" [common/otm5MT.cbl:L1556].
            host_variables[column] = decimal.Decimal(0).scaleb(0).quantize(
                decimal.Decimal(1).scaleb(-DECIMAL_SCALES[column]),
                rounding=decimal.ROUND_DOWN,
            )
        else:
            host_variables[column] = 0
    return host_variables


def blank_record() -> OiHeader:
    """Reproduce ``initialize WS-OTM5-Record`` [common/otm5MT.cbl:L1392].

    ANOMALY A29 - the unload paragraph's ``INITIALIZE`` is PLAIN, while three other
    sites in the same bridge write ``initialize WS-OTM5-Record with filler``
    [common/otm5MT.cbl:L630, L1129, L1284]. One field, two initialisation semantics, in
    one file.

    Returns:
        A fully populated :class:`OiHeader`; the dataclass declares no defaults, so
            every one of its 17 members is supplied explicitly.
    """
    supplier = OiSupplier(
        oi_nos=_SUPPLIER_FIELDS["oi_nos"].store(""),
        oi_check=_SUPPLIER_FIELDS["oi_check"].store(0),
    )
    return OiHeader(
        # OI-Key is a group; OI-Customer wraps OI-Supplier and is itself a group of
        # exactly one child - ANOMALY A7 [copybooks/plwsoi.cob:L14-L15].
        oi_key=OiKey(
            oi_customer=OiCustomer(oi_supplier=supplier),
            oi_invoice=_KEY_FIELDS["oi_invoice"].store(0),
        ),
        oi_date=_HEADER_FIELDS["oi_date"].store(0),
        oi_batch=OiBatch(
            oi_b_nos=_BATCH_FIELDS["oi_b_nos"].store(0),
            oi_b_item=_BATCH_FIELDS["oi_b_item"].store(0),
        ),
        oi_type=_HEADER_FIELDS["oi_type"].store(0),
        oi_ref=_HEADER_FIELDS["oi_ref"].store(""),
        oi_order=_HEADER_FIELDS["oi_order"].store(""),
        oi_hold_flag=_HEADER_FIELDS["oi_hold_flag"].store(""),
        oi_unapl=_HEADER_FIELDS["oi_unapl"].store(""),
        # The unnamed COMP-3 group [copybooks/plwsoi.cob:L41] holding the nine money
        # fields. OI-Approp REDEFINES OI-Net - ANOMALY A8 - and has no host variable and
        # no column [copybooks/plwsoi.cob:L44-L45].
        filler_1=Filler1(
            oi_p_c=_MONEY_FIELDS["oi_p_c"].store(0),
            oi_net=_MONEY_FIELDS["oi_net"].store(0),
            oi_approp=_MONEY_FIELDS["oi_approp"].store(0),
            oi_extra=_MONEY_FIELDS["oi_extra"].store(0),
            oi_carriage=_MONEY_FIELDS["oi_carriage"].store(0),
            oi_vat=_MONEY_FIELDS["oi_vat"].store(0),
            oi_discount=_MONEY_FIELDS["oi_discount"].store(0),
            oi_e_vat=_MONEY_FIELDS["oi_e_vat"].store(0),
            oi_c_vat=_MONEY_FIELDS["oi_c_vat"].store(0),
            oi_paid=_MONEY_FIELDS["oi_paid"].store(0),
        ),
        oi_status=_HEADER_FIELDS["oi_status"].store(0),
        oi_deduct_days=_HEADER_FIELDS["oi_deduct_days"].store(0),
        oi_deduct_amt=_HEADER_FIELDS["oi_deduct_amt"].store(0),
        oi_deduct_vat=_HEADER_FIELDS["oi_deduct_vat"].store(0),
        oi_days=_HEADER_FIELDS["oi_days"].store(0),
        oi_cr=_HEADER_FIELDS["oi_cr"].store(0),
        oi_applied=_HEADER_FIELDS["oi_applied"].store(""),
        oi_date_cleared=_HEADER_FIELDS["oi_date_cleared"].store(0),
    )


def _drop_sign(value: int, *, column: str) -> int:
    """Narrow a signed COBOL value into an unsigned host variable.

    ANOMALY A4 - FOUR of this table's columns are signed in the copybook,
    unsigned at the host variable and unsigned in the column, so the sign is
    lost AT THE BRIDGE, before any SQL executes:

    =================  ==========================  ==========================
    Column             Copybook                    Host variable
    =================  ==========================  ==========================
    ``OI5-DAT``        ``OI-Date BINARY-LONG``     ``PIC 9(10) COMP``
                       [copybooks/plwsoi.cob:L19]  [common/otm5MT.cbl:L307]
    ``OI5-DEDUCT-      ``OI-Deduct-Days            ``PIC 9(03) COMP``
    DAYS``             BINARY-CHAR``               [common/otm5MT.cbl:L326]
                       [copybooks/plwsoi.cob:L56]
    ``OI5-DAYS``       ``OI-Days BINARY-CHAR``     ``PIC 9(03) COMP``
                       [copybooks/plwsoi.cob:L59]  [common/otm5MT.cbl:L329]
    ``OI5-DATE-        ``OI-Date-Cleared           ``PIC 9(10) COMP``
    CLEARED``          BINARY-LONG``               [common/otm5MT.cbl:L332]
                       [copybooks/plwsoi.cob:L62]
    =================  ==========================  ==========================

    Agent Action Plan section 0.6.2 requires the bridge's conversion be
    reproduced rather than the computed value written and MySQL left to
    complain, and section 0.6.8 lists the resulting stored value as an
    AMBIGUITY that "must be measured rather than assumed".

    AMBIGUITY Q-OTM5-NARROW - RESOLVED BY MEASUREMENT, retained as the section
    0.6.8 audit trail. Measured on GnuCOBOL 3.2.0 [common/comp-common.sh:L9] - and
    RE-MEASURED independently since, on the same compiler version, with identical
    results - the signed-to-unsigned ``MOVE`` stores the MAGNITUDE, not a
    two's-complement reinterpretation::

        BINARY-LONG -5 -> PIC 9(10) COMP  = 0000000005   (not 4294967291)
        BINARY-CHAR -3 -> PIC  9(03) COMP = 003          (not 253)

    So the sign is discarded and the absolute value survives. This resolution
    belongs in ``docs/migration/ambiguity-resolutions.md``, which is another
    agent's file; it is recorded here so the measurement is not lost.

    Rule R-3 forbids making this a validation: a negative input is silently
    narrowed exactly as the bridge narrows it, never rejected.

    Args:
        value: the signed value held by the record field.
        column: the column name, for the diagnostic only.

    Returns:
        The magnitude of ``value``.
    """
    if value < 0:
        #  NO RECORD HERE. The frozen `move` into an unsigned host variable
        #  narrows in silence - it writes no status, sets no flag and displays
        #  nothing - so a record was invented (R-4), and the silence IS anomaly A4
        #  as the register describes it. It is documented in `ANOMALIES` and in
        #  `docs/migration/anomaly-log.md`, where a reader finds it without an
        #  operator seeing it once per column per row.
        del column
        # Magnitude by unary minus; the absolute-value builtin is avoided so
        # that rule R-2's compliance scan stays literally clean.
        return -value
    return value


def load_host_variables(otm5: OiHeader) -> dict[str, str | int | decimal.Decimal]:
    """Reproduce ``bb000-HV-Load`` [common/otm5MT.cbl:L1338-L1382].

    Loads all 29 host variables from the linkage record, applying every representation
    conversion the bridge applies. The mapping starts from :func:`blank_host_variables`,
    reproducing ``initialize TD-PUITM5-REC`` [common/otm5MT.cbl:L1346], so no column can
    be missing and none can be ``None``.

    Args:
        otm5: the ``WS-OTM5-Record`` linkage parameter [common/acas029.cbl:L221], typed
            as its full ``OI-Header`` view [copybooks/plwsoi.cob:L12].

    Returns:
        All 29 host variables keyed by column name. Never contains ``None``.
    """
    host_variables = blank_host_variables()
    supplier_text = supplier_characters(otm5.oi_key.oi_customer.oi_supplier)

    invoice = int(_KEY_FIELDS["oi_invoice"].store(otm5.oi_key.oi_invoice))
    host_variables["OI5-INVOICE"] = invoice

    host_variables["OI5-SUPPLIER"] = supplier_text

    # ANOMALY A3 - the key is COMPOSED from the staging area
    # [common/otm5MT.cbl:L233-L236], not copied from the record's own OI-Key group.
    host_variables["OI5-KEY"] = compose_key(supplier_text, invoice)

    # ANOMALY A6 - both are COMP (binary) in the copybook [copybooks/plwsoi.cob:L21-L22]
    # and char(5)/char(3) in the table.
    b_nos = int(_BATCH_FIELDS["oi_b_nos"].store(otm5.oi_batch.oi_b_nos))
    b_item = int(_BATCH_FIELDS["oi_b_item"].store(otm5.oi_batch.oi_b_item))
    host_variables["OI5-BATCH-NOS"] = f"{b_nos:0{_BATCH_NOS_DIGITS}d}"
    host_variables["OI5-BATCH-ITEM"] = f"{b_item:0{_BATCH_ITEM_DIGITS}d}"

    # ANOMALY A2 - the batch group carries COMP at the GROUP level
    # [copybooks/plwsoi.cob:L20] and is SIX bytes wide, yet its column is char(8).
    host_variables["OI5-BATCH"] = compose_batch(b_nos, b_item)

    # ANOMALY A4, sign loss 1 of 4.
    host_variables["OI5-DAT"] = _drop_sign(
        int(_HEADER_FIELDS["oi_date"].store(otm5.oi_date)), column="OI5-DAT"
    )

    # ANOMALY A5, numeric-to-char 1 of 2. OI-Type is PIC 9 [copybooks/plwsoi.cob:L23];
    # the host variable is X(1). Measured: OI-Type = 2 -> "2".
    host_variables["OI5-TYPE"] = f"{int(_HEADER_FIELDS['oi_type'].store(otm5.oi_type)):01d}"

    host_variables["OI5-REF"] = _HEADER_FIELDS["oi_ref"].store(otm5.oi_ref)
    host_variables["OI5-ORDER"] = _HEADER_FIELDS["oi_order"].store(otm5.oi_order)
    host_variables["OI5-HOLD-FLAG"] = _HEADER_FIELDS["oi_hold_flag"].store(
        otm5.oi_hold_flag
    )
    host_variables["OI5-UNAPL"] = _HEADER_FIELDS["oi_unapl"].store(otm5.oi_unapl)

    # COMP-3 in the copybook [copybooks/plwsoi.cob:L42-L52], S9(07)V9(02) COMP at the
    # host variable [common/otm5MT.cbl:L316-L324], decimal(9,2) in the table.
    money = otm5.filler_1
    host_variables["OI5-P-C"] = _MONEY_FIELDS["oi_p_c"].store(money.oi_p_c)
    # OI-Approp REDEFINES OI-Net and is NOT loaded - ANOMALY A8.
    host_variables["OI5-NET"] = _MONEY_FIELDS["oi_net"].store(money.oi_net)
    host_variables["OI5-EXTRA"] = _MONEY_FIELDS["oi_extra"].store(money.oi_extra)
    host_variables["OI5-CARRIAGE"] = _MONEY_FIELDS["oi_carriage"].store(
        money.oi_carriage
    )
    host_variables["OI5-VAT"] = _MONEY_FIELDS["oi_vat"].store(money.oi_vat)
    host_variables["OI5-DISCOUNT"] = _MONEY_FIELDS["oi_discount"].store(
        money.oi_discount
    )
    host_variables["OI5-E-VAT"] = _MONEY_FIELDS["oi_e_vat"].store(money.oi_e_vat)
    host_variables["OI5-C-VAT"] = _MONEY_FIELDS["oi_c_vat"].store(money.oi_c_vat)
    host_variables["OI5-PAID"] = _MONEY_FIELDS["oi_paid"].store(money.oi_paid)

    # ANOMALY A5, numeric-to-char 2 of 2. OI-Status is PIC 9 with the 88-level names
    # S-Open and S-Closed [copybooks/plwsoi.cob:L53-L55].
    host_variables["OI5-STATUS"] = (
        f"{int(_HEADER_FIELDS['oi_status'].store(otm5.oi_status)):01d}"
    )

    # ANOMALY A4, sign loss 2 of 4 - BINARY-CHAR signed to PIC 9(03) COMP.
    host_variables["OI5-DEDUCT-DAYS"] = _drop_sign(
        int(_HEADER_FIELDS["oi_deduct_days"].store(otm5.oi_deduct_days)),
        column="OI5-DEDUCT-DAYS",
    )

    # The sign SURVIVES both hops here - S9(03)V9(02) COMP at the host variable
    # [common/otm5MT.cbl:L327-L328] and signed decimal(5,2) in the table - the OPPOSITE
    # of plinvoiceMT, which is the same subsystem.
    host_variables["OI5-DEDUCT-AMT"] = _HEADER_FIELDS["oi_deduct_amt"].store(
        otm5.oi_deduct_amt
    )
    host_variables["OI5-DEDUCT-VAT"] = _HEADER_FIELDS["oi_deduct_vat"].store(
        otm5.oi_deduct_vat
    )

    # ANOMALY A4, sign loss 3 of 4.
    host_variables["OI5-DAYS"] = _drop_sign(
        int(_HEADER_FIELDS["oi_days"].store(otm5.oi_days)), column="OI5-DAYS"
    )

    host_variables["OI5-CR"] = int(_HEADER_FIELDS["oi_cr"].store(otm5.oi_cr))

    host_variables["OI5-APPLIED"] = _HEADER_FIELDS["oi_applied"].store(
        otm5.oi_applied
    )

    # ANOMALY A4, sign loss 4 of 4. The last statement of the paragraph, and the only
    # one that carries a terminating period.
    host_variables["OI5-DATE-CLEARED"] = _drop_sign(
        int(_HEADER_FIELDS["oi_date_cleared"].store(otm5.oi_date_cleared)),
        column="OI5-DATE-CLEARED",
    )

    return host_variables


def _column_text(row: Mapping[str, Any], column: str) -> str:
    """Read a ``char`` column back as the host variable's fixed-width value.

    MySQL strips trailing spaces from a ``CHAR`` on retrieval under the
    ``utf8mb3_general_ci`` PAD SPACE collation the frozen schema declares
    [mysql/ACASDB.sql:L626], whereas the host variable is a fixed-width ``PIC X(n)``
    [common/otm5MT.cbl:L304-L331].

    Args:
        row: the retrieved row, keyed by column name.
        column: the column to read.

    Returns:
        The column value padded with spaces to its declared width and truncated to it.
            Never ``None``.
    """
    width = CHARACTER_WIDTHS[column]
    value = row[column]
    text = "" if value is None else str(value)
    return text.ljust(width)[:width]


def unload_host_variables(
    row: Mapping[str, Any], otm5: OiHeader | None = None
) -> OiHeader:
    """Reproduce ``bb100-UnloadHVs`` [common/otm5MT.cbl:L1387-L1422].

    ANOMALY A1, THE HEADLINE DEFECT OF THIS BRIDGE. ``bb000-HV-Load`` loads ALL 29 host
    variables; this paragraph moves back only TWENTY-SEVEN. ``HV-OI5-KEY`` and ``HV-
    OI5-BATCH`` - precisely the two DERIVED host variables - are loaded
    [common/otm5MT.cbl:L1352, L1358] and unloaded NOWHERE
    [common/otm5MT.cbl:L1394-L1422].

    Args:
        row: one retrieved row keyed by column name, as produced by the ``FETCH`` blocks
            [common/otm5MT.cbl:L580-L609, L702-L732].
        otm5: the ``WS-OTM5-Record`` linkage parameter to fill IN PLACE, reproducing
            COBOL's pass-by-reference linkage [common/acas029.cbl:L221]. When omitted, a
            freshly initialised record is created, matching ``initialize WS-
            OTM5-Record`` [common/otm5MT.cbl:L1392].

    Returns:
        The filled record - the same object as ``otm5`` when one was supplied.
    """
    record = blank_record() if otm5 is None else otm5
    if otm5 is not None:
        blank = blank_record()
        for member in ("oi_key", "oi_date", "oi_batch", "oi_type", "oi_ref",
                       "oi_order", "oi_hold_flag", "oi_unapl", "filler_1",
                       "oi_status", "oi_deduct_days", "oi_deduct_amt",
                       "oi_deduct_vat", "oi_days", "oi_cr", "oi_applied",
                       "oi_date_cleared"):
            setattr(record, member, getattr(blank, member))

    # Numeric to numeric; PIC 9(10) COMP back into PIC 9(8) DISPLAY, so the descriptor
    # discards any high-order digit exactly as COBOL does.
    record.oi_key.oi_invoice = _KEY_FIELDS["oi_invoice"].store(row["OI5-INVOICE"])

    # A GROUP move: seven bytes into OI-Nos X(6) plus OI-Check PIC 9
    # [copybooks/plwsoi.cob:L15-L17], byte for byte.
    supplier_text = _column_text(row, "OI5-SUPPLIER")
    supplier = record.oi_key.oi_customer.oi_supplier
    supplier.oi_nos = _SUPPLIER_FIELDS["oi_nos"].store(supplier_text[:6])
    supplier.oi_check = _SUPPLIER_FIELDS["oi_check"].store(
        _zoned_integer(supplier_text[6:7], column="OI5-SUPPLIER")
    )

    # ANOMALY A4 in reverse: the column is unsigned, the field signed.
    record.oi_date = _HEADER_FIELDS["oi_date"].store(row["OI5-DAT"])

    # ANOMALY A6 in reverse: char(5) and char(3) back into COMP fields, by the measured
    # alphanumeric-to-numeric MOVE. ANOMALY A1: HV-OI5-BATCH itself is NOT read.
    record.oi_batch.oi_b_nos = _BATCH_FIELDS["oi_b_nos"].store(
        _zoned_integer(_column_text(row, "OI5-BATCH-NOS"), column="OI5-BATCH-NOS")
    )
    record.oi_batch.oi_b_item = _BATCH_FIELDS["oi_b_item"].store(
        _zoned_integer(_column_text(row, "OI5-BATCH-ITEM"), column="OI5-BATCH-ITEM")
    )

    # ANOMALY A5 in reverse: char(1) back into PIC 9. No validation against the type
    # legend [copybooks/plwsoi.cob:L25-L34] - rule R-3.
    record.oi_type = _HEADER_FIELDS["oi_type"].store(
        _zoned_integer(_column_text(row, "OI5-TYPE"), column="OI5-TYPE")
    )

    record.oi_ref = _HEADER_FIELDS["oi_ref"].store(_column_text(row, "OI5-REF"))
    record.oi_order = _HEADER_FIELDS["oi_order"].store(_column_text(row, "OI5-ORDER"))
    record.oi_hold_flag = _HEADER_FIELDS["oi_hold_flag"].store(
        _column_text(row, "OI5-HOLD-FLAG")
    )
    record.oi_unapl = _HEADER_FIELDS["oi_unapl"].store(_column_text(row, "OI5-UNAPL"))

    # decimal(9,2) back into COMP-3 s9(7)v99. Rule R-2: Decimal throughout.
    money = record.filler_1
    money.oi_p_c = _MONEY_FIELDS["oi_p_c"].store(row["OI5-P-C"])
    money.oi_net = _MONEY_FIELDS["oi_net"].store(row["OI5-NET"])
    # ANOMALY A8 - OI-Approp REDEFINES OI-Net: one storage location, two names. The
    # bridge moves only into OI-Net [common/otm5MT.cbl:L1407].
    money.oi_approp = money.oi_net
    money.oi_extra = _MONEY_FIELDS["oi_extra"].store(row["OI5-EXTRA"])
    money.oi_carriage = _MONEY_FIELDS["oi_carriage"].store(row["OI5-CARRIAGE"])
    money.oi_vat = _MONEY_FIELDS["oi_vat"].store(row["OI5-VAT"])
    money.oi_discount = _MONEY_FIELDS["oi_discount"].store(row["OI5-DISCOUNT"])
    money.oi_e_vat = _MONEY_FIELDS["oi_e_vat"].store(row["OI5-E-VAT"])
    money.oi_c_vat = _MONEY_FIELDS["oi_c_vat"].store(row["OI5-C-VAT"])
    money.oi_paid = _MONEY_FIELDS["oi_paid"].store(row["OI5-PAID"])

    # ANOMALY A5 in reverse. The 88-level predicates S-Open and S-Closed
    # [copybooks/plwsoi.cob:L54-L55] live in records/otm5.py, not here.
    record.oi_status = _HEADER_FIELDS["oi_status"].store(
        _zoned_integer(_column_text(row, "OI5-STATUS"), column="OI5-STATUS")
    )

    # tinyint(3) unsigned (0..255) back into BINARY-CHAR signed (-128..127).
    record.oi_deduct_days = _HEADER_FIELDS["oi_deduct_days"].store(
        row["OI5-DEDUCT-DAYS"]
    )

    record.oi_deduct_amt = _HEADER_FIELDS["oi_deduct_amt"].store(
        row["OI5-DEDUCT-AMT"]
    )
    record.oi_deduct_vat = _HEADER_FIELDS["oi_deduct_vat"].store(
        row["OI5-DEDUCT-VAT"]
    )

    record.oi_days = _HEADER_FIELDS["oi_days"].store(row["OI5-DAYS"])

    record.oi_cr = _HEADER_FIELDS["oi_cr"].store(row["OI5-CR"])

    record.oi_applied = _HEADER_FIELDS["oi_applied"].store(
        _column_text(row, "OI5-APPLIED")
    )

    # The last move of the paragraph. ANOMALY A4 in reverse, sign already lost.
    record.oi_date_cleared = _HEADER_FIELDS["oi_date_cleared"].store(
        row["OI5-DATE-CLEARED"]
    )

    # NOT UNLOADED, and deliberately so - ANOMALY A1: HV-OI5-KEY
    # [common/otm5MT.cbl:L304, loaded L1352] HV-OI5-BATCH [common/otm5MT.cbl:L308,
    # loaded L1358] Twenty-seven moves for twenty-nine host variables.
    return record


def _bridge_initialise(file_access: FileAccess) -> None:
    """Reproduce ``ba010-Initialise`` [common/otm5MT.cbl:L387-L399].

    ANOMALY A36, NEW AND NOT IN THE WORKING SPECIFICATION. The paragraph zeroes ``SQL-
    State`` and blanks six diagnostic fields, but its zeroing of ``We-Error`` and ``Fs-
    Reply`` is COMMENTED OUT [common/otm5MT.cbl:L390-L391].

    Args:
        file_access: the ``File-Access`` linkage block whose ``Logging-Data`` sub-block
            carries the diagnostic fields [copybooks/wsfnctn.cob:L44-L55].
    """
    logging_data = file_access.logging_data
    logging_data.sql_state = "0" * SQL_STATE_WIDTH
    # L393-L399: move spaces to WS-MYSQL-Error-Message, WS-MYSQL-Error-Number, WS-Log-
    # Where, WS-File-Key, SQL-Msg, SQL-Err. The first two are the bridge's own working
    # storage and have no linkage counterpart.
    logging_data.ws_log_where = " " * WS_LOG_WHERE_WIDTH
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    # L390-L391 - the zeroing of We-Error and Fs-Reply is COMMENTED OUT and is therefore
    # NOT performed here. Anomaly A36.


def _set_file_key(file_access: FileAccess, value: str) -> None:
    """Store the logging key, reproducing ``move ... to WS-File-Key``.

    ``WS-File-Key`` is ``pic x(64)`` [copybooks/wsfnctn.cob:L52], so a shorter value is
    space-padded and a longer one truncated, exactly as a COBOL ``MOVE`` to an
    alphanumeric field does.

    Args:
        file_access: the linkage block holding ``Logging-Data``.
        value: the key or literal to record.
    """
    file_access.logging_data.ws_file_key = value.ljust(WS_FILE_KEY_WIDTH)[
        :WS_FILE_KEY_WIDTH
    ]


def _set_log_where(file_access: FileAccess, value: str) -> None:
    """Store the predicate text, reproducing ``move WS-Where (1:J)``.

    ``WS-Log-Where`` is ``pic x(231)`` [copybooks/wsfnctn.cob:L53], and the width is
    taken from that declaration rather than from the field's current contents -
    correction C9, as for :func:`_set_file_key`.

    Args:
        file_access: the linkage block holding ``Logging-Data``.
        value: the ``WHERE`` text the verb built.
    """
    file_access.logging_data.ws_log_where = value.ljust(WS_LOG_WHERE_WIDTH)[
        :WS_LOG_WHERE_WIDTH
    ]


def _trace(file_access: FileAccess, number: int) -> None:
    """Record ``move <n> to ws-No-Paragraph``, the bridge's trace number.

    Args:
        file_access: the linkage block holding ``Logging-Data``.
        number: the paragraph number the frozen source moves.
    """
    file_access.logging_data.ws_no_paragraph = number


def _status(file_access: FileAccess, fs_reply: int, we_error: int) -> StatusPair:
    """Assign the status pair to the linkage block and return it.

    Args:
        file_access: the linkage block to update.
        fs_reply: the ``FS-Reply`` value the frozen source moves.
        we_error: the ``WE-Error`` value the frozen source moves.

    Returns:
        The pair, so a verb can ``return _status(...)`` in one statement the way the
            COBOL falls through to ``ba999-end``.
    """
    file_access.fs_reply = int(fs_reply)
    file_access.we_error = int(we_error)
    return (FsReply(fs_reply) if fs_reply in _FS_REPLY_VALUES else fs_reply, int(we_error))


_FS_REPLY_VALUES: Final[frozenset[int]] = frozenset(int(member) for member in FsReply)


def record_size_gate(file_access: FileAccess) -> StatusPair | None:
    """Reproduce ``ba012-Test-WS-Rec-Size-2`` [common/acas029.cbl:L553-L593].

    The ``string``/``display``/``accept`` between them [common/acas029.cbl:L568-L579] is
    presentation and is dropped per Agent Action Plan section 0.3.4, but the CONTROL
    TRANSFER it guards is preserved: when the gate trips, no statement is issued and the
    pair is returned.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``None`` when the gate passes and the bridge call may proceed, or the ``(99,
            901)`` status pair when it trips, in which case the caller must NOT issue
            any statement.
    """
    global _A, _B
    if _A == 0:
        # L556-L561: function Length (WS-OTM5-Record) and function length (Open-Item-
        # Record-5). ANOMALY A40, NEW - the same intrinsic is spelled "Length" then
        # "length" on adjacent statements.
        _A = RECORD_LENGTH
        _B = RECORD_LENGTH
        if _A < _B:
            _LOG.error(
                "%s: temp record length %d is shorter than the file record "
                "length %d; the caller must stop - WE-Error 901 "
                "[common/acas029.cbl:L562-L564]",
                HANDLER,
                _A,
                _B,
            )
            return _status(file_access, FsReply.ERROR, RECORD_SIZE_WE_ERROR)
    return None


# STATEMENT ASSEMBLY - bb200-Insert, bb300-Update, and the two predicates The frozen
# bridge assembles LITERAL SQL text and wraps EVERY value in double quotes, numerics
# included.

_INT_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "INT"
)

_TINYINT_COLUMNS: Final[tuple[str, ...]] = tuple(
    loader.column_for(entry.key).name
    for entry in _ENTRIES
    if loader.column_for(entry.key).base_type.value == "TINYINT"
)

#: The nine ``decimal(9,2)`` money columns, rendered as ``(14:07)`` plus a stop plus
#: ``(22:02)``.
_MONEY_COLUMNS: Final[tuple[str, ...]] = tuple(
    name
    for name in DECIMAL_COLUMNS
    if int(loader.column_for(DICTIONARY_KEYS[name]).display_width or 0) == 9
)

_DEDUCTION_COLUMNS: Final[tuple[str, ...]] = tuple(
    name
    for name in DECIMAL_COLUMNS
    if int(loader.column_for(DICTIONARY_KEYS[name]).display_width or 0) == 5
)


def render_column(column: str, value: str | int | decimal.Decimal) -> str:
    """Render one host variable to the characters the bridge would inline.

    Routes to the renderer the frozen source uses for that column, chosen from the
    DICTIONARY-resolved SQL type and declared width rather than from the column's name,
    so the routing is derived and not transcribed (rule R-5).

    Args:
        column: the column name, which must be one of :data:`COLUMNS`.
        value: the host-variable value from :func:`load_host_variables`.

    Returns:
        The exact characters the bridge's ``STRING`` would have emitted.

    Raises:
        KeyError: if ``column`` is not a column of this table.
    """
    if column in CHARACTER_WIDTHS:
        return render_character_column(str(value))
    if column in _INT_COLUMNS:
        return render_integer_column(int(value))
    if column in _TINYINT_COLUMNS:
        return render_tinyint_column(int(value))
    if column in _MONEY_COLUMNS:
        return render_money_column(decimal.Decimal(value))
    if column in _DEDUCTION_COLUMNS:
        return render_deduction_column(decimal.Decimal(value))
    raise KeyError(f"{TABLE} has no column {column!r}")


def rendered_values(
    host_variables: Mapping[str, str | int | decimal.Decimal],
) -> tuple[str, ...]:
    """Render all 29 host variables, in COLUMN order.

    ANOMALY A28 - column order is the third of the bridge's three orders, and it is the
    one both mutating paragraphs emit [common/otm5MT.cbl:L1441-L1805, L1831-L2195].

    Args:
        host_variables: the mapping from :func:`load_host_variables`.

    Returns:
        Twenty-nine rendered strings in :data:`COLUMNS` order.
    """
    return tuple(render_column(column, host_variables[column]) for column in COLUMNS)


def _assignment_list() -> str:
    r"""Build the shared ``SET`` list of both mutating statements.

    Every identifier goes through :func:`quote_identifier`, without exception. Agent
    Action Plan section 3.21's warning applies to every name in this schema.

    Returns:
        ``\`OI5-KEY\`=%s, \`OI5-SUPPLIER\`=%s, ...`` for all 29 columns.
    """
    return ", ".join(f"{quote_identifier(column)}=%s" for column in COLUMNS)


def _record_key(otm5: OiHeader) -> str:
    """Return ``WS-OTM5-Record (K:L)`` - the record's own leading 15 bytes.

    The delete and rewrite predicates are built from the RECORD BUFFER, not from ``HV-
    OI5-KEY`` [common/otm5MT.cbl:L909, L963], using the offset and length the bridge's
    key metadata declares - ``'00010015'``, offset 1 length 15 [common/otm5MT.cbl:L252],
    read here from :data:`KEY_OFFSET`/:data:`KEY_LENGTH` through
    ``cursor_state.key_of_reference`` so the numbers are never hard-coded.

    Args:
        otm5: the linkage record.

    Returns:
        Exactly :data:`KEY_LENGTH` characters, untrimmed - the bridge strings the slice
            ``delimited by size`` [common/otm5MT.cbl:L907-L909], so any interior space
            is part of the predicate.
    """
    supplier = supplier_characters(otm5.oi_key.oi_customer.oi_supplier)
    key = compose_key(supplier, int(otm5.oi_key.oi_invoice))
    start = KEY_OFFSET - 1
    return key[start : start + KEY_LENGTH]


def _key_predicate(key: str) -> tuple[str, str]:
    r"""Build the primary-key predicate in both of its needed forms.

    Reproduces the ``string`` at [common/otm5MT.cbl:L903-L911] for delete and
    [common/otm5MT.cbl:L957-L967] for rewrite - identical text in both.

    Args:
        key: the fifteen key characters from :func:`_record_key`.

    Returns:
        A pair. First the parameterised text for execution, ``\`OI5-KEY\`=%s``.
    """
    quoted = quote_identifier(PRIMARY_KEY)
    return (f"{quoted}=%s", f'{quoted}="{key}"')


@contextmanager
def _cursor(connection: MySQLConnectionAbstract) -> Iterator[DatabaseCursor]:
    """Yield a plain driver cursor for the positioning verbs.

    ``cursor_state``'s ``start``, ``read_next`` and ``read_indexed`` issue their OWN
    statement on the cursor they are handed, so they cannot be fed from
    :func:`execute_statement`, which executes the statement itself.

    Args:
        connection: the open connection.

    Yields:
        A cursor satisfying the ``DatabaseCursor`` protocol - ``execute``, ``fetchone``
            and ``description``.
    """
    cursor = acquire_cursor(connection)
    try:
        yield cursor
    finally:
        #  NEITHER CLEANUP PATH LOGS, AND NEITHER BINDS A NAME. The frozen
        #  bridge has no result-discard step and no cursor-close step - `MySQL_query`
        #  owns the statement and the handle - so a record on either was invented
        #  (R-4), and both records interpolated the driver's own text, which for
        #  these tables renders the statement and its bound values (CWE-532).
        #  `redact_for_log` escaped it and removed none of it. Binding no name means
        #  nothing can leak from either block by accident; the underlying failure, if
        #  it matters, is reported once by the statement path that owns it.
        discard_unread = getattr(connection, "consume_results", None)
        if discard_unread is not None:
            try:
                discard_unread()
            except Exception:  # noqa: BLE001, S110 - see above
                pass
        try:
            cursor.close()
        except Exception:  # noqa: BLE001, S110 - see above
            pass


def _driver_failure(error: BaseException) -> tuple[str, str, str]:
    """Describe a driver failure the way the frozen error path describes one.

    The bridge calls ``MySQL_errno``, ``MySQL_sqlstate`` and ``MySQL_error`` in that
    order and moves the three results into ``SQL-Err``, ``SQL-State`` and ``SQL-Msg``
    [common/otm5MT.cbl:L878-L884].

    Args:
        error: the exception the driver raised.

    Returns:
        The error number as text, its log category, and the redacted message.
    """
    errno = getattr(error, "errno", "") or ""
    return (
        str(errno),
        db_error_log_category(errno),
        redact_for_log(str(error)),
    )


def _apply_driver_failure(
    file_access: FileAccess, error: BaseException, *, command: str
) -> tuple[str, str]:
    """Fill the diagnostic fields from a driver failure and report the pair.

    Reproduces the inner block every mutating verb shares [common/otm5MT.cbl:L878-L890,
    L931-L939, L972-L980]: fetch the SQLSTATE into ``SQL-State`` unconditionally, and
    fetch the number and message into ``SQL-Err`` and ``SQL-Msg`` ONLY when the number
    is not ``"0 "``.

    Args:
        file_access: the linkage block to fill.
        error: the exception the driver raised.
        command: the operation name, for ``status.py``'s duplicate detection.

    Returns:
        The ``(SQL-Err, SQL-State)`` pair, which the write verb then tests for a
            duplicate key.
    """
    errno, _category, message = _driver_failure(error)
    status = mysql_1100_db_error(
        errno=errno,
        message=message,
        sql_state=str(getattr(error, "sqlstate", "") or ""),
        command=command,
    )
    logging_data = file_access.logging_data
    logging_data.sql_state = str(status.sql_state).ljust(SQL_STATE_WIDTH)[
        :SQL_STATE_WIDTH
    ]
    if errno and errno != "0":
        logging_data.sql_err = str(status.sql_err).ljust(SQL_ERR_WIDTH)[
            :SQL_ERR_WIDTH
        ]
        logging_data.sql_msg = str(status.sql_msg).ljust(SQL_MSG_WIDTH)[
            :SQL_MSG_WIDTH
        ]
    return (str(status.sql_err), str(status.sql_state))


def _clear_sql_diagnostics(file_access: FileAccess) -> None:
    """Reproduce ``move spaces to SQL-Msg`` plus ``move zero to SQL-Err``.

    Args:
        file_access: the linkage block to clear.
    """
    logging_data = file_access.logging_data
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = "0" * SQL_ERR_WIDTH


def _require_connection(operation: str) -> MySQLConnectionAbstract:
    """Return the open connection, or refuse the verb.

    The bridge keeps its connection in its own working storage across calls -
    ``MYSQL-1000-OPEN`` establishes it [common/otm5MT.cbl:L463] and ``MYSQL-1980-CLOSE``
    tears it down [common/otm5MT.cbl:L487] - so a module-level handle is the faithful
    model, not a per-call connect.

    Args:
        operation: the function-code name, for the message.

    Returns:
        The open connection.

    Raises:
        AcasFileHandlerError: if :func:`open_` has not run, or :func:`close` has already
            run.
    """
    if _CONNECTION is None:
        raise AcasFileHandlerError(
            int(FsReply.ERROR),
            int(WeError.UNKNOWN_UNEXPECTED),
            operation=operation,
            table=TABLE,
        )
    return _CONNECTION


# SECTION. The handler's flat-file verbs ``aa020`` through ``aa100``
# [common/acas029.cbl:L301-L523] ARE NEVER REACHED ON THE RDB PATH, and the frozen
# source says so in its own words.


def open_(
    system: SystemRecord,
    file_access: FileAccess,
    *,
    transport: TransportSecurity | None = None,
) -> StatusPair:
    """Reproduce ``ba020-Process-Open`` [common/otm5MT.cbl:L433-L475].

    1. String the six connection fields, each ``delimited by space`` and terminated
    ``X"00"`` [common/otm5MT.cbl:L438-L461]. ANOMALY A32 - the order here is Schema,
    HOST, UName, UPass, Port, Socket, which is the THIRD order these six fields appear
    in; see :func:`record_size_gate`.

    Args:
        system: the ``System-Record`` linkage parameter [common/acas029.cbl:L219], whose
            ``RDBMS-`` fields carry the six connection parameters
            [copybooks/wsfnctn.cob:L56-L62].
        file_access: the ``File-Access`` linkage block.
        transport: TLS material for the connection. ``None`` - what every
            in-scope caller passes - defers to the ONE policy the deployment
            installed with
            :func:`acas_posting.dal.connection.set_connection_policy`, so this
            handler declares nothing of its own.

    Returns:
        ``(0, 0)`` when the database opened, otherwise the pair ``mysql_1000_open``
            reported, unchanged - the bridge performs no recovery of its own.
    """
    global _CONNECTION
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba020-Process-Open"][0])
    outcome = mysql_1090_exit(mysql_1000_open(system, transport=transport))
    logging_data = file_access.logging_data
    logging_data.sql_err = str(outcome.sql_err).ljust(SQL_ERR_WIDTH)[
        :SQL_ERR_WIDTH
    ]
    logging_data.sql_msg = str(outcome.sql_msg).ljust(SQL_MSG_WIDTH)[
        :SQL_MSG_WIDTH
    ]
    logging_data.sql_state = str(outcome.sql_state).ljust(SQL_STATE_WIDTH)[
        :SQL_STATE_WIDTH
    ]
    if int(outcome.fs_reply) != int(FsReply.SUCCESS):
        # Step 4 - L464-L465: no file key, no cursor change, straight out.
        # ONE ERROR, through the shared reporter, so this failure renders with the
        # same fields in the same order as every other handler's.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba020-Process-Open",
            locator="[common/otm5MT.cbl:L463]",
            fs_reply=int(outcome.fs_reply),
            we_error=int(outcome.we_error),
            sql_state=str(outcome.sql_state),
            detail="MYSQL-1000-OPEN failed; no file key is written and the cursor "
            "state is left as it stood",
        )
        return _status(file_access, int(outcome.fs_reply), int(outcome.we_error))
    _CONNECTION = outcome.connection
    _set_file_key(file_access, OPEN_FILE_KEY)
    _STATES.reset(TABLE)
    return _status(file_access, int(outcome.fs_reply), int(outcome.we_error))


#: ``fn-input`` (Access-Type 1). The bridge's open takes NO access type
#: [common/otm5MT.cbl:L433-L475], so this is the same open.
open_input = open_

#: ``fn-i-o`` (Access-Type 2). Same open.
open_i_o = open_

#: ``fn-output`` (Access-Type 3). Same open.
open_output = open_

#: ``fn-extend`` (Access-Type 4). Same open.
open_extend = open_


def close(file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba030-Process-Close`` [common/otm5MT.cbl:L477-L489].

    ANOMALY A36 - the paragraph ASSIGNS NO STATUS. Combined with ``ba010-Initialise``
    declining to zero the pair [common/otm5MT.cbl:L390-L391], a close therefore returns
    the caller's INCOMING ``FS-Reply`` and ``WE-Error`` untouched.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        The incoming status pair, unmodified.
    """
    global _CONNECTION
    # Step 1 - L478-L479, and ANOMALY A10.
    state = _STATES.state_for(TABLE, CURSOR_SLOT)
    if state.cursor_active():
        _trace(file_access, BRIDGE_TRACE_NUMBERS["ba998-Free"][0])
        state.free()
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba030-Process-Close"][0])
    _set_file_key(file_access, CLOSE_FILE_KEY)
    mysql_1980_close(_CONNECTION)
    mysql_1999_exit()
    _CONNECTION = None
    # ANOMALY A36 - no status is written; the incoming pair stands.
    incoming = int(file_access.fs_reply)
    return (
        FsReply(incoming) if incoming in _FS_REPLY_VALUES else incoming,
        int(file_access.we_error),
    )


def start(
    otm5: OiHeader, file_access: FileAccess, access_type: int
) -> StatusPair:
    """Reproduce ``ba060-Process-Start`` [common/otm5MT.cbl:L761-L863].

    Delegated to ``cursor_state.start``, which implements exactly this shape: the guard,
    the ``if Cursor-Active perform ba998-Free`` [common/otm5MT.cbl:L772-L773], the
    relation map, the predicate with ``ORDER BY <key> ASC``
    [common/otm5MT.cbl:L798-L813], and the positioning.

    Args:
        otm5: the linkage record, whose leading fifteen bytes supply the key - ``WS-
            OTM5-Record (K:L)`` [common/otm5MT.cbl:L802].
        file_access: the ``File-Access`` linkage block.
        access_type: ``Access-Type``, ``5``..``8`` accepted. The declaration is ``03
            Access-Type pic 9`` [copybooks/wsfnctn.cob:L107] and its condition names run
            ``fn-input`` value 1 through ``fn-not-greater-than`` value 9
            [copybooks/wsfnctn.cob:L108-L116].

    Returns:
        ``(0, 0)`` when positioned, ``(21, 0)`` when nothing qualified, or ``(99, 997)``
            when the access type is out of range.

    Raises:
        AcasFileHandlerError: if no connection is open. The frozen source has no status
            for a verb issued before its open, because the menu always opens first.
    """
    connection = _require_connection("fn-start")
    key = _record_key(otm5)
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba060-Process-Start"][0])
    with _cursor(connection) as cursor:
        outcome = _cursor_start(
            cursor,
            TABLE,
            key,
            access_type,
            key_number=KEY_COUNT,
            slot=CURSOR_SLOT,
            states=_STATES,
            file_access=file_access,
        )
    if outcome.statement:
        _set_log_where(file_access, outcome.statement)
    if not outcome.status_written:
        # ANOMALY A41 - otm5MT ALWAYS writes (21, 0) here, unlike glpostingMT.
        # [common/otm5MT.cbl:L850-L851].
        _set_file_key(file_access, key)
        return _status(
            file_access, FsReply.INVALID_KEY_ON_START, int(WeError.SUCCESS)
        )
    if int(outcome.fs_reply) == int(FsReply.SUCCESS):
        _set_file_key(file_access, outcome.file_key or key)
    else:
        # L815: move WS-OTM5-Record (K:L) to WS-File-Key, on the guard path too.
        _set_file_key(file_access, key)
    return (
        FsReply(int(outcome.fs_reply))
        if int(outcome.fs_reply) in _FS_REPLY_VALUES
        else int(outcome.fs_reply),
        int(outcome.we_error),
    )


def read_next(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    r"""Reproduce ``ba040-Process-Read-Next`` plus ``ba041-Reread``.

    STAGE A, only ``if Cursor-Not-Active`` [common/otm5MT.cbl:L497]: issue ORDER BY
    \`OI5-KEY\` ASC;`` [common/otm5MT.cbl:L503-L533], store the result, and set the file
    key to the low key [common/otm5MT.cbl:L535]. The literal fifteen zeros are "the
    lowest possible key" [common/otm5MT.cbl:L493-L495].

    Args:
        otm5: the linkage record, filled in place on a successful fetch.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)`` with ``otm5`` filled, or ``(10, 10)`` at end of file.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-read-next")
    state = _STATES.state_for(TABLE, CURSOR_SLOT)
    stage_a = not state.cursor_active()
    _trace(
        file_access,
        BRIDGE_TRACE_NUMBERS["ba040-Process-Read-Next"][0 if stage_a else 1],
    )
    if stage_a:
        _set_file_key(file_access, SEQUENTIAL_LOW_KEY)
    else:
        _set_log_where(file_access, "")
    with _cursor(connection) as cursor:
        outcome = _cursor_read_next(
            cursor,
            TABLE,
            slot=CURSOR_SLOT,
            states=_STATES,
            file_access=file_access,
        )
    if stage_a and outcome.statement:
        _set_log_where(file_access, outcome.statement)
    if outcome.row is None:
        # L551-L554 / L613-L618 / L622-L636 / L639-L642 - every exhaustion path is (10,
        # 10) and each stamps its own marker. ANOMALY A11.
        _set_file_key(file_access, outcome.file_key or EOF_FILE_KEYS[0])
        return _status(file_access, int(outcome.fs_reply), int(outcome.we_error))
    # L645-L647: perform bb100-UnloadHVs, then the KEY column becomes the file key, then
    # (0, 0).
    unload_host_variables(outcome.row, otm5)
    _set_file_key(file_access, _column_text(outcome.row, PRIMARY_KEY))
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def read_indexed(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    r"""Reproduce ``ba050-Process-Read-Indexed`` [common/otm5MT.cbl:L650-L759].

    ``SELECT * FROM \`PUITM5-REC\` WHERE \`OI5-KEY\`="<15 bytes>";`` with NO ``ORDER
    BY`` [common/otm5MT.cbl:L661-L688] - rule R-6 forbids adding one, and none is
    needed.

    Args:
        otm5: the linkage record; supplies the key and is filled in place.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)``, ``(23, 0)`` on a miss, or ``(23, 990)``/``(23, 989)`` on a driver
            failure.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-read-indexed")
    key = _record_key(otm5)
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba050-Process-Read-Indexed"][0])
    _, literal = _key_predicate(key)
    _set_log_where(file_access, literal)
    with _cursor(connection) as cursor:
        outcome = _cursor_read_indexed(
            cursor,
            TABLE,
            key,
            key_number=KEY_COUNT,
            slot=CURSOR_SLOT,
            states=_STATES,
            file_access=file_access,
        )
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba050-Process-Read-Indexed"][1])
    _STATES.state_for(TABLE, CURSOR_SLOT).free()
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba998-Free"][0])
    if outcome.row is None:
        # ANOMALY A49, NEW - THE SHARED HELPER CARRIES ANOTHER BRIDGE'S CODES,
        # `dal.cursor_state.read_indexed` is written against `glpostingMT`, whose ba050
        # does `move 21 to fs-Reply *> could also be 23 or 14`
        # [common/glpostingMT.cbl:L634] and deliberately leaves `We-Error` at the
        # caller's incoming value.
        if int(outcome.we_error) == int(WeError.RDB_INIT_ERROR):
            # L737-L753: the FETCH stage found the count not greater than zero, so the
            # driver is reporting a real error.
            we_error = READ_INDEXED_DRIVER_WE_ERROR
            _set_file_key(file_access, "")
        else:
            # L691-L695: the clean miss. `move 23 to fs-Reply`, `move zero to WE-Error`,
            # `go to ba998-Free` - and NOTHING ELSE.
            we_error = int(WeError.SUCCESS)
        return _status(file_access, READ_INDEXED_MISS_FS_REPLY, we_error)
    unload_host_variables(outcome.row, otm5)
    _set_file_key(file_access, _column_text(outcome.row, PRIMARY_KEY))
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def write(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba070-Process-Write`` [common/otm5MT.cbl:L867-L892].

    1. ``perform bb000-HV-Load`` [common/otm5MT.cbl:L868] - all 29 host variables,
    including the two write-only ones (ANOMALY A1). 2. ``move OI-Key to WS-File-Key``
    [common/otm5MT.cbl:L869] - the RECORD's key group, not ``HV-OI5-KEY``. 3.

    Args:
        otm5: the linkage record to insert.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)`` on success, ``(22, 0)`` on a duplicate key, ``(99, 0)`` otherwise.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-write")
    host_variables = load_host_variables(otm5)
    _set_file_key(file_access, _record_key(otm5))
    _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))
    logging_data = file_access.logging_data
    logging_data.sql_state = "0" * SQL_STATE_WIDTH
    _clear_sql_diagnostics(file_access)
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba070-Process-Write"][0])
    statement = (
        f"INSERT INTO {quote_identifier(TABLE)} SET {_assignment_list()};"
    )
    parameters = rendered_values(host_variables)
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:
        # L878-L890 - the count stays at zero when the query fails, so the failure arm
        # below is what the COBOL reaches.
        sql_err, sql_state = _apply_driver_failure(
            file_access, error, command="INSERT"
        )
        # L886-L889: the duplicate test, delegated to status.py so the "1062" or "1022"
        # or SQLSTATE "23000" triple is expressed in one place.
        if is_duplicate_key_bridge_level(sql_err, sql_state):
            # ANOMALY A44 - WE-Error stays zero even here.
            return _status(
                file_access, FsReply.DUPLICATE_KEY, int(WeError.SUCCESS)
            )
        return _status(file_access, FsReply.ERROR, int(WeError.SUCCESS))
    if affected != 1:
        # L877 with no exception raised - the row count disagreed, and the
        # frozen source's only outcome for that is (99, 0). ANOMALY A44.
        # ONE ERROR, through the shared reporter. The arm writes (99, 0) back to
        # the caller, so it is a failure and WARNING put it below the level an
        # operator watches; the row COUNT is safe to name, the row is not.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba070-Process-Write",
            locator="[common/otm5MT.cbl:L877-L881]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.SUCCESS),
            detail="the INSERT affected %d rows, not 1; WE-Error stays zero "
            "(anomaly A44)" % affected,
        )
        return _status(file_access, FsReply.ERROR, int(WeError.SUCCESS))
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def rewrite(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba090-Process-Rewrite`` [common/otm5MT.cbl:L949-L991].

    1. ``perform bb000-HV-Load`` [common/otm5MT.cbl:L950]. 2. ``move OI-Key to WS-File-
    Key`` [common/otm5MT.cbl:L951]. 3. ``move 17 to ws-No-Paragraph``
    [common/otm5MT.cbl:L952] - set BEFORE the predicate is built, where the write sets
    its number after the clears. 4.

    Args:
        otm5: the linkage record; supplies both the new values and the key.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(0, 0)`` on success, ``(99, 994)`` when the affected count is not 1.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-re-write")
    host_variables = load_host_variables(otm5)
    key = _record_key(otm5)
    _set_file_key(file_access, key)
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba090-Process-Rewrite"][0])
    predicate, literal = _key_predicate(key)
    _set_log_where(file_access, literal)
    statement = (
        f"UPDATE {quote_identifier(TABLE)} SET {_assignment_list()} "
        f"WHERE {predicate};"
    )
    parameters = (*rendered_values(host_variables), key)
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:
        _apply_driver_failure(file_access, error, command="UPDATE")
        return _status(file_access, FsReply.ERROR, REWRITE_ROWCOUNT_WE_ERROR)
    if affected != 1:
        # Step 6 - L984-L985.
        # ONE ERROR, through the shared reporter, as for the write arm above.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba090-Process-Rewrite",
            locator="[common/otm5MT.cbl:L982-L985]",
            fs_reply=int(FsReply.ERROR),
            we_error=REWRITE_ROWCOUNT_WE_ERROR,
            detail="the UPDATE affected %d rows, not 1" % affected,
        )
        return _status(file_access, FsReply.ERROR, REWRITE_ROWCOUNT_WE_ERROR)
    _clear_sql_diagnostics(file_access)
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def delete(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    r"""Reproduce ``ba080-Process-Delete`` [common/otm5MT.cbl:L895-L947].

    1. Build ``\`OI5-KEY\`="<15 bytes>"`` from the RECORD BUFFER
    [common/otm5MT.cbl:L903-L911]. NO ``bb000-HV-Load`` here - a delete needs only the
    key, so the host variables are never loaded. 2. ``move WS-OTM5-Record (K:L) to WS-
    File-Key`` [common/otm5MT.cbl:L912] and the predicate to ``WS-Log-Where``
    [common/otm5MT.cbl:L913].

    Args:
        otm5: the linkage record; only its leading fifteen bytes are used.
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(99, 995)`` when the affected count is not 1, otherwise the caller's incoming
            pair, unmodified.

    Raises:
        AcasFileHandlerError: if no connection is open.
    """
    connection = _require_connection("fn-delete")
    key = _record_key(otm5)
    predicate, literal = _key_predicate(key)
    _set_file_key(file_access, key)
    _set_log_where(file_access, literal)
    _trace(file_access, BRIDGE_TRACE_NUMBERS["ba080-Process-Delete"][0])
    statement = f"DELETE FROM {quote_identifier(TABLE)} WHERE {predicate};"
    try:
        with execute_statement(connection, statement, (key,)) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:
        _apply_driver_failure(file_access, error, command="DELETE")
        return _status(file_access, FsReply.ERROR, DELETE_ROWCOUNT_WE_ERROR)
    if affected != 1:
        # Step 5 - L940-L941.
        # ONE ERROR, through the shared reporter, as for the two arms above.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba080-Process-Delete",
            locator="[common/otm5MT.cbl:L930-L941]",
            fs_reply=int(FsReply.ERROR),
            we_error=DELETE_ROWCOUNT_WE_ERROR,
            detail="the DELETE affected %d rows, not 1" % affected,
        )
        return _status(file_access, FsReply.ERROR, DELETE_ROWCOUNT_WE_ERROR)
    # Step 6 - L943-L945: the diagnostics only. ANOMALY A36 - the status pair is NOT
    # written, so the caller's incoming values stand.
    _clear_sql_diagnostics(file_access)
    incoming = int(file_access.fs_reply)
    return (
        FsReply(incoming) if incoming in _FS_REPLY_VALUES else incoming,
        int(file_access.we_error),
    )


def delete_all(file_access: FileAccess) -> StatusPair:
    """Refuse ``fn-Delete-All`` - this pair implements no such verb.

    ANOMALY A16, stated as an ABSENCE. Function code 6 is dispatched by NEITHER program.

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(99, 990)`` - the BRIDGE's bad-function pair, per ANOMALY A12.
    """
    # ONE ERROR, through the shared reporter. A published facade verb that can
    # NEVER succeed is exactly what an operator must be able to find; at DEBUG it
    # was invisible at the level anyone watches - the same reasoning that took
    # anomaly A6's refusal in `acas008` off DEBUG.
    log_handler_failure(
        _LOG,
        program=HANDLER,
        paragraph="fn-Delete-All",
        locator="[common/acas029.cbl:L294]",
        detail="fn-Delete-All is implemented by neither program; function code 6 "
        "is 'spare / unused' and reaches bad-function in both, so no statement "
        "is issued (anomaly A12)",
    )
    return bad_function(file_access)


def _sorted_where_1_to_j(function: FileFunction) -> str:
    """Return ``WS-Where (1:J)`` for one of the two sorted reads.

    THE POINTER OVERRUNS BY ONE, AND THAT ONE CHARACTER IS OBSERVABLE. ``J`` starts at
    1 and ``STRING ...

    Args:
        function: :attr:`~acas_posting.dal.status.FileFunction.READ_BY_BATCH` (32) or
            :attr:`~acas_posting.dal.status.FileFunction.READ_BY_CUST` (33).

    Returns:
        The transcribed ``ORDER BY`` text plus the one space the pointer overran -
            exactly what ``ws-Where (1:J)`` holds.

    Raises:
        ValueError: If the transcribed text and the shared table's declared ordering
            disagree, which would mean one of the two had been misread.
    """
    text = _SORTED_ORDER_BY_TEXT[function]
    declared = _EXTRA_READS[function]
    if declared.predicate_present:
        raise ValueError(
            f"{BRIDGE} declares a predicate for {function.name}, but "
            f"{declared.source_locator} builds ORDER BY only"
        )
    missing = tuple(
        term.column_name
        for term in declared.order_terms
        if f"'{term.column_name}'" not in text
    )
    if missing:
        raise ValueError(
            f"{BRIDGE} ORDER BY text for {function.name} omits "
            f"{', '.join(missing)} {declared.source_locator}"
        )
    return f"{text} "


def _sorted_select_statement(where_1_to_j: str) -> str:
    """Assemble the sorted read's ``SELECT``, malformed exactly as frozen.

    Args:
        where_1_to_j: The slice from :func:`_sorted_where_1_to_j`.

    Returns:
        The statement text, malformed. NOT corrected - rule R-4, and Agent Action Plan
            section 0.8.2 states the standard it is measured against.
    """
    return f"SELECT * FROM {quote_identifier(TABLE)} WHERE {where_1_to_j};"


def _sorted_store_result(cursor: DatabaseCursor) -> tuple[Mapping[str, Any], ...]:
    """Materialise the whole result, reproducing ``MYSQL-1220-STORE-RESULT``.

    ``Mysql-1220-Store-Result`` pulls every qualifying row to the client
    [copybooks/mysql-procedures.cpy:L187-L192] and ``MySQL_num_rows`` then counts it
    [:L191-L192], before ``MySQL_fetch_record`` walks it one row at a time.

    Args:
        cursor: The cursor the ``SELECT`` was issued on.

    Returns:
        Every row keyed by column name, in the order the statement returned them - which
            for ``SELECT *`` is the frozen table's declared column order.
    """
    description = cursor.description
    names = tuple(str(column[0]) for column in description) if description else ()
    rows: list[Mapping[str, Any]] = []
    while True:
        row = cursor.fetchone()
        if row is None:
            return tuple(rows)
        if isinstance(row, Mapping):
            rows.append(row)
        elif names:
            rows.append(dict(zip(names, row, strict=False)))
        else:
            rows.append({str(index): value for index, value in enumerate(row)})


def _sorted_reread(
    otm5: OiHeader,
    file_access: FileAccess,
    *,
    function: FileFunction,
    paragraph: str,
) -> StatusPair:
    """The body ``ba141-Reread`` and ``ba151-Reread`` share.

    Three exhaustion arms, ALL of them ``(10, 10)``, each stamping its own marker - the
    same anomaly A11 that ``ba041`` carries, here duplicated twice more.

    Args:
        otm5: The linkage record, filled in place on a successful fetch.
        file_access: The ``File-Access`` linkage block.
        function: Which sorted read is walking, selecting the cursor slot.
        paragraph: The reread's frozen paragraph name, for the trace number.

    Returns:
        ``(0, 0)`` with ``otm5`` filled, ``(10, 10)`` at exhaustion, or the caller's own
            untouched pair on the ``"EOF3"`` discard.
    """
    state = _STATES.state_for(TABLE, SORTED_CURSOR_SLOTS[function])
    # L1071 / L1226: move spaces to WS-Log-Where - the reread clears it, so a caller
    # inspecting the log after a fetch sees no predicate at all.
    _set_log_where(file_access, "")
    # L1072 / L1227: move 22 to ws-No-Paragraph. Both rereads stamp 22, as does `ba041`,
    # so the stamp cannot tell the three walks apart.
    _trace(file_access, BRIDGE_TRACE_NUMBERS[paragraph][1])
    # The caller's pair, read LIVE rather than snapshotted, because the frozen source
    # tests the shared field after the fetch and nothing between entry and the test
    # writes it - `ba010-Initialise` does not reset the pair (anomaly A36) and neither
    # the SELECT half's success path nor this paragraph's own moves touch it.
    incoming_fs_reply = int(file_access.fs_reply)
    row = state.fetch_record()
    if row is None:
        # L1114-L1118 / L1269-L1273: `if return-code = -1 / move 10 to fs-Reply WE-
        # Error` - ONE statement writing BOTH fields, so We-Error is 10 and not zero.
        state.set_cursor_not_active()
        _set_file_key(file_access, EOF_FILE_KEYS[0])
        end_fs_reply, end_we_error = end_of_file_status()
        return _status(file_access, int(end_fs_reply), end_we_error)
    if incoming_fs_reply == int(FsReply.END_OF_FILE):
        # L1138-L1142 / L1293-L1297. The row has ALREADY been consumed from the stored
        # result above, exactly as the frozen fetch consumes it, and is now discarded.
        state.set_cursor_not_active()
        #  NO RECORD HERE. [common/otm5MT.cbl:L1138-L1142] assigns NO status -
        #  the stale pair stands - and displays nothing, so a record was invented
        #  (R-4). The silent discard IS the anomaly, recorded in `ANOMALIES` and in
        #  `docs/migration/anomaly-log.md`; the identical record was removed from
        #  `dal/cursor_state.py` for the same reason.
        _set_file_key(file_access, EOF_FILE_KEYS[2])
        return (
            FsReply.END_OF_FILE,
            int(file_access.we_error),
        )
    unload_host_variables(row, otm5)
    # L1145 / L1300: move HV-OI5-KEY to WS-File-Key.
    _set_file_key(file_access, _column_text(row, PRIMARY_KEY))
    return _status(file_access, FsReply.SUCCESS, int(WeError.SUCCESS))


def _sorted_read_next(
    otm5: OiHeader,
    file_access: FileAccess,
    *,
    function: FileFunction,
    paragraph: str,
    reread_paragraph: str,
) -> StatusPair:
    """The body ``ba140`` and ``ba150`` share, statement for statement.

    ANOMALY N-sorted-order-is-a-syntax-error. THREE INDEPENDENT DEFECTS COMPOUND
    HERE, and the third hides the first two.

    Args:
        otm5: The linkage record, filled in place on a successful fetch.
        file_access: The ``File-Access`` linkage block.
        function: Which sorted read this is - 32 or 33.
        paragraph: The frozen paragraph name of the ``SELECT`` half.
        reread_paragraph: The frozen paragraph name of the reread it falls into.

    Returns:
        ``(10, 10)`` while the frozen statement stays malformed, which is always; ``(0,
            0)`` with ``otm5`` filled would require the defect to be repaired.

    Raises:
        AcasFileHandlerError: If no connection is open, which the frozen bridge has no
            status code for.
    """
    connection = _require_connection(f"fn-{function.name.lower().replace('_', '-')}")
    state = _STATES.state_for(TABLE, SORTED_CURSOR_SLOTS[function])
    if not state.cursor_not_active():
        return _sorted_reread(
            otm5, file_access, function=function, paragraph=reread_paragraph
        )
    # L1003-L1005 / L1160-L1162: the key metadata is read into K and L, and
    # then used by nothing at all - defect 3 above.
    # NO RECORD HERE. Two frozen `move`s that display nothing and whose values go
    # unused; that they go unused is a fact about the SOURCE, recorded in the comment
    # above and in `docs/migration/anomaly-log.md`, not an event.
    where_1_to_j = _sorted_where_1_to_j(function)
    # L1019 / L1174: the log records `ws-Where (1:J)` - the ORDER BY text ALONE, not the
    # statement, so the malformed `WHERE` never appears in it.
    _set_log_where(file_access, where_1_to_j)
    _trace(file_access, BRIDGE_TRACE_NUMBERS[paragraph][0])
    statement = _sorted_select_statement(where_1_to_j)
    # L1037-L1039 / L1192-L1194: `if Testing-2 display Display-Message-1`.
    #  NOTHING IS EMITTED. The record carried the WHOLE STATEMENT, which the
    #  safe-event schema forbids outright (CWE-532), and `sanitise_for_log` escaped
    #  it rather than removing it. It was also emitted UNCONDITIONALLY, so it fired
    #  on every sorted read even though the frozen `display` is gated on a switch the
    #  copybook leaves at zero. `WS-Log-Where` is still built and still stored above,
    #  because the bridge's own statements read it (R-3).
    try:
        with execute_statement(connection, statement, ()) as cursor:
            rows = _sorted_store_result(cursor)
    except Exception as error:
        # L1044-L1051 / L1199-L1206: errno, SQLSTATE and message are fetched and stored
        # - SQL-State always, the number and text only when the number is not "0 ".
        _apply_driver_failure(file_access, error, command="SELECT")
        count_rows = 0
    else:
        count_rows = len(rows)
    # L1036 / L1191: move "Sorted" to WS-File-Key - written AFTER the statement and
    # BEFORE the zero-rows test, so it survives only on the success path.
    _set_file_key(file_access, SORTED_FILE_KEY)
    if count_rows == 0:
        # `(99, 911)` the failed statement produced is replaced here by end of file, and
        # the caller sees an empty table.
        _set_file_key(file_access, NO_DATA_FILE_KEY)
        end_fs_reply, end_we_error = end_of_file_status()
        return _status(file_access, int(end_fs_reply), end_we_error)
    state.store_result(rows)
    state.set_cursor_active()
    _set_file_key(
        file_access,
        f"> 0 got cnt={count_rows:0{_TEMP_ED_ROW_DIGITS}d}{SORTED_FILE_KEY_SUFFIX}",
    )
    return _sorted_reread(
        otm5, file_access, function=function, paragraph=reread_paragraph
    )


def read_next_sorted_by_batch(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba140-Process-Read-Next`` plus ``ba141-Reread``. Function 32.

    It drives ``Most-Cursor-Set-2`` [common/otm5MT.cbl:L1002, L1057], so a by-batch walk
    and a by-key walk can be open at once - and ``ba998-Free`` clears only the first,
    which is part of anomaly A10.

    Args:
        otm5: The linkage record, filled in place on a successful fetch.
        file_access: The ``File-Access`` linkage block.

    Returns:
        ``(10, 10)`` with the file key ``"No Data"``.

    Raises:
        AcasFileHandlerError: If no connection is open.
    """
    return _sorted_read_next(
        otm5,
        file_access,
        function=FileFunction.READ_BY_BATCH,
        paragraph="ba140-Process-Read-Next",
        reread_paragraph="ba141-Reread",
    )


def read_next_sorted_by_cust(otm5: OiHeader, file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba150-Process-Read-Next`` plus ``ba151-Reread``. Function 33.

    ``fn-Read-By-Cust``, declared "for OTM3 (sl110, 120, 190)"
    [copybooks/wsfnctn.cob:L104] - three SALES report programs, and the note does not
    mention OTM5 at all, yet the frozen facade publishes the verb for this purchase
    entity too [copybooks/Proc-ACAS-FH-Calls.cob:L1305-L1308] and the bridge dispatches
    it [common/otm5MT.cbl:L427-L428].

    Args:
        otm5: The linkage record, filled in place on a successful fetch.
        file_access: The ``File-Access`` linkage block.

    Returns:
        ``(10, 10)`` with the file key ``"No Data"``.

    Raises:
        AcasFileHandlerError: If no connection is open.
    """
    return _sorted_read_next(
        otm5,
        file_access,
        function=FileFunction.READ_BY_CUST,
        paragraph="ba150-Process-Read-Next",
        reread_paragraph="ba151-Reread",
    )


def bad_function(file_access: FileAccess) -> StatusPair:
    """Reproduce ``ba100-Bad-Function`` [common/otm5MT.cbl:L1304-L1310].

    handler's ``aa100-Bad-Function`` moves ``999`` [common/acas029.cbl:L522-L523]; the
    bridge's moves ``990`` [common/otm5MT.cbl:L1308-L1309].

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``(99, 990)``.
    """
    return _status(file_access, FsReply.ERROR, BRIDGE_BAD_FUNCTION_WE_ERROR)


# ``dispatch`` is the ``acas029`` analogue.


def _process_logs(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """Reproduce ``Ca-Process-Logs`` [common/acas029.cbl:L617-L621].

    The frozen paragraph calls ``fhlogger`` passing ``File-Access`` and ``ACAS-DAL-
    Common-data``, gated on the ``Testing-1`` condition name
    [copybooks/Test-Data-Flags.cob:L11] over ``SW-Testing pic 9 value 1``.

    Args:
        file_access: the ``File-Access`` linkage block, whose ``Logging-Data`` sub-block
            carries the trace number, the file key and the ``WS-Log-Where`` text the
            frozen logger would have written.
        dal_common: the ``ACAS-DAL-Common-data`` block holding ``SW-Testing``.
    """
    if int(dal_common.sw_testing) != 1:
        return
    logging_data = file_access.logging_data
    #  THE ONE ADAPTER, shared by every handler in this package, so the single
    # legacy log this cycle produces reads the same whichever table wrote it. Two
    # fields are WITHHELD rather than sanitised: `WS-File-Key` is the open-item key
    # and `WS-Log-Where` is a predicate carrying it as a literal, and escaping either
    # leaves its content intact (CWE-532).
    #
    # `Log-File-Rec-Written` [copybooks/Test-Data-Flags.cob:L18] is `pic 9(6)`, and
    # the adapter advances it by one modulo a million exactly once per record it
    # emits. The advance USED TO BE DONE HERE as well as being the adapter's job in
    # every sibling handler; doing it in one place is what makes the counter mean the
    # same thing across the cycle.
    log_file_handler_record(
        _LOG,
        program=HANDLER,
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


def _key_guard(file_access: FileAccess) -> StatusPair | None:
    """Reproduce the handler's key guard [common/acas029.cbl:L239-L253].

    ANOMALY A18 - THE 996/998 SPLIT. The guard is a three-branch ``evaluate File-
    Function`` in which ``fn-read-indexed`` (4) and ``fn-start`` (9) FALL THROUGH into
    one shared body returning ``998`` [L240-L246] while ``fn-delete`` (8) has its own
    body returning ``996`` [L247-L252].

    Args:
        file_access: the ``File-Access`` linkage block.

    Returns:
        ``None`` when the call may proceed; otherwise the status pair the frozen guard
            would have left, already written into ``file_access``.
    """
    function = int(file_access.file_function)
    if function not in {int(code) for code in KEY_GUARDED_FUNCTIONS}:
        return None
    if int(file_access.logging_data.file_key_no) == KEY_COUNT:
        return None
    if function == int(FileFunction.DELETE):
        we_error = KEY_GUARD_WE_ERROR_DELETE
    else:
        we_error = KEY_GUARD_WE_ERROR_READ_START
    return _status(file_access, FsReply.ERROR, we_error)


def _copy_rdbms_flat_statuses(
    system: SystemRecord, file_access: FileAccess
) -> None:
    """Reproduce ``move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses``.

    A two-byte GROUP move from the system record into ``File-Access``
    [common/acas029.cbl:L258], annotated by the maintainer "needed for DAL? not JC/dbpre
    versions".

    Args:
        system: the ``System-Record`` linkage block.
        file_access: the ``File-Access`` linkage block, mutated in place.
    """
    source = system.system_data_block.rdbms_flat_statuses
    destination = file_access.fa_rdbms_flat_statuses
    destination.fa_file_system_used = int(source.file_system_used)
    destination.fa_file_duplicates_in_use = int(source.file_duplicates_in_use)


def dispatch(
    system: SystemRecord,
    otm5: OiHeader,
    file_access: FileAccess,
    file_defs: FileDefsA,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
) -> StatusPair:
    """Reproduce ``acas029``, the OTM5 file handler [common/acas029.cbl].

    This is the single entry point the facade calls, standing in for ``call "acas029"
    using System-Record WS-OTM5-Record File-Access File-Defs ACAS-DAL-Common-data``.

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob], supplying the flat/RDB
            switch and the six connection fields.
        otm5: ``WS-OTM5-Record`` viewed as ``OI-Header`` [copybooks/plwsoi.cob:L12], the
            caller's record buffer. Mutated in place by the reading verbs, exactly as
            the frozen linkage block is.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob], carrying the function
            code, the access type, the key number, the returned status pair and the
            whole ``Logging-Data`` sub-block.
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Accepted for argument-list
            fidelity and not read; see above.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob:L6], whose
            ``SW-Testing`` gates the logging.
        transport: TLS material for the connection. Keyword-only, so the five positional
            parameters still diff against the COBOL.

    Returns:
        The ``(FS-Reply, WE-Error)`` pair, also written into ``file_access``.

    Raises:
        AcasFileHandlerError: if the system record selects Cobol flat files, or if a
            data verb is issued before :func:`open_`.
    """
    logging_data = file_access.logging_data

    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT

    # [common/acas029.cbl:L239-L253] sits above the flat/RDB branch at L257, so it is
    # evaluated before the path is chosen.
    guarded = _key_guard(file_access)
    if guarded is not None:
        _process_logs(file_access, dal_common)
        return guarded

    if int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0:
        # DELIBERATE OMISSION O1, and the loudest one in this module. The frozen handler
        # would now perform ISAM I/O against open-item-file-5 [copybooks/plseloi5.cob:L2
        # assign file-29].
        raise AcasFileHandlerError(
            int(FsReply.ERROR),
            int(WeError.UNKNOWN_UNEXPECTED),
            operation="fs-cobol-files-used",
            table=TABLE,
        )

    _copy_rdbms_flat_statuses(system, file_access)

    # ba010-Test-WS-Rec-Size [L545] contains exactly one statement, and nothing performs
    # it.
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    fatal = record_size_gate(file_access)
    if fatal is not None:
        # [L576-L578] the 901 path logs INLINE - the one place other than the key guard
        # where the handler logs on the RDB path (anomaly A45) - and then [L580] go to
        # ba-rdbms-exit, which is [L613] followed by exit section [L614].
        _process_logs(file_access, dal_common)
        return fatal

    _bridge_initialise(file_access)

    function = int(file_access.file_function)

    # The bridge's own dispatch [common/otm5MT.cbl:L408-L431]. Written as an explicit
    # chain in the frozen order, one branch per ``when``, so that each arm carries its
    # locator.
    if function == int(FileFunction.OPEN):
        status = open_(system, file_access, transport=transport)
    elif function == int(FileFunction.CLOSE):
        status = close(file_access)
    elif function == int(FileFunction.READ_NEXT):
        status = read_next(otm5, file_access)
    elif function == int(FileFunction.READ_INDEXED):
        status = read_indexed(otm5, file_access)
    elif function == int(FileFunction.WRITE):
        status = write(otm5, file_access)
    elif function == int(FileFunction.RE_WRITE):
        status = rewrite(otm5, file_access)
    elif function == int(FileFunction.DELETE):
        status = delete(otm5, file_access)
    elif function == int(FileFunction.START):
        # [common/otm5MT.cbl:L423-L424] when 9 -> ba060 "Uses Header table only".
        status = start(otm5, file_access, AccessType(int(file_access.access_type)))
    elif function == int(FileFunction.READ_BY_BATCH):
        # [common/otm5MT.cbl:L425-L426] when 32 -> ba140-Process-Read-Next *> Sorted-By-
        # Batch (nos,item,type,date,inv).
        status = read_next_sorted_by_batch(otm5, file_access)
    elif function == int(FileFunction.READ_BY_CUST):
        status = read_next_sorted_by_cust(otm5, file_access)
    else:
        # [common/otm5MT.cbl:L429-L430] when other *> 6 is spare / unused. THIS ARM
        # CATCHES.
        status = bad_function(file_access)

    # if Testing-1 / perform Ca-Process-Logs / end-if, then ba999-exit [L1335] exit
    # program [L1336].
    _process_logs(file_access, dal_common)

    # [common/acas029.cbl:L611] "Any errors leave it to caller to recover from".
    return status
