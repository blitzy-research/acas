"""The `maps03-ws` date-conversion interface record [copybooks/wsmaps03.cob:L6-L30].

Fourteen bytes: ten characters of date text plus a signed 32-bit binary day
number. This is the block every caller of the date module fills in and reads back,
so its layout is the whole interface between a program and
`acas_posting.dates`.

The UK redefine over the text field is load-bearing - `u-days` at 1:2, a `/` at
3, `u-month` at 4:2, a `/` at 6 and `u-year` at 7:4
[copybooks/wsmaps03.cob:L8-L15] - because the conversion writes only the digit
positions and relies on the separators already being there.

WHERE THE BEHAVIOUR LIVES - NOT HERE
------------------------------------
This record is the single parameter of the date module. Section 0.2.1.1 puts
`common/maps04.cbl` in scope as "the specification for all date conversion", a
189-line program that converts a 10-character UK date to and from a binary day
number, reached from each posting program through a thin wrapper section - for
example [sales/sl060.cbl:L1295]. Section 0.4.3 spells both translations::

    copy "wsmaps03.cob".            ->  from acas_posting.records.maps03
                                            import Maps03Ws
    call "maps04" using maps03-ws   ->  dates.maps04(maps03_ws)

Everything on the far side of that call belongs to `acas_posting/dates.py`,
which section 0.4.1.6 assigns it to: the separator replacement for ".", ","
and "-", the six-part reject test [common/maps04.cbl:L140-L146], the calendar
validity test [:L153], the conversion to a day number counted from 31/12/1600
[:L167] with the remark that makes that counting explicit [:L39-L41], the
reverse unpack [:L181-L186], and the UK / USA / International reformatting the
per-program wrapper sections perform - for example [general/gl070.cbl:L573-
L601]. None of that is reimplemented here.

The line this module draws is between LAYOUT and LOGIC, and it falls where the
copybook puts it. `u-UK`, `u-USA` and `u-Intl` each `redefines u-date`, so
ADDRESSING a component - the two bytes `u-days` names, the four `u-year` names -
is a declared property of this record and is reproduced below. Deciding which
reading applies, normalising a separator, judging a date, counting days from the
1600 epoch and unpacking a day number back into text are CONVERSION, and every
one of them stays in `acas_posting/dates.py`. A second copy of that module's
conversion living in a record module is precisely the divergence rule R-4 exists
to prevent. A record that could not address its own redefinitions is a different
failure, and was one: the date module grew a second class of this very name to
supply what was missing here, so one dictionary-covered linkage area was
described twice, the second time without provenance (rule R-5).

THE FOURTEEN BYTES
------------------
One storage item of ten characters, three alternative readings of it, then a
four-byte binary item. Offsets are 1-based, the way COBOL counts them::

    offset        1  2  3  4  5  6  7  8  9 10 | 11 12 13 14
    u-date        x  x  x  x  x  x  x  x  x  x |
      u-UK        d  d  /  m  m  /  c  c  y  y |
      u-USA       m  m  /  d  d  /  f  f  f  f |
      u-Intl      c  c  y  y  /  m  m  /  d  d |
    u-bin                                      |  b  b  b  b

Each reading's declared widths reconstruct the same ten characters: `u-UK` is
u-days 2 + filler 1 + u-month 2 + filler 1 + u-year (u-cc 2 + u-yy 2); `u-USA`
is u-usa-month 2 + filler 1 + u-usa-days 2 + filler 1 + filler 4; `u-Intl` is
u-intl-year (u-intl-cc 2 + u-intl-yy 2) + filler 1 + u-intl-month 2 + filler 1
+ u-intl-days 2. So u-date 10 + u-bin 4 = 14 bytes.

The filler items are the date separators, and their differing positions are the
whole reason the three readings differ. The second and third readings were
added deliberately; the copybook's own note says so, verbatim
[copybooks/wsmaps03.cob:L5]: "Support for UK, USA, Intl formats".

THREE READINGS, ONE STORAGE - METADATA AND ADDRESSING
-----------------------------------------------------
`u-UK`, `u-USA` and `u-Intl` each `redefines u-date`: three names for the same
ten bytes. That one fact is carried two ways here, because it has two
consequences.

As METADATA: all three descriptors report `redefines == "u-date"`, taken from
the dictionary entry the copybook produced, and no `redefines` value appears
here that the copybook does not state. Each subordinate component keeps its own
declared picture, digit count and scale on its own descriptor, in the `FIELDS`
tuple of the class that declares it.

As ADDRESSING: Python has no storage aliasing, so `Maps03Ws` publishes one view
per named component over the ten characters `u_date` holds, each reading and
writing only its own offsets. `record.u_days = "21"` writes offsets 1 and 2 and
leaves the separators standing, exactly as `move 21 to u-days` does. That is
what callers of the date module manipulate - the menu shell writes the run date
one component at a time [copybooks/Proc-ACAS-Mapser-RDB.cob:L74-L76] - and what
the date module's own six-part test reads [common/maps04.cbl:L140-L146].

What is deliberately absent, and why:

  * NO fourth reading that decides which of the three is in play. The three
    are equal declarations of one piece of storage; picking one would be an
    accounting decision taken inside a record module. Which form a run uses is
    the calling program's business, and `acas_posting/dates.py` is where that
    selection lives (section 0.4.1.6).
  * NO synchronisation between `Maps03Ws` and the three reading classes. The
    views on the record address `u_date` directly; the reading classes carry
    the copybook's declaration structure and their own independent attributes.
    Leaving the two unlinked is deliberate - a COBOL redefinition has ONE piece
    of storage, and `u-date` is it.
  * NO conversion on any view. A view moves characters and does nothing else:
    it does not parse, validate, renumber, zero-pad, choose a reading or touch
    `u_bin`. All of that is `acas_posting/dates.py`'s, entirely
    (section 0.4.1.6).
  * NO post-initialisation hook and no checking of any value. Rule R-3 forbids
    added validation, and this record must be able to hold exactly the
    malformed text the COBOL can hold - the two reject paths at
    [common/maps04.cbl:L146] and [:L154] exist because it does.

THE ATTRIBUTE RULE, INCLUDING FILLER
------------------------------------
One rule decides whether a declared item becomes a dataclass attribute, applied
uniformly across all six classes. What separates the two group cases is whether
the item occupies storage of its own or re-reads storage a sibling declared:

  * an elementary item that names a value  ->  a dataclass attribute on the
    class that declares it, plus its descriptor in that class's `FIELDS`
  * a subordinate group that is NOT a redefinition - `u-year` and
    `u-intl-year` - occupies its own run of bytes inside its parent, so it
    becomes a nested dataclass AND an attribute holding one instance of it
  * a group that IS a redefinition - `u-UK`, `u-USA`, `u-Intl` - re-reads bytes
    `u-date` already declares, so it becomes a dataclass but NO attribute.
    Three co-resident attributes would imply three separate pieces of storage,
    the opposite of what `redefines` means.
  * a FILLER  ->  its descriptor in `FIELDS` with `is_filler` true, and NO
    attribute

That yields exactly fourteen attributes for the fourteen items the copybook
names: `u_date` and `u_bin`; `u_days`, `u_month`, `u_year`; `u_cc`, `u_yy`;
`u_usa_month`, `u_usa_days`; `u_intl_year`, `u_intl_month`, `u_intl_days`;
`u_intl_cc`, `u_intl_yy`. Each is the mechanical snake_case of its COBOL name.

Twelve of those names appear a SECOND time, as views on `Maps03Ws` itself -
every component of the three readings, that is, all fourteen less `u_date` and
`u_bin`, which are storage in their own right. A view is the addressing of the
redefinition described above and declared on the record below; the attribute of
the same name on `MapsUUk`, `MapsUUsa`, `MapsUIntl`, `MapsUYear` or
`MapsUIntlYear` is that class's mirror of the copybook declaration. The two are
not linked and are not meant to be: the record's ten characters are the only
storage the copybook declares for any of them.

FILLER gets no attribute deliberately. A COBOL FILLER names no value and no
statement anywhere can reference it, so giving it a Python attribute would add
an addressable name the frozen source does not declare - the one thing R-3
rules out. Keeping its descriptor in `FIELDS` costs nothing: declaration order
stays intact, the separator bytes stay visible, and the width arithmetic above
still sums, which is what R-5 needs of it. All SEVEN fillers are carried this
way - [copybooks/wsmaps03.cob:L10], [:L12], [:L18], [:L20], [:L21], [:L26] and
[:L28].

Class names are the PascalCase of the COBOL group name with hyphens removed,
and the mixed-case COBOL spellings are carried verbatim beside every
declaration below: `Maps03Ws` for `01 maps03-ws.` [:L6], `MapsUUk` for `03
u-UK redefines u-date.` [:L8], `MapsUYear` for `05 u-year.` [:L13], `MapsUUsa`
[:L16], `MapsUIntl` [:L22], `MapsUIntlYear` [:L23]. `Maps03Ws` is not a free
choice: section 0.4.3 writes out the import line every consumer uses.

TWO COBOL DECLARATIONS OF THE SAME FOURTEEN BYTES (RULE R-4)
------------------------------------------------------------
The caller's copybook and the called program declare the same 14 bytes under
different names, with different structure, in different files. Both are real,
and neither is bent to fit the other here::

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
    `A-*` fields in the program's LINKAGE SECTION, which is what `procedure
    division using Mapa03-WS.` binds [common/maps04.cbl:L122]. Note also that
    the program `maps04` names its own record after maps0*3*.
  * STRUCTURE, first difference. The program declares ONE reading and it is
    anonymous - `03 filler redefines A-Date.` [:L111] - so it sees neither the
    USA nor the International reading at all. The three named readings exist
    only in the caller's copybook.
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

ANOMALY A-16 - WHAT `u-bin` HOLDS AFTER A REJECTED DATE (RULES R-4, R-6)
-----------------------------------------------------------------------
The date module documents one contract and implements another. Its own comments
say errors come back as zero - "Date errors returned as A-Bin equal zero"
[common/maps04.cbl:L163] and "if dd/mm/ccyy is bad A-Bin = zero" [:L125] - but
both reject paths leave the binary item untouched: the six-part text test
transfers straight to the exit [:L146], the calendar test does the same [:L154],
and the exit itself performs no store at all [:L188-L189]. The documented zero
holds only because the known caller writes it first - `move zero to u-bin`
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78], immediately before `call "maps04"
using maps03-ws` [:L79]. Section 0.6.8 keeps this OPEN: not every in-scope
caller has been shown to pre-zero, so what each one observes is arbitrated by
the compiled program (rule R-6). Nothing here settles it, and nothing repairs
it.

TRACEABILITY - EVERY FIELD FROM THE DICTIONARY (RULE R-5)
---------------------------------------------------------
The dictionary was probed before a line of this module was written, and it
covers this record completely. `entries_for_copybook_record("maps03-ws")`
returns 25 entries in copybook declaration order, L6 through L30: the 01 group,
the two storage items, the three readings, the two nested year groups, the ten
two-digit components and all seven fillers. Every descriptor below is therefore
built by `FieldDescriptor.from_dictionary_key`, the principal path, and NOT ONE
storage component is stated by hand - no picture, no digit count, no scale, no
sign position and no width appears as a literal anywhere below.

Keys are `<COPYBOOK-RECORD>.<FIELD-NAME>`, both halves verbatim from the frozen
source. So the record half is the LOWER-case `maps03-ws` the copybook writes,
and the field half keeps its own mixed case - `maps03-ws.u-UK`,
`maps03-ws.u-Intl`. A FILLER, which repeats, is keyed by its declaration line:
`maps03-ws.filler#21`. Lookup is exact and case-sensitive, so an upper-cased key
such as `MAPS03-WS.U-BIN` matches nothing at all; that was checked, not assumed.

This record reaches NO MySQL table and no bridge host variable, which is correct
rather than a gap: it is a call-interface block and appears nowhere in the
entity-to-table spine of section 0.2.1.1. Its provenance is one-sided by design,
and `FieldDescriptor.cite` says so out loud::

    maps03-ws.u-bin  copybook=copybooks/wsmaps03.cob:L30  bridge=absent
    column=absent

That string comes from `acas_posting.dictionary.loader.cite`, surfaced through
the descriptor and never reimplemented here. Each class publishes its own
declared items as a `FIELDS` tuple, element 0 being the class's own group
header, in copybook declaration order. A nested or redefining group appears
twice on purpose - once as a child in its parent's `FIELDS`, which keeps the
parent's declaration order and width arithmetic whole, and once as element 0 of
its own class - and the union of the six tuples is exactly the dictionary's 25
keys, with nothing added and nothing dropped.

The classes below follow copybook declaration order with one mechanical
adjustment: a nested group's class is hoisted immediately above the class that
contains it, because a dataclass default is built by name at class-creation
time and Python needs the name to exist first. So `MapsUYear` precedes
`MapsUUk`, and `MapsUIntlYear` precedes `MapsUIntl`. Nothing else is reordered.

TYPE DISCIPLINE (R-2), LAYERING (0.4.3) AND DETERMINISM (R-6)
-------------------------------------------------------------
    u-date          pic x(10)     ->  str
    the ten `pic 99` components   ->  int  (DISPLAY, 2 digits, no fraction)
    u-bin           binary-long   ->  int  (signed 32-bit)

`u-bin` being an `int` is not a shortcut: it counts whole days, so it has no
fractional part, and any other carrier would invite fractional-day arithmetic
COBOL cannot express. This record holds no money at all, so no exact-decimal
carrier is needed and none is imported. One derived detail is worth stating
exactly, because it is the kind of value that gets asserted from habit rather
than read: `u-bin` carries NO picture, NO digit count and NO scale - the copybook
declares `binary-long` on the field and states no PICTURE clause
[copybooks/wsmaps03.cob:L30], so the dictionary reports all three ABSENT rather
than zero, and its whole-number nature travels on its usage instead (BINARY-LONG,
`python_storage` INT, four bytes, integral domain). Writing a scale of zero here
would invent a value the frozen source does not state. The ten `pic 99`
components do carry a picture, so their digits and scale come from it.

`acas_posting.records` states the leaf-layering contract for every record module;
two consequences are specific to this one. First, the fixed-width mechanics the
redefinition views need - an alphanumeric move, a reference modification and a
component poke - are three module-private functions rather than an import of
`acas_posting.cobol.move`, which owns the general MOVE verb but is not on the
record layer's permitted list; `acas_posting/dates.py` carries the same three for
its own working storage, and the duplication is confined to character mechanics
that hold no business rule and is recorded at the definitions. Second, this
module does NOT import `acas_posting.dates`: the edge runs one way, the date
module consuming this record and this record knowing nothing of it, so a leaf
that imported it would close a cycle and drag date logic into the record layer.

DETERMINISM (RULE R-6)
----------------------
Section 0.1.1 records that "every one of the in-scope posting programs contains
zero clock reads; the date arrives purely through linkage". THIS RECORD IS THAT
LINKAGE. The frozen call chain's fourteen ambient date and time reads all sit in
out-of-scope menu shells or the date-service copybook they COPY, and the census
plus the pinning of both observables live in `acas_posting/clock.py`. So there is
no clock here, no unpredictable value, no environment read and no filesystem
walk: a date reaches these fields only because a caller put it there. The one
thing read at import is the generated dictionary, through the loader's lazy
cached read. See `acas_posting.records` for shared conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[tuple[str, ...]] = (
    # The 01-level record first, then its readings in name order. Sorted with `sorted()`
    # so the order is mechanical rather than a matter of taste.
    "Maps03Ws",
    "MapsUIntl",
    "MapsUIntlYear",
    "MapsUUk",
    "MapsUUsa",
    "MapsUYear",
)


# The 01-level record name, verbatim from [copybooks/wsmaps03.cob:L6] - LOWER case,
# because that is how the copybook writes it and dictionary keys carry names exactly as
# the frozen source spells them.
_COPYBOOK_RECORD: Final[str] = "maps03-ws"


def _descriptor(field_name: str) -> FieldDescriptor:
    """Return the dictionary-backed descriptor for one field of this record.

    Composes the qualified key and delegates. It holds no metadata of its own, which is
    the whole point: every storage component comes from the generated dictionary (rule
    R-5), and a bare field name is never used as a key.

    Args:
        field_name: The field's COBOL name verbatim - `"u-date"`, `"u-UK"`, `"u-intl-
            days"` - or `"filler#<line>"` for one of the seven fillers, which repeat and
            are therefore keyed by the line that declares them.

    Returns:
        That field's descriptor, carrying both its dictionary key and its
            `copybooks/wsmaps03.cob:L<n>` locator as provenance.
    """
    return FieldDescriptor.from_dictionary_key(
        f"{_COPYBOOK_RECORD}.{field_name}"
    )


# `u-date`'s declared character width, taken from its own descriptor rather than typed
# here [copybooks/wsmaps03.cob:L7].
_DATE_TEXT_WIDTH: Final[int] = _descriptor("u-date").byte_length


# `u-UK`, `u-USA` and `u-Intl` each `redefines u-date`, so the bytes they name ARE
# `u-date`'s bytes.


def _alphanumeric_move(source: str, width: int) -> str:
    """Reproduce a COBOL `MOVE` into an alphanumeric `PIC X(width)` field."""
    if len(source) >= width:
        return source[:width]
    return source + " " * (width - len(source))


def _ref_mod(field_text: str, offset: int, length: int) -> str:
    """Reproduce COBOL reference modification `field (offset:length)`.

    `offset` is 1-based, the way COBOL writes it.
    """
    start = offset - 1
    required_width = max(len(field_text), start + length)
    materialised = _alphanumeric_move(field_text, required_width)
    return materialised[start:start + length]


def _poke(
    base_text: str, offset: int, length: int, value: str, width: int
) -> str:
    """Reproduce a COBOL `MOVE` into a `REDEFINES` sub-field of a group.

    Writes `value` into the `length` characters at 1-based `offset` of a
    `width`-character group and leaves every other character exactly as it was. That is
    how a component move keeps the separators.
    """
    start = offset - 1
    materialised = _alphanumeric_move(base_text, width)
    stored = _alphanumeric_move(value, length)
    return materialised[:start] + stored + materialised[start + length:]


@dataclass(slots=True)
class Maps03Ws:
    """`01 maps03-ws.` [copybooks/wsmaps03.cob:L6] - the date record.

    The record every in-scope posting program obtains by `copy "wsmaps03.cob"` and hands
    over by `call "maps04" using maps03-ws`. Fourteen bytes: ten characters of date
    text, then a four-byte binary day number.

    Attributes:
        u_date: `u-date pic x(10)` [copybooks/wsmaps03.cob:L7]. The date text, ten
            characters. Which of the three readings applies to a given value is the
            calling program's business.
        u_bin: `u-bin binary-long` [copybooks/wsmaps03.cob:L30]. The binary day number -
            a signed 32-bit integer, hence a Python `int` and never a binary floating-
            point value (rule R-2).
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("maps03-ws"),
        _descriptor("u-date"),
        _descriptor("u-UK"),
        _descriptor("u-USA"),
        _descriptor("u-Intl"),
        _descriptor("u-bin"),
    )

    u_date: str = " " * _DATE_TEXT_WIDTH

    # u-bin binary-long [copybooks/wsmaps03.cob:L30] ANOMALY A-16, RECORDED HERE AND
    # SETTLED NOWHERE (rules R-4, R-6).
    u_bin: int = 0

    # One view per component the copybook names under `u-UK`, `u-USA` and `u-Intl`, in
    # copybook declaration order within each reading.


    @property
    def u_days(self) -> str:
        """`u-days pic 99` [copybooks/wsmaps03.cob:L9] - offset 1, length 2."""
        return _ref_mod(self.u_date, 1, 2)

    @u_days.setter
    def u_days(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 2, value, _DATE_TEXT_WIDTH)

    @property
    def u_month(self) -> str:
        """`u-month pic 99` [copybooks/wsmaps03.cob:L11] - offset 4, len 2."""
        return _ref_mod(self.u_date, 4, 2)

    @u_month.setter
    def u_month(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 4, 2, value, _DATE_TEXT_WIDTH)

    @property
    def u_year(self) -> str:
        """`u-year` group [copybooks/wsmaps03.cob:L13] - offset 7, length 4.

        The group's four characters as one field. The date module declares the same four
        as `A-CCYY pic 9(4)` [common/maps04.cbl:L116]; that structural divergence is
        recorded in this module's docstring and not harmonised (rule R-4).
        """
        return _ref_mod(self.u_date, 7, 4)

    @u_year.setter
    def u_year(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 7, 4, value, _DATE_TEXT_WIDTH)

    @property
    def u_cc(self) -> str:
        """`u-cc pic 99` [copybooks/wsmaps03.cob:L14] - offset 7, length 2."""
        return _ref_mod(self.u_date, 7, 2)

    @u_cc.setter
    def u_cc(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 7, 2, value, _DATE_TEXT_WIDTH)

    @property
    def u_yy(self) -> str:
        """`u-yy pic 99` [copybooks/wsmaps03.cob:L15] - offset 9, length 2."""
        return _ref_mod(self.u_date, 9, 2)

    @u_yy.setter
    def u_yy(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 9, 2, value, _DATE_TEXT_WIDTH)

    # u-USA [copybooks/wsmaps03.cob:L16-L21] - MM/DD. Declared by the CALLER's copybook
    # only; the date module has no such redefinition [common/maps04.cbl:L111] and never
    # addresses these two.

    @property
    def u_usa_month(self) -> str:
        """`u-usa-month pic 99` [:L17] - offset 1, length 2."""
        return _ref_mod(self.u_date, 1, 2)

    @u_usa_month.setter
    def u_usa_month(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 2, value, _DATE_TEXT_WIDTH)

    @property
    def u_usa_days(self) -> str:
        """`u-usa-days pic 99` [:L19] - offset 4, length 2."""
        return _ref_mod(self.u_date, 4, 2)

    @u_usa_days.setter
    def u_usa_days(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 4, 2, value, _DATE_TEXT_WIDTH)


    @property
    def u_intl_year(self) -> str:
        """`u-intl-year` group [:L23] - offset 1, length 4."""
        return _ref_mod(self.u_date, 1, 4)

    @u_intl_year.setter
    def u_intl_year(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 4, value, _DATE_TEXT_WIDTH)

    @property
    def u_intl_cc(self) -> str:
        """`u-intl-cc pic 99` [:L24] - offset 1, length 2."""
        return _ref_mod(self.u_date, 1, 2)

    @u_intl_cc.setter
    def u_intl_cc(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 2, value, _DATE_TEXT_WIDTH)

    @property
    def u_intl_yy(self) -> str:
        """`u-intl-yy pic 99` [:L25] - offset 3, length 2."""
        return _ref_mod(self.u_date, 3, 2)

    @u_intl_yy.setter
    def u_intl_yy(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 3, 2, value, _DATE_TEXT_WIDTH)

    @property
    def u_intl_month(self) -> str:
        """`u-intl-month pic 99` [:L27] - offset 6, length 2."""
        return _ref_mod(self.u_date, 6, 2)

    @u_intl_month.setter
    def u_intl_month(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 6, 2, value, _DATE_TEXT_WIDTH)

    @property
    def u_intl_days(self) -> str:
        """`u-intl-days pic 99` [:L29] - offset 9, length 2."""
        return _ref_mod(self.u_date, 9, 2)

    @u_intl_days.setter
    def u_intl_days(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 9, 2, value, _DATE_TEXT_WIDTH)


