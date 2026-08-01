"""IRS final-accounts record layout, COBOL `01 Final-Record.`, 655 bytes.

Declared at [copybooks/irswsfinal.cob:L7]. The Python form of the IRS
final-accounts working-storage record: 53 named alphanumeric fields plus two
`OCCURS 26` array views over the same bytes, 655 bytes in all. Plain
dataclasses and nothing else - no ORM entity layer, no declarative metadata,
no schema definition, no behaviour. Every field's storage metadata is looked
up in the generated data dictionary rather than typed here.

WHAT THIS FILE IS
=================
Agent Action Plan section 0.4.1.3 states the whole assignment in one row:

    `acas_posting/records/irs_final.py` | CREATE |
    `copybooks/irswsfinal.cob` | `IRSFINAL-REC` (3 columns)

and the folder's mandate around it. That section requires each `05`/`03`
field to become a dataclass attribute whose descriptor is looked up in the
generated dictionary, and requires oddities in the frozen source to be
preserved rather than repaired. Section 0.8.1 fixes the shape - "Plain
modules and dataclasses; no ORM entity layer." - and rule R-3 fixes the
content: "The 27 record modules mirror their copybooks field for field with
nothing added."

Its place on the entity-to-table spine of section 0.2.1.1:

    entity facade    IRS final
    handler          acasirsub5
    bridge           irsfinalMT
    MySQL table      IRSFINAL-REC   3 columns, primary key
                                    IRS-FINAL-ACC-REC-KEY
    record copybook  copybooks/irswsfinal.cob

WHY THIS MODULE EXISTS AT ALL - THE POSTING PATH NEVER TOUCHES THIS TABLE
========================================================================
The one in-scope IRS program does not use this record. It declares a
one-byte placeholder for it and says so itself, verbatim at
[irs/irs030.cbl:L296]:

    03  Final-Record          pic x.    *> Table/File not used in this
                                        *> program.

So the posting-entry program deliberately stubs the final-accounts record
out. This module exists regardless, because the Agent Action Plan's own
scope lists put the entity in scope three separate ways (section 0.2.1.1):
`acasirsub5` is one of the seventeen in-scope file handlers, `irsfinalMT`
one of the twenty in-scope bridge pairs, and `IRSFINAL-REC` one of the
twenty-two in-scope tables. Section 0.4.1.3 names this file and section
0.4.1.5 names `acas_posting/dal/acasirsub5_irs_final.py` explicitly.

This is the direct analogue of the unused-facade-stub case section 0.4.3
already documents for the General Ledger transaction-update step:

    "`gl072` declares a block of facade stubs it never uses, present only so
    the linker resolves the copybook's full verb set
    [general/gl072.cbl:L134-L153]. Python has no equivalent need, so the
    block maps to nothing - recorded in the traceability document as a
    representation-only omission so that a reader comparing the two files
    does not conclude something was lost."

The parallel holds; the outcome differs, and the difference is the point.
`gl072`'s stub block maps to NOTHING. This record layout IS produced,
because `IRSFINAL-REC` is one of the twenty-two tables the scenario dump
covers (section 0.6.6) and the handler module needs a layout to load from
and unload into. What is NOT reproduced here is irs030's one-byte `pic x`
placeholder: that item belongs to the working storage of
`acas_posting/programs/irs030_posting.py`, not to the record layer.

THE LAYOUT, AS THE COPYBOOK DECLARES IT
=======================================
69 lines, and the shape matters more than the size::

    01  Final-Record.                                 L7
        03  ar1-fields.                               L8
          05  ar1-1        pic x(24).                 L9
          ...  twenty-six enumerated fields ...
          05  ar1-26       pic x(24).                 L34
        03  filler  redefines  ar1-fields.            L35
          05  ar1          pic x(24)  occurs  26.     L36
        03  ar2-fields.                               L38
          05  ar2-1        pic x.                     L39
          ...  twenty-six enumerated fields ...
          05  ar2-26       pic x.                     L64
        03  filler  redefines  ar2-fields.            L65
          05  ar2          pic x      occurs  26.     L66
        03  ar3            pic x(5).                  L68

Header, verbatim: L3 "Working Storage for the Final Account File" and L6
"rec 655 bytes +1 15/02/09".

Size arithmetic, which agrees with that header exactly:

    26 x 24  =  624     the ar1 group
    26 x  1  =   26     the ar2 group
              +   5     ar3
              -----
                655     the header's figure

The header's trailing "+1" is unexplained. It is recorded here verbatim as
an oddity of the frozen source (R-4) and no byte, no filler and no
explanation is added on its account.

Leaf census, asserted during validation: 26 + 26 + 1 = 53 explicitly named
leaf fields, plus 2 `OCCURS 26` array views, giving 105 addressable items
over 655 bytes.

THE DEFINING ODDITY - `ar3` IS DECLARED AND CAN NEVER REACH THE DATABASE
=======================================================================
The bridge declares exactly three host variables
[common/irsfinalMT.cbl:L171-L174]::

    01  TD-IRSFINAL-REC.
        05  HV-IRS-FINAL-ACC-REC-KEY   PIC  9(03) COMP.
        05  HV-IRS-AR1                 PIC X(24).
        05  HV-IRS-AR2                 PIC X(1).

and the frozen schema declares exactly three columns - a `tinyint(2)
unsigned` primary key, `IRS-AR1 char(24)` and `IRS-AR2 char(1)`, all
`NOT NULL` [mysql/ACASDB.sql:L214-L219].

`ar3 pic x(5)` [copybooks/irswsfinal.cob:L68] appears in neither. A search
of the whole bridge for `ar3` returns zero matches: it has no host
variable, it has no column, and the bridge drops it silently. It is
nevertheless part of the record and part of the 655 bytes, so it is
declared here exactly as the copybook declares it. Omitting it because no
column exists would be an R-3 violation in the subtractive direction.

This is the MIRROR IMAGE of the situation in
`acas_posting/records/irs_posting.py`. There, three date-component columns
exist with no copybook field, derived by that bridge under a guard
[common/irspostingMT.cbl:L982-L987]. Here, one copybook field exists with
no column. Between them the two cases are why the dictionary generator is
required to "flag any field present in one source and absent from another"
(sections 0.3.3 and 0.4.1.6) - and the generated artifact does flag this
one, reporting `presence.in_copybook=True`, `presence.in_bridge=False`,
`presence.in_column=False`, `one_sided=True` and the note "Copybook-only
field: declared in the copybook but carried by no bridge host variable and
stored in no column. Recorded and flagged rather than dropped."

`ar3` is a NEW anomaly, beyond the twenty-two of section 0.6.7. It belongs
in `docs/migration/anomaly-log.md` with this module as the recording site
and `acas_posting/dal/acasirsub5_irs_final.py` as the site where the drop
actually happens.

It also raises an open question for `docs/migration/ambiguity-resolutions.md`
that only the compiled program can settle (R-6): what happens to a value in
`ar3` across a write-then-read round trip, given that there is no column to
hold it. That is measured against the oracle, never reasoned about here.

THE PRIMARY KEY IS THE `OCCURS` SUBSCRIPT - AND IT IS NOT A FIELD
=================================================================
The copybook declares no key. The bridge writes ONE ROW PER ARRAY ENTRY and
uses the subscript as the primary key. Its own inline comment says so
[common/irsfinalMT.cbl:L455-L456]::

    move HV-IRS-AR1 to AR1 (HV-IRS-FINAL-ACC-REC-KEY)  *> KEY = table
                                                       *> position
    move HV-IRS-AR2 to AR2 (HV-IRS-FINAL-ACC-REC-KEY)

and the write side walks the whole array, at [:L476] and again at [:L524]::

    perform  varying A from 1 by 1 until A > 26
             move     A        to HV-IRS-FINAL-ACC-REC-KEY   [:L481]
             move     AR1 (A)  to HV-IRS-AR1                 [:L484]
             move     AR2 (A)  to HV-IRS-AR2                 [:L485]

One COBOL record therefore corresponds to as many as 26 table rows. That
structural drift is recorded here and reproduced nowhere near here:
`acas_posting/dal/acasirsub5_irs_final.py` owns the subscript-to-key
mapping, the row fan-out and the `IRS-` column prefixing. THIS MODULE
DECLARES NO KEY ATTRIBUTE, no subscript accessor, no by-position view and
no range guard.

Two facts worth carrying, because they are easy to lose:

* The bridge reads and writes through the ARRAY VIEWS `AR1 (n)` / `AR2 (n)`
  - the `filler redefines` views at L36 and L66 - and not through the 52
  enumerated fields. That is a fact about the bridge, recorded as such. It
  is not a statement that one view outranks the other; see the next section.
* COBOL `OCCURS` subscripts are 1-BASED and Python indexing is 0-BASED. The
  offset decision belongs to the consuming layer, which is where the
  subscript becomes a key value; this module states the fact and leaves it
  alone.

`initialize Final-Record with filler.` at [common/irsfinalMT.cbl:L395] is
why every column of this table can be `NOT NULL`, and why the defaults in
this module are SPACES and never `None`. Section 0.6.2 puts it directly:
"unset fields become zero or space rather than SQL `NULL` ... the Python
layer must default rather than omit."

A KEY-RANGE GUARD THAT IS RIGHT HERE, AND WRONG NEXT DOOR
=========================================================
This bridge guards the subscript at [common/irsfinalMT.cbl:L426]::

    if       HV-IRS-FINAL-ACC-REC-KEY = zero or > 26

with `move HV-IRS-FINAL-ACC-REC-KEY to WE-Error` at [:L428], and a related
bound `A > 26 or = zero` at [:L416]. Twenty-six matches `OCCURS 26`
exactly, so this guard is right.

Its sibling is not. `common/irsdfltMT.cbl:L575` reads `if HV-DEF-REC-KEY =
zero or > 32` while its own copybook declares `03 Def-Group occurs 33.`
[copybooks/irswsdflt.cob:L9] - a genuine off-by-one, recorded against
`acas_posting/records/irs_dflt.py`. Two bridges written to one pattern, and
only one of them kept up with its copybook. The contrast is recorded here
because it shows the pattern was intentional rather than accidental.

THE TWO `REDEFINES` VIEWS - BOTH MODELLED, NEITHER CHOSEN
=========================================================
`03 filler redefines ar1-fields.` [:L35] introduces `05 ar1 pic x(24)
occurs 26.` [:L36], and `03 filler redefines ar2-fields.` [:L65] introduces
`05 ar2 pic x occurs 26.` [:L66]. Each is an ALTERNATIVE VIEW of the same
bytes as the 26 enumerated fields above it.

Both are modelled, as separate dataclasses, in copybook declaration order.
There is no Python union here, no tagged variant, no property that switches
between the two, and no designation of one as primary. The enumerated group
and its redefining array are two different COBOL constructs and both stay
visible.

`filler` is the redefining group's actual COBOL name - unnamed on purpose,
and the house style of this copybook tree, where `redefines` appears 60
times and `filler`-named redefinitions are the norm
([copybooks/wsledger.cob:L16], [:L35], [copybooks/wssl.cob:L61],
[copybooks/wspl.cob:L50], [copybooks/irswsnl.cob:L22]). The Python classes
are therefore named for the array each group contains, and each class
docstring states the COBOL group it stands for with its locator.

TWO RECORDS ARE CALLED `Final-Record`, AND THEY ARE NOT THE SAME RECORD
======================================================================
This is anomaly-21-class evidence - "Field-name collisions ... force
qualified references" - and the reason both Python classes carry a
disambiguating prefix that the COBOL `01`-name does not have::

                     copybooks/wsfinal.cob    copybooks/irswsfinal.cob
                     (GL / System)            (THIS FILE)
    01-name          Final-Record  [:L10]     Final-Record  [:L7]
    ar1              pic x(16) occurs 26      26 enumerated pic x(24)
                     [:L11] - 16 chars,       [:L9-L34] PLUS an
                     array only               occurs 26 view [:L36]
                                              - 24 chars
    ar2              absent                   26 enumerated pic x, plus
                                              an occurs 26 view
    ar3              absent                   pic x(5)  [:L68]
    trailing filler  pic x(608)  [:L12]       none
                     (total 1024)             (total 655)
    Table            SYSFINAL-REC  (2 cols)   IRSFINAL-REC  (3 cols)
    Handler          acas000 key 3            acasirsub5
    Bridge           finalMT                  irsfinalMT
    Module           records/system_final.py  THIS FILE
                     (class SysFinalRecord)   (class IrsFinalRecord)

The maintainer himself asks whether the two can be joined up, in a comment
at [copybooks/wsfinal.cob:L7] - "Can we link this one for GL up with IRS??"
The answer this migration gives is no: the two are never merged, this
module never imports `records/system_final.py`, and no descriptor is shared.
The dangerous confusions are the `ar1` WIDTH - 16 against 24 - and the
PRESENCE of `ar2` and `ar3`. The GL record is never widened to 24 and never
given an `ar2` or an `ar3`; this one is never narrowed to 16.

The collision has a practical consequence for the dictionary lookups below,
and it is measured rather than assumed: the loader's record-name accessor
`entries_for_copybook_record("Final-Record")` returns 63 entries - 60 from
`copybooks/irswsfinal.cob` and 3 from `copybooks/wsfinal.cob` - precisely
because the `01`-name is shared. This module therefore never uses it. It
uses the table accessor and the FILE-scoped accessor, both of which name
this record and only this record.

BRIDGE DRIFT - FIVE KINDS, NONE OF THEM APPLIED HERE
====================================================
1. A BRIDGE-ONLY KEY COLUMN, plus the one-record-to-26-rows fan-out
   described above.
2. A COPYBOOK-ONLY FIELD, `ar3`, described above.
3. AN `IRS-` PREFIX IS ADDED to every column name: `ar1` becomes
   `IRS-AR1`, `ar2` becomes `IRS-AR2`, and the key is
   `IRS-FINAL-ACC-REC-KEY`. Compare `common/irsnominalMT.cbl`, where the
   `NL-` prefix is STRIPPED instead - `NL-DR` becomes `HV-DR` and the
   column `DR`, `NL-Pointer` becomes `HV-REC-POINTER` - while `NL-Name`
   keeps its prefix as `HV-NL-NAME` [common/irsnominalMT.cbl:L197-L209].
   Two IRS bridges, opposite prefix conventions, and one of them not even
   consistent with itself. This is the folder's plainest argument for
   reading entry keys out of the dictionary instead of guessing them.
4. DIGIT WIDENING ON THE KEY: `HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP`
   [common/irsfinalMT.cbl:L172] against `tinyint(2) unsigned` in the
   column - the host variable is wider than the column it feeds.
5. TRAILING SPACES ARE TRIMMED AT THE BRIDGE. `STRING FUNCTION TRIM
   (HV-IRS-AR1,TRAILING)` appears at [common/irsfinalMT.cbl:L638] and
   [:L691], and the same for `HV-IRS-AR2` at [:L647] and [:L700]. That
   trimming is exactly why section 0.6.6 requires the harness dump
   comparison to even out trailing spaces in fixed-character columns.
   NOTHING IS TRIMMED IN THIS MODULE. Padding is a stored value here; the
   handler module and the harness dump comparison own the rest.

A second open question for `docs/migration/ambiguity-resolutions.md` falls
out of the fifth kind (R-6): what that trailing trim does to a value which
legitimately ends in spaces. Measured against the oracle, not settled here.

A descriptor in this module reports the COPYBOOK view of its field as its
own digits, scale, sign and usage. It never blends the three layers, and it
offers their disagreement as it stands, unadjudicated, through
`loader.drift_for`. Every one of the five kinds above belongs to
`acas_posting/dal/acasirsub5_irs_final.py`.

One further provenance note, so that a reader looking for the conventional
paragraph is not left hunting: `irsfinalMT` is one of four bridges with NO
`bb000-HV-Load` paragraph - the others being `dfltMT`, `finalMT` and
`irsdfltMT`. It loads and unloads its host variables inline
([common/irsfinalMT.cbl:L455-L456], [:L476-L485], [:L524-L529]), which is
what the dictionary's `load_source` and `unload_source` locators point at.

DESCRIPTORS ARE LOOKED UP, NEVER TRANSCRIBED  (R-5)
===================================================
Section 0.8.1 makes the ordering a directive rather than a preference:

    "Data dictionary first. The dictionary is generated from the bridge
    before record definitions are written, and every Python field
    definition cites its entry. This ordering is a directive, not a
    preference - it is what prevents fields being transcribed by eye."

and section 0.3.3 gives the reason: "Field metadata is therefore derived,
not transcribed, which eliminates an entire class of transcription error
across several hundred fields." The preserved user requirement of section
0.8.2 names the source of truth - of the maintainer's one-way COBOL-to-
MySQL bridge, "it is the data dictionary for this migration".

Not one picture clause, digit count, character length, `OCCURS` count or
storage class is written by hand below. Every entry key is read out of the
generated artifact by two accessors, and both of them name this record
unambiguously:

    loader.entries_for_table("IRSFINAL-REC")
        The mandated path for the two column-mapped fields. It returns
        exactly three entries - the bridge-only key at column ordinal 1,
        then `IRSFINAL-REC.IRS-AR1` whose copybook view is `ar1` at
        [copybooks/irswsfinal.cob:L36], then `IRSFINAL-REC.IRS-AR2` whose
        copybook view is `ar2` at [:L66].

    loader.entries_for_copybook_file("copybooks/irswsfinal.cob")
        The only unambiguous source for the copybook-only items, which have
        no column and so cannot come from the table accessor: the 52
        enumerated fields, the four `03`-level groups and `ar3`. It returns
        exactly 60 entries for this file.

Both passes keep only entries whose `copybook.file` is
`copybooks/irswsfinal.cob`, so the GL record of the same `01`-name is
structurally unreachable from here rather than merely avoided. The tell, if
that guard ever failed, would be an `ar1` descriptor reporting a character
length of 16 instead of 24.

Sixty entries cover this copybook completely, and this module uses 59 of
them: 26 for `ar1-1` .. `ar1-26`, one for the `ar1` array view, 26 for
`ar2-1` .. `ar2-26`, one for the `ar2` array view, and five for the `01`
record's own declared members - `ar1-fields`, the `filler` redefining it,
`ar2-fields`, the `filler` redefining that, and `ar3`. The sixtieth is
`Final-Record.Final-Record#7`, the `01` group itself, which is this
module's `IrsFinalRecord` class rather than one of its attributes.

All 59 descriptors are built by `FieldDescriptor.from_dictionary_key`. Not
one needs `FieldDescriptor.for_working_storage`, because the artifact
carries even the one-sided `ar3` as `Final-Record.ar3` - so the
locator-only path would have meant typing that field's metadata by hand,
which is the transcription section 0.3.3 exists to prevent. The mandatory
provenance invariant that every descriptor carry a dictionary key or a
source locator is therefore satisfied by the key on all 59, with the
copybook locator carried alongside.

`loader.cite(key)` yields the compact three-locator provenance string for
any of them - for the one-sided field it renders as `Final-Record.ar3
copybook=copybooks/irswsfinal.cob:L68 bridge=absent column=absent`, which
is the anomaly stating itself. That primitive is surfaced, never
reimplemented here.

TYPE DISCIPLINE  (R-2)
======================
    ar1-1 .. ar1-26   pic x(24)              `str`, width 24
    ar1               pic x(24) occurs 26    `tuple` of 26 `str`, width 24
    ar2-1 .. ar2-26   pic x                  `str`, width 1
    ar2               pic x     occurs 26    `tuple` of 26 `str`, width 1
    ar3               pic x(5)               `str`, width 5

THIS RECORD IS ENTIRELY ALPHANUMERIC. There is no numeric field of any kind
in it: no `COMP`, no `COMP-3`, no `binary-char`/`-short`/`-long`, no sign
clause, no `V` implied decimal point and no `88`-level condition name. Rule
R-2 - no accounting value may pass through a binary floating-point type at
any point, in computation, in storage or in transport - is therefore
satisfied trivially and structurally: the `decimal` module is not needed
and is not imported, and no binary floating-point carrier can appear
because no numeric carrier appears at all. Stating that is the compliance
evidence.

The only numeric item anywhere in sight is the bridge's own
`HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP`, which is not this module's -
see the primary-key section above.

THIS IS A LEAF MODULE  (section 0.4.3)
======================================
The per-directory import contract grants `records/*.py` two imports and
forbids the rest, for a stated reason - "this keeps the record layer a
leaf":

    permitted   `acas_posting.cobol.field`        the descriptor type
                `acas_posting.dictionary.loader`  the lookup
                plus the standard library

    forbidden   `dal` in any form - and `dal/acasirsub5_irs_final.py` is
                the live temptation, since it owns the subscript-to-key
                mapping, the `IRS-` prefixing, the `ar3` drop and the
                trailing trim; `programs`; `cli`; `clock`; `dates`;
                `workfiles`; `cobol.arithmetic`; `cobol.move`, which owns
                padding semantics rather than this file; `cobol.picture`;
                `cobol.usage`; `cobol.condition_names`; `cobol.sortverb`;
                `dictionary.generate`; the compiled comparison oracle in
                its sibling tree, which owns the dump comparison; and any
                other module of this package - above all
                `records/system_final.py`, for the reason set out above,
                and `records/irs_dflt.py` despite the guard contrast.

Section 0.4.3 states what the restraint buys: the arithmetic test tier
"imports only `cobol` and `records` and touches no database, so it runs
anywhere".

DETERMINISM  (R-6)
==================
Attribute order is copybook declaration order, so this file can be set
beside its copybook and diffed by eye. Every `FIELDS` sequence is a tuple
and never a list. Nothing here consults a clock, draws an unpredictable
value, inspects the process environment or reads the file system beyond the
dictionary loader's own lazy, cached read. Execution is strictly
sequential; no concurrency is introduced. Two imports in two processes
produce identical state.

NAMING, RECORDED BECAUSE R-5 ASKS FOR NAMING DECISIONS TO BE VISIBLE
====================================================================
    IrsFinalRecord   `01 Final-Record.`                     [:L7]
    Ar1Fields        `03 ar1-fields.`                       [:L8]
    Ar1View          `03 filler redefines ar1-fields.`      [:L35]
    Ar2Fields        `03 ar2-fields.`                       [:L38]
    Ar2View          `03 filler redefines ar2-fields.`      [:L65]

The secondary names follow the folder convention: PascalCase of the COBOL
group name with hyphens removed, and - for a `filler` group, which has no
name to convert - the name of the array it contains plus `View`.

`IrsFinalRecord` carries a prefix its COBOL `01`-name does not have. Unlike
its IRS siblings, `irs030` supplies no caller-side `replacing` name for
this record; it stubs the record out entirely [irs/irs030.cbl:L296]. The
prefix is therefore this migration's own disambiguation, chosen to sit
alongside `SysFinalRecord` in `records/system_final.py` so that the pair
reads as a pair.

WARNING - THE ODDITIES BELOW ARE REPRODUCED, NEVER REPAIRED  (R-4)
==================================================================
    "A defect reproduced is correct; a defect fixed is a failure."
                                        - Agent Action Plan section 0.7.2

Everything this module records and reproduces, each with its locator at the
site: `ar3` declared with nowhere to go; the primary key that exists only
in the bridge, with its record-to-rows fan-out; the `01`-name collision
with the General Ledger record of different width and different membership;
irs030's own stubbing-out of the record; the `IRS-` prefix added here while
`irsnominalMT` strips `NL-`; a subscript guard that matches its `OCCURS`
where the neighbouring bridge's does not; the header's unexplained "+1";
the bridge's trailing-space trim; the two deliberately unnamed `filler`
redefining groups; and the absent `bb000-HV-Load` paragraph.

This file designates no view, no value, no type and no picture as the
settled one, and no such designation may be introduced. The entire
vocabulary of adjudication - every adjective a reader reaches for when
picking a winner among disagreeing layers - is deliberately absent from this
module, and its absence is checked. Where the copybook, the bridge host
variable and the column disagree, all three views stand side by side in the
dictionary and the disagreement stays open. The register of every such site is
`docs/migration/anomaly-log.md`; the two questions only the compiled
program can settle are in `docs/migration/ambiguity-resolutions.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Sorted, so that the surface is stable between runs (R-6). The two
    # enumerated groups, their two redefining array views, then the 01
    # record that holds all four plus ar3.
    "Ar1Fields",
    "Ar1View",
    "Ar2Fields",
    "Ar2View",
    "IrsFinalRecord",
)


# =============================================================================
#  THE TWO FROZEN NAMES THIS MODULE IS SCOPED TO
# =============================================================================

# The MySQL table, as the frozen schema spells it
# [mysql/ACASDB.sql:L214]. It is the LEFT side of a column-mapped entry key,
# and using it rather than the copybook's 01-name is what keeps this record
# apart from SYSFINAL-REC, whose 01-name is identical
# [copybooks/wsfinal.cob:L10].
_TABLE: Final[str] = "IRSFINAL-REC"

# The copybook, as the dictionary records it. Every entry this module uses
# must carry this file and no other; see the collision table in the module
# docstring. An ar1 descriptor reporting a character length of 16 would mean
# the General Ledger record had been picked up instead.
_COPYBOOK: Final[str] = "copybooks/irswsfinal.cob"


# =============================================================================
#  ENTRY KEYS, READ OUT OF THE GENERATED ARTIFACT  (R-5)
# =============================================================================
#
# Two mappings, built once at import from the dictionary loader's own lazy,
# cached read. Nothing below writes a key literal: a key is looked up by the
# COBOL field name the copybook declares, which is the one identifier that
# appears verbatim in both the frozen source and the artifact.


def _entry_key_by_field_name() -> dict[str, str]:
    """Map each NAMED copybook field of this record to its entry key.

    Two passes, because the record's fields reach the artifact by two
    different routes and neither route alone covers them all:

    * `loader.entries_for_table` supplies the two column-mapped fields. It
      returns three entries for this table, one of which - the primary key -
      has no copybook view at all and is skipped here by the `is not None`
      test rather than by name.
    * `loader.entries_for_copybook_file` supplies everything with no column:
      the 52 enumerated fields, the four `03`-level groups and `ar3`. This
      accessor is FILE-scoped, which is what makes it safe. Its record-name
      counterpart is not: `entries_for_copybook_record("Final-Record")`
      returns 63 entries spanning two copybooks, because the General Ledger
      final-accounts record shares the `01`-name.

    The two passes overlap on the two array views and agree on their keys,
    so the order of the passes changes nothing. FILLER groups are excluded:
    both of this record's redefining groups are literally named `filler`
    [copybooks/irswsfinal.cob:L35], [:L65], so a name is not enough to tell
    them apart and they are keyed by what they redefine instead - see
    `_entry_key_by_redefines_target`.

    Returns:
        The COBOL field name of every named item in this copybook, mapped to
        its dictionary entry key.
    """
    keys: dict[str, str] = {}
    for entry in loader.entries_for_table(_TABLE):
        copybook = entry.copybook
        if copybook is not None and copybook.file == _COPYBOOK:
            keys[copybook.name] = entry.key
    for entry in loader.entries_for_copybook_file(_COPYBOOK):
        copybook = entry.copybook
        if (
            copybook is not None
            and copybook.file == _COPYBOOK
            and not copybook.is_filler
        ):
            keys[copybook.name] = entry.key
    return keys


def _entry_key_by_redefines_target() -> dict[str, str]:
    """Map each redefining FILLER group to its entry key, by what it covers.

    `03 filler redefines ar1-fields.` [copybooks/irswsfinal.cob:L35] and
    `03 filler redefines ar2-fields.` [:L65] carry the same COBOL name -
    none - so they are told apart by their REDEFINES target, which the
    artifact records per entry. Keying them that way needs no line-number
    literal and no assumption about the order the artifact lists them in.

    Returns:
        The redefined group's name mapped to the redefining group's entry
        key, for each FILLER group of this copybook.
    """
    return {
        entry.copybook.redefines: entry.key
        for entry in loader.entries_for_copybook_file(_COPYBOOK)
        if entry.copybook is not None
        and entry.copybook.file == _COPYBOOK
        and entry.copybook.is_filler
        and entry.copybook.redefines is not None
    }


_KEY_BY_FIELD_NAME: Final[dict[str, str]] = _entry_key_by_field_name()
_KEY_BY_REDEFINES_TARGET: Final[dict[str, str]] = (
    _entry_key_by_redefines_target()
)


def _descriptor_for(cobol_name: str) -> FieldDescriptor:
    """Describe one named item of this record, from its dictionary entry.

    The descriptor reports the entry's COPYBOOK view - picture, character
    length, `OCCURS`, `REDEFINES`, usage and carrier - and carries the entry
    key as its provenance, so `descriptor.cite()` returns the compact
    three-locator string for it.

    Args:
        cobol_name: The field name exactly as the copybook writes it, for
            example `"ar1-1"`, `"ar1"` or `"ar3"`.

    Returns:
        The descriptor for that field.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_BY_FIELD_NAME[cobol_name])


