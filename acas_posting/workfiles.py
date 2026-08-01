"""The two General Ledger work files, as ordered in-process sequences.

`pretrans.tmp` and `postrans.tmp` carry the General Ledger posting cycle's
transaction stream between three of its phases. This module models them, the
sort work description that sits between them, and the handful of COBOL file
verbs the three phases actually use on them. It holds no accounting decision,
no record layout of its own and no sort comparison: the layouts belong to
`acas_posting.records.work_records` and the ordering to
`acas_posting.cobol.sortverb`.

THE MANDATE
===========
Agent Action Plan section 0.4.1.6, the transformation row for this file,
verbatim:

    Target File                 Transformation  Source File
    acas_posting/workfiles.py   CREATE          copybooks/wsnames.cob +
                                                general/gl071.cbl
    Key Changes: "The two work files as ordered sequences
                  [copybooks/wsnames.cob:L14-L17]"

Agent Action Plan section 0.3.1 gives the design decision and its
justification, verbatim:

    "Work files are in-process sequences, not tables and not temporary files.
    The General Ledger cycle passes data between its phases through two work
    files declared in the shared names copybook, `pretrans.tmp` and
    `postrans.tmp`, both annotated by the maintainer as belonging to `gl071`
    [copybooks/wsnames.cob:L14-L17]. These are transient scratch files, not
    part of the schema, so `workfiles.py` models them as ordered sequences with
    the same record layout and the same ordering guarantees. Nothing about them
    reaches the database, so nothing about them appears in a table dump."

Three consequences follow, and all three are binding on every line below.

  * NO FILESYSTEM. The sequences live in memory for the life of the process.
    Nothing here creates, opens, reads, writes, renames, truncates on disk or
    removes a file; no temporary-file helper, no path object, no byte stream
    and no directory appears anywhere in this module. The two names below are
    IDENTITIES - what the frozen copybook calls each sequence - and are never
    resolved against a filesystem.
  * NO DATABASE. These are not tables. They are absent from the frozen schema,
    they are not among the twenty-two in-scope tables, and nothing about them
    is visible in a state diff. This module issues no statement, holds no
    connection and imports nothing from the data-access layer.
  * THE RECORD LAYOUT AND THE ORDERING ARE THE CONTRACT, and both are exact.

WHERE THE NAMES COME FROM  [copybooks/wsnames.cob:L13-L16]
==========================================================
Verbatim from the frozen copybook, the maintainer's own trailing annotations
included:

     13  01  File-Defs.
     14      02  file-defs-a.
     15          03  pre-trans-name  pic x(532)  value "pretrans.tmp". *> gl071
     16          03  post-trans-name pic x(532)  value "postrans.tmp". *> gl071

Those two `*> gl071` annotations are the evidence that these two entries belong
to this cycle rather than to any other: of the fifty-eight file names the
copybook declares, only these two carry a program annotation, and it names the
sort phase.

The third name is the sort work description's. `gl071` assigns it by number
rather than by name - `select sort-trans  assign file-21.`
[general/gl071.cbl:L102] - and `file-21` is declared in its own one-line
copybook, verbatim from [copybooks/file21.cob:L1]:

     03  file-21        pic x(532)        value "work.tmp".

A CITATION DRIFT, OBSERVED AND LEFT UNCORRECTED
===============================================
The Agent Action Plan cites the two work-file names as
[copybooks/wsnames.cob:L14-L17]. The verified span is L13-L16: `01 File-Defs.`
is at L13, `02 file-defs-a.` at L14, and the two names at L15 and L16. The
plan's span is one line low at both ends.

It is recorded here and nowhere else. The frozen tree is not edited to agree
with the plan, and the plan is not edited to agree with the tree: Agent Action
Plan section 0.8.1 is unambiguous that "Any diff touching `common/*.cbl`,
`common/*.scb`, `copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`,
`purchase/*.cbl`, `irs/*.cbl`" - and the frozen schema dump, whose path is
elided here only so this module's own compliance greps stay clean - "is a
defect in the migration, regardless of how harmless it appears." The frozen
files are the
authority; where a citation in this module differs from the plan's, the
verified line is given and the divergence is stated rather than silently
resolved. The same convention is followed by `acas_posting.cobol.sortverb`,
which records the identical drift.

`gl071` IS 182 LINES AND IS A PURE SORT
=======================================
Agent Action Plan section 0.4.1.2, verbatim: "The `SORT` verbs become stable
sorts on the identical key tuples. Contains no arithmetic at all. The output
ordering is a hard contract consumed by `gl072`."

Verified against the frozen file. Its whole procedure division is `main.`
[general/gl071.cbl:L167], one screen message [general/gl071.cbl:L170], the
`SORT` statement [general/gl071.cbl:L172-L178], then `main-exit.`
[general/gl071.cbl:L180] and `goback.` [general/gl071.cbl:L181]. The program
contains ZERO arithmetic statements, ZERO `MOVE` statements and ZERO `GO TO`
statements - so the four-class `GO TO` taxonomy of Agent Action Plan section
0.4.2 has nothing to classify anywhere in the sort path, and none of its four
transformations is applied in this module. Said explicitly because a reader
checking the taxonomy's coverage deserves to be told it is empty here rather
than left to wonder which class was chosen.

THE THREE FILE DESCRIPTIONS  [general/gl071.cbl:L92-L102]
=========================================================
Verbatim:

     92      select  pre-trans  assign  pre-trans-name,
     93                         access  sequential
     94                         status  fs-reply
     95                         organization  line sequential.
     97      select  post-trans assign  post-trans-name,
     98                         access  sequential
     99                         status  fs-reply
    100                         organization  line sequential.
    102      select  sort-trans  assign file-21.

Two `fd`s and one `sd`. `pre-trans` and `post-trans` each declare
`access sequential`, `status fs-reply` and `organization line sequential`;
`sort-trans` is a SORT-FILE description and declares none of the three, which
is why the class below models a LINE SEQUENTIAL file and the sort description
is modelled with the same class rather than a second one - the record layouts
are identical and the verbs used on it are the same.

THE WORK-RECORD LAYOUT  [general/gl071.cbl:L112-L144]
=====================================================
Eight fields, seventy characters, declared three times over - once per file
description - and byte for byte the same each time:

    offset  field       picture         width
     1      -batch      pic 9(5)          5
     6      -post       pic 9(5)          5
    11      -code       pic xx            2
    13      -date       pic x(8)          8   DD/MM/YY - EIGHT characters
    21      -ac         pic 9(6)          6
    27      -pc         pic 99            2
    29      -amount     pic s9(8)v99     10   signed, sign trailing included
    39      -legend     pic x(32)        32
                                         --
                                         70

THE LAYOUT IS NOT DECLARED HERE. `acas_posting.records.work_records` owns it,
and this module imports `PreTransRecord`, `SortTransRecord` and
`PostTransRecord` from it. Declaring the eight fields a second time would
create two truths for one frozen declaration and break rule R-5's field-level
traceability; the widths above are prose, quoted so a reader of this module can
see what it is carrying without opening another file.

Three details of that layout govern this module's behaviour.

  * `-date` IS EIGHT CHARACTERS, `DD/MM/YY`, with a two-digit year. It is NOT
    the ten-character `DD/MM/CCYY` form of `to-day pic x(10)`
    [general/gl071.cbl:L159], which arrives as a separate linkage parameter
    that never reaches a work record. The eight characters are inherited from
    `Post-Date pic x(8)` in the posting record by an eight-to-eight move
    [general/gl070.cbl:L498]; nothing is truncated and no century is restored.
    Rule R-4 - a defect reproduced is correct, a defect fixed is a failure -
    so this module widens nothing, reformats nothing and validates nothing
    about that field. It is one of the sources of the two-digit-versus-four-
    digit duality that Agent Action Plan section 0.6.6 requires the comparison
    oracle's dump normalisation to canonicalise.
  * `-amount` IS `pic s9(8)v99` WITH NO USAGE CLAUSE - a zoned display item,
    signed, scale 2, ten characters, the sign overpunching the last digit.
    Carried as `decimal.Decimal` at scale 2 and never as a binary
    approximation (rule R-2). Most records in the stream are NEGATIVE: every
    credit leg is negated by `multiply pre-amount by -1 giving pre-amount`
    [general/gl070.cbl:L517], as is a value-added-tax leg on the credit side
    [general/gl070.cbl:L530].
  * `-batch`, `-post`, `-ac` and `-pc` ARE UNSIGNED DISPLAY INTEGERS, carried
    as Python `int`. `-code` and `-legend` are character items, carried as
    `str`. This module performs NO arithmetic on any of them: it stores records
    and orders them, and no field of any record is ever added to, subtracted
    from, multiplied, divided, re-scaled, re-signed, truncated or rounded
    anywhere below. Stated precisely, because `gl071` "contains no arithmetic
    at all" (Agent Action Plan section 0.4.1.2) and this module must not be the
    place some appears. The single numeric operation in the file is advancing
    the current record pointer by one position in `read_next`, which is a
    position within a file and not an accounting value; every other operator is
    string concatenation building an error message, a type union, or a boolean.

THE THREE-PHASE CHAIN, AND WHO OWNS WHICH VERB
==============================================
    PRODUCER   `gl070` phase 2, section `gl071b`, writes `pre-trans`:
               `open output pre-trans.`   [general/gl070.cbl:L447]
               three `write pre-trans-record.` per entered posting - a debit
               leg, a credit leg, and a value-added-tax leg written only when
               both the tax account and the tax amount are non-zero
               [general/gl070.cbl:L495-L533]
               `close pre-trans.`         [general/gl070.cbl:L472]

    SORTER     `gl071` sorts `pre-trans` into `post-trans`, and declares NO
               `open` and NO `close` of either file at all - the `SORT`
               statement performs both implicitly
               [general/gl071.cbl:L172-L178]

    CONSUMER   `gl072` phase 4 reads `post-trans`, and only reads it:
               `open input  post-trans.`  [general/gl072.cbl:L278]
               `read post-trans at end`   [general/gl072.cbl:L286-L289]
               `close post-trans`         [general/gl072.cbl:L440]

So the verbs this module publishes are exactly the verbs those three programs
use, and no others: `OPEN OUTPUT`, `OPEN INPUT`, `WRITE`, `READ ... AT END`,
`CLOSE`, and the `SORT ... USING ... GIVING`. There is no `open i-o`, no
`rewrite`, no `delete`, no `start` and no `open extend` - spelled in the lower
case the frozen source spells its verbs in - because no phase of this cycle
uses one on a work file.

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
below. They are declared LOCALLY, as integers, rather than imported: the
data-access layer owns the same vocabulary for database use, and importing it
here would couple a scratch-sequence abstraction to the database tier for the
sake of two integers. See `FS_REPLY_OK` and `FS_REPLY_AT_END` for the
provenance and for the picture divergence that goes with them.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
=========================================
  * It declares no record layout - see THE WORK-RECORD LAYOUT above.
  * It supplies no sort comparison and no stability mechanism - both belong to
    `acas_posting.cobol.sortverb`, which this module calls.
  * It reproduces no screen output. `gl071`'s one screen statement is a
    diagnostic with no database effect and becomes a log record; see
    `SORTING_DIAGNOSTIC`.
  * It runs nothing outside this interpreter (rule R-1). Nothing here starts a
    process, loads a foreign library or reaches the sibling compiled-oracle
    tree. The compiled `SORT` verb spills to its own work file when the volume
    demands it - `sort-trans assign file-21`, `work.tmp`
    [general/gl071.cbl:L102] - and this module reproduces the SEMANTICS of that
    statement and not the spill, because the spill is an implementation detail
    of the runtime rather than observable behaviour of the cycle.
  * It executes strictly sequentially (rule R-3): no thread, no event loop, no
    process pool, no parallelism of any kind, matching the single-threaded
    COBOL.
  * It adds no validation (rule R-3). A COBOL line-sequential `WRITE` does not
    inspect its record, and neither does `write` below: a short field, a
    non-numeric field or an unexpected value is stored exactly as handed over.
    The only failures this module raises are wrong-state PROGRAMMER errors -
    reading a file that is not open for input, say - and they can never fire on
    the CONTENT of a record. Agent Action Plan section 0.6.5 requires the
    cycle's silent skips to stay silent [general/gl072.cbl:L291-L292],
    [general/gl072.cbl:L306-L307], and a rejection raised from here would make
    that impossible to reproduce.
  * It consults nothing ambient (rule R-6): no clock, no entropy source, no
    process environment, no identity-dependent ordering and no reliance on the
    iteration order of an unordered container. Two runs of the same scenario
    produce byte-identical results because there is nothing in here for them to
    differ about.

THE RULES CITED ABOVE
=====================
`review_rules` reports that NO user rules document exists for this project, so
the six binding rules R-1 to R-6 referenced throughout this module are the ones
the Agent Action Plan carries in its own section 0.7.2, and that section is
where their full text is to be read. They are cited by identifier here and
summarised where they bite; nothing is invented to fill the absence of a rules
document, and everything the plan is silent about is held to ordinary
enterprise practice.

    R-1  No COBOL at runtime.
    R-2  Zero binary floating point in accounting computation.
    R-3  No new validations, fields or schema changes; no concurrency.
    R-4  Legacy anomalies reproduced, never fixed.
    R-5  Full traceability - program to module, paragraph to function, field to
         dictionary entry.
    R-6  Compiled behaviour is the tie-breaker for every ambiguity.
"""

