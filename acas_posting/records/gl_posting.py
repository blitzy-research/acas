"""General Ledger posting record - `01 WS-Posting-Record` [copybooks/wspost.cob:L12].

A CREATE from `copybooks/wspost.cob`, the 96-byte record `gl070` reads and
`gl072` posts: the batch and posting numbers, the DR and CR accounts with their
profit-centre codes, the amount, the VAT account, side and amount, and the
legend.

Three of its field names collide with names in the two other posting copybooks
the same programs `COPY`, which is why the COBOL has to qualify them -
`post-code in WS-Posting-Record` [general/gl070.cbl:L497] and `vat-ac of
WS-Posting-Record` [general/gl070.cbl:L521], [general/gl070.cbl:L525]. The
collision is preserved: the names are the copybook's own and are not
disambiguated by renaming.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = ["WsPostKey", "WsPostingRecord"]


#  KEY LOOKUP  (R-5)  -  asked of the dictionary, never spelled out

# The two names the dictionary is keyed by for this record.
_TABLE_NAME: Final[str] = "GLPOSTING-REC"
_RECORD_NAME: Final[str] = "WS-Posting-Record"


def _key_by_cobol_name() -> dict[str, str]:
    """Map every COBOL field name in this record to its dictionary key.

    Two passes, because the record is keyed two ways and a single pass would miss three
    fields.

    Returns:
        COBOL field name, verbatim from the copybook, to dictionary key.
    """
    mapping: dict[str, str] = {}
    for entry in loader.entries_for_table(_TABLE_NAME):
        if entry.copybook is not None:
            mapping[entry.copybook.name] = entry.key
    for entry in loader.entries_for_copybook_record(_RECORD_NAME):
        if entry.copybook is not None and entry.column is None:
            mapping[entry.copybook.name] = entry.key
    return mapping


_KEY_BY_COBOL_NAME: Final[dict[str, str]] = _key_by_cobol_name()


def _descriptor(cobol_name: str) -> FieldDescriptor:
    """Return the descriptor the dictionary holds for one COBOL field.

    The single point at which this module reaches the dictionary for storage metadata.
    Memoised upstream on the key, so the repeated calls below cost one lookup each.

    Args:
        cobol_name: The field name exactly as the copybook spells it, hyphens and mixed
            case intact - ``"WS-Post-rrn"``, not ``"ws_post_rrn"`` and not ``"WS-POST-
            RRN"``.

    Returns:
        The descriptor, carrying the copybook view of the field's storage plus the
            provenance that makes it auditable against the frozen source.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_BY_COBOL_NAME[cobol_name])


def _spaces(cobol_name: str) -> str:
    """Return the declared width of an alphanumeric field, in spaces.

    The default for every ``str`` attribute below, and the reason they are space-filled
    rather than empty.

    Args:
        cobol_name: The field name exactly as the copybook spells it.

    Returns:
        That many spaces, or the empty string for an item the dictionary gives no
            character length - which none of this record's four alphanumeric fields
            does.
    """
    declared = _descriptor(cobol_name).character_length
    return " " * declared if declared is not None else ""


# Both money fields default to a scale-2 zero.
_MONEY_ZERO: Final[decimal.Decimal] = decimal.Decimal("0.00")


@dataclass(slots=True)
class WsPostKey:
    """``03 WS-Post-Key.`` [copybooks/wspost.cob:L14].

    Not frozen. ``gl070`` assigns through this group field by field, at
    [general/gl070.cbl:L495-L496], so the attributes must be settable.

    Attributes:
        batch: Batch number. ``05 Batch pic 9(5).``.
        post_number: Number within the batch. ``05 Post-Number pic 9(5).``.
    """

    # Batch pic 9(5) DISPLAY, unsigned, scale 0 no byte offset comment
    # [copybooks/wspost.cob:L15] -> key WS-Posting-Record.Batch Keyed under the copybook
    # record, not the table.
    batch: int = 0

    post_number: int = 0

    # Declaration order, as a tuple so it cannot be added to at runtime (R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Batch"),
        _descriptor("Post-Number"),
    )