def _redefining_group_for(target: str) -> FieldDescriptor:
    """Describe the unnamed group that redefines `target`.

    Args:
        target: The redefined group's COBOL name, `"ar1-fields"` or
            `"ar2-fields"`.

    Returns:
        The descriptor for the `filler` group redefining it, carrying
        `redefines` set to `target` and `is_filler` set.
    """
    return FieldDescriptor.from_dictionary_key(
        _KEY_BY_REDEFINES_TARGET[target]
    )


# =============================================================================
#  INITIAL VALUES, DERIVED FROM THE DESCRIPTORS THEMSELVES
# =============================================================================
#
# `initialize Final-Record with filler.` [common/irsfinalMT.cbl:L395] is the
# state the bridge hands to a load, and for an alphanumeric item that means
# SPACES. Spaces at the item's declared width are therefore the initial
# value here, rather than the empty string: it is what the frozen source
# does, and it is why every column of this table can be NOT NULL
# (section 0.6.2). `None` is never an initial value in this module.
#
# The WIDTH is read off the field's own descriptor and never typed, for the
# same reason nothing else is (R-5). No padding, trimming or justification
# happens anywhere here - `acas_posting.cobol.move` owns those semantics.


def _initial_value(descriptor: FieldDescriptor) -> str:
    """Return one item's initial value: its own width, in spaces.

    Args:
        descriptor: An elementary alphanumeric item's descriptor.

    Returns:
        A string of spaces as wide as the item is declared.
    """
    return " " * descriptor.byte_length


