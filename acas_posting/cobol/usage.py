"""The six COBOL numeric storage classes, modelled as storage behaviour.

`DISPLAY` (zoned decimal), `COMP` (binary within a picture-declared range),
`COMP-3` (packed decimal), `DISPLAY` with `SIGN LEADING`
[copybooks/wspost-irs.cob:L21], and the `BINARY-CHAR` / `BINARY-SHORT` /
`BINARY-LONG` family. Collapsing any of them into a single numeric type would
change stored values, so each is modelled: its byte length, its value domain, its
Python carrier and its coercion.

Two behaviours are load-bearing. A field's carrier follows its declaration, so a
`binary-long` statistics field is a Python `int` and its divide truncates as
integer arithmetic does [copybooks/wssl.cob:L49] - which is what makes the
migrated moving averages match. And truncation is TOWARD ZERO, which is not
Python's floor division: the two agree on positive values and disagree on every
negative one.

No value here is ever carried in binary floating point (R-2).
"""

from __future__ import annotations

import decimal
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

# Agent Action Plan section 0.4.3 lets `cobol/*.py` import `dictionary.loader` and
# nothing else from the dictionary package.
from acas_posting.dictionary.loader import CobolPythonStorage, SignPosition, Usage

# The export surface, sorted so that it is stable and reviewable. Sorting the EXPORT
# LIST is not the same thing as sorting the DECLARATIONS.
__all__: Final[tuple[str, ...]] = (
    "ALPHANUMERIC_USAGES",
    "BINARY_FAMILY_USAGES",
    "BINARY_TRUNCATE",
    "BINARY_WIDTH_BYTES",
    "COMPUTATIONAL_BINARY_USAGES",
    "DEFAULT_BINARY_SIZE_THRESHOLDS",
    "GROUP_USAGES",
    "NUMERIC_USAGES",
    "PACKED_DECIMAL_USAGES",
    "PACKED_SIGN_NEGATIVE",
    "PACKED_SIGN_POSITIVE",
    "PACKED_SIGN_UNSIGNED",
    "SEPARATE_SIGN_BYTE_NEGATIVE",
    "SEPARATE_SIGN_BYTE_POSITIVE",
    "SIGN_LEADING_SPELLINGS",
    "ZONED_DECIMAL_USAGES",
    "ZONED_NEGATIVE_BASE",
    "ZONED_NEGATIVE_ZONE",
    "ZONED_POSITIVE_BASE",
    "ZONED_POSITIVE_ZONE",
    "ZonedDisplayInt",
    "byte_length",
    "coerce",
    "decode",
    "encode",
    "is_alphanumeric",
    "is_binary_family",
    "is_group",
    "is_numeric",
    "is_packed",
    "is_zoned_display",
    "python_storage_for",
    "truncate_toward_zero",
    "value_domain",
    "zoned_image_of",
)


#  THE BINARY FAMILY'S TRUE HARDWARE WIDTHS  (rule R-4: the declaration wins)

BINARY_WIDTH_BYTES: Final[Mapping[Usage, int]] = MappingProxyType(
    {
        Usage.BINARY_CHAR: 1,
        Usage.BINARY_SHORT: 2,
        Usage.BINARY_LONG: 4,
    }
)


# Both spellings are live in the frozen sources and neither is rewritten into the other.
SIGN_LEADING_SPELLINGS: Final[tuple[str, ...]] = ("sign leading", "sign is leading")


# A COMP-3 item stores one digit per nibble and spends its LAST nibble on the sign -
# which an unsigned item spends too, so `pic 9(9)v99` inherited from `03 Amounts
# comp-3.` [copybooks/wsbatch.cob:L40] is eleven digits in six bytes, sign nibble
# included and unsigned.
PACKED_SIGN_POSITIVE: Final[int] = 0xC
PACKED_SIGN_NEGATIVE: Final[int] = 0xD
PACKED_SIGN_UNSIGNED: Final[int] = 0xF


# Q-5.3 RESOLVED - the zoned overpunch byte values. A zoned DISPLAY digit is one byte
# whose low nibble is the digit.
ZONED_POSITIVE_ZONE: Final[int] = 0x30
ZONED_NEGATIVE_ZONE: Final[int] = 0x70

# Digit-indexed byte tables, built from the two zone nibbles in one fixed pass so that
# they cannot drift apart from them.
ZONED_POSITIVE_BASE: Final[tuple[int, ...]] = tuple(
    ZONED_POSITIVE_ZONE | digit for digit in range(10)
)
ZONED_NEGATIVE_BASE: Final[tuple[int, ...]] = tuple(
    ZONED_NEGATIVE_ZONE | digit for digit in range(10)
)

# The sign character of a SEPARATE sign, which is a byte of its own rather than an
# overpunch. Written for completeness of the vocabulary.
SEPARATE_SIGN_BYTE_POSITIVE: Final[int] = 0x2B
SEPARATE_SIGN_BYTE_NEGATIVE: Final[int] = 0x2D


# Q-5.1 RESOLVED - the default `binary-size` and `binary-truncate` policy, which set a
# COMP item's width and its behaviour on store. Agent Action Plan section 0.5.2,
# verbatim.

# (maximum declared digits, bytes allocated), ascending.
DEFAULT_BINARY_SIZE_THRESHOLDS: Final[tuple[tuple[int, int], ...]] = (
    (2, 1),
    (4, 2),
    (9, 4),
    (18, 8),
)

# True reproduces GnuCOBOL's default `binary-truncate: yes`. Set it False and a COMP
# store reduces into its byte capacity instead of its digit count.
BINARY_TRUNCATE: Final[bool] = True


# Membership sets, and membership is ALL they are used for. Never iterate one where a
# caller can observe the order.

ZONED_DECIMAL_USAGES: Final[frozenset[Usage]] = frozenset({Usage.DISPLAY})

PACKED_DECIMAL_USAGES: Final[frozenset[Usage]] = frozenset({Usage.COMP_3})

# Binary bounded by a declared digit count [copybooks/wssl.cob:L42],
# [copybooks/wsfnctn.cob:L24]. COMP-5 joins COMP here because it is binary in the same
# sense.
COMPUTATIONAL_BINARY_USAGES: Final[frozenset[Usage]] = frozenset(
    {Usage.COMP, Usage.COMP_5}
)

# The native binary family, whose range comes from its width rather than from a picture
# [copybooks/wssl.cob:L43-L53], [copybooks/wsbatch.cob:L36-L39],
# [copybooks/wssystem.cob:L62-L69].
BINARY_FAMILY_USAGES: Final[frozenset[Usage]] = frozenset(
    {Usage.BINARY_CHAR, Usage.BINARY_SHORT, Usage.BINARY_LONG}
)

ALPHANUMERIC_USAGES: Final[frozenset[Usage]] = frozenset({Usage.ALPHANUMERIC})

GROUP_USAGES: Final[frozenset[Usage]] = frozenset({Usage.GROUP})

NUMERIC_USAGES: Final[frozenset[Usage]] = (
    ZONED_DECIMAL_USAGES
    | PACKED_DECIMAL_USAGES
    | COMPUTATIONAL_BINARY_USAGES
    | BINARY_FAMILY_USAGES
)


_MAX_POLICY_DIGITS: Final[int] = DEFAULT_BINARY_SIZE_THRESHOLDS[-1][0]

# The floor on the working precision of the `decimal` contexts constructed below.
_MINIMUM_WORKING_PRECISION: Final[int] = 40

_DEFAULT_STORE_ROUNDING: Final[str] = decimal.ROUND_DOWN


# Every public entry point is keyed by the dictionary vocabularies imported above
# through `acas_posting.dictionary.loader`, and takes either the member or the string
# the artifact records for it, so that a caller reading raw dictionary JSON is not
# forced to import the enumeration at all.


def _normalise_token(text: str) -> str:
    """Fold one vocabulary token to the form the lookup tables are keyed by."""
    return "-".join(text.strip().upper().replace("_", "-").split())


_USAGE_BY_TEXT: Final[Mapping[str, Usage]] = MappingProxyType(
    {_normalise_token(member.value): member for member in Usage}
)

_SIGN_POSITION_BY_TEXT: Final[Mapping[str, SignPosition]] = MappingProxyType(
    {_normalise_token(member.value): member for member in SignPosition}
)


def _usage_of(usage: Usage | str) -> Usage:
    """Return the `Usage` member for a member or its recorded text.

    Raises:
        TypeError: if `usage` is neither a `Usage` member nor a string. A PROGRAMMER
            error: the caller has passed something that is not a storage class at all.
        ValueError: if the text names no member of the vocabulary. Also a PROGRAMMER
            error, and the reason `BINARY-DOUBLE` needs no branch of its own.
    """
    if isinstance(usage, Usage):
        return usage
    if not isinstance(usage, str):
        raise TypeError(
            "usage must be a Usage member or its recorded text, "
            f"not {type(usage).__name__}"
        )
    member = _USAGE_BY_TEXT.get(_normalise_token(usage))
    if member is None:
        raise ValueError(f"unknown COBOL usage: {usage!r}")
    return member


def _sign_position_of(sign_position: SignPosition | str) -> SignPosition:
    """Return the `SignPosition` member for a member or its recorded text.

    Raises:
        TypeError: if the argument is neither a member nor a string - a PROGRAMMER
            error, as above.
        ValueError: if the text names no member - likewise a PROGRAMMER error.
    """
    if isinstance(sign_position, SignPosition):
        return sign_position
    if not isinstance(sign_position, str):
        raise TypeError(
            "sign_position must be a SignPosition member or its recorded "
            f"text, not {type(sign_position).__name__}"
        )
    member = _SIGN_POSITION_BY_TEXT.get(_normalise_token(sign_position))
    if member is None:
        raise ValueError(f"unknown COBOL sign position: {sign_position!r}")
    return member


def _checked_count(name: str, value: int | None) -> int | None:
    """Pass a digit, scale or character count through, or report a bad one.

    Raises:
        TypeError: if the count is not an integer. A PROGRAMMER error.
        ValueError: if it is negative.
    """
    if value is None:
        return None
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an int or None, not {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} cannot be negative: {value}")
    return value


