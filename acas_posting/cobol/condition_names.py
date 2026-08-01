"""88-level condition names: the frozen value sets, and predicates over them.

This module is the one place in the Python migration where the `88`-level value
sets of the in-scope COBOL record layouts are written down. Each condition name
is carried under its original COBOL spelling, with the value clause exactly as
declared, the conditional variable that owns it, and the copybook line that
declares it. Predicates then answer, for one value, whether that condition name
holds. Agent Action Plan sections 0.3.1 and 0.4.1.4 assign this file the function
codes and access types, the batch status names and the IRS fan-out names;
transformation rule 12 in section 0.1.2 asks for a predicate per `88`-level.

This module decides nothing: section 0.3.1 keeps business logic out of `cobol/`,
so every function here answers only "does this value satisfy this condition
name?" There is no routing table from a function code to an action, no run-ending
gate and no branch on an accounting outcome; those belong to
`acas_posting.programs` and `acas_posting.dal`.

THE COUNT, AND HOW IT IS COMPOSED  (rule R-5)
=============================================
`CONDITION_NAMES` holds 159 entries - EVERY `88`-level declaration in the
in-scope copybook closure, not a selection from it. Verified twice: once by
reading the frozen copybooks and once against
data_dictionary/acas_posting_dictionary.json, which records condition names per
copybook file and agrees entry for entry:

    copybooks/wsfnctn.cob            30    the operation vocabulary
    copybooks/wsbatch.cob             8    the ledger, batch and cleared statuses
    copybooks/wssystem.cob           60    the system record, IRS fan-out included
    copybooks/wssl.cob                8    the sales ledger's own switches
    copybooks/wspl.cob                2    the purchase ledger's supplier status
    copybooks/slwsinv.cob            12    sales invoice header and lines
    copybooks/slwsinv2.cob           12    the second sales invoice layout
    copybooks/slwsoi.cob              2    the sales open-item status
    copybooks/plwspinv.cob           12    purchase invoice header and lines
    copybooks/plwspinv2.cob           6    the second purchase invoice layout
    copybooks/plwsoi.cob              3    the purchase open-item hold and status
    copybooks/irswsnl.cob             2    the IRS nominal account type
    copybooks/Test-Data-Flags.cob     2    the two DAL logging switches
                                    ---
                                    159

`COUNTS_BY_COPYBOOK` publishes that breakdown as data, so the composition can
be checked rather than taken on trust, and `cross_check_against_dictionary`
corroborates all thirteen files against the independently generated artifact.

WHY ALL THIRTEEN, AND NOT THE FOUR THE PLAN NAMES
=================================================
Agent Action Plan section 0.4.1.4 names three copybooks for this module and
section 0.3.1 lists the predicates it calls out by name; the plan is naming the
`88`s it needs a predicate for, not bounding what the registry may contain. Rule
R-5 asks that "every field" be findable, and a `88` that the migrated cycle
tests but the registry omits is a traceability hole that surfaces as a
`KeyError` inside a program module rather than as a review finding.

Nineteen of the fifty-three declarations outside the original four ARE tested by
in-scope source, so the hole was live rather than theoretical:

    Testing-1       `if Testing-1` in every handler, e.g.
                    [common/acas000.cbl:L495] and [common/acas000.cbl:L546]
    Owner, Sub      [common/acasirsub1.cbl:L577], [common/acasirsub1.cbl:L616],
                    [common/acasirsub1.cbl:L414], [common/acasirsub1.cbl:L506]
    pending         [sales/sl055.cbl:L433]
    applied         [sales/sl055.cbl:L427], [purchase/pl055.cbl:L365]
    ih-analyised    [sales/sl055.cbl:L427], [sales/sl055.cbl:L440],
                    [purchase/pl055.cbl:L365], [purchase/pl055.cbl:L370]
    il-analyised    [sales/sl055.cbl:L373], [purchase/pl055.cbl:L314]
    S-Closed        [sales/sl060.cbl:L668], [sales/sl060.cbl:L877],
                    [sales/sl100.cbl:L350], [purchase/pl060.cbl:L594],
                    [purchase/pl060.cbl:L799], [purchase/pl100.cbl:L342]
    Supplier-dead   [purchase/pl060.cbl:L503]

The remaining thirty-four are registered for the same reason the eighth
`copybooks/wssl.cob` row is: transcribing part of a copybook would BE the hole.

`S-Closed` is worth one further sentence, because only one of the four programs
that test it copies its copybook directly. [purchase/pl060.cbl:L152] does;
[sales/sl060.cbl:L279] and [sales/sl100.cbl:L219] copy
[copybooks/slwsoi3.cob], which copies [copybooks/slwsoi.cob] under a REPLACING
clause at [copybooks/slwsoi3.cob:L18]; and [purchase/pl100.cbl:L213] copies
[copybooks/plwsoi5C.cob], which copies [copybooks/plwsoi.cob] the same way at
[copybooks/plwsoi5C.cob:L19]. The nested COPY is why a grep for the copybook
name in those three programs finds nothing. Two near-twins,
[copybooks/slwssoi.cob:L49-L50] and [copybooks/plwssoi.cob:L52-L53], declare the
same pair of conditions under the DIFFERENT names `si-s-open` and `si-s-closed`;
neither file is among the thirteen the dictionary reports, so neither
contributes a registry row and neither is reachable by these predicates.

FOURTEEN NAMES ARE DECLARED MORE THAN ONCE, AND ARE NEVER COLLAPSED
===================================================================
Across the thirteen copybooks, fourteen COBOL names occur in more than one file
- thirty-seven rows in all - and their value clauses genuinely DIFFER, so a
registry keyed on the bare name would answer the wrong question:

    pending    `values "P" "p"`  [copybooks/slwsinv.cob:L53]
               `values "P" "p"`  [copybooks/plwspinv.cob:L41]
               `values "p" "P"`  [copybooks/plwspinv2.cob:L41]  case order flipped
               `value "P"`       [copybooks/slwsinv2.cob:L72]   ONE literal only

`is_pending` cannot mean all four. So identity here is the DECLARATION, not the
name: `locator` is unique across the registry, `(copybook, cobol_name)` is
unique too - no name repeats inside one copybook - and every accessor takes an
optional `copybook=` or `conditional_variable=` to say which declaration is
meant. `BY_COBOL_NAME` publishes only the names declared exactly once;
`SPECS_BY_COBOL_NAME` publishes every name against all of its declarations;
`DUPLICATED_COBOL_NAMES` names the fourteen; and an unqualified `lookup` of an
ambiguous name raises a `KeyError` listing the locators rather than guessing.
This mirrors what the compiled code itself must do - anomaly A-21 records that
field-name collisions across the posting copybooks force `gl070` to write
QUALIFIED references, at [general/gl070.cbl:L510].

EVERY DECLARATION HAS A PREDICATE
=================================
`PREDICATES` maps a unique predicate name to a one-argument callable for each of
the 159 rows, derived mechanically: `is_<name>` where the folded name occurs
once, `is_<name>_<copybook-stem>` where it does not, so `is_pending_slwsinv` and
`is_pending_slwsinv2` are different predicates over different value sets.
`predicate_for` builds one on demand. The named `is_*` functions below are the
call-site conveniences for the vocabularies the plan calls out and for the
nineteen live rows above; they are a readability surface over `evaluate`, not
the coverage guarantee.

THREE READINGS OF THE FROZEN SOURCE THAT DIFFER FROM THE PLAN'S CITATIONS
Each was settled by reading the frozen file, which outranks any citation of it.

1.  `copybooks/wsfnctn.cob` is 117 lines long, so the plan's
    `[copybooks/wsfnctn.cob:L88-L118]` names a line past end of file. The
    vocabulary spans L88-L116: `03 File-Function pic 99.` at L88 with its
    fifteen condition names at L89-L105, then `03 Access-Type pic 9.` at L107
    with its nine at L108-L116.
2.  Four File-Function locators sit one line later than the plan's working note
    states, because L98, L101 and L106 are `*>` comment lines:
    `fn-Read-By-Name` L102, `fn-Read-By-Batch` L103, `fn-Read-By-Cust` L104,
    `fn-Read-Next-Header` L105.
3.  The plan's note describes one `88` in `copybooks/wssl.cob`, at L67; the file
    declares eight, at L26, L27, L29, L31, L33, L35, L37 and L67, and the
    generated dictionary records eight there too. All eight are registered, on
    the plan's own reasoning for including L67: each is a live `88` in an
    in-scope record, and omitting any would open a traceability hole.

THE SEVEN SHAPES A VALUE CLAUSE TAKES
=====================================
All seven occur in the in-scope layouts, and `ConditionKind` names six of them
(a contiguous list and a gapped list are one shape mechanically, and are told
apart by their values, never by being rewritten):

    SINGLE            `88  G-L  value 1.`             [wssystem.cob:L85]
    FIGURATIVE        `88  No-OS  value zero.`        [wssystem.cob:L102]
    VALUE_LIST        `88  valid-os-type  values 1 2 3 4 5 6.`
                                                      [wssystem.cob:L101]
    VALUE_LIST        `88  OS-Single  values 1 2 4.`  [wssystem.cob:L109]
                      GAPPED. 3 is NOT a member. It must never become a range.
    THRU_RANGE        `88  FS-Valid-Options  values 0 thru 1.`
                                                      [wssystem.cob:L122]
                      Inclusive on BOTH bounds.
    ALPHANUMERIC      `88  Auto-Vat  value "Y".`      [wssystem.cob:L174]
    ALPHANUMERIC_LIST `88  pending  values "P" "p".`  [slwsinv.cob:L53]
                      TWO OR MORE quoted literals, tested by membership.

`ALPHANUMERIC_LIST` is a separate member and not a flag on `ALPHANUMERIC`
because the difference is load-bearing: twenty of the 159 declarations list
several literals, and reading only the first would silently drop the rest -
`pending` at [copybooks/slwsinv.cob:L53] would stop holding for a lower-case
"p" even though the frozen line says it does, while `pending` at
[copybooks/slwsinv2.cob:L72] genuinely holds for "P" alone. Three rows list
four: `sih-Valid-Freqs` [copybooks/slwsinv.cob:L35], `ih-Valid-Freqs`
[copybooks/slwsinv2.cob:L54] and `ih-Valid-Freqs`
[copybooks/plwspinv.cob:L24], each `values "Y" "M" "Q" "D"`.

A figurative `zero` reads as the number 0, so `No-OS` holds for 0 and for the
text "0". An alphanumeric comparison is case-sensitive and space-padded, as
COBOL does it; `evaluate` records that question.

A NON-MATCHING VALUE IS False, NEVER AN ERROR  (rule R-3)
A `pic 9` field holding 7 fails every condition name declared on it, silently,
and the program carries on - so `evaluate` returns False, without raising,
warning or offering a sentinel a caller could branch on. Anything else would let
a program module take a branch the compiled original never takes. The frozen
cycle makes the point itself: where `general/gl072.cbl` needs to know a value is
unusable it tests for that explicitly, at L291-L292 - `if post-batch not numeric
/ go to loop.` - rather than leaning on a comparison to tell it. Two failures
are still raised, neither about a data value: `TypeError` for a `float` or
`complex` operand (the rule R-2 type gate below), and `KeyError` for a condition
name this registry does not declare.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
    MAY import       `acas_posting.cobol.field`, `acas_posting.dictionary.loader`
                     - the one door section 0.4.3 opens from this layer onto the
                     dictionary package, and the source of the object-model
                     records this module reads through its re-exports - and the
                     standard library.
    MUST NOT import  `acas_posting.dictionary.model` (reached only through the
                     loader, whose re-exports are bindings to the one
                     definition rather than copies),
                     `acas_posting.records`, `acas_posting.dal`,
                     `acas_posting.programs`, `acas_posting.cli`,
                     `acas_posting.clock`, `acas_posting.dates`,
                     `acas_posting.workfiles`, the sibling compiled-oracle
                     tree, and the sibling semantics modules `picture`,
                     `usage`, `arithmetic`, `move` and `sortverb`.
    No third-party import anywhere. Python is pinned to `==3.12.*`.

CONFLICT 1 - "PREDICATE OVER THE RECORD", FROM A PACKAGE THAT CANNOT SEE ONE
Transformation rule 12 asks for a predicate over the record; section 0.4.3
forbids importing `acas_posting.records` here. Both bind, so each half lives
where it can: the predicates here are VALUE-level, taking the field's value and
optionally its `FieldDescriptor`, never a record object, while `records/*.py`
exposes them as record-level properties - `records/gl_batch.py` already imports
`acas_posting.cobol.field`, so it defines a property returning
`condition_names.is_status_open(self.batch_status)`. Do not "fix" this by
importing the record layer here; that creates the cycle section 0.4.3 forbids.

CONFLICT 2 - THIS FILE IS THE REGISTRY; `dal/status.py` PUBLISHES THE ENUMS
Section 0.4.1.4 gives this file the function codes and access types, while
section 0.5.3 routes the status and vocabulary enumerations to `dal/status.py`,
because the single COBOL copybook mixes data layout with operation vocabulary and
the Python layering separates them. So this module is the declarative REGISTRY,
transcribed once, each row with its own locator, plus the predicates over them;
`dal/status.py` holds the call-site ENUMERATIONS and should BUILD its members
from this registry - `values_for` and `specs_for_variable` exist for that -
rather than transcribing fifteen out-of-order function codes a second time, which
is the class of error rule R-5 exists to prevent. The dependency runs one way,
from the data-access layer toward this one, so no cycle appears; accordingly this
module defines no type under the names that layer uses for its three
enumerations, since a duplicate would collide at every call site importing both.
The vocabulary really is the facade's: `SET fn-* TO TRUE` appears 302 times in
`copybooks/Proc-ACAS-FH-Calls.cob` and 56 in
`copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob`.

`Fs-Reply` HAS NO CONDITION NAMES
`03 Fs-Reply pic 99.` at [copybooks/wsfnctn.cob:L25] declares no `88` at all,
anywhere in the frozen tree; section 0.4.1.5 assigns its value set -
0 / 10 / 21 / 22 / 23 / 99 - entirely to `dal/status.py`, alongside the
`We-Error` codes and the SQLSTATE mapping. The zero is recorded so the absence
reads as read from the file rather than overlooked. Rule R-3 forbids inventing a
condition name the frozen copybooks do not declare, so none has been.

WHAT THE ANOMALIES REQUIRE OF THIS FILE  (rule R-4)
A defect reproduced is correct; a defect fixed is a failure (section 0.8.2), and
section 0.7.4 asks for a comment at each reproduction site citing its locator.

1.  THE FUNCTION CODES ARE DECLARED OUT OF NUMERIC ORDER, AND STAY THAT WAY.
    `88 fn-Write-Raw value 15.` at [copybooks/wsfnctn.cob:L99] precedes
    `88 fn-Read-Next-Raw value 13.` at [copybooks/wsfnctn.cob:L100], so the
    sequence runs 1 2 3 4 5 6 7 8 9 15 13 31 32 33 34. The maintainer's header
    explains it at [copybooks/wsfnctn.cob:L14-L15]: "Oops, previous chg should
    have been for File-Function. / next-read-raw changed to 13." The registry is
    in DECLARATION order, and `dal/status.py` builds its members from that order,
    so tidying the sequence here would silently reorder an enumeration there.
2.  TWO CONDITION NAMES ARE DECLARED AND NEVER TESTED, AND BOTH ARE KEPT.
    `88 Date-Valid-Formats values 1 2 3.` at [copybooks/wssystem.cob:L132] and
    `88 Date-Intl value 3.` at [copybooks/wssystem.cob:L131] are named by no
    in-scope program: the date wrapper sections test the conditional variable
    against a figurative constant at [general/gl070.cbl:L583-L584] - `if
    Date-Form = zero / move 1 to Date-Form.` - then test `Date-UK` at
    [general/gl070.cbl:L585] and `Date-USA` at [general/gl070.cbl:L587], falling
    through to the international form without naming it. Both are registered and
    publish a predicate that nothing calls: the requirement is to model the
    predicate, not to make the code use a test the COBOL ignores.
3.  THE IRS FAN-OUT IS A THREE-STATE SWITCH, AND THE THIRD STATE HAS NO NAME.
        copybooks/wssystem.cob:L179       05  IRS-Instead     pic x.
        copybooks/wssystem.cob:L180           88  IRS-Used        value "Y".
        copybooks/wssystem.cob:L181           88  IRS-Both-Used   value "B".
    The third state is space, and for space BOTH predicates are False; inventing
    a third condition name would breach rule R-3. This matters to database
    state: section 0.6.4 requires scenario definitions to pin the switch
    explicitly, since a default would make the affected-table list ambiguous.
    `sales/sl060.cbl` tests the two names at seven sites - L1039, L1046, L1126,
    L1144, L1172, L1175 and L1177 - three in the `IRS-Used OR IRS-Both-Used`
    shape, three as `IRS-Both-Used or G-L`, and L1144 alone.
4.  TWO CONDITION NAMES SHARE ONE VALUE ON ONE FIELD.
    `88 FS-MySql-Used value 1.` at [copybooks/wssystem.cob:L114] and
    `88 FS-RDBMS-Used value 1.` at [copybooks/wssystem.cob:L116] are both
    declared on `File-System-Used` with value 1, so each holds exactly when the
    other does. Both are registered as declared.
5.  COMMENTED-OUT CONDITION NAMES ARE NOT REGISTERED.
    [copybooks/wsfnctn.cob:L76-L80] and [copybooks/wssystem.cob:L117-L121] each
    carry five `88` declarations behind a `*>`, for storage engines the
    maintainer marks "THESE NOT IN USE". A comment declares nothing, so none of
    the ten appears here - and none has been deleted from the frozen file.

ANOMALY A-15, RECORDED AND LEFT UNSETTLED  (rule R-4)
The batch record's declared length contradicts the sum of its fields, as the
maintainer says at [copybooks/wsbatch.cob:L7-L9]. Section 0.6.8 lists it among
the questions only the compiled program can settle, because which of the two
governs the record actually read changes the alignment of the trailing fields.
Nothing here settles it: the three batch groups are registered from the `88`
lines themselves.

A NAMING TRAP: four condition names in `copybooks/wssystem.cob` begin with
`Stock` - `Stock` L91, `Stock-Audit-On` L244, `Stock-Control-Exists` L301,
`Stock-Averaging` L303. They are in-scope SYSTEM-REC condition names, not the
out-of-scope table and bridge identifiers section 0.2.2 excludes, so match whole
identifiers rather than the substring "stock".

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
`loader.ConditionName.value`, and read as an exact `decimal.Decimal` only at the
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
from pathlib import Path
from typing import Callable, Final, Mapping

from acas_posting.cobol.field import FieldDescriptor

# Agent Action Plan section 0.4.3 lets `cobol/*.py` import `dictionary.loader`
# and nothing else from the dictionary package. `loader.ConditionName` is a
# BINDING to the one definition in `acas_posting.dictionary.model` rather than a
# copy (see `loader.RE_EXPORTED_MODEL_NAMES`), so the cross-check below reads the
# dictionary's own condition-name record through the single permitted door.
from acas_posting.dictionary import loader


#  THE SHAPE OF A VALUE CLAUSE


class ConditionKind(enum.StrEnum):
    """The shape of the VALUE clause a condition name is declared with.

    Six members, one per shape the in-scope layouts actually use. A contiguous
    list and a gapped list share `VALUE_LIST`, because mechanically they are the
    same construct - a run of literals - and telling them apart by collapsing
    the contiguous one into a range would lose the declaration. `OS-Single` at
    [copybooks/wssystem.cob:L109] is the reason that matters: its members are
    1, 2 and 4, and 3 is not one of them.

    A single quoted literal and a list of them are, by contrast, KEPT APART, as
    `ALPHANUMERIC` and `ALPHANUMERIC_LIST`. Collapsing those two would not lose a
    declaration in the abstract - it would change twenty answers concretely,
    because a reader of `values` that stopped at the first token would make
    `pending` [copybooks/slwsinv.cob:L53] false for the lower-case "p" its own
    line admits. `is_alphanumeric` is true for both, so a caller asking "is this
    text?" needs neither member by name.

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
        ALPHANUMERIC: ONE quoted literal, its delimiters kept in the recorded
            value so a one-character switch is unambiguous. `88 Auto-Vat value
            "Y".` [copybooks/wssystem.cob:L174]
        ALPHANUMERIC_LIST: TWO OR MORE quoted literals, in declaration order,
            tested by membership exactly as `VALUE_LIST` is on the numeric side.
            `88 pending values "P" "p".` [copybooks/slwsinv.cob:L53] and
            `88 sih-Valid-Freqs values "Y" "M" "Q" "D".`
            [copybooks/slwsinv.cob:L35]
    """

    SINGLE = "SINGLE"
    FIGURATIVE = "FIGURATIVE"
    VALUE_LIST = "VALUE_LIST"
    THRU_RANGE = "THRU_RANGE"
    ALPHANUMERIC = "ALPHANUMERIC"
    ALPHANUMERIC_LIST = "ALPHANUMERIC_LIST"


# Short private aliases, bound once. The registry below is 159 entries long and
# reads as a table; spelling the enumeration out in full on every row would
# push the locator off the line, and the locator is the point of the row.
_SINGLE: Final[ConditionKind] = ConditionKind.SINGLE
_FIG: Final[ConditionKind] = ConditionKind.FIGURATIVE
_LIST: Final[ConditionKind] = ConditionKind.VALUE_LIST
_THRU: Final[ConditionKind] = ConditionKind.THRU_RANGE
_ALNUM: Final[ConditionKind] = ConditionKind.ALPHANUMERIC
_ALIST: Final[ConditionKind] = ConditionKind.ALPHANUMERIC_LIST

# The two alphanumeric shapes, as a tuple so `is_alphanumeric` and the two
# `numeric_values` guards all read from one place and cannot drift apart. A
# tuple and not a set: rule R-6 admits no unordered container in this module.
_ALPHANUMERIC_KINDS: Final[tuple[ConditionKind, ...]] = (
    ConditionKind.ALPHANUMERIC,
    ConditionKind.ALPHANUMERIC_LIST,
)

# The thirteen frozen copybooks the registry is transcribed from, as
# repository-relative paths spelled the way the generated dictionary spells
# them, so a locator built here and one read from the dictionary compare
# equal without either side being touched.
#
# The first four carry the operation, batch, system and sales-ledger
# vocabularies. The nine below them carry the invoice, open-item, purchase
# ledger, IRS nominal and DAL-logging `88`s that the migrated cycle also tests -
# see the module docstring on why all thirteen are transcribed rather than four.
_WSFNCTN: Final[str] = "copybooks/wsfnctn.cob"
_WSBATCH: Final[str] = "copybooks/wsbatch.cob"
_WSSYSTEM: Final[str] = "copybooks/wssystem.cob"
_WSSL: Final[str] = "copybooks/wssl.cob"
_WSPL: Final[str] = "copybooks/wspl.cob"
_SLWSINV: Final[str] = "copybooks/slwsinv.cob"
_SLWSINV2: Final[str] = "copybooks/slwsinv2.cob"
_SLWSOI: Final[str] = "copybooks/slwsoi.cob"
_PLWSPINV: Final[str] = "copybooks/plwspinv.cob"
_PLWSPINV2: Final[str] = "copybooks/plwspinv2.cob"
_PLWSOI: Final[str] = "copybooks/plwsoi.cob"
_IRSWSNL: Final[str] = "copybooks/irswsnl.cob"
_TESTFLAGS: Final[str] = "copybooks/Test-Data-Flags.cob"

# The figurative constants a VALUE clause may use, mapped to the number each
# one reads as. Only `zero` occurs in the in-scope layouts - in eight places, at
# [copybooks/wsfnctn.cob:L74], [copybooks/wssystem.cob:L94],
# [copybooks/wssystem.cob:L102], [copybooks/wssystem.cob:L113],
# [copybooks/wssystem.cob:L134], [copybooks/wssl.cob:L27],
# [copybooks/slwsoi.cob:L48] and [copybooks/plwsoi.cob:L54] - and its three
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


#  ONE REGISTRY ENTRY


@dataclasses.dataclass(frozen=True, slots=True)
class ConditionNameSpec:
    """One `88`-level condition name, exactly as the frozen copybook declares it.

    Frozen and slotted for the same reasons the sibling value objects are: a
    spec is compared by value, may be used as a mapping key, and must not be
    mutated by a caller that received it from the registry.

    EVERY SPEC CARRIES ITS OWN LINE  (rule R-5)
    -------------------------------------------
    `locator` names the line that declares THIS condition name, not the line
    that declares its group and not a span, so a reader following a name back to
    the frozen source lands on the declaration itself. The traceability document
    the plan mandates is built from these.

    THE ORIGINAL SPELLING IS DATA  (rule R-5)
    -----------------------------------------
    `cobol_name` preserves the maintainer's own capitalisation, inconsistencies
    included - `fn-open` all lower at [copybooks/wsfnctn.cob:L89],
    `fn-Delete-All` mixed at [copybooks/wsfnctn.cob:L94], `fn-re-write` lower
    at [copybooks/wsfnctn.cob:L95], `FA-FS-Cobol-Files-Used` upper at
    [copybooks/wsfnctn.cob:L74] and `valid-os-type` lower at
    [copybooks/wssystem.cob:L101]. Lookup by the COBOL name therefore works
    with the spelling a reader copied out of the copybook.

    THE DECLARATION IS THE IDENTITY, NOT THE NAME
    ---------------------------------------------
    Fourteen COBOL names are declared in more than one copybook with DIFFERENT
    value clauses, so a name alone does not identify a declaration. `locator` is
    unique across the registry and `(copybook, cobol_name)` is unique too - no
    name repeats inside one copybook. `qualified_cobol_name` renders the
    qualified form COBOL itself falls back on for the same reason (anomaly A-21,
    [general/gl070.cbl:L510]), and `predicate_name` is guaranteed unique across
    all 159 rows even where `python_name` is not.

    Attributes:
        cobol_name: The condition name verbatim, its case preserved.
        python_name: The snake_case predicate name for it, DERIVED from
            `cobol_name` by lowercasing, turning each hyphen into an
            underscore and prefixing `is_`. Derived rather than transcribed so
            that 159 rows offer no chance to mistype one, and so a name and its
            predicate can never disagree. Every one of the 159 derives to a
            valid Python identifier. NOT unique: the fourteen names declared in
            more than one copybook derive the same `python_name`, which is
            precisely why `predicate_name` exists.
        predicate_name: The row's UNIQUE published predicate name. Equal to
            `python_name` where the folded COBOL name occurs exactly once in the
            registry, and `python_name + "_" + <copybook stem>` where it does
            not - `is_pending_slwsinv` against `is_pending_slwsinv2`. Derived by
            walking the finished registry, so uniqueness is a measured property
            and not a promise; `PREDICATES` is keyed on it.
        values: The literals of the VALUE clause, as separate tokens, in
            declaration order, each carried as `str` (rule R-2). An
            alphanumeric literal keeps its delimiters, so `Auto-Vat` holds
            `('"Y"',)` and `pending` at [copybooks/slwsinv.cob:L53] holds
            `('"P"', '"p"')`; a figurative constant keeps its spelling, so
            `No-OS` holds `('zero',)`; and a numeric literal keeps its digits,
            so `Date-Valid-Formats` holds `('1', '2', '3')`. A `THRU_RANGE`
            holds exactly two, the lower bound then the upper.
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
    predicate_name: str = ""

    @property
    def value_clause_text(self) -> str:
        """The VALUE clause text, rebuilt from `values` and `kind`.

        DERIVED, not stored, so it cannot drift from `values`. The rebuilt text
        is byte-identical to `loader.ConditionName.value` for all 159 entries,
        which is what lets `cross_check_against_dictionary` compare the two
        sources without either being touched:

            SINGLE, FIGURATIVE, ALPHANUMERIC   the one token
            VALUE_LIST, ALPHANUMERIC_LIST      the tokens joined by one space
            THRU_RANGE                         `<lower> thru <upper>`

        Returns:
            The clause text, for example `"1 2 4"`, `"0 thru 1"`, `"zero"`,
            `'"Y"'` or `'"P" "p"'`.
        """
        if self.kind is ConditionKind.THRU_RANGE:
            return self.values[0] + " thru " + self.values[1]
        return " ".join(self.values)

    @property
    def qualified_cobol_name(self) -> str:
        """The name in COBOL's own qualified form, for an unambiguous citation.

        Fourteen of the registry's names are declared in more than one copybook,
        and the compiled cycle meets the same problem: anomaly A-21 records that
        field-name collisions across the posting copybooks force `gl070` to
        write qualified references, at [general/gl070.cbl:L510]. This renders the
        same idea, extended with the file so that two declarations on
        same-named carriers in different copybooks - `ih-status` in
        `copybooks/slwsinv2.cob` and in `copybooks/plwspinv.cob` - still read
        apart.

        Returns:
            `<name> of <conditional variable> in <copybook>`, for example
            `pending of sih-status in copybooks/slwsinv.cob`.
        """
        return (
            self.cobol_name + " of " + self.conditional_variable
            + " in " + self.copybook
        )

    @property
    def is_alphanumeric(self) -> bool:
        """Whether the clause is quoted literals rather than numbers.

        True for BOTH alphanumeric shapes, so a caller asking "is this text?"
        never has to know that a multi-literal clause is a separate member.

        Returns:
            True for `ALPHANUMERIC` and `ALPHANUMERIC_LIST`, False for every
            numeric shape.
        """
        return self.kind in _ALPHANUMERIC_KINDS

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
        """The characters inside the FIRST alphanumeric literal, undelimited.

        This reads the literal's content the way the compiler does when it
        compares a quoted literal with an alphanumeric item: the delimiters
        belong to the source text, not to the value. `'"Y"'` reads as `Y`.

        Only fully meaningful for an `ALPHANUMERIC` spec, which has exactly one
        literal. For an `ALPHANUMERIC_LIST` this returns the first of several and
        is therefore NOT the whole clause - use `literal_texts` for that, which
        is what `evaluate` does. It is kept single-valued rather than widened
        because a caller wanting the one literal of a one-literal declaration
        should not have to unpack a tuple. For any numeric shape the token is
        returned unchanged, so a caller that asks anyway gets the digits rather
        than an exception.

        Returns:
            The first literal's characters.
        """
        return _undelimit(self.values[0])

    def literal_texts(self) -> tuple[str, ...]:
        """Every alphanumeric literal's characters, in declaration order.

        The whole clause, which is what a comparison must test against: COBOL
        tests an alphanumeric condition name by membership over ALL of its
        literals, exactly as it does a numeric `VALUE_LIST`. Twenty of the 159
        declarations list more than one, and three list four, so reading only
        `literal_text` would give the wrong answer for a fifth of the text
        clauses.

        Case is preserved verbatim, including where two declarations of one name
        list the same two characters in opposite order - `pending` is
        `values "P" "p"` at [copybooks/plwspinv.cob:L41] and `values "p" "P"` at
        [copybooks/plwspinv2.cob:L41]. Order does not change which values match,
        but it is the frozen source's own order and rule R-4 keeps it.

        For any numeric shape the tokens come back unchanged rather than raising,
        matching `literal_text`.

        Returns:
            The literals' characters, delimiters removed, in declaration order.
        """
        return tuple(_undelimit(token) for token in self.values)

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
            ValueError: The spec is alphanumeric - of either alphanumeric shape -
                so its literals are text and have no numeric reading. A
                programmer error - `kind` states the shape - and never reachable
                from a data value.
        """
        if self.is_alphanumeric:
            raise ValueError(
                "Condition name " + repr(self.cobol_name) + " at " + self.locator
                + " is declared with "
                + ("an alphanumeric literal, " if len(self.values) == 1
                   else "alphanumeric literals, ")
                + ", ".join(repr(token) for token in self.values)
                + ", so it has no numeric reading. Compare it as text; "
                + "`kind` and `is_alphanumeric` state the shape."
            )
        return tuple(_read_number(token) for token in self.values)


#  READING A RECORDED LITERAL


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


def _undelimit(token: str) -> str:
    """Strip a quoted literal's delimiters, leaving its characters.

    The delimiters belong to the source text, not to the value: the compiler
    compares the CHARACTERS of a quoted literal against an alphanumeric item, so
    `'"Y"'` reads as `Y`. A token that is not delimited comes back unchanged, so
    calling this on a numeric or figurative token is harmless - which is what
    lets `literal_text` and `literal_texts` answer for any shape rather than
    raising.

    Only a token delimited by the SAME character at both ends and at least two
    characters long is unwrapped, so a value that legitimately contains a quote
    is not damaged.

    Args:
        token: One value token as the copybook writes it.

    Returns:
        Its characters, without delimiters.
    """
    for delimiter in _LITERAL_DELIMITERS:
        if (
            len(token) >= 2
            and token.startswith(delimiter)
            and token.endswith(delimiter)
        ):
            return token[1:-1]
    return token


def _pad(text: str, width: int) -> str:
    """Space-pad text on the right to a width, the way COBOL compares.

    An alphanumeric comparison in COBOL treats the shorter operand as though it
    were padded on the right with spaces to the length of the longer. Every
    alphanumeric conditional variable in the in-scope layouts is `pic x`, one
    character wide, so this is a no-op for all of them - it is written
    faithfully anyway, because a caller may hold a wider field's value and
    getting the rule right costs nothing.

    Args:
        text: The operand.
        width: The width to pad to.

    Returns:
        The operand, padded if it was shorter.
    """
    return text if len(text) >= width else text + " " * (width - len(text))


#  BUILDING ONE REGISTRY ROW


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

    Two members are DERIVED here rather than written 159 times, which removes
    159 chances to mistype one and makes it impossible for a name and its
    locator to disagree with the row they sit on:

        python_name  `is_` + the COBOL name lowercased with hyphens turned into
                     underscores. `fn-Delete-All` yields `is_fn_delete_all`;
                     `G-L` yields `is_g_l`; `Date-Valid-Formats` yields
                     `is_date_valid_formats`.
        locator      `<copybook>:L<line>`.

    A third, `predicate_name`, cannot be derived here because uniqueness is a
    property of the WHOLE registry rather than of one row. It is filled in by
    `_with_predicate_names` once the rows are built, and is left empty by this
    function; no row of `CONDITION_NAMES` carries an empty one.

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


#  THE REGISTRY  (rule R-5: every row carries its own line)
# =============================================================================
#
# 159 rows - every `88`-level declaration in the in-scope copybook closure.
# Thirteen copybooks, in the order the module docstring tabulates them: the four
# vocabulary copybooks first (wsfnctn 30, wsbatch 8, wssystem 60, wssl 8), then
# the nine record copybooks the migrated cycle also tests (wspl 2, slwsinv 12,
# slwsinv2 12, slwsoi 2, plwspinv 12, plwspinv2 6, plwsoi 3, irswsnl 2,
# Test-Data-Flags 2). Sales before Purchase as the plan orders the ledgers, IRS
# after both, the shared DAL switches last.
#
# Within a copybook, grouped by conditional variable in FILE order, and within
# each group in DECLARATION order - which for the function codes is not numeric
# order.
#
# Row columns, in order:
#     COBOL name | value tokens | shape | conditional variable | copybook |
#     line | index within group | notes
# A tuple, not a list and not a set: an ordering here is behaviour, because
# `dal/status.py` builds enumeration members from it (rule R-6).
#
# Named with a leading underscore because it is the registry BEFORE unique
# predicate names are derived; `CONDITION_NAMES` below is the published tuple and
# is what every accessor walks.

_REGISTRY_ROWS: Final[tuple[ConditionNameSpec, ...]] = (
    # =========================================================================
    #  copybooks/wsfnctn.cob - 30 rows. The file is 117 lines long, so the
    #  plan's L88-L118 citation of the vocabulary names a line past its end;
    #  the vocabulary spans L88-L116.
    #  03  Main-Record-Move-Flag pic 9 value zero.  [copybooks/wsfnctn.cob:L66]
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
    #  07  FA-File-System-Used  pic 9.  [copybooks/wsfnctn.cob:L73]
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
    #  07  FA-File-Duplicates-In-Use  pic 9.  [copybooks/wsfnctn.cob:L82]
    _spec(
        "FA-FS-Duplicate-Processing", ("1",), _SINGLE,
        "FA-File-Duplicates-In-Use", _WSFNCTN, 83, 0,
        "The field's own comment at [copybooks/wsfnctn.cob:L82] reads "
        "\"NO LONGER USED other than for a '6' = rdb\" - and 6 is not one of "
        "the values any condition name on it declares.",
    ),
    #  03  File-Function  pic 99.  [copybooks/wsfnctn.cob:L88]
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
    #  THE NEXT TWO ROWS ARE OUT OF NUMERIC ORDER, AND MUST STAY SO. 15 is
    #  declared before 13 - `88 fn-Write-Raw value 15.` at
    #  [copybooks/wsfnctn.cob:L99], `88 fn-Read-Next-Raw value 13.` at
    #  [copybooks/wsfnctn.cob:L100] - so the group's declaration sequence is
    #  1 2 3 4 5 6 7 8 9 15 13 31 32 33 34. The maintainer explains it in the file
    #  header at [copybooks/wsfnctn.cob:L14-L15]: "Oops, previous chg should have
    #  been for File-Function. / next-read-raw changed to 13." `dal/status.py`
    #  builds its enumeration members from this order and member order is
    #  observable, so sorting these two rows into numeric order would silently
    #  reorder that enumeration. A defect reproduced is correct; a defect fixed is
    #  a failure (rules R-4, R-6).
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
    #  03  Access-Type  pic 9.  [copybooks/wsfnctn.cob:L107]
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
    #  copybooks/wsbatch.cob - 8 rows. The three most load-bearing groups in the
    #  whole cycle: they gate whether posting happens at all. ANOMALY A-15 lives
    #  in this copybook's header, in the maintainer's own words at
    #  [copybooks/wsbatch.cob:L7-L9], and Agent Action Plan section 0.6.8 lists it
    #  among the questions only the compiled program can settle. The rows below
    #  are transcribed from the `88` lines, which no reading of the record length
    #  moves.
    #  05  WS-Ledger  pic 9.  [copybooks/wsbatch.cob:L15]
    # Which ledger a batch belongs to. The first component of WS-Batch-Key, which
    # [copybooks/wsbatch.cob:L20-L21] also redefines as WS-Batch-Key9.
    _spec(
        "GL-Batch", ("1",), _SINGLE, "WS-Ledger", _WSBATCH, 16, 0,
        "Named in the Agent Action Plan section 0.3.1 example list. Tested in "
        "the second, stricter pass over the batch file at "
        "[general/gl070.cbl:L460-L463], `if status-open or not waiting or not "
        "gl-batch / go to loop.`",
    ),
    _spec("PL-Batch", ("2",), _SINGLE, "WS-Ledger", _WSBATCH, 17, 1),
    _spec("SL-Batch", ("3",), _SINGLE, "WS-Ledger", _WSBATCH, 18, 2),
    #  03  Batch-Status  pic 9.  [copybooks/wsbatch.cob:L25]
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
    #  03  Cleared-Status  pic 9.  [copybooks/wsbatch.cob:L29]
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
    #  copybooks/wssystem.cob - 60 rows, in file order across L85 to L303.
    #  The 169-column system record. Carries the IRS fan-out switch, the
    #  date-format group, and six of the seven shapes a value clause takes -
    #  every one except ALPHANUMERIC_LIST, which only the invoice and open-item
    #  copybooks declare.
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
    #  05  Host  pic 9.  [copybooks/wssystem.cob:L98]
    _spec("Multi-User", ("1",), _SINGLE, "Host", _WSSYSTEM, 99, 0),
    #  05  Op-System  pic 9.  [copybooks/wssystem.cob:L100]
    # Nine condition names on one field, and the group that exhibits three of
    # the seven shapes: a contiguous list, a figurative constant, and a GAPPED
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
    #  07  File-System-Used  pic 9.  [copybooks/wssystem.cob:L112]
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
    #  07  File-Duplicates-In-Use  pic 9.  [copybooks/wssystem.cob:L123]
    _spec(
        "FS-Duplicate-Processing", ("1",), _SINGLE,
        "File-Duplicates-In-Use", _WSSYSTEM, 124, 0,
        'The field\'s comment reads "No longer in use" and this row\'s reads '
        '"Ditto".',
    ),
    #  05  Date-Form  pic 9.  [copybooks/wssystem.cob:L128]
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
    #  05  Data-Capture-Used  pic 9.  [copybooks/wssystem.cob:L133]
    _spec(
        "DC-Cobol-Standard", ("zero",), _FIG,
        "Data-Capture-Used", _WSSYSTEM, 134, 0,
        "Figurative constant; reads as 0.",
    ),
    _spec("DC-GUI", ("1",), _SINGLE, "Data-Capture-Used", _WSSYSTEM, 135, 1),
    _spec("DC-Widget", ("2",), _SINGLE, "Data-Capture-Used", _WSSYSTEM, 136, 2),
    #  03  General-Ledger-Block.  [copybooks/wssystem.cob:L150]
    #  From here to L272 every conditional variable is `pic x`, one character
    #  wide, and every condition name is a quoted literal. All 24 alphanumeric
    #  rows in the registry are one character, so the space-padding rule
    #  `evaluate` applies is a no-op for each of them.
    #  05  P-C  pic x.  [copybooks/wssystem.cob:L151]
    _spec(
        "Profit-Centres", ('"P"',), _ALNUM, "P-C", _WSSYSTEM, 152, 0,
        "Quoted literal, delimiters kept in the recorded value so a "
        "one-character switch is unambiguous.",
    ),
    _spec("Branches", ('"B"',), _ALNUM, "P-C", _WSSYSTEM, 153, 1),
    #  05  P-C-Grouped  pic x.  [copybooks/wssystem.cob:L154]
    _spec("Grouped", ('"Y"',), _ALNUM, "P-C-Grouped", _WSSYSTEM, 155, 0),
    #  05  P-C-Level  pic x.  [copybooks/wssystem.cob:L156]
    _spec("Revenue-Only", ('"R"',), _ALNUM, "P-C-Level", _WSSYSTEM, 157, 0),
    #  05  Comps  pic x.  [copybooks/wssystem.cob:L158]
    _spec("Comparatives", ('"Y"',), _ALNUM, "Comps", _WSSYSTEM, 159, 0),
    #  05  Comps-Active  pic x.  [copybooks/wssystem.cob:L160]
    _spec(
        "Comparatives-Active", ('"Y"',), _ALNUM,
        "Comps-Active", _WSSYSTEM, 161, 0,
    ),
    #  05  M-V  pic x.  [copybooks/wssystem.cob:L162]
    _spec("Minimum-Validation", ('"Y"',), _ALNUM, "M-V", _WSSYSTEM, 163, 0),
    #  05  Arch  pic x.  [copybooks/wssystem.cob:L164]
    _spec("Archiving", ('"Y"',), _ALNUM, "Arch", _WSSYSTEM, 165, 0),
    #  05  Trans-Print  pic x.  [copybooks/wssystem.cob:L166]
    _spec("Mandatory", ('"Y"',), _ALNUM, "Trans-Print", _WSSYSTEM, 167, 0),
    #  05  Trans-Printed  pic x.  [copybooks/wssystem.cob:L168]
    _spec("Trans-Done", ('"Y"',), _ALNUM, "Trans-Printed", _WSSYSTEM, 169, 0),
    #  05  Vat  pic x.  [copybooks/wssystem.cob:L173]
    _spec(
        "Auto-Vat", ('"Y"',), _ALNUM, "Vat", _WSSYSTEM, 174, 0,
        "The alphanumeric exemplar the folder's own shape table cites. The "
        "comparison is case-SENSITIVE, so \"y\" does not hold; see the "
        "question `evaluate` records about that.",
    ),
    #  05  Batch-Id  pic x.  [copybooks/wssystem.cob:L175]
    _spec("Preserve-Batch", ('"Y"',), _ALNUM, "Batch-Id", _WSSYSTEM, 176, 0),
    #  05  Ledger-2nd-Index  pic x.  [copybooks/wssystem.cob:L177]
    _spec(
        "Index-2", ('"Y"',), _ALNUM, "Ledger-2nd-Index", _WSSYSTEM, 178, 0,
        "The field's own comment at [copybooks/wssystem.cob:L177] reads "
        '"But file uses SINGLE INDEX only & gl030 uses a table."',
    ),
    #  05  IRS-Instead  pic x.  [copybooks/wssystem.cob:L179]
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
    #  03  Purchase-Ledger-Block.  [copybooks/wssystem.cob:L192]
    #  05  Purchase-Ledger  pic x.  [copybooks/wssystem.cob:L200]
    _spec(
        "P-L-Exists", ('"Y"',), _ALNUM, "Purchase-Ledger", _WSSYSTEM, 201, 0,
    ),
    #  03  Sales-Ledger-Block.  [copybooks/wssystem.cob:L215]
    #  05  Sales-Ledger  pic x.  [copybooks/wssystem.cob:L216]
    _spec("S-L-Exists", ('"Y"',), _ALNUM, "Sales-Ledger", _WSSYSTEM, 217, 0),
    #  05  invoicer  pic 9.  [copybooks/wssystem.cob:L232]
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
    #  05  Extra-Type  pic x.  [copybooks/wssystem.cob:L238]
    _spec("Discount", ('"D"',), _ALNUM, "Extra-Type", _WSSYSTEM, 239, 0),
    _spec("Charge", ('"C"',), _ALNUM, "Extra-Type", _WSSYSTEM, 240, 1),
    #  05  SL-Stock-Audit  pic x.  [copybooks/wssystem.cob:L243]
    _spec(
        "Stock-Audit-On", ('"Y"',), _ALNUM,
        "SL-Stock-Audit", _WSSYSTEM, 244, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes. "
        'Trailing comment: "Invoicing will create an audit record '
        '(15/05/13)".',
    ),
    #  05  SL-Comp-Head-*  pic x.  [copybooks/wssystem.cob:L263-L270]
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
    #  05  SL-VAT-Printed  pic x.  [copybooks/wssystem.cob:L271]
    _spec(
        "SL-VAT-Prints", ('"Y"',), _ALNUM, "SL-VAT-Printed", _WSSYSTEM, 272, 0,
    ),
    #  03  Stock-Control-Block.  [copybooks/wssystem.cob:L290]
    #  The last two rows of this copybook. Both names begin with `Stock` and
    #  both are LEGITIMATE in-scope SYSTEM-REC condition names.
    #  05  Stock-Control  pic x.  [copybooks/wssystem.cob:L300]
    _spec(
        "Stock-Control-Exists", ('"Y"',), _ALNUM,
        "Stock-Control", _WSSYSTEM, 301, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes.",
    ),
    #  05  Stk-Averaging  pic 9.  [copybooks/wssystem.cob:L302]
    _spec(
        "Stock-Averaging", ("1",), _SINGLE,
        "Stk-Averaging", _WSSYSTEM, 303, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes. "
        "Note the name says Stock while its conditional variable says Stk.",
    ),
    #  copybooks/wssl.cob - 8 rows. Agent Action Plan section 0.4.1.4 names three
    #  source copybooks for this file and this is not one of them; it is included
    #  because these are live `88` declarations on an in-scope record -
    #  WS-Sales-Record, the SALEDGER-REC layout acas012/salesMT carries - and
    #  leaving them out would open a traceability hole (rule R-5). WHY EIGHT AND
    #  NOT ONE: the plan's working note describes a single `88` here, at L67, while
    #  the frozen file declares eight, at L26, L27, L29, L31, L33, L35, L37 and
    #  L67 - `grep -cE '^ +88 '` returns 8 - and the generated dictionary records
    #  eight for the file too. The file governs, and the justification for
    #  registering L67 applies word for word to the other seven.
    #  03  Sales-Status  pic 9.  [copybooks/wssl.cob:L25]
    _spec("Customer-Live", ("1",), _SINGLE, "Sales-Status", _WSSL, 26, 0),
    _spec(
        "Customer-Dead", ("zero",), _FIG, "Sales-Status", _WSSL, 27, 1,
        "Figurative constant; reads as 0. Worth comparing with "
        "[copybooks/wsbatch.cob:L26], which writes `value 0` for the same "
        "idea: the two spellings behave identically and both stay recorded as "
        "written (rule R-4).",
    ),
    #  03  Sales-Late  pic 9.  [copybooks/wssl.cob:L28]
    _spec("Late-Charges", ("1",), _SINGLE, "Sales-Late", _WSSL, 29, 0),
    #  03  Sales-Dunning  pic 9.  [copybooks/wssl.cob:L30]
    _spec(
        "Dunning-Letters", ("1",), _SINGLE, "Sales-Dunning", _WSSL, 31, 0,
        'The field\'s trailing comment reads "Reminder letters".',
    ),
    #  03  Email-Invoice  pic 9.  [copybooks/wssl.cob:L32]
    _spec("Email-Invoicing", ("1",), _SINGLE, "Email-Invoice", _WSSL, 33, 0),
    #  03  Email-Statement  pic 9.  [copybooks/wssl.cob:L34]
    _spec(
        "Email-Statementing", ("1",), _SINGLE, "Email-Statement", _WSSL, 35, 0,
    ),
    #  03  Email-Letters  pic 9.  [copybooks/wssl.cob:L36]
    _spec(
        "Email-Dunning", ("1",), _SINGLE, "Email-Letters", _WSSL, 37, 0,
        "The name and its conditional variable disagree about the subject - "
        "Email-Letters carries Email-Dunning - which is left as declared "
        "(rule R-4).",
    ),
    #  03  Sales-Partial-Ship-Flag  pic x.  [copybooks/wssl.cob:L65-L66]
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
    # =========================================================================
    #  copybooks/wspl.cob - 2 rows. The purchase ledger's supplier status, the
    #  mirror of `copybooks/wssl.cob`'s Sales-Status pair. `Supplier-dead` is
    #  LIVE: [purchase/pl060.cbl:L503] tests it.
    # =========================================================================
    #
    # --- 03  Purch-Status  pic 9.  [wspl.cob:L18] ---------------------------
    _spec("Supplier-live", ("1",), _SINGLE, "Purch-Status", _WSPL, 19, 0),
    _spec(
        "Supplier-dead", ("0",), _SINGLE, "Purch-Status", _WSPL, 20, 1,
        "Written as the DIGIT 0, where the sales mirror `Customer-Dead` at "
        "[copybooks/wssl.cob:L27] writes the figurative `zero` for the same "
        "idea. The two behave identically and both stay recorded as written "
        "(rule R-4). LIVE at [purchase/pl060.cbl:L503].",
    ),
    # =========================================================================
    #  copybooks/slwsinv.cob - 12 rows. The sales invoice header and lines.
    #  Two of its names diverge from the three sibling invoice copybooks and the
    #  divergences are preserved, not normalised: the status flag is spelled
    #  `sapplied` here and `applied` in the other three, and `sil-analyised`
    #  lists ONE literal where its three counterparts list two.
    # =========================================================================
    #
    # --- 05  sih-Freq  pic x.  [slwsinv.cob:L29] -----------------------------
    # Inside `03 filler redefines sih-order.` at [copybooks/slwsinv.cob:L28],
    # the autogen recurrence frequency.
    _spec("Sih-Yearly", ('"Y"',), _ALNUM, "sih-Freq", _SLWSINV, 30, 0),
    _spec("Sih-Monthly", ('"M"',), _ALNUM, "sih-Freq", _SLWSINV, 31, 1),
    _spec("Sih-Quarterly", ('"Q"',), _ALNUM, "sih-Freq", _SLWSINV, 32, 2),
    _spec(
        "sih-Daily", ('"D"',), _ALNUM, "sih-Freq", _SLWSINV, 33, 3,
        'SHARES the value "D" with `sih-Testing` on the next line, so both '
        "hold for the same character and neither can be told from the other by "
        "its value. The maintainer's own trailing comments say so: \"These two "
        'are only for testing." and "So NOT documented and removed after '
        'tests." Reproduced as declared (rule R-4). Note also the '
        "capitalisation change mid-group - the first three names are `Sih-` "
        "and this one is `sih-`.",
    ),
    _spec(
        "sih-Testing", ('"D"',), _ALNUM, "sih-Freq", _SLWSINV, 34, 4,
        'The second of the two "D" declarations; see `sih-Daily` above.',
    ),
    _spec(
        "sih-Valid-Freqs", ('"Y"', '"M"', '"Q"', '"D"'), _ALIST,
        "sih-Freq", _SLWSINV, 35, 5,
        "The only four-literal shape in the registry, alongside its two "
        "purchase and second-sales counterparts. It INCLUDES the testing-only "
        '"D", which the maintainer\'s trailing comment flags: "Last one D, for '
        'TESTING ONLY so remove after". So a frequency of "D" is both a '
        "testing artefact and a valid frequency, and the registry keeps that "
        "as it stands.",
    ),
    #
    # --- 03  sih-status  pic x.  [slwsinv.cob:L52] ---------------------------
    _spec(
        "pending", ('"P"', '"p"'), _ALIST, "sih-status", _SLWSINV, 53, 0,
        "One of FOUR declarations of this name. Upper case FIRST here and at "
        "[copybooks/plwspinv.cob:L41]; lower case first at "
        "[copybooks/plwspinv2.cob:L41]; and a SINGLE upper-case literal at "
        "[copybooks/slwsinv2.cob:L72], which therefore does NOT hold for a "
        "lower-case \"p\". The four are never collapsed - see "
        "`DUPLICATED_COBOL_NAMES`. LIVE at [sales/sl055.cbl:L433].",
    ),
    _spec(
        "invoiced", ('"I"', '"i"'), _ALIST, "sih-status", _SLWSINV, 54, 1,
        "One of four declarations; the case order and the literal count differ "
        "between them exactly as `pending`'s do.",
    ),
    _spec(
        "sapplied", ('"Z"', '"z"'), _ALIST, "sih-status", _SLWSINV, 55, 2,
        "Spelled `sapplied` HERE ALONE. The same status flag is `applied` in "
        "[copybooks/slwsinv2.cob:L74], [copybooks/plwspinv.cob:L43] and "
        "[copybooks/plwspinv2.cob:L43], and it is `applied` that "
        "[sales/sl055.cbl:L427] tests. The leading `s` is left exactly as "
        "declared (rule R-4), which means a caller reaching for `applied` in "
        "this copybook will not find it - and should not, because the frozen "
        "line does not declare it here.",
    ),
    #
    # --- 03  sih-day-book-flag  pic x  value space.  [slwsinv.cob:L67] -------
    _spec(
        "day-booked", ('"B"', '"b"'), _ALIST,
        "sih-day-book-flag", _SLWSINV, 68, 0,
        "Its conditional variable is initialised to `space`, for which this "
        "condition name is False - the flag's unset state has no name of its "
        "own, exactly as the IRS fan-out's third state has none "
        "[copybooks/wssystem.cob:L179-L181].",
    ),
    #
    # --- 03  sih-update  pic x.  [slwsinv.cob:L69] ---------------------------
    _spec(
        "sih-analyised", ('"Z"', '"z"'), _ALIST, "sih-update", _SLWSINV, 70, 0,
        "The maintainer's own spelling of \"analysed\", kept (rule R-5).",
    ),
    #
    # --- 05  sil-update  pic x.  [slwsinv.cob:L95] ---------------------------
    _spec(
        "sil-analyised", ('"Z"',), _ALNUM, "sil-update", _SLWSINV, 96, 0,
        "ONE literal, where the three sibling `il-analyised` declarations at "
        "[copybooks/slwsinv2.cob:L105], [copybooks/plwspinv.cob:L83] and "
        "[copybooks/plwspinv2.cob:L72] each list two. This one therefore does "
        'NOT hold for a lower-case "z". Also spelled `sil-` here where the '
        "other three are `il-`, so it is the one line-level analysis flag that "
        "does not collide with its siblings.",
    ),
    # =========================================================================
    #  copybooks/slwsinv2.cob - 12 rows. The second sales invoice layout. Its
    #  names match the purchase copybooks' while its VALUES do not: every status
    #  clause here is a SINGLE upper-case literal, so this layout is the strict
    #  case-sensitive one. `il-analyised` is LIVE at [sales/sl055.cbl:L373];
    #  `pending`, `applied` and `ih-analyised` are LIVE at
    #  [sales/sl055.cbl:L427], [sales/sl055.cbl:L433] and
    #  [sales/sl055.cbl:L440].
    # =========================================================================
    #
    # --- 05  ih-Freq  pic x.  [slwsinv2.cob:L48] -----------------------------
    # Inside `03 filler redefines ih-order.` at [copybooks/slwsinv2.cob:L47].
    _spec("ih-Yearly", ('"Y"',), _ALNUM, "ih-Freq", _SLWSINV2, 49, 0),
    _spec("ih-Monthly", ('"M"',), _ALNUM, "ih-Freq", _SLWSINV2, 50, 1),
    _spec("ih-Quarterly", ('"Q"',), _ALNUM, "ih-Freq", _SLWSINV2, 51, 2),
    _spec(
        "ih-Daily", ('"D"',), _ALNUM, "ih-Freq", _SLWSINV2, 52, 3,
        'SHARES the value "D" with `ih-Testing` on the next line, with the '
        "maintainer's testing-only comments. The same pair recurs at "
        "[copybooks/plwspinv.cob:L22-L23].",
    ),
    _spec(
        "ih-Testing", ('"D"',), _ALNUM, "ih-Freq", _SLWSINV2, 53, 4,
        'The second of the two "D" declarations; see `ih-Daily` above.',
    ),
    _spec(
        "ih-Valid-Freqs", ('"Y"', '"M"', '"Q"', '"D"'), _ALIST,
        "ih-Freq", _SLWSINV2, 54, 5,
        'Includes the testing-only "D", per the maintainer\'s trailing '
        'comment "Last one D, for TESTING ONLY so remove after".',
    ),
    #
    # --- 03  ih-status  pic x.  [slwsinv2.cob:L71] ---------------------------
    _spec(
        "pending", ('"P"',), _ALNUM, "ih-status", _SLWSINV2, 72, 0,
        "A SINGLE literal, where the three sibling `pending` declarations each "
        'list two. This one is case-SENSITIVE: a lower-case "p" satisfies '
        "[copybooks/slwsinv.cob:L53] and [copybooks/plwspinv.cob:L41] but NOT "
        "this line. The difference is the frozen source's and is preserved "
        "(rule R-4). LIVE at [sales/sl055.cbl:L433].",
    ),
    _spec(
        "invoiced", ('"I"',), _ALNUM, "ih-status", _SLWSINV2, 73, 1,
        "A single literal; see `pending` above for the divergence.",
    ),
    _spec(
        "applied", ('"Z"',), _ALNUM, "ih-status", _SLWSINV2, 74, 2,
        "A single literal. The sales mirror of this flag in "
        "[copybooks/slwsinv.cob:L55] is spelled `sapplied` and lists two "
        "literals, so the two sales invoice copybooks agree on neither the "
        "name nor the value set. LIVE at [sales/sl055.cbl:L427].",
    ),
    #
    # --- 03  ih-day-book-flag  pic x.  [slwsinv2.cob:L86] --------------------
    _spec(
        "day-booked", ('"B"',), _ALNUM,
        "ih-day-book-flag", _SLWSINV2, 87, 0,
        "A single literal, and its conditional variable carries NO `value "
        "space` initialisation where [copybooks/slwsinv.cob:L67] and "
        "[copybooks/plwspinv.cob:L51] both do.",
    ),
    #
    # --- 03  ih-update  pic x.  [slwsinv2.cob:L88] ---------------------------
    _spec(
        "ih-analyised", ('"Z"',), _ALNUM, "ih-update", _SLWSINV2, 89, 0,
        "A single literal. LIVE at [sales/sl055.cbl:L427] and "
        "[sales/sl055.cbl:L440].",
    ),
    #
    # --- 05  il-update  pic x.  [slwsinv2.cob:L104] --------------------------
    _spec(
        "il-analyised", ('"Z"',), _ALNUM, "il-update", _SLWSINV2, 105, 0,
        "A single literal. LIVE at [sales/sl055.cbl:L373].",
    ),
    # =========================================================================
    #  copybooks/slwsoi.cob - 2 rows. The sales open-item status. `S-Closed` is
    #  LIVE at [sales/sl060.cbl:L668], [sales/sl060.cbl:L877] and
    #  [sales/sl100.cbl:L350]. Neither program copies this copybook directly:
    #  both copy [copybooks/slwsoi3.cob] - at [sales/sl060.cbl:L279] and
    #  [sales/sl100.cbl:L219] - and that copybook itself copies this one under
    #  a REPLACING clause at [copybooks/slwsoi3.cob:L18], so these two
    #  declarations reach the programs transitively. [copybooks/slwssoi.cob],
    #  also copied by [sales/sl060.cbl:L280], declares the SAME two conditions
    #  under different names - `si-s-open` and `si-s-closed`
    #  [copybooks/slwssoi.cob:L49-L50] - and is not one of the thirteen
    #  copybooks the dictionary reports, so it contributes no registry row.
    # =========================================================================
    #
    # --- 03  OI-Status  pic 9.  [slwsoi.cob:L47] -----------------------------
    _spec(
        "S-Open", ("zero",), _FIG, "OI-Status", _SLWSOI, 48, 0,
        "Figurative constant; reads as 0. Declared identically at "
        "[copybooks/plwsoi.cob:L54] on a same-named carrier, which is why the "
        "two are told apart by locator rather than by name.",
    ),
    _spec(
        "S-Closed", ("1",), _SINGLE, "OI-Status", _SLWSOI, 49, 1,
        'Trailing comment "Paid". LIVE at [sales/sl060.cbl:L668], '
        "[sales/sl060.cbl:L877] and [sales/sl100.cbl:L350], reached through "
        "the nested COPY at [copybooks/slwsoi3.cob:L18]. Declared again at "
        "[copybooks/plwsoi.cob:L55] with the same value, and that one is LIVE "
        "in the purchase programs.",
    ),
    # =========================================================================
    #  copybooks/plwspinv.cob - 12 rows. The purchase invoice header and lines.
    #  Its NAMES match copybooks/slwsinv2.cob's and its VALUES match
    #  copybooks/slwsinv.cob's - two literals per status clause, upper case
    #  first, except `il-analyised`, which flips. Its `ih-Freq` sits inside a
    #  plain GROUP, `05 ih-order.` at [copybooks/plwspinv.cob:L17], not a
    #  `filler redefines` as both sales copybooks use. `applied`,
    #  `ih-analyised` and `il-analyised` are LIVE at [purchase/pl055.cbl:L365],
    #  [purchase/pl055.cbl:L370] and [purchase/pl055.cbl:L314].
    # =========================================================================
    #
    # --- 07  ih-Freq  pic x.  [plwspinv.cob:L18] -----------------------------
    _spec("ih-Yearly", ('"Y"',), _ALNUM, "ih-Freq", _PLWSPINV, 19, 0),
    _spec("ih-Monthly", ('"M"',), _ALNUM, "ih-Freq", _PLWSPINV, 20, 1),
    _spec("ih-Quarterly", ('"Q"',), _ALNUM, "ih-Freq", _PLWSPINV, 21, 2),
    _spec(
        "ih-Daily", ('"D"',), _ALNUM, "ih-Freq", _PLWSPINV, 22, 3,
        'SHARES the value "D" with `ih-Testing` on the next line, with the '
        "maintainer's testing-only comments, exactly as "
        "[copybooks/slwsinv2.cob:L52-L53] does.",
    ),
    _spec(
        "ih-Testing", ('"D"',), _ALNUM, "ih-Freq", _PLWSPINV, 23, 4,
        'The second of the two "D" declarations; see `ih-Daily` above.',
    ),
    _spec(
        "ih-Valid-Freqs", ('"Y"', '"M"', '"Q"', '"D"'), _ALIST,
        "ih-Freq", _PLWSPINV, 24, 5,
        'Includes the testing-only "D". The maintainer\'s trailing comment '
        'here reads "LAst one for TESTING ONLY so remove after" - the '
        "transposed capitals and the missing \"D,\" are his, and the comment "
        "is not data, so only the value clause is transcribed.",
    ),
    #
    # --- 05  ih-status  pic x.  [plwspinv.cob:L40] ---------------------------
    _spec(
        "pending", ('"P"', '"p"'), _ALIST, "ih-status", _PLWSPINV, 41, 0,
        "Two literals, upper case first - the same clause as "
        "[copybooks/slwsinv.cob:L53], and the reverse case order of "
        "[copybooks/plwspinv2.cob:L41].",
    ),
    _spec(
        "invoiced", ('"I"', '"i"'), _ALIST, "ih-status", _PLWSPINV, 42, 1,
        "Two literals, upper case first.",
    ),
    _spec(
        "applied", ('"Z"', '"z"'), _ALIST, "ih-status", _PLWSPINV, 43, 2,
        "Two literals, upper case first. LIVE at [purchase/pl055.cbl:L365].",
    ),
    #
    # --- 05  ih-day-book-flag  pic x  value space.  [plwspinv.cob:L50] -------
    _spec(
        "day-booked", ('"B"', '"b"'), _ALIST,
        "ih-day-book-flag", _PLWSPINV, 51, 0,
        "The frozen line carries a space before its full stop - "
        '`values "B" "b" .` - which is whitespace to the compiler and is not '
        "part of the clause, so the tokens are transcribed without it.",
    ),
    #
    # --- 05  ih-update  pic x.  [plwspinv.cob:L52] ---------------------------
    _spec(
        "ih-analyised", ('"Z"', '"z"'), _ALIST,
        "ih-update", _PLWSPINV, 53, 0,
        "Two literals, upper case first. LIVE at [purchase/pl055.cbl:L365] "
        "and [purchase/pl055.cbl:L370].",
    ),
    #
    # --- 05  il-update  pic x.  [plwspinv.cob:L82] ---------------------------
    _spec(
        "il-analyised", ('"z"', '"Z"'), _ALIST,
        "il-update", _PLWSPINV, 83, 0,
        "LOWER case first, unlike every other clause in this copybook, with "
        'the maintainer\'s own trailing comment "using Z hopefully" recording '
        "his uncertainty about which case the data carries. Reproduced as "
        "declared (rule R-4). LIVE at [purchase/pl055.cbl:L314].",
    ),
    # =========================================================================
    #  copybooks/plwspinv2.cob - 6 rows. The second purchase invoice layout,
    #  and the only copybook in which EVERY clause lists lower case first. It
    #  declares no `ih-Freq` group at all, so its six rows are the status,
    #  day-book and analysis flags only.
    # =========================================================================
    #
    # --- 03  ih-status  pic x.  [plwspinv2.cob:L40] --------------------------
    _spec(
        "pending", ('"p"', '"P"'), _ALIST, "ih-status", _PLWSPINV2, 41, 0,
        "LOWER case first, the reverse of [copybooks/plwspinv.cob:L41] and "
        "[copybooks/slwsinv.cob:L53]. Which values match is unaffected; the "
        "ORDER is the frozen source's and rule R-4 keeps it.",
    ),
    _spec(
        "invoiced", ('"i"', '"I"'), _ALIST, "ih-status", _PLWSPINV2, 42, 1,
        "Lower case first.",
    ),
    _spec(
        "applied", ('"z"', '"Z"'), _ALIST, "ih-status", _PLWSPINV2, 43, 2,
        "Lower case first.",
    ),
    #
    # --- 03  ih-day-book-flag  pic x.  [plwspinv2.cob:L50] -------------------
    _spec(
        "day-booked", ('"b"', '"B"'), _ALIST,
        "ih-day-book-flag", _PLWSPINV2, 51, 0,
        "Lower case first, and no `value space` initialisation on the carrier.",
    ),
    #
    # --- 03  ih-update  pic x.  [plwspinv2.cob:L52] --------------------------
    _spec(
        "ih-analyised", ('"z"', '"Z"'), _ALIST,
        "ih-update", _PLWSPINV2, 53, 0, "Lower case first.",
    ),
    #
    # --- 03  il-update  pic x.  [plwspinv2.cob:L71] --------------------------
    _spec(
        "il-analyised", ('"z"', '"Z"'), _ALIST,
        "il-update", _PLWSPINV2, 72, 0,
        "Lower case first - agreeing with [copybooks/plwspinv.cob:L83], which "
        "is the one clause in THAT copybook to do so.",
    ),
    # =========================================================================
    #  copybooks/plwsoi.cob - 3 rows. The purchase open-item hold flag and
    #  status. `S-Closed` is LIVE at [purchase/pl060.cbl:L594],
    #  [purchase/pl060.cbl:L799] and [purchase/pl100.cbl:L342].
    #  [purchase/pl060.cbl:L152] copies this copybook directly;
    #  [purchase/pl100.cbl:L213] copies [copybooks/plwsoi5C.cob], which copies
    #  this one under a REPLACING clause at [copybooks/plwsoi5C.cob:L19], so
    #  pl100 reaches these declarations transitively.
    #  [copybooks/plwssoi.cob], copied at [purchase/pl060.cbl:L153], declares
    #  the same two conditions as `si-s-open` and `si-s-closed`
    #  [copybooks/plwssoi.cob:L52-L53]; it is not one of the thirteen copybooks
    #  the dictionary reports, so it contributes no registry row.
    #  [copybooks/plwsoi5B.cob], copied at [purchase/pl060.cbl:L147], declares
    #  no condition names at all.
    # =========================================================================
    #
    # --- 03  OI-hold-flag  pic x.  [plwsoi.cob:L38] --------------------------
    _spec(
        "payment-held", ('"H"',), _ALNUM, "OI-hold-flag", _PLWSOI, 39, 0,
        "The purchase side's payment hold. It has no sales counterpart: "
        "copybooks/slwsoi.cob declares no hold flag at all.",
    ),
    #
    # --- 03  OI-Status  pic 9.  [plwsoi.cob:L53] -----------------------------
    _spec(
        "S-Open", ("zero",), _FIG, "OI-Status", _PLWSOI, 54, 0,
        "Figurative constant; reads as 0. The same name, carrier and value as "
        "[copybooks/slwsoi.cob:L48], which is why identity here is the "
        "declaration rather than the name.",
    ),
    _spec(
        "S-Closed", ("1",), _SINGLE, "OI-Status", _PLWSOI, 55, 1,
        "LIVE at [purchase/pl060.cbl:L594], [purchase/pl060.cbl:L799] and "
        "[purchase/pl100.cbl:L342] - the last reached through the nested COPY "
        "at [copybooks/plwsoi5C.cob:L19]. Its sales twin at "
        "[copybooks/slwsoi.cob:L49] carries the trailing comment \"Paid\"; "
        "this line carries none.",
    ),
    # =========================================================================
    #  copybooks/irswsnl.cob - 2 rows. The IRS nominal account type, and the
    #  only two declarations in the registry written with the `value IS`
    #  spelling. BOTH are LIVE: [common/acasirsub1.cbl:L577] and
    #  [common/acasirsub1.cbl:L616] test `Owner`, and
    #  [common/acasirsub1.cbl:L414] and [common/acasirsub1.cbl:L506] test `Sub`.
    # =========================================================================
    #
    # --- 03  NL-Type  pic x.  [irswsnl.cob:L12] ------------------------------
    _spec(
        "Owner", ('"O"',), _ALNUM, "NL-Type", _IRSWSNL, 13, 0,
        "Declared `value is \"O\"`. The optional `IS` is noise words to the "
        "compiler and carries no meaning, so `value_clause_text` renders "
        "`\"O\"` and matches the generated dictionary, which records the "
        "clause the same way. LIVE at [common/acasirsub1.cbl:L577] and "
        "[common/acasirsub1.cbl:L616].",
    ),
    _spec(
        "Sub", ('"S"',), _ALNUM, "NL-Type", _IRSWSNL, 14, 1,
        "Declared `value is \"S\"`. LIVE at [common/acasirsub1.cbl:L414] and "
        "[common/acasirsub1.cbl:L506]. Its three-letter name is a substring of "
        "many identifiers, `WS-Sub-Function` among them, so a search for it "
        "needs word boundaries - which is why the liveness check that found "
        "these call sites used them.",
    ),
    # =========================================================================
    #  copybooks/Test-Data-Flags.cob - 2 rows. The two DAL logging switches,
    #  present in every ACAS module per the copybook's own header. `Testing-1`
    #  is the most widely tested condition name in the whole registry: every
    #  file handler gates its logging on it, for example
    #  [common/acas000.cbl:L495] and [common/acas000.cbl:L546].
    # =========================================================================
    #
    # --- 03  SW-Testing  pic 9  value 1.  [Test-Data-Flags.cob:L10] ----------
    _spec(
        "Testing-1", ("1",), _SINGLE, "SW-Testing", _TESTFLAGS, 11, 0,
        "Its conditional variable is initialised to 1 in the FROZEN copybook, "
        "with the maintainer's own alternative `zero` sitting beside it as a "
        "trailing comment, so file-handler logging is ON by default and cannot "
        "be turned off without editing a frozen file. That is a reproduced "
        "condition, not a defect to repair (rule R-4): the header at "
        "[copybooks/Test-Data-Flags.cob:L3-L4] says to set it to zero when "
        "testing is complete, and it was not. LIVE in every handler, e.g. "
        "[common/acas000.cbl:L495] and [common/acas000.cbl:L546].",
    ),
    #
    # --- 03  SW-Testing-2  pic 9  value zero.  [Test-Data-Flags.cob:L15] -----
    _spec(
        "Testing-2", ("1",), _SINGLE, "SW-Testing-2", _TESTFLAGS, 16, 0,
        "The second switch, whose carrier IS initialised to zero, so this one "
        "is off by default - the asymmetry with `SW-Testing` is the frozen "
        "source's. The copybook's comment at "
        "[copybooks/Test-Data-Flags.cob:L13] describes it as for displays of "
        "`ws-where` and similar.",
    ),
)


# =============================================================================
#  DERIVING A UNIQUE PREDICATE NAME FOR EVERY DECLARATION
# =============================================================================


def _copybook_stem(copybook: str) -> str:
    """The identifier-safe stem of a copybook path, for disambiguating a name.

    `copybooks/slwsinv2.cob` yields `slwsinv2` and
    `copybooks/Test-Data-Flags.cob` yields `test_data_flags`, so a predicate name
    built from it is a valid Python identifier in lower case, matching the
    `is_<name>` convention the rest of the module uses.

    Args:
        copybook: The copybook's repository-relative path.

    Returns:
        Its file stem, folded and with every non-alphanumeric character turned
        into an underscore.
    """
    stem = copybook.rsplit("/", 1)[-1]
    if stem.endswith(".cob"):
        stem = stem[: -len(".cob")]
    return "".join(
        character if character.isalnum() else "_" for character in stem
    ).casefold()


def _with_predicate_names(
    rows: tuple[ConditionNameSpec, ...],
) -> tuple[ConditionNameSpec, ...]:
    """Fill in each row's `predicate_name`, guaranteeing uniqueness.

    Uniqueness is a property of the whole registry, so it cannot be settled row
    by row inside `_spec`. This makes one pass to count how often each FOLDED
    COBOL name occurs and a second to name the rows:

        occurs once   `predicate_name` is `python_name` unchanged, so all of the
                      established predicate names are exactly what they were.
        occurs twice
        or more       `python_name + "_" + <copybook stem>`, so
                      `is_pending_slwsinv`, `is_pending_slwsinv2`,
                      `is_pending_plwspinv` and `is_pending_plwspinv2` are four
                      distinct predicates over four distinct value sets.

    That suffix is sufficient because no condition name is declared twice within
    one copybook - `BY_LOCATOR` and the module's own tests assert it - and it is
    the right suffix because the copybook is what actually distinguishes the
    declarations a reader is trying to tell apart.

    Rows are returned in the SAME ORDER they came in (rule R-6), rebuilt with
    `dataclasses.replace` so nothing is mutated in place.

    Args:
        rows: The registry rows, in registry order, with `predicate_name` empty.

    Returns:
        The same rows in the same order, each carrying a unique
        `predicate_name`.
    """
    occurrences: dict[str, int] = dict()
    for row in rows:
        folded = row.cobol_name.casefold()
        occurrences[folded] = occurrences.get(folded, 0) + 1
    return tuple(
        dataclasses.replace(
            row,
            predicate_name=(
                row.python_name
                if occurrences[row.cobol_name.casefold()] == 1
                else row.python_name + "_" + _copybook_stem(row.copybook)
            ),
        )
        for row in rows
    )


# The published registry: the rows above, each carrying a unique
# `predicate_name`. Everything downstream walks THIS tuple.
CONDITION_NAMES: Final[tuple[ConditionNameSpec, ...]] = _with_predicate_names(
    _REGISTRY_ROWS
)


#  LOOKUP AND ORDERED ACCESS

# Every declaration of a name, keyed by the EXACT COBOL spelling. THE PRIMARY
# INDEX, because a name does not identify a declaration: fourteen names are
# declared in more than one copybook with different value clauses, so the honest
# answer to "what is `pending`?" is a tuple of four rows, not one of them chosen
# silently. A read-only proxy over an insertion-ordered dictionary, and each
# tuple is in registry order (rule R-6).
SPECS_BY_COBOL_NAME: Final[Mapping[str, tuple[ConditionNameSpec, ...]]] = (
    types.MappingProxyType(
        {
            name: tuple(
                spec for spec in CONDITION_NAMES if spec.cobol_name == name
            )
            for name in dict.fromkeys(
                spec.cobol_name for spec in CONDITION_NAMES
            )
        }
    )
)

# The names declared MORE THAN ONCE, each against its declarations, in registry
# order. Published rather than left implicit so that the collision is a
# documented property of the frozen source a caller can enumerate, and so a test
# can assert the count (rule R-5). Fourteen names, thirty-seven declarations.
DUPLICATED_COBOL_NAMES: Final[Mapping[str, tuple[ConditionNameSpec, ...]]] = (
    types.MappingProxyType(
        {
            name: specs
            for name, specs in SPECS_BY_COBOL_NAME.items()
            if len(specs) > 1
        }
    )
)

# Keyed by the EXACT COBOL spelling for the names declared EXACTLY ONCE, so a
# name copied out of a copybook finds its row when - and only when - that row is
# the unambiguous answer. Every one of the 122 unambiguous names is here,
# including all of the operation, batch, system and sales-ledger vocabularies
# the rest of the migration is written against; the fourteen ambiguous names are
# deliberately ABSENT, because publishing one arbitrary declaration of `pending`
# under that key is precisely the collapse this registry must not perform. Reach
# them through `SPECS_BY_COBOL_NAME`, or through `lookup` with a `copybook=`.
BY_COBOL_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {
        name: specs[0]
        for name, specs in SPECS_BY_COBOL_NAME.items()
        if len(specs) == 1
    }
)

# The same unambiguous rows keyed by their derived predicate name, for a caller
# holding the Python side of the mapping - `dal/status.py` generating member
# names, or docs/migration/traceability.md rendering the two columns side by
# side. For an unambiguous row `python_name` and `predicate_name` are equal, so
# this index is keyed on either.
BY_PYTHON_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {spec.python_name: spec for spec in BY_COBOL_NAME.values()}
)

# EVERY row keyed by its locator, which is unique across all 159 - one `88` per
# line. The index that identifies a DECLARATION rather than a name, and the one
# a traceability document walks.
BY_LOCATOR: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {spec.locator: spec for spec in CONDITION_NAMES}
)

# A case-insensitive index over the unambiguous names, private because the
# PUBLISHED key is the exact spelling. COBOL is case-insensitive about names, so
# `lookup` accepts `STATUS-OPEN` and `status-open` as well; but the registry must
# not appear to have two spellings of one row, so this stays behind the accessor.
_BY_FOLDED_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {
        spec.cobol_name.casefold(): spec
        for spec in BY_COBOL_NAME.values()
    }
)

# Every declaration keyed by its FOLDED name, so a case-insensitive lookup of an
# ambiguous name can report all of its locators rather than merely failing.
_SPECS_BY_FOLDED_NAME: Final[Mapping[str, tuple[ConditionNameSpec, ...]]] = (
    types.MappingProxyType(
        {
            folded: tuple(
                spec
                for spec in CONDITION_NAMES
                if spec.cobol_name.casefold() == folded
            )
            for folded in dict.fromkeys(
                spec.cobol_name.casefold() for spec in CONDITION_NAMES
            )
        }
    )
)

# The per-copybook composition, published as data so the count can be checked
# rather than trusted: 30 + 8 + 60 + 8 + 2 + 12 + 12 + 2 + 12 + 6 + 3 + 2 + 2
# = 159. Built by walking `CONDITION_NAMES` in order, so the copybooks appear in
# the order the registry introduces them.
COUNTS_BY_COPYBOOK: Final[Mapping[str, int]] = types.MappingProxyType(
    {
        copybook: sum(
            1 for spec in CONDITION_NAMES if spec.copybook == copybook
        )
        for copybook in dict.fromkeys(spec.copybook for spec in CONDITION_NAMES)
    }
)

# The number of condition names declared on `Fs-Reply`, read from the frozen
# file. `03 Fs-Reply pic 99.` at [copybooks/wsfnctn.cob:L25] carries no `88`
# anywhere in the frozen tree; its 0 / 10 / 21 / 22 / 23 / 99 value set belongs
# to `dal/status.py` per Agent Action Plan section 0.4.1.5. Published so the
# absence reads as deliberate rather than overlooked, and so a test can assert
# it (rules R-3, R-5).
FS_REPLY_CONDITION_NAME_COUNT: Final[int] = 0


def specs_for_name(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> tuple[ConditionNameSpec, ...]:
    """Every declaration of one condition name, narrowed by copybook or carrier.

    The honest primitive the rest of the lookup surface is built on: a name may
    have several declarations with different value clauses, so this returns all
    of the matches and lets the caller say which it meant.

    Matching on the name is case-INSENSITIVE, because COBOL is: a caller reading
    `status-open` out of [general/gl070.cbl:L314] finds `Status-Open` as declared
    at [copybooks/wsbatch.cob:L26]. The two narrowing arguments match the same
    way, so `conditional_variable="IH-STATUS"` finds `ih-status`.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook's repository-relative path,
            in any casing - `"copybooks/slwsinv2.cob"`.
        conditional_variable: Optionally, the owning field's COBOL name, in any
            casing - `"sih-status"`.

    Returns:
        The matching declarations in registry order, or an empty tuple. Empty is
        a real answer here, not an error - `find` and `is_declared` are built on
        it.
    """
    probe = cobol_name.casefold()
    matches = _SPECS_BY_FOLDED_NAME.get(probe, ())
    if copybook is not None:
        wanted_file = copybook.casefold()
        matches = tuple(
            spec for spec in matches if spec.copybook.casefold() == wanted_file
        )
    if conditional_variable is not None:
        wanted_carrier = conditional_variable.casefold()
        matches = tuple(
            spec
            for spec in matches
            if spec.conditional_variable.casefold() == wanted_carrier
        )
    return matches


def lookup(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> ConditionNameSpec:
    """Find ONE row by its COBOL condition name, unambiguously.

    The exact spelling is tried first, then a case-insensitive match, because
    COBOL is case-insensitive about names and a caller reading
    [general/gl070.cbl:L314] finds `status-open` in lower case while
    [copybooks/wsbatch.cob:L26] declares `Status-Open`. Both reach the same row.

    AN AMBIGUOUS NAME IS REFUSED, NOT GUESSED. Fourteen names are declared in
    more than one copybook with different value clauses, so `lookup("pending")`
    has four candidate answers and no basis for choosing between them. It raises,
    listing the locators, and `copybook=` or `conditional_variable=` settles it:

        lookup("pending", copybook="copybooks/slwsinv2.cob")

    That refusal is the whole point of the identity design. Returning the first
    declaration would make `is_pending` mean whichever copybook happens to be
    transcribed earliest, and a program module testing a purchase invoice would
    silently get a sales invoice's value set.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook's repository-relative path,
            to pick between declarations of one name.
        conditional_variable: Optionally, the owning field's COBOL name, for the
            same purpose.

    Returns:
        Its row.

    Raises:
        KeyError: No row of that name, or several and no way to tell which was
            meant. Both are PROGRAMMER errors - a name that does not exist in the
            frozen copybooks, or a question that has more than one answer - and
            no data value can cause either. Contrast `evaluate`, which returns
            False for a value that matches nothing (rule R-3).
    """
    if copybook is None and conditional_variable is None:
        found = BY_COBOL_NAME.get(cobol_name)
        if found is not None:
            return found
        folded = _BY_FOLDED_NAME.get(cobol_name.casefold())
        if folded is not None:
            return folded

    matches = specs_for_name(
        cobol_name,
        copybook=copybook,
        conditional_variable=conditional_variable,
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise KeyError(
            _unknown_name_message(
                cobol_name,
                copybook=copybook,
                conditional_variable=conditional_variable,
            )
        )
    raise KeyError(_ambiguous_name_message(cobol_name, matches))


def find(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> ConditionNameSpec | None:
    """Find one row by its COBOL condition name, or None.

    The non-raising companion to `lookup`, for a caller probing whether a name
    is declared at all - a traceability report walking names harvested from
    program source, for instance.

    An AMBIGUOUS name returns None rather than a guess, for the same reason
    `lookup` raises: there is no single row to return. Use `specs_for_name` to
    see all of them, or `is_declared` to ask only whether the name exists.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook's repository-relative path.
        conditional_variable: Optionally, the owning field's COBOL name.

    Returns:
        Its row, or None when the registry declares no such name or declares
        several and none was singled out.
    """
    if copybook is None and conditional_variable is None:
        found = BY_COBOL_NAME.get(cobol_name)
        if found is not None:
            return found
    matches = specs_for_name(
        cobol_name,
        copybook=copybook,
        conditional_variable=conditional_variable,
    )
    return matches[0] if len(matches) == 1 else None


def is_declared(cobol_name: str) -> bool:
    """Whether the frozen copybooks declare a condition name of this name at all.

    The pure existence probe, which `find` cannot serve because `find` returns
    None for an ambiguous name that certainly does exist. A traceability report
    harvesting names from program source wants this question, not `find`'s.

    Args:
        cobol_name: The condition name, in any casing.

    Returns:
        True when at least one declaration carries that name.
    """
    return bool(_SPECS_BY_FOLDED_NAME.get(cobol_name.casefold(), ()))


def _unknown_name_message(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> str:
    """Explain an unknown condition name and offer the nearest spellings.

    Near misses are found by a plain substring test rather than an edit
    distance, which is enough to catch the realistic mistakes - a wrong prefix
    (`FS-` for `FA-FS-`), a wrong separator, a partial name - and keeps the
    message reproducible. Candidates are drawn by walking `CONDITION_NAMES`, so
    their order is the registry's and two calls give the same message
    (rule R-6).

    Args:
        cobol_name: The name that was not found.
        copybook: The copybook the caller narrowed to, if any. Named in the
            message, because a name that exists but not in THAT file is a
            different mistake from a name that does not exist at all.
        conditional_variable: The carrier the caller narrowed to, if any.

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
    narrowed = ""
    if copybook is not None or conditional_variable is not None:
        elsewhere = _SPECS_BY_FOLDED_NAME.get(cobol_name.casefold(), ())
        narrowed = (
            " The search was narrowed to "
            + (("copybook " + repr(copybook)) if copybook is not None else "")
            + (
                " and " if copybook is not None
                and conditional_variable is not None else ""
            )
            + (
                ("conditional variable " + repr(conditional_variable))
                if conditional_variable is not None else ""
            )
            + "."
        )
        if elsewhere:
            narrowed = narrowed + (
                " The name IS declared, at "
                + ", ".join(spec.locator for spec in elsewhere)
                + "; `SPECS_BY_COBOL_NAME` lists every declaration."
            )
    opening = (
        "No 88-level condition name " + repr(cobol_name) + " is declared in "
        "the frozen copybooks this registry transcribes. It holds "
        + str(len(CONDITION_NAMES))
        + " condition names from "
        + str(len(COUNTS_BY_COPYBOOK))
        + " copybooks; `SPECS_BY_COBOL_NAME` lists every one under its exact "
        "COBOL spelling."
    )
    if not near:
        return (
            opening + narrowed
            + " Nothing similar was found. Adding a condition name the "
            "copybooks do not declare is forbidden by rule R-3."
        )
    return opening + narrowed + " Did you mean: " + ", ".join(near[:8]) + "?"