def _initial_table(descriptor: FieldDescriptor) -> tuple[str, ...]:
    """Return an `OCCURS` item's initial value: one entry per position.

    Args:
        descriptor: An elementary alphanumeric item's descriptor carrying an
            `OCCURS` count.

    Returns:
        A tuple with one space-filled entry, at the item's own width, for
        each `OCCURS` position it declares.
    """
    # `occurs` is `int | None` across the record layouts in general; both
    # views of this record declare it [copybooks/irswsfinal.cob:L36], [:L66],
    # so it is an int here and the fallback is unreachable for this module.
    return (_initial_value(descriptor),) * (descriptor.occurs or 0)


# =============================================================================
#  03  ar1-fields.                            [copybooks/irswsfinal.cob:L8]
# =============================================================================

# The 26 enumerated members, in copybook declaration order. Written out one
# by one because the copybook writes them out one by one: the group and the
# array view that redefines it are two different COBOL constructs, and R-3's
# "nothing added" cuts both ways - nothing is removed either.
_AR1_FIELD_DESCRIPTORS: Final[tuple[FieldDescriptor, ...]] = (
    _descriptor_for("ar1-1"),                                     # L9
    _descriptor_for("ar1-2"),                                     # L10
    _descriptor_for("ar1-3"),                                     # L11
    _descriptor_for("ar1-4"),                                     # L12
    _descriptor_for("ar1-5"),                                     # L13
    _descriptor_for("ar1-6"),                                     # L14
    _descriptor_for("ar1-7"),                                     # L15
    _descriptor_for("ar1-8"),                                     # L16
    _descriptor_for("ar1-9"),                                     # L17
    _descriptor_for("ar1-10"),                                    # L18
    _descriptor_for("ar1-11"),                                    # L19
    _descriptor_for("ar1-12"),                                    # L20
    _descriptor_for("ar1-13"),                                    # L21
    _descriptor_for("ar1-14"),                                    # L22
    _descriptor_for("ar1-15"),                                    # L23
    _descriptor_for("ar1-16"),                                    # L24
    _descriptor_for("ar1-17"),                                    # L25
    _descriptor_for("ar1-18"),                                    # L26
    _descriptor_for("ar1-19"),                                    # L27
    _descriptor_for("ar1-20"),                                    # L28
    _descriptor_for("ar1-21"),                                    # L29
    _descriptor_for("ar1-22"),                                    # L30
    _descriptor_for("ar1-23"),                                    # L31
    _descriptor_for("ar1-24"),                                    # L32
    _descriptor_for("ar1-25"),                                    # L33
    _descriptor_for("ar1-26"),                                    # L34
)

