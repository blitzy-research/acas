r"""The system final-accounts record: `01 Final-Record.` [copybooks/wsfinal.cob:L10].

Twelve lines of frozen copybook, two of which are the whole record - a table of
26 sixteen-character slots and a 608-character FILLER. This module is their
Python mirror and holds nothing besides: no accessor, no per-slot name, no
parser, no computed size member and no key member. The copybook is the smallest
in the migration, and its smallness is not a licence to add convenience.

    01  Final-Record.                                                     L10
        03  ar1             pic x(16)      occurs  26.                    L11
        03  filler          pic x(608).  *> size now 1024 as used in sys002
                                                                          L12

THE ENTITY-TO-TABLE SPINE
-------------------------
From the Agent Action Plan's section 0.2.1.1 spine, every element below read
back out of the generated dictionary rather than taken on trust:

    entity facade   System final
    handler         acas000, at FILE-KEY NUMBER 3. Section 0.2.1.1 notes that
                    `acas000` is "a four-way dispatcher keyed by file-key
                    number rather than a single-table handler": one program
                    serves the system record at key 1, its defaults at key 2,
                    THIS record at key 3 and the system totals at key 4.
    bridge          finalMT  [common/finalMT.cbl]
    table           SYSFINAL-REC, 2 columns, primary key FINAL-ACC-REC-KEY
                    [mysql/ACASDB.sql:L1163-L1167]
    copybook        copybooks/wsfinal.cob

Section 0.6.6 records that this table carries no secondary index, no timestamp
column, no auto-increment column and no column-level default - which is what
lets a state dump of it be reproducible from a plain ordered select, and is why
the scenario diff needs no tie-breaking logic for it.

THE SIZE CONTRADICTION - RECORDED HERE, SETTLED ELSEWHERE (R-4, R-6)
--------------------------------------------------------------------
The copybook's own header states the contradiction, verbatim
[copybooks/wsfinal.cob:L6]:

    416 bytes 02/03/09 but written as 1024 (system-record size) 07/11/10

and [copybooks/wsfinal.cob:L8]:

    included filler 15/10/25 now = 1024 as created by sys002

The arithmetic is shown at each member below: 26 slots x 16 characters = 416
data bytes, and 416 + 608 filler characters = 1024. So the 608-byte FILLER is
precisely what makes the written size 1024 while the record's data occupies
416. That is the same CLASS of contradiction as the batch record's declared
length against the sum of its fields, which section 0.6.8 lists as an OPEN
question for the compiled oracle:

    "Whether the declared length or the field sum governs the record actually
    read affects field alignment for the trailing fields, and only execution
    shows which."

This module's obligation is therefore to RECORD the contradiction, not to
settle it. No side is taken here: the FILLER is kept as a member, and no
computed length is published. The arbitration belongs to the comparison oracle
and is written down in `docs/migration/ambiguity-resolutions.md` (R-6).

`sys002` is named only because the header names it. `common/sys002.cbl` is out
of scope per section 0.2.2, nothing here calls it, and no COBOL program is
executed, embedded or shelled out to from this package at all (R-1).

`01 Final-Record.` IS DECLARED TWICE IN THE FROZEN TREE (R-4)
-------------------------------------------------------------
The same COBOL `01`-name, and the same field name `ar1`, mean two materially
different things in two subsystems:

    copybooks/wsfinal.cob      L10  01  Final-Record.
                               L11      03  ar1  pic x(16)  occurs 26.
                               L12      03  filler  pic x(608).
                               ...12 lines in total, no other member.

    copybooks/irswsfinal.cob   L7   01  Final-Record.
                               L9-L34   26 individually named 05 items,
                                        each pic x(24)
                               L35-L36  a redefining `ar1 pic x(24) occurs 26`
                               L65-L66  a redefining one-character table,
                                        occurs 26
                               L68      a pic x(5) trailer
                               ...69 lines in total.

The two extra items of the IRS layout are identified above by picture and
locator rather than by name, deliberately: a grep for their names must find
nothing in this file, and that check is the mechanical proof that this module
declares neither of them. The IRS layout belongs to
`acas_posting/records/irs_final.py` as `IrsFinalRecord`, keyed in the
dictionary against IRSFINAL-REC, and the two modules are never merged, never
aliased to one another and never widened towards each other. `ar1` here is 16
characters and stays 16 characters.

Hence the class name. `SysFinalRecord` carries a `Sys` prefix rather than
mirroring the bare COBOL identifier, because two modules of one Python package
cannot both publish `FinalRecord` without one hiding the other in a reader's
mind - which is the same hazard the COBOL meets and answers with qualified
references. This is anomaly-#21-class evidence: field-name collisions across
posting copybooks force qualified references in the COBOL [general/gl070.cbl].
Python's module namespace answers it for free, but the collision is still
RECORDED here so that a reader understands why the COBOL qualifies at all.

The dictionary makes the hazard measurable rather than theoretical. Asking it
for the copybook record `Final-Record` returns 63 entries spanning BOTH files,
and the copybook-keyed entries stay distinct only because the key carries the
declaration line: `Final-Record.filler#12` is this file's FILLER while
`Final-Record.filler#35` and `Final-Record.filler#65` are the IRS layout's two
redefining groups. Every lookup below therefore pins
`copybooks/wsfinal.cob` explicitly and never keys by field name alone.

HOW THE BRIDGE CARRIES 26 SLOTS INTO A 2-COLUMN TABLE
-----------------------------------------------------
A 26-element table against a 2-column table looks like a mismatch and is not.
The bridge transposes: one ROW PER OCCURRENCE, keyed by the subscript
[common/finalMT.cbl:L608-L616], which loads its host variables by inline moves
because `finalMT` has NO `bb000-HV-Load` paragraph - one of the four bridges
that work that way, and a fact both dictionary entries carry as a note. Read
back, `HV-AR1` returns to `AR1 (HV-FINAL-ACC-REC-KEY)` under the maintainer's
own comment `KEY = table position` [common/finalMT.cbl:L588], guarded by a
subscript range test [common/finalMT.cbl:L560].

Three consequences are recorded rather than compensated for:

  * FINAL-ACC-REC-KEY IS THE 1-BASED OCCURS SUBSCRIPT, stored in the database
    as 1 through 26. The COBOL-1-based against Python-0-based offset is
    therefore visible in the primary key itself: `ar1[0]` here is
    FINAL-ACC-REC-KEY = 1 there. No 1-based wrapper is built below. Hiding the
    offset would be added machinery (R-3) and would hide the one place the DAL
    must apply it deliberately.
  * The column has no copybook counterpart at all: the dictionary reports it
    absent from every copybook and derived at the bridge by
    `move A to HV-FINAL-ACC-REC-KEY` [common/finalMT.cbl:L613]. So no member
    for it is declared here, exactly as the three bridge-derived IRS posting
    date components are owned by `dal/acasirsub4_irs_posting.py` rather than by
    a record module. This one belongs to `dal/acas000_system.py`.
  * A slot holding spaces is SKIPPED, under the maintainer's own comment
    `dont write out blank data` [common/finalMT.cbl:L609], so the table may
    hold fewer than 26 rows for a record that has 26 slots. That asymmetry is
    the bridge's behaviour to reproduce at the bridge boundary, not something
    for this module to even out.

Of the table's 2 columns, exactly ONE is backed by a copybook field, so this
module publishes exactly ONE column-mapped descriptor - `SYSFINAL-REC.AR1`
against the char(16) column - plus one copybook-only descriptor for the FILLER,
which reaches no host variable and no column whatsoever. No member is added or
dropped to make the two counts agree.

THE FILLER IS A MEMBER, AND THAT IS A DECISION
-----------------------------------------------
The FILLER is modelled as a NAMED ATTRIBUTE carrying its own descriptor, rather
than as a descriptor alone with no attribute. Both were open; this one was
taken for two reasons. First, the FILLER is the entire substance of the
416-against-1024 contradiction, and a record that did not carry it would have
quietly disposed of an anomaly that R-4 requires be reproduced. Second, it is
the record's trailing 608 characters, so a reader setting this file beside its
copybook sees the same two members in the same order and can diff them by eye.
Its descriptor still reports `is_filler` as true, because that is what the
copybook declares and the dictionary holds.

DESCRIPTORS ARE LOOKED UP, NEVER TRANSCRIBED (R-5)
--------------------------------------------------
Not one picture clause, digit count, scale, sign position, storage class,
character width or occurrence count is typed by hand below. Each is obtained
from the generated data dictionary, which is built from the maintainer's
one-way COBOL-to-MySQL bridge - the mapping that governs this migration, and in
the user's own preserved words "it is the data dictionary for this migration".
Section 0.8.1 makes the ordering binding rather than stylistic: the dictionary
is generated from the bridge BEFORE record definitions are written, and every
Python field definition cites its entry, which "is what prevents fields being
transcribed by eye".

Two keys back this record, and both are looked up rather than spelled:

    SYSFINAL-REC.AR1        found by asking the dictionary for the entries of
                            table SYSFINAL-REC and reading each entry's
                            copybook field name - the table name on the left
                            of the key is exactly what keeps SYSFINAL-REC and
                            IRSFINAL-REC from merging
    Final-Record.filler#12  found by asking the dictionary for the entries
                            declared in copybooks/wsfinal.cob and matching the
                            declaration line, because no column backs a FILLER
                            and the record-name form of the key repeats across
                            the two Final-Record copybooks

`FieldDescriptor.from_dictionary_key` is the principal constructor and the one
used here; it refuses to build a descriptor with no provenance at all, so the
traceability claim is enforced at construction rather than asserted in a
comment. `loader.cite(key)` renders the compact three-locator provenance
string, surfaced through each descriptor's own `cite()` and never
reimplemented. The whole mapping is recorded in
`docs/migration/traceability.md`.

Where the copybook, the bridge host variable and the column disagree, the
dictionary keeps all three views side by side plus an unsettled `drift` object,
and the disagreement stays unsettled. For this record it reports no drift at
all: 16 characters at every layer. There is no winner view here, and no
vocabulary of the kind `acas_posting/records/__init__.py` bans is used anywhere
below - which is also why several Agent Action Plan sentences are paraphrased
rather than quoted, since their wording includes words this package refuses to
carry in source.

LAYERING, TYPES AND DETERMINISM
-------------------------------
This module is a LEAF. Section 0.4.3 grants `records/*.py` exactly two internal
imports - `acas_posting.cobol.field` and `acas_posting.dictionary.loader` - and
forbids everything else, including any other module of this package, and
including `records/irs_final.py` despite the shared COBOL name. The promise
that depends on it: the arithmetic test tier "imports only `cobol` and
`records` and touches no database, so it runs anywhere".

The record is ENTIRELY alphanumeric - 26 slots of `pic x(16)` and one
`pic x(608)`. It declares no numeric member of any kind, so no numeric carrier
is imported and no character is ever read as a number. "Final accounts" sounds
numeric; the copybook says characters, and adding an interpretation the
copybook does not declare is forbidden outright (R-2, R-3). Binary floating
point appears nowhere in this package, ever.

Construction is deterministic: the 26 slots are built in index order, fixed
collections are tuples, member order is declaration order, and nothing here
consults a clock, draws an unpredictable value, inspects the process
environment or walks the file system. The only read at import is the loader's
own lazily cached read of the generated dictionary.

This project carries no separate user rules document - `review_rules` reports
that none was provided - so the rule identifiers R-1 through R-6 cited above
are the Agent Action Plan's own, section 0.7.2, and the plan is where their
full text lives. Where the plan is silent, enterprise-standard practice
applies; no rule has been invented to fill a gap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# Only the record type is published for import. `FIELDS`, `COPYBOOK` and
# `TABLE` below carry no leading underscore and are readable by anything that
# wants them, but they are kept out of `__all__` deliberately: the layering
# contract of section 0.4.3 has a consumer import ONE symbol out of ONE module,
# as a single line reading
# `from acas_posting.records.system_final import SysFinalRecord`.
__all__: list[str] = ["SysFinalRecord"]


# =============================================================================
#  THE FROZEN SOURCES THIS MODULE MIRRORS
# =============================================================================

#: The copybook this module is a CREATE from. Every lookup below pins it,
#: because `01 Final-Record.` is declared twice in the frozen tree - here and
#: in `copybooks/irswsfinal.cob` - and a lookup that did not pin the file could
#: land in the other one.
COPYBOOK: Final[str] = "copybooks/wsfinal.cob"

#: The MySQL table the bridge `finalMT` writes this record to, through handler
#: `acas000` at file-key number 3. Named because the left half of a
#: column-mapped dictionary key is the table name, and that is what keeps this
#: record and the IRS final-accounts record from merging.
TABLE: Final[str] = "SYSFINAL-REC"

#: The FILLER's declaration line, verbatim from the copybook
#: [copybooks/wsfinal.cob:L12]. Needed because no column backs a FILLER, so its
#: dictionary key takes the copybook-record form - and that form repeats across
#: the two `Final-Record` copybooks, which between them declare three FILLERs.
#: The declaration line is what tells them apart.
#:
#: `ar1` needs no such constant: its key is found through the table, and its
#: locator then arrives from the dictionary as the descriptor's own
#: `source_locator`.
_FILLER_DECLARED_AT: Final[str] = "copybooks/wsfinal.cob:L12"


# =============================================================================
#  FINDING THE TWO DICTIONARY KEYS, AND THE SHAPE THEY CARRY
#  (R-5 - looked up, never guessed)
# =============================================================================
#
# All three helpers below fail loudly when the dictionary does not hold what
# this module needs, and none substitutes a default. That is not added
# validation of record data - no accounting value is examined and nothing is
# rejected - but the mechanism by which "derived, not transcribed" is kept
# honest: a key that cannot be found is a broken artifact, and a broken
# artifact must not be papered over with a guess. Two of them find a key; the
# third takes a count the dictionary holds. `loader.DictionaryLookupError` is
# the loader's own failure type for "no such thing in the dictionary", so a
# failure here reads the same as any other dictionary miss.


def _column_backed_key(*, copybook_field: str) -> str:
    """Find the `TABLE` entry key whose copybook field is `copybook_field`.

    The path section 3.3 of this file's brief prescribes: ask the dictionary for
    the entries of table SYSFINAL-REC and read each entry's copybook field
    name. Two filters matter and both are deliberate. The copybook FILE is
    pinned, which is what proves the right side of the `Final-Record` collision
    was taken. And entries with no copybook view are skipped, because
    FINAL-ACC-REC-KEY is exactly such an entry - the bridge derives it and no
    copybook declares it, so it has no COBOL-side storage for a descriptor to
    describe.

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

    For a field no column backs, whose key therefore takes the
    `<COPYBOOK-RECORD>.<FIELD-NAME>` form. That form alone is ambiguous for this
    record: asking the dictionary for the copybook record `Final-Record` returns
    63 entries spanning two files, three of them named `filler`. Matching on the
    declaration LINE inside one pinned copybook file is unambiguous, and it is
    the same fact the dictionary itself uses to keep the keys distinct.

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
    dictionary's to state, not this module's. This narrows the optional count
    the dictionary carries without ever substituting a fallback, because a
    silent zero here would build an empty table and a silent width would build
    slots of the wrong size.

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


