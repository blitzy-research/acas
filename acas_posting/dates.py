"""Date validation and conversion - the Python migration of common/maps04.cbl.

This module is the whole of the ACAS date logic the batch posting cycle reaches.
It is a REIMPLEMENTATION of the COBOL, never a call into it, and it carries two
bodies of code that the COBOL keeps in two places:

  1. `common/maps04.cbl` itself - 189 lines, a CALLed sub-program that converts
     a 10-character UK date text to and from a binary day number. Reproduced
     statement for statement as `maps04` plus `ws_unpack`.
  2. The four date SECTIONS the in-scope posting programs each carry a private
     copy of - `zz050-Validate-Date`, `zz060-Convert-Date`,
     `zz070-Convert-Date` and the thin wrapper section around the `CALL`.

NO COBOL AT RUNTIME, AND NO DATE LIBRARY  (rule R-1)
Nothing here launches a process or loads a foreign library, and there is no
third-party date library either: the semantics being reproduced are those of one
program with a non-standard epoch and idiosyncratic rejection behaviour, and a
general-purpose library would be more correct than the specification - the one
outcome to avoid. `FUNCTION integer-of-date`, `FUNCTION date-of-integer` and
`FUNCTION Test-Date-YYYYMMDD` are therefore reimplemented natively. Imports are
the standard library plus three names from the leaf layers section 0.4.3 permits
a consumer of this kind: the linkage record `Maps03Ws`, which is that section's
own translation of `copy "wsmaps03.cob"`, and `FieldDescriptor` with the
dictionary `loader`, from which the layout of that record's redefinitions is
DERIVED rather than typed. Every edge runs one way and none reaches the DAL, the
program modules or the CLI, so `programs/*.py` can use this module freely.

THE DEFECTS HERE ARE REPRODUCED ON PURPOSE  (rule R-4)
This module is the primary carrier of anomaly #16: on rejection `maps04` leaves
its binary output field COMPLETELY UNTOUCHED - not zeroed, not set to a
sentinel, not raised - even though its own remarks claim that "Date errors
returned as A-Bin equal zero" [common/maps04.cbl:L163]. That documented contract
holds only because callers pre-zero the field themselves
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78] and in the `zz050-test-date` paragraph
below. Zeroing it here would be the single easiest way to "fix" a defect and
fail the migration. Every reproduction site carries its own [path:Lnnn] comment.

THE EPOCH, AND THE MAINTAINER'S OWN WARNING ABOUT IT
`FUNCTION integer-of-date` counts days from 1600-12-31, so 1601-01-01 is day 1
[common/maps04.cbl:L167]. In Python that epoch is `date(1600, 12, 31)`, whose
proleptic Gregorian ordinal is 584388; `COBOL_DATE_EPOCH_ORDINAL` derives it
rather than hard-coding it. The maintainer flags the consequence himself: this
"uses binary Dates from 31/12/1600 so is NOT usable within IRS as is, but in any
event uses Dates with CC e.g., dd/mm/ccYY where as IRS uses dd/mm/YY"
[common/maps04.cbl:L39-L41]. That is why the IRS posting path does not route
through this module and why irs/irs030.cbl's own `Date-Validate` is out of scope.

WHICH PROGRAM CARRIES WHICH SECTION
From the section headers in the frozen source. The distribution is NOT uniform:

    program   zz050   zz060   zz070   wrapper section
    -------   -----   -----   -----   -------------------------------
    gl051     L1169   L1208   L1243   maps03  L1273   (anomaly #22)
    gl070      -      L538    L573    maps03  L603    (anomaly #22)
    gl071      -       -       -       -   (a pure sort; no date logic at all)
    gl072      -       -      L467     -
    gl080      -       -      L719     -
    sl055      -       -      L694     -
    sl060     L1192   L1227   L1262   maps04  L1292
    sl100     L708    L743    L778    maps04  L808
    pl055      -       -      L599     -
    pl060     L1046   L1081   L1116   maps04  L1146
    pl100     L689    L724    L759    maps04  L789
    irs030     -       -       -      Date-Validate L1285 - OUT OF SCOPE

`gl070` has no `zz050` at all; four programs carry `zz070` only; `gl071` carries
none. Do not assume uniformity.

WHAT MAY BE CONSOLIDATED, AND WHAT MAY NOT
The plan calls these section bodies textually equivalent and so consolidatable.
Across the carriers in the frozen source that is only partly true:

  * `zz070-Convert-Date` - one body in all TEN carriers. Consolidated.
  * `zz060-Convert-Date` - one body in all SIX carriers except for the single
    token naming the wrapper it performs (`maps03` in gl051 and gl070, `maps04`
    in the other four). Consolidated, with the wrapper passed in explicitly.
  * `zz050-Validate-Date` - NOT EQUIVALENT. `gl051` alone carries three extra
    `inspect ws-test-date replacing all` statements
    [general/gl051.cbl:L1178-L1180] which mutate the caller's own text field. It
    is therefore published as TWO functions, and the mutating variant is not
    reachable by accident or by a defaulted argument.

FOUR POINTS THE SOURCE ALONE DOES NOT SETTLE  (rule R-6)
Each is resolved in the way the frozen control flow implies, with the reasoning
stated at its reproduction site so the compiled oracle can arbitrate it:

  * The reject contract. Both reject paths fall through without writing the
    binary field [common/maps04.cbl:L146], [common/maps04.cbl:L154].
  * A non-numeric year. `A-Year` is never tested for NUMERIC, so such a date is
    not rejected; `_zoned_decimal_value` reads whatever characters the field
    holds as zoned decimal, which is what the storage class means.
  * The domain of `FUNCTION Test-Date-YYYYMMDD`, taken as 1601-01-01 through
    9999-12-31. It follows from the epoch, and it rejects 1600-12-31 even though
    `datetime.date` accepts it.
  * An out-of-domain day number on the unpack path, which yields the seed's own
    "00/00/0000" rather than failing.

RULES R-2, R-3, R-5 AND DETERMINISM
Every value is a `str` - the date text and its fixed-width sub-fields - or an
`int` - the binary day number, the digit groups and the separator tally `Z`. No
binary float and no decimal: nothing here is monetary and `A-Bin` is
`binary-long` (rule R-2). No validation is added (rule R-3): the six-part reject
test is reproduced exactly as written [common/maps04.cbl:L140-L146] and does not
test `A-Year` for numeric, and nothing raises for a bad date, so the rejection
signal is precisely "the binary field was not written". Every reproduced
paragraph has a correspondingly named function and every `GO TO` site names its
class from the four-class taxonomy - only classes 3 (`return`) and 4 (call then
explicit `return`) occur here, as there is no loop in any of it (rule R-5). The
module converts dates it is GIVEN: no clock read, no entropy source and no
environment lookup, which is what makes two runs identical (rule R-6).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader
from acas_posting.records.maps03 import Maps03Ws

# ---------------------------------------------------------------------------
#  THE EPOCH  [common/maps04.cbl:L167]
#  `FUNCTION integer-of-date` returns 1 for 1601-01-01, so day zero is
#  1600-12-31. DERIVED, not hard-coded, so that the relationship to the
#  Gregorian calendar is stated once and cannot drift: the value is 584388.
#  The relationship the epoch fixes: integer-of-date(16010101) = 1,
#  integer-of-date(20250921) = 155127, integer-of-date(99991231) = 3067671.
#  The maintainer's own caveat on this epoch is at [common/maps04.cbl:L39-L41]:
#  it "is NOT usable within IRS as is", because IRS dates carry no century.
COBOL_DATE_EPOCH_ORDINAL: Final[int] = date(1600, 12, 31).toordinal()

#  THE DOMAIN OF THE DATE INTRINSICS
#  `FUNCTION Test-Date-YYYYMMDD` returns zero for a valid date and non-zero
#  otherwise, over the range the epoch implies: 16001231 and 00000000 are
#  rejected, 16010101 and 99991231 accepted. This matters because
#  `datetime.date` happily accepts 1600-12-31, so an implementation that gated
#  only on `date(...)` constructing successfully would accept a date the
#  specification rejects.
COBOL_MIN_DATE_YEAR: Final[int] = 1601
COBOL_MAX_DATE_YEAR: Final[int] = 9999

#  The corresponding binary day numbers, derived from the year bounds above so
#  the two can never disagree: 1 for 1601-01-01, 3067671 for 9999-12-31.
COBOL_MIN_DATE_INTEGER: Final[int] = (
    date(COBOL_MIN_DATE_YEAR, 1, 1).toordinal() - COBOL_DATE_EPOCH_ORDINAL
)
COBOL_MAX_DATE_INTEGER: Final[int] = (
    date(COBOL_MAX_DATE_YEAR, 12, 31).toordinal() - COBOL_DATE_EPOCH_ORDINAL
)

#  FIXED WIDTHS  [common/maps04.cbl:L110, L92-L100]
#  `A-Date pic x(10)` is the date text; `Test-Date` is the 8-byte CCYYMMDD
#  working-storage group that `Test-Date9 redefines ... pic 9(8)` reads as a
#  single number.
DATE_TEXT_LENGTH: Final[int] = 10
TEST_DATE_LENGTH: Final[int] = 8

#  THE THREE LOAD-BEARING STRING LITERALS
#  Each of these is moved into a 10-character field purely so that the SEPARATOR
#  characters land in fixed positions; the surrounding letters and zeros are
#  then overwritten by reference-modified moves. Reproducing the literals - and
#  the positional overwrites - rather than formatting a clean string is what
#  makes the output come out right for free. The LETTERS never survive into it,
#  because COBOL reference modification always yields exactly the requested
#  length and fully overwrites its target - so a spaces source gives
#  "    /  /  " and "  /  /    " respectively. What survives from each literal
#  is the "/" separators. That is their whole job.

#  [common/maps04.cbl:L182] - the unpack seed. Its "/" at positions 3 and 6 are
#  never overwritten, because the three moves that follow write only offsets
#  7-10, 4-5 and 1-2. THIS is why the unpacked form is DD/MM/CCYY.
UNPACK_SEED: Final[str] = "00/00/0000"

#  [general/gl070.cbl:L595] - used by zz060 and zz070, which convert UK order
#  INTO International. Its "/" land at positions 5 and 8, giving CCYY/MM/DD.
UK_TO_INTL_SEED: Final[str] = "ccyy/mm/dd"

#  [general/gl051.cbl:L1195] - used by zz050, which converts International order
#  INTO UK. A DIFFERENT literal from the one above, with "/" at positions 3 and
#  6, giving DD/MM/CCYY. The two directions read their source at different
#  offsets as well, so the two must never be copy-pasted into each other. The
#  names of these two constants state the direction for exactly that reason.
INTL_TO_UK_SEED: Final[str] = "dd/mm/ccyy"

#  THE PRESENTATION-FORMAT SWITCH  [copybooks/wssystem.cob:L128-L132]
#      05  Date-Form       pic 9.
#          88  Date-UK             value 1.   *> dd/mm/yyyy
#          88  Date-USA            value 2.   *> mm/dd/yyyy
#          88  Date-Intl           value 3.   *> yyyy/mm/dd
#          88  Date-Valid-Formats  values 1 2 3.
#  ANOMALY, reproduced: `Date-Valid-Formats` is declared but NEVER TESTED by
#  any of the date sections. They test `Date-Form = zero` and default to 1
#  instead, which means a Date-Form of 4 or 9 falls through every branch and is
#  treated as International. The unused condition name is therefore not
#  published as a predicate below - publishing it would invite a caller to use
#  the test the COBOL declines to make.
DATE_FORM_UNSET: Final[int] = 0
DATE_FORM_UK: Final[int] = 1
DATE_FORM_USA: Final[int] = 2
DATE_FORM_INTL: Final[int] = 3

#  The characters a PIC 9 DISPLAY field accepts as numeric. Spelled out rather
#  than delegated to `str.isdigit()`, which is True for superscripts and other
#  Unicode digit forms that a zoned-decimal COBOL field would reject.
_ASCII_DIGITS: Final[str] = "0123456789"


#  COBOL FIXED-WIDTH STORAGE SEMANTICS
#  A COBOL PIC X(n) field is n bytes wide at all times. That single fact is
#  what makes the seed literals above work, so these three helpers exist to
#  keep it true here as well rather than letting Python's variable-length
#  strings quietly change the result.
#  These are storage mechanics only - no business rule lives in them.


def _alphanumeric_move(source: str, width: int) -> str:
    """Reproduce a COBOL `MOVE` into an alphanumeric `PIC X(width)` field.

    An alphanumeric move is left-justified: a short sending field is padded on
    the right with spaces, and a long one is truncated on the right. The
    receiving field is always exactly `width` characters afterwards.
    """
    if len(source) >= width:
        return source[:width]
    return source + " " * (width - len(source))


def _ref_mod(field_text: str, offset: int, length: int) -> str:
    """Reproduce COBOL reference modification `field (offset:length)`.

    `offset` is 1-based, as COBOL writes it. The declared field is materialised
    at its full width first, so that reading past the end of a short Python
    string yields the spaces a real COBOL field would hold there rather than a
    short slice. The result is always exactly `length` characters.
    """
    required_width = max(len(field_text), offset - 1 + length)
    materialised = _alphanumeric_move(field_text, required_width)
    return materialised[offset - 1 : offset - 1 + length]


def _poke(base_text: str, offset: int, length: int, value: str, width: int) -> str:
    """Reproduce a COBOL `MOVE` into a `REDEFINES` sub-field of a group.

    Writes `value` into the `length` characters at 1-based `offset` of a
    `width`-character group, leaving every other character of the group exactly
    as it was. That is precisely how the seed literals keep their separators:
    the moves overwrite the digit positions and never touch positions 3 and 6
    (or 5 and 8).
    """
    materialised = _alphanumeric_move(base_text, width)
    stored = _alphanumeric_move(value, length)
    return materialised[: offset - 1] + stored + materialised[offset - 1 + length :]


def _is_numeric(field_text: str) -> bool:
    """Reproduce the COBOL `NUMERIC` class condition for a `PIC 9(n)` DISPLAY field.

    A zoned-decimal DISPLAY field is numeric only when every character is an
    ASCII decimal digit. A space, a "/", a letter or a sign character all fail,
    which is why `"2 "` at the century position is rejected by the six-part
    test while `"20"` is accepted.
    """
    return len(field_text) > 0 and all(
        character in _ASCII_DIGITS for character in field_text
    )


def _zoned_decimal_value(digits_text: str) -> int:
    """Read a `PIC 9(n)` DISPLAY field as a number, zoned-decimal fashion.

    ANOMALY, reproduced. `Test-Date9` is `PIC 9(8)` DISPLAY, and the six-part
    test [common/maps04.cbl:L140-L145] never checks `A-Year` for NUMERIC, so
    non-digit characters can reach it. A zoned-decimal read is what the storage
    class means: the low nibble of each byte is its digit, and the digits are
    positionally weighted with carry. So such a date is not rejected - it
    yields a DIFFERENT YEAR:

        year  low nibbles   Test-Date9   date
        ----  -----------   ----------   ----------
        "ab"  1, 2          20120921     2012-09-21
        "a0"  1, 0          20100921     2010-09-21
        "zz"  10, 10        21100921     2110-09-21   <- carries
        "  "  0, 0          20000921     2000-09-21

    Note the third row: a low nibble of 10 is not a decimal digit at all and it
    CARRIES into the next position, which is why this is an accumulate-and-carry
    loop rather than a digit-by-digit string substitution.

    Only `A-Year` can be non-numeric here - the century, month and day are all
    proved numeric by the six-part test before this is reached - so at most two
    of the eight bytes are ever anomalous. When they carry far enough to push
    the year past `COBOL_MAX_DATE_YEAR` the date is rejected by the validity
    check, with the binary field left untouched as always.
    """
    value = 0
    for character in digits_text:
        #  byte & 0x0F is the zoned-decimal digit: "0"-"9" are 0x30-0x39, so
        #  the low nibble is the digit; "a" is 0x61, so its low nibble is 1.
        value = value * 10 + (ord(character) & 0x0F)
    return value


#  THE LINKAGE RECORD, AND THE THREE READINGS OF ITS TEXT
#  [copybooks/wsmaps03.cob:L6-L30]  and  [common/maps04.cbl:L109-L120]
# ===========================================================================
#  THE RECORD ITSELF IS NOT DECLARED HERE. `acas_posting.records.maps03` owns
#  it, and Agent Action Plan section 0.4.3 fixes that mapping verbatim:
#
#      FROM:  copy "wsmaps03.cob".
#      TO:    from acas_posting.records.maps03 import Maps03Ws
#
#  So there is exactly ONE class of that name in this package, and its fields
#  cite generated dictionary entries like every other record field (rule R-5).
#  An earlier draft declared a SECOND class of the same name here, carrying the
#  reference-modification views `maps04` addresses while the canonical record
#  carried none of them: passing the canonical record to `maps04` raised
#  AttributeError, and a linkage area the dictionary already covers was
#  described twice, once without provenance. The views now live on the canonical
#  record, beside the `redefines` declarations that justify them, and the
#  name-keyed accessors below read and write through the same ten characters.
#
#  ONE record, TWO vocabularies. Every caller passes `maps03-ws` from
#  copybooks/wsmaps03.cob, whose fields are u-date / u-days / u-month / u-year /
#  u-cc / u-yy / u-bin and which additionally declares the USA and International
#  redefines. The called program declares the same 14 bytes as `Mapa03-WS` with
#  the names A-Date / A-Days / A-Month / A-CCYY / A-CC / A-Year / A-Bin, and sees
#  NEITHER of those extra redefines. The caller's names are the attribute names,
#  because the caller's copybook is the one every in-scope program actually
#  copies; the called program's own names appear in the comments at the statement
#  sites below. Note also that the record `maps04` declares is named after
#  maps0*3* while the program itself is maps04.
#
#  So this module imports that class and adds nothing to it. A second record
#  shape declared here would be a second truth for one copybook, and the two
#  would drift: the canonical class binds every field to the generated
#  dictionary (rule R-5) while a local one would carry transcribed metadata.
#
#  ONE record, TWO VOCABULARIES, and the two do not agree item for item. Every
#  caller passes `maps03-ws` [copybooks/wsmaps03.cob:L6-L30], whose items are
#  u-date, the three redefinitions u-UK / u-USA / u-Intl, and u-bin. The called
#  program declares the same fourteen characters in its own LINKAGE SECTION as
#  `01 Mapa03-WS` [common/maps04.cbl:L109-L120] - note that it is named after
#  maps0*3* although the program is maps04 - and it differs in three ways:
#
#    * its redefinition of the date text is FILLER, an unnamed group
#      [common/maps04.cbl:L111], so it has no counterpart of `u-UK`;
#    * it declares NEITHER the USA nor the International redefinition, so four
#      of the caller's items are invisible to it;
#    * its year is `A-CCYY pic 9(4)`, a NUMERIC item, itself redefined by
#      `A-CC` and `A-Year` [common/maps04.cbl:L116-L119], where the caller's
#      `u-year` is a GROUP over two `pic 99` items
#      [copybooks/wsmaps03.cob:L13-L15]. The observable is the same either way:
#      the digits are carried through the four assembly moves as they stand and
#      are read as a number only at the `Test-Date9` redefinition
#      [common/maps04.cbl:L100], which is what `_zoned_decimal_value` records.
#
#  The caller's names are the ones used below, because the caller's copybook is
#  the one every in-scope program actually copies; the called program's name for
#  the same characters appears in the comment at each site.
#
#  WHY AN ACCESSOR AND NOT THE CANONICAL READING CLASSES. `acas_posting.
#  records.maps03` models the three redefines as `MapsUUk`, `MapsUUsa` and
#  `MapsUIntl`, whose items are `pic 99` and therefore `int`. Those classes
#  cannot serve the work below, and the reason is the specification's own: the
#  six-part reject test asks whether the TEXT of a position is numeric -
#  `if u-days not numeric` [common/maps04.cbl:L140-L146] - so the value under
#  test must be the BYTES, including bytes no `int` can hold. Reading the text
#  into an `int` first would decide the very question the test asks. The
#  accessor below is therefore lossless text, which is exactly what a COBOL
#  `REDEFINES` sub-field of a `PIC X(10)` group is.
#
#  Byte layout of the 10-character text, 1-based, all three views at once. The
#  offsets are DERIVED from the dictionary below, not transcribed from this
#  picture, which is here to be read rather than to be authoritative:
#
#      offset  1  2  3  4  5  6  7  8  9  10
#      UK      d  d  /  m  m  /  c  c  y  y
#      USA     m  m  /  d  d  /  -  -  -  -
#      Intl    c  c  y  y  /  m  m  /  d  d
#
#  MUTABLE BY DESIGN, and this is not a style preference - see the canonical
#  class, which says so for the same reason. A COBOL linkage record is passed
#  by reference, and the entire point of anomaly #16 is that `maps04`
#  selectively DOES NOT WRITE one of these fields on the reject path. So the
#  record is a plain mutable dataclass, `maps04` returns None, and callers
#  observe both the writes and - crucially - the absences.
#  A frozen dataclass, or an entry point that returned a new object, would erase
#  the anomaly by making every field appear freshly assigned. There is likewise
#  no validating `__post_init__` (rule R-3): the record must be able to hold
#  exactly the malformed text the COBOL can hold.
# ===========================================================================


#: The `01` record name, verbatim from [copybooks/wsmaps03.cob:L6], LOWER case
#: because that is how the copybook writes it and dictionary keys carry names
#: exactly as the frozen source spells them.
_COPYBOOK_RECORD: Final[str] = "maps03-ws"


@dataclass(slots=True)
class _OpenGroup:
    """One group of `maps03-ws` whose subordinates are still being laid out.

    Scaffolding for the layout walk below and nothing more: it models a partly
    laid-out COBOL group, not a record. No date value is ever held here.

    Attributes:
        key: The group's qualified dictionary key.
        level: Its COBOL level number, which is what closes it - the next item
            at the same or a lower level ends this group.
        offset: The 1-based character position its first subordinate occupies.
        cursor: The next free character position within it, advanced by each
            subordinate laid out so far.
        redefining: Whether the group itself `REDEFINES` an earlier item, in
            which case it re-reads characters the enclosing group has already
            counted and must not advance the enclosing group's cursor.
    """

    key: str
    level: int
    offset: int
    cursor: int
    redefining: bool


def _qualify(item: str) -> str:
    """The dictionary key of one item of `maps03-ws`.

    Args:
        item: The item's own COBOL name, as [copybooks/wsmaps03.cob] spells it.

    Returns:
        That name qualified by the `01` record name, which is how the generated
        dictionary keys every field of a copybook record.
    """
    return f"{_COPYBOOK_RECORD}.{item}"


def _reading_layout() -> dict[str, tuple[int, int]]:
    """Derive every `maps03-ws` item's 1-based offset and width from the record.

    Walks the dictionary's entries for `maps03-ws` in DECLARATION ORDER and lays
    them out the way a COBOL compiler does, so that not one offset in this module
    is transcribed by hand (rule R-5). The rules applied are the language's:

      * a GROUP occupies no characters of its own - it is a name for the
        characters its subordinates occupy - so it contributes nothing and its
        subordinates lay out from its own start;
      * an item that `REDEFINES` another STARTS WHERE THAT ONE STARTS, and
        consumes no further characters of the enclosing group, which is what
        makes `u-UK`, `u-USA` and `u-Intl` three readings of the same ten bytes
        [copybooks/wsmaps03.cob:L8], [copybooks/wsmaps03.cob:L16],
        [copybooks/wsmaps03.cob:L22] rather than thirty;
      * every other elementary item starts at the enclosing group's cursor and
        advances it by its own width - FILLER included, which is why the
        separator positions fall out of the walk instead of being counted.

    Returns:
        Every item of the record - the groups and the seven fillers as well as
        the leaves - keyed by the COBOL name the copybook spells, mapped to
        `(offset, width)` with `offset` 1-based as COBOL writes it. A filler is
        keyed as the dictionary keys it, `filler#<line>`, because there are seven
        and only the declaring line tells them apart.

    Raises:
        acas_posting.dictionary.loader.DictionaryError: The dictionary is absent
            or does not carry this record. Nothing here falls back to a
            transcribed layout: a wrong offset would silently read the wrong two
            characters of a date, and every reject test and every conversion
            below would then be deciding on the wrong bytes.
    """
    layout: dict[str, tuple[int, int]] = {}
    #  The groups whose subordinates are still being laid out, innermost last.
    open_groups: list[_OpenGroup] = []

    def close_innermost() -> None:
        """Finish the innermost open group, sizing it by what it covered."""
        group = open_groups.pop()
        layout[group.key] = (group.offset, group.cursor - group.offset)
        #  A REDEFINES group re-reads characters the enclosing group has
        #  already counted, so it must not advance that group's cursor.
        if open_groups and not group.redefining:
            open_groups[-1].cursor = group.cursor

    for entry in loader.entries_for_copybook_record(_COPYBOOK_RECORD):
        item = entry.copybook
        level = int(item.level)
        while open_groups and open_groups[-1].level >= level:
            close_innermost()
        parent = open_groups[-1] if open_groups else None
        if item.redefines is not None:
            offset = layout[_qualify(item.redefines)][0]
        elif parent is not None:
            offset = parent.cursor
        else:
            offset = 1
        if item.is_group:
            open_groups.append(
                _OpenGroup(
                    key=entry.key,
                    level=level,
                    offset=offset,
                    cursor=offset,
                    redefining=item.redefines is not None,
                )
            )
            continue
        layout[entry.key] = (offset, _descriptor_byte_length(entry.key))
        if parent is not None and item.redefines is None:
            parent.cursor = offset + layout[entry.key][1]
    while open_groups:
        close_innermost()
    return layout


def _descriptor_byte_length(dictionary_key: str) -> int:
    """The declared width in characters of one item of `maps03-ws`.

    Taken from the item's own dictionary-backed descriptor, so a `pic 99` is two
    characters, a `pic x` one, and `u-bin binary-long` four, without any of those
    numbers appearing here.

    Args:
        dictionary_key: The item's qualified dictionary key.

    Returns:
        Its width in characters.
    """
    return int(FieldDescriptor.from_dictionary_key(dictionary_key).byte_length)


#: Every item's `(offset, width)`, derived once. Built at import so that a
#: missing or damaged dictionary fails immediately and visibly rather than at
#: the first date conversion of a posting run.
_LAYOUT: Final[dict[str, tuple[int, int]]] = _reading_layout()


def _items_within_date_text() -> dict[str, tuple[int, int]]:
    """The items of `maps03-ws` that lie inside `u-date`'s own characters.

    Two of the record's items do not: the `01` group, which spans the text AND
    the binary day number, and `u-bin` itself, which is the four characters
    after the text [copybooks/wsmaps03.cob:L30]. Neither is reachable through
    the accessors below - `u-bin` is `ws.u_bin`, an `int`, and the whole record
    is `ws` - and a write through a text accessor at their offsets would run off
    the end of the ten characters and lengthen the field. Deriving the boundary
    from `u-date`'s own extent keeps that impossible without naming either item.

    Returns:
        The subset of `_LAYOUT` whose extent falls entirely within `u-date`:
        `u-date`, the three `REDEFINES` groups, `u-year` and `u-intl-year`, the
        twelve leaves and the seven fillers.
    """
    date_offset, date_width = _LAYOUT[_qualify("u-date")]
    limit = date_offset + date_width
    return {
        key: (offset, width)
        for key, (offset, width) in _LAYOUT.items()
        if offset >= date_offset and offset + width <= limit
    }


#: What `reading_field` and `set_reading_field` will address.
_TEXT_ITEMS: Final[dict[str, tuple[int, int]]] = _items_within_date_text()


def reading_field(ws: Maps03Ws, item: str) -> str:
    """Read one item of a `REDEFINES` reading of `u-date`, as TEXT.

    The Python spelling of a reference-modified read of a `REDEFINES` sub-field:
    `u-days OF u-UK` is `reading_field(ws, "u-days")`. The item is named exactly
    as [copybooks/wsmaps03.cob] spells it, so every call site cites the frozen
    source rather than a renamed attribute, and the offset comes from `_LAYOUT`.

    LOSSLESS, and that is the point. The result is the bytes as they stand -
    spaces, letters, separators and all - because the six-part reject test asks
    whether they are numeric [common/maps04.cbl:L140-L146] and cannot be given a
    value that has already been read as a number.

    Args:
        ws: The linkage record, whose `u_date` holds the ten characters.
        item: The COBOL item name - `"u-days"`, `"u-month"`, `"u-year"`,
            `"u-cc"`, `"u-yy"`, `"u-usa-month"`, `"u-usa-days"`,
            `"u-intl-year"`, `"u-intl-cc"`, `"u-intl-yy"`, `"u-intl-month"` or
            `"u-intl-days"`.

    Returns:
        Exactly that item's declared width in characters. A `u_date` too short
        to cover the item reads as the spaces a real COBOL field would hold
        there, because `_ref_mod` materialises the sending text far enough to
        make the read whole before slicing it.

    Raises:
        KeyError: `item` is not an item of `maps03-ws` that lies inside
            `u-date`. `u-bin` is deliberately not addressable here - it is
            `ws.u_bin`, an `int`, not two characters of text.
    """
    offset, width = _TEXT_ITEMS[_qualify(item)]
    return _ref_mod(ws.u_date, offset, width)


def set_reading_field(ws: Maps03Ws, item: str, value: str) -> None:
    """Write one item of a `REDEFINES` reading of `u-date`, leaving the rest.

    The Python spelling of `move ... to u-year OF u-UK`. It overwrites only that
    item's own characters and leaves every other position of the ten exactly as
    it was, which is how the seed literals keep their separators: the moves land
    on the digit positions and never touch the "/" positions
    [common/maps04.cbl:L181-L186].

    Args:
        ws: The linkage record. Mutated in place, as a COBOL `MOVE` into a
            linkage item is.
        item: The COBOL item name, as `reading_field` documents.
        value: The sending text. Stored by the alphanumeric rule - padded on the
            right with spaces if short, truncated on the right if long - and NOT
            validated in any way (rule R-3), so this record can hold exactly the
            malformed text the COBOL can hold.

    Raises:
        KeyError: `item` is not an item of `maps03-ws` that lies inside
            `u-date`, as `reading_field` records. The ten characters therefore
            stay ten characters long whatever is written through here.
    """
    offset, width = _TEXT_ITEMS[_qualify(item)]
    ws.u_date = _poke(ws.u_date, offset, width, value, DATE_TEXT_LENGTH)


#  THE THREE COBOL INTRINSIC FUNCTIONS, REIMPLEMENTED  (rule R-1)
#  `common/maps04.cbl` delegates the real work to three intrinsics, a choice
#  its own change log dates to 2009 and explains: the migration to GnuCOBOL
#  used "intrinsic FUNCTIONs to do most of the work ... to help reduce risk of
#  format change problems in old programs" [common/maps04.cbl:L35-L37].
#  Rule R-1 forbids reaching the COBOL runtime for them, so all three are
#  reimplemented natively below, to the ISO semantics the intrinsics define.


def _is_leap_year(year: int) -> bool:
    """Apply the Gregorian leap rule, spelled out rather than delegated.

    Divisible by 4, except centuries, except every fourth century. Written
    explicitly because this is the rule that decides whether 29 February is
    accepted, and the program's own comment at
    [common/maps04.cbl:L137-L138] identifies exactly this as the check the
    six-part test deliberately leaves to the intrinsic: the earlier tests are
    "Very basic Testing here as FUNCTION Test-Date checks for February and leap
    years".
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year: int, month: int) -> int:
    """Return the day count for a Gregorian month, February by the leap rule."""
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def test_date_yyyymmdd(yyyymmdd: int) -> int:
    """Reimplement `FUNCTION Test-Date-YYYYMMDD` [common/maps04.cbl:L153].

    Returns ZERO for a valid date and non-zero for an invalid one. That polarity
    is the COBOL intrinsic's, not a Python convention, and the call site tests it
    exactly as the COBOL does - `not = zero` means "bad date". The non-zero return
    is 1, so a caller comparing against something other than zero still agrees.

    The accepted domain is tighter than `datetime.date`'s because it starts at the
    year after the epoch: 16001231 and 00000000 are rejected while 16010101,
    20250921 and 99991231 are accepted. An implementation that merely tried
    `date(y, m, d)` inside a `ValueError` guard would accept 1600-12-31 and diverge
    on that date, which is why the year bounds are tested explicitly.

    NOTE FOR TEST AUTHORS: the name is taken from the COBOL intrinsic for
    traceability (rule R-5) and so matches the `python_functions = ["test_*"]`
    pattern pyproject.toml configures for pytest. Importing it into a test module
    under its own name makes pytest try to collect it as a test; import it under an
    alias instead. Renaming it here would break the one-to-one correspondence with
    the intrinsic it replaces.
    """
    year, remainder = divmod(yyyymmdd, 10_000)
    month, day = divmod(remainder, 100)
    if year < COBOL_MIN_DATE_YEAR or year > COBOL_MAX_DATE_YEAR:
        return 1
    if month < 1 or month > 12:
        return 1
    if day < 1 or day > _days_in_month(year, month):
        return 1
    return 0


