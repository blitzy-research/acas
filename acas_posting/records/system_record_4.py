"""The period-totals record `System-Record-4` [copybooks/wssys4.cob:L8].

One module, one copybook, field for field: a Sales group and a Purchase group of
ten `pic s9(8)v99 comp-3` fields each, then a 904-character filler, 1024 bytes in
all to match the system record.

This record is the fifth parameter of the Sales/Purchase linkage shape
[sales/sl060.cbl:L395-L399] and is absent from the General Ledger's four-parameter
shape [general/gl070.cbl:L245-L248] - which is exactly why the two shapes differ.

Its writers are the nine period-total sites in the Sales and Purchase programs
[sales/sl055.cbl:L675], [sales/sl055.cbl:L677], [sales/sl060.cbl:L641],
[sales/sl060.cbl:L700], [sales/sl100.cbl:L404], [purchase/pl055.cbl:L582],
[purchase/pl055.cbl:L584], [purchase/pl060.cbl:L628],
[purchase/pl100.cbl:L396], and nothing else writes it - which is what makes a
period-end scenario checkable in one table.

Two spare fields inside the PURCHASE group carry the Sales prefix -
`sl4-spare3` and `sl4-spare4` [copybooks/wssys4.cob:L29-L30], beside
`sl4-spare1` and `sl4-spare2` in the Sales group at L18-L19. The misnaming is
preserved: R-3 forbids renaming what the copybook declares.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Sorted, the way the sibling modules sort theirs.
    "PurchaseLedgerData",
    "SalesLedgerData",
    "SystemRecord4",
)


_COPYBOOK: Final[str] = "copybooks/wssys4.cob"
_RECORD: Final[str] = "System-Record-4"
_TABLE: Final[str] = "SYSTOT-REC"

# The two `03` headers that carry `comp-3` on behalf of all twenty children, at
# [copybooks/wssys4.cob:L9] and [copybooks/wssys4.cob:L20].
_SALES_GROUP: Final[str] = "Sales-Ledger-Data"
_PURCHASE_GROUP: Final[str] = "Purchase-Ledger-Data"


def _dictionary_keys() -> dict[str, str]:
    """Map each COBOL field name of this record to its dictionary key.

    Built by ASKING the loader and reading each entry's own `copybook.name`, never by
    composing a key from a rule.

    Returns:
        The COBOL field name of every item of this record, in either key space, mapped
            to the entry key that describes it.
    """
    keys: dict[str, str] = {}
    for entry in loader.entries_for_table(_TABLE):
        copybook = entry.copybook
        if copybook is None:
            # LEDGER-TOTALS-REC-KEY: present in the bridge and in the schema, absent
            # from every copybook, and produced at the bridge by `move 1 to HV-LEDGER-
            # TOTALS-REC-KEY` [common/sys4MT.cbl:L769].
            continue
        keys[copybook.name] = entry.key
    for entry in loader.entries_for_copybook_record(_RECORD):
        copybook = entry.copybook
        if copybook is None or copybook.file != _COPYBOOK:
            continue
        # setdefault, so the column-mapped key already found for a field wins over
        # anything the copybook-only pass could offer for the same name.
        keys.setdefault(copybook.name, entry.key)
    return keys


# Looked up once, at import, which is the only import-time work in this module beyond
# the dictionary's own lazy cached read (rule R-6).
_KEYS: Final[dict[str, str]] = _dictionary_keys()


def _describe(cobol_name: str) -> FieldDescriptor:
    """Return the storage description the dictionary holds for one field.

    Args:
        cobol_name: A COBOL field name of this record, verbatim from
            `copybooks/wssys4.cob` - `"sl4-spare3"`, `"filler"`, `"Sales-Ledger-Data"`.
            Case-sensitive, as every name in the dictionary is.

    Returns:
        Its descriptor, carrying the COPYBOOK view of digits, scale, sign, usage and
            Python carrier, plus the dictionary key and the copybook locator that make
            it traceable.

    Raises:
        KeyError: No item of this record is named so, which can only be a mis-typed name
            in this module or an artifact that no longer covers this copybook.
    """
    return FieldDescriptor.from_dictionary_key(_KEYS[cobol_name])


def _declaration_line(descriptor: FieldDescriptor) -> int:
    """Return the copybook line a field is declared on.

    This exists so that declaration order is DERIVED rather than restated.
    `loader.entries_for_copybook_record` returns document order, and for a table-backed
    record that is column ordinal order first with the copybook-only fields after it.

    Args:
        descriptor: A descriptor built from a dictionary entry.

    Returns:
        The line number its declaration begins on.
    """
    _, _, tail = str(descriptor.source_locator).rpartition(":L")
    return int(tail.partition("-")[0])


def _children_of(group: str) -> tuple[FieldDescriptor, ...]:
    """Describe the items one group of this record declares, in order.

    Order comes from the copybook, through `_declaration_line`, so the result is an
    independent witness to the hand-written attribute order of the class it belongs to
    rather than a restatement of it.

    Args:
        group: A group name verbatim from the copybook - `"Sales-Ledger-Data"`,
            `"Purchase-Ledger-Data"` or `"System-Record-4"` for the record's own three
            children.

    Returns:
        The descriptors of the items immediately subordinate to it, in copybook
            declaration order.
    """
    return tuple(
        sorted(
            (
                descriptor
                for descriptor in (_describe(name) for name in _KEYS)
                if descriptor.parent_group == group
            ),
            key=_declaration_line,
        )
    )


# The FILLER at [copybooks/wssys4.cob:L31] and the width it pads the record to.
_FILLER: Final[FieldDescriptor] = _describe("filler")
_FILLER_SPACES: Final[str] = " " * _FILLER.byte_length


@dataclass(slots=True)
class SalesLedgerData:
    """`03 Sales-Ledger-Data comp-3.` [copybooks/wssys4.cob:L9].

    Mutable on purpose, never frozen: the posting sites add into these fields and the
    record is then rewritten through handler `acas000`.
    """

    # Class-level traceability, not record fields.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _children_of(_SALES_GROUP)
    DESCRIPTOR: ClassVar[FieldDescriptor] = _describe(_SALES_GROUP)

    sl_os_bal_last_month: Decimal = Decimal("0.00")

    sl_os_bal_this_month: Decimal = Decimal("0.00")

    sl_invoices_this_month: Decimal = Decimal("0.00")

    sl_credit_notes_this_month: Decimal = Decimal("0.00")

    # sl-variance pic s9(8)v99 comp-3 inherited from Sales-Ledger-Data
    # [copybooks/wssys4.cob:L14] STORED, never computed. Nothing in the migrated cycle
    # writes it and nothing here derives it.
    sl_variance: Decimal = Decimal("0.00")

    sl_credit_deductions: Decimal = Decimal("0.00")

    sl_cn_unappl_this_month: Decimal = Decimal("0.00")

    sl_payments: Decimal = Decimal("0.00")

    # sl4-spare1 pic s9(8)v99 comp-3 inherited from Sales-Ledger-Data
    # [copybooks/wssys4.cob:L18] a spare the maintainer left in the Sales group, where
    # its `sl4-` prefix belongs.
    sl4_spare1: Decimal = Decimal("0.00")

    # sl4-spare2 pic s9(8)v99 comp-3 inherited from Sales-Ledger-Data
    # [copybooks/wssys4.cob:L19] the second Sales spare, column `SL4-SPARE2`
    # [mysql/ACASDB.sql:L1387].
    sl4_spare2: Decimal = Decimal("0.00")


#  THE PURCHASE HALF  [copybooks/wssys4.cob:L20-L30]  -  HOLDS ANOMALY A-20


@dataclass(slots=True)
class PurchaseLedgerData:
    """`03 Purchase-Ledger-Data comp-3.` [copybooks/wssys4.cob:L20].

    Four of the ten are accumulated by the migrated cycle. The layout is the Sales
    half's mirror in eight of its ten positions and diverges in two places, both
    preserved.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _children_of(
        _PURCHASE_GROUP
    )
    DESCRIPTOR: ClassVar[FieldDescriptor] = _describe(_PURCHASE_GROUP)

    pl_os_bal_last_month: Decimal = Decimal("0.00")

    pl_os_bal_this_month: Decimal = Decimal("0.00")

    pl_invoices_this_month: Decimal = Decimal("0.00")

    pl_credit_notes_this_month: Decimal = Decimal("0.00")

    # pl-variance pic s9(8)v99 comp-3 inherited from Purchase-Ledger-Data
    # [copybooks/wssys4.cob:L25] STORED, never computed, exactly like its Sales
    # counterpart. The out-of-scope roll-over zeroes it [common/xl150.cbl:L1998].
    pl_variance: Decimal = Decimal("0.00")

    # pl-credit-deductions pic s9(8)v99 comp-3 inherited from Purchase-Ledger-Data
    # [copybooks/wssys4.cob:L26] NEVER ACCUMULATED BY THE MIGRATED CYCLE, unlike the
    # Sales counterpart at [sales/sl060.cbl:L641].
    pl_credit_deductions: Decimal = Decimal("0.00")

    pl_cn_unappl_this_month: Decimal = Decimal("0.00")

    pl_payments: Decimal = Decimal("0.00")

    # sl4-spare3 pic s9(8)v99 comp-3 inherited from Purchase-Ledger-Data
    # [copybooks/wssys4.cob:L29] ANOMALY A-20, REPRODUCED AND NOT PUT RIGHT.
    sl4_spare3: Decimal = Decimal("0.00")

    # sl4-spare4 pic s9(8)v99 comp-3 inherited from Purchase-Ledger-Data
    # [copybooks/wssys4.cob:L30] ANOMALY A-20, REPRODUCED AND NOT PUT RIGHT - the second
    # of the pair, on the same terms as `sl4_spare3` above.
    sl4_spare4: Decimal = Decimal("0.00")


@dataclass(slots=True)
class SystemRecord4:
    """`01 System-Record-4.` [copybooks/wssys4.cob:L8].

    It reaches the twenty-one column table `SYSTOT-REC` through the `sys4MT` bridge and
    handler `acas000` on file-key number 4, and it reaches a program through LINKAGE as
    the third parameter of the Sales and Purchase posting shape
    [sales/sl055.cbl:L269-L275] - never by a file read of its own.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _children_of(_RECORD)
    DESCRIPTOR: ClassVar[FieldDescriptor] = _describe(_RECORD)

    sales_ledger_data: SalesLedgerData = field(
        default_factory=SalesLedgerData
    )

    # Purchase-Ledger-Data group, comp-3 declared here for its ten children, two of
    # which keep the Sales prefix - anomaly A-20 [copybooks/wssys4.cob:L20].
    purchase_ledger_data: PurchaseLedgerData = field(
        default_factory=PurchaseLedgerData
    )

    # filler pic x(904) alphanumeric, no usage clause [copybooks/wssys4.cob:L31] 904
    # bytes of padding, and nothing else.
    filler: str = _FILLER_SPACES
