"""The value-analysis record: ``WS-Value-Record`` [copybooks/wsval.cob:L9].

A CREATE from ``copybooks/wsval.cob``, per the Agent Action Plan's
transformation mapping, section 0.4.1.3:

    ``acas_posting/records/value_analysis.py`` | CREATE |
    ``copybooks/wsval.cob`` | Value-analysis record

Three plain dataclasses mirror that copybook field for field, in its
declaration order, with nothing added and nothing removed. The Sales and
Purchase extract steps accumulate their analysis totals into this record in
place - ``sl055`` and ``pl055`` - which is why no class here is frozen.

THE ENTITY SPINE, MACHINE-READABLE
==================================
Section 0.2.1.1 places this record on the entity spine, and the generated
dictionary carries the same facts so that they are checkable rather than
asserted. ``loader.find_table("VALUEANAL-REC")`` returns::

    name           VALUEANAL-REC
    entity_facade  Value
    handler        acas013
    bridge         valueMT
    copybooks      ('copybooks/wsval.cob',)
    primary_key    VA-CODE
    column_count   10
    ordinal_source mysql/ACASDB.sql:L1418

Section 0.6.6 records the same 10 columns and the same single-column primary
key. Every one of the 22 in-scope tables has a single-column primary key and
no secondary index, which is what lets the harness dump each table with
``SELECT * FROM <table> ORDER BY <primary key>`` and no tie-breaking logic.
Ordering therefore belongs to the harness dump step, not to this module: no
ordering method, no comparison method and no key-building helper appears
below.

THE COPYBOOK, VERBATIM - SET THIS BESIDE THE MODULE AND DIFF BY EYE
===================================================================
All 24 lines were read; the layout occupies L9 to L23::

     01  WS-Value-Record.                                     L9
         03  va-code.                                         L10
             05  va-system      pic x.                        L11
             05  va-group.                                    L12
                 07 va-first    pic x.                        L13
                 07 va-second   pic x.                        L14
         03  va-gl              pic 9(6).                     L15
         03  va-desc            pic x(24).                    L16
         03  va-print           pic xxx.                      L17
         03  va-t-this          pic 9(5)         comp.        L18
         03  va-t-last          pic 9(5)         comp.        L19
         03  va-t-year          pic 9(5)         comp.        L20
         03  va-v-this          pic s9(8)v99     comp-3.      L21
         03  va-v-last          pic s9(8)v99     comp-3.      L22
         03  va-v-year          pic s9(8)v99     comp-3.      L23

Its header, quoted verbatim with locators, doubled asterisk included::

    *>  Record Definition For The Analysis Value File *   L3
    *>  record size 66 bytes ** 08/03/09                  L6
    *>  WS record created from fdval.cob                   L7

Four spellings in that layout are odd, and section 0.4.1.3 governs all four:
oddities in the source are preserved, never repaired.

  * THE LEVEL NUMBERING JUMPS 05 -> 07. The key group nests four levels deep,
    01 -> 03 ``va-code`` -> 05 ``va-system`` / 05 ``va-group`` -> 07
    ``va-first`` / 07 ``va-second``, and no 06 level exists anywhere in the
    file [copybooks/wsval.cob:L10-L14]. The nesting below is exactly four
    deep for the same reason.
  * L13 AND L14 INDENT DIFFERENTLY FROM EVERY OTHER LINE. Both write
    ``07 va-first`` with ONE space after the level number where every other
    level line in the file uses two [copybooks/wsval.cob:L13-L14]. Recorded,
    not tidied.
  * ``pic xxx`` IS SPELT OUT AT L17 rather than written ``pic x(3)``. The
    descriptor for ``va-print`` carries the picture text exactly as the
    copybook writes it. The same spelling recurs at
    [copybooks/wsanal.cob:L17] and at [common/valueMT.cbl:L310,L313].
  * THE COBOL NAMES ARE LOWER-CASE THROUGHOUT. ``va-code``, ``va-system``,
    ``va-group``, ``va-first``, ``va-second``, ``va-gl``, ``va-desc``,
    ``va-print``, ``va-t-this``, ``va-t-last``, ``va-t-year``, ``va-v-this``,
    ``va-v-last``, ``va-v-year``. Every descriptor name and every comment
    below carries that casing verbatim. The bridge spells the same fields in
    mixed case; that spelling is registered further down and is not adopted.

WHAT THIS RECORD IS EXCEPTIONALLY CLEAN ABOUT
=============================================
Confirmed by grep over the frozen copybook: ``FILLER`` occurs 0 times,
``REDEFINES`` occurs 0 times, and there is no 88-level condition name, no
``OCCURS``, no ``SIGN`` clause, no ``VALUE`` clause and no ``JUSTIFIED`` or
``BLANK WHEN ZERO``. So no predicate function, no enumeration, no filler
placeholder and no redefinition appears below - there is nothing of that kind
in the source to mirror. That cleanliness is worth stating because it makes
the remaining oddities stand out as the real findings.

THE THREE LAYERS, SIDE BY SIDE AND UNSETTLED
============================================
Section 0.8.2 preserves the user's own instruction that the maintainer's
one-way COBOL-to-MySQL bridge defines the record-layout-to-table mapping and
is the data dictionary for this migration. It is quoted by reference rather
than transcribed here because rule R-4 forbids one of its words from
appearing anywhere in this file. Note the subtlety that follows from it: the
bridge governs the MAPPING, yet the bridge's own inline record flattens and
renames this record's key, so the COPYBOOK remains the source of the field
STRUCTURE - and the copybook is what the posting programs ``COPY``. This
module is built from the copybook for exactly that reason.

Copybook field, bridge host variable, MySQL column - all ten, with locators::

  va-code    L10  group of 3    HV-VA-CODE    X(3)         L287  VA-CODE
  va-gl      L15  9(6) DISPLAY  HV-VA-GL      9(08) COMP   L288  VA-GL
  va-desc    L16  x(24)         HV-VA-DESC    X(24)        L289  VA-DESC
  va-print   L17  xxx           HV-VA-PRINT   X(3)         L290  VA-PRINT
  va-t-this  L18  9(5) comp     HV-VA-T-THIS  9(08) COMP   L291  VA-T-THIS
  va-t-last  L19  9(5) comp     HV-VA-T-LAST  9(08) COMP   L292  VA-T-LAST
  va-t-year  L20  9(5) comp     HV-VA-T-YEAR  9(08) COMP   L293  VA-T-YEAR
  va-v-this  L21  s9(8)v99 c-3  HV-VA-V-THIS  9(08)V9(02)  L294  VA-V-THIS
  va-v-last  L22  s9(8)v99 c-3  HV-VA-V-LAST  9(08)V9(02)  L295  VA-V-LAST
  va-v-year  L23  s9(8)v99 c-3  HV-VA-V-YEAR  9(08)V9(02)  L296  VA-V-YEAR

Copybook lines are [copybooks/wsval.cob], host-variable lines are
[common/valueMT.cbl] inside the group ``01 TD-VALUEANAL-REC.``
[common/valueMT.cbl:L286], and the columns are [mysql/ACASDB.sql:L1419-L1428]
under ``CREATE TABLE `VALUEANAL-REC``` [mysql/ACASDB.sql:L1418].

A descriptor below reports the COPYBOOK view and only ever that view, because
a descriptor describes COBOL-side storage. Where the three layers disagree,
the disagreement is surfaced through ``loader.drift_for`` and left standing.
Nothing here blends layers, widens a field to a column's width or applies the
bridge's signedness loss.

NEW ANOMALY - THE THREE MONEY FIELDS LOSE THEIR SIGN AT THE BRIDGE
==================================================================
This is the headline finding of this record, and it is NOT one of the
twenty-two entries in section 0.6.7. It should be ADDED to
``docs/migration/anomaly-log.md`` with this module named as the recording
site. It extends anomaly A-11's class - signed value narrowed to an unsigned
host variable and an unsigned column - from STATISTICS fields to MONETARY
ones. The nine locators::

    va-v-this  pic s9(8)v99 comp-3   SIGNED    copybooks/wsval.cob:L21
    va-v-last  pic s9(8)v99 comp-3   SIGNED    copybooks/wsval.cob:L22
    va-v-year  pic s9(8)v99 comp-3   SIGNED    copybooks/wsval.cob:L23
    HV-VA-V-THIS PIC 9(08)V9(02) COMP  UNSIGNED  common/valueMT.cbl:L294
    HV-VA-V-LAST PIC 9(08)V9(02) COMP  UNSIGNED  common/valueMT.cbl:L295
    HV-VA-V-YEAR PIC 9(08)V9(02) COMP  UNSIGNED  common/valueMT.cbl:L296
    VA-V-THIS  decimal(10,2) unsigned            mysql/ACASDB.sql:L1426
    VA-V-LAST  decimal(10,2) unsigned            mysql/ACASDB.sql:L1427
    VA-V-YEAR  decimal(10,2) unsigned            mysql/ACASDB.sql:L1428

READ THIS IF YOU HAVE INTERNALISED SECTION 0.6.2. That section says of the
sales ledger, verbatim: "By contrast the monetary fields are declared signed
at all three layers and pass through cleanly, so the drift is specific rather
than systemic and must be handled field by field from the dictionary." That
sentence is TRUE of ``SALEDGER-REC`` and ``PULEDGER-REC`` and FALSE of
``VALUEANAL-REC``. Here MONEY ITSELF loses its sign, at the bridge, before any
SQL runs - so the section's closing clause, "handled field by field from the
dictionary", is the operative part and the reassuring part is not general.

The dictionary reaches the same conclusion independently, from its own
comparison of the three views rather than from any hand-written list, which is
why it found this at all. For each of the three keys::

    drift.signedness  True   copybook signed, host variable and column not
    drift.usage       True   COMP-3 at the copybook, COMP at the bridge
    anomaly_refs      ('A-11',)
    ambiguity_refs    ('Q-3',)

What this module therefore does, and does not do:

  * The descriptor keeps the copybook view - ``signed`` True, usage COMP-3,
    ``digits`` 10, ``scale`` 2 - so a negative total is representable and
    stays negative here.
  * The attribute is ``decimal.Decimal``, never a binary carrier (R-2).
  * No clamping, no sign stripping, no rejection of a negative value and no
    assumed wrap-around is written anywhere below.
  * The bridge's conversion belongs to ``dal/acas013_value.py``, which
    reproduces the bridge boundary. It is deliberately absent from this leaf
    module, and this module must not import that one (see LAYERING).
  * The drift is surfaced unsettled, through ``loader.drift_for``, which the
    descriptor exposes as a pass-through.

THE CONTRAST THAT PROVES THE DRIFT IS PER FIELD, NOT PER TABLE
==============================================================
The three counters pass through cleanly on signedness. ``va-t-this``,
``va-t-last`` and ``va-t-year`` are ``pic 9(5) comp`` - UNSIGNED already in
the copybook [copybooks/wsval.cob:L18-L20] - against ``PIC 9(08) COMP``
[common/valueMT.cbl:L291-L293] and ``mediumint(5) unsigned``
[mysql/ACASDB.sql:L1423-L1425]. Unsigned at all three layers: digit widening
only, no signedness change, and ``drift.signedness`` is False for all three
while ``drift.digits`` is True. ``va-gl`` shows a third pattern again -
``drift.usage`` and ``drift.digits`` both True, DISPLAY at the copybook and
COMP at the bridge - while ``va-code``, ``va-desc`` and ``va-print`` show no
drift at all. Six fields, four different dispositions, one table.

THE BRIDGE'S INLINE RECORD IS NOT THIS COPYBOOK - FOUR DIVERGENCES
==================================================================
``valueMT`` declares its own record inline and does NOT ``COPY`` this
copybook: ``grep 'copy "wsval'`` over [common/valueMT.cbl] returns nothing,
and its five COPY statements are ``ACAS-SQLstate-error-list.cob`` L164,
``mysql-variables.cpy`` L281, ``wsfnctn.cob`` L303, ``Test-Data-Flags.cob``
L307 and ``mysql-procedures.cpy`` L1026. Its inline record is
``01 VALUEANAL-REC.`` [common/valueMT.cbl:L309] with ten subordinate items at
L310-L319. It is one of four bridges that inline their record this way,
alongside ``analMT``, ``purchMT`` and ``irsnominalMT``.

  1. THE 01-NAME DIFFERS. The bridge names its record after the TABLE,
     ``VALUEANAL-REC`` [common/valueMT.cbl:L309]; the copybook names it
     ``WS-Value-Record`` [copybooks/wsval.cob:L9]. The class below carries
     the copybook's name.
  2. THE KEY IS FLATTENED AND RENAMED. At [common/valueMT.cbl:L310] the
     bridge declares a single three-character item, ``pic xxx``, carrying a
     ``WS-`` prefix on the ``Va-Code`` stem - where the copybook declares a
     four-level group of three named fields [copybooks/wsval.cob:L10-L14].
     The bridge sees three bytes; the copybook sees three named fields. That
     flattened spelling is NOT reproduced here and NOT added as an alias; it
     is surfaced from the dictionary instead, by
     ``loader.derivation_for("VALUEANAL-REC.VA-CODE")``, which returns the
     bridge's own move statement and its locator
     [common/valueMT.cbl:L1060] rather than a copy of the name.
  3. CAPITALISATION DIFFERS THROUGHOUT. ``Va-Gl``, ``Va-Desc``, ``Va-Print``,
     ``Va-T-This`` and the rest are mixed case at
     [common/valueMT.cbl:L311-L319]; the copybook writes ``va-gl``,
     ``va-desc``, ``va-print``, ``va-t-this`` in lower case. COBOL folds
     case, so both spellings resolve to one field and the bridge's own load
     paragraph mixes them - it writes the flattened key in one casing at
     [common/valueMT.cbl:L1060] and lower case for the remaining nine at
     [common/valueMT.cbl:L1061-L1069]. This module carries the copybook's
     casing only.
  4. THE LOAD CALL COMMENT NAMES THE BRIDGE'S OWN RECORD. At
     [common/valueMT.cbl:L810] the comment reads "move VALUEANAL-REC fields
     to HV fields", naming the inline record rather than the copybook's.

Two further bridge facts belong in the register. ``valueMT`` itself carries
``copy "Test-Data-Flags.cob".`` [common/valueMT.cbl:L307] with the comment
"set sw-testing to zero to stop logging." - the same copybook
``records/test_data_flags.py`` models, which this module does not import. And
the bridge trims trailing spaces from its three character host variables
before building SQL text, ``STRING FUNCTION TRIM (...,TRAILING)`` at
[common/valueMT.cbl:L1119,L1140,L1149] on write and
[common/valueMT.cbl:L1268,L1289,L1298] on the alternate path. Trailing-space
handling belongs to the harness dump comparison step described in section
0.6.6, not here: THIS MODULE TRIMS NOTHING and pads to the declared width.

THE KEY GROUP COLLAPSES TO ONE COLUMN - AND ALL FOUR CHILDREN STAY
==================================================================
``va-code`` is three bytes carrying four declarations, and the whole group
maps to ONE column, ``VA-CODE char(3)`` [mysql/ACASDB.sql:L1419], which is
also the primary key [mysql/ACASDB.sql:L1429]. So ``va-system``,
``va-group``, ``va-first`` and ``va-second`` have NO column of their own. The
dictionary states that in machine-readable form - each of the four reports
``presence(in_copybook=True, in_bridge=False, in_column=False)`` and
``one_sided`` True - and it records the concatenation itself as
``derivation.kind == GROUP_CONCATENATION`` on ``VALUEANAL-REC.VA-CODE``,
sourced at [common/valueMT.cbl:L1060].

All four are declared below regardless. R-3 forbids removing what the
copybook declares, and the bridge's key metadata reads the group positionally
- keyname ``VA-CODE``, offset 0001, length 0003, ``OCCURS 1``
[common/valueMT.cbl:L237-L247] - so the three bytes are the key however they
are named. This is the same alphanumeric group-concatenation pattern
``records/sales_ledger.py`` meets on ``SALES-ADDRESS`` and
``records/gl_posting.py`` meets numerically on the posting key.

No helper builds the three-byte key from its parts, and no method renders or
orders it. Section 0.6.6 gives that job to the harness dump step, and R-3
forbids adding what the copybook does not declare.

BOTH DIRECTIONS OF THE COMP QUESTION LIVE IN THIS ONE RECORD
============================================================
Getting either direction wrong changes every stored value in the table, so
the rule is stated once, plainly: ``COMP`` implies ``int`` ONLY at scale 0.

    va-system, va-first, va-second   pic x            -> ``str``, width 1
    va-desc                          pic x(24)        -> ``str``, width 24
    va-print                         pic xxx          -> ``str``, width 3
    va-gl                            pic 9(6)         -> ``int``, DISPLAY
    va-t-this, va-t-last, va-t-year  pic 9(5) comp    -> ``int``   NO V
    va-v-this, va-v-last, va-v-year  pic s9(8)v99 c-3 -> ``Decimal``  V
    va-code, va-group                group items      -> no storage of their
                                                        own; nested classes

``pic 9(5) comp`` carries no ``V``, so its scale is 0 and its carrier is
``int`` - and its ``quantum`` is ``Decimal("1")``, not ``None``, because the
scale is an explicit zero rather than an absent one. ``pic s9(8)v99 comp-3``
carries a ``V``, so its scale is 2, its carrier is ``decimal.Decimal`` and its
``quantum`` is ``Decimal("0.01")``. ``records/irs_nominal.py`` carries the
same warning for ``pic 9(8)v99 comp`` and ``records/sales_ledger.py`` for
``pic 99v99 comp``: a scaled ``COMP`` item is a ``Decimal``, and only an
unscaled one is an ``int``.

Every carrier is taken from the dictionary entry's own storage class rather
than read off a picture clause by eye, so this table documents a decision the
generated artifact makes; it does not make it.

THE DECLARED RECORD SIZE - MEASURED, AND NO CONSTANT DECLARED EITHER WAY
=======================================================================
The header claims 66 bytes [copybooks/wsval.cob:L6]. Summing the fields under
the compiler settings the repository actually uses - no dialect flag anywhere,
so binary items size 1-2-4-8 and packed items pack two digits to the byte plus
a sign nibble::

    va-code    3   (va-system 1 + va-group 2, being va-first 1 + va-second 1)
    va-gl      6
    va-desc   24
    va-print   3
              --   36 characters
    va-t-this / -last / -year   4 bytes each   = 12   pic 9(5) comp
    va-v-this / -last / -year   6 bytes each   = 18   pic s9(8)v99 comp-3
                                                 --
                                                 66

Measured against the compiled oracle rather than argued: asking the compiler
for the length of ``WS-Value-Record`` returns 66, and for its parts 3, 1, 2,
1, 1, 6, 24, 3, 4 and 6 respectively. Header and field sum AGREE for this
record - which is NOT so for every record in this folder, where
``records/gl_batch.py`` carries a 96-versus-98 contradiction (anomaly A-15)
and ``records/irs_system.py`` a 256-versus-257 one.

No ``RECORD_LENGTH`` and no ``SIZE`` constant is declared here even so, in
either direction. The general question - whether a header's declared length or
the field sum governs the record actually read - stays open for
``docs/migration/ambiguity-resolutions.md``, because the packed and binary
widths above depend on a compiler setting that no source file and no compile
script pins, so the agreement is a measured property of the current toolchain
rather than a guarantee of the layout.

NEAR-DUPLICATE LAYOUT WITH ``copybooks/wsanal.cob`` - SHARE NOTHING WITH IT
==========================================================================
``copybooks/wsanal.cob``, which ``records/analysis.py`` implements, declares
structurally the same first four fields as this record and then stops::

     01  WS-Analysis-Record.        L9    vs   01  WS-Value-Record.      L9
         03  WS-Pa-Code.            L10   vs       03  va-code.          L10
             05  Pa-System  pic x.  L11   vs           05  va-system     L11
             05  Pa-Group.          L12   vs           05  va-group.     L12
                 07  Pa-First       L13   vs               07 va-first   L13
                 07  Pa-Second      L14   vs               07 va-second  L14
         03  Pa-Gl    pic 9(6).     L15   vs       03  va-gl             L15
         03  Pa-Desc  pic x(24).    L16   vs       03  va-desc           L16
         03  Pa-Print pic xxx.      L17   vs       03  va-print          L17

Four divergence axes: a different field prefix (``Pa-`` against ``va-``),
different capitalisation (``Pa-System`` against ``va-system``), a different
03-group name (prefixed in the analysis record, bare here) and even a
different indentation of the 07 lines (two spaces there, one here). The
analysis record then has NO numeric fields at all, while this one adds six.
Its own header claims 36 bytes [copybooks/wsanal.cob:L6] - the same 36
characters computed above before this record's numeric tail.

This is the class of anomaly A-21: near-identical layouts under divergent
names, which in COBOL forces qualified references. The consequence for this
module is a prohibition, not a convenience. ``records/analysis.py`` is NOT
imported, no base class, mixin, helper or descriptor table is shared with it,
and neither file is a copy-and-rename of the other. Two layouts that diverge
in four ways must be able to keep diverging.

NEVER ``None`` - WHY EVERY DEFAULT IS A REAL VALUE
==================================================
Every column of this table is ``NOT NULL`` [mysql/ACASDB.sql:L1419-L1428], and
section 0.6.2 gives the reason, verbatim: "This is why every column in the
schema can be declared ``NOT NULL`` and why the Python layer must default
rather than omit." The mechanism is visible in the bridge: its load paragraph
opens with ``initialize TD-VALUEANAL-REC.`` [common/valueMT.cbl:L1059] before
moving any field in, and its unload paragraph opens with
``initialize VALUEANAL-REC.`` [common/valueMT.cbl:L1086] before moving any
field out. An unset alphanumeric item is therefore SPACES at its declared
width and an unset numeric item is ZERO - never absent, never null.

So the defaults below are spaces at the declared width, ``0``, and
``Decimal("0.00")``, and ``None`` appears as no field's default. The space
widths and the decimal scale are DERIVED from each field's descriptor rather
than typed in, using the descriptor's own store primitive, so that a width can
never drift from the dictionary that states it.

DESCRIPTOR LOOKUP - LOOKED UP, NEVER TRANSCRIBED
================================================
Section 0.8.1 makes the ordering a directive rather than a preference: "Data
dictionary first. The dictionary is generated from the bridge before record
definitions are written, and every Python field definition cites its entry ...
it is what prevents fields being transcribed by eye." Section 0.3.3 states the
payoff: "Field metadata is therefore derived, not transcribed, which
eliminates an entire class of transcription error across several hundred
fields."

Every one of the FOURTEEN declarations here obtains its storage metadata from
``FieldDescriptor.from_dictionary_key`` - the principal path - and NONE uses
``FieldDescriptor.for_working_storage``. That split, 14 and 0, is a finding
rather than a choice: the generated dictionary covers all four group-only
children of ``va-code`` under its copybook-only key form, so there is no field
here without an entry to cite. ``records/__init__.py`` reserves
``for_working_storage`` for ``work_records.py``, whose layouts belong to no
copybook and to no table.

Keys take the two documented forms, and never a bare field name::

    <TABLE-NAME>.<COLUMN-NAME>       10 fields backed by a column
    <COPYBOOK-RECORD>.<FIELD-NAME>    4 fields the copybook declares alone

The left half is the MySQL TABLE name ``VALUEANAL-REC``, not the copybook
01-name, and the right half is the MySQL COLUMN name - UPPER-CASE where the
copybook is lower-case, and one column where the copybook has a four-field
group. Every key below was obtained by reading
``loader.entries_for_table("VALUEANAL-REC")`` and
``loader.entries_for_copybook_file("copybooks/wsval.cob")`` and matching each
entry's ``copybook.name``; no key is built by case-folding an attribute name,
and nothing below performs such a transformation. What the lookup returned::

    va-code    -> VALUEANAL-REC.VA-CODE        copybooks/wsval.cob:L10
    va-gl      -> VALUEANAL-REC.VA-GL          copybooks/wsval.cob:L15
    va-desc    -> VALUEANAL-REC.VA-DESC        copybooks/wsval.cob:L16
    va-print   -> VALUEANAL-REC.VA-PRINT       copybooks/wsval.cob:L17
    va-t-this  -> VALUEANAL-REC.VA-T-THIS      copybooks/wsval.cob:L18
    va-t-last  -> VALUEANAL-REC.VA-T-LAST      copybooks/wsval.cob:L19
    va-t-year  -> VALUEANAL-REC.VA-T-YEAR      copybooks/wsval.cob:L20
    va-v-this  -> VALUEANAL-REC.VA-V-THIS      copybooks/wsval.cob:L21
    va-v-last  -> VALUEANAL-REC.VA-V-LAST      copybooks/wsval.cob:L22
    va-v-year  -> VALUEANAL-REC.VA-V-YEAR      copybooks/wsval.cob:L23
    va-system  -> WS-Value-Record.va-system    copybooks/wsval.cob:L11
    va-group   -> WS-Value-Record.va-group     copybooks/wsval.cob:L12
    va-first   -> WS-Value-Record.va-first     copybooks/wsval.cob:L13
    va-second  -> WS-Value-Record.va-second    copybooks/wsval.cob:L14

Two guards were run against that lookup and both hold:
``len(loader.entries_for_table("VALUEANAL-REC")) == 10``, and every entry's
``copybook.file`` is ``copybooks/wsval.cob``. Neither an entry citing
``copybooks/wsanal.cob`` nor a ``copybook.name`` beginning ``Pa-`` appears,
which is the check that the near-duplicate analysis record was not picked up
by mistake.

The 01 record itself has an entry too, ``WS-Value-Record.WS-Value-Record``
[copybooks/wsval.cob:L9]. It is not a member field, so no attribute
corresponds to it and none is invented.

Provenance travels on every descriptor: the descriptor type refuses at
construction any instance carrying neither a dictionary key nor a source
locator, so R-5 holds structurally rather than by convention. Two loader
primitives are surfaced and neither is reimplemented -
``loader.cite(key)`` for the compact three-locator provenance string, as in::

    VALUEANAL-REC.VA-V-THIS  copybook=copybooks/wsval.cob:L21
    bridge=common/valueMT.cbl:L294  column=mysql/ACASDB.sql:L1426

and ``loader.drift_for(key)``, reached through the descriptor, for the
unsettled three-layer disagreement.

LAYERING - THIS IS A LEAF MODULE (SECTION 0.4.3)
================================================
    MAY import       ``acas_posting.cobol.field``,
                     ``acas_posting.dictionary.loader``, and the standard
                     library
    MUST NOT import  anything else - "this keeps the record layer a leaf"

Forbidden by name, because each is a live temptation for THIS module in
particular: ``dal`` and above all ``dal/acas013_value.py``, which owns the
bridge conversion this record's money fields undergo; every other module of
this package, and above all ``records/analysis.py`` with its near-duplicate
layout and ``records/test_data_flags.py``, which the bridge happens to copy;
``programs``, ``cli``, ``clock``, ``dates``, ``workfiles``; the sibling
modules of ``cobol`` - arithmetic, move, picture, usage, condition_names,
sortverb; ``dictionary.generate``; and the compiled comparison oracle in its
sibling tree. Nothing is shared with any of them.

Section 0.4.3 states what the restriction buys: "the arithmetic suite imports
only ``cobol`` and ``records`` and touches no database, so it runs anywhere". A
single import reaching into ``dal`` would pull a database driver into that
tier.

THE SIX BINDING RULES, AS THEY APPLY HERE
=========================================
The rule identifiers are the Agent Action Plan's own, section 0.7.2. This
project carries NO separate rules document - ``review_rules`` reports that
none was provided, checked twice - so the plan is where their full text lives.

    R-1  No COBOL at runtime. Nothing below starts a process, loads a shared
         library through a foreign-function interface, or names a COBOL tool
         or a database driver. The imports are the standard library and two
         modules of this package. The shipped artifact runs on a host with no
         COBOL compiler and no COBOL runtime present.
    R-2  Zero binary floating-point. The three money totals are
         ``decimal.Decimal`` at scale 2; the three counters and the general
         ledger account number are ``int``; the five character items are
         ``str``. No binary floating-point type is named or constructed
         anywhere below, and no binary floating-point literal appears.
    R-3  Nothing added. Exactly the fourteen declarations the copybook makes,
         in its order. No validation, no range check on the account number, no
         key-building helper, no rendering or ordering method, no post-init
         hook, no predicate, no enumeration, no length constant, no alias for
         the bridge's flattened key. No object-relational mapper, no
         declarative metadata, no schema emission. No concurrency primitive of
         any kind: execution is strictly sequential.
    R-4  Anomalies reproduced, never fixed. Every finding above is recorded
         with its locators and left standing, and each reproduction site below
         carries a comment citing its COBOL locator, as section 0.7.4 C-4
         prescribes. There is deliberately no settled, single-winner or
         tidied-up view, type, value or picture anywhere in this file: where
         the layers disagree, all three views stand and the drift object stays
         unsettled.
    R-5  Full traceability. Every field cites its dictionary entry; the
         program-to-module, paragraph-to-function and field-to-entry tables
         live in ``docs/migration/traceability.md`` and can lift the lookup
         table, the three-layer table and the locators above verbatim.
    R-6  Compiled behaviour is the tie-breaker, and runs are deterministic.
         Field order follows copybook declaration order; every exposed
         collection is a tuple; no clock, no entropy source, no environment
         read and no directory scan appears below.

TWO OPEN QUESTIONS FOR ``docs/migration/ambiguity-resolutions.md``
==================================================================
Neither can be settled by reading the source, so neither is settled here.

  1. WHAT IS STORED WHEN A NEGATIVE MONEY TOTAL PASSES THROUGH AN UNSIGNED
     ``COMP`` HOST VARIABLE INTO AN UNSIGNED ``decimal(10,2)`` COLUMN. This is
     section 0.6.8's existing question - "A negative binary value through an
     unsigned host variable into an unsigned column. Section 0.6.2 establishes
     that the sign is lost; what the resulting stored value IS depends on the
     conversion the bridge's C interface performs, which must be measured
     rather than assumed" - and it is sharper here than in the case that
     question was written for, because the receiving column is a DECIMAL
     column rather than an integer one. The dictionary tags all three money
     entries ``Q-3`` for exactly this. Nothing below assumes an answer: no
     absolute value, no modulus and no wrap-around is applied.
  2. WHETHER A HEADER'S DECLARED LENGTH OR THE FIELD SUM GOVERNS THE RECORD
     ACTUALLY READ. Both are 66 for this record, as measured above, so the
     question has no observable consequence HERE - but the widths that make
     them agree rest on a compiler setting nothing in the repository pins, and
     the two figures do NOT agree in ``records/gl_batch.py`` or
     ``records/irs_system.py``. Recorded rather than settled silently.

WHAT THIS MODULE DOES NOT DO
============================
It holds values; it does not compute with them. No arithmetic, no MOVE
semantics, no picture parsing, no sort, no SQL, no cursor, no report
formatting and no screen handling appears below - those belong to
``acas_posting.cobol``, to ``acas_posting.dal`` and to the program modules,
and the presentation layer is dropped rather than reimplemented. It performs
no import-time work beyond building its descriptors, which reads the generated
dictionary through the loader's own lazily cached read - the pattern
``records/__init__.py`` documents for this package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

# The dictionary loader is reached THROUGH the descriptor rather than imported
# here, deliberately. `FieldDescriptor.from_dictionary_key` performs the
# lookup, `FieldDescriptor.cite` is a pass-through of `loader.cite` and
# `FieldDescriptor.drift` is a pass-through of `loader.drift_for`, so both
# loader primitives are surfaced by every descriptor below without being
# reimplemented and without a second import that nothing in this file would
# call. Section 0.4.3 PERMITS `acas_posting.dictionary.loader` to a record
# module; it does not oblige one, and an import no statement uses would be
# dead weight in a leaf layer.

__all__ = ["VaCode", "VaGroup", "WsValueRecord"]


# ---------------------------------------------------------------------------
#  Field descriptors, one per COBOL declaration, LOOKED UP - NEVER TRANSCRIBED
#
#  Each key was obtained by reading the generated dictionary and matching on
#  the entry's `copybook.name`; see the DESCRIPTOR LOOKUP section of the module
#  docstring for the full fourteen-row table and the two guards that were run
#  against it. Ten keys take the `<TABLE-NAME>.<COLUMN-NAME>` form and four
#  take the `<COPYBOOK-RECORD>.<FIELD-NAME>` form, the latter for the group
#  children that back no column of their own. No key is built by case-folding
#  an attribute name.
#
#  Every descriptor reports the COPYBOOK view of its field. Digits, scale,
#  signedness, sign position, usage and character length all come from the
#  dictionary; none is typed in here.
# ---------------------------------------------------------------------------

# va-code  a group of three characters, level 03  [copybooks/wsval.cob:L10]
# ANOMALY, group concatenation: this ONE key covers FOUR copybook declarations,
# because the whole group is a single `char(3)` column [mysql/ACASDB.sql:L1419]
# which is also the primary key [mysql/ACASDB.sql:L1429]. The bridge performs
# the concatenation with one move [common/valueMT.cbl:L1060]; the dictionary
# records it as a GROUP_CONCATENATION derivation on this key. All four
# declarations are still modelled below - R-3 forbids dropping any of them.
_VA_CODE: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-CODE")

# va-system  pic x, level 05  [copybooks/wsval.cob:L11]
# Copybook-only: no host variable and no column of its own, which the
# dictionary states as presence(in_copybook=True, in_bridge=False,
# in_column=False). Keyed under the copybook record for that reason.
_VA_SYSTEM: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-system")

# va-group  a group of two characters, level 05  [copybooks/wsval.cob:L12]
# Copybook-only, and the reason the nesting below is four levels deep.
_VA_GROUP: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-group")

# va-first  pic x, level 07  [copybooks/wsval.cob:L13]
# ANOMALY, level numbering: the level jumps 05 -> 07 with no 06 anywhere in the
# copybook, and this line indents its picture with ONE space after the level
# number where every other level line in the file uses two. Both spellings are
# recorded and neither is tidied.
_VA_FIRST: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-first")

# va-second  pic x, level 07  [copybooks/wsval.cob:L14]
# Same level jump and same one-space indentation as va-first.
_VA_SECOND: Final = FieldDescriptor.from_dictionary_key("WS-Value-Record.va-second")

# va-gl  pic 9(6), zoned DISPLAY, level 03  [copybooks/wsval.cob:L15]
# The general ledger account this analysis code posts to. DRIFT, registered and
# left standing: DISPLAY at the copybook against COMP at the bridge
# [common/valueMT.cbl:L288] and MEDIUMINT at the column
# [mysql/ACASDB.sql:L1420], and 6 digits against 8 at the bridge. The
# descriptor reports the copybook's DISPLAY and its 6 digits.
_VA_GL: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-GL")

# va-desc  pic x(24), level 03  [copybooks/wsval.cob:L16]
_VA_DESC: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-DESC")

# va-print  pic xxx, level 03  [copybooks/wsval.cob:L17]
# ANOMALY, picture spelling: the copybook spells this `pic xxx` rather than
# `pic x(3)`. The descriptor carries the picture text exactly as written.
_VA_PRINT: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-PRINT")

# va-t-this  pic 9(5) comp, level 03  [copybooks/wsval.cob:L18]
# UNSIGNED in the copybook, so unsigned at all three layers: the drift here is
# digit widening ALONE, 5 digits against 8 at the bridge
# [common/valueMT.cbl:L291] and a 5-digit column [mysql/ACASDB.sql:L1423]. No
# `V` in the picture, so the scale is zero and the carrier is `int` - contrast
# the three money fields below, which are scaled and therefore `Decimal`.
_VA_T_THIS: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-T-THIS")

# va-t-last  pic 9(5) comp, level 03  [copybooks/wsval.cob:L19]
_VA_T_LAST: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-T-LAST")

# va-t-year  pic 9(5) comp, level 03  [copybooks/wsval.cob:L20]
_VA_T_YEAR: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-T-YEAR")

# va-v-this  pic s9(8)v99 comp-3, level 03  [copybooks/wsval.cob:L21]
# NEW ANOMALY - MONEY LOSES ITS SIGN AT THE BRIDGE. SIGNED here, against
# `PIC 9(08)V9(02) COMP` at the bridge [common/valueMT.cbl:L294] and a column
# declared without a sign [mysql/ACASDB.sql:L1426]. This QUALIFIES section
# 0.6.2's statement that monetary fields "pass through cleanly" - true of the
# sales and purchase ledgers, false of this record. The descriptor keeps the
# copybook's SIGNED view; the bridge conversion belongs to
# `dal/acas013_value.py`. The dictionary tags the entry A-11 and Q-3.
_VA_V_THIS: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-V-THIS")

# va-v-last  pic s9(8)v99 comp-3, level 03  [copybooks/wsval.cob:L22]
# Same sign loss at the bridge [common/valueMT.cbl:L295] and the same column
# treatment [mysql/ACASDB.sql:L1427].
_VA_V_LAST: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-V-LAST")

# va-v-year  pic s9(8)v99 comp-3, level 03  [copybooks/wsval.cob:L23]
# Same sign loss at the bridge [common/valueMT.cbl:L296] and the same column
# treatment [mysql/ACASDB.sql:L1428].
_VA_V_YEAR: Final = FieldDescriptor.from_dictionary_key("VALUEANAL-REC.VA-V-YEAR")


# ---------------------------------------------------------------------------
#  Initial content of each alphanumeric item
#
#  The bridge opens both of its transfer paragraphs by initialising the record
#  group - `initialize TD-VALUEANAL-REC.` [common/valueMT.cbl:L1059] on the way
#  in and `initialize VALUEANAL-REC.` [common/valueMT.cbl:L1086] on the way out
#  - so an unset alphanumeric item holds SPACES at its declared width, never a
#  null. Section 0.6.2: "the Python layer must default rather than omit".
#
#  The width is DERIVED from each descriptor's own store primitive rather than
#  typed in, so it can never drift from the dictionary that states it. The
#  `str()` call narrows that primitive's `Decimal | int | str` return for an
#  alphanumeric field; it converts nothing, since the value already is a `str`.
# ---------------------------------------------------------------------------

_INITIAL_VA_SYSTEM: Final[str] = str(_VA_SYSTEM.store(""))
_INITIAL_VA_FIRST: Final[str] = str(_VA_FIRST.store(""))
_INITIAL_VA_SECOND: Final[str] = str(_VA_SECOND.store(""))
_INITIAL_VA_DESC: Final[str] = str(_VA_DESC.store(""))
_INITIAL_VA_PRINT: Final[str] = str(_VA_PRINT.store(""))


# ---------------------------------------------------------------------------
#  The record
#
#  ATTRIBUTE order inside each class is the copybook's declaration order, L10
#  through L23, which is what rule R-6 pins and what lets a reader diff a class
#  against its copybook line by line. CLASS definition order is innermost
#  first - VaGroup, then VaCode, then WsValueRecord - because Python evaluates
#  a nested group's factory while the enclosing class body runs. The two orders
#  are independent and neither is a reordering of the copybook.
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class VaGroup:
    """``05  va-group.`` [copybooks/wsval.cob:L12] - two characters.

    The inner group of the analysis key, holding ``va-first`` and
    ``va-second``. Its two children are declared at level 07 with no level 06
    between them [copybooks/wsval.cob:L13-L14]; that jump is the copybook's and
    is reproduced by nesting this class inside :class:`VaCode`.

    Neither this group nor either child backs a column of its own: the
    enclosing ``va-code`` group is one ``char(3)`` column
    [mysql/ACASDB.sql:L1419]. All three are modelled regardless, because R-3
    forbids removing what the copybook declares.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VA_FIRST, _VA_SECOND)

    # va-first  07 va-first    pic x.  [copybooks/wsval.cob:L13]
    # The one-space indentation after the level number is the copybook's.
    va_first: str = _INITIAL_VA_FIRST

    # va-second  07 va-second   pic x.  [copybooks/wsval.cob:L14]
    va_second: str = _INITIAL_VA_SECOND


