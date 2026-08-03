"""IRS final-accounts record: `01 Final-Record.` [copybooks/irswsfinal.cob:L7].

A CREATE from `copybooks/irswsfinal.cob` - 655 bytes of named alphanumeric fields
plus the `OCCURS` tables, mirrored field for field with descriptors looked up in
the generated dictionary (R-5).

The record carries no fractional field, so the exact-decimal carrier is not
imported here; and nothing in it drifts in sign across the copybook, the bridge
host variable and the column.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Sorted, so that the surface is stable between runs (R-6).
    "Ar1Fields",
    "Ar1View",
    "Ar2Fields",
    "Ar2View",
    "IrsFinalRecord",
)


# The MySQL table, as the frozen schema spells it [mysql/ACASDB.sql:L214].
_TABLE: Final[str] = "IRSFINAL-REC"

# The copybook, as the dictionary records it. Every entry this module uses must carry
# this file and no other.
_COPYBOOK: Final[str] = "copybooks/irswsfinal.cob"


def _entry_key_by_field_name() -> dict[str, str]:
    """Map each NAMED copybook field of this record to its entry key.

    Two passes, because the record's fields reach the artifact by two different routes
    and neither route alone covers them all.

    Returns:
        The COBOL field name of every named item in this copybook, mapped to its
            dictionary entry key.
    """
    keys: dict[str, str] = {}
    for entry in loader.entries_for_table(_TABLE):
        copybook = entry.copybook
        if copybook is not None and copybook.file == _COPYBOOK:
            keys[copybook.name] = entry.key
    for entry in loader.entries_for_copybook_file(_COPYBOOK):
        copybook = entry.copybook
        if (
            copybook is not None
            and copybook.file == _COPYBOOK
            and not copybook.is_filler
        ):
            keys[copybook.name] = entry.key
    return keys


def _entry_key_by_redefines_target() -> dict[str, str]:
    """Map each redefining FILLER group to its entry key, by what it covers.

    Returns:
        The redefined group's name mapped to the redefining group's entry key, for each
            FILLER group of this copybook.
    """
    return {
        entry.copybook.redefines: entry.key
        for entry in loader.entries_for_copybook_file(_COPYBOOK)
        if entry.copybook is not None
        and entry.copybook.file == _COPYBOOK
        and entry.copybook.is_filler
        and entry.copybook.redefines is not None
    }


_KEY_BY_FIELD_NAME: Final[dict[str, str]] = _entry_key_by_field_name()
_KEY_BY_REDEFINES_TARGET: Final[dict[str, str]] = (
    _entry_key_by_redefines_target()
)


def _descriptor_for(cobol_name: str) -> FieldDescriptor:
    """Describe one named item of this record, from its dictionary entry.

    Args:
        cobol_name: The field name exactly as the copybook writes it, for example
            `"ar1-1"`, `"ar1"` or `"ar3"`.

    Returns:
        The descriptor for that field.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_BY_FIELD_NAME[cobol_name])


def _redefining_group_for(target: str) -> FieldDescriptor:
    """Describe the unnamed group that redefines `target`.

    Args:
        target: The redefined group's COBOL name, `"ar1-fields"` or `"ar2-fields"`.

    Returns:
        The descriptor for the `filler` group redefining it, carrying `redefines` set to
            `target` and `is_filler` set.
    """
    return FieldDescriptor.from_dictionary_key(
        _KEY_BY_REDEFINES_TARGET[target]
    )


# `initialize Final-Record with filler.` [common/irsfinalMT.cbl:L395] is the state the
# bridge hands to a load, and for an alphanumeric item that means SPACES.


def _initial_value(descriptor: FieldDescriptor) -> str:
    """Return one item's initial value: its own width, in spaces.

    Args:
        descriptor: An elementary alphanumeric item's descriptor.

    Returns:
        A string of spaces as wide as the item is declared.
    """
    return " " * descriptor.byte_length


