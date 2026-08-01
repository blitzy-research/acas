"""The IRS nominal ledger account layout - ``copybooks/irswsnl.cob``.

One copybook, one table, four plain dataclasses. This file is a RECORD
LAYOUT and nothing else. It mirrors ``01 NL-Record`` field for field and
takes every attribute's storage metadata from the generated data
dictionary rather than typing it in by hand, because "field metadata is
therefore derived, not transcribed, which eliminates an entire class of
transcription error across several hundred fields" (section 0.3.3).

THE TWO COBOL IDENTIFIERS
-------------------------
The record carries two names in the frozen sources, and both are recorded
here so that a reader arriving from either side lands in the right place:

    ``NL-Record``           the copybook's own 01-level name
                            [copybooks/irswsnl.cob:L8]

    ``WS-IRSNL-Record``     the name the caller substitutes
                            [irs/irs030.cbl:L286]

        copy "irswsnl.cob"   replacing NL-Record by WS-IRSNL-Record.

The Python class follows the caller-side substitution and is named
``WsIrsnlRecord``, because that is the disambiguated identifier the COBOL
itself supplies and the one the bridge program uses for its own copy of
the layout [common/irsnominalMT.cbl:L224]. The generated dictionary keys
the record under the copybook name instead - ``NL-Record`` - so a lookup
by ``WS-IRSNL-Record`` finds nothing. Both facts matter, and neither is
a mistake to be tidied away.

THE ENTITY SPINE
----------------
From the entity-to-table spine of section 0.2.1.1:

    entity facade     IRS nominal
    handler           ``acasirsub1``      [common/acasirsub1.cbl]
    bridge            ``irsnominalMT``    [common/irsnominalMT.cbl]
    table             ``IRSNL-REC``       15 columns, primary key KEY-1
    record copybook   ``copybooks/irswsnl.cob``

THE BRIDGE DECLARES ITS RECORD INLINE
-------------------------------------
``irsnominalMT`` is one of four bridges - with ``valueMT``, ``analMT``
and ``purchMT`` - that declare their working-storage record INLINE rather
than by ``COPY``. It writes out ``01 WS-IRSNL-Record.`` itself at
[common/irsnominalMT.cbl:L224] and copies ``irswsnl.cob`` nowhere. This
module is therefore built from the COPYBOOK, and the bridge is read only
for its host-variable group [common/irsnominalMT.cbl:L194-L209] and its
table directive, ``TABLE=IRSNL-REC,HV`` [common/irsnominalMT.scb:L187].

THE COPYBOOK, VERBATIM
----------------------
Twenty-four lines in full, the maintainer's own header included::

    *>*******************************************
    *>                                          *
    *>  Working Storage for the Nominal Ledger  *
    *>                                          *
    *>*******************************************
    *> Chgd 16/01/09 money to 99M
    *>
     01  NL-Record.                                          L8
         03  NL-Key.                                         L9
             05  NL-Owning      pic 9(5).                    L10
             05  NL-Sub-Nominal pic 9(5).                    L11
         03  NL-Type            pic x.                       L12
             88  Owner                   value is "O".       L13
             88  Sub                     value is "S".       L14
         03  NL-Data.                                        L15
             05  NL-Name        pic x(24).                   L16
             05  NL-DR          pic 9(8)v99   comp.          L17
             05  NL-CR          pic 9(8)v99   comp.          L18
             05  NL-DR-Last     pic 9(8)v99   comp  occurs  4.   L19
             05  NL-CR-Last     pic 9(8)v99   comp  occurs  4.   L20
             05  NL-AC          pic x.                       L21
         03  filler  redefines  NL-Data.                     L22
             05  NL-Pointer     pic 9(5).                    L23

FIFTEEN LEAF ITEMS, FIFTEEN COLUMNS
-----------------------------------
The two counts agree, but not for the reason a glance suggests, and the
arithmetic is worth writing down because it is the only way to be sure
nothing was dropped::

    2   NL-Owning + NL-Sub-Nominal
    1   NL-Type
    1   NL-Name
    2   NL-DR + NL-CR
    4   NL-DR-Last, expanded from OCCURS 4
    4   NL-CR-Last, expanded from OCCURS 4
    1   NL-AC
    1   NL-Pointer
    --
    15  leaf items

    15  columns in the table

They coincide because two adjustments cancel. The two key parts
CONCATENATE into the single column ``KEY-1``, which costs one; and the
redefining view still earns a column of its own, ``REC-POINTER``, which
returns one. A layout that dropped either would still total fifteen
somewhere and be wrong in two places at once.

THE DICTIONARY KEYS
-------------------
Every key below was read out of the artifact - through
``loader.entries_for_table("IRSNL-REC")`` and
``loader.entries_for_copybook_record("NL-Record")`` - and none was
guessed from the field name. On this table guessing does not survive
contact with the source, twice over. Thirteen fields are keyed by TABLE
and COLUMN; the two key parts have no column at all, because their parent
group owns it, so they are keyed by COPYBOOK RECORD and FIELD::

    copybook field      dictionary key                  column
    --------------      --------------                  ------
    NL-Key   (group)    IRSNL-REC.KEY-1                 KEY-1
    NL-Owning           NL-Record.NL-Owning             none
    NL-Sub-Nominal      NL-Record.NL-Sub-Nominal        none
    NL-Type             IRSNL-REC.TIPE                  TIPE
    NL-Data  (group)    NL-Record.NL-Data               none
    NL-Name             IRSNL-REC.NL-NAME               NL-NAME
    NL-DR               IRSNL-REC.DR                    DR
    NL-CR               IRSNL-REC.CR                    CR
    NL-DR-Last          IRSNL-REC.DR-LAST-01 .. -04     DR-LAST-01..04
    NL-CR-Last          IRSNL-REC.CR-LAST-01 .. -04     CR-LAST-01..04
    NL-AC               IRSNL-REC.AC                    AC
    filler   (group)    NL-Record.filler                none
    NL-Pointer          IRSNL-REC.REC-POINTER           REC-POINTER

    the record itself   NL-Record.NL-Record             none

THE COLUMN NAMES DROP THE PREFIX - EXCEPT ONCE
----------------------------------------------
The bridge strips the ``NL-`` prefix from five names and keeps it on the
sixth. There is no rule behind it::

    NL-Type      ->  TIPE          stripped, and spelled phonetically,
                                   presumably to dodge a reserved word
    NL-DR        ->  DR            stripped
    NL-CR        ->  CR            stripped
    NL-AC        ->  AC            stripped
    NL-Pointer   ->  REC-POINTER   stripped, and renamed
    NL-Name      ->  NL-NAME       KEPT

``loader.drift_for`` reports a name difference on every one of those
except ``NL-NAME``, which is exactly the asymmetry. This is the clearest
argument in the whole record folder for looking a key up instead of
deriving it from the field name by rule.

OCCURS 4 IS ONE-BASED, AND THE BRIDGE INTERLEAVES THE TWO ARRAYS
----------------------------------------------------------------
The copybook declares the two arrays CONSECUTIVELY, so in COBOL storage
all four DR entries precede all four CR entries. The bridge host variables
[common/irsnominalMT.cbl:L200-L207] and the table columns pair them off by
quarter instead::

    copybook storage order      bridge and column order
    ----------------------      -----------------------
    NL-DR-Last(1..4)            DR-LAST-01,  CR-LAST-01,
    NL-CR-Last(1..4)            DR-LAST-02,  CR-LAST-02,
                                DR-LAST-03,  CR-LAST-03,
                                DR-LAST-04,  CR-LAST-04

COBOL subscripts count from one, so ``NL-DR-Last(1)`` is ``DR-LAST-01``
and ``NL-DR-Last(4)`` is ``DR-LAST-04``; the Python tuples index from
zero, and no accessor is provided here to paper over the difference.
This module models the COPYBOOK order - two separate members, each a
fixed four-element tuple. Interleaving them is the flattening that
``dal/acasirsub1_irs_nominal.py`` performs at the bridge boundary, and it
is not performed here.

COMP WITH A V IS DECIMAL, NOT INT
---------------------------------
``NL-DR``, ``NL-CR``, ``NL-DR-Last`` and ``NL-CR-Last`` are declared
``pic 9(8)v99 comp`` - binary storage carrying an implied two-place
decimal scale - which is ten fields once the two arrays expand. The
dictionary gives all ten ``python_storage = DECIMAL``, ``scale = 2`` and
``quantum = 0.01``, so they are ``decimal.Decimal`` here.

The shortcut "binary means int" is right only at scale zero. The seven
statistics fields at [copybooks/wssl.cob:L46-L52] are ``binary-long``
with no ``V`` and no scale, so they ARE ``int``, and section 0.6.1
records why that matters: "their truncation on divide is integer
truncation, which is exactly what makes the moving-average defect
reproducible". Same storage family, opposite Python carrier, and the
scale alone decides. Typing these ten as ``int`` would silently discard
the pence from every IRS ledger balance.

One point of vocabulary, since it reads as a contradiction otherwise:
``FieldDescriptor.is_binary_family`` is FALSE for these fields.
That property means BINARY-CHAR, BINARY-SHORT or BINARY-LONG
specifically - the items whose range comes from a declared width - while
``COMP`` takes its range from a picture [acas_posting/cobol/field.py].
The fields are binary in storage and outside that family by name.

THE ACCUMULATORS CARRY NO SIGN
------------------------------
No ``S`` appears in ``pic 9(8)v99``, and the columns agree:
``decimal(10,2) unsigned``. The descriptors report ``signed = False``
with ``sign_position = NONE``, and their value domain runs from zero to
9999999999 - there is no negative range at all.

``NL-DR`` and ``NL-CR`` are nonetheless the ACCUMULATORS that the IRS
posting step adds into [irs/irs030.cbl:L1685-L1699]. An unsigned
accumulator has no defined behaviour for a result below zero, and that
question is left open here on purpose - see the open questions below. No
guard, no ceiling, no absolute value and no widening to a signed field
is applied, because any of those would be a repair.

A second point of vocabulary: the descriptors report
``unsigned = False`` even so. That member flags the explicit UNSIGNED
KEYWORD, which only a binary-family item can carry; a picture that
merely omits the ``S`` "is unsigned in a different sense: it still
occupies a sign nibble or an overpunch position"
[acas_posting/cobol/field.py]. Absence of a sign is read off ``signed``
and ``sign_position``, not off ``unsigned``.

USAGE IS DECLARED ON THE FIELD, NOT ON THE GROUP
------------------------------------------------
``NL-Data`` at [copybooks/irswsnl.cob:L15] carries NO usage clause - it
is the bare line ``03  NL-Data.`` - and each of the four numeric fields
writes ``comp`` on its own picture line. The dictionary therefore reports
``usage_declared_at = FIELD`` and ``usage_inherited_from = None``.

This copybook is the exception rather than the rule. The usage clause
sits on a GROUP HEADER, and is inherited by the children, at
[copybooks/wsbatch.cob:L40], [copybooks/wssys4.cob:L9] and [:L20],
[copybooks/wssystem.cob:L55], [copybooks/slwsinv.cob:L43],
[copybooks/plwspinv.cob:L31], [copybooks/slwsoi.cob:L16] and [:L35], and
[copybooks/plwsoi.cob:L20] and [:L41]. Reading the direction backwards
in either place retypes the fields and changes every stored value, so the
direction is stated here rather than left to be inferred.

NL-POINTER REDEFINES THE WHOLE DATA GROUP, AND STILL GETS A COLUMN
------------------------------------------------------------------
``03 filler redefines NL-Data.`` [copybooks/irswsnl.cob:L22] lays
``NL-Pointer pic 9(5)`` over the SAME BYTES as ``NL-Name``, the ten
accumulators and ``NL-AC``. In COBOL these are two views of one storage
area: writing through one disturbs what the other reads.

The bridge materialises BOTH regardless. ``HV-REC-POINTER PIC 9(08)
COMP`` [common/irsnominalMT.cbl:L209] becomes the column ``REC-POINTER
mediumint(5) unsigned``, so one row carries ``NL-NAME``, ``DR``, ``CR``,
the eight quarter columns, ``AC`` AND ``REC-POINTER`` - fifteen columns
of which the last is a different reading of eleven of the others.

The two views are modelled as two separate dataclasses, ``NlData`` and
``NlPointerView``. Neither is treated as the primary one, neither is
omitted, no discriminator says which is live, and no union or switching
accessor is offered. What the pointer column holds while the data view is
populated is an open question below, not a decision for this file.

The redefining group's COBOL name is ``filler`` - it is unnamed, and the
dictionary keys it as ``NL-Record.filler`` with ``is_filler`` true and
``redefines`` naming ``NL-Data``. The REDEFINES clause sits on that 03
group, not on the 05 item inside it. Naming the Python class after the
field it contains keeps it readable; this paragraph keeps the traceability
that the rename would otherwise cost. Unnamed redefinitions are the house
style across the frozen copybooks - ``redefines`` appears 60 times, among
them [copybooks/wsledger.cob:L16] and [:L35], [copybooks/wssl.cob:L61],
[copybooks/wspl.cob:L50] and [copybooks/wsval.cob].

THE 88 CONDITION NAMES ARE RECORDED HERE AND DECLARED ELSEWHERE
---------------------------------------------------------------
``NL-Type`` carries two condition names, spelled with the optional
``is``, which the sibling copybooks omit - compare
[copybooks/wsbatch.cob:L16-L18]::

    88  Owner   value is "O".       [copybooks/irswsnl.cob:L13]
    88  Sub     value is "S".       [copybooks/irswsnl.cob:L14]

Their values are the strings ``"O"`` and ``"S"``; the dictionary model
holds a condition name's value as a string always, even where it looks
numeric. No predicate, enumeration, literal type, class constant or
``is``-style method appears in this module: section 0.4.1.4 assigns the
88-levels to ``acas_posting/cobol/condition_names.py``, and a second
declaration here would be a second place to keep in step.

BRIDGE DRIFT: FOUR KINDS, ALL LEFT STANDING
-------------------------------------------
The copybook field, the bridge host variable and the table column
disagree in four distinct ways on this record::

    1  group concatenation and digit widening
       NL-Key, two unsigned 9(5) making ten digits
         ->  HV-KEY-1 PIC 9(18) COMP        widened to 18
         ->  KEY-1 bigint(10) unsigned      back down to 10

    2  the prefix inconsistency described above, five names changed and
       one left alone

    3  the array interleaving described above

    4  digit widening on the pointer
       NL-Pointer pic 9(5)
         ->  HV-REC-POINTER PIC 9(08) COMP  widened to 8, and retyped
         ->  REC-POINTER mediumint(5)       back down to 5

Kind 4 is not even monotonic: the host variable is wider than both the
copybook that feeds it and the column it feeds.

Each descriptor in this module reports the COPYBOOK view as its own
digits, scale, sign and usage, and offers the disagreement through
``descriptor.drift()``, which is a pass-through of ``loader.drift_for``.
Nothing here blends the three layers into one figure, widens a field,
renames an attribute to its column, or reorders the members into column
order. Reproducing the bridge's conversions is the handler module's work,
at the bridge boundary: ``dal/acasirsub1_irs_nominal.py``.

WHY EVERY DEFAULT IS A VALUE AND NEVER NONE
-------------------------------------------
All fifteen columns are declared ``NOT NULL``, and section 0.6.2 explains
why they can be: "each load paragraph begins by initialising the
host-variable group, so unset fields become zero or space rather than SQL
NULL. This is why every column in the schema can be declared NOT NULL and
why the Python layer must default rather than omit." On this bridge that
initialisation is ``initialize WS-IRSNL-Record with filler``
[common/irsnominalMT.cbl:L524].

So the defaults are ``0`` for the zoned integers, ``Decimal("0.00")`` for
the ten money fields, and spaces at the declared width for the three
alphanumerics - taken from each field's own descriptor rather than
written out as a number here. Never ``None``.

TWO ANOMALIES OPERATE ON THIS RECORD
------------------------------------
Both are reproduced in ``programs/irs030_posting.py``, which owns the
posting logic; they are recorded here because this is the layout they act
on, so that ``docs/migration/anomaly-log.md`` can cite it.

    Anomaly 4, the half-posted double entry. "the debit is rewritten
    before the credit account is looked up, so a missing credit leaves an
    unbalanced debit and no posting record"
    [irs/irs030.cbl:L1635-L1652].

    Anomaly 5, the lost update on the two VAT control accounts. Two
    accounts are read into snapshots before the loop
    [irs/irs030.cbl:L1602] and [:L1612] and written back from those
    snapshots at end of job [irs/irs030.cbl:L1704-L1708], so any
    in-loop rewrite of the same two accounts is discarded. Section 0.6.5
    calls it "a classic lost update".

This module supplies NO snapshot, clone, copy, replace, rewrite or
change-detection facility, and its dataclasses are not immutable. That is
deliberate to the point of being the main design constraint on the file: a
snapshot mechanism in the record layer would make anomaly 5 avoidable, and
rule R-4 requires that it stay reproducible. A defect reproduced is
correct; a defect fixed is a failure.

THREE OPEN QUESTIONS FOR THE COMPILED ORACLE
--------------------------------------------
Recorded, not settled. Each belongs in
``docs/migration/ambiguity-resolutions.md`` with the experiment that
decides it, per rule R-6.

    a.  What an unsigned ``9(8)v99 comp`` accumulator actually stores
        when a posting would drive it below zero. Section 0.6.8 already
        lists "a negative binary value through an unsigned host variable
        into an unsigned column" as something to be measured, "not
        assumed".

    b.  What ``REC-POINTER`` contains in a row whose data view is
        populated, and what the data columns contain in a row written
        through the pointer view.

    c.  Whether the interleaved column order is observable in a table
        dump at all, or whether it is invisible once rows are ordered by
        primary key.

WHAT THIS MODULE DOES NOT DO
----------------------------
It holds no posting, accumulation, snapshot or rewrite logic; those are
``programs/irs030_posting.py``. It holds no SQL, no key concatenation, no
column renaming, no array flattening and no host-variable conversion;
those are ``dal/acasirsub1_irs_nominal.py``. It performs no padding,
truncation, quantising or arithmetic; those are ``cobol/move.py`` and
``cobol/arithmetic.py``. It adds no field, alias or check of its own
(R-3), and it emits no DDL - the schema is frozen.

LAYERING - THIS IS A LEAF
-------------------------
Section 0.4.3 grants ``records/*.py`` exactly two internal imports and
forbids the rest, "this keeps the record layer a leaf". Only
``acas_posting.cobol.field`` is imported below, plus the standard
library; the loader is reached through the descriptors rather than
directly, so nothing here imports a module it does not use. Nothing in
this file runs, embeds or shells out to a COBOL program (R-1), no value
passes through binary floating-point storage (R-2), and nothing is read
at import time beyond the loader's own lazily cached read of the
generated artifact (R-6).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

__all__ = ["NlData", "NlKey", "NlPointerView", "WsIrsnlRecord"]


# =============================================================================
#  THE FIELD DESCRIPTORS  (rule R-5 - looked up, never transcribed)
# =============================================================================
#
# Each key below was read out of the generated artifact, by listing
# ``loader.entries_for_table("IRSNL-REC")`` and
# ``loader.entries_for_copybook_record("NL-Record")`` and reading each
# entry's copybook name, rather than being built from the field name by
# rule. On this record that distinction is load-bearing: the column names
# drop the ``NL-`` prefix five times and keep it once, ``NL-Type`` is
# spelled ``TIPE``, and the two key parts carry no column at all because
# their parent group carries it. Every entry here was confirmed to come
# from ``copybooks/irswsnl.cob`` - two IRS copybooks collide on
# ``Default-Record`` and ``Final-Record`` elsewhere in this folder, so the
# file is checked and not assumed.
#
# The lookups run while the classes below are being defined, which is this
# package's own convention. ``from_dictionary_key`` is memoised and the
# loader reads the artifact lazily and caches it, so this costs one read
# per process and none at all until the first record module is imported.

# -- 03  NL-Key.  [copybooks/irswsnl.cob:L9] ---------------------------------
#
# The GROUP carries the column: its two 9(5) children concatenate into the
# single ``KEY-1``, which is drift kind 1 and is applied at the bridge
# boundary, not here.
_NL_KEY: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.KEY-1")
_NL_OWNING: Final = FieldDescriptor.from_dictionary_key(
    "NL-Record.NL-Owning"
)
_NL_SUB_NOMINAL: Final = FieldDescriptor.from_dictionary_key(
    "NL-Record.NL-Sub-Nominal"
)

# -- 03  NL-Type  pic x.  [copybooks/irswsnl.cob:L12] ------------------------
#
# Two condition names hang off this field, ``88 Owner value is "O"`` and
# ``88 Sub value is "S"`` [copybooks/irswsnl.cob:L13-L14]. They are
# recorded in the module docstring and declared in
# ``cobol/condition_names.py``; nothing here tests them.
_NL_TYPE: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.TIPE")

# -- 03  NL-Data.  [copybooks/irswsnl.cob:L15] -------------------------------
#
# The group header carries NO usage clause, so each numeric child below
# declares ``comp`` itself and every descriptor reports
# ``usage_declared_at = FIELD``. Most sibling copybooks put the usage on
# the group header instead; see the module docstring.
_NL_DATA: Final = FieldDescriptor.from_dictionary_key("NL-Record.NL-Data")
_NL_NAME: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.NL-NAME")

# The ten money fields: COMP with an implied two-place scale, so DECIMAL
# and never int. See the module docstring for the contrast with the
# scale-zero binary-long fields at [copybooks/wssl.cob:L46-L52].
_NL_DR: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.DR")
_NL_CR: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.CR")

# ``occurs 4`` [copybooks/irswsnl.cob:L19-L20]. The dictionary holds one
# entry per OCCURRENCE, keyed by the column the bridge writes it to, and
# each of the four reports the same copybook name with ``occurs = 4``.
# The four keys are written out in full rather than generated from a
# counter, so that each stays greppable and auditable against the
# artifact. Subscripts below are the COBOL one-based ones: entry 1 is
# ``DR-LAST-01``. The copybook's own order - all four DR, then all four
# CR - is kept; the bridge's quarter-by-quarter interleaving is not
# applied here.
_NL_DR_LAST: Final[tuple[FieldDescriptor, ...]] = (
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-01"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-02"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-03"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.DR-LAST-04"),
)
_NL_CR_LAST: Final[tuple[FieldDescriptor, ...]] = (
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-01"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-02"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-03"),
    FieldDescriptor.from_dictionary_key("IRSNL-REC.CR-LAST-04"),
)

_NL_AC: Final = FieldDescriptor.from_dictionary_key("IRSNL-REC.AC")

# -- 03  filler  redefines  NL-Data.  [copybooks/irswsnl.cob:L22] -----------
#
# The REDEFINES clause sits on this 03 group, which the copybook leaves
# unnamed, so the artifact keys it ``NL-Record.filler`` with ``is_filler``
# true and ``redefines`` naming ``NL-Data``. Its single 05 child gets a
# column of its own even though it overlays eleven other columns' bytes.
_NL_POINTER_FILLER: Final = FieldDescriptor.from_dictionary_key(
    "NL-Record.filler"
)
_NL_POINTER: Final = FieldDescriptor.from_dictionary_key(
    "IRSNL-REC.REC-POINTER"
)


# =============================================================================
#  THE DEFAULTS  (a value always, never None - see the module docstring)
# =============================================================================
#
# ``initialize WS-IRSNL-Record with filler``
# [common/irsnominalMT.cbl:L524] leaves an unset numeric field at zero and
# an unset alphanumeric field at spaces before any row is written, which is
# how all fifteen columns can be ``NOT NULL``. These defaults reproduce
# that starting state and nothing more: no padding, quantising, truncation
# or checking happens here, because a store is ``cobol/move.py`` and
# ``cobol/arithmetic.py`` business.

# The two-place scale is the dictionary's, not a choice made here: all ten
# money descriptors report ``scale = 2`` and ``quantum = Decimal("0.01")``.
_ZERO_MONEY: Final = Decimal("0.00")

# Alphanumeric widths come from each field's own descriptor, so that the
# declared ``pic x(24)`` and ``pic x`` are never retyped as numbers here.
_NL_NAME_SPACES: Final = " " * _NL_NAME.byte_length
_NL_TYPE_SPACES: Final = " " * _NL_TYPE.byte_length
_NL_AC_SPACES: Final = " " * _NL_AC.byte_length


# =============================================================================
#  THE RECORD  (four dataclasses, in copybook declaration order)
# =============================================================================


@dataclass(slots=True)
class NlKey:
    """``03  NL-Key.`` [copybooks/irswsnl.cob:L9].

    The account number, in two unsigned zoned parts. Both are ``pic 9(5)``
    with no usage clause, so both are DISPLAY at scale zero and both are
    carried as ``int``.

    Neither part has a column of its own. The group above them owns the
    single ``KEY-1 bigint(10) unsigned``, the table's primary key, and the
    bridge concatenates the two into it through
    ``HV-KEY-1 PIC 9(18) COMP`` [common/irsnominalMT.cbl:L195] - ten
    declared digits widened to eighteen at the host variable and narrowed
    to ten again at the column. That concatenation is drift kind 1 and
    belongs to ``dal/acasirsub1_irs_nominal.py``; no combined key value is
    formed here.

    Because they map to no column, these two are the only fields of the
    record keyed by copybook record and field name rather than by table
    and column.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _NL_OWNING,
        _NL_SUB_NOMINAL,
    )

    # NL-Owning  pic 9(5)  DISPLAY  [copybooks/irswsnl.cob:L10]
    nl_owning: int = 0
    # NL-Sub-Nominal  pic 9(5)  DISPLAY  [copybooks/irswsnl.cob:L11]
    nl_sub_nominal: int = 0


