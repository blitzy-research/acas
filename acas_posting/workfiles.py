"""The two General Ledger work files, as ordered in-process sequences.

`pretrans.tmp` and `postrans.tmp` carry the General Ledger posting cycle's
transaction stream between three of its phases. This module models them, the
sort work description that sits between them, and the handful of COBOL file
verbs those phases use on them. It holds no accounting decision, no record
layout of its own and no sort comparison: the layouts belong to
`acas_posting.records.work_records` and the ordering to
`acas_posting.cobol.sortverb`.

WORK FILES ARE SEQUENCES - NOT TABLES, NOT FILES  (Agent Action Plan 0.3.1)
The sequences live in memory for the life of the process. NO FILESYSTEM:
nothing here creates, opens, renames, truncates or removes a file, and no
temporary-file helper, path object or byte stream appears - the two names are
IDENTITIES, what the frozen copybook calls each sequence, never resolved against
a filesystem. NO DATABASE: these are not tables, they are absent from the frozen
schema and from the twenty-two in-scope tables, nothing about them shows in a
state diff, and this module issues no statement and imports nothing from the
data-access layer. The record layout and the ordering are the contract, and both
are exact.

WHERE THE NAMES COME FROM  [copybooks/wsnames.cob:L13-L16]
Verbatim, the maintainer's own annotations included:

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
=================================================================
Agent Action Plan section 0.6.4 opens its ordering findings with this one, and
it is the strongest of them. Verbatim:

    "THE SORT FEEDS A SEQUENTIAL READ. `gl072` locates the nominal-ledger
    account for each posting with a sequential read-next rather than an indexed
    read [general/gl072.cbl:L410-L412]. It finds the right account only because
    `gl071` has already emitted the stream in nominal-key order. Any change in
    sort stability or key composition produces SILENT MISPOSTING - no error, no
    diagnostic, wrong balances. This single dependency is why `sortverb.py`
    guarantees stability and why a dedicated test asserts `gl071`'s output
    ordering."

That is anomaly A-14 of the register, and this module is one of the two places
an accidental reordering could be introduced. Concretely, of this file:

  * `write` APPENDS, and preserves insertion order absolutely. There is no
    reordering, no de-duplication, no unordered container, no mapping keyed by
    a record value, and no lazily-evaluated sequence a consumer could draw from
    out of order.
  * `read_next` RETURNS RECORDS IN EXACTLY THE STORED ORDER, one at a time,
    advancing a single forward-only pointer.
  * THE SORT IS STABLE, and cannot be made otherwise. Records equal on all
    four keys come out in the order they went in.
  * THE KEY TUPLE IS EXACTLY `(batch, ac, pc, post)`, ALL ASCENDING. Four keys,
    in that order, published as one constant so there is a single spelling of
    it in the package.

NO INDEX, NO LOOKUP, NO FAST PATH
=================================
Agent Action Plan section 0.8.4, verbatim, is a prohibition rather than a
preference:

    "the migration must not 'optimise' the sequential nominal read into an
    indexed one, even though that would obviously be faster, because section
    0.6.4's first finding shows the sequential read is entangled with
    sort-order correctness. Any performance work is therefore out of scope by
    construction, not merely unrequested."

So there is no index of any kind in this module, no key-to-record mapping, no
ordered-container library, no binary search, no memoised lookup and no `find`
verb. A consumer walks the sequence in order, exactly as the compiled program
walks its work file. The obvious speed-up is precisely the forbidden change.
`acas_posting.cobol.sortverb` carries the identical prohibition and the two are
consistent.

THE STATUS VOCABULARY
=====================
Both work files declare `status fs-reply` [general/gl071.cbl:L94],
[general/gl071.cbl:L99], and the two values this cycle tests are declared
below, alongside the one further value a read past the end was MEASURED to
leave. They are declared LOCALLY, as integers, rather than imported: the
data-access layer owns the same vocabulary for database use, and importing it
here would couple a scratch-sequence abstraction to the database tier for the
sake of three integers. See `FS_REPLY_OK`, `FS_REPLY_AT_END` and
`FS_REPLY_READ_NOT_READABLE` for the provenance, for the measurement, and for
the picture divergence that goes with them.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
Both work files declare `status fs-reply` [general/gl071.cbl:L94],
[general/gl071.cbl:L99]; the two values this cycle tests are declared LOCALLY as
integers rather than imported, so a scratch-sequence abstraction is not coupled
to the database tier for the sake of two integers - see `FS_REPLY_OK` and
`FS_REPLY_AT_END`. `gl071`'s one screen statement is a diagnostic with no
database effect and becomes `SORTING_DIAGNOSTIC`. Nothing runs outside this
interpreter (rule R-1): the compiled `SORT` spills to `work.tmp`
[general/gl071.cbl:L102] when volume demands it, and this module reproduces the
statement's semantics rather than the spill. Nothing is concurrent and no
validation is added (rule R-3): a line-sequential `WRITE` does not inspect its
record and neither does `write`, so the only failures raised are wrong-state
PROGRAMMER errors, which can never fire on record CONTENT - the cycle's silent
skips [general/gl072.cbl:L291-L292], [general/gl072.cbl:L306-L307] must stay
silent (Agent Action Plan 0.6.5). Nothing ambient is consulted (rule R-6): no
clock, no entropy source, no environment lookup and no reliance on an unordered
container's iteration order. Rules R-1 to R-6 are the six the Agent Action Plan
carries in its section 0.7.2, which is where their full text is read.
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

# The complete public surface. Sorted, and a tuple rather than a list, matching
# the convention of every sibling module: sorted so the order is a mechanical
# consequence of the names instead of an editorial choice, and a tuple so the
# surface cannot be reordered, extended or mutated in place at run time.
__all__: Final[tuple[str, ...]] = (
    "FS_REPLY_AT_END",
    "FS_REPLY_OK",
    "FS_REPLY_READ_NOT_READABLE",
    "POST_TRANS_NAME",
    "PRE_TRANS_NAME",
    "SORTING_DIAGNOSTIC",
    "SORT_TRANS_ASCENDING_KEYS",
    "SORT_TRANS_NAME",
    "GeneralLedgerWorkFiles",
    "LineSequentialWorkFile",
    "OpenMode",
    "WorkFileError",
    "general_ledger_work_files",
    "sort_using_giving",
)

#: The record a work file carries. Preserved through the class below so that a
#: caller that built a sequence over `PreTransRecord` reads `PreTransRecord`
#: back out of it, rather than `object`. Nothing about the type is inspected
#: beyond its dataclass field list, which is what the group move reads.
RecordT = TypeVar("RecordT")

#: The module's logger. `logging`, never a print: a diagnostic must be
#: suppressible, routable and absent from every table dump, and a print is none
#: of those. See `SORTING_DIAGNOSTIC` for the one message reproduced here.
logger: Final[logging.Logger] = logging.getLogger(__name__)


#  THE FILE STATUS VOCABULARY  [copybooks/wsfnctn.cob:L22-L26]
#     22  01  File-Access.
#     23      03  We-Error        pic 999.
#     24      03  Rrn             pic 9(5)   comp.
#     25      03  Fs-Reply        pic 99.
#     26      03  s1              pic x.
# Both work files declare `status fs-reply` [general/gl071.cbl:L94],
# [general/gl071.cbl:L99]. Only two of that field's values are reachable through
# a work file in this cycle - success and at-end - so only those two are
# declared, as the integers the COBOL compares against. Declared here rather
# than imported: the data-access layer owns the same field over the fuller value
# set the handlers and bridges produce, and both cite L25 as the one authority.

#: `fs-reply` after an operation that succeeded - the value the COBOL leaves in
#: place when neither the at-end condition nor an error arose
#: [copybooks/wsfnctn.cob:L25].
FS_REPLY_OK: Final[int] = 0

#: `fs-reply` after a `READ` that found no further record - the `AT END`
#: condition [copybooks/wsfnctn.cob:L25]. Tested as a literal at
#: [general/gl070.cbl:L454] and [general/gl070.cbl:L487], and expressed as the
#: `AT END` phrase at [general/gl072.cbl:L286]. A PICTURE DIVERGENCE, recorded
#: rather than resolved (rules R-4, R-5): `gl071` does not copy the block above
#: but declares `77 fs-reply pic xx.` [general/gl071.cbl:L150] - ALPHANUMERIC -
#: while [copybooks/wsfnctn.cob:L25] declares the same logical field as numeric.
#: `gl070` and `gl072` take the copybook's numeric form, so integers are used.
FS_REPLY_AT_END: Final[int] = 10

#: `fs-reply` after a `READ` issued when the file was ALREADY at its end - a
#: READ ATTEMPTED ON A FILE NOT IN A READABLE STATE.
#:
#: MEASURED, not assumed. The provisional answer was that a further read simply
#: repeats the at-end condition; GnuCOBOL 3.2.0 does something else. A
#: line-sequential file was written, opened for input and read past its end:
#:
#:     read 3 (the one that hits the end)  status 10, AT END FIRED
#:     read 4 (issued after that)          status 46, AT END DID NOT FIRE
#:     read 5 (issued after that)          status 46, AT END DID NOT FIRE
#:     the run continued and exited zero; CLOSE then returned 00, and a
#:     re-OPEN reset the file so that the first record was read again
#:
#: So the second and subsequent reads report 46 and the `AT END` phrase does
#: NOT run for them - which means a paragraph written as `read f at end go to
#: end-run` would NOT branch, and would fall through instead. That is why the
#: value is published rather than folded into the at-end constant: the two
#: conditions are distinguishable in the compiled program and `at_end` must
#: report False for this one.
#:
#: UNEXERCISED BY THE IN-SCOPE CYCLE, and recorded as such: every read loop
#: transfers control the moment the condition arises - `go to end-run`
#: [general/gl070.cbl:L455], `go to main-exit` [general/gl070.cbl:L488] and
#: `go to end-run` [general/gl072.cbl:L289] - so no in-scope paragraph issues a
#: second read. The value is nevertheless the measured one rather than an
#: invented one (rule R-6).
FS_REPLY_READ_NOT_READABLE: Final[int] = 46


#  THE THREE WORK-FILE IDENTITIES  [copybooks/wsnames.cob:L13-L16]
# These are IDENTITIES, not locations: a name by which a sequence identifies
# itself in a log line or a failure message. Nothing below resolves one against
# a filesystem, joins it to a directory or treats it as anything but text -
# Agent Action Plan section 0.3.1 makes these sequences, "not tables and not
# temporary files". Each value is the frozen `VALUE` clause, quoted from the
# copybook that declares it; `acas_posting.records.file_defs` models the whole
# name table including these two entries and is deliberately not imported here,
# so both modules quote the SAME frozen clause rather than deriving one from the
# other. The declared `pic x(532)` is a path allowance with no meaning for an
# in-memory sequence, so it is not reproduced.

#: `pre-trans-name` [copybooks/wsnames.cob:L15] - the stream `gl070` phase 2
#: writes [general/gl070.cbl:L447] and the `SORT`'s `USING` file
#: [general/gl071.cbl:L177]. The maintainer's own annotation on that line is
#: `*> gl071`.
PRE_TRANS_NAME: Final[str] = "pretrans.tmp"

#: `post-trans-name` [copybooks/wsnames.cob:L16] - the `SORT`'s `GIVING` file
#: [general/gl071.cbl:L178] and the stream `gl072` phase 4 reads
#: [general/gl072.cbl:L278]. Annotated `*> gl071` in the copybook too.
POST_TRANS_NAME: Final[str] = "postrans.tmp"

#: `file-21` [copybooks/file21.cob:L1] - the sort work description's assigned
#: name, `select sort-trans  assign file-21.` [general/gl071.cbl:L102].
#: Assigned by number rather than by name, which is why it is the one of the
#: three not declared in the `file-defs-a` prologue.
SORT_TRANS_NAME: Final[str] = "work.tmp"


#  THE ONE SCREEN STATEMENT, AS A LOG RECORD  [general/gl071.cbl:L170]
# `gl071` contains exactly one screen statement, verbatim:
#    170      display  "Sorting.......Please wait            " at 0801
#             with foreground-color 2.
# Agent Action Plan section 0.3.4 puts this in its first class: a diagnostic
# display with no database effect becomes a log record at a severity matching
# the original's intent, which "must not alter control flow and must not appear
# in any table dump". Emitted through `logging` at INFO - the original is a
# progress notice - with the screen padding, position and colour dropped as
# presentation. Published as a constant so the package has one spelling of it.

#: The progress notice `gl071` displays before sorting
#: [general/gl071.cbl:L170], carried as text so it can be logged rather than
#: drawn. Screen position, colour and the literal's trailing padding are
#: presentation and are dropped.
SORTING_DIAGNOSTIC: Final[str] = "Sorting.......Please wait"


#  OPEN MODE - `OPEN INPUT` / `OPEN OUTPUT`, AND CLOSED


class OpenMode(enum.StrEnum):
    """Which `OPEN` a work file is under, or none.

    The three states the cycle's verbs move a work file between. A `StrEnum`,
    matching the enumerations `acas_posting.dictionary.model` and
    `acas_posting.cobol.sortverb` publish, so a mode renders as its own name in
    a log line or a failure message without a conversion step.

    Only the two open modes the three phases actually use are members. There is
    deliberately no `I-O` and no `EXTEND`: `gl070` opens `pre-trans` for output
    [general/gl070.cbl:L447], `gl072` opens `post-trans` for input
    [general/gl072.cbl:L278], `gl071` opens neither explicitly at all, and no
    phase of this cycle opens a work file any other way. A member for a mode
    the compiled cycle never uses would be a behaviour with no evidence behind
    it (rule R-6).
    """

    CLOSED = "CLOSED"
    """Not open. The state a sequence starts in and the state `close` returns
    it to. A work file's CONTENTS survive this state - see
    `LineSequentialWorkFile.close` for why that is required rather than
    convenient."""

    INPUT = "INPUT"
    """`OPEN INPUT` - open for reading, positioned at the first record.
    [general/gl072.cbl:L278]."""

    OUTPUT = "OUTPUT"
    """`OPEN OUTPUT` - open for writing, and the previous contents discarded.
    [general/gl070.cbl:L447]."""


#  FAILURE


class WorkFileError(RuntimeError):
    """A work-file verb was used in a state that cannot carry it out.

    Every use of this error reports a PROGRAMMER error - a `write` to a
    sequence that is not open for output, a `read_next` from one that is not
    open for input, a group move between record layouts of different shapes.
    None of them can fire on the CONTENT of a record, which rule R-3 forbids: a
    COBOL line-sequential `WRITE` does not inspect its record, so neither does
    `LineSequentialWorkFile.write`, and a short, non-numeric or unexpected
    field is stored exactly as handed over.

    THE DISTINCTION IS LOAD-BEARING, not stylistic. Agent Action Plan section
    0.6.5 requires the cycle's rejection paths to be reproduced in both
    dimensions - the same disposition AND the same effect on the database - and
    two of this cycle's rejections are entirely silent: `gl072` skips a posting
    whose batch number is not numeric [general/gl072.cbl:L291-L292] and skips a
    record whose handler returned a specific error
    [general/gl072.cbl:L306-L307], with no message, no counter and no trace. A
    rejection raised from this module on a record's content would make that
    silence impossible to reproduce and would fail rule R-4 outright.

    A `RuntimeError` subclass rather than a `ValueError`, because what is wrong
    is the STATE the verb was issued in and not the value it was handed;
    `acas_posting.cobol.sortverb.SortVerbError` derives from `ValueError` for
    the converse reason, its checks all firing on a malformed key
    specification. No file-status value is invented for any of these: the frozen
    programs never issue a verb in a wrong state, so the specification says
    nothing about what one would return, and inventing a status would be a
    behaviour with nothing behind it (rule R-6).
    """


# =============================================================================
#  THE RECORD AREA, AND WHY EVERY CROSSING OF IT IS A COPY
# =============================================================================


def _record_area_snapshot(record: RecordT) -> RecordT:
    """Take the VALUE of a record area, the way a COBOL `WRITE` does.

    A COBOL `WRITE` DOES NOT STORE A REFERENCE. It moves the record area's
    current bytes into the file, after which the area remains the program's own
    to overwrite; a `READ` moves the other way, filling the area from the file.
    The area is therefore a value crossing, in both directions, and the frozen
    cycle depends on it being one.

    THE PROOF IS THE THREE-LEG DOUBLE-ENTRY EXPLOSION
    [general/gl070.cbl:L495-L532]. `gl070` declares ONE record area,
    `pre-trans-record`, loads the fields common to all three legs exactly once
    [general/gl070.cbl:L495-L499], and then writes it three times with the
    account, profit centre and amount OVERWRITTEN IN PLACE between the writes:

        move post-dr to pre-ac ... write pre-trans-record.   L501-L508  debit
        move post-cr to pre-ac ...
        multiply pre-amount by -1 giving pre-amount
                               ... write pre-trans-record.   L510-L519  credit
        move vat-ac  to pre-ac ... write pre-trans-record.   L525-L532  VAT

    Three postings reach the file, each holding the values the area held at the
    instant of its own `WRITE`. Store a reference instead and the file ends up
    holding one object three times, carrying only the LAST leg's account and
    the last leg's amount - so every debit and every credit in the batch would
    be replaced by the value-added-tax leg, the sort would order three
    identical records, and `gl072` would post the wrong figure to the wrong
    account. NOTHING WOULD REPORT IT: no exception, no diagnostic, no status.
    That is the exact failure class this migration exists to avoid, which is
    why the copy is made here rather than left to a caller's discipline.

    A DEEP COPY, AND THE DEPTH IS NECESSARY. `PostTransRecord` carries a
    nested group, `post_ledger: PostLedger`, which is `gl072`'s
    `03  post-ledger.` view over `05  post-ac     pic 9(6)` and
    `05  post-pc     pic 99` [general/gl072.cbl:L115-L117] - the two items
    `gl071` declares FLAT at level `03` in the very same file
    [general/gl071.cbl:L129-L130]. A shallow copy would duplicate the outer
    record and SHARE that group, so mutating `record.post_ledger.post_ac`
    after a write would still reach into the stored record - the same defect,
    one level down and harder to see. `copy.deepcopy` copies the whole area,
    which is what the verb it models does.

    THE COST IS NOT A CONSIDERATION. Agent Action Plan section 0.8.4, verbatim:
    "None are expected, and none are pursued", on performance. Correctness of
    the record-area semantics is not tradeable against the cost of copying a
    record of eight fields.

    IT VALIDATES NOTHING (rule R-3). No field is inspected, no type is checked,
    no value is coerced and nothing is filled in. A short, empty, non-numeric
    or nonsensical field is copied exactly as it stands, so a record that would
    make `gl072` take its silent skip [general/gl072.cbl:L291-L292] still does.

    DETERMINISM (rule R-6), MEASURED ON THIS INTERPRETER rather than assumed.
    `int`, `str` and `decimal.Decimal` are immutable, so `copy.deepcopy`
    returns the ORIGINAL OBJECT for each of them and performs no arithmetic at
    all; only the record and its nested group are duplicated. Under a
    deliberately hostile ambient context of precision 1 and a minimum exponent
    of -2, `copy.deepcopy(Decimal("1200.00"))` IS the original and still
    renders "1200.00" with `exponent=-2`, so no scale is normalised away and no
    ambient context can reach a copied amount. Two deepcopies of one record
    compare equal and hold distinct nested groups. Nothing about the result
    exposes an identity value, an address or an iteration order.

    Args:
        record: The record area to take the value of.

    Returns:
        An independent record carrying the same field values.
    """
    return copy.deepcopy(record)


# =============================================================================
#  ONE LINE SEQUENTIAL WORK FILE


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
    error, no diagnostic, wrong balances" [general/gl072.cbl:L410-L412]. A
    reordering introduced here would be exactly as silent.

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
            `PRE_TRANS_NAME`, `POST_TRANS_NAME` or `SORT_TRANS_NAME`. Text, and
            never resolved against a filesystem.
        record_type: The `01` record layout this file carries, as declared in
            `acas_posting.records.work_records`. A file description has exactly
            one record description in the frozen source, so this carries
            exactly one.
        open_mode: Which `OPEN` the file is under, or `OpenMode.CLOSED`.
        fs_reply: The `fs-reply` status of the last verb issued
            [copybooks/wsfnctn.cob:L25].
        at_end: Whether the last `read_next` met the `AT END` condition.
        records: Copies of the stored records, in stored order.
    """

    # Slotted. The six members below are the whole of an instance's state, and
    # fixing them prevents a caller attaching an index, a lookup mapping or a
    # cached position to a sequence - which Agent Action Plan section 0.8.4
    # forbids outright - by making the attempt fail loudly instead of silently
    # succeeding.
    # Sorted, for the same reason `__all__` is: the order is then a mechanical
    # consequence of the names rather than an editorial choice, and it does not
    # drift as members are added. It carries no information, so none is lost -
    # the members declare themselves in `__init__` below in the order that does
    # mean something: identity, then record description, then contents, then
    # position within them, then status, then open mode.
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

        Declaring a file opens nothing and reads nothing, exactly as a COBOL
        `select` clause does neither: an instance starts `OpenMode.CLOSED`,
        with no records and a successful status, and the first verb issued on
        it decides what happens next.

        Args:
            name: The identity the frozen copybook gives this file. Carried as
                given; never resolved, joined or otherwise treated as a
                location.
            record_type: The record layout this file carries - one of
                `PreTransRecord`, `SortTransRecord` or `PostTransRecord`. Held
                so that `sort_using_giving` can materialise a record of the
                right description when it moves one file's records into
                another's, which is what the compiled `SORT` verb does at its
                `USING` and `GIVING` boundaries.
        """
        self._name: str = name
        self._record_type: type[RecordT] = record_type
        # A list, because appending to it is the WRITE verb and its order is
        # the record order. Never a mapping, never an unordered container,
        # never a lazily-evaluated sequence.
        self._records: list[RecordT] = []
        # COBOL's own term for this is the CURRENT RECORD POINTER: the position
        # a sequential READ will take its record from. Forward-only, because
        # `access sequential` [general/gl071.cbl:L93] is the only access mode
        # declared and no phase of this cycle repositions within a work file.
        self._next_record_pointer: int = 0
        self._fs_reply: int = FS_REPLY_OK
        self._open_mode: OpenMode = OpenMode.CLOSED

    # -- what this file is ---------------------------------------------------

    @property
    def name(self) -> str:
        """The identity the frozen copybook gives this file.

        [copybooks/wsnames.cob:L15] for `pretrans.tmp`,
        [copybooks/wsnames.cob:L16] for `postrans.tmp`, and
        [copybooks/file21.cob:L1] for the sort description's `work.tmp`. Text
        for a log line or a failure message, never a location.
        """
        return self._name

    @property
    def record_type(self) -> type[RecordT]:
        """The `01` record layout this file carries.

        One description per file, as the frozen source declares
        [general/gl071.cbl:L112], [general/gl071.cbl:L124],
        [general/gl071.cbl:L136]. The layout itself belongs to
        `acas_posting.records.work_records`; this is a reference to it.
        """
        return self._record_type

    @property
    def open_mode(self) -> OpenMode:
        """Which `OPEN` this file is under, or `OpenMode.CLOSED`."""
        return self._open_mode

    @property
    def fs_reply(self) -> int:
        """The `fs-reply` status of the last verb issued.

        `status fs-reply` [general/gl071.cbl:L94], [general/gl071.cbl:L99],
        declared at [copybooks/wsfnctn.cob:L25]. `FS_REPLY_OK` after a verb
        that succeeded and `FS_REPLY_AT_END` after a `read_next` that found no
        further record - which is the test the frozen program makes,
        `if fs-reply = 10` [general/gl070.cbl:L454].

        A THIRD VALUE IS REACHABLE, and it was measured rather than assumed:
        `FS_REPLY_READ_NOT_READABLE` after a `read_next` issued once the at-end
        condition has already been reported. See `read_next` for the reading
        and `FS_REPLY_READ_NOT_READABLE` for the experiment. No in-scope phase
        reaches it, because every read loop transfers control the moment the
        condition arises.
        """
        return self._fs_reply

    @property
    def at_end(self) -> bool:
        """Whether the last `read_next` met the `AT END` condition.

        The `AT END` phrase of `read post-trans at end`
        [general/gl072.cbl:L286], expressed as a predicate so a caller may use
        either spelling the frozen source uses: this, or the explicit
        `fs_reply == FS_REPLY_AT_END` comparison `gl070` writes
        [general/gl070.cbl:L454], [general/gl070.cbl:L487]. The two are one
        condition; both are offered because both appear in the specification.

        IT REPORTS FALSE ONCE THE FILE HAS BEEN READ PAST ITS END, because
        that is what was measured: a read issued after the at-end condition
        has been reported gives status 46 and the `AT END` phrase DOES NOT RUN
        for it. So this predicate goes True on the read that meets the
        condition and back to False on the next one, rather than latching. See
        `read_next`.
        """
        return self._fs_reply == FS_REPLY_AT_END

    @property
    def records(self) -> tuple[RecordT, ...]:
        """The stored records, in stored order.

        A snapshot for inspection - the ordering assertions the verification
        suite makes read it, and `sort_using_giving` hands it to the sort. A
        `tuple` and not the underlying list, so the stored ORDER cannot be
        edited behind the verbs' back.

        THE RECORDS THEMSELVES ARE COPIES TOO, and for the same reason `write`
        and `read_next` copy: what a work file holds is a sequence of VALUES
        that crossed a record area [general/gl070.cbl:L495-L532], and a caller
        reading this must not be able to reach back into the stored stream by
        mutating what it was handed. Returning the stored objects would leave a
        hole in the record-area semantics that the two verbs otherwise close,
        and it would be a hole in the direction that matters: an inspection
        accessor is exactly what a verification assertion holds on to while a
        phase carries on writing. `_record_area_snapshot` carries the
        mechanism.

        THIS IS NOT KEYED ACCESS. It is the whole sequence in order, which is
        what the frozen program walks. Agent Action Plan section 0.8.4
        forbids an index, and there is none: retrieving a particular record
        from this means walking it, exactly as `gl072` walks its work file.
        """
        return tuple(_record_area_snapshot(record) for record in self._records)

    def __len__(self) -> int:
        """How many records the file holds.

        Independent of the current record pointer and of the open mode: it is
        the count of records stored, not the count remaining to be read.
        """
        return len(self._records)

    def __repr__(self) -> str:
        """A diagnostic form: the file, its layout, its mode and its size.

        Built entirely from this instance's own state, so it is stable between
        runs (rule R-6): no address, no identity value and nothing ambient.
        """
        return (
            f"{type(self).__name__}({self._name!r},"
            f" {self._record_type.__name__},"
            f" {self._open_mode}, {len(self._records)} record(s),"
            f" pointer {self._next_record_pointer})"
        )

    # -- the verbs -----------------------------------------------------------

    def open_output(self) -> None:
        """`OPEN OUTPUT` - open for writing, discarding what was there before.

        Reproduces `open     output  pre-trans.` [general/gl070.cbl:L447], the
        verb with which phase 2 begins writing the exploded transaction stream,
        and the implicit open the `SORT` verb performs on its `GIVING` file
        [general/gl071.cbl:L178].

        IT TRUNCATES, and that is COBOL semantics rather than a convenience.
        `OPEN OUTPUT` on a sequential file creates the file anew: any previous
        content is unavailable afterwards, and the first `WRITE` becomes the
        first record. The work files are reused across the cycle's phases - and
        across successive runs within one process - so a sequence that
        accumulated instead of truncating would hand `gl071` the previous run's
        legs as well as this one's, and every posted balance downstream would
        be wrong with no diagnostic anywhere. Hence the records are discarded
        here, the pointer is reset, and `close` deliberately does NOT discard
        them: see `close`.

        Idempotent in effect, not in consequence: issuing it twice truncates
        twice. `gl070` issues it once [general/gl070.cbl:L447].
        """
        self._records.clear()
        self._next_record_pointer = 0
        self._open_mode = OpenMode.OUTPUT
        self._fs_reply = FS_REPLY_OK

    def open_input(self) -> None:
        """`OPEN INPUT` - open for reading, positioned at the first record.

        Reproduces `open     input  post-trans.` [general/gl072.cbl:L278], the
        verb with which phase 4 begins walking the sorted stream, and the
        implicit open the `SORT` verb performs on its `USING` file
        [general/gl071.cbl:L177].

        The records are left exactly as they are and the current record pointer
        is set to the first of them, so the whole stream is readable from the
        start. This is what makes the three-phase handoff work in one process:
        phase 2 writes the stream, phase 4 opens the same logical file for
        input and reads what phase 2 wrote.

        Re-issuing it rewinds - the pointer returns to the first record and the
        at-end condition is cleared. No phase of this cycle rewinds a work
        file; the behaviour follows from positioning at the first record rather
        than being a facility added for its own sake.
        """
        self._next_record_pointer = 0
        self._open_mode = OpenMode.INPUT
        self._fs_reply = FS_REPLY_OK

    def write(self, record: RecordT) -> None:
        """`WRITE` - append one record, preserving insertion order absolutely.

        Reproduces the three `write    pre-trans-record.` statements of the
        double-entry explosion [general/gl070.cbl:L495-L533] - the debit leg at
        [general/gl070.cbl:L508], the credit leg at [general/gl070.cbl:L519]
        and the value-added-tax leg at [general/gl070.cbl:L532] - and the
        implicit write the `SORT` verb performs into its `GIVING` file
        [general/gl071.cbl:L178].

        ORDER IS ABSOLUTE. The record goes at the end and nothing else moves.
        There is no reordering, no de-duplication, no coalescing of records
        that happen to agree, and no container whose iteration order is
        anything but insertion order. Two of the three legs written per posting
        carry the SAME batch, account and profit centre as one another in the
        ordinary case, so they are exactly the records a stable sort must not
        reorder [general/gl072.cbl:L407-L408]; the order they are appended in
        here is the order the sort is obliged to preserve.

        IT VALIDATES NOTHING (rule R-3). A COBOL line-sequential `WRITE` does
        not inspect its record - it does not check that a numeric field is
        numeric, that a character field is filled or that an amount is in range
        - so neither does this. The record is stored as handed over, and a
        short, empty, unexpected or nonsensical field is stored as it stands.
        Nor is the record's TYPE checked against `record_type`: the compiled
        `WRITE` moves whatever is in the record area, and a check here would
        reject a case the frozen program accepts. Agent Action Plan section
        0.6.5 requires the cycle's silent skips to stay silent
        [general/gl072.cbl:L291-L292], [general/gl072.cbl:L306-L307], and a
        rejection raised here would make that unreproducible.

        THE RECORD'S VALUE IS SNAPSHOTTED, NOT ALIASED, and that is the whole
        of the verb's semantics rather than a convenience. A COBOL `WRITE`
        moves the record AREA's current bytes into the file; the area then
        remains the program's own to overwrite. So what this file holds
        afterwards is the value the record carried AT THE MOMENT OF THE VERB,
        and a caller may reuse and mutate one record object across successive
        writes exactly as `gl070` reuses one `pre-trans-record` area
        [general/gl070.cbl:L495-L532]: the debit leg at
        [general/gl070.cbl:L508], the credit leg after `multiply pre-amount by
        -1 giving pre-amount` [general/gl070.cbl:L517] at
        [general/gl070.cbl:L519], and the value-added-tax leg at
        [general/gl070.cbl:L532], all three from ONE area with the account,
        profit centre and amount overwritten in between.

        `_record_area_snapshot` carries the mechanism and the reasoning.
        Storing a reference instead would leave the file holding one object
        three times, carrying only the last leg's figures - every debit and
        credit in the batch silently replaced by the value-added-tax leg, with
        no exception, no diagnostic and no status to show for it.

        Args:
            record: The record area whose current value to append.

        Raises:
            WorkFileError: The file is not open for output. A PROGRAMMER error,
                never a judgement on the record: see `WorkFileError`.
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

        Reproduces `read     post-trans  at end ...` [general/gl072.cbl:L286],
        the verb with which phase 4 walks the sorted stream, and the implicit
        read the `SORT` verb performs over its `USING` file
        [general/gl071.cbl:L177].

        THE STATUS IS SET AND THEN TESTED, exactly as the frozen source does
        it. The two spellings the cycle uses are

            read     post-trans  at end ...      [general/gl072.cbl:L286]

            perform  GL-Batch-Read-Next
            if       fs-reply = 10               [general/gl070.cbl:L453-L454]

        so a caller issues this verb and then tests `fs_reply` against
        `FS_REPLY_AT_END`, or tests the `at_end` predicate, whichever spelling
        matches the paragraph being migrated.

        IT RETURNS RECORDS IN EXACTLY THE STORED ORDER, one per call, advancing
        one position each time. There is no skipping, no filtering, no
        look-ahead and no reordering. `gl072` depends on that order for
        correctness rather than for tidiness: it locates the nominal-ledger
        account for each posting with a sequential read-next rather than an
        indexed read [general/gl072.cbl:L407-L408], so the account it finds is
        decided by the order this verb hands records over.

        NO `StopIteration` LEAVES THIS METHOD. At end it returns `None` and
        sets `fs_reply` to `FS_REPLY_AT_END`; it does not raise, and it is not
        a generator. A `StopIteration` escaping into a migrated program module
        could be swallowed by an enclosing comprehension or generator and turn
        the end of a batch into the silent end of a loop somewhere else
        entirely - which is precisely the class of silent failure this
        migration cannot tolerate.

        THE RECORD HANDED BACK IS AN INDEPENDENT COPY of what the file holds,
        for the same reason `write` snapshots: a COBOL `READ` FILLS the record
        area from the file, so what the program then holds is a value it may
        freely overwrite without disturbing the file. A caller that mutates a
        record it has just read - and `gl072` does exactly that kind of thing,
        reloading fields as it posts - must not thereby edit the stored stream
        behind the verb's back. `_record_area_snapshot` carries the mechanism.

        READING ON PAST THE AT-END CONDITION REPORTS 46, NOT THE AT-END AGAIN.
        MEASURED, and the provisional answer was wrong. Under GnuCOBOL 3.2.0, a
        line-sequential file read past its end behaves like this:

            the read that hits the end      status 10, AT END FIRED
            the next read after that        status 46, AT END DID NOT FIRE
            the one after that              status 46, AT END DID NOT FIRE
            the run continued and exited zero; CLOSE returned 00, and a
            re-OPEN reset the file so the first record was read again

        so the condition is NOT repeated: it is replaced by a different status
        for which the `AT END` phrase does not run at all. `at_end` therefore
        reports False after such a read, and `fs_reply` carries
        `FS_REPLY_READ_NOT_READABLE`, which is the measured value rather than
        an invented one (rule R-6). It stays UNEXERCISED by the in-scope cycle
        - every read loop transfers control the moment the condition arises,
        and none reads again: `go to end-run` [general/gl070.cbl:L455], `go to
        main-exit` [general/gl070.cbl:L488] and `go to end-run`
        [general/gl072.cbl:L289]. It is reproduced anyway so that no branch
        here executes a guess.

        `None` is returned in both of those cases. The compiled program leaves
        the record AREA UNCHANGED rather than clearing it, which was measured
        too; in Python the area's counterpart is the caller's own variable, and
        this verb returning `None` leaves it exactly as untouched. Returning
        the previous record instead would hand a caller a record that the
        compiled program's own `AT END` phrase means it never to process.

        Returns:
            The next record, or `None` when there is none left.

        Raises:
            WorkFileError: The file is not open for input. A PROGRAMMER error;
                see `WorkFileError`.
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
            # Measured: the first read past the end reports the at-end
            # condition, and every read after that reports 46 instead, with the
            # `AT END` phrase not running for it.
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

        Reproduces `close    pre-trans.` [general/gl070.cbl:L472] and
        `close    post-trans print-file.` [general/gl072.cbl:L440], and the
        implicit closes the `SORT` verb performs on its `USING` and `GIVING`
        files [general/gl071.cbl:L177-L178].

        THE CONTENTS SURVIVE, and they must. A COBOL `CLOSE` releases a file;
        it does not delete it. The whole point of these two work files is that
        one phase writes a stream, closes it, and a LATER PHASE opens the same
        logical file and reads what was written - `gl070` closes `pre-trans`
        [general/gl070.cbl:L472] and `gl071` then reads it as the `SORT`'s
        `USING` file [general/gl071.cbl:L177]; `gl071` writes `post-trans` and
        `gl072` then opens it for input [general/gl072.cbl:L278]. A close that
        discarded the records would break the cycle at both of its joints.

        The current record pointer is reset, because the next `OPEN` positions
        the file anyway - `open_input` at the first record, `open_output` at
        the first record of an empty file - and leaving a stale position behind
        would be state with no meaning attached to it.

        Closing a file that is already closed is not an error here. UNEXERCISED
        BY THE COBOL: each phase closes each work file exactly once, so the
        frozen source says nothing about a redundant close and no behaviour is
        invented for one (rule R-6).
        """
        self._next_record_pointer = 0
        self._open_mode = OpenMode.CLOSED
        self._fs_reply = FS_REPLY_OK


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
    characters its subordinates occupy - so a positional carry must walk the
    ELEMENTARY items only. `post-trans-record` has one group among its
    subdivisions, `03  post-ledger.` [general/gl072.cbl:L115], and that group
    is a second view of two elementary items rather than a ninth field;
    excluding it here is what keeps the eight-to-eight correspondence exact.

    Args:
        record_type: A record layout from
            `acas_posting.records.work_records`.

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

    Exactly one exists across the three work-record descriptions - `gl072`'s
    `03  post-ledger.` over `05  post-ac  pic 9(6)` and `05  post-pc  pic 99`
    [general/gl072.cbl:L115-L117] - and `gl071` declares the very same two
    items FLAT at level `03` [general/gl071.cbl:L129-L130] with no enclosing
    group. R-4: one physical file, two incompatible declarations, both
    reproduced and neither normalised.

    Args:
        record_type: A record layout from
            `acas_posting.records.work_records`.

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

    `acas_posting.records.work_records` binds a `FieldDescriptor` to every
    attribute under `COBOL_FIELD_METADATA_KEY`, and the descriptor carries the
    name the frozen source spells - `pre-batch`, `sort-batch`, `post-ledger`
    and so on. Reading it here rather than deriving a name from the Python
    attribute keeps the frozen source the authority (rule R-5).

    Args:
        member: A dataclass member of a work-record description.

    Returns:
        The COBOL item name, exactly as the frozen source spells it.
    """
    return str(member.metadata[COBOL_FIELD_METADATA_KEY].name)


