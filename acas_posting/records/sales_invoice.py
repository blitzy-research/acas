"""Sales invoice header and lines record layouts.

A CREATE from two frozen copybooks - `copybooks/slwsinv.cob` and
`copybooks/slwsinv2.cob` - mirroring the two-table split the schema has,
`SAINVOICE-REC` and `SAINV-LINES-REC`, with descriptors looked up in the
generated dictionary (R-5).

The copybooks declare more than one view over the same bytes; every view is
declared here as written, because the posting programs address fields through
whichever view they `COPY`, and collapsing them would remove names the COBOL
uses.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from decimal import Decimal
from typing import Any, ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# Two dictionary types are needed for return annotations only, and neither has a
# substitute.
from acas_posting.dictionary.loader import ConditionName, Drift


# The frozen spine this record sits on Named once, here, so that every citation below is
# a locator rather than a repeated string literal.

COPYBOOK_SLWSINV: Final[str] = "copybooks/slwsinv.cob"

COPYBOOK_SLWSINV2: Final[str] = "copybooks/slwsinv2.cob"

BRIDGE: Final[str] = "common/slinvoiceMT.cbl"

HANDLER: Final[str] = "acas016"

ENTITY_FACADE: Final[str] = "Invoice"

HEADER_TABLE: Final[str] = "SAINVOICE-REC"

LINES_TABLE: Final[str] = "SAINV-LINES-REC"

# The dataclass-field metadata slot holding each attribute's dictionary key. Prefixed so
# it cannot collide with metadata any other tool attaches.
_DICTIONARY_KEY: Final[str] = "acas_posting.dictionary_key"


def _entry(dictionary_key: str) -> dict[str, str]:
    """Attach ``dictionary_key`` to a dataclass field as its provenance.

    R-5 requires every Python field definition to cite its data-dictionary entry.
    Carrying the key in field metadata rather than in a module-level constant keeps that
    citation attached to the attribute it describes and, critically, costs nothing at
    import.
    """
    return {_DICTIONARY_KEY: dictionary_key}


def dictionary_key_for(record: Any, attribute: str) -> str:
    """Return the data-dictionary key cited by ``attribute`` of ``record``.

    Raises:
        AttributeError: if ``record`` declares no such attribute.
        LookupError: if the attribute exists but cites no dictionary entry, which would
            mean the provenance invariant had been broken.
    """
    for declared in fields(record):
        if declared.name == attribute:
            key = declared.metadata.get(_DICTIONARY_KEY)
            if key is None:
                raise LookupError(
                    f"{_record_label(record)}.{attribute} cites no data-dictionary "
                    f"entry; every attribute in this module must carry one"
                )
            return key
    raise AttributeError(f"{_record_label(record)} declares no field {attribute!r}")


def dictionary_keys_for(record: Any) -> tuple[tuple[str, str], ...]:
    """Return ``(attribute, dictionary key)`` pairs in declaration order.

    Declaration order here is COBOL declaration order, because that is the order the
    dataclasses are written in. This is the pairing that the migration's traceability
    document tabulates, and the one a census diffs against ``cat -n`` of the copybook.
    """
    return tuple(
        (declared.name, declared.metadata[_DICTIONARY_KEY])
        for declared in fields(record)
        if _DICTIONARY_KEY in declared.metadata
    )


def descriptor_for(record: Any, attribute: str) -> FieldDescriptor:
    """Return the :class:`FieldDescriptor` for ``attribute`` of ``record``.

    The descriptor reports the COPYBOOK view of the field - its picture, usage, digits,
    scale, signedness and storage class as COBOL declares them - and offers any
    disagreement with the bridge host variable or the MySQL column through
    :func:`drift_for`, untouched.
    """
    return FieldDescriptor.from_dictionary_key(dictionary_key_for(record, attribute))


def cite_for(record: Any, attribute: str) -> str:
    """Return the three-locator provenance line for ``attribute``.

    The shape, straight from the loader, is the R-5 primitive - copybook line, bridge
    line and column line for one field.
    """
    return loader.cite(dictionary_key_for(record, attribute))


def drift_for(record: Any, attribute: str) -> Drift:
    """Return the copybook/bridge/column disagreement for ``attribute``.

    Surfaced and left as it stands.
    """
    return loader.drift_for(dictionary_key_for(record, attribute))


def record_dictionary_key(record: Any) -> str:
    """Return the dictionary key of the COBOL group ``record`` itself models."""
    return str(record.COBOL_DICTIONARY_KEY)


def record_descriptor(record: Any) -> FieldDescriptor:
    """Return the :class:`FieldDescriptor` for the COBOL group ``record`` models.

    This is where an OCCURS count lives: the descriptor for :class:`SilInvoiceLine`
    reports ``occurs == 40`` from [copybooks/slwsinv.cob:L81].
    """
    return FieldDescriptor.from_dictionary_key(record_dictionary_key(record))


def _record_label(record: Any) -> str:
    """Return a readable class name for ``record``, given a class or instance."""
    return record.__name__ if isinstance(record, type) else type(record).__name__


def _condition_source_line(condition: ConditionName) -> int:
    """Return the copybook line number a condition name was declared on.

    The dictionary does not hand condition names back in declaration order, and R-6
    requires a deterministic order, so they are ordered by the line in their own
    ``source`` locator - which is declaration order by construction.
    """
    tail = condition.source.rsplit(":L", 1)[-1]
    return int(tail.split("-", 1)[0])


def _condition_names_declared_in(copybook: str) -> tuple[ConditionName, ...]:
    """Return every 88-level declared in ``copybook``, in declaration order."""
    declared = [
        condition
        for entry in loader.entries_for_copybook_file(copybook)
        for condition in entry.copybook.condition_names
    ]
    declared.sort(key=_condition_source_line)
    return tuple(declared)


def condition_names_slwsinv() -> tuple[ConditionName, ...]:
    """Return the twelve 88-levels of `copybooks/slwsinv.cob`, in source order.

    Carried as DATA, with each ``value`` the VALUE or VALUES literal text exactly as
    written, so a multi-value form stays one condition name with four literals: ``sih-
    Valid-Freqs`` is ``'"Y" "M" "Q" "D"'``, not four entries
    [copybooks/slwsinv.cob:L35].
    """
    return _condition_names_declared_in(COPYBOOK_SLWSINV)


def condition_names_slwsinv2() -> tuple[ConditionName, ...]:
    """Return the twelve 88-levels of `copybooks/slwsinv2.cob`, in source order.

    The same twelve concepts as :func:`condition_names_slwsinv`, declared differently on
    purpose, and the module docstring lists every divergence: upper-case literals only
    where the twin is dual case, and ``applied`` [copybooks/slwsinv2.cob:L74] where the
    twin writes ``sapplied`` [copybooks/slwsinv.cob:L55].
    """
    return _condition_names_declared_in(COPYBOOK_SLWSINV2)


def condition_names_for(record: Any, attribute: str) -> tuple[ConditionName, ...]:
    """Return the 88-levels declared on one attribute, in declaration order."""
    entry = loader.get_entry(dictionary_key_for(record, attribute))
    return tuple(sorted(entry.copybook.condition_names, key=_condition_source_line))


# copybooks/slwsinv.cob - the layout the bridge copies Plain mutable dataclasses,
# because `sl055` and `sl060` read a record, change fields and write it back.


@dataclass(kw_only=True, slots=True)
class WsInvoiceKey:
    """``03 WS-Invoice-Key.`` [copybooks/slwsinv.cob:L20] - the invoice key group.

    The bridge concatenates the whole group into a single alphanumeric host variable,
    `HV-SINVOICE-KEY X(10)` [common/slinvoiceMT.cbl:L391], by `move WS-Invoice-Key to
    HV-SINVOICE-KEY` [:L1455], and that becomes the primary key column `SINVOICE-KEY
    char(10)`.
    """

    COBOL_NAME: ClassVar[str] = "WS-Invoice-Key"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L20"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SAINVOICE-REC.SINVOICE-KEY"

    sih_invoice: int = field(metadata=_entry("SAINVOICE-REC.IH-INVOICE"))

    # 05 sih-test pic 99 value zero. *> WAS binary-char [copybooks/slwsinv.cob:L22] R-4:
    # declaration beats comment. The comment records that this field once was binary.
    sih_test: int = field(default=0, metadata=_entry("SAINVOICE-REC.IH-TEST"))


@dataclass(kw_only=True, slots=True)
class SihCustomer:
    """``03 sih-customer.`` [copybooks/slwsinv.cob:L23] - the customer key group.

    R-4, alphanumeric group concatenation: the bridge collapses the group into one `HV-
    IH-CUSTOMER X(7)` [common/slinvoiceMT.cbl:L394] through `move WS-Sih-Customer to HV-
    IH-CUSTOMER` [:L1459], stored as `IH-CUSTOMER char(7)`.
    """

    COBOL_NAME: ClassVar[str] = "sih-customer"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L23"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SAINVOICE-REC.IH-CUSTOMER"

    sih_nos: str = field(metadata=_entry("SInvoice-Header.sih-nos"))

    sih_check: int = field(metadata=_entry("SInvoice-Header.sih-check"))


@dataclass(kw_only=True, slots=True)
class SihOrderView:
    """``03 filler redefines sih-order.`` [copybooks/slwsinv.cob:L28].

    R-4, copybook-only: not one of the four has a bridge host variable or a column.
    """

    COBOL_NAME: ClassVar[str] = "filler"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L28"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.filler#28"

    sih_freq: str = field(metadata=_entry("SInvoice-Header.sih-Freq"))

    sih_repeat: int = field(metadata=_entry("SInvoice-Header.sih-Repeat"))

    # 05 filler pic xxx. [copybooks/slwsinv.cob:L37] R-4: the `xxx` short form, not
    # `x(3)`. The entry keeps the literal picture text and reports character length 3.
    filler_37: str = field(metadata=_entry("SInvoice-Header.filler#37"))

    sih_last_date: int = field(metadata=_entry("SInvoice-Header.sih-Last-Date"))


@dataclass(kw_only=True, slots=True)
class SihPrime:
    """``02 sih-prime.`` [copybooks/slwsinv.cob:L19] - the first 42 bytes.

    The copybook annotates this group "42 bytes", and the declared members sum to 8 + 2
    + 6 + 1 + 4 + 10 + 1 + 10 = 42, so the annotation agrees.
    """

    COBOL_NAME: ClassVar[str] = "sih-prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L19"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.sih-prime"

    ws_invoice_key: WsInvoiceKey = field(
        metadata=_entry("SAINVOICE-REC.SINVOICE-KEY")
    )

    sih_customer: SihCustomer = field(metadata=_entry("SAINVOICE-REC.IH-CUSTOMER"))

    # 03 sih-date binary-long. [copybooks/slwsinv.cob:L26] "For autogen next date due".
    # R-4, two drifts at once on one field.
    sih_date: int = field(metadata=_entry("SAINVOICE-REC.IH-DAT"))

    sih_order: str = field(metadata=_entry("SAINVOICE-REC.IH-ORDER"))

    filler_28: SihOrderView = field(metadata=_entry("SInvoice-Header.filler#28"))

    sih_type: int = field(metadata=_entry("SAINVOICE-REC.IH-TYPE"))

    sih_ref: str = field(metadata=_entry("SAINVOICE-REC.IH-REF"))


@dataclass(kw_only=True, slots=True)
class SihFig:
    """``03 sih-fig comp-3.`` [copybooks/slwsinv.cob:L43].

    Reading usage off a child's own PICTURE line would type all eight as zoned DISPLAY.
    Nothing would fail; every stored figure would simply be wrong, and the first sign of
    it would be a scenario state diff.
    """

    COBOL_NAME: ClassVar[str] = "sih-fig"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L43"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.sih-fig"

    sih_p_c: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-P-C"))

    sih_net: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-NET"))

    sih_extra: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-EXTRA"))

    sih_carriage: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-CARRIAGE"))

    sih_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-VAT"))

    sih_discount: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-DISCOUNT"))

    sih_e_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-E-VAT"))

    sih_c_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-C-VAT"))


@dataclass(kw_only=True, slots=True)
class SihSubPrime:
    """``02 Sih-Sub-Prime.`` [copybooks/slwsinv.cob:L41] - the remaining 95 bytes.

    R-4, group-name casing: this group is mixed case here and lower case as `ih-sub-
    prime` in the twin [copybooks/slwsinv2.cob:L60], while `sih-prime` [:L19] and `ih-
    prime` [copybooks/slwsinv2.cob:L39] are both lower case. The casing is carried as
    declared, in each class's own COBOL_NAME.
    """

    COBOL_NAME: ClassVar[str] = "Sih-Sub-Prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L41"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.Sih-Sub-Prime"

    sih_description: str = field(metadata=_entry("SAINVOICE-REC.IH-DESCRIPTION"))

    sih_fig: SihFig = field(metadata=_entry("SInvoice-Header.sih-fig"))

    sih_status: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS"))

    sih_status_p: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-P"))

    sih_status_l: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-L"))

    sih_status_c: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-C"))

    sih_status_a: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-A"))

    sih_status_i: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-I"))

    # 03 sih-lines binary-char. [copybooks/slwsinv.cob:L61] "No. of following body line
    # recs". R-4, column reordering.
    sih_lines: int = field(metadata=_entry("SAINVOICE-REC.IH-LINES"))

    sih_deduct_days: int = field(metadata=_entry("SAINVOICE-REC.IH-DEDUCT-DAYS"))

    sih_deduct_amt: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-DEDUCT-AMT"))

    sih_deduct_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-DEDUCT-VAT"))

    sih_days: int = field(metadata=_entry("SAINVOICE-REC.IH-DAYS"))

    sih_cr: int = field(metadata=_entry("SAINVOICE-REC.IH-CR"))

    # 03 sih-day-book-flag pic x value space. [copybooks/slwsinv.cob:L67] R-4: this
    # field HAS a VALUE clause and its twin `ih-day-book-flag`
    # [copybooks/slwsinv2.cob:L86] has none.
    sih_day_book_flag: str = field(
        default=" ", metadata=_entry("SAINVOICE-REC.IH-DAY-BOOK-FLAG")
    )

    # 03 sih-update pic x. [copybooks/slwsinv.cob:L69] Carries `88 sih-analyised values
    # "Z" "z".` [:L70]. R-4.
    sih_update: str = field(metadata=_entry("SAINVOICE-REC.IH-UPDATE"))


@dataclass(kw_only=True, slots=True)
class SInvoiceHeader:
    """``01 SInvoice-Header.`` [copybooks/slwsinv.cob:L18] - 137 bytes."""

    COBOL_NAME: ClassVar[str] = "SInvoice-Header"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L18"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.SInvoice-Header"

    sih_prime: SihPrime = field(metadata=_entry("SInvoice-Header.sih-prime"))

    sih_sub_prime: SihSubPrime = field(
        metadata=_entry("SInvoice-Header.Sih-Sub-Prime")
    )


@dataclass(kw_only=True, slots=True)
class SilKey:
    """``05 sil-Key.`` [copybooks/slwsinv.cob:L82] - the line key group, 10 bytes.

    R-4, the second bridge-only primary key: the group is concatenated into `HV1-IL-
    LINE-KEY X(10)` [common/slinvoiceMT.cbl:L427] by `move WS-Sil-Key to HV1-IL-LINE-
    KEY` [:L2789] and stored as `IL-LINE-KEY char(10)`, while its two members are ALSO
    carried separately as `IL-INVOICE` and `IL-LINE`.
    """

    COBOL_NAME: ClassVar[str] = "sil-Key"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L82"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SAINV-LINES-REC.IL-LINE-KEY"

    sil_invoice: int = field(metadata=_entry("SAINV-LINES-REC.IL-INVOICE"))

    # 07 sil-line pic 99. *> was binary-char. [copybooks/slwsinv.cob:L84] R-4:
    # declaration beats comment, as with `sih-test`. `pic 99` is zoned DISPLAY at scale
    # 0, therefore `int`.
    sil_line: int = field(metadata=_entry("SAINV-LINES-REC.IL-LINE"))


@dataclass(kw_only=True, slots=True)
class SilInvoiceLine:
    """``03 Invoice-Line occurs 40.`` [copybooks/slwsinv.cob:L81].

    R-4, one concept treated three ways. The OCCURS 40 is declared here and reported by
    this class's own descriptor - ``record_descriptor(...).occurs
    [copybooks/slwsinv2.cob:L91] has no OCCURS at all, being a redefine of a by ==.==`
    [common/slinvoiceMT.cbl:L458], to spare the memory.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Line"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L81"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Bodies.Invoice-Line"

    sil_key: SilKey = field(metadata=_entry("SAINV-LINES-REC.IL-LINE-KEY"))

    sil_product: str = field(metadata=_entry("SAINV-LINES-REC.IL-PRODUCT"))

    # 05 sil-pa pic xx. *> 25 [copybooks/slwsinv.cob:L86] R-4: the `xx` short form.
    # Character length 2, literal picture text kept.
    sil_pa: str = field(metadata=_entry("SAINV-LINES-REC.IL-PA"))

    # 05 sil-qty binary-short. *> 2 - 27 [copybooks/slwsinv.cob:L87] R-4, signedness:
    # signed binary here, `HV1-IL-QTY PIC 9(05) COMP` [common/slinvoiceMT.cbl:L432],
    # unsigned smallint in the table.
    sil_qty: int = field(metadata=_entry("SAINV-LINES-REC.IL-QTY"))

    sil_type: str = field(metadata=_entry("SAINV-LINES-REC.IL-TYPE"))

    sil_description: str = field(metadata=_entry("SAINV-LINES-REC.IL-DESCRIPTION"))

    sil_net: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-NET"))

    sil_unit: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-UNIT"))

    # 05 sil-discount pic 99v99 comp. *> 2 [copybooks/slwsinv.cob:L92] COMP and still
    # `Decimal`, because the scale is 2. Unsigned throughout.
    sil_discount: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-DISCOUNT"))

    sil_vat: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-VAT"))

    sil_vat_code: int = field(metadata=_entry("SAINV-LINES-REC.IL-VAT-CODE"))

    # 05 sil-update pic x. [copybooks/slwsinv.cob:L95] Carries `88 sil-analyised value
    # "Z".` [:L96] - single case, inside a file whose header condition names are dual
    # case. R-4.
    sil_update: str = field(metadata=_entry("SAINV-LINES-REC.IL-UPDATE"))

    # 05 sil-Back-Ordered pic x. [copybooks/slwsinv.cob:L97-L98] *> value space, or B
    # for a BO item.
    sil_back_ordered: str = field(
        metadata=_entry("SInvoice-Bodies.sil-Back-Ordered")
    )


