"""The General Ledger batch header `01 WS-Batch-Record`, field for field.

A CREATE from the frozen copybook `copybooks/wsbatch.cob`, which is 55 lines
long and is read as the specification for this module and never modified. One
dataclass per COBOL group, one attribute per elementary item, in the copybook's
own declaration order, with every attribute's storage metadata looked up in the
generated data dictionary rather than typed by eye.

Nothing here decides anything. There is no batch-status predicate, no
control-total comparison, no date conversion and no account scaling below: this
module holds the twenty-three elementary items the copybook declares -
twenty-one of which reach a column - and stops. Where the batch record's own
sources disagree with one another, the disagreement is registered and left
standing.

WHY THIS RECORD MATTERS
=======================
It is the record the whole General Ledger posting cycle turns on. Agent Action
Plan section 0.6.4 sets out an abort chain four links long: a batch left open
sets a status condition; `gl070` detects it [general/gl070.cbl:L314-L315] and
raises the terminate code [general/gl070.cbl:L289]; the menu tests that code
and returns to the menu rather than continuing [general/general.cbl:L800-L814].
The effect is that `gl071` and `gl072` never run at all. The status condition
in link one is `Batch-Status` below, and the value that starts the chain is
zero.

Two of those locators are corrected against the frozen source rather than
taken from the plan, which cites L288 and L312-L313 in sections 0.4.1.2 and
0.6.4. L288 is `perform gl060a` and L312-L313 is the accounting-cycle filter;
the detection is `if status-open / move 1 to a.` at L314-L315 and the raise is
`move 5 to ws-term-code` at L289 - the only line in that program matching
`term-code` at all.

The entity spine, from the generated dictionary rather than restated by hand -
`loader.table_for("GLBATCH-REC")` returns all of it:

    entity facade   GL-Batch
    handler         acas007
    bridge          glbatchMT
    MySQL table     GLBATCH-REC, 21 columns, primary key BATCH-KEY
                    [mysql/ACASDB.sql:L102]
    copybook        copybooks/wsbatch.cob

The consumer's import line is fixed by Agent Action Plan section 0.4.3, and it
is the reason the principal class is named `GlBatchRecord` rather than the
mechanical `WsBatchRecord` that `01  WS-Batch-Record.`
[copybooks/wsbatch.cob:L13] would otherwise give:

    FROM:  copy "wsbatch.cob".
    TO:    from acas_posting.records.gl_batch import GlBatchRecord

ANOMALY A-15 - THE DECLARED LENGTH CONTRADICTION, THIS MODULE'S HEADLINE
========================================================================
This module is the reproducing site for anomaly A-15 of the register in
the migration's anomaly log, described by Agent Action Plan section 0.6.7
entry 15 as "The batch record's declared length contradicts the sum of its
fields". The dictionary agrees: all 28 entries of this record carry the
reference `A-15`. `GlBatchRecord` below points here for the detail, so it is
set out once, in full, at this level.

The contradiction is the maintainer's own, written in his own words in three
consecutive header comments [copybooks/wsbatch.cob:L7-L9], quoted verbatim:

    *> 96 bytes 26/03/09
    *> 98 bytes 20/12/11 (no, dont understand as I count 96)
    *>   but function length (Batch-record) says 98?

It is ALSO an open question for the compiled oracle - one of the five in Agent
Action Plan section 0.6.8, carried by all 28 entries as `Q-4` and to be
written up in the migration's ambiguity-resolutions document. Section 0.6.8
states the stake exactly: "Whether the declared length or the field sum governs
the record actually read affects field alignment for the trailing fields, and
only execution shows which." The trailing items most at risk of misalignment
are therefore the `posting-data` group [copybooks/wsbatch.cob:L47-L53] and
`Batch-Start` [copybooks/wsbatch.cob:L54], because they sit last in the layout
and a two-byte disagreement anywhere ahead of them shifts both.

NOTHING BELOW SETTLES IT. There is no record-length constant, no computed
size, no invented padding item and no widened or narrowed field anywhere in
this module. Rule R-4 makes the defect part of the specification - a defect
reproduced is a success, a defect fixed is a failure - and Agent Action Plan
section 0.4.1.3 is explicit that the contradiction is to be recorded and not
settled. The arbiter is the compiled program, not this file (rule R-6).

For the reader's benefit only, here is what the fields themselves add up to,
each width taken from the dictionary rather than counted by hand. This is a
COUNT of the sum, not a finding about which number is right:

    WS-Batch-Key9   redefines WS-Batch-Key ...........   6  running   6
                    (the redefined group's WS-Ledger 1 plus
                     WS-Batch-Nos 5 cover the very same six bytes)
    Items 2, Batch-Status 1, Cleared-Status 1, Bcycle 2   6  running  12
    Entered, Proofed, Posted, Stored - 4 x binary-long  16  running  28
    Input-Gross .. Actual-Vat - 4 x comp-3, 11 digits   24  running  52
    Description ......................................  24  running  76
    bDefault 2, Convention 2, Batch-Def-AC 6 ..........  10  running  86
    Batch-Def-PC 2, Batch-Def-Code 2, Batch-Def-Vat 1 .   5  running  91
    Batch-Start ......................................   5  running  96

The sum is 96, which is the figure the maintainer says he counts. His note
records a length of 98. The two disagree, and both statements stand;
this module picks neither.

One fact bears directly on that gap and must not be tidied away: the copybook
declares NO FILLER anywhere - `grep -ci filler copybooks/wsbatch.cob` returns
zero, which is unusual in this codebase. The absence is part of the
contradiction. No filler is introduced here to close it.

THE REDEFINITION IS THE ONLY ROUTE TO THE DATABASE
==================================================
`03  WS-Batch-Key9 redefines WS-Batch-Key` is ONE declaration spread over TWO
physical lines, its PICTURE sitting alone on the second
[copybooks/wsbatch.cob:L20-L21] - so a line-by-line reading misses `pic 9(6).`
and types the field wrongly. It is also the ONLY path by which the batch key
reaches `GLBATCH-REC.BATCH-KEY`: the bridge moves the redefinition, not the
group's two elementary children [common/glbatchMT.cbl:L1069], and unloads back
to it [common/glbatchMT.cbl:L1107]. `WS-Ledger` and `WS-Batch-Nos` have no
column of their own at all - a case-insensitive search of the whole bridge for
any of the three names returns only those two lines. `WsBatchKey9` below sets
out the declaration, the move, the resulting name disagreement and why nothing
reconciles the two Python views.

GROUP USAGE IS INHERITED - GET IT WRONG AND EVERY BATCH TOTAL IS WRONG
======================================================================
`03  Amounts  comp-3.` [copybooks/wsbatch.cob:L40] carries the usage clause and
its four children [copybooks/wsbatch.cob:L41-L44] carry none, so all four are
PACKED DECIMAL by inheritance with nothing on their own lines saying so.
Reading usage off the PICTURE line alone would call all four zoned DISPLAY and
every stored batch total would be wrong, invisibly, until a state diff. Usage
comes from the dictionary here for exactly that reason, and each descriptor
carries `usage_declared_at` and `usage_inherited_from` so the inheritance is
visible at the point of use rather than only in `BatchAmounts` below.

THE FOUR DATE ITEMS CARRY NO PICTURE AT ALL
===========================================
`Entered`, `Proofed`, `Posted` and `Stored` are declared `binary-long.` with no
PICTURE clause [copybooks/wsbatch.cob:L36-L39]. They are signed 32-bit
integers holding day numbers, so their Python carrier is `int` and never
`Decimal`. `gl072` stamps `Posted` from the run date as it clears a batch
[general/gl072.cbl:L375-L377].

Being dates, they are the most tempting place in this record to reach for a
clock. There is none, and there must be none (rule R-6): they start at zero and
are set by the posting programs from the run date injected at the command-line
boundary by `acas_posting/clock.py`. Converting a day number to or from text is
`acas_posting/dates.py`'s job, not this module's.

THE THREE LAYERS DISAGREE WIDELY, AND EVERY DISAGREEMENT IS LEFT STANDING
=========================================================================
The dictionary holds the copybook view, the bridge host-variable view and the
MySQL column view side by side, and detects their disagreements by comparing
them rather than from any list of known cases. `DRIFT_REGISTER` below carries
what that comparison finds: 35 entries over 17 of the 23 elementary items, in
four kinds - storage class (all 17), digit count (13), signedness (4) and name
(1) - each surfaced verbatim through
`acas_posting.dictionary.loader.drift_for`, unadjudicated. Two carry
consequences spelled out on the classes that hold the fields:

* SIGNEDNESS on the four date items, in `BatchDates`. Signed in the copybook,
  unsigned in the host variable and unsigned in the column, so a negative day
  number loses its sign AT THE BRIDGE before any SQL executes. This is NOT in
  the Agent Action Plan's register: it is the shape of its entry 11 - "Signed
  value narrowed to an unsigned host variable and an unsigned column, losing
  the sign before SQL executes" - which section 0.6.7 documents only for
  `SALEDGER-REC.SALES-AVERAGE`. It occurs in `GLBATCH-REC` too, and the
  migration's anomaly log should pick this record up as an entry-11-class
  occurrence the plan's own register does not name.
* DIGIT COUNT on the four amounts, in `BatchAmounts`. Unsigned at all three
  layers, so no sign is lost; eleven digits become fourteen at the host
  variable and stay fourteen in the `decimal(14,2)` column.

Elsewhere the host variable is wider than BOTH its neighbours, so the drift is
not even monotonic: `WS-Batch-Key9` goes `9(6)` -> `9(08) COMP` ->
`mediumint(6) unsigned`, and `Batch-Start` goes `9(5)` -> `9(08) COMP` ->
`mediumint(5) unsigned`.

No disagreement is acted on below. A descriptor reports the COPYBOOK view
of its field - that is the COBOL-side storage the arithmetic and MOVE layers
operate on - and never blends layers, never widens a field to a column width
and never applies the bridge's loss of sign. Reproducing the bridge's
conversion belongs to the `acas007` handler module, at the boundary
where it actually happens. There is no winning view, no widest picture and no
sensible reading anywhere in this file, by rule R-4.

Not every field drifts, which is what makes the drift worth registering rather
than assuming: the four alphanumerics - `DESCRIPTION`, `CONVENTION`,
`BATCH-DEF-CODE` and `BATCH-DEF-VAT` - agree across all three layers exactly,
with no disagreement of any kind.

CONDITION NAMES ARE DECLARED HERE, EVALUATED ELSEWHERE
======================================================
The record carries eight `88` condition names over three fields - `WS-Ledger`
[copybooks/wsbatch.cob:L16-L18], `Batch-Status` [copybooks/wsbatch.cob:L26-L27]
and `Cleared-Status` [copybooks/wsbatch.cob:L30-L32] - and each is listed
verbatim with its value and locator on the attribute it belongs to. This
module declares only the STORAGE those names test. The predicates themselves
live in `acas_posting/cobol/condition_names.py`, which Agent Action Plan
section 0.4.1.4 gives "Predicates for the 88-levels the cycle tests: ...
the batch status names ...". No predicate function, no enumerated type and no
named constant for any of the eight appears below, and this module does not
import that sibling: the record layer is a leaf.

WHAT THIS MODULE DELIBERATELY DOES NOT DO (RULE R-3)
====================================================
No control-total check of any kind - the gate belongs to the `gl051` program
module, and `BatchAmounts` below records both that boundary and the order of
operations that makes it matter. No account scaling either: `gl072` and `gl051`
scale account numbers by multiplying and dividing by one hundred
[general/gl072.cbl:L386], [general/gl072.cbl:L413], [general/gl051.cbl:L604],
[general/gl051.cbl:L607], [general/gl051.cbl:L654], [general/gl051.cbl:L657],
[general/gl051.cbl:L803], while `Batch-Def-AC pic 9(6)` below stores what the
copybook declares and is scaled nowhere in this file. And no validation:
nothing below rejects a value, coerces one on assignment or runs after
construction, because the frozen sources have no error path here to reproduce
and inventing one would change behaviour.

LAYERING AND THE BINDING RULES
==============================
A leaf module on the terms `records/__init__.py` sets out for the whole folder
and Agent Action Plan section 0.4.3 fixes: `acas_posting.cobol.field`,
`acas_posting.dictionary.loader` and the standard library, and nothing else.
Section 0.4.3 gives the reason - "this keeps the record layer a leaf" - so that
the arithmetic test tier "imports only cobol and records and touches no
database, so it runs anywhere".

The six binding rules R-1 to R-6 are the Agent Action Plan's own, section
0.7.2, and that is where their full text lives; this project carries no
separate rules document. As they bear on this file: nothing here spawns a
process or reaches for a driver (R-1); the four amounts are `Decimal` at scale
two while the four date items and every scale-zero DISPLAY item are `int`,
which matters most for the two control-total operands (R-2); twenty-three
elementary items in six dataclasses and not one member more (R-3); A-15, the
drift register, the two-line redefinition, the inherited group usage and the
camel-case field name are reproduced with their locators rather than repaired
(R-4); every attribute's metadata comes from the generated dictionary through
keys obtained from the loader (R-5); and declaration order is the copybook's,
fixed collections are tuples, and there is no clock, no entropy source and no
environment read anywhere (R-6).

The maintainer's one-way COBOL-to-MySQL bridge defines the record-layout to
table mapping and is the data dictionary for this migration - which is why the
generator reads `common/glbatchMT.scb` and `common/glbatchMT.cbl` and this
module reads what the generator produced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Ordered the way the sibling modules order theirs, and the way ruff's
    # RUF022 check reads an `__all__`: the module-level constant first, then
    # the class names alphabetically. Reproducible from the names alone, so no
    # reader has to guess a grouping (rule R-6).
    "DRIFT_REGISTER",
    "BatchAmounts",
    "BatchDates",
    "GlBatchRecord",
    "PostingData",
    "WsBatchKey",
    "WsBatchKey9",
)


#  THE FROZEN SOURCES THIS MODULE IS DERIVED FROM

# Named once, used for every lookup below, so that no string literal naming a
# frozen source is repeated and drifts out of step with its neighbours.
_COPYBOOK: Final[str] = "copybooks/wsbatch.cob"
_RECORD: Final[str] = "WS-Batch-Record"
_TABLE: Final[str] = "GLBATCH-REC"


#  DICTIONARY KEYS - OBTAINED FROM THE LOADER, NEVER GUESSED  (RULE R-5)


def _dictionary_keys_by_cobol_name() -> dict[str, str]:
    """Map each COBOL field name of this record to its dictionary key.

    Agent Action Plan section 0.8.1 makes the ordering a directive rather than
    a preference: "The dictionary is generated from the bridge before record
    definitions are written, and every Python field definition cites its
    entry ... it is what prevents fields being transcribed by eye." So the keys
    are asked for, not assembled from a naming rule.

    A key would be easy to guess wrongly, because BOTH halves can differ from
    what a reader expects. The left half is the MySQL TABLE name, not the
    copybook's `01`-level name. The right half is the MySQL COLUMN name, which
    need not match the field: this record's own key is declared as
    `WS-Batch-Key9` in the copybook and as `BATCH-KEY` in both the host
    variable and the column, so the key is `GLBATCH-REC.BATCH-KEY` and a guess
    built from the copybook name would miss it.

    Two passes, because the record has two kinds of item and each needs a
    different source of truth:

    1. `loader.entries_for_table` yields the column-backed entries in column
       ordinal order. There are twenty-one of them, matching the twenty-one
       columns of `GLBATCH-REC`.
    2. `loader.entries_for_copybook_record` yields every entry in copybook
       DECLARATION order, which additionally covers the items that reach no
       column at all: the `01` record itself, the four group headers, and
       `WS-Ledger` and `WS-Batch-Nos`, whose six bytes travel to the database
       only through the `WS-Batch-Key9` redefinition.

    The second pass adds without overwriting, so a column-backed field keeps
    the qualified table key that the first pass gave it.

    Returns:
        COBOL field name, exactly as the frozen copybook spells it, mapped to
        its dictionary key.

    Raises:
        loader.DictionaryLookupError: The table or the record is not in the
            generated dictionary. Allowed to propagate untouched, because its
            message lists near misses and restates the key convention - a
            better report than anything this module could add.
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


