"""The COBOL `MOVE` verb: receiving-field data-movement semantics.

A `MOVE` is not an assignment. The receiving field's picture decides everything:
an alphanumeric field truncates on the right and space-pads, a numeric field
aligns on the decimal point and truncates both ends, a group move is a byte copy,
and a figurative constant fills. Those rules live here so that no program module
implements one.

No validation is added on the way through (R-3), and one anomaly depends on that
absence: `gl072` skips a posting whose batch number is not numeric
[general/gl072.cbl:L291-L292], and its sibling skip on a handler error of 999
[general/gl072.cbl:L306-L307], both entirely silently. If a movement raised on
non-numeric text those silent skips could not be reproduced, so the numeric-class
test here is a plain predicate that never raises on content, and the skip itself
stays in the program module where the COBOL puts it.
"""

from __future__ import annotations

import dataclasses
import decimal
import enum
import logging
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Final

from acas_posting.cobol import arithmetic as cobol_arithmetic
from acas_posting.cobol import usage as cobol_usage
from acas_posting.cobol.field import FieldDescriptor
# Agent Action Plan section 0.4.3 lets `cobol/*.py` import `dictionary.loader` and
# nothing else from the dictionary package.
from acas_posting.dictionary.loader import SignPosition, Usage

#: Diagnostics only. The one thing this module logs is the reading or writing of
#: bytes OUTSIDE an enclosing group by an unchecked subscript - a condition whose
#: outcome is a property of the compiled binary rather than of the frozen source,
#: and therefore the one thing a maintainer must be able to see happening. No
#: control flow depends on a log record and none appears in a table dump.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

# The export surface, sorted so that it is stable and reviewable. It is the whole
# contract the record layer, the program layer and the arithmetic parity suite are
# written against, so it is stated exhaustively rather than left to be discovered:
# twelve verbs, two vocabularies, seven sentinels and seven published tables.
# There is deliberately NO calendar helper, NO print-line builder, NO
# `MOVE CORRESPONDING`, NO `JUSTIFIED` support, NO `UNSTRING`, and no business
# constant of any kind - the module docstring gives the frozen-source count behind
# each of those absences.
__all__: Final[tuple[str, ...]] = (
    "DELIMITED_BY_SIZE",
    "DELIMITED_BY_SPACE",
    "EDIT_SYMBOLS_IMPLEMENTED",
    "FIGURATIVE_FILL_CHARACTER",
    "FIGURATIVE_SPELLINGS",
    "MOVE_CENSUS",
    "MOVE_STATEMENT_CENSUS",
    "REFERENCE_MODIFICATION_CENSUS",
    "REFERENCE_MODIFICATION_OVERRUN_ORACLE_EVIDENCE",
    "SPACE",
    "SPACES",
    "PACKED_RECEIVER_READ_ORACLE_EVIDENCE",
    "UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE",
    "ZERO",
    "ZEROES",
    "ZEROS",
    "ZERO_OCCURRENCE_FORMS",
    "Delimiter",
    "Figurative",
    "FigurativeSpaceIntoNumeric",
    "GroupItem",
    "MovementWithNoCompiledAnswer",
    "ReferenceModificationOutOfRange",
    "StorageGroup",
    "UnobservableEditedPicture",
    "inspect_tallying_leading",
    "is_numeric_class",
    "move",
    "move_alphanumeric",
    "move_figurative",
    "move_group",
    "move_numeric",
    "move_to_all",
    "move_to_edited",
    "ref_mod",
    "ref_mod_into",
    "string_into",
    "subscripted_store",
    "subscripted_value",
)

# A figurative constant and a `DELIMITED BY` phrase are both closed sets in the frozen
# sources, and both are published as enums so that a program module transcribes the
# COBOL word rather than a bare Python literal, and so that an unrecognised word is
# reported by the enum constructor rather than by a validation branch added here (rule
# R-3).


class Figurative(enum.Enum):
    """The figurative constants the frozen sources actually move.

    Two members, because a census of the twelve in-scope program files finds exactly two
    figurative constants used as a `MOVE` sending operand.
    """

    ZERO = "zero"
    SPACE = "space"

    @classmethod
    def _missing_(cls, value: object) -> Figurative | None:
        """Accept every spelling the frozen sources and COBOL admit."""
        if not isinstance(value, str):
            return None
        return _FIGURATIVE_BY_SPELLING.get(value.strip().casefold())


class Delimiter(enum.Enum):
    """The `DELIMITED BY` phrases the frozen sources actually use.

    Across the twelve in-scope program files `DELIMITED BY SIZE` appears 22 times,
    `DELIMITED BY SPACE` 3 times, and a literal delimiter not at all.
    """

    SIZE = "size"
    SPACE = "space"

    @classmethod
    def _missing_(cls, value: object) -> Delimiter | None:
        """Accept the COBOL word in any case, so transcription stays literal."""
        if not isinstance(value, str):
            return None
        return _DELIMITER_BY_SPELLING.get(value.strip().casefold())


# Spelling to member, consulted by both `_missing_` hooks above.
_FIGURATIVE_BY_SPELLING: Final[Mapping[str, Figurative]] = MappingProxyType({
    "zero": Figurative.ZERO,
    "zeros": Figurative.ZERO,
    "zeroes": Figurative.ZERO,
    "space": Figurative.SPACE,
    "spaces": Figurative.SPACE,
})

_DELIMITER_BY_SPELLING: Final[Mapping[str, Delimiter]] = MappingProxyType({
    "size": Delimiter.SIZE,
    "space": Delimiter.SPACE,
})


# Rule R-6 makes compiled behaviour the arbiter.


class MovementWithNoCompiledAnswer(ValueError):
    """Base for a movement whose outcome the compiled system cannot supply.

    A `ValueError` because it reports an argument combination that cannot occur, not a
    numeric condition. One base so a program module can catch the whole family, and
    three subclasses so a traceback names which question it met.
    """


class FigurativeSpaceIntoNumeric(MovementWithNoCompiledAnswer):
    """`MOVE SPACE` into a numeric receiver - question Q-9, INEXPRESSIBLE.

    THE QUESTION. What COBOL leaves in a numeric `DISPLAY` item after `MOVE SPACE`,
    since spaces in a numeric item then fail a class test and anomaly A-13's silent skip
    [general/gl072.cbl:L291-L292] turns on exactly that.
    """


class ReferenceModificationOutOfRange(MovementWithNoCompiledAnswer):
    """A reference-modification range past the item - Q-10, UNREPRODUCIBLE.

    "error: length of 'leg' out of bounds: 4" - so a literal range that runs past its
    item cannot exist in the compiled system.

    A COMPUTED one can, and it was measured: it yields the characters inside the item
    followed by the bytes of whatever storage follows - `"25##"` for `(7:4)` on an
    eight-character item with a `#`-filled neighbour. See
    :data:`REFERENCE_MODIFICATION_OVERRUN_ORACLE_EVIDENCE`. A Python `str` has no
    neighbour, so there is no value to return and refusing is the honest reproduction;
    returning the inside characters alone would invent an answer the compiled system
    never gives.
    """


class UnobservableEditedPicture(MovementWithNoCompiledAnswer):
    """An edited picture outside Z-then-9 - question Q-14, UNOBSERVABLE.

    WHY NO EXPERIMENT CAN ANSWER IT. Rule R-6 makes compiled behaviour the arbiter, and
    arbitration needs an OBSERVABLE. The only observable this migration has is table
    state.
    """


ZERO: Final[Figurative] = Figurative.ZERO

ZEROS: Final[Figurative] = Figurative.ZERO

#: `MOVE ZEROES ...` - the variant spelling, zero occurrences, accepted anyway because
#: refusing it would be a validation (rule R-3).
ZEROES: Final[Figurative] = Figurative.ZERO

SPACE: Final[Figurative] = Figurative.SPACE

SPACES: Final[Figurative] = Figurative.SPACE

DELIMITED_BY_SIZE: Final[Delimiter] = Delimiter.SIZE

DELIMITED_BY_SPACE: Final[Delimiter] = Delimiter.SPACE


# Every table is a `tuple` or a `MappingProxyType`, so nothing published here can be
# mutated by a caller and no iteration order is a caller's to observe (rule R-6).

#: `MOVE` LINE counts per in-scope program - the Agent Action Plan's own metric, section
#: 0.4.1, counting every LINE mentioning the verb, comments and continuations included.
MOVE_CENSUS: Final[tuple[tuple[str, int], ...]] = (
    ("general/gl051.cbl", 157),
    ("general/gl070.cbl", 66),
    ("general/gl071.cbl", 0),
    ("general/gl072.cbl", 59),
    ("general/gl080.cbl", 48),
    ("sales/sl055.cbl", 92),
    ("sales/sl060.cbl", 177),
    ("sales/sl100.cbl", 124),
    ("purchase/pl055.cbl", 91),
    ("purchase/pl060.cbl", 165),
    ("purchase/pl100.cbl", 122),
    ("irs/irs030.cbl", 190),
)