@dataclass(slots=True)
class NlData:
    """``03  NL-Data.`` [copybooks/irswsnl.cob:L15].

    The account's name, its two running totals, its two four-quarter
    histories and its analysis code. Twelve of the table's fifteen columns
    come from here.

    Every numeric field in this group is ``pic 9(8)v99 comp`` - binary
    storage with an implied two-place scale and no sign - so every one is
    ``decimal.Decimal`` at scale 2, and none is ``int``. The group header
    itself declares no usage; each field declares ``comp`` on its own
    line. The module docstring sets out why both of those facts change
    stored values if read the other way round.

    ``nl_dr`` and ``nl_cr`` are the accumulators the IRS posting step adds
    into [irs/irs030.cbl:L1685-L1699], and they are unsigned, with a value
    domain starting at zero. What the compiled program stores when a
    posting would take one below zero is open question (a) in the module
    docstring. No guard against it appears here.

    ``FIELDS`` holds TWELVE descriptors for SIX attributes, because the
    dictionary keys each OCCURS entry separately - one per column - so the
    two arrays contribute four descriptors each. Its order is the
    copybook's own: name, DR, CR, the four DR quarters, the four CR
    quarters, then the analysis code. The table interleaves those eight
    quarter columns DR-then-CR by quarter; this does not.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _NL_NAME,
        _NL_DR,
        _NL_CR,
        *_NL_DR_LAST,
        *_NL_CR_LAST,
        _NL_AC,
    )

    # NL-Name  pic x(24)  [copybooks/irswsnl.cob:L16]
    #
    # 24 characters in the copybook, 24 in the host variable and 24 in the
    # column - the one name on this record the bridge leaves alone, and
    # the only one ``drift_for`` reports no name difference on. Contrast
    # ``Ledger-Name``, which widens from 24 to 32
    # [common/nominalMT.cbl:L299].
    nl_name: str = _NL_NAME_SPACES

    # NL-DR  pic 9(8)v99 comp  [copybooks/irswsnl.cob:L17]
    #
    # Debit accumulator. COMP with a V: 10 digits, 8 before the implied
    # point and 2 after, unsigned. Column ``DR decimal(10,2) unsigned``.
    nl_dr: Decimal = _ZERO_MONEY

    # NL-CR  pic 9(8)v99 comp  [copybooks/irswsnl.cob:L18]
    #
    # Credit accumulator, declared identically. Column ``CR``.
    nl_cr: Decimal = _ZERO_MONEY

    # NL-DR-Last  pic 9(8)v99 comp  occurs 4  [copybooks/irswsnl.cob:L19]
    #
    # The four previous quarters' debit totals, in the copybook's own
    # order. A fixed four-element tuple, not a list, so the shape cannot
    # drift between two runs (R-6). COBOL indexes it from one, Python from
    # zero: ``nl_dr_last[0]`` is ``NL-DR-Last(1)``, which the bridge
    # writes to ``DR-LAST-01`` [common/irsnominalMT.cbl:L200]. No
    # accessor is provided to hide that difference.
    nl_dr_last: tuple[Decimal, Decimal, Decimal, Decimal] = (
        dataclasses.field(
            default_factory=lambda: (
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
            )
        )
    )

    # NL-CR-Last  pic 9(8)v99 comp  occurs 4  [copybooks/irswsnl.cob:L20]
    #
    # The four previous quarters' credit totals. Declared immediately
    # after the debit array, so in COBOL storage all four debit entries
    # precede all four credit entries - while the host variables and the
    # columns pair them off by quarter instead
    # [common/irsnominalMT.cbl:L200-L207]. The copybook's order is the one
    # kept here.
    nl_cr_last: tuple[Decimal, Decimal, Decimal, Decimal] = (
        dataclasses.field(
            default_factory=lambda: (
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
                _ZERO_MONEY,
            )
        )
    )

    # NL-AC  pic x  [copybooks/irswsnl.cob:L21]
    #
    # Column ``AC char(1)``; the ``NL-`` prefix is dropped.
    nl_ac: str = _NL_AC_SPACES


@dataclass(slots=True)
class NlPointerView:
    """``03  filler  redefines  NL-Data.`` [copybooks/irswsnl.cob:L22].

    The second reading of the same bytes. This group redefines the whole
    of ``NL-Data``, so its one field overlays ``NL-Name``, the ten
    accumulators and ``NL-AC`` - in COBOL, writing through one view
    disturbs what the other reads.

    The COBOL group is UNNAMED: its name is ``filler``, and the artifact
    keys it ``NL-Record.filler``. This class is named after the field it
    contains, for readability; the group's real identity is recorded here
    so that the traceability the rename would cost is not lost.

    The bridge materialises this view ALONGSIDE the data view rather than
    instead of it, so a single row carries the eleven data columns and
    ``REC-POINTER`` together. Which of the two a given row actually means
    is open question (b) in the module docstring. This class picks no
    winner, omits neither view, and carries no flag saying which is live.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_NL_POINTER,)

    # NL-Pointer  pic 9(5)  DISPLAY  [copybooks/irswsnl.cob:L23]
    #
    # Drift kind 4, and the only non-monotonic one on this record: 5
    # digits in the copybook, widened to 8 and retyped to COMP at
    # ``HV-REC-POINTER PIC 9(08) COMP``
    # [common/irsnominalMT.cbl:L209], then narrowed back to
    # ``REC-POINTER mediumint(5) unsigned``. ``drift_for`` flags the
    # usage, the digit count and the name all three. The copybook view -
    # DISPLAY, 5 digits, scale 0 - is what the descriptor here reports.
    nl_pointer: int = 0


