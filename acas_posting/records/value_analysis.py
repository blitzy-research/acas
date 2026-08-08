"""The value-analysis record `WS-Value-Record` [copybooks/wsval.cob:L9].

A CREATE from `copybooks/wsval.cob`: three dataclasses mirroring the copybook's
declarations in order, descriptors looked up in the generated dictionary (R-5).

Three money fields are signed here and unsigned at the bridge host variable and
the column, so a negative value loses its sign before any SQL runs; the loss is
reproduced in `acas_posting.dal.acas013_value` and this module reports the
copybook view.

The layout is near-identical to the Analysis record's
[copybooks/wsanal.cob], which is why the two are kept strictly apart: a lookup
that reached the wrong copybook would produce a record that still looked right.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

# The dictionary loader is reached THROUGH the descriptor rather than imported here,
# deliberately.

__all__ = ["VaCode", "VaGroup", "WsValueRecord"]


# Field descriptors, one per COBOL declaration, LOOKED UP - NEVER TRANSCRIBED Each key
# was obtained by reading the generated dictionary and matching on the entry's
# `copybook.name`.

# va-code a group of three characters, level 03 [copybooks/wsval.cob:L10] A GROUP whose
# three subordinate characters concatenate into the column.
_VA_CODE: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-CODE")

_VA_SYSTEM: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-system")

_VA_GROUP: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-group")

# va-first pic x, level 07 [copybooks/wsval.cob:L13] Level 07 under a level 03, with no
# 05 between; carried as declared.
_VA_FIRST: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-first")

_VA_SECOND: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-second")

_VA_GL: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-GL")

_VA_DESC: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-DESC")

# va-print pic xxx, level 03 [copybooks/wsval.cob:L17] The copybook spells this
# `pic xxx` rather than `pic x(3)`; the spelling is preserved, never normalised (R-4).
_VA_PRINT: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-PRINT")

# va-t-this pic 9(5) comp, level 03 [copybooks/wsval.cob:L18] UNSIGNED in the copybook,
# so unsigned at all three layers.
_VA_T_THIS: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-T-THIS")

_VA_T_LAST: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-T-LAST")

_VA_T_YEAR: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-T-YEAR")

# va-v-this pic s9(8)v99 comp-3, level 03 [copybooks/wsval.cob:L21] MONEY LOSES ITS SIGN
# AT THE BRIDGE - the A-11 family, and the dictionary entry carries that reference.
_VA_V_THIS: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-V-THIS")

_VA_V_LAST: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-V-LAST")

_VA_V_YEAR: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-V-YEAR")


# Initial content of each alphanumeric item The bridge opens both of its transfer
# paragraphs by initialising the record group - `initialize TD-VALUEANAL-REC.`
# [common/valueMT.cbl:L1059] on the way in and `initialize VALUEANAL-REC.`
# [common/valueMT.cbl:L1086] on the way out - so an unset alphanumeric item holds SPACES
# at its declared width, never a null.

_INITIAL_VA_SYSTEM: Final[str] = str(_VA_SYSTEM.store(""))
_INITIAL_VA_FIRST: Final[str] = str(_VA_FIRST.store(""))
_INITIAL_VA_SECOND: Final[str] = str(_VA_SECOND.store(""))
_INITIAL_VA_DESC: Final[str] = str(_VA_DESC.store(""))
_INITIAL_VA_PRINT: Final[str] = str(_VA_PRINT.store(""))


# The record ATTRIBUTE order inside each class is the copybook's declaration order, L10
# through L23, which is what rule R-6 pins and what lets a reader diff a class against
# its copybook line by line.


@dataclass(slots=True)
class VaGroup:
    """``05 va-group.`` [copybooks/wsval.cob:L12] - two characters.

    The inner group of the analysis key, holding ``va-first`` and ``va-second``. Its two
    children are declared at level 07 with no level 06 between them
    [copybooks/wsval.cob:L13-L14].
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VA_FIRST, _VA_SECOND)

    va_first: str = _INITIAL_VA_FIRST

    va_second: str = _INITIAL_VA_SECOND


@dataclass(slots=True)
class VaCode:
    """``03 va-code.`` [copybooks/wsval.cob:L10] - three characters.

    The analysis key, and the primary key of ``VALUEANAL-REC`` [mysql/ACASDB.sql:L1429].
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VA_SYSTEM, _VA_GROUP)

    va_system: str = _INITIAL_VA_SYSTEM

    va_group: VaGroup = field(default_factory=VaGroup)


@dataclass(slots=True)
class WsValueRecord:
    """The value-analysis record, ``WS-Value-Record`` [copybooks/wsval.cob:L9].

    The copybook declares it ``01 WS-Value-Record.`` - that level number, that casing,
    that doubled space and that terminating period - at [copybooks/wsval.cob:L9].
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _VA_CODE,
        _VA_GL,
        _VA_DESC,
        _VA_PRINT,
        _VA_T_THIS,
        _VA_T_LAST,
        _VA_T_YEAR,
        _VA_V_THIS,
        _VA_V_LAST,
        _VA_V_YEAR,
    )

    va_code: VaCode = field(default_factory=VaCode)

    va_gl: int = 0

    va_desc: str = _INITIAL_VA_DESC

    va_print: str = _INITIAL_VA_PRINT

    va_t_this: int = 0

    va_t_last: int = 0

    va_t_year: int = 0

    va_v_this: Decimal = Decimal("0.00")

    va_v_last: Decimal = Decimal("0.00")

    va_v_year: Decimal = Decimal("0.00")