# THE UK READING - u-UK redefines u-date - DD/MM/CCYY `MapsUYear` is hoisted above
# `MapsUUk`, which declares it.


@dataclass(slots=True)
class MapsUYear:
    """`05 u-year.` [copybooks/wsmaps03.cob:L13] - century and year, CCYY.

    A GROUP is how the copybook splits these four bytes. The date module splits the same
    four bytes differently, with `05 A-CCYY pic 9(4)` redefined into `07 A-CC` and `07
    A-Year` [common/maps04.cbl:L116-L119]. Both declarations stand as written.

    Attributes:
        u_cc: `u-cc pic 99` [copybooks/wsmaps03.cob:L14]. The century part.
        u_yy: `u-yy pic 99` [copybooks/wsmaps03.cob:L15]. The year part.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-year"),
        _descriptor("u-cc"),
        _descriptor("u-yy"),
    )

    u_cc: int = 0

    u_yy: int = 0


@dataclass(slots=True)
class MapsUUk:
    """`03 u-UK redefines u-date.` [copybooks/wsmaps03.cob:L8] - DD/MM/CCYY.

    Real callers write these components rather than the whole text: the menu shell moves
    the year, month and day of the run date into `u-year`, `u-month` and `u-days`
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L74-L76], after seeding the text with
    "00/00/0000" [copybooks/Proc-ACAS-Mapser-RDB.cob:L73].

    Attributes:
        u_days: `u-days pic 99` [copybooks/wsmaps03.cob:L9]. Day of month, at offsets 1
            to 2.
        u_month: `u-month pic 99` [copybooks/wsmaps03.cob:L11]. Month, at offsets 4 to
            5.
        u_year: `u-year` [copybooks/wsmaps03.cob:L13]. The century-and-year group at
            offsets 7 to 10, held as one `MapsUYear`.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-UK"),
        _descriptor("u-days"),
        _descriptor("filler#10"),
        _descriptor("u-month"),
        _descriptor("filler#12"),
        _descriptor("u-year"),
    )

    u_days: int = 0

    u_month: int = 0

    # u-year [copybooks/wsmaps03.cob:L13] - a GROUP, and not a redefinition.
    u_year: MapsUYear = field(default_factory=MapsUYear)


