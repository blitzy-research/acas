"""The `File-Access` block: the file-status protocol record, laid out.

`01 File-Access.` [copybooks/wsfnctn.cob:L22] is a parameter of every handler
call the migrated cycle makes and the carrier of the status protocol:
`We-Error pic 999`, `Rrn pic 9(5) comp`, `Fs-Reply pic 99` and
`FS-Action pic x(22)`.

Two further blocks of the same copybook are declared here because they travel
with it: `Logging-Data` [copybooks/wsfnctn.cob:L43-L55], whose `WS-File-Key
pic x(64)` and `WS-Log-Where pic x(231)` widths truncate every log key a handler
writes, and `RDB-Data` [copybooks/wsfnctn.cob:L56-L63], the six connection
fields the data-access layer reads.

Plain dataclasses mirror that block field for field with nothing added (R-3).
The COBOL tree is frozen: read as the specification, never modified, and
nothing here executes, embeds or shells out to a COBOL program (R-1).

The central constraint is that the split of `wsfnctn.cob` is two-way: this module
takes the record LAYOUT and nothing else, while the function codes, access types,
`FS-Reply` values and the lock-retry ladder - the operation VOCABULARY - live in
`acas_posting.dal.status`, which is not on a record module's permitted import
list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Sorted deterministically - plain `sorted()` order over the public names, which
    # puts the two module constants and the six record classes ahead of the one
    # accessor.
    "ALL_FIELDS",
    "Curs2Parts",
    "CursParts",
    "DICTIONARY_RECORD",
    "FaRdbmsFlatStatuses",
    "FileAccess",
    "LoggingData",
    "RdbData",
    "citations",
)


#: The `01`-level record name, spelt as `copybooks/wsfnctn.cob` spells it at L22.
DICTIONARY_RECORD: Final[str] = "File-Access"

#: Every field of the block, in the dictionary's own copybook DECLARATION order.
ALL_FIELDS: Final[tuple[FieldDescriptor, ...]] = tuple(
    FieldDescriptor.from_dictionary_key(entry.key)
    for entry in loader.entries_for_copybook_record(DICTIONARY_RECORD)
)


def citations() -> tuple[str, ...]:
    """Return the provenance citation for every field of the block.

    The rule R-5 surface for this module, and the line the traceability document
    consumes. Each element is the loader's compact three-locator provenance string -
    copybook field, bridge host variable, database column - surfaced through
    `FieldDescriptor.cite` and reimplemented nowhere.

    Returns:
        One citation per field, in the copybook declaration order of `ALL_FIELDS`.
    """
    return tuple(descriptor.cite() for descriptor in ALL_FIELDS)


def _descriptor(field_name: str) -> FieldDescriptor:
    """Return the descriptor the dictionary holds for one item of the block.

    The single lookup path in this module.

    Args:
        field_name: The item's COBOL name, verbatim from the frozen copybook - case and
            hyphens preserved.

    Returns:
        The descriptor for that item.
    """
    return FieldDescriptor.from_dictionary_key(
        f"{DICTIONARY_RECORD}.{field_name}"
    )


def _members_of(group_name: str) -> tuple[FieldDescriptor, ...]:
    """Return one group's immediate members, in copybook declaration order.

    A filter over `ALL_FIELDS`, so the order is the dictionary's and the membership is
    the copybook's.

    Args:
        group_name: The group item's COBOL name, verbatim.

    Returns:
        Its immediate members, in declaration order.
    """
    return tuple(
        descriptor
        for descriptor in ALL_FIELDS
        if descriptor.parent_group == group_name
    )


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return the item's declared width filled with spaces.

    COBOL `value spaces` fills the WHOLE item, so an initial value must be as wide as
    the item is - 525 characters for either path item, 512 for the message item.

    Args:
        descriptor: The alphanumeric item to fill.

    Returns:
        A string of spaces at the item's declared character length.
    """
    return " " * (descriptor.character_length or 0)


# From the copybook's own VALUE clauses, of which SEVENTEEN sit on data items -
# amendment A-iii, the plan's enumeration having listed ten.


@dataclass(slots=True)
class CursParts:
    """The line-and-column view of `Curs`.

    A REDEFINES is one storage area seen two ways, not a second area. Whether the four
    digits of `Curs` or the two-plus-two of `Lin` and `Cole` are the live reading at a
    given moment is the reading program's business.
    """

    GROUP: ClassVar[FieldDescriptor] = _descriptor("filler#28")

    #: Its 2 members, L29 -> L30.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Lin"),
        _descriptor("Cole"),
    )

    lin: int = 0

    cole: int = 0


@dataclass(slots=True)
class Curs2Parts:
    """The line-and-column view of `Curs2`.

    The second anonymous redefining group, named here for its target `Curs2` [:L31] by
    the same rule and for the same reason as `CursParts` above.
    """

    GROUP: ClassVar[FieldDescriptor] = _descriptor("filler#32")

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Lin2"),
        _descriptor("Col2"),
    )

    lin2: int = 0

    col2: int = 0


