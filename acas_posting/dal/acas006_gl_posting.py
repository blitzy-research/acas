"""`acas006` and its bridge `glpostingMT` - the `GLPOSTING-REC` posting table.

The data-access module for the GL-Posting entity: `gl070` reads these rows and
`gl072` posts them, and this module owns all their SQL.

The bridge's own host-variable record [common/glpostingMT.cbl:L281-L295] is what
reaches the database, not the copybook record: a dedicated paragraph loads it
field by field before a write [common/glpostingMT.cbl:L1053-L1066] and another
unloads it after a read. The load paragraph initialises the group first, so an
unset field becomes zero or space rather than SQL NULL - which is why every column
can be NOT NULL.

Cursor positioning follows the bridge's declared key metadata, so a `START`
followed by `READ NEXT` walks the same order the frozen program walked.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import ClassVar, Final

from acas_posting.dal.connection import (
    BinaryFloatingPointError,
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
from acas_posting.dal.cursor_state import (
    CursorSlot,
    CursorStateTable,
    KeyOfReference,
    key_of_reference,
    read_indexed,
    read_next,
    start,
)
from acas_posting.dal.status import (
    START_ACCESS_TYPE_RANGE,
    AccessType,
    AcasFileHandlerFatalError,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    log_cobol_stop,
    log_file_handler_record,
    mysql_1100_db_error,
    override_we_error_for_operation,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_posting import (
    WsPostingRecord,
    WsPostKey,
    ZonedDisplayInt,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "HANDLER_NAME",
    "BRIDGE_NAME",
    "TABLE_NAME",
    "ENTITY_FACADE",
    "RECORD_COPYBOOK",
    "FILE_DESCRIPTION_COPYBOOK",
    "MYSQL_VAR_DIRECTIVE",
    "MISSING_SQLSTATE_COPYBOOK_SITE",
    "WS_LOG_SYSTEM",
    "WS_LOG_FILE_NO_COBOL_PATH",
    "WS_LOG_FILE_NO_RDB_PATH",
    "WS_FILE_KEY_WIDTH",
    "WS_FILE_KEY_LITERALS",
    "SQL_ERR_FIELD_WIDTH",
    "SQL_MSG_FIELD_WIDTH",
    "SQL_STATE_FIELD_WIDTH",
    "DISPLAY_BLK_WIDTH",
    "GL901_MESSAGE",
    "GL903_MESSAGE",
    "MINIMUM_SCREEN_LINES",
    "HANDLER_PARAGRAPH_NUMBERS",
    "BRIDGE_PARAGRAPH_NUMBERS",
    "EDIT_FIELD_PICTURE",
    "EDIT_FIELD_WIDTH",
    "EDIT_FIELD_SIGN_POSITION",
    "EDIT_FIELD_INTEGER_END",
    "EDIT_FIELD_FRACTION_START",
    "EDIT_FIELD_SIGN_IS_NEVER_RENDERED",
    "GlPostingColumn",
    "COLUMNS",
    "COLUMNS_BY_NAME",
    "COLUMN_NAMES",
    "KEY_OF_REFERENCE",
    "TABLE_OF_KEYNAMES_LITERALS",
    "KEY_OF_REFERENCE_SLICE_IS_NOT_THE_POST_KEY",
    "PRIMARY_KEY_COLUMN",
    "HOST_VARIABLE_NAMES_ARE_HV_PREFIXED",
    "PRIMARY_KEY_IS_NEVER_LOADED",
    "WS_POSTING_RECORD_BYTES",
    "POSTING_RECORD_BYTES",
    "POSTING_RECORD_DECLARED_FIELDS",
    "RECORD_SIZE_GUARD_IS_UNREACHABLE",
    "STATEMENT_TERMINATORS_ARE_TRANSPORT_ONLY",
    "TdGlpostingRec",
    "CobolFlatFileStoreUnavailableError",
    "BridgeNotOpenError",
    "dispatch",
    "glposting_mt",
    "cancel_acas006",
    "cancel_glposting_mt",
    "aa_process_flat_file",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_reread",
    "aa050_process_read_indexed",
    "aa051_reread",
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
    "ba020_process_dal",
    "ba_rdbms_exit",
    "ca_process_logs",
    "ca_exit",
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
    "ba085_process_delete_all",
    "ba090_process_rewrite",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba999_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "mt_ca_process_logs",
    "mt_ca_exit",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


HANDLER_NAME: Final[str] = "acas006"

BRIDGE_NAME: Final[str] = "glpostingMT"

TABLE_NAME: Final[str] = "GLPOSTING-REC"

ENTITY_FACADE: Final[str] = "GL-Posting"

RECORD_COPYBOOK: Final[str] = "copybooks/wspost.cob"

FILE_DESCRIPTION_COPYBOOK: Final[str] = "copybooks/fdpost.cob"

MYSQL_VAR_DIRECTIVE: Final[tuple[str, ...]] = (
    "/MYSQL VAR\\",
    "      BASE=ACASDB",
    "      TABLE=GLPOSTING-REC,HV",
    "/MYSQL-END\\",
)

#: `copy "ACAS-SQLstate-error-list.cob".` [common/glpostingMT.cbl:L160] names a copybook
#: ABSENT from the entire checkout - anomaly N10, a second missing build input,
#: alongside the bridge's C interface object that AAP section 0.5.2 names and records as
#: having no build rule in the repository.
MISSING_SQLSTATE_COPYBOOK_SITE: Final[str] = "common/glpostingMT.cbl:L160"


WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.GL

#: ANOMALY N-log. `move 12 to WS-Log-File-No.` on the Cobol path
#: [common/acas006.cbl:L289] ...
WS_LOG_FILE_NO_COBOL_PATH: Final[int] = 12

#: ... and `move 22 to WS-Log-File-no.` the moment the RDB path is entered
#: [common/acas006.cbl:L590], with the field's capitalisation differing between the two
#: sites.
WS_LOG_FILE_NO_RDB_PATH: Final[int] = 22

#: `WS-File-Key pic x(64).` [copybooks/wsfnctn.cob:L52].
WS_FILE_KEY_WIDTH: Final[int] = 64

SQL_ERR_FIELD_WIDTH: Final[int] = 5

SQL_MSG_FIELD_WIDTH: Final[int] = 512

SQL_STATE_FIELD_WIDTH: Final[int] = 5

HANDLER_PARAGRAPH_NUMBERS: Final[Mapping[str, int]] = MappingProxyType(
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

BRIDGE_PARAGRAPH_NUMBERS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed": 5,
        "ba050-Process-Read-Indexed-Fetch": 6,
        "ba060-Process-Start": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba085-Process-Delete-ALL": 15,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
    }
)

#: Every literal the two programs move into `WS-File-Key`, at its own site.
WS_FILE_KEY_LITERALS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "handler-open": "OPEN GL POSTING file",
        "handler-close": "CLOSE GL POSTING file",
        "handler-eof": "EOF",
        "bridge-open": "OPEN GLPOSTING",
        "bridge-close": "CLOSE GLPOSTING",
        "bridge-eof": "EOF",
        "bridge-eof2": "EOF2",
        "bridge-eof3": "EOF3",
        "bridge-no-data": "No Data",
        "bridge-read-next-low-key": "00000",
        "bridge-delete-all": "Deleting back from ",
    }
)


# `WS-MYSQL-EDIT` - the numeric-rendering field, and ANOMALY N-EDIT.

#: `01 WS-MYSQL-EDIT PIC -Z(18)9.9(9).` [common/glpostingMT.cbl:L217]. Thirty character
#: positions: position 1 the sign: space when positive, ``-`` when negative 2 ..
EDIT_FIELD_PICTURE: Final[str] = "-Z(18)9.9(9)"
EDIT_FIELD_WIDTH: Final[int] = 30
EDIT_FIELD_SIGN_POSITION: Final[int] = 1
#: The integer field ends at position 20, so an ``n``-digit integer window starts at
#: ``21 - n``.
EDIT_FIELD_INTEGER_END: Final[int] = 20
#: The fractional digits always begin at position 22, which is why every money window is
#: ``(22:02)``.
EDIT_FIELD_FRACTION_START: Final[int] = 22

#: ANOMALY N-EDIT, recorded once here and cited again at
#: :func:`_edit_field_image` and :func:`_edit_window`. Every ``STRING FUNCTION TRIM
#: (WS-MYSQL-EDIT (s:l))`` in `bb200-Insert` and `bb300-Update` starts at
#: position 3 or later, so position 1 - the sign - is never part of any window.
#: A negative ``POST-AMOUNT`` or ``VAT-AMOUNT`` therefore reaches the column as
#: its ABSOLUTE VALUE. Same class as AAP section 0.6.7 entry 11: the sign is
#: lost at the bridge, before any SQL executes.
EDIT_FIELD_SIGN_IS_NEVER_RENDERED: Final[bool] = True


# The key of reference, and ANOMALY N-KOR.

TABLE_OF_KEYNAMES_LITERALS: Final[tuple[str, str, str]] = (
    "POST-KEY                      ",
    "00010010",
    "STR",
)

#: Read from :mod:`acas_posting.dal.cursor_state`, which owns the cursor contract,
#: rather than re-declared here. AAP section 0.1.1: "Indexed-file read semantics must be
#: emulated, not approximated ...
KEY_OF_REFERENCE: Final[KeyOfReference] = key_of_reference(TABLE_NAME)

#: ANOMALY N-KOR. Offset 0001 length 0010 means every ``WHERE`` the bridge builds slices
#: ``WS-Posting-Record (1:10)``.
KEY_OF_REFERENCE_SLICE_IS_NOT_THE_POST_KEY: Final[bool] = True

#: `PRIMARY KEY (`POST-RRN`)` [mysql/ACASDB.sql:L169] - the column that `bb000-HV-Load`
#: never loads. See anomaly N-RRN.
PRIMARY_KEY_COLUMN: Final[str] = "POST-RRN"


# Declared record lengths, and ANOMALY N-901-DEAD.


def _declared_bytes(dictionary_key: str) -> int:
    """Return the declared byte length of one elementary copybook field.

    ``WS-Posting-Record`` contains only zoned ``DISPLAY`` numerics and ``ALPHANUMERIC``
    items - :class:`WsPostingRecord` records the same fact from the record side, that
    "no COMP/COMP-3/binary item appears anywhere" - so a zoned numeric occupies one byte
    per declared digit and an alphanumeric item occupies its character length.

    Args:
        dictionary_key: The data-dictionary key of an elementary field.

    Returns:
        The field's declared length in bytes.

    Raises:
        ValueError: If the field is a group, or declares a storage class this record
            does not contain. Unreachable for ``wspost.cob``.
    """
    field_view = loader.get_entry(dictionary_key).copybook
    if field_view.is_group:
        raise ValueError(
            f"{dictionary_key} is a group item; its children carry the bytes"
        )
    if field_view.character_length is not None:
        return int(field_view.character_length)
    if field_view.digits is not None:
        return int(field_view.digits)
    raise ValueError(
        f"{dictionary_key} declares neither a character length nor a digit "
        f"count, so its byte length cannot be derived from the dictionary"
    )


def _ws_posting_record_bytes() -> int:
    """Sum the declared bytes of ``WS-Posting-Record`` [copybooks/wspost.cob].

    Reproduces ``function Length (WS-Posting-Record)`` [common/acas006.cbl:L595-L597].
    Derived from the dictionary rather than transcribed, per the AAP section 0.8.1
    directive that field metadata be read from the dictionary and never by eye.
    """
    total = 0
    for entry in loader.entries_for_copybook_record("WS-Posting-Record"):
        if entry.copybook.is_group:
            continue
        total += _declared_bytes(entry.key)
    return total


WS_POSTING_RECORD_BYTES: Final[int] = _ws_posting_record_bytes()

#: The field-description record's declared fields, transcribed from
#: [copybooks/fdpost.cob:L12-L28] as ``(name, bytes)``.
POSTING_RECORD_DECLARED_FIELDS: Final[tuple[tuple[str, int], ...]] = (
    ("Post-rrn", 5),
    ("Batch", 5),
    ("Post-Number", 5),
    ("Post-Code", 2),
    ("Post-Date", 8),
    ("Post-DR", 6),
    ("DR-PC", 2),
    ("Post-CR", 6),
    ("CR-PC", 2),
    ("Post-Amount", 10),
    ("Post-Legend", 32),
    ("Vat-AC", 6),
    ("Vat-PC", 2),
    ("Post-Vat-Side", 2),
    ("Vat-Amount", 10),
)

POSTING_RECORD_BYTES: Final[int] = sum(
    declared for _name, declared in POSTING_RECORD_DECLARED_FIELDS
)

#: ANOMALY N-901-DEAD.
RECORD_SIZE_GUARD_IS_UNREACHABLE: Final[bool] = (
    WS_POSTING_RECORD_BYTES >= POSTING_RECORD_BYTES
)


class CobolFlatFileStoreUnavailableError(AcasFileHandlerFatalError):
    """Raised where the Cobol flat-file branch would execute an ISAM verb.

    The migrated artifact has no ISAM store - AAP section 0.2.1.2 scopes the Python
    target to SQL against the frozen schema, and rule R-1 forbids reaching back into the
    COBOL runtime that provides the indexed organisation - so this is a documented non-
    reproduction, recorded in the module docstring.
    """

    def __init__(self, detail: str, *, operation: str = "", table: str = "") -> None:
        """Carry the explanation, and a status pair that claims nothing.

        ``FS-Reply`` is 99, the vocabulary's only general failure
        [common/glpostingMT.cbl:L131], and ``We-Error`` is left at zero BECAUSE THE
        FROZEN SOURCE WRITES NONE HERE.

        Args:
            detail: What could not be done, and what to configure instead.
            operation: The COBOL verb, for the base class message.
            table: The table involved, for the base class message.
        """
        super().__init__(
            FsReply.ERROR,
            WeError.SUCCESS,
            operation=operation,
            table=table,
        )
        self.detail = detail
        self.args = (detail,)

    def __str__(self) -> str:
        """The explanation, which is the only useful thing to print."""
        return self.detail


class BridgeNotOpenError(AcasFileHandlerFatalError):
    """Raised when a bridge verb other than ``Open`` runs with no connection.

    ``glpostingMT`` keeps its connection in ``Ws-Mysql-Cid``, set by ``MYSQL-1000-OPEN``
    [copybooks/mysql-procedures.cpy:L63-L86] and used by every later statement.
    """

    def __init__(self, detail: str, *, operation: str = "", table: str = "") -> None:
        """Carry the explanation, with ``FS-Reply`` 99 and no detail code.

        ``We-Error`` stays zero for the same reason as
        :class:`CobolFlatFileStoreUnavailableError`: the frozen source writes no code
        for a statement issued against a null connection identifier, and rule R-3
        forbids adding one.

        Args:
            detail: What was attempted, and what must happen first.
            operation: The COBOL verb, for the base class message.
            table: The table involved, for the base class message.
        """
        super().__init__(
            FsReply.ERROR,
            WeError.SUCCESS,
            operation=operation,
            table=table,
        )
        self.detail = detail
        self.args = (detail,)

    def __str__(self) -> str:
        """The explanation, which is the only useful thing to print."""
        return self.detail


def _edit_field_image(value: Decimal) -> str:
    """Build the thirty-character ``WS-MYSQL-EDIT`` image for ``value``.

    Reproduces ``MOVE HV-<field> TO WS-MYSQL-EDIT`` where ``01 WS-MYSQL-EDIT PIC
    -Z(18)9.9(9)`` [common/glpostingMT.cbl:L217].

    Args:
        value: The host variable's value, already stored into the host variable with
            COBOL ``MOVE`` semantics by :func:`_store_numeric_into_hv`.

    Returns:
        The thirty-character image, exactly as the COBOL field would hold it.
    """
    sign = "-" if value < 0 else " "
    magnitude = -value if value < 0 else value
    integer_part = int(magnitude)
    # Nine fractional digits, taken EXACTLY.
    fraction_digits = str(int((magnitude - integer_part).scaleb(9))).rjust(
        EDIT_FIELD_WIDTH - EDIT_FIELD_FRACTION_START + 1, "0"
    )
    integer_image = str(integer_part).rjust(
        EDIT_FIELD_INTEGER_END - EDIT_FIELD_SIGN_POSITION
    )
    return f"{sign}{integer_image}.{fraction_digits}"


def _edit_window(image: str, start: int, length: int) -> str:
    """Take ``WS-MYSQL-EDIT (start:length)`` and apply ``FUNCTION TRIM``.

    Args:
        image: The thirty-character edit-field image.
        start: The one-based starting position of the window.
        length: The window length in characters.

    Returns:
        The trimmed window text.
    """
    return image[start - 1 : start - 1 + length].strip()


def _as_exact_decimal(value: object, *, where: str) -> Decimal:
    """Coerce a caller value to :class:`~decimal.Decimal`, exactly.

    Rule R-2 is absolute.

    Args:
        value: An ``int``, a ``Decimal``, or a digit string.
        where: The host-variable name, for the error message.

    Returns:
        The value as an exact :class:`~decimal.Decimal`.

    Raises:
        BinaryFloatingPointError: If ``value`` is an inexact numeric type - anything
            other than ``int``, ``Decimal`` or a digit string.
        TypeError: If ``value`` is a boolean, which is an ``int`` subclass but never a
            posting amount.
    """
    if isinstance(value, bool):
        raise TypeError(f"{where}: a boolean is not a numeric host-variable value")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    raise BinaryFloatingPointError(
        f"{where}: {type(value).__name__} is not an exact numeric type; rule R-2 "
        f"admits only int, Decimal and digit strings into a host variable"
    )


def _store_numeric_into_hv(
    value: object,
    *,
    name: str,
    digits: int,
    scale: int,
    signed: bool,
) -> Decimal:
    """Reproduce ``MOVE <record field> TO <numeric host variable>``.

    1. **Low-order truncation.** A ``MOVE`` into a field with fewer fractional digits
    than the sender truncates toward zero; it does not round. AAP section 0.6.1 settles
    the direction.

    Args:
        value: The record field's value.
        name: The host-variable name, for diagnostics.
        digits: The host variable's total declared digits.
        scale: The host variable's declared fractional digits.
        signed: Whether the host variable's picture carries ``S``.

    Returns:
        The value as the host variable would hold it, scaled to ``scale``.
    """
    exact = _as_exact_decimal(value, where=name)
    # Rule 1: truncate toward zero to the receiving scale.
    truncated_units = int(exact.scaleb(scale))
    # Rule 2: discard digits that do not fit the receiving field.
    magnitude = abs(truncated_units) % (10**digits)
    if signed and truncated_units < 0:
        magnitude = -magnitude
    return Decimal(magnitude).scaleb(-scale)


def _store_alphanumeric_into_hv(value: object, *, name: str, length: int) -> str:
    """Reproduce ``MOVE <record field> TO <alphanumeric host variable>``.

    A COBOL alphanumeric ``MOVE`` is left-justified: the sender is truncated on the
    right when it is longer than the receiver and space-filled on the right when it is
    shorter.

    Args:
        value: The record field's value.
        name: The host-variable name, for diagnostics.
        length: The host variable's declared character length.

    Returns:
        Exactly ``length`` characters.

    Raises:
        TypeError: If ``value`` is not a string.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{name}: an alphanumeric host variable takes str, not "
            f"{type(value).__name__}"
        )
    return value[:length].ljust(length)


