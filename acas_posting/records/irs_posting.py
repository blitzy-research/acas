"""The internal IRS posting record - `01 Posting-Record.` [copybooks/irswspost.cob:L8].

One dataclass mirroring the copybook's ten fields, two of which are signed in the
`sign is leading` form [copybooks/irswspost.cob:L14],
[copybooks/irswspost.cob:L18] - a zoned DISPLAY field whose sign travels in its
first character rather than over its last digit, so the stored bytes differ from
an ordinary signed DISPLAY field.

The table this record is written to carries THREE COLUMNS THAT APPEAR IN NO
COPYBOOK - `POST4-DAY`, `POST4-MONTH` and `POST4-YEAR` - which the bridge derives
from the date text under a guard [common/irspostingMT.cbl:L982-L987]. They are
therefore absent here by construction and belong to
`acas_posting.dal.acasirsub4_irs_posting`, which also reproduces the guard's
failure mode: the components stay zero while the raw date text is still stored.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: list[str] = ["PostingRecord"]


#  THE DICTIONARY LOOKUP  (rule R-5 - derived, never transcribed)

# The table whose entries describe this record.
_TABLE: Final[str] = "IRSPOSTING-REC"


def _copybook_descriptors() -> tuple[FieldDescriptor, ...]:
    """Describe every field of this record that a copybook declares.

    Keys are read from the dictionary rather than written out here: the loader is asked
    for the table's entries and each entry supplies its own key.

    Returns:
        The ten descriptors, in the order the dictionary yields them, which for this
            record is also copybook declaration order.
    """
    return tuple(
        FieldDescriptor.from_dictionary_key(entry.key)
        for entry in loader.entries_for_table(_TABLE)
        if entry.copybook is not None
    )


# The ten descriptors, in declaration order.
FIELDS: Final[tuple[FieldDescriptor, ...]] = _copybook_descriptors()

_BY_COBOL_NAME: Final[dict[str, FieldDescriptor]] = {
    descriptor.name: descriptor for descriptor in FIELDS
}


def _blanks(cobol_name: str) -> str:
    """Return spaces at the declared width of one alphanumeric field.

    The width comes from the field's dictionary entry, so a change in the frozen
    copybook reaches this module through the regenerated artifact instead of through an
    edit here.

    Args:
        cobol_name: The field name as the copybook spells it.

    Returns:
        A string of spaces at the field's declared character width.
    """
    width = _BY_COBOL_NAME[cobol_name].character_length
    # `character_length` is None for a numeric item; all four callers below are
    # alphanumeric, so the fallback is unreachable and exists only to keep the
    # expression total.
    return " " * (width or 0)


@dataclass(slots=True)
class PostingRecord:
    """`01 Posting-Record.` [copybooks/irswspost.cob:L8].

    The name is the copybook's own, undistinguished as the COBOL leaves it, even though
    it is the least telling of the three posting class names.
    """

    post_key: int = 0

    post_code: str = _blanks("Post-Code")

    post_date: str = _blanks("Post-Date")

    # These are ORDINALS 4, 5 AND 6 of IRSPOSTING-REC, `tinyint(2) unsigned NOT NULL`,
    # interleaved between POST4-DAT and POST4-DR [mysql/ACASDB.sql:L278-L280] rather
    # than appended.

    post_dr: int = 0

    post_cr: int = 0

    post_amount: decimal.Decimal = decimal.Decimal("0.00")

    post_legend: str = _blanks("Post-Legend")

    vat_ac_def: int = 0

    post_vat_side: str = _blanks("Post-Vat-Side")

    vat_amount: decimal.Decimal = decimal.Decimal("0.00")
