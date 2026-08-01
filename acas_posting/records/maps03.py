"""The `maps03-ws` date-conversion interface record.

Fourteen bytes: ten characters of date text plus a signed 32-bit binary day
number. Declared at [copybooks/wsmaps03.cob:L6-L30] and brought into every
in-scope posting program by `copy "wsmaps03.cob"`.

This module DECLARES that record and does nothing else. It holds no date
logic, no arithmetic, no database access and no control flow. The six
dataclasses below are the layout, and every attribute's storage metadata is
looked up in the generated data dictionary rather than typed by hand.

THE FOLDER'S MANDATE
--------------------
Agent Action Plan section 0.4.1.3 gives this file its row, verbatim:

    `acas_posting/records/maps03.py` | CREATE | `copybooks/wsmaps03.cob` |
    The date-conversion interface block passed to the date module

and, for the folder, requires each module to be a CREATE from its copybook
that translates every 03/05 item into a dataclass attribute whose descriptor
is looked up in the generated dictionary, with the oddities of the source
preserved rather than repaired. Its shape comes from section 0.8.1, verbatim -
"Plain modules and dataclasses; no ORM entity layer" - and rule R-3 adds that
the record modules mirror their copybooks field for field with nothing added.

WHERE THE BEHAVIOUR LIVES - NOT HERE
------------------------------------
This record is the single parameter of the date module. Section 0.2.1.1 puts
`common/maps04.cbl` in scope as "the specification for all date conversion", a
189-line program that converts a 10-character UK date to and from a binary day
number, reached from each posting program through a thin wrapper section - for
example [sales/sl060.cbl:L1295]. Section 0.4.3 spells both translations:

    copy "wsmaps03.cob".            ->  from acas_posting.records.maps03
                                            import Maps03Ws
    call "maps04" using maps03-ws   ->  dates.maps04(maps03_ws)

Everything on the far side of that call belongs to `acas_posting/dates.py`,
which section 0.4.1.6 assigns it to: the separator replacement for ".", ","
and "-", the six-part reject test [common/maps04.cbl:L140-L146], the calendar
validity test [common/maps04.cbl:L153], the conversion to a day number counted
from 31/12/1600 [common/maps04.cbl:L167] with the remark that makes that
counting explicit [common/maps04.cbl:L39-L41], the reverse unpack
[common/maps04.cbl:L181-L186], and the UK / USA / International reformatting
the per-program wrapper sections perform - for example
[general/gl070.cbl:L573-L601].

None of that is reimplemented here, and nothing below reads a component out of
the date text or rebuilds the text from components. A second copy of
`acas_posting/dates.py`'s behaviour living in a record module is precisely the
divergence rule R-4 exists to prevent.

THE FOURTEEN BYTES
------------------
One storage item of ten characters, three alternative readings of it, then a
four-byte binary item. Offsets are 1-based, the way COBOL counts them:

    offset        1  2  3  4  5  6  7  8  9 10 | 11 12 13 14
    u-date        x  x  x  x  x  x  x  x  x  x |
      u-UK        d  d  /  m  m  /  c  c  y  y |
      u-USA       m  m  /  d  d  /  f  f  f  f |
      u-Intl      c  c  y  y  /  m  m  /  d  d |
    u-bin                                      |  b  b  b  b

Each reading's declared widths reconstruct the same ten characters:

    u-UK     u-days 2 + filler 1 + u-month 2 + filler 1
             + u-year (u-cc 2 + u-yy 2)                          = 10
    u-USA    u-usa-month 2 + filler 1 + u-usa-days 2
             + filler 1 + filler 4                               = 10
    u-Intl   u-intl-year (u-intl-cc 2 + u-intl-yy 2)
             + filler 1 + u-intl-month 2 + filler 1
             + u-intl-days 2                                     = 10

    record   u-date 10 + u-bin 4                                 = 14 bytes

The filler items are the date separators, and their differing positions are
the whole reason the three readings differ. The second and third readings were
added deliberately; the copybook's own note says so, verbatim
[copybooks/wsmaps03.cob:L5]: "Support for UK, USA, Intl formats".

THREE READINGS, ONE STORAGE - METADATA, NOT MACHINERY
-----------------------------------------------------
`u-UK`, `u-USA` and `u-Intl` each `redefines u-date`: three names for the same
ten bytes. Python has no storage aliasing, so the relationship travels as
metadata on the descriptors instead of being built as behaviour. All three
report `redefines == "u-date"`, taken from the dictionary entry the copybook
produced, and no `redefines` value appears here that the copybook does not
state.

What is deliberately absent, and why:

  * NO fourth reading that decides which of the three is in play. The three
    are equal declarations of one piece of storage; picking one would be an
    accounting decision taken inside a record module. Which form a run uses is
    the calling program's business, and `acas_posting/dates.py` is where that
    selection lives (section 0.4.1.6).
  * NO property that reads a component out of `u_date` or writes one back into
    it, and no synchronisation between `Maps03Ws` and the three reading
    classes. That behaviour is `acas_posting/dates.py`'s, entirely.
  * NO post-initialisation hook and no checking of any value. Rule R-3 forbids
    added validation, and this record must be able to hold exactly the
    malformed text the COBOL can hold - the two reject paths at
    [common/maps04.cbl:L146] and [common/maps04.cbl:L154] exist because it
    does.

THE ATTRIBUTE RULE, INCLUDING FILLER
------------------------------------
One rule decides whether a declared item becomes a dataclass attribute, and it
is applied uniformly across all six classes. What separates the two group cases
is whether the item occupies storage of its own or re-reads storage a sibling
already declared:

  * an elementary item that names a value  ->  a dataclass attribute on the
    class that declares it, plus its descriptor in that class's `FIELDS`
  * a subordinate group that is NOT a redefinition - `u-year` and
    `u-intl-year` - occupies its own run of bytes inside its parent, so it
    becomes a nested dataclass AND an attribute holding one instance of it
  * a group that IS a redefinition - `u-UK`, `u-USA`, `u-Intl` - re-reads
    bytes `u-date` already declares, so it becomes a dataclass but NO
    attribute. Three co-resident attributes would imply three separate pieces
    of storage, which is the opposite of what `redefines` means.
  * a FILLER  ->  its descriptor in `FIELDS` with `is_filler` true, and NO
    attribute

That yields exactly fourteen attributes for the fourteen items the copybook
names: `u_date` and `u_bin`; `u_days`, `u_month` and `u_year`; `u_cc` and
`u_yy`; `u_usa_month` and `u_usa_days`; `u_intl_year`, `u_intl_month` and
`u_intl_days`; `u_intl_cc` and `u_intl_yy`. Each is the mechanical snake_case
of its COBOL name.

FILLER gets no attribute deliberately. A COBOL FILLER names no value and no
statement anywhere can reference it, so giving it a Python attribute would add
an addressable name the frozen source does not declare - the one thing rule
R-3 rules out. Keeping its descriptor in `FIELDS` costs nothing: declaration
order stays intact, the separator bytes stay visible, and the width arithmetic
above still sums, which is what rule R-5 needs of it. All SEVEN fillers are
carried this way - [copybooks/wsmaps03.cob:L10], [:L12], [:L18], [:L20],
[:L21], [:L26] and [:L28].

CLASS NAMES AND THEIR COBOL ORIGINALS
-------------------------------------
Each name is the PascalCase of its COBOL group name with the hyphens removed.
The COBOL spellings are mixed-case in the source and are carried verbatim in
the comment beside every declaration below:

    Maps03Ws        01  maps03-ws.                [copybooks/wsmaps03.cob:L6]
    MapsUUk         03  u-UK redefines u-date.    [copybooks/wsmaps03.cob:L8]
    MapsUYear       05  u-year.                   [copybooks/wsmaps03.cob:L13]
    MapsUUsa        03  u-USA redefines u-date.   [copybooks/wsmaps03.cob:L16]
    MapsUIntl       03  u-Intl redefines u-date.  [copybooks/wsmaps03.cob:L22]
    MapsUIntlYear   05  u-intl-year.              [copybooks/wsmaps03.cob:L23]

`Maps03Ws` is not a free choice: section 0.4.3 writes out the import line
every consumer uses, so the plan fixes that name.

TWO COBOL DECLARATIONS OF THE SAME FOURTEEN BYTES (RULE R-4)
------------------------------------------------------------
The caller's copybook and the called program declare the same 14 bytes under
different names, with different structure, in different files. Both are real,
and neither is bent to fit the other here.

    [copybooks/wsmaps03.cob:L6-L30]   [common/maps04.cbl:L109-L120]
    01  maps03-ws.                    01  Mapa03-WS.
      03  u-date  pic x(10).            03  A-Date  pic x(10).
      03  u-UK  redefines u-date.       03  filler  redefines A-Date.
        05  u-days   pic 99.              05  A-Days   pic 99.
        05  filler   pic x.               05  filler   pic x.
        05  u-month  pic 99.              05  A-Month  pic 99.
        05  filler   pic x.               05  filler   pic x.
        05  u-year.                       05  A-CCYY   pic 9(4).
          07  u-cc   pic 99.              05  filler redefines A-CCYY.
          07  u-yy   pic 99.                07  A-CC    pic 99.
      03  u-USA  redefines u-date.          07  A-Year  pic 99.
        ... four more items             03  A-Bin  binary-long.
      03  u-Intl  redefines u-date.
        ... five more items
      03  u-bin   binary-long.

Three differences, all preserved:

  * NAMES. `maps03-ws` with `u-*` fields in the copybook; `Mapa03-WS` with
    `A-*` fields in the program's LINKAGE SECTION, which is what
    `procedure division using Mapa03-WS.` binds [common/maps04.cbl:L122].
    Note also that the program `maps04` names its own record after maps0*3*.
  * STRUCTURE, first difference. The program declares ONE reading and it is
    anonymous - `03 filler redefines A-Date.` [common/maps04.cbl:L111] - so it
    sees neither the USA nor the International reading at all. The three named
    readings exist only in the caller's copybook.
  * STRUCTURE, second difference. The copybook splits century from year with a
    GROUP: `05 u-year.` containing `07 u-cc` and `07 u-yy`
    [copybooks/wsmaps03.cob:L13-L15]. The program splits it with a REDEFINES
    of a four-digit item: `05 A-CCYY pic 9(4)` redefined into `07 A-CC` and
    `07 A-Year` [common/maps04.cbl:L116-L119]. The same four bytes, declared
    two different ways.

This module models the CALLER's copybook - the `u-*` names, all three readings
- because `copy "wsmaps03.cob"` is what every in-scope program writes. It
carries no `Mapa03Ws` alias, no `A-*` name and nothing merged in from
`acas_posting/dates.py`. Rule R-4: a defect reproduced is correct and a defect
fixed is a failure, and two disagreeing declarations of one record are
evidence, not noise.

ANOMALY #16 - WHAT `u-bin` HOLDS AFTER A REJECTED DATE (RULES R-4, R-6)
-----------------------------------------------------------------------
The date module documents one contract and implements another. Its own comment
says errors come back as zero, verbatim [common/maps04.cbl:L163]:

    "Date errors returned as A-Bin equal zero"

and again at [common/maps04.cbl:L125]: "if dd/mm/ccyy is bad A-Bin = zero".
Both reject paths leave the binary item untouched, though: the six-part text
test transfers straight to the exit [common/maps04.cbl:L146], the calendar
test does the same [common/maps04.cbl:L154], and the exit itself performs no
store at all [common/maps04.cbl:L188-L189]. The documented zero holds only
because the known caller writes it first - `move zero to u-bin`
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78], immediately before
`call "maps04" using maps03-ws` [copybooks/Proc-ACAS-Mapser-RDB.cob:L79].

Section 0.6.8 keeps this OPEN: not every in-scope caller has been shown to
pre-zero, so what each one observes is arbitrated by the compiled program and
written up in `docs/migration/ambiguity-resolutions.md` (rule R-6). Nothing
here settles it, and nothing here repairs it.

TRACEABILITY - EVERY FIELD FROM THE DICTIONARY (RULE R-5)
---------------------------------------------------------
Section 0.8.1 is a directive and not a preference, verbatim: "The dictionary is
generated from the bridge before record definitions are written, and every
Python field definition cites its entry. This ordering is a directive, not a
preference - it is what prevents fields being transcribed by eye." Section
0.3.3 states the payoff: field metadata is "derived, not transcribed".

The dictionary was probed before a line of this module was written, and it
covers this record completely. `entries_for_copybook_record("maps03-ws")`
returns 25 entries in copybook declaration order, L6 through L30: the 01
group, the two storage items, the three readings, the two nested year groups,
the ten two-digit components and all seven fillers. Every descriptor below is
therefore built by `FieldDescriptor.from_dictionary_key`, the principal path,
and NOT ONE storage component is stated by hand - no picture, no digit count,
no scale, no sign position and no width appears as a literal anywhere below.

Keys are `<COPYBOOK-RECORD>.<FIELD-NAME>`, both halves verbatim from the
frozen source. So the record half is the LOWER-case `maps03-ws` the copybook
writes, and the field half keeps its own mixed case - `maps03-ws.u-UK`,
`maps03-ws.u-Intl`. A FILLER, which repeats, is keyed by its declaration line:
`maps03-ws.filler#21`. Lookup is exact and case-sensitive, so an upper-cased
key such as `MAPS03-WS.U-BIN` matches nothing at all; that was checked, not
assumed. A bare field name is never used as a key.

This record reaches NO MySQL table and no bridge host variable, which is
correct rather than a gap: it is a call-interface block and appears nowhere in
the entity-to-table spine of section 0.2.1.1. Its provenance is one-sided by
design, and `FieldDescriptor.cite` says so out loud:

    maps03-ws.u-bin  copybook=copybooks/wsmaps03.cob:L30  bridge=absent
    column=absent

That string comes from `acas_posting.dictionary.loader.cite`, surfaced through
the descriptor and never reimplemented here.

Each class publishes its own declared items as a `FIELDS` tuple, element 0
being the class's own group header, in copybook declaration order. A nested or
redefining group appears twice on purpose - once as a child in its parent's
`FIELDS`, which keeps the parent's declaration order and width arithmetic
whole, and once as element 0 of its own class - and the union of the six
tuples is exactly the dictionary's 25 keys, with nothing added and nothing
dropped.

The classes below follow copybook declaration order with one mechanical
adjustment: a nested group's class is hoisted immediately above the class that
contains it, because a dataclass default is built by name at class-creation
time and Python needs the name to exist first. So `MapsUYear` precedes
`MapsUUk`, and `MapsUIntlYear` precedes `MapsUIntl`. Nothing else is reordered.

TYPE DISCIPLINE (RULE R-2)
--------------------------
    u-date          pic x(10)     ->  str
    the ten `pic 99` components   ->  int  (DISPLAY, 2 digits, no fraction)
    u-bin           binary-long   ->  int  (signed 32-bit,
                                            -2147483648 .. 2147483647)

`u-bin` being an `int` is not a shortcut. It counts whole days, so it has no
fractional part to carry, and any other carrier would invite fractional-day
arithmetic that COBOL cannot express. No accounting value passes through a
binary floating-point type anywhere in this migration; this record holds no
money at all, so no exact-decimal carrier is needed here and none is imported.

One derived detail is worth stating exactly, because it is the kind of value
that gets asserted from habit rather than read. `u-bin` carries NO picture, NO
digit count and NO scale - the copybook declares `binary-long` on the field
itself and states no PICTURE clause [copybooks/wsmaps03.cob:L30], so the
dictionary reports all three as absent rather than as zero. Its whole-number
nature travels on its usage instead: BINARY-LONG, `python_storage` INT, a
four-byte width and an integral value domain. Writing a scale of zero here
would be inventing a value the frozen source does not state, which is exactly
what section 0.3.3's "derived, not transcribed" rules out. The ten `pic 99`
components DO carry a picture, and their digit count and scale come from it.

LAYERING - A LEAF MODULE (SECTION 0.4.3)
----------------------------------------
    MAY import       the standard library, `acas_posting.cobol.field`,
                     `acas_posting.dictionary.loader`
    MUST NOT import  anything else - "this keeps the record layer a leaf"

One of the two permitted package imports is enough and only that one is taken:
`FieldDescriptor`, because every field is dictionary-backed and
`FieldDescriptor.cite` already surfaces the loader's provenance string.

In particular this module does NOT import `acas_posting.dates`. The edge runs
one way - the date module consumes this record, and this record knows nothing
about the date module - so a leaf that imported it would close a cycle and
drag date logic into the record layer. Nor does it import any other record
module, any data-access module, the program modules, the entry points, the
clock or the comparison oracle in its sibling tree. Nothing here starts an
external process, loads a shared library or reaches outside Python, so the
migrated cycle runs on a host with no COBOL compiler and no COBOL runtime
present (rule R-1).

DETERMINISM (RULE R-6)
----------------------
Section 0.1.1 records that "every one of the in-scope posting programs contains
zero clock reads; the date arrives purely through linkage". THIS RECORD IS THAT
LINKAGE. The one clock read in the whole call chain sits in the menu shell -
`move function current-date to wse-date-block`
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72] - and the migration pins its two
observables at the entry-point boundary, in `acas_posting/clock.py`. So there
is no clock here, no unpredictable value, no process-environment read and no
filesystem walk: a date reaches these fields only because a caller put it
there. Dataclass field order follows copybook declaration order, every fixed
collection is a tuple, and execution stays strictly sequential with no
concurrency introduced.

The one thing read at import is the generated dictionary, through the loader's
lazy cached read, while the classes below are being defined - which is how
every record module in this package obtains its metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[tuple[str, ...]] = (
    # The 01-level record first, then its readings in name order. Sorted with
    # `sorted()` so the order is mechanical rather than a matter of taste:
    # "Maps03Ws" precedes the "MapsU..." names because "0" sorts before "U".
    "Maps03Ws",
    "MapsUIntl",
    "MapsUIntlYear",
    "MapsUUk",
    "MapsUUsa",
    "MapsUYear",
)


# =============================================================================
#  THE DICTIONARY LOOKUP  (RULE R-5)
# =============================================================================

# The 01-level record name, verbatim from [copybooks/wsmaps03.cob:L6] - LOWER
# case, because that is how the copybook writes it and dictionary keys carry
# names exactly as the frozen source spells them. It is the record half of
# every key below, and the argument
# `acas_posting.dictionary.loader.entries_for_copybook_record` takes.
_COPYBOOK_RECORD: Final[str] = "maps03-ws"


def _descriptor(field_name: str) -> FieldDescriptor:
    """Return the dictionary-backed descriptor for one field of this record.

    Composes the qualified key and delegates. It holds no metadata of its own,
    which is the whole point: every storage component comes from the generated
    dictionary (rule R-5), and a bare field name is never used as a key.

    Args:
        field_name: The field's COBOL name verbatim - `"u-date"`, `"u-UK"`,
            `"u-intl-days"` - or `"filler#<line>"` for one of the seven
            fillers, which repeat and are therefore keyed by the line that
            declares them.

    Returns:
        That field's descriptor, carrying both its dictionary key and its
        `copybooks/wsmaps03.cob:L<n>` locator as provenance. Memoised by
        `FieldDescriptor.from_dictionary_key`, so a repeated lookup of one key
        returns the same frozen object.
    """
    return FieldDescriptor.from_dictionary_key(
        f"{_COPYBOOK_RECORD}.{field_name}"
    )


# `u-date`'s declared character width, taken from its own descriptor rather
# than typed here [copybooks/wsmaps03.cob:L7]. It gives a freshly built record
# its declared text width instead of an empty string. Note what that starting
# value is NOT: `maps03-ws` is a LINKAGE item in the date module
# [common/maps04.cbl:L102-L109], so at run time the caller's own storage
# supplies the content and this value is never what the date module reads.
_DATE_TEXT_WIDTH: Final[int] = _descriptor("u-date").byte_length


# =============================================================================
#  THE RECORD  (Agent Action Plan section 0.4.3 fixes the class name)
# =============================================================================


@dataclass(slots=True)
class Maps03Ws:
    """`01  maps03-ws.` [copybooks/wsmaps03.cob:L6] - the date record.

    The record every in-scope posting program obtains by `copy "wsmaps03.cob"`
    and hands over by `call "maps04" using maps03-ws`. Fourteen bytes: ten
    characters of date text, then a four-byte binary day number. The date
    module declares the same fourteen bytes as `Mapa03-WS` with `A-*` field
    names [common/maps04.cbl:L109-L120]; see this module's docstring for that
    divergence, which is recorded and not harmonised (rule R-4).

    Only two of the five items the `01` group declares hold storage of their
    own. The other three - `u-UK`, `u-USA` and `u-Intl` - each `redefines
    u-date`, so they are alternative readings of the ten characters `u_date`
    already holds; they are modelled by `MapsUUk`, `MapsUUsa` and `MapsUIntl`
    and are attributes of nothing. All five appear in `FIELDS`, in declaration
    order.

    MUTABLE, and not as a matter of style. A COBOL linkage record is passed by
    reference and the date module writes into it selectively - which is exactly
    what anomaly #16 is about. A frozen record, or an entry point that returned
    a new object, would hide the absence of a write behind an apparently fresh
    value. There is no post-initialisation hook and no checking of any value
    (rule R-3): this record must be able to hold the malformed text the COBOL
    can hold.

    Attributes:
        u_date: `u-date pic x(10)` [copybooks/wsmaps03.cob:L7]. The date text,
            ten characters. Which of the three readings applies to a given
            value is the calling program's business; `acas_posting/dates.py`
            owns every conversion (section 0.4.1.6).
        u_bin: `u-bin binary-long` [copybooks/wsmaps03.cob:L30]. The binary day
            number - a signed 32-bit integer, hence a Python `int` and never a
            binary floating-point value (rule R-2). Its value after a REJECTED
            date is an open question; see the note on the attribute below.
    """

    #  Element 0 is the `01` group header itself, then the five items it
    #  declares, in copybook declaration order. `u-UK`, `u-USA` and `u-Intl`
    #  each carry `redefines == "u-date"`, straight from the dictionary entry
    #  the copybook produced; nothing here states a `redefines` that the
    #  copybook does not declare.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("maps03-ws"),  # 01 maps03-ws.               [:L6]  group
        _descriptor("u-date"),  # 03 u-date  pic x(10)           [:L7]
        _descriptor("u-UK"),  # 03 u-UK    redefines u-date      [:L8]  group
        _descriptor("u-USA"),  # 03 u-USA   redefines u-date     [:L16] group
        _descriptor("u-Intl"),  # 03 u-Intl  redefines u-date    [:L22] group
        _descriptor("u-bin"),  # 03 u-bin   binary-long          [:L30]
    )

    # u-date  pic x(10)  [copybooks/wsmaps03.cob:L7]
    u_date: str = " " * _DATE_TEXT_WIDTH

    # u-bin   binary-long  [copybooks/wsmaps03.cob:L30]
    #
    #  ANOMALY #16, RECORDED HERE AND SETTLED NOWHERE (rules R-4, R-6). The
    #  date module's own comments promise that a bad date comes back as zero -
    #  "Date errors returned as A-Bin equal zero" [common/maps04.cbl:L163], and
    #  "if dd/mm/ccyy is bad A-Bin = zero" [common/maps04.cbl:L125] - but
    #  neither reject path writes this field: the six-part text test transfers
    #  to the exit [common/maps04.cbl:L146], the calendar test does the same
    #  [common/maps04.cbl:L154], and the exit stores nothing
    #  [common/maps04.cbl:L188-L189]. The promise holds only because the known
    #  caller writes the zero itself, `move zero to u-bin`
    #  [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], one line before the
    #  `call "maps04" using maps03-ws` at
    #  [copybooks/Proc-ACAS-Mapser-RDB.cob:L79].
    #
    #  So AFTER A REJECTED DATE THIS FIELD IS NOT GUARANTEED TO BE ZERO: it
    #  holds whatever it held before the call. Section 0.6.8 lists that as an
    #  open question for the compiled program to arbitrate, and the answer is
    #  written up in `docs/migration/ambiguity-resolutions.md`. The zero below
    #  is a starting value that lets the record be built, nothing more - it is
    #  not a pre-zeroing of the field on any caller's behalf, and it makes no
    #  claim whatever about the value after a call.
    u_bin: int = 0


# =============================================================================
#  THE UK READING  -  u-UK redefines u-date  -  DD/MM/CCYY
# =============================================================================
#  `MapsUYear` is hoisted above `MapsUUk`, which declares it: a dataclass
#  default is built by name at class-creation time, so the name has to exist
#  first. Copybook order is otherwise untouched.
# =============================================================================


@dataclass(slots=True)
class MapsUYear:
    """`05  u-year.` [copybooks/wsmaps03.cob:L13] - century and year, CCYY.

    A group of two two-digit items inside the UK reading, occupying offsets 7
    to 10 of the date text. The class name is the PascalCase of the COBOL group
    name `u-year` with the hyphen removed.

    A GROUP is how the copybook splits these four bytes. The date module splits
    the same four bytes differently, with `05 A-CCYY pic 9(4)` redefined into
    `07 A-CC` and `07 A-Year` [common/maps04.cbl:L116-L119]. Both declarations
    stand as written; see this module's docstring (rule R-4).

    Declared widths: u-cc 2 + u-yy 2 = 4 characters.

    Attributes:
        u_cc: `u-cc pic 99` [copybooks/wsmaps03.cob:L14]. The century part.
        u_yy: `u-yy pic 99` [copybooks/wsmaps03.cob:L15]. The year part.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-year"),  # 05 u-year                      [:L13] group
        _descriptor("u-cc"),  # 07 u-cc  pic 99                  [:L14]
        _descriptor("u-yy"),  # 07 u-yy  pic 99                  [:L15]
    )

    # u-cc  pic 99  [copybooks/wsmaps03.cob:L14]
    u_cc: int = 0

    # u-yy  pic 99  [copybooks/wsmaps03.cob:L15]
    u_yy: int = 0


