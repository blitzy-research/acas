"""88-level condition names: the frozen value sets, and predicates over them.

This module is the ONE place in the Python migration where the `88`-level value
sets of the in-scope COBOL record layouts are written down. It carries each
condition name under its original COBOL spelling, the value clause exactly as
declared, the conditional variable that owns it, and the copybook line that
declares it - and it publishes predicates that answer, for one value, whether
that condition name holds.

Agent Action Plan section 0.3.1 fixes this file in one line, verbatim:

    condition_names.py (88-level predicates: Status-Open, Waiting, GL-Batch,
    IRS-Used, ...)

Agent Action Plan section 0.4.1.4 gives the transformation row, verbatim:

    | acas_posting/cobol/condition_names.py | CREATE |
    | copybooks/wsfnctn.cob + copybooks/wsbatch.cob + copybooks/wssystem.cob |
    | Predicates for the 88-levels the cycle tests: the function codes and
    | access types [copybooks/wsfnctn.cob:L88-L118], the batch status names,
    | and the IRS fan-out names [copybooks/wssystem.cob:L179-L181] |

Agent Action Plan section 0.1.2, transformation rule 12, verbatim:

    | 12 | `88`-level condition name | Predicate function over the record |
    | e.g. `Status-Open`, `Waiting`, `GL-Batch`, `IRS-Used` |

THIS MODULE DECIDES NOTHING
===========================
Agent Action Plan section 0.3.1, verbatim: "`cobol/` contains no business logic
and `programs/` contains no numeric primitives." Section 0.1.2 says this
package "contains no business logic whatsoever."

So every function below answers exactly one question - does this value satisfy
this condition name? - and no function decides what to do about the answer.
There is no posting rule here, no routing table from a function code to an
action, no run-ending gate, and no branch on an accounting outcome. Those
belong to `acas_posting.programs` and `acas_posting.dal`. What this module
supplies is the mechanism COBOL gave away for free: a name for a value set, and
a test against it.

THE COUNT, AND HOW IT IS COMPOSED  (rule R-5)
=============================================
`CONDITION_NAMES` holds 106 entries. Verified twice - once by reading the
frozen copybooks (`grep -cE '^ +88 ' <file>`) and once against
data_dictionary/acas_posting_dictionary.json, which records condition names
per copybook file and agrees entry for entry:

    copybooks/wsfnctn.cob    30    the operation vocabulary
    copybooks/wsbatch.cob     8    the ledger, batch and cleared statuses
    copybooks/wssystem.cob   60    the system record, IRS fan-out included
    copybooks/wssl.cob        8    the sales ledger's own switches
                            ---
                            106

`COUNTS_BY_COPYBOOK` publishes that breakdown as data, so the composition can
be checked rather than taken on trust.

TWO READINGS OF THE FROZEN SOURCE THAT DIFFER FROM THE PLAN'S CITATIONS
=======================================================================
Both were settled by reading the frozen file, which outranks any citation of
it. Recorded here so that a later reader does not chase the plan's numbers.

1.  `copybooks/wsfnctn.cob` is 117 lines long, so the plan's
    `[copybooks/wsfnctn.cob:L88-L118]` names a line one past end of file. The
    operation vocabulary really spans L88-L116: `03 File-Function pic 99.` at
    L88 with its fifteen condition names at L89-L105, then
    `03 Access-Type pic 9.` at L107 with its nine at L108-L116. Every locator
    in the registry below is the entry's own line, taken from the file.

2.  Four of the File-Function locators sit one line later than the plan's
    working note states, because L98, L101 and L106 are `*>` comment lines:
    `fn-Read-By-Name` is at L102 (not L101), `fn-Read-By-Batch` at L103,
    `fn-Read-By-Cust` at L104 and `fn-Read-Next-Header` at L105.

A third reading is a count rather than a line: the plan's note describes ONE
`88` in `copybooks/wssl.cob`, at L67. The file declares EIGHT, at L26, L27,
L29, L31, L33, L35, L37 and L67, and the generated dictionary records eight
for that file too. All eight are registered. The plan's own justification for
including L67 - that it is a live `88` in an in-scope record, and that leaving
it out would open a traceability hole - applies word for word to the other
seven, and registering one of eight from a single copybook would BE the hole.

THE SIX SHAPES A VALUE CLAUSE TAKES
===================================
All six occur in the in-scope layouts, and `ConditionKind` names five of them
(a contiguous list and a gapped list are one shape mechanically, and are told
apart by their values, never by being rewritten):

    SINGLE        `88  G-L  value 1.`                 [wssystem.cob:L85]
    FIGURATIVE    `88  No-OS  value zero.`            [wssystem.cob:L102]
    VALUE_LIST    `88  valid-os-type  values 1 2 3 4 5 6.`
                                                      [wssystem.cob:L101]
    VALUE_LIST    `88  OS-Single  values 1 2 4.`      [wssystem.cob:L109]
                  GAPPED. 3 is NOT a member. It must never become a range.
    THRU_RANGE    `88  FS-Valid-Options  values 0 thru 1.`
                                                      [wssystem.cob:L122]
                  Inclusive on BOTH bounds.
    ALPHANUMERIC  `88  Auto-Vat  value "Y".`          [wssystem.cob:L174]

A figurative `zero` reads as the number 0, so `No-OS` holds for 0 and for the
text "0". An alphanumeric comparison is case-SENSITIVE and space-padded, which
is what COBOL does; see `evaluate` for the question that records.

A NON-MATCHING VALUE IS False, NEVER AN ERROR  (rule R-3)
=========================================================
COBOL has no notion of an unknown value here. A `pic 9` field holding 7 simply
fails every condition name declared on it, silently, and the program carries
on. So `evaluate` returns False for such a value: it does not raise, does not
warn, and offers no "unrecognised value" sentinel a caller could branch on.
Handing a caller anything other than False would let a program module take a
branch the compiled original never takes, which is the exact failure mode rules
R-3 and R-4 exist to prevent. The compiled cycle makes the point itself: where
`general/gl072.cbl` needs to know that a value is unusable it tests for that
explicitly, at L291-L292 - `if post-batch not numeric / go to loop.` - rather
than leaning on a comparison to tell it.

Two failures are still raised, and neither is about a data value:

    TypeError   a `float` or `complex` comparison operand. This is the rule R-2
                type gate described below, not a validation of data.
    KeyError    a condition name this registry does not declare. That is a
                programmer naming a name that does not exist, which no input
                can cause.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
    MAY import       `acas_posting.cobol.field`, the `acas_posting.dictionary`
                     public surface (`loader` and `model`), and the standard
                     library.
    MUST NOT import  `acas_posting.records`, `acas_posting.dal`,
                     `acas_posting.programs`, `acas_posting.cli`,
                     `acas_posting.clock`, `acas_posting.dates`,
                     `acas_posting.workfiles`, the sibling compiled-oracle
                     tree, and the sibling semantics modules `picture`,
                     `usage`, `arithmetic`, `move` and `sortverb`.
    No third-party import anywhere. Python is pinned to `==3.12.*`.

CONFLICT 1 - "PREDICATE OVER THE RECORD", FROM A PACKAGE THAT CANNOT SEE ONE
============================================================================
Transformation rule 12 asks for a predicate over the record; section 0.4.3
forbids this package from importing `acas_posting.records`. Both bind, so the
tension is settled by where each half lives:

    Here          the predicates are VALUE-level. `is_status_open(value)` takes
                  the field's value, and optionally the `FieldDescriptor` that
                  describes the field, and never a record object.
    records/*.py  exposes them as record-level properties. `records/gl_batch.py`
                  already imports `acas_posting.cobol.field`, so it defines a
                  property returning `condition_names.is_status_open(
                  self.batch_status)`.

The predicate over the record therefore exists, at the layer that has the
record, and this package stays a leaf. DO NOT "fix" this by importing the
record layer here; that would create the cycle section 0.4.3 forbids.

CONFLICT 2 - THIS FILE IS THE REGISTRY; `dal/status.py` PUBLISHES THE ENUMS
===========================================================================
Section 0.4.1.4 says this file supplies "the function codes and access types",
while section 0.5.3 says, verbatim: "Every `COPY` of the function-code copybook
becomes two imports - the record classes from `records/file_access.py`, and the
status and vocabulary enumerations from `dal/status.py` - because the single
COBOL copybook mixes data layout with operation vocabulary and the Python
layering separates them." The split that satisfies both:

    this module      the single declarative REGISTRY. The values are
                     transcribed from the frozen copybook exactly once, here,
                     each with its own locator, plus the predicates over them.
    dal/status.py    the call-site ENUMERATIONS. It should BUILD its members
                     from this registry - `values_for` and `specs_for_variable`
                     exist for precisely that - rather than transcribing
                     fifteen out-of-order function codes a second time. A
                     second transcription is the class of error rule R-5 exists
                     to prevent.

The dependency runs one way, from the data-access layer toward this one, so no
cycle appears. Accordingly this module does not import the data-access layer,
and it deliberately defines no type under the names that layer uses for its
three enumerations. Those names belong to `dal/status.py`; a duplicate here
would collide with it at every call site that imports both.

The vocabulary really is the facade's, which is why the registry is worth its
weight: `SET fn-* TO TRUE` appears 302 times in
`copybooks/Proc-ACAS-FH-Calls.cob` and 56 times in
`copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob`.

`Fs-Reply` HAS NO CONDITION NAMES, AND THAT IS A VERIFIED ZERO
==============================================================
`03 Fs-Reply pic 99.` at [copybooks/wsfnctn.cob:L25] declares no `88` at all -
not one, anywhere in the frozen tree. Its value set, 0 / 10 / 21 / 22 / 23 /
99, is described by Agent Action Plan section 0.4.1.5 as belonging entirely to
`dal/status.py`, alongside the `We-Error` codes and the SQLSTATE mapping. The
zero is recorded here so the absence reads as measured rather than overlooked.
No condition name has been invented to fill it, and none may be: rule R-3
forbids adding a condition name the frozen copybooks do not declare.

WHAT THE ANOMALIES REQUIRE OF THIS FILE  (rule R-4)
===================================================
Agent Action Plan section 0.8.2, preserved verbatim from the user's own
requirements: "There is no test suite: compiled COBOL execution is the
behavioral specification, defects included. A defect reproduced is correct; a
defect fixed is a failure." Section 0.7.4 asks for a comment at each
reproduction site citing the COBOL locator, and there is one.

1.  THE FUNCTION CODES ARE DECLARED OUT OF NUMERIC ORDER, AND STAY THAT WAY.
    `88 fn-Write-Raw value 15.` is declared at [copybooks/wsfnctn.cob:L99] and
    `88 fn-Read-Next-Raw value 13.` at [copybooks/wsfnctn.cob:L100] - fifteen
    BEFORE thirteen - so the declaration sequence runs
    1 2 3 4 5 6 7 8 9 15 13 31 32 33 34. The maintainer's own file header
    explains it at [copybooks/wsfnctn.cob:L14-L15]: "Oops, previous chg should
    have been for File-Function. / next-read-raw changed to 13." The registry
    is in DECLARATION order, not value order, and `dal/status.py` builds its
    members from that order - so tidying the sequence here would silently
    reorder an enumeration there.

2.  ONE CONDITION NAME IS DECLARED AND NEVER TESTED, AND IT IS KEPT.
    `88 Date-Valid-Formats values 1 2 3.` at [copybooks/wssystem.cob:L132]
    exists, and the date wrapper sections ignore it: they test the conditional
    variable against a figurative constant instead, at
    [general/gl070.cbl:L583-L584] - `if Date-Form = zero / move 1 to
    Date-Form.` - and then test `Date-UK` at [general/gl070.cbl:L585] and
    `Date-USA` at [general/gl070.cbl:L587]. Searching the four in-scope
    programs `general/gl070.cbl`, `general/gl072.cbl`, `sales/sl060.cbl` and
    `irs/irs030.cbl` for the name returns zero occurrences. The folder
    requirement is verbatim: "Model the predicate for traceability, but do not
    make the code use a test the COBOL ignores." So it is registered, its
    predicate is published, and nothing in this package or above it calls it.
    The same measurement shows `Date-Intl` at [copybooks/wssystem.cob:L131] is
    never tested either - the wrapper falls through to the international form
    without naming it - and it is registered on the same footing.

3.  THE IRS FAN-OUT IS A THREE-STATE SWITCH, AND THE THIRD STATE HAS NO NAME.
        copybooks/wssystem.cob:L179       05  IRS-Instead     pic x.
        copybooks/wssystem.cob:L180           88  IRS-Used        value "Y".
        copybooks/wssystem.cob:L181           88  IRS-Both-Used   value "B".
    The third state is space, and for space BOTH predicates are False. There is
    no third condition name and inventing one would breach rule R-3. This
    matters to database state, not presentation: Agent Action Plan section
    0.6.4 records that the switch "is tested at three sites in each of the four
    Sales and Purchase posting programs" and that "The scenario definitions
    must therefore pin this switch explicitly, since leaving it at a default
    would make the affected-table list ambiguous." Reading `sales/sl060.cbl`
    finds the two names tested at seven sites in that one program - L1039,
    L1046, L1126, L1144, L1172, L1175 and L1177 - of which the plan's three,
    L1039, L1126 and L1175, are the `IRS-Used OR IRS-Both-Used` shape, L1046,
    L1172 and L1177 are `IRS-Both-Used or G-L`, and L1144 tests
    `IRS-Both-Used` alone.

4.  TWO CONDITION NAMES SHARE ONE VALUE ON ONE FIELD.
    `88 FS-MySql-Used value 1.` at [copybooks/wssystem.cob:L114] and
    `88 FS-RDBMS-Used value 1.` at [copybooks/wssystem.cob:L116] are both
    declared on `File-System-Used`, both with value 1, so each holds exactly
    when the other does. Both are registered as declared.

5.  COMMENTED-OUT CONDITION NAMES ARE NOT REGISTERED.
    [copybooks/wsfnctn.cob:L76-L80] and [copybooks/wssystem.cob:L117-L121] each
    carry five `88` declarations behind a `*>`, for storage engines the
    maintainer marks "THESE NOT IN USE". A comment declares nothing, so none of
    the ten appears here - and none has been deleted from the frozen file
    either.

ANOMALY A-15, RECORDED AND LEFT UNSETTLED  (rule R-4)
=====================================================
The batch record's declared length contradicts the sum of its fields. The
maintainer says so himself, at [copybooks/wsbatch.cob:L7-L9], quoted verbatim:

    *> 96 bytes 26/03/09
    *> 98 bytes 20/12/11 (no, dont understand as I count 96)
    *>   but function length (Batch-record) says 98?

Agent Action Plan section 0.6.8 lists it among the questions only the compiled
program can settle, because which of the two governs the record actually read
changes the alignment of the trailing fields. Nothing in this module settles
it. The three batch groups are registered from the `88` lines themselves,
which no reading of the record length moves.

A NAMING TRAP WORTH READING BEFORE RUNNING ANY SEARCH
=====================================================
Four condition names in `copybooks/wssystem.cob` begin with `Stock`:

    88  Stock                  value 1.    [copybooks/wssystem.cob:L91]
    88  Stock-Audit-On         value "Y".  [copybooks/wssystem.cob:L244]
    88  Stock-Control-Exists   value "Y".  [copybooks/wssystem.cob:L301]
    88  Stock-Averaging        value 1.    [copybooks/wssystem.cob:L303]

They are in-scope SYSTEM-REC condition names, and they are NOT the out-of-scope
table and bridge identifiers Agent Action Plan section 0.2.2 excludes. A search
for the substring "stock" will hit all four; a search for the excluded
identifiers themselves will hit none of them. Match whole identifiers.

ORDER IS OBSERVABLE, SO THERE IS NO `set` HERE  (rule R-6)
==========================================================
`dal/status.py` builds enumeration members from this registry, and an
enumeration's member order is observable, so an ordering here is behaviour. A
value list is a `tuple` in declaration order. The registry is a `tuple`.
`BY_COBOL_NAME` and `COUNTS_BY_COPYBOOK` are read-only mapping proxies over
insertion-ordered dictionaries. Nothing in this module is a `set`, a
`frozenset`, or a mutable list a caller could reorder in place; nothing reads a
clock, an entropy source or the process environment; and every ordered
accessor returns a tuple built by walking `CONDITION_NAMES`, never by
iterating a mapping.

ZERO BINARY FLOATING POINT  (rule R-2, verbatim)
================================================
    "No accounting value may pass through a binary floating-point type at any
    point - not in computation, not in storage, not in transport."

Rule R-2 forces the whole of `acas_posting/cobol/*.py` into scope, this file
included. Every value in the registry is carried as `str`, matching
`model.ConditionName.value`, and read as an exact `decimal.Decimal` only at the
moment of comparison. A `float` or `complex` operand is refused with a
`TypeError` rather than compared, because 0.1 cannot be a COBOL `pic 9` value
and rounding one into the nearest integer would invent an answer. That refusal
is a type gate, not a validation of data: it fires on the operand's TYPE, which
no legitimate caller and no database column can produce - the frozen schema
declares zero FLOAT, DOUBLE and REAL columns. `math`, `round`, `pandas` and
`numpy` appear nowhere.

NO COBOL AT RUNTIME  (rule R-1)
===============================
The registry is Python source. This module never launches a process, never
loads a foreign library, and never reads a `.cob` file - not at import time and
not later. The values were transcribed by hand from the frozen copybooks and
carry their locators as data and as comments, so the shipped package runs on a
host with no COBOL compiler and no COBOL runtime present, and with the
`copybooks/` tree absent altogether. Importing this module performs no I/O of
any kind. `cross_check_against_dictionary` is the only function that reads a
file, it reads the generated JSON dictionary rather than any COBOL, it is never
called at import time, and it fails soft.

SEQUENTIAL  (rule R-3)
======================
Nothing here starts a thread, an event loop or a process pool. Every function
is an ordinary synchronous function, matching the single-threaded COBOL.

VOCABULARY THIS MODULE MUST NOT PUBLISH  (rule R-4)
===================================================
No name, and no member meaning, may be `resolved`, `canonical`, `effective`,
`authoritative`, `corrected`, `recommended`, `preferred`, `normalise` or
`normalize`. Where the frozen source is odd, the registry records the oddity
and stops. This paragraph is the one place those words appear, and it appears
so that the prohibition is legible rather than folklore.

THE FREEZE  (Agent Action Plan section 0.8.1, verbatim)
=======================================================
    "Any diff touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`,
    `general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or
    `mysql/ACASDB.sql` is a defect in the migration, regardless of how harmless
    it appears."

Every copybook and program named in this module was read as specification. None
was modified.

FURTHER READING
===============
    docs/migration/traceability.md   is built from this registry: every
                                     `88`-level in the migrated cycle is
                                     findable here by its original COBOL name.
    docs/migration/anomaly-log.md    the register of legacy defects reproduced.
    docs/migration/ambiguity-resolutions.md
                                     the questions only the compiled program
                                     settles, A-15 among them.
"""

