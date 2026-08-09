"""Purchase invoice header and lines record layouts.

A CREATE from two frozen copybooks - `copybooks/plwspinv.cob` for the header and
`copybooks/plwspinv2.cob` for the lines - mirroring the two-table split the
schema has, `PUINVOICE-REC` and `PUINV-LINES-REC`, with descriptors looked up in
the generated dictionary (R-5).

The two records are declared separately because the handler writes them
separately: `acas_posting.dal.acas026_pinvoice` owns one header table and one
lines table, and nothing here decides which rows go where.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from decimal import Decimal
from types import MappingProxyType
from typing import Any, ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# `ConditionName` is the generated dictionary's own carrier for an 88-level, with
# exactly the three members this module needs - name, value and source.
from acas_posting.dictionary.loader import ConditionName

__all__: Final[tuple[str, ...]] = (
    # The 88-level inventory and the four lookups, then the sixteen record types in one
    # alphabetical run, so the surface is stable between runs.
    "CONDITION_NAMES",
    "IhFig",
    "IhFig2",
    "IhInvoiceHeader",
    "IhOrder",
    "IhPrime",
    "IhSubPrime",
    "IhSupplier",
    "IhSupplier2",
    "IlInvoiceLine",
    "IlInvoiceLineBody",
    "IlKey",
    "InvoiceKey",
    "PInvoiceBodies",
    "PInvoiceHeader",
    "WsInvoiceKey",
    "WsPInvoiceRecord",
    "cite_for",
    "condition_names_for",
    "descriptor_for",
    "dictionary_key_for",
)


# FIVE COLUMNS THAT NO COPYBOOK DECLARES.


_DICTIONARY_KEY: Final[str] = "dictionary_key"


def _cited(key: str) -> Mapping[str, str]:
    """Return the field metadata that cites one generated-dictionary entry.

    A formatting device and nothing else, so that the 102 cited attribute declarations
    below read as one line each.

    Args:
        key: A qualified entry key, `<TABLE-NAME>.<COLUMN-NAME>` for a column-mapped
            field or `<COPYBOOK-RECORD>.<FIELD-NAME>` with the loader's own line
            disambiguator for a copybook-only field.

    Returns:
        The metadata mapping for `dataclasses.field`.
    """
    return {_DICTIONARY_KEY: key}


# THE 88-LEVELS, AS DATA.
CONDITION_NAMES: Final[Mapping[str, tuple[ConditionName, ...]]] = MappingProxyType(
    {
        "PInvoice-Header.ih-Freq": (
            ConditionName(
                name="ih-Yearly",
                value='"Y"',
                source="copybooks/plwspinv.cob:L19",
            ),
            ConditionName(
                name="ih-Monthly",
                value='"M"',
                source="copybooks/plwspinv.cob:L20",
            ),
            ConditionName(
                name="ih-Quarterly",
                value='"Q"',
                source="copybooks/plwspinv.cob:L21",
            ),
            ConditionName(
                name="ih-Daily",
                value='"D"',
                source="copybooks/plwspinv.cob:L22",
            ),
            ConditionName(
                name="ih-Testing",
                value='"D"',
                source="copybooks/plwspinv.cob:L23",
            ),
            ConditionName(
                name="ih-Valid-Freqs",
                value='"Y" "M" "Q" "D"',
                source="copybooks/plwspinv.cob:L24",
            ),
        ),
        "PUINVOICE-REC.IH-STATUS": (
            ConditionName(
                name="pending",
                value='"P" "p"',
                source="copybooks/plwspinv.cob:L41",
            ),
            ConditionName(
                name="invoiced",
                value='"I" "i"',
                source="copybooks/plwspinv.cob:L42",
            ),
            ConditionName(
                name="applied",
                value='"Z" "z"',
                source="copybooks/plwspinv.cob:L43",
            ),
        ),
        "PUINVOICE-REC.IH-DAY-BOOK-FLAG": (
            ConditionName(
                name="day-booked",
                value='"B" "b"',
                source="copybooks/plwspinv.cob:L51",
            ),
        ),
        "PUINVOICE-REC.IH-UPDATE": (
            ConditionName(
                name="ih-analyised",
                value='"Z" "z"',
                source="copybooks/plwspinv.cob:L53",
            ),
        ),
        "PUINV-LINES-REC.IL-UPDATE": (
            ConditionName(
                name="il-analyised",
                value='"z" "Z"',
                source="copybooks/plwspinv.cob:L83",
            ),
        ),
        "Invoice-Header.ih-status#40": (
            ConditionName(
                name="pending",
                value='"p" "P"',
                source="copybooks/plwspinv2.cob:L41",
            ),
            ConditionName(
                name="invoiced",
                value='"i" "I"',
                source="copybooks/plwspinv2.cob:L42",
            ),
            ConditionName(
                name="applied",
                value='"z" "Z"',
                source="copybooks/plwspinv2.cob:L43",
            ),
        ),
        "Invoice-Header.ih-day-book-flag#50": (
            ConditionName(
                name="day-booked",
                value='"b" "B"',
                source="copybooks/plwspinv2.cob:L51",
            ),
        ),
        "Invoice-Header.ih-update#52": (
            ConditionName(
                name="ih-analyised",
                value='"z" "Z"',
                source="copybooks/plwspinv2.cob:L53",
            ),
        ),
        "Invoice-Line.il-update#71": (
            ConditionName(
                name="il-analyised",
                value='"z" "Z"',
                source="copybooks/plwspinv2.cob:L72",
            ),
        ),
    }
)


def dictionary_key_for(record: Any, attribute: str) -> str:
    """Return the generated-dictionary key one attribute is cited to.

    Args:
        record: Any dataclass in this module, or an instance of one.
        attribute: The Python attribute name, as `"ih_net"`.

    Returns:
        The qualified entry key, as `"PUINVOICE-REC.IH-NET"`.

    Raises:
        TypeError: `record` is not a dataclass type or instance.
        KeyError: No such attribute on that record, or - which cannot happen for a
            record declared in this module - an attribute carrying no citation.
    """
    for declared in fields(record):
        if declared.name == attribute:
            key = declared.metadata.get(_DICTIONARY_KEY)
            if key is None:
                raise KeyError(
                    f"{attribute!r} on "
                    f"{getattr(record, '__name__', type(record).__name__)!r} "
                    f"carries no data dictionary citation."
                )
            return str(key)
    raise KeyError(
        f"{getattr(record, '__name__', type(record).__name__)!r} declares no "
        f"attribute {attribute!r}. Its attributes, in copybook declaration "
        f"order, are: {', '.join(f.name for f in fields(record))}."
    )


def descriptor_for(record: Any, attribute: str) -> FieldDescriptor:
    """Describe one attribute's COBOL storage, from the generated dictionary.

    Args:
        record: Any dataclass in this module, or an instance of one.
        attribute: The Python attribute name, as `"il_qty"`.

    Returns:
        The descriptor for that field, carrying its dictionary key and the `<path>:L<n>`
            locator of its copybook declaration.

    Raises:
        KeyError: No such attribute on that record.
        loader.DictionaryKeyError: The dictionary carries no such entry, which would
            mean this module and the generated artifact had drifted apart.
    """
    return FieldDescriptor.from_dictionary_key(dictionary_key_for(record, attribute))


def cite_for(record: Any, attribute: str) -> str:
    """Return one attribute's three-locator provenance line.

    Args:
        record: Any dataclass in this module, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The provenance line for that field.

    Raises:
        KeyError: No such attribute on that record.
    """
    return loader.cite(dictionary_key_for(record, attribute))


def condition_names_for(key: str) -> tuple[ConditionName, ...]:
    """Return the 88-levels declared on the item one dictionary key names.

    Args:
        key: A qualified entry key, as returned by `dictionary_key_for`.

    Returns:
        The condition names in copybook declaration order, each with its literal list
            verbatim and its own locator.
    """
    return CONDITION_NAMES.get(key, ())


# copybooks/plwspinv.cob - THE WORKING-STORAGE INVOICE HEADER AND BODIES Field order
# below follows the copybook line for line, so that a reader can set `cat -n
# copybooks/plwspinv.cob` beside this section and walk both together.


@dataclass(slots=True, kw_only=True)
class WsInvoiceKey:
    """`05 WS-Invoice-Key.` [copybooks/plwspinv.cob:L10].

    Two children at level 07, which is one level deeper than the sales copybook nests
    the same idea.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINVOICE-REC.PINVOICE-KEY"

    ih_invoice: int = field(metadata=_cited("PUINVOICE-REC.IH-INVOICE"))

    # `07 ih-Test pic 99 value zero. *> was binary-char value zero.`
    # [copybooks/plwspinv.cob:L12] The frozen comment records the field's superseded
    # COBOL declaration; the live declaration is the `pic 99` one.
    ih_test: int = field(default=0, metadata=_cited("PUINVOICE-REC.IH-TEST"))