# Built once, at class-definition time. The loader reads the generated document
# lazily and caches it, and `FieldDescriptor.from_dictionary_key` memoises on
# the key, so importing this module performs one read of one file and no other
# input or output of any kind (rule R-6).
_KEYS: Final[dict[str, str]] = _dictionary_keys_by_cobol_name()


def _describe(cobol_name: str) -> FieldDescriptor:
    """Return the descriptor the generated dictionary holds for one field.

    The single lookup every attribute below goes through, and nothing in this
    module is assembled by hand: every one of the twenty-eight items this
    record declares has a dictionary entry, the twenty-one column-backed ones
    keyed by table and column and the other seven keyed by copybook record and
    field name.

    Args:
        cobol_name: The COBOL field name as `copybooks/wsbatch.cob` spells it,
            case and hyphens preserved - `"Actual-Vat"`, `"bDefault"`.

    Returns:
        The descriptor for that field, carrying its copybook view of usage,
        digits, scale, signedness and sign position, its Python carrier, its
        dictionary key and its source locator.

    Raises:
        KeyError: No item of this record is spelt so. A programmer error, not a
            data condition: the name is a literal in this file and the record
            is frozen, so it can only fire on a typing mistake here.
    """
    return FieldDescriptor.from_dictionary_key(_KEYS[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return the all-space initial value of an alphanumeric item.

    COBOL fills an alphanumeric item with spaces to its declared width, and the
    bridge does the same before every write: its load paragraph opens with
    `initialize TD-GLBATCH-REC` [common/glbatchMT.cbl:L1068], which is why
    every column of this table can be declared NOT NULL and why an unset field
    must default to spaces rather than be omitted. Agent Action Plan section
    0.6.2 puts it as "unset fields become zero or space rather than SQL NULL".

    The width is not written out here. It comes from the descriptor, which took
    it from the dictionary, so `Description` is 24 wide and `Batch-Def-Vat` is
    1 wide without either number appearing in this file. The value is produced
    by the descriptor's own store, so it is padded by exactly the code path a
    COBOL MOVE into that field would take.

    Args:
        descriptor: The alphanumeric field to produce the initial value for.

    Returns:
        A string of spaces at the field's declared character width.
    """
    return str(descriptor.store(""))


#  03  WS-Batch-Key.                          [copybooks/wsbatch.cob:L14]

_WS_BATCH_KEY: Final[FieldDescriptor] = _describe("WS-Batch-Key")
_WS_LEDGER: Final[FieldDescriptor] = _describe("WS-Ledger")
_WS_BATCH_NOS: Final[FieldDescriptor] = _describe("WS-Batch-Nos")


@dataclass(slots=True)
class WsBatchKey:
    """`03  WS-Batch-Key.` - the batch key as its two parts.

    COBOL identifier, verbatim: `WS-Batch-Key`
    [copybooks/wsbatch.cob:L14].

    A group, so it has no storage of its own: its six bytes are the one byte of
    `WS-Ledger` plus the five of `WS-Batch-Nos`. Neither child reaches the
    database on its own - the whole six bytes travel as one value through the
    `WS-Batch-Key9` redefinition, which is what the bridge moves into
    `HV-BATCH-KEY` [common/glbatchMT.cbl:L1069]. That is why neither child has
    a column and why both are keyed by copybook record rather than by table.

    Not frozen. The posting cycle writes batch keys.
    """

    # The group's own dictionary entry, so that every one of the record's
    # twenty-eight entries has a home in this module (rule R-5). A group has no
    # width of its own; sum its children.
    GROUP: ClassVar[FieldDescriptor] = _WS_BATCH_KEY

    # Declaration order, which for a record is also its byte layout (rule R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_LEDGER,
        _WS_BATCH_NOS,
    )

    # WS-Ledger pic 9 (display, unsigned, scale 0)  [copybooks/wsbatch.cob:L15]
    # Three 88-level condition names, verbatim with their values:
    #     88  GL-Batch  value 1.               [copybooks/wsbatch.cob:L16]
    #     88  PL-Batch  value 2.               [copybooks/wsbatch.cob:L17]
    #     88  SL-Batch  value 3.               [copybooks/wsbatch.cob:L18]
    # The storage is declared here; the predicates that read it belong to
    # acas_posting/cobol/condition_names.py - Agent Action Plan 0.4.1.4.
    ws_ledger: int = 0

    # WS-Batch-Nos pic 9(5) (display, unsigned, scale 0)
    #                                          [copybooks/wsbatch.cob:L19]
    ws_batch_nos: int = 0


#  03  WS-Batch-Key9 redefines WS-Batch-Key   [copybooks/wsbatch.cob:L20-L21]

_WS_BATCH_KEY9: Final[FieldDescriptor] = _describe("WS-Batch-Key9")


@dataclass(slots=True)
class WsBatchKey9:
    """`03  WS-Batch-Key9 redefines WS-Batch-Key` - the same six bytes, as one.

    COBOL identifier, verbatim: `WS-Batch-Key9`
    [copybooks/wsbatch.cob:L20-L21]. The maintainer added it on 09/01/17
    [copybooks/wsbatch.cob:L11].

    ONE declaration over TWO physical lines, with the PICTURE alone on the
    second:

        03  WS-Batch-Key9 redefines WS-Batch-Key
                                pic 9(6).

    Read the copybook a line at a time and `pic 9(6).` is missed and the field
    is typed wrongly - so the two-line form is recorded here rather than left
    to be rediscovered.

    Far from decorative, this redefinition is the ONLY route by which the batch
    key reaches the database. The bridge moves it, not the group's two
    children, into the single host variable for the key
    [common/glbatchMT.cbl:L1069]:

        move     WS-BATCH-KEY9      to HV-BATCH-KEY.

    Hence its dictionary key is `GLBATCH-REC.BATCH-KEY` and the dictionary
    registers a name disagreement across the three views: `WS-Batch-Key9` in
    the copybook, `BATCH-KEY` in the host variable and in the column.

    A COBOL REDEFINES is an alternate reading of storage that is already there,
    so this view and `WsBatchKey` are the same six bytes and cannot disagree.
    Two Python attributes can. Nothing below reconciles them - no property, no
    synchronising write, no derived accessor - because that would be logic the
    copybook does not declare (rule R-3). Keeping the two readings in step
    at the moment a row is written or read is the business of the handler
    module at the bridge boundary, the `acas007` handler module.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_WS_BATCH_KEY9,)

    # WS-Batch-Key9 pic 9(6) (display, unsigned, scale 0), redefining
    # WS-Batch-Key. The descriptor carries redefines="WS-Batch-Key".
    #                                     [copybooks/wsbatch.cob:L20-L21]
    ws_batch_key9: int = 0


#  03  Dates.                                 [copybooks/wsbatch.cob:L35]

_DATES: Final[FieldDescriptor] = _describe("Dates")
_ENTERED: Final[FieldDescriptor] = _describe("Entered")
_PROOFED: Final[FieldDescriptor] = _describe("Proofed")
_POSTED: Final[FieldDescriptor] = _describe("Posted")
_STORED: Final[FieldDescriptor] = _describe("Stored")


@dataclass(slots=True)
class BatchDates:
    """`03  Dates.` - the four day-number stamps of a batch's life.

    COBOL identifier, verbatim: `Dates` [copybooks/wsbatch.cob:L35]. The class
    is named `BatchDates` because a bare `Dates` reads poorly beside the other
    record types in this package and says nothing about what it belongs to; the
    COBOL original is recorded here so the mapping into
    the migration's traceability document stays mechanical.

    All four children are declared `binary-long.` with NO PICTURE CLAUSE AT ALL
    [copybooks/wsbatch.cob:L36-L39]. They are signed 32-bit integers, so their
    carrier is `int`: never `Decimal`, and by rule R-2 never an inexact binary
    carrier. Their values are day numbers, produced by
    `acas_posting/dates.py`'s reimplementation of the date module, whose epoch
    is 1600-12-31 [common/maps04.cbl:L39-L41].

    Being dates, these four are the most tempting place in this record to read
    a clock, and rule R-6 forbids it. They start at zero and are set by the
    posting programs from the run date injected at the command-line boundary by
    `acas_posting/clock.py`. `gl072` stamps `Posted` when it clears a batch
    [general/gl072.cbl:L375-L377].

    A DISAGREEMENT ACROSS THE THREE LAYERS, LEFT STANDING. All four are SIGNED
    in the copybook, UNSIGNED in the bridge host variable
    [common/glbatchMT.cbl:L287-L290] and unsigned in the column, so a negative
    day number loses its sign at the bridge before any SQL executes. This is
    the shape of the Agent Action Plan's register entry 11, which section 0.6.7
    documents only for `SALEDGER-REC.SALES-AVERAGE`; it is not named there for
    this record, and the migration's anomaly log should pick it up.
    `DRIFT_REGISTER` surfaces it verbatim. The descriptors below report the
    copybook view - signed - and the bridge's conversion is reproduced where it
    happens, in the `acas007` handler module.

    Not frozen. `Posted` is written during posting.
    """

    GROUP: ClassVar[FieldDescriptor] = _DATES

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _ENTERED,
        _PROOFED,
        _POSTED,
        _STORED,
    )

    # Entered binary-long, no picture (signed 32-bit, scale 0)
    #                                          [copybooks/wsbatch.cob:L36]
    # Signed here, `PIC 9(10) COMP` unsigned at [common/glbatchMT.cbl:L287],
    # `ENTERED int(8) unsigned` in the column: an entry-11-class disagreement
    # the plan's register does not list. Registered, not acted on.
    entered: int = 0

    # Proofed binary-long, no picture (signed 32-bit, scale 0)
    #                                          [copybooks/wsbatch.cob:L37]
    # Same three-layer disagreement: unsigned at [common/glbatchMT.cbl:L288]
    # and unsigned in column `PROOFED int(8) unsigned`.
    proofed: int = 0

    # Posted binary-long, no picture (signed 32-bit, scale 0)
    #                                          [copybooks/wsbatch.cob:L38]
    # Same three-layer disagreement: unsigned at [common/glbatchMT.cbl:L289]
    # and unsigned in column `POSTED int(8) unsigned`. Stamped by gl072 at
    # [general/gl072.cbl:L375-L377].
    posted: int = 0

    # Stored binary-long, no picture (signed 32-bit, scale 0)
    #                                          [copybooks/wsbatch.cob:L39]
    # Same three-layer disagreement: unsigned at [common/glbatchMT.cbl:L290]
    # and unsigned in column `STORED int(8) unsigned`.
    stored: int = 0


