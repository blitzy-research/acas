"""The two General Ledger work files, as ordered in-process sequences.

`pretrans.tmp` and `postrans.tmp` [copybooks/wsnames.cob:L14-L17] carry the
General Ledger transaction stream between the cycle's phases: gl070 writes the
pre-transaction stream, gl071 sorts it, gl072 consumes the sorted stream. This
module models the two files, the sort work description between them, and the
COBOL file verbs those phases use; the record layouts belong to
`acas_posting.records.work_records` and the key comparison to
`acas_posting.cobol.sortverb`.

Neither file is part of the schema, so nothing here reaches the database and
nothing here appears in a table dump.

The ordering is a correctness requirement, not a convenience: gl072 locates the
nominal-ledger account for each posting with a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so it finds the right account only
because the stream arrives in nominal-key order. A perturbed order misposts
silently - no error, no diagnostic, wrong balances.

     13  01  File-Defs.
     14      02  file-defs-a.
     15          03  pre-trans-name  pic x(532)  value "pretrans.tmp". *> gl071
     16          03  post-trans-name pic x(532)  value "postrans.tmp". *> gl071

Of the fifty-seven file-name entries reachable from that copybook, only these
two carry a `*> gl071` annotation, and it names the sort phase. Agent Action
Plan section 0.4.1.6 cites the span as L14-L17; the frozen file puts it at
L13-L16, and the frozen file is the authority. The sort work description is
assigned by number - `select sort-trans assign file-21.`
[general/gl071.cbl:L102] - and `file-21` is declared in a one-line copybook as
`pic x(532) value "work.tmp"` [copybooks/file21.cob:L1].

`gl071` IS 182 LINES AND IS A PURE SORT
Its whole procedure division is `main.` [general/gl071.cbl:L167], one screen
message [general/gl071.cbl:L170], the `SORT` statement
[general/gl071.cbl:L172-L178], then `main-exit.` [general/gl071.cbl:L180] and
`goback.` [general/gl071.cbl:L181]. ZERO arithmetic statements, ZERO `MOVE`
statements and ZERO `GO TO` statements - so the four-class `GO TO` taxonomy of
Agent Action Plan section 0.4.2 has nothing to classify here. Of the three file
descriptions [general/gl071.cbl:L92-L102], `pre-trans` and `post-trans` are
`fd`s declaring `access sequential`, `status fs-reply` and `organization line
sequential`; `sort-trans` is an `sd` declaring none of the three. One class
models all three, because the layouts are identical and the verbs are the same.

THE WORK-RECORD LAYOUT  [general/gl071.cbl:L112-L144]
Eight fields, seventy characters, declared once per file description and byte
for byte the same each time. `acas_posting.records.work_records` OWNS the
layout; the widths here are prose so a reader need not open another file.

    offset  field       picture         width
     1      -batch      pic 9(5)          5
     6      -post       pic 9(5)          5
    11      -code       pic xx            2
    13      -date       pic x(8)          8   DD/MM/YY - EIGHT characters
    21      -ac         pic 9(6)          6
    27      -pc         pic 99            2
    29      -amount     pic s9(8)v99     10   signed, sign trailing included
    39      -legend     pic x(32)        32   -> 70 characters in total

`-date` is EIGHT characters, not the ten-character `DD/MM/CCYY` of `to-day`
[general/gl071.cbl:L159], which never reaches a work record; the eight come from
`Post-Date pic x(8)` by an eight-to-eight move [general/gl070.cbl:L498], so rule
R-4 means this module widens, reformats and validates nothing about it.
`-amount` is zoned display, signed, scale 2, the sign overpunching the last
digit, carried as `decimal.Decimal` and never as a binary approximation (rule
R-2); most records are NEGATIVE, because every credit leg is negated by
`multiply pre-amount by -1 giving pre-amount` [general/gl070.cbl:L517], as is a
tax leg on the credit side [general/gl070.cbl:L530]. The other numeric fields
are unsigned display integers carried as `int`, `-code` and `-legend` are `str`,
and this module performs NO arithmetic on any of them - its one numeric
operation advances the current-record pointer by one position.

THE THREE-PHASE CHAIN, AND WHO OWNS WHICH VERB
    PRODUCER   `gl070` phase 2, section `gl071b`, writes `pre-trans`:
               `open output pre-trans.` [general/gl070.cbl:L447], three
               `write pre-trans-record.` per entered posting - a debit leg, a
               credit leg, and a tax leg written only when both the tax account
               and the tax amount are non-zero [general/gl070.cbl:L495-L533] -
               then `close pre-trans.` [general/gl070.cbl:L472]
    SORTER     `gl071` sorts `pre-trans` into `post-trans` and declares NO
               `open` and NO `close` of either: the `SORT` performs both
               implicitly [general/gl071.cbl:L172-L178]
    CONSUMER   `gl072` phase 4 only READS `post-trans`:
               `open input post-trans.` [general/gl072.cbl:L278],
               `read post-trans at end` [general/gl072.cbl:L286-L289],
               `close post-trans` [general/gl072.cbl:L440]

The verbs published below are exactly those and no others: `OPEN OUTPUT`,
`OPEN INPUT`, `WRITE`, `READ ... AT END`, `CLOSE` and `SORT ... USING ...
GIVING`. No `open i-o`, `rewrite`, `delete`, `start` or `open extend`, because
no phase of this cycle uses one on a work file.

THE ORDERING CONTRACT - THE MOST IMPORTANT PARAGRAPH IN THIS FILE
"""

from __future__ import annotations

import copy
import enum
import logging
from collections.abc import Sequence
from dataclasses import Field, dataclass, field, fields
from typing import Any, Final, Generic, TypeVar

from acas_posting.cobol.sortverb import SortDirection, SortKey, sort_records
from acas_posting.records.work_records import (
    COBOL_FIELD_METADATA_KEY,
    PostTransRecord,
    PreTransRecord,
    SortTransRecord,
)

# The complete public surface. Sorted, and a tuple rather than a list, matching the
# convention of every sibling module.
__all__: Final[tuple[str, ...]] = (
    "FS_REPLY_AT_END",
    "FS_REPLY_OK",
    "FS_REPLY_OPEN_NOT_FOUND",
    "FS_REPLY_READ_NOT_READABLE",
    "FS_REPLY_WRITE_NOT_OPEN",
    "OPEN_ITEM_2_NAME",
    "OPEN_ITEM_4_NAME",
    "POST_TRANS_NAME",
    "PRE_TRANS_NAME",
    "SORTING_DIAGNOSTIC",
    "SORT_TRANS_ASCENDING_KEYS",
    "SORT_TRANS_NAME",
    "GeneralLedgerWorkFiles",
    "LineSequentialWorkFile",
    "OpenItemWorkFile",
    "OpenMode",
    "WorkFileError",
    "general_ledger_work_files",
    "open_item_work_file",
    "sort_using_giving",
)

