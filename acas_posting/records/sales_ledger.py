"""`WS-Sales-Record` - the Sales Ledger customer account, field for field.

A CREATE from `copybooks/wssl.cob`, descriptors looked up in the generated
dictionary (R-5), nothing added and nothing dropped (R-3).

The statistics fields are declared `binary-long`
[copybooks/wssl.cob:L45-L53] and are therefore Python `int`, while the two money
fields [copybooks/wssl.cob:L54-L55] are `comp-3` and exact decimals. The
distinction is what makes `sl060`'s moving average reproducible:
`Sales-Average` is an integer [copybooks/wssl.cob:L49], so the divide that stores
into it truncates [sales/sl060.cbl:L827] - and the accumulator it divides has
zero decimal places [sales/sl060.cbl:L206] while the value added into it carries
two [sales/sl060.cbl:L218], so pence are already gone. Two truncations, both
reproduced.

Eleven fields are signed here and UNSIGNED at the bridge host variable and the
column [common/salesMT.cbl:L305-L312], so a negative value loses its sign before
any SQL runs. That loss is reproduced where it happens, in
`acas_posting.dal.acas012_sales`; this module reports the copybook view.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# `ConditionName` alone, taken from the loader - the one door Agent Action Plan section
# 0.4.3 opens from this layer onto the dictionary package.
from acas_posting.dictionary.loader import ConditionName

# Ordered by plain string comparison, so `tuple(__all__) == tuple(sorted(...))` holds
# and a test can assert it in one line.
__all__: Final[tuple[str, ...]] = (
    "BRIDGE_PROGRAM",
    "CONDITION_NAMES",
    "COPYBOOK_FILE",
    "COPYBOOK_RECORD",
    "DICTIONARY_KEYS",
    "ENTITY_FACADE",
    "FIELD_DESCRIPTORS",
    "FILE_HANDLER",
    "MYSQL_TABLE",
    "Quarters",
    "QuartersView",
    "RECORD_KEY",
    "SalesAddress",
    "WsSalesRecord",
)


ENTITY_FACADE: Final[str] = "Sales"
"""The entity facade name in `copybooks/Proc-ACAS-FH-Calls.cob`.

The facade publishes the twelve-verb vocabulary for this entity - Open, Open-Input,
Open-Output, Open-Extend, Close, Start, Read-Next, Read-Indexed, Write, Rewrite, Delete,
Delete-All. Recorded for traceability only; this module calls none of them and never
reaches the data-access layer.
"""

FILE_HANDLER: Final[str] = "acas012"
"""The numbered handler program the posting steps CALL for this entity.

Reproduced by the `acas012` handler module [common/acas012.cbl].
"""

BRIDGE_PROGRAM: Final[str] = "salesMT"
"""The generated bridge program that owns this table's SQL."""

MYSQL_TABLE: Final[str] = "SALEDGER-REC"
"""The frozen table name, spelt as `mysql/ACASDB.sql` spells it."""

COPYBOOK_FILE: Final[str] = "copybooks/wssl.cob"
"""The frozen copybook this module is a CREATE from - 68 lines, read-only."""

COPYBOOK_RECORD: Final[str] = "WS-Sales-Record"
"""The `01`-level record name, spelt as the copybook spells it."""

RECORD_KEY: Final[str] = "WS-Sales-Record.WS-Sales-Record"
"""The dictionary key of the `01`-level group itself.

A group has no storage of its own, so this entry's Python carrier is NONE and its
descriptor answers `is_group`. Held here rather than in `DICTIONARY_KEYS` because the
`01` level is the class, not one of its attributes.
"""


# The traceability table the migration's own document lifts, and the ONLY place here a
# key appears. Left half: the dotted attribute path rooted at `WsSalesRecord`.