#  03  Amounts                         comp-3. [copybooks/wsbatch.cob:L40]
#  THE GROUP HEADER CARRIES THE USAGE AND ITS FOUR CHILDREN CARRY NONE. All
#  four are packed decimal by inheritance. Typing them from their PICTURE lines
#  alone would make every one of them zoned DISPLAY and every stored batch
#  total wrong - silently, until a state diff. Usage comes from the dictionary.

_AMOUNTS: Final[FieldDescriptor] = _describe("Amounts")
_INPUT_GROSS: Final[FieldDescriptor] = _describe("Input-Gross")
_INPUT_VAT: Final[FieldDescriptor] = _describe("Input-Vat")
_ACTUAL_GROSS: Final[FieldDescriptor] = _describe("Actual-Gross")
_ACTUAL_VAT: Final[FieldDescriptor] = _describe("Actual-Vat")


@dataclass(slots=True)
class BatchAmounts:
    """`03  Amounts ... comp-3.` - the entered and actual totals of a batch.

    COBOL identifier, verbatim: `Amounts` [copybooks/wsbatch.cob:L40]. The
    class is named `BatchAmounts` for the same reason `BatchDates` is not
    `Dates`; the COBOL original is recorded here so the traceability mapping
    stays mechanical.

    THE GROUP HEADER DECLARES THE USAGE. `03  Amounts  comp-3.` at L40 carries
    `comp-3`, and the four children at L41-L44 carry no usage clause of their
    own, so all four INHERIT PACKED DECIMAL from the group. Each descriptor
    reports `usage_declared_at` as the group and `usage_inherited_from` as
    `"Amounts"`, so the inheritance is visible wherever the descriptor is used
    rather than only here.

    All four are UNSIGNED - the picture is `9(9)v99`, not `s9(9)v99` - so in
    this layout a batch's gross and VAT totals cannot go negative. Eleven
    digits, scale two, six bytes packed.

    A DISAGREEMENT ACROSS THE THREE LAYERS, LEFT STANDING. Unsigned at all
    three, so no sign is lost; what changes is width. Eleven digits in the
    copybook, fourteen in the host variable
    [common/glbatchMT.cbl:L291-L294] and fourteen in the
    `decimal(14,2) unsigned` column. The descriptors report the copybook's
    eleven. Nothing here widens a field to a column width, and
    `DRIFT_REGISTER` surfaces the disagreement verbatim.

    NO CONTROL-TOTAL COMPARISON LIVES HERE (rule R-3). `Input-Gross` and
    `Actual-Gross` are its operands, and the gate that compares them - adding
    actual VAT into actual gross BEFORE testing equality against the entered
    gross, because the entered figure is VAT-inclusive
    [general/gl051.cbl:L1109-L1118] - belongs to
    the `gl051` program module. This class stores
    four amounts and compares nothing.

    Not frozen. `Actual-Gross` and `Actual-Vat` are accumulated during the
    proof.
    """

    GROUP: ClassVar[FieldDescriptor] = _AMOUNTS

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _INPUT_GROSS,
        _INPUT_VAT,
        _ACTUAL_GROSS,
        _ACTUAL_VAT,
    )

    # Input-Gross pic 9(9)v99 (comp-3 INHERITED from the Amounts group header
    # at L40; unsigned; 11 digits; scale 2)    [copybooks/wsbatch.cob:L41]
    # 11 digits here, 14 at [common/glbatchMT.cbl:L291] and 14 in column
    # `INPUT-GROSS decimal(14,2) unsigned`. Registered, not acted on.
    # An operand of the control-total comparison, which lives in gl051.
    input_gross: Decimal = Decimal("0.00")

    # Input-Vat pic 9(9)v99 (comp-3 inherited from Amounts; unsigned; 11
    # digits; scale 2)                         [copybooks/wsbatch.cob:L42]
    # 14 digits at [common/glbatchMT.cbl:L292] and in the column.
    input_vat: Decimal = Decimal("0.00")

    # Actual-Gross pic 9(9)v99 (comp-3 inherited from Amounts; unsigned; 11
    # digits; scale 2)                         [copybooks/wsbatch.cob:L43]
    # 14 digits at [common/glbatchMT.cbl:L293] and in the column.
    # The other operand of the control-total comparison.
    actual_gross: Decimal = Decimal("0.00")

    # Actual-Vat pic 9(9)v99 (comp-3 inherited from Amounts; unsigned; 11
    # digits; scale 2)                         [copybooks/wsbatch.cob:L44]
    # 14 digits at [common/glbatchMT.cbl:L294] and in the column. Added into
    # the actual gross before the equality test, in gl051 and not here.
    actual_vat: Decimal = Decimal("0.00")