@dataclass(slots=True)
class VaCode:
    """``03  va-code.`` [copybooks/wsval.cob:L10] - three characters.

    The analysis key, and the primary key of ``VALUEANAL-REC``
    [mysql/ACASDB.sql:L1429]. Four copybook declarations - this group,
    ``va-system``, the nested ``va-group`` and its two children - collapse into
    the single column ``VA-CODE char(3)`` [mysql/ACASDB.sql:L1419], which the
    bridge fills with one move [common/valueMT.cbl:L1060]. The bridge's own
    inline record flattens the group to a single three-character item under a
    prefixed name [common/valueMT.cbl:L310]; that flattening is registered in
    the module docstring and is neither reproduced nor aliased here.

    No method assembles the three characters into a key, renders them or
    orders by them. Section 0.6.6 gives ordering to the harness dump step,
    which reads ``ORDER BY`` the primary key straight from the schema.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VA_SYSTEM, _VA_GROUP)

    # va-system  05  va-system      pic x.  [copybooks/wsval.cob:L11]
    va_system: str = _INITIAL_VA_SYSTEM

    # va-group  05  va-group.  [copybooks/wsval.cob:L12]
    va_group: VaGroup = field(default_factory=VaGroup)


@dataclass(slots=True)
class WsValueRecord:
    """The value-analysis record, ``WS-Value-Record`` [copybooks/wsval.cob:L9].

    The copybook declares it ``01  WS-Value-Record.`` - that level number,
    that casing, that doubled space and that terminating period - at
    [copybooks/wsval.cob:L9]. The bridge names its own inline record after the
    table instead, ``VALUEANAL-REC`` [common/valueMT.cbl:L309], and does not
    ``COPY`` this copybook at all. This class carries the copybook's name
    because the copybook is what the posting programs ``COPY``.

    Its place on the entity spine, from section 0.2.1.1 and confirmed by
    ``loader.find_table("VALUEANAL-REC")``::

        entity facade  Value
        handler        acas013
        bridge         valueMT
        table          VALUEANAL-REC   10 columns, primary key VA-CODE
        copybook       copybooks/wsval.cob

    The ten members below are the copybook's ten ``03``-level declarations in
    its order, L10 through L23, and they correspond one-for-one with the ten
    columns - ``va_code`` standing for the whole concatenated key. The four
    subordinate declarations of that key live on :class:`VaCode` and
    :class:`VaGroup`, giving fourteen declarations in total.

    NOT frozen, deliberately: the Sales and Purchase extract steps ``sl055``
    and ``pl055`` accumulate their analysis totals into this record in place.

    Three of its fields carry a legacy defect that must NOT be repaired here.
    ``va_v_this``, ``va_v_last`` and ``va_v_year`` are declared SIGNED
    [copybooks/wsval.cob:L21-L23] and lose that sign at the bridge
    [common/valueMT.cbl:L294-L296] before any SQL runs
    [mysql/ACASDB.sql:L1426-L1428]. The descriptors keep the signed copybook
    view and a negative total stays negative in this record; reproducing the
    bridge's conversion is ``dal/acas013_value.py``'s job. See the module
    docstring for the full nine-locator register and the open question it
    raises.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _VA_CODE,
        _VA_GL,
        _VA_DESC,
        _VA_PRINT,
        _VA_T_THIS,
        _VA_T_LAST,
        _VA_T_YEAR,
        _VA_V_THIS,
        _VA_V_LAST,
        _VA_V_YEAR,
    )

    # va-code  03  va-code.  [copybooks/wsval.cob:L10]
    # Three characters across four declarations, one column.
    va_code: VaCode = field(default_factory=VaCode)

    # va-gl  03  va-gl              pic 9(6).  [copybooks/wsval.cob:L15]
    # Zoned DISPLAY, unsigned, six digits, scale 0 -> `int`.
    va_gl: int = 0

    # va-desc  03  va-desc            pic x(24).  [copybooks/wsval.cob:L16]
    va_desc: str = _INITIAL_VA_DESC

    # va-print  03  va-print           pic xxx.  [copybooks/wsval.cob:L17]
    # The `pic xxx` spelling is the copybook's, kept as written.
    va_print: str = _INITIAL_VA_PRINT

    # va-t-this  03  va-t-this          pic 9(5)         comp.
    #                                            [copybooks/wsval.cob:L18]
    # COMP with NO `V`: scale 0, unsigned, five digits -> `int`.
    va_t_this: int = 0

    # va-t-last  03  va-t-last          pic 9(5)         comp.
    #                                            [copybooks/wsval.cob:L19]
    va_t_last: int = 0

    # va-t-year  03  va-t-year          pic 9(5)         comp.
    #                                            [copybooks/wsval.cob:L20]
    va_t_year: int = 0

    # va-v-this  03  va-v-this          pic s9(8)v99     comp-3.
    #                                            [copybooks/wsval.cob:L21]
    # SIGNED packed decimal, ten digits, scale 2 -> `Decimal`. The sign is lost
    # at the bridge [common/valueMT.cbl:L294]; it is NOT lost here.
    va_v_this: Decimal = Decimal("0.00")

    # va-v-last  03  va-v-last          pic s9(8)v99     comp-3.
    #                                            [copybooks/wsval.cob:L22]
    # Sign lost at the bridge [common/valueMT.cbl:L295]; kept here.
    va_v_last: Decimal = Decimal("0.00")

    # va-v-year  03  va-v-year          pic s9(8)v99     comp-3.
    #                                            [copybooks/wsval.cob:L23]
    # Sign lost at the bridge [common/valueMT.cbl:L296]; kept here.
    va_v_year: Decimal = Decimal("0.00")