@dataclass(slots=True)
class LoggingData:
    """`03 Logging-Data.` - the file-handler logging and error sub-block.

    Declared at [copybooks/wsfnctn.cob:L44] with ELEVEN members at L45 through L55. The
    plan quotes the span as L44-L56; L56 is the sibling group `RDB-Data`, so the frozen
    span ends at L55 (docstring amendment table).
    """

    GROUP: ClassVar[FieldDescriptor] = _descriptor("Logging-Data")

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of("Logging-Data")

    accept_reply: str = _spaces(_descriptor("Accept-Reply"))

    file_key_no: int = 0

    ws_log_system: int = 0

    ws_no_paragraph: int = 0

    sql_err: str = _spaces(_descriptor("SQL-Err"))

    sql_msg: str = _spaces(_descriptor("SQL-Msg"))

    sql_state: str = _spaces(_descriptor("SQL-State"))

    ws_file_key: str = _spaces(_descriptor("WS-File-Key"))

    ws_log_where: str = _spaces(_descriptor("WS-Log-Where"))

    ws_log_file_no: int = 0

    ws_count_rows: int = 0


@dataclass(slots=True)
class RdbData:
    """`03 RDB-Data.` - the relational connection parameter sub-block.

    Declared at [copybooks/wsfnctn.cob:L56] with SIX members at L57 through L62. The
    plan quotes it as L57-L64; L63-L64 are comments, so the frozen span is the header at
    L56 and six fields at L57-L62 (docstring amendment table).
    """

    GROUP: ClassVar[FieldDescriptor] = _descriptor("RDB-Data")

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of("RDB-Data")

    db_schema: str = _spaces(_descriptor("DB-Schema"))

    db_uname: str = _spaces(_descriptor("DB-UName"))

    # 05  DB-UPass    pic x(12)  value spaces.          [:L59]
    #
    # `repr=False`, AND NOTHING ELSE ABOUT THIS FIELD CHANGES. It is still the
    # third member of the group, still `x(12)`, still defaulted to twelve spaces
    # by the same `_spaces(_descriptor(...))` call, still readable and writable by
    # name, and still listed in `FIELDS` above - so the layout, the declaration
    # order, the value and every dictionary and descriptor lookup are byte-for-byte
    # what they were (rules R-3 and R-5).
    #
    # What changes is the DEFAULT `__repr__` this dataclass generates, which
    # rendered every field including this one. Nothing in the migrated cycle logs
    # the whole block today, and that is precisely the point: the exposure is
    # latent, one `_LOG.debug("%s", rdb_data)` or one failing assertion away, and a
    # password in a log file is not a defect that can be taken back afterwards
    # (CWE-532). Excluding it here removes the hazard at the source rather than
    # relying on every future call site to remember.
    #
    # THE VALUE IS NOT MASKED, only its rendering omitted. A caller that wants the
    # credential asks for `db_upass` and gets it, which is what
    # `dal/connection.py` does when it builds the connect parameters
    # [common/acas008.cbl:L558-L563]; a caller that renders the object gets every
    # other field and simply does not get this one.
    db_upass: str = field(default=_spaces(_descriptor("DB-UPass")), repr=False)

    db_host: str = _spaces(_descriptor("DB-Host"))

    db_socket: str = _spaces(_descriptor("DB-Socket"))

    db_port: str = _spaces(_descriptor("DB-Port"))


@dataclass(slots=True)
class FaRdbmsFlatStatuses:
    """`03 FA-RDBMS-Flat-Statuses.` - which store a handler should use.

    OBSERVATION O-1, THE LEVEL JUMP. The group is `03` and its children are `07` - not
    `05`, which is what every other group in this copybook uses.
    """

    GROUP: ClassVar[FieldDescriptor] = _descriptor("FA-RDBMS-Flat-Statuses")

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of(
        "FA-RDBMS-Flat-Statuses"
    )

    fa_file_system_used: int = 0

    fa_file_duplicates_in_use: int = 0


@dataclass(slots=True)
class FileAccess:
    """`01 File-Access.` - the file-status protocol block [:L22].

    That order is the record's byte layout and is preserved exactly (R-6). Note the two
    gaps it contains: L35-L37 and L40 are comments, so nothing is missing between `Col2`
    and `ACAS-Path`, or between `Path-Work` and `FS-Action`.
    """

    GROUP: ClassVar[FieldDescriptor] = _descriptor("File-Access")

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of("File-Access")

    we_error: int = 0

    # 03 Rrn pic 9(5) comp. [:L24] - no VALUE THE ONLY `COMP` ITEM IN THE BLOCK: binary,
    # unsigned, 5 digits, scale 0, 4 bytes.
    rrn: int = 0

    fs_reply: int = 0

    s1: str = _spaces(_descriptor("s1"))

    curs: int = 0

    curs_parts: CursParts = field(default_factory=CursParts)

    curs2: int = 0

    curs2_parts: Curs2Parts = field(default_factory=Curs2Parts)

    acas_path: str = _spaces(_descriptor("ACAS-Path"))

    path_work: str = _spaces(_descriptor("Path-Work"))

    fs_action: str = _spaces(_descriptor("FS-Action"))

    logging_data: LoggingData = field(default_factory=LoggingData)

    rdb_data: RdbData = field(default_factory=RdbData)

    main_record_move_flag: int = 0

    fa_rdbms_flat_statuses: FaRdbmsFlatStatuses = field(
        default_factory=FaRdbmsFlatStatuses
    )

    file_function: int = 0

    access_type: int = 0
