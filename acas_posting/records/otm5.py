"""The Purchase open-item record - OTM5, `PUITM5-REC`.

The purchase ledger's unpaid-item register, mirrored field for field from
`copybooks/plwsoi5B.cob` and `copybooks/plwsoi5C.cob`. `pl060` writes and applies
these rows; `pl100` clears them and reads `OI-Date` against `OI-Date-Cleared`.

As in the Sales twin, the date and batch fields are `binary-long` and therefore
`int`, so their arithmetic truncates the way the COBOL's does
[purchase/pl100.cbl:L498], [purchase/pl100.cbl:L502].
"""

from __future__ import annotations

import functools
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# ``ConditionName`` names the type the generated artifact's own condition-name entries
# are instances of.
from acas_posting.dictionary.loader import ConditionName

__all__: Final[tuple[str, ...]] = (
    # Deterministically sorted (R-6).
    "Filler1",
    "Oi5Key",
    "OiBatch",
    "OiCustomer",
    "OiHeader",
    "OiKey",
    "OiSupplier",
    "OpenItemRecord5",
    "WsOtm5Record",
    "condition_names",
    "descriptors_of",
)


# FIELD BINDING. Every dataclass field below is bound to two facts and no others.


def _declared(cobol_name: str, dictionary_key: str) -> Any:
    """Bind one dataclass field to its COBOL name and its dictionary key.

    Args:
        cobol_name: The identifier verbatim from the frozen copybook, case and hyphens
            intact - ``"OI-hold-flag"``, ``"oi5-supplier"``, ``"filler"``. Never
            rewritten, never case-folded.
        dictionary_key: The generated artifact's key for the field -
            ``"<TABLE>.<COLUMN>"`` for a column-backed field, ``"<COPYBOOK-
            RECORD>.<FIELD>"`` for one the bridge never sees, with a ``#`` and the
            declaration line where a name repeats across copybooks.

    Returns:
        A ``dataclasses.Field`` carrying the two names as metadata and no default, so
            the attribute remains required.
    """
    return field(
        metadata={
            "cobol_name": cobol_name,
            "dictionary_key": dictionary_key,
        }
    )


def descriptors_of(
    record_class: type[Any], *, path: Path | None = None
) -> Mapping[str, FieldDescriptor]:
    """Map each attribute of one of this module's classes to its descriptor.

    The R-5 primitive for this layout.

    Args:
        record_class: One of this module's nine dataclasses. Any dataclass whose fields
            carry a ``dictionary_key`` in their metadata works.
        path: An alternative dictionary artifact, for the generator's own round-trip
            checks. ``None`` uses the committed artifact.

    Returns:
        A read-only mapping from attribute name to descriptor, in copybook declaration
            order because that is the order the fields are declared in (R-6).

    Raises:
        KeyError: If a field carries no ``dictionary_key`` metadata, which would mean an
            attribute had been added here without provenance.
    """
    return MappingProxyType(
        {
            attribute.name: FieldDescriptor.from_dictionary_key(
                attribute.metadata["dictionary_key"], path=path
            )
            for attribute in fields(record_class)
        }
    )


# The two elementary items in this layout that carry an 88 level, in copybook
# declaration order.
_CONDITION_NAME_CARRIERS: Final[tuple[str, ...]] = (
    # 88 payment-held value "H". [copybooks/plwsoi.cob:L39] R-4 site 15: this condition
    # name exists here and NOT on the sales open-item copybook's hold flag, which
    # declares none.
    "PUITM5-REC.OI5-HOLD-FLAG",
    # 88 S-Open value zero. [copybooks/plwsoi.cob:L54] 88 S-Closed value 1.
    # [copybooks/plwsoi.cob:L55] R-4 site 21: one uses the figurative constant, the
    # other a literal.
    "PUITM5-REC.OI5-STATUS",
)


@functools.cache
def condition_names(*, path: Path | None = None) -> tuple[ConditionName, ...]:
    """The three 88-level condition names this layout declares, as data.

    Values are strings in their DECLARED form and are never rewritten. The figurative
    constant on ``S-Open`` stays the word it is written as and is never turned into a
    digit.

    Args:
        path: An alternative dictionary artifact, for the generator's own round-trip
            checks. ``None`` uses the committed artifact.

    Returns:
        A tuple of three ``ConditionName`` records in declaration order. Memoised, so
            two calls in one process return the same object and two processes agree
            (R-6).
    """
    return tuple(
        condition
        for key in _CONDITION_NAME_CARRIERS
        for condition in loader.copybook_field_for(key, path=path).condition_names
    )