@dataclass(slots=True, kw_only=True)
class IhSupplier:
    """`05 ih-Supplier.` [copybooks/plwspinv.cob:L13]."""

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINVOICE-REC.IH-SUPPLIER"

    ih_nos: str = field(metadata=_cited("PInvoice-Header.ih-Nos"))

    ih_check: int = field(metadata=_cited("PInvoice-Header.ih-Check"))


@dataclass(slots=True, kw_only=True)
class IhOrder:
    """`05 ih-order.` [copybooks/plwspinv.cob:L17].

    None of the four members below reaches the bridge or a table. Only the ten bytes as
    a whole do, as `HV-IH-ORDER X(10)` [common/plinvoiceMT.cbl:L396] -> `IH-ORDER
    char(10)`.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINVOICE-REC.IH-ORDER"

    ih_freq: str = field(metadata=_cited("PInvoice-Header.ih-Freq"))

    ih_repeat: int = field(metadata=_cited("PInvoice-Header.ih-Repeat"))

    # `07 filler pic xxx.` [copybooks/plwspinv.cob:L26] Written `xxx`, which is three
    # characters. It occupies bytes and is declared; a filler is never dropped from this
    # layer.
    filler_1: str = field(metadata=_cited("PInvoice-Header.filler"))

    ih_last_date: int = field(metadata=_cited("PInvoice-Header.ih-Last-Date"))


@dataclass(slots=True, kw_only=True)
class IhPrime:
    """The first of the header's two halves, 42 bytes."""

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.ih-prime"

    ws_invoice_key: WsInvoiceKey = field(metadata=_cited("PUINVOICE-REC.PINVOICE-KEY"))

    ih_supplier: IhSupplier = field(metadata=_cited("PUINVOICE-REC.IH-SUPPLIER"))

    # `05 ih-Date binary-long.` [copybooks/plwspinv.cob:L16] Signed in the copybook.
    ih_date: int = field(metadata=_cited("PUINVOICE-REC.IH-DAT"))

    ih_order: IhOrder = field(metadata=_cited("PUINVOICE-REC.IH-ORDER"))

    ih_type: int = field(metadata=_cited("PUINVOICE-REC.IH-TYPE"))

    ih_ref: str = field(metadata=_cited("PUINVOICE-REC.IH-REF"))