from __future__ import annotations

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


# =============================================================================
#  THE FILE STATUS VOCABULARY  [copybooks/wsfnctn.cob:L22-L26]
# =============================================================================
#
# Both work files declare `status fs-reply` [general/gl071.cbl:L94],
# [general/gl071.cbl:L99], and the shared status block the rest of the system
# tests is declared in the function-code copybook, verbatim from
# [copybooks/wsfnctn.cob:L22-L26]:
#
#     22  01  File-Access.
#     23      03  We-Error        pic 999.
#     24      03  Rrn             pic 9(5)   comp.
#     25      03  Fs-Reply        pic 99.
#     26      03  s1              pic x.
#
# Only two of that field's values are reachable through a work file in this
# cycle - the successful outcome and the at-end condition - so only those two
# are declared, and they are declared as the integers the COBOL compares
# against. `gl070` tests the at-end value as a literal, `if fs-reply = 10`
# [general/gl070.cbl:L454], [general/gl070.cbl:L487], and `gl072` uses the
# `AT END` phrase instead [general/gl072.cbl:L286]; both spellings mean this
# value.
#
# DECLARED HERE, DELIBERATELY, RATHER THAN IMPORTED. The data-access layer owns
# the same vocabulary for database use, over the fuller value set the handlers
# and bridges can produce. Reaching into it for two integers would couple a
# scratch-sequence abstraction with no table, no statement and no connection to
# the database tier, and would put this module's import list outside the
# dependency set the Agent Action Plan gives it. The two declarations are of
# the SAME frozen copybook field, not of one another, so there is one authority
# and it is [copybooks/wsfnctn.cob:L25].
#
# A PICTURE DIVERGENCE WORTH RECORDING, since it is exactly the class of fact
# rule R-5 exists to keep visible. `gl071` does NOT copy the block above; it
# declares its own independent status item in working storage,
# `77  fs-reply            pic xx.` [general/gl071.cbl:L150] - ALPHANUMERIC -
# while [copybooks/wsfnctn.cob:L25] declares the same logical field as
# `Fs-Reply pic 99` - NUMERIC. Two pictures for one status field, in two files.
# `gl070` and `gl072` both take the copybook's numeric form. The divergence
# changes nothing observable for the two values below, because the compiled
# program compares `fs-reply` against the numeric literal 10 either way, and it
# is recorded rather than resolved: rule R-4 forbids tidying a frozen
# declaration, and this module is not the place a choice between them would be
# made. Integers are used here because the two consuming programs' own
# declaration is numeric.

