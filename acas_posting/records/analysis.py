"""The Analysis code record: `01 WS-Analysis-Record` [copybooks/wsanal.cob:L9].

Four columns of `ANALYSIS-REC` and the smallest layout in the migration - nine
declarations in nine lines, 36 bytes. Descriptors are looked up in the generated
dictionary, never transcribed (R-5).

Two representation facts are worth keeping. The four-level key group `WS-Pa-Code`
[copybooks/wsanal.cob:L10-L14] collapses into ONE `char(3)` column because the
bridge moves it as a whole [common/analMT.cbl:L943], so its four members have no
columns of their own and are declared here regardless. And `Pa-Gl` changes
storage class and width across the three layers - zoned `pic 9(6)` in the
copybook, `PIC 9(08) COMP` at the host variable, `mediumint(6) unsigned` at the
column - which the descriptors report from the copybook view only.

No sign drifts anywhere in this record, and it carries no fractional field at
all, so the exact-decimal carrier is not imported here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = ["PaGroup", "WsAnalysisRecord", "WsPaCode"]


# One constant each, so that the table name appears exactly once in executable code and
# a reader can see at a glance which of the three names denoting this layout is used for
# what.

_TABLE: Final[str] = "ANALYSIS-REC"

_COPYBOOK_RECORD: Final[str] = "WS-Analysis-Record"

# The one copybook every field of this record must come from. The guard below turns that
# into a check rather than an expectation.
_COPYBOOK_FILE: Final[str] = "copybooks/wsanal.cob"

# The twin's field prefix [copybooks/wsval.cob:L10-L17]. Named so the guard can refuse
# it by name; nothing else in this module has any use for it.
_TWIN_FIELD_PREFIX: Final[str] = "va-"


def _admit(name: str, file: str) -> None:
    """Refuse an entry that did not come from this record's own copybook.

    Two guards, both aimed at one specific way of going wrong.

    Args:
        name: The `copybook.name` an entry reports, verbatim.
        file: The `copybook.file` that entry reports.
    """
    assert file == _COPYBOOK_FILE, (
        f"the dictionary entry for {name!r} reports copybook file {file!r}; "
        f"every field of {_COPYBOOK_RECORD} is declared in {_COPYBOOK_FILE}. "
        f"A hit in copybooks/wsval.cob means the Analysis VALUE record was "
        f"reached instead - the two layouts are near-identical."
    )
    assert not name.startswith(_TWIN_FIELD_PREFIX), (
        f"the dictionary entry {name!r} carries the {_TWIN_FIELD_PREFIX!r} "
        f"prefix of the Analysis Value record [copybooks/wsval.cob:L10-L17]; "
        f"every field of {_COPYBOOK_RECORD} carries 'Pa-' or 'WS-Pa-'"
    )


def _dictionary_keys() -> dict[str, str]:
    """Map every field name of this copybook to its data dictionary key.

    The whole of rule R-5's mechanism for this module, and the reason no key is written
    as a literal below. Each entry supplies its OWN key and its OWN `copybook.name`;
    this function only pairs the two.

    Returns:
        Each `copybook.name` in this copybook, verbatim in its own casing, against the
            key that names its entry.
    """
    keys: dict[str, str] = {}

    column_mapped = loader.entries_for_table(_TABLE)
    # Agent Action Plan section 0.6.6 tabulates this table at four columns, and
    # mysql/ACASDB.sql:L32-L35 declares four.
    assert len(column_mapped) == 4, (
        f"the generated dictionary holds {len(column_mapped)} column-mapped "
        f"entries for {_TABLE}; mysql/ACASDB.sql:L31-L36 declares four"
    )
    for entry in column_mapped:
        copybook = entry.copybook
        if copybook is None:
            continue
        _admit(copybook.name, copybook.file)
        keys[copybook.name] = entry.key

    for entry in loader.entries_for_copybook_record(_COPYBOOK_RECORD):
        copybook = entry.copybook
        if copybook is None or entry.column is not None:
            continue
        _admit(copybook.name, copybook.file)
        keys[copybook.name] = entry.key

    return keys


# Built once, at class-definition time, from the loader's lazily read and cached
# document. This is the one read this module performs.
_KEY_BY_COBOL_NAME: Final[dict[str, str]] = _dictionary_keys()


def _descriptor(cobol_name: str) -> FieldDescriptor:
    """Describe one field of this copybook, by dictionary lookup.

    A COBOL field name in, the descriptor the generated dictionary holds for it out.

    Args:
        cobol_name: The field name exactly as `copybooks/wsanal.cob` spells it, mixed
            case included - `"WS-Pa-Code"`, `"Pa-Gl"`, `"Pa-Print"`.

    Returns:
        Its descriptor, carrying its dictionary key and its copybook locator.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_BY_COBOL_NAME[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """SPACES at the character width one alphanumeric item declares.

    The width is taken from the descriptor rather than typed, for the same reason every
    other property of a field is (rule R-5): `Pa-Desc` is 24 characters because
    `copybooks/wsanal.cob:L16` says so, not because 24 is written here.

    Args:
        descriptor: An alphanumeric item's descriptor.

    Returns:
        That many spaces.
    """
    return " " * (descriptor.character_length or 0)


# One per member declared in copybooks/wsanal.cob, L10 through L17, obtained by lookup
# and never transcribed. Four carry a column key and four a copybook-record key.

# 03 WS-Pa-Code. [copybooks/wsanal.cob:L10] The three-byte key group.
_WS_PA_CODE: Final[FieldDescriptor] = _descriptor("WS-Pa-Code")

_PA_SYSTEM: Final[FieldDescriptor] = _descriptor("Pa-System")

_PA_GROUP: Final[FieldDescriptor] = _descriptor("Pa-Group")

# 07 Pa-First pic x.
_PA_FIRST: Final[FieldDescriptor] = _descriptor("Pa-First")

_PA_SECOND: Final[FieldDescriptor] = _descriptor("Pa-Second")

_PA_GL: Final[FieldDescriptor] = _descriptor("Pa-Gl")

_PA_DESC: Final[FieldDescriptor] = _descriptor("Pa-Desc")

# 03 Pa-Print pic xxx. [copybooks/wsanal.cob:L17] The picture is spelled `xxx` rather
# than `x(3)`, and the dictionary holds it that way.
_PA_PRINT: Final[FieldDescriptor] = _descriptor("Pa-Print")


# Definition order ascends the copybook's level numbers - 07 group, 03 group, 01 record
# - because a nested member's starting value must name a class that already exists.


@dataclass(slots=True)
class PaGroup:
    """`05 Pa-Group.` [copybooks/wsanal.cob:L12] - the inner two-byte group.

    The second and third bytes of the record's key.
    """

    pa_first: str = _spaces(_PA_FIRST)

    pa_second: str = _spaces(_PA_SECOND)

    # Declaration order, as a tuple so the order cannot be perturbed (R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_PA_FIRST, _PA_SECOND)


@dataclass(slots=True)
class WsPaCode:
    """`03 WS-Pa-Code.` [copybooks/wsanal.cob:L10] - the three-byte key group.

    The `Ws` prefix is kept in this class name because the COBOL group carries it and
    the near-duplicate twin's equivalent group does not - `WS-Pa-Code` against `va-code`
    [copybooks/wsval.cob:L10].
    """

    pa_system: str = _spaces(_PA_SYSTEM)

    # 05 Pa-Group. [copybooks/wsanal.cob:L12] A group, so its starting value is its own
    # dataclass and never None.
    pa_group: PaGroup = field(default_factory=PaGroup)

    # Declaration order. `Pa-Group`'s own descriptor reports usage GROUP and no carrier,
    # because a group is the bytes of its children and holds nothing itself.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_PA_SYSTEM, _PA_GROUP)


@dataclass(slots=True)
class WsAnalysisRecord:
    """`01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9] - the record.

    The bridge does not `COPY` this copybook.
    """

    ws_pa_code: WsPaCode = field(default_factory=WsPaCode)

    # 03 Pa-Gl pic 9(6). [copybooks/wsanal.cob:L15] An `int`, because the copybook
    # declares six digits at zero scale: a store into it truncates as an integer store.
    pa_gl: int = 0

    pa_desc: str = _spaces(_PA_DESC)

    pa_print: str = _spaces(_PA_PRINT)

    # Declaration order, matching L10 through L17 with the key group counted once - the
    # same four the artifact keys by column, in column ordinal order.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_PA_CODE,
        _PA_GL,
        _PA_DESC,
        _PA_PRINT,
    )