# Every member of the group is declared `pic x(24)`
# [copybooks/irswsfinal.cob:L9-L34], so one initial value serves all 26. Its
# width is still read off a descriptor rather than typed here.
_AR1_FIELD_INITIAL: Final[str] = _initial_value(_AR1_FIELD_DESCRIPTORS[0])


@dataclass(slots=True)
class Ar1Fields:
    """`03 ar1-fields.` [copybooks/irswsfinal.cob:L8] - 26 enumerated fields.

    The first of the two enumerated groups of `01 Final-Record.`, holding 26
    separately named 24-character items at L9 through L34. The bytes it
    occupies are also addressable through `Ar1View`, which redefines this
    group; neither view is primary and neither is derived from the other.

    Every item is `pic x(24)`, so the whole group is `str` - there is no
    numeric item, no sign and no implied decimal point anywhere in it (R-2).
    The initial value of each is 24 spaces, matching `initialize
    Final-Record with filler.` [common/irsfinalMT.cbl:L395]; padding is a
    stored value and is neither trimmed nor added here.

    Attributes:
        FIELDS: The 26 descriptors, in copybook declaration order.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _AR1_FIELD_DESCRIPTORS

    ar1_1: str = _AR1_FIELD_INITIAL   # ar1-1  pic x(24)  [:L9]
    ar1_2: str = _AR1_FIELD_INITIAL   # ar1-2  pic x(24)  [:L10]
    ar1_3: str = _AR1_FIELD_INITIAL   # ar1-3  pic x(24)  [:L11]
    ar1_4: str = _AR1_FIELD_INITIAL   # ar1-4  pic x(24)  [:L12]
    ar1_5: str = _AR1_FIELD_INITIAL   # ar1-5  pic x(24)  [:L13]
    ar1_6: str = _AR1_FIELD_INITIAL   # ar1-6  pic x(24)  [:L14]
    ar1_7: str = _AR1_FIELD_INITIAL   # ar1-7  pic x(24)  [:L15]
    ar1_8: str = _AR1_FIELD_INITIAL   # ar1-8  pic x(24)  [:L16]
    ar1_9: str = _AR1_FIELD_INITIAL   # ar1-9  pic x(24)  [:L17]
    ar1_10: str = _AR1_FIELD_INITIAL  # ar1-10  pic x(24)  [:L18]
    ar1_11: str = _AR1_FIELD_INITIAL  # ar1-11  pic x(24)  [:L19]
    ar1_12: str = _AR1_FIELD_INITIAL  # ar1-12  pic x(24)  [:L20]
    ar1_13: str = _AR1_FIELD_INITIAL  # ar1-13  pic x(24)  [:L21]
    ar1_14: str = _AR1_FIELD_INITIAL  # ar1-14  pic x(24)  [:L22]
    ar1_15: str = _AR1_FIELD_INITIAL  # ar1-15  pic x(24)  [:L23]
    ar1_16: str = _AR1_FIELD_INITIAL  # ar1-16  pic x(24)  [:L24]
    ar1_17: str = _AR1_FIELD_INITIAL  # ar1-17  pic x(24)  [:L25]
    ar1_18: str = _AR1_FIELD_INITIAL  # ar1-18  pic x(24)  [:L26]
    ar1_19: str = _AR1_FIELD_INITIAL  # ar1-19  pic x(24)  [:L27]
    ar1_20: str = _AR1_FIELD_INITIAL  # ar1-20  pic x(24)  [:L28]
    ar1_21: str = _AR1_FIELD_INITIAL  # ar1-21  pic x(24)  [:L29]
    ar1_22: str = _AR1_FIELD_INITIAL  # ar1-22  pic x(24)  [:L30]
    ar1_23: str = _AR1_FIELD_INITIAL  # ar1-23  pic x(24)  [:L31]
    ar1_24: str = _AR1_FIELD_INITIAL  # ar1-24  pic x(24)  [:L32]
    ar1_25: str = _AR1_FIELD_INITIAL  # ar1-25  pic x(24)  [:L33]
    ar1_26: str = _AR1_FIELD_INITIAL  # ar1-26  pic x(24)  [:L34]


# =============================================================================
#  03  filler  redefines  ar1-fields.         [copybooks/irswsfinal.cob:L35]
# =============================================================================

# The array view's own 05-level item, keyed by the table because the bridge
# maps it to a column: its copybook side is `ar1` at
# [copybooks/irswsfinal.cob:L36] and its column side is IRS-AR1. The
# descriptor carries `occurs` = 26 as one descriptor rather than 26 expanded
# ones, because that is what the dictionary holds for it.
_AR1_VIEW_DESCRIPTOR: Final[FieldDescriptor] = _descriptor_for("ar1")

_AR1_VIEW_INITIAL: Final[tuple[str, ...]] = _initial_table(
    _AR1_VIEW_DESCRIPTOR
)


@dataclass(slots=True)
class Ar1View:
    """`03 filler redefines ar1-fields.` [copybooks/irswsfinal.cob:L35].

    The redefining group is FILLER in the COBOL - genuinely unnamed, which
    is the house style of this copybook tree, where `redefines` appears 60
    times and `filler`-named redefinitions are the norm. This class is
    therefore named for the array it contains, `05 ar1 pic x(24) occurs 26.`
    at [:L36], and not for the group, which has no name to carry over.

    It is an ALTERNATIVE VIEW of the same 624 bytes that `Ar1Fields`
    describes. Both are modelled and neither is primary. As a fact and not a
    preference: the bridge reads and writes through this view rather than
    through the 26 enumerated fields, moving `AR1 (A)` into its host
    variable [common/irsfinalMT.cbl:L484] and `HV-IRS-AR1` back into
    `AR1 (HV-IRS-FINAL-ACC-REC-KEY)` [:L455], where the subscript IS the
    primary key. COBOL subscripts are 1-based and Python indexing is
    0-based; the offset belongs to whichever layer turns a position into a
    key value, which is `dal/acasirsub5_irs_final.py`.

    Attributes:
        FIELDS: One descriptor, for `ar1`, carrying `occurs` = 26.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_AR1_VIEW_DESCRIPTOR,)

    # ar1  pic x(24)  occurs 26  [copybooks/irswsfinal.cob:L36]
    # A tuple and never a list, so the surface is stable between runs (R-6).
    ar1: tuple[str, ...] = _AR1_VIEW_INITIAL