@dataclass(frozen=True, slots=True)
class GlPostingColumn:
    """One column of ``GLPOSTING-REC``, described entirely from the dictionary."""

    ordinal: int
    name: str
    dictionary_key: str
    citation: str
    #: ``loader.drift_for(dictionary_key).details`` - never re-derived here.
    drift_details: tuple[str, ...]
    sql_type: str
    is_primary_key: bool
    column_unsigned: bool
    column_comment: str | None
    cb_name: str
    cb_picture: str | None
    cb_usage: str
    cb_signed: bool
    cb_digits: int | None
    cb_scale: int | None
    cb_character_length: int | None
    cb_is_group: bool
    hv_name: str
    hv_picture: str
    hv_usage: str
    hv_signed: bool
    hv_digits: int | None
    hv_scale: int | None
    hv_character_length: int | None
    loaded_from_record: bool
    load_source: str | None
    unloaded_to_record: bool
    unload_source: str | None
    record_attribute: str
    python_storage: str

    @property
    def quoted_name(self) -> str:
        """The column name, backtick-quoted."""
        return quote_identifier(self.name)

    @property
    def is_alphanumeric(self) -> bool:
        """Whether the host variable is ``PIC X(n)`` rather than numeric."""
        return self.hv_character_length is not None

    @property
    def edit_integer_window(self) -> tuple[int, int]:
        """The ``WS-MYSQL-EDIT`` integer window as ``(start, length)``."""
        digits = self.hv_digits or 0
        scale = self.hv_scale or 0
        integer_digits = digits - scale
        return (EDIT_FIELD_INTEGER_END + 1 - integer_digits, integer_digits)

    @property
    def edit_fraction_window(self) -> tuple[int, int]:
        """The ``WS-MYSQL-EDIT`` fraction window as ``(start, length)``.

        Always starts at position 22, which is why both money fields render ``(22:02)``.
        A zero-scale column has a zero-length window and renders no decimal point at
        all.
        """
        return (EDIT_FIELD_FRACTION_START, self.hv_scale or 0)

    def store(self, value: object) -> Decimal | str:
        """Reproduce the ``MOVE`` of a record field into this host variable."""
        if self.is_alphanumeric:
            return _store_alphanumeric_into_hv(
                value, name=self.hv_name, length=int(self.hv_character_length or 0)
            )
        return _store_numeric_into_hv(
            value,
            name=self.hv_name,
            digits=int(self.hv_digits or 0),
            scale=int(self.hv_scale or 0),
            signed=self.hv_signed,
        )

    def store_into_record(self, hv_value: Decimal | str) -> Decimal | str:
        """Reproduce the ``MOVE`` of this host variable back into the record.

        This is the reverse direction of :meth:`store` and it is not symmetric, because
        the host variable is WIDER than the record field for every numeric column in
        this table except the two money fields.
        """
        if self.cb_character_length is not None:
            return _store_alphanumeric_into_hv(
                hv_value,
                name=self.cb_name,
                length=int(self.cb_character_length),
            )
        if self.cb_digits is None:
            raise ValueError(
                f"{self.cb_name} is a group item; bb100-UnloadHVs splits it "
                f"rather than moving it as one field"
            )
        return _store_numeric_into_hv(
            hv_value,
            name=self.cb_name,
            digits=int(self.cb_digits),
            scale=int(self.cb_scale or 0),
            signed=self.cb_signed,
        )

    def render(self, hv_value: Decimal | str) -> str:
        """Build the literal text the bridge would place in the statement.

        For an alphanumeric host variable this is ``FUNCTION TRIM (HV-x, TRAILING)``
        [common/glpostingMT.cbl:L1146-L1148 and siblings]: only trailing spaces go, so a
        leading space survives.
        """
        if isinstance(hv_value, str):
            return hv_value.rstrip(" ")
        image = _edit_field_image(hv_value)
        integer_start, integer_length = self.edit_integer_window
        integer_text = _edit_window(image, integer_start, integer_length)
        fraction_start, fraction_length = self.edit_fraction_window
        if fraction_length == 0:
            return integer_text
        fraction_text = _edit_window(image, fraction_start, fraction_length)
        return f"{integer_text}.{fraction_text}"

    def bind(self, hv_value: Decimal | str) -> Decimal | int | str:
        """The value to bind for this column, derived from :meth:`render`.

        The bound value is derived FROM the rendered text and not from the host
        variable, so every rendering anomaly - N-EDIT above all - reaches the column
        exactly as the COBOL would have sent it.
        """
        text = self.render(hv_value)
        if self.is_alphanumeric:
            return text
        if (self.hv_scale or 0) > 0:
            return Decimal(text)
        return int(text)


def _build_columns() -> tuple[GlPostingColumn, ...]:
    """Build :data:`COLUMNS` from the dictionary, in COLUMN-ORDINAL order.

    ``loader.entries_for_table`` returns the table's entries; they are sorted on the
    column ordinal so that the emitted column list matches the declared order of the
    frozen table [mysql/ACASDB.sql:L155-L168] and, with it, the order of the bridge's
    own ``INSERT`` [common/glpostingMT.cbl:L1120-L1287].
    """
    attribute_by_key = {
        key: attribute
        for attribute, key in loader.field_keys_for(WsPostingRecord()).items()
    }
    built: list[GlPostingColumn] = []
    for entry in sorted(
        loader.entries_for_table(TABLE_NAME), key=lambda item: item.column.ordinal
    ):
        host_variable = entry.bridge_host_variable
        column = entry.column
        copybook_field = entry.copybook
        built.append(
            GlPostingColumn(
                ordinal=int(column.ordinal),
                name=column.name,
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                drift_details=tuple(loader.drift_for(entry.key).details),
                sql_type=column.sql_type,
                is_primary_key=bool(column.is_primary_key),
                column_unsigned=bool(column.unsigned),
                column_comment=column.comment,
                cb_name=copybook_field.name,
                cb_picture=copybook_field.picture,
                cb_usage=copybook_field.usage.value,
                cb_signed=bool(copybook_field.signed),
                cb_digits=copybook_field.digits,
                cb_scale=copybook_field.scale,
                cb_character_length=copybook_field.character_length,
                cb_is_group=bool(copybook_field.is_group),
                hv_name=host_variable.name,
                hv_picture=str(host_variable.picture),
                hv_usage=host_variable.usage.value,
                hv_signed=bool(host_variable.signed),
                hv_digits=host_variable.digits,
                hv_scale=host_variable.scale,
                hv_character_length=host_variable.character_length,
                loaded_from_record=bool(host_variable.loaded_from_record),
                load_source=host_variable.load_source,
                unloaded_to_record=bool(host_variable.unloaded_to_record),
                unload_source=host_variable.unload_source,
                record_attribute=attribute_by_key[entry.key],
                python_storage=entry.cobol_python_storage.value,
            )
        )
    return tuple(built)


COLUMNS: Final[tuple[GlPostingColumn, ...]] = _build_columns()

COLUMNS_BY_NAME: Final[Mapping[str, GlPostingColumn]] = MappingProxyType(
    {column.name: column for column in COLUMNS}
)

COLUMN_NAMES: Final[tuple[str, ...]] = tuple(column.name for column in COLUMNS)

#: ANOMALY N-RRN, asserted from the dictionary rather than assumed.
PRIMARY_KEY_IS_NEVER_LOADED: Final[bool] = not COLUMNS_BY_NAME[
    PRIMARY_KEY_COLUMN
].loaded_from_record

#: The host-variable naming invariant, asserted from the dictionary rather than
#: transcribed.
HOST_VARIABLE_NAMES_ARE_HV_PREFIXED: Final[bool] = all(
    column.hv_name == "HV-" + column.name for column in COLUMNS
)


def _initialised_hv_value(column_name: str) -> Decimal | str:
    """The value ``initialize TD-GLPOSTING-REC`` leaves in one host variable.

    COBOL ``INITIALIZE`` sets numeric items to zero and alphanumeric items to spaces.
    This is the statement that makes every column of the table declarable ``NOT NULL``.

    Args:
        column_name: The column whose host variable is being initialised.

    Returns:
        Zero at the host variable's declared scale, or its width in spaces.
    """
    column = COLUMNS_BY_NAME[column_name]
    if column.is_alphanumeric:
        return " " * int(column.hv_character_length or 0)
    return Decimal(0).scaleb(-(column.hv_scale or 0))