def integer_of_date(year: int, month: int, day: int) -> int:
    """Reimplement `FUNCTION integer-of-date` [common/maps04.cbl:L167].

    Returns the binary day number counted from `COBOL_DATE_EPOCH_ORDINAL`,
    1600-12-31, so that 1601-01-01 is day 1, 2025-09-21 is 155127 and
    9999-12-31 is 3067671, the maximum.

    The subtraction is integer arithmetic and therefore exact (rule R-2); no
    floating point is involved at any point.

    As in COBOL, validating the argument is the caller's job and no validation
    is added here (rule R-3): `maps04` only ever reaches this after
    `test_date_yyyymmdd` has returned zero, so the date is always a real one by
    then.
    """
    return date(year, month, day).toordinal() - COBOL_DATE_EPOCH_ORDINAL


def date_of_integer(day_number: int) -> date:
    """Reimplement `FUNCTION Date-of-integer` [common/maps04.cbl:L183].

    The inverse of `integer_of_date`: day 1 is 1601-01-01. Returns a
    `datetime.date`, which the unpack path below then renders as CCYYMMDD text.

    The COBOL intrinsic returns zero rather than failing for a day number
    outside 1 through 3067671; `ws_unpack` reproduces that at the one place it
    reaches the output. This function models the in-domain conversion only, so
    the out-of-domain result stays visible where the COBOL's zero shows up.
    """
    return date.fromordinal(day_number + COBOL_DATE_EPOCH_ORDINAL)


