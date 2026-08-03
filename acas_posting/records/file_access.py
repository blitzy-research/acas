"""The `File-Access` block: the file-status protocol record, laid out.

`01 File-Access.` [copybooks/wsfnctn.cob:L22] is the third parameter of every
handler call the migrated cycle makes, and the carrier of the file-status
protocol between a program and the data-access layer. Agent Action Plan
section 0.4.3 gives the call it rides on, verbatim::

    FROM:  call "acas007" using System-Record WS-Batch-Record File-Access
                                File-Defs ACAS-DAL-Common-Data
    TO:    acas007_gl_batch.dispatch(system, batch, file_access, file_defs,
                                     dal_common)

Plain dataclasses mirror that block field for field with nothing added (R-3).
The COBOL tree is frozen: read as the specification, never modified, and
nothing here executes, embeds or shells out to a COBOL program (R-1).

THE TWO-WAY SPLIT - THE CENTRAL CONSTRAINT OF THIS MODULE
=========================================================
One COBOL copybook becomes TWO Python modules, because the copybook mixes a
data layout with an operation vocabulary and the Python layering separates
them - section 0.5.3 makes that split binding for every `COPY` of this
copybook. This module holds the LAYOUT half:

    THIS MODULE OWNS      the dataclasses and their attributes - every one of
                          the 35 elementary items the block declares,
                          including `File-Function` [:L88] and `Access-Type`
                          [:L107], plain `int` storage attributes here
                          because they are members of `01 File-Access` and
                          R-3 requires the record carry them.
    `dal/status.py` OWNS  the vocabulary: all 30 `88` condition names and
                          every enumeration built from them, the `Fs-Reply`
                          set 0/10/21/22/23/99, the `We-Error` codes, the
                          SQL-state mapping for duplicates and the lock-wait
                          ladder, per section 0.4.1.5.
    `dal/connection.py`   populates the six `RDB-Data` items [:L57-L62] -
    OWNS                  `DB-Schema`, `DB-UName`, `DB-UPass`, `DB-Host`,
                          `DB-Socket`, `DB-Port` - per section 0.4.1.5.

Nothing below defines an enumeration, a predicate over a `88` level, a reply
helper or a status table. The `88` levels are not lost: each travels on its
field's dictionary entry, as `notes` and as `copybook.condition_names` with a
per-name locator, so the vocabulary module derives them from the same
generated artifact this module reads rather than from a second transcription
(R-4 forbids two definitions of one vocabulary). Predicates over `88` levels
belong to `cobol/condition_names.py`, per section 0.4.1.4.

THE FROZEN STRUCTURE, AND SEVEN AMENDMENTS TO THE PLAN'S CITATIONS
==================================================================
`copybooks/wsfnctn.cob` is 117 lines and declares exactly ONE `01`-level item
- `01 File-Access.` at L22. Everything from L23 to L116 is subordinate to it;
L117 is a comment. Four spans quoted in the Agent Action Plan are approximate
and one runs past end-of-file, so the frozen spans are recorded here, this being
the authoritative record until `docs/migration/traceability.md` carries them
(R-5):

    PLAN SAYS                     FROZEN SOURCE
    File-Access L23-L38           `01 File-Access.` at L22; the group spans
                                  L22-L116; its elementary head is L23-L41
    Logging-Data L44-L56          header L44, children L45-L55, 11 fields.
                                  L56 is `03 RDB-Data.` - a SIBLING, so the
                                  quoted span swallows the next group header
    RDB-Data L57-L64              header L56, children L57-L62, 6 fields.
                                  L63-L64 are comments, not fields
    vocabulary L88-L118           the file has 117 lines, so L118 does not
                                  exist. `File-Function` L88 with its `88`
                                  levels L89-L105; `Access-Type` L107 with
                                  its `88` levels L108-L116

Three further amendments were found while checking the above, recorded rather
than quietly applied, because a wrong locator in a traceability document is
worse than none:

    A-i   The plan describes a duplicated `88` indicator separated by a TAB
          at L105, and calls it the only tab-containing line in the block. IT
          IS NOT PRESENT in this frozen copy: L105 reads `88
          fn-Read-Next-Header value 34.` with a single indicator and spaces
          only, and the file contains ZERO tab characters on any of its 117
          lines. Recorded as NOT REPRODUCED because there is nothing there to
          reproduce - inventing the oddity would misreport the specification
          just as surely as smoothing a real one away.
    A-ii  The maintainer's "NOT YET USED" annotation sits at L64, not L68. It
          is a comment ABOVE the `Main-Record-Move-Flag` group and annotates
          the whole flag mechanism; L68 carries no comment at all.
    A-iii The block carries SEVENTEEN data-item VALUE clauses, not the ten
          the plan enumerates. Seven more live in `Logging-Data`: L45, L47,
          L50, L52, L53, L54, L55. Every one is honoured below, because the
          governing directive is "defaults from the copybook's own VALUE
          clauses" and the enumeration accompanying it was partial.

ODDITIES PRESERVED, NEVER SMOOTHED (RULE R-4)
=============================================
None of the following carries an `A-` number in the anomaly register of
section 0.6.7 and none is flagged by the generated artifact, so they are
module-local observations and candidates for the migration's anomaly log:

    O-1  A LEVEL JUMP. `03 FA-RDBMS-Flat-Statuses.` [:L72] has `07`-level
         children at [:L73] and [:L82] - not `05`. COBOL permits any
         increasing level number; the jump is carried verbatim.
    O-2  NON-MONOTONIC condition-name values on `File-Function` [:L88]: 1
         through 9 [:L89-L97], then 15 [:L99], then 13 [:L100], then 31
         through 34 [:L102-L105], leaving 10-12, 14 and 16-30 unused. The
         header comments explain it - a widening was applied to the wrong
         item and reversed [:L11-L15]. Nobody may sort this into order.
    O-3  FIVE CONDITION NAMES ARE COMMENTED OUT at [:L76-L80] - MySql,
         Oracle, Postgres, DB2 and MS-SQL selectors - leaving the two live
         ones at [:L74-L75] and a `values 0 thru 1` range at [:L81]. They are
         named in this sentence and modelled NOWHERE: not as an attribute,
         not as a constant, not as commented-out code a later reader might
         mistake for a specification.
    O-4  `Fs-Reply` [:L25] declares ZERO condition names of its own. Its
         value set 0/10/21/22/23/99 comes from the handler programs, not this
         copybook - precisely why the vocabulary lives in a separate module.
    O-5  `Cole` [:L30] is spelt with a trailing `e` while its sibling is
         `Lin` [:L29]; the second view spells the same pair `Lin2` [:L33] and
         `Col2` [:L34]. Both spellings are carried as declared.
    O-6  BOTH anonymous redefining groups are named `filler` [:L28] and
         [:L32], so all four of `Lin`, `Cole`, `Lin2`, `Col2` report the SAME
         parent group and the parent name alone cannot tell the views apart.
         The member names separate them, which is why the two view classes
         below select their fields by name.
    O-7  All six `RDB-Data` items ship as `value spaces` [:L57-L62], so THERE
         IS NO CREDENTIAL ANYWHERE IN THE FROZEN SOURCE. Nothing is
         hard-coded here and nothing is read from the process environment;
         `dal/connection.py` fills the block (R-6).
    O-8  FIGURATIVE-CONSTANT SPELLINGS DISAGREE: `value space` singular at
         [:L45] against `value spaces` elsewhere, and `value zero` at [:L47]
         and [:L66] against `value zeroes` at [:L54] and [:L55]. Cosmetic in
         COBOL, and preserved in the comments regardless.
    O-9  A COMMENT IS ORPHANED FROM ITS FIELD: [:L42-L43] documents the value
         range of `File-Key-No`, declared four lines later at [:L46], and
         sits above the `Logging-Data` group header instead.
    O-10 `FA-File-Duplicates-In-Use` [:L82] is annotated "NO LONGER USED
         other than for a '6' = rdb", and `Main-Record-Move-Flag` [:L66] is
         annotated "NOT YET USED" at [:L64]. Both are declared anyway, so
         both are carried anyway.

THIS RECORD IS AN OUT PARAMETER - NEVER FROZEN
==============================================
`Fs-Reply` [:L25], `We-Error` [:L23], `SQL-Err` [:L49], `SQL-Msg` [:L50],
`SQL-State` [:L51] and `WS-Count-Rows` [:L55] are written BY the data-access
layer and read by the caller after the call returns; `File-Function` [:L88]
and `Access-Type` [:L107] are written by the caller before it. So every class
below is a mutable dataclass. `slots=True` is used - it costs nothing and
makes a mistyped attribute name an immediate error rather than a silently
ignored assignment, which suits a record R-3 forbids extending - but
`frozen=True` would break the parameter protocol outright and appears NOWHERE
in this module.

The block holds no monetary and no fractional item: the generated artifact
reports every one of its 35 elementary fields as INT or STR and NOT ONE as a
scaled numeric, so no exact-decimal carrier is imported and no binary-fraction
type is named anywhere below (R-2). `Rrn` [:L24] is the ONLY `COMP` item -
`pic 9(5) comp`, five digits, scale zero, unsigned, four bytes wide. Its usage
is declared on the item itself, not inherited from a group, and reading it off
the PICTURE line alone would type it as zoned DISPLAY and change its stored
representation. This module never reads a PICTURE line: usage arrives from the
dictionary.

DESCRIPTOR PROVENANCE - LOOKED UP, NEVER TRANSCRIBED (RULE R-5)
===============================================================
`File-Access` maps to NO table; it is file-status working storage and does not
appear in the entity-to-table spine of section 0.2.1.1. The dictionary covers
it all the same, and this was PROBED rather than assumed before a line of it
was written: `entries_for_copybook_record("File-Access")` returns 41 entries -
the `01` group, 5 subordinate groups and the 35 elementary items - each keyed
`File-Access.<FIELD-NAME>` and each carrying a copybook view with picture,
usage, digits, scale, character length, sign, level, redefines target and
parent group. The nested group names are NOT record names and raise on lookup,
which is the expected shape: a key names the `01` record, never a group inside
it.

Every descriptor below is therefore built by `from_dictionary_key`, and NOT
ONE component is typed in by hand - not a digit count, not a character width,
not a usage class, not a redefines target. Even the 525-character space
defaults are `" " * descriptor.character_length` rather than a literal, so a
width can never drift from the frozen source. Qualification matters even for a
table-less block: keyed by name alone, `Curs`'s two anonymous redefining views
would collide with each other. They are keyed by DECLARATION LINE -
`filler#28` and `filler#32` - the artifact's own convention for a repeated
name inside one record. `acas_posting.dictionary.loader` documents both key
forms; `FieldDescriptor.cite()` surfaces the three-locator provenance string
and `citations()` below surfaces it for the whole block at once. Neither is
reimplemented here.

LAYERING - THIS IS A LEAF MODULE (SECTION 0.4.3)
================================================
The temptation specific to this file is the status vocabulary: `dal/status.py`
and `dal/connection.py` import THIS module, never the reverse, so an import of
either would invert the dependency and close a cycle. They are pointed at in
prose above and imported nowhere. Section 0.4.3 gives the reason - the
arithmetic test tier "imports only `cobol` and `records` and touches no
database, so it runs anywhere" - and one import reaching into `dal` would drag
a database driver into that tier. Nothing here opens a connection, issues SQL
or emits DDL (R-3).

Field order is the copybook's declaration order and is not chosen here; the
whole-block descriptor tuple is ordered BY THE DICTIONARY rather than by a
sequence retyped in this file. Every fixed collection is a tuple. There is no
clock read, no entropy source, no process-environment read, no host lookup and
no directory scan anywhere below, so two runs of one scenario see identical
metadata (R-6). See `acas_posting.records` for the conventions every record
module shares.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Sorted deterministically - plain `sorted()` order over the public names,
    # which puts the two module constants and the six record classes ahead of
    # the one accessor. Every other `__all__` in this package is ordered the
    # same way, so regrouping the constants ahead of the classes in isort
    # style would leave this the only module out of step. The plain sort stays.
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


#  THE BLOCK AS THE GENERATED DICTIONARY HOLDS IT  (RULE R-5)

#: The `01`-level record name, spelt as `copybooks/wsfnctn.cob` spells it at
#: L22. It is the first half of every dictionary key this module uses, and it
#: is written ONCE so that no key in the file can carry a different record.
DICTIONARY_RECORD: Final[str] = "File-Access"

#: Every field of the block, in the dictionary's own copybook DECLARATION
#: order: the `01` group, its 5 subordinate groups and its 35 elementary
#: items - 41 descriptors, L22 through L107.
#:
#: The order is DERIVED and not chosen. Rule R-6 makes an observable ordering
#: part of behaviour, and a record's field order is its byte layout, so this
#: module takes the order the generated artifact publishes rather than
#: retyping a sequence that could drift from the frozen source. It is also
#: what lets each class below select its own members by filtering rather than
#: by listing them again.
ALL_FIELDS: Final[tuple[FieldDescriptor, ...]] = tuple(
    FieldDescriptor.from_dictionary_key(entry.key)
    for entry in loader.entries_for_copybook_record(DICTIONARY_RECORD)
)


def citations() -> tuple[str, ...]:
    """Return the provenance citation for every field of the block.

    The rule R-5 surface for this module, and the line
    the traceability document consumes. Each element is the loader's
    compact three-locator provenance string - copybook field, bridge host
    variable, database column - surfaced through
    `FieldDescriptor.cite` and reimplemented nowhere. Every field of this
    block is copybook-only, so each citation renders its bridge and column
    locators as `absent`, which is itself the fact worth recording: the
    file-status block reaches no table.

    Returns:
        One citation per field, in the copybook declaration order of
        `ALL_FIELDS`.
    """
    return tuple(descriptor.cite() for descriptor in ALL_FIELDS)


def _descriptor(field_name: str) -> FieldDescriptor:
    """Return the descriptor the dictionary holds for one item of the block.

    The single lookup path in this module. `FieldDescriptor
    .from_dictionary_key` is memoised on the key, so a repeated call returns
    the same frozen object and the class bodies below cost one lookup per
    field however many times a name is mentioned.

    Args:
        field_name: The item's COBOL name, verbatim from the frozen copybook -
            case and hyphens preserved. For either anonymous redefining group
            this is the artifact's repeated-name form, `filler#28` or
            `filler#32`, carrying the declaration line.

    Returns:
        The descriptor for that item.
    """
    return FieldDescriptor.from_dictionary_key(
        f"{DICTIONARY_RECORD}.{field_name}"
    )


def _members_of(group_name: str) -> tuple[FieldDescriptor, ...]:
    """Return one group's immediate members, in copybook declaration order.

    A filter over `ALL_FIELDS`, so the order is the dictionary's and the
    membership is the copybook's. Subordinate GROUPS are included, because a
    group item is an immediate member of its parent just as an elementary item
    is - which is what keeps each class's `FIELDS` aligned one-for-one with
    its own dataclass attributes, nested sub-records included.

    This cannot separate the two anonymous redefining views: both are named
    `filler` [copybooks/wsfnctn.cob:L28] and [:L32], so `Lin`, `Cole`, `Lin2`
    and `Col2` all report the same parent name (observation O-6). Those two
    classes list their members by name instead.

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

    COBOL `value spaces` fills the WHOLE item, so an initial value must be as
    wide as the item is - 525 characters for either path item, 512 for the
    message item. The width comes from the descriptor rather than from a
    literal typed here, so it cannot drift from the frozen source (R-5); a
    numeric item has no character length and is never passed to this helper.

    This is initialisation and not a store: padding, truncation and
    justification when a value is MOVEd into a field are `cobol/move.py`'s
    semantics, and no such rule is applied anywhere in this module.

    Args:
        descriptor: The alphanumeric item to fill.

    Returns:
        A string of spaces at the item's declared character length.
    """
    return " " * (descriptor.character_length or 0)


#   WHERE THE DEFAULT VALUES COME FROM
# From the copybook's own VALUE clauses, of which SEVENTEEN sit on data items - amendment A-iii,
# the plan's enumeration having listed ten. Eleven take `value spaces`
# [copybooks/wsfnctn.cob:L38-L39], [:L41], [:L50], [:L52-L53], [:L57-L62]; Accept-Reply [:L45]
# takes the SINGULAR `value space` (observation O-8); two take `value zero` [:L47], [:L66]; two
# take the PLURAL `value zeroes` [:L54-L55]. EIGHTEEN carry NO VALUE clause: [:L23-L27],
# [:L29-L31], [:L33-L34], [:L46], [:L48-L49], [:L51], [:L73], [:L82], [:L88], [:L107].
# COBOL leaves those eighteen unspecified and no dialect flag is set in the frozen build
# scripts, so only the compiled program settles them (R-6). ONE convention covers all eighteen -
# alphanumeric takes spaces at its declared width, numeric takes 0 - and nothing depends on the
# choice, deliberately: each is written before it is read. This is initialisation and not a
# store; see `AcasFileAccess`.


#  THE TWO REDEFINING VIEWS OVER THE CURSOR ITEMS


@dataclass(slots=True)
class CursParts:
    """The line-and-column view of `Curs`.

    COBOL original, verbatim [copybooks/wsfnctn.cob:L28-L30]:

        03  filler redefines Curs.
            05  Lin         pic 99.
            05  Cole        pic 99.

    WHY THIS CLASS IS NAMED AT ALL. The COBOL group is ANONYMOUS - it is
    declared `filler`, so it has no name a Python attribute could take, yet
    its two members must each have an attribute and a citable descriptor.
    `CursParts` is therefore named for the item it redefines, `Curs` [:L27],
    which is the only naming rule that stays true to the source: it says what
    storage the view describes and it invents no COBOL identity. The generated
    artifact keys the group by its declaration line, `File-Access.filler#28`,
    and its `redefines` component carries the target `Curs` as declared - this
    module reads that rather than asserting it.

    A REDEFINES is one storage area seen two ways, not a second area. Whether
    the four digits of `Curs` or the two-plus-two of `Lin` and `Cole` are the
    live reading at a given moment is the reading program's business; this
    module holds both views side by side and adjudicates nothing, because
    choosing one would be exactly the sort of tidying rule R-4 forbids.

    Note the spelling: `Cole` carries a trailing `e` that its sibling `Lin`
    does not, and that the second view's `Col2` does not either (observation
    O-5). It is preserved exactly as declared.
    """

    #: `03  filler redefines Curs.` [copybooks/wsfnctn.cob:L28]
    GROUP: ClassVar[FieldDescriptor] = _descriptor("filler#28")

    #: Its 2 members, L29 -> L30. Listed by NAME rather than filtered by
    #: parent, because both anonymous views are named `filler` and the parent
    #: name cannot separate them (observation O-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Lin"),
        _descriptor("Cole"),
    )

    # 05  Lin         pic 99.    [copybooks/wsfnctn.cob:L29] - no VALUE clause
    lin: int = 0

    # 05  Cole        pic 99.    [copybooks/wsfnctn.cob:L30] - no VALUE clause
    cole: int = 0


@dataclass(slots=True)
class Curs2Parts:
    """The line-and-column view of `Curs2`.

    COBOL original, verbatim [copybooks/wsfnctn.cob:L32-L34]:

        03  filler redefines Curs2.
            05  Lin2        pic 99.
            05  Col2        pic 99.

    The second anonymous redefining group, named here for its target `Curs2`
    [:L31] by the same rule and for the same reason as `CursParts` above: the
    COBOL group is `filler` and has no name to carry over, so the view is
    named for the storage it re-describes. The artifact keys it
    `File-Access.filler#32`.

    This is where the two views stop being interchangeable in the source: this
    pair is spelt `Lin2` and `Col2`, without the trailing `e` that `Cole`
    [:L30] carries. Two declarations of one idea that disagree on spelling are
    left disagreeing (observation O-5).
    """

    #: `03  filler redefines Curs2.` [copybooks/wsfnctn.cob:L32]
    GROUP: ClassVar[FieldDescriptor] = _descriptor("filler#32")

    #: Its 2 members, L33 -> L34. Listed by name, per observation O-6.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Lin2"),
        _descriptor("Col2"),
    )

    # 05  Lin2        pic 99.    [copybooks/wsfnctn.cob:L33] - no VALUE clause
    lin2: int = 0

    # 05  Col2        pic 99.    [copybooks/wsfnctn.cob:L34] - no VALUE clause
    col2: int = 0


#  THE LOGGING SUB-BLOCK


@dataclass(slots=True)
class LoggingData:
    """`03 Logging-Data.` - the file-handler logging and error sub-block.

    Declared at [copybooks/wsfnctn.cob:L44] with ELEVEN members at L45
    through L55. The plan quotes the span as L44-L56; L56 is the sibling group
    `RDB-Data`, so the frozen span ends at L55 (docstring amendment table).

    Four of its members are the data-access layer's report back to the caller
    after a call - `SQL-Err` [:L49], `SQL-Msg` [:L50], `SQL-State` [:L51] and
    `WS-Count-Rows` [:L55], the last of which the value-analysis handler uses
    to report how many rows a delete-all removed, per the maintainer's own
    note at [:L55]. The rest are set by the caller BEFORE a call, and the
    maintainer says so inline: `ws-Log-System` [:L47], `WS-File-Key` [:L52]
    and `WS-Log-File-No` [:L54] are each annotated "loaded by caller".

    `File-Key-No` [:L46] is the item the comment at [:L42-L43] documents - a
    value range - except that the comment sits above this group's header
    rather than beside the field it describes (observation O-9). It is the
    same key number the four-way system handler dispatches on, selecting one
    of four tables by value.

    Nothing here writes a log file, opens a stream or names a log path. This
    is the LAYOUT of the logging parameter block; the handler modules under
    `dal/` fill it, and the frozen file-handler logging program is out of
    scope for this migration.
    """

    #: `03  Logging-Data.` [copybooks/wsfnctn.cob:L44]
    GROUP: ClassVar[FieldDescriptor] = _descriptor("Logging-Data")

    #: Its 11 members, in copybook declaration order, L45 -> L55.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of("Logging-Data")

    # 05  Accept-Reply    pic x      value space.       [:L45]
    # `value space`, singular, where every sibling says `spaces` - O-8.
    accept_reply: str = _spaces(_descriptor("Accept-Reply"))

    # 05  File-Key-No     pic 9.                        [:L46] - no VALUE
    file_key_no: int = 0

    # 05  ws-Log-System   pic 9      value zero.        [:L47]
    ws_log_system: int = 0

    # 05  ws-No-Paragraph pic 999.                      [:L48] - no VALUE
    ws_no_paragraph: int = 0

    # 05  SQL-Err         pic x(5).                     [:L49] - no VALUE
    sql_err: str = _spaces(_descriptor("SQL-Err"))

    # 05  SQL-Msg         pic x(512) value spaces.      [:L50]
    sql_msg: str = _spaces(_descriptor("SQL-Msg"))

    # 05  SQL-State       pic x(5).                     [:L51] - no VALUE
    sql_state: str = _spaces(_descriptor("SQL-State"))

    # 05  WS-File-Key     pic x(64)  value spaces.      [:L52]
    ws_file_key: str = _spaces(_descriptor("WS-File-Key"))

    # 05  WS-Log-Where    pic x(231) value spaces.      [:L53]
    ws_log_where: str = _spaces(_descriptor("WS-Log-Where"))

    # 05  WS-Log-File-No  pic 99     value zeroes.      [:L54]
    ws_log_file_no: int = 0

    # 05  WS-Count-Rows   pic 9(7)   value zeroes.      [:L55]
    ws_count_rows: int = 0


#  THE DATABASE CONNECTION SUB-BLOCK


@dataclass(slots=True)
class RdbData:
    """`03 RDB-Data.` - the relational connection parameter sub-block.

    Declared at [copybooks/wsfnctn.cob:L56] with SIX members at L57 through
    L62. The plan quotes it as L57-L64; L63-L64 are comments, so the frozen
    span is the header at L56 and six fields at L57-L62 (docstring amendment
    table). The maintainer's own change history dates the block: `DB-UName`,
    `DB-UPass` and `DB-Schema` came first, `DB-Socket`, `DB-Host` and `DB-Port`
    were added later, and `DB-Socket` was widened from 32 to 64 characters
    [:L6-L7].

    THERE IS NO CREDENTIAL IN THE FROZEN SOURCE. All six items are declared
    `value spaces` (observation O-7), so a default-constructed block carries
    six runs of spaces and nothing else - which is exactly what it must carry.
    Per section 0.4.1.5 the job of filling it belongs to `dal/connection.py`,
    which builds its connection from this block's six items. This module
    declares the SHAPE and no value:

      * no schema name, user name, credential, host name, socket path or port
        number is written here, in any form, in code or in a comment;
      * nothing is read from the process environment, from a parameter file or
        from any ambient source - that would be both a layering violation and
        a determinism hazard under rule R-6, since two runs of one scenario
        must be byte-identical;
      * no connection is opened, no driver is imported and no statement is
        issued - this is a record layout in a leaf module (R-1).

    The declared widths are worth noting because they CONSTRAIN what may ever
    be stored: 12 characters each for `DB-Schema`, `DB-UName` and `DB-UPass`,
    32 for host, 64 for socket and 5 for port. A parameter longer than its
    item does not fit, and truncation on store is `cobol/move.py`'s semantics,
    not this module's.
    """

    #: `03  RDB-Data.` [copybooks/wsfnctn.cob:L56]
    GROUP: ClassVar[FieldDescriptor] = _descriptor("RDB-Data")

    #: Its 6 members, in copybook declaration order, L57 -> L62.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of("RDB-Data")

    # 05  DB-Schema   pic x(12)  value spaces.          [:L57]
    db_schema: str = _spaces(_descriptor("DB-Schema"))

    # 05  DB-UName    pic x(12)  value spaces.          [:L58]
    db_uname: str = _spaces(_descriptor("DB-UName"))

    # 05  DB-UPass    pic x(12)  value spaces.          [:L59]
    #
    # ⭐ `repr=False`, AND NOTHING ELSE ABOUT THIS FIELD CHANGES. It is still the
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

    # 05  DB-Host     pic x(32)  value spaces.          [:L60]
    db_host: str = _spaces(_descriptor("DB-Host"))

    # 05  DB-Socket   pic x(64)  value spaces.          [:L61]
    # Widened from 32 to 64 characters by the maintainer [:L7].
    db_socket: str = _spaces(_descriptor("DB-Socket"))

    # 05  DB-Port     pic x(5)   value spaces.          [:L62]
    # Alphanumeric, not numeric - the port travels as 5 characters.
    db_port: str = _spaces(_descriptor("DB-Port"))


#  THE FILE-SYSTEM SELECTION SUB-BLOCK  -  AND THE LEVEL JUMP


@dataclass(slots=True)
class FaRdbmsFlatStatuses:
    """`03 FA-RDBMS-Flat-Statuses.` - which store a handler should use.

    COBOL original, verbatim [copybooks/wsfnctn.cob:L72-L83], comments and all:

        03  FA-RDBMS-Flat-Statuses.    *> Comes from System-Record via acas0nn
            07  FA-File-System-Used  pic 9.
                88  FA-FS-Cobol-Files-Used        value zero.
                88  FA-FS-RDBMS-Used              value 1.
        *>                 ... five further options, commented out ...
                88  FA-FS-Valid-Options           values 0 thru 1.
            07  FA-File-Duplicates-In-Use pic 9.
                88  FA-FS-Duplicate-Processing    value 1.

    OBSERVATION O-1, THE LEVEL JUMP. The group is `03` and its children are
    `07` - not `05`, which is what every other group in this copybook uses.
    COBOL only requires a subordinate level number to be greater than its
    parent's, so `07` under `03` is legal and means precisely what `05` would
    have meant. It is carried verbatim, the generated artifact records the
    `07` on both items, and it is not renumbered: an oddity in the source is
    preserved, never smoothed (R-4, section 0.4.1.3).

    OBSERVATION O-3, THE COMMENTED-OUT OPTIONS. Five further back-end
    selectors are commented out at [:L76-L80], leaving two live values and a
    `values 0 thru 1` range at [:L81] whose own trailing comment shows the
    range once reached 5. They are named ONCE, in the module docstring, and
    modelled NOWHERE - not as an attribute, not as a constant, and not as
    commented-out Python that a later reader could mistake for a
    specification. Inactive source is inactive specification.

    OBSERVATION O-10. `FA-File-Duplicates-In-Use` [:L82] is annotated "NO
    LONGER USED other than for a '6' = rdb" by the maintainer. It is declared,
    so it is carried; a field the migration would rather not have is still a
    field the record has (R-3).

    The two `pic 9` items are plain `int` storage here. Their four condition
    names are vocabulary and belong to `dal/status.py` per section 0.5.3, and
    the group's own comment says where the values come from: the system record,
    by way of the numbered handler that was called.
    """

    #: `03  FA-RDBMS-Flat-Statuses.` [copybooks/wsfnctn.cob:L72]
    GROUP: ClassVar[FieldDescriptor] = _descriptor("FA-RDBMS-Flat-Statuses")

    #: Its 2 members, in copybook declaration order, L73 and L82 - both
    #: declared at level `07` under a `03` group (observation O-1).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of(
        "FA-RDBMS-Flat-Statuses"
    )

    # 07  FA-File-System-Used  pic 9.                   [:L73] - no VALUE
    # Level 07 under a 03 group - the jump of observation O-1.
    fa_file_system_used: int = 0

    # 07  FA-File-Duplicates-In-Use pic 9.              [:L82] - no VALUE
    fa_file_duplicates_in_use: int = 0


#  THE RECORD ITSELF


@dataclass(slots=True)
class FileAccess:
    """`01 File-Access.` - the file-status protocol block [:L22].

    The third parameter of every handler call, and the one record both sides of a
    call write. Its members are declared below in the copybook's own order, L23
    through L107, with each subordinate group appearing where its header is::

        L23  We-Error       L28  filler redefines Curs   L44  Logging-Data*
        L24  Rrn            L31  Curs2                   L56  RDB-Data*
        L25  Fs-Reply       L32  filler redefines Curs2  L66  Main-Record-Move-Flag
        L26  s1             L38  ACAS-Path               L72  FA-RDBMS-Flat-Stats*
        L27  Curs           L39  Path-Work               L88  File-Function
                            L41  FS-Action               L107 Access-Type
                                                         (* = sub-record)

    That order is the record's byte layout and is preserved exactly (R-6). Note
    the two gaps it contains: L35-L37 and L40 are comments, so nothing is missing
    between `Col2` and `ACAS-Path`, or between `Path-Work` and `FS-Action`.

    AN OUT PARAMETER, SO NEVER FROZEN. The caller sets `File-Function` and
    `Access-Type` before a call; the data-access layer sets `We-Error`, `Fs-Reply`
    and the four items of `Logging-Data` that report an error during one; the
    caller reads them after it returns. A frozen record would make the protocol
    impossible to express, so this class is mutable, and so is every sub-record it
    holds. `slots=True` makes a mistyped attribute name fail immediately instead of
    silently adding a field the copybook does not declare - which suits a record
    R-3 forbids extending.

    WHAT THIS RECORD DOES NOT CARRY. No reply-code enumeration, no code table, no
    predicate over a `88` level, no error-mapping helper and no method that
    interprets `Fs-Reply` - the vocabulary belongs to `dal/status.py` (section
    0.5.3) and the `88` predicates to `cobol/condition_names.py` (section
    0.4.1.4). `Fs-Reply` [:L25] declares no `88` levels of its own in any case
    (observation O-4): its value set is derived from the handler programs, which
    is the reason the split exists.

    Usage, both shapes the migrated cycle relies on - construction, then the
    caller stating an operation and reading the handler's reply back out:

        >>> access = FileAccess()
        >>> access.fs_reply, access.we_error
        (0, 0)
        >>> access.rdb_data.db_schema == " " * 12   # `value spaces` [:L57]
        True
        >>> access.file_function = 3               # `fn-read-next` [:L91]
        >>> access.access_type = 1                 # `fn-input`     [:L108]
        >>> access.fs_reply = 10                   # set by the handler
        >>> access.logging_data.ws_count_rows = 0
        >>> access.fs_reply
        10

    Every field's storage metadata is a dictionary lookup, and every lookup
    carries its own frozen-source locator:

        >>> FileAccess.FIELDS[1].name, FileAccess.FIELDS[1].usage.value
        ('Rrn', 'COMP')
        >>> len(FileAccess.FIELDS)
        17
    """

    #: `01  File-Access.` [copybooks/wsfnctn.cob:L22] - the sole `01`-level
    #: item in the copybook; L23 through L116 are all subordinate to it.
    GROUP: ClassVar[FieldDescriptor] = _descriptor("File-Access")

    #: Its 17 immediate members, in copybook declaration order, L23 -> L107.
    #: Subordinate groups are included, so this tuple aligns one-for-one with
    #: this class's own dataclass attributes, sub-records included.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _members_of("File-Access")

    # 03  We-Error        pic 999.                      [:L23] - no VALUE
    # Widened to 3 digits by the maintainer while chasing a missing-data bug
    # in the period-totals table [:L8-L9]. Written by the handler.
    we_error: int = 0

    # 03  Rrn             pic 9(5)   comp.              [:L24] - no VALUE
    # THE ONLY `COMP` ITEM IN THE BLOCK: binary, unsigned, 5 digits, scale 0,
    # 4 bytes. "increased from 9 for GL" [:L24], and again at [:L16]. Its
    # usage is declared on the item and is taken from the dictionary, never
    # read off the PICTURE line - which alone would type it zoned DISPLAY.
    rrn: int = 0

    # 03  Fs-Reply        pic 99.                       [:L25] - no VALUE
    # The file status the handler reports back. Declares ZERO condition names
    # here (observation O-4); its value set lives in `dal/status.py`.
    fs_reply: int = 0

    # 03  s1              pic x.                        [:L26] - no VALUE
    # "this is USED for some programs 28.05.18" - the maintainer's own note.
    s1: str = _spaces(_descriptor("s1"))

    # 03  Curs            pic 9(4).                     [:L27] - no VALUE
    # A cursor position as four digits; `curs_parts` below is the same four
    # digits seen as a line and a column.
    curs: int = 0

    # 03  filler redefines Curs.                        [:L28]
    # The anonymous redefining group, named `CursParts` for its target.
    curs_parts: CursParts = field(default_factory=CursParts)

    # 03  Curs2           pic 9(4).                     [:L31] - no VALUE
    curs2: int = 0

    # 03  filler redefines Curs2.                       [:L32]
    curs2_parts: Curs2Parts = field(default_factory=Curs2Parts)

    # 03  ACAS-Path       pic x(525)     value spaces.  [:L38]
    # "Holds path to current working dir - used for screen dump & restores"
    # [:L36], added for the save and dump files [:L18]. The migrated cycle is
    # headless, so it carries its declared default and nothing writes it.
    acas_path: str = _spaces(_descriptor("ACAS-Path"))

    # 03  Path-Work       pic x(525)     value spaces.  [:L39]
    path_work: str = _spaces(_descriptor("Path-Work"))

    # 03  FS-Action       pic x(22)  value spaces.      [:L41]
    # Widened from 20 to 22 characters for the longest message in the
    # system-setup program [:L10].
    fs_action: str = _spaces(_descriptor("FS-Action"))

    # 03  Logging-Data.                                 [:L44]
    logging_data: LoggingData = field(default_factory=LoggingData)

    # 03  RDB-Data.                                     [:L56]
    # Six items, all `value spaces`; `dal/connection.py` fills them (O-7).
    rdb_data: RdbData = field(default_factory=RdbData)

    # 03  Main-Record-Move-Flag pic 9 value zero.       [:L66]
    # Two condition names at [:L67-L68], both vocabulary. The maintainer's
    # "NOT YET USED" note is at [:L64], above this item - amendment A-ii,
    # which the plan places at [:L68].
    main_record_move_flag: int = 0

    # 03  FA-RDBMS-Flat-Statuses.                       [:L72]
    # `07`-level children under a `03` group - observation O-1.
    fa_rdbms_flat_statuses: FaRdbmsFlatStatuses = field(
        default_factory=FaRdbmsFlatStatuses
    )

    # 03  File-Function   pic 99.                       [:L88] - no VALUE
    # The operation the caller is asking for, as a plain 2-digit number. 15
    # condition names at [:L89-L105], with NON-MONOTONIC values - 9, then 15,
    # then 13, then 31 through 34 (observation O-2). Widened to `pic 99` after
    # the widening was first applied to the wrong item [:L11-L15]. The names
    # are vocabulary and are defined in `dal/status.py`, not here.
    file_function: int = 0

    # 03  Access-Type     pic 9.                        [:L107] - no VALUE
    # "For rdbms 2 should cover all !!!" [:L107]. Stayed `pic 9` when the
    # intended widening moved to `File-Function` [:L14]. 9 condition names at
    # [:L108-L116], the last of which the maintainer activated for the stock
    # file [:L20]; all of them vocabulary.
    access_type: int = 0