def _group_move(source: Any, destination_type: type[RecordT]) -> RecordT:
    """Move one record area into another of the same shape - a GROUP MOVE.

    The transfer the `SORT` verb performs at its `USING` and `GIVING`
    boundaries [general/gl071.cbl:L172-L178]. The elementary items of `source`
    are carried into a NEW record of `destination_type`, in declaration order,
    one to one.

    A NEW RECORD, NOT THE SAME ONE. COBOL moves into a DIFFERENT record area -
    the sort description's, then the output file's - so the record written to
    the receiving file is a distinct object from the one read. Reproducing that
    keeps the three sequences from sharing records, so a later mutation of one
    file's record cannot reach into another's.

    NO VALUE IS CONVERTED. The three descriptions are field-identical
    [general/gl071.cbl:L112-L144], so every carry is like into like: an `int`
    into the same picture, a `str` into the same width, a `decimal.Decimal` at
    scale 2 into the same signed scale-2 item. Nothing is truncated, padded,
    re-scaled, re-signed or rounded, and no picture-clause store is applied -
    there is nothing for one to do. A negative amount arrives negative and at
    the same scale, which matters because most legs are negative
    [general/gl070.cbl:L517].

    THE GROUP VIEW IS FILLED FROM THE SAME CHARACTERS. A group item is a second
    name for characters its subordinates already occupy, so after the
    elementary carry each group of the receiving record is filled from the
    values that landed in the elementary items of the same COBOL name.
    `gl072` reads the very file `gl071` writes and sees `03  post-ledger.`
    [general/gl072.cbl:L115]
    over the same eight characters `gl071` wrote as two flat items
    [general/gl071.cbl:L129-L130]; a receiving record whose group view were
    left empty would misrepresent what reading those seventy characters
    produces, and `gl072` compares that composite at three sites
    [general/gl072.cbl:L309], [general/gl072.cbl:L317],
    [general/gl072.cbl:L405] before its sequential nominal read
    [general/gl072.cbl:L407-L408].

    This is NOT the record class keeping its two views in step - it does not,
    by design, because the frozen source does not either. It is one crossing of
    a file boundary, where the two views are necessarily the same characters.

    Args:
        source: The record to move from. Its elementary items are read in
            declaration order; nothing about it is altered.
        destination_type: The record description to move into. Constructed with
            no arguments, as every work-record description permits, and then
            filled.

    Returns:
        A new record of `destination_type` carrying `source`'s values.

    Raises:
        WorkFileError: The two descriptions have different numbers of
            elementary items, or a group of the receiving description names an
            item the
            sending description does not carry. Both are PROGRAMMER errors
            about SHAPE and neither can fire on the content of a record; see
            `WorkFileError`.
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
    # The positional carry. `carried` records each value under the COBOL name it
    # landed in, so the group views below can be filled from the same characters
    # rather than from a second reading of the sending record.
    # NOT AN INDEX, and worth saying so because a reader checking this module
    # against Agent Action Plan section 0.8.4 will arrive at this line. It maps a
    # FIELD NAME to that field's VALUE within the single record being moved: it
    # holds no record, it is local to one call, it is never stored on a sequence
    # and never returned, and nothing can locate a record through it. The
    # prohibition is on anything that would let a consumer find a record by key
    # instead of walking the stream in order, which is what `gl072` does
    # [general/gl072.cbl:L405], [general/gl072.cbl:L407-L408].
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


#  THE KEY TUPLE  [general/gl071.cbl:L172-L178]
#    172      sort     sort-trans
#    173               on ascending key sort-batch
#    174                                sort-ac
#    175                                sort-pc
#    176                                sort-post
#    177               using  pre-trans
#    178               giving post-trans.
# FOUR KEYS, ALL ASCENDING, in the order batch, ac, pc, post - NOT the record's
# declaration order [general/gl071.cbl:L136-L144]. Keys two and three together
# are the ledger key `gl072` walks [general/gl072.cbl:L115-L117],
# [general/gl072.cbl:L405], so exchanging or dropping one misposts silently.


def _sort_trans_descriptor(attribute: str) -> Any:
    """The `FieldDescriptor` of one `sort-trans-record` item.

    Read out of `SortTransRecord`'s own dataclass metadata, which
    `acas_posting.records.work_records` populates from the frozen declaration
    at [general/gl071.cbl:L136-L144]. Nothing is constructed here and nothing
    is described here: the descriptor carries the picture, the usage, the
    scale, the sign and the source locator, and it is that module's to state.

    Annotated `Any` rather than by its own class deliberately. The descriptor's
    class lives in `acas_posting.cobol.field`, which is outside the dependency
    set the Agent Action Plan gives this file; the value is carried through to
    `acas_posting.cobol.sortverb.SortKey`, which does name the class and does
    check it. So the type is asserted exactly once, in the module that owns the
    check.

    Args:
        attribute: The `SortTransRecord` attribute name.

    Returns:
        That attribute's field descriptor.

    Raises:
        WorkFileError: `SortTransRecord` has no such attribute. A PROGRAMMER
            error, and one that would otherwise produce a WRONG ORDERING rather
            than a failure; see `WorkFileError`.
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