@dataclass(slots=True, kw_only=True)
class IhFig:
    """The header's eight packed money fields.

    GROUP-USAGE INHERITANCE. The usage clause is written once, on the group, and each of
    the eight children below carries only `pic s9(7)v99` with no usage of its own
    [copybooks/plwspinv.cob:L32-L39].
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.ih-Fig"

    ih_p_c: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-P-C"))

    ih_net: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-NET"))

    ih_extra: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-EXTRA"))

    ih_carriage: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-CARRIAGE"))

    ih_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-VAT"))

    ih_discount: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-DISCOUNT"))

    ih_e_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-E-VAT"))

    ih_c_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-C-VAT"))


@dataclass(slots=True, kw_only=True)
class IhSubPrime:
    """The header's second half - money, status and the deduction terms.

    ORDER NOTE. `ih-lines` is declared here at [copybooks/plwspinv.cob:L44], immediately
    before `ih-deduct-days`.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.ih-sub-prime"

    ih_fig: IhFig = field(metadata=_cited("PInvoice-Header.ih-Fig"))

    ih_status: str = field(metadata=_cited("PUINVOICE-REC.IH-STATUS"))

    ih_lines: int = field(metadata=_cited("PUINVOICE-REC.IH-LINES"))

    ih_deduct_days: int = field(metadata=_cited("PUINVOICE-REC.IH-DEDUCT-DAYS"))

    ih_deduct_amt: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-DEDUCT-AMT"))

    ih_deduct_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-DEDUCT-VAT"))

    ih_days: int = field(metadata=_cited("PUINVOICE-REC.IH-DAYS"))

    ih_cr: int = field(metadata=_cited("PUINVOICE-REC.IH-CR"))

    # `05 ih-day-book-flag pic x value space.` [copybooks/plwspinv.cob:L50] The VALUE
    # clause is declared, so the default below reproduces it.
    ih_day_book_flag: str = field(
        default=" ", metadata=_cited("PUINVOICE-REC.IH-DAY-BOOK-FLAG")
    )

    ih_update: str = field(metadata=_cited("PUINVOICE-REC.IH-UPDATE"))


