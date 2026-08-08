"""Date validation and conversion, migrated from `common/maps04.cbl`.

The whole of the ACAS date logic the batch posting cycle reaches,
reimplemented rather than called (R-1), and covering two bodies of COBOL that
the frozen tree keeps apart:

  1. `common/maps04.cbl` - the CALLed sub-program that converts a 10-character
     UK date text to and from a binary day number, as `maps04` and `ws_unpack`.
  2. The date sections each in-scope posting program carries privately -
     validation, the two conversion variants and the wrapper around the date
     module - as `zz050_*`, `zz060_convert_date`, `zz070_convert_date` and
     `maps03`. Their bodies are textually equivalent across the programs, which
     is why consolidating them here is safe.

Two behaviours are load-bearing and reproduced exactly. The epoch is
1600-12-31 [common/maps04.cbl:L39-L41], which the maintainer flags as making
the module unusable inside IRS as it stands. And a rejected date leaves the
output binary field UNCHANGED rather than zeroed [common/maps04.cbl:L146]; the
documented "errors return zero" contract holds only because callers pre-zero
the field [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], so callers that do not
observe whatever they left there.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader
from acas_posting.records.maps03 import Maps03Ws

# THE EPOCH [common/maps04.cbl:L167] `FUNCTION integer-of-date` returns 1 for
# 1601-01-01, so day zero is 1600-12-31.
COBOL_DATE_EPOCH_ORDINAL: Final[int] = date(1600, 12, 31).toordinal()

# `FUNCTION Test-Date-YYYYMMDD` returns zero for a valid date and non-zero otherwise,
# over the range the epoch implies: 16001231 and 00000000 are rejected, 16010101 and
# 99991231 accepted.
COBOL_MIN_DATE_YEAR: Final[int] = 1601
COBOL_MAX_DATE_YEAR: Final[int] = 9999

# The corresponding binary day numbers, derived from the year bounds above so the two
# can never disagree: 1 for 1601-01-01, 3067671 for 9999-12-31.
COBOL_MIN_DATE_INTEGER: Final[int] = (
    date(COBOL_MIN_DATE_YEAR, 1, 1).toordinal() - COBOL_DATE_EPOCH_ORDINAL
)
COBOL_MAX_DATE_INTEGER: Final[int] = (
    date(COBOL_MAX_DATE_YEAR, 12, 31).toordinal() - COBOL_DATE_EPOCH_ORDINAL
)

DATE_TEXT_LENGTH: Final[int] = 10
TEST_DATE_LENGTH: Final[int] = 8

# Each of these is moved into a 10-character field purely so that the SEPARATOR
# characters land in fixed positions.

# [common/maps04.cbl:L182] - the unpack seed.
UNPACK_SEED: Final[str] = "00/00/0000"

UK_TO_INTL_SEED: Final[str] = "ccyy/mm/dd"

# [general/gl051.cbl:L1195] - used by zz050, which converts International order INTO UK.
INTL_TO_UK_SEED: Final[str] = "dd/mm/ccyy"

# THE PRESENTATION-FORMAT SWITCH [copybooks/wssystem.cob:L128-L132] 05 Date-Form pic 9.
# 88 Date-UK value 1. *> dd/mm/yyyy 88 Date-USA value 2. *> mm/dd/yyyy 88 Date-Intl
# value 3.
DATE_FORM_UNSET: Final[int] = 0
DATE_FORM_UK: Final[int] = 1
DATE_FORM_USA: Final[int] = 2
DATE_FORM_INTL: Final[int] = 3

# The characters a PIC 9 DISPLAY field accepts as numeric.
_ASCII_DIGITS: Final[str] = "0123456789"


# A COBOL PIC X(n) field is n bytes wide at all times.


def _alphanumeric_move(source: str, width: int) -> str:
    """Reproduce a COBOL `MOVE` into an alphanumeric `PIC X(width)` field."""
    if len(source) >= width:
        return source[:width]
    return source + " " * (width - len(source))


def _ref_mod(field_text: str, offset: int, length: int) -> str:
    """Reproduce COBOL reference modification `field (offset:length)`.

    `offset` is 1-based, as COBOL writes it.
    """
    required_width = max(len(field_text), offset - 1 + length)
    materialised = _alphanumeric_move(field_text, required_width)
    return materialised[offset - 1 : offset - 1 + length]


def _poke(base_text: str, offset: int, length: int, value: str, width: int) -> str:
    """Reproduce a COBOL `MOVE` into a `REDEFINES` sub-field of a group.

    Writes `value` into the `length` characters at 1-based `offset` of a
    `width`-character group, leaving every other character of the group exactly as it
    was. That is precisely how the seed literals keep their separators.
    """
    materialised = _alphanumeric_move(base_text, width)
    stored = _alphanumeric_move(value, length)
    return materialised[: offset - 1] + stored + materialised[offset - 1 + length :]


def _is_numeric(field_text: str) -> bool:
    """Reproduce the COBOL `NUMERIC` class condition for a `PIC 9(n)` DISPLAY field.

    A zoned-decimal DISPLAY field is numeric only when every character is an ASCII
    decimal digit.
    """
    return len(field_text) > 0 and all(
        character in _ASCII_DIGITS for character in field_text
    )


def _zoned_decimal_value(digits_text: str) -> int:
    """Read a `PIC 9(n)` DISPLAY field as a number, zoned-decimal fashion.

    ANOMALY, reproduced. `Test-Date9` is `PIC 9(8)` DISPLAY, and the six-part test
    [common/maps04.cbl:L140-L145] never checks `A-Year` for NUMERIC, so non-digit
    characters can reach it. A zoned-decimal read is what the storage class means.
    """
    value = 0
    for character in digits_text:
        value = value * 10 + (ord(character) & 0x0F)
    return value


#: The `01` record name, verbatim from [copybooks/wsmaps03.cob:L6], LOWER case because
#: that is how the copybook writes it and dictionary keys carry names exactly as the
#: frozen source spells them.
_COPYBOOK_RECORD: Final[str] = "maps03-ws"


@dataclass(slots=True)
class _OpenGroup:
    """One group of `maps03-ws` whose subordinates are still being laid out.

    Attributes:
        key: The group's qualified dictionary key.
        level: Its COBOL level number, which is what closes it - the next item at the
            same or a lower level ends this group.
        offset: The 1-based character position its first subordinate occupies.
        cursor: The next free character position within it, advanced by each subordinate
            laid out so far.
        redefining: Whether the group itself `REDEFINES` an earlier item, in which case
            it re-reads characters the enclosing group has already counted and must not
            advance the enclosing group's cursor.
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

    Walks the dictionary's entries for `maps03-ws` in DECLARATION ORDER and lays them
    out the way a COBOL compiler does, so that not one offset in this module is
    transcribed by hand (rule R-5). The rules applied are the language's.

    Returns:
        Every item of the record - the groups and the seven fillers as well as the
            leaves - keyed by the COBOL name the copybook spells, mapped to `(offset,
            width)` with `offset` 1-based as COBOL writes it.

    Raises:
        acas_posting.dictionary.loader.DictionaryError: The dictionary is absent or does
            not carry this record. Nothing here falls back to a transcribed layout.
    """
    layout: dict[str, tuple[int, int]] = {}
    open_groups: list[_OpenGroup] = []

    def close_innermost() -> None:
        """Finish the innermost open group, sizing it by what it covered."""
        group = open_groups.pop()
        layout[group.key] = (group.offset, group.cursor - group.offset)
        # A REDEFINES group re-reads characters the enclosing group has already counted,
        # so it must not advance that group's cursor.
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


#: Every item's `(offset, width)`, derived once.
_LAYOUT: Final[dict[str, tuple[int, int]]] = _reading_layout()


def _items_within_date_text() -> dict[str, tuple[int, int]]:
    """The items of `maps03-ws` that lie inside `u-date`'s own characters.

    Two of the record's items do not: the `01` group, which spans the text AND the
    binary day number, and `u-bin` itself, which is the four characters after the text
    [copybooks/wsmaps03.cob:L30].

    Returns:
        The subset of `_LAYOUT` whose extent falls entirely within `u-date`: `u-date`,
            the three `REDEFINES` groups, `u-year` and `u-intl-year`, the twelve leaves
            and the seven fillers.
    """
    date_offset, date_width = _LAYOUT[_qualify("u-date")]
    limit = date_offset + date_width
    return {
        key: (offset, width)
        for key, (offset, width) in _LAYOUT.items()
        if offset >= date_offset and offset + width <= limit
    }


_TEXT_ITEMS: Final[dict[str, tuple[int, int]]] = _items_within_date_text()


def reading_field(ws: Maps03Ws, item: str) -> str:
    """Read one item of a `REDEFINES` reading of `u-date`, as TEXT.

    The Python spelling of a reference-modified read of a `REDEFINES` sub-field: `u-days
    OF u-UK` is `reading_field(ws, "u-days")`.

    Args:
        ws: The linkage record, whose `u_date` holds the ten characters.
        item: The COBOL item name - `"u-days"`, `"u-month"`, `"u-year"`, `"u-cc"`,
            `"u-yy"`, `"u-usa-month"`, `"u-usa-days"`, `"u-intl-year"`, `"u-intl-cc"`,
            `"u-intl-yy"`, `"u-intl-month"` or `"u-intl-days"`.

    Returns:
        Exactly that item's declared width in characters.

    Raises:
        KeyError: `item` is not an item of `maps03-ws` that lies inside `u-date`.
    """
    offset, width = _TEXT_ITEMS[_qualify(item)]
    return _ref_mod(ws.u_date, offset, width)


def set_reading_field(ws: Maps03Ws, item: str, value: str) -> None:
    """Write one item of a `REDEFINES` reading of `u-date`, leaving the rest.

    The Python spelling of `move ... to u-year OF u-UK`. It overwrites only that item's
    own characters and leaves every other position of the ten exactly as it was, which
    is how the seed literals keep their separators.

    Args:
        ws: The linkage record. Mutated in place, as a COBOL `MOVE` into a linkage item
            is.
        item: The COBOL item name, as `reading_field` documents.
        value: The sending text.

    Raises:
        KeyError: `item` is not an item of `maps03-ws` that lies inside `u-date`, as
            `reading_field` records.
    """
    offset, width = _TEXT_ITEMS[_qualify(item)]
    ws.u_date = _poke(ws.u_date, offset, width, value, DATE_TEXT_LENGTH)


# `common/maps04.cbl` delegates the real work to three intrinsics, a choice its own
# change log dates to 2009 and explains.


def _is_leap_year(year: int) -> bool:
    """Apply the Gregorian leap rule, spelled out rather than delegated.

    Divisible by 4, except centuries, except every fourth century.
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

    Returns ZERO for a valid date and non-zero for an invalid one.
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

    Returns the binary day number counted from `COBOL_DATE_EPOCH_ORDINAL`, 1600-12-31,
    so that 1601-01-01 is day 1, 2025-09-21 is 155127 and 9999-12-31 is 3067671, the
    maximum.
    """
    return date(year, month, day).toordinal() - COBOL_DATE_EPOCH_ORDINAL


def date_of_integer(day_number: int) -> date:
    """Reimplement `FUNCTION Date-of-integer` [common/maps04.cbl:L183].

    The COBOL intrinsic returns zero rather than failing for a day number outside 1
    through 3067671; `ws_unpack` reproduces that at the one place it reaches the output.
    """
    return date.fromordinal(day_number + COBOL_DATE_EPOCH_ORDINAL)


# maps04 - THE PROGRAM [common/maps04.cbl:L122-L189] `procedure division using
# Mapa03-WS.` - one parameter, passed by reference, and no return value.


def maps04(ws: Maps03Ws) -> None:
    """Validate and convert a date, in place, exactly as `common/maps04.cbl` does.

    * `u_bin > 0` - UNPACK. The binary day number is converted to DD/MM/CCYY text in
    `u_date`. * otherwise - VALIDATE AND PACK.
    """
    # [common/maps04.cbl:L128-L129] if A-Bin > zero go to WS-Unpack. Class 4 sibling re-
    # dispatch.
    if ws.u_bin > 0:
        ws_unpack(ws)
        return

    separator_tally = 0

    # [common/maps04.cbl:L132-L134] inspect A-Date replacing all "." by "/". inspect
    # A-Date replacing all "," by "/". inspect A-Date replacing all "-" by "/". ANOMALY,
    # reproduced.
    ws.u_date = _alphanumeric_move(ws.u_date, DATE_TEXT_LENGTH).replace(".", "/")
    ws.u_date = ws.u_date.replace(",", "/")
    ws.u_date = ws.u_date.replace("-", "/")

    # [common/maps04.cbl:L135] inspect A-Date tallying Z for all "/". The tally counts
    # "/" across the WHOLE ten characters, not just positions 3 and 6.
    separator_tally = ws.u_date.count("/")

    # [common/maps04.cbl:L140-L146] THE SIX-PART REJECT TEST if Z not = 2 or A-Days not
    # numeric or A-Month not numeric or A-CC not numeric or A-Days < 01 or > 31 or
    # A-Month < 01 or > 12 go to Main-Exit.
    days_text = reading_field(ws, "u-days")
    month_text = reading_field(ws, "u-month")
    if (
        separator_tally != 2
        or not _is_numeric(days_text)
        or not _is_numeric(month_text)
        or not _is_numeric(reading_field(ws, "u-cc"))
        or (int(days_text) < 1 or int(days_text) > 31)
        or (int(month_text) < 1 or int(month_text) > 12)
    ):
        # Class 3 -> Main-Exit [common/maps04.cbl:L146]. ANOMALY A-16: u_bin is NOT
        # written. Returning here leaves whatever the caller put there, and that is the
        # entire rejection signal.
        return

    # [common/maps04.cbl:L148-L151] assemble Test-Date as CCYYMMDD move A-CC to TD-CC.
    # move A-Year to TD-YY. move A-Month to TD-MM. move A-Days to TD-DD.
    test_date = " " * TEST_DATE_LENGTH
    cc_text = reading_field(ws, "u-cc")
    yy_text = reading_field(ws, "u-yy")
    test_date = _poke(test_date, 1, 2, cc_text, TEST_DATE_LENGTH)
    test_date = _poke(test_date, 3, 2, yy_text, TEST_DATE_LENGTH)
    test_date = _poke(test_date, 5, 2, month_text, TEST_DATE_LENGTH)
    test_date = _poke(test_date, 7, 2, days_text, TEST_DATE_LENGTH)

    test_date9 = _zoned_decimal_value(test_date)

    if test_date_yyyymmdd(test_date9) != 0:
        # Class 3 -> Main-Exit [common/maps04.cbl:L154]. ANOMALY A-16 again, on the
        # second and independent reject path: u_bin is NOT written here either.
        # "31/02/2025" reaches exactly this point.
        return

    # [common/maps04.cbl:L167] move FUNCTION integer-of-Date (Test-Date9) to A-Bin. The
    # single successful write to the binary field in the whole forward path.
    year, remainder = divmod(test_date9, 10_000)
    month, day = divmod(remainder, 100)
    ws.u_bin = integer_of_date(year, month, day)

    # [common/maps04.cbl:L168] go to Main-Exit. Class 3 -> Main-Exit.
    return


def ws_unpack(ws: Maps03Ws) -> None:
    """Reproduce the `WS-Unpack` paragraph [common/maps04.cbl:L181-L186].

    That raises a question `datetime` cannot answer: `date.fromordinal` raises for an
    out-of-range ordinal while `FUNCTION Date-of-integer` returns zero for one, its ISO
    domain running 1 (1601-01-01) to 3067671 (9999-12-31).
    """
    # [common/maps04.cbl:L182] move "00/00/0000" to A-Date. THE SEED. This literal is
    # the sole source of the separators in the unpacked date.
    ws.u_date = UNPACK_SEED

    if COBOL_MIN_DATE_INTEGER <= ws.u_bin <= COBOL_MAX_DATE_INTEGER:
        converted = date_of_integer(ws.u_bin)
        test_date = f"{converted.year:04d}{converted.month:02d}{converted.day:02d}"
    else:
        # Out of domain the intrinsic yields zero, so the 8-byte group reads "00000000".
        test_date = "0" * TEST_DATE_LENGTH

    # [common/maps04.cbl:L184-L186] move TD-CCYY to A-CCYY. *> 4 chars at offset 7 move
    # TD-MM to A-Month. *> 2 chars at offset 4 move TD-DD to A-Days.
    set_reading_field(ws, "u-year", _ref_mod(test_date, 1, 4))
    set_reading_field(ws, "u-month", _ref_mod(test_date, 5, 2))
    set_reading_field(ws, "u-days", _ref_mod(test_date, 7, 2))


# Six programs wrap the `CALL` in a section of their own, and the body is the same
# single statement in every one.


def maps03(ws: Maps03Ws) -> None:
    """Reproduce the wrapper section named `maps03`, carried by gl070 and gl051.

    ANOMALY A-22: the section is named after the interface copybook while its exit label
    is `maps04-exit`, named after the program it calls.
    """
    maps04(ws)


# [copybooks/wssystem.cob:L128-L132] Agent Action Plan section 0.1.2 rule 12 maps an
# 88-level condition name to "a predicate function over the record", so the three the
# date sections actually test become the three predicates below.


def date_form_is_uk(date_form: int) -> bool:
    """`88 Date-UK value 1` - dd/mm/yyyy [copybooks/wssystem.cob:L129]."""
    return date_form == DATE_FORM_UK


def date_form_is_usa(date_form: int) -> bool:
    """`88 Date-USA value 2` - mm/dd/yyyy [copybooks/wssystem.cob:L130]."""
    return date_form == DATE_FORM_USA


def date_form_is_intl(date_form: int) -> bool:
    """`88 Date-Intl value 3` - yyyy/mm/dd [copybooks/wssystem.cob:L131].

    Published for completeness and for callers that need the test, but note that NONE of
    the four date sections uses it: each reaches its International branch by FALLING
    THROUGH the UK and USA tests, never by testing this condition.
    """
    return date_form == DATE_FORM_INTL


# THE SECTIONS' WORKING STORAGE [general/gl070.cbl:L172-L194] 01 ws-Test-Date pic x(10).
# 01 ws-date-formats. 03 ws-swap pic xx. 03 ws-Conv-Date pic x(10). 03 ws-date pic
# x(10).


@dataclass
class WsDateFormats:
    """`ws-Test-Date` plus the `ws-date-formats` group [general/gl070.cbl:L172-L194].

    Attributes:
        ws_test_date: `ws-Test-Date pic x(10)` - the input text of `zz050`.
        ws_swap: `ws-swap pic xx` - the two-character scratch the USA branch swaps days
            and month through.
        ws_conv_date: `ws-Conv-Date pic x(10)` - declared in the group, unused by all
            four date sections.
        ws_date: `ws-date pic x(10)` - the output text of all four sections.
    """

    ws_test_date: str = field(default=" " * DATE_TEXT_LENGTH)
    ws_swap: str = field(default="  ")
    ws_conv_date: str = field(default=" " * DATE_TEXT_LENGTH)
    ws_date: str = field(default=" " * DATE_TEXT_LENGTH)


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

    Note what it does NOT touch: the separators. Only the two-character day and month
    windows are exchanged, so "21/09/2025" becomes "09/21/2025" with the "/" at
    positions 3 and 6 left where they were.
    """
    ws.ws_swap = _alphanumeric_move(ws.ws_days, 2)
    ws.ws_days = ws.ws_month
    ws.ws_month = ws.ws_swap


