"""The COBOL arithmetic verbs: ADD, SUBTRACT, MULTIPLY, DIVIDE and COMPUTE.

Every operation is performed on `decimal.Decimal` with the precision, scale, sign
and truncation direction of the field that RECEIVES the result (R-2). Nothing
here is a convenience wrapper around Python arithmetic: `store` is where a value
becomes what COBOL would have stored.

TRUNCATION IS THE DEFAULT AND ROUNDING IS THE EXCEPTION. A store without
`ROUNDED` truncates toward zero; `ROUNDED` rounds half away from zero. The whole
migrated cycle contains exactly five `ROUNDED` sites -
[general/gl080.cbl:L328], [general/gl051.cbl:L791], [general/gl051.cbl:L796],
[irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562] - so getting the default
backwards would corrupt essentially every posted figure.

The store path and the intermediate path are different on purpose. COBOL
evaluates arithmetic inside a relation condition at intermediate precision with
no receiving field, so `intermediate` does not quantize; a single all-purpose
function that always quantized would silently truncate where COBOL does not.

Both DIVIDE spellings are published because both are live in the frozen source
and they take their operands in opposite textual order: `DIVIDE a BY b GIVING c`
is c = a / b (thirteen sites) and `DIVIDE a INTO b GIVING c` is c = b / a (four).
Publishing them separately lets a program module transcribe its own line
literally instead of mentally swapping arguments. Note what this does NOT mean:
the two average sites [sales/sl060.cbl:L827] and [sales/sl100.cbl:L511] compute
the SAME quotient - accumulator over activity counter - so their divergence is in
their guards and their counter handling, not in the arithmetic.

Integer truncation is toward zero, not Python's floor. No zero-divisor guard is
added: the frozen programs guard in their own logic
[sales/sl060.cbl:L819], [sales/sl060.cbl:L835], [sales/sl100.cbl:L506], and
adding one here would be an added validation (R-3) masking a real divergence.
"""

from __future__ import annotations

import decimal
from collections.abc import Callable, Iterable
from types import MappingProxyType
from typing import Final

from acas_posting.cobol import usage as cobol_usage
from acas_posting.cobol.field import TRUNCATING_STORE, FieldDescriptor

# Sorted for reviewability, exactly as the sibling modules sort theirs.
__all__: Final[tuple[str, ...]] = (
    "INTERMEDIATE_CONTEXT",
    "INTERMEDIATE_PRECISION",
    "ROUNDED_STORE",
    "ROUNDING_DIRECTIONS",
    "SizeErrorNoStore",
    "add_giving",
    "add_to",
    "compare",
    "compute",
    "divide_by_giving",
    "divide_into_giving",
    "intermediate",
    "multiply_by",
    "multiply_by_giving",
    "store",
    "subtract_from",
    "subtract_giving",
)


# The whole rounding vocabulary, with two members because COBOL has two store directions
# and no more. THE SPELLING AT THE CALL SITE IS A KEYWORD-ONLY `rounded.

# COBOL ROUNDED means round half AWAY FROM ZERO - 1.995 to 2.00 and -1.995 to -2.00 -
# which is `ROUND_HALF_UP` in Python's `decimal`, NOT the built-in `round`'s banker's
# rounding and NOT `ROUND_HALF_EVEN`.
ROUNDED_STORE: Final[str] = decimal.ROUND_HALF_UP

# The two-member vocabulary, as immutable data rather than as a branch, so that the
# correspondence between the COBOL keyword and the Python rounding mode is stated in
# exactly one place and can be asserted by a test.
ROUNDING_DIRECTIONS: Final[MappingProxyType[bool, str]] = MappingProxyType(
    {
        False: TRUNCATING_STORE,
        True: ROUNDED_STORE,
    }
)


def _rounding(rounded: bool) -> str:
    """Return the `decimal` rounding mode a store in this direction takes.

    The single lookup every verb funnels through, so that `rounded=True` can only ever
    mean one thing.
    """
    return ROUNDING_DIRECTIONS[bool(rounded)]


# How many significant digits an intermediate result carries before the single quantize
# at the store. Q-2 asked two things and both were MEASURED against GnuCOBOL 3.2.0.
INTERMEDIATE_PRECISION: Final[int] = 60
# EVERY `decimal` operation in this module runs inside a copy of this context, entered
# with `decimal.localcontext`.