#  03  posting-data.                          [copybooks/wsbatch.cob:L47]

_POSTING_DATA: Final[FieldDescriptor] = _describe("posting-data")
_B_DEFAULT: Final[FieldDescriptor] = _describe("bDefault")
_CONVENTION: Final[FieldDescriptor] = _describe("Convention")
_BATCH_DEF_AC: Final[FieldDescriptor] = _describe("Batch-Def-AC")
_BATCH_DEF_PC: Final[FieldDescriptor] = _describe("Batch-Def-PC")
_BATCH_DEF_CODE: Final[FieldDescriptor] = _describe("Batch-Def-Code")
_BATCH_DEF_VAT: Final[FieldDescriptor] = _describe("Batch-Def-Vat")


@dataclass(slots=True)
class PostingData:
    """`03  posting-data.` - the per-batch posting defaults.

    COBOL identifier, verbatim: `posting-data`, spelt in lower case where its
    siblings are capitalised [copybooks/wsbatch.cob:L47]. The spelling is left
    as found.

    Six items: a default number, a convention code, a default account and
    profit centre, a default analysis code and a default VAT indicator.

    Not frozen. Batch defaults are amended by the data-entry programs, which
    are out of scope but write this same record.
    """

    GROUP: ClassVar[FieldDescriptor] = _POSTING_DATA

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _B_DEFAULT,
        _CONVENTION,
        _BATCH_DEF_AC,
        _BATCH_DEF_PC,
        _BATCH_DEF_CODE,
        _BATCH_DEF_VAT,
    )

    # bDefault pic 99 (display, unsigned, scale 0)
    #                                          [copybooks/wsbatch.cob:L48]
    # The COBOL name is camel case - `bDefault`, verbatim - which is unique in
    # this record and unusual in the codebase. The attribute is the mechanical
    # snake case of it, `b_default`, so that every attribute in this package
    # follows one naming rule; the descriptor's `name` carries `bDefault`
    # exactly as the frozen copybook spells it, so traceability is unaffected.
    b_default: int = 0

    # Convention pic xx (alphanumeric, 2 characters)
    #                                          [copybooks/wsbatch.cob:L49]
    convention: str = _spaces(_CONVENTION)

    # Batch-Def-AC pic 9(6) (display, unsigned, scale 0)
    #                                          [copybooks/wsbatch.cob:L50]
    # gl072 and gl051 scale account numbers by multiplying and dividing by one
    # hundred [general/gl072.cbl:L386], [general/gl072.cbl:L413],
    # [general/gl051.cbl:L604], [general/gl051.cbl:L607],
    # [general/gl051.cbl:L654], [general/gl051.cbl:L657],
    # [general/gl051.cbl:L803]. NO SCALING HAPPENS HERE. This attribute holds
    # the six digits the copybook declares, unscaled either way.
    batch_def_ac: int = 0

    # Batch-Def-PC pic 99 (display, unsigned, scale 0)
    #                                          [copybooks/wsbatch.cob:L51]
    batch_def_pc: int = 0

    # Batch-Def-Code pic xx (alphanumeric, 2 characters)
    #                                          [copybooks/wsbatch.cob:L52]
    batch_def_code: str = _spaces(_BATCH_DEF_CODE)

    # Batch-Def-Vat pic x (alphanumeric, 1 character)
    #                                          [copybooks/wsbatch.cob:L53]
    batch_def_vat: str = _spaces(_BATCH_DEF_VAT)