from __future__ import annotations

import dataclasses
import decimal
import enum
import types
from typing import TYPE_CHECKING, Callable, Final, Mapping

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader, model

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from pathlib import Path


# =============================================================================
#  THE SHAPE OF A VALUE CLAUSE
# =============================================================================


class ConditionKind(enum.StrEnum):
    """The shape of the VALUE clause a condition name is declared with.

    Five members, one per shape the in-scope layouts actually use. A contiguous
    list and a gapped list share `VALUE_LIST`, because mechanically they are the
    same construct - a run of literals - and telling them apart by collapsing
    the contiguous one into a range would lose the declaration. `OS-Single` at
    [copybooks/wssystem.cob:L109] is the reason that matters: its members are
    1, 2 and 4, and 3 is not one of them.

    A `StrEnum` so the member is its own text, which keeps a kind readable in a
    traceability table without a lookup, exactly as the dictionary object model
    does for its own enumerations.

    Attributes:
        SINGLE: One numeric literal. `88 G-L value 1.`
            [copybooks/wssystem.cob:L85]
        FIGURATIVE: One figurative constant, spelled as the copybook spells it.
            The only one used is `zero`, which reads as the number 0.
            `88 No-OS value zero.` [copybooks/wssystem.cob:L102]
        VALUE_LIST: Two or more numeric literals, contiguous or gapped. Tested
            by membership, never by range. `88 valid-os-type values 1 2 3 4 5
            6.` [copybooks/wssystem.cob:L101] and `88 OS-Single values 1 2 4.`
            [copybooks/wssystem.cob:L109]
        THRU_RANGE: A `thru` range, INCLUSIVE on both bounds. `88
            FS-Valid-Options values 0 thru 1.` [copybooks/wssystem.cob:L122]
        ALPHANUMERIC: One quoted literal, its delimiters kept in the recorded
            value so a one-character switch is unambiguous. `88 Auto-Vat value
            "Y".` [copybooks/wssystem.cob:L174]
    """

    SINGLE = "SINGLE"
    FIGURATIVE = "FIGURATIVE"
    VALUE_LIST = "VALUE_LIST"
    THRU_RANGE = "THRU_RANGE"
    ALPHANUMERIC = "ALPHANUMERIC"


# Short private aliases, bound once. The registry below is 106 entries long and
# reads as a table; spelling the enumeration out in full on every row would
# push the locator off the line, and the locator is the point of the row.
_SINGLE: Final[ConditionKind] = ConditionKind.SINGLE
_FIG: Final[ConditionKind] = ConditionKind.FIGURATIVE
_LIST: Final[ConditionKind] = ConditionKind.VALUE_LIST
_THRU: Final[ConditionKind] = ConditionKind.THRU_RANGE
_ALNUM: Final[ConditionKind] = ConditionKind.ALPHANUMERIC

# The four frozen copybooks the registry is transcribed from, as
# repository-relative paths spelled the way the generated dictionary spells
# them, so a locator built here and one read from the dictionary compare
# equal without either side being touched.
_WSFNCTN: Final[str] = "copybooks/wsfnctn.cob"
_WSBATCH: Final[str] = "copybooks/wsbatch.cob"
_WSSYSTEM: Final[str] = "copybooks/wssystem.cob"
_WSSL: Final[str] = "copybooks/wssl.cob"

# The figurative constants a VALUE clause may use, mapped to the number each
# one reads as. Only `zero` occurs in the in-scope layouts - in six places, at
# [copybooks/wsfnctn.cob:L74], [copybooks/wssystem.cob:L94],
# [copybooks/wssystem.cob:L102], [copybooks/wssystem.cob:L113],
# [copybooks/wssystem.cob:L134] and [copybooks/wssl.cob:L27] - and its three
# spellings are the ones COBOL allows for the same constant. A read-only proxy,
# so no caller can teach this module a constant the frozen source never used.
_FIGURATIVE_NUMBERS: Final[Mapping[str, int]] = types.MappingProxyType(
    {
        "zero": 0,
        "zeros": 0,
        "zeroes": 0,
    }
)

# The delimiters COBOL accepts around an alphanumeric literal. Every in-scope
# `88` uses the double quote; the apostrophe is accepted when reading a
# recorded value because the language accepts it and a future transcription
# should not have to care which the copybook chose.
_LITERAL_DELIMITERS: Final[tuple[str, ...]] = ('"', "'")


# =============================================================================
#  ONE REGISTRY ENTRY
# =============================================================================


@dataclasses.dataclass(frozen=True, slots=True)
class ConditionNameSpec:
    """One `88`-level condition name, exactly as the frozen copybook declares it.

    Frozen and slotted for the same reasons the sibling value objects are: a
    spec is compared by value, may be used as a mapping key, and must not be
    mutated by a caller that received it from the registry.

    EVERY SPEC CARRIES ITS OWN LINE  (rule R-5)
    -------------------------------------------
    `locator` names the line that declares THIS condition name, not the line
    that declares its group and not a span. docs/migration/traceability.md is
    built from these, and a reader following a name back to the frozen source
    must land on the declaration itself.

    THE ORIGINAL SPELLING IS DATA  (rule R-5)
    -----------------------------------------
    `cobol_name` preserves the maintainer's own capitalisation, inconsistencies
    included - `fn-open` all lower at [copybooks/wsfnctn.cob:L89],
    `fn-Delete-All` mixed at [copybooks/wsfnctn.cob:L94], `fn-re-write` lower
    at [copybooks/wsfnctn.cob:L95], `FA-FS-Cobol-Files-Used` upper at
    [copybooks/wsfnctn.cob:L74] and `valid-os-type` lower at
    [copybooks/wssystem.cob:L101]. Lookup by the COBOL name therefore works
    with the spelling a reader copied out of the copybook.

    Attributes:
        cobol_name: The condition name verbatim, its case preserved.
        python_name: The snake_case predicate name for it, DERIVED from
            `cobol_name` by lowercasing, turning each hyphen into an
            underscore and prefixing `is_`. Derived rather than transcribed so
            that 106 rows offer no chance to mistype one, and so a name and its
            predicate can never disagree. Every one of the 106 derives to a
            valid Python identifier.
        values: The literals of the VALUE clause, as separate tokens, in
            declaration order, each carried as `str` (rule R-2). An
            alphanumeric literal keeps its delimiters, so `Auto-Vat` holds
            `('"Y"',)`; a figurative constant keeps its spelling, so `No-OS`
            holds `('zero',)`; and a numeric literal keeps its digits, so
            `Date-Valid-Formats` holds `('1', '2', '3')`. A `THRU_RANGE` holds
            exactly two, the lower bound then the upper.
        kind: The shape of the clause.
        conditional_variable: The COBOL name of the field the condition name is
            declared on - its conditional variable - taken from the generated
            dictionary, which records which field owns each condition name.
        copybook: The repository-relative path of the declaring copybook.
        locator: `<copybook>:L<line>` for this entry's own declaration.
        declaration_index: This entry's zero-based position among the condition
            names of its conditional variable, in DECLARATION order. It is what
            makes the out-of-numeric-order function codes checkable: index 9 is
            `fn-Write-Raw` (value 15) and index 10 is `fn-Read-Next-Raw`
            (value 13).
        notes: Free prose recording what a reader needs to know about this
            entry - that it is never tested, that its value duplicates a
            sibling's, that the declaration order is not the numeric order.
            Empty when there is nothing to record.
    """

    cobol_name: str
    python_name: str
    values: tuple[str, ...]
    kind: ConditionKind
    conditional_variable: str
    copybook: str
    locator: str
    declaration_index: int
    notes: str

    @property
    def value_clause_text(self) -> str:
        """The VALUE clause text, rebuilt from `values` and `kind`.

        DERIVED, not stored, so it cannot drift from `values`. The rebuilt text
        is byte-identical to `model.ConditionName.value` for all 106 entries,
        which is what lets `cross_check_against_dictionary` compare the two
        sources without either being touched:

            SINGLE, FIGURATIVE, ALPHANUMERIC  the one token
            VALUE_LIST                        the tokens joined by one space
            THRU_RANGE                        `<lower> thru <upper>`

        Returns:
            The clause text, for example `"1 2 4"`, `"0 thru 1"`, `"zero"` or
            `'"Y"'`.
        """
        if self.kind is ConditionKind.THRU_RANGE:
            return self.values[0] + " thru " + self.values[1]
        return " ".join(self.values)

    @property
    def is_alphanumeric(self) -> bool:
        """Whether the clause is a quoted literal rather than a number.

        Returns:
            True for `ALPHANUMERIC`, False for every numeric shape.
        """
        return self.kind is ConditionKind.ALPHANUMERIC

    @property
    def declaration_text(self) -> str:
        """The `88` line rebuilt in COBOL form, for a report or a log line.

        `values` for a list clause is written with the plural keyword the
        copybook uses, and a range likewise, because that is how the frozen
        line reads.

        Returns:
            For example `88  OS-Single  values 1 2 4.`
        """
        keyword = "value" if len(self.values) == 1 else "values"
        head = "88  " + self.cobol_name + "  "
        return head + keyword + " " + self.value_clause_text + "."

    def cite(self) -> str:
        """The locator, for quoting in a message, a comment or a document.

        Named `cite` to match `FieldDescriptor.cite` and `loader.cite`, so one
        habit works across the whole migration.

        Returns:
            `<copybook>:L<line>`, for example `copybooks/wsbatch.cob:L26`.
        """
        return self.locator

    def literal_text(self) -> str:
        """The characters inside an alphanumeric literal, delimiters removed.

        This reads the literal's content the way the compiler does when it
        compares a quoted literal with an alphanumeric item: the delimiters
        belong to the source text, not to the value. `'"Y"'` reads as `Y`.

        Only meaningful for an `ALPHANUMERIC` spec. For any numeric shape the
        token is returned unchanged, so a caller that asks anyway gets the
        digits rather than an exception.

        Returns:
            The literal's characters.
        """
        token = self.values[0]
        for delimiter in _LITERAL_DELIMITERS:
            if (
                len(token) >= 2
                and token.startswith(delimiter)
                and token.endswith(delimiter)
            ):
                return token[1:-1]
        return token

    def numeric_values(self) -> tuple[decimal.Decimal, ...]:
        """The clause's literals as exact decimals, in declaration order.

        A figurative constant reads as the number it stands for, so `zero`
        yields `Decimal(0)` and compares equal to a field holding 0 - which is
        why [copybooks/wsbatch.cob:L26] writing `value 0` and
        [copybooks/wssl.cob:L27] writing `value zero` behave identically while
        both stay recorded as written (rule R-4).

        `decimal.Decimal` rather than `int` because rule R-2 admits no binary
        floating point anywhere and an exact decimal is the type the rest of
        this package compares with. Construction from a digit string is exact
        and takes no rounding decision, so no context is consulted.

        Returns:
            The literals as decimals.

        Raises:
            ValueError: The spec is alphanumeric, so its literal is text and
                has no numeric reading. A programmer error - `kind` states the
                shape - and never reachable from a data value.
        """
        if self.kind is ConditionKind.ALPHANUMERIC:
            raise ValueError(
                "Condition name " + repr(self.cobol_name) + " at " + self.locator
                + " is declared with an alphanumeric literal, "
                + repr(self.values[0])
                + ", so it has no numeric reading. Compare it as text; "
                + "`kind` and `is_alphanumeric` state the shape."
            )
        return tuple(_read_number(token) for token in self.values)