#: The record a work file carries.
RecordT = TypeVar("RecordT")

#: The module's logger. `logging`, never a print: a diagnostic must be suppressible,
#: routable and absent from every table dump, and a print is none of those.
logger: Final[logging.Logger] = logging.getLogger(__name__)


FS_REPLY_OK: Final[int] = 0

#: `fs-reply` after a `READ` that found no further record - the `AT END` condition
#: [copybooks/wsfnctn.cob:L25].
FS_REPLY_AT_END: Final[int] = 10

#: `fs-reply` after a `READ` issued when the file was ALREADY at its end - a READ
#: ATTEMPTED ON A FILE NOT IN A READABLE STATE.
FS_REPLY_READ_NOT_READABLE: Final[int] = 46

#: `fs-reply` after an `OPEN` of a file that does not exist, where the `SELECT`
#: did NOT say `OPTIONAL`.
#:
#: WHY THIS VALUE IS LOAD-BEARING RATHER THAN INCIDENTAL. Neither open-item
#: `SELECT` says `OPTIONAL` - `select open-item-file-2 assign file-18 access
#: sequential status fs-reply.` [copybooks/seloi2.cob] and its OTM4 twin
#: [copybooks/seloi4.cob:L1-L4] - so an `OPEN EXTEND` of a file that has never
#: been created REPORTS rather than creates, and the producer's very next
#: statement tests for exactly that: `if fs-reply not = zero / close / open
#: output` [sales/sl055.cbl:L360-L362], [purchase/pl055.cbl:L302-L304]. That is
#: the ordinary first-run path, not an error path, and the maintainer says so in
#: his own words at [purchase/pl055.cbl:L48] - *"On open extend otm4 if error
#: open as output as bug in OC."* A carrier whose `open_extend` always succeeded
#: would make the fallback unreachable and silently drop two statements.
FS_REPLY_OPEN_NOT_FOUND: Final[int] = 35

#: `fs-reply` after a `WRITE` issued while the file is not open for writing.
#: Reported rather than raised, because the compiled program reports and RUNS ON
#: - the producers test the field [sales/sl055.cbl:L682],
#: [purchase/pl055.cbl:L588] rather than being aborted by the runtime. Raising
#: here would invent a control-flow path the frozen program does not have
#: (rules R-3, R-4).
FS_REPLY_WRITE_NOT_OPEN: Final[int] = 48


# THE THREE WORK-FILE IDENTITIES [copybooks/wsnames.cob:L13-L16] These are IDENTITIES,
# not locations: a name by which a sequence identifies itself in a log line or a failure
# message.

PRE_TRANS_NAME: Final[str] = "pretrans.tmp"

POST_TRANS_NAME: Final[str] = "postrans.tmp"

#: `file-21` [copybooks/file21.cob:L1] - the sort work description's assigned name,
#: `select sort-trans assign file-21.` [general/gl071.cbl:L102].
SORT_TRANS_NAME: Final[str] = "work.tmp"

#  THE TWO OPEN-ITEM WORK-FILE IDENTITIES  [copybooks/wsnames.cob:L35, :L45]

#: `file-18` [copybooks/file18.cob] - the OTM2 extract `sl055` writes
#: [sales/sl055.cbl:L681] and `sl060` reads [sales/sl060.cbl:L484]. The names
#: copybook annotates the entry `*> "openitm2"` [copybooks/wsnames.cob:L35], and
#: `sl055`'s own remark calls it "OTM2. TEMP (Only) Open Item File 2 -
#: Preposting." [sales/sl055.cbl:L40] - the same species as the two General
#: Ledger work files above, which is why it belongs in this module. Its record
#: area is `01 open-item-record-2 pic x(118)` [copybooks/fdoi2.cob:L11].
#:
#: THE VALUE IS THE ASSIGNED NAME, NOT A FILENAME. It keys the carrier the
#: producer and the consumer share; nothing here resolves it against a
#: filesystem, because the sequence stores records rather than bytes.
OPEN_ITEM_2_NAME: Final[str] = "openitm2"

#: `file-28` [copybooks/file28.cob] - the OTM4 extract `pl055` writes
#: [purchase/pl055.cbl:L587] and `pl060` reads [purchase/pl060.cbl:L425].
#: Annotated `*> "openitm4"` [copybooks/wsnames.cob:L45], and `pl055` annotates
#: its own SELECT `*> Temp file only for i/p to pl060.`
#: [purchase/pl055.cbl:L109].
#:
#: ⭐ ITS RECORD AREA IS 113 BYTES, NOT 118. `01 open-item-record-4 pic x(113)`
#: [copybooks/fdoi4.cob:L10] against the sales file's `pic x(118)`
#: [copybooks/fdoi2.cob:L11], even though both hold an open-item header and the
#: purchase copybook's own comment says the width was set "to match invoice
#: record". The five-byte divergence is the frozen declaration's and is recorded
#: rather than harmonised (rule R-4). Nothing here depends on either width: a
#: sequence stores records, not bytes, and neither file reaches a schema table,
#: so neither width is observable in a table dump.
OPEN_ITEM_4_NAME: Final[str] = "openitm4"


# THE ONE SCREEN STATEMENT, AS A LOG RECORD [general/gl071.cbl:L170] `gl071` contains
# exactly one screen statement, verbatim: 170 display "Sorting.......Please wait " at
# 0801 with foreground-color 2.

#: The progress notice `gl071` displays before sorting [general/gl071.cbl:L170], carried
#: as text so it can be logged rather than drawn.
SORTING_DIAGNOSTIC: Final[str] = "Sorting.......Please wait"