# =============================================================================
#  THE TWO DESCRIPTORS, IN COPYBOOK DECLARATION ORDER
# =============================================================================

#: `03  ar1  pic x(16)  occurs 26.` [copybooks/wsfinal.cob:L11], backed by the
#: char(16) column AR1 [mysql/ACASDB.sql:L1165] through the host variable HV-AR1
#: [common/finalMT.cbl:L315]. The dictionary reports no drift across the three
#: layers: 16 characters at every one of them.
_AR1_KEY: Final[str] = _column_backed_key(copybook_field="ar1")

#: `03  filler  pic x(608).` [copybooks/wsfinal.cob:L12]. Reaches NO host
#: variable and NO column - its citation renders both as absent - which is the
#: substance of the 416-against-1024 contradiction the header records.
_FILLER_KEY: Final[str] = _copybook_only_key(declared_at=_FILLER_DECLARED_AT)

_AR1: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(_AR1_KEY)
_FILLER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(_FILLER_KEY)

#: The record's fields in copybook declaration order, one descriptor per
#: dataclass member. A tuple, because the order is part of the record's byte
#: layout and nothing may re-sort it (R-6).
#:
#: Two descriptors against the table's 2 columns is a coincidence of counts, not
#: a correspondence: only `ar1` is column-mapped, the FILLER is copybook-only,
#: and the second column FINAL-ACC-REC-KEY is bridge-derived with no copybook
#: field at all. Each descriptor answers `cite()` with its own three-locator
#: provenance string, and `drift()` with the dictionary's unsettled view of any
#: disagreement between the layers.
FIELDS: Final[tuple[FieldDescriptor, ...]] = (_AR1, _FILLER)


