"""The General Ledger batch header `01 WS-Batch-Record`, field for field.

A CREATE from the frozen `copybooks/wsbatch.cob`, carrying the batch's entered
control totals, its status condition names and the cleared/posted stamps that
`gl072` writes [general/gl072.cbl:L375-L377].

The copybook's own header contradicts itself about the record's length: it says
96 bytes, then 98, then records the maintainer counting 96 while `function
length` reports 98 [copybooks/wsbatch.cob:L7-L9]. The contradiction is RECORDED,
not resolved - no length constant is declared here, because a single honest
number cannot be written down.

The status condition names matter to the cycle rather than to this record: a
batch left open is what `gl070` detects [general/gl070.cbl:L314-L315] before it
raises the abort code [general/gl070.cbl:L289].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Ordered the way the sibling modules order theirs, and the way ruff's RUF022 check
    # reads an `__all__`: the module-level constant first, then the class names
    # alphabetically.
    "DRIFT_REGISTER",
    "BatchAmounts",
    "BatchDates",
    "GlBatchRecord",
    "PostingData",
    "WsBatchKey",
    "WsBatchKey9",
)


# Named once, used for every lookup below, so that no string literal naming a frozen
# source is repeated and drifts out of step with its neighbours.
_COPYBOOK: Final[str] = "copybooks/wsbatch.cob"
_RECORD: Final[str] = "WS-Batch-Record"
_TABLE: Final[str] = "GLBATCH-REC"


def _dictionary_keys_by_cobol_name() -> dict[str, str]:
    """Map each COBOL field name of this record to its dictionary key.

    Agent Action Plan section 0.8.1 makes the ordering a directive rather than a
    preference: "The dictionary is generated from the bridge before record definitions
    are written, and every Python field definition cites its entry ...

    Returns:
        COBOL field name, exactly as the frozen copybook spells it, mapped to its
            dictionary key.

    Raises:
        loader.DictionaryLookupError: The table or the record is not in the generated
            dictionary.
    """
    by_name: dict[str, str] = {}
    for entry in loader.entries_for_table(_TABLE):
        copybook = entry.copybook
        if copybook is not None and entry.column is not None:
            by_name[copybook.name] = entry.key
    for entry in loader.entries_for_copybook_record(_RECORD):
        copybook = entry.copybook
        if copybook is not None:
            by_name.setdefault(copybook.name, entry.key)
    return by_name


# Built once, at class-definition time.
_KEYS: Final[dict[str, str]] = _dictionary_keys_by_cobol_name()


def _describe(cobol_name: str) -> FieldDescriptor:
    """Return the descriptor the generated dictionary holds for one field.

    Args:
        cobol_name: The COBOL field name as `copybooks/wsbatch.cob` spells it, case and
            hyphens preserved - `"Actual-Vat"`, `"bDefault"`.

    Returns:
        The descriptor for that field, carrying its copybook view of usage, digits,
            scale, signedness and sign position, its Python carrier, its dictionary key
            and its source locator.

    Raises:
        KeyError: No item of this record is spelt so. A programmer error, not a data
            condition.
    """
    return FieldDescriptor.from_dictionary_key(_KEYS[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return the all-space initial value of an alphanumeric item.

    COBOL fills an alphanumeric item with spaces to its declared width, and the bridge
    does the same before every write.

    Args:
        descriptor: The alphanumeric field to produce the initial value for.

    Returns:
        A string of spaces at the field's declared character width.
    """
    return str(descriptor.store(""))


_WS_BATCH_KEY: Final[FieldDescriptor] = _describe("WS-Batch-Key")
_WS_LEDGER: Final[FieldDescriptor] = _describe("WS-Ledger")
_WS_BATCH_NOS: Final[FieldDescriptor] = _describe("WS-Batch-Nos")


@dataclass(slots=True)
class WsBatchKey:
    """`03 WS-Batch-Key.` - the batch key as its two parts.

    A group, so it has no storage of its own: its six bytes are the one byte of `WS-
    Ledger` plus the five of `WS-Batch-Nos`.
    """

    # The group's own dictionary entry, so that every one of the record's twenty-eight
    # entries has a home in this module (rule R-5).
    GROUP: ClassVar[FieldDescriptor] = _WS_BATCH_KEY

    # Declaration order, which for a record is also its byte layout (rule R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_LEDGER,
        _WS_BATCH_NOS,
    )

    ws_ledger: int = 0

    ws_batch_nos: int = 0


_WS_BATCH_KEY9: Final[FieldDescriptor] = _describe("WS-Batch-Key9")