class OpenMode(enum.StrEnum):
    """Which `OPEN` a work file is under, or none.

    The three states the cycle's verbs move a work file between. A `StrEnum`,
    matching the enumerations `acas_posting.dictionary.model` and
    `acas_posting.cobol.sortverb` publish, so a mode renders as its own name in
    a log line or a failure message without a conversion step.

    There is deliberately no `I-O`: no work file in the migrated cycle is opened
    that way, and a member for a mode the compiled cycle never uses would be a
    behaviour with no evidence behind it (rule R-6).

    `EXTEND` IS A MEMBER BECAUSE THE SALES AND PURCHASE CYCLES USE IT, even
    though the General Ledger cycle does not. `gl070` opens `pre-trans` for
    output [general/gl070.cbl:L447], `gl072` opens `post-trans` for input
    [general/gl072.cbl:L278] and `gl071` opens neither explicitly at all - which
    is why this enumeration once carried only three members. The open-item work
    files are opened a fourth way: `open extend open-item-file-2`
    [sales/sl055.cbl:L359] and `open extend open-item-file-4`
    [purchase/pl055.cbl:L301]. See `OpenItemWorkFile`.
    """

    CLOSED = "CLOSED"
    """Not open. The state a sequence starts in and the state `close` returns it to. A work
    file's CONTENTS survive this state - see `LineSequentialWorkFile.close` for why that
    is required rather than convenient.
    """

    INPUT = "INPUT"
    """`OPEN INPUT` - open for reading, positioned at the first record.
    [general/gl072.cbl:L278], [sales/sl060.cbl:L480],
    [purchase/pl060.cbl:L421]."""

    OUTPUT = "OUTPUT"
    """`OPEN OUTPUT` - open for writing, and the previous contents discarded.
    [general/gl070.cbl:L447], [sales/sl055.cbl:L362],
    [sales/sl060.cbl:L677]."""

    EXTEND = "EXTEND"
    """`OPEN EXTEND` - open for writing with the existing records PRESERVED and
    the write position after the last one. [sales/sl055.cbl:L359],
    [purchase/pl055.cbl:L301]. The mode that made both producers declare a
    module-private work file of their own before `OpenItemWorkFile` existed.

    ⭐ THE MODE THAT DISTINGUISHES THE TWO EXTRACT FILES FROM THE GENERAL LEDGER
    WORK FILES, and the reason it is not interchangeable with OUTPUT: OUTPUT
    truncates and EXTEND appends. Both extract programs try EXTEND FIRST and
    fall back to OUTPUT only when it fails [sales/sl055.cbl:L359-L362],
    [purchase/pl055.cbl:L301-L304], so on any run where the file already exists
    the extract is APPENDED to what is there. Collapsing the two modes would
    silently discard a previous extract that the frozen cycle preserves."""


#  FAILURE


class WorkFileError(RuntimeError):
    """A work-file verb was used in a state that cannot carry it out.

    Every use of this error reports a PROGRAMMER error - a `write` to a sequence that is
    not open for output, a `read_next` from one that is not open for input, a group move
    between record layouts of different shapes.
    """


def _record_area_snapshot(record: RecordT) -> RecordT:
    """Take the VALUE of a record area, the way a COBOL `WRITE` does.

    Three postings reach the file, each holding the values the area held at the instant
    of its own `WRITE`.

    Args:
        record: The record area to take the value of.

    Returns:
        An independent record carrying the same field values.
    """
    return copy.deepcopy(record)