@dataclass(slots=True)
class TdGlpostingRec:
    """``01 TD-GLPOSTING-REC.`` - the host-variable group, VERBATIM.

    The group is declared by the JC preSQL directive [common/glpostingMT.scb:L273-L276],
    reproduced in the C-interface pointer to the group and has no Python counterpart:
    the driver binds values directly, so there is no address to pass.
    """

    #: `05 HV-POST-RRN PIC 9(08) COMP.` [common/glpostingMT.cbl:L282]. ANOMALY N-RRN:
    #: never loaded [absent from :L1053-L1066], never unloaded [absent from
    #: :L1083-L1097], yet the table's ``PRIMARY KEY`` [mysql/ACASDB.sql:L169].
    hv_post_rrn: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-RRN")
    )
    hv_post_key: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-KEY")
    )
    hv_post_code: str = field(
        default_factory=lambda: _initialised_hv_value("POST-CODE")
    )
    hv_post_dat: str = field(
        default_factory=lambda: _initialised_hv_value("POST-DAT")
    )
    hv_post_dr: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-DR")
    )
    hv_dr_pc: Decimal = field(
        default_factory=lambda: _initialised_hv_value("DR-PC")
    )
    hv_post_cr: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-CR")
    )
    hv_cr_pc: Decimal = field(
        default_factory=lambda: _initialised_hv_value("CR-PC")
    )
    #: [common/glpostingMT.cbl:L290]. Signed here, signed in the copybook and signed in
    #: the column - yet ANOMALY N-EDIT drops the sign on the way out.
    hv_post_amount: Decimal = field(
        default_factory=lambda: _initialised_hv_value("POST-AMOUNT")
    )
    hv_post_legend: str = field(
        default_factory=lambda: _initialised_hv_value("POST-LEGEND")
    )
    hv_vat_ac: Decimal = field(
        default_factory=lambda: _initialised_hv_value("VAT-AC")
    )
    hv_vat_pc: Decimal = field(
        default_factory=lambda: _initialised_hv_value("VAT-PC")
    )
    hv_post_vat_side: str = field(
        default_factory=lambda: _initialised_hv_value("POST-VAT-SIDE")
    )
    hv_vat_amount: Decimal = field(
        default_factory=lambda: _initialised_hv_value("VAT-AMOUNT")
    )

    #: Column name to attribute name, so that the statement builders can walk
    #: :data:`COLUMNS` in ordinal order and reach the matching host variable without a
    #: second hand-written table.
    ATTRIBUTE_BY_COLUMN: ClassVar[Mapping[str, str]] = MappingProxyType(
        {
            "POST-RRN": "hv_post_rrn",
            "POST-KEY": "hv_post_key",
            "POST-CODE": "hv_post_code",
            "POST-DAT": "hv_post_dat",
            "POST-DR": "hv_post_dr",
            "DR-PC": "hv_dr_pc",
            "POST-CR": "hv_post_cr",
            "CR-PC": "hv_cr_pc",
            "POST-AMOUNT": "hv_post_amount",
            "POST-LEGEND": "hv_post_legend",
            "VAT-AC": "hv_vat_ac",
            "VAT-PC": "hv_vat_pc",
            "POST-VAT-SIDE": "hv_post_vat_side",
            "VAT-AMOUNT": "hv_vat_amount",
        }
    )

    def value_for(self, column: GlPostingColumn) -> Decimal | str:
        """The host variable corresponding to ``column``."""
        return getattr(self, self.ATTRIBUTE_BY_COLUMN[column.name])

    def set_for(self, column: GlPostingColumn, value: Decimal | str) -> None:
        """Store ``value`` into the host variable corresponding to ``column``."""
        setattr(self, self.ATTRIBUTE_BY_COLUMN[column.name], value)


def _join_post_key(key: WsPostKey) -> Decimal:
    """Reproduce the raw group-to-binary ``MOVE`` into ``HV-POST-KEY``.

    ``WS-Post-Key`` is a group of two ``pic 9(5)`` items, ``Batch`` and ``Post-Number``
    [copybooks/wspost.cob:L14-L16]. Because the sending operand is a GROUP, COBOL
    performs an alphanumeric byte move into the eight-byte COMP receiver rather than
    converting the ten displayed digits numerically. The bridge's 18-digit edit then
    drops the leading digit of that raw integer before SQL, which is why
    ``0000100001`` is stored as ``472328296244457520`` by the compiled oracle.

    Args:
        key: The record's ``ws_post_key`` group.

    Returns:
        The exact integer represented by the first eight group bytes, as a
        :class:`~decimal.Decimal`; the bridge renderer applies the declared 18-digit
        host-variable edit.
    """
    #  A CARRIED IMAGE IS THE GROUP'S ACTUAL BYTES AND OUTRANKS THE DIGITS. `move
    # WS-Post-Key to HV-POST-KEY` moves the group's STORAGE, so when a fetched row put
    # bytes in the group that its picture cannot produce - which every fetched row does,
    # ANOMALY N-KEY - re-writing that row must move those same bytes back rather than the
    # decimal re-encode of their tolerant reading. Measured: the round trip is exact.
    group_image = _post_key_group_image(key)
    return Decimal(int.from_bytes(group_image[:8], byteorder="big", signed=True))


def _post_key_group_image(key: WsPostKey) -> bytes:
    """The ten bytes ``WS-Post-Key`` holds, measured ones before derived ones.

    Args:
        key: The record's ``ws_post_key`` group.

    Returns:
        Ten bytes: each item's carried storage image when a fetch supplied one, and
            otherwise the five zoned digits the item's value implies.
    """
    halves: list[bytes] = []
    for value in (key.batch, key.post_number):
        carried = getattr(value, "zoned_image", None)
        if isinstance(carried, bytes) and len(carried) == _POST_KEY_ITEM_BYTES:
            halves.append(carried)
            continue
        halves.append(
            f"{abs(int(value)) % 100000:0{_POST_KEY_ITEM_BYTES}d}".encode("latin-1")
        )
    return b"".join(halves)


#: The two spaces the group receiver is padded with, MEASURED.
#:
#: ``WS-Post-Key`` is ten bytes and ``HV-POST-KEY`` is an eight-byte ``COMP`` item, so
#: the alphanumeric move into the group leaves two bytes over. A probe read all ten
#: after the move and the last two were ``0x20`` - space, the alphanumeric pad - not
#: zero, not left unchanged, and not the low-order bytes of anything.
_POST_KEY_GROUP_PAD: Final[bytes] = b"\x20\x20"

#: The eight bytes an eight-byte ``COMP`` item occupies.
_POST_KEY_HOST_BYTES: Final[int] = 8

#: The five bytes each ``pic 9(5)`` DISPLAY half of the group occupies
#: [copybooks/wspost.cob:L15-L16].
_POST_KEY_ITEM_BYTES: Final[int] = 5


def _split_post_key(
    hv_post_key: Decimal,
) -> tuple[ZonedDisplayInt, ZonedDisplayInt]:
    """Reproduce the raw binary-to-group ``MOVE`` out of ``HV-POST-KEY``.

    ``move HV-POST-KEY to WS-Post-Key.`` [common/glpostingMT.cbl:L1085]. The receiver is
    a GROUP [copybooks/wspost.cob:L14-L16], so COBOL performs an ALPHANUMERIC move: the
    sending ``PIC 9(18) COMP`` item's eight storage bytes are copied into the group's
    first eight bytes and the remaining two are space-filled. Nothing is converted
    numerically on the way, which is what makes this the mirror of
    :func:`_join_post_key` rather than its inverse.

    MEASURED, AND IT IS NEITHER OF THE TWO READINGS THE MIGRATION CONSIDERED. The
    open question was whether the group takes the FIRST ten decimal digits of the host
    variable or the LAST ten. It takes neither: it takes eight BYTES. A probe declared
    both operands exactly as the frozen sources declare them, set the host variable to
    ``472328296244457520`` - the value the compiled bridge stores for a
    ``0000100001`` key, so the value a fetch really returns - performed the frozen move
    and read all ten group bytes with ``FUNCTION ORD``:

    ==========================  ==========================================
    group bytes after the move  ``06 8E 0C 15 3B 04 30 30 20 20``
    ``Batch``                   ``0x06 8E 0C 15 3B`` - **NOT NUMERIC**
    ``Post-Number``             ``0x04 30 30 20 20`` - **NOT NUMERIC**
    first ten decimal digits    ``4723282962`` - does not match
    last ten decimal digits     ``6244457520`` - does not match
    ==========================  ==========================================

    The previous implementation took the last ten decimal digits and split them, giving
    a batch of ``62444`` - a perfectly legitimate five-digit batch number, which is
    precisely why it was wrong in a way no green scenario would have shown. The compiled
    program produces bytes that cannot be a batch number at all, so the guard
    ``if batch not = WS-Batch-Nos go to loop`` [general/gl070.cbl:L492-L493] discards
    every posting; a reproduction that yields ``62444`` would MATCH on a run that seeded
    batch 62444 and post where the frozen system posts nothing. That is ANOMALY N-KEY,
    and this function is where it is reproduced rather than repaired (R-4).

    WHY THE NUMERIC VALUE IS COMPUTED BY LOW NIBBLE. The record models these two fields
    as ``int`` because the copybook declares them ``pic 9(5)`` DISPLAY, so the bytes
    have to be read as COBOL reads them. COBOL's zoned read is tolerant: the digit of
    each byte is its LOW NIBBLE, accumulated base ten, with no validity check. Applied
    to ``Batch`` that gives ``6, 14, 12, 5, 11`` and therefore ``75261`` - and the
    compiled program agrees where that reading is the one it uses: ``if batch = 75261``,
    against a numeric LITERAL, is EQUAL in the compiled probe, while ``= 1``,
    ``= 62444`` and ``= ZERO`` are all false. No check is added and no error is raised
    (R-3).

    AND WHY THE VALUE ALONE IS NOT ENOUGH. Re-measured against the compiled oracle
    because a QA arbitration found the migration deleting rows the compiled ``gl080``
    leaves alone: a relation between ``Batch`` and a SAME-PICTURE FIELD is not the
    numeric reading at all but a comparison of the two items' BYTES, so
    ``if batch not = WS-Batch-Nos`` [general/gl080.cbl:L617] is true for EVERY batch
    number - a sweep of the whole ``pic 9(5)`` domain inside the probe matched none of
    ``0..99999``. The two readings cannot both live in one ``int``, so the bytes travel
    with the value in a ``ZonedDisplayInt`` and
    ``arithmetic.compare_zoned_display_fields`` uses them at the FOUR frozen gates a
    bridge-unloaded key reaches: ``gl080``'s deletion pass and archive pass,
    ``gl070``'s phase-2 loop and ``gl051``'s proof-total gate.
    Recorded as ``Q-NKEY-CMP`` in ``docs/migration/ambiguity-resolutions.md``.

    The rule is stated here rather than imported because
    ``acas_posting.cobol`` is outside this module's dependency set (section 0.4.3);
    ``tests/arithmetic/test_comp_binary.py`` asserts that
    this function agrees with ``acas_posting.cobol.usage.decode`` so the two cannot
    drift apart.

    Args:
        hv_post_key: The host variable a fetch has just populated, carrying the column's
            eighteen-digit value.

    Returns:
        The ``Batch`` and ``Post-Number`` values the group holds after the move, read
        with COBOL's own tolerant zoned semantics, each carrying the five storage bytes
        it was read out of so that a field-to-field relation can compare the storage the
        compiled program compares.
    """
    # The COMP item's storage image. `signed=True` mirrors `_join_post_key`, which built
    # the same eight bytes with the same signedness, so a load and an unload of one
    # in-memory value round-trip exactly - measured.
    stored = int(hv_post_key)
    image = stored.to_bytes(
        _POST_KEY_HOST_BYTES, byteorder="big", signed=stored < 0
    )
    group_image = image + _POST_KEY_GROUP_PAD

    def zoned(chunk: bytes) -> ZonedDisplayInt:
        """Read one ``pic 9(5)`` DISPLAY field, tolerantly, as COBOL does.

        The bytes are kept beside the value rather than discarded: they are what a
        field-to-field relation compares, and they cannot be recovered from the value.
        """
        magnitude = 0
        for byte in chunk:
            magnitude = magnitude * 10 + (byte & 0x0F)
        return ZonedDisplayInt(magnitude, zoned_image=chunk)

    return (
        zoned(group_image[:_POST_KEY_ITEM_BYTES]),
        zoned(group_image[_POST_KEY_ITEM_BYTES : 2 * _POST_KEY_ITEM_BYTES]),
    )