#  maps04 - THE PROGRAM  [common/maps04.cbl:L122-L189]
#  `procedure division using Mapa03-WS.` - one parameter, passed by reference,
#  and no return value. The COBOL has a single exit point, `Main-Exit.` at
#  [common/maps04.cbl:L188-L189], whose only statement is `exit program.`;
#  every `go to Main-Exit` in the program is therefore a Class 3 transfer and
#  becomes a bare `return` here. `Main-Exit` is not given a function of its own
#  because it holds no work - that single-return convention IS its
#  reproduction, and each of the three transfer sites is annotated below.


def maps04(ws: Maps03Ws) -> None:
    """Validate and convert a date, in place, exactly as `common/maps04.cbl` does.

    Two directions in one entry point, selected by `u_bin`:

      * `u_bin > 0` - UNPACK. The binary day number is converted to DD/MM/CCYY
        text in `u_date`.
      * otherwise - VALIDATE AND PACK. The text in `u_date` is normalised,
        checked, and on success converted to a binary day number in `u_bin`.

    Mutates `ws` and returns None, because the COBOL mutates its linkage record and
    returns nothing. THE ABSENCE of a write is as significant as a write here - see
    the reject paths below.

    ANOMALY #16, reproduced [common/maps04.cbl:L146, L154, L163]: on EITHER reject
    path the binary field `u_bin` is left COMPLETELY UNTOUCHED - not zeroed, not set
    to a sentinel, no exception raised - even though the program's own remarks at
    L163 claim "Date errors returned as A-Bin equal zero". That documented contract
    holds only because the callers zero the field themselves:
    `copybooks/Proc-ACAS-Mapser-RDB.cob:L78` and the `zz050-test-date` paragraph
    below both do. So a caller that pre-set `u_bin` to a sentinel and supplied
    "xx/yy/zzzz" still finds the sentinel afterwards, and likewise with
    "31-02-2025", which passes the six-part test and fails only the calendar check.
    """
    #  [common/maps04.cbl:L128-L129]
    #      if       A-Bin  >  zero
    #               go to  WS-Unpack.
    #  Class 4 sibling re-dispatch: the named paragraph is called and control
    #  then leaves the program, so it is a call followed by an explicit return.
    #  STRICTLY GREATER THAN ZERO, which is not interchangeable with "not zero".
    #  The program's own comment at [common/maps04.cbl:L125-L126] describes the
    #  switch as "if entry A-Bin not zero then convert to dd/mm/ccyy", but the
    #  code tests `> zero`, so a NEGATIVE binary value takes the forward TEXT
    #  path and the text decides the result. A second place where this program's
    #  comments overstate its code, independently of anomaly #16, and it is
    #  reproduced literally.
    if ws.u_bin > 0:
        ws_unpack(ws)
        return  # Class 3 -> Main-Exit [common/maps04.cbl:L188]

    #  [common/maps04.cbl:L131]  move zero to Z.
    #  `Z pic 99 binary` [common/maps04.cbl:L93] is the separator tally.
    separator_tally = 0

    #  [common/maps04.cbl:L132-L134]
    #      inspect  A-Date replacing all "." by "/".
    #      inspect  A-Date replacing all "," by "/".
    #      inspect  A-Date replacing all "-" by "/".
    #  ANOMALY, reproduced: these three statements rewrite the CALLER'S OWN
    #  10-character field in place, and they run BEFORE the reject test, so a
    #  date that is subsequently rejected still comes back with its separators
    #  normalised - a caller-visible side effect on the failure path. Three
    #  separate statements in the written order "." then "," then "-", each
    #  assigning back to the linkage field, which is also why this function must
    #  never be memoised. The first statement materialises the field at its
    #  declared 10-character width, which the positional tests below depend on.
    ws.u_date = _alphanumeric_move(ws.u_date, DATE_TEXT_LENGTH).replace(".", "/")
    ws.u_date = ws.u_date.replace(",", "/")
    ws.u_date = ws.u_date.replace("-", "/")

    #  [common/maps04.cbl:L135]  inspect A-Date tallying Z for all "/".
    #  The tally counts "/" across the WHOLE ten characters, not just positions
    #  3 and 6. Two consequences, both reproduced: a text carrying three or
    #  more "/" is rejected by part one of the test below, while a text with
    #  exactly two "/" in the WRONG positions passes the tally and is then
    #  judged only by the positional numeric tests.
    separator_tally = ws.u_date.count("/")

    #  [common/maps04.cbl:L140-L146]  THE SIX-PART REJECT TEST
    #      if       Z not = 2 or
    #               A-Days not numeric or
    #               A-Month not numeric or
    #               A-CC   not numeric or
    #               A-Days < 01 or > 31 or
    #               A-Month < 01 or > 12
    #               go to Main-Exit.
    #
    #  EXACTLY SIX PARTS, in exactly this order, with exactly these operands.
    #  Agent Action Plan section 0.7.2 R-3 requires it reproduced "exactly as
    #  written", and no part may be added, removed, reordered or strengthened.
    #
    #  *** A-Year IS NOT TESTED FOR NUMERIC ANYWHERE IN THIS LIST. ***
    #  The century (`A-CC`) is checked; the year within the century
    #  (`A-Year`, offset 9) is not. That gap is NOT an oversight to be
    #  corrected: it is observable in the compiled program's output, which
    #  ACCEPTS a date with a non-numeric year and posts a different year for it.
    #  See `_zoned_decimal_value` for the measured rule and the four cases it
    #  was verified against. Adding a year check here - or letting a regex, an
    #  int() conversion or a try/except reject such a value - would silently
    #  reject dates the specification accepts.
    #
    #  Parts five and six reproduce COBOL's abbreviated combined relations,
    #  `A-Days < 01 or > 31` meaning `A-Days < 1 OR A-Days > 31`; each is
    #  bracketed so that this remains six top-level operands rather than eight.
    #  Their int() conversions cannot fail: Python evaluates `or` left to right,
    #  so part five is only reached once part two has proved the days numeric,
    #  and part six only once part three has proved the month numeric.
    # -----------------------------------------------------------------------
    days_text = reading_field(ws, "u-days")
    month_text = reading_field(ws, "u-month")
    if (
        separator_tally != 2  # part 1  [L140]
        or not _is_numeric(days_text)  # part 2  [L141]
        or not _is_numeric(month_text)  # part 3  [L142]
        or not _is_numeric(reading_field(ws, "u-cc"))  # part 4  [L143]
        or (int(days_text) < 1 or int(days_text) > 31)  # part 5  [L144]
        or (int(month_text) < 1 or int(month_text) > 12)  # part 6  [L145]
    ):
        #  Class 3 -> Main-Exit [common/maps04.cbl:L146].
        #  ANOMALY #16: u_bin is NOT written. Returning here leaves whatever the
        #  caller put there, and that is the entire rejection signal.
        return

    #  [common/maps04.cbl:L148-L151]  assemble Test-Date as CCYYMMDD
    #      move     A-CC    to TD-CC.
    #      move     A-Year  to TD-YY.
    #      move     A-Month to TD-MM.
    #      move     A-Days  to TD-DD.
    #  `Test-Date` [common/maps04.cbl:L94-L99] is an 8-byte group of four 2-byte
    #  fields, and `Test-Date9 redefines Test-Date pic 9(8)` [L100] reads all
    #  eight bytes as one number. All four moves run in the written order and
    #  every byte of the group is written, so its previous working-storage
    #  content cannot leak through. A-Year arrives here without having been
    #  proved numeric, by the gap documented above; its characters are carried
    #  through as-is, exactly as the frozen program carries them.
    test_date = " " * TEST_DATE_LENGTH
    cc_text = reading_field(ws, "u-cc")  # A-CC     [common/maps04.cbl:L113]
    yy_text = reading_field(ws, "u-yy")  # A-Year   [common/maps04.cbl:L114]
    test_date = _poke(test_date, 1, 2, cc_text, TEST_DATE_LENGTH)  # [L148]
    test_date = _poke(test_date, 3, 2, yy_text, TEST_DATE_LENGTH)  # [L149]
    test_date = _poke(test_date, 5, 2, month_text, TEST_DATE_LENGTH)  # [L150]
    test_date = _poke(test_date, 7, 2, days_text, TEST_DATE_LENGTH)  # [L151]

    #  Reading the 8-byte group as `Test-Date9 pic 9(8)`. This is where a
    #  non-numeric year becomes a number - see `_zoned_decimal_value`.
    test_date9 = _zoned_decimal_value(test_date)

    #  [common/maps04.cbl:L153-L154]
    #      if       FUNCTION Test-Date-YYYYMMDD (Test-Date9) not = zero
    #               go to Main-Exit.
    #  The calendar check - the one that catches February and leap years, and
    #  the reason the six tests above are described in the source itself as
    #  "Very basic Testing".
    if test_date_yyyymmdd(test_date9) != 0:
        #  Class 3 -> Main-Exit [common/maps04.cbl:L154].
        #  ANOMALY #16 again, on the second and independent reject path: u_bin
        #  is NOT written here either. "31/02/2025" reaches exactly this point.
        return

    #  [common/maps04.cbl:L167]
    #      move     FUNCTION integer-of-Date (Test-Date9) to A-Bin.
    #  The single successful write to the binary field in the whole forward
    #  path. `Test-Date9` is a validated CCYYMMDD number by now, so splitting it
    #  into year, month and day cannot fail.
    year, remainder = divmod(test_date9, 10_000)
    month, day = divmod(remainder, 100)
    ws.u_bin = integer_of_date(year, month, day)

    #  [common/maps04.cbl:L168]  go to Main-Exit.
    #  Class 3 -> Main-Exit. Explicit rather than implicit, because the COBOL
    #  writes the transfer explicitly and a reader comparing the two should find
    #  it here.
    return