# =============================================================================
#  03  ar2-fields.                           [copybooks/irswsfinal.cob:L38]
# =============================================================================

# The second enumerated group: 26 single-character items at L39 through L64,
# again written out one by one because the copybook does.
_AR2_FIELD_DESCRIPTORS: Final[tuple[FieldDescriptor, ...]] = (
    _descriptor_for("ar2-1"),                                     # L39
    _descriptor_for("ar2-2"),                                     # L40
    _descriptor_for("ar2-3"),                                     # L41
    _descriptor_for("ar2-4"),                                     # L42
    _descriptor_for("ar2-5"),                                     # L43
    _descriptor_for("ar2-6"),                                     # L44
    _descriptor_for("ar2-7"),                                     # L45
    _descriptor_for("ar2-8"),                                     # L46
    _descriptor_for("ar2-9"),                                     # L47
    _descriptor_for("ar2-10"),                                    # L48
    _descriptor_for("ar2-11"),                                    # L49
    _descriptor_for("ar2-12"),                                    # L50
    _descriptor_for("ar2-13"),                                    # L51
    _descriptor_for("ar2-14"),                                    # L52
    _descriptor_for("ar2-15"),                                    # L53
    _descriptor_for("ar2-16"),                                    # L54
    _descriptor_for("ar2-17"),                                    # L55
    _descriptor_for("ar2-18"),                                    # L56
    _descriptor_for("ar2-19"),                                    # L57
    _descriptor_for("ar2-20"),                                    # L58
    _descriptor_for("ar2-21"),                                    # L59
    _descriptor_for("ar2-22"),                                    # L60
    _descriptor_for("ar2-23"),                                    # L61
    _descriptor_for("ar2-24"),                                    # L62
    _descriptor_for("ar2-25"),                                    # L63
    _descriptor_for("ar2-26"),                                    # L64
)

