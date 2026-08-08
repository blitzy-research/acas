"""The Sales/Purchase-to-IRS posting transfer record [copybooks/wspost-irs.cob].

"This is NOT the same as the internal IRS posting file"
[copybooks/wspost-irs.cob:L6-L7], in the copybook's own words: this is the
transfer file `sl060` and `pl060` write and `irs030` consumes, table
`PSIRSPOST-REC`, while `copybooks/irswspost.cob` is the IRS module's own posting
record.

Two fields are signed in the `sign leading` form
[copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25] - the sign travels
in the field's first character rather than over its last digit, so the stored
bytes differ from an ordinary signed DISPLAY field and the storage class is
modelled rather than approximated.

The handler for this file rejects four of its published verbs outright
[common/acas008.cbl:L299-L307] and implements open-output as deleting every row
[common/acas008.cbl:L313-L319]; both belong to
`acas_posting.dal.acas008_spl_posting`.
"""

# The COBOL system, its generated MySQL bridge and its schema are the maintainer's work.

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = ["WsIrsPostKey", "WsIrsPostingRecord"]


# Both are the frozen sources' own spellings, case and hyphens intact, because
# dictionary lookup is exact and case-sensitive.

_TABLE: Final[str] = "PSIRSPOST-REC"

_COPYBOOK_RECORD: Final[str] = "WS-IRS-Posting-Record"


def _entry_keys_by_cobol_name() -> dict[str, str]:
    """Return this record's dictionary key for each COBOL field name.

    Both loader accessors are asked, because between them they cover the record and
    neither covers it alone.

    Returns:
        Every COBOL field name this copybook declares, against its key.
    """
    keys = {
        entry.copybook.name: str(entry.key)
        for entry in loader.entries_for_table(_TABLE)
        if entry.copybook is not None
    }
    for entry in loader.entries_for_copybook_record(_COPYBOOK_RECORD):
        if entry.copybook is not None:
            keys.setdefault(entry.copybook.name, str(entry.key))
    return keys


_ENTRY_KEYS: Final[dict[str, str]] = _entry_keys_by_cobol_name()