def ws_unpack(ws: Maps03Ws) -> None:
    """Reproduce the `WS-Unpack` paragraph [common/maps04.cbl:L181-L186].

    Converts the binary day number in `u_bin` to DD/MM/CCYY text in `u_date`.
    Reached only from the `u_bin > 0` switch at the head of `maps04`, and it
    validates NOTHING: `FUNCTION Date-of-integer` is applied to whatever
    positive integer arrived.

    That raises a question `datetime` cannot answer: `date.fromordinal` raises
    for an out-of-range ordinal while `FUNCTION Date-of-integer` returns zero
    for one, its ISO domain running 1 (1601-01-01) to 3067671 (9999-12-31).
    Taking that zero at face value, an out-of-domain day number yields
    "00/00/0000" - the zero flows into the 8-byte group as "00000000" and the
    three moves below write zeros over the seed's zeros, leaving the seed's
    separators standing:

        u_bin = 1        -> "01/01/1601"
        u_bin = 3067671  -> "31/12/9999"
        u_bin = 3067672  -> "00/00/0000"

    Reproduced below rather than allowed to raise, on that reasoning, and
    flagged here so the compiled oracle can arbitrate it (rule R-6).
    """
    #  [common/maps04.cbl:L182]  move "00/00/0000" to A-Date.
    #  THE SEED. This literal is the sole source of the separators in the
    #  unpacked date: positions 3 and 6 hold "/" and are never overwritten,
    #  because the three moves below write only offsets 7-10, 4-5 and 1-2.
    #  That, and nothing else, is why the unpacked form is DD/MM/CCYY.
    ws.u_date = UNPACK_SEED

    #  [common/maps04.cbl:L183]
    #      move FUNCTION Date-of-integer (A-Bin) to Test-Date.  *> CCYYMMDD
    if COBOL_MIN_DATE_INTEGER <= ws.u_bin <= COBOL_MAX_DATE_INTEGER:
        converted = date_of_integer(ws.u_bin)
        test_date = f"{converted.year:04d}{converted.month:02d}{converted.day:02d}"
    else:
        #  Out of domain the intrinsic yields zero, so the 8-byte group reads
        #  "00000000".
        test_date = "0" * TEST_DATE_LENGTH

    #  [common/maps04.cbl:L184-L186]
    #      move     TD-CCYY to A-CCYY.      *> 4 chars at offset 7
    #      move     TD-MM   to A-Month.     *> 2 chars at offset 4
    #      move     TD-DD   to A-Days.      *> 2 chars at offset 1
    #  In the written order, which is CCYY then MM then DD - the maintainer's
    #  own comment on the last of the three reads "Now UK Date".
    # -----------------------------------------------------------------------
    #  Each of the three writes lands on its own item of the `u-UK` reading and
    #  leaves every other character of the ten alone, which is what preserves
    #  the seed's separators.
    set_reading_field(ws, "u-year", _ref_mod(test_date, 1, 4))  # TD-CCYY [L184]
    set_reading_field(ws, "u-month", _ref_mod(test_date, 5, 2))  # TD-MM  [L185]
    set_reading_field(ws, "u-days", _ref_mod(test_date, 7, 2))  # TD-DD   [L186]

    #  Falls straight through to `Main-Exit` in the COBOL; the caller's return
    #  statement stands in for that Class 3 transfer.