@dataclass(kw_only=True, slots=True)
class SInvoiceBodies:
    """``01 SInvoice-Bodies.`` [copybooks/slwsinv.cob:L80] - the 40-line table.

    A tuple, not a list, because R-6 requires a deterministic shape and a fixed COBOL
    table is fixed.
    """

    COBOL_NAME: ClassVar[str] = "SInvoice-Bodies"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L80"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Bodies.SInvoice-Bodies"

    invoice_line: tuple[SilInvoiceLine, ...] = field(
        metadata=_entry("SInvoice-Bodies.Invoice-Line")
    )


# copybooks/slwsinv2.cob - the second view set, and the source of the names "WS
# replacement of (File Definition) For The Invoice File" [:L3], taken from the Sales
# copy and prefixed [:L13], with lowercase values [:L14] and invoice-letter references
# [:L15] removed, reaching its present shape "from fdinv2.cob with FD removed" [:L19].


@dataclass(kw_only=True, slots=True)
class InvoiceKey:
    """``03 Invoice-Key.`` [copybooks/slwsinv2.cob:L28] - the base view's key group.

    Ten bytes, the same two members the header view splits differently. No column is
    spelt from this view.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Key"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L28"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Record.Invoice-Key"

    invoice_nos: int = field(metadata=_entry("Invoice-Record.Invoice-Nos"))

    # 05 Item-Nos pic 99. *> was binary-char. [copybooks/slwsinv2.cob:L30] R-4.
    item_nos: int = field(metadata=_entry("Invoice-Record.Item-Nos"))


@dataclass(kw_only=True, slots=True)
class InvoiceRecord:
    """``01 Invoice-Record.`` [copybooks/slwsinv2.cob:L27] - the base buffer, 137.

    R-4, structural divergence from its own redefine and from the twin file: this view
    declares a FLAT `Invoice-Customer pic x(7)` [:L31] with no members, where `Invoice-
    Header` nests `ih-nos` and `ih-check` [:L43-L44] and `slwsinv.cob` nests `sih-nos`
    and `sih-check` [copybooks/slwsinv.cob:L24-L25].
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Record"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L27"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Record.Invoice-Record"

    invoice_key: InvoiceKey = field(metadata=_entry("Invoice-Record.Invoice-Key"))

    invoice_customer: str = field(
        metadata=_entry("Invoice-Record.Invoice-Customer")
    )

    invoice_date: int = field(metadata=_entry("Invoice-Record.Invoice-Date"))

    # 03 Filler pic x(10). [copybooks/slwsinv2.cob:L33] R-4: capital F, unlike its two
    # lower-case siblings below.
    filler_33: str = field(metadata=_entry("Invoice-Record.Filler"))

    invoice_type: int = field(metadata=_entry("Invoice-Record.Invoice-Type"))

    filler_35: str = field(metadata=_entry("Invoice-Record.filler#35"))

    filler_36: str = field(metadata=_entry("Invoice-Record.filler#36"))