_FIELD_KEYS: Final[tuple[tuple[str, str], ...]] = (
    ("ws_sales_key", "SALEDGER-REC.SALES-KEY"),
    ("sales_name", "SALEDGER-REC.SALES-NAME"),
    ("sales_address", "SALEDGER-REC.SALES-ADDRESS"),
    ("sales_address.sales_addr1", "WS-Sales-Record.Sales-Addr1"),
    ("sales_address.sales_addr2", "WS-Sales-Record.Sales-Addr2"),
    ("sales_phone", "SALEDGER-REC.SALES-PHONE"),
    ("sales_ext", "SALEDGER-REC.SALES-EXT"),
    ("sales_email", "SALEDGER-REC.SALES-EMAIL"),
    ("sales_fax", "SALEDGER-REC.SALES-FAX"),
    ("sales_status", "SALEDGER-REC.SALES-STATUS"),
    ("sales_late", "SALEDGER-REC.SALES-LATE"),
    ("sales_dunning", "SALEDGER-REC.SALES-DUNNING"),
    ("email_invoice", "SALEDGER-REC.EMAIL-INVOICE"),
    ("email_statement", "SALEDGER-REC.EMAIL-STATEMENT"),
    ("email_letters", "SALEDGER-REC.EMAIL-LETTERS"),
    ("delivery_tag", "SALEDGER-REC.DELIVERY-TAG"),
    ("notes_tag", "SALEDGER-REC.NOTES-TAG"),
    ("filler_l40", "WS-Sales-Record.filler#40"),
    ("sales_credit", "SALEDGER-REC.SALES-CREDIT"),
    ("sales_discount", "SALEDGER-REC.SALES-DISCOUNT"),
    ("sales_late_min", "SALEDGER-REC.SALES-LATE-MIN"),
    ("sales_late_max", "SALEDGER-REC.SALES-LATE-MAX"),
    ("sales_limit", "SALEDGER-REC.SALES-LIMIT"),
    ("sales_activety", "SALEDGER-REC.SALES-ACTIVETY"),
    ("sales_last_inv", "SALEDGER-REC.SALES-LAST-INV"),
    ("sales_last_pay", "SALEDGER-REC.SALES-LAST-PAY"),
    ("sales_average", "SALEDGER-REC.SALES-AVERAGE"),
    ("sales_pay_activety", "SALEDGER-REC.SALES-PAY-ACTIVETY"),
    ("sales_pay_average", "SALEDGER-REC.SALES-PAY-AVERAGE"),
    ("sales_pay_worst", "SALEDGER-REC.SALES-PAY-WORST"),
    ("sales_create_date", "SALEDGER-REC.SALES-CREATE-DAT"),
    ("sales_current", "SALEDGER-REC.SALES-CURRENT"),
    ("sales_last", "SALEDGER-REC.SALES-LAST"),
    ("quarters", "WS-Sales-Record.Quarters"),
    ("quarters.turnover_q1", "SALEDGER-REC.TURNOVER-Q1"),
    ("quarters.turnover_q2", "SALEDGER-REC.TURNOVER-Q2"),
    ("quarters.turnover_q3", "SALEDGER-REC.TURNOVER-Q3"),
    ("quarters.turnover_q4", "SALEDGER-REC.TURNOVER-Q4"),
    ("quarters_view", "WS-Sales-Record.filler#61"),
    ("quarters_view.sturnover_q", "WS-Sales-Record.STurnover-Q"),
    ("sales_unapplied", "SALEDGER-REC.SALES-UNAPPLIED"),
    ("sales_stats_date", "SALEDGER-REC.SALES-STATS-DATE"),
    ("sales_partial_ship_flag", "SALEDGER-REC.SALES-PARTIAL-SHIP-FLAG"),
    ("filler_l68", "WS-Sales-Record.filler#68"),
)

DICTIONARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    dict(_FIELD_KEYS)
)
"""Dotted attribute path to dictionary key, in copybook declaration order."""

FIELD_DESCRIPTORS: Final[Mapping[str, FieldDescriptor]] = MappingProxyType(
    {
        path: FieldDescriptor.from_dictionary_key(key)
        for path, key in _FIELD_KEYS
    }
)
"""Dotted attribute path to `FieldDescriptor`, in declaration order.

The disagreement between the three layers is reached from a descriptor by `drift()`, and
its registered references by `anomaly_refs()` and `ambiguity_refs()`. For the eleven
narrowed binary fields those answer `('A-11',)` and `()` - the anomaly is published
because the sign loss is reproduced rather than repaired, and no ambiguity is
published because question `Q-3`, what the unsigned column then holds, has been
measured on the compiled oracle. For the money fields both answer `()`.
"""


