"""The General/Nominal Ledger account record `01 WS-Ledger-Record`.

A field-for-field CREATE from `copybooks/wsledger.cob`: the account key, its
name, the running `Ledger-Balance pic s9(8)v99 comp-3` that `gl072` accumulates
into, and the quarter table `gl080` writes.

Two drifts at the bridge boundary are recorded rather than adjusted. The ledger
name is 24 characters in the copybook and 32 at both the host variable
[common/nominalMT.cbl:L299] and the column, so the value is unharmed but the
padding differs - which is why comparing table dumps canonicalises trailing
spaces. The balance is signed at all three layers and passes through cleanly.

The account is located by `gl072` with a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so this record's arrival order - not
its key - is what makes the posting land on the right account.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[tuple[str, ...]] = (
    "LedgerQuarters",
    "LedgerQuartersTable",
    "WsLedgerKey",
    "WsLedgerKey9",
    "WsLedgerNosParts",
    "WsLedgerRecord",
)


# One descriptor per copybook item, in declaration order, each naming its own dictionary
# key.

_WS_LEDGER_RECORD: Final[FieldDescriptor] = (
    FieldDescriptor.from_dictionary_key("WS-Ledger-Record.WS-Ledger-Record")
)

_WS_LEDGER_KEY: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Key"
)

_WS_LEDGER_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Nos"
)

_WS_LEDGER_NOS_REDEFINES: Final[FieldDescriptor] = (
    FieldDescriptor.from_dictionary_key("WS-Ledger-Record.filler#16")
)

_LEDGER_N: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-n"
)

_LEDGER_S: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-s"
)

_LEDGER_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-PC"
)

# 03 WS-Ledger-Key9 redefines WS-Ledger-Key [:L21-L22] pic 9(8). TWO PHYSICAL LINES, ONE
# DECLARATION. L21 carries the name and the REDEFINES clause.
_WS_LEDGER_KEY9: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-KEY"
)

_LEDGER_TYPE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-TYPE"
)

_LEDGER_PLACE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-PLACE"
)

_LEDGER_LEVEL: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-LEVEL"
)

# 03 filler pic x(5). [:L26] Five bytes of real storage with NO MySQL column. Declared
# because R-3 has these modules mirror the copybook field for field.
_FILLER_L26: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.filler#26"
)

# 03 Ledger-Name pic x(24). [:L27] ANOMALY A-12. Twenty-four characters here, thirty-two
# at the bridge host variable [common/nominalMT.cbl:L299] and thirty-two at the column
# [mysql/ACASDB.sql:L127].
_LEDGER_NAME: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-NAME"
)

# Six fields, every one `pic s9(8)v99 comp-3` with the usage on its OWN line: signed,
# ten digits, scale two, packed into six bytes each.

# 03 Ledger-Balance pic s9(8)v99 comp-3. [:L28] THE ACCUMULATOR THE WHOLE GENERAL LEDGER
# CYCLE WRITES INTO. gl072 adds each posting into it.
_LEDGER_BALANCE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

_LEDGER_LAST: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-LAST"
)

_QUARTERS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Quarters"
)

_LEDGER_Q1: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q1"
)
_LEDGER_Q2: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q2"
)
_LEDGER_Q3: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q3"
)
_LEDGER_Q4: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q4"
)

_QUARTERS_REDEFINES: Final[FieldDescriptor] = (
    FieldDescriptor.from_dictionary_key("WS-Ledger-Record.filler#35")
)

# 05 Ledger-Q pic s9(8)v99 comp-3 occurs 4. [:L36] The same twenty-four bytes as
# Ledger-Q1..Q4, addressed as a table. Carries `occurs == 4`.
_LEDGER_Q: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-Q"
)

_FILLER_L37: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.filler#37"
)


@dataclass(slots=True)
class WsLedgerNosParts:
    """The two-part view of `WS-Ledger-Nos`: a nominal number and a sub-code.

    NAMING. The COBOL original is ANONYMOUS - `05 filler redefines WS-Ledger-Nos.`
    [copybooks/wsledger.cob:L16] - so this class needed a name that the copybook does
    not supply.
    """

    # The anonymous group that carries the REDEFINES clause, kept so the redefinition is
    # readable from the class that represents it.
    REDEFINES: ClassVar[FieldDescriptor] = _WS_LEDGER_NOS_REDEFINES
    LEDGER_N: ClassVar[FieldDescriptor] = _LEDGER_N
    LEDGER_S: ClassVar[FieldDescriptor] = _LEDGER_S
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_LEDGER_N, _LEDGER_S)

    ledger_n: int = 0

    ledger_s: int = 0


@dataclass(slots=True)
class WsLedgerKey:
    """`WS-Ledger-Key` - the eight bytes that identify a nominal account.

    WHY THE GROUP SHAPE MATTERS BEHAVIOURALLY. `gl072` moves a whole eight-digit group
    into this one in a single statement - `move post-ledger to WS-Ledger-Key`
    [general/gl072.cbl:L405] - where `post-ledger` combines `post-ac pic 9(6)` with
    `post-pc pic 99` [general/gl072.cbl:L115].
    """

    GROUP: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY
    WS_LEDGER_NOS: ClassVar[FieldDescriptor] = _WS_LEDGER_NOS
    LEDGER_PC: ClassVar[FieldDescriptor] = _LEDGER_PC
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_LEDGER_NOS,
        _WS_LEDGER_NOS_REDEFINES,
        _LEDGER_N,
        _LEDGER_S,
        _LEDGER_PC,
    )

    ws_ledger_nos: int = 0

    # 05 filler redefines WS-Ledger-Nos. [:L16-L18] The alternate two-part view of the
    # six digits above. Separate storage in Python.
    ws_ledger_nos_parts: WsLedgerNosParts = field(
        default_factory=WsLedgerNosParts
    )

    ledger_pc: int = 0


@dataclass(slots=True)
class WsLedgerKey9:
    """`WS-Ledger-Key9` - the same eight bytes read as one eight-digit number.

    From `03 WS-Ledger-Key9 redefines WS-Ledger-Key` [:L21] continued by `pic 9(8).`
    [:L22]. TWO PHYSICAL LINES, ONE DECLARATION.
    """

    WS_LEDGER_KEY9: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY9
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_WS_LEDGER_KEY9,)

    # 03 WS-Ledger-Key9 redefines WS-Ledger-Key pic 9(8). [:L21-L22] DISPLAY, unsigned,
    # 8 digits, scale 0, redefines WS-Ledger-Key.
    ws_ledger_key9: int = 0


# The zero every money field starts at: signed, scale two, exact.
_MONEY_ZERO: Final[Decimal] = Decimal("0.00")

# The quarter table's default, built deterministically in index order and as a TUPLE
# because R-6 makes a fixed collection immutable.
_QUARTER_TABLE_ZERO: Final[tuple[Decimal, ...]] = tuple(
    _MONEY_ZERO for _ in range(_LEDGER_Q.occurs or 0)
)


@dataclass(slots=True)
class LedgerQuarters:
    """The four quarterly balances, addressed by name.

    NAMING. The COBOL original is `03 Quarters.` [copybooks/wsledger.cob:L30].
    """

    GROUP: ClassVar[FieldDescriptor] = _QUARTERS
    LEDGER_Q1: ClassVar[FieldDescriptor] = _LEDGER_Q1
    LEDGER_Q2: ClassVar[FieldDescriptor] = _LEDGER_Q2
    LEDGER_Q3: ClassVar[FieldDescriptor] = _LEDGER_Q3
    LEDGER_Q4: ClassVar[FieldDescriptor] = _LEDGER_Q4
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _LEDGER_Q1,
        _LEDGER_Q2,
        _LEDGER_Q3,
        _LEDGER_Q4,
    )

    ledger_q1: Decimal = _MONEY_ZERO

    ledger_q2: Decimal = _MONEY_ZERO

    ledger_q3: Decimal = _MONEY_ZERO

    ledger_q4: Decimal = _MONEY_ZERO


@dataclass(slots=True)
class LedgerQuartersTable:
    """The same four quarterly balances, addressed as an OCCURS 4 table.

    NAMING. The COBOL original is ANONYMOUS - `03 filler redefines Quarters.`
    [copybooks/wsledger.cob:L35] - holding one subordinate, `05 Ledger-Q pic s9(8)v99
    comp-3 occurs 4.` [:L36].
    """

    REDEFINES: ClassVar[FieldDescriptor] = _QUARTERS_REDEFINES
    LEDGER_Q: ClassVar[FieldDescriptor] = _LEDGER_Q
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_LEDGER_Q,)

    # 05 Ledger-Q pic s9(8)v99 comp-3 occurs 4. [:L36] COMP-3, signed, 10 digits, scale
    # 2, four occurrences.
    ledger_q: tuple[Decimal, ...] = _QUARTER_TABLE_ZERO


@dataclass(slots=True)
class WsLedgerRecord:
    """`WS-Ledger-Record` - one General/Nominal Ledger account, 126 bytes.

    A field-for-field mirror of `01 WS-Ledger-Record.` [copybooks/wsledger.cob:L12],
    declared in copybook order from L13 through L37 so that this class can be set beside
    the copybook and diffed by eye.
    """

    RECORD: ClassVar[FieldDescriptor] = _WS_LEDGER_RECORD
    WS_LEDGER_KEY: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY
    WS_LEDGER_KEY9: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY9
    LEDGER_TYPE: ClassVar[FieldDescriptor] = _LEDGER_TYPE
    LEDGER_PLACE: ClassVar[FieldDescriptor] = _LEDGER_PLACE
    LEDGER_LEVEL: ClassVar[FieldDescriptor] = _LEDGER_LEVEL
    FILLER_L26: ClassVar[FieldDescriptor] = _FILLER_L26
    LEDGER_NAME: ClassVar[FieldDescriptor] = _LEDGER_NAME
    LEDGER_BALANCE: ClassVar[FieldDescriptor] = _LEDGER_BALANCE
    LEDGER_LAST: ClassVar[FieldDescriptor] = _LEDGER_LAST
    QUARTERS: ClassVar[FieldDescriptor] = _QUARTERS
    FILLER_L37: ClassVar[FieldDescriptor] = _FILLER_L37

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_LEDGER_KEY,
        _WS_LEDGER_NOS,
        _WS_LEDGER_NOS_REDEFINES,
        _LEDGER_N,
        _LEDGER_S,
        _LEDGER_PC,
        _WS_LEDGER_KEY9,
        _LEDGER_TYPE,
        _LEDGER_PLACE,
        _LEDGER_LEVEL,
        _FILLER_L26,
        _LEDGER_NAME,               # L27  ANOMALY A-12
        _LEDGER_BALANCE,
        _LEDGER_LAST,
        _QUARTERS,
        _LEDGER_Q1,
        _LEDGER_Q2,
        _LEDGER_Q3,
        _LEDGER_Q4,
        _QUARTERS_REDEFINES,
        _LEDGER_Q,
        _FILLER_L37,
    )

    # The eleven that reach GLLEDGER-REC, in declaration order.
    COLUMN_MAPPED_FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = tuple(
        descriptor
        for descriptor in FIELDS
        if descriptor.dictionary_key is not None
        and descriptor.dictionary_key.startswith("GLLEDGER-REC.")
    )


    ws_ledger_key: WsLedgerKey = field(default_factory=WsLedgerKey)

    # 03 WS-Ledger-Key9 redefines WS-Ledger-Key pic 9(8). [:L21-L22] THE FIELD BEHIND
    # THE LEDGER-KEY COLUMN. Two physical lines, one declaration.
    ws_ledger_key9: WsLedgerKey9 = field(default_factory=WsLedgerKey9)

    ledger_type: int = 0

    ledger_place: str = " " * (_LEDGER_PLACE.character_length or 0)

    ledger_level: int = 0

    # 03 filler pic x(5). [:L26] FIVE BYTES WITH NO MYSQL COLUMN, declared because R-3
    # requires a complete mirror. Keyed `WS-Ledger-Record.filler#26`; its descriptor
    # reports `is_filler` True.
    filler_l26: str = " " * (_FILLER_L26.character_length or 0)

    # 03 Ledger-Name pic x(24). [:L27] ANOMALY A-12 - REPRODUCED HERE, NOT FIXED (R-4).
    ledger_name: str = " " * (_LEDGER_NAME.character_length or 0)

    # 03 Ledger-Balance pic s9(8)v99 comp-3. [:L28] COMP-3, SIGNED, 10 digits, scale 2.
    # -> LEDGER-BALANCE decimal(10,2). each posting into it. Decimal, exact, never
    # binary floating point (R-2).
    ledger_balance: Decimal = _MONEY_ZERO

    ledger_last: Decimal = _MONEY_ZERO

    quarters: LedgerQuarters = field(default_factory=LedgerQuarters)

    # 03 filler redefines Quarters. [:L35-L36] The same twenty-four bytes as an OCCURS 4
    # table. No column. Separate storage from `quarters` here.
    quarters_table: LedgerQuartersTable = field(
        default_factory=LedgerQuartersTable
    )

    filler_l37: str = " " * (_FILLER_L37.character_length or 0)