def bb000_hv_load(posting: WsPostingRecord) -> TdGlpostingRec:
    """``bb000-HV-Load Section.`` [common/glpostingMT.cbl:L1045].

    Four facts about that paragraph, all reproduced below.

    Args:
        posting: The record the handler was passed.

    Returns:
        A freshly initialised host-variable group with the thirteen loaded values in it.
    """
    host_variables = TdGlpostingRec()

    # The moves below are in the SOURCE's order, which is NOT the column order. HV-POST-
    # RRN is deliberately absent - ANOMALY N-RRN [common/glpostingMT.cbl:L282 declared,
    # :L1053-L1066 never loaded].

    host_variables.hv_post_key = _join_post_key(posting.ws_post_key)
    host_variables.hv_post_code = COLUMNS_BY_NAME["POST-CODE"].store(
        posting.post_code
    )
    host_variables.hv_post_dat = COLUMNS_BY_NAME["POST-DAT"].store(posting.post_date)
    host_variables.hv_post_dr = COLUMNS_BY_NAME["POST-DR"].store(posting.post_dr)
    # L1058  move Post-CR to HV-POST-CR.   <-- ANOMALY N-loadorder: BEFORE DR-PC
    host_variables.hv_post_cr = COLUMNS_BY_NAME["POST-CR"].store(posting.post_cr)
    host_variables.hv_dr_pc = COLUMNS_BY_NAME["DR-PC"].store(posting.dr_pc)
    # L1060  move CR-PC to HV-CR-PC        <-- ANOMALY N17: no terminating period
    host_variables.hv_cr_pc = COLUMNS_BY_NAME["CR-PC"].store(posting.cr_pc)
    host_variables.hv_post_amount = COLUMNS_BY_NAME["POST-AMOUNT"].store(
        posting.post_amount
    )
    host_variables.hv_post_legend = COLUMNS_BY_NAME["POST-LEGEND"].store(
        posting.post_legend
    )
    host_variables.hv_vat_ac = COLUMNS_BY_NAME["VAT-AC"].store(posting.vat_ac)
    host_variables.hv_vat_pc = COLUMNS_BY_NAME["VAT-PC"].store(posting.vat_pc)
    host_variables.hv_post_vat_side = COLUMNS_BY_NAME["POST-VAT-SIDE"].store(
        posting.post_vat_side
    )
    host_variables.hv_vat_amount = COLUMNS_BY_NAME["VAT-AMOUNT"].store(
        posting.vat_amount
    )
    return host_variables


def bb100_unload_hvs(
    host_variables: TdGlpostingRec, posting: WsPostingRecord
) -> None:
    """``bb100-UnloadHVs Section.`` [common/glpostingMT.cbl:L1074].

    ANOMALY N-UNLOAD: there are only THIRTEEN moves. ``HV-POST-RRN`` is not unloaded
    either, so ``WS-Post-rrn`` keeps the zero that ``initialize WS-Posting-Record``
    [:L1083] put there, whatever the row's ``POST-RRN`` held.

    Args:
        host_variables: The group a fetch has just populated.
        posting: The record to unload into. MUTATED IN PLACE, exactly as the COBOL
            linkage mutates the caller's record.
    """
    # `initialize WS-Posting-Record.` [common/glpostingMT.cbl:L1083].
    initialised = WsPostingRecord()
    posting.ws_post_rrn = initialised.ws_post_rrn
    posting.ws_post_key.batch = initialised.ws_post_key.batch
    posting.ws_post_key.post_number = initialised.ws_post_key.post_number
    posting.post_code = initialised.post_code
    posting.post_date = initialised.post_date
    posting.post_dr = initialised.post_dr
    posting.dr_pc = initialised.dr_pc
    posting.post_cr = initialised.post_cr
    posting.cr_pc = initialised.cr_pc
    posting.post_amount = initialised.post_amount
    posting.post_legend = initialised.post_legend
    posting.vat_ac = initialised.vat_ac
    posting.vat_pc = initialised.vat_pc
    posting.post_vat_side = initialised.post_vat_side
    posting.vat_amount = initialised.vat_amount

    # ANOMALY N-UNLOAD: no `move HV-POST-RRN to WS-Post-rrn` exists
    # [common/glpostingMT.cbl:L1083-L1097], so ws_post_rrn keeps the zero above.

    batch, post_number = _split_post_key(host_variables.hv_post_key)
    posting.ws_post_key.batch = batch
    posting.ws_post_key.post_number = post_number
    posting.post_code = _unloaded(host_variables, "POST-CODE")
    posting.post_date = _unloaded(host_variables, "POST-DAT")
    posting.post_dr = _unloaded(host_variables, "POST-DR")
    posting.post_cr = _unloaded(host_variables, "POST-CR")
    posting.dr_pc = _unloaded(host_variables, "DR-PC")
    posting.cr_pc = _unloaded(host_variables, "CR-PC")
    posting.post_amount = _unloaded(host_variables, "POST-AMOUNT")
    posting.post_legend = _unloaded(host_variables, "POST-LEGEND")
    posting.vat_ac = _unloaded(host_variables, "VAT-AC")
    posting.vat_pc = _unloaded(host_variables, "VAT-PC")
    posting.post_vat_side = _unloaded(host_variables, "POST-VAT-SIDE")
    posting.vat_amount = _unloaded(host_variables, "VAT-AMOUNT")


def _unloaded(host_variables: TdGlpostingRec, column_name: str) -> Decimal | int | str:
    """One ``move <host variable> to <record field>`` of ``bb100-UnloadHVs``.

    Applies the receiving field's own ``MOVE`` semantics through
    :meth:`GlPostingColumn.store_into_record` - which truncates the high-order digits of
    anything wider than the record declares - and then coerces to the Python storage
    class the dictionary names for the record side, so that an ``int`` field receives an
    ``int`` and a money field a :class:`~decimal.Decimal`.
    """
    column = COLUMNS_BY_NAME[column_name]
    stored = column.store_into_record(host_variables.value_for(column))
    if column.python_storage == "INT":
        return int(stored)
    return stored


# `WS-Posting-Record (K:L)` - the record image, and ANOMALY N-KOR.

#: The record's elementary fields in declaration order, as ``(dictionary key, attribute
#: path)``. Built from the dictionary so the layout is derived rather than transcribed.
_RECORD_IMAGE_LAYOUT: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("GLPOSTING-REC.POST-RRN", ("ws_post_rrn",)),
    ("WS-Posting-Record.Batch", ("ws_post_key", "batch")),
    ("WS-Posting-Record.Post-Number", ("ws_post_key", "post_number")),
    ("GLPOSTING-REC.POST-CODE", ("post_code",)),
    ("GLPOSTING-REC.POST-DAT", ("post_date",)),
    ("GLPOSTING-REC.POST-DR", ("post_dr",)),
    ("GLPOSTING-REC.DR-PC", ("dr_pc",)),
    ("GLPOSTING-REC.POST-CR", ("post_cr",)),
    ("GLPOSTING-REC.CR-PC", ("cr_pc",)),
    ("GLPOSTING-REC.POST-AMOUNT", ("post_amount",)),
    ("GLPOSTING-REC.POST-LEGEND", ("post_legend",)),
    ("GLPOSTING-REC.VAT-AC", ("vat_ac",)),
    ("GLPOSTING-REC.VAT-PC", ("vat_pc",)),
    ("GLPOSTING-REC.POST-VAT-SIDE", ("post_vat_side",)),
    ("GLPOSTING-REC.VAT-AMOUNT", ("vat_amount",)),
)


def _ws_posting_record_image(posting: WsPostingRecord) -> str:
    """Build the fixed-width character image of ``WS-Posting-Record``.

    Needed because the bridge addresses the record by BYTE OFFSET, not by field: every
    ``WHERE`` it builds interpolates ``WS-Posting-Record (K:L)`` with ``K`` and ``L``
    taken from the key table [common/glpostingMT.cbl:L606, :L734.

    Args:
        posting: The record to render.

    Returns:
        The 103-character image [see :data:`WS_POSTING_RECORD_BYTES`].
    """
    pieces: list[str] = []
    for dictionary_key, attribute_path in _RECORD_IMAGE_LAYOUT:
        field_view = loader.get_entry(dictionary_key).copybook
        value: object = posting
        for attribute in attribute_path:
            value = getattr(value, attribute)
        if field_view.character_length is not None:
            width = int(field_view.character_length)
            pieces.append(str(value)[:width].ljust(width))
            continue
        digits = int(field_view.digits or 0)
        scale = int(field_view.scale or 0)
        units = abs(int(_as_exact_decimal(value, where=field_view.name).scaleb(scale)))
        pieces.append(f"{units % (10**digits):0{digits}d}")
    return "".join(pieces)


def _key_of_reference_value(posting: WsPostingRecord) -> str:
    """``WS-Posting-Record (K:L)`` - the value every keyed statement compares.

    ANOMALY N-KOR, reproduced here and nowhere else so that all five keyed statements
    inherit it from one place.

    Args:
        posting: The record the caller passed.

    Returns:
        The ten-character key text, leading zeros intact.
    """
    return KEY_OF_REFERENCE.key_from_record(_ws_posting_record_image(posting))


def _where_equal_to(posting: WsPostingRecord) -> tuple[str, tuple[object, ...]]:
    r"""``\`POST-KEY\`="<key>"`` - the equality predicate, four sites share it.

    Reproduces the identical ``string`` block at read-indexed
    [common/glpostingMT.cbl:L602-L611], delete [:L837-L846] and rewrite [:L977-L985].
    ``KeyName (KOR-x1) delimited by space`` drops the key name's trailing spaces, giving
    ``POST-KEY``.

    Returns:
        The predicate text with one placeholder, and the parameters to bind.
    """
    return (
        f"{quote_identifier(KEY_OF_REFERENCE.name)}=%s",
        (_key_of_reference_value(posting),),
    )


def _where_less_than(posting: WsPostingRecord) -> tuple[str, tuple[object, ...]]:
    r"""``\`POST-KEY\`<"<key>"`` - the ``Delete-All`` predicate.

    Reproduces [common/glpostingMT.cbl:L915-L923], the ONE site that uses ``<`` rather
    than ``=``: ``'<"'`` at :L918 where the other four write ``'="'``.
    """
    return (
        f"{quote_identifier(KEY_OF_REFERENCE.name)}<%s",
        (_key_of_reference_value(posting),),
    )


#: `STRING ";" ... STRING X"00"` [common/glpostingMT.cbl:L1283-L1286] terminate the
#: command for the C interface.
STATEMENT_TERMINATORS_ARE_TRANSPORT_ONLY: Final[bool] = True


def _column_assignments() -> tuple[str, ...]:
    r"""``\`<column>\`=%s`` for all fourteen columns, in ordinal order.

    The bridge emits ``'`POST-RRN`="'`` then the rendered value then ``'"'`` then ``',
    '`` [common/glpostingMT.cbl:L1120-L1130], repeating for each column in the frozen
    table's declared order [mysql/ACASDB.sql:L155-L168]. ``POST-RRN`` is FIRST [:L1120],
    which is why anomaly N-RRN reaches the column at all.
    """
    return tuple(f"{column.quoted_name}=%s" for column in COLUMNS)


def _bound_values(host_variables: TdGlpostingRec) -> tuple[object, ...]:
    """The fourteen bound values, in the same ordinal order.

    Every column is supplied, ``POST-RRN`` included, because all fourteen are ``NOT
    NULL`` [mysql/ACASDB.sql:L155-L168] and ``initialize TD-GLPOSTING-REC``
    [common/glpostingMT.cbl:L1053] guarantees a zero or a space rather than a ``NULL``.
    AAP section 0.6.2.
    """
    return tuple(
        column.bind(host_variables.value_for(column)) for column in COLUMNS
    )


def _literal_command(prefix: str, host_variables: TdGlpostingRec) -> str:
    """The statement text the bridge would build, for the log only.

    Reproduced so that the rendered values - and with them anomaly N-EDIT - are visible
    in the diagnostic record, matching ``move WS-Where (1:J) to WS-Log-Where. *> For
    test logging`` [common/glpostingMT.cbl:L612, :L848, :L929, :L986]. It is never
    executed.
    """
    assignments = ", ".join(
        f'{column.quoted_name}="{column.render(host_variables.value_for(column))}"'
        for column in COLUMNS
    )
    return f"{prefix}{assignments}"


def bb200_insert(
    connection: object, host_variables: TdGlpostingRec
) -> int:
    r"""``bb200-Insert Section.`` [common/glpostingMT.cbl:L1105].

    Reproduces the ``/MYSQL INSERT\`` block [common/glpostingMT.cbl:L1108-L1289]:
    ``INSERT INTO `GLPOSTING-REC` SET `` [:L1115-L1118] followed by all fourteen columns
    in the frozen table's ordinal order, each as ``\`<column>\`="<value>"`` separated by
    ``', '`` [:L1120-L1282], then ``";"`` and ``X"00"``.

    Args:
        connection: The open connection from :func:`ba020_process_open`.
        host_variables: The group :func:`bb000_hv_load` populated.

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the number of rows the statement affected.
    """
    statement = (
        f"INSERT INTO {quote_identifier(TABLE_NAME)} SET "
        f"{', '.join(_column_assignments())}"
    )
    #  THE STATEMENT IS NOT LOGGED, AND NEITHER IS THE LITERAL FORM OF IT.
    #  `_literal_command` renders the row exactly as the bridge's `string` builds
    #  it - every column of `GLPOSTING-REC` with its host-variable VALUE, which for
    #  this table means the batch number, the posting number, both account numbers,
    #  the amount and the VAT (CWE-532). `sanitise_for_log` escaped its control
    #  characters and bounded its length; it never removed a single value, because
    #  there is no rule that could tell a posted amount from a column name. A
    #  failed INSERT is reported once, with typed fields, by `dal/status.py`'s
    #  `mysql_1100_db_error`. `_literal_command` itself is retained: the bridge
    #  builds that text and stores its prefix in `SQL-Err`, which the duplicate-key
    #  test reads [copybooks/mysql-procedures.cpy:L99], so it is load-bearing for
    #  STATUS - just not for logging.
    parameters = _bound_values(host_variables)
    with execute_statement(connection, statement, parameters) as cursor:
        return int(cursor.rowcount)