@dataclass(slots=True, kw_only=True)
class PInvoiceHeader:
    """`01 PInvoice-Header.` [copybooks/plwspinv.cob:L8]."""

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.PInvoice-Header"

    ih_prime: IhPrime = field(metadata=_cited("PInvoice-Header.ih-prime"))

    ih_sub_prime: IhSubPrime = field(metadata=_cited("PInvoice-Header.ih-sub-prime"))


@dataclass(slots=True, kw_only=True)
class IlKey:
    """`05 il-Key.` [copybooks/plwspinv.cob:L67], commented `*> New 08/10/18`."""

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINV-LINES-REC.IL-LINE-KEY"

    il_invoice: int = field(metadata=_cited("PUINV-LINES-REC.IL-INVOICE"))

    il_line: int = field(metadata=_cited("PUINV-LINES-REC.IL-LINE"))


@dataclass(slots=True, kw_only=True)
class IlInvoiceLineBody:
    """One of the forty invoice lines the bodies record holds.

    Its description is 24 characters wide. The sales copybook's is 32; that is one of
    the fourteen divergences, not a transcription slip.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Pinvoice-Bodies.invoice-line"

    il_key: IlKey = field(metadata=_cited("PUINV-LINES-REC.IL-LINE-KEY"))

    il_product: str = field(metadata=_cited("PUINV-LINES-REC.IL-PRODUCT"))

    il_pa: str = field(metadata=_cited("PUINV-LINES-REC.IL-PA"))

    filler_1: str = field(metadata=_cited("Pinvoice-Bodies.filler#72"))

    # `05 il-qty binary-short.` [copybooks/plwspinv.cob:L73] Signed here; `HV1-IL-QTY
    # PIC 9(05) COMP` [common/plinvoiceMT.cbl:L431] and `smallint(6) unsigned` in the
    # table. The sixth and last of the signedness narrowings.
    il_qty: int = field(metadata=_cited("PUINV-LINES-REC.IL-QTY"))

    il_type: str = field(metadata=_cited("PUINV-LINES-REC.IL-TYPE"))

    il_description: str = field(metadata=_cited("PUINV-LINES-REC.IL-DESCRIPTION"))

    filler_2: str = field(metadata=_cited("Pinvoice-Bodies.filler#76"))

    il_net: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-NET"))

    il_unit: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-UNIT"))

    il_discount: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-DISCOUNT"))

    il_vat: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-VAT"))

    il_vat_code: int = field(metadata=_cited("PUINV-LINES-REC.IL-VAT-CODE"))

    il_update: str = field(metadata=_cited("PUINV-LINES-REC.IL-UPDATE"))


@dataclass(slots=True, kw_only=True)
class PInvoiceBodies:
    """`01 Pinvoice-Bodies. *> was lines.` [copybooks/plwspinv.cob:L65].

    The table is a `tuple`, fixed at forty elements, because the `OCCURS 40` is fixed at
    forty and because a run of this cycle has to come out the same way twice.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Pinvoice-Bodies.Pinvoice-Bodies"

    invoice_line: tuple[IlInvoiceLineBody, ...] = field(
        metadata=_cited("Pinvoice-Bodies.invoice-line")
    )