def _ambiguous_name_message(
    cobol_name: str, matches: tuple[ConditionNameSpec, ...]
) -> str:
    """Explain that a name has several declarations and how to pick one.

    Every candidate is named with its locator, its value clause and its carrier,
    because the value clauses are what differ and are therefore what the caller
    has to choose between. Candidates are listed in registry order, so the
    message is reproducible (rule R-6).

    Args:
        cobol_name: The ambiguous name as the caller spelled it.
        matches: Its declarations, in registry order.

    Returns:
        A message naming every candidate and the two ways to disambiguate.
    """
    candidates = "; ".join(
        spec.cobol_name + " " + spec.value_clause_text
        + " on " + spec.conditional_variable + " [" + spec.locator + "]"
        for spec in matches
    )
    return (
        "The condition name " + repr(cobol_name) + " is declared "
        + str(len(matches))
        + " times in the frozen copybooks, with value clauses that differ, so "
        "there is no single row to return: " + candidates + ". Say which by "
        "passing copybook= or conditional_variable=, or take them all from "
        "`SPECS_BY_COBOL_NAME`. Returning one of them silently would make the "
        "name mean whichever copybook this registry happens to transcribe "
        "first, which is the collapse rule R-4 forbids. COBOL meets the same "
        "problem and answers it the same way - anomaly A-21 records that "
        "field-name collisions force QUALIFIED references at "
        "[general/gl070.cbl:L510]; `qualified_cobol_name` renders that form."
    )