def bb300_update(
    connection: object,
    host_variables: TdGlpostingRec,
    where_clause: str,
    where_parameters: Sequence[object],
) -> int:
    r"""``bb300-Update Section.`` [common/glpostingMT.cbl:L1294].

    Reproduces the ``/MYSQL UPDATE\`` block [common/glpostingMT.cbl:L1297-L1482].

    Args:
        connection: The open connection from :func:`ba020_process_open`.
        host_variables: The group :func:`bb000_hv_load` populated.
        where_clause: The predicate text, identifiers already quoted.
        where_parameters: The predicate's bound values.

    Returns:
        ``WS-MYSQL-COUNT-ROWS`` - the number of rows the statement affected.
    """
    statement = (
        f"UPDATE {quote_identifier(TABLE_NAME)} SET "
        f"{', '.join(_column_assignments())} WHERE {where_clause}"
    )
    #  NEITHER THE STATEMENT NOR THE `WHERE` CLAUSE IS LOGGED - see the note in
    #  `bb200_insert` above. The clause is worse than the SET list here: it is the
    #  key of reference with its value, so it names the exact posting row being
    #  rewritten (CWE-532). Both are still BUILT, because the bridge builds them and
    #  their prefixes reach `SQL-Err`; they simply do not reach a log record.
    parameters = (*_bound_values(host_variables), *where_parameters)
    with execute_statement(connection, statement, parameters) as cursor:
        return int(cursor.rowcount)


@dataclass(slots=True)
class _BridgeLink:
    """The bridge's own connection handle, the ``Ws-Mysql-Cid`` analogue.

    ``MYSQL-1000-OPEN`` stores the connection identifier in working storage
    [copybooks/mysql-procedures.cpy:L63-L86] and every later statement uses it;
    ``MYSQL-1980-CLOSE`` [:L264-L265] releases it.
    """

    connection: object | None = None
    #: `ws-env-lines` / `ws-lines` [common/glpostingMT.cbl:L335-L340]. Screen geometry,
    #: kept because the paragraph that computes it is in scope.
    ws_lines: int = 24


#: The bridge's `01 DAL-Data.` [common/glpostingMT.scb:L247-L251].
_BRIDGE_CURSORS: Final[CursorStateTable] = CursorStateTable()

#: `Ws-Mysql-Cid` [copybooks/mysql-procedures.cpy]. One slot, no pool (R-3).
_LINK: Final[_BridgeLink] = _BridgeLink()

#: `accept ws-env-lines from lines.` with the floor of 24
#: [common/glpostingMT.cbl:L335-L340]. The terminal is not consulted.
MINIMUM_SCREEN_LINES: Final[int] = 24


def cancel_glposting_mt() -> None:
    """Discard the bridge's working storage - the COBOL ``CANCEL`` equivalent.

    A COBOL ``CALL`` leaves the called program's working storage intact between calls;
    ``CANCEL "glpostingMT"`` is what resets it.
    """
    _LINK.connection = None
    _LINK.ws_lines = MINIMUM_SCREEN_LINES
    _BRIDGE_CURSORS.reset(TABLE_NAME)


def _states(states: CursorStateTable | None) -> CursorStateTable:
    """The cursor table to use: the caller's when given, the bridge's otherwise."""
    return states if states is not None else _BRIDGE_CURSORS


def _write_file_key(file_access: FileAccess, text: str) -> None:
    """``move <literal> to WS-File-Key`` - truncated to the declared width.

    ``WS-File-Key pic x(64)`` [copybooks/wsfnctn.cob:L52], and a COBOL ``MOVE`` into a
    shorter alphanumeric receiving field truncates on the right. The truncation is
    reproduced.
    """
    file_access.logging_data.ws_file_key = text[:WS_FILE_KEY_WIDTH]


def _driver_error_status(
    error: BaseException, *, command: str, we_error: int = WeError.SUCCESS
) -> DbErrorStatus:
    """Turn a driver exception into the status ``Mysql-1100-Db-Error`` produces.

    The three ``call "MySQL_errno"`` / ``"MySQL_sqlstate"`` / ``"MySQL_error"``
    sequences the bridge writes after a failed command
    [common/glpostingMT.cbl:L811-L817, :L867-L873, :L994-L1000] read the fields this
    helper extracts, and :func:`acas_posting.dal.status.mysql_1100_db_error` owns the
    mapping from them to a status pair - including the driver-level duplicate-key short
    circuit [copybooks/mysql-procedures.cpy:L99-L105], which is anomaly N-DUPKEY-TWO-
    PLACES.

    Args:
        error: The exception the driver raised.
        command: The statement's leading verb, which the duplicate-key short circuit
            tests [copybooks/mysql-procedures.cpy:L100-L103].
        we_error: The value ``We-Error`` already holds. Returned unchanged on the
            duplicate path, where the COBOL jump skips the ``move 911``
            [copybooks/mysql-procedures.cpy:L104].

    Returns:
        The status the COBOL would have reported.
    """
    return mysql_1100_db_error(
        errno=str(getattr(error, "errno", "") or ""),
        message=str(error),
        sql_state=str(getattr(error, "sqlstate", "") or ""),
        command=command,
        we_error=we_error,
    )


def _apply_db_error_status(file_access: FileAccess, status: DbErrorStatus) -> None:
    """Write a :class:`DbErrorStatus` into the caller's ``File-Access`` block."""
    file_access.fs_reply = int(status.fs_reply)
    file_access.we_error = int(status.we_error)
    status.apply_to_logging_data(file_access.logging_data)


def _require_connection() -> object:
    """The open connection, or a named failure.

    Raises:
        BridgeNotOpenError: If no ``Open`` has succeeded.
    """
    if _LINK.connection is None:
        raise BridgeNotOpenError(
            f"{BRIDGE_NAME}: no connection; File-Function 1 (fn-Open) must "
            f"succeed before any other verb [common/glpostingMT.cbl:L419]",
            operation="any verb before fn-Open",
            table=TABLE_NAME,
        )
    return _LINK.connection


def _positioning_cursor(connection: object) -> object:
    """A cursor for :mod:`acas_posting.dal.cursor_state` to issue its statement on.

    The positioning verbs are the one case where this module does NOT own the statement:
    ``cursor_state`` builds and executes it, so it needs the cursor itself rather than
    the statement-plus-cursor that :func:`acas_posting.dal.connection.execute_statement`
    yields.
    """
    return acquire_cursor(connection)  # type: ignore[arg-type]


def _mysql_fetch_record(
    row: Mapping[str, object], host_variables: TdGlpostingRec
) -> None:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT <14 HVs>``.

    The same fourteen host variables appear in both fetch lists - read-next
    [common/glpostingMT.cbl:L537-L554] and read-indexed [:L644-L661] - in COLUMN ordinal
    order, and ``HV-POST-RRN`` IS among them [:L538, :L645].

    Args:
        row: One row of the stored result, keyed by column name.
        host_variables: The group to populate. MUTATED IN PLACE, as the COBOL ``CALL``
            populates the group by reference.
    """
    for column in COLUMNS:
        if column.name not in row:
            # A column absent from the result is left at whatever the group already
            # held, which is what a `CALL` with a short result list would leave.
            continue
        host_variables.set_for(column, column.store(row[column.name]))


def ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba-ACAS-DAL-Process section.`` [common/glpostingMT.cbl:L334].

    The bridge's entry section. Reproduces [common/glpostingMT.cbl:L335-L343]: ``accept
    ws-env-lines from lines`` with a floor of 24, then two ``set ENVIRONMENT``
    statements that force ``Esc``, ``PgUp``, ``PgDown`` and ``PrtSc`` to be detected by
    the curses screen handler.
    """
    # `accept ws-env-lines from lines.` [common/glpostingMT.cbl:L335] with the `if ws-
    # env-lines < 24 move 24 ...` floor [:L336-L340]. Headless, so the floor is the
    # value.
    _LINK.ws_lines = MINIMUM_SCREEN_LINES
    # curses key handling for a screen section this migration does not have. Deliberate
    # omission, recorded in the module docstring.

    ba010_initialise(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )


def ba010_initialise(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba010-Initialise.`` [common/glpostingMT.cbl:L345].

    So a path that writes no status leaves the caller's INCOMING ``FS-Reply`` and ``We-
    Error`` in place. That is reachable.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    logging_data.ws_file_key = ""
    logging_data.sql_msg = ""
    logging_data.sql_err = ""
    logging_data.sql_state = ""
    # ANOMALY N-NOSTATUS: `move zero to We-Error Fs-Reply` is commented out at
    # [common/glpostingMT.cbl:L347-L348]. The incoming values are left alone.

    function_code = int(file_access.file_function)

    if function_code == FileFunction.OPEN:
        ba020_process_open(
            file_access,
            dal_common,
            system_record=system_record,
            transport=transport,
            states=states,
        )
        return
    if function_code == FileFunction.CLOSE:
        ba030_process_close(file_access, dal_common, states=states)
        return
    if function_code == FileFunction.READ_NEXT:
        ba040_process_read_next(file_access, dal_common, posting, states=states)
        return
    if function_code == FileFunction.READ_INDEXED:
        ba050_process_read_indexed(file_access, dal_common, posting, states=states)
        return
    if function_code == FileFunction.WRITE:
        ba070_process_write(file_access, dal_common, posting)
        return
    if function_code == FileFunction.DELETE_ALL:
        # "option 6 is a special to cleardown all data" [:L375]. Reached only through
        # the handler's ba015-Test-Ends [common/acas006.cbl:L643], never through the
        # handler's own dispatch.
        ba085_process_delete_all(file_access, dal_common, posting)
        return
    if function_code == FileFunction.RE_WRITE:
        ba090_process_rewrite(file_access, dal_common, posting)
        return
    if function_code == FileFunction.DELETE:
        ba080_process_delete(file_access, dal_common, posting)
        return
    if function_code == FileFunction.START:
        ba060_process_start(file_access, dal_common, posting, states=states)
        return
    ba100_bad_function(file_access, dal_common)


def ba020_process_open(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba020-Process-Open.`` [common/glpostingMT.cbl:L389].

    All of that is owned by :mod:`acas_posting.dal.connection`:
    :func:`~acas_posting.dal.connection.mysql_1000_open` performs the three connect
    steps [copybooks/mysql-procedures.cpy:L63-L86] and pins the numeric converter so
    that no column can arrive as binary floating point (R-2). It is CALLED, not
    duplicated.

    Args:
        file_access: The caller's linkage block. Mutated in place.
        dal_common: The testing switches [copybooks/Test-Data-Flags.cob].
        system_record: The record the credentials come from. Required, because
            the COBOL smuggles them through ``RDB-Data`` after
            ``ba012-Test-WS-Rec-Size-2`` copied them there
            [common/acas006.cbl:L627-L632]; passing the record down instead
            lets ``connection.py`` own the load.
        transport: The caller's transport policy. ``None`` defers to the ONE
            policy the deployment installed with
            :func:`acas_posting.dal.connection.set_connection_policy`.
        states: The cursor table, for the ``Most-Cursor-Set`` reset.

    Raises:
        ValueError: If ``system_record`` is absent. There is no credential source
            without it, and inventing one would be a fabrication.
    """
    if system_record is None:
        raise ValueError(
            f"{BRIDGE_NAME} ba020-Process-Open: the system record supplies the "
            f"RDBMS credentials [common/acas006.cbl:L627-L632]; none was passed"
        )
    outcome: OpenOutcome = mysql_1090_exit(
        mysql_1000_open(
            system_record,
            ws_no_paragraph=BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"],
            transport=transport,
        )
    )
    outcome.apply_to_logging_data(file_access.logging_data)
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    if not outcome.opened or int(outcome.fs_reply) != FsReply.SUCCESS:
        ba999_end(file_access, dal_common)
        return
    _LINK.connection = outcome.connection
    _write_file_key(file_access, WS_FILE_KEY_LITERALS["bridge-open"])
    _states(states).state_for(TABLE_NAME, CursorSlot.PRIMARY).set_cursor_not_active()
    ba999_end(file_access, dal_common)


def ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba030-Process-Close.`` [common/glpostingMT.cbl:L433].

    Note the order: the paragraph number is set AFTER the conditional free, so a close
    that frees a live cursor logs 20 from ``ba998-Free`` [:L1024] and then 20 is
    replaced by 2. Reproduced as written.
    """
    cursor_state_for_table = _states(states).state_for(TABLE_NAME, CursorSlot.PRIMARY)
    if cursor_state_for_table.cursor_active():
        ba998_free(file_access, states=states)
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba030-Process-Close"
    ]
    _write_file_key(file_access, WS_FILE_KEY_LITERALS["bridge-close"])
    mysql_1980_close(_LINK.connection)
    mysql_1999_exit()
    _LINK.connection = None
    ba999_end(file_access, dal_common)


def ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba040-Process-Read-Next.`` [common/glpostingMT.cbl:L448].

    When the cursor is not active the paragraph self-positions.
    """
    connection = _require_connection()
    cursor = _positioning_cursor(connection)
    try:
        outcome = read_next(
            cursor,
            TABLE_NAME,
            slot=CursorSlot.PRIMARY,
            states=_states(states),
            file_access=file_access,
        )
    finally:
        cursor.close()

    ba041_reread(file_access, dal_common, posting, outcome_row=outcome.row)


def ba041_reread(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    outcome_row: Mapping[str, object] | None,
) -> None:
    """``ba041-Reread.`` [common/glpostingMT.cbl:L523].

    ``if return-code = -1`` [:L556] is end of snapshot.

    Args:
        file_access: Status and logging destination; the paragraph number and the file
            key are written here.
        dal_common: The handler-common block ``ba999_end`` reports through.
        posting: The record the unloaded host variables are moved into.
        outcome_row: The record the snapshot walk returned, or ``None`` for the
            ``return-code = -1`` end of snapshot.
    """
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba041-Reread"
    ]
    if outcome_row is None:
        ba999_end(file_access, dal_common)
        return
    host_variables = TdGlpostingRec()
    _mysql_fetch_record(outcome_row, host_variables)
    bb100_unload_hvs(host_variables, posting)
    _write_file_key(
        file_access, COLUMNS_BY_NAME["POST-KEY"].render(host_variables.hv_post_key)
    )
    ba999_end(file_access, dal_common)


def ba050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba050-Process-Read-Indexed.`` [common/glpostingMT.cbl:L591].

    ANOMALY N-DEAD-READ-INDEXED-ERRNO. ``Ws-Mysql-Count-Rows`` is declared ``binary-
    double unsigned`` [copybooks/mysql-variables.cpy:L73] - and ANOMALY N-COUNTROWS-NEG-
    DEAD is that the signed redefinition which would make the second guard live, ``01
    WS-Mysql-Count-Rows-Neg redefines WS-Mysql-Count-Rows binary-double signed.``
    [copybooks/mysql-variables.cpy:L74-L75], is referenced NOWHERE in the frozen tree.
    """
    connection = _require_connection()
    cursor = _positioning_cursor(connection)
    key_number = int(file_access.logging_data.file_key_no) or 1
    try:
        outcome = read_indexed(
            cursor,
            TABLE_NAME,
            _key_of_reference_value(posting),
            key_number=key_number,
            slot=CursorSlot.PRIMARY,
            states=_states(states),
            file_access=file_access,
        )
    finally:
        cursor.close()

    if outcome.row is not None:
        file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            "ba050-Process-Read-Indexed-Fetch"
        ]
        host_variables = TdGlpostingRec()
        _mysql_fetch_record(outcome.row, host_variables)
        bb100_unload_hvs(host_variables, posting)
        # `move HV-POST-KEY to ws-temp-ed.
        _write_file_key(
            file_access,
            COLUMNS_BY_NAME["POST-KEY"].render(host_variables.hv_post_key),
        )
    # `go to ba998-Free.` [:L689] - and [:L635] on the no-row path. Class 4: ba998-Free
    # does work and then control reaches ba999-end.
    ba998_free(file_access, states=states)
    ba999_end(file_access, dal_common)