#  01  WS-Batch-Record.                       [copybooks/wsbatch.cob:L13]

_WS_BATCH_RECORD: Final[FieldDescriptor] = _describe("WS-Batch-Record")
_ITEMS: Final[FieldDescriptor] = _describe("Items")
_BATCH_STATUS: Final[FieldDescriptor] = _describe("Batch-Status")
_CLEARED_STATUS: Final[FieldDescriptor] = _describe("Cleared-Status")
_BCYCLE: Final[FieldDescriptor] = _describe("Bcycle")
_DESCRIPTION: Final[FieldDescriptor] = _describe("Description")
_BATCH_START: Final[FieldDescriptor] = _describe("Batch-Start")


@dataclass(slots=True)
class GlBatchRecord:
    """`01  WS-Batch-Record.` - one General Ledger batch header.

    COBOL identifier, verbatim: `WS-Batch-Record`
    [copybooks/wsbatch.cob:L13]. The class name departs from the mechanical
    PascalCase of that identifier, which would be `WsBatchRecord`, because
    Agent Action Plan section 0.4.3 fixes the consumer's import line:

        from acas_posting.records.gl_batch import GlBatchRecord

    The record the whole General Ledger posting cycle turns on. It reaches
    the database as `GLBATCH-REC` through the GL-Batch facade, handler
    `acas007` and bridge `glbatchMT`, and the call the posting programs make
    is [general/gl072.cbl and its siblings]:

        call "acas007" using System-Record WS-Batch-Record File-Access
                             File-Defs ACAS-DAL-Common-Data

    Members follow the copybook's declaration order, L14 through L54, which for
    a record is also its byte layout (rule R-6). Set this class beside
    `copybooks/wsbatch.cob` and the two diff by eye.

    Deliberately NOT frozen. The posting cycle writes this record: `gl051`'s
    control-total gate sets `Batch-Status`, and `gl072` stamps `Cleared-Status`
    and `Posted` when it clears a batch [general/gl072.cbl:L375-L377].

    THIS MODULE IS THE REPRODUCING SITE FOR ANOMALY A-15, the declared-length
    contradiction the maintainer records in his own words
    [copybooks/wsbatch.cob:L7-L9] and which the dictionary references from
    every entry of this record. It is also open question Q-4 for the
    compiled oracle. Nothing here settles either; see this module's docstring
    for both, for the counted field-byte sum, and for the trailing items a
    misalignment would move.
    """

    # The 01-level record's own dictionary entry. A group, so no width of its
    # own - see the module docstring for what its children add up to and why
    # that sum is a count rather than a finding.
    GROUP: ClassVar[FieldDescriptor] = _WS_BATCH_RECORD

    # The elementary items declared directly at this level, in declaration
    # order. The items inside WS-Batch-Key, Dates, Amounts and posting-data are
    # published by those four classes' own FIELDS.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _ITEMS,
        _BATCH_STATUS,
        _CLEARED_STATUS,
        _BCYCLE,
        _DESCRIPTION,
        _BATCH_START,
    )

    # 03  WS-Batch-Key. - group of WS-Ledger + WS-Batch-Nos
    #                                          [copybooks/wsbatch.cob:L14]
    ws_batch_key: WsBatchKey = field(default_factory=WsBatchKey)

    # 03  WS-Batch-Key9 redefines WS-Batch-Key - THE SAME SIX BYTES read as one
    # 6-digit value, and the only route by which the key reaches the database
    # [common/glbatchMT.cbl:L1069]. Held as its own member because the copybook
    # declares it as its own item; nothing here keeps the two readings in step,
    # which is the handler module's business (rule R-3).
    #                                     [copybooks/wsbatch.cob:L20-L21]
    ws_batch_key9: WsBatchKey9 = field(default_factory=WsBatchKey9)

    # Items pic 99 (display, unsigned, scale 0) [copybooks/wsbatch.cob:L23]
    items: int = 0

    # Batch-Status  pic 9   DISPLAY, unsigned, scale 0   [copybooks/wsbatch.cob:L25]
    #     88  Status-Open    value 0.                    [copybooks/wsbatch.cob:L26]
    #     88  Status-Closed  value 1.                    [copybooks/wsbatch.cob:L27]
    # `Status-Open` - the value ZERO - is link one of the four-link abort chain in Agent Action
    # Plan section 0.6.4. An open batch is detected at [general/gl070.cbl:L314-L315], which
    # raises the terminate code at [general/gl070.cbl:L289]; the menu tests it and returns
    # [general/general.cbl:L800-L814], so gl071 and gl072 never run at all.
    # Declared here and tested nowhere in this module: the predicates belong to
    # acas_posting/cobol/condition_names.py.
    batch_status: int = 0

    # Cleared-Status pic 9 (display, unsigned, scale 0)
    #                                          [copybooks/wsbatch.cob:L29]
    # Three 88-level condition names, verbatim with their values:
    #     88  Waiting    value 0.              [copybooks/wsbatch.cob:L30]
    #     88  Processed  value 1.              [copybooks/wsbatch.cob:L31]
    #     88  Archived   value 2.              [copybooks/wsbatch.cob:L32]
    # Stamped by gl072 at [general/gl072.cbl:L375-L377]. Predicates live in
    # acas_posting/cobol/condition_names.py.
    cleared_status: int = 0

    # Bcycle pic 99 (display, unsigned, scale 0)
    #                                          [copybooks/wsbatch.cob:L34]
    # The accounting cycle. gl070 filters both of its passes over the batch
    # file on this field [general/gl070.cbl:L312-L313] and
    # [general/gl070.cbl:L457-L458]; the filtering is gl070's, not this
    # module's.
    bcycle: int = 0

    # 03  Dates. - group of Entered, Proofed, Posted, Stored
    #                                          [copybooks/wsbatch.cob:L35]
    dates: BatchDates = field(default_factory=BatchDates)

    # 03  Amounts ... comp-3. - group of Input-Gross, Input-Vat, Actual-Gross,
    # Actual-Vat, all four packed decimal by inheritance from the group header
    #                                          [copybooks/wsbatch.cob:L40]
    amounts: BatchAmounts = field(default_factory=BatchAmounts)

    # Description pic x(24) (alphanumeric, 24 characters)
    #                                          [copybooks/wsbatch.cob:L45]
    # The one field of this record that agrees across all three layers with no
    # disagreement of any kind - which is what makes the disagreements
    # elsewhere worth registering rather than assuming.
    description: str = _spaces(_DESCRIPTION)

    # 03  posting-data. - group of bDefault, Convention, Batch-Def-AC,
    # Batch-Def-PC, Batch-Def-Code, Batch-Def-Vat
    #                                          [copybooks/wsbatch.cob:L47]
    # One of the two trailing items a length misalignment would move (A-15).
    posting_data: PostingData = field(default_factory=PostingData)

    # Batch-Start pic 9(5) (display, unsigned, scale 0)
    #                                          [copybooks/wsbatch.cob:L54]
    # The last item in the layout, and the other trailing item most at risk if
    # the declared length rather than the field sum governs the record actually
    # read - open question Q-4, arbitrated by the compiled program (rule R-6).
    batch_start: int = 0


