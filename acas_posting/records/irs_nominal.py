"""The IRS nominal ledger account layout - `01 NL-Record` [copybooks/irswsnl.cob].

One copybook, one table (`IRSNL-REC`), four plain dataclasses. A record layout
and nothing else: it mirrors the copybook field for field and takes its storage
metadata from the generated dictionary (R-5).

The two DR and CR accumulators are what the IRS posting path updates, and it
updates the debit side BEFORE it looks the credit account up
[irs/irs030.cbl:L1635-L1652], so a missing credit account leaves a posted debit
here with nothing balancing it. That is reproduced, not repaired.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

__all__ = ["NlData", "NlKey", "NlPointerView", "WsIrsnlRecord"]


# THE FIELD DESCRIPTORS (rule R-5 - looked up, never transcribed) Each key below was
# read out of the generated artifact, by listing ``loader.entries_for_table("IRSNL-
# REC")`` and ``loader.entries_for_copybook_record("NL-Record")`` and taking each
# entry's copybook name, rather than being built from the field name by rule.

_NL_KEY: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.KEY-1")
_NL_OWNING: Final = FieldDescriptor.from_dictionary_key(
    "NL-Record.NL-Owning"
)
_NL_SUB_NOMINAL: Final = FieldDescriptor.from_dictionary_key(
    "NL-Record.NL-Sub-Nominal"
)

_NL_TYPE: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.TIPE")

_NL_DATA: Final = FieldDescriptor.from_dictionary_key("NL-Record.NL-Data")
_NL_NAME: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.NL-NAME")

# The ten money fields: COMP with an implied two-place scale, so DECIMAL and never int.
_NL_DR: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.DR")
_NL_CR: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.CR")

# ``occurs 4`` [copybooks/irswsnl.cob:L19-L20].
_NL_DR_LAST: Final[tuple[FieldDescriptor, ...]] = (
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-01"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-02"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-03"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-04"),
)
_NL_CR_LAST: Final[tuple[FieldDescriptor, ...]] = (
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-01"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-02"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-03"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-04"),
)

_NL_AC: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.AC")

# The REDEFINES clause sits on this 03 group, which the copybook leaves unnamed, so the
# artifact keys it ``NL-Record.filler`` with ``is_filler`` true and ``redefines`` naming
# ``NL-Data``.
_NL_POINTER_FILLER: Final = FieldDescriptor.from_dictionary_key(
    "NL-Record.filler"
)
_NL_POINTER: Final = FieldDescriptor.from_dictionary_key(
    "IRSNL-REC.REC-POINTER"
)


# THE DEFAULTS (a value always, never None - see the module docstring) ``initialize WS-
# IRSNL-Record with filler`` [common/irsnominalMT.cbl:L524] leaves an unset numeric
# field at zero and an unset alphanumeric field at spaces before any row is written,
# which is how all fifteen columns can be ``NOT NULL``.

_ZERO_MONEY: Final = Decimal("0.00")

# Alphanumeric widths come from each field's own descriptor, so that the declared ``pic
# x(24)`` and ``pic x`` are never retyped as numbers here.
_NL_NAME_SPACES: Final = " " * _NL_NAME.byte_length
_NL_TYPE_SPACES: Final = " " * _NL_TYPE.byte_length
_NL_AC_SPACES: Final = " " * _NL_AC.byte_length


@dataclass(slots=True)
class NlKey:
    """``03 NL-Key.`` [copybooks/irswsnl.cob:L9].

    Because they map to no column, these two are the only fields of the record keyed by
    copybook record and field name rather than by table and column.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _NL_OWNING,
        _NL_SUB_NOMINAL,
    )

    nl_owning: int = 0
    nl_sub_nominal: int = 0


@dataclass(slots=True)
class NlData:
    """``03 NL-Data.`` [copybooks/irswsnl.cob:L15].

    Every numeric field in this group is ``pic 9(8)v99 comp`` - binary storage with an
    implied two-place scale and no sign - so every one is ``decimal.Decimal`` at scale
    2, and none is ``int``.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _NL_NAME,
        _NL_DR,
        _NL_CR,
        *_NL_DR_LAST,
        *_NL_CR_LAST,
        _NL_AC,
    )

    nl_name: str = _NL_NAME_SPACES

    nl_dr: Decimal = _ZERO_MONEY

    nl_cr: Decimal = _ZERO_MONEY

    # NL-DR-Last pic 9(8)v99 comp occurs 4 [copybooks/irswsnl.cob:L19] The four previous
    # quarters' debit totals, in the copybook's own order.
    nl_dr_last: tuple[Decimal, Decimal, Decimal, Decimal] = (
        dataclasses.field(
            default_factory=lambda: (
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
            )
        )
    )

    nl_cr_last: tuple[Decimal, Decimal, Decimal, Decimal] = (
        dataclasses.field(
            default_factory=lambda: (
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
            )
        )
    )

    nl_ac: str = _NL_AC_SPACES


@dataclass(slots=True)
class NlPointerView:
    """``03 filler redefines NL-Data.`` [copybooks/irswsnl.cob:L22].

    The COBOL group is UNNAMED: its name is ``filler``, and the artifact keys it ``NL-
    Record.filler``. This class is named after the field it contains, for readability.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_NL_POINTER,)

    nl_pointer: int = 0


@dataclass(slots=True)
class WsIrsnlRecord:
    """``01 NL-Record.`` [copybooks/irswsnl.cob:L8].

    Members follow copybook declaration order, so this class can be set beside its
    copybook and read down.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _NL_KEY,
        _NL_TYPE,
        _NL_DATA,
        _NL_POINTER_FILLER,
    )

    nl_key: NlKey = dataclasses.field(default_factory=NlKey)

    nl_type: str = _NL_TYPE_SPACES

    nl_data: NlData = dataclasses.field(default_factory=NlData)

    nl_pointer_view: NlPointerView = dataclasses.field(
        default_factory=NlPointerView
    )