@dataclass(slots=True)
class MapsUUk:
    """`03  u-UK redefines u-date.` [copybooks/wsmaps03.cob:L8] - DD/MM/CCYY.

    The UK reading of the ten characters `Maps03Ws.u_date` holds. The class
    name is the PascalCase of the COBOL group name `u-UK` with the hyphen
    removed; the mixed-case COBOL spelling is kept verbatim in the comments.

    This is the one reading the date module itself declares - anonymously, as
    `03 filler redefines A-Date.` [common/maps04.cbl:L111] - so it is the
    reading that program's checks and conversion work in. The other two exist
    only in the caller's copybook.

    Declared widths: u-days 2 + filler 1 + u-month 2 + filler 1
    + u-year (u-cc 2 + u-yy 2) = 10 characters.

    Real callers write these components rather than the whole text: the menu
    shell moves the year, month and day of the run date into `u-year`,
    `u-month` and `u-days` [copybooks/Proc-ACAS-Mapser-RDB.cob:L74-L76], after
    seeding the text with "00/00/0000"
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L73]. The two `filler` items at L10
    and L12 are the "/" separators and get no attribute, because no COBOL
    statement can name a FILLER.

    Attributes:
        u_days: `u-days pic 99` [copybooks/wsmaps03.cob:L9]. Day of month, at
            offsets 1 to 2.
        u_month: `u-month pic 99` [copybooks/wsmaps03.cob:L11]. Month, at
            offsets 4 to 5.
        u_year: `u-year` [copybooks/wsmaps03.cob:L13]. The century-and-year
            group at offsets 7 to 10, held as one `MapsUYear`. It is a group
            and not an elementary item, so it is a nested record here rather
            than a number - and that is one half of the structural divergence
            this module's docstring records, the date module declaring the same
            four bytes as `A-CCYY pic 9(4)` redefined into `A-CC` and `A-Year`
            [common/maps04.cbl:L116-L119].
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-UK"),  # 03 u-UK  redefines u-date        [:L8]  group
        _descriptor("u-days"),  # 05 u-days   pic 99             [:L9]
        _descriptor("filler#10"),  # 05 filler pic x             [:L10] "/"
        _descriptor("u-month"),  # 05 u-month  pic 99            [:L11]
        _descriptor("filler#12"),  # 05 filler pic x             [:L12] "/"
        _descriptor("u-year"),  # 05 u-year                      [:L13] group
    )

    # u-days   pic 99  [copybooks/wsmaps03.cob:L9]
    u_days: int = 0

    # u-month  pic 99  [copybooks/wsmaps03.cob:L11]
    u_month: int = 0

    # u-year           [copybooks/wsmaps03.cob:L13]  - a GROUP, and not a
    # redefinition: it occupies its own four bytes inside this reading, so it
    # is both a nested record and an attribute. Built per instance by
    # `default_factory`, so two records never share one nested group.
    u_year: MapsUYear = field(default_factory=MapsUYear)


# =============================================================================
#  THE USA READING  -  u-USA redefines u-date  -  MM/DD
# =============================================================================


@dataclass(slots=True)
class MapsUUsa:
    """`03  u-USA redefines u-date.` [copybooks/wsmaps03.cob:L16] - MM/DD.

    The USA reading of the same ten characters: month first, then day. The
    class name is the PascalCase of the COBOL group name `u-USA` with the
    hyphen removed.

    Declared widths: u-usa-month 2 + filler 1 + u-usa-days 2 + filler 1
    + filler 4 = 10 characters.

    Note the shape of that arithmetic. This reading names only TWO components
    and then covers the remaining four characters with a single unnamed item,
    `05 filler pic x(4).` [copybooks/wsmaps03.cob:L21] - so the century and
    year bytes are reachable through the UK and International readings but not
    through this one. That is what the copybook declares and it stands as
    declared. Three of this reading's five subordinate items are FILLER and so
    have no attribute; only the two named components do.

    Attributes:
        u_usa_month: `u-usa-month pic 99` [copybooks/wsmaps03.cob:L17]. Month,
            at offsets 1 to 2 - where the UK reading has the day.
        u_usa_days: `u-usa-days pic 99` [copybooks/wsmaps03.cob:L19]. Day of
            month, at offsets 4 to 5 - where the UK reading has the month.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-USA"),  # 03 u-USA redefines u-date       [:L16] group
        _descriptor("u-usa-month"),  # 05 u-usa-month pic 99     [:L17]
        _descriptor("filler#18"),  # 05 filler pic x             [:L18] "/"
        _descriptor("u-usa-days"),  # 05 u-usa-days  pic 99      [:L19]
        _descriptor("filler#20"),  # 05 filler pic x             [:L20] "/"
        _descriptor("filler#21"),  # 05 filler pic x(4)          [:L21] tail
    )

    # u-usa-month  pic 99  [copybooks/wsmaps03.cob:L17]
    u_usa_month: int = 0

    # u-usa-days   pic 99  [copybooks/wsmaps03.cob:L19]
    u_usa_days: int = 0