def values_for(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> tuple[str, ...]:
    """The value tokens of one condition name, in declaration order.

    Published for `dal/status.py`, which builds its call-site enumerations from
    this registry rather than transcribing the values a second time - a second
    transcription of fifteen out-of-numeric-order function codes being exactly
    the error rule R-5 exists to prevent.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook, to pick between
            declarations of one name.
        conditional_variable: Optionally, the owning field's COBOL name, for the
            same purpose.

    Returns:
        Its tokens as `str`, in declaration order. `("1", "2", "4")` for
        `OS-Single`; `('"Y"',)` for `IRS-Used`; `("0", "1")` for the bounds of
        `FS-Valid-Options`; `('"P"', '"p"')` for `pending` in
        `copybooks/slwsinv.cob`.

    Raises:
        KeyError: No row of that name, or several and none singled out.
    """
    return lookup(
        cobol_name,
        copybook=copybook,
        conditional_variable=conditional_variable,
    ).values


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
        transcribes no such copybook. `COUNTS_BY_COPYBOOK` names the thirteen it
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


#  THE ONE GENERIC PREDICATE


def evaluate(
    spec_or_name: ConditionNameSpec | str,
    value: int | str | decimal.Decimal,
    *,
    descriptor: FieldDescriptor | None = None,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> bool:
    """Whether one value satisfies one 88-level condition name.

    This is the whole of the module's behaviour; every named predicate below is a
    thin wrapper over it. It answers a question and takes no decision - what to do
    about a True or a False belongs to the program layer.

    HOW THE COMPARISON IS MADE
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
        text shapes       Both sides are space-padded on the right to a common
                          width and compared character for character. The
                          literal's delimiters are not part of its value.
                          `ALPHANUMERIC` has one literal; `ALPHANUMERIC_LIST`
                          tests membership over ALL of its literals, so
                          `pending` [copybooks/slwsinv.cob:L53] holds for "P"
                          and for "p" while `pending`
                          [copybooks/slwsinv2.cob:L72] holds for "P" alone.

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
            character wide, so passing it changes no answer for any of them -
            it is honoured so that a wider field would behave correctly too.
        copybook: Optionally, the declaring copybook, used only when
            `spec_or_name` is a NAME and that name has several declarations.
            Ignored when a row was passed, because a row is already one
            declaration.
        conditional_variable: Optionally, the owning field's COBOL name, for the
            same purpose.

    Returns:
        True when the condition name holds for that value, otherwise False.

    Raises:
        TypeError: The value is a `float` or a `complex` (rule R-2), or is not
            a type a COBOL field can hold.
        KeyError: `spec_or_name` is a name the registry does not declare, or one
            it declares several times and neither narrowing argument said which.
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
        lookup(
            spec_or_name,
            copybook=copybook,
            conditional_variable=conditional_variable,
        )
    )

    if spec.is_alphanumeric:
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
    """Test a text conditional variable's value against the clause's literals.

    MEMBERSHIP over every literal the clause declares, which is what COBOL does
    for an alphanumeric condition name exactly as it does for a numeric
    `VALUE_LIST`. A one-literal `ALPHANUMERIC` therefore behaves as it always
    did - one candidate - while an `ALPHANUMERIC_LIST` tests all of them, so
    `pending` at [copybooks/slwsinv.cob:L53] holds for "P" and for "p" because
    its own line says `values "P" "p"`.

    The width is computed against the LONGEST candidate as well as the value and
    the declared field, so padding is the same for every comparison in one call
    and a short candidate cannot match by being padded differently from a long
    one.

    Args:
        spec: The row, of either alphanumeric shape.
        value: The value. A non-`str` is read through `str`, so a caller
            holding a one-character value as an int still gets an answer rather
            than an exception - and gets False, because a digit is not the
            letter the literal names.
        descriptor: The conditional variable's descriptor, or None. Its
            `character_length` supplies the declared field width to pad to.

    Returns:
        True when the padded value matches any padded literal character for
        character, case-SENSITIVELY. Otherwise False.
    """
    literals = spec.literal_texts()
    text = value if isinstance(value, str) else str(value)
    width = len(text)
    for literal in literals:
        width = max(width, len(literal))
    if descriptor is not None and descriptor.character_length:
        width = max(width, descriptor.character_length)
    padded = _pad(text, width)
    return any(padded == _pad(literal, width) for literal in literals)


def _build_predicate(
    spec: ConditionNameSpec,
) -> Callable[[int | str | decimal.Decimal], bool]:
    """Build the one-argument predicate for one registry row.

    Shared by `predicate_for` and by `PREDICATES`, so that a predicate obtained
    either way is built the same way and carries the same name and docstring.

    Args:
        spec: The row.

    Returns:
        A callable taking one value and returning whether that declaration holds
        for it. It closes over the row, so it does no lookup per call and keeps
        `evaluate`'s semantics exactly, including returning False rather than
        raising for a value that matches nothing.
    """

    def _predicate(value: int | str | decimal.Decimal) -> bool:
        """Whether the closed-over condition name holds for one value."""
        return evaluate(spec, value)

    _predicate.__name__ = spec.predicate_name
    _predicate.__qualname__ = spec.predicate_name
    _predicate.__doc__ = (
        "Whether `" + spec.declaration_text + "` holds for one value. "
        "Declared at [" + spec.locator + "] on " + spec.conditional_variable
        + "."
    )
    return _predicate


def predicate_for(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> Callable[[int | str | decimal.Decimal], bool]:
    """A one-argument predicate for any of the registry's condition names.

    The reason this module does not carry 159 near-identical functions. The
    condition names the Agent Action Plan calls out, and the nineteen the
    migrated cycle tests from the nine record copybooks, have their own published
    predicates below for readability at the call site; every other row is reached
    through here, through `PREDICATES`, or through `evaluate` directly.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook, to pick between
            declarations of one name - a name declared four times has four
            different predicates and this says which is wanted.
        conditional_variable: Optionally, the owning field's COBOL name, for the
            same purpose.

    Returns:
        A callable taking one value and returning whether the condition name
        holds for it.

    Raises:
        KeyError: No row of that name, or several and none singled out. For an
            ambiguous name the message lists every candidate with its value
            clause, because the value clauses are what differ.
    """
    return _build_predicate(
        lookup(
            cobol_name,
            copybook=copybook,
            conditional_variable=conditional_variable,
        )
    )


# A predicate for EVERY ONE of the 159 declarations, keyed by the row's unique
# `predicate_name`. This is the coverage guarantee rule R-5 asks for: not one
# condition name in the frozen closure is without a named, callable test, and a
# name declared four times has four predicates over four value sets rather than
# one predicate over whichever was transcribed first.
#
# Built by walking `CONDITION_NAMES`, so its order is the registry's (rule R-6),
# and wrapped in a read-only proxy so a caller cannot add a predicate for a
# condition name the copybooks do not declare (rule R-3).
#
# The named `is_*` functions below are a READABILITY surface over the same
# `evaluate`, for the vocabularies the plan calls out and the rows the cycle
# tests. They are not the coverage guarantee, and they do not duplicate logic -
# each is one call into `evaluate` against a spec bound at import time.
PREDICATES: Final[
    Mapping[str, Callable[[int | str | decimal.Decimal], bool]]
] = types.MappingProxyType(
    {spec.predicate_name: _build_predicate(spec) for spec in CONDITION_NAMES}
)


# =============================================================================
#  THE PUBLISHED PREDICATES
# =============================================================================
#
# 57 named predicates, in two groups:
#
#   38  the 24-name operation vocabulary from copybooks/wsfnctn.cob, plus the 14
#       condition names the Agent Action Plan calls out by name in section
#       0.3.1's example list and section 0.4.1.4's transformation row.
#   19  every declaration of the nine condition names that in-scope source
#       ACTUALLY TESTS outside those four copybooks - the live rows listed in
#       this module's docstring. All nineteen are named because a call site
#       reading `is_pending_slwsinv2(...)` says which of the four `pending`
#       declarations it means, whereas `evaluate(lookup("pending", ...), ...)`
#       makes the reader reconstruct it.
#
# Every OTHER row of the 159 is reached through `PREDICATES`, `predicate_for` or
# `evaluate`, so this module does not become 159 near-identical functions. The
# coverage guarantee is `PREDICATES`, which holds all 159; the functions below
# are the readability surface over the rows that are called for.
#
# Each row is bound to its spec HERE, at import time, so a mistyped condition
# name raises immediately rather than at some later call site. The bindings
# also read as a table of the published surface. Rows whose COBOL name is
# declared in more than one copybook are bound by LOCATOR rather than by name,
# because `BY_COBOL_NAME` deliberately holds only the unambiguous names and an
# unqualified lookup of an ambiguous one raises.

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

# The nineteen live rows outside those four copybooks. Unambiguous names are
# bound by name; the rest by locator, since their COBOL name resolves to two,
# three or four different value sets and `BY_COBOL_NAME` publishes none of them.
_TESTING_1: Final[ConditionNameSpec] = BY_COBOL_NAME["Testing-1"]
_OWNER: Final[ConditionNameSpec] = BY_COBOL_NAME["Owner"]
_SUB: Final[ConditionNameSpec] = BY_COBOL_NAME["Sub"]
_SUPPLIER_DEAD: Final[ConditionNameSpec] = BY_COBOL_NAME["Supplier-dead"]

_PENDING_SLWSINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv.cob:L53"
]
_PENDING_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L72"
]
_PENDING_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L41"
]
_PENDING_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L41"
]

_APPLIED_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L74"
]
_APPLIED_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L43"
]
_APPLIED_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L43"
]

_IH_ANALYISED_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L89"
]
_IH_ANALYISED_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L53"
]
_IH_ANALYISED_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L53"
]

_IL_ANALYISED_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L105"
]
_IL_ANALYISED_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L83"
]
_IL_ANALYISED_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L72"
]

_S_CLOSED_SLWSOI: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsoi.cob:L49"
]
_S_CLOSED_PLWSOI: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwsoi.cob:L55"
]


#  File-Function - the fifteen operation codes  [copybooks/wsfnctn.cob:L89-L105]


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


#  Access-Type - the nine access types  [copybooks/wsfnctn.cob:L108-L116]


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


#  WS-Ledger - which ledger a batch belongs to  [copybooks/wsbatch.cob:L16-L18]


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


#  Batch-Status  [copybooks/wsbatch.cob:L26-L27]


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


#  Cleared-Status  [copybooks/wsbatch.cob:L30-L32]


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


#  IRS-Instead - the three-state fan-out  [copybooks/wssystem.cob:L180-L181]
#  THREE states, TWO condition names. The third state is space, and for space
#  BOTH predicates below are False. There is no third condition name, and
#  adding one would breach rule R-3. The switch decides WHICH TABLES A RUN
#  TOUCHES, so a scenario must pin it explicitly (Agent Action Plan 0.6.4).


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


#  Date-Form  [copybooks/wssystem.cob:L129-L132]


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


# -----------------------------------------------------------------------------
#  THE NINETEEN LIVE ROWS OUTSIDE THE FOUR COPYBOOKS ABOVE
#
#  Nine COBOL names, nineteen declarations. Where a name is declared more than
#  once the function name carries the copybook stem, exactly as `PREDICATES`
#  derives it, so the two surfaces never disagree about which declaration a
#  given predicate name means.
#
#  WHICH ONE A PROGRAM ACTUALLY SEES IS DECIDED BY ITS `COPY` STATEMENTS, and
#  the answer is not always the obvious one - three of the four programs that
#  test `S-Closed` reach its copybook through a nested `COPY ... REPLACING`
#  rather than naming it. Each docstring below records the copy path it
#  verified, so a call site can be checked against the frozen source rather
#  than against an assumption.
# -----------------------------------------------------------------------------


def is_supplier_dead(value: int | str | decimal.Decimal) -> bool:
    """Whether `Purch-Status` holds `Supplier-dead`, value 0.

    Declared at [copybooks/wspl.cob:L20] and LIVE at
    [purchase/pl060.cbl:L503], which copies the layout directly at
    [purchase/pl060.cbl:L146].

    The carrier is `pic 9`, so this is the numeric 0 and not the character
    "0"; `is_supplier_live` is its complement over the two declared values,
    but the carrier can hold any digit and for 2 through 9 BOTH are False.
    Adding a third condition name to cover that would breach rule R-3.

    Args:
        value: The `Purch-Status` value.

    Returns:
        True when it is 0.
    """
    return evaluate(_SUPPLIER_DEAD, value)


def is_pending_slwsinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `sih-status` holds `pending`, the literals "P" or "p".

    Declared `values "P" "p".` at [copybooks/slwsinv.cob:L53] - TWO literals,
    upper case first, tested by membership. This is the sales invoice layout
    reached by [common/acas016.cbl]; the sibling declaration at
    [copybooks/slwsinv2.cob:L72] admits "P" ALONE, so the two predicates are
    not interchangeable and neither may be folded into the other (rule R-4).

    Args:
        value: The `sih-status` value, one character.

    Returns:
        True when it is "P" or "p".
    """
    return evaluate(_PENDING_SLWSINV, value)


def is_pending_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `pending`, the literal "P".

    Declared `value "P".` at [copybooks/slwsinv2.cob:L72] - ONE literal, so
    lower-case "p" is False here even though the three sibling declarations
    of the same name accept it. LIVE at [sales/sl055.cbl:L433], which copies
    this layout at [sales/sl055.cbl:L158].

    The single-literal form is the divergence, not a transcription slip: it is
    reproduced because rule R-4 makes the frozen declaration the specification.

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "P".
    """
    return evaluate(_PENDING_SLWSINV2, value)


def is_applied_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `applied`, the literal "Z".

    Declared `value "Z".` at [copybooks/slwsinv2.cob:L74] and LIVE at
    [sales/sl055.cbl:L427]. One literal, so "z" is False.

    [copybooks/slwsinv.cob:L55] declares the same idea under the DIFFERENT
    name `sapplied`, with values "Z" and "z"; that spelling is registered as
    its own row and is NOT reachable through this predicate.

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "Z".
    """
    return evaluate(_APPLIED_SLWSINV2, value)


def is_ih_analyised_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-update` holds `ih-analyised`, the literal "Z".

    Declared `value "Z".` at [copybooks/slwsinv2.cob:L89] and LIVE at
    [sales/sl055.cbl:L427] and [sales/sl055.cbl:L440] - the invoice-header
    analysis flag the extract sets once a header has been analysed. One
    literal, so "z" is False.

    Args:
        value: The `ih-update` value, one character.

    Returns:
        True when it is "Z".
    """
    return evaluate(_IH_ANALYISED_SLWSINV2, value)


def is_il_analyised_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `il-update` holds `il-analyised`, the literal "Z".

    Declared `value "Z".` at [copybooks/slwsinv2.cob:L105] and LIVE at
    [sales/sl055.cbl:L373] - the invoice-LINE analysis flag, the line-level
    counterpart of `ih-analyised`. One literal, so "z" is False.

    Args:
        value: The `il-update` value, one character.

    Returns:
        True when it is "Z".
    """
    return evaluate(_IL_ANALYISED_SLWSINV2, value)


def is_s_closed_slwsoi(value: int | str | decimal.Decimal) -> bool:
    """Whether the sales `OI-Status` holds `S-Closed`, value 1.

    Declared at [copybooks/slwsoi.cob:L49], where the maintainer's trailing
    comment reads "Paid". LIVE at [sales/sl060.cbl:L668],
    [sales/sl060.cbl:L877] and [sales/sl100.cbl:L350] - in every case a
    `go to` that SKIPS the open-item record, so the predicate decides whether
    a paid item is reprocessed.

    Neither program names this copybook: both copy [copybooks/slwsoi3.cob],
    at [sales/sl060.cbl:L279] and [sales/sl100.cbl:L219], and that copybook
    copies this one under a REPLACING clause at [copybooks/slwsoi3.cob:L18].
    [copybooks/slwssoi.cob:L50], also in scope of [sales/sl060.cbl:L280],
    declares the same test as `si-s-closed`; that name is not among the
    thirteen copybooks the dictionary reports and is not reachable here.

    Args:
        value: The `OI-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_S_CLOSED_SLWSOI, value)


def is_pending_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `pending`, the literals "P" or "p".

    Declared `values "P" "p".` at [copybooks/plwspinv.cob:L41] - two literals,
    upper case first, matching [copybooks/slwsinv.cob:L53]'s VALUES while its
    NAME matches [copybooks/slwsinv2.cob:L72]'s. The purchase invoice layout
    reached by [common/acas026.cbl].

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "P" or "p".
    """
    return evaluate(_PENDING_PLWSPINV, value)


def is_applied_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `applied`, the literals "Z" or "z".

    Declared `values "Z" "z".` at [copybooks/plwspinv.cob:L43] - two literals,
    upper case first.

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "Z" or "z".
    """
    return evaluate(_APPLIED_PLWSPINV, value)


def is_ih_analyised_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-update` holds `ih-analyised`, the literals "Z" or "z".

    Declared `values "Z" "z".` at [copybooks/plwspinv.cob:L53] - two literals,
    upper case first, like every other status clause in that copybook EXCEPT
    `il-analyised` at [copybooks/plwspinv.cob:L83], which flips them.

    Args:
        value: The `ih-update` value, one character.

    Returns:
        True when it is "Z" or "z".
    """
    return evaluate(_IH_ANALYISED_PLWSPINV, value)


def is_il_analyised_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `il-update` holds `il-analyised`, the literals "z" or "Z".

    Declared `values "z" "Z".` at [copybooks/plwspinv.cob:L83] - LOWER case
    first, the one clause in that copybook to do so. The membership test makes
    the order immaterial to the ANSWER, but `value_clause_text` renders it
    verbatim so the divergence stays visible rather than being tidied away
    (rule R-4, anomaly-register discipline).

    Args:
        value: The `il-update` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_IL_ANALYISED_PLWSPINV, value)


def is_pending_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `pending`, the literals "p" or "P".

    Declared `values "p" "P".` at [copybooks/plwspinv2.cob:L41] - LOWER case
    first, which is this copybook's convention throughout. The second purchase
    invoice layout, copied by [purchase/pl055.cbl:L135].

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "p" or "P".
    """
    return evaluate(_PENDING_PLWSPINV2, value)


def is_applied_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `applied`, the literals "z" or "Z".

    Declared `values "z" "Z".` at [copybooks/plwspinv2.cob:L43] and LIVE at
    [purchase/pl055.cbl:L365], which copies this layout at
    [purchase/pl055.cbl:L135]. Lower case first.

    Its sales counterpart at [copybooks/slwsinv2.cob:L74] admits "Z" alone,
    so `is_applied_slwsinv2` and this predicate answer differently for "z".

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_APPLIED_PLWSPINV2, value)


def is_ih_analyised_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-update` holds `ih-analyised`, the literals "z" or "Z".

    Declared `values "z" "Z".` at [copybooks/plwspinv2.cob:L53] and LIVE at
    [purchase/pl055.cbl:L365] and [purchase/pl055.cbl:L370] - the purchase
    mirror of [sales/sl055.cbl:L427] and [sales/sl055.cbl:L440], but over two
    literals rather than one.

    Args:
        value: The `ih-update` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_IH_ANALYISED_PLWSPINV2, value)