#: LIVE `MOVE` STATEMENT counts per in-scope program - statements that the compiler
#: executes, excluding commented-out lines and continuation lines.
MOVE_STATEMENT_CENSUS: Final[tuple[tuple[str, int], ...]] = (
    ("general/gl051.cbl", 155),
    ("general/gl070.cbl", 66),
    ("general/gl071.cbl", 0),
    ("general/gl072.cbl", 59),
    ("general/gl080.cbl", 48),
    ("sales/sl055.cbl", 90),
    ("sales/sl060.cbl", 168),
    ("sales/sl100.cbl", 117),
    ("purchase/pl055.cbl", 91),
    ("purchase/pl060.cbl", 158),
    ("purchase/pl100.cbl", 116),
    ("irs/irs030.cbl", 182),
)

#: Every literal `(offset:length)` reference-modification pair in the twelve in-scope
#: program files, with its occurrence count, most frequent first.
REFERENCE_MODIFICATION_CENSUS: Final[
    tuple[tuple[int, int, int], ...]
] = (
    (7, 4, 16),
    (4, 2, 16),
    (1, 2, 16),
    (9, 2, 9),
    (1, 6, 8),
    (6, 2, 5),
    (1, 4, 5),
    (7, 2, 4),
    (1, 1, 3),
    (1, 22, 1),
)

#: WHAT A RANGE THAT IS NOT WHOLLY INSIDE ITS ITEM ACTUALLY YIELDS - MEASURED
#: (question Q-10, rule R-6). Two readings were possible and they are not close: the
#: range might yield only the characters that ARE inside the item, or it might yield the
#: full requested length by continuing into the storage that follows. GnuCOBOL 3.2.0 was
#: driven with `post-date pic x(8)` holding `"21/09/25"` and a `pic x(10)` sentinel
#: filled with `#` declared IMMEDIATELY AFTER it in the same group - the only arrangement
#: in which the neighbouring bytes are observable at all:
#:
#:     a LITERAL `post-date (7:4)`     -> DOES NOT COMPILE. "error: length of
#:                                        'post-date' out of bounds: 4", cobc exit 1.
#:                                        So a literal overrun cannot exist in the
#:                                        compiled system at all.
#:     a COMPUTED `(off:len)`, 7 and 4 -> "25##". Four characters: the two inside the
#:                                        item followed by TWO BYTES OF THE NEIGHBOUR,
#:                                        read back individually as 0x23.
#:     a COMPUTED `(off:len)`, 9 and 2 -> "##". Wholly outside, wholly the neighbour's.
#:     a COMPUTED `(off:len)`, 7 and 2 -> "25". In range, for contrast.
#:
#: So the "characters that are inside it" reading is REFUTED, and the value the compiled
#: program produces depends on storage a Python `str` does not have. That is why
#: :class:`ReferenceModificationOutOfRange` REFUSES rather than returning a prefix:
#: returning "25" would be inventing an answer the compiled system never gives, and
#: clamping the range would be a validation (rules R-3, R-4). Each entry is
#: `(offset, length, item width, what the compiled program yielded)`.
REFERENCE_MODIFICATION_OVERRUN_ORACLE_EVIDENCE: Final[
    tuple[tuple[int, int, int, str], ...]
] = (
    (7, 4, 8, "25## - two characters of the item, then two bytes of the neighbour"),
    (9, 2, 8, "## - wholly the neighbour's bytes"),
    (7, 2, 8, "25 - in range, and the only one of the three that is reproducible"),
)

#: Accepted spelling to figurative constant, with the count of that exact spelling in
#: the twelve in-scope program files. Published so that `ZEROES`'s zero count is
#: visible.
FIGURATIVE_SPELLINGS: Final[Mapping[str, tuple[Figurative, int]]] = (
    MappingProxyType({
        "zero": (Figurative.ZERO, 532),
        "zeros": (Figurative.ZERO, 12),
        "zeroes": (Figurative.ZERO, 0),
        "space": (Figurative.SPACE, 64),
        "spaces": (Figurative.SPACE, 138),
    })
)

#: The single character each figurative constant fills a receiver with when the receiver
#: takes text.
FIGURATIVE_FILL_CHARACTER: Final[Mapping[Figurative, str]] = MappingProxyType(
    {
        Figurative.ZERO: "0",
        Figurative.SPACE: " ",
    }
)

#: COBOL data-movement forms that occur ZERO times across the twelve in-scope program
#: files and every in-scope copybook, mapped to that count.
ZERO_OCCURRENCE_FORMS: Final[Mapping[str, int]] = MappingProxyType({
    'ALL "x" as a MOVE sending operand': 0,
    "HIGH-VALUES": 0,
    "JUSTIFIED": 0,
    "LOW-VALUES": 0,
    "MOVE CORRESPONDING": 0,
    "ON OVERFLOW": 0,
    "QUOTES": 0,
    "UNSTRING": 0,
})

#: The picture edit symbols implemented by `move_to_edited`, and only those. `Z`
#: suppresses a leading zero with a space; `9` always prints its digit.
EDIT_SYMBOLS_IMPLEMENTED: Final[tuple[str, ...]] = ("Z", "9")

# The two edit symbols above, as a membership set for the picture reader.
_EDIT_SYMBOLS: Final[frozenset[str]] = frozenset(EDIT_SYMBOLS_IMPLEMENTED)

# The sign positions that place a sign INSIDE the item's digit positions rather than in
# a byte of its own. Consulted only for membership.
_SIGN_INSIDE_DIGITS: Final[frozenset[SignPosition]] = frozenset({
    SignPosition.LEADING_INCLUDED,
    SignPosition.TRAILING_INCLUDED,
})

# The sign positions that spend a byte of their own. Unexercised by this migration.
_SIGN_IN_ITS_OWN_BYTE: Final[frozenset[SignPosition]] = frozenset({
    SignPosition.LEADING_SEPARATE,
    SignPosition.TRAILING_SEPARATE,
})

# Byte-transparent for the single-byte character set the frozen sources use.
_BYTE_IMAGE_ENCODING: Final[str] = "latin-1"


# THE ONLY `raise` STATEMENT IN THIS FILE.


def _exact_carrier(value: object, *, role: str) -> None:
    """Refuse a binary floating-point carrier - the rule R-2 type gate.

    Rule R-2 forbids an accounting value passing through a binary floating-point type
    "at any point - not in computation, not in storage, not in transport".

    Args:
        value: The carrier to check. Anything exact passes untouched.
        role: What the value is, for the message - "sending value", "tally", "pointer"
            and so on.

    Raises:
        TypeError: If `value` is a `float` or a `complex`.
    """
    if isinstance(value, (float, complex)):
        raise TypeError(
            f"rule R-2 forbids a binary floating-point {role} anywhere in "
            f"this migration, and {value!r} is a "
            f"{type(value).__name__}: carry an accounting value on "
            "decimal.Decimal, and a count, a position or a binary item "
            "on int"
        )


# None of these is published.


def _receiver_width(
    receiving_field: FieldDescriptor,
    length: int | None,
) -> int | None:
    """Derive the character width a text movement fills, or None.

    The cascade, in order, and it is an ordering rather than a preference.

    Args:
        receiving_field: The receiving field.
        length: An explicit width, or None to derive one.

    Returns:
        The width in characters, or None when none can be derived.
    """
    if length is not None:
        return int(length)
    if receiving_field.character_length is not None:
        return int(receiving_field.character_length)
    try:
        return int(receiving_field.byte_length)
    except ValueError:
        return None


def _alphanumeric_to_numeric(text: str) -> decimal.Decimal:
    """Read sending characters as a value the way an elementary MOVE does.

    THE QUESTION. What an ELEMENTARY `MOVE` of an alphanumeric item into a numeric
    receiver does when the sending bytes are not a clean digit string.

    Args:
        text: The sending characters.

    Returns:
        The value the compiled program reads from them - zero for any image the
            measurement showed converting to zero.
    """
    body = text.replace(" ", "").replace(",", "")
    if body[-1:] in ("+", "-"):
        body = body[:-1]
    negative = body[:1] == "-"
    if body[:1] in ("+", "-"):
        body = body[1:]
    digits = body.replace(".", "", 1)
    if (
        not body
        or body.count(".") > 1
        or not digits
        or not digits.isascii()
        or not digits.isdigit()
    ):
        return decimal.Decimal(0)
    return decimal.Decimal(("-" if negative else "") + body)