# =============================================================================
#  READING A RECORDED LITERAL
# =============================================================================


def _read_number(token: str) -> decimal.Decimal:
    """Read one recorded numeric literal as an exact decimal.

    A figurative constant is looked up; anything else is read as digits. Exact
    in both directions and free of any rounding decision, so no `decimal`
    context is consulted (rule R-2, rule R-6).

    Args:
        token: The literal as the registry records it, for example `"15"` or
            `"zero"`.

    Returns:
        Its numeric reading.

    Raises:
        ValueError: The token is neither a figurative constant this module
            knows nor a number. Unreachable from the registry, which is closed
            and checked, and unreachable from a data value, which never
            travels through here.
    """
    figurative = _FIGURATIVE_NUMBERS.get(token.casefold())
    if figurative is not None:
        return decimal.Decimal(figurative)
    return decimal.Decimal(token)


def _read_operand(value: int | str | decimal.Decimal) -> decimal.Decimal | None:
    """Read a caller's value as an exact decimal, or report that it does not read.

    Returning None rather than raising is rule R-3 in one line: a `pic 9` field
    holding spaces satisfies no condition name, and COBOL says so by failing the
    comparison, not by stopping. The compiled cycle handles that case with an
    explicit test of its own where it needs to - `if post-batch not numeric` at
    [general/gl072.cbl:L291-L292] - so this module must not invent a louder
    answer.

    `bool` arrives here as an `int`, which is what Python makes it, and reads as
    1 or 0.

    Args:
        value: The caller's value. A `float` or `complex` never reaches this
            function; `evaluate` refuses those first.

    Returns:
        The value as an exact decimal, or None when it has no numeric reading.
    """
    if isinstance(value, decimal.Decimal):
        # A quiet NaN would compare unequal to everything, which is the right
        # answer, but a signalling one raises on comparison - so it is reported
        # as not reading rather than allowed through.
        return None if not value.is_finite() else value
    if isinstance(value, int):
        return decimal.Decimal(value)
    try:
        read = decimal.Decimal(value.strip())
    except (ArithmeticError, ValueError, AttributeError):
        return None
    return None if not read.is_finite() else read


def _pad(text: str, width: int) -> str:
    """Space-pad text on the right to a width, the way COBOL compares.

    An alphanumeric comparison in COBOL treats the shorter operand as though it
    were padded on the right with spaces to the length of the longer. Every
    alphanumeric conditional variable in the in-scope layouts is `pic x`, one
    character wide, so this is a no-op for all 24 of them - it is written
    faithfully anyway, because a caller may hold a wider field's value and
    getting the rule right costs nothing.

    Args:
        text: The operand.
        width: The width to pad to.

    Returns:
        The operand, padded if it was shorter.
    """
    return text if len(text) >= width else text + " " * (width - len(text))


# =============================================================================
#  BUILDING ONE REGISTRY ROW
# =============================================================================


def _spec(
    cobol_name: str,
    values: tuple[str, ...],
    kind: ConditionKind,
    conditional_variable: str,
    copybook: str,
    line: int,
    declaration_index: int,
    notes: str = "",
) -> ConditionNameSpec:
    """Build one registry row, deriving the predicate name and the locator.

    Two members are DERIVED here rather than written 106 times, which removes
    106 chances to mistype one and makes it impossible for a name and its
    locator to disagree with the row they sit on:

        python_name  `is_` + the COBOL name lowercased with hyphens turned into
                     underscores. `fn-Delete-All` yields `is_fn_delete_all`;
                     `G-L` yields `is_g_l`; `Date-Valid-Formats` yields
                     `is_date_valid_formats`.
        locator      `<copybook>:L<line>`.

    Args:
        cobol_name: The condition name verbatim, its case preserved.
        values: The clause's literals as separate tokens, in declaration order.
        kind: The shape of the clause.
        conditional_variable: The COBOL name of the owning field.
        copybook: The declaring copybook's repository-relative path.
        line: The line in that copybook that declares THIS condition name.
        declaration_index: Zero-based position among its group's condition
            names, in declaration order.
        notes: What a reader needs to know about this row, if anything.

    Returns:
        The row.
    """
    return ConditionNameSpec(
        cobol_name=cobol_name,
        python_name="is_" + cobol_name.casefold().replace("-", "_"),
        values=values,
        kind=kind,
        conditional_variable=conditional_variable,
        copybook=copybook,
        locator=copybook + ":L" + str(line),
        declaration_index=declaration_index,
        notes=notes,
    )


# =============================================================================
#  THE REGISTRY  (rule R-5: every row carries its own line)
# =============================================================================
#
# 106 rows: 30 from copybooks/wsfnctn.cob, 8 from copybooks/wsbatch.cob, 60
# from copybooks/wssystem.cob and 8 from copybooks/wssl.cob. Grouped by
# conditional variable in FILE order, and within each group in DECLARATION
# order - which for the function codes is not numeric order.
#
# Row columns, in order:
#     COBOL name | value tokens | shape | conditional variable | copybook |
#     line | index within group | notes
#
# A tuple, not a list and not a set: an ordering here is behaviour, because
# `dal/status.py` builds enumeration members from it (rule R-6).