# plwspinv2.cob: THREE VIEWS OVER ONE BUFFER.


@dataclass(slots=True, kw_only=True)
class InvoiceKey:
    """`03 Invoice-Key.` [copybooks/plwspinv2.cob:L11]."""

    COBOL_DICTIONARY_KEY: ClassVar[str] = "WS-PInvoice-Record.Invoice-Key"

    invoice_nos: int = field(metadata=_cited("WS-PInvoice-Record.Invoice-Nos"))

    item_nos: int = field(metadata=_cited("WS-PInvoice-Record.Item-Nos"))


@dataclass(slots=True, kw_only=True)
class WsPInvoiceRecord:
    """`01 WS-PInvoice-Record.` [copybooks/plwspinv2.cob:L10]."""

    COBOL_DICTIONARY_KEY: ClassVar[str] = "WS-PInvoice-Record.WS-PInvoice-Record"

    invoice_key: InvoiceKey = field(metadata=_cited("WS-PInvoice-Record.Invoice-Key"))

    invoice_supplier: str = field(
        metadata=_cited("WS-PInvoice-Record.Invoice-Supplier")
    )

    invoice_date: int = field(metadata=_cited("WS-PInvoice-Record.Invoice-Date"))

    inv_order: str = field(metadata=_cited("WS-PInvoice-Record.Inv-Order"))

    invoice_type: int = field(metadata=_cited("WS-PInvoice-Record.Invoice-Type"))

    filler_1: str = field(metadata=_cited("WS-PInvoice-Record.filler#18"))

    filler_2: str = field(metadata=_cited("WS-PInvoice-Record.filler#19"))


@dataclass(slots=True, kw_only=True)
class IhSupplier2:
    """`03 ih-supplier.` [copybooks/plwspinv2.cob:L24].

    The same supplier group as `IhSupplier`, declared lower case and one level shallower
    in the second copybook. The two classes are named apart only because Python cannot
    hold both spellings of one name in one module.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-supplier"

    ih_nos: str = field(metadata=_cited("Invoice-Header.ih-nos#25"))

    ih_check: int = field(metadata=_cited("Invoice-Header.ih-check#26"))


@dataclass(slots=True, kw_only=True)
class IhFig2:
    """The second copybook's spelling of the same eight money fields.

    Named apart from `IhFig` only because one module cannot hold both spellings; this is
    the second copybook's group.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-fig#31"

    ih_p_c: Decimal = field(metadata=_cited("Invoice-Header.ih-p-c#32"))

    ih_net: Decimal = field(metadata=_cited("Invoice-Header.ih-net#33"))

    ih_extra: Decimal = field(metadata=_cited("Invoice-Header.ih-extra#34"))

    ih_carriage: Decimal = field(metadata=_cited("Invoice-Header.ih-carriage#35"))

    ih_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-vat#36"))

    ih_discount: Decimal = field(metadata=_cited("Invoice-Header.ih-discount#37"))

    ih_e_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-e-vat#38"))

    ih_c_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-c-vat#39"))