def ba060_process_start(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    states: CursorStateTable | None = None,
) -> None:
    """``ba060-Process-Start.`` [common/glpostingMT.cbl:L691].

    ``if access-type < 5 or > 8`` [:L695] - the maintainer's own note reads "not using
    not < or not >" - yields ``FS-Reply 99`` [:L696] and ``WE-Error 997`` [:L697], where
    the HANDLER's equivalent guard uses ``WE-Error 998`` for the same condition
    [common/acas006.cbl:L488].
    """
    connection = _require_connection()
    cursor = _positioning_cursor(connection)
    try:
        start(
            cursor,
            TABLE_NAME,
            _key_of_reference_value(posting),
            # `Access-Type` is passed through UNMODIFIED: the facade clears it for every
            # verb except `-Start`, so for a START it carries the relation
            # [copybooks/Proc-ACAS-FH-Calls.cob:L456-L463].
            int(file_access.access_type),
            key_number=int(file_access.logging_data.file_key_no) or 1,
            slot=CursorSlot.PRIMARY,
            states=_states(states),
            file_access=file_access,
        )
    finally:
        cursor.close()
    ba999_end(file_access, dal_common)


def ba070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    """``ba070-Process-Write.`` [common/glpostingMT.cbl:L802].

    ANOMALY N-DUPKEY-TWO-PLACES: the same condition is ALSO tested at driver level,
    where ``Mysql-1100-Db-Error`` short-circuits on errno 1062 or 1022 before ``SQL-
    Msg`` or ``SQL-State`` is filled [copybooks/mysql-procedures.cpy:L99-L105]. Both are
    reproduced; :mod:`acas_posting.dal.status` owns both predicates.
    """
    host_variables = bb000_hv_load(posting)
    _write_file_key(file_access, _post_key_tag(posting))
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    file_access.logging_data.sql_state = ""
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba070-Process-Write"
    ]
    try:
        affected = bb200_insert(_require_connection(), host_variables)
    except Exception as error:
        status = _driver_error_status(error, command="INSERT")
        status.apply_to_logging_data(file_access.logging_data)
        if status.duplicate_key or is_duplicate_key_bridge_level(
            status.sql_err, status.sql_state
        ):
            file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
        else:
            file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(status.we_error)
        ba999_end(file_access, dal_common)
        return
    if affected != 1:
        # The count test [:L810] with no driver error to report: the inner `if
        # WS-MYSQL-Error-Number (1:1) not = "0"` [:L814] is false, so NOTHING is
        # written - ANOMALY N-NOSTATUS. The values set at [:L805] stand, which
        # here means success is reported for a row that was not inserted.
        #  AND NOTHING IS REPORTED, WHICH IS THE ANOMALY ITSELF. "The frozen
        #  source writes no status on this path" is the whole content of
        #  N-NOSTATUS: the values set at [:L805] stand, so SUCCESS is reported for
        #  a row that was not inserted, and no operator ever hears about it. A log
        #  record here would be a diagnostic the compiled program cannot produce
        #  and would make the defect look handled (rule R-4). N-NOSTATUS is
        #  recorded, with its four sites, in `docs/migration/anomaly-log.md`.
        #
        #  The frozen `if` is kept, with an empty body, because rule R-5 requires
        #  every branch of the paragraph to remain visible: a reader comparing the
        #  two files must find the test, and find that it does nothing.
        pass
    # `go to ba999-End.` [:L827] - Class 3.
    ba999_end(file_access, dal_common)


def _post_key_tag(posting: WsPostingRecord) -> str:
    """``move ws-Post-Key to WS-File-Key`` [common/glpostingMT.cbl:L804, :L969].

    The record's own ten-digit post key, ``Batch`` then ``Post-Number``. Distinct from
    :func:`_key_of_reference_value`, which is the ANOMALY N-KOR slice the ``WHERE``
    clauses compare. Two sites use this one - write and rewrite - and five use the
    slice.
    """
    return f"{int(_join_post_key(posting.ws_post_key)):010d}"


def ba080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    r"""``ba080-Process-Delete.`` [common/glpostingMT.cbl:L829].

    Builds ``\`POST-KEY\`="<WS-Posting-Record (1:10)>"`` [:L837-L846] - the ANOMALY
    N-KOR slice again, with the same commented-out ``*> Post-Key`` [:L842] - tags the
    log with the slice [:L847], sets paragraph 13 [:L852] and issues ``DELETE FROM
    \`GLPOSTING-REC\` WHERE ...`` [:L858-L864].
    """
    where_clause, where_parameters = _where_equal_to(posting)
    _write_file_key(file_access, _key_of_reference_value(posting))
    file_access.logging_data.ws_log_where = where_clause
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba080-Process-Delete"
    ]
    statement = (
        f"DELETE FROM {quote_identifier(TABLE_NAME)} WHERE {where_clause}"
    )
    try:
        with execute_statement(
            _require_connection(), statement, where_parameters
        ) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:
        # [:L867-L876] with `move 99 to fs-reply` [:L874] and `move 995 to WE-Error`
        # [:L875]. TWO STAGES, as the frozen source has them.
        status = override_we_error_for_operation(
            _driver_error_status(error, command="DELETE"), FileFunction.DELETE
        )
        _apply_db_error_status(file_access, status)
        ba999_end(file_access, dal_common)
        return
    if affected != 1:
        # ANOMALY N-NOSTATUS [:L866-L877]: the count is wrong but there is no
        # driver error, so the inner `if` [:L870] is false and NEITHER status
        # field is written. The caller's incoming values survive.
        #  SILENT, per N-NOSTATUS. The caller's incoming status values survive and
        #  nothing is written or reported - and `ba010-Initialise`'s clearing
        #  statement is commented out [:L347-L348], so those incoming values are
        #  whatever the previous operation left. Reproduced, not reported: a record
        #  here has no counterpart in the frozen source (rule R-4).
        #
        #  The frozen `if` is kept, with an empty body, because rule R-5 requires
        #  every branch of the paragraph to remain visible: a reader comparing the
        #  two files must find the test, and find that it does nothing.
        pass
        ba999_end(file_access, dal_common)
        return
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ba999_end(file_access, dal_common)


def ba085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    """``ba085-Process-Delete-ALL.`` [common/glpostingMT.cbl:L885].

    The maintainer labels the whole paragraph "THIS IS NON STANDARD". ANOMALY N-DELETE-
    ALL: it is NOT a truncate.
    """
    posting.ws_post_key.batch = 99999
    posting.ws_post_key.post_number = 99999
    where_clause, where_parameters = _where_less_than(posting)
    _write_file_key(
        file_access,
        f"{WS_FILE_KEY_LITERALS['bridge-delete-all']}{_post_key_tag(posting)}",
    )
    file_access.logging_data.ws_log_where = where_clause
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba085-Process-Delete-ALL"
    ]
    statement = f"DELETE FROM {quote_identifier(TABLE_NAME)} WHERE {where_clause}"
    try:
        with execute_statement(
            _require_connection(), statement, where_parameters
        ) as cursor:
            affected = int(cursor.rowcount)
    except Exception as error:
        status = override_we_error_for_operation(
            _driver_error_status(error, command="DELETE"), FileFunction.DELETE
        )
        _apply_db_error_status(file_access, status)
        ba999_end(file_access, dal_common)
        return
    if affected <= 0:
        # ANOMALY N-DELETE-ALL's own half: `not > zero` [:L947] means an empty
        # table is a failure. With no driver error the inner `if` [:L951] is
        # false, so nothing is written - ANOMALY N-NOSTATUS again - and control
        # transfers at [:L958].
        #  SILENT, per N-NOSTATUS. An already-empty table takes this path - `not >
        #  zero` [:L947] makes emptiness a failure - and the frozen source writes
        #  and displays nothing on it. Reproduced, not reported (rule R-4).
        #
        #  The frozen `if` is kept, with an empty body, because rule R-5 requires
        #  every branch of the paragraph to remain visible: a reader comparing the
        #  two files must find the test, and find that it does nothing.
        pass
        ba999_end(file_access, dal_common)
        return
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ba999_end(file_access, dal_common)


def ba090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
) -> None:
    """``ba090-Process-Rewrite.`` [common/glpostingMT.cbl:L966].

    ANOMALY N-RRN reaches the table on this path too, and that is easy to miss:
    ``bb300-Update`` puts ``POST-RRN`` in its ``SET`` list [:L1309-L1319] and
    ``bb000-HV-Load`` never loaded it, so EVERY REWRITE STAMPS THE PRIMARY KEY BACK TO
    ZERO.
    """
    host_variables = bb000_hv_load(posting)
    _write_file_key(file_access, _post_key_tag(posting))
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba090-Process-Rewrite"
    ]
    where_clause, where_parameters = _where_equal_to(posting)
    file_access.logging_data.ws_log_where = where_clause
    try:
        affected = bb300_update(
            _require_connection(), host_variables, where_clause, where_parameters
        )
    except Exception as error:
        status = override_we_error_for_operation(
            _driver_error_status(error, command="UPDATE"), FileFunction.RE_WRITE
        )
        _apply_db_error_status(file_access, status)
        ba999_end(file_access, dal_common)
        return
    if affected != 1:
        # ANOMALY N-NOSTATUS [:L993-L1005].
        #  SILENT, per N-NOSTATUS - the fourth and last of its sites. Reproduced,
        #  not reported (rule R-4).
        #
        #  The frozen `if` is kept, with an empty body, because rule R-5 requires
        #  every branch of the paragraph to remain visible: a reader comparing the
        #  two files must find the test, and find that it does nothing.
        pass
        ba999_end(file_access, dal_common)
        return
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    file_access.logging_data.sql_err = ""
    file_access.logging_data.sql_msg = ""
    ba999_end(file_access, dal_common)


