"""The Purchase Ledger record: `WS-Purch-Record` from `copybooks/wspl.cob`.

One supplier account, laid out field for field from the frozen copybook with
nothing added and nothing dropped (R-3), descriptors looked up in the generated
dictionary (R-5).

The statistics fields are declared `binary-long` and are therefore Python `int`,
not exact decimals. That is not a simplification: `pl100`'s payment average
divides an integer accumulator by an integer counter
[purchase/pl100.cbl:L502], so integer truncation IS the arithmetic, and modelling
the fields as decimals would diverge on almost every payment. Its `divide … by`
and the Sales `divide … into` [sales/sl060.cbl:L827] compute the same
accumulator-over-activity quotient; only the guards differ.

Twelve of these fields are signed here and UNSIGNED at the bridge host variable
and the column, so a negative value loses its sign before any SQL runs. The loss
is reproduced where it happens - in
`acas_posting.dal.acas022_purch` - and the copybook view is reported here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# Two dictionary types, reached through the loader - the one door Agent Action Plan
# section 0.4.3 opens from this layer onto the dictionary package.
from acas_posting.dictionary.loader import ConditionName, DictionaryEntry

__all__ = (
    "BRIDGE",
    "COPYBOOK",
    "HANDLER",
    "PURCH_STATUS_CONDITION_NAMES",
    "TABLE",
    "PurchAddress",
    "Quarters",
    "QuartersView",
    "WsPurchRecord",
)


COPYBOOK: Final[str] = "copybooks/wspl.cob"
"""The frozen record layout this module mirrors. Read-only, never modified."""

TABLE: Final[str] = "PULEDGER-REC"
"""The MySQL table, 29 columns [mysql/ACASDB.sql:L646-L677]; its `PRIMARY KEY (PURCH-KEY)`
clause is at [mysql/ACASDB.sql:L676].
"""

HANDLER: Final[str] = "acas022"
"""The COBOL file handler the posting programs CALL [common/acas022.cbl]."""

BRIDGE: Final[str] = "purchMT"
"""The generated bridge program [common/purchMT.cbl]."""

# Provenance: descriptors are looked up, never transcribed (R-5)


def _locator(line: int) -> str:
    """Build the source locator for a declaration line of the frozen copybook.

    Produces exactly the `<file>:L<line>` form the generated dictionary and
    `FieldDescriptor.source_locator` both use, so a locator written here is matched
    against the artifact rather than merely resembling it.
    """
    return f"{COPYBOOK}:L{line}"


def _index_copybook() -> dict[tuple[str, str], DictionaryEntry]:
    """Index this copybook's generated entries by COBOL name and locator.

    Keying on the pair rather than the name alone matters: `copybooks/wspl.cob` declares
    `filler` twice, at L50 and L54, and the dictionary disambiguates them as `filler#50`
    and `filler#54`.
    """
    return {
        (entry.copybook.name, entry.copybook.source): entry
        for entry in loader.entries_for_copybook_file(COPYBOOK)
    }


_ENTRIES: Final[dict[tuple[str, str], DictionaryEntry]] = _index_copybook()
"""All 37 generated entries for this copybook - 29 table-backed, 8 one-sided."""


def _descriptor(cobol_name: str, locator: str) -> FieldDescriptor:
    """Look up one field's descriptor by its COBOL name and declaration line.

    The dictionary key is READ from the matching entry, never assembled from the Python
    attribute name. That distinction is load-bearing for this record.
    """
    return FieldDescriptor.from_dictionary_key(_ENTRIES[(cobol_name, locator)].key)


def _metadata(descriptor: FieldDescriptor) -> dict[str, FieldDescriptor]:
    """Attach a descriptor to an attribute so the field literally cites its entry."""
    return {"descriptor": descriptor}


def _zero(descriptor: FieldDescriptor) -> Decimal:
    """Build the zero of a numeric field, at the scale its descriptor reports.

    Built from the Decimal tuple form so the scale comes from the dictionary: a scale of
    2 yields Decimal('0.00'), which is the value a NOT NULL decimal(10,2) column holds
    for an initialised COBOL field.
    """
    return Decimal((0, (0,), -(descriptor.scale or 0)))


def _spaces(descriptor: FieldDescriptor) -> str:
    """Build an alphanumeric field's initialised value: spaces at the declared width.

    Spaces rather than an empty string, because that is what a `char(n)` column holds
    for an initialised COBOL field, and the width is read from the descriptor's
    `character_length` rather than counted by eye.
    """
    return " " * (descriptor.character_length or 0)


# Each builder below returns the keyword arguments for `dataclasses.field`, and every
# attribute then spells `field(**...)` itself. Calling `field` directly at the attribute
# is the sanctioned form.


def _text_spec(cobol_name: str, locator: str) -> dict[str, object]:
    """Build the field arguments for an alphanumeric attribute, spaces-defaulted."""
    descriptor = _descriptor(cobol_name, locator)
    return {"default": _spaces(descriptor), "metadata": _metadata(descriptor)}


def _int_spec(cobol_name: str, locator: str) -> dict[str, object]:
    """Build the field arguments for an integer attribute - zoned DISPLAY or binary."""
    descriptor = _descriptor(cobol_name, locator)
    return {"default": 0, "metadata": _metadata(descriptor)}


def _dec_spec(cobol_name: str, locator: str) -> dict[str, object]:
    """Build the field arguments for an exact-decimal attribute, zero at its scale."""
    descriptor = _descriptor(cobol_name, locator)
    return {"default": _zero(descriptor), "metadata": _metadata(descriptor)}


def _group_spec(
    cobol_name: str, locator: str, factory: Callable[[], object]
) -> dict[str, object]:
    """Build the field arguments for a group attribute, built fresh per record.

    `default_factory` rather than `default`, so every record owns its own subordinate
    group and two records can never share one.
    """
    descriptor = _descriptor(cobol_name, locator)
    return {"default_factory": factory, "metadata": _metadata(descriptor)}


def _pturnover_zeroes() -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Build the initialised `PTurnover-q ... occurs 4` view: four zeroes at scale 2."""
    zero = _zero(_descriptor("PTurnover-q", _locator(51)))
    return (zero, zero, zero, zero)