def is_il_analyised_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `il-update` holds `il-analyised`, the literals "z" or "Z".

    Declared `values "z" "Z".` at [copybooks/plwspinv2.cob:L72] and LIVE at
    [purchase/pl055.cbl:L314] - the purchase mirror of
    [sales/sl055.cbl:L373], again over two literals rather than one.

    Args:
        value: The `il-update` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_IL_ANALYISED_PLWSPINV2, value)


def is_s_closed_plwsoi(value: int | str | decimal.Decimal) -> bool:
    """Whether the purchase `OI-Status` holds `S-Closed`, value 1.

    Declared at [copybooks/plwsoi.cob:L55] - the same name, carrier and value
    as [copybooks/slwsoi.cob:L49], without that line's "Paid" comment. LIVE at
    [purchase/pl060.cbl:L594], [purchase/pl060.cbl:L799] and
    [purchase/pl100.cbl:L342].

    [purchase/pl060.cbl:L152] copies this copybook directly;
    [purchase/pl100.cbl:L213] copies [copybooks/plwsoi5C.cob], which copies
    this one under a REPLACING clause at [copybooks/plwsoi5C.cob:L19].
    [copybooks/plwssoi.cob:L53] declares the same test as `si-s-closed` and is
    outside the thirteen copybooks the dictionary reports.

    Args:
        value: The `OI-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_S_CLOSED_PLWSOI, value)


def is_owner(value: int | str | decimal.Decimal) -> bool:
    """Whether `NL-Type` holds `Owner`, the literal "O".

    Declared `value is "O".` at [copybooks/irswsnl.cob:L13] - one of only two
    declarations in the registry written with the optional `IS`, which is a
    noise word and carries no meaning. LIVE at [common/acasirsub1.cbl:L577]
    and [common/acasirsub1.cbl:L616], the IRS nominal-ledger handler.

    Args:
        value: The `NL-Type` value, one character.

    Returns:
        True when it is "O".
    """
    return evaluate(_OWNER, value)


def is_sub(value: int | str | decimal.Decimal) -> bool:
    """Whether `NL-Type` holds `Sub`, the literal "S".

    Declared `value is "S".` at [copybooks/irswsnl.cob:L14] and LIVE at
    [common/acasirsub1.cbl:L414] and [common/acasirsub1.cbl:L506]. The
    sub-account type, the complement of `Owner` over the two declared values;
    for any other character both are False.

    Args:
        value: The `NL-Type` value, one character.

    Returns:
        True when it is "S".
    """
    return evaluate(_SUB, value)


def is_testing_1(value: int | str | decimal.Decimal) -> bool:
    """Whether `SW-Testing` holds `Testing-1`, value 1.

    Declared at [copybooks/Test-Data-Flags.cob:L11] and LIVE in every file
    handler - for example [common/acas000.cbl:L495] and
    [common/acas000.cbl:L546] - where `if Testing-1` gates the file-handler
    log write.

    THE FROZEN COPYBOOK INITIALISES THE CARRIER TO 1, so the switch is ON by
    default and handler logging cannot be turned off without editing a frozen
    file. That is anomaly territory, not a defect to fix: the setup log records
    the resulting log file reaching 473 MB in three minutes. The predicate
    reports the switch; it does not decide what to do about it.

    Args:
        value: The `SW-Testing` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_TESTING_1, value)