CONDITION_NAMES: Final[tuple[ConditionNameSpec, ...]] = (
    # =========================================================================
    #  copybooks/wsfnctn.cob - 30 rows. The file is 117 lines long, so the
    #  plan's L88-L118 citation of the vocabulary names a line past its end;
    #  the vocabulary spans L88-L116.
    # =========================================================================
    #
    # --- 03  Main-Record-Move-Flag pic 9 value zero.  [wsfnctn.cob:L66] ------
    # Which copy of the record the bridge is to take, the FD's or working
    # storage's. The maintainer's own note at [copybooks/wsfnctn.cob:L64] says
    # "NOT YET USED".
    _spec(
        "MRMF-Move-FD", ("1",), _SINGLE,
        "Main-Record-Move-Flag", _WSFNCTN, 67, 0,
        "Declared with the maintainer's note NOT YET USED at "
        "[copybooks/wsfnctn.cob:L64].",
    ),
    _spec(
        "MRMF-Move-WS", ("2",), _SINGLE,
        "Main-Record-Move-Flag", _WSFNCTN, 68, 1,
        "Declared with the maintainer's note NOT YET USED at "
        "[copybooks/wsfnctn.cob:L64].",
    ),
    #
    # --- 07  FA-File-System-Used  pic 9.  [wsfnctn.cob:L73] -----------------
    # Reaches the handler from the system record. Five further condition names
    # for other storage engines sit behind a `*>` at
    # [copybooks/wsfnctn.cob:L76-L80] under the heading "THESE NOT IN USE" - a
    # comment declares nothing, so none of the five is registered.
    _spec(
        "FA-FS-Cobol-Files-Used", ("zero",), _FIG,
        "FA-File-System-Used", _WSFNCTN, 74, 0,
        "Figurative constant. Reads as 0, so it holds for 0 and for the text "
        '"0".',
    ),
    _spec(
        "FA-FS-RDBMS-Used", ("1",), _SINGLE,
        "FA-File-System-Used", _WSFNCTN, 75, 1,
        "The generic name that replaced a per-engine one; the superseded "
        "FA-FS-MySql-Used sits behind a comment at "
        "[copybooks/wsfnctn.cob:L76].",
    ),
    _spec(
        "FA-FS-Valid-Options", ("0", "1"), _THRU,
        "FA-File-System-Used", _WSFNCTN, 81, 2,
        "A thru range, inclusive on both bounds. The trailing comment reads "
        '"5. (not in use unless 1-5)", so the range was narrowed from five '
        "options to two and the wider intent is recorded only in that "
        "comment.",
    ),
    #
    # --- 07  FA-File-Duplicates-In-Use  pic 9.  [wsfnctn.cob:L82] -----------
    _spec(
        "FA-FS-Duplicate-Processing", ("1",), _SINGLE,
        "FA-File-Duplicates-In-Use", _WSFNCTN, 83, 0,
        "The field's own comment at [copybooks/wsfnctn.cob:L82] reads "
        "\"NO LONGER USED other than for a '6' = rdb\" - and 6 is not one of "
        "the values any condition name on it declares.",
    ),
    #
    # --- 03  File-Function  pic 99.  [wsfnctn.cob:L88] ----------------------
    # The fifteen operation codes the facade paragraphs SET before calling a
    # handler. `SET fn-* TO TRUE` appears 302 times in
    # [copybooks/Proc-ACAS-FH-Calls.cob] and 56 times in
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob].
    _spec("fn-open", ("1",), _SINGLE, "File-Function", _WSFNCTN, 89, 0),
    _spec("fn-close", ("2",), _SINGLE, "File-Function", _WSFNCTN, 90, 1),
    _spec("fn-read-next", ("3",), _SINGLE, "File-Function", _WSFNCTN, 91, 2),
    _spec("fn-read-indexed", ("4",), _SINGLE, "File-Function", _WSFNCTN, 92, 3),
    _spec("fn-write", ("5",), _SINGLE, "File-Function", _WSFNCTN, 93, 4),
    _spec(
        "fn-Delete-All", ("6",), _SINGLE, "File-Function", _WSFNCTN, 94, 5,
        "Mixed capitalisation, kept as declared (rule R-5). Added 10/10/16 per "
        "the trailing comment.",
    ),
    _spec("fn-re-write", ("7",), _SINGLE, "File-Function", _WSFNCTN, 95, 6),
    _spec("fn-delete", ("8",), _SINGLE, "File-Function", _WSFNCTN, 96, 7),
    _spec("fn-start", ("9",), _SINGLE, "File-Function", _WSFNCTN, 97, 8),
    #
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # !!  THE NEXT TWO ROWS ARE OUT OF NUMERIC ORDER, AND MUST STAY SO.    !!
    # !!                                                                   !!
    # !!  15 is declared BEFORE 13:                                        !!
    # !!      88  fn-Write-Raw       value 15.   [copybooks/wsfnctn.cob:L99] !!
    # !!      88  fn-Read-Next-Raw   value 13.   [copybooks/wsfnctn.cob:L100]!!
    # !!                                                                   !!
    # !!  so the group's declaration sequence is                           !!
    # !!      1 2 3 4 5 6 7 8 9 15 13 31 32 33 34                          !!
    # !!                                                                   !!
    # !!  The maintainer explains it himself in the file header at          !!
    # !!  [copybooks/wsfnctn.cob:L14-L15]: "Oops, previous chg should have  !!
    # !!  been for File-Function. / next-read-raw changed to 13."           !!
    # !!                                                                   !!
    # !!  `dal/status.py` builds its enumeration members from this order,   !!
    # !!  and an enumeration's member order is observable, so sorting these !!
    # !!  two rows into numeric order would silently reorder that           !!
    # !!  enumeration. A DEFECT REPRODUCED IS CORRECT; A DEFECT FIXED IS A  !!
    # !!  FAILURE.                                        (rules R-4, R-6)  !!
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    _spec(
        "fn-Write-Raw", ("15",), _SINGLE, "File-Function", _WSFNCTN, 99, 9,
        "OUT OF NUMERIC ORDER: value 15 is declared at "
        "[copybooks/wsfnctn.cob:L99], BEFORE value 13 at "
        "[copybooks/wsfnctn.cob:L100], so the group runs "
        "1 2 3 4 5 6 7 8 9 15 13 31 32 33 34. Declaration order is preserved "
        "(rule R-4). Not SET anywhere in the frozen copybooks; it serves the "
        "*LD loader programs.",
    ),
    _spec(
        "fn-Read-Next-Raw", ("13",), _SINGLE, "File-Function", _WSFNCTN, 100, 10,
        "OUT OF NUMERIC ORDER: value 13 is declared at "
        "[copybooks/wsfnctn.cob:L100], AFTER value 15 at "
        "[copybooks/wsfnctn.cob:L99]. The trailing comment reads "
        '"14/11/16 - Special 4 LD." and the file header at '
        "[copybooks/wsfnctn.cob:L15] records the change: "
        '"next-read-raw changed to 13."',
    ),
    #
    # A `*>` comment at [copybooks/wsfnctn.cob:L101] separates the raw pair
    # from the by-name reads, which is why the next four sit at L102-L105 and
    # not at L101-L104 as the plan's working note states.
    _spec(
        "fn-Read-By-Name", ("31",), _SINGLE, "File-Function", _WSFNCTN, 102, 11,
        "L102, not L101: [copybooks/wsfnctn.cob:L101] is a comment line.",
    ),
    _spec(
        "fn-Read-By-Batch", ("32",), _SINGLE, "File-Function", _WSFNCTN, 103, 12,
    ),
    _spec(
        "fn-Read-By-Cust", ("33",), _SINGLE, "File-Function", _WSFNCTN, 104, 13,
    ),
    _spec(
        "fn-Read-Next-Header", ("34",), _SINGLE, "File-Function", _WSFNCTN, 105,
        14,
        "The last row of the group, at L105 - so the group spans L89-L105.",
    ),
    #
    # --- 03  Access-Type  pic 9.  [wsfnctn.cob:L107] ------------------------
    # Nine access types at L108-L116, values 1 through 9 in numeric order. The
    # field's own comment reads "For rdbms 2 should cover all !!!", and the
    # file header at [copybooks/wsfnctn.cob:L11-L14] records that a widening of
    # this field to `99` was made and then attributed to File-Function
    # instead. Values 5 to 9 are the ISAM START relational operators; the
    # header at [copybooks/wsfnctn.cob:L20] notes fn-not-greater-than was
    # activated on 06/08/23.
    _spec("fn-input", ("1",), _SINGLE, "Access-Type", _WSFNCTN, 108, 0),
    _spec("fn-i-o", ("2",), _SINGLE, "Access-Type", _WSFNCTN, 109, 1),
    _spec("fn-output", ("3",), _SINGLE, "Access-Type", _WSFNCTN, 110, 2),
    _spec(
        "fn-extend", ("4",), _SINGLE, "Access-Type", _WSFNCTN, 111, 3,
        'The trailing comment reads "not valid for ISAM".',
    ),
    _spec("fn-equal-to", ("5",), _SINGLE, "Access-Type", _WSFNCTN, 112, 4),
    _spec("fn-less-than", ("6",), _SINGLE, "Access-Type", _WSFNCTN, 113, 5),
    _spec("fn-greater-than", ("7",), _SINGLE, "Access-Type", _WSFNCTN, 114, 6),
    _spec("fn-not-less-than", ("8",), _SINGLE, "Access-Type", _WSFNCTN, 115, 7),
    _spec(
        "fn-not-greater-than", ("9",), _SINGLE, "Access-Type", _WSFNCTN, 116, 8,
        "The last condition name in the file. Activated 06/08/23 per the file "
        "header at [copybooks/wsfnctn.cob:L20].",
    ),
    # =========================================================================
    #  copybooks/wsbatch.cob - 8 rows. The three most load-bearing groups in
    #  the whole cycle: they gate whether posting happens at all.
    #
    #  ANOMALY A-15 lives in this copybook's header and is left unsettled. The
    #  maintainer's own words at [copybooks/wsbatch.cob:L7-L9], verbatim:
    #      *> 96 bytes 26/03/09
    #      *> 98 bytes 20/12/11 (no, dont understand as I count 96)
    #      *>   but function length (Batch-record) says 98?
    #  Agent Action Plan section 0.6.8 lists it among the questions only the
    #  compiled program can settle. The rows below are transcribed from the
    #  `88` lines, which no reading of the record length moves.
    # =========================================================================
    #
    # --- 05  WS-Ledger  pic 9.  [wsbatch.cob:L15] ---------------------------
    # Which ledger a batch belongs to. The first component of WS-Batch-Key,
    # which [copybooks/wsbatch.cob:L20-L21] also redefines as WS-Batch-Key9.
    _spec(
        "GL-Batch", ("1",), _SINGLE, "WS-Ledger", _WSBATCH, 16, 0,
        "Named in the Agent Action Plan section 0.3.1 example list. Tested in "
        "the second, stricter pass over the batch file at "
        "[general/gl070.cbl:L460-L463], `if status-open or not waiting or not "
        "gl-batch / go to loop.`",
    ),
    _spec("PL-Batch", ("2",), _SINGLE, "WS-Ledger", _WSBATCH, 17, 1),
    _spec("SL-Batch", ("3",), _SINGLE, "WS-Ledger", _WSBATCH, 18, 2),
    #
    # --- 03  Batch-Status  pic 9.  [wsbatch.cob:L25] ------------------------
    _spec(
        "Status-Open", ("0",), _SINGLE, "Batch-Status", _WSBATCH, 26, 0,
        "Named in the Agent Action Plan section 0.3.1 example list, and the "
        "single most consequential condition name in the cycle. A batch left "
        "open is detected in the first pass at [general/gl070.cbl:L314-L315], "
        "which raises ws-term-code at [general/gl070.cbl:L289]; the menu tests "
        "that code at [general/general.cbl:L800-L814] and returns rather than "
        "continuing, so gl071 and gl072 never run at all. It is tested again "
        "in the second pass at [general/gl070.cbl:L460]. This module reports "
        "the condition; what to do about it belongs to the program modules.",
    ),
    _spec("Status-Closed", ("1",), _SINGLE, "Batch-Status", _WSBATCH, 27, 1),
    #
    # --- 03  Cleared-Status  pic 9.  [wsbatch.cob:L29] ----------------------
    _spec(
        "Waiting", ("0",), _SINGLE, "Cleared-Status", _WSBATCH, 30, 0,
        "Named in the Agent Action Plan section 0.3.1 example list. Appears "
        "ONLY in the second pass over the batch file, at "
        "[general/gl070.cbl:L461] - the first pass at "
        "[general/gl070.cbl:L312-L315] filters on the cycle and the open "
        "status alone. Section 0.6.4 is verbatim: \"Collapsing the two passes "
        "into one would change which batches are pre-processed.\"",
    ),
    _spec(
        "Processed", ("1",), _SINGLE, "Cleared-Status", _WSBATCH, 31, 1,
        "The value gl072 stamps at end of batch, written as a literal rather "
        "than through the condition name: `move 1 to cleared-status.` at "
        "[general/gl072.cbl:L375], immediately before "
        "`move run-date to posted.` at [general/gl072.cbl:L376] and the "
        "rewrite at [general/gl072.cbl:L377].",
    ),
    _spec("Archived", ("2",), _SINGLE, "Cleared-Status", _WSBATCH, 32, 2),
    # =========================================================================
    #  copybooks/wssystem.cob - 60 rows, in file order across L85 to L303.
    #  The 169-column system record. Carries the IRS fan-out switch, the
    #  date-format group, and all six shapes a value clause takes.
    # =========================================================================
    #
    # --- 05  Level.  [wssystem.cob:L83] -------------------------------------
    # Six one-digit subordinate items, one per subsystem, each with its own
    # condition name. `Level-5` is the only one carrying two.
    _spec(
        "G-L", ("1",), _SINGLE, "Level-1", _WSSYSTEM, 85, 0,
        "The general ledger switch. Tested at three sites in "
        "sales/sl060.cbl - L1046, L1172 and L1177 - always as "
        "`IRS-Both-Used or G-L`, so it decides GL posting alongside the IRS "
        "fan-out rather than independently of it.",
    ),
    _spec("B-L", ("1",), _SINGLE, "Level-2", _WSSYSTEM, 87, 0),
    _spec("S-L", ("1",), _SINGLE, "Level-3", _WSSYSTEM, 89, 0),
    _spec(
        "Stock", ("1",), _SINGLE, "Level-4", _WSSYSTEM, 91, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not the out-of-scope "
        "table or bridge identifier a substring search would confuse it with. "
        "Agent Action Plan section 0.2.2 excludes those by their own exact "
        "names; this is none of them.",
    ),
    _spec(
        "IRS", ("1",), _SINGLE, "Level-5", _WSSYSTEM, 93, 0,
        'The trailing comment reads "IRS used (instead of General)."',
    ),
    _spec(
        "IRS-No", ("zero",), _FIG, "Level-5", _WSSYSTEM, 94, 1,
        "Figurative constant; reads as 0. The complement of its sibling on the "
        'same field, spelled out rather than tested as `not IRS`.',
    ),
    _spec("Payroll", ("1",), _SINGLE, "Level-6", _WSSYSTEM, 96, 0),
    #
    # --- 05  Host  pic 9.  [wssystem.cob:L98] -------------------------------
    _spec("Multi-User", ("1",), _SINGLE, "Host", _WSSYSTEM, 99, 0),
    #
    # --- 05  Op-System  pic 9.  [wssystem.cob:L100] -------------------------
    # Nine condition names on one field, and the group that exhibits three of
    # the six shapes: a contiguous list, a figurative constant, and a GAPPED
    # list. The two collective names bracket the six specific ones.
    _spec(
        "valid-os-type", ("1", "2", "3", "4", "5", "6"), _LIST,
        "Op-System", _WSSYSTEM, 101, 0,
        "A contiguous value list. Lower-case spelling kept as declared "
        "(rule R-5) - it is the only condition name in this copybook written "
        "entirely in lower case.",
    ),
    _spec(
        "No-OS", ("zero",), _FIG, "Op-System", _WSSYSTEM, 102, 1,
        "Figurative constant; reads as 0, and 0 is outside its sibling "
        "valid-os-type's range, so the two do not overlap.",
    ),
    _spec("Dos", ("1",), _SINGLE, "Op-System", _WSSYSTEM, 103, 2),
    _spec("Windows", ("2",), _SINGLE, "Op-System", _WSSYSTEM, 104, 3),
    _spec("Mac", ("3",), _SINGLE, "Op-System", _WSSYSTEM, 105, 4),
    _spec("Os2", ("4",), _SINGLE, "Op-System", _WSSYSTEM, 106, 5),
    _spec("Unix", ("5",), _SINGLE, "Op-System", _WSSYSTEM, 107, 6),
    _spec("Linux", ("6",), _SINGLE, "Op-System", _WSSYSTEM, 108, 7),
    _spec(
        "OS-Single", ("1", "2", "4"), _LIST, "Op-System", _WSSYSTEM, 109, 8,
        "A GAPPED value list: its members are 1, 2 and 4, and 3 is NOT one of "
        "them. It must never be collapsed into a 1-to-4 range - that would "
        "admit Mac, which the declaration excludes (rule R-4).",
    ),
    #
    # --- 07  File-System-Used  pic 9.  [wssystem.cob:L112] ------------------
    # The copybook's own counterpart to FA-File-System-Used in wsfnctn.cob.
    # Five further condition names for other storage engines sit behind a `*>`
    # at [copybooks/wssystem.cob:L117-L121]; a comment declares nothing, so
    # none of the five is registered.
    _spec(
        "FS-Cobol-Files-Used", ("zero",), _FIG,
        "File-System-Used", _WSSYSTEM, 113, 0,
        "Figurative constant; reads as 0.",
    ),
    _spec(
        "FS-MySql-Used", ("1",), _SINGLE, "File-System-Used", _WSSYSTEM, 114, 1,
        "SHARES ITS VALUE WITH A SIBLING: FS-RDBMS-Used at "
        "[copybooks/wssystem.cob:L116] is also declared `value 1` on this same "
        "field, so each of the two holds exactly when the other does. Both are "
        "registered as declared (rule R-4).",
    ),
    _spec(
        "FS-RDBMS-Used", ("1",), _SINGLE, "File-System-Used", _WSSYSTEM, 116, 2,
        "SHARES ITS VALUE WITH A SIBLING: FS-MySql-Used at "
        '[copybooks/wssystem.cob:L114]. The trailing comment reads "Was '
        'generic". Declared at L116, not L115: L115 carries the heading '
        '"THESE NOT IN USE at this time" in the comment area.',
    ),
    _spec(
        "FS-Valid-Options", ("0", "1"), _THRU,
        "File-System-Used", _WSSYSTEM, 122, 3,
        "A thru range, INCLUSIVE on both bounds: 0 holds, 1 holds, 2 does not. "
        'The trailing comment reads "5. (not in use unless 1-5)", recording a '
        "wider intent the declaration does not carry.",
    ),
    #
    # --- 07  File-Duplicates-In-Use  pic 9.  [wssystem.cob:L123] ------------
    _spec(
        "FS-Duplicate-Processing", ("1",), _SINGLE,
        "File-Duplicates-In-Use", _WSSYSTEM, 124, 0,
        'The field\'s comment reads "No longer in use" and this row\'s reads '
        '"Ditto".',
    ),
    #
    # --- 05  Date-Form  pic 9.  [wssystem.cob:L128] -------------------------
    # Three specific formats and one collective name. The collective name is
    # never tested, and neither is the third specific one; see the two rows
    # below and rule R-4.
    _spec(
        "Date-UK", ("1",), _SINGLE, "Date-Form", _WSSYSTEM, 129, 0,
        'Tested at [general/gl070.cbl:L585]. Trailing comment: "dd/mm/yyyy".',
    ),
    _spec(
        "Date-USA", ("2",), _SINGLE, "Date-Form", _WSSYSTEM, 130, 1,
        "Tested at [general/gl070.cbl:L587], where the wrapper swaps the day "
        'and month components. Trailing comment: "mm/dd/yyyy".',
    ),
    _spec(
        "Date-Intl", ("3",), _SINGLE, "Date-Form", _WSSYSTEM, 131, 2,
        "NEVER TESTED BY THE MIGRATED CYCLE. The date wrapper sections test "
        "Date-UK and Date-USA and then FALL THROUGH to the international form "
        "without naming it - the comment at [general/gl070.cbl:L591] reads "
        '"So its International date format". Searching general/gl070.cbl, '
        "general/gl072.cbl, sales/sl060.cbl and irs/irs030.cbl for this name "
        "returns zero occurrences. Registered for traceability; the migrated "
        'code must not start using a test the COBOL ignores. Trailing '
        'comment: "yyyy/mm/dd".',
    ),
    _spec(
        "Date-Valid-Formats", ("1", "2", "3"), _LIST,
        "Date-Form", _WSSYSTEM, 132, 3,
        "DECLARED AND NEVER TESTED - the anomaly this file is required to "
        "keep. The date wrapper sections do not use it: they test the "
        "conditional variable against a figurative constant and default it "
        "instead, at [general/gl070.cbl:L583-L584], `if Date-Form = zero / "
        "move 1 to Date-Form.` Searching the four in-scope programs "
        "general/gl070.cbl, general/gl072.cbl, sales/sl060.cbl and "
        "irs/irs030.cbl for this name returns zero occurrences. The folder "
        "requirement is verbatim: \"Model the predicate for traceability, but "
        "do not make the code use a test the COBOL ignores.\" So the row and "
        "its predicate exist, and nothing in the migration calls the "
        "predicate. Declared at [copybooks/wssystem.cob:L132] (rule R-4).",
    ),
    #
    # --- 05  Data-Capture-Used  pic 9.  [wssystem.cob:L133] -----------------
    _spec(
        "DC-Cobol-Standard", ("zero",), _FIG,
        "Data-Capture-Used", _WSSYSTEM, 134, 0,
        "Figurative constant; reads as 0.",
    ),
    _spec("DC-GUI", ("1",), _SINGLE, "Data-Capture-Used", _WSSYSTEM, 135, 1),
    _spec("DC-Widget", ("2",), _SINGLE, "Data-Capture-Used", _WSSYSTEM, 136, 2),
    #
    # =========================================================================
    #  03  General-Ledger-Block.  [wssystem.cob:L150]
    #  From here to L272 every conditional variable is `pic x`, one character
    #  wide, and every condition name is a quoted literal. All 24 alphanumeric
    #  rows in the registry are one character, so the space-padding rule
    #  `evaluate` applies is a no-op for each of them.
    # =========================================================================
    #
    # --- 05  P-C  pic x.  [wssystem.cob:L151] -------------------------------
    _spec(
        "Profit-Centres", ('"P"',), _ALNUM, "P-C", _WSSYSTEM, 152, 0,
        "Quoted literal, delimiters kept in the recorded value so a "
        "one-character switch is unambiguous.",
    ),
    _spec("Branches", ('"B"',), _ALNUM, "P-C", _WSSYSTEM, 153, 1),
    #
    # --- 05  P-C-Grouped  pic x.  [wssystem.cob:L154] -----------------------
    _spec("Grouped", ('"Y"',), _ALNUM, "P-C-Grouped", _WSSYSTEM, 155, 0),
    #
    # --- 05  P-C-Level  pic x.  [wssystem.cob:L156] -------------------------
    _spec("Revenue-Only", ('"R"',), _ALNUM, "P-C-Level", _WSSYSTEM, 157, 0),
    #
    # --- 05  Comps  pic x.  [wssystem.cob:L158] -----------------------------
    _spec("Comparatives", ('"Y"',), _ALNUM, "Comps", _WSSYSTEM, 159, 0),
    #
    # --- 05  Comps-Active  pic x.  [wssystem.cob:L160] ----------------------
    _spec(
        "Comparatives-Active", ('"Y"',), _ALNUM,
        "Comps-Active", _WSSYSTEM, 161, 0,
    ),
    #
    # --- 05  M-V  pic x.  [wssystem.cob:L162] -------------------------------
    _spec("Minimum-Validation", ('"Y"',), _ALNUM, "M-V", _WSSYSTEM, 163, 0),
    #
    # --- 05  Arch  pic x.  [wssystem.cob:L164] ------------------------------
    _spec("Archiving", ('"Y"',), _ALNUM, "Arch", _WSSYSTEM, 165, 0),
    #
    # --- 05  Trans-Print  pic x.  [wssystem.cob:L166] -----------------------
    _spec("Mandatory", ('"Y"',), _ALNUM, "Trans-Print", _WSSYSTEM, 167, 0),
    #
    # --- 05  Trans-Printed  pic x.  [wssystem.cob:L168] ---------------------
    _spec("Trans-Done", ('"Y"',), _ALNUM, "Trans-Printed", _WSSYSTEM, 169, 0),
    #
    # --- 05  Vat  pic x.  [wssystem.cob:L173] -------------------------------
    _spec(
        "Auto-Vat", ('"Y"',), _ALNUM, "Vat", _WSSYSTEM, 174, 0,
        "The alphanumeric exemplar the folder's own shape table cites. The "
        "comparison is case-SENSITIVE, so \"y\" does not hold; see the "
        "question `evaluate` records about that.",
    ),
    #
    # --- 05  Batch-Id  pic x.  [wssystem.cob:L175] --------------------------
    _spec("Preserve-Batch", ('"Y"',), _ALNUM, "Batch-Id", _WSSYSTEM, 176, 0),
    #
    # --- 05  Ledger-2nd-Index  pic x.  [wssystem.cob:L177] ------------------
    _spec(
        "Index-2", ('"Y"',), _ALNUM, "Ledger-2nd-Index", _WSSYSTEM, 178, 0,
        "The field's own comment at [copybooks/wssystem.cob:L177] reads "
        '"But file uses SINGLE INDEX only & gl030 uses a table."',
    ),
    #
    # --- 05  IRS-Instead  pic x.  [wssystem.cob:L179] -----------------------
    # THE IRS FAN-OUT: a THREE-state switch with only TWO condition names.
    # The third state is space, for which BOTH rows below are False. There is
    # no third condition name and none may be added (rule R-3).
    _spec(
        "IRS-Used", ('"Y"',), _ALNUM, "IRS-Instead", _WSSYSTEM, 180, 0,
        "Named in the Agent Action Plan section 0.3.1 example list. One of the "
        "two names on a THREE-state switch whose third state, space, has no "
        "name of its own - for space both this and IRS-Both-Used are False. "
        "The switch decides WHICH TABLES A RUN TOUCHES, so it is a "
        "database-state matter: sales/sl060.cbl tests the pair at seven sites "
        "- L1039, L1046, L1126, L1144, L1172, L1175 and L1177 - of which "
        "L1039, L1126 and L1175 use the `IRS-Used OR IRS-Both-Used` shape. "
        "Section 0.6.4 requires a scenario to pin the switch explicitly, "
        "because a default would make the affected-table list ambiguous.",
    ),
    _spec(
        "IRS-Both-Used", ('"B"',), _ALNUM, "IRS-Instead", _WSSYSTEM, 181, 1,
        "The \"IRS as well as\" state; trailing comment \"26/11/16\". The "
        "second of two names on a three-state switch - for space both are "
        "False, and for \"Y\" this one is False. Tested at all seven "
        "sales/sl060.cbl sites, three of them - L1046, L1172 and L1177 - as "
        "`IRS-Both-Used or G-L`, and L1144 on its own. The site at "
        "[sales/sl060.cbl:L1172-L1178] is where anomaly 1 lives: L1175's `if` "
        "carries no terminating period until L1178, so L1177's GL posting "
        "close is NESTED inside it and never runs in pure-GL mode. That "
        "anomaly belongs to the program module; this row only records the "
        "value set.",
    ),
    #
    # =========================================================================
    #  03  Purchase-Ledger-Block.  [wssystem.cob:L192]
    # =========================================================================
    #
    # --- 05  Purchase-Ledger  pic x.  [wssystem.cob:L200] -------------------
    _spec(
        "P-L-Exists", ('"Y"',), _ALNUM, "Purchase-Ledger", _WSSYSTEM, 201, 0,
    ),
    #
    # =========================================================================
    #  03  Sales-Ledger-Block.  [wssystem.cob:L215]
    # =========================================================================
    #
    # --- 05  Sales-Ledger  pic x.  [wssystem.cob:L216] ----------------------
    _spec("S-L-Exists", ('"Y"',), _ALNUM, "Sales-Ledger", _WSSYSTEM, 217, 0),
    #
    # --- 05  invoicer  pic 9.  [wssystem.cob:L232] --------------------------
    # Lower-case field name kept as declared. Four condition names whose
    # values are 0, 1, 2 and 9 - so 3 to 8 satisfy none of them, which the
    # trailing comment on the last row half-acknowledges.
    _spec(
        "I-Level-0", ("0",), _SINGLE, "invoicer", _WSSYSTEM, 233, 0,
        'Trailing comment: "show totals only (no net & vat) not used?"',
    ),
    _spec(
        "I-Level-1", ("1",), _SINGLE, "invoicer", _WSSYSTEM, 234, 1,
        'Trailing comment: "Show net, vat".',
    ),
    _spec(
        "I-Level-2", ("2",), _SINGLE, "invoicer", _WSSYSTEM, 235, 2,
        'Trailing comment: "show Details + vat etc looks wrong in sl910 '
        'totals only (no net & vat)".',
    ),
    _spec(
        "Not-Invoicing", ("9",), _SINGLE, "invoicer", _WSSYSTEM, 236, 3,
        "Value 9 leaves 3 to 8 satisfying no condition name on this field, "
        "which is not an error - it is simply False everywhere. The trailing "
        'comment reads "show totals only (no net & vat) but not found yet nor '
        'level 3 (see sl900)".',
    ),
    #
    # --- 05  Extra-Type  pic x.  [wssystem.cob:L238] ------------------------
    _spec("Discount", ('"D"',), _ALNUM, "Extra-Type", _WSSYSTEM, 239, 0),
    _spec("Charge", ('"C"',), _ALNUM, "Extra-Type", _WSSYSTEM, 240, 1),
    #
    # --- 05  SL-Stock-Audit  pic x.  [wssystem.cob:L243] --------------------
    _spec(
        "Stock-Audit-On", ('"Y"',), _ALNUM,
        "SL-Stock-Audit", _WSSYSTEM, 244, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes. "
        'Trailing comment: "Invoicing will create an audit record '
        '(15/05/13)".',
    ),
    #
    # --- 05  SL-Comp-Head-*  pic x.  [wssystem.cob:L263-L270] ---------------
    _spec(
        "SL-Comp-Pick", ('"Y"',), _ALNUM,
        "SL-Comp-Head-Pick", _WSSYSTEM, 264, 0,
        "Its conditional variable is declared `Pic x` with a capital P at "
        "[copybooks/wssystem.cob:L263], the only such spelling in the "
        "copybook.",
    ),
    _spec(
        "SL-Comp-Inv", ('"Y"',), _ALNUM, "SL-Comp-Head-Inv", _WSSYSTEM, 266, 0,
    ),
    _spec(
        "SL-Comp-Stat", ('"Y"',), _ALNUM,
        "SL-Comp-Head-Stat", _WSSYSTEM, 268, 0,
    ),
    _spec(
        "SL-Comp-Lets", ('"Y"',), _ALNUM,
        "SL-Comp-Head-Lets", _WSSYSTEM, 270, 0,
    ),
    #
    # --- 05  SL-VAT-Printed  pic x.  [wssystem.cob:L271] --------------------
    _spec(
        "SL-VAT-Prints", ('"Y"',), _ALNUM, "SL-VAT-Printed", _WSSYSTEM, 272, 0,
    ),
    #
    # =========================================================================
    #  03  Stock-Control-Block.  [wssystem.cob:L290]
    #  The last two rows of this copybook. Both names begin with `Stock` and
    #  both are LEGITIMATE in-scope SYSTEM-REC condition names.
    # =========================================================================
    #
    # --- 05  Stock-Control  pic x.  [wssystem.cob:L300] ---------------------
    _spec(
        "Stock-Control-Exists", ('"Y"',), _ALNUM,
        "Stock-Control", _WSSYSTEM, 301, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes.",
    ),
    #
    # --- 05  Stk-Averaging  pic 9.  [wssystem.cob:L302] --------------------
    _spec(
        "Stock-Averaging", ("1",), _SINGLE,
        "Stk-Averaging", _WSSYSTEM, 303, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes. "
        "Note the name says Stock while its conditional variable says Stk.",
    ),
    # =========================================================================
    #  copybooks/wssl.cob - 8 rows.
    #
    #  WHY THIS COPYBOOK IS HERE AT ALL. Agent Action Plan section 0.4.1.4
    #  names three source copybooks for this file, and this is not one of
    #  them. It is included because these are live `88` declarations on an
    #  in-scope record - WS-Sales-Record, the SALEDGER-REC layout that
    #  acas012/salesMT carries - and leaving them out would open a
    #  traceability hole (rule R-5). Being dictionary-backed, they are also
    #  the rows `cross_check_against_dictionary` can verify.
    #
    #  WHY EIGHT AND NOT ONE. The plan's working note describes a single `88`
    #  in this copybook, at L67. The frozen file declares EIGHT, at L26, L27,
    #  L29, L31, L33, L35, L37 and L67 - `grep -cE '^ +88 '` returns 8 - and
    #  data_dictionary/acas_posting_dictionary.json records eight for the file
    #  as well. The file governs. The justification for registering L67
    #  applies word for word to the other seven, and registering one of eight
    #  from a single copybook would itself be the hole it was meant to close.
    # =========================================================================
    #
    # --- 03  Sales-Status  pic 9.  [wssl.cob:L25] ---------------------------
    _spec("Customer-Live", ("1",), _SINGLE, "Sales-Status", _WSSL, 26, 0),
    _spec(
        "Customer-Dead", ("zero",), _FIG, "Sales-Status", _WSSL, 27, 1,
        "Figurative constant; reads as 0. Worth comparing with "
        "[copybooks/wsbatch.cob:L26], which writes `value 0` for the same "
        "idea: the two spellings behave identically and both stay recorded as "
        "written (rule R-4).",
    ),
    #
    # --- 03  Sales-Late  pic 9.  [wssl.cob:L28] -----------------------------
    _spec("Late-Charges", ("1",), _SINGLE, "Sales-Late", _WSSL, 29, 0),
    #
    # --- 03  Sales-Dunning  pic 9.  [wssl.cob:L30] --------------------------
    _spec(
        "Dunning-Letters", ("1",), _SINGLE, "Sales-Dunning", _WSSL, 31, 0,
        'The field\'s trailing comment reads "Reminder letters".',
    ),
    #
    # --- 03  Email-Invoice  pic 9.  [wssl.cob:L32] --------------------------
    _spec("Email-Invoicing", ("1",), _SINGLE, "Email-Invoice", _WSSL, 33, 0),
    #
    # --- 03  Email-Statement  pic 9.  [wssl.cob:L34] ------------------------
    _spec(
        "Email-Statementing", ("1",), _SINGLE, "Email-Statement", _WSSL, 35, 0,
    ),
    #
    # --- 03  Email-Letters  pic 9.  [wssl.cob:L36] --------------------------
    _spec(
        "Email-Dunning", ("1",), _SINGLE, "Email-Letters", _WSSL, 37, 0,
        "The name and its conditional variable disagree about the subject - "
        "Email-Letters carries Email-Dunning - which is left as declared "
        "(rule R-4).",
    ),
    #
    # --- 03  Sales-Partial-Ship-Flag  pic x.  [wssl.cob:L65-L66] ------------
    # A TWO-PHYSICAL-LINE declaration: the data name is on L65 and its `pic x`
    # continues on L66, with the `88` on L67.
    _spec(
        "Sales-BO-Set", ('"Y"',), _ALNUM,
        "Sales-Partial-Ship-Flag", _WSSL, 67, 0,
        "The row the plan names explicitly. Its conditional variable is "
        "declared across TWO physical lines, [copybooks/wssl.cob:L65-L66], "
        "with this `88` on the third. Added into filler with no change to the "
        "300-byte record size per [copybooks/wssl.cob:L9-L10]; trailing "
        'comment "added 17/03/24".',
    ),
)


