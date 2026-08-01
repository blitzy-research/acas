"""The IRS defaults record: one COBOL record holding a 33-entry table.

A CREATE from `copybooks/irswsdflt.cob`, the smallest record copybook in this
package at thirteen lines, and the one whose consequence is furthest out of
proportion to its size: the whole record IS a single OCCURS table, and two of
its entries are the VAT control accounts the IRS posting path turns on.

The record carries TWO COBOL identifiers, and a reader may meet either -
`01 Default-Record.` [copybooks/irswsdflt.cob:L8], renamed by its caller to
`WS-IRS-Default-Record` [irs/irs030.cbl:L287]. `WsIrsDefaultRecord` follows the
CALLER's name because the bare copybook name collides with
`copybooks/wsdflt.cob`, which declares an `01 Default-Record.` of its own that
is not the same record - see "TWO RECORDS ARE CALLED Default-Record" below.
`irs/irs030.cbl` disambiguates it on the way in; this module keeps that
disambiguation. Both quotes are reproduced verbatim on `WsIrsDefaultRecord`.

    entity facade   IRS defaults
    handler         acasirsub3
    bridge          irsdfltMT       [common/irsdfltMT.scb:L315-L318]
    table           IRSDFLT-REC     4 columns, primary key DEF-REC-KEY
                                    [mysql/ACASDB.sql:L189-L195]
    copybook        copybooks/irswsdflt.cob

The schema names the owner itself, in the table comment:

    COMMENT='Defaults table for IRS'       [mysql/ACASDB.sql:L195]

THE MODULE'S MANDATE
====================
Agent Action Plan section 0.4.1.3 gives this file one line:

    acas_posting/records/irs_dflt.py | CREATE | copybooks/irswsdflt.cob |
    "IRSDFLT-REC, including the account-code table the posting section
    indexes at 31 and 32"

plus the folder mandate `records/__init__.py` sets out for all 27 record
modules: dictionary-looked-up descriptors, oddities preserved, plain
dataclasses, nothing added.

So this file is a RECORD LAYOUT and nothing else - no posting logic, no
account selection, no SQL and no row model. The `irs030` program module owns
the posting logic; the `acasirsub3` handler module owns the SQL, the
subscript-to-key mapping and the row model.

THE FROZEN SOURCE, IN FULL - THIRTEEN LINES
===========================================
Short enough to set beside its translation in one screen, so here it is
whole, with its header history, which is evidence rather than decoration::

    L1-L5   an asterisk box reading "Working Storage for the Defaults File"
    *> rec 256 bytes 15/02/09                                   L6
    *> Rec 264 bytes 06/05/18 - to support temp. default 33 in
       postings (irs030).                                       L7
     01  Default-Record.                                        L8
         03  Def-Group                  occurs 33.              L9
             05  Def-Acs         pic 9(5).                      L10
             05  Def-Codes       pic xx.                        L11
             05  Def-Vat         pic x.                         L12
    *>                                                          L13

L7 is ONE physical line in the frozen file, wrapped above only to stay inside
this docstring's width.

The two header sizes are an arithmetic record of one change. Each `Def-Group`
entry is 5 + 2 + 1 = 8 bytes, and this module does not take that on trust - it
is the sum of the three descriptors' own `byte_length`:

    32 x 8 = 256      the 2009 size    [copybooks/irswsdflt.cob:L6]
    33 x 8 = 264      the 2018 size    [copybooks/irswsdflt.cob:L7]

The table was therefore widened by exactly ONE entry, and the maintainer states
the reason on the same line: "to support temp. default 33 in postings
(irs030)".

Nothing else is in this copybook, and each absence was counted rather than
assumed. A case-insensitive search for FILLER, REDEFINES, COMP, binary and
SIGN returns zero matches, as do VALUE and any 88-level, so this module
declares no predicate. Three declared leaf fields; 3 x 33 = 99 storage items;
one OCCURS clause; three PICTURE clauses.

WHY 33 IS LOAD-BEARING - ENTRIES 31 AND 32
==========================================
Two entries of this table are the input-tax and output-tax control accounts
of the IRS ledger, and the posting path reaches them by literal subscript:

    move     def-acs (31) to nl-owning.         [irs/irs030.cbl:L1594]
    move     def-acs (32) to nl-owning.         [irs/irs030.cbl:L1604]

each under the maintainer's own heading at [irs/irs030.cbl:L1592], "Get
default input and output tax accounts via acs 31 & 32 and save them", and
each followed by an indexed read whose result is kept in a pre-loop snapshot
[irs/irs030.cbl:L1602] and [irs/irs030.cbl:L1612]. The same two entries are
tested twice more:

    or  NL-Owning = Def-ACS (31) or Def-ACS (32)   [irs/irs030.cbl:L668]
    if  input-account = def-acs (31) or def-acs (32)
                                                  [irs/irs030.cbl:L871]

Those four sites are the whole reason Agent Action Plan section 0.4.1.3
singles this record out. They are also anomaly A-5's mechanism: the two
snapshots are written back from working storage at end of job
[irs/irs030.cbl:L1704-L1708], discarding any in-loop rewrite of the same two
accounts - a lost update, reproduced deliberately.

NONE of that is implemented here, and the locators above are recorded so that
the migration's traceability document can lift them. This module has no
entry-31 or entry-32 constant, no VAT-account accessor, no selection helper,
no subscript accessor, no one-based helper and no by-position mapping. COBOL
OCCURS is 1-BASED - `Def-Acs (31)` is `def_group[30]` - and that offset is
deliberately left at the call site that makes it, where it can be read against
the COBOL literal beside it; `WsIrsDefaultRecord` states the rule again on the
attribute itself.

ANOMALY: THE BRIDGE REJECTS THE VERY ENTRY 33 EXISTS FOR
========================================================
The copybook says the table grew to 33 entries for the posting program. The
bridge then refuses to carry entry 33 at all. Both statements sit in the
frozen source; both are reproduced, neither is reconciled.

The bridge's guard, verbatim:

    if       HV-DEF-REC-KEY = zero or > 32     [common/irsdfltMT.cbl:L575]

followed two lines later by

    move     HV-DEF-REC-KEY to WE-Error        [common/irsdfltMT.cbl:L577]

so a key of zero, or one above 32, is reported as an error and the row is not
carried. That is not an isolated bound: the same ceiling appears EIGHT times
in the one bridge - in the maintainer's comments at [common/irsdfltMT.cbl:
L385], [:L470] and [:L539], and in code at [:L545] (the read loop), [:L565],
[:L575] (the guard above), [:L626] (the write loop) and [:L678] (the rewrite
loop). Entry 33 can therefore be neither read, written nor rewritten through
the bridge.

Against that, three facts. The copybook header at L7 says the record was
grown to 264 bytes "to support temp. default 33 in postings (irs030)". The
column `DEF-REC-KEY tinyint(2) unsigned` [mysql/ACASDB.sql:L190] holds 33
without difficulty. And `irs/irs030.cbl` really does use the entry - it
accepts all three of its fields from the operator when the subscript reaches
33, at [irs/irs030.cbl:L644] `if w = 33`, then [:L651], [:L653] and [:L655].

This is NOT one of the twenty-two anomalies Agent Action Plan section 0.6.7
enumerates. It is a twenty-third, found while checking that register, and it
belongs in the migration's anomaly log with the `acasirsub3` handler module
as the reproduction site and this module as the recording site. It is also an
open question for the compiled oracle - see "OPEN QUESTIONS" below.

The table is declared with THIRTY-THREE entries, exactly as the copybook
declares it, and the count is taken from the dictionary rather than typed
here. It is not shortened to thirty-two, no range check is added, no index is
refused and the two numbers are not reconciled. Rule R-4: a defect reproduced
is correct; a defect fixed is a failure.

DEF-REC-KEY IS DECLARED BY NO COPYBOOK
======================================
The table's primary key has no counterpart in the record layout. It exists
because the bridge writes ONE ROW PER OCCURS ENTRY and stores the subscript
itself as the key, and it says so in its own comment. All of the frozen
evidence - the three unload moves carrying `*> KEY = table position`, the load
path that sets the key from the loop subscript, the host-variable group that
declares it first of four, the column and its PRIMARY KEY clause, and the
maintainer's revision note - is quoted with locators on `WsIrsDefaultRecord`,
so it is not repeated here.

    the copybook holds   ONE record containing a 33-entry table
    the schema holds     UP TO 33 ROWS of a 4-column table

This is the SECOND bridge-only-column case in this package, and the
structurally larger of the two - `WsIrsDefaultRecord` sets both out. Agent
Action Plan section 0.1.1 uses the first to settle where field metadata comes
from: "A migration driven from the copybooks alone would silently omit three
columns of a posting table."

This module models the RECORD. It declares no key attribute, no row identity
and no row collection, because the copybook declares none. The dictionary keeps
the bridge and column views of the key under `IRSDFLT-REC.DEF-REC-KEY`,
reachable through `loader.host_variable_for`, `loader.column_for` and
`loader.derivation_for`. Asking `FieldDescriptor.from_dictionary_key` for it
is refused on purpose - it has no COBOL-side storage to describe.

TWO RECORDS ARE CALLED Default-Record, AND THEY ARE NOT THE SAME
================================================================
Two in-scope copybooks declare an `01 Default-Record.`, with the same three
field names and the same OCCURS count, describing different data. The
maintainer flags it himself, in the GL copybook's header:

    *>   This is NOT the same as for IRS as DEF-ACAS is different size
                                                 [copybooks/wsdflt.cob:L7]

                       GL / System                  IRS  (THIS module)
    ---------------- ---------------------------- -------------------------
    copybook         copybooks/wsdflt.cob         copybooks/irswsdflt.cob
    Def-Acs          pic 9(4)v99 comp      [:L16] pic 9(5)           [:L10]
                     -> Decimal, scale 2          -> int, scale 0
    DEF-ACS column   decimal(6,2) unsigned        decimal(5,0) unsigned
    trailing filler  pic x(793)            [:L19] none
    record size      1024 bytes            [:L19] 264 bytes           [:L7]
    table / handler  SYSDEFLT-REC / acas000 key 2 IRSDFLT-REC / acasirsub3
    module / class   system_dflt.SysDefaultRecord irs_dflt.WsIrsDefaultRecord

The `01`-name and the `occurs 33` are IDENTICAL in both - which is what makes
the collision dangerous rather than obvious.

This is anomaly-A-21-class evidence - field-name collisions across copybooks
forcing qualified references - and why both classes carry a prefix the COBOL
`01`-name does not have. The two never merge, never share a descriptor, and
this module imports nothing from `records/system_dflt.py`.

The dangerous confusion is the TYPE of `Def-Acs`: `int` here, `Decimal`
there. Take the wrong one and every IRS default account code changes value
silently. Three independent guards stand against it - the dictionary key's
left side is the TABLE name `IRSDFLT-REC` rather than the colliding `01`-name,
so the two records cannot key to one entry; the entries come from
`loader.entries_for_copybook_file`, scoped to `copybooks/irswsdflt.cob` by
construction, where
`loader.entries_for_copybook_record("Default-Record")` returns ELEVEN entries
spanning BOTH copybooks; and `_keys_by_cobol_name` asserts the declaring file
of every entry it uses.

The type is the tell in the other direction too. `Def-Acs` is an ACCOUNT CODE,
`pic 9(5)`, unsigned zoned DISPLAY, scale ZERO, carried by `int`. The column is
spelled `DEF-ACS decimal(5,0) unsigned` [mysql/ACASDB.sql:L191] and that
spelling is a trap: a DECIMAL of scale zero holds integers, so the SQL type
name does not make the field a `decimal.Decimal`. This module imports no
arbitrary-precision numeric type at all, having no monetary and no fractional
field to hold - and no binary floating-point value either, which rule R-2
forbids outright. The carrier is `python_storage` as the dictionary records
it, INT.

BRIDGE DRIFT - THREE KINDS, ALL HANDED OVER UNADJUDICATED  (rule R-4)
=====================================================================
The bridge is not a transparent pipe. For this four-column table the three
layers disagree in three distinct ways, and this module records all three
without settling any of them:

1. A BRIDGE-ONLY KEY COLUMN, plus the one-record-to-many-rows transformation
   that produced it. Covered above.

2. STORAGE-CLASS DRIFT ON `Def-Acs`: zoned DISPLAY in the copybook
   [copybooks/irswsdflt.cob:L10], binary `PIC 9(05) COMP` in the host variable
   [common/irsdfltMT.cbl:L325], DECIMAL in the column [mysql/ACASDB.sql:L191].
   Digits and scale survive intact at 5 and 0; the storage class does not.
   `_DEF_ACS.drift()` passes `loader.drift_for("IRSDFLT-REC.DEF-ACS")` and its
   one-sentence description straight through, unadjudicated. It applies no
   conversion; the bridge boundary is where one belongs, and
   the `acasirsub3` handler module owns it.

3. `Def-Codes` and `Def-Vat` PASS THROUGH CLEAN - X(2) and X(1) at all three
   layers [copybooks/irswsdflt.cob:L11-L12], [common/irsdfltMT.cbl:L326-L327]
   and [mysql/ACASDB.sql:L192-L193]. Agent Action Plan section 0.6.2's point
   that the drift is specific rather than systemic is visible inside a table
   of four columns: one field drifts, two do not, and one has no copybook at
   all.

A `FieldDescriptor` here reports the COPYBOOK view as its own digits, scale,
sign and usage. It never blends the three layers into one figure, never adds
the key column and never models rows.

THE BRIDGE HAS NO DEDICATED HOST-VARIABLE LOAD PARAGRAPH
========================================================
`irsdfltMT` is one of four bridges with no `bb000-HV-Load` paragraph - the
others being `dfltMT`, `finalMT` and `irsfinalMT` - and a reader who goes
looking for the conventional two-paragraph shape will not find it. A search
of the whole bridge for a load or unload paragraph name returns nothing. It
does the work inline instead, inside the verb paragraphs themselves, whose
own opening lines are:

    unload, into the record   ba040-Process-Read-Next  [:L470],
                              the moves at             [:L603-L606]
    load, out of the record   ba070-Process-Write      [:L617],
                              the moves at             [:L633-L641]
    and again                 ba090-Process-Rewrite    [:L673],
                              the moves at             [:L685-L693]

which is why the dictionary's provenance for these fields points at statement
lines rather than a paragraph name, and why `group_initialised_before_load` is
False on every one of them.

One statement in that path fixes the DEFAULT VALUES in this module:

    initialize Default-Record with filler.     [common/irsdfltMT.cbl:L543]

COBOL's INITIALIZE sets a numeric item to zero and an alphanumeric item to
spaces, so an unset entry is zeros and spaces, never absent - which is why all
four columns can be declared NOT NULL with no column DEFAULT and why, in the
words of Agent Action Plan section 0.6.2, "the Python layer must default rather
than omit". The `_spaces` helper carries the consequence and the locators;
`def_acs` defaults to `0`.

FOUR SPELLINGS OF ONE FIELD NAME
================================
COBOL is case-insensitive, so the same field compiles under any casing, and
the frozen source uses four for this one. Recorded verbatim, with locators,
because rule R-4 preserves oddities:

    Def-Acs    the declaration            [copybooks/irswsdflt.cob:L10]
    Def-ACS    [irs/irs030.cbl:L651], [:L659], [:L668] (twice on L668)
    Def-acs    [irs/irs030.cbl:L854]
    def-acs    [irs/irs030.cbl:L762], [:L871] (twice), [:L964], [:L977],
               [:L983], [:L1091], [:L1108], [:L1114], [:L1174], [:L1193],
               [:L1248], [:L1450], [:L1594], [:L1604]

Nor is it confined to that field. `Def-Vat` also has four spellings -
`Def-Vat` [copybooks/irswsdflt.cob:L12] and [irs/irs030.cbl:L677], `Def-VAT`
[irs/irs030.cbl:L655] and [:L697], `DEF-Vat` [irs/irs030.cbl:L674], and
`def-vat` at seven further sites - and `Def-Codes` has two, `Def-Codes`
[copybooks/irswsdflt.cob:L11] and [irs/irs030.cbl:L653] against `def-codes`
[irs/irs030.cbl:L794], [:L835] and [:L1261].

Each descriptor's `name` carries the COPYBOOK's spelling and only that. No
alias is published, no case-insensitive lookup exists and no spelling is
rewritten to match another.

TRACEABILITY: EVERY FIELD CITES A DICTIONARY ENTRY  (rule R-5)
==============================================================
Dictionary-first, on the terms `records/__init__.py` sets out: no picture
clause, digit count, scale, sign or storage class is written by hand here.
Five keys are looked up and none is guessed - read back from
`loader.entries_for_copybook_file("copybooks/irswsdflt.cob")`, matching on
each entry's own `copybook.name`.

    copybook field    dictionary key                     column
    ---------------- ---------------------------------- --------------
    Default-Record    Default-Record.Default-Record#8    (no column)
    Def-Group         Default-Record.Def-Group#9         (no column)
    Def-Acs           IRSDFLT-REC.DEF-ACS                DEF-ACS
    Def-Codes         IRSDFLT-REC.DEF-CODES              DEF-CODES
    Def-Vat           IRSDFLT-REC.DEF-VAT                DEF-VAT
                      IRSDFLT-REC.DEF-REC-KEY            DEF-REC-KEY
                        ^ no copybook side; no attribute here

The `#8` and `#9` suffixes are the generator's own disambiguation for the two
copybook-only group items whose names the GL copybook also declares - that one
carries `#14` and `#15`, plus a `filler` this record does not have. Four
entries for the table against three fields on `DefGroup`; the difference is
`DEF-REC-KEY` at ordinal 1.

`cite()` passes through to `loader.cite(<its key>)`, reimplementing nothing.
For `Def-Acs` it reads:

    IRSDFLT-REC.DEF-ACS  copybook=copybooks/irswsdflt.cob:L10
    bridge=common/irsdfltMT.cbl:L325  column=mysql/ACASDB.sql:L191

OPEN QUESTIONS FOR THE COMPILED ORACLE  (rule R-6)
==================================================
Two questions about this record cannot be settled by reading the frozen
source. Both belong in the migration's ambiguity-resolutions document, and this
module settles NEITHER - it records them and stops.

  Q-a  What does the compiled system actually do when `irs030` uses default
       entry 33, given that the bridge reports a key above 32 as an error
       [common/irsdfltMT.cbl:L575] while the copybook exists in its 264-byte
       form precisely to carry that entry [copybooks/irswsdflt.cob:L7]? Is
       the entry silently dropped at the bridge, is the whole write refused,
       or does the handler surface a status the program acts on? This must be
       measured against the compiled oracle, not reasoned about.

  Q-b  What does a `pic 9(5)` zoned value become after passing through a
       `PIC 9(05) COMP` host variable [common/irsdfltMT.cbl:L325] into a
       `decimal(5,0) unsigned` column [mysql/ACASDB.sql:L191]? The digits and
       scale agree at all three layers, so the question is what the bridge's
       C interface does with the representation change - again a measurement.

Determinism, the other half of rule R-6, holds here on the folder-wide terms:
no clock, no unpredictable value, no environment inspection, no input or output
beyond the loader's cached read, copybook declaration order, and tuples
throughout, so two imports in two processes produce identical state.

LAYERING: THIS IS A LEAF MODULE  (Agent Action Plan section 0.4.3)
==================================================================
A leaf module on the terms `records/__init__.py` sets out for the whole folder
- `acas_posting.cobol.field`, `acas_posting.dictionary.loader` and the
standard library, and nothing else, so that the arithmetic test tier "imports
only `cobol` and `records` and touches no database". Two of the prohibitions
are live temptations for this file in particular: the `acasirsub3` handler
module, which owns the subscript-to-key mapping, and the `irs030` program
module, which owns the entry-31 and entry-32 selection. Also forbidden is ANY
other module of this package - above all `records/system_dflt.py`, for the
collision reason given above.

WHAT THIS MODULE DELIBERATELY DOES NOT HAVE
===========================================
Written down because each absence is a decision, and because the next reader
will be tempted by at least one of them:

    * no `def_rec_key` attribute, no row model, no row identity, no
      collection of rows - the copybook declares no key field
    * no subscript accessor, one-based helper or by-position mapping; no
      ceiling of thirty-two entries, range check or index refusal; no
      entry-31 or entry-32 constant, VAT-account accessor or search helper
    * no storage-class conversion, and no arbitrary-precision numeric type
      for a scale-zero account code
    * no alias for the other spellings of a field name, and no 88-level
      predicate - the copybook declares none
    * no construction hook, padding step, validation or exception of its own;
      a value too wide for a field is the consuming layer's business
    * no schema definition, object-relational mapping base, declarative
      metadata or DDL of any kind; and no concurrency

The register of every reproduction site in this package is
the migration's anomaly log; the arbitrations are in
the migration's ambiguity-resolutions document.
"""

