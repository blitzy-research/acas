"""The COBOL `SORT` verb: COBOL key semantics with guaranteed stability.

Sorts a sequence of records on a key tuple using COBOL comparison rules - a
numeric key compares by algebraic value including its sign, an alphanumeric key
compares by character, and the direction is per key.

STABILITY IS A CORRECTNESS REQUIREMENT, NOT A QUALITY OF IMPLEMENTATION. `gl072`
locates the nominal-ledger account for each posting with a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so it finds the right account only
because `gl071` emitted the stream in nominal-key order. An unstable sort would
reorder equal keys and the program would post to the wrong account with no error
and no diagnostic - which is why `is_sorted` is published, so the ordering can be
asserted directly rather than inferred from a state difference.

A sort is transport: nothing here rounds, truncates, reformats or otherwise
touches a value on its way through.
"""

from __future__ import annotations

import decimal
import enum
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, TypeVar

from acas_posting.cobol.field import FieldDescriptor

# Agent Action Plan section 0.4.3 lets `cobol/*.py` import `dictionary.loader` and
# nothing else from the dictionary package.
from acas_posting.dictionary.loader import CobolPythonStorage, SignPosition

# The export surface, sorted so that it is stable and reviewable. It is short by design.
__all__: Final[tuple[str, ...]] = (
    "RANK_ABSENT",
    "RANK_VALUE",
    "ComparisonValue",
    "SortDirection",
    "SortKey",
    "SortVerbError",
    "algebraic_value",
    "comparison_values",
    "is_sorted",
    "sort_records",
)

#: A record type, preserved across the sort so that a caller gets back a tuple of what
#: it passed in rather than a tuple of `object`.
RecordT = TypeVar("RecordT")

ComparisonValue = tuple[int, Any]
"""One key's value, reduced to something totally ordered."""


# THE TWO RANKS OF `ComparisonValue` Two, not three.

RANK_ABSENT: Final[int] = 0
"""Rank of a key value that is `None`.

COBOL has no null: every field in the frozen record layouts holds something, and the
bridge's load paragraphs initialise their host-variable group so an unset field becomes
zero or space rather than SQL NULL.
"""

RANK_VALUE: Final[int] = 1
"""Rank of a value that is present - every value a key can be handed.

A number, the zoned ordering value of a numeric key's byte form, or text for a character
key. There is deliberately no companion rank for a value a numeric key "cannot hold".
"""


# The two zones COBOL's own numeric class test recognises on a signed zoned item's sign-
# bearing digit, MEASURED as byte values by the sibling `acas_posting.cobol.usage` under
# its question Q-5.3 and re-measured here through a real `SORT`.
_ZONE_POSITIVE: Final[int] = 0x3
_ZONE_NEGATIVE: Final[int] = 0x7

# `byte & 0x0F` - the digit a zoned byte contributes at its own position, measured.
_LOW_NIBBLE: Final[int] = 0x0F

_ZONE_SHIFT: Final[int] = 4

# The sign positions that put the sign on the FIRST digit rather than the last. Both
# spellings the frozen layouts use are here.
_SIGN_LEADING: Final[tuple[SignPosition, ...]] = (
    SignPosition.LEADING_INCLUDED,
    SignPosition.LEADING_SEPARATE,
)

# ASCII only, and deliberately so.
_ASCII_DIGITS: Final[str] = "0123456789"
_SIGN_CHARACTERS: Final[str] = "+-"
_MINUS_SIGN: Final[str] = "-"
_DECIMAL_POINT: Final[str] = "."
_SPACE: Final[str] = " "

# `ord("0")`, so a digit character becomes its value without any lookup by character.
_ZERO_ORDINAL: Final[int] = ord(_ASCII_DIGITS[0])

# Payload carried by an absent value. A constant, so that two absent values compare
# equal and their relative order is then decided by input order alone.
_ABSENT_PAYLOAD: Final[str] = ""


class SortDirection(enum.StrEnum):
    """Which way one key orders - the `ASCENDING` / `DESCENDING` phrase.

    A `StrEnum`, matching the shape of the dictionary vocabularies the loader re-
    exports, so a direction renders as its own name in a log line or a test failure
    without a conversion step.
    """

    ASCENDING = "ASCENDING"
    """Ascending, as every key of the one in-scope `SORT` is declared.

    `on ascending key sort-batch sort-ac sort-pc sort-post`
    [general/gl071.cbl:L173-L176]. This is the default, because it is the only direction
    the migrated cycle uses.
    """

    DESCENDING = "DESCENDING"
    """Descending. UNEXERCISED by the in-scope cycle, so the oracle has confirmed nothing
    about it.
    """