# =============================================================================
#  THE OPTIONAL CROSS-CHECK AGAINST THE GENERATED DATA DICTIONARY  (rule R-5)
#
#  Rule R-5 wants field-level traceability to be MECHANICAL rather than
#  hand-maintained, and this registry is a hand transcription - the one place in
#  the migration where 159 value clauses are typed out from thirteen frozen
#  copybooks. The check below is how that transcription is held to account: it
#  re-reads the same condition names from
#  data_dictionary/acas_posting_dictionary.json, which the generator parses out
#  of the copybooks independently, and reports every disagreement.
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
#  working-storage record name, so all thirteen copybooks and all 159 condition
#  names are verifiable and none has to be excused. That is the artifact
#  speaking, and the artifact wins; if a future regeneration drops the block,
#  the check reports it as a note naming the copybook rather than as 30
#  mismatches.
#
#  THE CHECK IS WHAT MAKES DUPLICATE NAMES SAFE. Fourteen COBOL names are
#  declared in more than one copybook, so a comparison keyed on the bare name
#  would match the wrong rows and pass. Every row is therefore matched on
#  `(copybook, cobol_name)`, which the registry guarantees is unique, and the
#  per-conditional-variable declaration order is compared inside each copybook
#  rather than across the registry.
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

# The thirteen copybooks the registry transcribes, in registry order. A tuple,
# not an iteration over `COUNTS_BY_COPYBOOK`, so the reporting order is fixed in
# the source where a reader can see it (rule R-6).
_COPYBOOKS_IN_REGISTRY_ORDER: Final[tuple[str, ...]] = (
    _WSFNCTN,
    _WSBATCH,
    _WSSYSTEM,
    _WSSL,
    _WSPL,
    _SLWSINV,
    _SLWSINV2,
    _SLWSOI,
    _PLWSPINV,
    _PLWSPINV2,
    _PLWSOI,
    _IRSWSNL,
    _TESTFLAGS,
)