from __future__ import annotations

import dataclasses
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# `__all__` is the one list in this module, and deliberately so: it is a
# module-export declaration, spelled the way the standard library and
# `records/__init__.py` spell it, and not one of the data collections rule R-6
# holds to tuples. Sorted, so its order cannot drift.
__all__: Final[list[str]] = ["DefGroup", "WsIrsDefaultRecord"]


#  THE ONE FROZEN NAME THIS MODULE IS SCOPED TO

# The declaring copybook. Every dictionary entry used below must come from
# this file and no other: `copybooks/wsdflt.cob` declares an 01 of the same
# name whose `Def-Acs` is a scale-2 decimal, and picking that one up would
# change every IRS default account code without changing a visible line of
# logic. See "TWO RECORDS ARE CALLED Default-Record" in the module docstring.
_COPYBOOK: Final[str] = "copybooks/irswsdflt.cob"


#  THE DICTIONARY KEYS, LOOKED UP RATHER THAN TYPED  (rule R-5)


def _keys_by_cobol_name() -> dict[str, str]:
    """Map each COBOL field name this copybook declares to its entry key.

    The keys are read back from the generated dictionary instead of being
    written out here, which is the ordering Agent Action Plan section 0.8.1
    makes a directive rather than a preference: the dictionary is generated
    from the bridge first, and a record module cites it.

    `loader.entries_for_copybook_file` is the precise accessor for this
    record. The obvious alternative takes an 01-name, and `Default-Record` is
    declared by TWO in-scope copybooks, so it answers with eleven entries
    spanning both of them. Scoping by FILE puts the GL record out of reach by
    construction rather than by care.

    Returns:
        Copybook field name to dictionary entry key, in the document's own
        declaration order for this copybook, which makes the mapping
        deterministic (rule R-6). Five pairs: the 01 group, the 03 group and
        the three 05 items. `DEF-REC-KEY` is not among them, because no
        copybook declares it.
    """
    keys: dict[str, str] = {}
    for entry in loader.entries_for_copybook_file(_COPYBOOK):
        declaration = entry.copybook
        # Belt and braces on the collision. The accessor above cannot hand
        # back an entry from another copybook, and this states the invariant
        # the rest of the module rests on. It checks PROVENANCE and not a data
        # value: no accounting figure passes through it, and it can only fire
        # on a malformed artifact. Rule R-3 bars added validation of the
        # POSTING BEHAVIOUR, which this is not.
        assert declaration is not None, entry.key
        assert declaration.file == _COPYBOOK, declaration.file
        keys[declaration.name] = entry.key
    return keys