@dataclass(kw_only=True, slots=True)
class IhCustomer:
    """``03 ih-customer.`` [copybooks/slwsinv2.cob:L42] - the customer key group."""

    COBOL_NAME: ClassVar[str] = "ih-customer"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L42"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-customer"

    ih_nos: str = field(metadata=_entry("Invoice-Header.ih-nos#43"))

    ih_check: int = field(metadata=_entry("Invoice-Header.ih-check#44"))


@dataclass(kw_only=True, slots=True)
class IhOrderView:
    """``03 filler redefines ih-order.`` [copybooks/slwsinv2.cob:L47].

    R-4, copybook-only, same as its twin: none of the four members has a bridge host
    variable or a column, only the base `IH-ORDER char(10)`. Declared in full
    regardless.
    """

    COBOL_NAME: ClassVar[str] = "filler"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L47"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.filler#47"

    ih_freq: str = field(metadata=_entry("Invoice-Header.ih-Freq"))

    ih_repeat: int = field(metadata=_entry("Invoice-Header.ih-Repeat"))

    filler_56: str = field(metadata=_entry("Invoice-Header.filler#56"))

    ih_last_date: int = field(metadata=_entry("Invoice-Header.ih-Last-Date"))


@dataclass(kw_only=True, slots=True)
class IhPrime:
    """``02 ih-prime.`` [copybooks/slwsinv2.cob:L39] - annotated "42 ??? bytes".

    R-4, and the question mark is the maintainer's: the annotation reads "42 ??? bytes"
    here where the twin reads a plain "42 bytes" [copybooks/slwsinv.cob:L19]. Quoted,
    not answered.
    """

    COBOL_NAME: ClassVar[str] = "ih-prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L39"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-prime"

    ih_invoice: int = field(metadata=_entry("Invoice-Header.ih-invoice#40"))

    # 03 ih-test pic 99. *> was binary-char. [copybooks/slwsinv2.cob:L41] R-4, twice
    # over. Declaration beats comment, as always. And note what is NOT here.
    ih_test: int = field(metadata=_entry("Invoice-Header.ih-test#41"))

    ih_customer: IhCustomer = field(metadata=_entry("Invoice-Header.ih-customer"))

    ih_date: int = field(metadata=_entry("Invoice-Header.ih-date#45"))

    ih_order: str = field(metadata=_entry("Invoice-Header.ih-order#46"))

    filler_47: IhOrderView = field(metadata=_entry("Invoice-Header.filler#47"))

    ih_type: int = field(metadata=_entry("Invoice-Header.ih-type#58"))

    ih_ref: str = field(metadata=_entry("Invoice-Header.ih-ref#59"))