#  THE WRAPPER SECTION - ONE IMPLEMENTATION, TWO PUBLISHED NAMES
#  Six programs wrap the `CALL` in a section of their own, and the body is the
#  same single statement in every one: `call "maps04" using maps03-ws.`
#  ANOMALY #22, reproduced - and it occurs in TWO programs, not one. Agent
#  Action Plan section 0.6.7 entry 22 cites only gl070; gl051 carries the
#  identical defect. In both, the SECTION is named after the interface copybook
#  (maps03) while its EXIT LABEL is named after the called program:
#      gl051 section maps03 L1273 / exit maps04-exit L1278   <- anomaly #22
#      gl070 section maps03 L603  / exit maps04-exit L608    <- anomaly #22
#      sl060 L1292, sl100 L808, pl060 L1146, pl100 L789      agree
#  Both names are published over ONE implementation, on the reasoning Agent
#  Action Plan section 0.3.3 gives for the dual-aliased data-access facade.


def maps03(ws: Maps03Ws) -> None:
    """Reproduce the wrapper section named `maps03`, carried by gl070 and gl051.

    Locators: [general/gl070.cbl:L603-L609] and [general/gl051.cbl:L1273-L1278].

    ANOMALY #22: the section is named after the interface copybook while its
    exit label is `maps04-exit`, named after the program it calls. Its body is
    the single statement `call "maps04" using maps03-ws.`, so it is exactly
    `maps04` under a second name, and it delegates rather than duplicating.

    Published so that a reader following the General Ledger convention finds a
    correspondingly named function; the four Sales and Purchase carriers name
    the same section `maps04` and should call that instead.
    """
    maps04(ws)