#: The four keys of `gl071`'s `SORT`, in the order the statement names them,
#: every one ascending [general/gl071.cbl:L172-L178]. MOST SIGNIFICANT FIRST,
#: which is what `sort_records` requires and what the statement's own order
#: means; `SortDirection.ASCENDING` is written out on all four because
#: `on ascending key` is written out in the frozen source. A tuple, so the one
#: key list in the package cannot be reordered, extended or shortened in place.
#: It lives here rather than in `acas_posting.cobol.sortverb` because a choice of
#: which four fields a ledger sorts on is business logic and `cobol/` holds none
#: (Agent Action Plan 0.3.1), while section 0.4.1.6 derives this file from
#: `general/gl071.cbl` itself. The comparison and the stability stay
#: `sortverb`'s, and `sort_using_giving` still takes the list as a PARAMETER, so
#: a caller names the four keys at its own call site.
SORT_TRANS_ASCENDING_KEYS: Final[tuple[SortKey, ...]] = (
    # 173  on ascending key sort-batch      first key, first field
    SortKey(
        accessor="sort_batch",
        descriptor=_sort_trans_descriptor("sort_batch"),
        direction=SortDirection.ASCENDING,
    ),
    # 174                   sort-ac         second key, FIFTH field
    SortKey(
        accessor="sort_ac",
        descriptor=_sort_trans_descriptor("sort_ac"),
        direction=SortDirection.ASCENDING,
    ),
    # 175                   sort-pc         third key, sixth field
    SortKey(
        accessor="sort_pc",
        descriptor=_sort_trans_descriptor("sort_pc"),
        direction=SortDirection.ASCENDING,
    ),
    # 176                   sort-post       FOURTH key, second field
    SortKey(
        accessor="sort_post",
        descriptor=_sort_trans_descriptor("sort_post"),
        direction=SortDirection.ASCENDING,
    ),
)