@dataclass(kw_only=True, slots=True)
class IhFig:
    """``03 ih-fig comp-3.`` [copybooks/slwsinv2.cob:L62].

    Taking usage from a child's PICTURE line would type all eight as zoned DISPLAY and
    silently change every stored figure.
    """

    COBOL_NAME: ClassVar[str] = "ih-fig"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L62"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-fig#62"

    ih_p_c: Decimal = field(metadata=_entry("Invoice-Header.ih-p-c#63"))

    ih_net: Decimal = field(metadata=_entry("Invoice-Header.ih-net#64"))

    ih_extra: Decimal = field(metadata=_entry("Invoice-Header.ih-extra#65"))

    ih_carriage: Decimal = field(metadata=_entry("Invoice-Header.ih-carriage#66"))

    ih_vat: Decimal = field(metadata=_entry("Invoice-Header.ih-vat#67"))

    ih_discount: Decimal = field(metadata=_entry("Invoice-Header.ih-discount#68"))

    ih_e_vat: Decimal = field(metadata=_entry("Invoice-Header.ih-e-vat#69"))

    ih_c_vat: Decimal = field(metadata=_entry("Invoice-Header.ih-c-vat#70"))


@dataclass(kw_only=True, slots=True)
class IhSubPrime:
    """``02 ih-sub-prime.`` [copybooks/slwsinv2.cob:L60] - annotated "95 ??? bytes".

    R-4 twice on one line. The group name is lower case where the twin is mixed case,
    `Sih-Sub-Prime` [copybooks/slwsinv.cob:L41], even though `ih-prime` and `sih-prime`
    are both lower case - so the casing divergence is confined to this one group.
    """

    COBOL_NAME: ClassVar[str] = "ih-sub-prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L60"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-sub-prime"

    ih_description: str = field(metadata=_entry("Invoice-Header.ih-description"))

    ih_fig: IhFig = field(metadata=_entry("Invoice-Header.ih-fig#62"))

    # 03 ih-status pic x. [copybooks/slwsinv2.cob:L71] R-4.
    ih_status: str = field(metadata=_entry("Invoice-Header.ih-status#71"))

    ih_status_p: str = field(metadata=_entry("Invoice-Header.ih-status-P"))

    ih_status_l: str = field(metadata=_entry("Invoice-Header.ih-status-L"))

    ih_status_c: str = field(metadata=_entry("Invoice-Header.ih-status-C"))

    ih_status_a: str = field(metadata=_entry("Invoice-Header.ih-status-A"))

    ih_status_i: str = field(metadata=_entry("Invoice-Header.ih-status-I"))

    # 03 ih-lines binary-char. [copybooks/slwsinv2.cob:L80] R-4, column reordering:
    # declared third from the end of the group, written to the table at ordinal 29 after
    # `IH-CR` [common/slinvoiceMT.cbl:L419].
    ih_lines: int = field(metadata=_entry("Invoice-Header.ih-lines#80"))

    ih_deduct_days: int = field(
        metadata=_entry("Invoice-Header.ih-deduct-days#81")
    )

    # 03 ih-deduct-amt pic 999v99 comp. [copybooks/slwsinv2.cob:L82] Usage on its own
    # PICTURE line, so no inheritance - and `Decimal` despite COMP, because the scale is
    # 2.
    ih_deduct_amt: Decimal = field(
        metadata=_entry("Invoice-Header.ih-deduct-amt#82")
    )

    ih_deduct_vat: Decimal = field(
        metadata=_entry("Invoice-Header.ih-deduct-vat#83")
    )

    ih_days: int = field(metadata=_entry("Invoice-Header.ih-days#84"))

    ih_cr: int = field(metadata=_entry("Invoice-Header.ih-cr#85"))

    # 03 ih-day-book-flag pic x. [copybooks/slwsinv2.cob:L86] R-4: NO `value space`
    # here, where the twin writes one [copybooks/slwsinv.cob:L67]. No default is
    # declared, deliberately.
    ih_day_book_flag: str = field(
        metadata=_entry("Invoice-Header.ih-day-book-flag#86")
    )

    # 03 ih-update pic x. [copybooks/slwsinv2.cob:L88] Carries `88 ih-analyised value
    # "Z".` [:L89] - single case here, dual case in the twin. R-4: `analyised` keeps its
    # misspelling.
    ih_update: str = field(metadata=_entry("Invoice-Header.ih-update#88"))