# Condition names.

PURCH_STATUS_CONDITION_NAMES: Final[tuple[ConditionName, ...]] = (
    _ENTRIES[("Purch-Status", _locator(18))].copybook.condition_names
)
"""The two 88-levels on `Purch-Status` [copybooks/wspl.cob:L19-L20]."""


@dataclass(slots=True)
class PurchAddress:
    """`03 Purch-Address.` [copybooks/wspl.cob:L23] - two lines, one column.

    The bridge concatenates this group into a single `HV-PURCH-ADDRESS PIC X(96)`
    [common/purchMT.cbl:L289] and the schema stores one `PURCH-ADDRESS char(96)`, so
    NEITHER child has a column of its own - drift KIND 3. Both are declared anyway.
    """

    GROUP_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor(
        "Purch-Address", _locator(23)
    )
    """The group's own descriptor - usage GROUP, keyed on PULEDGER-REC.PURCH-ADDRESS."""

    purch_addr1: str = field(**_text_spec("Purch-Addr1", _locator(24)))

    purch_addr2: str = field(**_text_spec("Purch-Addr2", _locator(25)))


@dataclass(slots=True)
class Quarters:
    """`03 Quarters.` [copybooks/wspl.cob:L45] - the four quarterly turnover figures.

    Two naming points are preserved rather than tidied.
    """

    GROUP_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor("Quarters", _locator(45))
    """The group's own descriptor - a one-sided copybook entry, usage GROUP."""

    turnover_q1: Decimal = field(**_dec_spec("Turnover-q1", _locator(46)))

    turnover_q2: Decimal = field(**_dec_spec("Turnover-q2", _locator(47)))

    turnover_q3: Decimal = field(**_dec_spec("Turnover-q3", _locator(48)))

    turnover_q4: Decimal = field(**_dec_spec("Turnover-q4", _locator(49)))


@dataclass(slots=True)
class QuartersView:
    """`03 filler redefines Quarters.` [copybooks/wspl.cob:L50] - the array view."""

    GROUP_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor("filler", _locator(50))
    """The unnamed redefining group's descriptor - is_filler and is_group both true."""

    # 05 PTurnover-q pic s9(8)v99 comp-3 occurs 4. [copybooks/wspl.cob:L51] A fixed
    # four-element tuple, never a list.
    pturnover_q: tuple[Decimal, Decimal, Decimal, Decimal] = field(
        **_group_spec("PTurnover-q", _locator(51), _pturnover_zeroes)
    )