def _sender_text(
    value: decimal.Decimal | int | str,
    sending_field: FieldDescriptor | None,
) -> str:
    """Derive the byte image a sending item presents to a text receiver.

    In COBOL a numeric `DISPLAY` item IS a character item: `Batch pic 9(5)`
    [copybooks/wspost.cob:L15] holding 42 occupies the five bytes `00042`, and that is
    what a move or a `STRING` into an alphanumeric receiver moves.

    Args:
        value: The sending value.
        sending_field: The sending item's descriptor, or None.

    Returns:
        The byte image, as characters.
    """
    if isinstance(value, str):
        return value
    if sending_field is not None and not sending_field.is_group:
        if sending_field.is_edited:
            return move_to_edited(value, sending_field)
        if sending_field.is_numeric:
            raw = cobol_usage.encode(
                value,
                usage=sending_field.usage,
                digits=sending_field.digits,
                scale=sending_field.scale,
                character_length=sending_field.character_length,
                signed=sending_field.signed,
                unsigned=sending_field.unsigned,
                sign_position=sending_field.sign_position,
            )
            return raw.decode(_BYTE_IMAGE_ENCODING)
    plain = str(value) if isinstance(value, int) else format(value, "f")
    return plain.lstrip("+-").replace(".", "")


def _edited_shape_of(clause: str | None) -> tuple[int, int] | None:
    """Read a `Z`-then-`9` edited picture, or report that it is not one.

    `acas_posting.cobol.picture` may not be imported from here - the layering table in
    the module docstring forbids it - so this is a local, deliberately minimal reader
    that recognises `Z` and `9` and nothing else.

    Args:
        clause: The receiving field's recorded picture clause, or None.

    Returns:
        The count of suppressed positions and the count of always-printing positions, or
            None when the clause is not of this shape.
    """
    if not clause:
        return None
    text = clause.strip().upper()
    symbols: list[str] = []
    index = 0
    while index < len(text):
        symbol = text[index]
        if symbol not in _EDIT_SYMBOLS:
            return None
        index += 1
        repeat = 1
        if index < len(text) and text[index] == "(":
            close = text.find(")", index)
            if close < 0:
                return None
            inner = text[index + 1:close]
            if not inner or not inner.isascii() or not inner.isdigit():
                return None
            repeat = int(inner)
            index = close + 1
        symbols.append(symbol * repeat)
    expanded = "".join(symbols)
    if not expanded:
        return None
    suppressed = len(expanded) - len(expanded.lstrip("Z"))
    remainder = expanded[suppressed:]
    if remainder.count("9") != len(remainder):
        return None
    return suppressed, len(remainder)


def _string_source(
    source: object,
    default_delimiter: Delimiter,
) -> tuple[object, Delimiter, FieldDescriptor | None]:
    """Unpack one `STRING` sending operand into its three parts.

    A `STRING` statement carries a delimiter per operand rather than one for the
    statement, and the frozen sources use that: [general/gl080.cbl:L530] through
    [general/gl080.cbl:L536] mixes `DELIMITED BY SPACE`, single statement.

    Args:
        source: The operand, as text or as a tuple.
        default_delimiter: The delimiter for an operand that names none.

    Returns:
        The value, its delimiter and its sending descriptor or None.
    """
    if not isinstance(source, tuple):
        return source, default_delimiter, None
    padded = tuple(source) + (None, None, None)
    value, delimiter, field = padded[0], padded[1], padded[2]
    member = default_delimiter if delimiter is None else Delimiter(delimiter)
    descriptor = field if isinstance(field, FieldDescriptor) else None
    return value, member, descriptor


# One primitive per category, because the truncation direction differs by category and
# both directions are silent.


def move_alphanumeric(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
    length: int | None = None,
) -> str:
    """`MOVE` into an alphanumeric receiver - category (a) and category (c).

    THE RECEIVER GOVERNS, AND IT TRUNCATES ON THE RIGHT. The sending characters are
    placed from the left of the receiver.

    Args:
        value: The sending value - text, an exact numeric carrier, or a figurative
            constant.
        receiving_field: The receiving field.
        sending_field: The sending item's descriptor. Needed only when `value` is
            numeric and its byte image must come from its picture.
        length: An explicit receiver width, overriding the cascade in `_receiver_width`.
            A group receiver needs it.

    Returns:
        What the receiver now holds, as text of the receiver's own width.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    if isinstance(value, Figurative):
        return str(move_figurative(value, receiving_field, length=length))
    text = _sender_text(value, sending_field)
    width = _receiver_width(receiving_field, length)
    if width is None:
        return text
    return str(
        cobol_usage.coerce(
            text,
            usage=Usage.ALPHANUMERIC,
            character_length=width,
        )
    )


def move_numeric(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
) -> decimal.Decimal | int | str:
    """`MOVE` into a numeric receiver - category (b) and category (d).

    THE RECEIVER GOVERNS, AND IT TRUNCATES AT BOTH ENDS. Alignment is on the implied
    decimal point, and each end is then reduced or filled independently.

    Args:
        value: The sending value - an exact numeric carrier, text, or a figurative
            constant.
        receiving_field: The receiving field.
        sending_field: Accepted for symmetry with the other categories, and unused -
            a numeric receiver reads the sending VALUE, and a sending item's own
            picture cannot change it.

    Returns:
        What the receiver now holds - `decimal.Decimal` for a scaled field, `int` for
            the binary family and a zero-scale integer.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
        FigurativeSpaceIntoNumeric: If `value` is the figurative constant SPACE, which
            GnuCOBOL 3.2 rejects at compile time for a numeric receiver (question Q-9).
    """
    _exact_carrier(value, role="sending value")
    del sending_field
    if isinstance(value, Figurative):
        return move_figurative(value, receiving_field)
    if isinstance(value, str):
        return cobol_arithmetic.store(
            _alphanumeric_to_numeric(value), receiving_field
        )
    return cobol_arithmetic.store(value, receiving_field)


def move_group(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
    length: int | None = None,
) -> str:
    """`MOVE` into a group receiver - the whole byte image, unconverted.

    A `MOVE` whose receiver is a group item is an ALPHANUMERIC move of the group's
    entire byte image.

    Args:
        value: The sending value.
        receiving_field: The receiving group.
        sending_field: The sending item's descriptor, when the sender is numeric.
        length: The group's width in characters, from the copybook.

    Returns:
        The receiving group's byte image, as characters.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    return move_alphanumeric(
        value,
        receiving_field,
        sending_field=sending_field,
        length=length,
    )


def move_figurative(
    figurative: Figurative | str,
    receiving_field: FieldDescriptor,
    *,
    length: int | None = None,
) -> decimal.Decimal | int | str:
    """`MOVE ZERO`/`MOVE SPACE` - category (e), a constant with no sender.

    A figurative constant has no sending field and no width: it fills the receiver,
    whatever the receiver's width is.

    Args:
        figurative: A `Figurative` member or any accepted spelling of one - `zero`,
            `zeros`, `zeroes`, `space` or `spaces`, in any case.
        receiving_field: The receiving field.
        length: An explicit receiver width, needed for a group receiver.

    Returns:
        What the receiver now holds: `decimal.Decimal` or `int` for a numeric receiver
            filled with `ZERO`, and text in every other case.

    Raises:
        FigurativeSpaceIntoNumeric: `MOVE SPACE` into a numeric or numeric-edited
            receiver, which GnuCOBOL 3.2 rejects at compile time (question Q-9).
    """
    member = (
        figurative if isinstance(figurative, Figurative)
        else Figurative(figurative)
    )
    if member is Figurative.SPACE:
        if receiving_field.is_numeric or receiving_field.is_edited:
            # Q-9: measured as a COMPILE ERROR, so there is no behaviour to reproduce.
            # See FigurativeSpaceIntoNumeric.
            kind = (
                "numeric-edited" if receiving_field.is_edited else "numeric"
            )
            raise FigurativeSpaceIntoNumeric(
                f"MOVE SPACE into {receiving_field.name!r}, a {kind}"
                " item, does not compile under GnuCOBOL 3.2: 'error: MOVE of "
                "figurative constant SPACE to numeric item used'. The "
                "statement cannot exist in the compiled system, so no value "
                "is reproducible (question Q-9, measured). MOVE SPACE into an "
                "alphanumeric or group receiver is supported."
            )
        width = _receiver_width(receiving_field, length)
        fill = FIGURATIVE_FILL_CHARACTER[member]
        return fill if width is None else fill * width
    if receiving_field.is_edited:
        return move_to_edited(0, receiving_field)
    if receiving_field.is_numeric:
        return cobol_arithmetic.store(0, receiving_field)
    width = _receiver_width(receiving_field, length)
    fill = FIGURATIVE_FILL_CHARACTER[member]
    return fill if width is None else fill * width