@dataclass(kw_only=True, slots=True)
class IhInvoiceHeader:
    """``01 Invoice-Header redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L38].

    Nothing here keeps this view and :class:`InvoiceRecord` in step. In COBOL a
    REDEFINES shares storage, so the two are the same bytes seen two ways.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Header"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L38"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.Invoice-Header#38"

    ih_prime: IhPrime = field(metadata=_entry("Invoice-Header.ih-prime"))

    ih_sub_prime: IhSubPrime = field(
        metadata=_entry("Invoice-Header.ih-sub-prime")
    )


@dataclass(kw_only=True, slots=True)
class IlInvoiceLine:
    """``01 Invoice-Line redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L91].

    The view is documented at 80 bytes yet redefines a 137-byte record, so 57 bytes are
    unreachable through it. Recorded as declared; nothing is realigned (R-3, R-4).
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Line"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L91"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Line.Invoice-Line#91"

    il_invoice: int = field(metadata=_entry("Invoice-Line.il-invoice#92"))

    # 05 il-line pic 99. *> was binary-char. [copybooks/slwsinv2.cob:L93] R-4:
    # declaration beats comment. Zoned DISPLAY at scale 0, so `int`.
    il_line: int = field(metadata=_entry("Invoice-Line.il-line#93"))

    il_product: str = field(metadata=_entry("Invoice-Line.il-product#94"))

    il_pa: str = field(metadata=_entry("Invoice-Line.il-pa#95"))

    # 05 il-qty binary-short. [copybooks/slwsinv2.cob:L96] R-4, signedness: signed here,
    # unsigned smallint in the table.
    il_qty: int = field(metadata=_entry("Invoice-Line.il-qty#96"))

    il_type: str = field(metadata=_entry("Invoice-Line.il-type#97"))

    il_description: str = field(metadata=_entry("Invoice-Line.il-description#98"))

    il_net: Decimal = field(metadata=_entry("Invoice-Line.il-net#99"))

    il_unit: Decimal = field(metadata=_entry("Invoice-Line.il-unit#100"))

    il_discount: Decimal = field(metadata=_entry("Invoice-Line.il-discount#101"))

    il_vat: Decimal = field(metadata=_entry("Invoice-Line.il-vat#102"))

    il_vat_code: int = field(metadata=_entry("Invoice-Line.il-vat-code#103"))

    il_update: str = field(metadata=_entry("Invoice-Line.il-update#104"))

    # 05 il-Back-Ordered pic x. *> value space, or B for a BO item.
    # [copybooks/slwsinv2.cob:L106] Declared with a comment-only default, exactly as its
    # twin `sil-Back-Ordered` [copybooks/slwsinv.cob:L97-L98]; carried as declared (R-4).
    il_back_ordered: str = field(metadata=_entry("Invoice-Line.il-Back-Ordered"))


__all__: Final[tuple[str, ...]] = (
    "BRIDGE",
    "COPYBOOK_SLWSINV",
    "COPYBOOK_SLWSINV2",
    "ENTITY_FACADE",
    "HANDLER",
    "HEADER_TABLE",
    "IhCustomer",
    "IhFig",
    "IhInvoiceHeader",
    "IhOrderView",
    "IhPrime",
    "IhSubPrime",
    "IlInvoiceLine",
    "InvoiceKey",
    "InvoiceRecord",
    "LINES_TABLE",
    "SInvoiceBodies",
    "SInvoiceHeader",
    "SihCustomer",
    "SihFig",
    "SihOrderView",
    "SihPrime",
    "SihSubPrime",
    "SilInvoiceLine",
    "SilKey",
    "WsInvoiceKey",
    "cite_for",
    "condition_names_for",
    "condition_names_slwsinv",
    "condition_names_slwsinv2",
    "descriptor_for",
    "dictionary_key_for",
    "dictionary_keys_for",
    "drift_for",
    "record_descriptor",
    "record_dictionary_key",
)
