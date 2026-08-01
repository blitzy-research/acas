"""The Analysis code record: `01 WS-Analysis-Record` [copybooks/wsanal.cob:L9].

The smallest record layout in the migrated cycle - 36 bytes, four columns, one
of which is a three-byte key group - and the one that shows most plainly why
every field's storage metadata is looked up rather than typed by eye. Nothing
in this module computes anything. It declares three plain dataclasses that
mirror `copybooks/wsanal.cob` field for field and attaches each attribute to
its entry in the generated data dictionary.

Small is not the same as casual. This record's key is the primary key of an
in-scope table that every scenario diff inspects, and the record takes part in
the analysis-total build that `sales/sl055.cbl` and `purchase/pl055.cbl`
perform. Every rule that governs the 300-byte sales record governs this one.

WHERE THIS RECORD SITS
======================
Entity facade `Analysis`, handler `acas015` [common/acas015.cbl], bridge
`analMT` [common/analMT.cbl], table `ANALYSIS-REC` [mysql/ACASDB.sql:L31] -
the spine row Agent Action Plan section 0.2.1.1 gives, restated on
`WsAnalysisRecord` below. Section 0.6.6 tabulates that table at four columns
with the single-column primary key `PA-CODE` and zero secondary indexes, which
is what lets the harness dump be `SELECT * FROM <table> ORDER BY <primary
key>` with no tie-breaking logic. Ordering therefore belongs to
`harness/dump_tables.py` and this module supplies none - see "WHAT THIS MODULE
DELIBERATELY DOES NOT DECLARE" below.

THE COPYBOOK, WHOLE
===================
Nine declarations across nine lines, quoted here so a reader can set the
dataclasses below against the frozen source without opening it. Indentation is
the copybook's own::

     01  WS-Analysis-Record.                          L9
         03  WS-Pa-Code.                              L10
             05  Pa-System     pic x.                 L11
             05  Pa-Group.                            L12
                 07  Pa-First  pic x.                 L13
                 07  Pa-Second pic x.                 L14
         03  Pa-Gl             pic 9(6).              L15
         03  Pa-Desc           pic x(24).             L16
         03  Pa-Print          pic xxx.               L17

The file's own header, verbatim::

    *>  Record Definition For The Analysis File *      L3
    *> 36 bytes 25/3/09                                L6
    *> 24/07/16 vbc - Taken from fdanal.cob            L7

The identifiers are MIXED CASE - `WS-Pa-Code`, `Pa-System`, `Pa-Group`,
`Pa-First`, `Pa-Second`, `Pa-Gl`, `Pa-Desc`, `Pa-Print` - and are carried
below exactly as written, neither lower-cased nor raised to the column's upper
case. Every descriptor `name` is the copybook's spelling, because that is the
spelling a reader diffing this module against the frozen source looks for.

THE BRIDGE'S INLINE RECORD IS NOT THE SAME SHAPE
================================================
The bridge does not `COPY` this copybook. It declares its own record inline,
under its own name `Analysis-Rec` [common/analMT.cbl:L315], beneath a comment
recording that the buffer was generated from a source set rather than from the
copybook [common/analMT.cbl:L310-L313]; its load paragraph's call site names
that inline record too [common/analMT.cbl:L774]. Counted from
[copybooks/wsanal.cob:L9-L17] and [common/analMT.cbl:L315-L319]::

    the copybook                           the bridge's own inline record
    -------------------------------------  -----------------------------
     01  WS-Analysis-Record.                01  Analysis-Rec.
         03  WS-Pa-Code.                        03  Pa-Code   pic xxx.
             05  Pa-System     pic x.
             05  Pa-Group.
                 07  Pa-First  pic x.
                 07  Pa-Second pic x.
         03  Pa-Gl             pic 9(6).        03  Pa-Gl     pic 9(6).
         03  Pa-Desc           pic x(24).       03  Pa-Desc   pic x(24).
         03  Pa-Print          pic xxx.         03  Pa-Print  pic xxx.

Four differences, none of them repaired: the 01 is renamed; the
four-declaration key group is FLATTENED to one elementary item; that item is
also renamed, losing the `WS-` prefix; and the 05 and 07 levels disappear.
Eight declarations become four, in the same 36 bytes - byte-compatible while
structurally different, which is precisely the divergence a byte-count check
cannot catch. `Pa-Gl`, `Pa-Desc` and `Pa-Print` are identical throughout.

THIS MODULE FOLLOWS THE COPYBOOK, for a structural reason: the copybook is
what the posting programs `COPY`, so it is the field structure they
manipulate. Section 0.8.2 preserves the user's own words on the other half -
the maintainer's one-way COBOL-to-MySQL bridge DEFINES the
record-layout-to-table mapping, and "it is the data dictionary for this
migration". Both hold at once: the bridge governs which field reaches which
column, the copybook governs what the fields ARE. Neither name is adopted here
as an alias for the other.

THE FOUR-LEVEL KEY GROUP BECOMES ONE COLUMN
===========================================
`WS-Pa-Code` nests four levels deep, the level numbering JUMPING FROM 05
STRAIGHT TO 07 [copybooks/wsanal.cob:L12-L14], and the whole three-byte group
collapses into ONE `char(3)` column - recorded as a `GROUP_CONCATENATION`
derivation whose expression is the bridge's own move [common/analMT.cbl:L943].
`Pa-System`, `Pa-Group`, `Pa-First` and `Pa-Second` therefore have no columns
of their own, and are declared below regardless: R-3 forbids removing what the
copybook declares as firmly as adding what it does not, and the COBOL
addresses them by name. `WsPaCode` and `PaGroup` below carry the detail.

The column arithmetic, which is how the collapse is checked rather than
assumed: counting `WS-Pa-Code` ONCE gives four, matching section 0.6.6 and the
schema. Counting its children individually gives six, which matches nothing.

WHAT DRIFTS HERE, AND WHAT NOTABLY DOES NOT
===========================================
Three kinds cross the bridge boundary here, each recorded unadjudicated: the
dictionary holds all three layer views side by side plus an unsettled `drift`
object, and `loader.drift_for` names them exactly.

1. GROUP CONCATENATION AND PREFIX STRIP, on the key. Four declarations and
   three bytes become one `HV-PA-CODE PIC X(3)` [common/analMT.cbl:L283] and
   one `PA-CODE char(3)` [mysql/ACASDB.sql:L32]. `name=True`, nothing else.
2. STORAGE CLASS AND DIGIT WIDTH, on `Pa-Gl`: `pic 9(6)` zoned DISPLAY in the
   copybook, `PIC  9(08) COMP` binary and eight digits at the host variable,
   `mediumint(6) unsigned` back down to six at the column. `usage=True` and
   `digits=True`. The comment above `_PA_GL` below carries the locators, the
   round trip and the open question it raises.
3. THE SAME THREE BYTES SPELLED THREE WAYS, on `Pa-Print`. Carried through
   verbatim as `xxx` and never rewritten `x(3)`; the comment above `_PA_PRINT`
   below has the three spellings and their locators.

THE DESCRIPTORS REPORT THE COPYBOOK VIEW AND NOTHING ELSE - DISPLAY and six
digits for `Pa-Gl`, not COMP and not eight. Widening one to a host variable's
width would blend two layers into a view of the field that exists in neither.
Converting between them belongs to the `acas015` handler module, which is
also, for exactly that reason, a live temptation this file must not reach for
- see "LAYERING".

SIGNEDNESS DOES NOT DRIFT ANYWHERE IN THIS RECORD, and that is worth stating
outright. `Pa-Gl` is unsigned in the copybook - `pic 9(6)` carries no `S` -
unsigned at the host variable, and `unsigned` at the column;
`loader.drift_for` reports `signedness=False` on all four columns. Section
0.6.2 argues that drift in this system is "specific rather than systemic", and
this record is the count that makes the argument checkable:
`records/sales_ledger.py` loses eleven signs at the bridge,
`records/purchase_ledger.py` twelve and `records/value_analysis.py` three
money signs - and this record loses none.

Trailing-space handling is likewise not this module's business. The bridge
trims trailing spaces as it builds its statement text
[common/analMT.cbl:L991], [common/analMT.cbl:L1012],
[common/analMT.cbl:L1021], [common/analMT.cbl:L1053], and renders the numeric
field via an edited picture [common/analMT.cbl:L1000],
[common/analMT.cbl:L1062]. Bringing two table dumps into a comparable form is
a harness step, listed in its own file inventory at section 0.3.1, and happens
after both runs finish. Nothing is trimmed, padded or reshaped here.

Note on wording: this file names none of the harness's comparison step, the
adjudication vocabulary, or section 0.4.1.3's own verb for what must not
happen to an oddity. All three belong to the family of words R-4 bans
outright, so each is described rather than spelled, with the requirements they
carry unchanged - see "ODDITIES ARE PRESERVED" below.

THE DECLARED SIZE AGREES WITH THE FIELD SUM
===========================================
    WS-Pa-Code   3   =  Pa-System 1 + Pa-Group ( Pa-First 1 + Pa-Second 1 )
    Pa-Gl        6      pic 9(6)
    Pa-Desc     24      pic x(24)
    Pa-Print     3      pic xxx
    -------------------------------------------------------------------
                36      and the header declares 36 [copybooks/wsanal.cob:L6]

The sum closes, and it closes because there is no `COMP`, no `COMP-3`, no
`binary-*` usage, no `SIGN` clause and no implied decimal point anywhere in
this copybook - every item is alphanumeric or unsigned zoned DISPLAY, so the
byte count is a plain character sum with no storage-class arithmetic in it.
Four greps confirm the absences, all returning zero: no FILLER, no REDEFINES,
no 88-level condition name, and none of the computational usages.

Agreement is not unique to this record - summing the descriptors closes
against the declared header for several of these layouts. What is worth
stating is the contrast with the three that carry a DISPUTED number:
`records/gl_batch.py` carries anomaly 15, the batch record's 96-versus-98
contradiction [copybooks/wsbatch.cob:L7-L9]; `records/irs_system.py` carries a
256-versus-257 contradiction; `records/value_analysis.py` records an open
question raised by its own header. Those three are specific rather than a
systemic habit of the codebase, and this record is one of the counts that
shows it. NO length, size or byte-count constant is declared below all the
same: R-3 forbids adding what the copybook does not declare, and a constant
here would invite one in the three records where the number is disputed -
exactly where a single number cannot honestly be written down.

R-2 IS SATISFIED HERE BY AN ABSENCE
===================================
Rule R-2 admits no binary floating point into an accounting value, in
computation, in storage or in transport. This record has no monetary and no
fractional field at all: one unsigned integer and five alphanumeric items. So
the exact-decimal carrier the money-bearing records use is NOT imported here,
and its absence is the point rather than an oversight - an unused import is
noise, and R-2 is met by there being nothing fractional to carry. Counted over
the dictionary, four in-scope tables carry no fractional column, so
`records/irs_dflt.py`, `records/irs_final.py` and `records/system_final.py`
are the other record modules in this position.

    Pa-System, Pa-First, Pa-Second, Pa-Desc, Pa-Print   ->  str
    Pa-Gl                                              ->  int
    WS-Pa-Code, Pa-Group                               ->  groups, no storage

The carrier is never chosen by reading what a field "means". It is taken from
the dictionary entry's own `cobol_python_storage`, which is why `Pa-Gl` is an
`int` rather than an exact-decimal value: the copybook declares zero scale, so
integer truncation is what a store into it does.

DESCRIPTORS ARE LOOKED UP, NEVER TRANSCRIBED (R-5)
==================================================
Section 0.8.1 makes the ordering a directive rather than a preference - the
dictionary is generated from the bridge BEFORE record definitions are written,
and every Python field definition cites its entry, because that "is what
prevents fields being transcribed by eye". Section 0.3.3 states the payoff:
field metadata is "derived, not transcribed, which eliminates an entire class
transcription error". So no picture clause, digit count, scale, sign position,
storage class or character width is written by hand below; `_dictionary_keys`
and `_descriptor` carry the mechanism. Two key conventions appear, both out of
the lookup rather than out of a rule about naming::

    <TABLE-NAME>.<COLUMN-NAME>       the four column-mapped fields, e.g.
                                     ANALYSIS-REC.PA-CODE, ANALYSIS-REC.PA-GL
    <COPYBOOK-RECORD>.<FIELD-NAME>   the five column-less ones, e.g.
                                     WS-Analysis-Record.Pa-System

That the group's key is `PA-CODE` and not `WS-PA-CODE` is the clearest
demonstration in the whole records package of why a dictionary key is obtained
by LOOKUP and never by transforming an attribute name: raising `ws_pa_code` to
upper case and swapping underscores for hyphens yields a name that is not a
column, is not a key, and exists nowhere in the frozen schema.

EIGHT LOOKED UP AND NONE HAND-BUILT: all eight members take
`FieldDescriptor.from_dictionary_key`, which is the only path there is - a
finding of the lookup, not an assumption. It would be easy to reason that the
three column-less members need their metadata typed in, and it would be wrong:
the artifact covers all nine declarations, so every member has an entry to cite.
There is no locator-only factory to fall back on either - even the General
Ledger work-file records, the one population that ever had one, are catalogued
as program-source entries and bound by key. Hand-typing metadata the artifact
already holds is the transcription error class R-5 exists to close. The
ninth entry is the record's own 01, keyed
`WS-Analysis-Record.WS-Analysis-Record` [copybooks/wsanal.cob:L9]; it is a
member of nothing, so no descriptor is built for it, and it is named here so
the migration's traceability document can carry all nine.

`loader.cite(key)` returns the compact three-locator provenance string,
surfaced through `FieldDescriptor.cite()` and never reimplemented::

    ANALYSIS-REC.PA-GL  copybook=copybooks/wsanal.cob:L15
    bridge=common/analMT.cbl:L284  column=mysql/ACASDB.sql:L33

`loader.drift_for(key)` is surfaced the same way, through
`FieldDescriptor.drift()`, and is not reduced to a boolean, not summarised as
safe and not acted upon.

THE NEAR-DUPLICATE TWIN IS A TRAP (anomaly 21's class)
======================================================
`copybooks/wsval.cob`, which `records/value_analysis.py` is built from,
declares structurally the same four fields - a three-byte four-level key
group, a
print flag - then adds six numeric fields this record does not have. Eight
divergences separate the twins, every one counted::

                        this record            the twin
                        copybooks/wsanal.cob   copybooks/wsval.cob
    01-name             WS-Analysis-Record L9  WS-Value-Record L9
    key group           WS-Pa-Code L10         va-code L10
                        WS- prefixed           bare
    field prefix        Pa-                    va-
    casing              mixed case             lower case
    gap after `07`      two spaces L13-L14     one space L13-L14
    extra fields        none                   six, L18-L23
    trailing *>         absent, ends at L17    present at L24
    declared bytes      36                     66

Both files indent their 07 items by the same thirteen columns; what differs is
the gap between the level number and the field name, which is why the row
above names the gap rather than the indentation.

Section 0.6.7 entry 21 records field-name collisions across near-identical
posting copybooks as an anomaly in its own right, because in COBOL they force
qualified references. For Python the consequence is sharper: the two layouts
are similar enough to invite a shared base class, a shared descriptor table, a
mixin or a copy-and-rename, and every one would couple two records the frozen
source keeps apart, in a package whose layering contract forbids one record
module from importing another. NOTHING is shared with
`records/value_analysis.py`; `_admit` below is the pair of checks a machine can
apply against having reached the wrong record.

ODDITIES ARE PRESERVED, NEVER REPAIRED (R-4)
============================================
Section 0.8.2 preserves the user's own words:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included.
    A defect reproduced is correct; a defect fixed is a failure."

Section 0.4.1.3 says the same of this folder - oddities in the source are
preserved, never [repaired], the bracket marking a substituted word as the
note above explains. There is deliberately no winner view, no widest picture,
no settled reading and no "sensible" alternative below, and none may be
introduced.

What this module records, each with its locator at the point of use and none
of it altered. The register lives in the migration's anomaly log:

  * Three names for one layout, and the bridge's inline record flattens and
    renames the key while keeping the other three fields identical
    [copybooks/wsanal.cob:L9], [common/analMT.cbl:L315-L319].
  * The bridge's generated-buffer comment credits the buffer to a source set
    belonging to a DIFFERENT ledger [common/analMT.cbl:L310-L313] - boilerplate
    carried over verbatim into the Analysis bridge.
  * The `WS-` prefix disappears between the copybook group and the column
    [copybooks/wsanal.cob:L10], [mysql/ACASDB.sql:L32].
  * Storage class and digit width both change at the host variable and change
    back at the column [common/analMT.cbl:L284], [mysql/ACASDB.sql:L33].
  * Four declarations map to one column; three of the four map to nothing
    [common/analMT.cbl:L943].
  * The level numbering jumps 05 to 07, and sets the field name two spaces
    after that level number where the twin uses one
  * `pic xxx` is spelled out rather than written `x(3)`
    [copybooks/wsanal.cob:L17].
  * The header stamps a single-digit month, `25/3/09`, where sibling copybooks
    zero-pad, and carries the maintainer's initials
    [copybooks/wsanal.cob:L6-L7].
  * The file ends at its last field with no trailing comment line, where the
    twin has one [copybooks/wsanal.cob:L17], [copybooks/wsval.cob:L24].
  * The near-duplicate twin, under divergent names, prefix, casing and level
    spacing [copybooks/wsval.cob:L9-L17].
  * Signedness does not drift and the declared size agrees with the field sum -
    the two contrast counts above, which is why both are stated rather than
    left implied.

The artifact reports `anomaly_refs` and `ambiguity_refs` as empty for all four
of this table's entries, so none of the above is tagged in the generated
document; the register above and the question below are where they are written
down.

AN OPEN QUESTION FOR THE COMPILED ORACLE (R-6)
==============================================
Rule R-6 makes the compiled program the tie-breaker for any question reading
the frozen source cannot settle, and requires the arbitration be written down.
One question bears on this record, recorded in the migration's
ambiguity-resolutions document: `Pa-Gl` holds six digits, the host variable it
is moved into holds eight, the column is back down to six - so what does the
round trip do to a value that does not fit six digits, and what does the
column's narrowing then do to it? A third place the answer could be decided is
the statement text, where the digits are rendered through an edited picture
and sliced to eight characters [common/analMT.cbl:L1000]. The comment above
`_PA_GL` carries the remaining locators.

MEASURE IT AGAINST THE COMPILED ORACLE. No clamp, no wrap, no width check and
no guard against it is stored in this module, because storing one would settle
by assumption a question that only execution can settle - and would add a
validation R-3 forbids.

LAYERING - THIS IS A LEAF MODULE
================================
Section 0.4.3 grants `records/*.py` exactly two imports and forbids everything
else, for a stated reason: "this keeps the record layer a leaf".

    permitted   acas_posting.cobol.field         the FieldDescriptor type
                acas_posting.dictionary.loader   the descriptor lookup

Forbidden is everything else: any handler module, `programs`, `cli`, `clock`,
`dates`, `workfiles`, every other `cobol` module, `dictionary.generate`, the
compiled comparison oracle in its sibling tree, and any other module of this
package - `records/value_analysis.py` above all. Two are live temptations than
theoretical. The `acas015` handler module owns the DISPLAY-to-binary
conversion this record's one numeric field undergoes, and reaching for it
would drag a database driver into the tier section 0.4.3 promises "imports
only `cobol` and `records` and touches no database, so it runs anywhere".
`records/value_analysis.py` owns a near-identical layout, and reaching for it
would couple two records the frozen source keeps separate. Neither is
imported.

R-1 holds trivially and is stated so the reader need not check: nothing below
runs, embeds or shells out to a COBOL program, and no COBOL toolchain, no
foreign-function bridge and no database driver is reachable from here. The
COBOL is read as the specification and cited by locator, never as a
dependency.

WHAT THIS MODULE DELIBERATELY DOES NOT DECLARE
==============================================
R-3 admits no added field, no added validation and no added surface. Absent by
decision, not by omission: no key-composition helper and no text conversion
that concatenates the three key bytes; no comparison, ordering or sort
support, `harness/dump_tables.py` ordering rows by the primary key the schema
declares; no length, size or byte-count constant; no alias, subclass or second
name for the bridge's inline record; no condition-name predicate and no
enumeration, this copybook declaring no 88-level; no FILLER and no REDEFINES
member, it declaring neither; no initialiser hook, no width padding, no
analysis-code check and no general-ledger account range check, the COBOL
performing none of those here; and no exact-decimal import, for the reason
given under R-2. Nor is anything frozen - the comment above the class
definitions gives that reason, which is an R-4 one rather than a matter of
style.

DETERMINISM (R-6)
=================
Member order follows copybook declaration order, so this module and its
copybook diff by eye, and `FIELDS` is a tuple on every class, never a list.
Nothing below consults a clock, draws an unpredictable value, inspects the
process environment or reads the filesystem beyond the loader's own lazy
cached read of the generated document, and execution is strictly sequential
with no concurrency introduced. Two imports in two processes produce identical
state. The class definitions ascend the copybook's level numbers for the
reason the comment above them gives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = ["PaGroup", "WsAnalysisRecord", "WsPaCode"]


#  THE THREE FROZEN NAMES THIS MODULE IS KEYED AGAINST
# One constant each, so that the table name appears exactly once in executable
# code and a reader can see at a glance which of the three names denoting this
# layout is used for what. The bridge's own inline record name is deliberately
# NOT among them: it names a differently shaped record and this module
# offers no alias for it (see "THREE NAMES DENOTE THIS ONE LAYOUT" above).

# The MySQL table [mysql/ACASDB.sql:L31]. Left side of a column-mapped key.
_TABLE: Final[str] = "ANALYSIS-REC"

# The copybook 01 [copybooks/wsanal.cob:L9], in the copybook's own casing.
# Left side of a key for a field the bridge maps to no column.
_COPYBOOK_RECORD: Final[str] = "WS-Analysis-Record"

# The one copybook every field of this record must come from. The guard below
# turns that into a check rather than an expectation.
_COPYBOOK_FILE: Final[str] = "copybooks/wsanal.cob"

# The twin's field prefix [copybooks/wsval.cob:L10-L17]. Named so the guard can
# refuse it by name; nothing else in this module has any use for it.
_TWIN_FIELD_PREFIX: Final[str] = "va-"


def _admit(name: str, file: str) -> None:
    """Refuse an entry that did not come from this record's own copybook.

    Two guards, both aimed at one specific way of going wrong. This record's
    layout is near-identical to the Analysis Value record's - the same
    three-byte four-level key group, the same six-digit account, the same
    24-character description, the same three-character print flag - so a lookup
    that drifted onto `copybooks/wsval.cob` would return a plausible set of
    fields with plausible widths and would be caught by nothing else. The
    divergence table in this module's docstring lists all eight differences;
    these two checks are the pair a machine can apply.

    Both are `assert` rather than a raised failure on purpose: they check the
    GENERATED ARTIFACT for consistency with the frozen source at import, which
    is a build-time question about this migration, not a runtime question about
    a value. Nothing here validates data - rule R-3 admits no added validation
    - and a caller cannot reach these checks with a value of any kind. If the
    interpreter is run with assertions disabled the module still cannot bind
    the wrong field, because a name that is absent from the lookup raises when
    it is looked up.

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

    The whole of rule R-5's mechanism for this module, and the reason no key is
    written as a literal below. Each entry supplies its OWN key and its OWN
    `copybook.name`; this function only pairs the two. No name is upper-cased,
    hyphenated, prefixed or stripped on the way - which matters here more than
    almost anywhere, because the copybook group `WS-Pa-Code`
    [copybooks/wsanal.cob:L10] becomes the column `PA-CODE`
    [mysql/ACASDB.sql:L32] with its `WS-` prefix gone, so transforming the
    Python attribute name would produce `WS-PA-CODE` and find nothing.

    Two passes, because the artifact keys this record's fields two ways:

    1. `entries_for_table` yields the four column-mapped fields in column
       ordinal order, keyed `<TABLE-NAME>.<COLUMN-NAME>`.
    2. `entries_for_copybook_record` yields all nine declarations; the five the
       first pass did not cover are the ones the bridge maps to no column - the
       01 itself and the four members of the key group - and are keyed
       `<COPYBOOK-RECORD>.<FIELD-NAME>`.

    Insertion order is therefore column ordinal order followed by copybook
    declaration order, both of which are the loader's own and neither of which
    is re-sorted here (rule R-6).

    Returns:
        Each `copybook.name` in this copybook, verbatim in its own casing,
        against the key that names its entry.
    """
    keys: dict[str, str] = {}

    column_mapped = loader.entries_for_table(_TABLE)
    # Agent Action Plan section 0.6.6 tabulates this table at four columns, and
    # mysql/ACASDB.sql:L32-L35 declares four. A fifth or a third would mean the
    # artifact and the frozen schema had parted company.
    assert len(column_mapped) == 4, (
        f"the generated dictionary holds {len(column_mapped)} column-mapped "
        f"entries for {_TABLE}; mysql/ACASDB.sql:L31-L36 declares four"
    )
    for entry in column_mapped:
        copybook = entry.copybook
        if copybook is None:
            # A column the bridge derives with no copybook counterpart. This
            # table has none - the three IRS posting date components are the
            # in-scope example [common/irspostingMT.cbl:L982-L987] - and such a
            # field has no COBOL-side storage for a record module to declare.
            continue
        _admit(copybook.name, copybook.file)
        keys[copybook.name] = entry.key

    for entry in loader.entries_for_copybook_record(_COPYBOOK_RECORD):
        copybook = entry.copybook
        if copybook is None or entry.column is not None:
            # Already carried by the first pass under its column key.
            continue
        _admit(copybook.name, copybook.file)
        keys[copybook.name] = entry.key

    return keys


# Built once, at class-definition time, from the loader's lazily read and
# cached document. This is the one read this module performs; rule R-6 permits
# it precisely because the loader caches and because the document is immutable
# once read, so two imports in two processes see identical state.
_KEY_BY_COBOL_NAME: Final[dict[str, str]] = _dictionary_keys()


def _descriptor(cobol_name: str) -> FieldDescriptor:
    """Describe one field of this copybook, by dictionary lookup.

    A COBOL field name in, the descriptor the generated dictionary holds for
    it out. `FieldDescriptor.from_dictionary_key` reads the entry's COPYBOOK
    view for usage, digits, scale, signedness and character width, and takes
    the carrier from the entry's own storage decision - so nothing about a
    field's shape is stated in this module (rule R-5).

    A name this copybook does not declare fails here on the mapping lookup,
    naming the name. That is the intended failure: it means the artifact and
    the frozen copybook have parted company, and it needs a regenerated
    dictionary rather than a widened lookup.

    Args:
        cobol_name: The field name exactly as `copybooks/wsanal.cob` spells it,
            mixed case included - `"WS-Pa-Code"`, `"Pa-Gl"`, `"Pa-Print"`.

    Returns:
        Its descriptor, carrying its dictionary key and its copybook locator.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_BY_COBOL_NAME[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """SPACES at the character width one alphanumeric item declares.

    The width is taken from the descriptor rather than typed, for the same
    reason every other property of a field is (rule R-5): `Pa-Desc` is 24
    characters because `copybooks/wsanal.cob:L16` says so, not because 24 is
    written here.

    SPACES is the COBOL-faithful starting value, and the frozen bridge is what
    establishes that. Its load paragraph opens with `initialize
    TD-ANALYSIS-REC` [common/analMT.cbl:L942] and its unload paragraph with
    `initialize Analysis-Rec` [common/analMT.cbl:L963], and COBOL's
    `INITIALIZE` sets an alphanumeric item to spaces and a numeric one to zero.
    Section 0.6.2 draws the consequence out: that group initialisation "is why
    every column in the schema can be declared NOT NULL and why the Python
    layer must default rather than omit". Every column of this table is
    `NOT NULL` [mysql/ACASDB.sql:L32-L35], and no member of this record is ever
    absent.

    Args:
        descriptor: An alphanumeric item's descriptor.

    Returns:
        That many spaces. A group item, which declares no character width of
        its own, yields the empty string - groups take a nested dataclass as
        their starting value instead and never reach this function.
    """
    return " " * (descriptor.character_length or 0)


#  THE EIGHT DESCRIPTORS, IN COPYBOOK DECLARATION ORDER
# One per member declared in copybooks/wsanal.cob, L10 through L17, obtained by
# lookup and never transcribed. Four carry a column key and four a
# copybook-record key; the split is a result of the lookup, not a rule applied
# to it. The two groups report usage GROUP and no carrier at all, because a
# group has no storage of its own - it is the bytes of its children.

# 03  WS-Pa-Code.                          [copybooks/wsanal.cob:L10]
# The three-byte key group. FOUR declarations collapse into the ONE column
# `PA-CODE char(3)` [mysql/ACASDB.sql:L32], and the `WS-` prefix is gone by the
# time the name reaches the host variable [common/analMT.cbl:L283]. Recorded,
# not repaired; the key is the entry's own, so the prefix never has to be
# guessed at.
_WS_PA_CODE: Final[FieldDescriptor] = _descriptor("WS-Pa-Code")

# 05      Pa-System     pic x.             [copybooks/wsanal.cob:L11]
# No column of its own - the first byte of the concatenated key.
_PA_SYSTEM: Final[FieldDescriptor] = _descriptor("Pa-System")

# 05      Pa-Group.                        [copybooks/wsanal.cob:L12]
# The inner two-byte group. No column of its own.
_PA_GROUP: Final[FieldDescriptor] = _descriptor("Pa-Group")

# 07          Pa-First  pic x.             [copybooks/wsanal.cob:L13]
# The level numbering jumps 05 to 07 here, and the field name is set two spaces
# after that level number where the near-duplicate twin uses one space
# [copybooks/wsval.cob:L13-L14]. Both files indent these items by the same
# thirteen columns; only the gap differs. Both preserved as evidence.
_PA_FIRST: Final[FieldDescriptor] = _descriptor("Pa-First")

# 07          Pa-Second pic x.             [copybooks/wsanal.cob:L14]
_PA_SECOND: Final[FieldDescriptor] = _descriptor("Pa-Second")

# 03  Pa-Gl             pic 9(6).          [copybooks/wsanal.cob:L15]
# THE COPYBOOK VIEW, AND ONLY THE COPYBOOK VIEW: zoned DISPLAY, six digits,
# scale zero, unsigned. The host variable this field is moved into declares
# `PIC  9(08) COMP` - binary, eight digits [common/analMT.cbl:L284] - and the
# column narrows back to `mediumint(6) unsigned` [mysql/ACASDB.sql:L33]. That
# disagreement is surfaced by `drift()` and settled nowhere; converting across
# it is the bridge boundary's work, in the `acas015` handler module. What the round
# trip [common/analMT.cbl:L944] then [common/analMT.cbl:L966] does to a value
# too wide for six digits is an open question for the compiled oracle, recorded
# in the migration's ambiguity-resolutions document, and answered here by nothing.
_PA_GL: Final[FieldDescriptor] = _descriptor("Pa-Gl")

# 03  Pa-Desc           pic x(24).         [copybooks/wsanal.cob:L16]
_PA_DESC: Final[FieldDescriptor] = _descriptor("Pa-Desc")

# 03  Pa-Print          pic xxx.           [copybooks/wsanal.cob:L17]
# The picture is spelled `xxx` rather than `x(3)`, and the dictionary holds it
# that way. Three bytes written three different ways across the three layers -
# `xxx` here, `PIC X(3)` at the host variable [common/analMT.cbl:L286],
# `char(3)` at the column [mysql/ACASDB.sql:L35]. The last field of the record:
# the file ends on this line, with no trailing comment, where the twin has one
# [copybooks/wsval.cob:L24].
_PA_PRINT: Final[FieldDescriptor] = _descriptor("Pa-Print")


#  THE RECORD, INNERMOST GROUP FIRST
# Definition order ascends the copybook's level numbers - 07 group, 03 group,
# 01 record - because a nested member's starting value must name a class that
# already exists. MEMBER order inside each class is the copybook's own, so each
# class body reads top to bottom against copybooks/wsanal.cob.
# None of the three is frozen. sales/sl055.cbl and purchase/pl055.cbl read and
# update analysis records as they build their analysis totals, and an immutable
# or snapshotting record could make a lost-update defect impossible to
# reproduce - which R-4 requires stay reproducible.


@dataclass(slots=True)
class PaGroup:
    """`05 Pa-Group.` [copybooks/wsanal.cob:L12] - the inner two-byte group.

    The second and third bytes of the record's key. Its two members are
    declared at level 07 [copybooks/wsanal.cob:L13-L14], the level numbering
    jumping straight past 06 - preserved, along with the two-space gap after
    that level number where the near-duplicate twin leaves one
    [copybooks/wsval.cob:L13-L14]; the indentation itself is identical.

    Neither member has a column of its own. The whole of `WS-Pa-Code`, this
    group included, reaches MySQL as the single `PA-CODE char(3)`
    [mysql/ACASDB.sql:L32], concatenated by the bridge
    [common/analMT.cbl:L943]. Both are declared all the same, because rule R-3
    forbids dropping what the copybook declares and the COBOL addresses them by
    name.
    """

    # 07  Pa-First   pic x.    [copybooks/wsanal.cob:L13]
    pa_first: str = _spaces(_PA_FIRST)

    # 07  Pa-Second  pic x.    [copybooks/wsanal.cob:L14]
    pa_second: str = _spaces(_PA_SECOND)

    # Declaration order, as a tuple so the order cannot be perturbed (R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_PA_FIRST, _PA_SECOND)


@dataclass(slots=True)
class WsPaCode:
    """`03 WS-Pa-Code.` [copybooks/wsanal.cob:L10] - the three-byte key group.

    The `Ws` prefix is kept in this class name because the COBOL group carries
    it and the near-duplicate twin's equivalent group does not - `WS-Pa-Code`
    against `va-code` [copybooks/wsval.cob:L10]. That asymmetry is evidence
    about two records the frozen source keeps apart, so it is carried rather
    than tidied away.

    THE PREFIX DOES NOT SURVIVE THE BRIDGE. The host variable is `HV-PA-CODE`
    [common/analMT.cbl:L283] and the column is `PA-CODE`
    [mysql/ACASDB.sql:L32], both with the `WS-` gone, and `drift()` reports the
    name disagreement across the three layers. It is recorded and left
    unsettled; it is also the reason this module's dictionary keys are obtained
    by lookup, since raising this class's attribute name to upper case would
    ask the artifact for `WS-PA-CODE`, which nothing declares.

    Four declarations - this group, `Pa-System`, `Pa-Group` and its two members
    - occupy three bytes and become ONE column. No text conversion, ordering
    method or key-composition helper is offered for assembling those bytes:
    `harness/dump_tables.py` orders rows by the primary key the schema
    declares, and R-3 admits no added surface here.
    """

    # 05  Pa-System  pic x.    [copybooks/wsanal.cob:L11]
    pa_system: str = _spaces(_PA_SYSTEM)

    # 05  Pa-Group.            [copybooks/wsanal.cob:L12]
    # A group, so its starting value is its own dataclass and never None: every
    # column of this table is NOT NULL [mysql/ACASDB.sql:L32-L35] because the
    # bridge initialises its host-variable group before loading it
    # [common/analMT.cbl:L942].
    pa_group: PaGroup = field(default_factory=PaGroup)

    # Declaration order. `Pa-Group`'s own descriptor reports usage GROUP and no
    # carrier, because a group is the bytes of its children and holds nothing
    # itself.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_PA_SYSTEM, _PA_GROUP)


@dataclass(slots=True)
class WsAnalysisRecord:
    """`01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9] - the record.

    36 bytes, four columns, and the smallest record layout in the migrated
    cycle. Reached through entity facade `Analysis` and handler `acas015`
    [common/acas015.cbl], carried to MySQL by bridge `analMT`
    [common/analMT.cbl], and stored in table `ANALYSIS-REC`
    [mysql/ACASDB.sql:L31] whose primary key is the concatenated `PA-CODE`
    [mysql/ACASDB.sql:L36].

    THREE NAMES DENOTE THIS LAYOUT, and this class takes the copybook's:

        `WS-Analysis-Record`  the copybook 01     [copybooks/wsanal.cob:L9]
        `Analysis-Rec`        the bridge's own 01 [common/analMT.cbl:L315]
        `ANALYSIS-REC`        the MySQL table     [mysql/ACASDB.sql:L31]

    The bridge does not `COPY` this copybook; it declares its own record inline
    and that record is a DIFFERENT SHAPE - four declarations rather than eight,
    with the four-level key group flattened to one elementary `Pa-Code pic xxx`
    and renamed [common/analMT.cbl:L315-L319]. Both layouts occupy 36 bytes, so
    the divergence is structural rather than dimensional. This class follows
    the copybook, because the copybook is what the posting programs `COPY` and
    therefore what they manipulate. No alias for the bridge's name is offered.

    The declared size and the field sum AGREE here - 3 + 6 + 24 + 3 = 36
    against the header's 36 [copybooks/wsanal.cob:L6] - and signedness drifts
    on none of the four columns. Both counts are set out in this module's
    docstring, where they serve as the contrast cases for the records whose
    sizes are disputed and whose signs are lost at the bridge.

    Every member is always present and never None. The bridge initialises its
    host-variable group before loading it [common/analMT.cbl:L942], which is
    why the schema can declare all four columns `NOT NULL`
    [mysql/ACASDB.sql:L32-L35] and why this record defaults rather than omits:
    spaces at the declared width for an alphanumeric item, zero for the one
    numeric item, and a nested dataclass for a group.
    """

    # 03  WS-Pa-Code.          [copybooks/wsanal.cob:L10]
    # The key group. Four declarations, three bytes, ONE column - concatenated
    # by the bridge [common/analMT.cbl:L943] with the `WS-` prefix dropped.
    ws_pa_code: WsPaCode = field(default_factory=WsPaCode)

    # 03  Pa-Gl     pic 9(6).  [copybooks/wsanal.cob:L15]
    # An `int`, because the copybook declares six digits at zero scale: a store
    # into it truncates as an integer store. Zero is the starting value COBOL's
    # INITIALIZE gives a numeric item [common/analMT.cbl:L942]. The storage
    # class and the digit count both change at the host variable and change
    # back at the column; the descriptor reports the copybook's DISPLAY and six
    # digits, and the disagreement is surfaced unsettled by
    # `FIELDS[1].drift()`.
    pa_gl: int = 0

    # 03  Pa-Desc   pic x(24). [copybooks/wsanal.cob:L16]
    pa_desc: str = _spaces(_PA_DESC)

    # 03  Pa-Print  pic xxx.   [copybooks/wsanal.cob:L17]
    # The picture's `xxx` spelling is carried verbatim by the descriptor rather
    # than rewritten as `x(3)`.
    pa_print: str = _spaces(_PA_PRINT)

    # Declaration order, matching L10 through L17 with the key group counted
    # once - the same four the artifact keys by column, in column ordinal
    # order.
    # Each carries its own provenance: `FIELDS[n].cite()` returns the compact
    # three-locator string and `FIELDS[n].drift()` the unsettled disagreement,
    # both surfaced from the loader rather than reimplemented here (R-5).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_PA_CODE,
        _PA_GL,
        _PA_DESC,
        _PA_PRINT,
    )
