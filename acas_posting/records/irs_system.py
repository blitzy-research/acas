"""IRS system-parameter record - `copybooks/irswssystem.cob`.

The first parameter of the migration's third linkage shape
[irs/irs030.cbl:L552-L554], mirrored field for field with descriptors looked up
in the generated dictionary (R-5).

The copybook's header records the record growing and then shrinking again - 256
bytes, then 288, then 312, then 256 once the system file names were dropped in
favour of tables [copybooks/irswssystem.cob:L7-L10]. The current declaration is
what is mirrored; the history is not reconstructed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

# Sorted, as the three names of this module's public surface.
__all__: Final[tuple[str, ...]] = (
    "IrsSystemParams",
    "VatGroup",
    "VatRates",
)


# THE DICTIONARY KEYS (rule R-5.

_desc: Final = FieldDescriptor.from_dictionary_key

_SYSTEM_RECORD: Final = _desc("system-record.system-record")

_RUN_DATE: Final = _desc("system-record.run-date")
_SUSER: Final = _desc("system-record.suser")
_CLIENT: Final = _desc("system-record.client")
_ADDRESS_1: Final = _desc("system-record.address-1")
_ADDRESS_2: Final = _desc("system-record.address-2")
_ADDRESS_3: Final = _desc("system-record.address-3")
_ADDRESS_4: Final = _desc("system-record.address-4")
_START_DATE: Final = _desc("system-record.start-date")
_END_DATE: Final = _desc("system-record.end-date")
_SYSTEM_OPS: Final = _desc("system-record.system-ops")
_PASS_WORD: Final = _desc("system-record.pass-word")
_NEXT_POST: Final = _desc("system-record.next-post")
_VAT_RATES: Final = _desc("system-record.vat-rates")
_VAT: Final = _desc("system-record.vat")
_VAT2: Final = _desc("system-record.vat2")
_VAT3: Final = _desc("system-record.vat3")
_VAT_GROUP: Final = _desc("system-record.vat-group")
_VAT_PSENT: Final = _desc("system-record.vat-psent")
_PASS_VALUE: Final = _desc("system-record.pass-value")
_SAVE_SEQU: Final = _desc("system-record.save-sequ")
_SYSTEM_WORK_GROUP: Final = _desc("system-record.system-work-group")
_PL_APP_CREATED: Final = _desc("system-record.PL-App-Created")
_PL_APPROP_AC: Final = _desc("system-record.PL-Approp-AC")
_PRINT_SPOOL_NAME: Final = _desc("system-record.Print-Spool-Name")
_FIRST_TIME_FLAG: Final = _desc("system-record.First-Time-FLag")
_FILLER_39: Final = _desc("system-record.filler#39")
_FILLER_40: Final = _desc("system-record.filler#40")


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return an alphanumeric item's declared width, in spaces.

    The default for every `PIC X(n)` member below, DERIVED from that member's own
    dictionary entry rather than written as a literal width, in the spirit of section
    0.3.3: "Field metadata is therefore derived, not transcribed".

    Args:
        descriptor: The member's descriptor, from the generated dictionary.

    Returns:
        The member's declared width as a run of spaces.
    """
    return " " * (descriptor.character_length or 0)


@dataclass(slots=True)
class VatRates:
    """The three VAT rates - `03 vat-rates.` [copybooks/irswssystem.cob:L26].

    Which VAT rate group this is matters, because the frozen tree holds two that are
    easy to confuse.
    """

    GROUP: ClassVar[FieldDescriptor] = _VAT_RATES
    #: Its members' descriptors, in copybook declaration order (rule R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VAT, _VAT2, _VAT3)

    # 05 vat pic 99v99.
    vat: Decimal = Decimal("0.00")

    vat2: Decimal = Decimal("0.00")

    vat3: Decimal = Decimal("0.00")


@dataclass(slots=True)
class VatGroup:
    """The array view over the rates - `03 vat-group redefines vat-rates.`.

    COBOL `OCCURS` subscripts are ONE-BASED: `vat-psent (1)` is `vat_psent[0]`, `vat-
    psent (3)` is `vat_psent[2]`. No accessor is provided that hides that offset,
    because hiding it would be a behaviour this migration invented rather than one it
    reproduces.
    """

    GROUP: ClassVar[FieldDescriptor] = _VAT_GROUP
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VAT_PSENT,)

    vat_psent: tuple[Decimal, Decimal, Decimal] = (
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    )