def move_to_edited(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
) -> str:
    """`MOVE` into a numeric-edited receiver - the one form that writes.

    LINE and therefore has no database effect and no oracle evidence behind it.
    `EDIT_SYMBOLS_IMPLEMENTED` lists the two symbols implemented and names the ten
    deliberately absent.

    Args:
        value: The sending value - an exact numeric carrier, a numeric byte image as
            text, or a figurative constant.
        receiving_field: The edited receiving field.

    Returns:
        The edited characters, at the picture's own width.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
        FigurativeSpaceIntoNumeric: If `value` is the figurative constant SPACE, which
            does not compile against an edited receiver either (question Q-9).
        UnobservableEditedPicture: If the receiving picture is outside the `Z`-then-`9`
            shape (question Q-14).
    """
    _exact_carrier(value, role="sending value")
    shape = _edited_shape_of(receiving_field.picture)
    if isinstance(value, Figurative):
        if value is Figurative.SPACE:
            raise FigurativeSpaceIntoNumeric(
                f"MOVE SPACE into {receiving_field.name!r}, a numeric-edited "
                "item, does not compile under GnuCOBOL 3.2: 'error: MOVE of "
                "figurative constant SPACE to numeric item used'. The "
                "statement cannot exist in the compiled system, so no value "
                "is reproducible (question Q-9, measured)."
            )
        exact: decimal.Decimal | int = 0
    elif isinstance(value, str):
        exact = _alphanumeric_to_numeric(value)
    else:
        exact = value
    if shape is None:
        raise UnobservableEditedPicture(
            f"{receiving_field.name!r} declares the edited picture "
            f"{receiving_field.picture!r}, which is outside the Z-then-9 "
            f"shape {EDIT_SYMBOLS_IMPLEMENTED} implements. No in-scope "
            "database "
            "write reaches such a picture - every other edited picture in the "
            "frozen sources receives into a print line - so no experiment "
            "against the compiled cycle can observe its rendering and none is "
            "reproduced here (question Q-14). Report formatting beyond "
            "database effects is out of scope by Agent Action Plan section "
            "0.2.2."
        )
    stored = cobol_arithmetic.store(exact, receiving_field)
    plain = str(stored) if isinstance(stored, int) else format(stored, "f")
    digits = plain.lstrip("+-").replace(".", "")
    suppressed, printing = shape
    span = suppressed + printing
    digits = digits.zfill(span)[-span:]
    rendered: list[str] = []
    significant = False
    for position, digit in enumerate(digits):
        if position < suppressed and not significant and digit == "0":
            rendered.append(" ")
            continue
        significant = True
        rendered.append(digit)
    return "".join(rendered)


# One entry point a program module normally calls, and one for the multiple-receiver
# form.


def move(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
    length: int | None = None,
) -> decimal.Decimal | int | str:
    """`MOVE <sender> TO <one receiver>` - the single audited dispatch.

    THE RECEIVING FIELD DECIDES EVERYTHING. A `MOVE` is not an assignment: Agent Action
    Plan section 0.1.2, transformation rule 11, requires "Sending-field-to-receiving-
    field rules, not assignment", and the rules differ by the receiver's category, not
    by the sender's type.

    Args:
        value: The sending value - text, an exact numeric carrier, or a figurative
            constant.
        receiving_field: The receiving field, which governs the movement.
        sending_field: The sending item's descriptor, needed only when a numeric value
            crosses into a text receiver and its byte image must come from its own
            picture [sales/sl100.cbl:L622].
        length: An explicit receiver width. A group receiver needs it, every group view
            in the generated dictionary leaving `character_length` unset.

    Returns:
        What the receiver now holds, in the carrier its storage class calls for.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    if isinstance(value, Figurative):
        return move_figurative(value, receiving_field, length=length)
    if receiving_field.is_group:
        return move_group(
            value,
            receiving_field,
            sending_field=sending_field,
            length=length,
        )
    if receiving_field.is_edited:
        return move_to_edited(value, receiving_field)
    if receiving_field.is_numeric:
        return move_numeric(
            value,
            receiving_field,
            sending_field=sending_field,
        )
    return move_alphanumeric(
        value,
        receiving_field,
        sending_field=sending_field,
        length=length,
    )


def move_to_all(
    value: decimal.Decimal | int | str | Figurative,
    receiving_fields: Sequence[FieldDescriptor],
    *,
    sending_field: FieldDescriptor | None = None,
) -> tuple[decimal.Decimal | int | str, ...]:
    """`MOVE <sender> TO <several receivers>` - each applying its own rules.

    The results come back in RECEIVER ORDER, in a `tuple`, so a program module unpacks
    them in the order the COBOL statement names them and a reader can diff the two
    lists position by position.

    Args:
        value: The sending value, converted once per receiver.
        receiving_fields: The receivers, in the order the statement names them.
        sending_field: The sending item's descriptor, when a numeric value crosses into
            a text receiver.

    Returns:
        One stored value per receiver, in receiver order.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    return tuple(
        move(value, receiver, sending_field=sending_field)
        for receiver in receiving_fields
    )


def ref_mod(text: str, offset: int, length: int) -> str:
    """`sending-item (offset:length)` - the sending-side character range.

    ONE-BASED, BECAUSE THE COBOL IS. `(1:2)` is the first two characters and `(7:4)`
    starts at the seventh.

    Args:
        text: The sending item's characters.
        offset: The 1-based first character position.
        length: The number of characters.

    Returns:
        The character range.

    Raises:
        TypeError: If `offset` or `length` is a binary floating-point carrier (rule
            R-2).
        ReferenceModificationOutOfRange: The range is not wholly inside `text` (question
            Q-10).
    """
    _exact_carrier(offset, role="reference-modification offset")
    _exact_carrier(length, role="reference-modification length")
    start = int(offset) - 1
    span = int(length)
    if start < 0 or span < 1 or start + span > len(text):
        raise ReferenceModificationOutOfRange(
            f"({offset}:{length}) is not wholly inside an item of "
            f"{len(text)} characters. A literal range like this does not "
            "compile under GnuCOBOL 3.2, and a computed one reads ADJACENT "
            "STORAGE, which a Python str does not have - so no value here is "
            "reproducible (question Q-10, measured). Every in-scope range is "
            "in bounds; see this function's reachability proof."
        )
    return text[start:start + span]


def ref_mod_into(
    receiver_text: str,
    offset: int,
    length: int,
    value: str,
) -> str:
    """`receiving-item (offset:length)` - a partial overwrite in place.

    ONE-BASED, and the positions OUTSIDE the range are left exactly as they were.

    Args:
        receiver_text: The receiver's current characters, at its declared width.
        offset: The 1-based first character position of the range.
        length: The number of characters in the range.
        value: The characters to place in the range.

    Returns:
        The receiver's characters after the overwrite.

    Raises:
        TypeError: If `offset` or `length` is a binary floating-point carrier (rule
            R-2).
        ReferenceModificationOutOfRange: The range is not wholly inside `receiver_text`
            (question Q-10).
    """
    _exact_carrier(offset, role="reference-modification offset")
    _exact_carrier(length, role="reference-modification length")
    start = int(offset) - 1
    span = int(length)
    stop = start + span
    if start < 0 or span < 1 or stop > len(receiver_text):
        raise ReferenceModificationOutOfRange(
            f"({offset}:{length}) is not wholly inside a receiver of "
            f"{len(receiver_text)} characters. The compiled program would "
            "write over ADJACENT STORAGE, which a Python str does not have, "
            "so no result here is reproducible (question Q-10, measured). "
            "Hold the receiver at its declared width - every record layout "
            "initialises it to that - and every in-scope range fits."
        )
    placed = value[:span].ljust(span)
    return receiver_text[:start] + placed + receiver_text[stop:]


# `STRING ... DELIMITED BY ... INTO ...


