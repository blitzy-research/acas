"""The system final-accounts record `01 Final-Record.` [copybooks/wsfinal.cob:L10].

Twelve lines of frozen copybook, two of which are the whole record: a table of 26
sixteen-character slots and a 608-character FILLER. Mirrored as written, with
descriptors looked up in the generated dictionary (R-5).

The FILLER is declared rather than omitted, because the record's byte layout is
what the bridge writes and a missing filler would move every field after it.
This record carries no fractional field, so the exact-decimal carrier is not
imported here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# Only the record type is published for import.
__all__: list[str] = ["SysFinalRecord"]


#: The copybook this module is a CREATE from.
COPYBOOK: Final[str] = "copybooks/wsfinal.cob"

#: The MySQL table the bridge `finalMT` writes this record to, through handler `acas000`
#: at file-key number 3.
TABLE: Final[str] = "SYSFINAL-REC"

#: The FILLER's declaration line, verbatim from the copybook
#: [copybooks/wsfinal.cob:L12].
_FILLER_DECLARED_AT: Final[str] = "copybooks/wsfinal.cob:L12"


# (R-5 - looked up, never guessed) All three helpers below fail loudly when the
# dictionary does not hold what this module needs, and none substitutes a default.


def _column_backed_key(*, copybook_field: str) -> str:
    """Find the `TABLE` entry key whose copybook field is `copybook_field`.

    The path section 3.3 of this file's brief prescribes: ask the dictionary for the
    entries of table SYSFINAL-REC and read each entry's copybook field name. Two filters
    matter and both are deliberate.

    Args:
        copybook_field: The COBOL field name, verbatim from the copybook.

    Returns:
        The entry key, in the dictionary's `<TABLE-NAME>.<COLUMN-NAME>` form.

    Raises:
        loader.DictionaryLookupError: The dictionary holds no such entry.
    """
    for entry in loader.entries_for_table(TABLE):
        view = entry.copybook
        if view is not None and view.name == copybook_field and view.file == COPYBOOK:
            return entry.key
    raise loader.DictionaryLookupError(
        f"the generated data dictionary holds no {TABLE} entry for the copybook "
        f"field {copybook_field!r} declared in {COPYBOOK}. This module cannot be "
        f"written without it and must never spell its key by hand: regenerate "
        f"the dictionary with acas_posting/dictionary/generate.py"
    )


def _copybook_only_key(*, declared_at: str) -> str:
    """Find the `COPYBOOK` entry key for the field declared at `declared_at`.

    Args:
        declared_at: The declaration locator, as `copybooks/wsfinal.cob:L12`.

    Returns:
        The entry key the dictionary holds for that declaration.

    Raises:
        loader.DictionaryLookupError: The dictionary holds no such entry.
    """
    for entry in loader.entries_for_copybook_file(COPYBOOK):
        view = entry.copybook
        if view is not None and view.source == declared_at:
            return entry.key
    raise loader.DictionaryLookupError(
        f"the generated data dictionary holds no {COPYBOOK} entry declared at "
        f"{declared_at!r}. This module cannot be written without it and must "
        f"never spell its key by hand: regenerate the dictionary with "
        f"acas_posting/dictionary/generate.py"
    )


def _from_dictionary(value: int | None, *, key: str, member: str) -> int:
    """Take a count the dictionary holds, loudly rather than by default.

    The shape of the `ar1` table - how many slots, how wide each one - is the
    dictionary's to state, not this module's.

    Args:
        value: The count as the dictionary holds it, possibly absent.
        key: The entry key it came from, for the failure message.
        member: Which count it is, for the failure message.

    Returns:
        That count.

    Raises:
        loader.DictionaryLookupError: The dictionary holds no such count.
    """
    if value is None:
        raise loader.DictionaryLookupError(
            f"the generated data dictionary holds no {member} for entry {key!r}. "
            f"This module derives the shape of its members from the dictionary "
            f"and states no width and no occurrence count of its own (R-5)"
        )
    return value


_AR1_KEY: Final[str] = _column_backed_key(copybook_field="ar1")

_FILLER_KEY: Final[str] = _copybook_only_key(declared_at=_FILLER_DECLARED_AT)

_AR1: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(_AR1_KEY)
_FILLER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(_FILLER_KEY)

#: The record's fields in copybook declaration order, one descriptor per dataclass
#: member.
FIELDS: Final[tuple[FieldDescriptor, ...]] = (_AR1, _FILLER)


# Sizes come from the dictionary, never from this file. The arithmetic the copybook
# header turns on.

_AR1_OCCURS: Final[int] = _from_dictionary(
    _AR1.occurs, key=_AR1_KEY, member="OCCURS count"
)
_AR1_WIDTH: Final[int] = _from_dictionary(
    _AR1.character_length, key=_AR1_KEY, member="character length"
)
_FILLER_WIDTH: Final[int] = _from_dictionary(
    _FILLER.character_length, key=_FILLER_KEY, member="character length"
)

#: Every slot of an unset table, built in index order.
_AR1_UNSET: Final[tuple[str, ...]] = tuple(" " * _AR1_WIDTH for _ in range(_AR1_OCCURS))

_FILLER_UNSET: Final[str] = " " * _FILLER_WIDTH


@dataclass(slots=True)
class SysFinalRecord:
    """`01 Final-Record.` of `copybooks/wsfinal.cob` [copybooks/wsfinal.cob:L10].

    NOT FROZEN. The final-accounts layout is read and written by the maintenance
    programs, so instances are mutable. Assigning to `ar1` replaces the whole table,
    since a tuple is immutable by design (R-6).
    """

    # ar1 pic x(16) occurs 26 [copybooks/wsfinal.cob:L11] 26 slots x 16 characters = 416
    # data bytes. Sixteen-character slots with no per-slot names.
    ar1: tuple[str, ...] = field(default_factory=lambda: _AR1_UNSET)

    # filler pic x(608) [copybooks/wsfinal.cob:L12] The copybook's own inline note reads
    # "size now 1024 as used in sys002", and 416 + 608 = 1024.
    filler: str = _FILLER_UNSET