#  THE THREE-LAYER DISAGREEMENTS, REGISTERED AND LEFT STANDING  (RULE R-4)


def _drift_register() -> tuple[str, ...]:
    """Collect this record's three-layer disagreements as they stand.

    A pass-through of `acas_posting.dictionary.loader.drift_for` over every
    item of the record in copybook declaration order. Each line names the
    COBOL field, its dictionary key and one disagreement, in the dictionary's
    own words.

    Nothing is reduced to a flag, summarised as safe, averaged or decided.
    Rule R-4 makes a legacy defect part of the specification, so the three
    views are registered side by side and the disagreement stays open. The
    two that matter for this record are described in full in the module
    docstring: signedness on the four date items, and digit count on the four
    amounts.

    Derived by walking the record rather than from a list of known cases, which
    is the same discipline the dictionary generator applies - a hand-written
    list is exactly what would have missed the signedness narrowing in this
    record, since the Agent Action Plan names it only for the sales record.

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


#: Every three-layer disagreement this record carries, in the dictionary's own
#: words and in copybook declaration order. Published so that a reader of the
#: record layer sees the disagreements without having to query the dictionary,
#: and so that the migration's anomaly log can cite this module for the
#: entry-11-class signedness narrowing that the Agent Action Plan's register
#: does not list. A tuple, so it cannot be edited in place and its order is
#: fixed (rule R-6).
DRIFT_REGISTER: Final[tuple[str, ...]] = _drift_register()