def inspect_tallying_leading(
    text: str,
    figurative: Figurative | str,
    tally: int,
) -> int:
    """`INSPECT <item> TALLYING <n> FOR LEADING <figurative>`.

    to the tally item rather than replacing it, which is exactly why the frozen source
    clears it first.

    Args:
        text: The item's characters.
        figurative: `SPACE` or `ZERO`, as a member or any accepted spelling.
        tally: The tally item's current value, added to.

    Returns:
        The tally item's new value.

    Raises:
        TypeError: If `tally` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(tally, role="tally")
    member = (
        figurative if isinstance(figurative, Figurative)
        else Figurative(figurative)
    )
    wanted = FIGURATIVE_FILL_CHARACTER[member]
    run = 0
    for character in text:
        if character != wanted:
            break
        run += 1
    return int(tally) + run


def string_into(
    receiver_text: str,
    sources: Sequence[object],
    *,
    pointer: int = 1,
    delimited_by: Delimiter | str = Delimiter.SIZE,
) -> tuple[str, int]:
    """Reproduce `STRING <sources> DELIMITED BY ... INTO ... POINTER <n>`.

    Writes each source's contributed characters into the receiver starting at the
    1-based pointer, advancing the pointer by what was written, and OVERWRITING rather
    than clearing.

    Args:
        receiver_text: The receiver's current characters, at its own width.
        sources: The sending operands, in statement order.
        pointer: The 1-based position to write from.
        delimited_by: The delimiter for any source that names none.

    Returns:
        The receiver's characters after the write, and the pointer's new 1-based value,
            so that the next statement can be handed both.

    Raises:
        TypeError: If `pointer` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(pointer, role="pointer")
    fallback = (
        delimited_by if isinstance(delimited_by, Delimiter)
        else Delimiter(delimited_by)
    )
    text = receiver_text
    width = len(text)
    position = int(pointer)
    for source in sources:
        value, delimiter, descriptor = _string_source(source, fallback)
        _exact_carrier(value, role="STRING sending value")
        piece = _sender_text(value, descriptor)
        if delimiter is Delimiter.SPACE:
            piece = piece.partition(" ")[0]
        if position < 1 or position > width:
            # Q-11, measured: nothing is written AND the pointer does not advance,
            # silently.
            continue
        start = position - 1
        written = piece[:width - start]
        text = text[:start] + written + text[start + len(written):]
        position += len(written)
    return text, position


# A predicate, never an exception, because anomaly A-13 depends on it.