@dataclass(slots=True)
class WsOtm5Record:
    """The raw 113-byte buffer ``WS-OTM5-Record``, declared elementary.

    R-4 site 5: an ELEMENTARY alphanumeric item - a raw 113-byte buffer - and not a
    group, even though ``OpenItemRecord5`` and ``OiHeader`` are both views over the same
    bytes.
    """

    ws_otm5_record: str = _declared(
        "WS-OTM5-Record", "WS-OTM5-Record.WS-OTM5-Record"
    )


@dataclass(slots=True)
class Oi5Key:
    """The composite key group ``oi5-key``, named in lower case.

    R-4 site 12: the name is ALL LOWER CASE in both files, unlike every field in the
    body copybook, and it is this spelling - not the bridge - that the ``OI5-`` column
    prefix comes from. Carried verbatim.
    """

    oi5_supplier: str = _declared(
        "oi5-supplier", "Open-Item-Record-5.oi5-supplier"
    )
    # 05 oi5-invoice PIC 9(8). *> Was binary-long. *> 15 [copybooks/plwsoi5B.cob:L15]
    # R-4 site 18: upper-case PIC amid lower-case pic in the same file. R-4 site 19.
    oi5_invoice: int = _declared(
        "oi5-invoice", "Open-Item-Record-5.oi5-invoice"
    )


@dataclass(slots=True)
class OpenItemRecord5:
    """The key-only view ``Open-Item-Record-5`` over the 113-byte buffer.

    R-4 site 1: that one space is one of exactly two differences between the two plan-
    named copybooks.
    """

    # 03 oi5-key. [copybooks/plwsoi5C.cob:L13] Two entries hold this group, one per
    # copybook file, and both are cited.
    oi5_key: Oi5Key = field(
        metadata={
            "cobol_name": "oi5-key",
            "dictionary_key": "PUITM5-REC.OI5-KEY",
            "twin_dictionary_key": "Open-Item-Record-5.oi5-key",
        }
    )
    # 03 oi5-date binary-long. *> 19 [copybooks/plwsoi5C.cob:L16] R-4 site 11.
    oi5_date: int = _declared("oi5-date", "Open-Item-Record-5.oi5-date")
    # 03 filler pic x(94). *> 113 [copybooks/plwsoi5C.cob:L17] Declared, never silently
    # dropped (R-3). Positionally named: it is the first and only FILLER in this record.
    filler_1: str = _declared("filler", "Open-Item-Record-5.filler")


# THE BODY - copybooks/plwsoi.cob, the 29-field layout Field order within every class
# below follows copybook declaration order, L12 to L62, so a reader can set this file
# beside `cat -n copybooks/ plwsoi.cob` and diff the two by eye (R-6).


@dataclass(slots=True)
class OiSupplier:
    """The seven-byte supplier group ``OI-Supplier``, nested four deep.

    R-4 site 4: the bridge loads its host variable from THIS group, not from the outer
    one, at ``[common/otm5MT.cbl:L1350-L1351]``.
    """

    # 09 OI-Nos Pic X(6). [copybooks/plwsoi.cob:L16] R-4 site 17.
    oi_nos: str = _declared("OI-Nos", "OI-Header.OI-Nos#16")
    # 09 OI-Check Pic 9. [copybooks/plwsoi.cob:L17] Zoned display, scale zero, so int
    # (R-2). No column.
    oi_check: int = _declared("OI-Check", "OI-Header.OI-Check#17")


@dataclass(slots=True)
class OiCustomer:
    """The column-less group ``OI-Customer``, declared but never loaded.

    R-4 site 4: it is declared here even so. The bridge loads ``HV-OI5-SUPPLIER`` from
    the INNER ``OI-Supplier`` group at ``[common/otm5MT.cbl:L1350-L1351]`` and moves
    this group nowhere, so this is a copybook-only item.
    """

    oi_supplier: OiSupplier = _declared(
        "OI-Supplier", "PUITM5-REC.OI5-SUPPLIER"
    )