def ba100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba100-Bad-Function.`` [common/glpostingMT.cbl:L1011].

    ANOMALY N-BRIDGE-BAD-FN: the HANDLER's ``aa100-Bad-Function`` reports ``WE-Error
    999`` for the same condition [common/acas006.cbl:L561], so one call chain carries
    two different "bad function" codes depending on which program detected it.
    """
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    file_access.fs_reply = int(FsReply.ERROR)
    ba999_end(file_access, dal_common)


def ba998_free(
    file_access: FileAccess, *, states: CursorStateTable | None = None
) -> None:
    """``ba998-Free.`` [common/glpostingMT.cbl:L1023].

    ``move 20 to ws-No-Paragraph.`` [:L1024], ``CALL "MySQL_free_result" USING WS-MYSQL-
    RESULT`` [:L1030-L1031] and ``set Cursor-Not-Active to true.`` [:L1033]. This is the
    ONLY paragraph that frees the stored result.
    """
    file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba998-Free"]
    _states(states).state_for(TABLE_NAME, CursorSlot.PRIMARY).free()


def ba999_end(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """``ba999-end.`` [common/glpostingMT.cbl:L1035]."""
    if int(dal_common.sw_testing) == 1:
        mt_ca_process_logs(file_access, dal_common)
    ba999_exit()


def ba999_exit() -> None:
    """``ba999-exit. exit program.`` [common/glpostingMT.cbl:L1042-L1043].

    Returns control to the handler. Nothing to do: the Python call returns, and the
    caller's ``File-Access`` block already carries every field the COBOL would have left
    in it.
    """
    return


def mt_ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` of the BRIDGE [common/glpostingMT.cbl:L1487].

    ``call "fhlogger" using File-Access ACAS-DAL-Common-data.`` [:L1489-L1490].

    ``common/fhlogger.cbl`` is explicitly out of scope (AAP section 0.2.2 lists it
    among the non-posting utilities) and rule R-1 forbids calling it, so the
    external log file it writes is not reproduced. It carries no database effect
    and appears in no table dump, which is why AAP section 0.3.4 classes such
    output as a log record rather than behaviour. A structured record with the
    same fields is emitted instead, by the ONE adapter every handler and bridge in
    this layer shares - :func:`acas_posting.dal.status.log_file_handler_record`.

    ``Log-File-Rec-Written`` [copybooks/Test-Data-Flags.cob:L18] IS ADVANCED, and
    leaving it alone was a defect rather than a decision: ``fhlogger`` owns the
    counter but the counter itself lives in ``ACAS-DAL-Common-data``, which this
    function is handed and which the caller keeps, so an untouched field made the
    shared block diverge from what the frozen run would hold. The adapter advances
    it modulo one million, which is the wrap its ``pic 9(6)`` imposes.

    THREE FIELDS ARE WITHHELD, and the adapter's docstring says why: ``WS-File-Key``
    is the posting row's own ten-digit key, ``WS-Log-Where`` is the ``WHERE`` clause
    built around it, and ``SQL-Msg`` is text the server builds out of material that
    can include account names, host names and data values. ``sanitise_for_log`` was
    applied to all three and only ever escaped and bounded them - it removed no
    value, because no rule can tell a posted amount from a column name (CWE-532).
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program=BRIDGE_NAME,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=str(logging_data.sql_err),
        sql_state=str(logging_data.sql_state),
        dal_common=dal_common,
    )
    mt_ca_exit()


def mt_ca_exit() -> None:
    """``ca-Exit. exit.`` of the BRIDGE [common/glpostingMT.cbl:L1493]."""
    return


def glposting_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``glpostingMT`` - the bridge, entered at its ``PROCEDURE DIVISION``.

    This is the handler-named half of the dual vocabulary R-5 requires: a reader
    following the bridge's own calling convention finds a function of this name and this
    signature, while a reader following the facade's finds :func:`dispatch`.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L22]. Carries the
            requested ``File-Function`` and ``Access-Type`` in and the status
            out. MUTATED IN PLACE.
        dal_common: ``ACAS-DAL-Common-data``
            [copybooks/Test-Data-Flags.cob:L6].
        posting: ``WS-Posting-Record`` [copybooks/wspost.cob:L12]. Read on a
            write, mutated on a read.
        system_record: Needed by ``fn-Open`` alone, to reach the credentials the
            COBOL had already copied into ``RDB-Data``.
        transport: The transport policy for the open; ``None`` defers to the one
            installed ``ConnectionPolicy``.
        states: The cursor table; ``None`` uses the bridge's own, which is the
            faithful analogue of its ``01 DAL-Data`` working storage.
    """
    ba_acas_dal_process(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )


# HANDLER `acas006` - `common/acas006.cbl` The handler is a SEPARATE COBOL PROGRAM from
# the bridge above, with its own working storage, its own paragraph numbering series
# (201..208 against the bridge's 1..20) and its own five-parameter linkage
# [common/acas006.cbl:L273-L279].


DISPLAY_BLK_WIDTH: Final[int] = 75

#: `03 GL901 pic x(31) value "GL901 Note error and hit return".`
#: [common/acas006.cbl:L257]. Displayed at 2401 beside the record-length error [:L614].
GL901_MESSAGE: Final[str] = "GL901 Note error and hit return"

#: `03 GL903 pic x(32) value "GL903 Program Error.
GL903_MESSAGE: Final[str] = "GL903 Program Error: Temp rec = "


@dataclass(slots=True)
class _HandlerWorkingStorage:
    """The handler's own working storage, the three fields with run-long state.

    ``A`` and ``B`` are the record lengths, and the maintainer's own comment "A & B used
    in 1st test ONLY" is the whole point of them.
    """

    a: int = 0
    b: int = 0
    cobol_file_status: int = 0

    def cobol_file_eof(self) -> bool:
        """``88 Cobol-File-Eof value 1.`` [common/acas006.cbl:L252]."""
        return self.cobol_file_status == 1

    def set_cobol_file_eof(self) -> None:
        """``set Cobol-File-EoF to true`` [common/acas006.cbl:L439]."""
        self.cobol_file_status = 1


#: The handler's working storage. ONE instance, no lock: rule R-3 forbids concurrency,
#: so the single-threaded COBOL's single copy is the faithful model.
_HANDLER: Final[_HandlerWorkingStorage] = _HandlerWorkingStorage()


def cancel_acas006() -> None:
    """Discard the handler's working storage - the COBOL ``CANCEL`` equivalent.

    Resets ``A``, ``B`` and ``Cobol-File-Status`` to their ``VALUE`` clauses.
    """
    _HANDLER.a = 0
    _HANDLER.b = 0
    _HANDLER.cobol_file_status = 0


def _flat_file_store_unavailable(
    verb: str, locator: str
) -> CobolFlatFileStoreUnavailableError:
    """The failure raised where the COBOL would have issued an ISAM verb.

    ``Posting-File`` is an indexed file declared by ``copybooks/selpost.cob`` over
    ``copybooks/fdpost.cob``, and the migration's store is the frozen MySQL schema.
    """
    return CobolFlatFileStoreUnavailableError(
        f"{HANDLER_NAME}: the COBOL flat-file store is not part of this "
        f"migration, so `{verb} Posting-File` [{locator}] has no target; the "
        f"in-scope store is `{TABLE_NAME}` reached through {BRIDGE_NAME}. Set "
        f"File-System-Used to 1 (FS-RDBMS-Used) "
        f"[copybooks/wssystem.cob:L116] so that the RDB branch "
        f"[common/acas006.cbl:L322-L326] is taken.",
        operation=verb,
        table=TABLE_NAME,
    )