def zz070_convert_date(ws: WsDateFormats, to_day: str, date_form: int) -> int:
    """`zz070-Convert-Date`: reformat the run date into the configured form.

    This function does not read a clock (rule R-6): the run date arrives as an argument,
    which is exactly how every in-scope COBOL program receives it.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten.
        to_day: `to-day pic x(10)` - the run date text, DD/MM/CCYY.
        date_form: `System-Record.Date-Form` on entry.

    Returns:
        The EFFECTIVE `Date-Form`.
    """
    ws.ws_date = _alphanumeric_move(to_day, DATE_TEXT_LENGTH)

    # [general/gl070.cbl:L583-L584] if Date-Form = zero move 1 to Date-Form.
    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    if date_form_is_uk(date_form):
        return date_form

    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)
        return date_form

    # [general/gl070.cbl:L593-L598] the International branch, reached by FALL-THROUGH
    # rather than by testing `Date-Intl`. The source's own comment is "So its
    # International date format". move "ccyy/mm/dd" to ws-date.
    ws.ws_date = UK_TO_INTL_SEED
    ws.ws_intl_year = _ref_mod(to_day, 7, 4)
    ws.ws_intl_month = _ref_mod(to_day, 4, 2)
    ws.ws_intl_days = _ref_mod(to_day, 1, 2)

    return date_form