def _initial_table(descriptor: FieldDescriptor) -> tuple[str, ...]:
    """Return an `OCCURS` item's initial value: one entry per position.

    Args:
        descriptor: An elementary alphanumeric item's descriptor carrying an `OCCURS`
            count.

    Returns:
        A tuple with one space-filled entry, at the item's own width, for each `OCCURS`
            position it declares.
    """
    return (_initial_value(descriptor),) * (descriptor.occurs or 0)


# The 26 enumerated members, in copybook declaration order. Written out one by one
# because the copybook writes them out one by one.
_AR1_FIELD_DESCRIPTORS: Final[tuple[FieldDescriptor, ...]] = (
    _descriptor_for("ar1-1"),
    _descriptor_for("ar1-2"),
    _descriptor_for("ar1-3"),
    _descriptor_for("ar1-4"),
    _descriptor_for("ar1-5"),
    _descriptor_for("ar1-6"),
    _descriptor_for("ar1-7"),
    _descriptor_for("ar1-8"),
    _descriptor_for("ar1-9"),
    _descriptor_for("ar1-10"),
    _descriptor_for("ar1-11"),
    _descriptor_for("ar1-12"),
    _descriptor_for("ar1-13"),
    _descriptor_for("ar1-14"),
    _descriptor_for("ar1-15"),
    _descriptor_for("ar1-16"),
    _descriptor_for("ar1-17"),
    _descriptor_for("ar1-18"),
    _descriptor_for("ar1-19"),
    _descriptor_for("ar1-20"),
    _descriptor_for("ar1-21"),
    _descriptor_for("ar1-22"),
    _descriptor_for("ar1-23"),
    _descriptor_for("ar1-24"),
    _descriptor_for("ar1-25"),
    _descriptor_for("ar1-26"),
)

# Every member of the group is declared `pic x(24)` [copybooks/irswsfinal.cob:L9-L34],
# so one initial value serves all 26.
_AR1_FIELD_INITIAL: Final[str] = _initial_value(_AR1_FIELD_DESCRIPTORS[0])


@dataclass(slots=True)
class Ar1Fields:
    """`03 ar1-fields.` [copybooks/irswsfinal.cob:L8] - 26 enumerated fields.

    Every item is `pic x(24)`, so the whole group is `str` - there is no numeric item,
    no sign and no implied decimal point anywhere in it (R-2).

    Attributes:
        FIELDS: The 26 descriptors, in copybook declaration order.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _AR1_FIELD_DESCRIPTORS

    ar1_1: str = _AR1_FIELD_INITIAL
    ar1_2: str = _AR1_FIELD_INITIAL
    ar1_3: str = _AR1_FIELD_INITIAL
    ar1_4: str = _AR1_FIELD_INITIAL
    ar1_5: str = _AR1_FIELD_INITIAL
    ar1_6: str = _AR1_FIELD_INITIAL
    ar1_7: str = _AR1_FIELD_INITIAL
    ar1_8: str = _AR1_FIELD_INITIAL
    ar1_9: str = _AR1_FIELD_INITIAL
    ar1_10: str = _AR1_FIELD_INITIAL
    ar1_11: str = _AR1_FIELD_INITIAL
    ar1_12: str = _AR1_FIELD_INITIAL
    ar1_13: str = _AR1_FIELD_INITIAL
    ar1_14: str = _AR1_FIELD_INITIAL
    ar1_15: str = _AR1_FIELD_INITIAL
    ar1_16: str = _AR1_FIELD_INITIAL
    ar1_17: str = _AR1_FIELD_INITIAL
    ar1_18: str = _AR1_FIELD_INITIAL
    ar1_19: str = _AR1_FIELD_INITIAL
    ar1_20: str = _AR1_FIELD_INITIAL
    ar1_21: str = _AR1_FIELD_INITIAL
    ar1_22: str = _AR1_FIELD_INITIAL
    ar1_23: str = _AR1_FIELD_INITIAL
    ar1_24: str = _AR1_FIELD_INITIAL
    ar1_25: str = _AR1_FIELD_INITIAL
    ar1_26: str = _AR1_FIELD_INITIAL


# The array view's own 05-level item, keyed by the table because the bridge maps it to a
# column.
_AR1_VIEW_DESCRIPTOR: Final[FieldDescriptor] = _descriptor_for("ar1")

_AR1_VIEW_INITIAL: Final[tuple[str, ...]] = _initial_table(
    _AR1_VIEW_DESCRIPTOR
)


@dataclass(slots=True)
class Ar1View:
    """`03 filler redefines ar1-fields.` [copybooks/irswsfinal.cob:L35].

    It is an ALTERNATIVE VIEW of the same 624 bytes that `Ar1Fields` describes. Both are
    modelled and neither is primary. As a fact and not a preference.

    Attributes:
        FIELDS: One descriptor, for `ar1`, carrying `occurs` = 26.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_AR1_VIEW_DESCRIPTOR,)

    # ar1 pic x(24) occurs 26 [copybooks/irswsfinal.cob:L36] A tuple and never a list,
    # so the surface is stable between runs (R-6).
    ar1: tuple[str, ...] = _AR1_VIEW_INITIAL