def _condition_names(
    field_keys: tuple[tuple[str, str], ...] = _FIELD_KEYS,
) -> Mapping[str, tuple[ConditionName, ...]]:
    """Collect the `88`-level condition names the copybook declares.

    Each item's copybook view is asked for the condition names it already carries, so
    every name, its value-clause text and its locator are DERIVED from the dictionary
    rather than retyped here (rule R-5).

    Args:
        field_keys: Attribute-path and dictionary-key pairs to read, in declaration
            order. Defaults to this record's own 44 pairs.

    Returns:
        A read-only mapping of dotted attribute path to the tuple of `ConditionName`
            triples declared on that item.
    """
    collected: dict[str, tuple[ConditionName, ...]] = {}
    for path, key in field_keys:
        copybook_field = loader.copybook_field_for(key)
        if copybook_field is None:
            continue
        declared = tuple(copybook_field.condition_names)
        if declared:
            collected[path] = declared
    return MappingProxyType(collected)


CONDITION_NAMES: Final[Mapping[str, tuple[ConditionName, ...]]] = (
    _condition_names()
)
"""Dotted attribute path to the `88`-level condition names declared on it.

Seven entries carrying eight condition names between them, in declaration order, taken
from the dictionary rather than restated. `Sales-Status` carries two
[copybooks/wssl.cob:L26-L27]; the other six carry one each.
"""


# The bridge's load paragraph opens with `initialize TD-SALEDGER-REC.`
# [common/salesMT.cbl:L1204], so an unset field reaches SQL as zero or space and never
# as NULL, and all 37 columns are NOT NULL with no column default
# [mysql/ACASDB.sql:L945-L984].

_ZERO_MONEY: Final[Decimal] = Decimal("0.00")
"""Zero at scale 2, the scale every `comp-3` money field here declares.

Written as a string literal so the value is exact and its scale explicit; `Decimal`
never sees a binary floating-point value anywhere in this package (rule R-2).
"""

_QUARTER_ZEROS: Final[tuple[Decimal, Decimal, Decimal, Decimal]] = (
    _ZERO_MONEY,
    _ZERO_MONEY,
    _ZERO_MONEY,
    _ZERO_MONEY,
)
"""The four-element default for `STurnover-Q`, whose OCCURS is 4.

A tuple, so it is immutable and safe as a dataclass default, and so that two runs cannot
differ through a shared mutable default (rule R-6).
"""


def _spaces(path: str) -> str:
    """SPACES at the width the copybook declares for one field.

    The width is read from the field's own `FieldDescriptor`, so it is never retyped in
    this module and cannot drift from the copybook. Called only while the classes below
    are being defined, to build a default.

    Args:
        path: A dotted attribute path, as `DICTIONARY_KEYS` keys them.

    Returns:
        A string of that many spaces.
    """
    width = FIELD_DESCRIPTORS[path].character_length
    return " " * width if width is not None else ""


@dataclass(slots=True)
class SalesAddress:
    """`03 Sales-Address.` [copybooks/wssl.cob:L18] - two lines of address.

    A COBOL group of two 48-character children [copybooks/wssl.cob:L19-L20]. The group
    is what the bridge and the schema see: ONE `HV-SALES-ADDRESS PIC X(96)`
    [common/salesMT.cbl:L287], moved whole by `move Sales-ADDRESS to HV-SALES-ADDRESS`
    [common/salesMT.cbl:L1207], into ONE `SALES-ADDRESS char(96)` column
    [mysql/ACASDB.sql:L948].

    Attributes:
        sales_addr1: First address line, 48 characters.
        sales_addr2: Second address line, 48 characters.
    """

    sales_addr1: str = _spaces("sales_address.sales_addr1")

    sales_addr2: str = _spaces("sales_address.sales_addr2")