@dataclass(slots=True, kw_only=True)
class IhInvoiceHeader:
    """The header view over the shared buffer.

    The first of the two redefinitions. The record's own descriptor - the one behind
    `COBOL_DICTIONARY_KEY` - carries `redefines` "WS-PInvoice-Record", which is where
    the COBOL writes the clause; the members below carry none, because the COBOL gives
    them none.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.Invoice-Header#21"

    ih_invoice: int = field(metadata=_cited("Invoice-Header.ih-invoice#22"))

    ih_test: int = field(metadata=_cited("Invoice-Header.ih-test#23"))

    ih_supplier: IhSupplier2 = field(metadata=_cited("Invoice-Header.ih-supplier"))

    ih_date: int = field(metadata=_cited("Invoice-Header.ih-date#27"))

    ih_order: str = field(metadata=_cited("Invoice-Header.ih-order#28"))

    ih_type: int = field(metadata=_cited("Invoice-Header.ih-type#29"))

    ih_ref: str = field(metadata=_cited("Invoice-Header.ih-ref#30"))

    ih_fig: IhFig2 = field(metadata=_cited("Invoice-Header.ih-fig#31"))

    ih_status: str = field(metadata=_cited("Invoice-Header.ih-status#40"))

    ih_lines: int = field(metadata=_cited("Invoice-Header.ih-lines#44"))

    ih_deduct_days: int = field(metadata=_cited("Invoice-Header.ih-deduct-days#45"))

    ih_deduct_amt: Decimal = field(metadata=_cited("Invoice-Header.ih-deduct-amt#46"))

    ih_deduct_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-deduct-vat#47"))

    ih_days: int = field(metadata=_cited("Invoice-Header.ih-days#48"))

    ih_cr: int = field(metadata=_cited("Invoice-Header.ih-cr#49"))

    # `03 ih-day-book-flag pic x.` [copybooks/plwspinv2.cob:L50] NO VALUE clause here,
    # where [copybooks/plwspinv.cob:L50] declares `value space`. No default is given,
    # because the copybook declares none.
    ih_day_book_flag: str = field(metadata=_cited("Invoice-Header.ih-day-book-flag#50"))

    ih_update: str = field(metadata=_cited("Invoice-Header.ih-update#52"))


@dataclass(slots=True, kw_only=True)
class IlInvoiceLine:
    """The invoice-line view over the shared buffer."""

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Line.Invoice-Line#56"

    il_invoice: int = field(metadata=_cited("Invoice-Line.il-invoice#57"))

    il_line: int = field(metadata=_cited("Invoice-Line.il-line#58"))

    il_product: str = field(metadata=_cited("Invoice-Line.il-product#59"))

    il_pa: str = field(metadata=_cited("Invoice-Line.il-pa#60"))

    filler_1: str = field(metadata=_cited("Invoice-Line.filler#61"))

    il_qty: int = field(metadata=_cited("Invoice-Line.il-qty#62"))

    il_type: str = field(metadata=_cited("Invoice-Line.il-type#63"))

    il_description: str = field(metadata=_cited("Invoice-Line.il-description#64"))

    filler_2: str = field(metadata=_cited("Invoice-Line.filler#65"))

    il_net: Decimal = field(metadata=_cited("Invoice-Line.il-net#66"))

    il_unit: Decimal = field(metadata=_cited("Invoice-Line.il-unit#67"))

    il_discount: Decimal = field(metadata=_cited("Invoice-Line.il-discount#68"))

    il_vat: Decimal = field(metadata=_cited("Invoice-Line.il-vat#69"))

    il_vat_code: int = field(metadata=_cited("Invoice-Line.il-vat-code#70"))

    il_update: str = field(metadata=_cited("Invoice-Line.il-update#71"))