_KEYS: Final[dict[str, str]] = _keys_by_cobol_name()


def _described(cobol_name: str) -> FieldDescriptor:
    """Return the descriptor the dictionary holds for one COBOL field name.

    Args:
        cobol_name: The field name with the copybook's own casing, as
            `"Def-Acs"` - case-sensitive, like every name in the dictionary,
            and never one of the three other spellings the programs use.

    Returns:
        The descriptor built from that entry's COPYBOOK view, with its
        digits, scale, sign, usage and Python carrier exactly as the frozen
        declaration has them, and its provenance attached.
    """
    return FieldDescriptor.from_dictionary_key(_KEYS[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return the initial value of an alphanumeric item: spaces, full width.

    The width is the descriptor's own `character_length`, so the default
    cannot drift from the picture clause it comes from. Spaces rather than an
    empty string, and never `None`, because that is the state
    `initialize Default-Record with filler` leaves the record in
    [common/irsdfltMT.cbl:L543] and the reason all four columns are declared
    NOT NULL [mysql/ACASDB.sql:L190-L193].

    Args:
        descriptor: An alphanumeric field's descriptor.

    Returns:
        As many spaces as the copybook declares characters.
    """
    assert descriptor.character_length is not None, descriptor.name
    return " " * descriptor.character_length


# The 03 group, with its OCCURS. ONE descriptor carrying `occurs == 33`, which
# is what the dictionary yields for this record: the copybook declares one
# table, so there is no expansion into thirty-three descriptors.
_DEF_GROUP: Final[FieldDescriptor] = _described("Def-Group")

# The three 05 items, in copybook declaration order, L10 -> L11 -> L12.
_DEF_ACS: Final[FieldDescriptor] = _described("Def-Acs")
_DEF_CODES: Final[FieldDescriptor] = _described("Def-Codes")
_DEF_VAT: Final[FieldDescriptor] = _described("Def-Vat")

# The table's length is the copybook's own number, taken from the descriptor
# [copybooks/irswsdflt.cob:L9] so that it cannot drift from the declaration.
assert _DEF_GROUP.occurs is not None, _DEF_GROUP.dictionary_key
_OCCURS: Final[int] = _DEF_GROUP.occurs

# The two alphanumeric initial values, computed once. Strings are immutable, so
# a plain dataclass default is safe for them and no factory is needed.
_DEF_CODES_INITIAL: Final[str] = _spaces(_DEF_CODES)
_DEF_VAT_INITIAL: Final[str] = _spaces(_DEF_VAT)


#  THE RECORD LAYOUT
#  Two plain dataclasses, neither frozen. The defaults record is read into
#  WORKING STORAGE and amended there - the out-of-scope maintenance paths of
#  `irs/irs030.cbl` accept new values into it field by field, entry 33
#  included [irs/irs030.cbl:L651-L655] - so a frozen record could not hold
#  what the COBOL holds. `slots=True` on both, which costs nothing and makes
#  an attribute the copybook does not declare impossible to attach (rule R-3).


@dataclasses.dataclass(slots=True)
class DefGroup:
    """One entry of the IRS defaults table: an account code and two codes.

        03  Def-Group                  occurs 33.
            05  Def-Acs         pic 9(5).
            05  Def-Codes       pic xx.
            05  Def-Vat         pic x.
                                        [copybooks/irswsdflt.cob:L9-L12]

    THIS IS THE IRS GROUP, from `copybooks/irswsdflt.cob`, behind table
    `IRSDFLT-REC` and handler `acasirsub3`. `records/system_dflt.py` declares
    a group of the same shape for `copybooks/wsdflt.cob:L15`, behind
    `SYSDEFLT-REC` and handler `acas000` file key 2, whose `Def-Acs` is a
    SCALE-2 DECIMAL rather than a scale-0 integer. Python module namespaces
    keep the two apart, so both may keep the COBOL name; a reader importing
    both must keep the tables straight, and the type of `def_acs` is the tell.

    Three attributes, in copybook declaration order, and nothing else. No
    key, no row identity, no subscript, no predicate, no accessor.

    Attributes:
        def_acs: `Def-Acs pic 9(5)` - the default ACCOUNT CODE. Unsigned
            zoned DISPLAY, five digits, scale zero, so an `int` and never an
            arbitrary-precision decimal, whatever the column's type name
            suggests. Entries 31 and 32 hold the two VAT control accounts
            [irs/irs030.cbl:L1594] and [irs/irs030.cbl:L1604], but this class
            knows nothing of that.
        def_codes: `Def-Codes pic xx` - the default posting code, two
            characters, initially spaces.
        def_vat: `Def-Vat pic x` - the default VAT code, one character,
            initially a space. `irs/irs030.cbl` prompts for it as "{I, O, N}"
            [irs/irs030.cbl:L650] and tests it against "N" [:L674]; the
            record itself carries no such condition name, so this class
            declares no predicate over it.
    """

    # The three 05 items of this group, in copybook declaration order. Order
    # is fixed by the copybook and is part of behaviour (rule R-6): a reader
    # can set this class beside its thirteen lines and diff the two by eye.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _DEF_ACS,
        _DEF_CODES,
        _DEF_VAT,
    )

    # 05  Def-Acs         pic 9(5).        [copybooks/irswsdflt.cob:L10]
    # DISPLAY, unsigned, digits 5, scale 0 -> int. Zero after
    # `initialize Default-Record with filler` [common/irsdfltMT.cbl:L543].
    # The bridge narrows the storage class to `PIC 9(05) COMP`
    # [common/irsdfltMT.cbl:L325] and the column is `decimal(5,0) unsigned`
    # [mysql/ACASDB.sql:L191]; that disagreement is handed over untouched by
    # `_DEF_ACS.drift()` and is applied at the bridge boundary, not here.
    def_acs: int = 0

    # 05  Def-Codes       pic xx.          [copybooks/irswsdflt.cob:L11]
    # X(2) at all three layers: host variable [common/irsdfltMT.cbl:L326],
    # column `char(2)` [mysql/ACASDB.sql:L192]. No drift.
    def_codes: str = _DEF_CODES_INITIAL

    # 05  Def-Vat         pic x.           [copybooks/irswsdflt.cob:L12]
    # X(1) at all three layers: host variable [common/irsdfltMT.cbl:L327],
    # column `char(1)` [mysql/ACASDB.sql:L193]. No drift.
    def_vat: str = _DEF_VAT_INITIAL


@dataclasses.dataclass(slots=True)
class WsIrsDefaultRecord:
    """The IRS defaults record: one record that is entirely one table.

        01  Default-Record.                 [copybooks/irswsdflt.cob:L8]

    renamed by its caller, which is where this class takes its name from:

        copy "irswsdflt.cob" replacing Default-Record
                                  by WS-IRS-Default-Record.
                                        [irs/irs030.cbl:L287]

    THE PRIMARY KEY IS NOT HERE, AND THAT IS THE POINT
    --------------------------------------------------
    `IRSDFLT-REC` has four columns; this record declares three fields. The
    fourth, `DEF-REC-KEY`, is declared by NO COPYBOOK. It exists because the
    bridge writes one row per OCCURS entry and stores the SUBSCRIPT as the
    key - it says as much in its own comment, `*> KEY = table position`
    [common/irsdfltMT.cbl:L603], alongside [:L604] and [:L605]; it loads the
    key from the loop subscript at [common/irsdfltMT.cbl:L633-L641]; it
    declares it first of four in the host-variable group
    [common/irsdfltMT.cbl:L323-L327], as `HV-DEF-REC-KEY PIC 9(03) COMP`
    [:L324]; and the schema carries it as `DEF-REC-KEY tinyint(2) unsigned
    NOT NULL` [mysql/ACASDB.sql:L190] with `PRIMARY KEY (DEF-REC-KEY)`
    [mysql/ACASDB.sql:L194]. The maintainer's own revision note records the
    change: "Changed for one Cobol File/Record to many table rows - irsdfltMT
    and finalMT" [common/irsdfltMT.cbl:L137].

    So there is deliberately no attribute for it here, and no row model
    either: the `acasirsub3` handler module owns the subscript-to-key mapping in
    both directions, and `loader.host_variable_for`, `loader.column_for` and
    `loader.derivation_for` answer for the two layers that do declare it,
    under the key `IRSDFLT-REC.DEF-REC-KEY`. This is the second bridge-only
    case in this package after the three IRS posting date components in
    `records/irs_posting.py`, and the structurally larger of the two: one
    record becomes up to thirty-three rows, and the extra column is prepended
    at ordinal 1 rather than interleaved.

    Attributes:
        def_group: The thirty-three entries of `Def-Group`, as a fixed-length
            tuple - `occurs 33` [copybooks/irswsdflt.cob:L9]. THIRTY-THREE and
            not thirty-two, even though the bridge reports a key above 32 as
            an error [common/irsdfltMT.cbl:L575]; that contradiction is
            recorded in this module's docstring and reproduced, not repaired.
            A tuple rather than a list so the SHAPE cannot change while the
            entries stay amendable, and thirty-three DISTINCT entries rather
            than one shared entry repeated, which would alias every default
            to every other. Remember that COBOL subscripts are 1-based:
            `Def-Acs (31)` is `def_group[30].def_acs` at the call site that
            makes the conversion.
    """

    # The record's one member is its 03 group, so this carries a single
    # descriptor whose `occurs` is 33 - the shape the dictionary yields for
    # this copybook, rather than a thirty-three-fold expansion.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_DEF_GROUP,)

    # 03  Def-Group                  occurs 33.  [copybooks/irswsdflt.cob:L9]
    # 8 bytes per entry, 264 bytes in all [copybooks/irswsdflt.cob:L7].
    def_group: tuple[DefGroup, ...] = dataclasses.field(
        default_factory=lambda: tuple(DefGroup() for _ in range(_OCCURS))
    )