@dataclass(slots=True)
class Quarters:
    """`03 Quarters.` [copybooks/wssl.cob:L56] - four quarterly turnovers.

    Each child is `pic s9(8)v99 comp-3` [copybooks/wssl.cob:L57-L60]: packed decimal,
    ten digits, scale 2, SIGNED - and signed at all three layers, `PIC S9(08)V9(02)
    COMP` in the bridge [common/salesMT.cbl:L315-L318] and `decimal(10,2)` in the schema
    [mysql/ACASDB.sql:L976-L979].

    Attributes:
        turnover_q1: First quarter's turnover.
        turnover_q2: Second quarter's turnover.
        turnover_q3: Third quarter's turnover.
        turnover_q4: Fourth quarter's turnover.
    """

    turnover_q1: Decimal = _ZERO_MONEY

    turnover_q2: Decimal = _ZERO_MONEY

    turnover_q3: Decimal = _ZERO_MONEY

    turnover_q4: Decimal = _ZERO_MONEY


@dataclass(slots=True)
class QuartersView:
    """`03 filler redefines Quarters.` [copybooks/wssl.cob:L61] as a table.

    THE COBOL GROUP HAS NO NAME. It is declared as an unnamed `filler` that redefines
    `Quarters`, so `QuartersView` is a Python name for something the copybook does not
    name at all.

    Attributes:
        sturnover_q: The four turnovers as a fixed four-element tuple.
    """

    sturnover_q: tuple[Decimal, Decimal, Decimal, Decimal] = _QUARTER_ZEROS