# =============================================================================
#  LOOKUP AND ORDERED ACCESS
# =============================================================================

# Keyed by the EXACT COBOL spelling, so a name copied out of a copybook finds
# its row. A read-only proxy over an insertion-ordered dictionary: a caller can
# read it and cannot reorder, extend or mutate it, and its order is
# `CONDITION_NAMES`'s order (rule R-6).
BY_COBOL_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {spec.cobol_name: spec for spec in CONDITION_NAMES}
)

# The same rows keyed by their derived predicate name, for a caller holding the
# Python side of the mapping - `dal/status.py` generating member names, or
# docs/migration/traceability.md rendering the two columns side by side.
BY_PYTHON_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {spec.python_name: spec for spec in CONDITION_NAMES}
)

# A case-insensitive index, private because the PUBLISHED key is the exact
# spelling. COBOL is case-insensitive about names, so `lookup` accepts
# `STATUS-OPEN` and `status-open` as well; but the registry must not appear to
# have two spellings of one row, so this stays behind the accessor.
_BY_FOLDED_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {spec.cobol_name.casefold(): spec for spec in CONDITION_NAMES}
)

# The per-copybook composition, published as data so the count can be checked
# rather than trusted: 30 + 8 + 60 + 8 = 106. Built by walking
# `CONDITION_NAMES` in order, so the copybooks appear in the order the registry
# introduces them.
COUNTS_BY_COPYBOOK: Final[Mapping[str, int]] = types.MappingProxyType(
    {
        copybook: sum(
            1 for spec in CONDITION_NAMES if spec.copybook == copybook
        )
        for copybook in dict.fromkeys(spec.copybook for spec in CONDITION_NAMES)
    }
)

# The number of condition names declared on `Fs-Reply`, measured rather than
# assumed. `03 Fs-Reply pic 99.` at [copybooks/wsfnctn.cob:L25] carries no `88`
# anywhere in the frozen tree; its 0 / 10 / 21 / 22 / 23 / 99 value set belongs
# to `dal/status.py` per Agent Action Plan section 0.4.1.5. Published so the
# absence reads as verified rather than overlooked, and so a test can assert it
# (rules R-3, R-5).
FS_REPLY_CONDITION_NAME_COUNT: Final[int] = 0


def lookup(cobol_name: str) -> ConditionNameSpec:
    """Find one row by its COBOL condition name.

    The exact spelling is tried first, then a case-insensitive match, because
    COBOL is case-insensitive about names and a caller reading
    [general/gl070.cbl:L314] finds `status-open` in lower case while
    [copybooks/wsbatch.cob:L26] declares `Status-Open`. Both reach the same row.

    Args:
        cobol_name: The condition name, in any casing.

    Returns:
        Its row.

    Raises:
        KeyError: No row of that name. This is a PROGRAMMER error - a name that
            does not exist in the frozen copybooks - and no data value can
            cause it. Contrast `evaluate`, which returns False for a value that
            matches nothing (rule R-3).
    """
    found = BY_COBOL_NAME.get(cobol_name)
    if found is not None:
        return found
    folded = _BY_FOLDED_NAME.get(cobol_name.casefold())
    if folded is not None:
        return folded
    raise KeyError(_unknown_name_message(cobol_name))


def find(cobol_name: str) -> ConditionNameSpec | None:
    """Find one row by its COBOL condition name, or None.

    The non-raising companion to `lookup`, for a caller probing whether a name
    is declared at all - a traceability report walking names harvested from
    program source, for instance.

    Args:
        cobol_name: The condition name, in any casing.

    Returns:
        Its row, or None when the registry declares no such name.
    """
    return BY_COBOL_NAME.get(cobol_name) or _BY_FOLDED_NAME.get(
        cobol_name.casefold()
    )