def _is_unsigned(*, signed: bool, unsigned: bool) -> bool:
    """Decide signedness from the two flags every entry point accepts.

    Two flags rather than one, because the two callers of this module hold the fact in
    the two different forms the frozen sources present it in. The generated dictionary
    records a `signed` boolean for each view.
    """
    return unsigned or not signed


# Six predicates over the vocabulary, so that a caller can branch on the family without
# importing the family sets or knowing which member sits in which.


def is_zoned_display(usage: Usage | str) -> bool:
    """Report whether this is the zoned-decimal class.

    False for `ALPHANUMERIC`, even though COBOL itself classes `PIC X(n)` as usage
    display, because the two behave differently on store: a number is truncated at its
    high-order end and text at its right-hand end.
    """
    return _usage_of(usage) in ZONED_DECIMAL_USAGES


def is_packed(usage: Usage | str) -> bool:
    """Report whether this is the packed-decimal class.

    True for `COMP-3`, whether it was declared on the item [copybooks/wsledger.cob:L28]
    or inherited from a group [copybooks/wsbatch.cob:L40], which this module cannot and
    need not tell apart: the dictionary records which at `usage_declared_at`.
    """
    return _usage_of(usage) in PACKED_DECIMAL_USAGES


def is_binary_family(usage: Usage | str) -> bool:
    """Report whether this is the native binary family.

    These are true 8-, 16- and 32-bit integers whose range comes from their width rather
    than from a picture, and which frequently carry no picture at all
    [copybooks/wsbatch.cob:L36-L39]. Their Python carrier is native `int`, which is
    load-bearing.
    """
    return _usage_of(usage) in BINARY_FAMILY_USAGES


def is_alphanumeric(usage: Usage | str) -> bool:
    """Report whether this is text rather than a number."""
    return _usage_of(usage) in ALPHANUMERIC_USAGES


def is_group(usage: Usage | str) -> bool:
    """Report whether this is a group item.

    A group's byte length is the sum of its children's, so it is not a fact this module
    can state - `byte_length` reports the request as a programmer error rather than
    inventing an answer.
    """
    return _usage_of(usage) in GROUP_USAGES


def is_numeric(usage: Usage | str) -> bool:
    """Report whether this class holds a number."""
    return _usage_of(usage) in NUMERIC_USAGES


#  THE PYTHON CARRIER  (rule R-2)


def python_storage_for(
    usage: Usage | str, scale: int | None = None
) -> CobolPythonStorage:
    """Which Python type carries a value of this class and scale.

    READ THIS BEFORE USING IT. For a RECORD FIELD, the value to use is the one the
    dictionary entry already records at `cobol_python_storage`, generated from the
    frozen sources.

    Args:
        usage: A `Usage` member or its recorded text.
        scale: Digits after the implied decimal point, or None for an item with no
            picture - a group, or a binary-family item whose range comes from its width
            [copybooks/wsbatch.cob:L36-L39]; the generated artifact records None for
            exactly those items.

    Returns:
        The `CobolPythonStorage` member naming the carrier.

    Raises:
        ValueError: for `POINTER`, which is not record storage in this migration - it
            appears only as the `TP-` item each generated bridge declares beside its
            host-variable group.
    """
    member = _usage_of(usage)
    scale_count = _checked_count("scale", scale) or 0

    if member in GROUP_USAGES:
        return CobolPythonStorage.NONE
    if member in ALPHANUMERIC_USAGES:
        return CobolPythonStorage.STR
    if member in NUMERIC_USAGES:
        # The order below is the artifact's.
        if scale_count > 0:
            return CobolPythonStorage.DECIMAL
        return CobolPythonStorage.INT
    raise ValueError(f"{member.value} is not record storage: no Python carrier")


def byte_length(
    usage: Usage | str,
    *,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    sign_position: SignPosition | str = SignPosition.NONE,
    unsigned: bool = False,
) -> int:
    """How many bytes an elementary item of this description occupies.

    ZONED DISPLAY - one byte per digit CHARACTER. The implied decimal point of a `V`
    occupies no byte, which is why `scale` does not enter the arithmetic.

    Args:
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits, integer plus fractional. Required for a zoned,
            packed, COMP or COMP-5 item; ignored for the binary family.
        scale: Accepted for a uniform signature and deliberately not consulted: an
            implied decimal point occupies no byte.
        character_length: Required for an alphanumeric item.
        sign_position: Where the sign sits. Only the SEPARATE forms change width.
        unsigned: Accepted for a uniform signature. Signedness never changes a width in
            COBOL.

    Returns:
        The byte width.

    Raises:
        ValueError: for a group or a pointer, which have no elementary width of their
            own; for a required component the caller omitted.
    """
    member = _usage_of(usage)
    position = _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    _checked_count("scale", scale)
    text_length = _checked_count("character_length", character_length)
    del unsigned  # width never depends on signedness; see the docstring

    if member in GROUP_USAGES:
        # A group's width is the sum of its children's, which this module cannot see.
        # Reporting the request beats inventing an answer.
        raise ValueError(
            "a group item has no width of its own: sum its children's widths"
        )
    if member in ALPHANUMERIC_USAGES:
        if text_length is None:
            raise ValueError("character_length is required for an alphanumeric item")
        return text_length
    if member in BINARY_FAMILY_USAGES:
        return BINARY_WIDTH_BYTES[member]
    if member not in NUMERIC_USAGES:
        raise ValueError(f"{member.value} has no byte width in a record layout")
    if digit_count is None:
        raise ValueError(f"digits is required for a {member.value} item")

    if member in ZONED_DECIMAL_USAGES:
        # Q-5.2 RESOLVED - the width of a leading-sign display item.
        if position in (
            SignPosition.LEADING_SEPARATE,
            SignPosition.TRAILING_SEPARATE,
        ):
            return digit_count + 1
        return digit_count

    if member in PACKED_DECIMAL_USAGES:
        return (digit_count + 2) // 2

    if digit_count > _MAX_POLICY_DIGITS:
        raise ValueError(
            f"digits={digit_count} exceeds the {_MAX_POLICY_DIGITS}-digit "
            "binary size policy; the widest in-scope item declares 11"
        )
    for policy_digits, policy_bytes in DEFAULT_BINARY_SIZE_THRESHOLDS:
        if digit_count <= policy_digits:
            return policy_bytes
    # Unreachable while the size policy above covers every digit count up to
    # `_MAX_POLICY_DIGITS`.
    raise ValueError(  # pragma: no cover - a policy-edit guard, not a data path
        f"no binary size covers digits={digit_count}"
    )


def value_domain(
    usage: Usage | str,
    *,
    digits: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
) -> tuple[int, int]:
    """Return the inclusive bounds an item of this description can hold.

    The bounds are on the item's DIGITS, not on its value: they count scaled units, so
    `pic s9(8)v99` returns (-9999999999, 9999999999) and a caller that wants the value
    bounds divides by ten to the power of the scale itself.

    Args:
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required for a zoned, packed, COMP or COMP-5
            item; ignored for the binary family, which has none.
        signed: The dictionary's `signed` boolean for the item.
        unsigned: The copybook's `UNSIGNED` keyword. See `_is_unsigned` for how the two
            combine.

    Returns:
        `(minimum, maximum)`, inclusive, in scaled units.

    Raises:
        ValueError: for a class that holds no number, or for a missing digit count.
    """
    member = _usage_of(usage)
    digit_count = _checked_count("digits", digits)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    if member not in NUMERIC_USAGES:
        raise ValueError(f"{member.value} holds no number: it has no value domain")

    if member in BINARY_FAMILY_USAGES:
        bits = 8 * BINARY_WIDTH_BYTES[member]
        if without_sign:
            return (0, (1 << bits) - 1)
        return (-(1 << (bits - 1)), (1 << (bits - 1)) - 1)

    if digit_count is None:
        raise ValueError(f"digits is required for a {member.value} item")
    magnitude = 10**digit_count - 1
    if without_sign:
        return (0, magnitude)
    return (-magnitude, magnitude)


def truncate_toward_zero(numerator: int, denominator: int) -> int:
    """Divide two integers the way COBOL does: truncating TOWARD ZERO.

    THIS IS NOT PYTHON'S `//`. The two operators agree on every positive dividend and
    disagree on every negative one, because `//` floors toward negative infinity while
    COBOL discards the remainder and keeps the sign.

    Args:
        numerator: The dividend, in whatever units the caller is working in.
        denominator: The divisor.

    Returns:
        The quotient, remainder discarded, sign preserved.
    """
    quotient = abs(numerator) // abs(denominator)
    if (numerator < 0) != (denominator < 0):
        return -quotient
    return quotient


# Everything below reproduces what happens to a value on its way INTO a field. Three
# commitments hold throughout, each a rule rather than a preference.


def _exact_decimal(value: decimal.Decimal | int | str) -> decimal.Decimal:
    """Bring an incoming value into exact decimal form without any loss.

    Accepts what an exact computation produces and nothing else: a `Decimal`, a Python
    `int`, or a string holding a numeric literal.

    Raises:
        TypeError: for any other type. A PROGRAMMER error.
        ValueError: for a non-finite decimal. Also a PROGRAMMER error - COBOL has no
            representation for one, so its appearance means the caller computed outside
            the exact-decimal discipline.
    """
    if isinstance(value, decimal.Decimal):
        candidate = value
    elif isinstance(value, int):
        candidate = decimal.Decimal(value)
    elif isinstance(value, str):
        # An unparseable literal raises decimal.InvalidOperation from the constructor.
        candidate = decimal.Decimal(value)
    else:
        raise TypeError(
            "an exact numeric value is required - Decimal, int or a numeric "
            f"string - not {type(value).__name__}"
        )
    if not candidate.is_finite():
        raise ValueError(f"COBOL has no representation for {candidate}")
    return candidate


def _quantum(scale: int) -> decimal.Decimal:
    """Return the unit of the last place at this scale, without a context."""
    return decimal.Decimal((0, (1,), -scale))


def _rebuild_decimal(units: int, scale: int) -> decimal.Decimal:
    """Rebuild an exact `Decimal` at `scale` from its scaled integer units.

    Constructed from the digit tuple rather than by scaling, so the result is exact,
    carries exactly `scale` decimal places, and depends on no context.
    """
    magnitude = abs(units)
    return decimal.Decimal(
        (1 if units < 0 else 0, tuple(int(digit) for digit in str(magnitude)), -scale)
    )


def _scaled_units(value: decimal.Decimal, scale: int, rounding: str) -> int:
    """Align a value to `scale` and return it as an exact integer of units.

    This is the half of a COBOL store that acts on the LOW-ORDER end: the fractional
    excess is discarded, or rounded if the statement said ROUNDED.
    """
    _, incoming_digits, exponent = value.as_tuple()
    span = len(incoming_digits) + abs(int(exponent)) + scale + 2
    precision = max(_MINIMUM_WORKING_PRECISION, span)
    exponent_limit = max(999_999, span)
    with decimal.localcontext(
        decimal.Context(
            prec=precision,
            rounding=rounding,
            Emax=exponent_limit,
            Emin=-exponent_limit,
        )
    ):
        aligned = value.quantize(_quantum(scale))
    sign, aligned_digits, _ = aligned.as_tuple()
    magnitude = 0
    for digit in aligned_digits:
        magnitude = magnitude * 10 + digit
    return -magnitude if sign else magnitude


def _wrap_into_bits(units: int, *, bits: int, without_sign: bool) -> int:
    """Reduce an integer into a binary field's own capacity.

    The half of a store that acts on the HIGH-ORDER end, for a field whose capacity is a
    number of bits rather than a number of digits.
    """
    span = 1 << bits
    if without_sign:
        return abs(units) % span
    half = span >> 1
    return ((units + half) % span) - half


def _reduce_units(
    units: int,
    member: Usage,
    digit_count: int | None,
    without_sign: bool,
) -> int:
    """Reduce aligned units into the receiving field's capacity, silently.

    A DECLARED DIGIT COUNT - zoned, packed, and COMP under `BINARY_TRUNCATE` - discards
    high-order DIGITS, so 12345.67 stored into a `pic 9(3)v99` item is 345.67. Nothing
    is raised, nothing is clamped.
    """
    if member in BINARY_FAMILY_USAGES:
        bits = 8 * BINARY_WIDTH_BYTES[member]
        return _wrap_into_bits(units, bits=bits, without_sign=without_sign)

    if digit_count is None:
        raise ValueError(f"digits is required to store into a {member.value} item")

    if member is Usage.COMP_5 or (member is Usage.COMP and not BINARY_TRUNCATE):
        bits = 8 * byte_length(member, digits=digit_count)
        return _wrap_into_bits(units, bits=bits, without_sign=without_sign)

    magnitude = abs(units) % 10**digit_count
    if without_sign or units >= 0:
        return magnitude
    return -magnitude


def _stored_units(
    value: decimal.Decimal | int | str,
    *,
    member: Usage,
    digit_count: int | None,
    scale_count: int,
    without_sign: bool,
    rounding: str,
) -> int:
    """Perform a whole numeric store and return the result as scaled units.

    Units rather than a carrier type, because both public callers need the integer:
    `coerce` wraps it into `Decimal` or `int`, and `encode` lays it out as bytes.
    """
    aligned = _scaled_units(_exact_decimal(value), scale_count, rounding)
    return _reduce_units(aligned, member, digit_count, without_sign)


def _require_text(value: decimal.Decimal | int | str) -> str:
    """Accept a string for an alphanumeric item, or report a category error.

    Raises:
        TypeError: for anything else. A PROGRAMMER error, and a deliberate.
        boundary: storing a number into a `PIC X(n)` item is a MOVE between unlike
            CATEGORIES, whose unpacking rules belong to `move.py`.
    """
    if not isinstance(value, str):
        raise TypeError(
            "an alphanumeric item stores str; a numeric-to-alphanumeric MOVE "
            f"belongs to move.py, not here (got {type(value).__name__})"
        )
    return value


def _stored_text(value: str, character_length: int) -> str:
    """Store text into a `PIC X(n)` item: right-truncated, right-padded.

    COBOL's default alphanumeric MOVE is left-justified with space fill, so a value
    shorter than the item is padded on the right and a longer one loses its right-hand
    end. Neither is an error and neither is reported.
    """
    return value[:character_length].ljust(character_length)


def coerce(
    value: decimal.Decimal | int | str,
    *,
    usage: Usage | str,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
    sign_position: SignPosition | str = SignPosition.NONE,
    rounding: str = _DEFAULT_STORE_ROUNDING,
) -> decimal.Decimal | int | str:
    """Store a value into a field of this description and return what it holds.

    TRUNCATION IS THE DEFAULT AND ROUNDING IS THE EXCEPTION. `rounding` defaults to
    `decimal.ROUND_DOWN` because COBOL truncates toward zero on store unless the
    statement is written with ROUNDED.

    Args:
        value: An exact value - `Decimal`, `int`, or a numeric string. No binary
            floating-point carrier is accepted (rule R-2).
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required except for the binary family.
        scale: Digits after the implied decimal point; None means none.
        character_length: Required for an alphanumeric item.
        signed: The dictionary's `signed` boolean for the receiving field.
        unsigned: The copybook's `UNSIGNED` keyword.
        sign_position: Where the sign sits. It does not affect the stored VALUE, only
            its byte layout, which `encode` handles.
        rounding: A `decimal` rounding mode. Truncating by default.

    Returns:
        The value the field holds after the store, in the carrier `python_storage_for`
            names for it.

    Raises:
        TypeError: for a value in a carrier this module will not accept, or for text
            stored into an alphanumeric item as a non-string.
        ValueError: for a group or pointer, a non-finite decimal, or a missing
            component. All PROGRAMMER errors.
    """
    member = _usage_of(usage)
    _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    scale_count = _checked_count("scale", scale) or 0
    text_length = _checked_count("character_length", character_length)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    if member in ALPHANUMERIC_USAGES:
        if text_length is None:
            raise ValueError("character_length is required for an alphanumeric item")
        return _stored_text(_require_text(value), text_length)

    if member not in NUMERIC_USAGES:
        raise ValueError(f"{member.value} has no elementary store")

    units = _stored_units(
        value,
        member=member,
        digit_count=digit_count,
        scale_count=scale_count,
        without_sign=without_sign,
        rounding=rounding,
    )
    if python_storage_for(member, scale_count) is CobolPythonStorage.INT:
        return units
    return _rebuild_decimal(units, scale_count)


# Byte-transparent for the single-byte character set the frozen sources use, so that a
# record's bytes survive a round trip through `str` unchanged.
_TEXT_ENCODING: Final[str] = "latin-1"

# The zoned sign placements that spend a byte of their own, rather than overpunching a
# digit. Unexercised.
_SEPARATE_SIGN_POSITIONS: Final[frozenset[SignPosition]] = frozenset(
    {SignPosition.LEADING_SEPARATE, SignPosition.TRAILING_SEPARATE}
)


def _sign_carrying_index(digit_count: int, position: SignPosition) -> int:
    """Which digit of a zoned item carries the overpunched sign.

    The first for a LEADING sign - `pic s9(7)v99 sign leading`
    [copybooks/wspost-irs.cob:L21] - and the last otherwise. `SignPosition.NONE` on a signed
    item lands here as the last digit deliberately.
    """
    if position is SignPosition.LEADING_INCLUDED:
        return 0
    return digit_count - 1


class ZonedDisplayInt(int):
    """An integer that also carries the zoned DISPLAY bytes it was read out of.

    WHY A ZONED FIELD CANNOT ALWAYS BE MODELLED BY ITS VALUE ALONE. A `pic 9(n)`
    DISPLAY item is n bytes, one per digit, and COBOL reads a digit as a byte's LOW
    NIBBLE with no validity check - so an item holding bytes that are not characters
    `0`..`9` still has a numeric reading, and `_decode_zoned` above computes it. What it
    does NOT have is one reading: GnuCOBOL 3.2 answers a relation on such an item
    DIFFERENTLY depending on what it is compared WITH, and both answers were measured on
    the compiled oracle against the frozen declarations:

    ================================================  ==========================
    `Batch` = 75261, a numeric LITERAL                EQUAL      - numeric reading
    `Batch` = `WS-Batch-Nos`, a same-picture FIELD    NOT EQUAL  - BYTE comparison
    ================================================  ==========================

    Both operands there are `pic 9(5)` DISPLAY - `Batch` [copybooks/wspost.cob:L15] and
    `WS-Batch-Nos` [copybooks/wsbatch.cob:L19] - and `Batch` held the eight bytes the
    frozen bridge's group move leaves in it, `06 8E 0C 15 3B` (ANOMALY N-KEY). A single
    `int` can carry the first answer or the second, never both, so the bytes travel
    beside the value and `arithmetic.compare_zoned_display_fields` uses them.

    IMMUTABLE ON PURPOSE, so the image can never go stale. `int` is immutable, so any
    later `MOVE` into the same record attribute REPLACES this object rather than
    mutating it, and a plain `int` carries no image - which is exactly right, because a
    value that came from anywhere but a byte-level read has the canonical image its
    digits imply.

    Attributes:
        zoned_image: The item's declared-width bytes, verbatim. Never re-derived from
            the value: re-deriving is what loses the anomaly.
    """

    #  NO `__slots__`: CPython refuses a non-empty one on an `int` subtype, because
    # `int` is variable-length. The attribute therefore lives in an instance
    # dictionary, which costs one small dict per corrupt key read and nothing at all
    # for every value that is a plain `int`.
    zoned_image: bytes

    def __new__(cls, value: int, *, zoned_image: bytes) -> "ZonedDisplayInt":
        """Build the value/bytes pair.

        Args:
            value: The item's numeric reading, as COBOL's tolerant zoned read gives it.
            zoned_image: The item's storage bytes, exactly its declared width.

        Returns:
            An `int` that answers every arithmetic and formatting use as `value`, and
                additionally publishes the bytes.

        Raises:
            TypeError: `zoned_image` is not `bytes`.
            ValueError: `zoned_image` is empty. A zero-width DISPLAY item cannot exist,
                so an empty image is a programmer error rather than a data condition.
        """
        if not isinstance(zoned_image, (bytes, bytearray)):
            raise TypeError(
                f"zoned_image must be bytes, not {type(zoned_image).__name__}"
            )
        if not zoned_image:
            raise ValueError(
                "zoned_image is empty; a DISPLAY item is at least one byte wide"
            )
        instance = super().__new__(cls, value)
        object.__setattr__(instance, "zoned_image", bytes(zoned_image))
        return instance

    def __repr__(self) -> str:
        """Show the value AND the bytes, because the pair is the point."""
        return f"ZonedDisplayInt({int(self)}, zoned_image={self.zoned_image!r})"


def zoned_image_of(
    value: object,
    *,
    digits: int,
    signed: bool = False,
    sign_position: SignPosition | str = SignPosition.NONE,
) -> bytes:
    """The zoned DISPLAY bytes of `value`, measured ones in preference to derived ones.

    A `ZonedDisplayInt` publishes the bytes a byte-level read put in the item, and they
    are returned verbatim when their width matches the declaration. Anything else has
    only the canonical layout its digits imply, which `encode` lays out.

    Args:
        value: The item's contents.
        digits: The item's declared digit count, which is its byte width for an
            unsigned zoned item.
        signed: The declaration's sign flag.
        sign_position: Where the sign sits, which decides the layout.

    Returns:
        Exactly `digits` bytes for an unsigned item, and `encode`'s width otherwise.

    Raises:
        TypeError: `value` is a binary floating-point carrier (rule R-2).
        decimal.InvalidOperation: `value` is not an exact numeric.
    """
    carried = getattr(value, "zoned_image", None)
    if isinstance(carried, bytes) and len(carried) == digits:
        return carried
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    numeric: decimal.Decimal | int | str
    if isinstance(value, (decimal.Decimal, int, str)):
        numeric = value
    else:
        raise TypeError(
            f"a zoned DISPLAY item cannot hold {type(value).__name__} (rule R-2)"
        )
    return encode(
        numeric,
        usage=Usage.DISPLAY,
        digits=digits,
        scale=0,
        signed=signed,
        sign_position=sign_position,
    )


def _encode_zoned(
    units: int, digit_count: int, position: SignPosition, without_sign: bool
) -> bytes:
    """Lay out zoned decimal: one byte per digit, sign overpunched or separate."""
    digits_text = format(abs(units), f"0{digit_count}d")
    body = bytearray(ZONED_POSITIVE_BASE[int(character)] for character in digits_text)
    negative = units < 0 and not without_sign

    if position in _SEPARATE_SIGN_POSITIONS:
        sign_byte = (
            SEPARATE_SIGN_BYTE_NEGATIVE if negative else SEPARATE_SIGN_BYTE_POSITIVE
        )
        if position is SignPosition.LEADING_SEPARATE:
            return bytes(bytearray([sign_byte]) + body)
        return bytes(body + bytearray([sign_byte]))

    if negative:
        index = _sign_carrying_index(digit_count, position)
        body[index] = ZONED_NEGATIVE_BASE[int(digits_text[index])]
    return bytes(body)


def _decode_zoned(
    raw: bytes, digit_count: int, position: SignPosition, without_sign: bool
) -> int:
    """Read zoned decimal back, tolerantly, and return its scaled units.

    The digit of each byte is its LOW NIBBLE, which is what makes this tolerant without
    any check being added.
    """
    body = raw
    negative = False

    if position in _SEPARATE_SIGN_POSITIONS:
        if position is SignPosition.LEADING_SEPARATE:
            negative = body[0] == SEPARATE_SIGN_BYTE_NEGATIVE
            body = body[1:]
        else:
            negative = body[-1] == SEPARATE_SIGN_BYTE_NEGATIVE
            body = body[:-1]
    elif not without_sign:
        index = _sign_carrying_index(digit_count, position)
        negative = (body[index] & 0xF0) == ZONED_NEGATIVE_ZONE

    magnitude = 0
    for byte in body:
        magnitude = magnitude * 10 + (byte & 0x0F)
    return -magnitude if negative else magnitude


def _encode_packed(units: int, digit_count: int, without_sign: bool) -> bytes:
    """Lay out packed decimal: two digits per byte, sign in the last nibble."""
    width = byte_length(Usage.COMP_3, digits=digit_count)
    digit_positions = 2 * width - 1
    digits_text = format(abs(units), f"0{digit_positions}d")

    if without_sign:
        sign_nibble = PACKED_SIGN_UNSIGNED
    elif units < 0:
        sign_nibble = PACKED_SIGN_NEGATIVE
    else:
        sign_nibble = PACKED_SIGN_POSITIVE

    nibbles = [int(character) for character in digits_text]
    nibbles.append(sign_nibble)
    return bytes(
        (nibbles[index] << 4) | nibbles[index + 1]
        for index in range(0, len(nibbles), 2)
    )