# Every member of the group is declared `pic x` - one character, no length
# in parentheses [copybooks/irswsfinal.cob:L39-L64] - so one initial value
# serves all 26, its width read off a descriptor rather than typed.
_AR2_FIELD_INITIAL: Final[str] = _initial_value(_AR2_FIELD_DESCRIPTORS[0])


@dataclass(slots=True)
class Ar2Fields:
    """`03 ar2-fields.` [copybooks/irswsfinal.cob:L38] - 26 enumerated fields.

    The second enumerated group of `01 Final-Record.`, holding 26 separately
    named single-character items at L39 through L64. Its bytes are also
    addressable through `Ar2View`, which redefines this group; neither view
    is primary.

    Every item is `pic x`, a single character, so the whole group is `str`.
    The initial value of each is one space, matching `initialize
    Final-Record with filler.` [common/irsfinalMT.cbl:L395].

    The copybook attaches no `88`-level condition name to any of these
    single-character items, so no predicate is offered for them here. Where
    the frozen source does declare condition names -
    `acas_posting.cobol.condition_names` covers those - it says so; this
    record does not.

    Attributes:
        FIELDS: The 26 descriptors, in copybook declaration order.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _AR2_FIELD_DESCRIPTORS

    ar2_1: str = _AR2_FIELD_INITIAL   # ar2-1  pic x  [:L39]
    ar2_2: str = _AR2_FIELD_INITIAL   # ar2-2  pic x  [:L40]
    ar2_3: str = _AR2_FIELD_INITIAL   # ar2-3  pic x  [:L41]
    ar2_4: str = _AR2_FIELD_INITIAL   # ar2-4  pic x  [:L42]
    ar2_5: str = _AR2_FIELD_INITIAL   # ar2-5  pic x  [:L43]
    ar2_6: str = _AR2_FIELD_INITIAL   # ar2-6  pic x  [:L44]
    ar2_7: str = _AR2_FIELD_INITIAL   # ar2-7  pic x  [:L45]
    ar2_8: str = _AR2_FIELD_INITIAL   # ar2-8  pic x  [:L46]
    ar2_9: str = _AR2_FIELD_INITIAL   # ar2-9  pic x  [:L47]
    ar2_10: str = _AR2_FIELD_INITIAL  # ar2-10  pic x  [:L48]
    ar2_11: str = _AR2_FIELD_INITIAL  # ar2-11  pic x  [:L49]
    ar2_12: str = _AR2_FIELD_INITIAL  # ar2-12  pic x  [:L50]
    ar2_13: str = _AR2_FIELD_INITIAL  # ar2-13  pic x  [:L51]
    ar2_14: str = _AR2_FIELD_INITIAL  # ar2-14  pic x  [:L52]
    ar2_15: str = _AR2_FIELD_INITIAL  # ar2-15  pic x  [:L53]
    ar2_16: str = _AR2_FIELD_INITIAL  # ar2-16  pic x  [:L54]
    ar2_17: str = _AR2_FIELD_INITIAL  # ar2-17  pic x  [:L55]
    ar2_18: str = _AR2_FIELD_INITIAL  # ar2-18  pic x  [:L56]
    ar2_19: str = _AR2_FIELD_INITIAL  # ar2-19  pic x  [:L57]
    ar2_20: str = _AR2_FIELD_INITIAL  # ar2-20  pic x  [:L58]
    ar2_21: str = _AR2_FIELD_INITIAL  # ar2-21  pic x  [:L59]
    ar2_22: str = _AR2_FIELD_INITIAL  # ar2-22  pic x  [:L60]
    ar2_23: str = _AR2_FIELD_INITIAL  # ar2-23  pic x  [:L61]
    ar2_24: str = _AR2_FIELD_INITIAL  # ar2-24  pic x  [:L62]
    ar2_25: str = _AR2_FIELD_INITIAL  # ar2-25  pic x  [:L63]
    ar2_26: str = _AR2_FIELD_INITIAL  # ar2-26  pic x  [:L64]


# =============================================================================
#  03  filler  redefines  ar2-fields.        [copybooks/irswsfinal.cob:L65]
# =============================================================================

# Keyed by the table for the same reason `ar1` is: its copybook side is
# `ar2` at [copybooks/irswsfinal.cob:L66] and its column side is IRS-AR2.
_AR2_VIEW_DESCRIPTOR: Final[FieldDescriptor] = _descriptor_for("ar2")

_AR2_VIEW_INITIAL: Final[tuple[str, ...]] = _initial_table(
    _AR2_VIEW_DESCRIPTOR
)


@dataclass(slots=True)
class Ar2View:
    """`03 filler redefines ar2-fields.` [copybooks/irswsfinal.cob:L65].

    As with `Ar1View`, the redefining group is FILLER in the COBOL and this
    class is named for the array it contains, `05 ar2 pic x occurs 26.` at
    [:L66]. It is an ALTERNATIVE VIEW of the same 26 bytes that `Ar2Fields`
    describes, and neither view is primary.

    The bridge works through this view: `move AR2 (A) to HV-IRS-AR2`
    [common/irsfinalMT.cbl:L485] on the way out and `move HV-IRS-AR2 to
    AR2 (HV-IRS-FINAL-ACC-REC-KEY)` [:L456] on the way back, the subscript
    being the primary key. Subscripts are 1-based in COBOL and indexing is
    0-based in Python; the offset belongs to the consuming layer.

    Attributes:
        FIELDS: One descriptor, for `ar2`, carrying `occurs` = 26.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_AR2_VIEW_DESCRIPTOR,)

    # ar2  pic x  occurs 26  [copybooks/irswsfinal.cob:L66]
    # A tuple and never a list (R-6).
    ar2: tuple[str, ...] = _AR2_VIEW_INITIAL