@dataclass(slots=True)
class WsIrsnlRecord:
    """``01  NL-Record.`` [copybooks/irswsnl.cob:L8].

    One IRS nominal ledger account: the row of ``IRSNL-REC``, reached
    through handler ``acasirsub1`` and bridge ``irsnominalMT``.

    Named for the caller's substitution, ``WS-IRSNL-Record``
    [irs/irs030.cbl:L286], which is also the name the bridge gives its own
    inline copy of this layout [common/irsnominalMT.cbl:L224]. The
    copybook's own 01-level name is ``NL-Record`` [copybooks/irswsnl.cob:L8],
    and that is the name the generated dictionary keys the record under -
    ``NL-Record.NL-Record`` for the group itself.

    Members follow copybook declaration order, so this class can be set
    beside its copybook and read down. ``nl_data`` and
    ``nl_pointer_view`` are the two views of one storage area, held as two
    separate members because the bridge writes columns for both.

    The record is MUTABLE by design. It offers no snapshot, clone, copy,
    replace or rewrite facility and is not immutable, because anomaly 5 -
    the lost update on the two VAT control accounts
    [irs/irs030.cbl:L1602], [:L1612], [:L1704-L1708] - has to stay
    reproducible in ``programs/irs030_posting.py``, and a snapshot
    mechanism here would let a caller avoid it.

    This is a layout only. Posting, accumulation and rewriting are
    ``programs/irs030_posting.py``; SQL, key concatenation, column
    renaming and array flattening are
    ``dal/acasirsub1_irs_nominal.py``.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _NL_KEY,
        _NL_TYPE,
        _NL_DATA,
        _NL_POINTER_FILLER,
    )

    # NL-Key  group  [copybooks/irswsnl.cob:L9] -> column KEY-1
    nl_key: NlKey = dataclasses.field(default_factory=NlKey)

    # NL-Type  pic x  [copybooks/irswsnl.cob:L12] -> column TIPE
    #
    # The column name is the phonetic ``TIPE``, presumably dodging a
    # reserved word. Two condition names are declared on this field,
    # ``88 Owner value is "O"`` and ``88 Sub value is "S"``
    # [copybooks/irswsnl.cob:L13-L14] - note the optional ``is``, which
    # the sibling copybooks omit [copybooks/wsbatch.cob:L16-L18]. The
    # values are the strings "O" and "S". The predicates over them belong
    # to ``cobol/condition_names.py``, not here.
    nl_type: str = _NL_TYPE_SPACES

    # NL-Data  group  [copybooks/irswsnl.cob:L15] -> 12 columns
    nl_data: NlData = dataclasses.field(default_factory=NlData)

    # filler redefines NL-Data  [copybooks/irswsnl.cob:L22]
    #                                            -> column REC-POINTER
    nl_pointer_view: NlPointerView = dataclasses.field(
        default_factory=NlPointerView
    )