def _describe(cobol_name: str) -> FieldDescriptor:
    """Return the dictionary's description of one item of this record.

    Args:
        cobol_name: The item's COBOL name, exactly as `copybooks/wspost-irs.cob` spells
            it.

    Returns:
        The `FieldDescriptor` built from that item's dictionary entry, carrying its key
            and its copybook locator as provenance.
    """
    return FieldDescriptor.from_dictionary_key(_ENTRY_KEYS[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return one space for each character the copybook declares.

    The width comes from the dictionary, not from this file, so a default can never
    drift from the declaration it stands for.

    Args:
        descriptor: The item's description.

    Returns:
        The item's character default.
    """
    width = descriptor.character_length
    return " " * width if width is not None else ""


_POST_KEY: Final[FieldDescriptor] = _describe("WS-IRS-Post-Key")
_BATCH: Final[FieldDescriptor] = _describe("WS-IRS-Batch")
_POST_NUMBER: Final[FieldDescriptor] = _describe("WS-IRS-Post-Number")
_POST_CODE: Final[FieldDescriptor] = _describe("WS-IRS-Post-Code")
_POST_DATE: Final[FieldDescriptor] = _describe("WS-IRS-Post-Date")
_POST_DR: Final[FieldDescriptor] = _describe("WS-IRS-Post-DR")
_POST_CR: Final[FieldDescriptor] = _describe("WS-IRS-Post-CR")
_POST_AMOUNT: Final[FieldDescriptor] = _describe("WS-IRS-Post-Amount")
_POST_LEGEND: Final[FieldDescriptor] = _describe("WS-IRS-Post-Legend")
_VAT_AC_DEF: Final[FieldDescriptor] = _describe("WS-IRS-Vat-AC-Def")
_POST_VAT_SIDE: Final[FieldDescriptor] = _describe("WS-IRS-Post-Vat-Side")
_VAT_AMOUNT: Final[FieldDescriptor] = _describe("WS-IRS-Vat-Amount")


@dataclass(slots=True)
class WsIrsPostKey:
    """`03 WS-IRS-Post-Key.` [copybooks/wspost-irs.cob:L14].

    Not frozen, because those steps populate a record item by item before writing it.

    Attributes:
        ws_irs_batch: `WS-IRS-Batch`, the batch this posting belongs to.
        ws_irs_post_number: `WS-IRS-Post-Number`, the posting's number within that
            batch.
        FIELDS: The two descriptors, in copybook declaration order.
    """

    # 05 WS-IRS-Batch pic 9(5). unsigned zoned DISPLAY, scale 0
    # [copybooks/wspost-irs.cob:L15] Declared by the copybook alone.
    ws_irs_batch: int = 0

    ws_irs_post_number: int = 0

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_BATCH, _POST_NUMBER)


@dataclass(slots=True)
class WsIrsPostingRecord:
    """`01 WS-IRS-Posting-Record.` [copybooks/wspost-irs.cob:L13].

    Not frozen, because the four Sales and Purchase posting steps populate a record item
    by item before writing it [sales/sl060.cbl:L1126-L1142]. Members are in copybook
    declaration order, L14 through L25.

    Attributes:
        ws_irs_post_key: `WS-IRS-Post-Key`, the batch and posting number.
        ws_irs_post_code: `WS-IRS-Post-Code`, the posting's type code.
        ws_irs_post_date: `WS-IRS-Post-Date`, eight characters of date TEXT.
        ws_irs_post_dr: `WS-IRS-Post-DR`, the debit account.
        ws_irs_post_cr: `WS-IRS-Post-CR`, the credit account.
        ws_irs_post_amount: `WS-IRS-Post-Amount`, SIGN LEADING.
        ws_irs_post_legend: `WS-IRS-Post-Legend`, the posting narrative.
        ws_irs_vat_ac_def: `WS-IRS-Vat-AC-Def`, a defaults-table selector.
        ws_irs_post_vat_side: `WS-IRS-Post-Vat-Side`, which side the VAT falls on.
        ws_irs_vat_amount: `WS-IRS-Vat-Amount`, SIGN LEADING.
        FIELDS: The ten descriptors, in copybook declaration order, each with its
            dictionary key, its copybook locator, `cite()` and the unsettled `drift()`.
    """

    ws_irs_post_key: WsIrsPostKey = field(default_factory=WsIrsPostKey)

    ws_irs_post_code: str = _spaces(_POST_CODE)

    # 03 WS-IRS-Post-Date pic x(8). alphanumeric, 8 characters
    # [copybooks/wspost-irs.cob:L18] EIGHT characters of TEXT, a two-digit-year form - not a
    # date object and not a binary day number.
    ws_irs_post_date: str = _spaces(_POST_DATE)

    # 03 WS-IRS-Post-DR pic 9(5). unsigned zoned DISPLAY, scale 0
    # [copybooks/wspost-irs.cob:L19] FIVE digits. The General Ledger posting record's equivalent
    # is `9(6)` [copybooks/wspost.cob:L19].
    ws_irs_post_dr: int = 0

    ws_irs_post_cr: int = 0

    # 03 WS-IRS-Post-Amount pic s9(7)v99 sign leading. [copybooks/wspost-irs.cob:L21]
    # The sign clause is written exactly so - "sign leading", lower case, without `is`.
    ws_irs_post_amount: Decimal = Decimal("0.00")

    ws_irs_post_legend: str = _spaces(_POST_LEGEND)

    ws_irs_vat_ac_def: int = 0

    ws_irs_post_vat_side: str = _spaces(_POST_VAT_SIDE)

    ws_irs_vat_amount: Decimal = Decimal("0.00")

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _POST_KEY,
        _POST_CODE,
        _POST_DATE,
        _POST_DR,
        _POST_CR,
        _POST_AMOUNT,
        _POST_LEGEND,
        _VAT_AC_DEF,
        _POST_VAT_SIDE,
        _VAT_AMOUNT,
    )