@dataclass(slots=True)
class WsSalesRecord:
    """`01 WS-Sales-Record.` [copybooks/wssl.cob:L12] - a customer account.

    37 attributes in copybook declaration order, L13 through L68, backed by the 37
    columns of `SALEDGER-REC` [mysql/ACASDB.sql:L945-L984] through handler `acas012` and
    bridge `salesMT`, and rewritten in place by `sl055`, `sl060` and `sl100`.

    Attributes:
        ws_sales_key: `pic x(7)` - account key and the table's primary key.
        sales_name: `pic x(30)` - the customer name.
        sales_address: Two-line group; both children share ONE 96-char column.
        sales_phone: `pic x(13)`.
        sales_ext: `pic x(4)` - telephone extension.
        sales_email: `pic x(30)`.
        sales_fax: `pic x(13)`.
        sales_status: `pic 9` - live or dead. Carries two condition names.
        sales_late: `pic 9` - late-charge switch.
        sales_dunning: `pic 9` - reminder-letter switch.
        email_invoice: `pic 9` - e-mail the invoice.
        email_statement: `pic 9` - e-mail the statement.
        email_letters: `pic 9` - e-mail the reminder letters.
        delivery_tag: `pic 9` - a field of THIS table, not the delivery table.
        notes_tag: `pic 9`.
        filler_l40: FILLER, three characters, no column.
        sales_credit: `pic 99` - credit period in days.
        sales_discount: `pic 99v99 comp` - `Decimal`, scale 2, unsigned.
        sales_late_min: `binary-short` - `int`, signed 16-bit.
        sales_late_max: `binary-short` - `int`, signed 16-bit.
        sales_limit: `binary-long` - `int`, signed 32-bit.
        sales_activety: `binary-long` - `int`. Misspelt everywhere; A-9.
        sales_last_inv: `binary-long` - `int`, a day number.
        sales_last_pay: `binary-long` - `int`, a day number.
        sales_average: `binary-long` - `int`. A-11, and A-8's truncation.
        sales_pay_activety: `binary-long` - `int`. Misspelt as above.
        sales_pay_average: `binary-long` - `int`.
        sales_pay_worst: `binary-long` - `int`, a watermark.
        sales_create_date: `binary-long` - `int`. Column drops the trailing `E`.
        sales_current: `pic s9(8)v99 comp-3` - `Decimal`, signed, scale 2.
        sales_last: `pic s9(8)v99 comp-3` - `Decimal`, signed, scale 2.
        quarters: The four named quarterly turnovers.
        quarters_view: The same 24 bytes as a four-element table.
        sales_unapplied: `pic s9(8)v99 comp-3` - `Decimal`, signed, scale 2.
        sales_stats_date: `pic 9(4)` - NUMERIC declared, `int` here, `char(4)`.
        sales_partial_ship_flag: `pic x` - back-order switch, two lines.
        filler_l68: FILLER, five characters, no column.
    """

    ws_sales_key: str = _spaces("ws_sales_key")

    sales_name: str = _spaces("sales_name")

    sales_address: SalesAddress = field(default_factory=SalesAddress)

    sales_phone: str = _spaces("sales_phone")

    sales_ext: str = _spaces("sales_ext")

    sales_email: str = _spaces("sales_email")

    sales_fax: str = _spaces("sales_fax")

    sales_status: int = 0

    sales_late: int = 0

    sales_dunning: int = 0

    email_invoice: int = 0

    email_statement: int = 0

    email_letters: int = 0

    delivery_tag: int = 0

    notes_tag: int = 0

    # `03 filler pic xxx.` L40 COBOL name is `filler`; the width is spelt as three `x`
    # characters rather than `x(3)`, and is recorded that way.
    filler_l40: str = _spaces("filler_l40")

    sales_credit: int = 0

    # `03 Sales-Discount pic 99v99 comp.` L42 `comp` WITH a `V`, so `Decimal` at scale 2
    # and NOT `int`. Four digits, unsigned; column `SALES-DISCOUNT decimal(4,2)
    # unsigned` [mysql/ACASDB.sql:L962].
    sales_discount: Decimal = _ZERO_MONEY

    # Every one is signed at the copybook and unsigned from the bridge onwards
    # [common/salesMT.cbl:L302-L312] - anomaly A-11. Question Q-3, what the unsigned
    # column then holds, is MEASURED: the absolute value, magnitude first and any
    # high-order truncation second.
    sales_late_min: int = 0

    sales_late_max: int = 0

    sales_limit: int = 0

    # `03 Sales-Activety binary-long. *> 9(8) comp` L46 STALE comment, as L45.
    sales_activety: int = 0

    sales_last_inv: int = 0

    sales_last_pay: int = 0

    # `03 Sales-Average binary-long. *> 9(8) comp` L49 STALE comment, as L45. THE
    # TEXTBOOK CASE OF A-11, and the single most consequential type in this folder.
    sales_average: int = 0

    sales_pay_activety: int = 0

    # `03 Sales-Pay-Average binary-long. *> 9(8) comp` L51 STALE comment, as L45.
    sales_pay_average: int = 0

    sales_pay_worst: int = 0

    # `03 Sales-Create-Date binary-long. *> 9(8) comp` L53 STALE comment, as L45. NAME
    # TRUNCATION at the bridge.
    sales_create_date: int = 0

    sales_current: Decimal = _ZERO_MONEY

    sales_last: Decimal = _ZERO_MONEY

    quarters: Quarters = field(default_factory=Quarters)

    # `03 filler redefines Quarters.` L61 Declared second because the copybook declares
    # it second. It describes the SAME 24 bytes as `quarters`.
    quarters_view: QuartersView = field(default_factory=QuartersView)

    sales_unapplied: Decimal = _ZERO_MONEY

    # `03 Sales-Stats-Date pic 9(4). *> added 15/01/18.` L64 TYPE-CLASS DRIFT, numeric
    # to character, and the only instance of it in this folder.
    sales_stats_date: int = 0

    # `03 Sales-Partial-Ship-Flag` L65 ` pic x. *> added 06/02/24` L66 A line-oriented
    # reader takes L65 for a group and loses the PICTURE entirely.
    sales_partial_ship_flag: str = _spaces("sales_partial_ship_flag")

    # `03 filler pic x(5).` L68 COBOL name is `filler`; named for its line number here,
    # as at L40. Five characters, no column.
    filler_l68: str = _spaces("filler_l68")