# =============================================================================
#  THE UNSET STATE, DERIVED FROM THE DESCRIPTORS
# =============================================================================
#
# Sizes come from the dictionary, never from this file. The arithmetic the
# copybook header turns on:
#
#     _AR1_OCCURS x _AR1_WIDTH  =  26 x 16   =  416 data bytes
#     416 + _FILLER_WIDTH       =  416 + 608 = 1024 bytes as written
#
# which is exactly the contradiction stated at [copybooks/wsfinal.cob:L6] -
# "416 bytes 02/03/09 but written as 1024" - and it is recorded, not settled.

_AR1_OCCURS: Final[int] = _from_dictionary(
    _AR1.occurs, key=_AR1_KEY, member="OCCURS count"
)
_AR1_WIDTH: Final[int] = _from_dictionary(
    _AR1.character_length, key=_AR1_KEY, member="character length"
)
_FILLER_WIDTH: Final[int] = _from_dictionary(
    _FILLER.character_length, key=_FILLER_KEY, member="character length"
)

#: Every slot of an unset table, built in index order. Spaces rather than the
#: empty string, for two reasons drawn from the frozen source rather than from
#: taste: a `pic x(n)` item is n characters wide by declaration and is never
#: narrower, and the bridge itself tests `if AR1 (A) = spaces` before deciding
#: whether a slot is worth a row [common/finalMT.cbl:L609] - so spaces is the
#: frozen code's own reading of "nothing here". Padding a value INTO a slot is
#: `acas_posting/cobol/move.py`'s business and appears nowhere here.
#:
#: Shared safely between instances: a tuple of `str` is immutable through and
#: through, so no instance can alter another's default.
_AR1_UNSET: Final[tuple[str, ...]] = tuple(" " * _AR1_WIDTH for _ in range(_AR1_OCCURS))