@dataclass(slots=True)
class WsPurchRecord:
    """`01 WS-Purch-Record.` [copybooks/wspl.cob:L13] - one supplier account.

    Twenty-nine attributes in the copybook's own declaration order, L14 through L54,
    which is NOT the Sales record's order.
    """

    RECORD_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor(
        "WS-Purch-Record", _locator(13)
    )
    """The 01 level's own descriptor, keyed `WS-Purch-Record.WS-Purch-Record`."""

    # 03 WS-Purch-Key pic x(7). [copybooks/wspl.cob:L14] The primary key. Its only drift
    # is `name`: the column is PURCH-KEY, so the WS- prefix is dropped at the bridge.
    ws_purch_key: str = field(**_text_spec("WS-Purch-Key", _locator(14)))

    purch_status: int = field(**_int_spec("Purch-Status", _locator(18)))

    purch_notes_tag: int = field(**_int_spec("Purch-Notes-Tag", _locator(21)))

    purch_name: str = field(**_text_spec("Purch-Name", _locator(22)))

    purch_address: PurchAddress = field(
        **_group_spec("Purch-Address", _locator(23), PurchAddress)
    )

    purch_phone: str = field(**_text_spec("Purch-Phone", _locator(26)))

    purch_ext: str = field(**_text_spec("Purch-Ext", _locator(27)))

    purch_fax: str = field(**_text_spec("Purch-Fax", _locator(28)))

    purch_email: str = field(**_text_spec("Purch-Email", _locator(29)))

    # 03 Purch-Discount pic 99v99 comp. *> RDB comp-3 [copybooks/wspl.cob:L30] DECIMAL,
    # not int.
    purch_discount: Decimal = field(**_dec_spec("Purch-Discount", _locator(30)))

    purch_credit: int = field(**_int_spec("Purch-Credit", _locator(31)))

    # 03 Purch-SortCode binary-long. *> all these were pic 9(8) comp
    # [copybooks/wspl.cob:L32] int: SIGNED 32-BIT, no picture, scale 0.
    purch_sortcode: int = field(**_int_spec("Purch-SortCode", _locator(32)))

    purch_accountno: int = field(**_int_spec("Purch-Accountno", _locator(33)))

    purch_limit: int = field(**_int_spec("Purch-Limit", _locator(34)))

    # 03 Purch-Activety binary-long.
    purch_activety: int = field(**_int_spec("Purch-Activety", _locator(35)))

    purch_last_inv: int = field(**_int_spec("Purch-Last-inv", _locator(36)))

    purch_last_pay: int = field(**_int_spec("Purch-Last-pay", _locator(37)))

    # 03 Purch-Average binary-long. [copybooks/wspl.cob:L38] int, NOT Decimal - the
    # single most consequential type in this module.
    purch_average: int = field(**_int_spec("Purch-Average", _locator(38)))

    purch_create_date: int = field(**_int_spec("Purch-Create-Date", _locator(39)))

    # 03 Purch-Pay-Activety binary-long. [copybooks/wspl.cob:L40] MISSPELLED IN THE
    # SOURCE and carried verbatim, like L35. int, NOT Decimal.
    purch_pay_activety: int = field(**_int_spec("Purch-Pay-Activety", _locator(40)))

    # 03 Purch-Pay-Average binary-long. [copybooks/wspl.cob:L41] int, NOT Decimal.
    purch_pay_average: int = field(**_int_spec("Purch-Pay-Average", _locator(41)))

    purch_pay_worst: int = field(**_int_spec("Purch-Pay-Worst", _locator(42)))

    purch_current: Decimal = field(**_dec_spec("Purch-Current", _locator(43)))

    purch_last: Decimal = field(**_dec_spec("Purch-Last", _locator(44)))

    quarters: Quarters = field(
        **_group_spec("Quarters", _locator(45), Quarters)
    )

    quarters_view: QuartersView = field(
        **_group_spec("filler", _locator(50), QuartersView)
    )

    purch_unapplied: Decimal = field(**_dec_spec("Purch-Unapplied", _locator(52)))

    # 03 Purch-Stats-Date pic 9(4). *> added 15/01/18. [copybooks/wspl.cob:L53] Reaches
    # NO host variable and NO column: the dictionary entry records it copybook-only rather
    # than searching for a carrier it does not have.
    purch_stats_date: int = field(**_int_spec("Purch-Stats-Date", _locator(53)))

    # 03 filler pic x(12). [copybooks/wspl.cob:L54] The trailing FILLER, declared rather
    # than skipped: it is part of the 302 declared bytes and R-3 forbids dropping it.
    filler_l54: str = field(**_text_spec("filler", _locator(54)))