# TRAP POLICY, stated once and in full. TRAPPED.
INTERMEDIATE_CONTEXT: Final[decimal.Context] = decimal.Context(
    prec=INTERMEDIATE_PRECISION,
    rounding=TRUNCATING_STORE,
    Emin=-999999,
    Emax=999999,
    capitals=1,
    clamp=0,
    flags=[],
    traps={
        decimal.Clamped: False,
        decimal.DivisionByZero: True,
        decimal.Inexact: False,
        decimal.InvalidOperation: True,
        decimal.Overflow: True,
        decimal.Rounded: False,
        decimal.Subnormal: False,
        decimal.Underflow: False,
        decimal.FloatOperation: True,
    },
)


class SizeErrorNoStore(ZeroDivisionError):
    """The compiled program stores NOTHING here and carries on.

    THE RESOLUTION, and it OVERTURNS the provisional answer. The provisional behaviour
    propagated the divide-by-zero, on the reasoning that a silent zero would mask a
    divergence. That reasoning was sound and the answer was still wrong.

    Attributes:
        operation: The verb form that met the zero divisor, as the COBOL statement
            writes it, so a traceback names the transcription site.
    """

    def __init__(self, operation: str) -> None:
        """Record which verb form met the zero divisor.

        Args:
            operation: The COBOL verb form, e.g. `DIVIDE ... BY ... GIVING`.
        """
        self.operation = operation
        super().__init__(
            f"{operation}: the divisor is zero. GnuCOBOL 3.2 raises the SIZE "
            "ERROR condition, performs NO STORE and continues, so the "
            "receiving field keeps its previous value (question Q-7, "
            "measured). Pass receiver_value= to have that previous value "
            "returned unchanged, or catch this and leave the field alone. "
            "Storing a zero instead would be an invented answer."
        )


def _no_store(
    operation: str,
    receiver_value: decimal.Decimal | int | str | None,
    receiving: FieldDescriptor,
) -> decimal.Decimal | int:
    """Apply the measured Q-7 outcome for a zero divisor: store nothing.

    The single place the resolution recorded on `SizeErrorNoStore` is applied, so that
    every verb form reaches it the same way and none can develop its own.

    Args:
        operation: The COBOL verb form, for the exception message.
        receiver_value: What the receiving field held before the statement, or None if
            the caller did not pass it.
        receiving: The receiving field's descriptor.

    Returns:
        The receiving field's previous value, on the field's own carrier.

    Raises:
        SizeErrorNoStore: `receiver_value` was not supplied.
    """
    if receiver_value is None:
        raise SizeErrorNoStore(operation)
    return store(receiver_value, receiving)


def _is_undefined_division(signalled: decimal.InvalidOperation) -> bool:
    """Whether an `InvalidOperation` reports `0 / 0` rather than a bad operand.

    `0 / 0` is a division by zero in COBOL terms and must reach the same measured no-
    store outcome as `n / 0`, but the two arrive as different Python classes because
    they are different `decimal` CONDITIONS.

    Args:
        signalled: The exception the trap raised.

    Returns:
        True only for the undefined-division condition.
    """
    reported: tuple[object, ...] = (type(signalled),)
    if signalled.args:
        first = signalled.args[0]
        reported += tuple(first) if isinstance(first, (list, tuple)) else (first,)
    return any(
        isinstance(item, type) and issubclass(item, decimal.DivisionUndefined)
        for item in reported
    )


# The message a refused carrier produces.
_INEXACT_CARRIER: Final[str] = (
    "rule R-2 forbids a binary floating-point accounting value: {kind} is not "
    "an exact carrier. Pass decimal.Decimal, int, or a numeric str. "
    "decimal.Decimal(0.1) is 0.1000000000000000055511151231257827021181583"
    "404541015625, so converting here would launder a loss that happened "
    "before this module was reached."
)