class LineSequentialWorkFile(Generic[RecordT]):
    """One `organization line sequential` work file, as an ordered sequence.

    Models a single file description of the General Ledger cycle's work files:
    a name, the `01` record layout it carries, the records themselves in the
    order they were written, one forward-only current record pointer, and the
    `fs-reply` status of the last verb issued. ONE class serves all
    three descriptions, because the frozen source declares three with identical
    layouts [general/gl071.cbl:L112-L144] and the phases use the same verbs on
    each - a second class would be a second truth for one declaration.

    The three descriptions it models [general/gl071.cbl:L92-L102]:

         92      select  pre-trans  assign  pre-trans-name,
         93                         access  sequential
         94                         status  fs-reply
         95                         organization  line sequential.
         97      select  post-trans assign  post-trans-name,
         98                         access  sequential
         99                         status  fs-reply
        100                         organization  line sequential.
        102      select  sort-trans  assign file-21.

    `access sequential` is why there is one forward-only pointer and no
    positioning verb; `status fs-reply` is why `fs_reply` is published; and
    `organization line sequential` is why `open_output` discards what was there
    before. The `sd` at L102 declares none of the three and is modelled with the
    same class, its layout [general/gl071.cbl:L136-L144] being field-identical.

    IN MEMORY, NEVER ON DISK. Agent Action Plan section 0.3.1: these are
    "in-process sequences, not tables and not temporary files". No instance of
    this class touches a filesystem or a database, holds a descriptor or a
    handle, or leaves anything behind when the process ends.

    ORDER IS THE WHOLE POINT. Records are held in a list and appended to; they
    are read back by advancing an integer. Nothing sorts, groups,
    de-duplicates, hashes or re-associates them, and no unordered container
    appears anywhere in this class. Agent Action Plan section 0.6.4: "Any
    change in sort stability or key composition produces silent misposting - no
    error, no diagnostic, wrong balances" - the read itself being the guarded
    `perform GL-Nominal-Read-Next` at [general/gl072.cbl:L407-L408], which the
    plan cites as [general/gl072.cbl:L410-L412]. A reordering introduced here
    would be exactly as silent.

    THE RECORD AREA IS CROSSED BY VALUE, IN BOTH DIRECTIONS. A COBOL `WRITE`
    moves the record area's current bytes into the file and a `READ` fills the
    area from the file, so neither verb leaves the program and the file sharing
    storage. Every crossing here is therefore a copy - `write` stores the value
    the record carried at the instant of the verb, `read_next` hands back an
    independent record, and `records` yields copies - which is what lets a
    caller reuse ONE record object across successive writes exactly as `gl070`
    reuses one `pre-trans-record` area for the debit, credit and
    value-added-tax legs of a posting [general/gl070.cbl:L495-L532].
    `_record_area_snapshot` carries the mechanism and the proof.

    NO KEYED ACCESS (Agent Action Plan section 0.8.4). There is no `find`, no
    index, no key-to-record mapping and no search. `records` exposes the stored
    order for inspection and for the ordering assertions the verification suite
    makes; walking it is a sequential walk, which is what the compiled program
    does.

    NOT THREAD-SAFE, AND DELIBERATELY SO (rule R-3). Execution is strictly
    sequential, matching the single-threaded COBOL, so there is no guard of any
    kind around the pointer or the record list. A guard would imply a
    concurrency this migration does not have.

    Typical use - the exact `gl070` to `gl071` to `gl072` handoff:

        pre_trans = LineSequentialWorkFile(PRE_TRANS_NAME, PreTransRecord)
        pre_trans.open_output()                 # [general/gl070.cbl:L447]
        pre_trans.write(leg)                    # [general/gl070.cbl:L508]
        pre_trans.close()                       # [general/gl070.cbl:L472]

        pre_trans.open_input()                  # [general/gl072.cbl:L278]
        record = pre_trans.read_next()          # [general/gl072.cbl:L286]
        if pre_trans.fs_reply == FS_REPLY_AT_END:
            ...
        pre_trans.close()                       # [general/gl072.cbl:L440]

    Attributes:
        name: The identity the frozen copybook gives this file - one of
            `PRE_TRANS_NAME`, `POST_TRANS_NAME` or `SORT_TRANS_NAME`. Text, and never
            resolved against a filesystem.
        record_type: The `01` record layout this file carries, as declared in
            `acas_posting.records.work_records`.
        open_mode: Which `OPEN` the file is under, or `OpenMode.CLOSED`.
        fs_reply: The `fs-reply` status of the last verb issued
            [copybooks/wsfnctn.cob:L25].
        at_end: Whether the last `read_next` met the `AT END` condition.
        records: Copies of the stored records, in stored order.
    """

    __slots__ = (
        "_fs_reply",
        "_name",
        "_next_record_pointer",
        "_open_mode",
        "_record_type",
        "_records",
    )

    def __init__(self, name: str, record_type: type[RecordT]) -> None:
        """Declare one work file. The equivalent of its FILE-CONTROL entry.

        Args:
            name: The identity the frozen copybook gives this file. Carried as given;
                never resolved, joined or otherwise treated as a location.
            record_type: The record layout this file carries - one of `PreTransRecord`,
                `SortTransRecord` or `PostTransRecord`.
        """
        self._name: str = name
        self._record_type: type[RecordT] = record_type
        # A list, because appending to it is the WRITE verb and its order is the record
        # order.
        self._records: list[RecordT] = []
        # COBOL's own term for this is the CURRENT RECORD POINTER: the position a
        # sequential READ will take its record from.
        self._next_record_pointer: int = 0
        self._fs_reply: int = FS_REPLY_OK
        self._open_mode: OpenMode = OpenMode.CLOSED


    @property
    def name(self) -> str:
        """The identity the frozen copybook gives this file.

        [copybooks/wsnames.cob:L15] for `pretrans.tmp`, [copybooks/wsnames.cob:L16] for
        `postrans.tmp`, and [copybooks/file21.cob:L1] for the sort description's
        `work.tmp`. Text for a log line or a failure message, never a location.
        """
        return self._name

    @property
    def record_type(self) -> type[RecordT]:
        """The `01` record layout this file carries."""
        return self._record_type

    @property
    def open_mode(self) -> OpenMode:
        """Which `OPEN` this file is under, or `OpenMode.CLOSED`."""
        return self._open_mode

    @property
    def fs_reply(self) -> int:
        """The `fs-reply` status of the last verb issued.

        A THIRD VALUE IS REACHABLE, and it was measured rather than assumed:
        `FS_REPLY_READ_NOT_READABLE` after a `read_next` issued once the at-end
        condition has already been reported. See `read_next` for the reading and
        `FS_REPLY_READ_NOT_READABLE` for the experiment.
        """
        return self._fs_reply

    @property
    def at_end(self) -> bool:
        """Whether the last `read_next` met the `AT END` condition.

        The `AT END` phrase of `read post-trans at end` [general/gl072.cbl:L286],
        expressed as a predicate so a caller may use either spelling the frozen source
        uses: this, or the explicit `fs_reply == FS_REPLY_AT_END` comparison `gl070`
        writes [general/gl070.cbl:L454], [general/gl070.cbl:L487].
        """
        return self._fs_reply == FS_REPLY_AT_END

    @property
    def records(self) -> tuple[RecordT, ...]:
        """The stored records, in stored order.

        A snapshot for inspection - the ordering assertions the verification suite makes
        read it, and `sort_using_giving` hands it to the sort. A `tuple` and not the
        underlying list, so the stored ORDER cannot be edited behind the verbs' back.
        """
        return tuple(_record_area_snapshot(record) for record in self._records)

    def __len__(self) -> int:
        """How many records the file holds."""
        return len(self._records)

    def __repr__(self) -> str:
        """A diagnostic form: the file, its layout, its mode and its size.

        Built entirely from this instance's own state, so it is stable between runs
        (rule R-6): no address, no identity value and nothing ambient.
        """
        return (
            f"{type(self).__name__}({self._name!r},"
            f" {self._record_type.__name__},"
            f" {self._open_mode}, {len(self._records)} record(s),"
            f" pointer {self._next_record_pointer})"
        )


    def open_output(self) -> None:
        """`OPEN OUTPUT` - open for writing, discarding what was there before.

        Reproduces `open output pre-trans.` [general/gl070.cbl:L447], the verb with
        which phase 2 begins writing the exploded transaction stream, and the implicit
        open the `SORT` verb performs on its `GIVING` file [general/gl071.cbl:L178].
        """
        self._records.clear()
        self._next_record_pointer = 0
        self._open_mode = OpenMode.OUTPUT
        self._fs_reply = FS_REPLY_OK

    def open_input(self) -> None:
        """`OPEN INPUT` - open for reading, positioned at the first record.

        Reproduces `open input post-trans.` [general/gl072.cbl:L278], the verb with
        which phase 4 begins walking the sorted stream, and the implicit open the `SORT`
        verb performs on its `USING` file [general/gl071.cbl:L177].
        """
        self._next_record_pointer = 0
        self._open_mode = OpenMode.INPUT
        self._fs_reply = FS_REPLY_OK

    def write(self, record: RecordT) -> None:
        """`WRITE` - append one record, preserving insertion order absolutely.

        Reproduces the three `write pre-trans-record.` statements of the double-entry
        explosion [general/gl070.cbl:L495-L533] - the debit leg at
        [general/gl070.cbl:L508], the credit leg at [general/gl070.cbl:L519] and the
        value-added-tax leg at [general/gl070.cbl:L532] - and the implicit write the
        `SORT` verb performs into its `GIVING` file [general/gl071.cbl:L178].

        Args:
            record: The record area whose current value to append.

        Raises:
            WorkFileError: The file is not open for output. A PROGRAMMER error, never a
                judgement on the record: see `WorkFileError`.
        """
        if self._open_mode is not OpenMode.OUTPUT:
            raise WorkFileError(
                "WRITE requires the work file to be open for output - `open"
                " output pre-trans.` [general/gl070.cbl:L447] - and "
                + self._name
                + " is "
                + str(self._open_mode)
                + ". Nothing was written."
            )
        self._records.append(_record_area_snapshot(record))
        self._fs_reply = FS_REPLY_OK

    def read_next(self) -> RecordT | None:
        """`READ ... AT END` - the next record in stored order, or the at-end.

        Reproduces `read post-trans at end ...` [general/gl072.cbl:L286], the verb with
        which phase 4 walks the sorted stream, and the implicit read the `SORT` verb
        performs over its `USING` file [general/gl071.cbl:L177].

        Returns:
            The next record, or `None` when there is none left.

        Raises:
            WorkFileError: The file is not open for input. A PROGRAMMER error; see
                `WorkFileError`.
        """
        if self._open_mode is not OpenMode.INPUT:
            raise WorkFileError(
                "READ requires the work file to be open for input - `open"
                " input post-trans.` [general/gl072.cbl:L278] - and "
                + self._name
                + " is "
                + str(self._open_mode)
                + ". No record was read."
            )
        if self._next_record_pointer >= len(self._records):
            self._fs_reply = (
                FS_REPLY_READ_NOT_READABLE
                if self._fs_reply in (
                    FS_REPLY_AT_END, FS_REPLY_READ_NOT_READABLE
                )
                else FS_REPLY_AT_END
            )
            return None
        record = self._records[self._next_record_pointer]
        self._next_record_pointer += 1
        self._fs_reply = FS_REPLY_OK
        return _record_area_snapshot(record)

    def close(self) -> None:
        """`CLOSE` - release the file, and KEEP its records.

        Reproduces `close pre-trans.` [general/gl070.cbl:L472] and `close post-trans
        print-file.` [general/gl072.cbl:L440], and the implicit closes the `SORT` verb
        performs on its `USING` and `GIVING` files [general/gl071.cbl:L177-L178].
        """
        self._next_record_pointer = 0
        self._open_mode = OpenMode.CLOSED
        self._fs_reply = FS_REPLY_OK


