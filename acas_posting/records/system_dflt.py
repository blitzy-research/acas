"""The General Ledger / system defaults record, `SYSDEFLT-REC`.

A CREATE from `copybooks/wsdflt.cob`, which is twenty lines long and declares
one record: a table of thirty-three three-field entries followed by a filler
that pads the whole thing to 1024 bytes. Two plain dataclasses mirror it field
for field and add nothing. No account code is interpreted here, no VAT code is
read, no default is selected for a caller and no figure is computed: this
module says what the record IS, and nothing about what it MEANS.

WHERE THIS RECORD SITS IN THE SYSTEM
====================================
The entity-to-table spine of the Agent Action Plan, section 0.2.1.1, gives the
whole chain in one row, and every link was checked against the frozen source
rather than taken on trust::

    entity facade   System defaults
    handler         acas000, FILE KEY NUMBER 2
    bridge          dfltMT
    MySQL table     SYSDEFLT-REC, four columns, primary key DEF-REC-KEY
    copybook        copybooks/wsdflt.cob

`acas000` is not a single-table handler. Section 0.2.1.1 calls it "a four-way
dispatcher keyed by file-key number rather than a single-table handler": key 1
reaches `SYSTEM-REC` through `systemMT`, key 2 reaches this record through
`dfltMT`, key 3 reaches `SYSFINAL-REC` through `finalMT` and key 4 reaches
`SYSTOT-REC` through `sys4MT`. This record is key 2 of that dispatch, and the
dispatch itself belongs to `acas_posting/dal/acas000_system.py`, not here.

Per section 0.6.6 the table carries a single-column primary key, no secondary
index, no TIMESTAMP column, no AUTO_INCREMENT column and no column-level
default, so a state dump of it is `SELECT * ... ORDER BY DEF-REC-KEY` with no
tie-breaking logic at all.

THE RECORD, VERBATIM FROM THE FROZEN COPYBOOK
=============================================
::

     01  Default-Record.                              [:L14]
         03  Def-Group                  occurs 33.    [:L15]
             05  Def-Acs         pic 9(4)v99 comp.    [:L16]
             05  Def-Codes       pic xx.              [:L17]
             05  Def-Vat         pic x.               [:L18]
         03  filler              pic x(793).          [:L19]

Six items, and all six are looked up in the generated data dictionary below -
the three leaf fields, the two group items and the filler. Nothing in this
module writes a picture clause, a digit count, a scale, a width or a storage
class by hand.

THE 1024 BYTES, AND WHY THE COUNT IS 33 AND NOT A ROUNDER NUMBER
================================================================
The size arithmetic, every term of it taken from the dictionary rather than
asserted (`FieldDescriptor.byte_length` on each leaf field)::

    Def-Acs    pic 9(4)v99 comp    6 digits binary   ->   4 bytes
    Def-Codes  pic xx                                ->   2 bytes
    Def-Vat    pic x                                 ->   1 byte
                                            one entry  =  7 bytes

    33 entries  x  7 bytes  =  231 bytes
    231 bytes   +  793 filler bytes  =  1024 bytes

1024 is the size the copybook's own trailing comment states, "total 1024"
[copybooks/wsdflt.cob:L19], and the header explains where the number comes
from: the record is "written as 1024 (system-record size)"
[copybooks/wsdflt.cob:L6], so it matches `System-Record` on disk, and the
filler was "included filler 15/10/25 now = 1024 as created by sys002"
[copybooks/wsdflt.cob:L12].

The entry count has a history the header records in full, and it is worth
reading in the order it happened rather than as a single step:

    thirty-three, 231 bytes   the original shape, implied by L9 and L10
    thirty-two,   224 bytes   "05/11/16 vbc - Changed to 32 (from 33).
                               Record size 224 bytes from 231."
                                              [copybooks/wsdflt.cob:L8-L9]
    thirty-three, 231 bytes   "Brought back to 33 and 231 bytes for posting
                               program to match up with IRS change 01/05/18
                               in irs030."    [copybooks/wsdflt.cob:L10-L11]

So the count is thirty-three because a posting program needed a thirty-third
entry, and the IRS side of the house needed it first. The IRS defaults
copybook carries the matching note, "Rec 264 bytes 06/05/18 - to support temp.
default 33 in postings (irs030)." [copybooks/irswsdflt.cob:L7]. Section
0.4.1.3 records that the IRS defaults record holds "the account-code table the
posting section indexes at 31 and 32", so particular subscripts near the end
of the table carry meaning to callers. All thirty-three entries are therefore
kept, in index order, with no truncation, no reordering and no compaction of
empty entries.

TWO COPYBOOKS DECLARE `Default-Record`, AND THEY ARE NOT THE SAME RECORD
=======================================================================
This is why the class below is `SysDefaultRecord` and not the bare
`DefaultRecord` its COBOL `01`-name would suggest. Set the two declarations
side by side::

    copybooks/wsdflt.cob                    copybooks/irswsdflt.cob
    ---------------------------------       ---------------------------------
    01  Default-Record.          [:L14]     01  Default-Record.        [:L8]
      03 Def-Group  occurs 33.   [:L15]       03 Def-Group occurs 33.  [:L9]
        05 Def-Acs   pic 9(4)v99            05 Def-Acs   pic 9(5).    [:L10]
                       comp.     [:L16]
        05 Def-Codes pic xx.     [:L17]       05 Def-Codes pic xx.    [:L11]
        05 Def-Vat   pic x.      [:L18]       05 Def-Vat   pic x.     [:L12]
      03 filler pic x(793).      [:L19]       (no filler)

Same `01`-name. Same group name. Same `occurs` count. Same two character
fields. And a `Def-Acs` that differs in all three of the things that decide
how a value is stored and computed on:

    here    `pic 9(4)v99 comp`   six digits, SCALE 2, binary, unsigned
    there   `pic 9(5)`           five digits, SCALE 0, zoned display, unsigned

The maintainer flagged it himself, in this copybook's own header: "This is NOT
the same as for IRS as DEF-ACAS is different size"
[copybooks/wsdflt.cob:L7]. It is recorded here and it is NOT harmonised. The
IRS variant is modelled separately in `acas_posting/records/irs_dflt.py`, this
module never imports that one, and neither is aliased to, derived from or
reconciled against the other. Merging them would silently give one subsystem
the other's scale, which under rule R-4 is a failure rather than a tidy-up.

This is the record layer's instance of the anomaly the register numbers 21 -
field-name collisions across posting copybooks that force COBOL into qualified
references, as `[general/gl070.cbl:L510]` shows. Python's module namespace
separates the two for free; the collision is written down anyway, because a
reader who does not know it exists cannot understand why the COBOL qualifies.

WHY THE FOUR-COLUMN TABLE DOES NOT CONTRADICT THE THIRTY-THREE-ENTRY RECORD
===========================================================================
`SYSDEFLT-REC` has four columns while this copybook declares a table of
thirty-three three-field entries. That is not a discrepancy to settle - it is
the bridge's own flattening, and the bridge states it in a comment::

    move  HV-DEF-ACS   to Def-Acs (HV-DEF-REC-KEY)  *> KEY = table position
                                              [common/dfltMT.cbl:L579]
    move  A            to HV-DEF-REC-KEY      [common/dfltMT.cbl:L612]

`DEF-REC-KEY` carries the OCCURS SUBSCRIPT. One table entry becomes one SQL
row, so the table's four columns are the subscript plus the entry's three
fields, and the record's thirty-three entries become up to thirty-three rows.
What the dictionary holds for the four columns, checked by lookup:

    DEF-REC-KEY  ordinal 1, primary key  <- NO copybook field at all
    DEF-ACS      ordinal 2               <- Def-Acs    [:L16]
    DEF-CODES    ordinal 3               <- Def-Codes  [:L17]
    DEF-VAT      ordinal 4               <- Def-Vat    [:L18]

Three of the four columns have a copybook counterpart and this module carries
exactly those three, plus the two group items and the filler that reach no
column. `DEF-REC-KEY` has none: its dictionary entry has a null copybook view
and a `derivation` of `move A to HV-DEF-REC-KEY`, so it is declared by the
bridge host-variable group and the frozen schema only.

No attribute is invented for it. Asking `cobol.field` for a descriptor for it
raises `BridgeOnlyFieldError`, deliberately, because a field no COBOL program
can name has no COBOL-side storage to describe. Supplying its value is the
handler's job, in `acas_posting/dal/acas000_system.py` - exactly as the three
date components of the internal IRS posting table, which likewise appear in no
copybook, belong to `acas_posting/dal/acasirsub4_irs_posting.py`.

`dfltMT` HAS NO HOST-VARIABLE LOAD PARAGRAPH
============================================
Worth knowing before reading this record's dictionary entries, because they
look different from most. Sixteen of the twenty in-scope bridges load their
host-variable group in a dedicated `bb000-HV-Load` paragraph. Four do not, and
`dfltMT` is one of them: it moves record fields into host variables inline,
in the middle of its write path [common/dfltMT.cbl:L606-L614], and back out
inline in its read path [common/dfltMT.cbl:L579-L581]. So each entry's
`load_source` points at an inline move rather than at a named paragraph, and
each carries the dictionary's own note:

    "dfltMT issues no INITIALIZE of TD-SYSDEFLT-REC before loading it, unlike
    the bridges that use a dedicated bb000-HV-Load section."

Nothing is done about that here and nothing compensates for it. It is
recorded so that a reader of the dictionary is not surprised, and so that the
handler module knows the group is not pre-initialised for it.

WHAT THIS MODULE DELIBERATELY LEAVES TO OTHER LAYERS
====================================================
Three behaviours of the frozen source touch this record and belong elsewhere.
They are named here so nobody looks for them in this file and concludes they
were lost:

  * THE BRIDGE ONLY EVER MOVES THIRTY-TWO OF THE THIRTY-THREE ENTRIES.
    `dfltMT` walks the table with `varying A from 1 by 1 until A > 32`
    [common/dfltMT.cbl:L531-L532] on the way in and again
    [common/dfltMT.cbl:L599] on the way out, and rejects a fetched row whose
    key is "zero or > 32" [common/dfltMT.cbl:L559]. The loop bound was left at
    thirty-two when the copybook went back to thirty-three, so entry 33 - the
    one L10-L11 says was restored for `irs030` - never reaches the database
    and never comes back from it. Under R-4 that is part of the
    specification. This record still carries all thirty-three entries, exactly
    as the copybook declares them; reproducing the bridge's bound is
    `acas_posting/dal/acas000_system.py`'s work, at the bridge boundary.
  * AN ENTRY THAT IS ZERO AND BLANK IS SKIPPED RATHER THAN WRITTEN.
    `dfltMT` cycles past any entry whose amount is zero and whose two
    character fields are blank [common/dfltMT.cbl:L600-L604], so an untouched
    entry produces no row. Again the handler's business, not the record's.
  * A NON-NUMERIC AMOUNT IS WRITTEN AS ZERO. The bridge guards its move with
    `if Def-Acs (A) numeric` and substitutes zeros when the guard fails
    [common/dfltMT.cbl:L606-L610]; the dictionary carries that as the entry's
    `derivation` guard. Storage semantics belong to
    `acas_posting/cobol/move.py` and `acas_posting/cobol/arithmetic.py`.

THE FILLER IS MODELLED AS A NAMED ATTRIBUTE, AND HERE IS WHY
============================================================
`03 filler pic x(793)` [copybooks/wsdflt.cob:L19] gets a real attribute on
`SysDefaultRecord`, and its descriptor - looked up like every other - carries
`is_filler=True`. The choice was between that and a descriptor with no
attribute at all, and three facts from the frozen source decided it:

1. The bridge names the filler explicitly. `initialize Default-Record with
   filler.` [common/dfltMT.cbl:L530] uses the WITH FILLER phrase, whose only
   purpose is to reach filler items, so the 793 bytes are storage the frozen
   code touches rather than a gap in the layout.
2. `sys002` writes the record at its full 1024 bytes
   [copybooks/wsdflt.cob:L12], and a record object that cannot carry those
   bytes is not this record.
3. Declaration order L15 -> L19 is the byte layout. Dropping the trailing
   item would leave the record's own width underivable from the module.

The `is_filler=True` on the descriptor is what records the other half of the
truth: COBOL FILLER names no value, so no COBOL program can read or write
these bytes, and the dictionary's note for the entry says as much - "a FILLER,
which names no value and reaches no column". The attribute exists to carry the
padding, not to be read as a figure, and it reaches no column in any table
dump.

DEFAULTS: SPACES AND ZERO, WHICH IS WHAT THE FROZEN CODE DOES
=============================================================
One convention, applied to every character field in the module: a character
field defaults to its declared width filled with SPACES - never to the empty
string - and the amount field defaults to zero at its declared scale. The
width and the scale are both taken from the dictionary rather than typed in.

This is not a house preference; it is what the bridge does to this very
record. `initialize Default-Record with filler.` [common/dfltMT.cbl:L530]
runs immediately before the read loop, and COBOL INITIALIZE sets numeric
items to zero and alphanumeric items - filler included, by the WITH FILLER
phrase - to spaces. A fresh `SysDefaultRecord` therefore holds what a fresh
`Default-Record` holds inside the compiled bridge, which is also precisely
the state the bridge reads as "an empty occurs" when it decides whether to
write a row [common/dfltMT.cbl:L600-L604]. An empty-string default would
break that correspondence silently.

Padding and truncation on assignment are NOT performed here. Those are MOVE
semantics and they live in `acas_posting/cobol/move.py`; a store into a
numeric item lives in `acas_posting/cobol/arithmetic.py`. This module holds
no construction-time coercion of any kind, so a value written to an attribute
is the value read back.

TYPES (R-2)
===========
    Def-Acs    `pic 9(4)v99 comp`  ->  `decimal.Decimal`, scale 2, unsigned,
                                       six digits, four of them integral
    Def-Codes  `pic xx`            ->  `str`, two characters
    Def-Vat    `pic x`             ->  `str`, one character
    filler     `pic x(793)`        ->  `str`, 793 characters

`Def-Acs` is the one that has to be got right. It is `COMP` - a binary item -
which invites `int`, and it is money, which invites the wrong thing entirely.
It has a SCALE OF 2, so its carrier is `Decimal` and the dictionary says so
independently: `cobol_python_storage` is `DECIMAL`, `scale` is 2 and `quantum`
is `Decimal("0.01")`. Not `int`, because an integer carrier would discard the
pence. Never a binary floating-point carrier, in computation, in storage or in
transport - the name of that builtin appears nowhere in this file at all.

Note also that its usage is declared ON THE FIELD, not inherited from
`Def-Group`, so its descriptor reports `usage_declared_at` as `FIELD`. This
record has no group-usage inheritance anywhere in it.

TRACEABILITY (R-5) - LOOKED UP, NEVER TRANSCRIBED
=================================================
Section 0.8.1 makes the ordering a directive rather than a preference: "The
dictionary is generated from the bridge before record definitions are written,
and every Python field definition cites its entry ... it is what prevents
fields being transcribed by eye." Section 0.3.3 gives the reason: field
metadata is "derived, not transcribed, which eliminates an entire class of
transcription error across several hundred fields".

Every descriptor below therefore comes from `FieldDescriptor
.from_dictionary_key`, and its key is obtained by asking the loader rather
than by being written out from memory. Two accessors are used, in this order:

    loader.entries_for_table("SYSDEFLT-REC")
        The column-mapped entries, in the column ordinal order of the frozen
        schema dump. Each entry's `copybook.name` is read to learn which
        COBOL field the column backs. This is the path that matters for the
        collision above: the LEFT half of an entry key is the MySQL TABLE
        name, not the copybook `01`-name, and it is the table name that keeps
        `SYSDEFLT-REC` and `IRSDFLT-REC` apart. The RIGHT half is the MySQL
        COLUMN name, which drifts from the COBOL field name elsewhere in this
        system - `Post-Date` reaches `POST4-DAT`, `Vat-AC-Def` reaches
        `VAT-AC-DEF4`, `Post-Key` reaches `KEY-4` - so it cannot be guessed
        from a field name either.

    loader.entries_for_copybook_file("copybooks/wsdflt.cob")
        The remaining three items, which reach no column and so appear in no
        table result: the `01` group, the `03` group that carries the OCCURS,
        and the filler.

The second accessor is the FILE-keyed one on purpose, and the reason is
measured rather than theoretical. `loader.entries_for_copybook_record
("Default-Record")` returns ELEVEN entries here, not six: five of them come
from `copybooks/irswsdflt.cob`. The loader documents that trap itself, naming
`Default-Record` among the record names that more than one copybook declares
and directing callers to the file-keyed accessor to separate them. Keying by
file makes this module structurally incapable of picking up an IRS field, and
a check on every entry's `copybook.file` states the same thing again in code.

`loader.cite(key)` is the compact three-locator provenance string for any
field, and it is surfaced rather than reimplemented: call `.cite()` on any
descriptor in a `FIELDS` tuple and it delegates there. For `Def-Acs` it
returns

    SYSDEFLT-REC.DEF-ACS  copybook=copybooks/wsdflt.cob:L16
    bridge=common/dfltMT.cbl:L317  column=mysql/ACASDB.sql:L1140

Where the three layer views of a field disagree, `.drift()` hands back the
disagreement untouched. Nothing in this module settles such a disagreement,
scores one view above another or blends layers into a single figure; under
R-4 registering a discrepancy is the requirement and choosing a winner is the
failure. For this record the dictionary reports no drift on any of the three
leaf fields - copybook, host variable and column agree on every one - which
is a fact worth having rather than an absence worth ignoring.

The full program-to-module, paragraph-to-function and field-to-entry mapping
is recorded in `docs/migration/traceability.md`, and the register of
reproduced legacy defects in `docs/migration/anomaly-log.md`.

LAYERING (section 0.4.3) - THIS IS A LEAF
=========================================
The record layer may import `acas_posting.cobol.field` and
`acas_posting.dictionary.loader` and nothing else, "this keeps the record
layer a leaf". Forbidden, and absent below: every `dal` module, `programs`,
`cli`, the clock, the date module, the work files, `cobol.arithmetic`,
`cobol.move`, `cobol.picture`, `cobol.usage`, `cobol.condition_names`,
`cobol.sortverb`, `dictionary.generate`, the compiled comparison oracle in
its sibling tree, and every other module of this package - including
`records/irs_dflt.py`, notwithstanding the shared `01`-name. Section 0.4.3
promises that the arithmetic test tier "imports only `cobol` and `records` and
touches no database, so it runs anywhere", and one import reaching into `dal`
would break that promise for every test in the tier.

Nothing here executes, embeds or shells out to a COBOL program, and nothing
links a database driver: the migrated cycle runs on a host with no COBOL
compiler and no COBOL runtime present (R-1). The frozen COBOL tree is read as
the specification for this module and is never modified.

DETERMINISM (R-6)
=================
Attribute order follows copybook declaration order, so this module can be set
beside its twenty-line copybook and diffed by eye. The thirty-three entries
are built in index order into a TUPLE, and every fixed collection in the file
is a tuple. No clock is consulted, no unpredictable value is drawn, the
process environment is not inspected, and execution is strictly sequential
with no concurrency introduced. The only import-time read is the loader's own
lazy, cached read of the frozen generated artifact, which is deterministic and
shared with every sibling record module. Two imports in two processes produce
identical state.

Where a semantic question cannot be settled by reading the frozen source, the
compiled program's observed behaviour settles it and the arbitration is
written down in `docs/migration/ambiguity-resolutions.md`.

A NOTE ON SUBSCRIPTS
====================
COBOL `OCCURS` is ONE-based: `Def-Acs (1)` is the first entry and
`Def-Acs (33)` the last. Python indexing is ZERO-based, so `def_group[0]` is
COBOL's entry 1 and `def_group[32]` is COBOL's entry 33. That offset is left
in plain sight. No one-based wrapper, no shim and no index-translating
accessor is provided: hiding the offset would be machinery R-3 forbids, and a
reader who does not know about it would be misled by a wrapper as easily as by
its absence. Where a COBOL locator in this file names a subscript, it names
the COBOL one.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = [
    "DefGroup",
    "SysDefaultRecord",
]


# =============================================================================
#  THE TWO FROZEN NAMES THIS MODULE IS KEYED TO
#
#  Both are written once, here, and every lookup below goes through them. They
#  are the only two literals in the file that name a frozen artifact, and the
#  pair is what makes the `Default-Record` collision impossible to walk into:
#  the copybook path selects the General Ledger declaration rather than the IRS
#  one, and the table name is the left half of every column-mapped entry key.
# =============================================================================

_COPYBOOK: Final[str] = "copybooks/wsdflt.cob"
_TABLE: Final[str] = "SYSDEFLT-REC"


# =============================================================================
#  ENTRY-KEY LOOKUP  (rule R-5)
#
#  Not one dictionary key is written out by hand below. Each is asked for, by
#  COBOL field name, against the generated artifact - which is what section
#  0.8.1 means by "every Python field definition cites its entry ... it is what
#  prevents fields being transcribed by eye". Guessing a key would be
#  especially unsafe for this record: two copybooks declare a `Default-Record`
#  holding a `Def-Acs`, and the column names on the right of a key drift from
#  the COBOL field names elsewhere in this system.
# =============================================================================


def _entry_keys_of_this_copybook() -> dict[str, str]:
    """Map each COBOL field name of `copybooks/wsdflt.cob` to its entry key.

    Two passes, in the order the Agent Action Plan's field-metadata direction
    implies - the table first, because the table name is what disambiguates
    this record from the IRS one, then the copybook file for the items that
    reach no column and so appear in no table result.

    Pass one reads `loader.entries_for_table`, which yields the four
    column-mapped entries in the column ordinal order of the frozen schema
    dump, and takes each entry's `copybook.name` as the COBOL field the column
    backs. One of the four has no copybook view at all - `DEF-REC-KEY`, which
    the bridge derives from the OCCURS subscript [common/dfltMT.cbl:L612] - and
    it is passed over, because a field no COBOL program can name is not a field
    of this record.

    Pass two reads `loader.entries_for_copybook_file`, whose result is
    restricted to one copybook by construction. That is the point of using it
    rather than the record-keyed accessor: `entries_for_copybook_record
    ("Default-Record")` reaches into `copybooks/irswsdflt.cob` as well, and the
    loader documents `Default-Record` as one of the record names that more than
    one copybook declares.

    Returns:
        Every COBOL field name this copybook declares, mapped to the key its
        dictionary entry carries. Six names for this record: the `01` group,
        the `03` group, the three leaf fields and the filler.
    """
    keyed: dict[str, str] = {}

    for entry in loader.entries_for_table(_TABLE):
        copybook_field = entry.copybook
        if copybook_field is None:
            # The bridge-derived primary key. Owned by
            # `acas_posting/dal/acas000_system.py`; see the module docstring.
            continue
        keyed[copybook_field.name] = entry.key

    for entry in loader.entries_for_copybook_file(_COPYBOOK):
        copybook_field = entry.copybook
        if copybook_field is None:
            continue
        keyed.setdefault(copybook_field.name, entry.key)

    return keyed


_ENTRY_KEYS: Final[dict[str, str]] = _entry_keys_of_this_copybook()


def _descriptor(cobol_name: str) -> FieldDescriptor:
    """Return the looked-up descriptor for one field of THIS copybook.

    The single door every descriptor in this module comes through. It reads the
    storage description off the generated artifact rather than accepting one
    from a caller, and it states in code the thing the module docstring states
    in prose: the entry it uses is declared by `copybooks/wsdflt.cob` and not
    by the IRS defaults copybook that shares this record's `01`-name.

    Args:
        cobol_name: The field name exactly as the copybook spells it, with its
            own casing and hyphens - `"Def-Acs"`, not `"DEF-ACS"` and not
            `"def_acs"`.

    Returns:
        The descriptor the dictionary holds for that field, carrying its
        digits, scale, sign, usage, width and Python carrier, plus both halves
        of its provenance.

    Raises:
        loader.DictionaryLookupError: This copybook declares no such field, or
            the entry found for it is declared by some other copybook. The
            second case cannot arise from the artifact as it stands and is
            checked anyway, because the failure it would produce - an IRS
            five-digit unscaled amount silently standing in for a General
            Ledger two-place one - is exactly the kind a later reader would
            never trace back to a lookup.
    """
    key = _ENTRY_KEYS.get(cobol_name)
    if key is None:
        raise loader.DictionaryLookupError(
            f"{_COPYBOOK} declares no field named {cobol_name!r} in the "
            f"generated data dictionary. The names it does declare are "
            f"{sorted(_ENTRY_KEYS)}. Field names are the copybook's own, "
            f"case-sensitive and hyphenated."
        )

    copybook_field = loader.copybook_field_for(key)
    if copybook_field is None or copybook_field.file != _COPYBOOK:
        declaring_file = (
            "no copybook" if copybook_field is None else copybook_field.file
        )
        raise loader.DictionaryLookupError(
            f"the entry keyed {key!r} is declared by {declaring_file}, not by "
            f"{_COPYBOOK}. This module models the General Ledger defaults "
            f"record; the record of the same COBOL 01-name in "
            f"copybooks/irswsdflt.cob is modelled by "
            f"acas_posting/records/irs_dflt.py and the two are deliberately "
            f"separate - their Def-Acs fields differ in width, scale and "
            f"storage class."
        )

    return FieldDescriptor.from_dictionary_key(key)


# The six items of the record, each looked up by its verbatim COBOL name. The
# order is the copybook's own declaration order, L14 through L19, so this block
# can be read straight down against the twenty-line source.
_DEFAULT_RECORD: Final[FieldDescriptor] = _descriptor("Default-Record")
_DEF_GROUP: Final[FieldDescriptor] = _descriptor("Def-Group")
_DEF_ACS: Final[FieldDescriptor] = _descriptor("Def-Acs")
_DEF_CODES: Final[FieldDescriptor] = _descriptor("Def-Codes")
_DEF_VAT: Final[FieldDescriptor] = _descriptor("Def-Vat")
_FILLER: Final[FieldDescriptor] = _descriptor("filler")


# =============================================================================
#  THE TWO COUNTS THAT SHAPE THE RECORD, TAKEN FROM THE DICTIONARY
#
#  The entry count and the character widths are as much part of a field's
#  declaration as its picture is, so they are looked up on the same terms. The
#  thirty-three is `Def-Group`'s own OCCURS [copybooks/wsdflt.cob:L15] and the
#  793 is the filler's own width [copybooks/wsdflt.cob:L19]; neither is typed
#  in, so neither can drift from the frozen source without the dictionary
#  drifting first.
# =============================================================================


def _occurs_count(descriptor: FieldDescriptor) -> int:
    """Return a table item's OCCURS count, refusing to guess at one.

    Args:
        descriptor: The descriptor of a COBOL table item.

    Returns:
        The number of entries the item's OCCURS clause declares.

    Raises:
        loader.DictionaryLookupError: The dictionary records no OCCURS for the
            item. There is no defensible fallback: a zero would build an empty
            table and a hard-coded thirty-three would be the transcription
            rule R-5 exists to prevent, and either would be discovered as a
            wrong posted figure rather than as an error.
    """
    occurs = descriptor.occurs
    if occurs is None:
        raise loader.DictionaryLookupError(
            f"the dictionary records no OCCURS count for "
            f"{descriptor.name!r} at {descriptor.source_locator}, so the "
            f"size of the table it heads cannot be taken from the frozen "
            f"source."
        )
    return occurs


def _character_width(descriptor: FieldDescriptor) -> int:
    """Return an alphanumeric item's declared width, refusing to guess at one.

    Args:
        descriptor: The descriptor of a COBOL alphanumeric item.

    Returns:
        The number of characters the item's PICTURE clause declares.

    Raises:
        loader.DictionaryLookupError: The dictionary records no character
            length for the item, so its space-filled initial value could not
            be built at the declared width.
    """
    width = descriptor.character_length
    if width is None:
        raise loader.DictionaryLookupError(
            f"the dictionary records no character length for "
            f"{descriptor.name!r} at {descriptor.source_locator}, so its "
            f"space-filled initial value cannot be built at the width the "
            f"frozen source declares."
        )
    return width


# 33, from `03 Def-Group occurs 33.` [copybooks/wsdflt.cob:L15].
_DEF_GROUP_ENTRIES: Final[int] = _occurs_count(_DEF_GROUP)

# 2, 1 and 793, from L17, L18 and L19 of the same copybook.
_DEF_CODES_WIDTH: Final[int] = _character_width(_DEF_CODES)
_DEF_VAT_WIDTH: Final[int] = _character_width(_DEF_VAT)
_FILLER_WIDTH: Final[int] = _character_width(_FILLER)


# =============================================================================
#  THE RECORD
# =============================================================================


@dataclass(slots=True)
class DefGroup:
    """One entry of the `03 Def-Group occurs 33.` defaults table.

    From [copybooks/wsdflt.cob:L15]. Three fields, seven bytes, and the unit
    the bridge turns into one row of `SYSDEFLT-REC` - `DEF-REC-KEY` carrying
    the subscript of the entry, as `move HV-DEF-ACS to Def-Acs
    (HV-DEF-REC-KEY)  *> KEY = table position` [common/dfltMT.cbl:L579] says
    outright.

    MUTABLE on purpose, and never `frozen=True`: the defaults are read and
    written by the maintenance programs, and the bridge writes straight into
    an entry on the way in from the database [common/dfltMT.cbl:L579-L581].

    A fresh entry holds zero at two places and spaces in both character
    fields, which is what `initialize Default-Record with filler.`
    [common/dfltMT.cbl:L530] leaves in one, and also exactly the state the
    bridge reads as an empty entry when deciding whether to write a row
    [common/dfltMT.cbl:L600-L604]. Nothing is coerced, padded, truncated or
    quantized on assignment: MOVE semantics belong to
    `acas_posting/cobol/move.py` and a numeric store to
    `acas_posting/cobol/arithmetic.py`.

    Attributes:
        def_acs: `Def-Acs`, the amount. `Decimal` at scale 2.
        def_codes: `Def-Codes`, two characters.
        def_vat: `Def-Vat`, one character.
    """

    # Traceability metadata (R-5), not record content. `RECORD` is the group
    # item itself and `FIELDS` its three subordinate items in declaration
    # order; both are tuples of looked-up descriptors, and `.cite()` on any of
    # them surfaces the loader's three-locator provenance string.
    RECORD: ClassVar[FieldDescriptor] = _DEF_GROUP
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _DEF_ACS,
        _DEF_CODES,
        _DEF_VAT,
    )

    # Def-Acs  pic 9(4)v99 comp  [copybooks/wsdflt.cob:L16]
    #
    # SCALED, so `Decimal` and not `int` - six digits, four of them integral,
    # two fractional, unsigned, binary storage. The dictionary says all of
    # that independently: `cobol_python_storage` DECIMAL, `digits` 6, `scale`
    # 2, `quantum` Decimal("0.01"), `signed` False. Its USAGE IS DECLARED ON
    # THE FIELD, not on `Def-Group`, so its descriptor reports
    # `usage_declared_at` as FIELD; this record inherits no usage from any
    # group. Four bytes of the entry's seven.
    #
    # Beware the same name in the other defaults copybook: `Def-Acs pic 9(5)`
    # [copybooks/irswsdflt.cob:L10] is five digits, UNSCALED and zoned
    # display. See the module docstring; the two are never reconciled.
    def_acs: Decimal = Decimal("0.00")

    # Def-Codes  pic xx  [copybooks/wsdflt.cob:L17]
    #
    # Two characters, space-filled at the width the dictionary carries.
    def_codes: str = " " * _DEF_CODES_WIDTH

    # Def-Vat  pic x  [copybooks/wsdflt.cob:L18]
    #
    # One character, space-filled on the same terms as `def_codes` - a single
    # space rather than the empty string, so that every character field in
    # this module starts at its declared width, as COBOL INITIALIZE leaves it.
    def_vat: str = " " * _DEF_VAT_WIDTH


@dataclass(slots=True)
class SysDefaultRecord:
    """The `01 Default-Record.` General Ledger / system defaults record.

    From [copybooks/wsdflt.cob:L14]: a thirty-three entry table followed by a
    793-byte filler, 1024 bytes in all. Reached as key 2 of the `acas000`
    four-way dispatch, through bridge `dfltMT`, into MySQL table
    `SYSDEFLT-REC`.

    THE CLASS NAME CARRIES A `Sys` PREFIX ITS COBOL NAME DOES NOT.
    The COBOL identifier is `Default-Record`, verbatim, at
    [copybooks/wsdflt.cob:L14] - and `copybooks/irswsdflt.cob:L8` declares a
    record of that same `01`-name, holding a `Def-Group occurs 33` of its own
    whose `Def-Acs pic 9(5)` [copybooks/irswsdflt.cob:L10] differs from this
    record's `Def-Acs pic 9(4)v99 comp` [copybooks/wsdflt.cob:L16] in width, in
    scale and in storage class. The maintainer flagged the divergence in this
    copybook's own header - "This is NOT the same as for IRS as DEF-ACAS is
    different size" [copybooks/wsdflt.cob:L7]. A bare `DefaultRecord` here
    would invite a reader to assume one record where the frozen source has two;
    the prefix names the subsystem instead. The IRS variant is
    `acas_posting/records/irs_dflt.py`, this module never imports it, and
    neither record is aliased to or derived from the other.

    MUTABLE on purpose, and never `frozen=True`.

    SUBSCRIPTS. `def_group` is indexed from zero while COBOL's `Def-Group` is
    indexed from one, so `def_group[0]` is `Def-Group (1)` and `def_group[32]`
    is `Def-Group (33)`. The offset is deliberately left in the open; see the
    module docstring for why no one-based wrapper is provided.

    Attributes:
        def_group: `Def-Group`, the thirty-three entry table, as a tuple of
            thirty-three distinct `DefGroup` instances in index order.
        filler: `filler`, the 793 bytes of padding that take the record to
            1024.
    """

    # Traceability metadata (R-5), not record content. `RECORD` is the 01-level
    # item [copybooks/wsdflt.cob:L14]; `FIELDS` holds its two subordinate items
    # in declaration order, L15 then L19 - the group that heads the table, then
    # the filler, whose descriptor carries `is_filler=True`.
    RECORD: ClassVar[FieldDescriptor] = _DEFAULT_RECORD
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _DEF_GROUP,
        _FILLER,
    )

    # Def-Group  occurs 33  [copybooks/wsdflt.cob:L15]
    #
    # A TUPLE of thirty-three distinct entries, built in index order, because
    # a COBOL table is fixed-length: entries are written into, never appended
    # or removed, and the length is part of the record's 1024-byte layout. The
    # entries themselves are mutable; the table that holds them is not.
    #
    # The thirty-three is the OCCURS count the dictionary carries for this
    # very item, not a number typed in here. It matters that all thirty-three
    # survive: section 0.4.1.3 records that the IRS defaults record - which
    # shares this shape, and whose 01/05/18 change is why the count came back
    # to thirty-three [copybooks/wsdflt.cob:L10-L11] - has "the account-code
    # table the posting section indexes at 31 and 32", so subscripts near the
    # end of the table carry meaning to callers. No truncation, no reordering,
    # and no compaction of entries that happen to be empty.
    #
    # 33 entries x 7 bytes = 231 bytes; 231 + 793 filler = 1024 bytes, which
    # is the "total 1024" the copybook states at L19 and the system-record size
    # it states at L6.
    def_group: tuple[DefGroup, ...] = dataclass_field(
        default_factory=lambda: tuple(
            DefGroup() for _ in range(_DEF_GROUP_ENTRIES)
        )
    )

    # filler  pic x(793)  [copybooks/wsdflt.cob:L19]
    #
    # Padding, and nothing else: it exists so the record is written at 1024
    # bytes and so matches `System-Record` on disk [copybooks/wsdflt.cob:L6],
    # and it was added when `sys002` began creating the record at that size
    # [copybooks/wsdflt.cob:L12]. It reaches no column of `SYSDEFLT-REC`, so
    # it appears in no table dump.
    #
    # It is carried as a real attribute because the frozen bridge treats these
    # bytes as part of the record - `initialize Default-Record with filler.`
    # [common/dfltMT.cbl:L530] names them explicitly through the WITH FILLER
    # phrase - while its descriptor's `is_filler=True` records the other half
    # of the truth: COBOL FILLER names no value, so no COBOL program can read
    # or write these bytes. Space-filled at the width the dictionary carries,
    # as INITIALIZE leaves it. See the module docstring for the full rationale.
    filler: str = " " * _FILLER_WIDTH