@dataclass(slots=True)
class OiKey:
    """The fifteen-byte key group ``OI-Key`` of the purchase open item.

    R-4 site 14: four levels of nesting for a fifteen-byte key - ``OI-Key`` to ``OI-
    Customer`` to ``OI-Supplier`` to the two 09-level children - with the middle two
    spanning identical bytes.
    """

    oi_customer: OiCustomer = _declared(
        "OI-Customer", "OI-Header.OI-Customer"
    )
    # 05 OI-Invoice Pic 9(8). *> Was Binary-long. *> and inv was outside the key
    # [copybooks/plwsoi.cob:L18] R-4 site 19: declaration beats comment.
    oi_invoice: int = _declared("OI-Invoice", "PUITM5-REC.OI5-INVOICE")


@dataclass(slots=True)
class OiBatch:
    """The batch group ``OI-Batch``, carrying ``Comp`` for both children.

    R-4 site 7: TRIPLE materialisation. This group gets a column of its own AND so does
    each of its two children ``[common/otm5MT.cbl:L308-L310]``, and all three columns
    are CHARACTER although both children are numeric under the inherited COMP.
    """

    # 05 OI-B-Nos Pic 9(5). [copybooks/plwsoi.cob:L21] COMP inherited from the group
    # header at L20; scale zero, so int (R-2).
    oi_b_nos: int = _declared("OI-B-Nos", "PUITM5-REC.OI5-BATCH-NOS")
    # 05 OI-B-Item Pic 999. [copybooks/plwsoi.cob:L22] COMP inherited from the group
    # header at L20; scale zero, so int (R-2).
    oi_b_item: int = _declared("OI-B-Item", "PUITM5-REC.OI5-BATCH-ITEM")


@dataclass(slots=True)
class Filler1:
    """The unnamed ``filler`` group carrying ``comp-3`` for ten children.

    R-4 site 13: the group is a FILLER and it is load-bearing.
    """

    # 05 OI-P-C pic s9(7)v99. [copybooks/plwsoi.cob:L42] COMP-3 inherited from the
    # filler header at L41; scale two, so Decimal (R-2).
    oi_p_c: Decimal = _declared("OI-P-C", "PUITM5-REC.OI5-P-C")
    oi_net: Decimal = _declared("OI-Net", "PUITM5-REC.OI5-NET")
    # 05 OI-Approp redefines OI-Net pic s9(7)v99. [copybooks/plwsoi.cob:L44-L45] R-4
    # site 6.
    oi_approp: Decimal = _declared("OI-Approp", "OI-Header.OI-Approp#44")
    oi_extra: Decimal = _declared("OI-Extra", "PUITM5-REC.OI5-EXTRA")
    oi_carriage: Decimal = _declared("OI-Carriage", "PUITM5-REC.OI5-CARRIAGE")
    oi_vat: Decimal = _declared("OI-Vat", "PUITM5-REC.OI5-VAT")
    oi_discount: Decimal = _declared("OI-Discount", "PUITM5-REC.OI5-DISCOUNT")
    oi_e_vat: Decimal = _declared("OI-E-Vat", "PUITM5-REC.OI5-E-VAT")
    oi_c_vat: Decimal = _declared("OI-C-Vat", "PUITM5-REC.OI5-C-VAT")
    oi_paid: Decimal = _declared("OI-Paid", "PUITM5-REC.OI5-PAID")