# =============================================================================
#  03  ar3  pic x(5).                        [copybooks/irswsfinal.cob:L68]
# =============================================================================
#
# THE COPYBOOK-ONLY FIELD. `ar3` is declared here and appears NOWHERE else:
#
#   * no bridge host variable. The group is exactly three items long -
#     HV-IRS-FINAL-ACC-REC-KEY, HV-IRS-AR1, HV-IRS-AR2
#     [common/irsfinalMT.cbl:L171-L174] - and a search of the whole bridge
#     for `ar3` returns zero matches.
#   * no column. The table is exactly three columns wide -
#     IRS-FINAL-ACC-REC-KEY tinyint(2) unsigned, IRS-AR1 char(24),
#     IRS-AR2 char(1), all NOT NULL [mysql/ACASDB.sql:L214-L219].
#
# So the bridge drops it, silently, on every write. It is kept here because
# it is part of the record and part of the 655 bytes, and because R-3 forbids
# removing what the copybook declares just as firmly as it forbids adding
# what the copybook does not. Its entry key is looked up like every other,
# and the artifact flags the one-sidedness itself.
#
# The mirror case is `records/irs_posting.py`, where three columns exist with
# no copybook field [common/irspostingMT.cbl:L982-L987]. What happens to a
# value in `ar3` across a write-then-read round trip is an open question for
# `docs/migration/ambiguity-resolutions.md`, to be measured against the
# compiled program rather than reasoned about (R-6).
_AR3_DESCRIPTOR: Final[FieldDescriptor] = _descriptor_for("ar3")

