"""The system defaults record `SYSDEFLT-REC` [copybooks/wsdflt.cob].

A CREATE from twenty lines of frozen copybook declaring one record: a table of
thirty-three three-field entries followed by a filler. Mirrored entry for entry
with descriptors looked up in the generated dictionary (R-5).

The entries are addressed by subscript in the COBOL, so the table is declared
here with the same bounds and the same order; nothing is keyed by name.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = [
    "DefGroup",
    "SysDefaultRecord",
]


# Both are written once, here, and every lookup below goes through them.

_COPYBOOK: Final[str] = "copybooks/wsdflt.cob"
_TABLE: Final[str] = "SYSDEFLT-REC"


# ENTRY-KEY LOOKUP (rule R-5) Not one dictionary key is written out by hand below.


def _entry_keys_of_this_copybook() -> dict[str, str]:
    """Map each COBOL field name of `copybooks/wsdflt.cob` to its entry key.

    Two passes, in the order the Agent Action Plan's field-metadata direction implies -
    the table first, because the table name is what disambiguates this record from the
    IRS one, then the copybook file for the items that reach no column and so appear in
    no table result.

    Returns:
        Every COBOL field name this copybook declares, mapped to the key its dictionary
            entry carries. Six names for this record.
    """
    keyed: dict[str, str] = {}

    for entry in loader.entries_for_table(_TABLE):
        copybook_field = entry.copybook
        if copybook_field is None:
            continue
        keyed[copybook_field.name] = entry.key

    for entry in loader.entries_for_copybook_file(_COPYBOOK):
        copybook_field = entry.copybook
        if copybook_field is None:
            continue
        keyed.setdefault(copybook_field.name, entry.key)

    return keyed


_ENTRY_KEYS: Final[dict[str, str]] = _entry_keys_of_this_copybook()


def _descriptor(cobol_name: str) -> FieldDescriptor:
    """Return the looked-up descriptor for one field of THIS copybook.

    The single door every descriptor in this module comes through. It reads the storage
    description off the generated artifact rather than accepting one from a caller, and
    it states in code the thing the module docstring states in prose.

    Args:
        cobol_name: The field name exactly as the copybook spells it, with its own
            casing and hyphens - `"Def-Acs"`, not `"DEF-ACS"` and not `"def_acs"`.

    Returns:
        The descriptor the dictionary holds for that field, carrying its digits, scale,
            sign, usage, width and Python carrier, plus both halves of its provenance.

    Raises:
        loader.DictionaryLookupError: This copybook declares no such field, or the entry
            found for it is declared by some other copybook.
    """
    key = _ENTRY_KEYS.get(cobol_name)
    if key is None:
        raise loader.DictionaryLookupError(
            f"{_COPYBOOK} declares no field named {cobol_name!r} in the "
            f"generated data dictionary. The names it does declare are "
            f"{sorted(_ENTRY_KEYS)}. Field names are the copybook's own, "
            f"case-sensitive and hyphenated."
        )

    copybook_field = loader.copybook_field_for(key)
    if copybook_field is None or copybook_field.file != _COPYBOOK:
        declaring_file = (
            "no copybook" if copybook_field is None else copybook_field.file
        )
        raise loader.DictionaryLookupError(
            f"the entry keyed {key!r} is declared by {declaring_file}, not by "
            f"{_COPYBOOK}. This module models the General Ledger defaults "
            f"record; the record of the same COBOL 01-name in "
            f"copybooks/irswsdflt.cob is modelled by "
            f"acas_posting/records/irs_dflt.py and the two are deliberately "
            f"separate - their Def-Acs fields differ in width, scale and "
            f"storage class."
        )

    return FieldDescriptor.from_dictionary_key(key)


_DEFAULT_RECORD: Final[FieldDescriptor] = _descriptor("Default-Record")
_DEF_GROUP: Final[FieldDescriptor] = _descriptor("Def-Group")
_DEF_ACS: Final[FieldDescriptor] = _descriptor("Def-Acs")
_DEF_CODES: Final[FieldDescriptor] = _descriptor("Def-Codes")
_DEF_VAT: Final[FieldDescriptor] = _descriptor("Def-Vat")
_FILLER: Final[FieldDescriptor] = _descriptor("filler")


def _occurs_count(descriptor: FieldDescriptor) -> int:
    """Return a table item's OCCURS count, refusing to guess at one.

    Args:
        descriptor: The descriptor of a COBOL table item.

    Returns:
        The number of entries the item's OCCURS clause declares.

    Raises:
        loader.DictionaryLookupError: The dictionary records no OCCURS for the item.
            There is no defensible fallback.
    """
    occurs = descriptor.occurs
    if occurs is None:
        raise loader.DictionaryLookupError(
            f"the dictionary records no OCCURS count for "
            f"{descriptor.name!r} at {descriptor.source_locator}, so the "
            f"size of the table it heads cannot be taken from the frozen "
            f"source."
        )
    return occurs


def _character_width(descriptor: FieldDescriptor) -> int:
    """Return an alphanumeric item's declared width, refusing to guess at one.

    Args:
        descriptor: The descriptor of a COBOL alphanumeric item.

    Returns:
        The number of characters the item's PICTURE clause declares.

    Raises:
        loader.DictionaryLookupError: The dictionary records no character length for the
            item, so its space-filled initial value could not be built at the declared
            width.
    """
    width = descriptor.character_length
    if width is None:
        raise loader.DictionaryLookupError(
            f"the dictionary records no character length for "
            f"{descriptor.name!r} at {descriptor.source_locator}, so its "
            f"space-filled initial value cannot be built at the width the "
            f"frozen source declares."
        )
    return width


_DEF_GROUP_ENTRIES: Final[int] = _occurs_count(_DEF_GROUP)

_DEF_CODES_WIDTH: Final[int] = _character_width(_DEF_CODES)
_DEF_VAT_WIDTH: Final[int] = _character_width(_DEF_VAT)
_FILLER_WIDTH: Final[int] = _character_width(_FILLER)


@dataclass(slots=True)
class DefGroup:
    """One entry of the `03 Def-Group occurs 33.` defaults table.

    MUTABLE on purpose, and never `frozen=True`: the defaults are read and written by
    the maintenance programs, and the bridge writes straight into an entry on the way in
    from the database [common/dfltMT.cbl:L579-L581].

    Attributes:
        def_acs: `Def-Acs`, the amount. `Decimal` at scale 2.
        def_codes: `Def-Codes`, two characters.
        def_vat: `Def-Vat`, one character.
    """

    # Traceability metadata (R-5), not record content. `RECORD` is the group item itself
    # and `FIELDS` its three subordinate items in declaration order.
    RECORD: ClassVar[FieldDescriptor] = _DEF_GROUP
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _DEF_ACS,
        _DEF_CODES,
        _DEF_VAT,
    )

    # Def-Acs pic 9(4)v99 comp [copybooks/wsdflt.cob:L16] SCALED, so `Decimal` and not
    # `int` - six digits, four of them integral, two fractional, unsigned, binary
    # storage.
    def_acs: Decimal = Decimal("0.00")

    def_codes: str = " " * _DEF_CODES_WIDTH

    # Def-Vat pic x [copybooks/wsdflt.cob:L18] One character, space-filled on the same
    # terms as `def_codes` - a single space rather than the empty string, so that every
    # character field in this module starts at its declared width, as COBOL INITIALIZE
    # leaves it.
    def_vat: str = " " * _DEF_VAT_WIDTH


@dataclass(slots=True)
class SysDefaultRecord:
    """The `01 Default-Record.` General Ledger / system defaults record.

    THE CLASS NAME CARRIES A `Sys` PREFIX ITS COBOL NAME DOES NOT.

    Attributes:
        def_group: `Def-Group`, the thirty-three entry table, as a tuple of thirty-three
            distinct `DefGroup` instances in index order.
        filler: `filler`, the 793 bytes of padding that take the record to 1024.
    """

    # Traceability metadata (R-5), not record content. `RECORD` is the 01-level item
    # [copybooks/wsdflt.cob:L14].
    RECORD: ClassVar[FieldDescriptor] = _DEFAULT_RECORD
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _DEF_GROUP,
        _FILLER,
    )

    # Def-Group occurs 33 [copybooks/wsdflt.cob:L15] A TUPLE of thirty-three distinct
    # entries, built in index order, because a COBOL table is fixed-length.
    def_group: tuple[DefGroup, ...] = dataclass_field(
        default_factory=lambda: tuple(
            DefGroup() for _ in range(_DEF_GROUP_ENTRIES)
        )
    )

    # filler pic x(793) [copybooks/wsdflt.cob:L19] Padding, and nothing else.
    filler: str = " " * _FILLER_WIDTH