#  THE PRESENTATION-FORMAT CONDITION NAMES
#  [copybooks/wssystem.cob:L128-L132]
#  Agent Action Plan section 0.1.2 rule 12 maps an 88-level condition name to
#  "a predicate function over the record", so the three the date sections
#  actually test become the three predicates below.
#  `Date-Valid-Formats` (values 1 2 3) is deliberately NOT published. It is
#  declared in the copybook and never tested by any date section - they test
#  `Date-Form = zero` and default to 1 instead. Publishing a predicate for the
#  test the COBOL declines to make would invite a caller to make it, which
#  would be a new validation (rule R-3). A Date-Form of 4 or 9 consequently
#  falls through every branch and is treated as International, and that is the
#  specified behaviour.


def date_form_is_uk(date_form: int) -> bool:
    """`88 Date-UK value 1` - dd/mm/yyyy [copybooks/wssystem.cob:L129]."""
    return date_form == DATE_FORM_UK


def date_form_is_usa(date_form: int) -> bool:
    """`88 Date-USA value 2` - mm/dd/yyyy [copybooks/wssystem.cob:L130]."""
    return date_form == DATE_FORM_USA


def date_form_is_intl(date_form: int) -> bool:
    """`88 Date-Intl value 3` - yyyy/mm/dd [copybooks/wssystem.cob:L131].

    Published for completeness and for callers that need the test, but note that
    NONE of the four date sections uses it: each reaches its International
    branch by FALLING THROUGH the UK and USA tests, never by testing this
    condition. That is why a Date-Form of 4 or 9 is treated as International.
    """
    return date_form == DATE_FORM_INTL


#  THE SECTIONS' WORKING STORAGE  [general/gl070.cbl:L172-L194]
#      01  ws-Test-Date            pic x(10).
#      01  ws-date-formats.
#          03  ws-swap             pic xx.
#          03  ws-Conv-Date        pic x(10).
#          03  ws-date             pic x(10).
#          03  ws-UK   redefines ws-date.  ws-days xx / ws-month xx / ws-year x(4)
#          03  ws-USA  redefines ws-date.  ws-usa-month xx / ws-usa-days xx
#          03  ws-Intl redefines ws-date.  ws-intl-year x(4) / -month xx / -days xx
#  The redefines are alphanumeric, so the USA swap moves characters, never a
#  number. `ws-Test-Date` is a separate `01` item bundled into the same mutable
#  dataclass because the `zz050` sections read and write it alongside the group.