def _exact(value: decimal.Decimal | int | str) -> decimal.Decimal:
    """Bring one incoming operand into exact decimal form, refusing a float.

    PROGRAMMER-error gate protecting rule R-2 rather than a business validation of the
    kind rule R-3 forbids: it cannot fire on the magnitude or the sign of a value, only
    on the carrier it arrived in.

    Args:
        value: The operand, as `decimal.Decimal`, `int`, or a numeric `str`.

    Returns:
        The operand as an exact `decimal.Decimal`.

    Raises:
        TypeError: The operand arrived in a carrier that is not exact - a `float` or a
            `complex` - or in a carrier this module does not accept at all.
        decimal.InvalidOperation: A `str` operand did not hold a numeric literal.
    """
    if isinstance(value, (float, complex)):
        raise TypeError(_INEXACT_CARRIER.format(kind=type(value).__name__))
    if isinstance(value, decimal.Decimal):
        return value
    if isinstance(value, int):
        # Exact and context-independent: an int of any width converts without rounding
        # and cannot signal, so no context is entered for it.
        return decimal.Decimal(value)
    if isinstance(value, str):
        # A malformed literal signals InvalidOperation, which this module's context
        # traps.
        with decimal.localcontext(INTERMEDIATE_CONTEXT):
            return decimal.Decimal(value)
    raise TypeError(_INEXACT_CARRIER.format(kind=type(value).__name__))


def _evaluated(
    expression: Callable[[], decimal.Decimal | int | str]
    | decimal.Decimal
    | int
    | str,
) -> decimal.Decimal:
    """Evaluate an expression in `INTERMEDIATE_CONTEXT`, returning it exact.

    Args:
        expression: A zero-argument callable returning an exact value, or an exact
            value.

    Returns:
        The result as an exact `decimal.Decimal`, unquantized.

    Raises:
        TypeError: The expression, or its result, arrived in an inexact carrier (rule
            R-2).
    """
    if callable(expression):
        with decimal.localcontext(INTERMEDIATE_CONTEXT):
            return _exact(expression())
    return _exact(expression)


def _sum(sources: Iterable[decimal.Decimal | int | str]) -> decimal.Decimal:
    """Total a variadic operand list at intermediate precision, exactly.

    ONE running total at `INTERMEDIATE_PRECISION`, so that the quantize into the
    receiving field happens ONCE. Quantizing per term instead would discard a fraction
    of every operand and change the answer.

    Args:
        sources: The operands, in the order the COBOL statement writes them. Addition is
            associative and exact at this precision, so the order does not change the
            total.

    Returns:
        The total as an exact `decimal.Decimal`.
    """
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        total = decimal.Decimal(0)
        for source in sources:
            total = total + _exact(source)
        return total


def _require_operands(
    sources: tuple[decimal.Decimal | int | str, ...], verb: str
) -> None:
    """Refuse a verb written with no operand at all.

    A PROGRAMMER error - no COBOL statement has an empty operand list, so an empty call
    is a transcription slip rather than a data condition, and it would otherwise store
    the receiver's own value back over itself and look like a working line.

    Raises:
        ValueError: `sources` is empty.
    """
    if not sources:
        raise ValueError(f"{verb} needs at least one operand; none was given")