def _decode_packed(raw: bytes, without_sign: bool) -> int:
    """Read packed decimal back and return its scaled units.

    A digit nibble is accumulated arithmetically, so a nibble above nine yields a
    deterministic value instead of an exception.
    """
    magnitude = 0
    nibbles: list[int] = []
    for byte in raw:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)
    for nibble in nibbles[:-1]:
        magnitude = magnitude * 10 + nibble
    negative = not without_sign and nibbles[-1] == PACKED_SIGN_NEGATIVE
    return -magnitude if negative else magnitude


def encode(
    value: decimal.Decimal | int | str,
    *,
    usage: Usage | str,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
    sign_position: SignPosition | str = SignPosition.NONE,
    rounding: str = _DEFAULT_STORE_ROUNDING,
) -> bytes:
    """Store a value into a field of this description and lay out its bytes.

    The store runs first, exactly as `coerce` performs it - alignment to the receiving
    scale with the caller's rounding, then silent reduction into the field's capacity -
    because a field cannot hold bytes it has no room for.

    Args:
        value: An exact value, as `coerce` accepts.
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required except for the binary family.
        scale: Digits after the implied decimal point; None means none.
        character_length: Required for an alphanumeric item.
        signed: The dictionary's `signed` boolean for the receiving field.
        unsigned: The copybook's `UNSIGNED` keyword.
        sign_position: Where the sign sits, which here decides the layout.
        rounding: A `decimal` rounding mode. Truncating by default.

    Returns:
        Exactly `byte_length(...)` bytes.

    Raises:
        TypeError, ValueError.
    """
    member = _usage_of(usage)
    position = _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    scale_count = _checked_count("scale", scale) or 0
    text_length = _checked_count("character_length", character_length)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    width = byte_length(
        member,
        digits=digit_count,
        scale=scale_count,
        character_length=text_length,
        sign_position=position,
        unsigned=unsigned,
    )

    if member in ALPHANUMERIC_USAGES:
        # `width` is `text_length` here, and `byte_length` has already refused a missing
        # one, so the store below cannot be handed None.
        return _stored_text(_require_text(value), width).encode(_TEXT_ENCODING)

    units = _stored_units(
        value,
        member=member,
        digit_count=digit_count,
        scale_count=scale_count,
        without_sign=without_sign,
        rounding=rounding,
    )

    # A zoned or packed item always declares its digits, and `byte_length` has already
    # refused the call if the caller omitted them, so the fallbacks below are
    # unreachable and exist only to keep the types honest.
    if member in ZONED_DECIMAL_USAGES:
        return _encode_zoned(units, digit_count or 0, position, without_sign)
    if member in PACKED_DECIMAL_USAGES:
        return _encode_packed(units, digit_count or 0, without_sign)
    return units.to_bytes(width, "big", signed=not without_sign)


def decode(
    raw: bytes,
    *,
    usage: Usage | str,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
    sign_position: SignPosition | str = SignPosition.NONE,
) -> decimal.Decimal | int | str:
    """Read a field's bytes back into the carrier its storage class calls for.

    The inverse of `encode`, and deliberately tolerant of bytes `encode` would not have
    produced.

    Args:
        raw: Exactly `byte_length(...)` bytes.
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required except for the binary family.
        scale: Digits after the implied decimal point; None means none.
        character_length: Required for an alphanumeric item.
        signed: The dictionary's `signed` boolean for the field.
        unsigned: The copybook's `UNSIGNED` keyword.
        sign_position: Where the sign sits.

    Returns:
        The field's value in the carrier `python_storage_for` names for it -
            `decimal.Decimal` for anything scaled, `int` for the binary family and for a
            zero-scale integer, `str` for text, padding included.

    Raises:
        TypeError: if `raw` is not a bytes-like object. A PROGRAMMER error.
        ValueError: if the buffer is not the field's width, or as `byte_length` raises
            it. A PROGRAMMER error too.
    """
    member = _usage_of(usage)
    position = _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    scale_count = _checked_count("scale", scale) or 0
    text_length = _checked_count("character_length", character_length)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    if not isinstance(raw, bytes | bytearray | memoryview):
        raise TypeError(f"raw must be bytes-like, not {type(raw).__name__}")
    buffer = bytes(raw)

    width = byte_length(
        member,
        digits=digit_count,
        scale=scale_count,
        character_length=text_length,
        sign_position=position,
        unsigned=unsigned,
    )
    if len(buffer) != width:
        raise ValueError(
            f"a {member.value} field of this description is {width} bytes, "
            f"not {len(buffer)}"
        )

    if member in ALPHANUMERIC_USAGES:
        return buffer.decode(_TEXT_ENCODING)

    if member in ZONED_DECIMAL_USAGES:
        units = _decode_zoned(buffer, digit_count or 0, position, without_sign)
    elif member in PACKED_DECIMAL_USAGES:
        units = _decode_packed(buffer, without_sign)
    else:
        units = int.from_bytes(buffer, "big", signed=not without_sign)

    if python_storage_for(member, scale_count) is CobolPythonStorage.INT:
        return units
    return _rebuild_decimal(units, scale_count)