# =============================================================================
#  THE INTERNATIONAL READING  -  u-Intl redefines u-date  -  CCYY/MM/DD
# =============================================================================
#  `MapsUIntlYear` is hoisted above `MapsUIntl` for the same reason `MapsUYear`
#  is hoisted above `MapsUUk`.
# =============================================================================


@dataclass(slots=True)
class MapsUIntlYear:
    """`05  u-intl-year.` [copybooks/wsmaps03.cob:L23] - CCYY, 1 to 4.

    A group of two two-digit items inside the International reading, occupying
    offsets 1 to 4 of the date text - the same CCYY the UK reading places at
    offsets 7 to 10. The class name is the PascalCase of the COBOL group name
    `u-intl-year` with the hyphens removed.

    Declared widths: u-intl-cc 2 + u-intl-yy 2 = 4 characters.

    Attributes:
        u_intl_cc: `u-intl-cc pic 99` [copybooks/wsmaps03.cob:L24]. Century.
        u_intl_yy: `u-intl-yy pic 99` [copybooks/wsmaps03.cob:L25]. Year.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-intl-year"),  # 05 u-intl-year            [:L23] group
        _descriptor("u-intl-cc"),  # 07 u-intl-cc  pic 99        [:L24]
        _descriptor("u-intl-yy"),  # 07 u-intl-yy  pic 99        [:L25]
    )

    # u-intl-cc  pic 99  [copybooks/wsmaps03.cob:L24]
    u_intl_cc: int = 0

    # u-intl-yy  pic 99  [copybooks/wsmaps03.cob:L25]
    u_intl_yy: int = 0


@dataclass(slots=True)
class MapsUIntl:
    """`03  u-Intl redefines u-date.` [copybooks/wsmaps03.cob:L22].

    The CCYY/MM/DD reading of the same ten characters: century and year
    first, then month, then day. The class name is the PascalCase of the COBOL
    group name `u-Intl` with the hyphen removed.

    Declared widths: u-intl-year (u-intl-cc 2 + u-intl-yy 2) + filler 1
    + u-intl-month 2 + filler 1 + u-intl-days 2 = 10 characters.

    This reading leads with its group rather than trailing it, which is why its
    separators fall at offsets 5 and 8 instead of 3 and 6. The two `filler`
    items at L26 and L28 are those separators and get no attribute.

    Attributes:
        u_intl_year: `u-intl-year` [copybooks/wsmaps03.cob:L23]. The
            century-and-year group at offsets 1 to 4, held as one
            `MapsUIntlYear`. A group and not an elementary item, so a nested
            record here rather than a number.
        u_intl_month: `u-intl-month pic 99` [copybooks/wsmaps03.cob:L27].
            Month, at offsets 6 to 7.
        u_intl_days: `u-intl-days pic 99` [copybooks/wsmaps03.cob:L29]. Day of
            month, at offsets 9 to 10.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-Intl"),  # 03 u-Intl redefines u-date     [:L22] group
        _descriptor("u-intl-year"),  # 05 u-intl-year            [:L23] group
        _descriptor("filler#26"),  # 05 filler pic x             [:L26] "/"
        _descriptor("u-intl-month"),  # 05 u-intl-month pic 99    [:L27]
        _descriptor("filler#28"),  # 05 filler pic x             [:L28] "/"
        _descriptor("u-intl-days"),  # 05 u-intl-days  pic 99    [:L29]
    )

    # u-intl-year           [copybooks/wsmaps03.cob:L23]  - a GROUP, and not a
    # redefinition: its four bytes are its own inside this reading. Built per
    # instance by `default_factory`, as `MapsUUk.u_year` is.
    u_intl_year: MapsUIntlYear = field(default_factory=MapsUIntlYear)

    # u-intl-month  pic 99  [copybooks/wsmaps03.cob:L27]
    u_intl_month: int = 0

    # u-intl-days   pic 99  [copybooks/wsmaps03.cob:L29]
    u_intl_days: int = 0