def _unknown_name_message(cobol_name: str) -> str:
    """Explain an unknown condition name and offer the nearest spellings.

    Near misses are found by a plain substring test rather than an edit
    distance, which is enough to catch the realistic mistakes - a wrong prefix
    (`FS-` for `FA-FS-`), a wrong separator, a partial name - and keeps the
    message reproducible. Candidates are drawn by walking `CONDITION_NAMES`, so
    their order is the registry's and two calls give the same message
    (rule R-6).

    Args:
        cobol_name: The name that was not found.

    Returns:
        A message naming what was asked for, how many rows exist, and any near
        miss.
    """
    probe = cobol_name.casefold().replace("_", "-")
    near = tuple(
        spec.cobol_name
        for spec in CONDITION_NAMES
        if probe in spec.cobol_name.casefold()
        or spec.cobol_name.casefold() in probe
    )
    opening = (
        "No 88-level condition name " + repr(cobol_name) + " is declared in "
        "the frozen copybooks this registry transcribes. It holds "
        + str(len(CONDITION_NAMES))
        + " condition names from "
        + str(len(COUNTS_BY_COPYBOOK))
        + " copybooks; `BY_COBOL_NAME` lists every one under its exact COBOL "
        "spelling."
    )
    if not near:
        return (
            opening + " Nothing similar was found. Adding a condition name the "
            "copybooks do not declare is forbidden by rule R-3."
        )
    return opening + " Did you mean: " + ", ".join(near[:8]) + "?"


def values_for(cobol_name: str) -> tuple[str, ...]:
    """The value tokens of one condition name, in declaration order.

    Published for `dal/status.py`, which builds its call-site enumerations from
    this registry rather than transcribing the values a second time - a second
    transcription of fifteen out-of-numeric-order function codes being exactly
    the error rule R-5 exists to prevent.

    Args:
        cobol_name: The condition name, in any casing.

    Returns:
        Its tokens as `str`, in declaration order. `("1", "2", "4")` for
        `OS-Single`; `('"Y"',)` for `IRS-Used`; `("0", "1")` for the bounds of
        `FS-Valid-Options`.

    Raises:
        KeyError: No row of that name.
    """
    return lookup(cobol_name).values


def specs_for_variable(cobol_variable_name: str) -> tuple[ConditionNameSpec, ...]:
    """Every condition name declared on one conditional variable, in order.

    DECLARATION order, which for `File-Function` is NOT numeric order: the
    values come back `1 2 3 4 5 6 7 8 9 15 13 31 32 33 34`, because
    [copybooks/wsfnctn.cob:L99] declares 15 before
    [copybooks/wsfnctn.cob:L100] declares 13. `dal/status.py` builds its
    enumeration members from this order, and an enumeration's member order is
    observable, so re-sorting the result would change behaviour there
    (rules R-4, R-6).

    Built by walking `CONDITION_NAMES`, never by iterating a mapping, so the
    order is the registry's.

    Args:
        cobol_variable_name: The conditional variable's COBOL name, in any
            casing - `"File-Function"`, `"Batch-Status"`, `"IRS-Instead"`.

    Returns:
        Its condition names in declaration order, or an empty tuple when no
        condition name is declared on a field of that name. Empty is a real
        answer, not an error: `Fs-Reply` genuinely has none.
    """
    probe = cobol_variable_name.casefold()
    return tuple(
        spec
        for spec in CONDITION_NAMES
        if spec.conditional_variable.casefold() == probe
    )


def specs_for_copybook(copybook: str) -> tuple[ConditionNameSpec, ...]:
    """Every condition name one copybook declares, in file order.

    Args:
        copybook: The copybook's repository-relative path, for example
            `"copybooks/wsbatch.cob"`.

    Returns:
        Its condition names in file order, or an empty tuple when the registry
        transcribes no such copybook. `COUNTS_BY_COPYBOOK` names the four it
        does.
    """
    return tuple(spec for spec in CONDITION_NAMES if spec.copybook == copybook)


def conditional_variables() -> tuple[str, ...]:
    """Every conditional variable that carries a condition name, in file order.

    Built by walking `CONDITION_NAMES` and keeping first appearances, so the
    order is the registry's and no mapping is iterated (rule R-6).

    Returns:
        The COBOL names of the owning fields, each once.
    """
    return tuple(
        dict.fromkeys(spec.conditional_variable for spec in CONDITION_NAMES)
    )


# =============================================================================
#  THE ONE GENERIC PREDICATE
# =============================================================================


def evaluate(
    spec_or_name: ConditionNameSpec | str,
    value: int | str | decimal.Decimal,
    *,
    descriptor: FieldDescriptor | None = None,
) -> bool:
    """Whether one value satisfies one 88-level condition name.

    This is the whole of the module's behaviour; every named predicate below is
    a thin wrapper over it. It answers a question and takes no decision - what
    to do about a True or a False belongs to `acas_posting.programs`.

    HOW THE COMPARISON IS MADE
    --------------------------
    The shape of the declaration chooses the comparison, so nothing here is a
    judgement call:

        numeric shapes    Both sides are read as exact `decimal.Decimal` and
                          compared algebraically, which is what COBOL does for
                          a numeric conditional variable. A figurative `zero`
                          reads as 0, so `Customer-Dead`
                          [copybooks/wssl.cob:L27] and `Status-Open`
                          [copybooks/wsbatch.cob:L26] behave alike while
                          staying recorded as written. `SINGLE`, `FIGURATIVE`
                          and `VALUE_LIST` test membership; `THRU_RANGE` tests
                          `lower <= value <= upper`, inclusive on BOTH bounds.
        ALPHANUMERIC      Both sides are space-padded on the right to a common
                          width and compared character for character. The
                          literal's delimiters are not part of its value.

    A GAPPED list stays gapped. `OS-Single` [copybooks/wssystem.cob:L109] holds
    for 1, 2 and 4 and NOT for 3, because membership is tested against the
    tokens and never against a range spanning them (rule R-4).

    A NON-MATCHING VALUE IS False, NOT AN ERROR  (rule R-3)
    -------------------------------------------------------
    A value that satisfies no condition name of its group returns False, and so
    does a value with no reading at all - spaces in a `pic 9` field, say. COBOL
    behaves the same way: it fails the comparison and carries on. No warning is
    emitted, nothing is logged in a way that changes control flow, and there is
    no third answer a caller could branch on. Where the compiled cycle needs to
    know that a value is unusable it tests for that itself, at
    [general/gl072.cbl:L291-L292].

    THE RULE R-2 TYPE GATE
    ----------------------
    A `float` or `complex` operand raises `TypeError` instead of being
    compared. That is a gate on the operand's TYPE, not a validation of data:
    binary floating point may not carry an accounting value at any point, the
    frozen schema declares no FLOAT, DOUBLE or REAL column for one to arrive
    from, and silently rounding 0.999 into 1 would invent an answer the
    compiled program never gives. `bool` is admitted, because Python makes it
    an `int`, and reads as 1 or 0.

    A QUESTION THE COMPILED PROGRAM SETTLES  (rule R-6)
    ---------------------------------------------------
    Q-CN-1, alphanumeric case sensitivity. GnuCOBOL compares alphanumeric
    operands by the native collating sequence, in which "y" and "Y" are
    different characters, so this function is case-SENSITIVE:
    `is_irs_used("y")` is False. That follows from the language rather than
    from a choice, and it is the reading the migration adopts; if a scenario
    ever seeds a lower-case switch, the compiled oracle arbitrates and
    docs/migration/ambiguity-resolutions.md records the outcome. Nothing here
    folds case, because folding would be a behaviour this module invented.

    Args:
        spec_or_name: A row from the registry, or a condition name in any
            casing.
        value: The conditional variable's value. An `int` (or `bool`), a `str`,
            or an exact `decimal.Decimal`.
        descriptor: Optionally, the `FieldDescriptor` of the conditional
            variable. Used only for an alphanumeric comparison, to supply the
            declared field width COBOL would pad to. Every alphanumeric
            conditional variable in the in-scope layouts is `pic x`, one
            character wide, so passing it changes no answer for any of the 24 -
            it is honoured so that a wider field would behave correctly too.

    Returns:
        True when the condition name holds for that value, otherwise False.

    Raises:
        TypeError: The value is a `float` or a `complex` (rule R-2), or is not
            a type a COBOL field can hold.
        KeyError: `spec_or_name` is a name the registry does not declare.
    """
    # Rule R-2 first, before anything reads the value: a binary float must not
    # reach a comparison even to be rejected by it.
    if isinstance(value, (float, complex)):
        raise TypeError(
            "Rule R-2 admits no binary floating point: " + repr(value)
            + " is a " + type(value).__name__ + ", which cannot hold a COBOL "
            "field's value exactly. Pass an int, a str, or a decimal.Decimal. "
            "This is a gate on the operand's type, not a validation of data - "
            "a value that merely fails to match returns False."
        )
    if not isinstance(value, (int, str, decimal.Decimal)):
        raise TypeError(
            "A condition name is tested against a COBOL field's value, so "
            + repr(value) + " of type " + type(value).__name__ + " has no "
            "reading here. Pass an int, a str, or a decimal.Decimal."
        )

    spec = spec_or_name if isinstance(spec_or_name, ConditionNameSpec) else (
        lookup(spec_or_name)
    )

    if spec.kind is ConditionKind.ALPHANUMERIC:
        return _matches_literal(spec, value, descriptor)
    return _matches_number(spec, value)


def _matches_number(
    spec: ConditionNameSpec, value: int | str | decimal.Decimal
) -> bool:
    """Test a numeric conditional variable's value against a numeric clause.

    Args:
        spec: The row, of any shape but `ALPHANUMERIC`.
        value: The value.

    Returns:
        True when it satisfies the clause. False when it does not, and False
        when it has no numeric reading at all - spaces in a `pic 9` field, for
        instance (rule R-3).
    """
    read = _read_operand(value)
    if read is None:
        return False
    numbers = spec.numeric_values()
    if spec.kind is ConditionKind.THRU_RANGE:
        # Inclusive on BOTH bounds, which is what COBOL's THRU means.
        lower, upper = numbers
        return lower <= read <= upper
    # Membership, for SINGLE, FIGURATIVE and VALUE_LIST alike - so a gapped
    # list stays gapped (rule R-4).
    return any(read == number for number in numbers)


def _matches_literal(
    spec: ConditionNameSpec,
    value: int | str | decimal.Decimal,
    descriptor: FieldDescriptor | None,
) -> bool:
    """Test an alphanumeric conditional variable's value against a quoted literal.

    Args:
        spec: The row, of shape `ALPHANUMERIC`.
        value: The value. A non-`str` is read through `str`, so a caller
            holding a one-character value as an int still gets an answer rather
            than an exception - and gets False, because a digit is not the
            letter the literal names.
        descriptor: The conditional variable's descriptor, or None. Its
            `character_length` supplies the declared field width to pad to.

    Returns:
        True when the padded operands match character for character,
        case-SENSITIVELY. Otherwise False.
    """
    literal = spec.literal_text()
    text = value if isinstance(value, str) else str(value)
    width = max(len(literal), len(text))
    if descriptor is not None and descriptor.character_length:
        width = max(width, descriptor.character_length)
    return _pad(text, width) == _pad(literal, width)


def predicate_for(cobol_name: str) -> Callable[[int | str | decimal.Decimal], bool]:
    """A one-argument predicate for any of the registry's condition names.

    The reason this module does not carry 106 near-identical functions. The 38
    condition names the Agent Action Plan calls out by name have their own
    published predicates below, for readability at the call site; every other
    row is reached through here or through `evaluate` directly.

    Args:
        cobol_name: The condition name, in any casing.

    Returns:
        A callable taking one value and returning whether the condition name
        holds for it. It closes over the row, so it does no lookup per call and
        keeps `evaluate`'s semantics exactly, including returning False rather
        than raising for a value that matches nothing.

    Raises:
        KeyError: No row of that name.
    """
    spec = lookup(cobol_name)

    def _predicate(value: int | str | decimal.Decimal) -> bool:
        """Whether the closed-over condition name holds for one value."""
        return evaluate(spec, value)

    _predicate.__name__ = spec.python_name
    _predicate.__qualname__ = spec.python_name
    _predicate.__doc__ = (
        "Whether `" + spec.declaration_text + "` holds for one value. "
        "Declared at [" + spec.locator + "] on " + spec.conditional_variable
        + "."
    )
    return _predicate


# =============================================================================
#  THE PUBLISHED PREDICATES
# =============================================================================
#
# 38 named predicates: the 24-name operation vocabulary, plus the 14 condition
# names the Agent Action Plan calls out by name in section 0.3.1's example list
# and section 0.4.1.4's transformation row. Every other row of the 106 is
# reached through `evaluate` or `predicate_for`, so this module does not become
# 106 near-identical functions.
#
# Each row is bound to its spec HERE, at import time, so a mistyped condition
# name raises immediately rather than at some later call site. The bindings
# also read as a table of the published surface.

# copybooks/wsfnctn.cob - 03 File-Function pic 99. [L88], names at L89-L105.
# BOUND IN DECLARATION ORDER, which is not numeric order: 15 at L99 precedes
# 13 at L100 (rule R-4).
_FN_OPEN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-open"]
_FN_CLOSE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-close"]
_FN_READ_NEXT: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-read-next"]
_FN_READ_INDEXED: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-read-indexed"]
_FN_WRITE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-write"]
_FN_DELETE_ALL: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Delete-All"]
_FN_RE_WRITE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-re-write"]
_FN_DELETE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-delete"]
_FN_START: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-start"]
_FN_WRITE_RAW: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Write-Raw"]
_FN_READ_NEXT_RAW: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-Next-Raw"]
_FN_READ_BY_NAME: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-By-Name"]
_FN_READ_BY_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-By-Batch"]
_FN_READ_BY_CUST: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-By-Cust"]
_FN_READ_NEXT_HEADER: Final[ConditionNameSpec] = BY_COBOL_NAME[
    "fn-Read-Next-Header"
]

# copybooks/wsfnctn.cob - 03 Access-Type pic 9. [L107], names at L108-L116.
_FN_INPUT: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-input"]
_FN_I_O: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-i-o"]
_FN_OUTPUT: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-output"]
_FN_EXTEND: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-extend"]
_FN_EQUAL_TO: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-equal-to"]
_FN_LESS_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-less-than"]
_FN_GREATER_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-greater-than"]
_FN_NOT_LESS_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-not-less-than"]
_FN_NOT_GREATER_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME[
    "fn-not-greater-than"
]