@dataclass
class WsBatchKey9:
    """`03 WS-Batch-Key9 redefines WS-Batch-Key` - the same six bytes, as one.

    Read the copybook a line at a time and `pic 9(6).` is missed and the field is typed
    wrongly - so the two-line form is recorded here rather than left to be rediscovered.
    This view owns no independent integer: it is bound to :class:`WsBatchKey`, exactly
    as a COBOL ``REDEFINES`` names the same storage.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_WS_BATCH_KEY9,)

    ws_batch_key9: int = 0

    def __getattribute__(self, name: str) -> object:
        """Derive the six-digit field whenever this view has been bound."""
        if name == "ws_batch_key9":
            namespace = object.__getattribute__(self, "__dict__")
            key = namespace.get("_key")
            if key is not None:
                return (
                    int(key.ws_ledger) * 100_000
                    + int(key.ws_batch_nos)
                )
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: object) -> None:
        """Store the six-digit field into both subordinate grouped fields."""
        if name == "ws_batch_key9":
            numeric = int(value)
            object.__setattr__(self, name, numeric)
            key = self.__dict__.get("_key")
            if key is not None:
                ledger, batch_nos = divmod(numeric, 100_000)
                key.ws_ledger = ledger
                key.ws_batch_nos = batch_nos
            return
        object.__setattr__(self, name, value)

    def bind(self, key: WsBatchKey) -> None:
        """Rebind this view to ``key`` without losing either initialized reading."""
        grouped = int(key.ws_ledger) * 100_000 + int(key.ws_batch_nos)
        redefined = int(self.ws_batch_key9)
        object.__setattr__(self, "_key", key)
        self.ws_batch_key9 = redefined or grouped


_DATES: Final[FieldDescriptor] = _describe("Dates")
_ENTERED: Final[FieldDescriptor] = _describe("Entered")
_PROOFED: Final[FieldDescriptor] = _describe("Proofed")
_POSTED: Final[FieldDescriptor] = _describe("Posted")
_STORED: Final[FieldDescriptor] = _describe("Stored")


@dataclass(slots=True)
class BatchDates:
    """`03 Dates.` - the four day-number stamps of a batch's life.

    COBOL identifier, verbatim: `Dates` [copybooks/wsbatch.cob:L35]. The class is named
    `BatchDates` because a bare `Dates` reads poorly beside the other record types in
    this package and says nothing about what it belongs to.
    """

    GROUP: ClassVar[FieldDescriptor] = _DATES

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _ENTERED,
        _PROOFED,
        _POSTED,
        _STORED,
    )

    entered: int = 0

    proofed: int = 0

    posted: int = 0

    stored: int = 0


# 03 Amounts comp-3. [copybooks/wsbatch.cob:L40] four are packed decimal by inheritance.

_AMOUNTS: Final[FieldDescriptor] = _describe("Amounts")
_INPUT_GROSS: Final[FieldDescriptor] = _describe("Input-Gross")
_INPUT_VAT: Final[FieldDescriptor] = _describe("Input-Vat")
_ACTUAL_GROSS: Final[FieldDescriptor] = _describe("Actual-Gross")
_ACTUAL_VAT: Final[FieldDescriptor] = _describe("Actual-Vat")


@dataclass(slots=True)
class BatchAmounts:
    """`03 Amounts ... comp-3.` - the entered and actual totals of a batch.

    COBOL identifier, verbatim: `Amounts` [copybooks/wsbatch.cob:L40]. The class is
    named `BatchAmounts` for the same reason `BatchDates` is not `Dates`; the COBOL
    original is recorded here so the traceability mapping stays mechanical.
    """

    GROUP: ClassVar[FieldDescriptor] = _AMOUNTS

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _INPUT_GROSS,
        _INPUT_VAT,
        _ACTUAL_GROSS,
        _ACTUAL_VAT,
    )

    input_gross: Decimal = Decimal("0.00")

    input_vat: Decimal = Decimal("0.00")

    actual_gross: Decimal = Decimal("0.00")

    actual_vat: Decimal = Decimal("0.00")


_POSTING_DATA: Final[FieldDescriptor] = _describe("posting-data")
_B_DEFAULT: Final[FieldDescriptor] = _describe("bDefault")
_CONVENTION: Final[FieldDescriptor] = _describe("Convention")
_BATCH_DEF_AC: Final[FieldDescriptor] = _describe("Batch-Def-AC")
_BATCH_DEF_PC: Final[FieldDescriptor] = _describe("Batch-Def-PC")
_BATCH_DEF_CODE: Final[FieldDescriptor] = _describe("Batch-Def-Code")
_BATCH_DEF_VAT: Final[FieldDescriptor] = _describe("Batch-Def-Vat")


@dataclass(slots=True)
class PostingData:
    """`03 posting-data.` - the per-batch posting defaults."""

    GROUP: ClassVar[FieldDescriptor] = _POSTING_DATA

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _B_DEFAULT,
        _CONVENTION,
        _BATCH_DEF_AC,
        _BATCH_DEF_PC,
        _BATCH_DEF_CODE,
        _BATCH_DEF_VAT,
    )

    # bDefault pic 99 (display, unsigned, scale 0) [copybooks/wsbatch.cob:L48] The COBOL
    # name is camel case - `bDefault`, verbatim - which is unique in this record and
    # unusual in the codebase.
    b_default: int = 0

    convention: str = _spaces(_CONVENTION)

    batch_def_ac: int = 0

    batch_def_pc: int = 0

    batch_def_code: str = _spaces(_BATCH_DEF_CODE)

    batch_def_vat: str = _spaces(_BATCH_DEF_VAT)


_WS_BATCH_RECORD: Final[FieldDescriptor] = _describe("WS-Batch-Record")
_ITEMS: Final[FieldDescriptor] = _describe("Items")
_BATCH_STATUS: Final[FieldDescriptor] = _describe("Batch-Status")
_CLEARED_STATUS: Final[FieldDescriptor] = _describe("Cleared-Status")
_BCYCLE: Final[FieldDescriptor] = _describe("Bcycle")
_DESCRIPTION: Final[FieldDescriptor] = _describe("Description")
_BATCH_START: Final[FieldDescriptor] = _describe("Batch-Start")


@dataclass(slots=True)
class GlBatchRecord:
    """`01 WS-Batch-Record.` - one General Ledger batch header.

    COBOL identifier, verbatim: `WS-Batch-Record` [copybooks/wsbatch.cob:L13]. The class
    name departs from the mechanical PascalCase of that identifier, which would be
    `WsBatchRecord`, because Agent Action Plan section 0.4.3 fixes the consumer's import
    line.
    """

    # The 01-level record's own dictionary entry.
    GROUP: ClassVar[FieldDescriptor] = _WS_BATCH_RECORD

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _ITEMS,
        _BATCH_STATUS,
        _CLEARED_STATUS,
        _BCYCLE,
        _DESCRIPTION,
        _BATCH_START,
    )

    ws_batch_key: WsBatchKey = field(default_factory=WsBatchKey)

    # 03 WS-Batch-Key9 redefines WS-Batch-Key - THE SAME SIX BYTES read as one 6-digit
    # value, and the only route by which the key reaches the database
    # [common/glbatchMT.cbl:L1069].
    ws_batch_key9: WsBatchKey9 = field(default_factory=WsBatchKey9)

    items: int = 0

    # Batch-Status pic 9 DISPLAY, unsigned, scale 0 [copybooks/wsbatch.cob:L25] 88
    # Status-Open value 0. [copybooks/wsbatch.cob:L26] 88 Status-Closed value 1.
    batch_status: int = 0

    cleared_status: int = 0

    bcycle: int = 0

    dates: BatchDates = field(default_factory=BatchDates)

    amounts: BatchAmounts = field(default_factory=BatchAmounts)

    # Description pic x(24) (alphanumeric, 24 characters) [copybooks/wsbatch.cob:L45]
    # The one field of this record that agrees across all three layers with no
    # disagreement of any kind - which is what makes the disagreements elsewhere worth
    # registering rather than assuming.
    description: str = _spaces(_DESCRIPTION)

    # 03 posting-data. - group of bDefault, Convention, Batch-Def-AC, Batch-Def-PC,
    # Batch-Def-Code, Batch-Def-Vat [copybooks/wsbatch.cob:L47] One of the two trailing
    # items a length misalignment would move (A-15).
    posting_data: PostingData = field(default_factory=PostingData)

    # Batch-Start pic 9(5) (display, unsigned, scale 0) [copybooks/wsbatch.cob:L54] The
    # last item in the layout, and the trailing item a length misalignment would move.
    # Question Q-4 settled it against the compiled program (rule R-6): both declared
    # copies measure 96 bytes and the 98-byte note is false, so the field sum governs and
    # nothing here shifts.
    batch_start: int = 0

    def __post_init__(self) -> None:
        """Bind the two declared key readings to their one six-byte storage."""
        self.ws_batch_key9.bind(self.ws_batch_key)


def _drift_register() -> tuple[str, ...]:
    """Collect this record's three-layer disagreements as they stand.

    Nothing is reduced to a flag, summarised as safe, averaged or decided. Rule R-4
    makes a legacy defect part of the specification, so the three views are registered
    side by side and the disagreement stays open.

    Returns:
        One line per disagreement, in copybook declaration order.
    """
    lines: list[str] = []
    for entry in loader.entries_for_copybook_record(_RECORD):
        copybook = entry.copybook
        if copybook is None:
            continue
        for detail in loader.drift_for(entry.key).details:
            lines.append(f"{copybook.name} [{entry.key}]: {detail}")
    return tuple(lines)


#: Every three-layer disagreement this record carries, in the dictionary's own words and
#: in copybook declaration order.
DRIFT_REGISTER: Final[tuple[str, ...]] = _drift_register()