@dataclass(slots=True)
class IrsSystemParams:
    """IRS system parameters - parameter #1 of the IRS linkage shape.

    TWO COBOL identifiers name this one record, and both are quoted verbatim because the
    pair is the whole reason this class is not called `SystemRecord`.
    """

    GROUP: ClassVar[FieldDescriptor] = _SYSTEM_RECORD
    #: Its members' descriptors, in copybook declaration order L14 -> L40 (rule R-6). 23
    #: of them: 19 scalars, 2 groups and 2 FILLERs.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _RUN_DATE,
        _SUSER,
        _CLIENT,
        _ADDRESS_1,
        _ADDRESS_2,
        _ADDRESS_3,
        _ADDRESS_4,
        _START_DATE,
        _END_DATE,
        _SYSTEM_OPS,
        _PASS_WORD,
        _NEXT_POST,
        _VAT_RATES,
        _VAT_GROUP,
        _PASS_VALUE,
        _SAVE_SEQU,
        _SYSTEM_WORK_GROUP,
        _PL_APP_CREATED,
        _PL_APPROP_AC,
        _PRINT_SPOOL_NAME,
        _FIRST_TIME_FLAG,
        _FILLER_39,
        _FILLER_40,
    )

    run_date: str = _spaces(_RUN_DATE)

    suser: str = _spaces(_SUSER)

    client: str = _spaces(_CLIENT)

    address_1: str = _spaces(_ADDRESS_1)

    address_2: str = _spaces(_ADDRESS_2)

    address_3: str = _spaces(_ADDRESS_3)

    address_4: str = _spaces(_ADDRESS_4)

    start_date: str = _spaces(_START_DATE)

    end_date: str = _spaces(_END_DATE)

    system_ops: str = _spaces(_SYSTEM_OPS)

    # 03 pass-word pic x(4).
    pass_word: str = _spaces(_PASS_WORD)

    # 03 next-post pic 9(5).
    next_post: int = 0

    vat_rates: VatRates = field(default_factory=VatRates)

    # 03 vat-group redefines vat-rates. <- the array view over the SAME twelve bytes.
    vat_group: VatGroup = field(default_factory=VatGroup)

    pass_value: int = 0

    # 03 save-sequ pic 9. *> 191 <- the copybook's own comment, REPRODUCED AS WRITTEN
    # and one byte short.
    save_sequ: int = 0

    # 03 system-work-group pic x(18). *> 209 <- the copybook's own comment, reproduced
    # as written and one byte short; computed 210 | [copybooks/irswssystem.cob:L34].
    system_work_group: str = _spaces(_SYSTEM_WORK_GROUP)

    # 03 PL-App-Created pic x. *> 210 <- the copybook's own comment, reproduced as
    # written and one byte short; computed 211 | [copybooks/irswssystem.cob:L35].
    pl_app_created: str = _spaces(_PL_APP_CREATED)

    # 03 PL-Approp-AC pic 9(5). *> 215 <- the copybook's own comment, reproduced as
    # written and one byte short; computed 216 | [copybooks/irswssystem.cob:L36].
    pl_approp_ac: int = 0

    # 03 Print-Spool-Name pic x(32). *> 247 <- the copybook's own comment, reproduced as
    # written and one byte short.
    print_spool_name: str = _spaces(_PRINT_SPOOL_NAME)

    # 03 First-Time-FLag pic 9. *> 248 <- the copybook's own comment, reproduced as
    # written and one byte short.
    first_time_flag: int = 0

    # 03 filler pic 9(7). *> 255 <- the copybook's own comment, reproduced as written
    # and one byte short; computed 256 | [copybooks/irswssystem.cob:L39] COBOL name
    # `filler`.
    filler_39: int = 0

    # 03 filler pic x. *> 256 <- the copybook's own comment, reproduced as written and
    # one byte short.
    filler_40: str = _spaces(_FILLER_40)