#: The FILLER's 608 unset characters [copybooks/wsfinal.cob:L12].
_FILLER_UNSET: Final[str] = " " * _FILLER_WIDTH


# =============================================================================
#  THE RECORD
# =============================================================================


@dataclass(slots=True)
class SysFinalRecord:
    """`01 Final-Record.` of `copybooks/wsfinal.cob` [copybooks/wsfinal.cob:L10].

    The system final-accounts record: entity facade System final, handler
    `acas000` at file-key number 3, bridge `finalMT`, table SYSFINAL-REC.

    WHY THE CLASS NAME IS PREFIXED. The COBOL identifier is `Final-Record`,
    verbatim [copybooks/wsfinal.cob:L10] - and `copybooks/irswsfinal.cob`
    declares an `01 Final-Record.` of its own [copybooks/irswsfinal.cob:L7],
    with its own `ar1` at `pic x(24) occurs 26`
    [copybooks/irswsfinal.cob:L35-L36] plus two further items this record does
    not have [copybooks/irswsfinal.cob:L65-L66, L68]. The two are materially
    different records that share a name, so the bare mirror `FinalRecord` would
    read as though either file could be meant. `SysFinalRecord` is this one;
    `IrsFinalRecord` in `acas_posting/records/irs_final.py` is that one; neither
    imports the other and neither is widened towards the other.

    NOT FROZEN. The final-accounts layout is read and written by the
    maintenance programs, so instances are mutable. Assigning to `ar1` replaces
    the whole table, since a tuple is immutable by design (R-6); a program
    changing one slot rebuilds the tuple at its own call site, and no helper for
    doing so is published here (R-3).

    MEMBERS, in copybook declaration order, which is the record's byte layout:

        ar1     the 26-slot table, 16 characters each   L11
        filler  the trailing 608 characters             L12

    Nothing else. There is no member for FINAL-ACC-REC-KEY: no copybook
    declares that column, the bridge derives it from the OCCURS subscript
    [common/finalMT.cbl:L613], and reproducing that derivation belongs to
    `acas_posting/dal/acas000_system.py` at the bridge boundary.
    """

    # ar1  pic x(16)  occurs 26      [copybooks/wsfinal.cob:L11]
    #   26 slots x 16 characters = 416 data bytes. Sixteen-character slots with
    #   no per-slot names: the copybook gives the individual entries no
    #   semantics whatever, and none is invented here (R-3, R-4).
    #
    #   COBOL `OCCURS` SUBSCRIPTS ARE 1-BASED; PYTHON INDICES ARE 0-BASED. The
    #   offset is a whole position: `ar1 (1)` in COBOL is `ar1[0]` here, and
    #   `ar1 (26)` is `ar1[25]`. It is not merely a language nicety either - the
    #   bridge stores that very subscript as the table's primary key, one row per
    #   occurrence [common/finalMT.cbl:L608-L616], reading it back with the
    #   maintainer's own comment `KEY = table position`
    #   [common/finalMT.cbl:L588]. So `ar1[0]` here is FINAL-ACC-REC-KEY = 1
    #   there. No 1-based accessor is provided: the offset is applied
    #   deliberately at the bridge boundary and hiding it here would be added
    #   machinery (R-3).
    ar1: tuple[str, ...] = field(default_factory=lambda: _AR1_UNSET)

    # filler  pic x(608)             [copybooks/wsfinal.cob:L12]
    #   The copybook's own inline note reads "size now 1024 as used in sys002",
    #   and 416 + 608 = 1024. Kept as a member precisely because it is the
    #   substance of the header's declared-against-written contradiction
    #   [copybooks/wsfinal.cob:L6]; dropping it would quietly dispose of an
    #   anomaly that must be reproduced (R-4). It reaches no host variable and
    #   no column, so nothing about it appears in a table dump.
    filler: str = _FILLER_UNSET