# copybooks/wsbatch.cob - the three status groups, at L15, L25 and L29.
_GL_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["GL-Batch"]
_PL_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["PL-Batch"]
_SL_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["SL-Batch"]
_STATUS_OPEN: Final[ConditionNameSpec] = BY_COBOL_NAME["Status-Open"]
_STATUS_CLOSED: Final[ConditionNameSpec] = BY_COBOL_NAME["Status-Closed"]
_WAITING: Final[ConditionNameSpec] = BY_COBOL_NAME["Waiting"]
_PROCESSED: Final[ConditionNameSpec] = BY_COBOL_NAME["Processed"]
_ARCHIVED: Final[ConditionNameSpec] = BY_COBOL_NAME["Archived"]

# copybooks/wssystem.cob - the IRS fan-out at L179 and the date group at L128.
_IRS_USED: Final[ConditionNameSpec] = BY_COBOL_NAME["IRS-Used"]
_IRS_BOTH_USED: Final[ConditionNameSpec] = BY_COBOL_NAME["IRS-Both-Used"]
_DATE_UK: Final[ConditionNameSpec] = BY_COBOL_NAME["Date-UK"]
_DATE_USA: Final[ConditionNameSpec] = BY_COBOL_NAME["Date-USA"]
_DATE_INTL: Final[ConditionNameSpec] = BY_COBOL_NAME["Date-Intl"]
_DATE_VALID_FORMATS: Final[ConditionNameSpec] = BY_COBOL_NAME[
    "Date-Valid-Formats"
]


# -----------------------------------------------------------------------------
#  File-Function - the fifteen operation codes  [copybooks/wsfnctn.cob:L89-L105]
# -----------------------------------------------------------------------------


def is_fn_open(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-open`, value 1.

    Declared at [copybooks/wsfnctn.cob:L89].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_FN_OPEN, value)


def is_fn_close(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-close`, value 2.

    Declared at [copybooks/wsfnctn.cob:L90].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_FN_CLOSE, value)