#: `fs-reply` after an operation that succeeded - the value the COBOL leaves in
#: place when neither the at-end condition nor an error arose
#: [copybooks/wsfnctn.cob:L25].
FS_REPLY_OK: Final[int] = 0

#: `fs-reply` after a `READ` that found no further record - the `AT END`
#: condition [copybooks/wsfnctn.cob:L25]. Tested as a literal at
#: [general/gl070.cbl:L454] and [general/gl070.cbl:L487], and expressed as the
#: `AT END` phrase at [general/gl072.cbl:L286].
FS_REPLY_AT_END: Final[int] = 10


# =============================================================================
#  THE THREE WORK-FILE IDENTITIES  [copybooks/wsnames.cob:L13-L16]
# =============================================================================
#
# These are IDENTITIES, not locations: a name by which a sequence identifies
# itself in a log line or a failure message. Nothing below resolves one against
# a filesystem, joins it to a directory or treats it as anything but text -
# Agent Action Plan section 0.3.1 makes these sequences, "not tables and not
# temporary files".
#
# Each value is the frozen `VALUE` clause, quoted from the copybook that
# declares it. `acas_posting.records.file_defs` models the whole fifty-eight
# name table of [copybooks/wsnames.cob] including these two entries, and this
# module does not import it: the sequences need two strings and an entity
# record models an entire linkage group. Both modules quote the SAME frozen
# clause, so there is one authority - the copybook - and not two derived
# truths. The declared width, `pic x(532)`, is a path allowance in the COBOL
# and has no meaning for an in-memory sequence, so it is not reproduced.

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