#  THE OPEN-ITEM WORK FILE  -  ONE CARRIER, TWO PROGRAMS, FOUR CALL SITES
#
# ⭐⭐ WHY THIS CLASS EXISTS AT ALL. The open-item work file is the CHANNEL
# between a producer and a consumer, and a channel that is not one object is not
# a channel. `sl055` opens `open-item-file-2` for EXTEND [sales/sl055.cbl:L359],
# writes a header per invoice [sales/sl055.cbl:L681] and closes it
# [sales/sl055.cbl:L501]; `sl060` then opens THE SAME FILE for INPUT
# [sales/sl060.cbl:L480], reads those headers [sales/sl060.cbl:L484], closes it
# [sales/sl060.cbl:L613] and finally truncates it once the transfer to OTM3 is
# complete [sales/sl060.cbl:L677-L678]. `pl055` and `pl060` do the same over
# `open-item-file-4` [purchase/pl055.cbl:L301, :L587, :L423] and
# [purchase/pl060.cbl:L421, :L425, :L548, :L605-L606].
#
# In COBOL the two programs name the same `assign` and the operating system
# supplies the identity. In Python the identity has to be an OBJECT that outlives
# each `CALL`, exactly as `GeneralLedgerWorkFiles` is for the three General
# Ledger phases - and for the same reason, stated in that class's own docstring.
#
# WHAT THIS REPLACES. Both producers previously declared a module-private work
# file, and each said in its own docstring that it had to, because
# `LineSequentialWorkFile` published no `EXTEND` and its only writable mode
# truncated. That reasoning was correct about the class as it stood and wrong
# about the conclusion: the answer is to publish the mode here, once, rather than
# to declare the file twice and leave the consumers reading a different object
# from the one the producers wrote. `OpenMode.EXTEND` and
# `FS_REPLY_OPEN_NOT_FOUND` above are that mode and its status.
#
# ⛔ AND NOT A MODULE-LEVEL REGISTRY. Both consumers previously reached a
# sequence through a dict keyed by the assigned name at module scope, which made
# the extract reachable but shared it across every run in one interpreter. Rule
# R-6 requires two runs of the same scenario under the same pinned clock to be
# byte-identical, and a sequence carrying the previous run's invoices breaks that
# without anything failing. `open_item_work_file` below caches nothing.
#
# THE STATUS FIELD IS ONE FIELD, DELIBERATELY. Both `SELECT`s name
# `status fs-reply` [copybooks/seloi2.cob], [copybooks/seloi4.cob:L4], and
# `03 Fs-Reply pic 99.` [copybooks/wsfnctn.cob:L25] is the very field every
# facade verb writes. Every verb below therefore takes an OPTIONAL `file_access`
# and writes it when given one, and also keeps the value readable as `fs_reply` -
# so a program that tests `state.file_access.fs_reply` straight after a native
# `OPEN` and one that reads `ws.otm4.fs_reply` are looking at the same value
# through the two spellings the four programs actually use.