_AR3_INITIAL: Final[str] = _initial_value(_AR3_DESCRIPTOR)


# =============================================================================
#  01  Final-Record.                          [copybooks/irswsfinal.cob:L7]
# =============================================================================

# The record's own five declared members, in copybook declaration order: the
# first enumerated group, the FILLER group redefining it, the second
# enumerated group, the FILLER group redefining that, and `ar3`. The two
# FILLER groups are looked up by what they redefine, since neither has a
# name to look up.
_RECORD_MEMBER_DESCRIPTORS: Final[tuple[FieldDescriptor, ...]] = (
    _descriptor_for("ar1-fields"),                                # L8
    _redefining_group_for("ar1-fields"),                           # L35
    _descriptor_for("ar2-fields"),                                # L38
    _redefining_group_for("ar2-fields"),                           # L65
    _AR3_DESCRIPTOR,                                               # L68
)


@dataclass(slots=True)
class IrsFinalRecord:
    """The IRS final-accounts record: COBOL `01 Final-Record.`, 655 bytes.

    Declared at [copybooks/irswsfinal.cob:L7]. The COBOL identifier is
    `Final-Record`, verbatim, and the Python name carries a prefix it does
    not have, because a second in-scope copybook declares an `01` of
    exactly the same name that is a DIFFERENT RECORD:
    `copybooks/wsfinal.cob:L10`, whose `ar1` is `pic x(16) occurs 26` with no
    `ar2` and no `ar3`, which totals 1024 bytes, maps to `SYSFINAL-REC` and
    is migrated as `SysFinalRecord` in `records/system_final.py`. The two are
    never merged, never share a descriptor and never import one another; the
    module docstring above sets out the full comparison. `irs030` supplies no
    caller-side `replacing` name to borrow, since it stubs this record out
    altogether [irs/irs030.cbl:L296], so the prefix is this migration's own
    disambiguation, chosen to pair with `SysFinalRecord`.

    655 bytes: 26 x 24 for the first group, 26 x 1 for the second and 5 for
    `ar3`, which is the figure the copybook header states at L6, "rec 655
    bytes +1 15/02/09". The trailing "+1" of that header is unexplained and
    is recorded rather than acted on.

    Five members, in copybook declaration order, and no others. In
    particular THERE IS NO KEY ATTRIBUTE: the table's primary key,
    `IRS-FINAL-ACC-REC-KEY`, is declared by the bridge and the schema alone
    and its value is the `OCCURS` SUBSCRIPT, so one instance of this record
    corresponds to as many as 26 rows. The bridge says so in its own comment,
    `*> KEY = table position` [common/irsfinalMT.cbl:L455], and walks the
    array to write them [:L476-L485], [:L524-L529]. Reproducing that fan-out,
    the `IRS-` prefix the bridge adds to every column name, the drop of
    `ar3` and the trailing-space trim at [:L638] and [:L647] is the work of
    `acas_posting/dal/acasirsub5_irs_final.py`, not of this module.

    Attributes:
        ar1_fields: `03 ar1-fields.` [:L8], the 26 enumerated 24-character
            items.
        ar1_view: `03 filler redefines ar1-fields.` [:L35], the same bytes as
            `05 ar1 pic x(24) occurs 26.` [:L36].
        ar2_fields: `03 ar2-fields.` [:L38], the 26 enumerated
            single-character items.
        ar2_view: `03 filler redefines ar2-fields.` [:L65], the same bytes as
            `05 ar2 pic x occurs 26.` [:L66].
        ar3: `03 ar3 pic x(5).` [:L68]. Declared by the copybook, carried by
            no host variable and stored in no column - see the block above
            this class.
        FIELDS: The five member descriptors, in copybook declaration order.
            The `01` group has an entry of its own,
            `Final-Record.Final-Record#7`, which this class stands for rather
            than holds.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _RECORD_MEMBER_DESCRIPTORS

    # 03  ar1-fields.                      [copybooks/irswsfinal.cob:L8]
    ar1_fields: Ar1Fields = field(default_factory=Ar1Fields)

    # 03  filler  redefines  ar1-fields.   [copybooks/irswsfinal.cob:L35]
    ar1_view: Ar1View = field(default_factory=Ar1View)

    # 03  ar2-fields.                      [copybooks/irswsfinal.cob:L38]
    ar2_fields: Ar2Fields = field(default_factory=Ar2Fields)

    # 03  filler  redefines  ar2-fields.   [copybooks/irswsfinal.cob:L65]
    ar2_view: Ar2View = field(default_factory=Ar2View)

    # 03  ar3  pic x(5).                   [copybooks/irswsfinal.cob:L68]
    # Copybook-only: no host variable, no column, dropped by the bridge.
    ar3: str = _AR3_INITIAL

    # DELIBERATE ABSENCE - do not add an attribute here.
    #
    # `IRS-FINAL-ACC-REC-KEY`, the table's primary key
    # [mysql/ACASDB.sql:L215], has no counterpart in this copybook and gets
    # none here. It is the bridge's own host variable
    # `HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP`
    # [common/irsfinalMT.cbl:L172] - wider, at three digits, than the
    # `tinyint(2) unsigned` column it feeds - and its value is the array
    # subscript, set by `move A to HV-IRS-FINAL-ACC-REC-KEY` [:L481] inside
    # `perform varying A from 1 by 1 until A > 26` [:L476].
    #
    # The bridge guards it at [:L426], `if HV-IRS-FINAL-ACC-REC-KEY = zero
    # or > 26`, reporting the offending value through `WE-Error` [:L428];
    # 26 agrees with `OCCURS 26` exactly. Its sibling `irsdfltMT` guards the
    # same shape of key with `> 32` against a copybook declaring
    # `occurs 33` [common/irsdfltMT.cbl:L575],
    # [copybooks/irswsdflt.cob:L9] - an off-by-one there, and none here.
    #
    # No key attribute, no subscript accessor, no by-position view, no
    # range guard and no 1-based-to-0-based adjustment lives in this
    # module. `acas_posting/dal/acasirsub5_irs_final.py` owns every part of
    # it.