def is_numeric_class(
    value: decimal.Decimal | int | str | Figurative,
    field: FieldDescriptor,
) -> bool:
    """`IF <item> IS NUMERIC` - the class condition, as a plain boolean.

    frozen source tests an item for numeric class and, on failure, skips the record
    entirely - with, as the anomaly register puts it, "no message, counter or trace".

    Args:
        value: What the item holds.
        field: The item's descriptor, which supplies the sign position.

    Returns:
        True when the item's contents satisfy COBOL's numeric class condition.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="tested value")
    if isinstance(value, Figurative):
        return value is Figurative.ZERO
    if not isinstance(value, str):
        return True
    if not value:
        return False
    signed_zoned = (
        field.is_numeric
        and field.signed
        and not field.is_binary_family
        and not field.is_packed
    )
    body = value
    if signed_zoned and field.sign_position in _SIGN_IN_ITS_OWN_BYTE:
        leading = field.sign_position is SignPosition.LEADING_SEPARATE
        sign_character = value[0] if leading else value[-1]
        accepted = (
            cobol_usage.SEPARATE_SIGN_BYTE_POSITIVE,
            cobol_usage.SEPARATE_SIGN_BYTE_NEGATIVE,
        )
        if ord(sign_character) not in accepted:
            return False
        body = value[1:] if leading else value[:-1]
    elif signed_zoned and field.sign_position in _SIGN_INSIDE_DIGITS:
        leading = field.sign_position is SignPosition.LEADING_INCLUDED
        overpunched = value[0] if leading else value[-1]
        code = ord(overpunched)
        if (
            code not in cobol_usage.ZONED_POSITIVE_BASE
            and code not in cobol_usage.ZONED_NEGATIVE_BASE
        ):
            return False
        body = value[1:] if leading else value[:-1]
    if not body:
        # A one-character signed item is all sign and no digit; the sign itself was
        # accepted above, so the item is numeric.
        return True
    return body.isascii() and body.isdigit()


# ---------------------------------------------------------------------------
#  UNCHECKED SUBSCRIPTED STORAGE - `table (n)` where `n` is outside `OCCURS`
# ---------------------------------------------------------------------------
#
# WHY THIS EXISTS. Four of the in-scope programs index an `OCCURS` table with
# a variable that nothing constrains to the declared range:
#
#  move     ledger-balance  to  ledger-q (a).          [general/gl080.cbl:L345]
#  add      work-vat  to  total-vat (a).               [sales/sl060.cbl:L526]
#  add      work-net  to  total-net (a).              [sales/sl060.cbl:L527]
#  add      work-goods to STurnover-Q (current-quarter)
#  [sales/sl060.cbl:L545, :L551, :L558]
#  add      work-vat  to  total-vat (a).            [purchase/pl060.cbl:L467]
#  add      work-net  to  total-net (a).            [purchase/pl060.cbl:L468]
#  add      work-goods to pturnover-q (current-quarter)
#  [purchase/pl060.cbl:L484, :L490, :L497]
#
# `a` is loaded straight from `oi-type` [sales/sl060.cbl:L509],
# [purchase/pl060.cbl:L450], whose own copybook documents type codes running to
# 9 [copybooks/plwsoi.cob:L25-L34] against a table of `occurs 3`; and
# `05 Current-Quarter pic 9` [copybooks/wssystem.cob:L110] is a single digit
# indexing a table of `occurs 4`. Nothing tests either before it is used, and the
# compile scripts pass no subscript-checking flag, so the generated code addresses
# whatever byte the arithmetic lands on. That is anomaly A-2 in the register and
# it is reproduced, never fixed (rule R-4).
#
# WHAT THE COMPILED PROGRAM ACTUALLY DOES - MEASURED, NOT INFERRED (rule R-6).
# GnuCOBOL 3.2.0 - the version the maintainer's own compile script targets
# [common/comp-common.sh:L9] - was driven with each of the four real layouts
# transcribed verbatim and a VARIABLE subscript, a literal one being refused at
# compile time (which is itself why the frozen `move oi-type to a` form is what
# makes any of this reachable). In every case the store is PLAIN LINEAR BYTE
# ADDRESSING with no bounds test, no diagnostic, no status and no abort:
# `element (n)` is written at `offset(element 1) + (n - 1) * bytes-per-occurrence`
# and whichever elementary items share those bytes are what change.
# :data:`UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE` records every reading.
#
# WHAT MUST NOT BE DONE HERE, and each of these was measured to be wrong:
#  * NO clamp, NO modulo, NO default occurrence, NO skip. The compiled program
#  does none of them.
#  * NO Python `[n - 1]`. Subscript 0 becomes index -1 and silently accumulates
#  into the LAST occurrence, which corresponds to nothing: the measured
#  answer is the field IMMEDIATELY BEFORE the table.
#  * NO exception for an in-group window. The compiled program has a definite,
#  measured answer there, so raising would replace a reproduced anomaly with
#  an invented one (rules R-3, R-4).
#
# HOW IT IS MODELLED. A :class:`StorageGroup` is the enclosing COBOL group
# expressed as what the compiled program addresses: an ordered list of elementary
# items and their pictures, hence a byte image. A store encodes the value into the
# member's own picture and pokes those bytes at the computed offset; every
# elementary item overlapping the window is then decoded back out of the image, so
# an invalid packed nibble reads exactly as the compiled program reads it -
# tolerantly, which the measurement also confirmed.
#
# THE ONE THING THAT IS NOT REPRODUCIBLE, stated rather than guessed: a window
# that extends PAST the end of the enclosing group lands on a different `01` item,
# and which item that is - and whether the generated code padded between them - is
# a property of the compiled binary and not of the frozen source. The measurement
# showed the compiled program CONTINUES in that case (it ran to completion and
# returned normally, having also changed the process's own exit status), so control
# flow is preserved: the in-group bytes are written exactly, and the overflow is
# reported as a log record with no effect on control flow. Section 0.3.4's rule
# for a diagnostic that has no database effect is what licenses the log record.
#
# HOW FAR "NOT REPRODUCIBLE" ACTUALLY EXTENDS. The boundary is a reading rather
# than a hedge: question Q-19 in `docs/migration/ambiguity-resolutions.md` records
# the byte-by-byte result for occurrence 13 of the 126-byte ledger record, and
# occurrence 14 landed six bytes further on, so the addressing stays plainly
# linear past the record's end rather than wrapping, clamping or faulting.
# TWO METHOD POINTS THAT STOP A LATER READER MEASURING THE WRONG THING: the probe
# must use a VARIABLE subscript, because cobc refuses the literal form at compile
# time ("error: subscript of 'Ledger-Q' out of bounds: 13") and a probe written
# that way measures the parser instead of the program; and the sentinel must be
# declared inside the SAME enclosing `01`, which is the only arrangement that
# makes the neighbouring bytes observable. What stays genuinely unknowable from
# the frozen source is only WHICH `01` item the overrun bytes belong to in the
# real program, because that is the compiler's allocation; the two facts this
# layer needs - that control flow continues and that NO column of `GLLEDGER-REC`
# changes - are measured, not assumed.


#: Every reading taken from the compiled oracle, kept beside the code that
#: reproduces it so that a maintainer can re-run the experiment rather than
#: trust a comment. Each entry is
#: `(statement locator, subscript, what received the value)`.
#:
#: The probes transcribed `copybooks/wsledger.cob`, the tail of
#: `sales/sl060.cbl`'s `01 ws-data` [sales/sl060.cbl:L216-L233], the tail of
#: `purchase/pl060.cbl`'s `01 ws-data` [purchase/pl060.cbl:L208-L220] and the
#: `Quarters` window of `copybooks/wssl.cob` [copybooks/wssl.cob:L54-L66], and
#: `function length` of each group was read back to pin the widths GnuCOBOL
#: chose: `pic 99 comp` is ONE byte, `pic s9(5) comp` is FOUR, and
#: `pic s9(7)v99 comp-3` is FIVE. The ledger probe also read back
#: `function length` of the record itself as 126 and of one occurrence as 6, so
#: the offsets in the two past-the-record entries below are the compiler's own
#: arithmetic rather than this file's.
UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE: Final[tuple[tuple[str, int, str], ...]] = (
    # `move ledger-balance to ledger-q (a)`; WS-Ledger-Record is 126 bytes.
    ("general/gl080.cbl:L345", 0, "Ledger-Last [copybooks/wsledger.cob:L29] - A COLUMN"),
    ("general/gl080.cbl:L345", 5, "bytes 1-6 of the trailing filler x(50) - no column"),
    ("general/gl080.cbl:L345", 6, "bytes 7-12 of the trailing filler x(50) - no column"),
    (
        "general/gl080.cbl:L345",
        13,
        "bytes 49-50 of the trailing filler x(50) and FOUR bytes past the "
        "record's 126th, in the following 01 item - no column, no diagnostic, "
        "exit 0, and Ledger-Q1..Q4 and Ledger-Last all unchanged",
    ),
    (
        "general/gl080.cbl:L345",
        14,
        "six bytes wholly past the record's 126th, six further on than "
        "subscript 13 - the addressing stays linear, it does not wrap or clamp",
    ),
    # `add work-vat to total-vat (a)` then `add work-net to total-net (a)`;
    # sl060's `01 ws-data` measures 62 bytes.
    ("sales/sl060.cbl:L526", 0, "work-goods [sales/sl060.cbl:L218]"),
    ("sales/sl060.cbl:L527", 0, "work-vat [sales/sl060.cbl:L217]"),
    ("sales/sl060.cbl:L526", 4, "ws-deduction and total-deduct, partially"),
    ("sales/sl060.cbl:L527", 4, "a, line-cnt and ws-deduction, partially"),
    # pl060's `01 ws-data` measures 50 bytes and the table is near its END.
    ("purchase/pl060.cbl:L467", 0, "work-goods [purchase/pl060.cbl:L213]"),
    ("purchase/pl060.cbl:L468", 0, "work-vat [purchase/pl060.cbl:L212]"),
    (
        "purchase/pl060.cbl:L467",
        4,
        "line-cnt and File-28-status, then 8 bytes PAST the 01 group",
    ),
    # `add work-goods to STurnover-Q (current-quarter)`; the sales-ledger window
    # measures 52 bytes. BOTH out-of-range neighbours are COLUMNS.
    ("sales/sl060.cbl:L545", 0, "Sales-Last [copybooks/wssl.cob:L55] - A COLUMN"),
    (
        "sales/sl060.cbl:L545",
        5,
        "Sales-Unapplied [copybooks/wssl.cob:L63] - A COLUMN",
    ),
    (
        "sales/sl060.cbl:L545",
        6,
        "Sales-Stats-Date and Sales-Partial-Ship-Flag - BOTH COLUMNS",
    ),
    # `add work-goods to PTurnover-q (current-quarter)`; the purchase-ledger
    # window [copybooks/wspl.cob:L43-L54] measures 58 bytes, SIX more than the
    # sales one, because the purchase record carries no partial-ship flag and its
    # trailing filler is x(12) rather than x(5). Seeded Purch-Last 200.02,
    # quarters 1.01/2.02/3.03/4.04, Purch-Unapplied 500.05, addend 77.77:
    # q=1 left Q1 78.78 and q=4 left Q4 81.81.
    ("purchase/pl060.cbl:L484", 0, "Purch-Last [copybooks/wspl.cob:L44] - A COLUMN"),
    (
        "purchase/pl060.cbl:L484",
        5,
        "Purch-Unapplied [copybooks/wspl.cob:L52] - A COLUMN",
    ),
    (
        "purchase/pl060.cbl:L484",
        6,
        "Purch-Stats-Date [copybooks/wspl.cob:L53] - A COLUMN - and the first "
        "two bytes of the trailing filler x(12)",
    ),
)


#: HOW THE COMPILED PROGRAM READS THE RECEIVER OF A SUBSCRIPTED `ADD` -
#: MEASURED, NOT INFERRED (rule R-6).
#:
#: An unchecked subscript makes the receiver's bytes an arbitrary slice of the
#: enclosing group rather than a field that was ever stored, so the receiver can
#: carry a nibble no `MOVE` would ever put there - typically the sign nibble of the
#: neighbouring packed field, landing in a DIGIT position. What the compiled
#: program then reads is NOT the digit-by-digit reading that
#: :func:`acas_posting.cobol.usage.decode` performs.
#:
#: `cobc -C` was used to confirm the code path first: `add <field> to <comp-3>`
#: compiles to `cob_add (&receiver, &addend, 0)`, the runtime's generic add. That
#: routine reads a COMP-3 receiver BYTE BY BYTE in base 100 rather than nibble by
#: nibble in base 10, and the two agree for every byte pattern a `MOVE` can
#: produce but diverge for the rest. The per-byte contribution was measured
#: directly, 26 byte values in each of three positions of a
#: `pic s9(7)v99 comp-3` field:
#:
#:     high nibble <= 9 and low nibble <= 9  ->  high * 10 + low   (ordinary BCD)
#:     high nibble <= 9 and low nibble >= 10 ->  255
#:     high nibble >= 10                     ->  0
#:
#: and the LAST byte of the field, whose low nibble is the sign, contributes its
#: high nibble as a single digit - EXCEPT when that low nibble is zero, which is
#: not a sign nibble at all, in which case the last byte contributes two digits
#: like any other. Readings that pin this: `0x4C` -> 4, `0x5C` -> 5, `0x99` -> 9,
#: `0x9A` -> 9, `0x9F` -> 9, against `0x10` -> 10, `0x20` -> 20, `0x30` -> 30.
#:
#: The reading is then truncated to the field's digit count with no diagnostic,
#: which is how a window whose bytes decode to more digits than the field holds
#: still yields a definite answer.
#:
#: SIX READINGS ARE DELIBERATELY NOT REPRODUCED, and they are named rather than
#: quietly absorbed. When the receiver's LAST byte has an invalid HIGH nibble and a
#: zero low nibble - `0xA0`, `0xC0`, `0xD0`, `0xE0`, `0xF0` - the runtime yielded
#: 2550 where every other rule it obeys predicts 0, and no consistent digit rule
#: reproduces that column alongside the `0x20` -> 20 readings. The value is a
#: sentinel from the runtime's own lookup, so encoding it would assert a property
#: of one libcob build as if it were the accounting specification. The sixth is a
#: probe artefact rather than a program state: a trailing filler seeded with `"Z"`
#: (`0x5A`) instead of the SPACES the frozen programs hold.
#:
#: NEITHER EXCLUSION IS REACHABLE AT ANY MIGRATED SITE. A receiver window's last
#: byte is always one of three things, and none can carry a high nibble above 9: a
#: byte of a stored packed value (whose high nibble is a decimal digit), a
#: character byte of a DISPLAY field or filler (`0x20`-`0x3F`), or a small binary
#: counter. Every other reading - 89 of the 95 taken - is reproduced exactly,
#: including `0x32 0x30 0x32 0x34 0x20 0x20`, the real six-byte window that
#: `PTurnover-q (6)` addresses over `Purch-Stats-Date`.
#:
#: AND IT IS RECORDED IN A DELIVERABLE, NOT ONLY HERE. Agent Action Plan section
#: 0.1.1 requires a deliberate non-reproduction be recorded "so the omission is
#: visible rather than accidental", and rule R-6 makes
#: [docs/migration/ambiguity-resolutions.md] the register of measured arbitrations.
#: This one is `Q-PACKED-RECEIVER-SENTINEL` there: the five byte patterns, the 2550
#: reading, the rule implemented instead, the case analysis above and the
#: probe-artefact sixth. For a period it appeared in no deliverable at all, which
#: made an exemplary in-code disclosure invisible to every reader who starts from
#: the documents - the failure mode that requirement exists to prevent.
PACKED_RECEIVER_READ_ORACLE_EVIDENCE: Final[tuple[tuple[str, str], ...]] = (
    ("444C000005 + 22.22", "465502222C"),
    ("444C00000C + 22.22", "465502222C"),
    ("000000000C + 22.22", "000002222C"),
    ("0A0000000C + 22.22", "550002222C"),
    ("00000000AC + 22.22", "000002222C"),
    ("0000000C0C + 22.22", "000004772C"),
    ("0000044655 + 22.22", "000006687C"),
    ("2020202020 + 22.22", "020204242C"),
    ("FFFFFFFFFC + 22.22", "000002222C"),
    ("123456789C + 22.22", "123459011C"),
    ("323032342020 + 77.77", "030323497 97C"),
)


def _packed_byte_contribution(byte_value: int) -> int:
    """One byte's contribution to a COMP-3 receiver read, as measured.

    See :data:`PACKED_RECEIVER_READ_ORACLE_EVIDENCE` for the readings. The two
    non-BCD branches return the runtime's own sentinels rather than raising,
    because the compiled program does not raise (rules R-3, R-4).
    """
    high, low = byte_value >> 4, byte_value & 0x0F
    if high > 9:
        return 0
    if low > 9:
        return 255
    return high * 10 + low


def _packed_receiver_value(
    raw: bytes, *, digits: int, scale: int
) -> decimal.Decimal:
    """Read a signed COMP-3 receiver the way `cob_add` reads it.

    Identical to :func:`acas_posting.cobol.usage.decode` for every byte pattern a
    `MOVE` can produce, and different only where an unchecked subscript has
    aliased bytes that were never a field. That equivalence is not asserted: it
    was measured on ordinary values of both widths the cycle uses,
    `pic s9(7)v99 comp-3` and `pic s9(8)v99 comp-3`, positive and negative.
    """
    accumulator = 0
    for byte_value in raw[:-1]:
        accumulator = accumulator * 100 + _packed_byte_contribution(byte_value)

    last = raw[-1]
    high, low = last >> 4, last & 0x0F
    if low == 0:
        #  A zero low nibble is not a sign nibble, so the byte carries two
        #  digits like any other. Measured: 0x10 -> 10, 0x20 -> 20, 0x30 -> 30.
        accumulator = accumulator * 100 + _packed_byte_contribution(last)
    else:
        accumulator = accumulator * 10 + (high if high <= 9 else 0)

    #  Silent high-order truncation to the field's digit count; `cob_add` was
    #  called with opt = 0, so there is no size-error path to take.
    accumulator %= 10**digits
    if low == 0x0D:
        accumulator = -accumulator
    return decimal.Decimal(accumulator).scaleb(-scale)


@dataclasses.dataclass(frozen=True)
class GroupItem:
    """One elementary item of a COBOL group, in declaration order.

    Attributes:
        name: The item's own name, exactly as the frozen source spells it. An
            occurrence of a table is named `item (n)` so that the layout reads
            like the storage the compiled program addresses.
        descriptor: Its picture, from `acas_posting.cobol.picture` or from the
            generated dictionary. `descriptor.byte_length` is the item's width,
            so no width is written here.
    """

    name: str
    descriptor: FieldDescriptor


class StorageGroup:
    """A COBOL group as the byte image the compiled program addresses.

    A group item in COBOL is not a container of independent fields; it is a run
    of bytes that its elementary items divide up, and two declarations can name
    the same bytes. That is the only reason this class exists: an unchecked
    subscript lands on bytes, so a byte model is the only thing that can say
    what it hits.

    NOT A RECORD LAYER, and not a substitute for one. It holds no values, no
    identity and no defaults; the record dataclasses in
    `acas_posting.records` remain the layouts. This is a projection of ONE group
    for ONE statement, built at module scope beside the statement that needs it.

    Args:
        items: The group's elementary items, in DECLARATION ORDER, which in
            COBOL is byte order.
        source_locator: Where the group is declared, for the message a failure
            carries (rule R-5).

    Raises:
        ValueError: Two items share a name, which would make an offset
            ambiguous. A programmer error in the layout, never a data
            condition.
    """

    __slots__ = ("_items", "_offsets", "_size", "_source_locator")

    def __init__(self, items: Sequence[GroupItem], *, source_locator: str) -> None:
        offsets: dict[str, int] = {}
        cursor = 0
        for item in items:
            if item.name in offsets:
                raise ValueError(
                    f"StorageGroup {source_locator}: two items named "
                    f"{item.name!r}; an offset would be ambiguous"
                )
            offsets[item.name] = cursor
            cursor += item.descriptor.byte_length
        self._items: Final[tuple[GroupItem, ...]] = tuple(items)
        self._offsets: Final[Mapping[str, int]] = MappingProxyType(offsets)
        self._size: Final[int] = cursor
        self._source_locator: Final[str] = source_locator

    @property
    def items(self) -> tuple[GroupItem, ...]:
        """The elementary items, in declaration order."""
        return self._items

    @property
    def size(self) -> int:
        """The group's length in bytes - what `function length` reports."""
        return self._size

    @property
    def source_locator(self) -> str:
        """Where the group is declared in the frozen source."""
        return self._source_locator

    def __repr__(self) -> str:
        return (
            f"StorageGroup({self._source_locator}, "
            f"{len(self._items)} items, {self._size} bytes)"
        )

    def offset_of(self, name: str) -> int:
        """The item's byte offset from the start of the group, zero-based.

        Raises:
            KeyError: No item of that name. A programmer error in the layout.
        """
        try:
            return self._offsets[name]
        except KeyError:
            raise KeyError(
                f"StorageGroup {self._source_locator} has no item {name!r}"
            ) from None

    def descriptor_of(self, name: str) -> FieldDescriptor:
        """The item's descriptor.

        Raises:
            KeyError: No item of that name.
        """
        for item in self._items:
            if item.name == name:
                return item.descriptor
        raise KeyError(f"StorageGroup {self._source_locator} has no item {name!r}")

    def image(self, values: Mapping[str, object]) -> bytes:
        """Lay the group out as bytes, exactly as the compiled program holds it.

        Args:
            values: The current contents, keyed by item name. An item the
                mapping omits is laid out at its category's figurative value -
                zero for a numeric item, spaces for an alphanumeric one - which
                is how COBOL `INITIALIZE` leaves it and how every bridge's own
                load paragraph leaves an unset host variable.

        Returns:
            Exactly `size` bytes.
        """
        out = bytearray()
        for item in self._items:
            descriptor = item.descriptor
            if item.name in values:
                value = values[item.name]
            elif descriptor.is_str:
                value = ""
            else:
                value = 0
            out += cobol_usage.encode(
                _exact_or_text(value),
                usage=descriptor.usage,
                digits=descriptor.digits,
                scale=descriptor.scale,
                character_length=descriptor.character_length,
                signed=descriptor.signed,
                unsigned=descriptor.unsigned,
                sign_position=descriptor.sign_position,
            )
        return bytes(out)

    def read(self, image: bytes) -> dict[str, decimal.Decimal | int | str]:
        """Decode every elementary item out of a byte image.

        Tolerant in exactly the way the compiled program is tolerant: a byte
        pattern no `MOVE` would have produced is still decoded rather than
        rejected, which is what makes an out-of-range store's aftermath
        observable instead of fatal.
        """
        out: dict[str, decimal.Decimal | int | str] = {}
        for item in self._items:
            descriptor = item.descriptor
            start = self._offsets[item.name]
            raw = image[start : start + descriptor.byte_length]
            out[item.name] = cobol_usage.decode(
                raw,
                usage=descriptor.usage,
                digits=descriptor.digits,
                scale=descriptor.scale,
                character_length=descriptor.character_length,
                signed=descriptor.signed,
                unsigned=descriptor.unsigned,
                sign_position=descriptor.sign_position,
            )
        return out