def is_fn_read_next(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-read-next`, value 3.

    Declared at [copybooks/wsfnctn.cob:L91].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_FN_READ_NEXT, value)


def is_fn_read_indexed(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-read-indexed`, value 4.

    Declared at [copybooks/wsfnctn.cob:L92].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 4.
    """
    return evaluate(_FN_READ_INDEXED, value)


def is_fn_write(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-write`, value 5.

    Declared at [copybooks/wsfnctn.cob:L93].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 5.
    """
    return evaluate(_FN_WRITE, value)


def is_fn_delete_all(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Delete-All`, value 6.

    Declared at [copybooks/wsfnctn.cob:L94], its mixed capitalisation kept in
    the registry as the copybook writes it (rule R-5).

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 6.
    """
    return evaluate(_FN_DELETE_ALL, value)


def is_fn_re_write(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-re-write`, value 7.

    Declared at [copybooks/wsfnctn.cob:L95].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 7.
    """
    return evaluate(_FN_RE_WRITE, value)


def is_fn_delete(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-delete`, value 8.

    Declared at [copybooks/wsfnctn.cob:L96].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 8.
    """
    return evaluate(_FN_DELETE, value)


def is_fn_start(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-start`, value 9.

    Declared at [copybooks/wsfnctn.cob:L97].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 9.
    """
    return evaluate(_FN_START, value)


def is_fn_write_raw(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Write-Raw`, value 15.

    Declared at [copybooks/wsfnctn.cob:L99] - BEFORE value 13 at
    [copybooks/wsfnctn.cob:L100], so the group's declaration order is not its
    numeric order. Both are preserved as declared (rule R-4).

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 15.
    """
    return evaluate(_FN_WRITE_RAW, value)


def is_fn_read_next_raw(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-Next-Raw`, value 13.

    Declared at [copybooks/wsfnctn.cob:L100] - AFTER value 15 at
    [copybooks/wsfnctn.cob:L99]. The maintainer records the renumbering at
    [copybooks/wsfnctn.cob:L15]: "next-read-raw changed to 13" (rule R-4).

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 13.
    """
    return evaluate(_FN_READ_NEXT_RAW, value)


def is_fn_read_by_name(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-By-Name`, value 31.

    Declared at [copybooks/wsfnctn.cob:L102], not L101 - that line is a
    comment.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 31.
    """
    return evaluate(_FN_READ_BY_NAME, value)


def is_fn_read_by_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-By-Batch`, value 32.

    Declared at [copybooks/wsfnctn.cob:L103].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 32.
    """
    return evaluate(_FN_READ_BY_BATCH, value)


def is_fn_read_by_cust(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-By-Cust`, value 33.

    Declared at [copybooks/wsfnctn.cob:L104].

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 33.
    """
    return evaluate(_FN_READ_BY_CUST, value)


def is_fn_read_next_header(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-Next-Header`, value 34.

    Declared at [copybooks/wsfnctn.cob:L105], the last row of its group.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 34.
    """
    return evaluate(_FN_READ_NEXT_HEADER, value)


# -----------------------------------------------------------------------------
#  Access-Type - the nine access types  [copybooks/wsfnctn.cob:L108-L116]
# -----------------------------------------------------------------------------


def is_fn_input(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-input`, value 1.

    Declared at [copybooks/wsfnctn.cob:L108].

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_FN_INPUT, value)


def is_fn_i_o(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-i-o`, value 2.

    Declared at [copybooks/wsfnctn.cob:L109].

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_FN_I_O, value)


def is_fn_output(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-output`, value 3.

    Declared at [copybooks/wsfnctn.cob:L110].

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_FN_OUTPUT, value)


def is_fn_extend(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-extend`, value 4.

    Declared at [copybooks/wsfnctn.cob:L111], whose trailing comment reads
    "not valid for ISAM".

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 4.
    """
    return evaluate(_FN_EXTEND, value)


def is_fn_equal_to(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-equal-to`, value 5.

    Declared at [copybooks/wsfnctn.cob:L112]. Values 5 to 9 are the relational
    operators an indexed START positions with.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 5.
    """
    return evaluate(_FN_EQUAL_TO, value)


def is_fn_less_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-less-than`, value 6.

    Declared at [copybooks/wsfnctn.cob:L113].

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 6.
    """
    return evaluate(_FN_LESS_THAN, value)


def is_fn_greater_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-greater-than`, value 7.

    Declared at [copybooks/wsfnctn.cob:L114].

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 7.
    """
    return evaluate(_FN_GREATER_THAN, value)


def is_fn_not_less_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-not-less-than`, value 8.

    Declared at [copybooks/wsfnctn.cob:L115].

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 8.
    """
    return evaluate(_FN_NOT_LESS_THAN, value)


def is_fn_not_greater_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-not-greater-than`, value 9.

    Declared at [copybooks/wsfnctn.cob:L116], the last condition name in that
    copybook. The file header at [copybooks/wsfnctn.cob:L20] records that it
    was activated on 06/08/23.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 9.
    """
    return evaluate(_FN_NOT_GREATER_THAN, value)


# -----------------------------------------------------------------------------
#  WS-Ledger - which ledger a batch belongs to  [copybooks/wsbatch.cob:L16-L18]
# -----------------------------------------------------------------------------


def is_gl_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `WS-Ledger` holds `GL-Batch`, value 1.

    Declared at [copybooks/wsbatch.cob:L16]. Tested in the second, stricter
    pass over the batch file at [general/gl070.cbl:L462].

    Args:
        value: The `WS-Ledger` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_GL_BATCH, value)


def is_pl_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `WS-Ledger` holds `PL-Batch`, value 2.

    Declared at [copybooks/wsbatch.cob:L17].

    Args:
        value: The `WS-Ledger` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_PL_BATCH, value)


def is_sl_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `WS-Ledger` holds `SL-Batch`, value 3.

    Declared at [copybooks/wsbatch.cob:L18].

    Args:
        value: The `WS-Ledger` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_SL_BATCH, value)


# -----------------------------------------------------------------------------
#  Batch-Status  [copybooks/wsbatch.cob:L26-L27]
# -----------------------------------------------------------------------------


def is_status_open(value: int | str | decimal.Decimal) -> bool:
    """Whether `Batch-Status` holds `Status-Open`, value 0.

    Declared at [copybooks/wsbatch.cob:L26]. The condition the first pass
    detects at [general/gl070.cbl:L314-L315] and the second pass tests again at
    [general/gl070.cbl:L460].

    This function reports the condition and nothing more. What a program does
    about an open batch - raising ws-term-code at [general/gl070.cbl:L289], and
    the menu returning at [general/general.cbl:L800-L814] so that gl071 and
    gl072 never run - belongs to `acas_posting.programs` and
    `acas_posting.cli`, because this package holds no business logic.

    Args:
        value: The `Batch-Status` value.

    Returns:
        True when it is 0.
    """
    return evaluate(_STATUS_OPEN, value)


def is_status_closed(value: int | str | decimal.Decimal) -> bool:
    """Whether `Batch-Status` holds `Status-Closed`, value 1.

    Declared at [copybooks/wsbatch.cob:L27].

    Args:
        value: The `Batch-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_STATUS_CLOSED, value)


# -----------------------------------------------------------------------------
#  Cleared-Status  [copybooks/wsbatch.cob:L30-L32]
# -----------------------------------------------------------------------------


def is_waiting(value: int | str | decimal.Decimal) -> bool:
    """Whether `Cleared-Status` holds `Waiting`, value 0.

    Declared at [copybooks/wsbatch.cob:L30]. Tested ONLY in the second pass
    over the batch file, at [general/gl070.cbl:L461]; the first pass at
    [general/gl070.cbl:L312-L315] filters on the cycle and the open status
    alone.

    Args:
        value: The `Cleared-Status` value.

    Returns:
        True when it is 0.
    """
    return evaluate(_WAITING, value)


def is_processed(value: int | str | decimal.Decimal) -> bool:
    """Whether `Cleared-Status` holds `Processed`, value 1.

    Declared at [copybooks/wsbatch.cob:L31]. gl072 stamps the value as a
    literal rather than through the condition name, at
    [general/gl072.cbl:L375].

    Args:
        value: The `Cleared-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_PROCESSED, value)


def is_archived(value: int | str | decimal.Decimal) -> bool:
    """Whether `Cleared-Status` holds `Archived`, value 2.

    Declared at [copybooks/wsbatch.cob:L32].

    Args:
        value: The `Cleared-Status` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_ARCHIVED, value)


# -----------------------------------------------------------------------------
#  IRS-Instead - the three-state fan-out  [copybooks/wssystem.cob:L180-L181]
#
#  THREE states, TWO condition names. The third state is space, and for space
#  BOTH predicates below are False. There is no third condition name, and
#  adding one would breach rule R-3. The switch decides WHICH TABLES A RUN
#  TOUCHES, so a scenario must pin it explicitly (Agent Action Plan 0.6.4).
# -----------------------------------------------------------------------------


def is_irs_used(value: int | str | decimal.Decimal) -> bool:
    """Whether `IRS-Instead` holds `IRS-Used`, the literal "Y".

    Declared at [copybooks/wssystem.cob:L180] - the "IRS instead of General"
    state. False for "B", and False for space, which is the unnamed third state.
    Case-SENSITIVE, so "y" is False; see `evaluate` for the question Q-CN-1
    that records.

    Args:
        value: The `IRS-Instead` value, one character.

    Returns:
        True when it is "Y".
    """
    return evaluate(_IRS_USED, value)


def is_irs_both_used(value: int | str | decimal.Decimal) -> bool:
    """Whether `IRS-Instead` holds `IRS-Both-Used`, the literal "B".

    Declared at [copybooks/wssystem.cob:L181] - the "IRS as well as General"
    state. False for "Y", and False for space.

    Args:
        value: The `IRS-Instead` value, one character.

    Returns:
        True when it is "B".
    """
    return evaluate(_IRS_BOTH_USED, value)


# -----------------------------------------------------------------------------
#  Date-Form  [copybooks/wssystem.cob:L129-L132]
# -----------------------------------------------------------------------------


def is_date_uk(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-UK`, value 1.

    Declared at [copybooks/wssystem.cob:L129] and tested at
    [general/gl070.cbl:L585].

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_DATE_UK, value)


def is_date_usa(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-USA`, value 2.

    Declared at [copybooks/wssystem.cob:L130] and tested at
    [general/gl070.cbl:L587], where the wrapper swaps the day and month
    components.

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_DATE_USA, value)


def is_date_intl(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-Intl`, value 3.

    Declared at [copybooks/wssystem.cob:L131]. NEVER TESTED BY THE MIGRATED
    CYCLE: the date wrapper sections test `Date-UK` and `Date-USA` and then
    fall through to the international form without naming it. Published for
    traceability; the migration must not start using a test the COBOL ignores
    (rule R-4).

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_DATE_INTL, value)


def is_date_valid_formats(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-Valid-Formats`, values 1, 2 or 3.

    Declared at [copybooks/wssystem.cob:L132]. DECLARED AND NEVER TESTED - the
    date wrapper sections ignore it and test the conditional variable against a
    figurative constant instead, at [general/gl070.cbl:L583-L584]:
    `if Date-Form = zero / move 1 to Date-Form.` Searching the four in-scope
    programs for the name returns zero occurrences.

    The folder requirement is verbatim: "Model the predicate for traceability,
    but do not make the code use a test the COBOL ignores." So this predicate
    exists and NOTHING in the migration calls it. Reproducing the omission is
    the correct outcome; making the migrated code consult it would be a defect
    fixed, which rule R-4 counts as a failure.

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 1, 2 or 3.
    """
    return evaluate(_DATE_VALID_FORMATS, value)


# =============================================================================
#  THE OPTIONAL CROSS-CHECK AGAINST THE GENERATED DATA DICTIONARY  (rule R-5)
#
#  Rule R-5 wants field-level traceability to be MECHANICAL rather than
#  hand-maintained, and this registry is a hand transcription - the one place in
#  the migration where 106 values are typed out from a frozen copybook. The
#  check below is how that transcription is held to account: it re-reads the
#  same condition names from data_dictionary/acas_posting_dictionary.json, which
#  the generator parses out of the copybooks independently, and reports every
#  disagreement.
#
#  IT IS OPTIONAL, LAZY AND SILENT ABOUT ITS OWN FAILURE. Nothing calls it at
#  import time and nothing here reads a file at import time, because rule R-1
#  requires the shipped package to run on a host that carries neither the
#  copybooks nor the compiler; the dictionary artifact is likewise not a runtime
#  dependency of a predicate. It raises nothing: an unreadable or ungenerated
#  artifact comes back as a note, so a caller cannot be broken by the check it
#  ran to reassure itself.
#
#  WHAT IT CAN AND CANNOT VERIFY - a reading that differs from the Agent Action
#  Plan's expectation, recorded rather than quietly adopted. The plan's working
#  note for this file expected `copybooks/wsfnctn.cob` to be absent from the
#  dictionary, on the ground that it is a working-storage block with no table.
#  The GENERATED ARTIFACT CATALOGUES IT ANYWAY, keying its fields under a
#  working-storage record name, so all four copybooks and all 106 condition
#  names are verifiable and none has to be excused. That is the artifact
#  speaking, and the artifact wins; if a future regeneration drops the block,
#  the check reports it as a note naming the copybook rather than as 30
#  mismatches.
#
#  ONE ORDERING DIFFERENCE IS EXPECTED AND IS NOT A DISAGREEMENT. The dictionary
#  orders a copybook's entries by RECORD KEY, so `copybooks/wsbatch.cob` yields
#  the two `GLBATCH-REC` groups before the `WS-Batch-Record` group even though
#  `WS-Ledger` is declared first, at [copybooks/wsbatch.cob:L15]. This registry
#  orders by SOURCE LINE. Order is therefore compared WITHIN each conditional
#  variable, where both sources mean declaration order and where the comparison
#  actually bites - it is what would catch a re-sorted `File-Function` group.
#  File order across groups is a guarantee this registry owns alone, so the
#  check tests it against the line numbers instead.
# =============================================================================

# The four copybooks the registry transcribes, in registry order. A tuple, not
# an iteration over `COUNTS_BY_COPYBOOK`, so the reporting order is fixed in the
# source where a reader can see it (rule R-6).
_COPYBOOKS_IN_REGISTRY_ORDER: Final[tuple[str, ...]] = (
    _WSFNCTN,
    _WSBATCH,
    _WSSYSTEM,
    _WSSL,
)

# The fields of the dictionary's own condition-name record, read from the model
# at import time. Named in the findings so a reader knows exactly which three
# values were compared, and so a change to the dictionary's representation shows
# up in the report rather than passing unnoticed.
_DICTIONARY_CONDITION_FIELDS: Final[tuple[str, ...]] = tuple(
    field.name for field in dataclasses.fields(model.ConditionName)
)

# Findings carry a prefix so a caller can tell a real disagreement from a
# remark about what could not be checked.
_NOTE: Final[str] = "note: "
_MISMATCH: Final[str] = "mismatch: "


def _dictionary_condition_names(
    copybook: str, path: Path | None
) -> tuple[tuple[str, str, str, str, str], ...]:
    """Read one copybook's condition names out of the generated dictionary.

    Args:
        copybook: The copybook's repository-relative path.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        One row per condition name, in the document's own order, as
        `(name, value, source, conditional_variable, entry_key)`. The first
        three are the dictionary's `ConditionName` fields verbatim; the fourth
        and fifth say which field and which entry carried it.

    Raises:
        loader.DictionaryError: The artifact is missing, unreadable, or
            catalogues no such copybook. The caller turns that into a note.
    """
    rows: list[tuple[str, str, str, str, str]] = []
    for entry in loader.entries_for_copybook_file(copybook, path=path):
        field = entry.copybook
        # A bridge-derived column has no copybook view at all - the three IRS
        # date components at [common/irspostingMT.cbl:L982-L987] are the case -
        # and therefore no condition name either.
        if field is None:
            continue
        for condition in field.condition_names:
            rows.append(
                (
                    condition.name,
                    condition.value,
                    condition.source,
                    field.name,
                    entry.key,
                )
            )
    return tuple(rows)


def _compare_one_row(
    spec: ConditionNameSpec, row: tuple[str, str, str, str, str]
) -> tuple[str, ...]:
    """Compare one registry row against its dictionary counterpart.

    Args:
        spec: The registry's row.
        row: The dictionary's row, as `_dictionary_condition_names` builds it.

    Returns:
        One finding per field that disagrees, in a fixed order, or an empty
        tuple when the two agree on the spelling, the value clause, the locator
        and the owning conditional variable.
    """
    name, value, source, variable, key = row
    findings: list[str] = []
    lead = _MISMATCH + spec.cobol_name + " [" + spec.locator + "]: "
    if name != spec.cobol_name:
        findings.append(
            lead + "the dictionary spells it " + repr(name) + " at entry "
            + key + "; rule R-5 keeps the copybook's exact spelling."
        )
    if value != spec.value_clause_text:
        findings.append(
            lead + "value clause " + repr(spec.value_clause_text)
            + " here against " + repr(value) + " in the dictionary."
        )
    if source != spec.locator:
        findings.append(
            lead + "locator " + repr(spec.locator) + " here against "
            + repr(source) + " in the dictionary."
        )
    if variable != spec.conditional_variable:
        findings.append(
            lead + "declared on " + repr(spec.conditional_variable)
            + " here against " + repr(variable) + " in the dictionary."
        )
    return tuple(findings)


def _compare_one_copybook(
    copybook: str, rows: tuple[tuple[str, str, str, str, str], ...]
) -> tuple[str, ...]:
    """Compare one copybook's registry rows against its dictionary rows.

    Args:
        copybook: The copybook's repository-relative path.
        rows: Its dictionary rows, in document order.

    Returns:
        Every finding for that copybook, in a fixed order: the count, then each
        registry row in registry order, then any dictionary row the registry
        does not carry, then the declaration order within each conditional
        variable.
    """
    specs = specs_for_copybook(copybook)
    findings: list[str] = []

    if len(rows) != len(specs):
        findings.append(
            _MISMATCH + copybook + ": the registry carries " + str(len(specs))
            + " condition names and the dictionary " + str(len(rows)) + "."
        )

    # Index the dictionary's rows by folded name, keeping every row of a name so
    # a duplicated name is visible rather than silently overwritten. Both
    # mappings are spelled `dict()` rather than with a brace literal so that a
    # reader auditing this module for an unordered container - rule R-6 admits
    # none - can see at a glance that neither is a set.
    by_folded_name: dict[str, tuple[tuple[str, str, str, str, str], ...]] = dict()
    for row in rows:
        folded = row[0].casefold()
        by_folded_name[folded] = by_folded_name.get(folded, ()) + (row,)

    matched: dict[str, bool] = dict()
    for spec in specs:
        folded = spec.cobol_name.casefold()
        candidates = by_folded_name.get(folded, ())
        if not candidates:
            findings.append(
                _MISMATCH + spec.cobol_name + " [" + spec.locator + "]: the "
                "registry declares it and the dictionary does not catalogue it "
                "under " + copybook + "."
            )
            continue
        matched[folded] = True
        if len(candidates) > 1:
            findings.append(
                _MISMATCH + spec.cobol_name + " [" + spec.locator + "]: the "
                "dictionary catalogues the name " + str(len(candidates))
                + " times under " + copybook + ", at "
                + ", ".join(candidate[2] for candidate in candidates) + "."
            )
        findings.extend(_compare_one_row(spec, candidates[0]))

    for row in rows:
        if not matched.get(row[0].casefold(), False):
            findings.append(
                _MISMATCH + row[0] + " [" + row[2] + "]: the dictionary "
                "catalogues it on " + row[3] + " and this registry does not "
                "transcribe it. Rule R-5 wants every 88-level of the migrated "
                "cycle findable here."
            )

    findings.extend(_compare_declaration_order(copybook, specs, rows))
    findings.extend(_check_file_order(copybook, specs))
    return tuple(findings)


def _compare_declaration_order(
    copybook: str,
    specs: tuple[ConditionNameSpec, ...],
    rows: tuple[tuple[str, str, str, str, str], ...],
) -> tuple[str, ...]:
    """Compare declaration order within each conditional variable.

    Order is compared per conditional variable rather than across the whole
    copybook, because the dictionary orders a copybook's entries by record key
    while this registry orders them by source line - the difference explained
    at the head of this section. Within one variable both sources mean
    declaration order, and that is the comparison that matters: it is what
    would catch a `File-Function` group tidied into numeric order.

    Args:
        copybook: The copybook's repository-relative path.
        specs: Its registry rows, in registry order.
        rows: Its dictionary rows, in document order.

    Returns:
        One finding per conditional variable whose two orders differ.
    """
    findings: list[str] = []
    variables = tuple(dict.fromkeys(spec.conditional_variable for spec in specs))
    for variable in variables:
        folded = variable.casefold()
        here = tuple(
            spec.cobol_name
            for spec in specs
            if spec.conditional_variable.casefold() == folded
        )
        there = tuple(
            row[0] for row in rows if row[3].casefold() == folded
        )
        if here != there:
            findings.append(
                _MISMATCH + copybook + " " + variable + ": declaration order "
                "differs. Registry " + " ".join(here) + "; dictionary "
                + " ".join(there) + ". Declaration order is not numeric order "
                "for File-Function [copybooks/wsfnctn.cob:L99-L100] and "
                "dal/status.py builds enumeration members from it, so the two "
                "have to agree."
            )
    return tuple(findings)


def _check_file_order(
    copybook: str, specs: tuple[ConditionNameSpec, ...]
) -> tuple[str, ...]:
    """Check that one copybook's registry rows ascend by source line.

    File order across groups is a guarantee this registry owns alone, the
    dictionary ordering by record key instead, so it is tested against the
    locators rather than against the artifact.

    Args:
        copybook: The copybook's repository-relative path.
        specs: Its registry rows, in registry order.

    Returns:
        One finding per row that sits below an earlier one, or an empty tuple.
    """
    findings: list[str] = []
    previous = 0
    previous_name = ""
    for spec in specs:
        line = int(spec.locator.rsplit(":L", 1)[1])
        if line < previous:
            findings.append(
                _MISMATCH + copybook + ": " + spec.cobol_name + " at line "
                + str(line) + " follows " + previous_name + " at line "
                + str(previous) + ", so the rows are not in file order."
            )
        previous = line
        previous_name = spec.cobol_name
    return tuple(findings)


def cross_check_against_dictionary(*, path: Path | None = None) -> tuple[str, ...]:
    """Check this registry against the generated data dictionary (rule R-5).

    Re-reads the same 88-level condition names from
    `data_dictionary/acas_posting_dictionary.json`, which
    `acas_posting/dictionary/generate.py` parses out of the frozen copybooks
    independently of this hand transcription, and reports every disagreement.
    Two independent readings of the same frozen source agreeing is the evidence
    that the transcription is right; that is what rule R-5 asks for, and it is
    why this module is worth cross-checking at all.

    WHAT IS COMPARED, per condition name:

        * the exact COBOL spelling, hyphens and capitalisation included;
        * the value clause as text - `"0"`, `"zero"`, `"1 2 4"`, `"0 thru 1"`,
          `'"Y"'` - so a gapped list caught as a range would show up;
        * the locator, line number and all;
        * the owning conditional variable;
        * the count, per copybook;
        * declaration order within each conditional variable;
        * ascending source line across each copybook.

    WHAT IS NOT COMPARED. Order across the conditional variables of one
    copybook: the dictionary orders entries by record key, this registry by
    source line, and for `copybooks/wsbatch.cob` those genuinely differ. The
    ascending-line check covers what that omission leaves.

    THIS FUNCTION NEVER RAISES AND NEVER RUNS AT IMPORT TIME. A missing or
    unreadable artifact, or one that catalogues no such copybook, comes back as
    a note. Rule R-1 requires the shipped package to run where neither the
    copybooks nor the compiler exist, and a predicate must not acquire a file
    dependency just because a check for it exists.

    Args:
        path: An explicit artifact path, for a test pointing at a fixture, or
            None for the repository's own dictionary.

    Returns:
        The findings, in a fixed order: the whole-registry count first, then one
        copybook at a time in registry order. Each is prefixed `"mismatch: "`
        for a real disagreement or `"note: "` for a remark about something that
        could not be checked. An EMPTY TUPLE means the two readings agree
        completely and there was nothing to remark on.
    """
    findings: list[str] = []
    total = 0

    for copybook in _COPYBOOKS_IN_REGISTRY_ORDER:
        try:
            rows = _dictionary_condition_names(copybook, path)
        except loader.DictionaryError as unavailable:
            findings.append(
                _NOTE + copybook + " was not checked: "
                + type(unavailable).__name__ + " - "
                + _first_line(str(unavailable))
                + " The registry stands on its own transcription of the frozen "
                "copybook; regenerate data_dictionary/"
                "acas_posting_dictionary.json to have it corroborated."
            )
            continue
        total = total + len(rows)
        findings.extend(_compare_one_copybook(copybook, rows))

    if total and total != len(CONDITION_NAMES):
        findings.insert(
            0,
            _MISMATCH + "the registry carries " + str(len(CONDITION_NAMES))
            + " condition names and the dictionary " + str(total)
            + " across the same "
            + str(len(_COPYBOOKS_IN_REGISTRY_ORDER))
            + " copybooks. Compared on "
            + ", ".join(_DICTIONARY_CONDITION_FIELDS) + ".",
        )
    return tuple(findings)


def _first_line(message: str) -> str:
    """The first line of a message, for quoting inside a one-line finding.

    Args:
        message: A message that may run to several lines.

    Returns:
        Its first non-empty line, ending in a full stop so the finding reads as
        prose. An empty message reads as an unexplained failure rather than as
        nothing at all.
    """
    for line in message.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped if stripped.endswith(".") else stripped + "."
    return "no explanation was given."


# =============================================================================
#  THE PUBLISHED SURFACE
#
#  `FsReply`, `FileFunction` and `AccessType` are DELIBERATELY ABSENT. This
#  module is the registry those enumerations are built FROM, and it publishes
#  `values_for` and `specs_for_variable` so that dal/status.py can build them
#  without transcribing fifteen out-of-numeric-order function codes a second
#  time. Naming them here would collide with the module that owns them
#  (Agent Action Plan 0.5.3).
# =============================================================================

__all__ = [
    # The value sets, and the shape of a row.
    "CONDITION_NAMES",
    "ConditionKind",
    "ConditionNameSpec",
    # The lookup surface.
    "BY_COBOL_NAME",
    "BY_PYTHON_NAME",
    "COUNTS_BY_COPYBOOK",
    "FS_REPLY_CONDITION_NAME_COUNT",
    "conditional_variables",
    "find",
    "lookup",
    "specs_for_copybook",
    "specs_for_variable",
    "values_for",
    # The one generic predicate, and a predicate for any row.
    "evaluate",
    "predicate_for",
    # copybooks/wsfnctn.cob - File-Function, in DECLARATION order (15 before
    # 13, at [copybooks/wsfnctn.cob:L99-L100]).
    "is_fn_open",
    "is_fn_close",
    "is_fn_read_next",
    "is_fn_read_indexed",
    "is_fn_write",
    "is_fn_delete_all",
    "is_fn_re_write",
    "is_fn_delete",
    "is_fn_start",
    "is_fn_write_raw",
    "is_fn_read_next_raw",
    "is_fn_read_by_name",
    "is_fn_read_by_batch",
    "is_fn_read_by_cust",
    "is_fn_read_next_header",
    # copybooks/wsfnctn.cob - Access-Type.
    "is_fn_input",
    "is_fn_i_o",
    "is_fn_output",
    "is_fn_extend",
    "is_fn_equal_to",
    "is_fn_less_than",
    "is_fn_greater_than",
    "is_fn_not_less_than",
    "is_fn_not_greater_than",
    # copybooks/wsbatch.cob - the ledger and the two status groups.
    "is_gl_batch",
    "is_pl_batch",
    "is_sl_batch",
    "is_status_open",
    "is_status_closed",
    "is_waiting",
    "is_processed",
    "is_archived",
    # copybooks/wssystem.cob - the three-state IRS fan-out and the date group.
    "is_irs_used",
    "is_irs_both_used",
    "is_date_uk",
    "is_date_usa",
    "is_date_intl",
    "is_date_valid_formats",
    # The rule R-5 corroboration.
    "cross_check_against_dictionary",
]