# zz060-Convert-Date - CONSOLIDATED, IDENTICAL IN 6 CARRIERS BUT FOR ONE TOKEN Reference
# body: [general/gl070.cbl:L538-L571].


def zz060_convert_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """`zz060-Convert-Date`: unpack a binary date, then reformat it for presentation.

    This is `zz070` with a conversion in front of it: input is `u-bin`, not a text date,
    so the wrapper is performed first to turn the binary day number into text and only
    then is the presentation format applied.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten.
        maps03_ws: the shared linkage record. `u_bin` is the input; the wrapper writes
            `u_date` in place.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: the wrapper section this program performs - pass `maps03` from gl051 or
            gl070, `maps04` from sl060, sl100, pl060 or pl100.

    Returns:
        The effective `Date-Form`, to be stored back into the system record as described
            in `zz070_convert_date`.
    """
    wrapper(maps03_ws)

    # [general/gl070.cbl:L548-L550] if u-date = spaces move spaces to ws-Date go to
    # zz060-Exit. Class 3 section exit.
    if _alphanumeric_move(maps03_ws.u_date, DATE_TEXT_LENGTH) == " " * DATE_TEXT_LENGTH:
        ws.ws_date = " " * DATE_TEXT_LENGTH
        return date_form

    ws.ws_date = _alphanumeric_move(maps03_ws.u_date, DATE_TEXT_LENGTH)

    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    if date_form_is_uk(date_form):
        return date_form

    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)
        return date_form

    # [general/gl070.cbl:L563-L568] the International branch, again by fall-through.
    ws.ws_date = UK_TO_INTL_SEED
    ws.ws_intl_year = _ref_mod(maps03_ws.u_date, 7, 4)
    ws.ws_intl_month = _ref_mod(maps03_ws.u_date, 4, 2)
    ws.ws_intl_days = _ref_mod(maps03_ws.u_date, 1, 2)

    return date_form