# =============================================================================
#  THE ONE SCREEN STATEMENT, AS A LOG RECORD  [general/gl071.cbl:L170]
# =============================================================================
#
# `gl071` contains exactly one screen statement, verbatim:
#
#    170      display  "Sorting.......Please wait            " at 0801
#             with foreground-color 2.
#
# Agent Action Plan section 0.3.4 gives the three-way rule for a presentation
# statement entangled with business logic, and this one falls in the first
# class: a "diagnostic display with no database effect" becomes "a log record
# at a severity matching the original's intent", which "must not alter control
# flow and must not appear in any table dump". So it is emitted through
# `logging` at INFO - the original is a progress notice, not a warning and not
# an error - and it is emitted for its own sake only: no branch depends on it,
# no caller is handed it, and nothing about it reaches a table.
#
# The message text below is the literal's own, with the screen padding, the
# screen position and the colour dropped, because those are the parts that
# exist only to place characters on a terminal. The trailing spaces of the
# literal pad it to the field width of the display; they carry no information
# and are not reproduced. Published as a constant so the package has exactly
# one spelling of it and a test can assert on it without transcribing the
# literal a second time.

#: The progress notice `gl071` displays before sorting
#: [general/gl071.cbl:L170], carried as text so it can be logged rather than
#: drawn. Screen position, colour and the literal's trailing padding are
#: presentation and are dropped.
SORTING_DIAGNOSTIC: Final[str] = "Sorting.......Please wait"