def aa_process_flat_file(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas006.cbl:L282].

    A label only: the section header carries no statements, so control falls straight
    into :func:`aa010_main` at [:L284].
    """
    aa010_main(
        system,
        posting,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def aa010_main(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``aa010-main.`` [common/acas006.cbl:L284] - the handler's whole mainline.

    Six things happen, in this order, and the order is the contract (rule R-6).

    Args:
        system: ``System-Record`` - the first linkage parameter. Read for ``RDBMS-Flat-
            Statuses`` [:L323] and for the six credentials [:L627].
        posting: ``WS-Posting-Record`` - the second. Read on a write, mutated on a read.
        file_access: ``File-Access`` - the third. Mutated in place; this is how the
            status reaches the caller.
        file_defs: ``File-Defs`` - the fourth. Carries the file and work-file names
            [copybooks/wsnames.cob]; consulted by the flat-file store only, which is why
            nothing below reads it.
        dal_common: ``ACAS-DAL-Common-data`` - the fifth.
        transport: The transport policy handed to the open.
        states: The cursor table; ``None`` uses the bridge's own.
    """
    file_access.logging_data.ws_log_system = int(WS_LOG_SYSTEM)
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_COBOL_PATH

    # 2. The key guard [:L293-L307]. `evaluate File-Function` over 4, 9 and 8.
    function_code = int(file_access.file_function)
    key_number = int(file_access.logging_data.file_key_no)
    if function_code in (FileFunction.READ_INDEXED, FileFunction.START):
        if key_number != 1:
            # `move 998 to WE-Error` [:L297] - ANOMALY N-998, meaning 2 of 3.
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(file_access, dal_common)
            return
    elif function_code == FileFunction.DELETE:
        if key_number != 1:
            # `move 996 to WE-Error` [:L303] - and ANOMALY N-996-comment, the copy-
            # pasted gloss.
            file_access.we_error = int(WeError.DELETE_KEY_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(file_access, dal_common)
            return

    flat_statuses = system.system_data_block.rdbms_flat_statuses
    cobol_files_used = int(flat_statuses.file_system_used) == 0

    # 3. ANOMALY N18b, stage 1 [:L313-L318]. Note the ABSENCE of any `set fn-delete-all
    # to true` here, where common/acas008.cbl:L316 has one.
    if (
        function_code == FileFunction.OPEN
        and int(file_access.access_type) == AccessType.OUTPUT
        and not cobol_files_used
    ):
        ba_process_rdbms(
            system,
            posting,
            file_access,
            dal_common,
            transport=transport,
            states=states,
        )
        aa_main_exit()
        return

    if not cobol_files_used:
        flat_statuses = system.system_data_block.rdbms_flat_statuses
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = int(
            flat_statuses.file_system_used
        )
        file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = int(
            flat_statuses.file_duplicates_in_use
        )
        ba_process_rdbms(
            system,
            posting,
            file_access,
            dal_common,
            transport=transport,
            states=states,
        )
        aa_main_exit()
        return

    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        # `go to ba-rdbms-exit` [:L620] left the section, so the flat-file dispatch
        # below is not reached.
        return

    # ANOMALY N-NOSTATUS, handler side: [:L340-L341] are COMMENTED OUT, so only the
    # three diagnostic fields are cleared here. *> move zero to WE-Error *> ? FS-Reply.
    file_access.logging_data.sql_err = ""
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_state = ""

    fired = _aa010_dispatch_flat_file(posting, file_access, dal_common)
    if not fired:
        # `go to aa100-Bad-Function.` [:L366], the maintainer's belt and braces: "Should
        # never get here but in case :(".
        aa100_bad_function(file_access, dal_common)


def _aa010_dispatch_flat_file(
    posting: WsPostingRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> bool:
    """``evaluate File-Function`` of ``aa010-main`` [common/acas006.cbl:L344-L363].

    Split out so that the unconditional ``go to aa100-Bad-Function.`` at [:L366] can be
    modelled as the guarded statement it is rather than as dead text.

    Returns:
        ``True`` if any arm fired, which is always: ``when other`` is an arm too.
    """
    function_code = int(file_access.file_function)
    if function_code == FileFunction.OPEN:
        aa020_process_open(file_access, dal_common)
        return True
    if function_code == FileFunction.CLOSE:
        aa030_process_close(file_access, dal_common)
        return True
    if function_code == FileFunction.READ_NEXT:
        aa040_process_read_next(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.READ_INDEXED:
        aa050_process_read_indexed(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.WRITE:
        aa070_process_write(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.RE_WRITE:
        aa090_process_rewrite(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.DELETE:
        aa080_process_delete(posting, file_access, dal_common)
        return True
    if function_code == FileFunction.START:
        aa060_process_start(posting, file_access, dal_common)
        return True
    aa100_bad_function(file_access, dal_common)
    return True


def aa020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa020-Process-Open.`` [common/acas006.cbl:L368].

    Raises:
        CobolFlatFileStoreUnavailableError: For input, i-o and output, where the COBOL
            issues an ISAM ``open``.
    """
    _write_file_key(file_access, "")
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa020-Process-Open"
    ]
    access_type = int(file_access.access_type)
    if access_type == AccessType.EXTEND:
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(file_access, dal_common)
        return
    if access_type == AccessType.INPUT:
        raise _flat_file_store_unavailable("open input", "common/acas006.cbl:L372")
    if access_type == AccessType.I_O:
        raise _flat_file_store_unavailable("open i-o", "common/acas006.cbl:L380")
    if access_type == AccessType.OUTPUT:
        raise _flat_file_store_unavailable("open output", "common/acas006.cbl:L389")
    # No arm matched, which the COBOL's nested `if` also allows.
    _HANDLER.cobol_file_status = 0
    _write_file_key(file_access, WS_FILE_KEY_LITERALS["handler-open"])
    if int(file_access.fs_reply) != FsReply.SUCCESS:
        file_access.we_error = int(WeError.NOT_USED)
    aa999_main_exit(file_access, dal_common)


def aa030_process_close(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa030-Process-Close.`` [common/acas006.cbl:L406].

    ``[:L410]`` is a dated commented-out ``move zeros to FS-Reply WE-Error`` - a THIRD
    member of the ANOMALY N-NOSTATUS family, alongside [:L340-L341] here and
    [common/glpostingMT.cbl:L347-L348] in the bridge. The close therefore reports
    whatever the ``close`` verb left.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``close Posting-File`` [:L409].
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa030-Process-Close"
    ]
    _write_file_key(file_access, "")
    raise _flat_file_store_unavailable("close", "common/acas006.cbl:L409")


def aa040_process_read_next(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas006.cbl:L419].

    ``move 10 to FS-Reply WE-Error`` is one statement writing BOTH fields, the same
    idiom the bridge uses at [common/glpostingMT.cbl:L557], which is why end of file
    carries ``We-Error`` 10 rather than zero.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa040-Process-Read-Next"
    ]
    if _HANDLER.cobol_file_eof():
        fs_reply, we_error = end_of_file_status()
        file_access.fs_reply = int(fs_reply)
        file_access.we_error = int(we_error)
        file_access.logging_data.sql_err = ""
        file_access.logging_data.sql_msg = ""
        # L431  move zeros to Post-Key - the FD record's key, which this
        # migration does not carry; the WS record the caller passed is NOT
        # touched, so nothing is written here.
        # L432  stop "Cobol File EOF"  *> for testing - the operator pause is
        # dropped per Agent Action Plan section 0.3.4; the transfer is kept.
        #  ONE ERROR, THROUGH THE ONE REPORTER. Six handlers carry a `stop "Cobol
        #  File EOF"` and each used to report it at its own level - WARNING here,
        #  INFO, DEBUG and ERROR elsewhere - which made the same event unfindable.
        #  `log_cobol_stop` emits it at ERROR everywhere, because reaching a
        #  debugging stop in a shipped handler is the strongest signal the frozen
        #  source has. The pause is dropped, the transfer below is kept.
        log_cobol_stop(
            _LOG,
            program=HANDLER_NAME,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas006.cbl:L425-L432]",
        )
        aa999_main_exit(file_access, dal_common)
        return
    aa041_reread(posting, file_access, dal_common)


def aa041_reread(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa041-Reread.`` [common/acas006.cbl:L436].

    ANOMALY N-REREAD-ASYMMETRY. ``acas006`` has TWO reread paragraphs, this one and
    :func:`aa051_reread` after the indexed read.

    Raises:
        CobolFlatFileStoreUnavailableError: At ``read ... next record`` [:L437].
    """
    raise _flat_file_store_unavailable(
        "read ... next record", "common/acas006.cbl:L437"
    )


def aa050_process_read_indexed(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas006.cbl:L452].

    That comment block is the flat-file side of the ``POST-RRN`` question the ``.scb``
    raises at [common/glpostingMT.scb:L229] and ``copybooks/selpost.cob`` raises a third
    time with ``record key Post-Rrn *> MAY NEED CHANGING <<<``.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa050-Process-Read-Indexed"
    ]
    aa051_reread(posting, file_access, dal_common)


def aa051_reread(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa051-Reread.`` [common/acas006.cbl:L461].

    Raises:
        CobolFlatFileStoreUnavailableError: At ``read ... invalid key`` [:L465].
    """
    _write_file_key(file_access, _post_key_tag(posting))
    _HANDLER.cobol_file_status = 0
    raise _flat_file_store_unavailable(
        "read ... invalid key", "common/acas006.cbl:L465"
    )


def aa060_process_start(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa060-Process-Start.`` [common/acas006.cbl:L473].

    There is no ``move 99 to fs-reply``. Since [:L480] had just cleared ``FS-Reply`` to
    zero, an invalid access type returns ``(0, 998)`` - SUCCESS paired with an error
    code. The BRIDGE's equivalent guard writes both, ``99`` and ``997``
    [common/glpostingMT.cbl:L695-L697].

    Raises:
        CobolFlatFileStoreUnavailableError: At the first ``start`` verb reached.
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa060-Process-Start"
    ]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    _write_file_key(file_access, _post_key_tag(posting))
    access_type = int(file_access.access_type)
    lowest, highest = START_ACCESS_TYPE_RANGE
    if access_type < lowest or access_type > highest:
        # ANOMALY N-START-NO-FSREPLY: `move 998 to WE-Error` [:L488] and NOTHING to FS-
        # Reply, which [:L480] left at zero. Success paired with an error.
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        aa999_main_exit(file_access, dal_common)
        return
    if access_type == AccessType.EQUAL_TO:
        raise _flat_file_store_unavailable(
            "start ... key =", "common/acas006.cbl:L495"
        )
    if access_type == AccessType.NOT_LESS_THAN:
        raise _flat_file_store_unavailable(
            "start ... key not <", "common/acas006.cbl:L501"
        )
    if access_type == AccessType.GREATER_THAN:
        raise _flat_file_store_unavailable(
            "start ... key >", "common/acas006.cbl:L507"
        )
    if access_type == AccessType.LESS_THAN:
        raise _flat_file_store_unavailable(
            "start ... key <", "common/acas006.cbl:L514"
        )
    # L520 go to aa999-main-exit. *> logging - Class 3. Unreachable given the guard
    # above admits only 5 through 8 and all four have arms.
    aa999_main_exit(file_access, dal_common)


def aa070_process_write(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa070-Process-Write.`` [common/acas006.cbl:L522].

    Raises:
        CobolFlatFileStoreUnavailableError: At ``write ... invalid key`` [:L528].
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa070-Process-Write"
    ]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    # L527 move Post-Key to WS-File-Key.
    _write_file_key(file_access, _post_key_tag(posting))
    raise _flat_file_store_unavailable(
        "write ... invalid key", "common/acas006.cbl:L528"
    )


def aa080_process_delete(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa080-Process-Delete.`` [common/acas006.cbl:L534].

    ``delete`` carries NO ``invalid key`` clause [:L544], so a delete that matches
    nothing reports whatever the file status left in ``FS-Reply`` - the flat-file twin
    of ANOMALY N-NOSTATUS, where the bridge's zero-row delete writes no status either
    [common/glpostingMT.cbl:L866-L877].

    Raises:
        CobolFlatFileStoreUnavailableError: At ``delete ... record`` [:L544].
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa080-Process-Delete"
    ]
    _write_file_key(file_access, _post_key_tag(posting))
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    raise _flat_file_store_unavailable("delete ... record", "common/acas006.cbl:L544")


def aa090_process_rewrite(
    posting: WsPostingRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas006.cbl:L547].

    Like the delete, ``rewrite`` carries no ``invalid key`` clause [:L554].

    Raises:
        CobolFlatFileStoreUnavailableError: At ``rewrite`` [:L554].
    """
    file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa090-Process-Rewrite"
    ]
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    _write_file_key(file_access, _post_key_tag(posting))
    raise _flat_file_store_unavailable("rewrite", "common/acas006.cbl:L554")


def aa100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa100-Bad-Function.`` [common/acas006.cbl:L557].

    ANOMALY N-BRIDGE-BAD-FN, handler side: 999 here against the bridge's 990
    [common/glpostingMT.cbl:L1015], and the authoritative table's own "Invalid Function
    requested" code 992 [:L146] written by neither. Three codes for one condition; none
    harmonised.
    """
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit.`` [common/acas006.cbl:L564].

    ``Testing-1`` is ``88 Testing-1 value 1`` over ``SW-Testing pic 9 value 1``
    [copybooks/Test-Data-Flags.cob:L10-L11], so the DECLARED DEFAULT IS ON and the
    maintainer's note says how to turn it off: "set sw-testing to zero to stop logging"
    [common/acas006.cbl:L271].
    """
    if int(dal_common.sw_testing) == 1:
        ca_process_logs(file_access, dal_common)
    aa_main_exit()


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas006.cbl:L569]."""
    aa_exit()


def aa_exit() -> None:
    """``aa-Exit. exit program.`` [common/acas006.cbl:L573-L574]."""
    return


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` of the HANDLER [common/acas006.cbl:L666].

    ``call "fhlogger" using File-Access ACAS-DAL-Common-data.`` [:L669-L670],
    under the maintainer's "Not called on DAL access as it does it already"
    [:L666] - which is exactly right and exactly why a close produces several
    records: the bridge's ``ba999-end`` has already logged before the handler's
    ``aa999-main-exit`` logs again.

    Distinct from :func:`mt_ca_process_logs`, the bridge's paragraph of the same
    name [common/glpostingMT.cbl:L1487]. The two are separate programs, so the
    COBOL names do not collide; in one Python module they would, and the bridge's
    copies carry the ``mt_`` prefix for that reason - recorded here because a
    reader looking for ``Ca-Process-Logs`` will find two.

    ``common/fhlogger.cbl`` is out of scope (Agent Action Plan section 0.2.2) and
    rule R-1 forbids calling it, so a structured record stands in for the file it
    writes. It reaches no table and appears in no dump. The record is composed by
    the ONE adapter this layer shares,
    :func:`acas_posting.dal.status.log_file_handler_record`, which also advances
    ``Log-File-Rec-Written`` modulo one million and withholds ``WS-File-Key``,
    ``WS-Log-Where`` and ``SQL-Msg`` - see the note on :func:`mt_ca_process_logs`.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program=HANDLER_NAME,
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
    ca_exit()


def ca_exit() -> None:
    """``ca-Exit. exit.`` of the HANDLER [common/acas006.cbl:L672]."""
    return


def ba_process_rdbms(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas006.cbl:L576].

    THE WHOLE SECTION IS A CHAIN OF FALL-THROUGHS: ``ba010-Test-WS-Rec-Size`` [:L584]
    into ``ba012-Test-WS-Rec-Size-2`` [:L592] into ``ba015-Test-Ends`` [:L635] into
    ``ba020-Process-DAL`` [:L653] into ``ba-rdbms-exit`` [:L662]. There is not one ``go
    to`` between them except the record-length escape at [:L620].
    """
    ba010_test_ws_rec_size(
        system,
        posting,
        file_access,
        dal_common,
        transport=transport,
        states=states,
    )


def ba010_test_ws_rec_size(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas006.cbl:L584].

    The 12 written by ``aa010-main`` at [:L289] is replaced by 22 the instant the RDB
    path is entered, so every migrated run logs 22 and only a flat-file run logs 12.
    """
    # L590 move 22 to WS-Log-File-no. - ANOMALY N-log. Note the lower-case `no` here
    # against `No` at [:L289].
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB_PATH
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        ba_rdbms_exit()
        return
    ba015_test_ends(
        file_access,
        dal_common,
        posting,
        system_record=system,
        transport=transport,
        states=states,
    )


def ba012_test_ws_rec_size_2(
    system: SystemRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas006.cbl:L592].

    ``copybooks/fdpost.cob`` and ``copybooks/wspost.cob`` declare the SAME fifteen
    fields with the same pictures, differing only in the ``WS-`` name prefixes, so both
    records are 103 bytes and ``A < B`` can never hold.

    Returns:
        ``True`` if the record-length branch transferred to ``ba-rdbms-exit`` [:L620],
            which by ANOMALY N-901-DEAD it never does.
    """
    if _HANDLER.a == 0:
        _HANDLER.a = WS_POSTING_RECORD_BYTES
        _HANDLER.b = POSTING_RECORD_BYTES
        if _HANDLER.a < _HANDLER.b:
            # ANOMALY N-901-DEAD: unreachable, because both records are
            # WS_POSTING_RECORD_BYTES == POSTING_RECORD_BYTES == 103 bytes. `move 901 to
            # WE-Error` [:L602], `move 99 to fs-reply` [:L603].
            file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
            file_access.fs_reply = int(FsReply.ERROR)
        if int(file_access.we_error) == WeError.RECORD_SIZE_MISMATCH:
            display_blk = (
                f"{GL903_MESSAGE}{_HANDLER.a:04d} < Posting-Rec = "
                f"{_HANDLER.b:04d}"
            )[:DISPLAY_BLK_WIDTH]
            file_access.logging_data.sql_msg = display_blk
            if int(dal_common.sw_testing) == 1:
                ca_process_logs(file_access, dal_common)
            _LOG.error(
                "ba012-Test-WS-Rec-Size-2 [common/acas006.cbl:L601-L620]: %s "
                "- WE-Error 901; the caller must stop",
                display_blk,
            )
            return True
        load_rdb_data_once(system)
    return False


def ba015_test_ends(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba015-Test-Ends.`` [common/acas006.cbl:L635] - ANOMALY N18b, stage 2.

    first with ``fn-Open`` / ``fn-Output``, then with ``fn-Delete-All``.

    N18b is registered by name under A-NEW-8 in ``docs/migration/anomaly-log.md``. Its
    key-bound note carries the MEASURED consequence for this table: the delete-all runs,
    but the bound `glpostingMT` composes is the key text ``9999999999``
    [common/glpostingMT.cbl:L907], while every key this bridge stores is a group-move
    image near 4.7e17 [common/glpostingMT.cbl:L1054] - so a bridge-written
    ``GLPOSTING-REC`` row SURVIVES an ``Open-Output``, where the sibling
    ``GLBATCH-REC`` row does not.
    """
    if (
        int(file_access.file_function) == FileFunction.OPEN
        and int(file_access.access_type) == AccessType.OUTPUT
    ):
        ba020_process_dal(
            file_access,
            dal_common,
            posting,
            system_record=system_record,
            transport=transport,
            states=states,
        )
        file_access.file_function = int(FileFunction.DELETE_ALL)
    ba020_process_dal(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )
    ba_rdbms_exit()


def ba020_process_dal(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    posting: WsPostingRecord,
    *,
    system_record: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``ba020-Process-DAL.`` [common/acas006.cbl:L653].

    THREE parameters with ``File-Access`` FIRST, where the handler's own linkage takes
    five with ``System-Record`` first [:L273-L279]. The blank line between the second
    and third arguments is the maintainer's own [:L656].
    """
    glposting_mt(
        file_access,
        dal_common,
        posting,
        system_record=system_record,
        transport=transport,
        states=states,
    )


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit. exit section.`` [common/acas006.cbl:L662-L663]."""
    return


def dispatch(
    system: SystemRecord,
    posting: WsPostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> None:
    """``acas006`` - the file handler, entered at its ``PROCEDURE DIVISION``.

    This is the entity-named half of the dual vocabulary rule R-5 requires: the GL-
    Posting facade verbs [copybooks/Proc-ACAS-FH-Calls.cob] reach the table through
    here, while a reader following the bridge's own convention uses
    :func:`glposting_mt`. One implementation, two published entry points.

    Args:
        system: ``System-Record``. Read for ``RDBMS-Flat-Statuses`` and the six RDBMS
            credentials.
        posting: ``WS-Posting-Record``. Read on a write, mutated on a read.
        file_access: ``File-Access``. Carries the verb in and the status out.
        file_defs: ``File-Defs``. Part of the linkage; consulted by the flat-file store
            alone.
        dal_common: ``ACAS-DAL-Common-data``, the two testing switches and the log
            counter.
        transport: Transport policy for the open. Keyword-only, and NOT part of the
            COBOL linkage - the compiled system reaches its connection through
            ``RDB-Data`` and a C interface that has no transport policy at all, so
            this is the migration's own reporting layer rather than a reproduction
            of anything. ``None`` defers to the one installed
            ``ConnectionPolicy``.
        states: The cursor table. Keyword-only for the same reason: the bridge's
            ``01 DAL-Data`` is its own working storage, and this parameter exists so
            a test can supply an isolated copy.

    Raises:
        CobolFlatFileStoreUnavailableError: If ``File-System-Used`` says COBOL files
            [copybooks/wssystem.cob:L113] and the verb reaches an ISAM statement. Every
            migrated configuration takes the RDB branch instead.
        BridgeNotOpenError: If a verb other than ``fn-Open`` is issued before an open
            has succeeded.
    """
    aa_process_flat_file(
        system,
        posting,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )
