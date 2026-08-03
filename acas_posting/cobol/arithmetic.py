"""The COBOL arithmetic verbs: ADD, SUBTRACT, MULTIPLY, DIVIDE and COMPUTE.

Agent Action Plan section 0.3.1 fixes this module in one line - "arithmetic.py
(ADD/SUBTRACT/MULTIPLY/DIVIDE/COMPUTE; default truncate, ROUNDED=half-up)" -
and section 0.1.2 states the two transformation rules it implements: those
verbs WITHOUT `ROUNDED` become `Decimal` arithmetic then
`quantize(..., ROUND_DOWN)`, and WITH `ROUNDED` they become
`quantize(..., ROUND_HALF_UP)` at exactly five sites. Intermediates carry
extended precision; the binary family is `int`.

TRUNCATION IS THE DEFAULT; ROUNDING IS THE ANNOTATED EXCEPTION
==============================================================
Agent Action Plan section 0.1.1, verbatim: "COBOL `COMPUTE` truncates toward
zero on store unless `ROUNDED` is written. Across the entire in-scope cycle
there are exactly five `ROUNDED` sites ... Every other store truncates.
Getting this backwards would corrupt essentially every posted figure, so
truncation is the default and rounding is the annotated exception."

Those five, read from the frozen source:

    [general/gl051.cbl:L791]  in paragraph `net.` (L788)
        compute  vat-amount rounded = post-amount * ws-vat-rate / 100.
    [general/gl051.cbl:L796]  in paragraph `gross.` (L793)
        compute  vat-amount rounded = post-amount - (post-amount /
                 ((ws-vat-rate + 100) / 100)).
    [general/gl080.cbl:L328]
        divide   scycle by period giving a rounded.
    [irs/irs030.cbl:L1551]  in `Net section.` (L1544)
        compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.
    [irs/irs030.cbl:L1562]  in `Gross section.` (L1556), ONE statement split
                            across two physical lines, L1562 and L1563
        compute  vat-amount rounded =
                 post-amount - (post-amount / ((WS-Vat-Current + 100) / 100)).

Counted per file against the frozen sources: `gl051` two, `gl080` one,
`irs030` two, and ZERO in `gl070`, `gl071`, `gl072`, `sl055`, `sl060`,
`sl100`, `pl055`, `pl060` and `pl100`. So `rounded` is a per-CALL keyword
argument defaulting to False, and there is deliberately no module-level,
context-level or descriptor-level rounding mode anyone could switch on. THREE
OF THE FIVE SITES ARE IMMEDIATELY FOLLOWED BY AN UN-ROUNDED STORE, which is
the whole argument for that design:

    [general/gl051.cbl:L797]  subtract vat-amount  from  post-amount.
    [general/gl080.cbl:L329]  multiply a  by  period  giving  y.
    [irs/irs030.cbl:L1564]    subtract vat-amount from post-amount.

A mode would carry rounding across those boundaries and move a posted figure.

Two commented-out predecessors of the IRS pair sit immediately above the live
ones and name a differently spelled rate item, `vat` rather than
`WS-Vat-Current` - anomaly A-19, at [irs/irs030.cbl:L1550] and
[irs/irs030.cbl:L1561]. They are comments, so they are not implemented; they
are recorded so that a reader diffing this module against the frozen program
does not conclude a variant was lost.

WHY THE TWO PYTHON ROUNDING MODES ARE THE RIGHT ONES
====================================================
`decimal.ROUND_DOWN` rounds TOWARD ZERO, not toward negative infinity, so it
matches COBOL truncation for BOTH signs, which the sign flips scattered
through the cycle make load-bearing. `decimal.ROUND_HALF_UP` rounds ties AWAY
FROM ZERO, which is what COBOL `ROUNDED` means and is NOT Python's built-in
banker's rounding:

    ROUND_DOWN      1.999 ->  1.99      -1.999 -> -1.99
    (ROUND_FLOOR would give             -1.999 -> -2.00, which is wrong)
    ROUND_HALF_UP   1.995 ->  2.00      -1.995 -> -2.00
                    1.994 ->  1.99       2.50  ->  3   (into `pic 99`)
    (the default ROUND_HALF_EVEN gives   2.50  ->  2, which is not COBOL)

NO ON SIZE ERROR, NO REMAINDER - SO OVERFLOW IS SILENT
======================================================
`ON SIZE ERROR` occurs ZERO times across the twelve in-scope programs, and so
does `REMAINDER`. Both were counted directly. Two consequences, and neither is
a matter of taste. First, a store whose value does not fit its receiving field
keeps the LOW-ORDER digits and discards the high-order ones, silently: nothing
raises, nothing is clamped, no field is widened and no warning is emitted,
because there is no error path anywhere in the specification to reproduce
(rule R-3). So 12345.67 stored into a five-digit two-place item is 345.67, and
-12345.67 into the signed form of the same item is -345.67. Second, there is
no remainder surface - `DIVIDE ... REMAINDER ...` is not implemented because
no in-scope statement writes it.

The absence of the clause does NOT mean the absence of behaviour, and the two
outcomes it leaves undefined were measured to be DIFFERENT from each other. An
overflowing store stores its low-order digits, as above. A ZERO DIVISOR stores
nothing whatever - the receiving field keeps the value it already held and the
run continues, with no diagnostic and exit status zero. That is question Q-7,
and `SizeErrorNoStore` carries the experiment and the observation.

THE STORE PATH AND THE INTERMEDIATE PATH ARE DIFFERENT
======================================================
`store` quantizes to a receiving field. `intermediate` does not, and it exists
because COBOL evaluates arithmetic inside a relation condition at intermediate
precision with NO receiving field, so nothing truncates there. Six live sites,
all of the form `if line-cnt > Page-Lines - n`: [general/gl051.cbl:L1060],
[general/gl051.cbl:L1111], [sales/sl060.cbl:L621], [sales/sl060.cbl:L691],
[purchase/pl060.cbl:L556] and [purchase/pl060.cbl:L619]. Their operands happen
to be integers - `line-cnt pic 99 comp` [sales/sl060.cbl:L223], `line-cnt
binary-char` [sales/sl100.cbl:L173] and `Page-Lines binary-char unsigned`
[copybooks/wssystem.cob:L65] - so no penny turns on these six. The PATH is
published anyway, because the rule is what matters: a single all-purpose
function that always quantized would silently truncate where COBOL does not,
and a future reader must not conclude from this module's shape that
intermediates truncate.

THE TWO DIVIDE OPERAND ORDERS ARE BOTH LIVE AND BOTH PUBLISHED
==============================================================
`DIVIDE a BY b GIVING c` means c = a / b, at thirteen sites; `DIVIDE a INTO b
GIVING c` means c = b / a, at four. Seventeen in all, every one of them with
GIVING, and each is enumerated with its own locator at the function that
reproduces it - `divide_by_giving` and `divide_into_giving`.

Two of those compute the SAME quotient shape - an accumulator over a counter -
written with the operands reversed, which is the substance of anomaly A-10:

    [sales/sl060.cbl:L827]  divide sales-activety into work-2
                                   giving sales-average.
    [sales/sl100.cbl:L511]  divide work-b by sales-pay-activety
                                   giving sales-pay-average.

So the two are published SEPARATELY, each naming its operands the way its own
verb form does, so that a program module transcribes its own line literally
instead of mentally swapping arguments. They are not one function behind a
flag and neither forwards to the other with the arguments exchanged. Neither
the no-GIVING forms of DIVIDE nor a REMAINDER phrase is published: the census
found no in-scope statement using either.

INTEGER TRUNCATION IS NOT PYTHON'S FLOOR DIVISION
=================================================
Python's floor division FLOORS; COBOL truncates TOWARD ZERO. They agree on
every positive quotient and disagree on every negative one - -7 // 2 is -4
where COBOL gives -3 - so floor division appears nowhere in this module's
arithmetic and every integer quotient goes through
`usage.truncate_toward_zero`, which exists for exactly this reason. It matters
because whole paths of the cycle are integer arithmetic end to end: the seven
sales statistics are picture-less `binary-long` [copybooks/wssl.cob:L46-L52],
including `Sales-Average` at L49 and `Sales-Pay-Average` at L51, and the
program's own working items are `binary-long` too - `work-a`
[sales/sl100.cbl:L182], `work-b` [sales/sl100.cbl:L183].

WHICH CARRIER A RESULT LANDS ON IS THE FIELD'S DECISION, NOT THIS MODULE'S
==========================================================================
`store` returns `decimal.Decimal` or `int` according to the receiving
descriptor's `python_storage`, so the two truncation mechanisms behind anomaly
A-8 are both expressible and NEITHER is the default:

    03  work-2      pic s9(14)    comp-3.        [sales/sl060.cbl:L206]
    03  work-goods  pic s9(7)v99  comp-3.        [sales/sl060.cbl:L218]

`work-2` has ZERO scale while the value added into it carries two, so
`add work-goods to work-2` [sales/sl060.cbl:L826] discards the pence -
truncation number one - and the divide that follows at [sales/sl060.cbl:L827]
stores into a `binary-long`, discarding the remainder - truncation number two.
Meanwhile `03  work-a  binary-long  value zero.` [sales/sl100.cbl:L182] makes
the cash path 32-bit integer arithmetic instead: a DIFFERENT mechanism, in a
different program, reached through the same `store`.

NO AVERAGE HELPER IS PUBLISHED HERE, AND NONE MAY BE ADDED
==========================================================
Three in-scope programs maintain a running average, and the three idioms are
mutually incompatible. Read from the frozen source:

  (a) [sales/sl060.cbl:L816] `ba000-Sales-Comp section.` - a guard on TWO
      conditions (L819, L820), an ELSE that zeroes the accumulator (L823), the
      counter incremented BEFORE the divide (L825), and the INTO form (L827).
  (b) [sales/sl060.cbl:L832] `ba000-Credit-Comp section.` - the same two-part
      guard (L835, L836) but NO counter increment anywhere, which silently
      drops a customer's first credit note (anomaly A-9), PLUS an extra outer
      guard `if work-2 not = zero` (L841) wrapping both the add (L842) and the
      divide (L843).
  (c) [sales/sl100.cbl:L497] `compute-sales-pay.` - a SINGLE-condition guard
      (L506) with no ELSE, the counter incremented AFTER the add (L510), and
      the BY form with the operands reversed (L511).

The purchase mirrors pair [purchase/pl060.cbl:L745] with
[purchase/pl060.cbl:L751], [purchase/pl060.cbl:L760] with
[purchase/pl060.cbl:L766], and [purchase/pl100.cbl:L498] with
[purchase/pl100.cbl:L502].

They differ in five independent dimensions - the number of guard conditions,
whether an ELSE is present, whether and when the counter is incremented, which
DIVIDE verb form is written, and the accumulator's storage class - so a helper
covering all three would need a flag per dimension, at which point it is not a
helper. Agent Action Plan section 0.6.1, verbatim: "All three must be
reproduced as they are. Normalising them into one helper would be the single
easiest way to fail this migration." This module therefore publishes
primitives, each program module writes its own guard, and no `moving_average`,
`running_average` or `average` may ever be added here.

Nothing else is published either: no percentage, no VAT formula, no
apportionment, no rounding-to-pence convenience and no business constant.
Agent Action Plan section 0.3.1 draws the line - "`cobol/` contains no
business logic and `programs/` contains no numeric primitives ... any parity
failure localises immediately to one layer or the other" - so no account
number, no tax rate, no ledger balance, no batch status and no period index
appears below. A numeric literal from the frozen source is quoted only inside
a locator-cited comment or docstring, never written as code.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
MAY import the standard library, `acas_posting.cobol.field` and
`acas_posting.cobol.usage`, and the `acas_posting.dictionary` public surface.
MUST NOT import the records, data-access, program, CLI, clock, date or
work-file layers, the compiled-oracle tree, or the sibling `picture`, `move`,
`condition_names` and `sortverb` modules. No third-party import belongs here:
the pinned dependency set holds nothing this folder needs. The program layer
will import THIS module; the edge runs one way only.

ZERO BINARY FLOATING POINT  (rule R-2, and this module is the primary site)
===========================================================================
Rule R-2, verbatim: "No accounting value may pass through a binary
floating-point type at any point - not in computation, not in storage, not in
transport." Agent Action Plan section 0.7.2 names this file directly:
"`acas_posting/cobol/arithmetic.py` performs all computation on
`decimal.Decimal` with explicit contexts ... Binary integer fields are Python
`int`, never float."

So `float`, `complex`, `math`, `statistics`, `fractions`, the builtin `round`,
`numpy` and `pandas` appear nowhere below, and a `float` or `complex` ARGUMENT
IS REFUSED rather than converted. `decimal.Decimal(0.1)` is
0.1000000000000000055511151231257827021181583404541015625, so accepting a
float would launder a loss that happened before this module was reached. That
refusal is the ONE check here that inspects an argument's type; it is a
PROGRAMMER-error gate protecting rule R-2, not a business validation of the
kind rule R-3 forbids, because it cannot fire on the magnitude or the sign of
a value, only on its carrier. `int`, `decimal.Decimal` and a numeric `str` are
accepted, nothing else is, and a Python `bool` is an `int` by inheritance and
accepted as one - COBOL has no boolean numeric, and a special case would be
exactly the sort of invention rule R-3 rules out.

EXPLICIT DECIMAL CONTEXTS, NEVER THE AMBIENT ONE  (rule R-6)
============================================================
Every computation below runs inside
`decimal.localcontext(INTERMEDIATE_CONTEXT)` and the interpreter's ambient
global context is neither read nor written, so a caller who set
`getcontext().prec = 4` earlier cannot move a posted figure.
`decimal.localcontext` enters a COPY of the context handed to it, so no signal
flag ever accumulates on the module-level object and two runs of one scenario
cannot diverge through it. Nothing here reads a clock, an environment variable
or an entropy source, and no `set` or `dict` iteration is observable: the one
published table is a `MappingProxyType` over two boolean keys.

ARBITRATED AGAINST COMPILED BEHAVIOUR  (rule R-6)
=================================================
Rule R-6 makes compiled behaviour the tie-breaker for an ambiguous semantic
question and requires each resolution to be documented rather than settled
silently. Four bear on this module and ALL FOUR ARE NOW MEASURED against
GnuCOBOL 3.2.0 - the compiler [common/comp-common.sh:L9] names, invoked as the
compile scripts invoke it, with no dialect flag and no arithmetic directive.
Each experiment and its observed output are recorded at the site that uses the
answer. THREE CONFIRMED THE PROVISIONAL BEHAVIOUR AND ONE OVERTURNED IT:

    Q-2  RESOLVED, CONFIRMED. DEFAULT INTERMEDIATE PRECISION. Agent Action
         Plan section 0.6.8, verbatim: "With no dialect flag and no arithmetic
         directive anywhere, the compiler's default intermediate precision
         governs every multi-term expression ... which is the one place a
         precision difference could change a stored penny." Measured: at least
         THIRTY significant decimal digits are carried, and a result is
         quantized ONCE AT THE STORE rather than once per term. See
         `INTERMEDIATE_PRECISION`.
    Q-3  RESOLVED, CONFIRMED. A SIGNED VALUE INTO AN UNSIGNED RECEIVING FIELD.
         Already numbered in the register and CROSS-REFERENCED rather than
         renumbered. Measured: the ABSOLUTE VALUE is stored and the sign is
         dropped silently, at the COBOL level and at the bridge's own narrowing
         alike. The unsigned receiving fields are real - `Input-Gross`,
         `Input-Vat`, `Actual-Gross` and `Actual-Vat` are all `pic 9(9)v99`
         under `03 Amounts comp-3.` [copybooks/wsbatch.cob:L40-L44], and `a`
         and `y` are `pic 99` [general/gl080.cbl:L182-L183]. See `store`,
         step 3; the bridge half is measured at `usage.coerce` and reproduced
         by the data-access layer, which is where anomaly A-11 belongs.
    Q-7  RESOLVED, AND THE PROVISIONAL ANSWER WAS WRONG. DIVISION BY ZERO. The
         provisional behaviour propagated the divide-by-zero, on the reasoning
         that a silent zero would mask a divergence. Measured behaviour is
         neither: GnuCOBOL 3.2 raises the SIZE ERROR condition, PERFORMS NO
         STORE - the receiving field keeps its previous value - and CONTINUES,
         with no diagnostic and exit status zero. Encoded as
         `SizeErrorNoStore`, raised only where the receiving field's previous
         value was not supplied and the no-store outcome therefore cannot be
         returned.
    Q-8  RESOLVED, CONFIRMED. THE SIGN OF AN OVERFLOWING STORE. When the
         low-order digits are kept, is the sign that of the value being
         stored? Measured: yes. -12345.67 into a signed three-digit two-place
         item is -345.67; the sign of the SENDING value survives and there is
         no two's-complement wrap. See `store`, step 4.

Q-7 and Q-8 divide between them the two ways a store can go wrong, and the
compiled answers DIFFER: an OVERFLOWING store truncates silently and stores,
while a ZERO DIVISOR stores nothing at all. `ON SIZE ERROR` occurs zero times
across the twelve in-scope programs, so neither outcome is ever handled by the
specification - which is exactly why both had to be measured rather than
reasoned about.

Numbering audit, so neither register disturbs the other: `Q-3`, `Q-4` and
`Q-6` are in use in `data_dictionary/acas_posting_dictionary.json` and `Q-5.1`
to `Q-5.3` are `usage.py`'s own sub-labels. `Q-2` is the second of the five
questions Agent Action Plan section 0.6.8 lists, a mapping anchored twice: the
dictionary emits `Q-3` for the sign narrowing, that section's third question,
and `Q-4` for the batch record length contradiction, its fourth. `Q-7` and
`Q-8` originate here.

THE FREEZE, NO COBOL AT RUNTIME (R-1), AND SEQUENTIAL EXECUTION (R-3)
=====================================================================
Agent Action Plan section 0.8.1, verbatim: "Any diff touching `common/*.cbl`,
`common/*.scb`, `copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`,
`purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect in the
migration, regardless of how harmless it appears." Every COBOL line quoted
above was read, never written.

The implementation is pure `decimal` and `int`: no subprocess, no
foreign-function interface, no compiler and no runtime library, so the shipped
package runs on a host with neither `cobc` nor `cobcrun` present. And no
thread, no event loop, no process pool and no connection pool - every function
below is a pure function of its arguments with no shared mutable state, which
is what makes the single-threaded COBOL reproducible.
"""

from __future__ import annotations

import decimal
from collections.abc import Callable, Iterable
from types import MappingProxyType
from typing import Final

from acas_posting.cobol import usage as cobol_usage
from acas_posting.cobol.field import TRUNCATING_STORE, FieldDescriptor

# Sorted for reviewability, exactly as the sibling modules sort theirs. The
# DECLARATIONS below run in layering order instead - rounding directions, then
# the intermediate context, then coercion, then the store, then the verbs that
# end in it - because that is the order in which each builds on the last.
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


#  THE TWO STORE DIRECTIONS
#  The whole rounding vocabulary, with two members because COBOL has two store
#  directions and no more. THE SPELLING AT THE CALL SITE IS A KEYWORD-ONLY
#  `rounded: bool`, DEFAULTING TO False, on every verb that stores. It was
#  chosen over an enumeration for three reasons, all about how a module reads:
#  (1) `rounded=True` is the literal word the statement writes, so
#      `divide_by_giving(scycle, period, A, rounded=True)` transcribes
#      `divide scycle by period giving a rounded.` [general/gl080.cbl:L328]
#      word for word, and the 12 statements without ROUNDED simply omit it;
#  (2) being keyword-only it can never be mistaken for a value operand;
#  (3) omitting it yields TRUNCATION, so the direction a caller gets for free
#  cannot corrupt a figure - the way round AAP section 0.1.1 insists on.

# COBOL ROUNDED means round half AWAY FROM ZERO - 1.995 to 2.00 and -1.995 to
# -2.00 - which is `ROUND_HALF_UP` in Python's `decimal`, NOT the built-in
# `round`'s banker's rounding and NOT `ROUND_HALF_EVEN`. Named here rather than
# in the sibling field module because which sites are ROUNDED is this layer's
# knowledge: there are five, they are listed in this module's docstring, and
# the field layer deliberately publishes only the truncating direction.
ROUNDED_STORE: Final[str] = decimal.ROUND_HALF_UP

# The two-member vocabulary, as immutable data rather than as a branch, so that
# the correspondence between the COBOL keyword and the Python rounding mode is
# stated in exactly one place and can be asserted by a test. A
# `MappingProxyType`, so a caller cannot rebind either direction at runtime and
# two runs cannot diverge through it (rule R-6). `TRUNCATING_STORE` is
# `decimal.ROUND_DOWN`, imported from the field layer rather than restated, so
# the default direction has one definition across the whole package.
ROUNDING_DIRECTIONS: Final[MappingProxyType[bool, str]] = MappingProxyType(
    {
        False: TRUNCATING_STORE,
        True: ROUNDED_STORE,
    }
)


def _rounding(rounded: bool) -> str:
    """Return the `decimal` rounding mode a store in this direction takes.

    The single lookup every verb funnels through, so that `rounded=True` can
    only ever mean one thing.
    """
    return ROUNDING_DIRECTIONS[bool(rounded)]


#  THE INTERMEDIATE CONTEXT  (Q-2: RESOLVED against the compiled oracle)

# How many significant digits an intermediate result carries before the single
# quantize at the store. Q-2 asked two things and both were MEASURED against
# GnuCOBOL 3.2.0: how many digits an intermediate carries, and whether the
# quantize to the receiving field's scale happens once at the store or once per
# operator. The width first, storing quotients into a very wide receiver -
#
#       1 / 3 into pic  v9(30)            -> .333333333333333333333333333333
#       2 / 3 into pic  v9(30)  ROUNDED   -> .666666666666666666666666666667
#       1 / 7 into pic  v9(30)            -> .142857142857142857142857142857
#     100 / 7 into pic 9v9(17)            -> 4.28571428571428571
#
# so AT LEAST THIRTY significant digits are carried: the receiver ran out of
# room before the intermediate did, and the ROUNDED line is the proof rather
# than a curiosity - 2/3 truncates to thirty 6s and rounds to a final 7, so the
# intermediate still held a thirty-FIRST digit for the rounding to see. Then the
# placement, which is the part that could have moved a penny -
#
#       2 / 3 + 2 / 3 + 2 / 3   into pic 9v99  ->  1.99   (not 1.98)
#       10 / 3 * 3              into pic 9v99  ->  9.99
#       100 / 7 * 7             into pic 9v99  -> 99.99
#
# 1.99 rather than 1.98 is decisive: had each term been truncated to two places
# on the way, three truncated 0.66s would have summed to 1.98. So the quantize
# happens ONCE, AT THE STORE, which is the model this module already implements
# - one `store` at the end of every verb and no intermediate quantize anywhere.
# The provisional answer was CORRECT on both counts, and the precision below is
# generous rather than merely sufficient: it exceeds the measured 30 with room
# over, so no expression in the cycle can reach it. The widest declared item in
# scope is 14 digits - `03 work-2 pic s9(14) comp-3.` [sales/sl060.cbl:L206] -
# and the widest money item is the 11 digits of `pic 9(9)v99`
# [copybooks/wsbatch.cob:L41], so a product of two needs 28 and the deepest
# expression [general/gl051.cbl:L796] needs far fewer. Here an exactly
# representable result is exact, and a non-terminating quotient carries enough
# digits that no rounding at the last can reach a money store's pence.
#
# ONE FURTHER MEASUREMENT, recorded because it is what makes the parity suite
# able to tell the two models apart. The compound VAT shape at
# [general/gl051.cbl:L796] and its twin [irs/irs030.cbl:L1562] agree to the
# penny under both models for the rate and amount the frozen defaults carry -
# 148.15 at 20 per cent gives 24.69 rounded and 24.69 truncated - while a
# DIFFERENT amount separates them: 33.33 at 20 per cent gives 5.56 ROUNDED and
# 5.55 truncated. So it is that amount, and not the default one, that must be
# the fixture proving the five ROUNDED sites are genuinely rounding. The
# precision stays a named constant rather than an inlined number so that one
# edit re-targets every computation in the migrated cycle.
INTERMEDIATE_PRECISION: Final[int] = 60
# EVERY `decimal` operation in this module runs inside a copy of this context,
# entered with `decimal.localcontext`. The interpreter's ambient global context
# is never read and never written, so a caller who reconfigured `getcontext()`
# earlier cannot move a posted figure (rule R-6). Every field is stated
# explicitly, including those whose value equals the library default, because a
# context inheriting half its settings from `DefaultContext` is one whose
# behaviour depends on the interpreter's state rather than on this file.
# `rounding` is the TRUNCATING direction even though it governs only a result
# exceeding `INTERMEDIATE_PRECISION` significant digits, which nothing in scope
# can produce: it is set this way so that the truncating direction is what any
# operation inside this context takes by default, so a caller's expression that
# quantized on its own would truncate - the safe way for that mistake to land.

# TRAP POLICY, stated once and in full. TRAPPED: InvalidOperation, because
# a non-numeric operand or a NaN is a programmer error and a quiet NaN could
# reach a database column; DivisionByZero, so that a zero divisor can never
# become a quiet Infinity that reaches a database column - the trap is the
# MECHANISM, not the answer, every verb catching it and applying the MEASURED
# Q-7 outcome, which is to store nothing at all (see `SizeErrorNoStore`);
# Overflow, reachable only beyond an exponent of 999999, which no COBOL field
# can express; and FloatOperation, a rule R-2 guard rather than a numeric one -
# it makes `Decimal(<float>)` raise anywhere inside this context, catching a
# float a caller's own expression builds, which the explicit type gate below
# cannot reach. NOT TRAPPED: Inexact, Rounded, Subnormal, Underflow and
# Clamped, because a non-terminating quotient such as [general/gl051.cbl:L796]
# computes is ordinary; trapping it would make the specification's arithmetic
# raise.
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


# =============================================================================
#  THE SIZE ERROR CONDITION  (Q-7: RESOLVED against the compiled oracle)
# =============================================================================


class SizeErrorNoStore(ZeroDivisionError):
    """The compiled program stores NOTHING here and carries on.

    Q-7  RESOLVED - what a division by zero does when no `ON SIZE ERROR`
         clause is written, which is every arithmetic statement in the cycle.

    THE QUESTION.  `ON SIZE ERROR` occurs ZERO times across the twelve
    in-scope programs, so no in-scope statement handles the condition and the
    ISO standard leaves the result undefined. Three outcomes were possible and
    they are not alike: abort the run, store a zero, or store nothing.

    THE EXPERIMENT.  A standalone GnuCOBOL 3.2.0 program, no dialect flag, in
    which a receiving field is PRE-LOADED with a recognisable value and then
    divided by a zero divisor with no `ON SIZE ERROR` clause, in every verb
    form the cycle can reach, with the receiver displayed afterwards:

        01  r    pic s9(5)v99  value +00077.77.
        01  n    pic s9(5)v99  value +00100.00.
        01  z    pic s9(5)v99  value  zero.
        compute r = n / z
        divide  n by z giving r
        divide  n by z giving r remainder rem
        compute r = 5 + (n / z) + 1
        add 1 to ctr-comp / divide ctr-comp by z giving ctr-comp

    THE MEASURED RESULT.  In EVERY form the receiving field kept the value it
    held before the statement - `+00077.77`, and `+00011.11` where that was
    the pre-load - the REMAINDER receiver was untouched as well, no message was
    printed to either stream, the run continued to the next statement, and the
    process exited with status ZERO. The same program with an `ON SIZE ERROR`
    clause added DID fire that clause, which proves the condition raised really
    is SIZE ERROR and not something else. An integer `comp` counter divided by
    zero behaved identically.

    THE RESOLUTION, and it OVERTURNS the provisional answer.  The provisional
    behaviour propagated the divide-by-zero, on the reasoning that a silent
    zero would mask a divergence. That reasoning was sound and the answer was
    still wrong: the compiled program neither aborts nor stores a zero. It
    stores NOTHING, and the receiving field's previous value survives.

    HOW THAT IS ENCODED.  A verb whose receiving field is a GIVING destination
    is not handed that field's previous value, so it cannot return it. Every
    such verb therefore accepts an optional `receiver_value`:

      * SUPPLIED - the verb returns it UNCHANGED, which reproduces the measured
        outcome exactly and lets the caller assign unconditionally.
      * OMITTED - this exception is raised, naming the operation. It is not an
        invented answer and it is not a silent zero: it says that the compiled
        program performs no store and that the information needed to reproduce
        that was not passed in. A calling program module reproduces the
        measurement by catching it and leaving its field alone.

    Either way the caller's field ends up holding what it held before, which is
    the whole of what was measured.

    THIS IS NOT THE OVERFLOW PATH.  A store too wide for its receiving field
    does NOT raise: it truncates the high-order digits silently and keeps the
    sign of the sending value, which is Q-8, measured separately and
    reproduced in `store`. The two conditions share the COBOL name SIZE ERROR
    and behave differently, and conflating them would corrupt every posted
    figure that overflows.

    REACHABILITY - CORRECTED.  This condition IS reachable, at exactly one
    in-scope site, and an earlier reading of this module said otherwise. The
    moving-average divides are guarded by their own business logic -
    [sales/sl060.cbl:L819], [sales/sl060.cbl:L835], [sales/sl100.cbl:L506] each
    test their counter before dividing - and every other divisor in the cycle is
    a literal EXCEPT ONE: `divide scycle by period giving a rounded`
    [general/gl080.cbl:L328], whose divisor is `Period pic 99`
    [copybooks/wssystem.cob] and whose only gate is
    `if a = 9 or scycle < period` [general/gl080.cbl:L326-L327]. `Period` is
    UNSIGNED, so `scycle < 0` is false for every `scycle` and a zeroed system row
    - `period = 0` - falls straight through the gate into the divide. The call
    site therefore passes `receiver_value`, and this exception stays unraised
    there because the measured outcome can be returned rather than announced.
    No guard is added here, because adding one would be an added validation
    (rule R-3) and would hide a real divergence from the oracle.

    docs/migration/ambiguity-resolutions.md carries the register entry; this
    class is the resolution itself, recorded where the condition is raised.

    Attributes:
        operation: The verb form that met the zero divisor, as the COBOL
            statement writes it, so a traceback names the transcription site.
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

    The single place the resolution recorded on `SizeErrorNoStore` is applied,
    so that every verb form reaches it the same way and none can develop its
    own.

    Where the receiving field's previous value was supplied, it is handed back
    UNCHANGED, which is what the compiled program leaves behind. It is routed
    through `store` so that the carrier - `decimal.Decimal` or `int` - is the
    one the field's storage class calls for, whichever carrier the caller
    passed it on; for a value the field could actually have held that pass is
    IDEMPOTENT and changes nothing, which is why it is safe to make.

    Where it was not supplied, `SizeErrorNoStore` is raised rather than a value
    being invented.

    Args:
        operation: The COBOL verb form, for the exception message.
        receiver_value: What the receiving field held before the statement, or
            None if the caller did not pass it.
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

    `0 / 0` is a division by zero in COBOL terms and must reach the same
    measured no-store outcome as `n / 0`, but the two arrive as different Python
    classes because they are different `decimal` CONDITIONS: `n / 0` signals
    DivisionByZero, whose class subclasses `ZeroDivisionError`, while `0 / 0`
    signals DivisionUndefined, whose SIGNAL is `InvalidOperation` and which
    therefore does not.

    THE CONDITION IS READ OFF THE EXCEPTION, because the two `decimal`
    implementations deliver it differently and both must be handled:

    * the C implementation - the one this interpreter runs, `libmpdec` 4.0.0 -
      raises the SIGNAL class and reports the condition in the argument list, so
      `0 / 0` arrives as `InvalidOperation([DivisionUndefined])`;
    * the pure-Python fallback raises the CONDITION class itself, so the same
      divide arrives as `DivisionUndefined`, a subclass of `InvalidOperation`.

    Both are recognised, and nothing else is: `InvalidOperation([ConversionSyntax])`
    from a malformed numeric string and `InvalidOperation([InvalidOperation])`
    from an infinity subtraction are programmer errors this module raises on
    (rule R-2's carrier gate and `_exact`), never a zero divisor to absorb.

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


# =============================================================================
#  COERCION - THE RULE R-2 TYPE GATE

# The message a refused carrier produces. Held as a constant so that every
# caller sees one wording, and so that the rule it protects is named at the
# point of failure rather than left for a reader to look up.
_INEXACT_CARRIER: Final[str] = (
    "rule R-2 forbids a binary floating-point accounting value: {kind} is not "
    "an exact carrier. Pass decimal.Decimal, int, or a numeric str. "
    "decimal.Decimal(0.1) is 0.1000000000000000055511151231257827021181583"
    "404541015625, so converting here would launder a loss that happened "
    "before this module was reached."
)


def _exact(value: decimal.Decimal | int | str) -> decimal.Decimal:
    """Bring one incoming operand into exact decimal form, refusing a float.

    THE ONE CHECK IN THIS MODULE THAT INSPECTS AN ARGUMENT'S TYPE, and a
    PROGRAMMER-error gate protecting rule R-2 rather than a business validation
    of the kind rule R-3 forbids: it cannot fire on the magnitude or the sign
    of a value, only on the carrier it arrived in. A `float` reaching an
    accounting computation has already lost precision, so it is refused by name
    with a message that says why, instead of being quietly converted.

    A Python `bool` is an `int` by inheritance and is accepted as one. COBOL
    has no boolean numeric, so there is nothing for a special case to
    reproduce.

    Non-finite values are not screened here. A NaN or an infinity cannot
    survive what follows: inside `INTERMEDIATE_CONTEXT` an arithmetic operation
    on one raises `decimal.InvalidOperation`, and a store rejects one with a
    `ValueError` from the field layer, which owns that invariant. Restating it
    here would give the same rule two definitions.

    Args:
        value: The operand, as `decimal.Decimal`, `int`, or a numeric `str`.

    Returns:
        The operand as an exact `decimal.Decimal`.

    Raises:
        TypeError: The operand arrived in a carrier that is not exact - a
            `float` or a `complex` - or in a carrier this module does not
            accept at all.
        decimal.InvalidOperation: A `str` operand did not hold a numeric
            literal. Raised by the `decimal` constructor inside this module's
            own trapped context, so a malformed literal always raises rather
            than becoming a quiet NaN in a caller's untrapped context.
    """
    if isinstance(value, (float, complex)):
        raise TypeError(_INEXACT_CARRIER.format(kind=type(value).__name__))
    if isinstance(value, decimal.Decimal):
        return value
    if isinstance(value, int):
        # Exact and context-independent: an int of any width converts without
        # rounding and cannot signal, so no context is entered for it.
        return decimal.Decimal(value)
    if isinstance(value, str):
        # A malformed literal signals InvalidOperation, which this module's
        # context traps. Entered explicitly so the outcome does not depend on
        # whatever trap settings the caller happens to be running under.
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

    A callable is CALLED inside the context, which is the point: the caller's
    own `decimal` arithmetic - every multiply, divide, add and parenthesised
    sub-expression of it - then runs at `INTERMEDIATE_PRECISION` under this
    module's trap policy instead of under whatever the ambient context happens
    to be. A bare value is accepted for the degenerate single-term case and is
    simply coerced.

    Args:
        expression: A zero-argument callable returning an exact value, or an
            exact value.

    Returns:
        The result as an exact `decimal.Decimal`, unquantized.

    Raises:
        TypeError: The expression, or its result, arrived in an inexact
            carrier (rule R-2).
    """
    if callable(expression):
        with decimal.localcontext(INTERMEDIATE_CONTEXT):
            return _exact(expression())
    return _exact(expression)


def _sum(sources: Iterable[decimal.Decimal | int | str]) -> decimal.Decimal:
    """Total a variadic operand list at intermediate precision, exactly.

    ONE running total at `INTERMEDIATE_PRECISION`, so that the quantize into
    the receiving field happens ONCE. Quantizing per term instead would discard
    a fraction of every operand and change the answer: five operands of four
    thousandths each total twenty thousandths, which is two hundredths in a
    two-place field, whereas truncating each one first totals nothing at all.
    The widest live case is five sources -

        add oi-net oi-extra oi-carriage oi-discount oi-deduct-amt
                 giving work-net                   [sales/sl060.cbl:L523]

    - so the arity is genuinely variadic and not a pair.

    Args:
        sources: The operands, in the order the COBOL statement writes them.
            Addition is associative and exact at this precision, so the order
            does not change the total; it is preserved because a reader
            comparing the two sources should see the same sequence.

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

    A PROGRAMMER error - no COBOL statement has an empty operand list, so an
    empty call is a transcription slip rather than a data condition, and it
    would otherwise store the receiver's own value back over itself and look
    like a working line. Cannot fire on any value (rule R-3).

    Raises:
        ValueError: `sources` is empty.
    """
    if not sources:
        raise ValueError(f"{verb} needs at least one operand; none was given")


#  THE STORE - THE ONE AUDITED CHOKEPOINT


def store(
    value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Store an arithmetic result into a receiving field and return it.

    EVERY verb in this module ends here, so there is exactly one place where
    scale alignment, rounding direction, the unsigned sign drop, silent
    high-order truncation and the choice between `decimal.Decimal` and `int`
    are decided - and exactly one place to test exhaustively.

    The five steps, in the order COBOL performs them:

      1. The value is coerced to an exact `decimal.Decimal`. A `float` or
         `complex` is REFUSED (rule R-2); see `_exact`.
      2. It is aligned to the receiving field's scale, TRUNCATING toward zero
         unless `rounded` is passed: 1.999 into a two-place item gives 1.99
         and -1.999 gives -1.99, where `rounded=True` gives 2.00 and -2.00
         from 1.995 and -1.995.
      3. A negative value stored into an UNSIGNED field loses its sign - the
         absolute value is stored, not an error. Such fields are real:
         `pic 9(9)v99` under `03 Amounts comp-3.`
         [copybooks/wsbatch.cob:L40-L44] and `pic 99`
         [general/gl080.cbl:L182-L183]. QUESTION Q-3, RESOLVED and CONFIRMED
         against the compiled oracle: `move -123.45` into `pic 9(3)v99` was
         measured as the bytes `31 32 33 34 35`, the plain digits of 123.45
         with no overpunch anywhere, and `move -123` into `pic 9(3)` as 123.
         The bridge's own narrowing of a signed `binary-long` into an unsigned
         `PIC 9(10) COMP` host variable [common/salesMT.cbl:L1228] was measured
         separately and behaves identically - -5 becomes 0000000005 - so
         anomaly A-11's sign loss is this same rule one layer out.
      4. A value too wide keeps its LOW-ORDER digits and loses the high-order
         ones, SILENTLY - 12345.67 into a five-digit two-place item gives
         345.67. Nothing raises and nothing is clamped, because
         `ON SIZE ERROR` occurs zero times across the twelve in-scope
         programs, so the specification has no error path to reproduce
         (rule R-3). QUESTION Q-8, RESOLVED and CONFIRMED: the SIGN OF THE
         SENDING VALUE survives the truncation. Measured, storing into
         `pic s9(3)v99` and `pic 9(3)`:

             12345.67  ->  +345.67          -12345.67  ->  -345.67
             12345     ->   345             1234.567   ->   234.56

         so the low-order digits are kept with the original sign and there is
         no two's-complement wrap. NOTE that this is the OTHER outcome from
         Q-7's: an overflowing store stores, while a zero divisor stores
         nothing at all. See `SizeErrorNoStore`.
      5. The result comes back on the carrier the field's storage class calls
         for: `decimal.Decimal` for anything scaled, `int` for the binary
         family and for a zero-scale integer. Being DATA-DRIVEN is what makes
         both truncation mechanisms behind anomaly A-8 expressible with
         neither one privileged.

    Steps 2 to 5 are DELEGATED to `FieldDescriptor.store`, and so to
    `usage.coerce`: the storage module already owns those rules byte for byte,
    and a second implementation here could drift without either looking wrong.
    A NUMERIC-EDITED item is stored numerically and no edited string is
    produced; see `divide_by_giving`. Zeroing a field is this same call with a
    zero value - `move zero to work-2` [sales/sl060.cbl:L823].

    Args:
        value: The result to store, as `decimal.Decimal`, `int`, or a numeric
            `str`. Never a binary float (rule R-2).
        receiving: The receiving field's descriptor. Its digits, scale,
            signedness and storage class decide everything above.
        rounded: True ONLY where the COBOL statement writes ROUNDED. Five such
            sites exist in the cycle, listed in this module's docstring.
            Defaults to False, which truncates.

    Returns:
        The value the field holds after the store: `decimal.Decimal` for a
        scaled item, `int` for the binary family and a zero-scale integer.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a receiving field that is
            not numeric - a store across data categories is a MOVE, which is
            the sibling module's subject.
        ValueError: The value is non-finite, or the descriptor omits a
            component its storage class needs. PROGRAMMER errors both.
    """
    if not receiving.is_numeric:
        raise TypeError(
            f"{receiving.name!r} is a {receiving.usage.value} item, which has "
            "no arithmetic store; a store across data categories is a MOVE"
        )
    stored = receiving.store(_exact(value), rounding=_rounding(rounded))
    # `usage.coerce` returns str only for an alphanumeric item, which the guard
    # above has already excluded, so this narrowing is a statement of that fact
    # for a reader and for a type checker rather than a branch that can run.
    if isinstance(stored, str):  # pragma: no cover - excluded by the guard
        raise TypeError(
            f"{receiving.name!r} stored text where a number was expected"
        )
    return stored


#  THE INTERMEDIATE PATH - NO RECEIVING FIELD, SO NO TRUNCATION


def intermediate(
    expression: Callable[[], decimal.Decimal | int | str]
    | decimal.Decimal
    | int
    | str,
) -> decimal.Decimal:
    """Evaluate an expression that has NO receiving field, without quantizing.

    THE COMPANION TO `store`, AND DELIBERATELY NOT THE SAME FUNCTION. COBOL
    evaluates the arithmetic inside a relation condition at intermediate
    precision and compares the result: there is no receiving item, so there is
    nothing to truncate to. Six live sites, every one of the same shape:

        if       line-cnt > Page-Lines - 6      [general/gl051.cbl:L1060]
        if       line-cnt > Page-Lines - 12     [general/gl051.cbl:L1111]
        if       line-cnt > Page-Lines - 7      [sales/sl060.cbl:L621]
        if       line-cnt > Page-Lines - 6 and  [sales/sl060.cbl:L691]
        if       line-cnt > Page-Lines - 7      [purchase/pl060.cbl:L556]
        if       line-cnt > Page-Lines - 6 and  [purchase/pl060.cbl:L619]

    Pair it with `compare` to reproduce such a condition:

        if compare(line_cnt, intermediate(lambda: page_lines - 6)) > 0: ...

    Their operands are integers at all six - `line-cnt pic 99 comp`
    [sales/sl060.cbl:L223], `line-cnt binary-char` [sales/sl100.cbl:L173] and
    `Page-Lines binary-char unsigned` [copybooks/wssystem.cob:L65] - so no
    fraction is at stake in the cycle as it stands. The path is published
    regardless, because routing a relation-condition expression through `store`
    would truncate it to some field's scale, which COBOL does not do, and
    because a reader must not infer from this module's shape that an
    intermediate truncates.

    Always returns a `decimal.Decimal`, never an `int`, precisely because there
    is no storage class in play: an intermediate is a value, not a field.

    Args:
        expression: A zero-argument callable holding the expression - the form
            to prefer, since the caller's own arithmetic then runs inside
            `INTERMEDIATE_CONTEXT` - or an already-computed exact value.

    Returns:
        The result as an exact, UNQUANTIZED `decimal.Decimal`.

    Raises:
        TypeError: The expression, or its result, arrived in an inexact carrier
            (rule R-2).
    """
    return _evaluated(expression)


#  COMPUTE  -  five live statements


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

    There are exactly FIVE live COMPUTE statements in the in-scope cycle. Four
    are the VAT computes and are ROUNDED - [general/gl051.cbl:L791],
    [general/gl051.cbl:L796], [irs/irs030.cbl:L1551] and
    [irs/irs030.cbl:L1562] - and the fifth is un-rounded:

        compute u-bin  = u-year * 365.          [irs/irs030.cbl:L1362]

    The caller writes the expression as ordinary `decimal` arithmetic inside a
    zero-argument callable, and this function evaluates it at
    `INTERMEDIATE_PRECISION` and then performs ONE store. That shape is what
    lets a program module transcribe a nested expression literally:
    [general/gl051.cbl:L796] parenthesises two deep, and its transcription
    keeps the same shape -

        vat_amount = compute(
            lambda: post_amount
            - (post_amount / ((ws_vat_rate + 100) / 100)),
            VAT_AMOUNT,
            rounded=True,
        )

    - with the literal 100 belonging to the program module that transcribes the
    statement, not to this layer.

    ONE store, at the end, and no intermediate quantize: COBOL truncates or
    rounds when it STORES, not at each operator. Passing a callable rather than
    a value is what guarantees the caller's operators run inside this module's
    context; a bare value is accepted for the degenerate single-term case, but
    then the arithmetic that produced it ran wherever the caller was.

    Args:
        expression: A zero-argument callable holding the expression, or an
            already-computed exact value.
        receiving: The receiving field's descriptor.
        rounded: True ONLY where the statement writes ROUNDED - four of the
            five COMPUTE sites do. Defaults to False, which truncates.
        receiver_value: What the receiving field holds BEFORE the statement.
            Needed only to reproduce the measured outcome of a zero divisor,
            which is that the field is left exactly as it was (question Q-7;
            see `SizeErrorNoStore`). None of the five in-scope COMPUTE
            statements can divide by zero - the two VAT forms divide by a rate
            plus 100 and the third by a literal - so it is optional and
            defaults to None.

    Returns:
        What the receiving field now holds. On a zero divisor with
        `receiver_value` supplied, that is the previous value, unchanged.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
        ValueError: A non-finite value, or a descriptor missing a component.
        SizeErrorNoStore: The expression divided by zero and `receiver_value`
            was not supplied, so the measured no-store outcome cannot be
            returned. See that class for the experiment and its result.
    """
    try:
        evaluated = _evaluated(expression)
    except SizeErrorNoStore:
        raise
    except ZeroDivisionError:
        # `decimal.DivisionByZero` from an `x / 0` inside the caller's
        # expression, and the builtin from an integer one.
        return _no_store("COMPUTE", receiver_value, receiving)
    except decimal.InvalidOperation as signalled:
        # A `0 / 0` inside the caller's expression signals DivisionUndefined,
        # whose SIGNAL class is `decimal.InvalidOperation` and NOT a
        # `ZeroDivisionError` - the same distinction `_quotient` records. Here
        # the divisor lives inside the caller's callable and cannot be
        # inspected, so the CONDITION is read off the signal itself; every other
        # InvalidOperation - a signalling NaN, a malformed numeric string - is
        # re-raised as the programmer error it is.
        if _is_undefined_division(signalled):
            return _no_store("COMPUTE", receiver_value, receiving)
        raise
    return store(evaluated, receiving, rounded=rounded)


#  ADD  -  268 live occurrences, 32 of them with GIVING


def add_to(
    *sources: decimal.Decimal | int | str,
    receiver_value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `ADD <sources> TO <receiver>`: the receiver is an operand too.

    The dominant form in the cycle by a wide margin. The receiving item is BOTH
    an operand and the destination, so its current value is passed in and the
    new value is returned; nothing is mutated in place.

    The load-bearing single site is the control-total gate's order of
    operations, where VAT is folded into the actual gross BEFORE the equality
    test that decides whether a batch is accepted:

        add      actual-vat   to  actual-gross.  [general/gl051.cbl:L1109]
        ...
        if       input-gross = actual-gross      [general/gl051.cbl:L1117]
          and    input-vat   = actual-vat        [general/gl051.cbl:L1118]

    Agent Action Plan section 0.1.1, Goal 3, verbatim: "the order of operations
    inside the comparison: VAT is added into the actual gross BEFORE the
    equality test against the entered gross [general/gl051.cbl:L1109-L1118]".
    That ORDER is the calling program module's business; this function supplies
    only the add, and `compare` only the test.

    Other live sites this reproduces: `add ledger-balance to tot-cr.`
    [general/gl072.cbl:L427], `add work-goods to work-2.`
    [sales/sl060.cbl:L826], `add work-a to work-b.` [sales/sl100.cbl:L509],
    `add 1 to sales-activety.` [sales/sl060.cbl:L825], `add 1 to
    sales-pay-activety.` [sales/sl100.cbl:L510] and `add 1 to
    current-quarter.` [general/gl080.cbl:L355].

    The work-goods site is truncation number one of anomaly A-8: `work-goods`
    is `pic s9(7)v99 comp-3` [sales/sl060.cbl:L218] and `work-2` is
    `pic s9(14) comp-3` [sales/sl060.cbl:L206] with ZERO scale, so the pence
    are discarded here, before the divide that discards the remainder.

    A STATEMENT WITH SEVERAL RECEIVERS BECOMES ONE CALL PER RECEIVER, in
    source order. `add oi-paid to t-paid sl-payments` [sales/sl100.cbl:L404]
    and `add il-net to va-v-this va-v-year` [purchase/pl055.cbl:L330] each add
    one source into two fields, and each field applies its own scale, capacity
    and signedness - two stores, not one. A single call taking a list of
    receivers would hide that.

    Args:
        *sources: The operands to add in, in the order the statement writes
            them. Variadic: `ADD a b TO c` is legal COBOL.
        receiver_value: The receiving item's CURRENT value, itself an operand.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope ADD
            does; the argument exists so the verb set is uniform and a future
            ROUNDED site cannot be mis-expressed. Defaults to False.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or
            the descriptor omits a component. PROGRAMMER errors.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
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

    Thirty-two live sites, and genuinely VARIADIC - up to five sources:

        add  post-amount  vat-amount  giving  pre-amount
                                                [general/gl070.cbl:L504]
        add  post-amount  vat-amount  giving  arc-amount
                                                [general/gl080.cbl:L477]
        add  ih-c-vat ih-vat ih-e-vat giving work-2
                                                [sales/sl055.cbl:L444]
        add  oi-vat oi-c-vat oi-e-vat oi-deduct-vat giving work-vat
                                                [sales/sl060.cbl:L520]
        add  oi-net  oi-extra  oi-carriage  oi-discount oi-deduct-amt
                 giving work-net                [sales/sl060.cbl:L523]
        add  ih-net ih-carriage ih-vat ih-c-vat giving ws-inv-amt
                                                [purchase/pl055.cbl:L580]

    Unlike `add_to`, the receiving item contributes NOTHING: whatever it held
    is overwritten.

    THE SOURCES ARE TOTALLED AT INTERMEDIATE PRECISION AND QUANTIZED ONCE, not
    pairwise. Five operands of four thousandths each total twenty thousandths,
    which lands as two hundredths in a two-place field; truncating each operand
    first would land nothing at all. The two answers differ, so the choice is
    stated here rather than left for a reader to infer from the code.

    Args:
        *sources: The operands, in the order the statement writes them.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope ADD
            does. Defaults to False.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or
            the descriptor omits a component.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
    """
    _require_operands(sources, "ADD ... GIVING")
    return store(_sum(sources), receiving, rounded=rounded)


#  SUBTRACT  -  82 live occurrences, 29 of them with GIVING


def subtract_from(
    *sources: decimal.Decimal | int | str,
    receiver_value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `SUBTRACT <sources> FROM <receiver>`: receiver minus the sum.

    The receiving item is both an operand and the destination, and the sources
    are TOTALLED FIRST and then subtracted once - which is what COBOL does, and
    what the multi-source sites require:

        subtract post-amount vat-amount from ws-batch
                                                [irs/irs030.cbl:L967]
        subtract post-amount vat-amount from ws-batch
                                                [irs/irs030.cbl:L1098]
        subtract post-amount vat-amount from ws-default
                                                [irs/irs030.cbl:L1102]

    The single-source form is the net-of-VAT step, and at two of the three
    sites it is the UN-ROUNDED statement that immediately follows a ROUNDED
    compute - which is the clearest demonstration in the cycle of why rounding
    is a per-call argument here and never a mode:

        subtract vat-amount  from  post-amount. [general/gl051.cbl:L797]
        subtract vat-amount from post-amount.   [irs/irs030.cbl:L1564]

    Args:
        *sources: The operands to subtract, in the order the statement writes
            them. Variadic: `SUBTRACT a b FROM c` is legal COBOL.
        receiver_value: The receiving item's CURRENT value - the minuend.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope
            SUBTRACT does. Defaults to False, which truncates.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or
            the descriptor omits a component.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
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

    MIND THE OPERAND ORDER, WHICH READS BACKWARDS. `SUBTRACT a FROM b GIVING c`
    means c = b - a, NOT a - b. The parameters are named after the COBOL
    keywords for exactly that reason - the sources are what the statement lists
    first and subtracts, while `minuend` is the item written after FROM - the
    one they are taken away from - so a call cannot silently invert the sense:

        subtract input-vat  from  input-gross  giving  l9-amount.
                                                [general/gl051.cbl:L1105]
        subtract oi-date from oi-date-cleared giving work-a.
                                                [sales/sl100.cbl:L503]
        subtract oi-approp from oi-paid giving work-1
                                                [sales/sl100.cbl:L391]
        subtract sales-unapplied from sales-current giving l5-old-bal.
                                                [sales/sl060.cbl:L538]
        subtract nl-cr from nl-dr giving ws-default.
                                                [irs/irs030.cbl:L749]
        subtract 1 from ws-lines giving ws-23-lines.
                                                [general/gl070.cbl:L260]

    Transcribed, the first of those keeps the COBOL word order:

        l9_amount = subtract_giving(
            input_vat, minuend=input_gross, receiving=L9_AMOUNT
        )

    The second is the first half of the third moving-average idiom
    [sales/sl100.cbl:L497], whose receiving item `work-a` is `binary-long`
    [sales/sl100.cbl:L182] - so that whole path is integer arithmetic, a
    different mechanism from the packed-decimal accumulator its sibling
    programs use.

    Args:
        *sources: The operands to subtract, in the order written. Variadic.
        minuend: The value they are subtracted FROM.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope
            SUBTRACT does. Defaults to False.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        ValueError: No source operand was given, the value is non-finite, or
            the descriptor omits a component.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
    """
    _require_operands(sources, "SUBTRACT ... FROM ... GIVING")
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        difference = _exact(minuend) - _sum(sources)
    return store(difference, receiving, rounded=rounded)


#  MULTIPLY  -  50 live occurrences, 25 of them with GIVING
#  BOTH FORMS ARE LIVE AND BOTH ARE PUBLISHED; the difference is which
#  operand receives:
#      MULTIPLY a BY b            ->  b = a * b       (the SECOND receives)
#      MULTIPLY a BY b GIVING c   ->  c = a * b
#  The sign-flip idiom that runs through the cycle is written BOTH ways, which
#  is why neither form can be dropped: `multiply -1 by work-2.`
#  [sales/sl055.cbl:L446] against `multiply pre-amount by -1 giving
#  pre-amount.` [general/gl070.cbl:L517].
#  NO `negate` HELPER IS PUBLISHED. It would map faithfully to NEITHER form,
#  and a reader could no longer tell which of them the frozen program wrote -
#  what traceability rule R-5 asks for and normalisation rule R-4 forbids.
def multiply_by(
    multiplier: decimal.Decimal | int | str,
    receiver_value: decimal.Decimal | int | str,
    receiving: FieldDescriptor,
    *,
    rounded: bool = False,
) -> decimal.Decimal | int:
    """Reproduce `MULTIPLY <multiplier> BY <receiver>`: the SECOND receives.

    The no-GIVING form, in which the second operand is both a factor and the
    destination. Every in-scope site is a sign flip written with the literal
    first:

        multiply -1 by work-2.                  [sales/sl055.cbl:L446]
        multiply -1 by work-2.                  [sales/sl055.cbl:L457]
        multiply -1 by work-2.                  [sales/sl055.cbl:L463]
        multiply -1  by  oi-deduct-amt          [sales/sl055.cbl:L658]
        multiply -1  by  oi-discount.           [sales/sl055.cbl:L666]
        multiply -1 by sales-current            [sales/sl060.cbl:L571]
        multiply -1 by work-1.                  [sales/sl060.cbl:L758]
        multiply -1 by work-1.                  [sales/sl060.cbl:L861]
        multiply -1 by work-2.                  [purchase/pl055.cbl:L376]
        multiply -1 by work-2.                  [purchase/pl055.cbl:L387]
        multiply  -1  by  oi-net                [purchase/pl055.cbl:L572]
        multiply  -1  by  oi-c-vat.             [purchase/pl055.cbl:L575]
        multiply -1 by purch-current            [purchase/pl060.cbl:L507]
        multiply -1 by work-1.                  [purchase/pl060.cbl:L683]
        multiply  -1  by  work-1.               [purchase/pl060.cbl:L783]
        multiply -1 by amt-ok                   [irs/irs030.cbl:L1083]

    The nine-field negation block runs [sales/sl055.cbl:L658-L666] and its
    purchase counterpart, four fields long, runs
    [purchase/pl055.cbl:L572-L575]; each line is one call.

    A SIGN FLIP IS STILL A STORE. It truncates to the receiving field's scale
    like any other, and if the receiving field is UNSIGNED it silently loses
    the sign it just applied - question Q-3, measured and recorded at `store`,
    step 3. Neither is an error condition.

    Args:
        multiplier: The first operand - what the statement writes before BY.
        receiver_value: The receiving item's CURRENT value, which is also the
            second factor.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope
            MULTIPLY does. Defaults to False, which truncates.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
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

    The GIVING form: the receiving item contributes nothing and is overwritten.
    Twenty-five live sites, of three kinds - 14 sign flips, 3 scalings and 8
    companions of a divide.

    The sign flips are written with the field first and the literal second, the
    mirror image of the no-GIVING form above, which is why both must exist:

        multiply pre-amount by -1 giving pre-amount.
            [general/gl070.cbl:L517], [general/gl070.cbl:L530]
        multiply arc-amount by -1 giving arc-amount.
            [general/gl080.cbl:L493], [general/gl080.cbl:L506]
        multiply -1 by sales-current giving work-1
            [sales/sl100.cbl:L395], and its purchase twin
            [purchase/pl100.cbl:L387]
        multiply post-amount by -1 giving post-amount.
            [irs/irs030.cbl] at L947, L963, L1096, L1125, L1127, L1139, L1141
            and L1179

    The gl070 pair is the credit leg of the three-leg double-entry explosion.
    As with the no-GIVING form, a flip into an UNSIGNED receiving field
    silently drops the sign - question Q-3, measured and recorded at `store`,
    step 3 - and the store still truncates.

    The scaling multiplies, whose literal factor belongs to the calling program
    module and not to this layer, are `multiply account-in by 100 giving ...`
    at [general/gl051.cbl:L654], [general/gl051.cbl:L657] and
    [general/gl051.cbl:L803].

    The divide companions are `multiply a by period giving y.`
    [general/gl080.cbl:L329], `multiply ws-work1 by 4 giving ws-work2.`
    [irs/irs030.cbl:L1334], and six of the shape `multiply <counter> by
    <average> giving <accumulator>` at [sales/sl060.cbl:L821],
    [sales/sl060.cbl:L837], [sales/sl100.cbl:L507], [purchase/pl060.cbl:L745],
    [purchase/pl060.cbl:L760] and [purchase/pl100.cbl:L498].

    [general/gl080.cbl:L329] is the UN-ROUNDED companion of the ROUNDED divide
    on the line before it [general/gl080.cbl:L328]; the six are the first step
    of the three divergent moving-average idioms, which each program module
    assembles with its own guard. This function supplies the multiply and
    nothing more - see this module's docstring for why no helper bundles them.

    Args:
        multiplier: The first operand - what the statement writes before BY.
        multiplicand: The second operand - what it writes after BY.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope
            MULTIPLY does. Defaults to False, which truncates.

    Returns:
        The value the receiving field holds after the store.

    Raises:
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
        ValueError: A non-finite value, or a descriptor missing a component.
    """
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        product = _exact(multiplier) * _exact(multiplicand)
    return store(product, receiving, rounded=rounded)


#  DIVIDE  -  17 live occurrences, EVERY one of them with GIVING
#  BOTH OPERAND ORDERS ARE LIVE, and they are opposites:
#      DIVIDE a BY   b GIVING c   ->  c = a / b     13 sites
#      DIVIDE a INTO b GIVING c   ->  c = b / a      4 sites
#  Two sites compute the SAME quotient shape with the operands REVERSED:
#  [sales/sl060.cbl:L827] `divide sales-activety into work-2 giving
#  sales-average.` against [sales/sl100.cbl:L511] `divide work-b by
#  sales-pay-activety giving sales-pay-average.` That is anomaly A-10, so both
#  are published separately, named after their COBOL roles. NEITHER `REMAINDER`
#  NOR A NO-GIVING FORM IS IMPLEMENTED - both occur zero times. NO ZERO-DIVISOR
#  GUARD IS ADDED: the frozen programs guard in their own logic
#  [sales/sl060.cbl:L819], [sales/sl060.cbl:L835], [sales/sl100.cbl:L506], and
#  adding one here would be an added validation (rule R-3) that masked a real
#  divergence. A genuine zero divisor therefore takes the MEASURED path rather
#  than a substituted value - GnuCOBOL 3.2 stores nothing at all and continues,
#  which is question Q-7 and which `SizeErrorNoStore` records in full.
def _as_whole(value: decimal.Decimal) -> int | None:
    """Return the exact integer equal to `value`, or None if it has a fraction.

    `Decimal("12.00")` is a whole number written at scale two, so the test is
    against the value and not against the exponent. Used only to decide whether
    `_quotient` may take its exact-integer path.
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

    When an un-ROUNDED divide of two whole numbers lands in an integer field -
    which is every site of the moving-average idiom, because the receiving
    statistics items are picture-less `binary-long`
    [copybooks/wssl.cob:L46-L52] - the quotient is taken with
    `usage.truncate_toward_zero`. That is an exact integer division truncating
    TOWARD ZERO, which is what COBOL does and what Python's `//` does NOT do:
    `truncate_toward_zero(-7, 2)` is -3 where `-7 // 2` is -4.

    The decimal route reaches the same answer for every field width this cycle
    declares - the intermediate context rounds toward zero, so a 60-digit
    quotient truncates to the same integer as the exact one - but taking the
    integer route makes the equality a guarantee rather than a consequence of
    the precision being generous. Both routes end at `store`, so the receiving
    field still decides the carrier, the sign and the overflow behaviour.

    A ROUNDED divide always takes the decimal route: half-away-from-zero is not
    something an exact integer division can express, and the one ROUNDED divide
    in the cycle [general/gl080.cbl:L328] stores into `pic 99`
    [general/gl080.cbl:L183], an integer field, so this distinction is live and
    not theoretical.

    A ZERO DIVISOR is not tested for in advance - the divisor is used, and the
    routes fail differently. `usage.truncate_toward_zero` raises the builtin
    `ZeroDivisionError`. The decimal route raises whichever signal the libmpdec
    trap policy attaches to the CONDITION the operands produce, and there are
    TWO conditions, not one:

        1 / 0   signals DivisionByZero, trapped as `decimal.DivisionByZero`,
                which subclasses `ZeroDivisionError`;
        0 / 0   signals DivisionUndefined, whose SIGNAL - and therefore the
                class the trap raises - is `decimal.InvalidOperation`, which
                does NOT subclass `ZeroDivisionError`.

    Both are a divide by zero in COBOL terms and both must reach the ONE
    measured outcome, `_no_store`, so both are caught. The `InvalidOperation`
    arm is admitted ONLY when the divisor is genuinely zero: the same signal
    also carries a NaN operand and a malformed numeric string, and those are
    programmer errors this module raises on rather than silently turns into a
    no-store (see `_exact`). Nothing here tests the divisor to DECIDE anything -
    the divide has already happened and failed; the test only attributes the
    failure, so no guard is added to the arithmetic itself (rule R-3).
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
        # `usage.truncate_toward_zero`'s builtin, and the decimal route's
        # `decimal.DivisionByZero`, which subclasses it.
        return _no_store(operation, receiver_value, receiving)
    except decimal.InvalidOperation:
        # 0 / 0 - DivisionUndefined, delivered as its signal class.
        # `is_zero()` is a predicate on the value's own class and signals
        # nothing, so a NaN divisor answers False here instead of raising a
        # second exception from inside the handler.
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

    The operands appear in the order the statement writes them, so a call reads
    the same way round as the COBOL. Thirteen live sites, nine of them scalings
    and four computations of substance.

    The scaling divides, whose literal divisor belongs to the calling program
    module and not to this layer, are `divide post-dr by 100 giving acc-ok`
    [general/gl051.cbl:L604] and its post-cr twin [general/gl051.cbl:L607]; the
    report pair `divide post-dr by 100 giving l7-dr.` [general/gl051.cbl:L1035]
    and [general/gl051.cbl:L1037]; `divide vat-ac of WS-Posting-Record by 100
    giving l7-vat-ac.` [general/gl051.cbl:L1044]; `divide WS-Ledger-Nos by 100
    giving l6-account.` at [general/gl072.cbl:L386] and
    [general/gl072.cbl:L413]; and `divide ws-nstrg by 100` / `by 10 giving
    amt-ok` at [irs/irs030.cbl:L1074] and [irs/irs030.cbl:L1077].

    Three of those store into an EDITED receiving item -
    `l6-account pic 9999.99 blank when zero` [general/gl072.cbl:L233] and
    `l7-cr pic zzz9.99b` [general/gl051.cbl:L310]. Only the NUMERIC store
    happens here: digits and scale come from the edited picture, and no edited
    string is produced - rendering is outside this package's surface.

    The four computations of substance:

        divide scycle by period giving a rounded. [general/gl080.cbl:L328]
        divide u-year by 4 giving ws-work1.       [irs/irs030.cbl:L1333]
        divide work-b by sales-pay-activety giving sales-pay-average.
                                                  [sales/sl100.cbl:L511]
        divide work-b by purch-pay-activety giving purch-pay-average.
                                                  [purchase/pl100.cbl:L502]

    The first is THE ONLY ROUNDED DIVIDE IN THE CYCLE, and the only site where
    this function is called with `rounded=True`; its un-ROUNDED companion sits
    on the very next line [general/gl080.cbl:L329]. The second is the leap-year
    test, paired with a multiply [irs/irs030.cbl:L1334]. The last two are the
    third moving-average idiom [sales/sl100.cbl:L497] - written with these
    operands and not the other way round (anomaly A-10) - whose operands are
    both `binary-long` [sales/sl100.cbl:L182-L183], so the quotient truncates
    toward zero as an integer.

    Args:
        dividend: The operand written first - what is divided.
        divisor: The operand written after BY - what it is divided by.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. Exactly one
            in-scope site does, [general/gl080.cbl:L328]. Defaults to False,
            which truncates toward zero.
        receiver_value: What the receiving field holds BEFORE the statement.
            Needed only to reproduce the measured outcome of a zero divisor,
            which is that the field is left exactly as it was (question Q-7;
            see `SizeErrorNoStore`). Every in-scope divisor here is either a
            literal or a counter its own program guards, so it is optional and
            defaults to None.

    Returns:
        What the receiving field now holds. On a zero divisor with
        `receiver_value` supplied, that is the previous value, unchanged.

    Raises:
        SizeErrorNoStore: The divisor is zero and `receiver_value` was not
            supplied, so the measured no-store outcome cannot be returned. It
            subclasses `ZeroDivisionError`, and both internal routes reach it,
            so a caller may catch either name.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
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

    THE OPERANDS ARE THE OTHER WAY ROUND FROM `divide_by_giving`. The item
    written first is the DIVISOR - it is divided INTO the second - so the
    quotient is the second operand over the first. The parameters are named
    after those roles and appear in the order the statement writes them, so a
    transcription stays word for word and the two verb forms cannot be
    confused. All four live sites:

        divide   sales-activety into work-2 giving sales-average.
                                                [sales/sl060.cbl:L827]
        divide sales-activety into work-2 giving sales-average
                                                [sales/sl060.cbl:L843]
        divide   purch-activety into work-2 giving purch-average.
                                                [purchase/pl060.cbl:L751]
        divide purch-activety into work-2 giving purch-average
                                                [purchase/pl060.cbl:L766]

    Transcribed, the first of those is:

        sales_average = divide_into_giving(
            sales_activety, work_2, receiving=SALES_AVERAGE
        )

    All four are the second half of a moving-average idiom, and all four are
    the site of the SECOND of the two truncations that make anomaly A-8. The
    first truncation already happened in the accumulate: `work-2` carries NO
    decimal places, being `pic s9(14) comp-3` [sales/sl060.cbl:L206], while
    the value added into it carries two [sales/sl060.cbl:L218], so the pence
    were discarded at [sales/sl060.cbl:L826]. Here the receiving item is
    `Sales-Average`, a picture-less `binary-long` [copybooks/wssl.cob:L49], so
    the remainder is discarded too.

    The two pairs differ in more than their line numbers: the sales-invoice
    idiom increments its counter before dividing [sales/sl060.cbl:L825] and the
    credit-note idiom never increments it at all (anomaly A-9), which is why
    this module publishes the divide and leaves the guard, the accumulate and
    the counter to each calling program module.

    Args:
        divisor: The operand written first - what is divided INTO the other.
        dividend: The operand written after INTO - what is divided.
        receiving: The receiving field's descriptor.
        rounded: True only where the statement writes ROUNDED. No in-scope
            INTO site does. Defaults to False, which truncates toward zero.
        receiver_value: What the receiving field holds BEFORE the statement.
            Needed only to reproduce the measured outcome of a zero divisor,
            which is that the field is left exactly as it was (question Q-7;
            see `SizeErrorNoStore`). All four in-scope sites are moving-average
            divides whose counter their own program tests first - and one of
            them, anomaly A-9, never increments that counter at all - so it is
            optional and defaults to None.

    Returns:
        What the receiving field now holds. On a zero divisor with
        `receiver_value` supplied, that is the previous value, unchanged.

    Raises:
        SizeErrorNoStore: The divisor is zero and `receiver_value` was not
            supplied, so the measured no-store outcome cannot be returned. It
            subclasses `ZeroDivisionError`, so a caller may catch either name.
        TypeError: An inexact carrier (rule R-2), or a non-numeric receiving
            field.
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


#  RELATION CONDITIONS  -  algebraic comparison, no receiving field


def compare(
    left: decimal.Decimal | int | str,
    right: decimal.Decimal | int | str,
) -> int:
    """Compare two numerics the way a COBOL relation condition compares them.

    COBOL compares numeric operands ALGEBRAICALLY - by value, after aligning
    their decimal points - and not by byte pattern, not by digit string and not
    by storage class. So a two-place value and a one-place value that are
    numerically equal ARE equal, and an integer zero equals a packed-decimal
    zero.

    That is what the batch control-total gate depends on. Its two tests compare
    `pic 9(9)v99 comp-3` items [copybooks/wsbatch.cob:L41-L44]:

        add      actual-vat   to  actual-gross. [general/gl051.cbl:L1109]
        if       input-gross = actual-gross     [general/gl051.cbl:L1117]
          and    input-vat   = actual-vat       [general/gl051.cbl:L1118]

    and the order of those two statements is load-bearing. As AAP section 0.1.1
    Goal 3 puts it: "the order of operations inside the comparison: VAT is
    added into the actual gross BEFORE the equality test against the entered
    gross".
    THE ADD, THE TEST'S CONSEQUENCES AND THE STATUS IT SETS
    [general/gl051.cbl:L1119], [general/gl051.cbl:L1121] ARE BUSINESS LOGIC AND
    BELONG IN THE `gl051` PROGRAM MODULE. This function supplies only the
    comparison.

    It also serves the six relation conditions that compute an expression with
    no receiving field - pair it with `intermediate`, which does not quantize:

        if compare(line_cnt, intermediate(lambda: page_lines - 6)) > 0:

    and the equality tests that are not control totals, such as

        if       scycle not = y                 [general/gl080.cbl:L331]

    which decides whether the end-of-period path runs at all.

    Args:
        left: The operand written on the left of the relational operator.
        right: The operand written on the right.

    Returns:
        -1 when `left` is the smaller, 0 when the two are numerically equal,
        and 1 when `left` is the greater. A COBOL `=` is `compare(...) == 0`,
        a `>` is `> 0`, a `not =` is `!= 0`.

    Raises:
        TypeError: Either operand is an inexact carrier (rule R-2).
        decimal.InvalidOperation: An operand is a NaN, or a `str` operand did
            not hold a numeric literal. There is no receiving field here, so no
            store follows to reject it; this function raises instead of
            answering.
    """
    with decimal.localcontext(INTERMEDIATE_CONTEXT):
        # `compare_signal` rather than `compare`: this module's context traps
        # InvalidOperation, so an unordered comparison RAISES instead of
        # quietly answering NaN and being read as "not equal" by a caller
        # testing `!= 0` - which, at the control-total gate, would silently
        # reject a batch.
        return int(_exact(left).compare_signal(_exact(right)))