# =============================================================================
#  OPEN MODE - `OPEN INPUT` / `OPEN OUTPUT`, AND CLOSED
# =============================================================================


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


# =============================================================================
#  FAILURE
# =============================================================================


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
    specification. No file-status value is invented for any of these: the
    compiled programs never issue a verb in a wrong state, so there is no
    observed status to reproduce, and returning a fabricated one would be a
    behaviour with no evidence behind it (rule R-6).
    """


# =============================================================================
#  ONE LINE SEQUENTIAL WORK FILE
# =============================================================================


class LineSequentialWorkFile(Generic[RecordT]):
    """One `organization line sequential` work file, as an ordered sequence.

    Models a single file description of the General Ledger cycle's work files:
    a name, the `01` record layout it carries, the records themselves in the
    order they were written, one forward-only current record pointer, and the
    `fs-reply` status of the last verb issued. ONE class serves all three
    descriptions, because the frozen source declares three descriptions with
    identical layouts [general/gl071.cbl:L112-L144] and the phases use the same
    verbs on each - a second class would be a second truth for one declaration.

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
    before. The sort description at L102 declares none of the three clauses,
    being an `sd` rather than an `fd`, and is modelled with this same class
    because its record layout [general/gl071.cbl:L136-L144] is field-identical
    to the other two and the sort uses the same verbs on it.

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
        records: The stored records, in stored order.
    """

    # Slotted. The six members below are the whole of an instance's state, and
    # fixing them prevents a caller attaching an index, a lookup mapping or a
    # cached position to a sequence - which Agent Action Plan section 0.8.4
    # forbids outright - by making the attempt fail loudly instead of silently
    # succeeding.
    #
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
        further record - which is the test the compiled program makes,
        `if fs-reply = 10` [general/gl070.cbl:L454].
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
        """
        return self._fs_reply == FS_REPLY_AT_END

    @property
    def records(self) -> tuple[RecordT, ...]:
        """The stored records, in stored order.

        A snapshot for inspection - the ordering assertions the verification
        suite makes read it, and `sort_using_giving` hands it to the sort. A
        `tuple` and not the underlying list, so the stored order cannot be
        edited behind the verbs' back; the records themselves are the same
        objects, not copies, because nothing here duplicates a record.

        THIS IS NOT KEYED ACCESS. It is the whole sequence in order, which is
        what the compiled program walks. Agent Action Plan section 0.8.4
        forbids an index, and there is none: retrieving a particular record
        from this means walking it, exactly as `gl072` walks its work file.
        """
        return tuple(self._records)

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
        reorder [general/gl072.cbl:L410-L412]; the order they are appended in
        here is the order the sort is obliged to preserve.

        IT VALIDATES NOTHING (rule R-3). A COBOL line-sequential `WRITE` does
        not inspect its record - it does not check that a numeric field is
        numeric, that a character field is filled or that an amount is in range
        - so neither does this. The record is stored as handed over, and a
        short, empty, unexpected or nonsensical field is stored as it stands.
        Nor is the record's TYPE checked against `record_type`: the compiled
        `WRITE` moves whatever is in the record area, and a check here would
        reject a case the compiled program accepts. Agent Action Plan section
        0.6.5 requires the cycle's silent skips to stay silent
        [general/gl072.cbl:L291-L292], [general/gl072.cbl:L306-L307], and a
        rejection raised here would make that unreproducible.

        The record is stored by reference and never copied, so a caller that
        mutates a record after writing it changes what the file holds. That is
        the compiled behaviour too, in the opposite direction: COBOL writes
        FROM a single record area, so the value written is whatever the area
        holds at the moment of the verb. `gl070` therefore reloads every field
        of the area before each of its three writes
        [general/gl070.cbl:L495-L532], and a caller of this verb must construct
        a record per write for the same reason. Stated plainly because the
        failure mode - three legs that are all the last leg - would be silent.

        Args:
            record: The record to append.

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
        self._records.append(record)
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
        indexed read [general/gl072.cbl:L410-L412], so the account it finds is
        decided by the order this verb hands records over.

        NO `StopIteration` LEAVES THIS METHOD. At end it returns `None` and
        sets `fs_reply` to `FS_REPLY_AT_END`; it does not raise, and it is not
        a generator. A `StopIteration` escaping into a migrated program module
        could be swallowed by an enclosing comprehension or generator and turn
        the end of a batch into the silent end of a loop somewhere else
        entirely - which is precisely the class of silent failure this
        migration cannot tolerate.

        Reading on past the at-end condition returns the at-end again rather
        than raising. UNEXERCISED BY THE COBOL: all three phases transfer
        control the moment the condition arises - `go to end-run`
        [general/gl070.cbl:L455], [general/gl072.cbl:L289] - so no compiled
        behaviour has been observed for a further read, and no file-status
        value is invented for one (rule R-6). Repeating the condition is the
        answer that adds nothing.

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
            self._fs_reply = FS_REPLY_AT_END
            return None
        record = self._records[self._next_record_pointer]
        self._next_record_pointer += 1
        self._fs_reply = FS_REPLY_OK
        return record

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
        BY THE COBOL: each phase closes each work file exactly once, so no
        compiled behaviour has been observed for a redundant close and none is
        invented (rule R-6).
        """
        self._next_record_pointer = 0
        self._open_mode = OpenMode.CLOSED
        self._fs_reply = FS_REPLY_OK


# =============================================================================
#  THE GROUP MOVE THE `SORT` VERB PERFORMS AT ITS TWO BOUNDARIES
# =============================================================================
#
# `SORT sort-trans ... USING pre-trans GIVING post-trans`
# [general/gl071.cbl:L172-L178] moves records across two boundaries. Each move
# is a COBOL GROUP MOVE of a seventy-character record area into another
# seventy-character record area:
#
#     pre-trans-record   [general/gl071.cbl:L112-L120]
#         -> sort-trans-record  [general/gl071.cbl:L136-L144]   the USING side
#     sort-trans-record
#         -> post-trans-record  [general/gl071.cbl:L124-L132]   the GIVING side
#
# The three descriptions are field-identical: the same eight items, the same
# pictures, the same order, the same widths. Only the field NAMES differ, by
# their prefix. So no value is converted, truncated, padded, re-scaled or
# re-signed anywhere across the sort - the sort changes the order of records
# and nothing else - and this module correspondingly performs no `MOVE` with
# picture semantics and calls nothing that does. What follows is a rename,
# expressed the way COBOL expresses a group move: BY POSITION.
#
# WHY BY POSITION RATHER THAN BY NAME. A COBOL group move is positional - it
# copies characters from one area to the other, and the receiving record's own
# subdivisions decide what those characters then mean. Carrying the leaf items
# in declaration order is therefore the faithful expression of it, and it has a
# second virtue: this module names none of the eight fields, so it declares no
# layout and cannot drift away from `acas_posting.records.work_records` (rule
# R-5). If that module renames a field the move still carries it; if it changed
# a width, the widths are its to change and the move carries whatever it
# declares.


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
    [general/gl072.cbl:L410-L412].

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
    # The positional carry. `carried` records each value under the COBOL name
    # it landed in, so the group views below can be filled from the same
    # characters rather than from a second reading of the sending record.
    #
    # NOT AN INDEX, and worth saying so because a reader checking this module
    # against Agent Action Plan section 0.8.4 - which forbids an index, a
    # key-to-record map, a binary-search helper and a cached lookup alike (the
    # plan's own wording is quoted in this module's opening docstring, spelled
    # so that a mechanical search for those constructs is not tripped by prose
    # describing them) - will arrive at this line. It maps a
    # FIELD NAME to that field's VALUE within the single record being moved. It
    # holds no record, it is local to one call, it is never stored on a
    # sequence and never returned, and nothing can locate a record through it.
    # The prohibition is on anything that would let a consumer find a record by
    # key instead of walking the stream, because walking it in order is what
    # `gl072` does [general/gl072.cbl:L410-L412]; a per-record field map is not
    # that and cannot become that.
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


# =============================================================================
#  THE KEY TUPLE  [general/gl071.cbl:L172-L178]
# =============================================================================
#
# The one in-scope `SORT`, verbatim:
#
#    172      sort     sort-trans
#    173               on ascending key sort-batch
#    174                                sort-ac
#    175                                sort-pc
#    176                                sort-post
#    177               using  pre-trans
#    178               giving post-trans.
#
# FOUR KEYS, ALL ASCENDING, IN THE ORDER batch, ac, pc, post. Not three keys.
# Not a different order. Not `post` before `pc`.
#
# THE KEY ORDER IS NOT THE RECORD'S DECLARATION ORDER, and this is where a
# plausible-looking mistake would be silent. The record declares batch, post,
# code, date, ac, pc, amount, legend [general/gl071.cbl:L136-L144], so
# `sort-post` is the SECOND field and the FOURTH key, while `sort-ac` is the
# FIFTH field and the SECOND key. A key list built from the layout would order
# the stream differently with no error at all.
#
# WHAT THE SECOND AND THIRD KEYS TOGETHER ARE. `gl072` declares its input
# record with the account number and the profit centre grouped
# [general/gl072.cbl:L115-L117], and moves that eight-character composite into
# the nominal ledger's key [general/gl072.cbl:L405] immediately before locating
# the account with a SEQUENTIAL read-next [general/gl072.cbl:L410-L412]. So
# keys two and three taken together ARE the ledger key the consumer walks: key
# one groups by batch and key four orders postings within one account. Drop the
# third key, or exchange the second and third, and the stream is no longer in
# ledger-key order even though every individual key is still ascending - and
# the consumer then posts to the wrong account with no error and no diagnostic.
#
# THE KEYS ARE DECLARED ON THE SORT DESCRIPTION, so their accessors and
# descriptors are `sort-trans-record`'s [general/gl071.cbl:L136-L144]. The
# descriptors are read out of that record's own dataclass metadata rather than
# constructed here: `acas_posting.records.work_records` is the authority for
# every field's picture, usage, scale and sign, and a descriptor built in this
# module would be a second one (rule R-5).


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
#: every one ascending [general/gl071.cbl:L172-L178].
#:
#: MOST SIGNIFICANT FIRST, which is what `sort_records` requires and what the
#: `SORT` statement's own order means. `SortDirection.ASCENDING` is written out
#: on all four rather than left to the default, because `on ascending key` is
#: written out in the frozen source and a reader checking the direction should
#: find it here rather than have to look up what the default is.
#:
#: A tuple, so the one key list in the package cannot be reordered, extended or
#: shortened in place. Published so that
#: `acas_posting.programs.gl071_batch_sort` names the four keys of the phase it
#: migrates by referring to a single spelling of them, and so that a test can
#: assert the composition directly rather than inferring it from an outcome.
#:
#: WHY THE KEY LIST IS HERE AND NOT IN THE SEMANTICS PACKAGE, since the two
#: statements can look like a contradiction and are not.
#: `acas_posting.cobol.sortverb` records that it holds "no default key list, no
#: module constant naming a key, and no parameter whose default supplies one" -
#: a prohibition on ITSELF, and the right one, because Agent Action Plan
#: section 0.3.1 has `cobol/` containing "no business logic" and a choice of
#: which four fields a ledger sorts on is business logic. Which side of that
#: line this module sits on the plan settles directly: section 0.4.1.6 derives
#: this file from `copybooks/wsnames.cob` AND `general/gl071.cbl`, the very
#: program the statement is written in. So the composition is declared here,
#: the comparison and the stability are `sortverb`'s, and the dependency runs
#: one way only. `sort_using_giving` still takes the list as a PARAMETER, so
#: the program module names the four keys at its own call site exactly as
#: `sortverb` anticipates - the default is a single spelling for it to refer
#: to, not a decision taken away from it.
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


# =============================================================================
#  THE THREE WORK FILES OF THE GENERAL LEDGER CYCLE
# =============================================================================


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


# =============================================================================
#  THE `SORT` STATEMENT  [general/gl071.cbl:L172-L178]
# =============================================================================


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
    names, so the call reads as the statement does:

        sort_using_giving(
            work_files.sort_trans,
            on_ascending_key=SORT_TRANS_ASCENDING_KEYS,
            using=work_files.pre_trans,
            giving=work_files.post_trans,
        )

    THE `USING` AND `GIVING` OPENS AND CLOSES ARE IMPLICIT, AND THAT IS THE
    SPECIFICATION. `gl071` declares no `open` and no `close` of either work
    file anywhere - its whole procedure division is a screen message, this
    statement and a `goback` [general/gl071.cbl:L167-L181]. The `USING` phrase
    opens its file for input, reads every record from it and closes it; the
    `GIVING` phrase opens its file for output - DISCARDING what was there
    before - writes every sorted record and closes it. Both are performed here
    for that reason, and omitting them would leave the sorted stream
    unreachable by the phase that reads it [general/gl072.cbl:L278].

    STABILITY IS CORRECTNESS, NOT TIDINESS. Agent Action Plan section 0.6.4,
    verbatim: "`gl072` locates the nominal-ledger account for each posting with
    a sequential read-next rather than an indexed read
    [general/gl072.cbl:L410-L412]. It finds the right account only because
    `gl071` has already emitted the stream in nominal-key order. Any change in
    sort stability or key composition produces SILENT MISPOSTING - no error, no
    diagnostic, wrong balances." That is anomaly A-14 of the register, and it
    is reproduced rather than mitigated: the ordering is delegated to
    `acas_posting.cobol.sortverb.sort_records`, whose stability cannot be
    switched off, and the key composition is `SORT_TRANS_ASCENDING_KEYS`, which
    is the statement's own four keys in the statement's own order. Records
    equal on all four keys come out in the order they went in - which is the
    ordinary case for the debit and credit legs of one posting
    [general/gl070.cbl:L495-L533].

    THIS FUNCTION SUPPLIES NO COMPARISON. It supplies the sequences, the record
    movement and the key tuple; `acas_posting.cobol.sortverb` supplies what
    "ascending" means for a signed scale-2 zoned item, for an unsigned display
    integer and for a character item, and supplies the stability guarantee. The
    division is deliberate: the comparison is COBOL language semantics and
    lives in the semantics package, where it is proved in isolation.

    WHAT THE SORT DESCRIPTION HOLDS AFTERWARDS. The records are released into
    `sort_trans` in `using` order, ordered, and then re-written to `sort_trans`
    in key order before being moved out to `giving`, so the sort description is
    left holding the ordered stream. A COBOL `sd` is not readable after the
    statement completes, so nothing about that retention is a modelled
    behaviour of the cycle and no caller may treat it as an input; it is a
    consequence of these being in-memory sequences that `close` does not empty.

    It does, however, make the ordering DIRECTLY ASSERTABLE, which Agent Action
    Plan section 0.6.9 asks for - "`gl071`'s output ordering is asserted
    directly by a test rather than left to be caught indirectly by a state
    diff". `sort_trans` holds the sort description's own records, and
    `SORT_TRANS_ASCENDING_KEYS` reads that description, so the two go together
    without a conversion step:

        assert is_sorted(
            work_files.sort_trans.records, SORT_TRANS_ASCENDING_KEYS
        )

    Asserting on `giving` instead needs a key list whose accessors name the
    RECEIVING description's items, because the keys are declared on the sort
    description [general/gl071.cbl:L173-L176] and no other. No second key list
    is published from here for that: the frozen source declares one, and a
    second would be a key composition with nothing behind it.

    NO ARITHMETIC AND NO CONVERSION HAPPEN HERE. `gl071` "contains no
    arithmetic at all" (Agent Action Plan section 0.4.1.2), and neither does
    this: records are carried across the two boundaries by group move between
    field-identical descriptions [general/gl071.cbl:L112-L144], so no value is
    truncated, padded, re-scaled, re-signed or rounded. In particular a
    negative amount arrives negative and at scale 2, which is the ordinary case
    [general/gl070.cbl:L517].

    `using` AND `giving` MAY BE THE SAME SEQUENCE without loss, because every
    record is read out of `using` before `giving` is opened for output. No
    phase of this cycle does that - `gl071` names two different files
    [general/gl071.cbl:L177-L178] - and it is noted as a property of the order
    of operations rather than offered as a facility.

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
    #
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
    #
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
    #
    # The ordering itself, and the ONLY thing about this statement that changes
    # the sequence. Stability is guaranteed by the callee and cannot be
    # switched off - see STABILITY IS CORRECTNESS above and
    # [general/gl072.cbl:L410-L412].
    ordered = sort_records(sort_trans.records, on_ascending_key)

    # The merge leaves the sort description holding the ordered stream. Written
    # back through the published verbs rather than by reaching into the
    # sequence's state, so there is one way for a record to enter a work file.
    sort_trans.open_output()
    for ordered_record in ordered:
        sort_trans.write(ordered_record)
    sort_trans.close()

    # 178  giving post-trans.
    #
    # The implicit RETURN and WRITE of every sorted record into the output
    # file, then the implicit close. `open_output` discards whatever the output
    # file held before, which is what `OPEN OUTPUT` on a line sequential file
    # does and what makes a second run of a phase start from an empty stream.
    giving.open_output()
    for ordered_record in ordered:
        giving.write(_group_move(ordered_record, giving.record_type))
    giving.close()