#  THE THREE WORK FILES OF THE GENERAL LEDGER CYCLE


@dataclass(slots=True)
class GeneralLedgerWorkFiles:
    """The three work files `gl070`, `gl071` and `gl072` share.

    Named after the file descriptions the frozen source declares - `pre-trans`,
    `post-trans` and `sort-trans` [general/gl071.cbl:L92-L102] - so a reader
    following any of the three programs finds the sequence it is looking at
    under the name that program uses.

    HELD TOGETHER BECAUSE THE PHASES SHARE THEM. Agent Action Plan section
    0.3.1 describes the handoff: `gl070` writes `pre-trans`, `gl071` sorts it
    into `post-trans`, `gl072` reads `post-trans`. The three phases run one
    after another in one process, so the sequences must outlive each phase and
    be reachable by the next; a container passed between them is how that
    happens without any module-level mutable state.

    NOT A MODULE-LEVEL SINGLETON, deliberately. `general_ledger_work_files`
    returns a NEW container each time it is called. Shared mutable state at
    module scope would leak one run's records into the next - and rule R-6
    requires two runs of the same scenario to produce byte-identical results,
    which a sequence carrying the previous run's legs would break silently.

    Attributes:
        pre_trans: `pre-trans` [general/gl071.cbl:L92-L95] over
            `pre-trans-record` [general/gl071.cbl:L112-L120]. Written by
            `gl070` phase 2 [general/gl070.cbl:L447-L472] and read as the
            `SORT`'s `USING` file [general/gl071.cbl:L177].
        post_trans: `post-trans` [general/gl071.cbl:L97-L100] over
            `post-trans-record`. Written as the `SORT`'s `GIVING` file
            [general/gl071.cbl:L178] and read by `gl072` phase 4
            [general/gl072.cbl:L278-L440]. Carried over `PostTransRecord`,
            which is `gl072`'s declaration [general/gl072.cbl:L110-L119] - the
            one
            with the `03  post-ledger.` group - because `gl072` is what reads
            this file.
        sort_trans: `sort-trans` [general/gl071.cbl:L102] over
            `sort-trans-record` [general/gl071.cbl:L136-L144]. The SORT-FILE
            description, an `sd` rather than an `fd`, assigned by number to
            `file-21` [copybooks/file21.cob:L1].
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

    The equivalent of the three FILE-CONTROL entries taking effect
    [general/gl071.cbl:L92-L102]: three files declared, none open, all empty.

    A NEW SET EVERY CALL. Nothing is cached, memoised or held at module scope,
    so one run cannot inherit another's records. Rule R-6 requires two runs of
    the same scenario under the same pinned clock to produce byte-identical
    results, and shared sequences would be the easiest way to lose that without
    anything failing.

    Returns:
        A container of three closed, empty work files, each over its own record
        description.
    """
    return GeneralLedgerWorkFiles()