# The second enumerated group: 26 single-character items at L39 through L64, again
# written out one by one because the copybook does.
_AR2_FIELD_DESCRIPTORS: Final[tuple[FieldDescriptor, ...]] = (
    _descriptor_for("ar2-1"),
    _descriptor_for("ar2-2"),
    _descriptor_for("ar2-3"),
    _descriptor_for("ar2-4"),
    _descriptor_for("ar2-5"),
    _descriptor_for("ar2-6"),
    _descriptor_for("ar2-7"),
    _descriptor_for("ar2-8"),
    _descriptor_for("ar2-9"),
    _descriptor_for("ar2-10"),
    _descriptor_for("ar2-11"),
    _descriptor_for("ar2-12"),
    _descriptor_for("ar2-13"),
    _descriptor_for("ar2-14"),
    _descriptor_for("ar2-15"),
    _descriptor_for("ar2-16"),
    _descriptor_for("ar2-17"),
    _descriptor_for("ar2-18"),
    _descriptor_for("ar2-19"),
    _descriptor_for("ar2-20"),
    _descriptor_for("ar2-21"),
    _descriptor_for("ar2-22"),
    _descriptor_for("ar2-23"),
    _descriptor_for("ar2-24"),
    _descriptor_for("ar2-25"),
    _descriptor_for("ar2-26"),
)

# Every member of the group is declared `pic x` - one character, no length in
# parentheses [copybooks/irswsfinal.cob:L39-L64] - so one initial value serves all 26,
# its width read off a descriptor rather than typed.
_AR2_FIELD_INITIAL: Final[str] = _initial_value(_AR2_FIELD_DESCRIPTORS[0])


