"""The Sales open-item record - OTM3, `SAITM3-REC` [copybooks/slwsoi3.cob].

The sales ledger's unpaid-item register, mirrored field for field. `sl060` writes
these rows and applies credit against them; `sl100` clears them and reads
`OI-Date` against `OI-Date-Cleared` to compute the payment-days figures.

The date and batch fields are declared `binary-long`, so they are Python `int`
here and their arithmetic truncates as integer arithmetic does - which is what
makes `sl100`'s payment-days average reproducible
[sales/sl100.cbl:L503], [sales/sl100.cbl:L511].
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Final, Mapping

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# `ConditionName` and `Drift` are imported for the two return annotations below and for
# nothing else.
from acas_posting.dictionary.loader import ConditionName, Drift

__all__: Final[tuple[str, ...]] = (
    "Filler1",
    "Filler2",
    "Oi3Key",
    "OiBatch",
    "OiCustomer",
    "OiHeader",
    "OiKey",
    "OpenItemRecord3",
    "WsOtm3Record",
    "cite",
    "cobol_name_for",
    "condition_names_for",
    "copybook_source_for",
    "descriptor_for",
    "dictionary_key_for",
    "drift_for",
)


# Each attribute below declares the verbatim COBOL name, the dictionary key and the
# copybook locator.

_COBOL_NAME: Final[str] = "cobol_name"
_DICTIONARY_KEY: Final[str] = "dictionary_key"
_COPYBOOK_SOURCE: Final[str] = "copybook_source"


def _cobol(name: str, key: str, source: str) -> Mapping[str, str]:
    """Bind one attribute to its COBOL declaration and its dictionary entry.

    Args:
        name: The COBOL data-name VERBATIM, case and hyphens intact - `"OI-Hold-flag"`,
            `"OI-B-Nos"`, `"OI3-Invoice"`, `"filler"`. Never rewritten and never snake-
            cased.
        key: The dictionary entry key - `<TABLE-NAME>.<COLUMN-NAME>` for a column-mapped
            field, `<COPYBOOK-RECORD>.<FIELD-NAME>` for a copybook-only one. Obtained
            from the loader, never assembled by upper casing `name`.
        source: The `<path>:L<n>` locator of the declaration, so a reader has the
            citation at the declaration site without a dictionary read.

    Returns:
        The metadata mapping for `dataclasses.field`.
    """
    return {_COBOL_NAME: name, _DICTIONARY_KEY: key, _COPYBOOK_SOURCE: source}


def _metadata_for(record: Any, attribute: str) -> Mapping[str, Any]:
    """Return one attribute's metadata mapping from a record class or instance.

    Args:
        record: Any dataclass this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        That attribute's metadata mapping.

    Raises:
        AttributeError: The record declares no such attribute.
    """
    for member in dataclasses.fields(record):
        if member.name == attribute:
            return member.metadata
    declared = ", ".join(member.name for member in dataclasses.fields(record))
    raise AttributeError(
        "%s declares no attribute %r. Its attributes, in copybook declaration "
        "order, are: %s" % (_record_name(record), attribute, declared)
    )


def _record_name(record: Any) -> str:
    """Return a record class's or instance's class name, for a message."""
    return record.__name__ if isinstance(record, type) else type(record).__name__


# Module-level FUNCTIONS taking a record and an attribute name - deliberately not
# properties or attributes on the records themselves, so that none of them can be
# mistaken for a stored field of the COBOL layout (rule R-3).


def descriptor_for(record: Any, attribute: str) -> FieldDescriptor:
    """Return the storage description the dictionary holds for one attribute.

    The descriptor reports the COPYBOOK view of the field - its own digits, scale,
    signedness and usage - and never a blend of the copybook, bridge and column views.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name, for example `"oi_net"`.

    Returns:
        The field's descriptor.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so. Allowed to propagate untouched
            because its own message lists near misses and restates the key convention.
    """
    return FieldDescriptor.from_dictionary_key(dictionary_key_for(record, attribute))


def dictionary_key_for(record: Any, attribute: str) -> str:
    """Return one attribute's dictionary entry key.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The entry key - `"SAITM3-REC.OI3-NET"` for a column-mapped field, `"OI-
            Header.OI-Approp#38"` for a copybook-only one.

    Raises:
        AttributeError: The record declares no such attribute.
    """
    return str(_metadata_for(record, attribute)[_DICTIONARY_KEY])


def cobol_name_for(record: Any, attribute: str) -> str:
    """Return one attribute's COBOL data-name, verbatim.

    Case and hyphens are exactly as the frozen copybook writes them, which is why `"OI-
    Hold-flag"` keeps its lower-case f, `"OI-key"` its lower-case k and `"OI-Cr"` its
    lower-case r - the purchase copybook spells that last one `OI-CR`, and the two are
    different records (rule R-4).

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The COBOL data-name.

    Raises:
        AttributeError: The record declares no such attribute.
    """
    return str(_metadata_for(record, attribute)[_COBOL_NAME])


def copybook_source_for(record: Any, attribute: str) -> str:
    """Return the `<path>:L<n>` locator of one attribute's COBOL declaration.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The locator, for example `"copybooks/slwsoi.cob:L37"`.

    Raises:
        AttributeError: The record declares no such attribute.
    """
    return str(_metadata_for(record, attribute)[_COPYBOOK_SOURCE])


def cite(record: Any, attribute: str) -> str:
    """Return the three-locator provenance string for one attribute.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The provenance string.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so.
    """
    return loader.cite(dictionary_key_for(record, attribute))


def drift_for(record: Any, attribute: str) -> Drift:
    """Return the UNSETTLED disagreement between one field's three views.

    The copybook, the bridge host variable and the MySQL column disagree for most fields
    of this record - on name for twenty-seven of the twenty-eight columns, on storage
    class for nineteen, on signedness for four, on digit width for one and on character
    length for one.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The drift object, with its per-aspect flags and its detail sentences.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so.
    """
    return loader.drift_for(dictionary_key_for(record, attribute))


def condition_names_for(record: Any, attribute: str) -> tuple[ConditionName, ...]:
    """Return the 88-level condition names declared on one attribute, as DATA.

    A tuple, never a list, and empty for every attribute of this record except
    `OiHeader`'s `oi_status`, which carries the two the copybook declares at
    [copybooks/slwsoi.cob:L48-L49]. Each carries its name, its value-clause text and its
    locator.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The condition names in declaration order, empty if the field declares none.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so.
    """
    copybook_field = loader.copybook_field_for(dictionary_key_for(record, attribute))
    if copybook_field is None:
        return ()
    return tuple(copybook_field.condition_names)


@dataclass
class WsOtm3Record:
    """The raw 118-byte buffer `WS-OTM3-Record`, declared elementary.

    R-4: THE SAME IDENTIFIER NAMES SOMETHING ELSE ENTIRELY IN THE BRIDGE.
    [copybooks/slwsoi3.cob:L18-L19] copies the body copybook while KEEPING the copied
    name and ADDING a redefines clause, so `WS-OTM3-Record` there is this buffer.
    """

    ws_otm3_record: str = field(
        metadata=_cobol(
            "WS-OTM3-Record",
            "WS-OTM3-Record.WS-OTM3-Record",
            "copybooks/slwsoi3.cob:L9",
        )
    )


@dataclass
class Oi3Key:
    """The fifteen-byte key group `OI3-Key`, customer plus invoice number.

    R-4: DUAL MATERIALISATION. Both children are ALSO stored, as `OI3-CUSTOMER` and
    `OI3-INVOICE` - but from the BODY copybook's `OI-Customer` and `OI-Invoice`, not
    from these two.
    """

    oi3_customer: str = field(
        metadata=_cobol(
            "OI3-Customer",
            "Open-Item-Record-3.OI3-Customer",
            "copybooks/slwsoi3.cob:L13",
        )
    )
    oi3_invoice: int = field(
        metadata=_cobol(
            "OI3-Invoice",
            "Open-Item-Record-3.OI3-Invoice",
            "copybooks/slwsoi3.cob:L14",
        )
    )


@dataclass
class OpenItemRecord3:
    """The `Open-Item-Record-3` view redefining the 118-byte buffer.

    The full field set arrives at [copybooks/slwsoi3.cob:L18-L19] through a COPY of
    `copybooks/slwsoi.cob`, producing a THIRD view over the same 118 bytes - `OiHeader`
    in section B below. Base and views are not kept in step with one another.
    """

    oi3_key: Oi3Key = field(
        metadata=_cobol("OI3-Key", "SAITM3-REC.OI3-KEY", "copybooks/slwsoi3.cob:L12")
    )
    oi3_date: int = field(
        metadata=_cobol(
            "OI3-Date", "Open-Item-Record-3.OI3-Date", "copybooks/slwsoi3.cob:L15"
        )
    )
    # The one ELEMENTARY filler in this module - 99 characters, not a group. It is
    # declared rather than dropped: rule R-3 removes nothing.
    filler_1: str = field(
        metadata=_cobol(
            "filler", "Open-Item-Record-3.filler", "copybooks/slwsoi3.cob:L16"
        )
    )


@dataclass
class OiCustomer:
    """The seven-byte group `OI-Customer`, number plus check digit."""

    oi_nos: str = field(
        metadata=_cobol("OI-Nos", "OI-Header.OI-Nos#11", "copybooks/slwsoi.cob:L11")
    )
    oi_check: int = field(
        metadata=_cobol("OI-Check", "OI-Header.OI-Check#12", "copybooks/slwsoi.cob:L12")
    )


@dataclass
class OiKey:
    """The fifteen-byte key group `OI-key`, spelled with a lower-case key.

    R-4: the copybook writes `OI-key` with a LOWER-CASE k, while the purchase copybook
    writes `OI-Key` with a capital one [copybooks/plwsoi.cob:L13]. The casing is
    preserved exactly, and it is load-bearing rather than cosmetic.
    """

    oi_customer: OiCustomer = field(
        metadata=_cobol(
            "OI-Customer", "SAITM3-REC.OI3-CUSTOMER", "copybooks/slwsoi.cob:L10"
        )
    )
    # R-4: DECLARATION BEATS COMMENT. `pic 9(8). *> was binary-long.` - zoned display,
    # eight digits, scale zero, so the carrier is `int`.
    oi_invoice: int = field(
        metadata=_cobol(
            "OI-Invoice", "SAITM3-REC.OI3-INVOICE", "copybooks/slwsoi.cob:L13"
        )
    )


@dataclass
class OiBatch:
    """The batch group `OI-Batch`, carrying `comp` for both children.

    A GROUP CARRYING A USAGE CLAUSE. Neither child below writes a usage of its own, so
    both inherit `comp` from this header - and both descriptors record that provenance,
    reporting `usage_declared_at` GROUP with `usage_inherited_from` `"OI-Batch"`.
    """

    oi_b_nos: int = field(
        metadata=_cobol(
            "OI-B-Nos", "SAITM3-REC.OI3-BATCH-NOS", "copybooks/slwsoi.cob:L17"
        )
    )
    oi_b_item: int = field(
        metadata=_cobol(
            "OI-B-Item", "SAITM3-REC.OI3-BATCH-ITEM", "copybooks/slwsoi.cob:L18"
        )
    )


@dataclass
class Filler2:
    """The unnamed `filler` group carrying `comp-3` for ten children.

    The group is declared rather than dropped even though it has no column and no host
    variable, for two reasons.
    """

    oi_p_c: Decimal = field(
        metadata=_cobol("OI-P-C", "SAITM3-REC.OI3-P-C", "copybooks/slwsoi.cob:L36")
    )
    oi_net: Decimal = field(
        metadata=_cobol("OI-Net", "SAITM3-REC.OI3-NET", "copybooks/slwsoi.cob:L37")
    )
    # R-4: `OI-Approp` HAS NO HOST VARIABLE - `grep -inc "approp" common/otm3MT.cbl`
    # returns 0.
    oi_approp: Decimal = field(
        metadata=_cobol(
            "OI-Approp", "OI-Header.OI-Approp#38", "copybooks/slwsoi.cob:L38"
        )
    )
    oi_extra: Decimal = field(
        metadata=_cobol("OI-Extra", "SAITM3-REC.OI3-EXTRA", "copybooks/slwsoi.cob:L40")
    )
    oi_carriage: Decimal = field(
        metadata=_cobol(
            "OI-Carriage", "SAITM3-REC.OI3-CARRIAGE", "copybooks/slwsoi.cob:L41"
        )
    )
    oi_vat: Decimal = field(
        metadata=_cobol("OI-Vat", "SAITM3-REC.OI3-VAT", "copybooks/slwsoi.cob:L42")
    )
    oi_discount: Decimal = field(
        metadata=_cobol(
            "OI-Discount", "SAITM3-REC.OI3-DISCOUNT", "copybooks/slwsoi.cob:L43"
        )
    )
    oi_e_vat: Decimal = field(
        metadata=_cobol("OI-E-Vat", "SAITM3-REC.OI3-E-VAT", "copybooks/slwsoi.cob:L44")
    )
    oi_c_vat: Decimal = field(
        metadata=_cobol("OI-C-Vat", "SAITM3-REC.OI3-C-VAT", "copybooks/slwsoi.cob:L45")
    )
    oi_paid: Decimal = field(
        metadata=_cobol("OI-Paid", "SAITM3-REC.OI3-PAID", "copybooks/slwsoi.cob:L46")
    )


@dataclass
class Filler1:
    """The unnamed `filler` group at `02` level, holding fifteen children.

    Unlike `Filler2` this header carries NO usage clause of its own, so its descriptor
    reports `usage_declared_at` DEFAULT. It has no column and no host variable.
    """

    # R-4: SIGN LOST AT THE BRIDGE, NOT AT THE DATABASE. `binary-long` is signed; the
    # host variable is `9(10) COMP`, unsigned [common/otm3MT.cbl:L305]; the column is
    # `int(8) unsigned`.
    oi_date: int = field(
        metadata=_cobol("OI-Date", "SAITM3-REC.OI3-DAT", "copybooks/slwsoi.cob:L15")
    )
    oi_batch: OiBatch = field(
        metadata=_cobol("OI-Batch", "SAITM3-REC.OI3-BATCH", "copybooks/slwsoi.cob:L16")
    )
    # R-4: NUMERIC TO CHARACTER. `pic 9` in the copybook, `X(1)` in the host variable
    # [common/otm3MT.cbl:L309], `char(1)` in the schema.
    oi_type: int = field(
        metadata=_cobol("OI-Type", "SAITM3-REC.OI3-TYPE", "copybooks/slwsoi.cob:L19")
    )
    # R-4: WIDTH DRIFT, 25 TO 32.
    oi_description: str = field(
        metadata=_cobol(
            "OI-Description", "SAITM3-REC.OI3-DESCRIPTION", "copybooks/slwsoi.cob:L32"
        )
    )
    # `03 OI-Hold-flag pic x. *> Q(uery)` purchase counterpart declares `88 payment-held
    # value "H".` [copybooks/plwsoi.cob:L39].
    oi_hold_flag: str = field(
        metadata=_cobol(
            "OI-Hold-flag", "SAITM3-REC.OI3-HOLD-FLAG", "copybooks/slwsoi.cob:L33"
        )
    )
    oi_unapl: str = field(
        metadata=_cobol("OI-Unapl", "SAITM3-REC.OI3-UNAPL", "copybooks/slwsoi.cob:L34")
    )
    filler_2: Filler2 = field(
        metadata=_cobol("filler", "OI-Header.filler#35", "copybooks/slwsoi.cob:L35")
    )
    # R-4: NUMERIC TO CHARACTER, and the pointed instance of it.
    oi_status: int = field(
        metadata=_cobol(
            "OI-Status", "SAITM3-REC.OI3-STATUS", "copybooks/slwsoi.cob:L47"
        )
    )
    oi_deduct_days: int = field(
        metadata=_cobol(
            "OI-Deduct-Days", "SAITM3-REC.OI3-DEDUCT-DAYS", "copybooks/slwsoi.cob:L50"
        )
    )
    # THE OPPOSITE CASE TO GROUP-USAGE INHERITANCE, and the contrast that makes the rule
    # readable.
    oi_deduct_amt: Decimal = field(
        metadata=_cobol(
            "OI-Deduct-Amt", "SAITM3-REC.OI3-DEDUCT-AMT", "copybooks/slwsoi.cob:L51"
        )
    )
    oi_deduct_vat: Decimal = field(
        metadata=_cobol(
            "OI-Deduct-Vat", "SAITM3-REC.OI3-DEDUCT-VAT", "copybooks/slwsoi.cob:L52"
        )
    )
    # R-4: SIGN LOST AT THE BRIDGE - signed `binary-Char`, unsigned `9(03) COMP`
    # [common/otm3MT.cbl:L326], `tinyint(3) unsigned`. Surfaced unsettled.
    oi_days: int = field(
        metadata=_cobol("OI-Days", "SAITM3-REC.OI3-DAYS", "copybooks/slwsoi.cob:L53")
    )
    oi_cr: int = field(
        metadata=_cobol("OI-Cr", "SAITM3-REC.OI3-CR", "copybooks/slwsoi.cob:L54")
    )
    oi_applied: str = field(
        metadata=_cobol(
            "OI-Applied", "SAITM3-REC.OI3-APPLIED", "copybooks/slwsoi.cob:L55"
        )
    )
    # R-4: SIGN LOST AT THE BRIDGE - signed `binary-long`, unsigned `9(10) COMP`
    # [common/otm3MT.cbl:L329], `int(8) unsigned`. Its name, unlike `OI-Date`'s, is NOT
    # truncated. R-2.
    oi_date_cleared: int = field(
        metadata=_cobol(
            "OI-Date-Cleared", "SAITM3-REC.OI3-DATE-CLEARED", "copybooks/slwsoi.cob:L56"
        )
    )


@dataclass
class OiHeader:
    """The sales open-item record `OI-Header`, two groups over 29 leaves.

    Exactly TWO direct children, because everything from L15 to L56 nests inside the
    unnamed level-02 filler: the key group, then that filler.
    """

    oi_key: OiKey = field(
        metadata=_cobol("OI-key", "OI-Header.OI-key", "copybooks/slwsoi.cob:L9")
    )
    filler_1: Filler1 = field(
        metadata=_cobol("filler", "OI-Header.filler#14", "copybooks/slwsoi.cob:L14")
    )