class SortVerbError(ValueError):
    """A `SORT` was requested that could not order anything truthfully.

    Every use of this error reports a PROGRAMMER error: an empty key list, an attempt to
    switch stability off, or a malformed `SortKey`.
    """


@dataclass(frozen=True, slots=True, eq=True)
class SortKey:
    """One `ON ASCENDING KEY` / `ON DESCENDING KEY` item.

    Frozen, slotted and value-equal.

    Attributes:
        accessor: How to read this key's value out of a record. A CALLABLE is applied to
            the record.
        descriptor: The `FieldDescriptor` for the field this key reads.
        direction: Which way the key orders. Defaults to `SortDirection.ASCENDING`, the
            only direction the in-scope cycle uses.
    """

    accessor: str | Callable[[Any], Any]
    descriptor: FieldDescriptor
    direction: SortDirection = SortDirection.ASCENDING

    def __post_init__(self) -> None:
        """Reject a key specification that could not order anything.

        Each check fires on a PROGRAMMER error, at construction time and not part-way
        through a sort, because a malformed key produces a WRONG ORDERING rather than an
        exception - and a wrong ordering here is money posted to the wrong nominal
        account with no diagnostic at all [general/gl072.cbl:L405],
        [general/gl072.cbl:L407-L408].

        Raises:
            SortVerbError: The descriptor is not a `FieldDescriptor`, the accessor is
                neither a non-empty attribute or mapping name nor a callable, or the
                direction is not a `SortDirection` member.
        """
        if not isinstance(self.descriptor, FieldDescriptor):
            raise SortVerbError(
                "A sort key needs the FieldDescriptor of the field it reads,"
                " because that descriptor is what decides numeric versus"
                " character comparison; got "
                + type(self.descriptor).__name__
            )
        if not callable(self.accessor) and not (
            isinstance(self.accessor, str) and self.accessor
        ):
            raise SortVerbError(
                "A sort key accessor must be a callable applied to the record,"
                " or a non-empty attribute or mapping name; got "
                + repr(self.accessor)
                + " for field "
                + self.descriptor.name
            )
        if not isinstance(self.direction, SortDirection):
            raise SortVerbError(
                "A sort key direction must be a SortDirection member, not a"
                " bare string, so that an unrecognised direction cannot be"
                " read as ascending; got "
                + repr(self.direction)
                + " for field "
                + self.descriptor.name
            )


def _raw_value(record: Any, key: SortKey) -> Any:
    """Read one key's value out of one record, exactly as the key says to.

    Three accessor shapes, and no guessing between them: a callable is applied; a name
    is a mapping key when the record is a `Mapping`, and an attribute otherwise.

    Args:
        record: The record to read from.
        key: The key naming what to read.

    Returns:
        The raw value, in whatever Python type the record holds it.
    """
    accessor = key.accessor
    if callable(accessor):
        return accessor(record)
    if isinstance(record, Mapping):
        return record[accessor]
    return getattr(record, accessor)


def _zoned_ordering_value(
    text: str,
    descriptor: FieldDescriptor,
) -> tuple[int, tuple[int, ...]]:
    """Order a NUMERIC key's byte form exactly as the compiled `SORT` does.

    THE QUESTION. Where the compiled sort places a DISPLAY numeric key holding bytes the
    field cannot represent as a number.

    Args:
        text: The key's byte form, as held.
        descriptor: The field's description, giving the width and the sign position.

    Returns:
        The ordering payload: a signum and the nibble tuple.
    """
    width = descriptor.character_length or len(text)
    body = text.ljust(width, _SPACE)[:width] if width else text

    sign_index: int | None = None
    if descriptor.is_numeric and descriptor.signed:
        # Which position carries the sign is the field's own declaration, and both
        # spellings the frozen layouts use put it in a digit position.
        sign_index = 0 if descriptor.sign_position in _SIGN_LEADING else -1

    negative = False
    nibbles: list[int] = []
    for position, character in enumerate(body):
        byte = ord(character)
        digit = byte & _LOW_NIBBLE
        if sign_index is not None and position == (
            0 if sign_index == 0 else len(body) - 1
        ):
            zone = byte >> _ZONE_SHIFT
            if zone == _ZONE_NEGATIVE:
                negative = True
            elif zone != _ZONE_POSITIVE:
                digit = 0
        nibbles.append(digit)

    if negative:
        return (0, tuple(-digit for digit in nibbles))
    return (1, tuple(nibbles))


def algebraic_value(
    text: str,
    descriptor: FieldDescriptor,
) -> decimal.Decimal | int | None:
    """Read a NUMERIC key's byte form as a number, or None if it is not one.

    THIS DOES NOT DECIDE ANY ORDERING, and it is published so that a test can state what
    a key's value IS rather than only how two of them order. The ordering is
    `_zoned_ordering_value`'s, for the reason question Q-8 records.

    Args:
        text: The key's value as held.
        descriptor: The field's description, giving the scale and carrier.

    Returns:
        The algebraic value, or None when the bytes are not a number the field could
            hold. None is a report, not a refusal.
    """
    body = text
    negative = False
    if body and body[0] in _SIGN_CHARACTERS:
        negative = body[0] == _MINUS_SIGN
        body = body[1:]
    elif body and body[-1] in _SIGN_CHARACTERS:
        negative = body[-1] == _MINUS_SIGN
        body = body[:-1]

    point_count = body.count(_DECIMAL_POINT)
    if point_count > 1:
        return None
    fraction_length = 0
    if point_count == 1:
        fraction_length = len(body) - body.find(_DECIMAL_POINT) - 1
        body = body.replace(_DECIMAL_POINT, "", 1)

    # Membership against an explicit ASCII digit string rather than `str.isdigit`, which
    # is true for characters such as a superscript two that no COBOL field can hold and
    # that `int` then refuses.
    if not body:
        return None
    for character in body:
        if character not in _ASCII_DIGITS:
            return None

    if point_count == 1:
        exponent = -fraction_length
    elif descriptor.python_storage is CobolPythonStorage.DECIMAL:
        exponent = -(descriptor.scale or 0)
    else:
        exponent = 0

    # Built from the three-tuple form, which consults NO decimal context and so cannot
    # be perturbed by what a caller did before.
    digits = tuple(ord(character) - _ZERO_ORDINAL for character in body)
    value = decimal.Decimal((1 if negative else 0, digits, exponent))
    if exponent == 0:
        return int(value)
    return value


def _zoned_text_of(
    value: decimal.Decimal | int,
    descriptor: FieldDescriptor,
) -> str:
    """Lay an already-numeric key value out as the bytes its field would hold.

    A key value may reach this module as text - the field's byte form, straight off a
    record or a `READ` - or as the `int` or `decimal.Decimal` a program module computed.

    Args:
        value: The key's value.
        descriptor: The field's description, giving the width and scale.

    Returns:
        The magnitude's digit string at the field's declared width.
    """
    scale = descriptor.scale or 0
    if isinstance(value, int):
        units = abs(value) * (10 ** scale)
    else:
        # `scaleb` would consult the ambient decimal context; the three-tuple form and
        # an explicit integer power do not.
        shifted = abs(value) * (10 ** scale)
        units = int(shifted.to_integral_value(rounding=decimal.ROUND_DOWN))
    width = descriptor.character_length or descriptor.digits or len(str(units))
    return str(units).rjust(width, "0")[-width:] if width else str(units)


def _comparison_value(record: Any, key: SortKey) -> ComparisonValue:
    """Reduce one key of one record to something totally ordered.

    The single decision point for what "COBOL key semantics" means, and it is driven by
    the key's `FieldDescriptor` and not by the runtime type of the value, so that the
    answer is a property of the frozen declaration.

    Args:
        record: The record to read from.
        key: The key naming what to read and how it is declared.

    Returns:
        The comparison value for that key of that record.

    Raises:
        TypeError: The value is a `float` or a `complex`. This is rule R-2's TYPE GATE,
            not a validation of content.
    """
    raw = _raw_value(record, key)
    if isinstance(raw, (float, complex)):
        raise TypeError(
            "Rule R-2 forbids a binary floating-point value anywhere in this"
            " migration, including as a sort key, because a float comparison"
            " can reorder equal decimal values; field "
            + key.descriptor.name
            + " was handed a "
            + type(raw).__name__
            + ". Pass an int, a decimal.Decimal or the field's text form."
        )
    if raw is None:
        return (RANK_ABSENT, _ABSENT_PAYLOAD)
    if key.descriptor.is_numeric:
        if isinstance(raw, decimal.Decimal) and not raw.is_finite():
            # A non-finite Decimal has no byte form: no COBOL field can hold one, so
            # there is nothing measured to reproduce.
            return (RANK_ABSENT, str(raw))
        if isinstance(raw, (int, decimal.Decimal)):
            payload = _zoned_ordering_value(
                _zoned_text_of(raw, key.descriptor), key.descriptor
            )
            if raw < 0:
                # The magnitude was laid out without a sign, so the sign is applied
                # here, by the same element-wise negation `_zoned_ordering_value` uses
                # for a negative zone.
                return (RANK_VALUE, (0, tuple(-n for n in payload[1])))
            return (RANK_VALUE, payload)
        if isinstance(raw, str):
            return (RANK_VALUE, _zoned_ordering_value(raw, key.descriptor))
        return (RANK_VALUE, _zoned_ordering_value(str(raw), key.descriptor))
    text = raw if isinstance(raw, str) else str(raw)
    width = key.descriptor.character_length
    if width is not None and len(text) < width:
        text = text.ljust(width, _SPACE)
    return (RANK_VALUE, text)


def _require_keys(keys: Sequence[SortKey]) -> None:
    """Refuse a `SORT` with no key at all.

    A `SORT` statement with no key does not exist in COBOL, and returning the input
    order unchanged would be INDISTINGUISHABLE from a correct sort at the call site.

    Args:
        keys: The key list to check.

    Raises:
        SortVerbError: The key list is empty.
    """
    if not keys:
        raise SortVerbError(
            "A COBOL SORT names at least one key - the one in-scope statement"
            " names four, [general/gl071.cbl:L173-L176] - and a sort on no key"
            " would return the input order while looking like a sort, which is"
            " exactly the silent misposting this module exists to prevent"
        )


def comparison_values(
    record: Any, keys: Sequence[SortKey]
) -> tuple[ComparisonValue, ...]:
    """Reduce one record to the ordered tuple of its key values.

    Published so that a test - or `is_sorted` - can inspect precisely what the sort
    compares, rather than inferring it from an outcome.

    Args:
        record: The record to reduce.
        keys: The keys, most significant first.

    Returns:
        One comparison value per key, in the order the keys were given.

    Raises:
        SortVerbError: The key list is empty.
        TypeError: A key value is a `float` or a `complex` (rule R-2).
    """
    _require_keys(keys)
    return tuple(_comparison_value(record, key) for key in keys)


def _pass_selector(
    place: int,
) -> Callable[[tuple[tuple[ComparisonValue, ...], Any]], ComparisonValue]:
    """Build the key function for one pass of the sort.

    Args:
        place: Which key's comparison value the pass orders on.

    Returns:
        A function selecting that comparison value from a paired record.
    """

    def selector(
        pair: tuple[tuple[ComparisonValue, ...], Any],
    ) -> ComparisonValue:
        return pair[0][place]

    return selector


def sort_records(
    records: Sequence[RecordT],
    keys: Sequence[SortKey],
    *,
    stable: bool = True,
) -> tuple[RecordT, ...]:
    """Order records on the given keys, stably - the `SORT` verb itself.

    Reproduces the `USING` / `GIVING` form, which is the only form the in-scope cycle
    uses [general/gl071.cbl:L172-L178]: an ordered sequence in, an ordered sequence out,
    and every input record present in the output exactly once.

    Args:
        records: The records to order, in a sequence whose order is defined - that order
            is what breaks a tie on every key, so an unordered container would make the
            result vary between runs (rule R-6).
        keys: The keys, MOST SIGNIFICANT FIRST, in exactly the order the `SORT`
            statement names them. They are used exactly as given.
        stable: Accepted only as `True`. Present so that the guarantee is visible in the
            signature rather than merely documented.

    Returns:
        The same records, in key order, as a `tuple`.

    Raises:
        SortVerbError: The key list is empty, or `stable` was not `True`.
        TypeError: A key value is a `float` or a `complex` (rule R-2).
    """
    _require_keys(keys)
    if stable is not True:
        raise SortVerbError(
            "Stability cannot be switched off. The consuming program locates a"
            " nominal-ledger account with a sequential read"
            " [general/gl072.cbl:L407-L408] and is correct only because this"
            " ordering held, so an unstable sort would post to the wrong"
            " account with no error and no diagnostic; got stable="
            + repr(stable)
        )
    paired: list[tuple[tuple[ComparisonValue, ...], RecordT]] = [
        (comparison_values(record, keys), record) for record in records
    ]
    place = len(keys) - 1
    while place >= 0:
        paired.sort(
            key=_pass_selector(place),
            reverse=keys[place].direction is SortDirection.DESCENDING,
        )
        place -= 1
    return tuple(record for _, record in paired)


def is_sorted(records: Sequence[Any], keys: Sequence[SortKey]) -> bool:
    """Whether the records are already in the order these keys describe.

    The mechanism by which Agent Action Plan section 0.6.9's mitigation is realised,
    verbatim.

    Args:
        records: The records to check, in the order they are held.
        keys: The keys, most significant first.

    Returns:
        True when no adjacent pair is out of order.

    Raises:
        SortVerbError: The key list is empty.
        TypeError: A key value is a `float` or a `complex` (rule R-2).
    """
    _require_keys(keys)
    previous: tuple[ComparisonValue, ...] | None = None
    for record in records:
        current = comparison_values(record, keys)
        if previous is not None:
            for place, key in enumerate(keys):
                if previous[place] == current[place]:
                    continue
                ascending = previous[place] < current[place]
                if ascending is not (
                    key.direction is SortDirection.ASCENDING
                ):
                    return False
                break
        previous = current
    return True