@dataclass(slots=True)
class WsPostingRecord:
    """``01 WS-Posting-Record.`` [copybooks/wspost.cob:L12].

    Not frozen, and deliberately so. ``gl070`` reads this record and ``gl072``'s work
    stream is built from it; the posting programs assign into it one field at a time, so
    a frozen dataclass would be unusable.

    Attributes:
        ws_post_rrn: Relative-record replacement, and the table's primary key. See its
            comment for the never-loaded host variable the dictionary records against it.
        ws_post_key: The batch and post number, as a group.
        post_code: Posting type code.
        post_date: Posting date, as eight characters of text.
        post_dr: Debit account number.
        dr_pc: Debit profit centre.
        post_cr: Credit account number.
        cr_pc: Credit profit centre.
        post_amount: Posted amount, signed, scale 2.
        post_legend: Free-text narrative.
        vat_ac: VAT account number.
        vat_pc: VAT profit centre.
        post_vat_side: Which side of the posting the VAT falls on.
        vat_amount: VAT amount, signed, scale 2.
    """

    # WS-Post-rrn pic 9(5) DISPLAY, unsigned, scale 0 [copybooks/wspost.cob:L13] -> key
    # GLPOSTING-REC.POST-RRN. The mixed case is the COBOL's own. Its host variable
    # HV-POST-RRN is declared and fetched but never loaded from the record
    # [common/glpostingMT.cbl:L282], which the dictionary entry records with its own
    # ambiguity reference rather than repairing.
    ws_post_rrn: int = 0

    # WS-Post-Key group, no picture, no storage of its own, no offset
    # [copybooks/wspost.cob:L14] -> key GLPOSTING-REC.POST-KEY.
    ws_post_key: WsPostKey = field(default_factory=WsPostKey)

    # Post-Code pic xx alphanumeric, 2 characters *> 12 [copybooks/wspost.cob:L17] ->
    # key GLPOSTING-REC.POST-CODE. One of the names that collide across the three posting
    # copybooks; the qualified references that collision forces are anomaly A-21, and they
    # are in the programs [general/gl070.cbl:L497] rather than here.
    post_code: str = _spaces("Post-Code")

    # Post-Date pic x(8) alphanumeric, 8 characters *> 20 [copybooks/wspost.cob:L18] ->
    # key GLPOSTING-REC.POST-DAT EIGHT characters of text. Not ten, not a binary day
    # number.
    post_date: str = _spaces("Post-Date")

    post_dr: int = 0

    dr_pc: int = 0

    post_cr: int = 0

    cr_pc: int = 0

    # Post-Amount pic s9(8)v99 DISPLAY zoned, signed, sign TRAILING and INCLUDED, 10
    # digits, scale 2, 10 bytes *> 46 [copybooks/wspost.cob:L23] -> key GLPOSTING-
    # REC.POST-AMOUNT `decimal.Decimal`, never a binary floating-point carrier and never
    # an int - it has a scale (R-2).
    post_amount: decimal.Decimal = _MONEY_ZERO

    post_legend: str = _spaces("Post-Legend")

    vat_ac: int = 0

    vat_pc: int = 0

    # Post-Vat-Side pic xx alphanumeric, 2 characters *> 86 [copybooks/wspost.cob:L27]
    # -> key GLPOSTING-REC.POST-VAT-SIDE.
    post_vat_side: str = _spaces("Post-Vat-Side")

    # Vat-Amount pic s9(8)v99 DISPLAY zoned, signed, *> 96 sign TRAILING and INCLUDED,
    # 10 digits, scale 2, 10 bytes [copybooks/wspost.cob:L28] -> key GLPOSTING-REC.VAT-
    # AMOUNT The record's last field, and the offset that closes the copybook's own
    # arithmetic at 96 while the declared pictures reach 98 without `WS-Post-rrn` and
    # 103 with it. That disagreement is this copybook's own, recorded at
    # [copybooks/wspost.cob:L6-L7]; the registered length anomaly A-15 is `wsbatch.cob`'s,
    # not this one.
    vat_amount: decimal.Decimal = _MONEY_ZERO

    # Declaration order, L13 through L28, as a tuple (R-6). Fourteen descriptors for
    # fourteen attributes and fourteen columns; the key group's own two members are on
    # `WsPostKey.FIELDS`.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("WS-Post-rrn"),
        _descriptor("WS-Post-Key"),
        _descriptor("Post-Code"),
        _descriptor("Post-Date"),
        _descriptor("Post-DR"),
        _descriptor("DR-PC"),
        _descriptor("Post-CR"),
        _descriptor("CR-PC"),
        _descriptor("Post-Amount"),
        _descriptor("Post-Legend"),
        _descriptor("Vat-AC"),
        _descriptor("Vat-PC"),
        _descriptor("Post-Vat-Side"),
        _descriptor("Vat-Amount"),
    )