@dataclass
class OpenItemWorkFile(Generic[RecordT]):
    """`open-item-file-2` / `open-item-file-4` - the open-item extract channel.

    THE FILE, NOT THE RECORD. The record layouts are `01 OI-Header.`
    [copybooks/slwsoi.cob:L8] for the sales side and its purchase twin
    [copybooks/plwsoi.cob:L9], which `acas_posting.records.otm3` and
    `acas_posting.records.otm5` already publish in full with every leaf and its
    dictionary key. Nothing about either layout is declared here; the class is
    generic over the record type and inspects nothing about it, so the record
    layer stays the single authority for field metadata (rule R-5).

    THE FILE DECLARATIONS, VERBATIM

        select  open-item-file-2  assign        file-18
                                  access        sequential
                                  status        fs-reply.        [copybooks/seloi2.cob]
        fd  open-item-file-2.
        01  open-item-record-2  pic x(118).                       [copybooks/fdoi2.cob]

        select  open-item-file-4  assign        file-28
                                  access        sequential
                                  status        fs-reply.  [copybooks/seloi4.cob:L1-L4]
        fd  open-item-file-4.
        01  open-item-record-4  pic x(113).      [copybooks/fdoi4.cob:L1-L2]

    Each producer adds the OI-Header description as a SECOND `01` under the same
    FD - `copy "slwsoi.cob"` [sales/sl055.cbl:L145] and `copy "plwsoi.cob"`
    [purchase/pl055.cbl:L121] - which is why `write oi-header.`
    [sales/sl055.cbl:L681] and `write open-item-record-4.`
    [purchase/pl055.cbl:L587] both write the OI-Header layout into that one
    record area. A second `01` under an FD is an alternative description of the
    same bytes, not a second buffer.

    NEITHER `SELECT` SAYS `OPTIONAL`, which is what makes the producers' fallback
    a normal path rather than an error path - see `FS_REPLY_OPEN_NOT_FOUND`.

    A TRANSIENT WORK FILE, NOT A TABLE. `copy "seloi4.cob"` carries its author's
    own note, *"Temp file only for i/p to pl060."* [purchase/pl055.cbl:L109].
    Neither file reaches a schema table and neither appears in any table dump, so
    the Agent Action Plan models them the way it models the General Ledger work
    files (section 0.3.1): an ordered sequence with the same record layout and
    the same ordering guarantee, and nothing else.

    ⛔ NO VERB RAISES ON A STATUS. Every verb reports through `fs-reply` and
    returns, because that is what the compiled program does - the producers test
    the field after the `OPEN` and after the `WRITE` rather than being aborted by
    the runtime. Raising would invent a control-flow path the frozen source does
    not have (rules R-3, R-4).

    Attributes:
        name: The assigned name, `OPEN_ITEM_2_NAME` or `OPEN_ITEM_4_NAME`, or
            whatever `file-18` / `file-28` resolves to in the caller's
            `File-Defs`. Carried for diagnostics; nothing keys off it.
        record_type: The record description the sequence carries. Preserved so a
            caller reads back the class it wrote.
    """

    name: str
    record_type: type[RecordT]
    #: Whether the file exists on the notional filesystem. False until an
    #: `OPEN OUTPUT` creates it, which is what makes the first `OPEN EXTEND`
    #: report `FS_REPLY_OPEN_NOT_FOUND` and drives the producers' fallback.
    exists: bool = False
    _records: list[RecordT] = field(default_factory=list)
    _open_mode: OpenMode = OpenMode.CLOSED
    _next_record_pointer: int = 0
    _fs_reply: int = FS_REPLY_OK

    #  ---- readable state -------------------------------------------------

    @property
    def fs_reply(self) -> int:
        """`fs-reply` after the most recent verb [copybooks/wsfnctn.cob:L25].

        Readable here as well as writable into a caller's `FileAccess`, because
        the four programs spell the same field two ways: `pl060` reads
        `ws.otm4.fs_reply` and copies it across, while `sl055` hands its own
        `FileAccess` to every verb. One field, two spellings.
        """
        return self._fs_reply

    @property
    def open_mode(self) -> OpenMode:
        """Which `OPEN` the file is under, or `OpenMode.CLOSED`."""
        return self._open_mode

    @property
    def at_end(self) -> bool:
        """Whether a further `READ` would raise the `AT END` condition."""
        return self._next_record_pointer >= len(self._records)

    @property
    def records(self) -> tuple[RecordT, ...]:
        """The sequence as written, in insertion order.

        A sequential file has no other order, and the consumer reads them back
        in exactly this one [sales/sl060.cbl:L484],
        [purchase/pl060.cbl:L425].
        """
        return tuple(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        return (
            f"OpenItemWorkFile(name={self.name!r}, "
            f"record_type={self.record_type.__name__}, "
            f"mode={self._open_mode.value}, records={len(self._records)}, "
            f"exists={self.exists})"
        )

    #  ---- the verbs ------------------------------------------------------

    def _report(self, status: int, file_access: Any | None) -> None:
        """Write `fs-reply` here and, when given one, into the caller's field."""
        self._fs_reply = status
        if file_access is not None:
            file_access.fs_reply = status

    def open_extend(self, file_access: Any | None = None) -> None:
        """`open extend`  [sales/sl055.cbl:L359], [purchase/pl055.cbl:L301].

        Append: the existing records survive and the write position is the end.
        Succeeds only if the file EXISTS, because neither `SELECT` is `OPTIONAL`;
        otherwise it reports `FS_REPLY_OPEN_NOT_FOUND` and leaves the file
        closed, which is what the producer's next statement tests for.
        """
        if not self.exists:
            self._open_mode = OpenMode.CLOSED
            self._report(FS_REPLY_OPEN_NOT_FOUND, file_access)
            return
        self._open_mode = OpenMode.EXTEND
        self._next_record_pointer = len(self._records)
        self._report(FS_REPLY_OK, file_access)

    def open_output(self, file_access: Any | None = None) -> None:
        """`open output`  [sales/sl055.cbl:L362], [sales/sl060.cbl:L677].

        CREATES OR TRUNCATES, which is what `OPEN OUTPUT` on a sequential file
        means. It is both the producers' create-on-first-run fallback and the
        consumers' clear-down once the transfer to OTM3 / OTM5 is complete
        [sales/sl060.cbl:L677], [purchase/pl060.cbl:L605].
        """
        self.exists = True
        self._records.clear()
        self._open_mode = OpenMode.OUTPUT
        self._next_record_pointer = 0
        self._report(FS_REPLY_OK, file_access)

    def open_input(self, file_access: Any | None = None) -> None:
        """`open input`  [sales/sl060.cbl:L480], [purchase/pl060.cbl:L421].

        Positions at the FIRST record. A file the producer never created reports
        `FS_REPLY_OPEN_NOT_FOUND` for the same reason `open_extend` does, and the
        consumer's own read then sees the at-end condition rather than a record.
        """
        if not self.exists:
            self._open_mode = OpenMode.CLOSED
            self._report(FS_REPLY_OPEN_NOT_FOUND, file_access)
            return
        self._open_mode = OpenMode.INPUT
        self._next_record_pointer = 0
        self._report(FS_REPLY_OK, file_access)

    def write(self, record: RecordT, file_access: Any | None = None) -> None:
        """`write`  [sales/sl055.cbl:L681], [purchase/pl055.cbl:L587].

        A SNAPSHOT IS APPENDED, NOT THE RECORD AREA ITSELF. A COBOL `WRITE`
        transfers the record area's BYTES to the file and the producer then goes
        on mutating that same area for the next invoice, so appending the live
        object would leave every element of the sequence aliasing the last one
        written.
        """
        if self._open_mode not in (OpenMode.EXTEND, OpenMode.OUTPUT):
            self._report(FS_REPLY_WRITE_NOT_OPEN, file_access)
            return
        self._records.append(copy.deepcopy(record))
        self._next_record_pointer = len(self._records)
        self._report(FS_REPLY_OK, file_access)

    def read_next(self, file_access: Any | None = None) -> RecordT | None:
        """`read ... at end`  [sales/sl060.cbl:L484], [purchase/pl060.cbl:L425].

        Returns the next record and reports success, or returns None and reports
        `FS_REPLY_AT_END` when the sequence is exhausted - which is the `AT END`
        branch both consumers take to their main-end paragraph.

        A READ while the file is not open for input reports
        `FS_REPLY_READ_NOT_READABLE` and returns None, matching the value
        `LineSequentialWorkFile` reports for the same misuse rather than
        inventing a second vocabulary alongside it.
        """
        if self._open_mode is not OpenMode.INPUT:
            self._report(FS_REPLY_READ_NOT_READABLE, file_access)
            return None
        if self._next_record_pointer >= len(self._records):
            self._report(FS_REPLY_AT_END, file_access)
            return None
        record = self._records[self._next_record_pointer]
        self._next_record_pointer += 1
        self._report(FS_REPLY_OK, file_access)
        return copy.deepcopy(record)

    def close(self, file_access: Any | None = None) -> None:
        """`close`  [sales/sl055.cbl:L501], [sales/sl060.cbl:L613].

        Closes WITHOUT discarding: the records are the deliverable the consumer
        opens the same file to read. Only `open_output` empties the sequence.
        """
        self._open_mode = OpenMode.CLOSED
        self._next_record_pointer = 0
        self._report(FS_REPLY_OK, file_access)


def open_item_work_file(
    name: str, record_type: type[RecordT]
) -> OpenItemWorkFile[RecordT]:
    """Declare one open-item work file - the equivalent of its `SELECT` taking effect.

    A NEW FILE EVERY CALL. Nothing is cached, memoised or held at module scope,
    for the reason `general_ledger_work_files` gives: rule R-6 requires two runs
    of the same scenario under the same pinned clock to produce byte-identical
    results, and a shared sequence would carry one run's invoices into the next
    without anything failing.

    Args:
        name: The assigned name - `OPEN_ITEM_2_NAME`, `OPEN_ITEM_4_NAME`, or
            whatever `file-18` / `file-28` resolves to in the caller's
            `File-Defs`.
        record_type: The record description the sequence carries.

    Returns:
        A closed, empty, not-yet-existing work file. Not existing is the correct
        initial state: it is what makes the producer's first `OPEN EXTEND` report
        `FS_REPLY_OPEN_NOT_FOUND` and take the create fallback
        [sales/sl055.cbl:L360-L362], [purchase/pl055.cbl:L302-L304].
    """
    return OpenItemWorkFile(name, record_type)


#  THE GROUP MOVE THE `SORT` VERB PERFORMS AT ITS TWO BOUNDARIES
# `SORT sort-trans ... USING pre-trans GIVING post-trans`
# [general/gl071.cbl:L172-L178] moves a seventy-character record area into
# another at each boundary:
#     pre-trans-record   [general/gl071.cbl:L112-L120]
#         -> sort-trans-record  [general/gl071.cbl:L136-L144]   the USING side
#     sort-trans-record
#         -> post-trans-record  [general/gl071.cbl:L124-L132]   the GIVING side
# The three descriptions are field-identical - same eight items, pictures, order
# and widths, differing only in the name prefix - so no value is converted,
# truncated, padded, re-scaled or re-signed across the sort. What follows is
# therefore a rename, expressed as COBOL expresses a group move: BY POSITION.


def _leaf_members(record_type: type[Any]) -> tuple[Field[Any], ...]:
    """The elementary items of one record description, in declaration order.

    A COBOL group item occupies no characters of its own - it is a name for the
    characters its subordinates occupy - so a positional carry must walk the ELEMENTARY
    items only.

    Args:
        record_type: A record layout from `acas_posting.records.work_records`.

    Returns:
        Its elementary items, in the order the frozen source declares them.
    """
    return tuple(
        member
        for member in fields(record_type)
        if not member.metadata[COBOL_FIELD_METADATA_KEY].is_group
    )


def _group_members(record_type: type[Any]) -> tuple[Field[Any], ...]:
    """The group items of one record description, in declaration order.

    Exactly one exists across the three work-record descriptions - `gl072`'s `03 post-
    ledger.` over `05 post-ac pic 9(6)` and `05 post-pc pic 99`
    [general/gl072.cbl:L115-L117] - and `gl071` declares the very same two items FLAT at
    level `03` [general/gl071.cbl:L129-L130] with no enclosing group.

    Args:
        record_type: A record layout from `acas_posting.records.work_records`.

    Returns:
        Its group items, in the order the frozen source declares them.
    """
    return tuple(
        member
        for member in fields(record_type)
        if member.metadata[COBOL_FIELD_METADATA_KEY].is_group
    )


def _cobol_name(member: Field[Any]) -> str:
    """The frozen COBOL name of the item one dataclass attribute mirrors.

    `acas_posting.records.work_records` binds a `FieldDescriptor` to every attribute
    under `COBOL_FIELD_METADATA_KEY`, and the descriptor carries the name the frozen
    source spells - `pre-batch`, `sort-batch`, `post-ledger` and so on.

    Args:
        member: A dataclass member of a work-record description.

    Returns:
        The COBOL item name, exactly as the frozen source spells it.
    """
    return str(member.metadata[COBOL_FIELD_METADATA_KEY].name)


def _group_move(source: Any, destination_type: type[RecordT]) -> RecordT:
    """Move one record area into another of the same shape - a GROUP MOVE.

    NO VALUE IS CONVERTED. The three descriptions are field-identical
    [general/gl071.cbl:L112-L144], so every carry is like into like.

    Args:
        source: The record to move from. Its elementary items are read in declaration
            order; nothing about it is altered.
        destination_type: The record description to move into. Constructed with no
            arguments, as every work-record description permits, and then filled.

    Returns:
        A new record of `destination_type` carrying `source`'s values.

    Raises:
        WorkFileError: The two descriptions have different numbers of elementary items,
            or a group of the receiving description names an item the sending
            description does not carry.
    """
    sending = _leaf_members(type(source))
    receiving = _leaf_members(destination_type)
    if len(sending) != len(receiving):
        raise WorkFileError(
            "A group move carries elementary items one to one and the three"
            " work-record descriptions are field-identical"
            " [general/gl071.cbl:L112-L144], so "
            + type(source).__name__
            + " with "
            + str(len(sending))
            + " elementary item(s) cannot be moved into "
            + destination_type.__name__
            + " with "
            + str(len(receiving))
            + ". Nothing was moved."
        )
    destination = destination_type()
    # The positional carry.
    carried: dict[str, Any] = {}
    for sending_member, receiving_member in zip(
        sending, receiving, strict=True
    ):
        value = getattr(source, sending_member.name)
        setattr(destination, receiving_member.name, value)
        carried[_cobol_name(receiving_member)] = value
    for group_member in _group_members(destination_type):
        group_view = getattr(destination, group_member.name)
        for subordinate in fields(group_view):
            subordinate_name = _cobol_name(subordinate)
            if subordinate_name not in carried:
                raise WorkFileError(
                    "The group item "
                    + _cobol_name(group_member)
                    + " names a subordinate, "
                    + subordinate_name
                    + ", that "
                    + type(source).__name__
                    + " does not carry, so the group view of those"
                    " characters cannot be filled. A group is a second name"
                    " for characters its subordinates already occupy"
                    " [general/gl072.cbl:L115-L117]."
                )
            setattr(group_view, subordinate.name, carried[subordinate_name])
    return destination


# THE KEY TUPLE [general/gl071.cbl:L172-L178] 172 sort sort-trans 173 on ascending key
# sort-batch 174 sort-ac 175 sort-pc 176 sort-post 177 using pre-trans 178 giving post-
# trans.


def _sort_trans_descriptor(attribute: str) -> Any:
    """The `FieldDescriptor` of one `sort-trans-record` item.

    Annotated `Any` rather than by its own class deliberately. The descriptor's class
    lives in `acas_posting.cobol.field`, which is outside the dependency set the Agent
    Action Plan gives this file.

    Args:
        attribute: The `SortTransRecord` attribute name.

    Returns:
        That attribute's field descriptor.

    Raises:
        WorkFileError: `SortTransRecord` has no such attribute. A PROGRAMMER error, and
            one that would otherwise produce a WRONG ORDERING rather than a failure; see
            `WorkFileError`.
    """
    for member in fields(SortTransRecord):
        if member.name == attribute:
            return member.metadata[COBOL_FIELD_METADATA_KEY]
    raise WorkFileError(
        "sort-trans-record [general/gl071.cbl:L136-L144] has no item "
        + attribute
        + ", so no sort key can be built for it. The four keys of"
        " [general/gl071.cbl:L173-L176] are sort-batch, sort-ac, sort-pc and"
        " sort-post."
    )


#: The four keys of `gl071`'s `SORT`, in the order the statement names them, every one
#: ascending [general/gl071.cbl:L172-L178].
SORT_TRANS_ASCENDING_KEYS: Final[tuple[SortKey, ...]] = (
    SortKey(
        accessor="sort_batch",
        descriptor=_sort_trans_descriptor("sort_batch"),
        direction=SortDirection.ASCENDING,
    ),
    SortKey(
        accessor="sort_ac",
        descriptor=_sort_trans_descriptor("sort_ac"),
        direction=SortDirection.ASCENDING,
    ),
    SortKey(
        accessor="sort_pc",
        descriptor=_sort_trans_descriptor("sort_pc"),
        direction=SortDirection.ASCENDING,
    ),
    SortKey(
        accessor="sort_post",
        descriptor=_sort_trans_descriptor("sort_post"),
        direction=SortDirection.ASCENDING,
    ),
)


@dataclass(slots=True)
class GeneralLedgerWorkFiles:
    """The three work files `gl070`, `gl071` and `gl072` share.

    Named after the file descriptions the frozen source declares - `pre-trans`, `post-
    trans` and `sort-trans` [general/gl071.cbl:L92-L102] - so a reader following any of
    the three programs finds the sequence it is looking at under the name that program
    uses.

    Attributes:
        pre_trans: `pre-trans` [general/gl071.cbl:L92-L95] over `pre-trans-record`
            [general/gl071.cbl:L112-L120]. Written by `gl070` phase 2
            [general/gl070.cbl:L447-L472] and read as the `SORT`'s `USING` file
            [general/gl071.cbl:L177].
        post_trans: `post-trans` [general/gl071.cbl:L97-L100] over `post-trans-record`.
            Written as the `SORT`'s `GIVING` file [general/gl071.cbl:L178] and read by
            `gl072` phase 4 [general/gl072.cbl:L278-L440].
        sort_trans: `sort-trans` [general/gl071.cbl:L102] over `sort-trans-record`
            [general/gl071.cbl:L136-L144]. The SORT-FILE description, an `sd` rather
            than an `fd`, assigned by number to `file-21` [copybooks/file21.cob:L1].
    """

    pre_trans: LineSequentialWorkFile[PreTransRecord] = field(
        default_factory=lambda: LineSequentialWorkFile(
            PRE_TRANS_NAME, PreTransRecord
        )
    )
    post_trans: LineSequentialWorkFile[PostTransRecord] = field(
        default_factory=lambda: LineSequentialWorkFile(
            POST_TRANS_NAME, PostTransRecord
        )
    )
    sort_trans: LineSequentialWorkFile[SortTransRecord] = field(
        default_factory=lambda: LineSequentialWorkFile(
            SORT_TRANS_NAME, SortTransRecord
        )
    )


def general_ledger_work_files() -> GeneralLedgerWorkFiles:
    """Declare a fresh set of the cycle's three work files.

    A NEW SET EVERY CALL. Nothing is cached, memoised or held at module scope, so one
    run cannot inherit another's records.

    Returns:
        A container of three closed, empty work files, each over its own record
            description.
    """
    return GeneralLedgerWorkFiles()


def sort_using_giving(
    sort_trans: LineSequentialWorkFile[Any],
    *,
    on_ascending_key: Sequence[SortKey] = SORT_TRANS_ASCENDING_KEYS,
    using: LineSequentialWorkFile[Any],
    giving: LineSequentialWorkFile[Any],
) -> None:
    """`SORT ... ON ASCENDING KEY ... USING ... GIVING ...` - the whole of it.

    Reproduces the one in-scope `SORT`, verbatim [general/gl071.cbl:L172-L178].

    Args:
        sort_trans: The SORT-FILE description, `sort-trans` [general/gl071.cbl:L102].
            Its `record_type` is the description the records are ordered in.
        on_ascending_key: The keys, MOST SIGNIFICANT FIRST, exactly as the statement
            names them. Defaults to `SORT_TRANS_ASCENDING_KEYS`, which IS the
            statement's key list.
        using: The input file, `pre-trans` [general/gl071.cbl:L177]. Opened for input,
            read to the at-end condition, and closed.
        giving: The output file, `post-trans` [general/gl071.cbl:L178]. Opened for
            output - which discards its previous contents - written to, and closed.

    Raises:
        WorkFileError: A record description does not have the shape another's group move
            requires; see `_group_move`. acas_posting.cobol.sortverb.SortVerbError: The
            key list is empty.
        TypeError: A key value is a binary floating-point value, which rule R-2 forbids
            anywhere in this migration including as a sort key.
    """
    # 170 display "Sorting.......Please wait " at 0801 ... The one screen statement of
    # the program, as a log record. Agent Action Plan section 0.3.4.
    logger.info(
        "%s (%s -> %s -> %s, %d key(s))",
        SORTING_DIAGNOSTIC,
        using.name,
        sort_trans.name,
        giving.name,
        len(on_ascending_key),
    )

    sort_trans.open_output()
    using.open_input()
    while True:
        source_record = using.read_next()
        if using.fs_reply == FS_REPLY_AT_END:
            break
        sort_trans.write(_group_move(source_record, sort_trans.record_type))
    using.close()

    # 172 sort sort-trans 173 on ascending key sort-batch sort-ac sort-pc sort-post The
    # ordering itself, and the ONLY thing about this statement that changes the
    # sequence.
    ordered = sort_records(sort_trans.records, on_ascending_key)

    # The merge leaves the sort description holding the ordered stream.
    sort_trans.open_output()
    for ordered_record in ordered:
        sort_trans.write(ordered_record)
    sort_trans.close()

    giving.open_output()
    for ordered_record in ordered:
        giving.write(_group_move(ordered_record, giving.record_type))
    giving.close()