def _exact_or_text(value: object) -> decimal.Decimal | int | str:
    """Narrow a group value to a carrier `usage.encode` accepts.

    Raises:
        TypeError: The value is a binary floating-point carrier (rule R-2) or a
            type no COBOL item can hold.
    """
    if isinstance(value, bool):
        # `bool` is an `int` subclass, and a COBOL item never holds one.
        raise TypeError(f"a COBOL item cannot hold a bool: {value!r}")
    if isinstance(value, float):
        raise TypeError(
            "binary floating point cannot reach COBOL storage (rule R-2): "
            f"{value!r}"
        )
    if isinstance(value, (decimal.Decimal, int, str)):
        return value
    raise TypeError(f"unsupported carrier for COBOL storage: {value!r}")


def _subscript_window(
    group: StorageGroup,
    *,
    member: str,
    element_length: int,
    subscript: int,
) -> tuple[int, int]:
    """Where `member (subscript)` lands, as `(offset, length)`.

    The whole of the unchecked-subscript reproduction is this one expression -
    `offset(member of occurrence 1) + (subscript - 1) * element_length` - which
    is the address the generated code computes and the reason a subscript of
    zero reaches the field BEFORE the table rather than its last occurrence.

    Args:
        group: The enclosing group.
        member: The name the layout gives this member of occurrence ONE, e.g.
            `"total-vat (1)"`.
        element_length: Bytes per occurrence, i.e. the sum of one occurrence's
            members. Stated by the caller from the frozen declaration rather
            than derived, because a table's occurrence may carry members the
            statement does not name.
        subscript: The subscript as the program computed it. NOT validated.

    Returns:
        The zero-based byte offset and the member's own width. The offset may be
        negative and the window may run past the end of the group; both are
        conditions the compiled program has, so neither is refused here.
    """
    base = group.offset_of(member)
    width = group.descriptor_of(member).byte_length
    return base + (subscript - 1) * element_length, width