@dataclass(slots=True)
class Ar2Fields:
    """`03 ar2-fields.` [copybooks/irswsfinal.cob:L38] - 26 enumerated fields.

    Every item is `pic x`, a single character, so the whole group is `str`. The initial
    value of each is one space, matching `initialize Final-Record with filler.`
    [common/irsfinalMT.cbl:L395].

    Attributes:
        FIELDS: The 26 descriptors, in copybook declaration order.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _AR2_FIELD_DESCRIPTORS

    ar2_1: str = _AR2_FIELD_INITIAL
    ar2_2: str = _AR2_FIELD_INITIAL
    ar2_3: str = _AR2_FIELD_INITIAL
    ar2_4: str = _AR2_FIELD_INITIAL
    ar2_5: str = _AR2_FIELD_INITIAL
    ar2_6: str = _AR2_FIELD_INITIAL
    ar2_7: str = _AR2_FIELD_INITIAL
    ar2_8: str = _AR2_FIELD_INITIAL
    ar2_9: str = _AR2_FIELD_INITIAL
    ar2_10: str = _AR2_FIELD_INITIAL
    ar2_11: str = _AR2_FIELD_INITIAL
    ar2_12: str = _AR2_FIELD_INITIAL
    ar2_13: str = _AR2_FIELD_INITIAL
    ar2_14: str = _AR2_FIELD_INITIAL
    ar2_15: str = _AR2_FIELD_INITIAL
    ar2_16: str = _AR2_FIELD_INITIAL
    ar2_17: str = _AR2_FIELD_INITIAL
    ar2_18: str = _AR2_FIELD_INITIAL
    ar2_19: str = _AR2_FIELD_INITIAL
    ar2_20: str = _AR2_FIELD_INITIAL
    ar2_21: str = _AR2_FIELD_INITIAL
    ar2_22: str = _AR2_FIELD_INITIAL
    ar2_23: str = _AR2_FIELD_INITIAL
    ar2_24: str = _AR2_FIELD_INITIAL
    ar2_25: str = _AR2_FIELD_INITIAL
    ar2_26: str = _AR2_FIELD_INITIAL


_AR2_VIEW_DESCRIPTOR: Final[FieldDescriptor] = _descriptor_for("ar2")

_AR2_VIEW_INITIAL: Final[tuple[str, ...]] = _initial_table(
    _AR2_VIEW_DESCRIPTOR
)


@dataclass(slots=True)
class Ar2View:
    """`03 filler redefines ar2-fields.` [copybooks/irswsfinal.cob:L65].

    Attributes:
        FIELDS: One descriptor, for `ar2`, carrying `occurs` = 26.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_AR2_VIEW_DESCRIPTOR,)

    # ar2 pic x occurs 26 [copybooks/irswsfinal.cob:L66] A tuple and never a list (R-6).
    ar2: tuple[str, ...] = _AR2_VIEW_INITIAL


# 03 ar3 pic x(5). [copybooks/irswsfinal.cob:L68] THE COPYBOOK-ONLY FIELD. `ar3` is
# declared here and appears NOWHERE else.
_AR3_DESCRIPTOR: Final[FieldDescriptor] = _descriptor_for("ar3")

_AR3_INITIAL: Final[str] = _initial_value(_AR3_DESCRIPTOR)


_RECORD_MEMBER_DESCRIPTORS: Final[tuple[FieldDescriptor, ...]] = (
    _descriptor_for("ar1-fields"),
    _redefining_group_for("ar1-fields"),
    _descriptor_for("ar2-fields"),
    _redefining_group_for("ar2-fields"),
    _AR3_DESCRIPTOR,
)


@dataclass(slots=True)
class IrsFinalRecord:
    """The IRS final-accounts record: COBOL `01 Final-Record.`, 655 bytes.

    Declared at [copybooks/irswsfinal.cob:L7]. The COBOL identifier is `Final-Record`,
    verbatim, and the Python name carries a prefix it does not have, because a second
    in-scope copybook declares an `01` of exactly the same name that is a DIFFERENT
    RECORD.

    Attributes:
        ar1_fields: `03 ar1-fields.` [:L8], the 26 enumerated 24-character items.
        ar1_view: `03 filler redefines ar1-fields.` [:L35], the same bytes as `05 ar1
            pic x(24) occurs 26.` [:L36].
        ar2_fields: `03 ar2-fields.` [:L38], the 26 enumerated single-character items.
        ar2_view: `03 filler redefines ar2-fields.` [:L65], the same bytes as `05 ar2
            pic x occurs 26.` [:L66].
        ar3: `03 ar3 pic x(5).` [:L68]. Declared by the copybook, carried by no host
            variable and stored in no column - see the block above this class.
        FIELDS: The five member descriptors, in copybook declaration order. The `01`
            group has an entry of its own, `Final-Record.Final-Record#7`, which this
            class stands for rather than holds.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _RECORD_MEMBER_DESCRIPTORS

    ar1_fields: Ar1Fields = field(default_factory=Ar1Fields)

    ar1_view: Ar1View = field(default_factory=Ar1View)

    ar2_fields: Ar2Fields = field(default_factory=Ar2Fields)

    ar2_view: Ar2View = field(default_factory=Ar2View)

    ar3: str = _AR3_INITIAL

    # DELIBERATE ABSENCE - do not add an attribute here. `IRS-FINAL-ACC-REC-KEY` has no
    # counterpart in this copybook and gets none here.