@dataclass
class WsDateFormats:
    """`ws-Test-Date` plus the `ws-date-formats` group [general/gl070.cbl:L172-L194].

    Attributes:
        ws_test_date: `ws-Test-Date pic x(10)` - the input text of `zz050`.
        ws_swap: `ws-swap pic xx` - the two-character scratch the USA branch
            swaps days and month through.
        ws_conv_date: `ws-Conv-Date pic x(10)` - declared in the group, unused
            by all four date sections.
        ws_date: `ws-date pic x(10)` - the output text of all four sections.
    """

    ws_test_date: str = field(default=" " * DATE_TEXT_LENGTH)
    ws_swap: str = field(default="  ")
    ws_conv_date: str = field(default=" " * DATE_TEXT_LENGTH)
    ws_date: str = field(default=" " * DATE_TEXT_LENGTH)

    # -- `ws-UK redefines ws-date` -----------------------------------------

    @property
    def ws_days(self) -> str:
        """`ws-days pic xx` - offset 1, length 2."""
        return _ref_mod(self.ws_date, 1, 2)

    @ws_days.setter
    def ws_days(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 1, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_month(self) -> str:
        """`ws-month pic xx` - offset 4, length 2."""
        return _ref_mod(self.ws_date, 4, 2)

    @ws_month.setter
    def ws_month(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 4, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_year(self) -> str:
        """`ws-year pic x(4)` - offset 7, length 4."""
        return _ref_mod(self.ws_date, 7, 4)

    @ws_year.setter
    def ws_year(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 7, 4, value, DATE_TEXT_LENGTH)

    # -- `ws-USA redefines ws-date` ----------------------------------------

    @property
    def ws_usa_month(self) -> str:
        """`ws-usa-month pic xx` - offset 1, length 2."""
        return _ref_mod(self.ws_date, 1, 2)

    @ws_usa_month.setter
    def ws_usa_month(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 1, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_usa_days(self) -> str:
        """`ws-usa-days pic xx` - offset 4, length 2."""
        return _ref_mod(self.ws_date, 4, 2)

    @ws_usa_days.setter
    def ws_usa_days(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 4, 2, value, DATE_TEXT_LENGTH)

    # -- `ws-Intl redefines ws-date` ---------------------------------------

    @property
    def ws_intl_year(self) -> str:
        """`ws-intl-year pic x(4)` - offset 1, length 4."""
        return _ref_mod(self.ws_date, 1, 4)

    @ws_intl_year.setter
    def ws_intl_year(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 1, 4, value, DATE_TEXT_LENGTH)

    @property
    def ws_intl_month(self) -> str:
        """`ws-intl-month pic xx` - offset 6, length 2."""
        return _ref_mod(self.ws_date, 6, 2)

    @ws_intl_month.setter
    def ws_intl_month(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 6, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_intl_days(self) -> str:
        """`ws-intl-days pic xx` - offset 9, length 2."""
        return _ref_mod(self.ws_date, 9, 2)

    @ws_intl_days.setter
    def ws_intl_days(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 9, 2, value, DATE_TEXT_LENGTH)


def _swap_days_and_month(ws: WsDateFormats) -> None:
    """Swap days and month through the `ws-swap` scratch field (USA branch).

        move ws-days to ws-swap
        move ws-month to ws-days
        move ws-swap to ws-month

    The same three statements appear in every section that carries it, so it is
    written once: [general/gl070.cbl:L588-L590] in zz070,
    [general/gl070.cbl:L558-L560] in zz060, [general/gl051.cbl:L1188-L1190] in
    zz050, and at the corresponding lines of the other carriers.

    Note what it does NOT touch: the separators. Only the two-character day and
    month windows are exchanged, so "21/09/2025" becomes "09/21/2025" with the
    "/" at positions 3 and 6 left where they were. The scratch field is left
    holding the original day characters afterwards, exactly as the COBOL leaves
    it, because the third statement reads it rather than clearing it.
    """
    ws.ws_swap = _alphanumeric_move(ws.ws_days, 2)
    ws.ws_days = ws.ws_month
    ws.ws_month = ws.ws_swap


#  zz070-Convert-Date  -  CONSOLIDATED FROM 10 CARRIERS
#  Reference body: [general/gl070.cbl:L573-L601]. The ten carriers are:
#      gl051 L1243  gl070 L573  gl072 L467  gl080 L719  sl055 L694
#      sl060 L1262  sl100 L778  pl055 L599  pl060 L1116  pl100 L759
#  Agent Action Plan section 0.6.3 permits this consolidation; each carrier
#  spells the same statements in the same order.


def zz070_convert_date(ws: WsDateFormats, to_day: str, date_form: int) -> int:
    """`zz070-Convert-Date`: reformat the run date into the configured form.

    Input is `to-day pic x(10)`, the run date the menu passes down through
    linkage; output is `ws.ws_date`, written in place.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten.
        to_day: `to-day pic x(10)` - the run date text, DD/MM/CCYY.
        date_form: `System-Record.Date-Form` on entry.

    Returns:
        The EFFECTIVE `Date-Form`. The COBOL writes a defaulted value straight
        back into the system record, so a caller MUST store this return value
        back into `System-Record.Date-Form` for the migration to stay faithful -
        see the note at the default site below.

    This function does not read a clock (rule R-6): the run date arrives as an
    argument, which is exactly how every in-scope COBOL program receives it.
    """
    #  [general/gl070.cbl:L581]  move to-day to ws-date.
    ws.ws_date = _alphanumeric_move(to_day, DATE_TEXT_LENGTH)

    #  [general/gl070.cbl:L583-L584]
    #      if       Date-Form = zero
    #               move 1 to Date-Form.
    #  THIS WRITES BACK INTO THE SYSTEM RECORD, and the system record is a table
    #  row (`SYSTEM-REC`), so the write is observable in a state diff and not
    #  merely in memory. It is reproduced by returning the effective value for
    #  the caller to store.
    #  Note that the test is `= zero` and the default is 1: the declared
    #  condition name `Date-Valid-Formats` (values 1 2 3) is NOT used here, so
    #  an out-of-range Date-Form such as 4 is neither defaulted nor rejected -
    #  it simply falls through to the International branch below.
    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    #  [general/gl070.cbl:L585-L586]  if Date-UK go to zz070-Exit.
    #  Class 3 section exit -> `zz070-Exit. exit section.` [L600-L601].
    #  The UK form is what `to-day` already holds, so there is nothing to do.
    if date_form_is_uk(date_form):
        return date_form

    #  [general/gl070.cbl:L587-L591]  if Date-USA ... go to zz070-Exit.
    #  Class 3 section exit.
    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)  # [L588-L590]
        return date_form

    #  [general/gl070.cbl:L593-L598]  the International branch, reached by
    #  FALL-THROUGH rather than by testing `Date-Intl`. The source's own comment
    #  is "So its International date format".
    #      move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
    #      move     to-day (7:4) to ws-Intl-Year.
    #      move     to-day (4:2) to ws-Intl-Month.
    #      move     to-day (1:2) to ws-Intl-Days.
    #  The seed literal at [general/gl070.cbl:L595] is moved in purely so its
    #  "/" characters land at positions 5 and 8; the three reference-modified
    #  moves overwrite offsets 1-4, 6-7 and 9-10 and leave those separators
    #  standing. The inline comment "swap Intl to UK form" names the opposite
    #  direction from what the code does; the code is the specification.
    ws.ws_date = UK_TO_INTL_SEED  # [L595]
    ws.ws_intl_year = _ref_mod(to_day, 7, 4)  # [L596]
    ws.ws_intl_month = _ref_mod(to_day, 4, 2)  # [L597]
    ws.ws_intl_days = _ref_mod(to_day, 1, 2)  # [L598]

    #  Falls through to `zz070-Exit. exit section.` [L600-L601].
    return date_form


#  zz060-Convert-Date  -  CONSOLIDATED, IDENTICAL IN 6 CARRIERS BUT FOR ONE
#                          TOKEN
#  Reference body: [general/gl070.cbl:L538-L571]. Normalised diff across all six
#  carriers - gl051 L1208, gl070 L538, sl060 L1227, sl100 L743, pl060 L1081,
#  pl100 L724 - shows exactly ONE difference between them:
#      -  perform maps03.        <- gl051 and gl070
#      +  perform maps04.        <- sl060, sl100, pl060 and pl100
#  Since both wrapper sections have the identical single-statement body, the two
#  spellings invoke the same code and the section is safely consolidated. The
#  wrapper is nonetheless taken as an EXPLICIT, NON-DEFAULTED argument so the
#  calling program states which convention it follows, keeping the distinction
#  visible for traceability (rule R-5).


def zz060_convert_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """`zz060-Convert-Date`: unpack a binary date, then reformat it for presentation.

    This is `zz070` with a conversion in front of it: input is `u-bin`, not a
    text date, so the wrapper is performed first to turn the binary day number
    into text and only then is the presentation format applied.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten.
        maps03_ws: the shared linkage record. `u_bin` is the input; the wrapper
            writes `u_date` in place.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: the wrapper section this program performs - pass `maps03` from
            gl051 or gl070, `maps04` from sl060, sl100, pl060 or pl100. Required
            and never defaulted, so the caller states its own convention.

    Returns:
        The effective `Date-Form`, to be stored back into the system record as
        described in `zz070_convert_date`.

    The section's own header comment at [general/gl070.cbl:L543-L545] claims
    "u-date & ws-Date = spaces if invalid date". That is not quite what happens:
    `ws_unpack` always writes the "00/00/0000" seed first, so a `u_bin` that was
    greater than zero can never come back as spaces. The spaces guard can
    therefore only fire when the caller left `u_date` as spaces AND `u_bin` was
    not greater than zero - in which case `maps04` took its forward text path and
    rejected the empty text. The guard is reproduced as written and the
    misleading comment is left uncorrected.
    """
    #  [general/gl070.cbl:L547]  perform maps03.  (or maps04 - see above)
    wrapper(maps03_ws)

    #  [general/gl070.cbl:L548-L550]
    #      if       u-date = spaces
    #               move spaces to ws-Date
    #               go to zz060-Exit.
    #  Class 3 section exit. Compared against figurative SPACES across the whole
    #  declared 10-byte field, so the field is materialised at its full width
    #  before the comparison.
    if _alphanumeric_move(maps03_ws.u_date, DATE_TEXT_LENGTH) == " " * DATE_TEXT_LENGTH:
        ws.ws_date = " " * DATE_TEXT_LENGTH
        return date_form

    #  [general/gl070.cbl:L551]  move u-date to ws-date.
    ws.ws_date = _alphanumeric_move(maps03_ws.u_date, DATE_TEXT_LENGTH)

    #  [general/gl070.cbl:L553-L554]  the same write-back into the system record
    #  as zz070's; see the note there.
    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    #  [general/gl070.cbl:L555-L556]  if Date-UK go to zz060-Exit.  Class 3.
    if date_form_is_uk(date_form):
        return date_form

    #  [general/gl070.cbl:L557-L561]  if Date-USA ... go to zz060-Exit.  Class 3.
    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)  # [L558-L560]
        return date_form

    #  [general/gl070.cbl:L563-L568]  the International branch, again by
    #  fall-through. Identical to zz070's except that it reads the unpacked
    #  `u-date` rather than `to-day`, and it uses the SAME seed literal and the
    #  SAME offsets - (7:4), (4:2), (1:2). Contrast zz050, which uses a
    #  different literal and different offsets because it converts in the
    #  opposite direction.
    ws.ws_date = UK_TO_INTL_SEED  # [L565]
    ws.ws_intl_year = _ref_mod(maps03_ws.u_date, 7, 4)  # [L566]
    ws.ws_intl_month = _ref_mod(maps03_ws.u_date, 4, 2)  # [L567]
    ws.ws_intl_days = _ref_mod(maps03_ws.u_date, 1, 2)  # [L568]

    #  Falls through to `zz060-Exit. exit section.` [L570-L571].
    return date_form


#  zz050-Validate-Date  -  NOT EQUIVALENT ACROSS CARRIERS.
#                          PUBLISHED AS TWO SEPARATE FUNCTIONS.
#  Agent Action Plan section 0.6.3 asserts these section bodies are "textually
#  equivalent" and so may be consolidated. For zz050 the frozen source
#  contradicts that, and consolidating would lose a caller-visible side effect.
#  A normalised diff across the five carriers - gl051 L1169, sl060 L1192,
#  sl100 L708, pl060 L1046, pl100 L689 - splits them in two: gl051 alone
#  carries three extra statements at [general/gl051.cbl:L1178-L1180] that
#  rewrite the caller's own `ws-test-date` in place before anything else, while
#  sl060, sl100, pl060 and pl100 spell one and the same body. Two
#  functions therefore, and the mutating variant is not reachable through a
#  defaulted argument. Both share the `zz050-test-date` paragraph below.


def zz050_test_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> None:
    """Reproduce the `zz050-test-date` paragraph [general/gl051.cbl:L1200-L1203].

        move     ws-date to u-date.
        move     zero to u-bin.
        perform  maps03.            (or maps04)

    Common to all five carriers of `zz050`. Reached from the UK and USA branches
    by a Class 4 sibling re-dispatch, and by fall-through from the International
    branch.

    ⭐ THE CALLER PRE-ZERO. `move zero to u-bin` is one of the only two places
    in the whole call chain that zeroes the binary field before calling
    `maps04`, and it is the reason `maps04`'s documented "Date errors returned
    as A-Bin equal zero" contract [common/maps04.cbl:L163] appears to hold. It
    does not hold in `maps04` itself - see anomaly #16 there. The other
    pre-zeroing caller is [copybooks/Proc-ACAS-Mapser-RDB.cob:L78].

    Agent Action Plan section 0.6.8 records that not every in-scope caller
    pre-zeroes, so this is preserved exactly where the COBOL puts it - in the
    CALLER - rather than being pushed down into `maps04` where it would mask the
    anomaly for every caller at once.

    After this returns, `maps03_ws.u_bin` is non-zero if and only if the date
    was valid. That is the section's entire output contract, per its own header
    comment "u-bin not zero if valid date".
    """
    #  [general/gl051.cbl:L1201]  move ws-date to u-date.
    maps03_ws.u_date = _alphanumeric_move(ws.ws_date, DATE_TEXT_LENGTH)

    #  [general/gl051.cbl:L1202]  move zero to u-bin.   <- the caller pre-zero
    maps03_ws.u_bin = 0

    #  [general/gl051.cbl:L1203]  perform maps03.  (maps04 in the other four)
    wrapper(maps03_ws)

    #  Falls through to `zz050-exit. exit section.` [general/gl051.cbl:L1205-L1206].


def _zz050_validate_date_body(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """Run the part of `zz050-Validate-Date` that all five carriers share.

    Covers [general/gl051.cbl:L1182-L1203] - everything from `move ws-test-date
    to ws-date` onwards. The three `inspect` statements that precede it in
    gl051 only are NOT here; they belong to `zz050_validate_date_gl051` alone,
    which is the whole point of the split.
    """
    #  [general/gl051.cbl:L1182]  move ws-test-date to ws-date.
    ws.ws_date = _alphanumeric_move(ws.ws_test_date, DATE_TEXT_LENGTH)

    #  [general/gl051.cbl:L1183-L1184]  the same system-record write-back as
    #  zz060 and zz070; see the note in `zz070_convert_date`.
    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    #  [general/gl051.cbl:L1185-L1186]  if Date-UK go to zz050-test-date.
    #  Class 4 sibling re-dispatch: the target is a peer PARAGRAPH that performs
    #  work and then itself transfers control to the section exit. So it becomes
    #  a named call followed by an explicit return, not a bare return.
    if date_form_is_uk(date_form):
        zz050_test_date(ws, maps03_ws, wrapper=wrapper)
        return date_form

    #  [general/gl051.cbl:L1187-L1191]  if Date-USA ... go to zz050-test-date.
    #  Class 4, as above.
    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)  # [L1188-L1190]
        zz050_test_date(ws, maps03_ws, wrapper=wrapper)
        return date_form

    #  [general/gl051.cbl:L1193-L1198]  the International branch, by
    #  fall-through.
    #      move     "dd/mm/ccyy" to ws-date.  *> swap Intl to UK form
    #      move     ws-test-date (1:4) to ws-Year.
    #      move     ws-test-date (6:2) to ws-Month.
    #      move     ws-test-date (9:2) to ws-Days.
    #  THE OPPOSITE DIRECTION FROM zz060 AND zz070, and it differs in both
    #  details: the seed is "dd/mm/ccyy" so the separators land at 3 and 6
    #  rather than 5 and 8, and the source is read in International order at
    #  (1:4), (6:2) and (9:2) into the UK-ordered targets. This converts
    #  International INTO UK because zz050 normalises operator input; copying
    #  between the two directions would silently produce a wrong date.
    ws.ws_date = INTL_TO_UK_SEED  # [L1195]
    ws.ws_year = _ref_mod(ws.ws_test_date, 1, 4)  # [L1196]
    ws.ws_month = _ref_mod(ws.ws_test_date, 6, 2)  # [L1197]
    ws.ws_days = _ref_mod(ws.ws_test_date, 9, 2)  # [L1198]

    #  Falls through into the `zz050-test-date` paragraph [L1200].
    zz050_test_date(ws, maps03_ws, wrapper=wrapper)
    return date_form


def zz050_validate_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """`zz050-Validate-Date` AS CARRIED BY sl060, sl100, pl060 AND pl100.

    Carriers, which all spell one body:
        sales/sl060.cbl:L1192-L1225
        sales/sl100.cbl:L708-L741
        purchase/pl060.cbl:L1046-L1079
        purchase/pl100.cbl:L689-L722

    Converts operator input in `ws.ws_test_date` from the configured
    presentation format into UK order, then validates it through `maps04`.

    THIS VARIANT DOES NOT MUTATE `ws.ws_test_date`. It has no separator
    normalisation of any kind, so an input using "." or "-" as its separator
    reaches `maps04` unchanged - where `maps04`'s own three `inspect` statements
    then normalise it, but in `maps03_ws.u_date` rather than here. gl051's
    variant additionally normalises the input field itself; use
    `zz050_validate_date_gl051` for that program and only that program.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten;
            `ws.ws_test_date` is READ ONLY here.
        maps03_ws: the shared linkage record, written by `zz050_test_date`.
            On return `u_bin` is non-zero if and only if the date was valid.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: `maps04` for all four of this variant's carriers. Required and
            never defaulted.

    Returns:
        The effective `Date-Form`, to be stored back into the system record.
    """
    return _zz050_validate_date_body(ws, maps03_ws, date_form, wrapper)


def zz050_validate_date_gl051(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """`zz050-Validate-Date` AS CARRIED BY gl051 ONLY - the divergent variant.

    Carrier: general/gl051.cbl:L1169-L1206.

    Identical to `zz050_validate_date` EXCEPT that it opens with three
    `inspect ... replacing all` statements at [general/gl051.cbl:L1178-L1180]
    which none of the other four carriers has:

        inspect  ws-test-date replacing all "." by "/".
        inspect  ws-test-date replacing all "," by "/".
        inspect  ws-test-date replacing all "-" by "/".

    These rewrite the CALLER'S OWN `ws-test-date` field in place, so gl051's
    working storage differs after the call from what the other four programs'
    would hold for the same input. That divergence is deliberate here,
    not tidied away: this is published as its own named function precisely so
    that it cannot be reached by accident or through a defaulted argument, and
    so that a reader of gl051 finds a function that matches gl051.

    Args:
        ws: the section's working storage. BOTH `ws.ws_test_date` AND
            `ws.ws_date` are overwritten.
        maps03_ws: the shared linkage record, written by `zz050_test_date`.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: `maps03` for gl051 - the anomaly #22 spelling. Required and
            never defaulted.

    Returns:
        The effective `Date-Form`, to be stored back into the system record.
    """
    #  [general/gl051.cbl:L1178-L1180]  THE THREE STATEMENTS gl051 ALONE HAS.
    #  Applied in the written order "." then "," then "-", each assigning back
    #  to the caller's field. The field is materialised at its declared
    #  10-character width by the first of them, as `maps04` does with its own.
    #  Note that this duplicates work `maps04` will do anyway on `u_date`
    #  [common/maps04.cbl:L132-L134]; the difference, and the only reason this
    #  variant exists, is WHICH FIELD ends up normalised. Here it is gl051's own
    #  `ws-test-date` as well.
    ws.ws_test_date = _alphanumeric_move(ws.ws_test_date, DATE_TEXT_LENGTH)
    ws.ws_test_date = ws.ws_test_date.replace(".", "/")
    ws.ws_test_date = ws.ws_test_date.replace(",", "/")
    ws.ws_test_date = ws.ws_test_date.replace("-", "/")

    return _zz050_validate_date_body(ws, maps03_ws, date_form, wrapper)


#  THE PUBLIC SURFACE
#  Both `zz050` variants are exported and neither is the default; the storage
#  helpers and `_zz050_validate_date_body` stay private because they are
#  mechanics rather than migrated paragraphs. Sorted alphabetically to satisfy
#  the package lint gate - rule R-5 traceability lives in the module docstring
#  and at each definition site, not in this list.
__all__: Final[tuple[str, ...]] = (
    "COBOL_DATE_EPOCH_ORDINAL",
    "COBOL_MAX_DATE_INTEGER",
    "COBOL_MAX_DATE_YEAR",
    "COBOL_MIN_DATE_INTEGER",
    "COBOL_MIN_DATE_YEAR",
    "DATE_FORM_INTL",
    "DATE_FORM_UK",
    "DATE_FORM_UNSET",
    "DATE_FORM_USA",
    "DATE_TEXT_LENGTH",
    "INTL_TO_UK_SEED",
    "TEST_DATE_LENGTH",
    "UK_TO_INTL_SEED",
    "UNPACK_SEED",
    #  RE-EXPORT, not a definition. This name is the SAME class object as
    #  `acas_posting.records.maps03.Maps03Ws`; it is listed so that
    #  `dates.maps04(dates.Maps03Ws())` reads as one API and so that a reader
    #  following the section 0.4.3 translation finds it on the module the call
    #  belongs to.
    "Maps03Ws",
    "WsDateFormats",
    "date_form_is_intl",
    "date_form_is_uk",
    "date_form_is_usa",
    "date_of_integer",
    "integer_of_date",
    "maps03",
    "maps04",
    "reading_field",
    "set_reading_field",
    "test_date_yyyymmdd",
    "ws_unpack",
    "zz050_test_date",
    "zz050_validate_date",
    "zz050_validate_date_gl051",
    "zz060_convert_date",
    "zz070_convert_date",
)