@dataclass(slots=True)
class OiHeader:
    """The purchase open-item record ``OI-Header``, 29 leaf fields.

    Declared ``01 OI-Header.`` at ``[copybooks/plwsoi.cob:L12]``. Dictionary entry ``OI-
    Header.OI-Header#12`` - the ``#12`` being the declaration line the generated
    artifact appends because the sales open-item copybook declares an ``01 OI-Header``
    too, at L8. The purchase open-item layout.
    """

    oi_key: OiKey = _declared("OI-Key", "OI-Header.OI-Key")
    # 03 OI-Date Binary-long. [copybooks/plwsoi.cob:L19] R-4 site 13 (contrast): at 03
    # level DIRECTLY under the record.
    oi_date: int = _declared("OI-Date", "PUITM5-REC.OI5-DAT")
    oi_batch: OiBatch = _declared("OI-Batch", "PUITM5-REC.OI5-BATCH")
    # 03 OI-Type pic 9. [copybooks/plwsoi.cob:L23] R-4 site 10: numeric in the copybook,
    # `OI5-TYPE char(1)` [mysql/ACASDB.sql:L604] in the table. int, because the
    # descriptor reports the copybook view.
    oi_type: int = _declared("OI-Type", "PUITM5-REC.OI5-TYPE")
    # 03 OI-ref pic x(10). [copybooks/plwsoi.cob:L36] R-4 site 16: lower-case `ref`
    # after the prefix. Carried verbatim. Purchase-only.
    oi_ref: str = _declared("OI-ref", "PUITM5-REC.OI5-REF")
    # 03 OI-order pic x(10). [copybooks/plwsoi.cob:L37] R-4 site 16: lower-case `order`.
    # Purchase-only, as above.
    oi_order: str = _declared("OI-order", "PUITM5-REC.OI5-ORDER")
    # 03 OI-hold-flag pic x. [copybooks/plwsoi.cob:L38] 88 payment-held value "H".
    # [:L39] R-4 site 15.
    oi_hold_flag: str = _declared("OI-hold-flag", "PUITM5-REC.OI5-HOLD-FLAG")
    # 03 OI-unapl pic x. [copybooks/plwsoi.cob:L40] R-4 site 16: lower-case `unapl`,
    # capitalised by the bridge's load paragraph. Copybook spelling recorded.
    oi_unapl: str = _declared("OI-unapl", "PUITM5-REC.OI5-UNAPL")
    # 03 filler comp-3. [copybooks/plwsoi.cob:L41] The unnamed usage-bearing group.
    # Declared, never dropped (R-3); it is what gives ten money fields their storage
    # class.
    filler_1: Filler1 = _declared("filler", "OI-Header.filler#41")
    # 03 OI-Status pic 9. [copybooks/plwsoi.cob:L53] 88 S-Open value zero. [:L54] 88
    # S-Closed value 1. [:L55] R-4 site 10.
    oi_status: int = _declared("OI-Status", "PUITM5-REC.OI5-STATUS")
    # 03 OI-Deduct-Days binary-char. [copybooks/plwsoi.cob:L56] R-4 site 9.
    oi_deduct_days: int = _declared(
        "OI-Deduct-Days", "PUITM5-REC.OI5-DEDUCT-DAYS"
    )
    # 03 OI-Deduct-Amt pic s999v99 comp. [copybooks/plwsoi.cob:L57] THE OPPOSITE CASE to
    # the two group headers: `comp` sits on this field's UsageDeclaredAt.FIELD` and
    # `usage_inherited_from is None`.
    oi_deduct_amt: Decimal = _declared(
        "OI-Deduct-Amt", "PUITM5-REC.OI5-DEDUCT-AMT"
    )
    oi_deduct_vat: Decimal = _declared(
        "OI-Deduct-Vat", "PUITM5-REC.OI5-DEDUCT-VAT"
    )
    # 03 OI-Days binary-char. [copybooks/plwsoi.cob:L59] R-4 site 9: sign lost at the
    # bridge [common/otm5MT.cbl:L329], `OI5-DAYS tinyint(3) unsigned`
    # [mysql/ACASDB.sql:L622]. int (R-2).
    oi_days: int = _declared("OI-Days", "PUITM5-REC.OI5-DAYS")
    # 03 OI-CR binary-long. [copybooks/plwsoi.cob:L60] R-4 site 16: UPPER-CASE `CR`,
    # where the sales open-item copybook writes it in mixed case. Carried verbatim. R-4
    # site 8.
    oi_cr: int = _declared("OI-CR", "PUITM5-REC.OI5-CR")
    oi_applied: str = _declared("OI-Applied", "PUITM5-REC.OI5-APPLIED")
    # 03 OI-Date-Cleared binary-long. [copybooks/plwsoi.cob:L62] R-4 site 11: NOT
    # truncated - the column keeps the full name `OI5-DATE-CLEARED`
    # [common/otm5MT.cbl:L332], unlike OI-Date which became OI5-DAT.
    oi_date_cleared: int = _declared(
        "OI-Date-Cleared", "PUITM5-REC.OI5-DATE-CLEARED"
    )