# The fields of the dictionary's own condition-name record, read at import time
# from `loader.ConditionName` - the loader's binding to the one object-model
# definition. Named in the findings so a reader knows exactly which three values
# were compared, and so a change to the dictionary's representation shows up in
# the report rather than passing unnoticed.
_DICTIONARY_CONDITION_FIELDS: Final[tuple[str, ...]] = tuple(
    field.name for field in dataclasses.fields(loader.ConditionName)
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


#  THE PUBLISHED SURFACE
#  `FsReply`, `FileFunction` and `AccessType` are DELIBERATELY ABSENT. This
#  module is the registry those enumerations are built FROM, and it publishes
#  `values_for` and `specs_for_variable` so that dal/status.py can build them
#  without transcribing fifteen out-of-numeric-order function codes a second
#  time. Naming them here would collide with the module that owns them
#  (Agent Action Plan 0.5.3).

__all__ = [
    # The value sets, and the shape of a row.
    "CONDITION_NAMES",
    "ConditionKind",
    "ConditionNameSpec",
    # The lookup surface. `BY_COBOL_NAME` and `BY_PYTHON_NAME` publish only the
    # names declared exactly once; `SPECS_BY_COBOL_NAME`, `BY_LOCATOR` and
    # `DUPLICATED_COBOL_NAMES` are how the other fourteen names are reached.
    "BY_COBOL_NAME",
    "BY_LOCATOR",
    "BY_PYTHON_NAME",
    "COUNTS_BY_COPYBOOK",
    "DUPLICATED_COBOL_NAMES",
    "FS_REPLY_CONDITION_NAME_COUNT",
    "SPECS_BY_COBOL_NAME",
    "conditional_variables",
    "find",
    "is_declared",
    "lookup",
    "specs_for_copybook",
    "specs_for_name",
    "specs_for_variable",
    "values_for",
    # The one generic predicate, a predicate for any row, and the mapping that
    # holds one for EVERY row - the coverage guarantee behind rule R-5.
    "PREDICATES",
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
    # The nineteen live rows outside those four copybooks. Where a name is
    # declared more than once the copybook stem disambiguates, exactly as
    # `PREDICATES` derives it. Grouped by copybook, in registry order.
    "is_supplier_dead",
    "is_pending_slwsinv",
    "is_pending_slwsinv2",
    "is_applied_slwsinv2",
    "is_ih_analyised_slwsinv2",
    "is_il_analyised_slwsinv2",
    "is_s_closed_slwsoi",
    "is_pending_plwspinv",
    "is_applied_plwspinv",
    "is_ih_analyised_plwspinv",
    "is_il_analyised_plwspinv",
    "is_pending_plwspinv2",
    "is_applied_plwspinv2",
    "is_ih_analyised_plwspinv2",
    "is_il_analyised_plwspinv2",
    "is_s_closed_plwsoi",
    "is_owner",
    "is_sub",
    "is_testing_1",
    # The rule R-5 corroboration.
    "cross_check_against_dictionary",
]