def _window_bytes(
    group: StorageGroup, image: bytes, offset: int, width: int, *, statement: str
) -> bytes:
    """The window's current bytes, padded where it leaves the group.

    A window that starts before the group or ends after it reaches a different
    `01` item, whose identity is a property of the compiled binary rather than
    of the frozen source. Those bytes are read as NUL, which is what an
    `INITIALIZE`d group holds, and the substitution is logged so it is never
    silent.
    """
    if offset >= 0 and offset + width <= len(image):
        return image[offset : offset + width]
    raw = bytearray(width)
    for index in range(width):
        position = offset + index
        if 0 <= position < len(image):
            raw[index] = image[position]
    _LOG.error(
        "%s: unchecked subscript reads %d byte(s) outside %s (offset %d, width "
        "%d, group %d bytes); those bytes belong to an adjacent 01 item whose "
        "identity is a property of the compiled binary and are read as zero. "
        "Anomaly A-2 reproduced; see UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE.",
        statement,
        sum(
            1
            for index in range(width)
            if not 0 <= offset + index < len(image)
        ),
        group.source_locator,
        offset,
        width,
        len(image),
    )
    return bytes(raw)


def subscripted_value(
    group: StorageGroup,
    values: Mapping[str, object],
    *,
    member: str,
    element_length: int,
    subscript: int,
    statement: str,
) -> decimal.Decimal | int | str:
    """Read `member (subscript)` through the group's storage, unchecked.

    The read half of an `ADD ... TO table (n)`: the receiver is read from
    whichever bytes the subscript addresses, exactly as the generated code reads
    them, so an out-of-range receiver contributes its ALIASED value to the sum.

    Args:
        group: The enclosing group.
        values: Its current contents, keyed by item name.
        member: The member of occurrence ONE, as the layout names it.
        element_length: Bytes per occurrence.
        subscript: As the program computed it. NOT validated (rule R-3).
        statement: The frozen statement's locator, for the log record.

    Returns:
        The value those bytes decode to under the member's own picture.
    """
    image = group.image(values)
    offset, width = _subscript_window(
        group, member=member, element_length=element_length, subscript=subscript
    )
    raw = _window_bytes(group, image, offset, width, statement=statement)
    descriptor = group.descriptor_of(member)
    if (
        descriptor.usage is cobol_usage.Usage.COMP_3
        and descriptor.signed
        and descriptor.digits is not None
    ):
        #  A signed COMP-3 receiver is read by `cob_add`, whose base-100 per-byte
        #  reading differs from a nibble-by-nibble one exactly where an unchecked
        #  subscript has aliased bytes that were never a field. Measured; see
        #  :data:`PACKED_RECEIVER_READ_ORACLE_EVIDENCE`.
        return _packed_receiver_value(
            raw, digits=descriptor.digits, scale=descriptor.scale or 0
        )
    return cobol_usage.decode(
        raw,
        usage=descriptor.usage,
        digits=descriptor.digits,
        scale=descriptor.scale,
        character_length=descriptor.character_length,
        signed=descriptor.signed,
        unsigned=descriptor.unsigned,
        sign_position=descriptor.sign_position,
    )


def subscripted_store(
    group: StorageGroup,
    values: Mapping[str, object],
    *,
    member: str,
    element_length: int,
    subscript: int,
    value: decimal.Decimal | int | str,
    statement: str,
    rounding: str | None = None,
) -> dict[str, decimal.Decimal | int | str]:
    """Store into `member (subscript)` through the group's storage, unchecked.

    The write half. The value is stored into the member's own picture first -
    truncating toward zero unless the caller names a rounding mode, which is the
    COBOL default for a store without `ROUNDED` - and the resulting bytes are
    poked at the address the subscript computes. Every elementary item of the
    group is then decoded back out, so a caller sees exactly what the compiled
    program would leave behind, including in the fields that share the window.

    NOTHING IS VALIDATED, CLAMPED OR REFUSED for an in-group window. That is
    the whole point: see this section's header for the measurements.

    Args:
        group: The enclosing group.
        values: Its current contents, keyed by item name.
        member: The member of occurrence ONE, as the layout names it.
        element_length: Bytes per occurrence.
        subscript: As the program computed it. NOT validated (rule R-3).
        value: What the statement stores.
        statement: The frozen statement's locator, for the log record.
        rounding: A `decimal` rounding mode for the store into the member's
            picture. None means the COBOL default, truncation toward zero.

    Returns:
        Every elementary item of the group, decoded after the store.

    THE ONE LIMIT OF A VALUE-CARRYING MODEL, stated rather than left to be
    discovered. The window's own bytes are reproduced exactly, and so is the
    VALUE of every neighbour the window clips - which is what reaches the
    database, because the bridge's host variables carry values and never raw
    bytes. What is NOT carried forward is a clipped neighbour's non-canonical BYTE
    IMAGE. Two measured examples of the same thing:

      * a clipped PACKED neighbour can be left holding a `0x5` where its sign
        nibble was `0xC`; decoding then re-encoding normalises the nibble and
        preserves the value;
      * a clipped DISPLAY neighbour can be left holding `03 03 23 49`, which
        `Purch-Stats-Date` reads as 3339 by the zoned low-nibble rule - the value
        the oracle's own bytes yield, verified against them - and which
        re-encodes to `33 33 33 39`.

    The consequence to be aware of is narrow: a LATER `cob_add` whose RECEIVER is
    that same clipped neighbour reads raw bytes, so it could diverge. Exactly one
    migrated site could reach that - `sl060`'s `a = 4` clips `total-deduct`, which
    [sales/sl060.cbl:L565] then accumulates into - and it needs `oi-type = 4`,
    which [copybooks/slwsoi.cob:L24] documents as `Proforma (Not used)` on the
    sales side. The purchase side DOES use type 4 [copybooks/plwsoi.cob:L28] -
    - which is why the purchase group's tail matters - but there the clipped
    neighbours are `line-cnt`
    (`binary-char`) and `File-28-status` (`pic 9` DISPLAY), neither of which any
    later statement accumulates into as a packed receiver, and the whole site was
    checked against the oracle: `line-cnt` came out at 115 in both.
    """
    descriptor = group.descriptor_of(member)
    encode_kwargs: dict[str, object] = {
        "usage": descriptor.usage,
        "digits": descriptor.digits,
        "scale": descriptor.scale,
        "character_length": descriptor.character_length,
        "signed": descriptor.signed,
        "unsigned": descriptor.unsigned,
        "sign_position": descriptor.sign_position,
    }
    if rounding is not None:
        encode_kwargs["rounding"] = rounding
    raw = cobol_usage.encode(_exact_or_text(value), **encode_kwargs)  # type: ignore[arg-type]

    image = bytearray(group.image(values))
    offset, width = _subscript_window(
        group, member=member, element_length=element_length, subscript=subscript
    )

    outside = 0
    for index in range(width):
        position = offset + index
        if 0 <= position < len(image):
            image[position] = raw[index]
        else:
            outside += 1
    if outside:
        _LOG.error(
            "%s: unchecked subscript %d writes %d byte(s) outside %s (offset "
            "%d, width %d, group %d bytes). The compiled program writes them "
            "into an adjacent 01 item and CONTINUES, so control flow is "
            "preserved and only the in-group bytes are reproduced here. "
            "Anomaly A-2; see UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE.",
            statement,
            subscript,
            outside,
            group.source_locator,
            offset,
            width,
            len(image),
        )
    return group.read(bytes(image))