# zz050-Validate-Date - NOT EQUIVALENT ACROSS CARRIERS. PUBLISHED AS TWO SEPARATE
# FUNCTIONS.


def zz050_test_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> None:
    """Reproduce the `zz050-test-date` paragraph [general/gl051.cbl:L1200-L1203].

    THE CALLER PRE-ZERO.
    """
    maps03_ws.u_date = _alphanumeric_move(ws.ws_date, DATE_TEXT_LENGTH)

    maps03_ws.u_bin = 0

    wrapper(maps03_ws)


def _zz050_validate_date_body(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """Run the part of `zz050-Validate-Date` that all five carriers share."""
    ws.ws_date = _alphanumeric_move(ws.ws_test_date, DATE_TEXT_LENGTH)

    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    if date_form_is_uk(date_form):
        zz050_test_date(ws, maps03_ws, wrapper=wrapper)
        return date_form

    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)
        zz050_test_date(ws, maps03_ws, wrapper=wrapper)
        return date_form

    # [general/gl051.cbl:L1193-L1198] the International branch, by fall-through. move
    # "dd/mm/ccyy" to ws-date. *> swap Intl to UK form move ws-test-date (1:4) to ws-
    # Year. move ws-test-date (6:2) to ws-Month.
    ws.ws_date = INTL_TO_UK_SEED
    ws.ws_year = _ref_mod(ws.ws_test_date, 1, 4)
    ws.ws_month = _ref_mod(ws.ws_test_date, 6, 2)
    ws.ws_days = _ref_mod(ws.ws_test_date, 9, 2)

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

    THIS VARIANT DOES NOT MUTATE `ws.ws_test_date`.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten;
            `ws.ws_test_date` is READ ONLY here.
        maps03_ws: the shared linkage record, written by `zz050_test_date`. On return
            `u_bin` is non-zero if and only if the date was valid.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: `maps04` for all four of this variant's carriers. Required and never
            defaulted.

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

    These rewrite the CALLER'S OWN `ws-test-date` field in place, so gl051's working
    storage differs after the call from what the other four programs' would hold for the
    same input. That divergence is deliberate here, not tidied away.

    Args:
        ws: the section's working storage. BOTH `ws.ws_test_date` AND `ws.ws_date` are
            overwritten.
        maps03_ws: the shared linkage record, written by `zz050_test_date`.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: `maps03` for gl051 - the anomaly A-22 spelling. Required and never
            defaulted.

    Returns:
        The effective `Date-Form`, to be stored back into the system record.
    """
    ws.ws_test_date = _alphanumeric_move(ws.ws_test_date, DATE_TEXT_LENGTH)
    ws.ws_test_date = ws.ws_test_date.replace(".", "/")
    ws.ws_test_date = ws.ws_test_date.replace(",", "/")
    ws.ws_test_date = ws.ws_test_date.replace("-", "/")

    return _zz050_validate_date_body(ws, maps03_ws, date_form, wrapper)


# Both `zz050` variants are exported and neither is the default; the storage helpers and
# `_zz050_validate_date_body` stay private because they are mechanics rather than
# migrated paragraphs.
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
    # RE-EXPORT, not a definition. This name is the SAME class object as
    # `acas_posting.records.maps03.Maps03Ws`.
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