@dataclass(slots=True)
class MapsUUsa:
    """`03 u-USA redefines u-date.` [copybooks/wsmaps03.cob:L16] - MM/DD.

    Note the shape of that arithmetic.

    Attributes:
        u_usa_month: `u-usa-month pic 99` [copybooks/wsmaps03.cob:L17]. Month, at
            offsets 1 to 2 - where the UK reading has the day.
        u_usa_days: `u-usa-days pic 99` [copybooks/wsmaps03.cob:L19]. Day of month, at
            offsets 4 to 5 - where the UK reading has the month.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-USA"),
        _descriptor("u-usa-month"),
        _descriptor("filler#18"),
        _descriptor("u-usa-days"),
        _descriptor("filler#20"),
        _descriptor("filler#21"),
    )

    u_usa_month: int = 0

    u_usa_days: int = 0


@dataclass(slots=True)
class MapsUIntlYear:
    """`05 u-intl-year.` [copybooks/wsmaps03.cob:L23] - CCYY, 1 to 4.

    Attributes:
        u_intl_cc: `u-intl-cc pic 99` [copybooks/wsmaps03.cob:L24]. Century.
        u_intl_yy: `u-intl-yy pic 99` [copybooks/wsmaps03.cob:L25]. Year.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-intl-year"),
        _descriptor("u-intl-cc"),
        _descriptor("u-intl-yy"),
    )

    u_intl_cc: int = 0

    u_intl_yy: int = 0


@dataclass(slots=True)
class MapsUIntl:
    """`03 u-Intl redefines u-date.` [copybooks/wsmaps03.cob:L22].

    This reading leads with its group rather than trailing it, which is why its
    separators fall at offsets 5 and 8 instead of 3 and 6.

    Attributes:
        u_intl_year: `u-intl-year` [copybooks/wsmaps03.cob:L23]. The century-and-year
            group at offsets 1 to 4, held as one `MapsUIntlYear`.
        u_intl_month: `u-intl-month pic 99` [copybooks/wsmaps03.cob:L27]. Month, at
            offsets 6 to 7.
        u_intl_days: `u-intl-days pic 99` [copybooks/wsmaps03.cob:L29]. Day of month, at
            offsets 9 to 10.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("u-Intl"),
        _descriptor("u-intl-year"),
        _descriptor("filler#26"),
        _descriptor("u-intl-month"),
        _descriptor("filler#28"),
        _descriptor("u-intl-days"),
    )

    u_intl_year: MapsUIntlYear = field(default_factory=MapsUIntlYear)

    u_intl_month: int = 0

    u_intl_days: int = 0