def store(
    value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Store an arithmetic result into a receiving field and return it.

    EVERY verb in this module ends here, so there is exactly one place where scale
    alignment, rounding direction, the unsigned sign drop, silent high-order truncation
    and the choice between `decimal.Decimal` and `int` are decided - and exactly one
    place to test exhaustively.

    Args:
        value: The result to store, as `decimal.Decimal`, `int`, or a numeric `str`.
            Never a binary float (rule R-2).
        receiving: The receiving field's descriptor. Its digits, scale, signedness and
            storage class decide everything above.
        rounded: True ONLY where the COBOL statement writes ROUNDED. Five such sites
            exist in the cycle, listed in this module's docstring. Defaults to False,
            which truncates.

    Returns:
        The value the field holds after the store: `decimal.Decimal` for a scaled item,
            `int` for the binary family and a zero-scale integer.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a receiving field that is not
            numeric - a store across data categories is a MOVE, which is the sibling
            module's subject.
        ValueError: The value is non-finite, or the descriptor omits a component its
            storage class needs. PROGRAMMER errors both.
    """
    if not receiving.is_numeric:
        raise TypeError(
            f"{receiving.name!r} is a {receiving.usage.value} item, which has "
            "no arithmetic store; a store across data categories is a MOVE"
        )
    stored = receiving.store(_exact(value), rounding=_rounding(rounded))
    # `usage.coerce` returns str only for an alphanumeric item, which the guard above
    # has already excluded, so this narrowing is a statement of that fact for a reader
    # and for a type checker rather than a branch that can run.
    if isinstance(stored, str):  # pragma: no cover - excluded by the guard
        raise TypeError(
            f"{receiving.name!r} stored text where a number was expected"
        )
    return stored


def intermediate(
    expression: Callable[[], decimal.Decimal | int | str]
    | decimal.Decimal
    | int
    | str,
) -> decimal.Decimal:
    """Evaluate an expression that has NO receiving field, without quantizing.

    evaluates the arithmetic inside a relation condition at intermediate precision and
    compares the result: there is no receiving item, so there is nothing to truncate to.
    Six live sites, every one of the same shape.

    Args:
        expression: A zero-argument callable holding the expression - the form to
            prefer, since the caller's own arithmetic then runs inside
            `INTERMEDIATE_CONTEXT` - or an already-computed exact value.

    Returns:
        The result as an exact, UNQUANTIZED `decimal.Decimal`.

    Raises:
        TypeError: The expression, or its result, arrived in an inexact carrier (rule
            R-2).
    """
    return _evaluated(expression)


def compute(
    expression: Callable[[], decimal.Decimal | int | str]
    | decimal.Decimal
    | int
    | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
    receiver_value: decimal.Decimal | int | str | None = None,
) -> decimal.Decimal | int:
    """Reproduce a COBOL COMPUTE: evaluate an expression, then store it once.

    ONE store, at the end, and no intermediate quantize: COBOL truncates or rounds when
    it STORES, not at each operator. Passing a callable rather than a value is what
    guarantees the caller's operators run inside this module's context.

    Args:
        expression: A zero-argument callable holding the expression, or an already-
            computed exact value.
        receiving: The receiving field's descriptor.
        rounded: True ONLY where the statement writes ROUNDED - four of the five COMPUTE
            sites do. Defaults to False, which truncates.
        receiver_value: What the receiving field holds BEFORE the statement.

    Returns:
        What the receiving field now holds. On a zero divisor with `receiver_value`
            supplied, that is the previous value, unchanged.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
        ValueError: A non-finite value, or a descriptor missing a component.
        SizeErrorNoStore: The expression divided by zero and `receiver_value` was not
            supplied, so the measured no-store outcome cannot be returned.
    """
    try:
        evaluated = _evaluated(expression)
    except SizeErrorNoStore:
        raise
    except ZeroDivisionError:
        return _no_store("COMPUTE", receiver_value, receiving)
    except decimal.InvalidOperation as signalled:
        # A `0 / 0` inside the caller's expression signals DivisionUndefined, whose
        # SIGNAL class is `decimal.InvalidOperation` and NOT a `ZeroDivisionError` - the
        # same distinction `_quotient` records.
        if _is_undefined_division(signalled):
            return _no_store("COMPUTE", receiver_value, receiving)
        raise
    return store(evaluated, receiving, rounded=rounded)


def add_to(
    *sources: decimal.Decimal | int | str,
    receiver_value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `ADD <sources> TO <receiver>`: the receiver is an operand too.

    Other live sites this reproduces: `add ledger-balance to tot-cr.`
    [general/gl072.cbl:L427], `add work-goods to work-2.` [sales/sl060.cbl:L826], `add
    work-a to work-b.` [sales/sl100.cbl:L509], `add 1 to sales-activety.`
    [sales/sl060.cbl:L825], `add 1 to sales-pay-activety.` [sales/sl100.cbl:L510] and
    `add 1 to current-quarter.` [general/gl080.cbl:L355].

    Args:
        *sources: The operands to add in, in the order the statement writes them;
            variadic, because `ADD a b TO c` is legal COBOL.
        receiver_value: The receiving item's CURRENT value, itself an operand.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope ADD does.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or the
            descriptor omits a component. PROGRAMMER errors.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
    """
    _require_operands(sources, "ADD ... TO")
    total = _sum((receiver_value, *sources))
    return store(total, receiving, rounded=rounded)


def add_giving(
    *sources: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `ADD <sources> GIVING <receiver>`: the receiver is not summed.

    pairwise. Five operands of four thousandths each total twenty thousandths, which
    lands as two hundredths in a two-place field; truncating each operand first would
    land nothing at all.

    Args:
        *sources: The operands, in the order the statement writes them.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope ADD does.
            Defaults to False.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or the
            descriptor omits a component.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
    """
    _require_operands(sources, "ADD ... GIVING")
    return store(_sum(sources), receiving, rounded=rounded)


def subtract_from(
    *sources: decimal.Decimal | int | str,
    receiver_value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `SUBTRACT <sources> FROM <receiver>`: receiver minus the sum.

    The single-source form is the net-of-VAT step, and at two of the three sites it is
    the UN-ROUNDED statement that immediately follows a ROUNDED compute - which is the
    clearest demonstration in the cycle of why rounding is a per-call argument here and
    never a mode.

    Args:
        *sources: The operands to subtract, in the order the statement writes them;
            variadic, because `SUBTRACT a b FROM c` is legal COBOL.
        receiver_value: The receiving item's CURRENT value - the minuend.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope SUBTRACT
            does. Defaults to False, which truncates.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or the
            descriptor omits a component.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
    """
    _require_operands(sources, "SUBTRACT ... FROM")
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        difference = _exact(receiver_value) - _sum(sources)
    return store(difference, receiving, rounded=rounded)


def subtract_giving(
    *sources: decimal.Decimal | int | str,
    minuend: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `SUBTRACT <sources> FROM <minuend> GIVING <receiver>`.

    The second is the first half of the third moving-average idiom
    [sales/sl100.cbl:L497], whose receiving item `work-a` is `binary-long`
    [sales/sl100.cbl:L182] - so that whole path is integer arithmetic, a different
    mechanism from the packed-decimal accumulator its sibling programs use.

    Args:
        *sources: The operands to subtract, in the order written. Variadic.
        minuend: The value they are subtracted FROM.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope SUBTRACT
            does. Defaults to False.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or the
            descriptor omits a component.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
    """
    _require_operands(sources, "SUBTRACT ... FROM ... GIVING")
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        difference = _exact(minuend) - _sum(sources)
    return store(difference, receiving, rounded=rounded)


# MULTIPLY - 50 live occurrences, 25 of them with GIVING BOTH FORMS ARE LIVE AND BOTH
# ARE PUBLISHED; the difference is which operand receives.
def multiply_by(
    multiplier: decimal.Decimal | int | str,
    receiver_value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `MULTIPLY <multiplier> BY <receiver>`: the SECOND receives.

    Args:
        multiplier: The first operand - what the statement writes before BY.
        receiver_value: The receiving item's CURRENT value, which is also the second
            factor.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope MULTIPLY
            does. Defaults to False, which truncates.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
        ValueError: A non-finite value, or a descriptor missing a component.
    """
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        product = _exact(multiplier) * _exact(receiver_value)
    return store(product, receiving, rounded=rounded)


def multiply_by_giving(
    multiplier: decimal.Decimal | int | str,
    multiplicand: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `MULTIPLY <multiplier> BY <multiplicand> GIVING <receiver>`.

    The sign flips are written with the field first and the literal second, the mirror
    image of the no-GIVING form above, which is why both must exist.

    Args:
        multiplier: The first operand - what the statement writes before BY.
        multiplicand: The second operand - what it writes after BY.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope MULTIPLY
            does. Defaults to False, which truncates.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
        ValueError: A non-finite value, or a descriptor missing a component.
    """
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        product = _exact(multiplier) * _exact(multiplicand)
    return store(product, receiving, rounded=rounded)


def _as_whole(value: decimal.Decimal) -> int | None:
    """Return the exact integer equal to `value`, or None if it has a fraction.

    `Decimal("12.00")` is a whole number written at scale two, so the test is against
    the value and not against the exponent. Used only to decide whether `_quotient` may
    take its exact-integer path.
    """
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        if value == value.to_integral_value(rounding=TRUNCATING_STORE):
            return int(value)
    return None


def _quotient(
    dividend: decimal.Decimal,
    divisor: decimal.Decimal,
    receiving: FieldDescriptor,
    *,
    rounded: bool,
    operation: str,
    receiver_value: decimal.Decimal | int | str | None,
) -> decimal.Decimal | int:
    """Divide and store, by the exact integer route wherever COBOL's is exact.

    When an un-ROUNDED divide of two whole numbers lands in an integer field - which is
    every site of the moving-average idiom, because the receiving statistics items are
    picture-less `binary-long` [copybooks/wssl.cob:L46-L52] - the quotient is taken with
    `usage.truncate_toward_zero`.
    """
    try:
        if not rounded and receiving.is_int:
            whole_dividend = _as_whole(dividend)
            whole_divisor = _as_whole(divisor)
            if whole_dividend is not None and whole_divisor is not None:
                exact = cobol_usage.truncate_toward_zero(
                    whole_dividend, whole_divisor
                )
                return store(exact, receiving)
        with decimal.localcontext(INTERMEDIATE_CONTEXT):
            quotient = dividend / divisor
    except ZeroDivisionError:
        return _no_store(operation, receiver_value, receiving)
    except decimal.InvalidOperation:
        # 0 / 0 - DivisionUndefined, delivered as its signal class.
        if divisor.is_zero():
            return _no_store(operation, receiver_value, receiving)
        raise
    return store(quotient, receiving, rounded=rounded)


def divide_by_giving(
    dividend: decimal.Decimal | int | str,
    divisor: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
    receiver_value: decimal.Decimal | int | str | None = None,
) -> decimal.Decimal | int:
    """Reproduce `DIVIDE <dividend> BY <divisor> GIVING <receiver>`: a / b.

    The operands appear in the order the statement writes them, so a call reads the same
    way round as the COBOL. Thirteen live sites, nine of them scalings and four
    computations of substance.

    Args:
        dividend: The operand written first - what is divided.
        divisor: The operand written after BY - what it is divided by.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. Exactly one in-scope site
            does, [general/gl080.cbl:L328]. Defaults to False, which truncates toward
            zero.
        receiver_value: What the receiving field holds BEFORE the statement.

    Returns:
        What the receiving field now holds. On a zero divisor with `receiver_value`
            supplied, that is the previous value, unchanged.

    Raises:
        SizeErrorNoStore: The divisor is zero and `receiver_value` was not supplied, so
            the measured no-store outcome cannot be returned.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
        ValueError: A non-finite value, or a descriptor missing a component.
    """
    return _quotient(
        _exact(dividend),
        _exact(divisor),
        receiving,
        rounded=rounded,
        operation="DIVIDE ... BY ... GIVING",
        receiver_value=receiver_value,
    )


def divide_into_giving(
    divisor: decimal.Decimal | int | str,
    dividend: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
    receiver_value: decimal.Decimal | int | str | None = None,
) -> decimal.Decimal | int:
    """Reproduce `DIVIDE <divisor> INTO <dividend> GIVING <receiver>`: b / a.

    THE OPERANDS ARE THE OTHER WAY ROUND FROM `divide_by_giving`. The item written first
    is the DIVISOR - it is divided INTO the second - so the quotient is the second
    operand over the first.

    Args:
        divisor: The operand written first - what is divided INTO the other.
        dividend: The operand written after INTO - what is divided.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope INTO site
            does. Defaults to False, which truncates toward zero.
        receiver_value: What the receiving field holds BEFORE the statement.

    Returns:
        What the receiving field now holds. On a zero divisor with `receiver_value`
            supplied, that is the previous value, unchanged.

    Raises:
        SizeErrorNoStore: The divisor is zero and `receiver_value` was not supplied, so
            the measured no-store outcome cannot be returned.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving field.
        ValueError: A non-finite value, or a descriptor missing a component.
    """
    return _quotient(
        _exact(dividend),
        _exact(divisor),
        receiving,
        rounded=rounded,
        operation="DIVIDE ... INTO ... GIVING",
        receiver_value=receiver_value,
    )


def compare(
    left: decimal.Decimal | int | str,
    right: decimal.Decimal | int | str,
) -> int:
    """Compare two numerics the way a COBOL relation condition compares them.

    COBOL compares numeric operands ALGEBRAICALLY - by value, after aligning their
    decimal points - and not by byte pattern, not by digit string and not by storage
    class.

    Args:
        left: The operand written on the left of the relational operator.
        right: The operand written on the right.

    Returns:
        -1 when `left` is the smaller, 0 when the two are numerically equal, and 1 when
            `left` is the greater.

    Raises:
        TypeError: Either operand is an inexact carrier (rule R-2).
        decimal.InvalidOperation: An operand is a NaN, or a `str` operand did not hold a
            numeric literal.
    """
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        # `compare_signal` rather than `compare`.
        return int(_exact(left).compare_signal(_exact(right)))