#  THE `SORT` STATEMENT  [general/gl071.cbl:L172-L178]


def sort_using_giving(
    sort_trans: LineSequentialWorkFile[Any],
    *,
    on_ascending_key: Sequence[SortKey] = SORT_TRANS_ASCENDING_KEYS,
    using: LineSequentialWorkFile[Any],
    giving: LineSequentialWorkFile[Any],
) -> None:
    """`SORT ... ON ASCENDING KEY ... USING ... GIVING ...` - the whole of it.

    Reproduces the one in-scope `SORT`, verbatim
    [general/gl071.cbl:L172-L178]:

        172      sort     sort-trans
        173               on ascending key sort-batch
        174                                sort-ac
        175                                sort-pc
        176                                sort-post
        177               using  pre-trans
        178               giving post-trans.

    The parameters are that statement's phrases, in that order and under those
    names, so the call reads as the statement does.

    THE `USING` AND `GIVING` OPENS AND CLOSES ARE IMPLICIT, AND THAT IS THE
    SPECIFICATION. `gl071` declares no `open` and no `close` of either work file
    anywhere - its whole procedure division is a screen message, this statement
    and a `goback` [general/gl071.cbl:L167-L181]. The `USING` phrase opens its
    file for input, reads every record and closes it; the `GIVING` phrase opens
    its file for output - DISCARDING what was there before - writes every sorted
    record and closes it. Omitting either would leave the sorted stream
    unreachable by the phase that reads it [general/gl072.cbl:L278].

    STABILITY IS CORRECTNESS, NOT TIDINESS. `gl072` locates the nominal-ledger
    account for each posting with a sequential read-next rather than an indexed
    read [general/gl072.cbl:L405], [general/gl072.cbl:L407-L408], so it finds
    the right account only because this sort emitted the stream in nominal-key
    order; any change in stability or key composition misposts SILENTLY (Agent
    Action Plan 0.6.4; anomaly A-14). Reproduced rather than mitigated: the
    ordering is delegated to `acas_posting.cobol.sortverb.sort_records`, whose
    stability cannot be switched off, and the key composition is
    `SORT_TRANS_ASCENDING_KEYS`. Records equal on all four keys come out in the
    order they went in, the ordinary case for the debit and credit legs of one
    posting [general/gl070.cbl:L495-L533]. This function supplies NO COMPARISON:
    `sortverb` owns what "ascending" means for a signed scale-2 zoned item, an
    unsigned display integer and a character item, because that is COBOL
    language semantics rather than an accounting decision.

    NO ARITHMETIC AND NO CONVERSION HAPPEN HERE. Records cross the two
    boundaries by group move between field-identical descriptions
    [general/gl071.cbl:L112-L144], so no value is truncated, padded, re-scaled,
    re-signed or rounded; a negative amount arrives negative and at scale 2
    [general/gl070.cbl:L517].

    Afterwards the sort description is left holding the ordered stream. A COBOL
    `sd` is not readable once the statement completes, so no caller may treat
    that retention as an input - it is a consequence of these being in-memory
    sequences that `close` does not empty. It does make the ordering DIRECTLY
    ASSERTABLE, which Agent Action Plan section 0.6.9 asks for:

        assert is_sorted(
            work_files.sort_trans.records, SORT_TRANS_ASCENDING_KEYS
        )

    Asserting on `giving` instead needs a key list naming the RECEIVING
    description's items, because the keys are declared on the sort description
    [general/gl071.cbl:L173-L176] and no other; no second list is published from
    here, because the frozen source declares one.

    Args:
        sort_trans: The SORT-FILE description, `sort-trans`
            [general/gl071.cbl:L102]. Its `record_type` is the description the
            records are ordered in.
        on_ascending_key: The keys, MOST SIGNIFICANT FIRST, exactly as the
            statement names them. Defaults to `SORT_TRANS_ASCENDING_KEYS`,
            which IS the statement's key list; a caller migrating the phase may
            pass it explicitly to name the four keys at the call site. Used
            exactly as given - none is reordered, dropped or added.
        using: The input file, `pre-trans` [general/gl071.cbl:L177]. Opened for
            input, read to the at-end condition, and closed.
        giving: The output file, `post-trans` [general/gl071.cbl:L178]. Opened
            for output - which discards its previous contents - written to, and
            closed.

    Raises:
        WorkFileError: A record description does not have the shape another's
            group move requires; see `_group_move`.
        acas_posting.cobol.sortverb.SortVerbError: The key list is empty. A
            `SORT` on no key would return the input order while looking like a
            sort, and the consumer would then walk an unordered stream with a
            sequential read.
        TypeError: A key value is a binary floating-point value, which rule R-2
            forbids anywhere in this migration including as a sort key.
    """
    # 170  display  "Sorting.......Please wait            " at 0801 ...
    # The one screen statement of the program, as a log record. Agent Action
    # Plan section 0.3.4: a diagnostic display with no database effect "must
    # not alter control flow and must not appear in any table dump". It does
    # neither - no branch below reads it, and nothing about it reaches a table.
    # INFO because the original is a progress notice.
    logger.info(
        "%s (%s -> %s -> %s, %d key(s))",
        SORTING_DIAGNOSTIC,
        using.name,
        sort_trans.name,
        giving.name,
        len(on_ascending_key),
    )

    # 177  using  pre-trans.
    # The implicit RELEASE of every input record into the sort description. The
    # input file is opened for input, read to the at-end condition and closed,
    # exactly as the `USING` phrase does it, and each record is group-moved
    # into the sort description's own layout on the way in.
    sort_trans.open_output()
    using.open_input()
    while True:
        source_record = using.read_next()
        if using.fs_reply == FS_REPLY_AT_END:
            break
        sort_trans.write(_group_move(source_record, sort_trans.record_type))
    using.close()

    # 172  sort     sort-trans
    # 173           on ascending key sort-batch sort-ac sort-pc sort-post
    # The ordering itself, and the ONLY thing about this statement that changes
    # the sequence. Stability is guaranteed by the callee and cannot be
    # switched off - see STABILITY IS CORRECTNESS above and
    # [general/gl072.cbl:L407-L408].
    ordered = sort_records(sort_trans.records, on_ascending_key)

    # The merge leaves the sort description holding the ordered stream. Written
    # back through the published verbs rather than by reaching into the
    # sequence's state, so there is one way for a record to enter a work file.
    sort_trans.open_output()
    for ordered_record in ordered:
        sort_trans.write(ordered_record)
    sort_trans.close()

    # 178  giving post-trans.
    # The implicit RETURN and WRITE of every sorted record into the output
    # file, then the implicit close. `open_output` discards whatever the output
    # file held before, which is what `OPEN OUTPUT` on a line sequential file
    # does and what makes a second run of a phase start from an empty stream.
    giving.open_output()
    for ordered_record in ordered:
        giving.write(_group_move(ordered_record, giving.record_type))
    giving.close()
