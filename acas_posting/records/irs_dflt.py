"""The IRS defaults record: one COBOL record holding a 33-entry table.

A CREATE from `copybooks/irswsdflt.cob`, thirteen lines declaring a table of
account codes indexed by entry number.

Two of those entries are the load-bearing ones: the IRS posting path reads
entries 31 and 32 as the two VAT control accounts
[irs/irs030.cbl:L1602], [irs/irs030.cbl:L1612], takes a snapshot of each before
its loop and rewrites both from those snapshots at end of job
[irs/irs030.cbl:L1704-L1708] - which is why an in-loop rewrite of the same
account is lost. The table is declared here exactly as the copybook does so that
the subscripts the COBOL uses remain the subscripts used here.
"""

from __future__ import annotations

import dataclasses
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# `__all__` is the one list in this module, and deliberately so.
__all__: Final[list[str]] = ["DefGroup", "WsIrsDefaultRecord"]


# The declaring copybook. Every dictionary entry used below must come from this file and
# no other.
_COPYBOOK: Final[str] = "copybooks/irswsdflt.cob"


def _keys_by_cobol_name() -> dict[str, str]:
    """Map each COBOL field name this copybook declares to its entry key.

    The keys are read back from the generated dictionary instead of being written out
    here, which is the ordering Agent Action Plan section 0.8.1 makes a directive rather
    than a preference.

    Returns:
        Copybook field name to dictionary entry key, in the document's own declaration
            order for this copybook, which makes the mapping deterministic (rule R-6).
            Five pairs.
    """
    keys: dict[str, str] = {}
    for entry in loader.entries_for_copybook_file(_COPYBOOK):
        declaration = entry.copybook
        # Belt and braces on the collision.
        assert declaration is not None, entry.key
        assert declaration.file == _COPYBOOK, declaration.file
        keys[declaration.name] = entry.key
    return keys


_KEYS: Final[dict[str, str]] = _keys_by_cobol_name()


def _described(cobol_name: str) -> FieldDescriptor:
    """Return the descriptor the dictionary holds for one COBOL field name.

    Args:
        cobol_name: The field name with the copybook's own casing, as `"Def-Acs"` -
            case-sensitive, like every name in the dictionary, and never one of the
            three other spellings the programs use.

    Returns:
        The descriptor built from that entry's COPYBOOK view, with its digits, scale,
            sign, usage and Python carrier exactly as the frozen declaration has them,
            and its provenance attached.
    """
    return FieldDescriptor.from_dictionary_key(_KEYS[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return the initial value of an alphanumeric item: spaces, full width.

    The width is the descriptor's own `character_length`, so the default cannot drift
    from the picture clause it comes from.

    Args:
        descriptor: An alphanumeric field's descriptor.

    Returns:
        As many spaces as the copybook declares characters.
    """
    assert descriptor.character_length is not None, descriptor.name
    return " " * descriptor.character_length


_DEF_GROUP: Final[FieldDescriptor] = _described("Def-Group")

_DEF_ACS: Final[FieldDescriptor] = _described("Def-Acs")
_DEF_CODES: Final[FieldDescriptor] = _described("Def-Codes")
_DEF_VAT: Final[FieldDescriptor] = _described("Def-Vat")

# The table's length is the copybook's own number, taken from the descriptor
# [copybooks/irswsdflt.cob:L9] so that it cannot drift from the declaration.
assert _DEF_GROUP.occurs is not None, _DEF_GROUP.dictionary_key
_OCCURS: Final[int] = _DEF_GROUP.occurs

_DEF_CODES_INITIAL: Final[str] = _spaces(_DEF_CODES)
_DEF_VAT_INITIAL: Final[str] = _spaces(_DEF_VAT)


# Two plain dataclasses, neither frozen.


@dataclasses.dataclass(slots=True)
class DefGroup:
    """One entry of the IRS defaults table: an account code and two codes.

    THIS IS THE IRS GROUP, from `copybooks/irswsdflt.cob`, behind table `IRSDFLT-REC`
    and handler `acasirsub3`.

    Attributes:
        def_acs: `Def-Acs pic 9(5)` - the default ACCOUNT CODE.
        def_codes: `Def-Codes pic xx` - the default posting code, two characters,
            initially spaces.
        def_vat: `Def-Vat pic x` - the default VAT code, one character, initially a
            space.
    """

    # The three 05 items of this group, in copybook declaration order. Order is fixed by
    # the copybook and is part of behaviour (rule R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _DEF_ACS,
        _DEF_CODES,
        _DEF_VAT,
    )

    def_acs: int = 0

    def_codes: str = _DEF_CODES_INITIAL

    def_vat: str = _DEF_VAT_INITIAL


@dataclasses.dataclass(slots=True)
class WsIrsDefaultRecord:
    """The IRS defaults record: one record that is entirely one table.

    `IRSDFLT-REC` has four columns; this record declares three fields. The fourth, `DEF-
    REC-KEY`, is declared by NO COPYBOOK.

    Attributes:
        def_group: The thirty-three entries of `Def-Group`, as a fixed-length tuple -
            `occurs 33` [copybooks/irswsdflt.cob:L9].
    """

    # The record's one member is its 03 group, so this carries a single descriptor whose
    # `occurs` is 33 - the shape the dictionary yields for this copybook, rather than a
    # thirty-three-fold expansion.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_DEF_GROUP,)

    def_group: tuple[DefGroup, ...] = dataclasses.field(
        default_factory=lambda: tuple(DefGroup() for _ in range(_OCCURS))
    )
