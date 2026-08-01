"""The IRS defaults record: one COBOL record holding a 33-entry table.

A CREATE from `copybooks/irswsdflt.cob`, the smallest record copybook in this
package at thirteen lines, and the one whose consequence is furthest out of
proportion to its size: the whole record IS a single OCCURS table, and two of
its entries are the VAT control accounts the IRS posting path turns on.

The record carries TWO COBOL identifiers, and a reader may meet either:

    01  Default-Record.                    [copybooks/irswsdflt.cob:L8]

    copy "irswsdflt.cob" replacing Default-Record
                              by WS-IRS-Default-Record.
                                           [irs/irs030.cbl:L287]

`WsIrsDefaultRecord` follows the CALLER's name rather than the copybook's,
because the bare copybook name collides with `copybooks/wsdflt.cob`, which
declares an `01 Default-Record.` of its own that is not the same record - see
"TWO RECORDS ARE CALLED Default-Record" below. `irs/irs030.cbl` disambiguates
it on the way in; this module keeps that disambiguation.

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

plus the folder mandate that governs all 27 record modules - every module is
a CREATE from its copybook, translating each 05/03 field to a dataclass
attribute whose descriptor is looked up in the generated dictionary, and
oddities in the source are preserved rather than repaired. Its shape comes
from section 0.8.1, "Plain modules and dataclasses; no ORM entity layer", and
its scope from rule R-3, which has the record modules mirror their copybooks
field for field with nothing added.

So this file is a RECORD LAYOUT and nothing else. It holds no posting logic,
no account selection, no SQL and no row model:

    programs/irs030_posting.py      owns the posting logic
    dal/acasirsub3_irs_dflt.py      owns the SQL, the subscript-to-key
                                    mapping and the row model

THE FROZEN SOURCE, IN FULL - THIRTEEN LINES
===========================================
Short enough to set beside its translation in one screen, so here it is
whole, with its header history, which is evidence rather than decoration::

    *>*******************************************               L1
    *>                                          *               L2
    *>  Working Storage for the Defaults File   *               L3
    *>                                          *               L4
    *>*******************************************               L5
    *> rec 256 bytes 15/02/09                                   L6
    *> Rec 264 bytes 06/05/18 - to support temp. default 33 in
       postings (irs030).                                       L7
     01  Default-Record.                                        L8
         03  Def-Group                  occurs 33.              L9
             05  Def-Acs         pic 9(5).                      L10
             05  Def-Codes       pic xx.                        L11
             05  Def-Vat         pic x.                         L12
    *>                                                          L13

L7 is one physical line in the frozen file, wrapped above only to stay inside
this docstring's width. Verbatim, it reads:

  *> Rec 264 bytes 06/05/18 - to support temp. default 33 in postings (irs030).

The two header sizes are an arithmetic record of one change. Each `Def-Group`
entry is 5 + 2 + 1 = 8 bytes, and this module does not take that on trust -
it is the sum of the three descriptors' own `byte_length`:

    32 x 8 = 256      the 2009 size    [copybooks/irswsdflt.cob:L6]
    33 x 8 = 264      the 2018 size    [copybooks/irswsdflt.cob:L7]

The table was therefore widened by exactly ONE entry, and the maintainer
states the reason on the same line: "to support temp. default 33 in postings
(irs030)".

Nothing else is in this copybook, and each absence was checked rather than
assumed. There is no FILLER, no REDEFINES, no COMP, no binary-family item and
no SIGN clause anywhere in it - a case-insensitive search for all four terms
returns zero matches - and no VALUE clause and no 88-level condition name, so
this module declares no predicate. Three declared leaf fields; 3 x 33 = 99
storage items; one OCCURS clause; three PICTURE clauses.

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
`docs/migration/traceability.md` can lift them. This module has no entry-31
constant, no entry-32 constant, no VAT-account accessor and no selection
helper. Every subscript decision stays at the site that makes it, where it
can be read against the COBOL literal beside it.

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
33, at [irs/irs030.cbl:L645] `if w = 33`, then [:L651], [:L653] and [:L655].

This is NOT one of the twenty-two anomalies Agent Action Plan section 0.6.7
enumerates. It is a twenty-third, found while writing this module, and it
belongs in `docs/migration/anomaly-log.md` with `dal/acasirsub3_irs_dflt.py`
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
itself as the key. The bridge says so in its own comment:

    move  HV-DEF-ACS   to Def-Acs (HV-DEF-REC-KEY)  *> KEY = table position
                                              [common/irsdfltMT.cbl:L603]
    move  HV-DEF-VAT   to Def-Vat (HV-DEF-REC-KEY)  [:L604]
    move  HV-DEF-CODES to Def-Codes (HV-DEF-REC-KEY)  [:L605]

and in the other direction it loads the key from the loop subscript `A`:

    move     Def-Acs (A) to HV-DEF-ACS         [common/irsdfltMT.cbl:L633]
    move     zeros       to HV-DEF-ACS         [:L635]   (the else branch)
    move     WS-Key        to HV-DEF-REC-KEY   [:L639]

The host-variable group [common/irsdfltMT.cbl:L323-L327] declares it first of
four, `HV-DEF-REC-KEY PIC 9(03) COMP` at [:L324], and the schema carries it
as `DEF-REC-KEY tinyint(2) unsigned NOT NULL` with `PRIMARY KEY
(DEF-REC-KEY)` [mysql/ACASDB.sql:L190] and [:L194].

This is the SECOND bridge-only-column case in this package. The first is
`POST4-DAY`, `POST4-MONTH` and `POST4-YEAR` in `records/irs_posting.py`,
which Agent Action Plan section 0.1.1 uses to settle where field metadata
comes from: "A migration driven from the copybooks alone would silently omit
three columns of a posting table." This case is structurally worse. There the
bridge adds three derived columns to a row; here it turns ONE RECORD INTO UP
TO 33 ROWS. The two also differ in position: the IRS posting components are
interleaved at column ordinals 4, 5 and 6, whereas `DEF-REC-KEY` is
PREPENDED, at ordinal 1.

The maintainer describes the transformation himself, in the bridge's revision
history: "Changed for one Cobol File/Record to many table rows - irsdfltMT
and finalMT" [common/irsdfltMT.cbl:L137], repeated at
[common/irsdfltMT.scb:L137].

    the copybook holds   ONE record containing a 33-entry table
    the schema holds     UP TO 33 ROWS of a 4-column table

This module models the RECORD. It declares no key attribute, no row identity
and no row collection, because the copybook declares none;
`dal/acasirsub3_irs_dflt.py` owns the subscript-to-key mapping in both
directions. The dictionary keeps the bridge and column views of the key under
`IRSDFLT-REC.DEF-REC-KEY`, reachable through `loader.host_variable_for`,
`loader.column_for` and `loader.derivation_for`, and asking
`FieldDescriptor.from_dictionary_key` for it is refused on purpose - it has
no COBOL-side storage to describe.

ONE MORE THING ABOUT SUBSCRIPTS: COBOL OCCURS IS 1-BASED
========================================================
`Def-Acs (31)` is the THIRTY-FIRST entry, which in Python is index 30 of a
33-element sequence. That offset is real, it is easy to get wrong, and it is
deliberately NOT hidden here. There is no subscript accessor on either class,
no one-based helper and no mapping keyed by position: a reader of
`programs/irs030_posting.py` must see the conversion next to the COBOL
literal it comes from, where it can be checked. A helper here would move
thirty-odd such decisions out of sight of the source they answer to.

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
    01-name          Default-Record        [:L14] Default-Record      [:L8]
    Def-Group        occurs 33             [:L15] occurs 33           [:L9]
    Def-Acs          pic 9(4)v99 comp      [:L16] pic 9(5)           [:L10]
                     -> Decimal, scale 2          -> int, scale 0
    trailing filler  pic x(793)            [:L19] none
    record size      1024 bytes            [:L19] 264 bytes           [:L7]
    table            SYSDEFLT-REC                 IRSDFLT-REC
    DEF-ACS column   decimal(6,2) unsigned        decimal(5,0) unsigned
    handler          acas000, file key 2          acasirsub3
    bridge           dfltMT                       irsdfltMT
    module           records/system_dflt.py       records/irs_dflt.py
    class            SysDefaultRecord             WsIrsDefaultRecord

This is anomaly-A-21-class evidence - field-name collisions across copybooks
forcing qualified references - and it is why both classes carry a prefix the
COBOL `01`-name does not have. The two are never merged, never share a
descriptor, and this module imports nothing from `records/system_dflt.py`.

The dangerous confusion is the TYPE of `Def-Acs`: `int` here, `Decimal`
there. Take the wrong one and every IRS default account code changes value
silently. Three independent guards stand against it:

  * the dictionary key's left side is the TABLE name, `IRSDFLT-REC`, not the
    colliding `01`-name, so the two records cannot key to one entry;
  * the entries are obtained through `loader.entries_for_copybook_file`,
    which is scoped to `copybooks/irswsdflt.cob` by construction - note that
    `loader.entries_for_copybook_record("Default-Record")` returns ELEVEN
    entries spanning BOTH copybooks, and the loader's own docstring names
    this record as one of five whose name more than one copybook declares;
  * `_keys_by_cobol_name` asserts the declaring file of every entry it uses.

decimal(5,0) IS NOT A Decimal  (rule R-2)
=========================================
`Def-Acs` is an ACCOUNT CODE: `pic 9(5)`, unsigned zoned DISPLAY, five
digits, scale ZERO. Its Python carrier is `int`.

The column is spelled `DEF-ACS decimal(5,0) unsigned`
[mysql/ACASDB.sql:L191], and that spelling is a trap: a DECIMAL of scale zero
holds integers, so the SQL type name does not make the field a
`decimal.Decimal`. This module imports no arbitrary-precision numeric type at
all, because it has no monetary and no fractional field to hold - and it
holds no binary floating-point value either, which rule R-2 forbids outright.

The carrier is not typed by eye: it is `python_storage` as the generated
dictionary records it, INT. That also makes the type a GUARD, as noted above
- the GL sibling's `Def-Acs` is a scale-2 decimal, so a `Decimal` carrier
appearing here would mean the wrong record had been picked up.

BRIDGE DRIFT - THREE KINDS, ALL HANDED OVER UNADJUDICATED  (rule R-4)
=====================================================================
The bridge is not a transparent pipe. For this four-column table the three
layers disagree in three distinct ways, and this module records all three
without settling any of them:

1. A BRIDGE-ONLY KEY COLUMN, plus the one-record-to-many-rows transformation
   that produced it. Covered above.

2. STORAGE-CLASS DRIFT ON `Def-Acs`. The copybook declares zoned DISPLAY
   [copybooks/irswsdflt.cob:L10]; the host variable declares binary
   `PIC 9(05) COMP` [common/irsdfltMT.cbl:L325]; the column is DECIMAL
   [mysql/ACASDB.sql:L191]. Digits and scale survive intact at 5 and 0; the
   storage class does not. The dictionary states it in one sentence -
   "Storage class changes at the bridge: copybook declares DISPLAY, host
   variable declares COMP, column is DECIMAL" - and this module hands that
   sentence over untouched through `_DEF_ACS.drift()`, which passes
   `loader.drift_for("IRSDFLT-REC.DEF-ACS")` straight through. It applies no
   conversion; the bridge boundary is where a conversion belongs, and
   `dal/acasirsub3_irs_dflt.py` owns it.

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
does the work inline instead, inside the verb paragraphs themselves:

    unload, into the record   ba040-Process-Read-Next  [:L470-L616],
                              the moves at             [:L603-L606]
    load, out of the record   ba070-Process-Write      [:L617-L672],
                              the moves at             [:L633-L641]
    and again                 ba090-Process-Rewrite,   [:L685-L693]

which is why the dictionary's load and unload provenance for these fields
points at statement lines rather than at a paragraph name.

One statement in that path fixes the DEFAULT VALUES in this module:

    initialize Default-Record with filler.     [common/irsdfltMT.cbl:L543]

COBOL's INITIALIZE sets a numeric item to zero and an alphanumeric item to
spaces. So an unset entry is zeros and spaces, never absent - which is
exactly why all four columns can be declared NOT NULL with no column DEFAULT
[mysql/ACASDB.sql:L190-L193], and, in the words of Agent Action Plan section
0.6.2, why "the Python layer must default rather than omit".

Hence: `def_acs` defaults to `0`, and the two alphanumeric fields default to
SPACES OF THEIR DECLARED WIDTH - two and one - rather than to an empty string
and never to `None`. The widths come from the descriptors' own
`character_length`, so the defaults cannot drift from the copybook.

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
Agent Action Plan section 0.8.1 makes the ordering a directive rather than a
preference - the dictionary is generated from the bridge BEFORE record
definitions are written, and every Python field definition cites its entry,
"what prevents fields being transcribed by eye". Section 0.3.3 states the
effect: field metadata is derived, not transcribed.

So no picture clause, digit count, scale, sign or storage class is written by
hand in this file. Five keys are looked up, and NONE is guessed: they are
read back from `loader.entries_for_copybook_file("copybooks/irswsdflt.cob")`,
matching on each entry's own `copybook.name`.

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
copybook-only group items whose names the GL copybook also declares - that
one carries `#14` and `#15`, plus a `filler` this record does not have.

THE COUNT RECONCILIATION, which is worth stating because the numbers differ
on purpose:

    entries for table IRSDFLT-REC        4    (the four columns)
    fields on DefGroup                   3    (the three 05 items)
    the difference                       1    DEF-REC-KEY, at ordinal 1

Each descriptor's `cite()` hands back `loader.cite(<its key>)` - the compact
three-locator provenance line - and this module reimplements none of it. For
`Def-Acs` it reads:

    IRSDFLT-REC.DEF-ACS  copybook=copybooks/irswsdflt.cob:L10
    bridge=common/irsdfltMT.cbl:L325  column=mysql/ACASDB.sql:L191

`docs/migration/traceability.md` lifts the tables above; the field-level
mapping is mechanical rather than hand-kept, which is the whole point.

OPEN QUESTIONS FOR THE COMPILED ORACLE  (rule R-6)
==================================================
Two questions about this record cannot be settled by reading the frozen
source. Both belong in `docs/migration/ambiguity-resolutions.md`, and this
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

Determinism, which is the other half of rule R-6: this module reads no clock,
draws no unpredictable value, inspects no process environment and performs no
input or output of its own beyond the loader's lazy, cached read of the
generated dictionary. Field order is copybook declaration order. Collections
are tuples, so two imports in two processes produce identical state.

LAYERING: THIS IS A LEAF MODULE  (Agent Action Plan section 0.4.3)
==================================================================
The import contract grants a `records/*.py` module exactly two imports, "this
keeps the record layer a leaf":

    permitted    acas_posting.cobol.field         the descriptor type
                 acas_posting.dictionary.loader   the descriptor lookup
                 the standard library

Everything else is forbidden, and two of the prohibitions are live
temptations for this file in particular: `dal/acasirsub3_irs_dflt.py`, which
owns the subscript-to-key mapping described above, and
`programs/irs030_posting.py`, which owns the entry-31 and entry-32 selection.
Also forbidden: `cli`, the clock, the date module, the work-file module, the
rest of the `cobol` package, the dictionary generator, the compiled
comparison oracle in its sibling tree, and ANY other module of this package -
above all `records/system_dflt.py`, for the reason given above.

The reason is stated in section 0.4.3: the arithmetic test tier "imports only
`cobol` and `records` and touches no database, so it runs anywhere". One
import reaching into the data-access layer would drag a database driver into
that tier and break the promise for every test in it.

WHAT THIS MODULE DELIBERATELY DOES NOT HAVE
===========================================
Written down because each absence is a decision, and because the next reader
will be tempted by at least one of them:

    * no `def_rec_key` attribute - the copybook declares no key field
    * no row model, no row identity, no collection of rows
    * no subscript accessor, no one-based helper, no by-position mapping
    * no ceiling of thirty-two entries, no range check, no index refusal
    * no entry-31 or entry-32 constant, no VAT-account or control-account
      accessor, no selection or search helper
    * no storage-class conversion, and no arbitrary-precision numeric type
      for a scale-zero account code
    * no alias for the other spellings of a field name
    * no 88-level predicate - the copybook declares none
    * no construction hook, no padding step, no validation, no exception of
      its own; a value too wide for a field is the consuming layer's business
    * no schema definition of any kind, no object-relational mapping base,
      no declarative metadata, no DDL
    * no concurrency

The register of every reproduction site in this package is
`docs/migration/anomaly-log.md`; the arbitrations are in
`docs/migration/ambiguity-resolutions.md`.
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


# =============================================================================
#  THE ONE FROZEN NAME THIS MODULE IS SCOPED TO
# =============================================================================

# The declaring copybook. Every dictionary entry used below must come from
# this file and no other: `copybooks/wsdflt.cob` declares an 01 of the same
# name whose `Def-Acs` is a scale-2 decimal, and picking that one up would
# change every IRS default account code without changing a visible line of
# logic. See "TWO RECORDS ARE CALLED Default-Record" in the module docstring.
_COPYBOOK: Final[str] = "copybooks/irswsdflt.cob"


# =============================================================================
#  THE DICTIONARY KEYS, LOOKED UP RATHER THAN TYPED  (rule R-5)
# =============================================================================


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


# =============================================================================
#  THE RECORD LAYOUT
#
#  Two plain dataclasses, neither frozen. The defaults record is read into
#  WORKING STORAGE and amended there - the out-of-scope maintenance paths of
#  `irs/irs030.cbl` accept new values into it field by field, entry 33
#  included [irs/irs030.cbl:L651-L655] - so a frozen record could not hold
#  what the COBOL holds. `slots=True` on both, which costs nothing and makes
#  an attribute the copybook does not declare impossible to attach (rule R-3).
# =============================================================================


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
    either: `dal/acasirsub3_irs_dflt.py` owns the subscript-to-key mapping in
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
