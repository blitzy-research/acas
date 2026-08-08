"""VAT FROM GROSS - the three-level compound COMPUTE and its destructive subtract.

File 9 of 14 in the arithmetic parity tier. It pins the `Gross` section of
`irs/irs030.cbl` together with its structurally identical General Ledger mirror in
`general/gl051.cbl`; between them they are the whole of the VAT-from-gross
formulation in the migrated posting cycle. The sibling `test_irs_vat_from_net.py`
owns the `Net` formulation, and the two files divide the subject on a fact rather
than on taste: `Gross` ends with a destructive subtract and `Net` does not.

PROVENANCE OF RULES - READ FIRST
    The six binding rules R-1 .. R-6 live in the Technical Specification section
    0.7.2 and are restated below wherever they bite. Where the specification is
    silent, enterprise-standard practice applies.

THE FROZEN SPECIFICATION, VERBATIM
    `irs/irs030.cbl` lines 1556-1567, exactly as they stand in the checkout:

        1556:  Gross section.
        1557: *>------------
        1558: *>
        1559: *> calculate vat from gross
        1560: *>
        1561:  *>    compute  vat-amount rounded = post-amount - (post-amount / ( (vat + 100) / 100)).
        1562:      compute  vat-amount rounded =
        1563:               post-amount - (post-amount / ( (WS-Vat-Current + 100) / 100)).
        1564:      subtract vat-amount from post-amount.
        1565: *>
        1566:  Main-Exitb.
        1567:      exit.

    Four facts in that block are load-bearing, and this file asserts every one.

    1.  ONE `COMPUTE` SPANNING TWO PHYSICAL LINES, L1562-L1563. The statement is a
        single one; the line break after the `=` is COBOL continuation and carries
        no semantics. The General Ledger mirror writes the same statement on ONE
        physical line, [general/gl051.cbl:L796] - same semantics, different
        physical form, and `test_gl_mirror_is_the_same_three_level_expression`
        proves the two reduce to the same expression.

    2.  THREE LEVELS OF NESTING:

            post-amount - ( post-amount / ( ( rate + 100 ) / 100 ) )

        the outer subtract, the middle divide, and the innermost
        percentage-to-multiplier conversion. There is no `vat` helper, no
        `percentage` helper and no `round_to_pence` helper in
        `acas_posting.cobol.arithmetic`, and this file deliberately does not invent
        one: the formula is spelled out at each site so a reader can diff it
        against the COBOL line by eye.

    3.  L1564 IS A DESTRUCTIVE, UN-`ROUNDED` SUBTRACT that reduces `post-amount` IN
        PLACE, turning the gross figure into the net one. CITATION CORRECTION: the
        Technical Specification body cites "the net-of-VAT subtraction
        [irs/irs030.cbl:L1565]"; L1565 is a `*>` comment line. The real statement
        is [irs/irs030.cbl:L1564], verified in the checkout, and every citation in
        this file uses L1564.

    4.  THE `ROUNDED` / UN-`ROUNDED` PAIR. [irs/irs030.cbl:L1562-L1563] is one of
        the FIVE `ROUNDED` sites in the entire migrated cycle, and
        [irs/irs030.cbl:L1564] - the very next statement - is un-`ROUNDED`. Quoting
        section 0.1.1, because this is one of those five: "Every other store
        truncates. Getting this backwards would corrupt essentially every posted
        figure, so truncation is the default and rounding is the annotated
        exception." Two adjacent statements needing opposite store directions is
        why rounding is a PER-CALL keyword argument in
        `acas_posting.cobol.arithmetic` and can NEVER be a module-level or
        context-level mode.
        `test_rounded_compute_and_unrounded_subtract_are_one_per_call_pair`
        performs both stores in sequence in a single test and
        `test_no_module_level_rounding_switch_exists` closes the door on the mode.

QUANTIZE ONCE - THE CENTRAL CONCERN
    Section 0.6.8 names this expression as "the one place a precision difference
    could change a stored penny". The whole compound expression is therefore
    evaluated at `arithmetic.INTERMEDIATE_CONTEXT` precision - 60 significant
    digits - and quantized EXACTLY ONCE, at the store into `vat-amount`.
    `test_per_sub_expression_quantization_shifts_the_stored_penny` demonstrates the
    consequence with two deliberately constructed input pairs, recorded in the test
    itself, in which quantizing a sub-expression early moves the stored penny.

THE Q- IDS THIS FILE USES (rule R-6)
    Q-2  DEFAULT ARITHMETIC PRECISION - the intermediate precision of this
         compound expression. This file OWNS it, because section 0.6.8 names the
         compound VAT expression explicitly. The id is not newly minted: it is
         already the recorded id for the same question at
         `acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION`, where the answer is recorded as
         MEASURED against GnuCOBOL 3.2.0, and in
         `docs/migration/ambiguity-resolutions.md`, which carries `Q-2` as
         `RESOLVED BY ORACLE` with the probe, its captured table and the rejected
         reading measured for contrast. ONE STATUS, IN BOTH PLACES. Q-2 asks two
         things and they were closed by different means: the SHAPE - evaluate the
         whole expression, then quantize ONCE, at the store - by the language,
         because a `ROUNDED` phrase belongs to the store; and the NUMBER OF
         INTERMEDIATE DIGITS by measurement, there being no `-std=` selection, no
         `>>SET ARITHMETIC` directive and no `binary-truncate` flag anywhere in the
         frozen scripts to read it from.

    Rule R-6 forbids reading the COBOL and reasoning about what it ought to
    produce; expected values come from the compiled oracle. This file honours that
    by splitting the pennies it asserts in two:

      * A penny whose exact value TERMINATES is precision-INDEPENDENT - every
        intermediate precision at or above a handful of digits yields the same
        figure - so no oracle capture can change it and it is asserted directly,
        with a provenance comment naming the arbitrated rounding direction.
        `rate = 20.00` gives the divisor `1.20` exactly and `99.99 / 1.20 =
        83.325` exactly, so the whole statement is exact in five significant
        digits.

      * A penny from a NON-TERMINATING quotient - `rate = 17.50` gives the divisor
        `1.175`, and `1000.00 / 1.175` repeats forever - is exactly the value
        section 0.6.8 warns about. Its literal is NOT guessed here and never was:
        it is looked up in `ORACLE_CAPTURED_PENNIES`, and that table is now
        POPULATED from the compiled oracle. Four rows were measured
        on GnuCOBOL 3.2.0 under the frozen statement, and the `117.55` row is the
        discriminating one - it reads 17.51, which only extended precision with a
        single rounding at the store produces. A capture identity that is still
        absent raises `OracleCaptureUnavailable` rather than inventing a figure, so
        a new operand pair cannot be smuggled in as an assumption, and the
        `xfail(strict=True)` this proposition once carried against Q-2 is gone
        because the question it deferred to has an answer.

ANOMALY A-19 - RECORDED, NOT IMPLEMENTED (rule R-4)
    [irs/irs030.cbl:L1561] holds a superseded, commented-out variant of the live
    compute:

         *>    compute  vat-amount rounded = post-amount - (post-amount / ( (vat + 100) / 100)).

    It names `vat` where the live statement names `WS-Vat-Current`, and the
    difference is behavioural rather than cosmetic. `irs030` copies
    `irswssystem.cob` into its LINKAGE SECTION at [irs/irs030.cbl:L416-L417]
    WITHOUT renaming `vat`, so `vat` there is `05 vat pic 99v99`
    [copybooks/irswssystem.cob:L27] - the FIRST of the three IRS parameter rates,
    and only ever the first. The live `WS-Vat-Current` [irs/irs030.cbl:L277] is
    loaded from `WS-Vat-Rate (WS-Vat-Number)` [irs/irs030.cbl:L721], itself filled
    from `VAT-Psent (b)` [irs/irs030.cbl:L1472], so the live statement uses
    WHICHEVER rate the posting's VAT code selects. Reinstating the superseded line
    would silently force every posting onto rate 1.

    The same program copies `wssystem.cob` at [irs/irs030.cbl:L419] and renames
    `Vat` to `VatCode` at [irs/irs030.cbl:L436] precisely to keep that name clear
    of `05 Vat pic x` [copybooks/wssystem.cob:L173], the IRS fan-out switch - which
    is a third, alphanumeric item that the bare name `vat` could otherwise have
    reached. The superseded line is NOT implemented anywhere in this migration.
    `test_a19_superseded_variant_is_not_implemented` locks the record by proving
    the rate selection is observable. The `Net` path has its own superseded variant
    at [irs/irs030.cbl:L1550]; it belongs to `test_irs_vat_from_net.py` and is not
    duplicated here.

THE GENERAL LEDGER MIRROR
    `general/gl051.cbl` lines 793-797:

        793:  gross.
        796:      compute  vat-amount rounded = post-amount - (post-amount / ((ws-vat-rate + 100) / 100)).
        797:      subtract vat-amount  from  post-amount.

    The SAME `ROUNDED`-then-un-`ROUNDED` pair: [general/gl051.cbl:L796] is one of
    the five `ROUNDED` sites and [general/gl051.cbl:L797] is its un-`ROUNDED`
    successor. Its receivers are wider, and the width matters: `gl051` copies
    `wspost.cob` at [general/gl051.cbl:L132], so its `post-amount` is
    `pic s9(8)v99` [copybooks/wspost.cob:L23] and its `vat-amount` is
    `pic s9(8)v99` [copybooks/wspost.cob:L28] - ten digits with a TRAILING included
    sign - against the IRS record's nine digits with a LEADING one,
    [copybooks/irswspost.cob:L14] and [copybooks/irswspost.cob:L18]. (The
    Technical Specification names those two locators in the reverse order to the
    field names; the checkout has POST-AMOUNT at L23 and VAT-AMOUNT at L28, and
    this file cites each correctly.)
    `test_irs_seven_integer_digits_overflow_where_gl_eight_do_not` drives an amount
    through the gap.

WHAT THIS FILE MAY REACH (the tier contract, rule R-1)
    "The compiled oracle exists only under harness/ and is consumed only by
    tests/scenarios/* and tests/determinism/* as an out-of-process comparison;
    tests/arithmetic/* touch neither COBOL nor a database." Accordingly this module
    imports `pytest`, the standard library, `acas_posting.cobol` and
    `acas_posting.dictionary` - and nothing else. No database, no COBOL, no
    Docker, no subprocess, no file reading. Its one prerequisite is
    `data_dictionary/acas_posting_dictionary.json`, and it runs from the repository
    root on a bare host.

    Rule R-2 bars binary floating point outright: every value here is
    `decimal.Decimal` or `int`, every comparison is exact, and there is no
    tolerance, no approximate comparison helper and no closeness helper anywhere in
    the file. numpy and pandas are absent from the project's dependency sets for
    the same reason. Rule R-3 bars added validation and concurrency: a zero VAT
    rate is asserted exactly as the frozen program leaves it, unguarded, and the
    tier is strictly sequential with no parallel runner. Rule R-5 requires
    traceability: every test names the `[path:Lnnn]` it pins, and coverage is
    evidence only - the project sets no coverage failure threshold. Section 0.8.4
    bars timing and performance assertions, and there are none.

    Every value that could be affected by the process-wide decimal context is
    computed through `acas_posting.cobol.arithmetic`, which enters its own context,
    so this file passes unchanged in a session where an earlier test has narrowed
    `decimal.getcontext()` - verified by running it under a hostile four-digit
    ambient context.

ONE DELIBERATE DEPARTURE FROM THE HOUSE STYLE
    Every line of code and prose in this file stays inside the 88-column budget its
    sibling modules keep. FIVE lines exceed it, and all five are VERBATIM
    quotations of frozen COBOL: [irs/irs030.cbl:L1561] is 88 characters in the
    checkout, [general/gl051.cbl:L796] is 93, and [irs/irs030.cbl:L1563] is 76 but
    crosses the budget once the quoting indent and its line-number prefix are added.
    Wrapping or eliding a quotation would falsify it, which matters more here than a
    column count, so all three are reproduced exactly and this paragraph records
    why.
"""

from __future__ import annotations

import contextlib
import importlib
import dataclasses
import decimal
import dis
import sys
import types
from collections.abc import Callable, Iterator, Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import Final

import pytest

from acas_posting.cobol import arithmetic
from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  SECTION 0  -  THE PROVENANCE RULE FOR EVERY ASSERTED FIGURE (rule R-6)
#
#  Stated once here so that each site can carry a short `# oracle:` line rather
#  than repeat the argument. EVERY figure this file asserts falls into exactly one
#  of four classes, and no figure falls outside them:
#
#    (a) EXACT AND TERMINATING, therefore precision-INDEPENDENT. `rate = 20.00`
#        gives the divisor `1.20` exactly and `99.99 / 1.20 = 83.325` exactly, so
#        every figure on that path needs five significant digits and no more. Only
#        the DIRECTION of the store is in question, and that is settled BY THE
#        LANGUAGE rather than by a measurement of this project's:
#        `acas_posting/cobol/arithmetic.py ROUNDED_STORE` records COBOL ROUNDED as
#        half away from zero. Question Q-2's other half is the intermediate
#        PRECISION, measured against GnuCOBOL 3.2.0, and it cannot reach these
#        figures either, so they are asserted directly.
#
#    (b) A FIELD-CAPACITY OR SIGN FACT, not an arithmetic result: a store past a
#        field's declared digits keeps the low-order digits, and an unsigned
#        receiver drops the sign. The census finds ZERO `ON SIZE ERROR` phrases in
#        the twelve in-scope programs, so there is no handler to reproduce, and
#        GnuCOBOL's default binary-size and binary-truncate policy is recorded
#        RESOLVED in `acas_posting.cobol.usage` as question Q-5.1. Also not
#        un-arbitrated, so also asserted directly.
#
#    (c) STRUCTURAL - derived inside the test from the inputs by the statement
#        under test, never written down as a literal expectation of what the
#        compiled program produces.
#
#    (d) NON-TERMINATING, therefore precision-DEPENDENT, and taken from the
#        compiled oracle through `ORACLE_CAPTURED_PENNIES` rather than derived.
#        `rate = 17.50` is the whole of this class in this file, and it is now
#        MEASURED - see question Q-2 in docs/migration/ambiguity-resolutions.md.
#
#  A figure asserted anywhere below WITHOUT one of these four justifications would
#  be a guessed penny, which rule R-6 forbids outright.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#  SECTION 1  -  THE QUESTION REGISTER (rule R-6)
#
#  One entry, spelled out in full, because a bare "Q-2" in an xfail reason tells a
#  reader nothing. The id is the one already in use for this question at
#  acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION; it is not newly minted here.
# ---------------------------------------------------------------------------

Q_INTERMEDIATE_PRECISION: Final[str] = (
    "Q-2 (DEFAULT ARITHMETIC PRECISION): with no -std= dialect flag, no "
    ">>SET ARITHMETIC directive and no binary-truncate flag anywhere in the "
    "frozen build scripts, the compiler's own default intermediate precision "
    "governs every multi-term expression. Section 0.6.8 names the compound VAT "
    "expression at [irs/irs030.cbl:L1562-L1563] as the one place a precision "
    "difference could change a stored penny, so a penny from a NON-TERMINATING "
    "quotient must be captured from the compiled oracle and never derived by "
    "reading the COBOL. Record the capture in ORACLE_CAPTURED_PENNIES below and "
    "in docs/migration/ambiguity-resolutions.md, then remove this marker."
)



class OracleCaptureUnavailable(AssertionError):
    """No compiled capture is recorded for the operands this test needs.

    An `AssertionError` rather than a skip on purpose: rule R-6 makes compiled
    behaviour the arbiter, so an uncaptured figure is an OPEN QUESTION that must stay
    visible in the report rather than being quietly stepped over.

    EVERY OPERAND PAIR THIS FILE ASSERTS IS NOW CAPTURED, so nothing
    raises this today and no `xfail` marks it. It stays because the guard is the reason
    a figure can never be GUESSED: add an assertion for new operands and it fails until
    someone measures them, which is the intended cost.
    """


# THE ORACLE CAPTURE TABLE - POPULATED FROM A COMPILED RUN.
#
# Every figure below was PRINTED BY GnuCOBOL 3.2.0, the compiler the maintainer targets
# [common/comp-common.sh:L9], from a program that reproduces the frozen statement and
# the frozen field declarations verbatim and nothing else:
#
#     01 post-amount     pic s9(7)v99 sign is leading.   [copybooks/irswspost.cob:L14]
#     01 vat-amount      pic s9(7)v99 sign is leading.   [copybooks/irswspost.cob:L18]
#     01 ws-vat-current  pic 99v99.                      [irs/irs030.cbl:L277]
#
#     compute vat-amount rounded =
#         post-amount - (post-amount / ((ws-vat-current + 100) / 100)).
#     subtract vat-amount from post-amount.
#
# compiled with `cobc -x -free`, no `-std=` dialect selection, no `>>SET ARITHMETIC`
# directive and no `binary-truncate` flag - the same defaults every ACAS compile line
# uses (Agent Action Plan section 0.5.2). The measured output, verbatim:
#
#     post=1000.00  rate=17.50  vat-amount = +0000148.94   post-amount= +0000851.06
#     post=-1000.00 rate=17.50  vat-amount = -0000148.94   post-amount= -0000851.06
#     post=117.55   rate=17.50  vat-amount = +0000017.51   post-amount= +0000100.04
#     post=0.01     rate=17.50  vat-amount = +0000000.00   post-amount= +0000000.01
#
# WHAT THE MEASUREMENT SETTLES (question Q-2, intermediate precision). 1000.00 / 1.175
# does not terminate, so the stored penny depends on how much precision the compiler
# carries through the intermediate quotient before the `ROUNDED` store. The two candidate
# answers differed:
#
#   * carrying EXTENDED precision, then rounding half-away-from-zero at scale 2, gives
#     1000 - 851.0638297... = 148.9361702... -> 148.94;
#   * reducing the quotient to the receiving field's own scale 2 FIRST, giving 851.06,
#     and only then subtracting, gives 148.94 as well - but the same reduction applied
#     to 117.55 gives 100.04 -> 17.51 one way and 17.08 the other.
#
# The 117.55 row is therefore the discriminating one, and it measures 17.51. So the
# compiler carries extended precision through the whole expression and rounds ONCE, at
# the store. That is what `acas_posting/cobol/arithmetic.py` implements.
#
# The NEGATIVE row is captured for its own reason: `ROUNDED` rounds half AWAY FROM ZERO,
# so the sign interacts with the rounding, and -148.94 rather than -148.93 is the
# measurement that pins the direction.
#
# The 0.01 row pins the sub-half-penny case: the VAT of one penny at 17.5% is 0.00, so
# the amount is left untouched and no penny is manufactured.
#
# The key is the capture identity - the statement, then its inputs - so that a captured
# figure can never be silently reused for different operands.
ORACLE_CAPTURED_PENNIES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "irs030:L1562-L1563:post=1000.00,rate=17.50": "148.94",
        "irs030:L1562-L1563:post=-1000.00,rate=17.50": "-148.94",
        #  THE DISCRIMINATING ROW, and the reason the table is not just the round
        #  thousand: 17.51 is what extended precision then one rounding gives, and
        #  17.08 is what reducing the quotient to scale 2 first would give.
        "irs030:L1562-L1563:post=117.55,rate=17.50": "17.51",
        #  The sub-half-penny row: no penny is manufactured.
        "irs030:L1562-L1563:post=0.01,rate=17.50": "0.00",
    }
)


def oracle_penny(capture_id: str) -> Decimal:
    """Return the oracle-captured figure for one statement-and-inputs identity.

    Args:
        capture_id: The capture identity, `<program>:<statement>:<operands>`.

    Returns:
        The captured figure, as an exact `decimal.Decimal`.

    Raises:
        OracleCaptureUnavailable: Nothing has been captured under that identity.
    """
    try:
        recorded = ORACLE_CAPTURED_PENNIES[capture_id]
    except KeyError as unrecorded:
        raise OracleCaptureUnavailable(
            f"no oracle capture is recorded for {capture_id!r}. "
            f"{Q_INTERMEDIATE_PRECISION}"
        ) from unrecorded
    # A string in the table and a Decimal out of it, so the recorded figure keeps
    # its scale exactly as the oracle printed it (rule R-2: never a binary carrier).
    return Decimal(recorded)


# ---------------------------------------------------------------------------
#  SECTION 2  -  DEFENSIVE DICTIONARY-KEY RESOLUTION
#
#  Every descriptor in this file is built from a generated data-dictionary entry
#  (rule R-5), never from a hand-written picture clause - and
#  `FieldDescriptor.for_working_storage` no longer exists, so
#  `from_dictionary_key` is the only factory. A key that a later dictionary
#  regeneration renames must therefore fail LEGIBLY, naming the near misses in the
#  same table, rather than as a bare KeyError three frames deep. Local to this
#  file, as the tier contract requires: no helper module, no nested conftest.
# ---------------------------------------------------------------------------


class DictionaryKeyNearMiss(KeyError):
    """A dictionary key did not resolve, with the near misses named.

    A `KeyError` subclass so that it is still the exception a caller of a mapping
    would catch, mirroring `loader.DictionaryKeyError`, from which it is always
    raised.
    """


def _normalised(name: str) -> str:
    """Reduce a field or column name to its comparable core.

    Case and separator differences are what a rename usually amounts to -
    `VAT-AMOUNT4` against `VAT_AMOUNT_4` - so both are stripped before comparing.
    """
    return "".join(character for character in name if character.isalnum()).casefold()


def _is_near(wanted: str, candidate: str) -> bool:
    """Whether two normalised names are near enough that one became the other.

    Containment either way, which catches the two renames that actually happen: a
    prefix or suffix gained, and a separator or digit moved.
    """
    if not wanted or not candidate:
        return False
    return wanted in candidate or candidate in wanted


def _near_misses(key: str) -> tuple[str, ...]:
    """Name the keys in the same table that a missing key most likely became.

    Args:
        key: The qualified key that failed to resolve.

    Returns:
        The near-miss keys, in dictionary order, or every key of that table when
            nothing looks near. Empty when the table itself is unknown.
    """
    table, _, column = key.partition(".")
    try:
        candidates = loader.entries_for_table(table)
    except loader.DictionaryError:
        # An unknown table: the loader's own message already lists the nearest
        # table names, so adding a guess here would only crowd it out.
        return ()
    wanted = _normalised(column)
    near = tuple(
        entry.key
        for entry in candidates
        if _is_near(wanted, _normalised(entry.key.partition(".")[2]))
    )
    return near or tuple(entry.key for entry in candidates)


def entry_for(key: str) -> model.DictionaryEntry:
    """Return the dictionary entry for one qualified key, or fail legibly.

    Args:
        key: A qualified entry key, `<TABLE-NAME>.<COLUMN-NAME>`.

    Returns:
        The entry the generated dictionary holds.

    Raises:
        DictionaryKeyNearMiss: No entry is keyed so.
    """
    try:
        return loader.get_entry(key)
    except loader.DictionaryKeyError as absent:
        raise DictionaryKeyNearMiss(
            f"{key!r} is not a key in the generated data dictionary. Nearest "
            f"keys in that table: {', '.join(_near_misses(key)) or '(none)'}. "
            "Regenerate with `python -m acas_posting.dictionary.generate` and "
            "update this test to the key the artifact actually carries; do not "
            "hand-write the picture clause instead (rule R-5)."
        ) from absent


def descriptor_for(key: str) -> cobol_field.FieldDescriptor:
    """Build the field descriptor for one qualified dictionary key.

    Args:
        key: A qualified entry key, `<TABLE-NAME>.<COLUMN-NAME>`.

    Returns:
        The descriptor: digits, scale, signedness, usage and sign position, all
            taken from the generated artifact.

    Raises:
        DictionaryKeyNearMiss: No entry is keyed so.
    """
    # Resolve the entry first, so a bad key reports the near misses rather than the
    # factory's own message.
    entry_for(key)
    return cobol_field.FieldDescriptor.from_dictionary_key(key)


# ---------------------------------------------------------------------------
#  SECTION 3  -  THE FIELDS THE TWO STATEMENTS TOUCH
#
#  Resolved at import time so that a renamed key fails at COLLECTION, loudly, and
#  cannot be mistaken for a behavioural difference in a later assertion.
# ---------------------------------------------------------------------------

# [irs/irs030.cbl:L1562-L1564] receivers. Both `pic s9(7)v99 sign is leading` -
# nine digits, seven of them before the point, a LEADING included sign.
IRS_POST_AMOUNT_KEY: Final[str] = "IRSPOSTING-REC.POST4-AMOUNT"
IRS_VAT_AMOUNT_KEY: Final[str] = "IRSPOSTING-REC.VAT-AMOUNT4"

# [general/gl051.cbl:L796-L797] receivers. Both `pic s9(8)v99` - ten digits, eight
# before the point, a TRAILING included sign.
GL_POST_AMOUNT_KEY: Final[str] = "GLPOSTING-REC.POST-AMOUNT"
GL_VAT_AMOUNT_KEY: Final[str] = "GLPOSTING-REC.VAT-AMOUNT"

# The rate. Neither program's rate item is itself a dictionary field: the IRS one is
# `WS-Vat-Current pic 99v99` in WORKING-STORAGE [irs/irs030.cbl:L277] and the GL one
# is `ws-vat-rate pic 99v99 comp` [general/gl051.cbl:L183]. Both are filled from the
# rate tables that ARE in the dictionary - the IRS one from `VAT-Psent (b)`
# [irs/irs030.cbl:L1472] by way of [irs/irs030.cbl:L721], the GL one from
# `vat-rate (v)` [general/gl051.cbl:L522] - so `SYSTEM-REC.VAT-RATE-n` is the
# descriptor source the Technical Specification names for the rate, and it is the
# only route available since `FieldDescriptor.for_working_storage` was removed.
# `99v99` in both places: four digits, two before the point, UNSIGNED. The COMP
# usage is inherited from the group header `05 Vat-Rates comp.`
# [copybooks/wssystem.cob:L55] and affects byte layout only, never the value.
VAT_RATE_KEYS: Final[tuple[str, ...]] = tuple(
    f"SYSTEM-REC.VAT-RATE-{ordinal}" for ordinal in range(1, 6)
)

IRS_POST_AMOUNT: Final[cobol_field.FieldDescriptor] = descriptor_for(
    IRS_POST_AMOUNT_KEY
)
IRS_VAT_AMOUNT: Final[cobol_field.FieldDescriptor] = descriptor_for(IRS_VAT_AMOUNT_KEY)
GL_POST_AMOUNT: Final[cobol_field.FieldDescriptor] = descriptor_for(GL_POST_AMOUNT_KEY)
GL_VAT_AMOUNT: Final[cobol_field.FieldDescriptor] = descriptor_for(GL_VAT_AMOUNT_KEY)
VAT_RATE: Final[cobol_field.FieldDescriptor] = descriptor_for(VAT_RATE_KEYS[0])


# ---------------------------------------------------------------------------
#  SECTION 4  -  THE STATEMENT UNDER TEST, SPELLED OUT
# ---------------------------------------------------------------------------

# The literal the COBOL statement writes twice, in two different roles: as an addend
# it lifts the percentage to a percentage-plus-par, and as a divisor it turns that
# into the multiplier the gross figure is divided by. `Decimal(100)` from an int, so
# the literal is exact and carries no scale of its own to interfere with the store.
ONE_HUNDRED: Final[Decimal] = Decimal(100)

# The scale both money receivers carry, as an exponent, for the "quantized once and
# to two places" assertions.
PENNY_EXPONENT: Final[int] = -2

# Standard UK VAT rates, as the frozen `pic 99v99` rate table would hold them. Used
# as INPUTS only; no expected value is derived from them by reasoning.
RATE_17_50: Final[Decimal] = Decimal("17.50")
RATE_20_00: Final[Decimal] = Decimal("20.00")
RATE_ZERO: Final[Decimal] = Decimal("0.00")


def gross_expression(post_amount: Decimal, rate: Decimal) -> Callable[[], Decimal]:
    """Return the L1562-L1563 expression as a zero-argument callable.

    A CALLABLE and not a value, deliberately: `arithmetic.compute` and
    `arithmetic.intermediate` evaluate a callable INSIDE
    `arithmetic.INTERMEDIATE_CONTEXT`, so the operators below run at 60 significant
    digits. Handing them an already-computed value would evaluate the operators in
    whatever context happened to be current, which is exactly the mistake
    `test_the_ambient_decimal_context_cannot_change_the_stored_figure` guards
    against.

    The three levels of nesting are written exactly as
    [irs/irs030.cbl:L1562-L1563] writes them, and as
    [general/gl051.cbl:L796] writes them on one line:

        post-amount - (post-amount / ( (rate + 100) / 100 ))

    Args:
        post_amount: The gross figure, `post-amount` before the statement.
        rate: The VAT percentage, `WS-Vat-Current` for IRS or `ws-vat-rate` for GL.

    Returns:
        A zero-argument callable yielding the unquantized result.
    """
    return lambda: post_amount - (
        post_amount / ((rate + ONE_HUNDRED) / ONE_HUNDRED)
    )


def gross_vat(
    post_amount: Decimal, rate: Decimal, receiving: cobol_field.FieldDescriptor
) -> Decimal:
    """Perform [irs/irs030.cbl:L1562-L1563] - the one ROUNDED store.

    `rounded=True` because the statement is written `compute vat-amount rounded`.
    This is one of the five ROUNDED sites in the whole migrated cycle.

    THE STORE IS MADE BY THE SHIPPED SECTION, NEVER BY AN EXPRESSION WRITTEN HERE,
    so this file cannot become a second source for [irs/irs030.cbl:L1562-L1563]. The
    driver selects `irs030_posting._gross_section` for the IRS receiving field or
    `gl051_batch_control_check._gross` for the General Ledger twin
    [general/gl051.cbl:L796] by the descriptor the caller names, so a store is never
    reported from a module that does not make it. `gross_expression` remains, and is
    called directly by the intermediate-precision assertions, whose subject is the
    EVALUATION ORDER rather than the store: those need the three nesting levels as
    separate callables, which a completed store cannot give them.

    Args:
        post_amount: The gross figure.
        rate: The VAT percentage.
        receiving: The `vat-amount` descriptor - the IRS one or the GL one.

    Returns:
        What `vat-amount` holds after the store.
    """
    stored = _shipped_gross_store(post_amount, rate, receiving)
    # A money receiver always yields a Decimal; the narrowing states that for a
    # reader and keeps the annotations honest without adding a branch that can run.
    assert isinstance(stored, Decimal)
    return stored


def _shipped_gross_store(
    post_amount: Decimal, rate: Decimal, receiving: cobol_field.FieldDescriptor
) -> Decimal:
    """Drive the shipped `Gross` section for one receiving field and return its store.

    Selected by the descriptor because the frozen system has TWO of these statements -
    IRS `Vat-Amount pic s9(7)v99` [copybooks/irswspost.cob:L18] and General Ledger
    `Vat-Amount pic s9(8)v99` [copybooks/wspost.cob:L28] - and reporting one module's
    store against the other's field would misattribute the divergence this file is
    about.

    Args:
        post_amount: The gross figure, before the statement.
        rate: The VAT percentage.
        receiving: Which `vat-amount` the caller means.

    Returns:
        What that field holds after the ROUNDED store.

    Raises:
        AssertionError: `receiving` is neither of the two the frozen system uses.
    """
    from acas_posting.programs import (  # noqa: PLC0415 - scoped; see the tier rule
        gl051_batch_control_check as gl051,
    )
    from acas_posting.programs import (  # noqa: PLC0415
        irs030_posting as irs030,
    )

    if receiving == irs030._VAT_AMOUNT:
        record = irs030.PostingRecord()
        record.post_amount = post_amount
        irs030._gross_section(record, rate)
        return record.vat_amount
    if receiving == gl051._VAT_AMOUNT:
        posting = gl051.WsPostingRecord()
        posting.post_amount = post_amount
        gl051._gross(posting, rate)
        return posting.vat_amount
    raise AssertionError(
        f"the frozen system writes this statement twice, into the IRS and the General "
        f"Ledger `vat-amount`; {receiving!r} is neither, and answering it from either "
        f"module would report a store into a field that module does not make."
    )


def net_of_vat(
    vat_amount: Decimal,
    post_amount: Decimal,
    receiving: cobol_field.FieldDescriptor,
    *,
    rounded: bool = False,
) -> Decimal:
    """Perform [irs/irs030.cbl:L1564] - `subtract vat-amount from post-amount`.

    DESTRUCTIVE: `post-amount` is both an operand and the receiver, so the gross
    figure is replaced by the net one in place. UN-`ROUNDED`, which is why
    `rounded` defaults to False.

    Args:
        vat_amount: The VAT figure the previous statement stored - the subtrahend.
        post_amount: What `post-amount` holds BEFORE this statement.
        receiving: The `post-amount` descriptor.
        rounded: Exposed ONLY so a test can show that flipping it is observable.
            The frozen statement writes no ROUNDED, so every reproduction of
            L1564 leaves it False.

    Returns:
        What `post-amount` holds after the store.
    """
    stored = arithmetic.subtract_from(
        vat_amount,
        receiver_value=post_amount,
        receiving=receiving,
        rounded=rounded,
    )
    assert isinstance(stored, Decimal)
    return stored


# ---------------------------------------------------------------------------
#  SECTION 5  -  THE THREE-LEVEL NESTED EXPRESSION
#               [irs/irs030.cbl:L1562-L1563]
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("post_amount", "rate"),
    [
        (Decimal("99.99"), RATE_20_00),
        (Decimal("1000.00"), RATE_17_50),
        (Decimal("1234.56"), RATE_17_50),
        (Decimal("7.77"), RATE_20_00),
    ],
)
def test_gross_is_one_compute_evaluated_then_stored_once(
    post_amount: Decimal, rate: Decimal
) -> None:
    """The two physical lines are ONE statement: evaluate, then store once.

    [irs/irs030.cbl:L1562-L1563] is a single `compute` whose text continues after
    the `=`; the line break is COBOL continuation and carries no semantics. The
    proof that the migration treats it as one statement is that
    `arithmetic.compute` is exactly `arithmetic.store` of
    `arithmetic.intermediate` - one evaluation at intermediate precision, then one
    quantize - with nothing quantized in between.
    """
    unquantized = arithmetic.intermediate(gross_expression(post_amount, rate))
    stored_in_two_steps = arithmetic.store(
        unquantized, IRS_VAT_AMOUNT, rounded=True
    )

    assert gross_vat(post_amount, rate, IRS_VAT_AMOUNT) == stored_in_two_steps


@pytest.mark.parametrize(
    ("post_amount", "rate"),
    [
        (Decimal("99.99"), RATE_20_00),
        (Decimal("1000.00"), RATE_17_50),
    ],
)
def test_gross_nests_three_levels_in_the_written_order(
    post_amount: Decimal, rate: Decimal
) -> None:
    """`post - (post / ((rate + 100) / 100))`, innermost level first.

    The nesting written at [irs/irs030.cbl:L1562-L1563] is reconstructed here one
    level at a time, at intermediate precision throughout, and the result must
    equal the one-shot expression. This is what makes the parenthesisation an
    asserted fact rather than a transcription that happens to look right: flattening
    the innermost level - dividing by `rate + 100` and forgetting the `/ 100`, or
    multiplying by `rate / 100` instead - fails here.
    """
    innermost = arithmetic.intermediate(lambda: (rate + ONE_HUNDRED) / ONE_HUNDRED)
    middle = arithmetic.intermediate(lambda: post_amount / innermost)
    outer = arithmetic.intermediate(lambda: post_amount - middle)

    assert arithmetic.intermediate(gross_expression(post_amount, rate)) == outer

    # And the level that is easiest to lose really is load-bearing: dividing by
    # `rate + 100` without the `/ 100` is a different number entirely.
    flattened = arithmetic.intermediate(
        lambda: post_amount - (post_amount / (rate + ONE_HUNDRED))
    )
    assert flattened != outer


def test_irs_receivers_match_the_frozen_copybook_declarations() -> None:
    """`post-amount` and `vat-amount` are `pic s9(7)v99 sign is leading`.

    [copybooks/irswspost.cob:L14] and [copybooks/irswspost.cob:L18]. The
    `vat-amount` locator is L18 - NOT L19, which some citations give - and the
    descriptor's own recorded locator is asserted so the file cannot drift from the
    checkout silently.

    Nine digits, seven before the implied point, scale two, a LEADING included sign
    and a nine-byte zoned DISPLAY layout: the sign is an overpunch on the first
    digit, so it costs no byte of its own.
    """
    for descriptor, locator in (
        (IRS_POST_AMOUNT, "copybooks/irswspost.cob:L14"),
        (IRS_VAT_AMOUNT, "copybooks/irswspost.cob:L18"),
    ):
        assert descriptor.picture == "s9(7)v99"
        assert descriptor.usage is model.Usage.DISPLAY
        assert descriptor.signed is True
        assert descriptor.sign_position is model.SignPosition.LEADING_INCLUDED
        # The copybook's spelling, preserved rather than normalised against the
        # other spelling the codebase uses [copybooks/wspost-irs.cob:L21].
        assert descriptor.sign_clause_text == "sign is leading"
        assert descriptor.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS
        assert descriptor.digits == 9
        assert descriptor.integer_digits == 7
        assert descriptor.scale == 2
        assert descriptor.byte_length == 9
        # The field's own quantum - metadata from the picture clause, not a figure.
        assert descriptor.quantum == Decimal("0.01")
        assert descriptor.python_storage is model.CobolPythonStorage.DECIMAL
        assert cobol_usage.is_zoned_display(descriptor.usage)
        assert cobol_usage.is_numeric(descriptor.usage)
        assert descriptor.source_locator == locator

    # Signed at nine digits, so the domain is symmetric about zero in units of a
    # penny. The `value_domain` is in UNITS, hence 999999999 rather than 9999999.99.
    assert cobol_usage.value_domain(
        IRS_VAT_AMOUNT.usage,
        digits=IRS_VAT_AMOUNT.digits,
        signed=IRS_VAT_AMOUNT.signed,
        unsigned=IRS_VAT_AMOUNT.unsigned,
    ) == (-999_999_999, 999_999_999)


def test_vat_rate_is_an_unsigned_two_place_percentage() -> None:
    """The rate is `pic 99v99`, unsigned, four digits, COMP by group inheritance.

    `Vat-Rate-1` through `Vat-Rate-5` sit under the group header
    `05  Vat-Rates  comp.` [copybooks/wssystem.cob:L55], so their COMP usage is
    INHERITED rather than written on the item, [copybooks/wssystem.cob:L56]. The
    rate items the two frozen statements actually name are working-storage copies of
    these - `WS-Vat-Current pic 99v99` [irs/irs030.cbl:L277] and
    `ws-vat-rate pic 99v99 comp` [general/gl051.cbl:L183] - with the same picture,
    so the numeric domain asserted here is theirs too.

    Two integer digits is the fact that matters to the statement under test: a rate
    of `17.50` fits, and `117.50` does not.
    """
    assert len(VAT_RATE_KEYS) == 5
    assert len(set(VAT_RATE_KEYS)) == 5

    for key in VAT_RATE_KEYS:
        rate_descriptor = descriptor_for(key)
        assert rate_descriptor.picture == "99v99"
        assert rate_descriptor.usage is model.Usage.COMP
        assert rate_descriptor.usage_declared_at is model.UsageDeclaredAt.GROUP
        assert rate_descriptor.usage_inherited_from == "Vat-Rates"
        assert rate_descriptor.digits == 4
        assert rate_descriptor.integer_digits == 2
        assert rate_descriptor.scale == 2
        # No `S` in the picture and no UNSIGNED keyword: unsigned by omission.
        assert rate_descriptor.signed is False
        assert rate_descriptor.sign_position is model.SignPosition.NONE

    assert entry_for(VAT_RATE_KEYS[0]).copybook.usage_group_source == (
        "copybooks/wssystem.cob:L55"
    )
    assert cobol_usage.value_domain(
        VAT_RATE.usage,
        digits=VAT_RATE.digits,
        signed=VAT_RATE.signed,
        unsigned=VAT_RATE.unsigned,
    ) == (0, 9999)


# ---------------------------------------------------------------------------
#  SECTION 6  -  QUANTIZE ONCE  (the central concern of this file)
#
#  Section 0.6.8: this expression is "the one place a precision difference could
#  change a stored penny".
# ---------------------------------------------------------------------------


def quantized_per_sub_expression(
    post_amount: Decimal, rate: Decimal, receiving: cobol_field.FieldDescriptor
) -> Decimal:
    """Evaluate the same expression the WRONG way - one store per level.

    The realistic mistake, not a straw man: an implementer transcribing the nesting
    level by level reaches for `arithmetic.store` at each level, because that is the
    function that "makes a value COBOL". Three stores instead of one, each aligning
    to the receiver's two places. COBOL quantizes when it STORES, and
    [irs/irs030.cbl:L1562-L1563] stores exactly once, at the end.

    Every operator below still runs inside `arithmetic.INTERMEDIATE_CONTEXT`, through
    `arithmetic.intermediate`, so the precision is identical to the correct
    evaluation and the ONLY difference between the two is how many times the value is
    quantized. That isolation is what makes the divergence attributable to the
    premature stores rather than to a difference in working precision.

    Args:
        post_amount: The gross figure.
        rate: The VAT percentage.
        receiving: The `vat-amount` descriptor whose scale each level is aligned to.

    Returns:
        What the receiver would hold under the mistaken evaluation.
    """
    divisor = arithmetic.store(
        arithmetic.intermediate(lambda: (rate + ONE_HUNDRED) / ONE_HUNDRED),
        receiving,
        rounded=True,
    )
    quotient = arithmetic.store(
        arithmetic.intermediate(lambda: post_amount / divisor),
        receiving,
        rounded=True,
    )
    stored = arithmetic.store(
        arithmetic.intermediate(lambda: post_amount - quotient),
        receiving,
        rounded=True,
    )
    assert isinstance(stored, Decimal)
    return stored


# The inputs below were CONSTRUCTED and then MEASURED on this interpreter until each
# one demonstrably shifted the stored penny; they are recorded here so that a later
# reader does not have to rediscover them, and so that a change of inputs is a
# visible edit rather than a silent weakening of the test.
#
#   rate 20.00, post 99.99   - the DIVISOR is exact at two places (120.00 / 100 =
#                              1.20), so early quantization of the divisor changes
#                              nothing and the whole shift is attributable to
#                              quantizing the INNER QUOTIENT: 99.99 / 1.20 = 83.325
#                              exactly, which rounds to 83.33 and leaves 16.66,
#                              where quantizing once leaves 16.665 -> 16.67. One
#                              penny, from one premature quantize.
#
#   rate 17.50, post 1000.00 - the DIVISOR is NOT representable at two places
#                              (117.50 / 100 = 1.175), so quantizing it first turns
#                              it into 1.18 and the error is large rather than
#                              marginal. This is the case that proves the innermost
#                              level must not be aligned to the receiver either.
#
# Rate 5.00 was tried and DOES NOT diverge for any of these amounts - 1.05 is exact
# at two places and its quotients happen to land clear of a half penny - so it is
# recorded here as unsuitable rather than left as a trap for the next editor.
DIVERGING_INPUTS: Final[tuple[tuple[Decimal, Decimal], ...]] = (
    (Decimal("99.99"), RATE_20_00),
    (Decimal("1000.00"), RATE_17_50),
    (Decimal("1234.56"), RATE_17_50),
    (Decimal("7.77"), RATE_20_00),
)


@pytest.mark.parametrize(("post_amount", "rate"), DIVERGING_INPUTS)
def test_per_sub_expression_quantization_shifts_the_stored_penny(
    post_amount: Decimal, rate: Decimal
) -> None:
    """Quantizing a sub-expression early changes the figure that reaches the table.

    The point of the whole intermediate-precision design, made observable:
    [irs/irs030.cbl:L1562-L1563] is ONE store, and evaluating it as three stores
    produces a DIFFERENT stored penny for every pair recorded in
    `DIVERGING_INPUTS`. A test that could not make early quantization diverge would
    have proved nothing at all.
    """
    quantized_once = gross_vat(post_amount, rate, IRS_VAT_AMOUNT)
    quantized_early = quantized_per_sub_expression(
        post_amount, rate, IRS_VAT_AMOUNT
    )

    assert quantized_once != quantized_early


def test_the_inner_quotient_alone_moves_the_penny_by_one() -> None:
    """Isolate the premature quantize to a single level, and to a single penny.

    With `rate = 20.00` the innermost level is exact at two places - `(20.00 + 100)
    / 100 = 1.20` - so quantizing THAT level changes nothing, and the divergence in
    `test_per_sub_expression_quantization_shifts_the_stored_penny` can only come
    from the middle level. Asserted here rather than argued in a comment.

    Every figure below is exact and TERMINATING, so no intermediate precision at or
    above five significant digits can alter it and question Q-2 does not reach it.
    """
    post_amount = Decimal("99.99")

    divisor = arithmetic.intermediate(
        lambda: (RATE_20_00 + ONE_HUNDRED) / ONE_HUNDRED
    )
    # oracle: not required - exact and terminating, so precision-independent.
    # spec: [irs/irs030.cbl:L1562-L1563] innermost level.
    assert divisor == Decimal("1.2")
    stored_divisor = arithmetic.store(divisor, IRS_VAT_AMOUNT, rounded=True)
    # Numerically untouched by the store, and carried at the receiver's scale.
    assert stored_divisor == divisor
    assert stored_divisor == Decimal("1.20")

    quotient = arithmetic.intermediate(lambda: post_amount / divisor)
    # 99.99 / 1.2 terminates at three places: an exact half penny.
    assert quotient == Decimal("83.325")

    quantized_once = gross_vat(post_amount, RATE_20_00, IRS_VAT_AMOUNT)
    # The middle level quantized, and nothing else: the same subtraction, the same
    # precision, one premature store.
    with_quotient_quantized_early = arithmetic.subtract_giving(
        arithmetic.store(quotient, IRS_VAT_AMOUNT, rounded=True),
        minuend=post_amount,
        receiving=IRS_VAT_AMOUNT,
        rounded=True,
    )

    # oracle: class (c) - the DIFFERENCE between two evaluations of the same inputs,
    # derived here rather than expected from the compiled program. One penny, and the
    # only thing that moved is where the quantize happened.
    assert arithmetic.intermediate(
        lambda: quantized_once - with_quotient_quantized_early
    ) == Decimal("0.01")


def test_intermediate_context_carries_at_least_sixty_digits() -> None:
    """The intermediate context is wide, and it is the only context in play.

    Rule R-2 requires exact decimal arithmetic; a compound expression with a
    repeating quotient needs room to be exact enough that the single quantize at the
    end is the only place a digit is lost. `arithmetic.INTERMEDIATE_CONTEXT` provides
    60 significant digits and traps the conditions that would otherwise pass a
    surprise through - notably `FloatOperation`, which turns a stray binary carrier
    into an exception rather than a rounding difference.
    """
    assert arithmetic.INTERMEDIATE_PRECISION == 60
    assert arithmetic.INTERMEDIATE_CONTEXT.prec >= 60
    assert arithmetic.INTERMEDIATE_CONTEXT.traps[decimal.FloatOperation] is True

    # The repeating case really does use that room: `1000.00 / 1.175` recurs, so the
    # unquantized intermediate carries the full precision rather than a few places.
    unquantized = arithmetic.intermediate(
        gross_expression(Decimal("1000.00"), RATE_17_50)
    )
    digits, exponent = (
        unquantized.as_tuple().digits,
        unquantized.as_tuple().exponent,
    )
    assert len(digits) >= 20
    assert isinstance(exponent, int)
    # Finer than a penny by a wide margin - nothing has been aligned to the
    # receiver's scale yet.
    assert exponent < PENNY_EXPONENT


@pytest.mark.parametrize(
    ("post_amount", "rate"),
    [
        (Decimal("99.99"), RATE_20_00),
        (Decimal("1000.00"), RATE_17_50),
        (Decimal("0.01"), RATE_20_00),
        (Decimal("-99.99"), RATE_20_00),
        (Decimal("123.45"), RATE_ZERO),
    ],
)
def test_the_stored_vat_amount_is_quantized_to_exactly_two_places(
    post_amount: Decimal, rate: Decimal
) -> None:
    """Whatever goes in, `vat-amount` comes out at scale two - once.

    `pic s9(7)v99` [copybooks/irswspost.cob:L18] has two digits after the implied
    point, so the stored exponent is -2 for every input, including a zero rate and a
    negative gross. A trailing-zero-stripping implementation would return
    `Decimal("0")` for the zero-rate case and fail here.
    """
    stored = gross_vat(post_amount, rate, IRS_VAT_AMOUNT)

    assert stored.as_tuple().exponent == PENNY_EXPONENT


def test_the_ambient_decimal_context_cannot_change_the_stored_figure() -> None:
    """Sabotage the process-wide context; the stored figure must not move.

    `arithmetic` enters its own `INTERMEDIATE_CONTEXT` with
    `decimal.localcontext` for every operation and never reads
    `decimal.getcontext()`. If it did, an unrelated module setting a narrow
    precision - or a test running earlier in the session - could change a posted
    figure, which would make the whole cycle non-deterministic and break rule R-6's
    determinism requirement.

    The ambient context is restored in a `finally`, so this test cannot leak its
    sabotage into any other test in the session.
    """
    baseline = {
        inputs: gross_vat(inputs[0], inputs[1], IRS_VAT_AMOUNT)
        for inputs in DIVERGING_INPUTS
    }

    saved = decimal.getcontext()
    try:
        # Four significant digits: far too few for any of these expressions, and
        # narrow enough that a single ambient operation would round visibly.
        decimal.setcontext(decimal.Context(prec=4))
        under_sabotage = {
            inputs: gross_vat(inputs[0], inputs[1], IRS_VAT_AMOUNT)
            for inputs in DIVERGING_INPUTS
        }
        # The sabotage is real: prove it by rounding in the ambient context, so a
        # future `setcontext` that silently failed cannot make this test vacuous.
        assert +Decimal("148.936170212765957") == Decimal("148.9")
    finally:
        decimal.setcontext(saved)

    assert under_sabotage == baseline
    assert decimal.getcontext() is saved


@pytest.mark.parametrize(
    ("post_amount", "rate", "capture_id"),
    [
        (
            Decimal("1000.00"),
            RATE_17_50,
            "irs030:L1562-L1563:post=1000.00,rate=17.50",
        ),
        (
            Decimal("-1000.00"),
            RATE_17_50,
            "irs030:L1562-L1563:post=-1000.00,rate=17.50",
        ),
    ],
)
def test_non_terminating_quotient_penny_matches_the_compiled_oracle(
    post_amount: Decimal, rate: Decimal, capture_id: str
) -> None:
    """The one figure this file refuses to derive by reading the COBOL - now MEASURED.

    `1000.00 / 1.175` does not terminate, so the stored penny is the value Agent Action
    Plan section 0.6.8 says an intermediate-precision difference could move, and rule
    R-6 makes the compiled program the arbiter of it. This test used to compare against
    an EMPTY `ORACLE_CAPTURED_PENNIES` and report the open question through
    `xfail(strict=True)` rather than assert a guess.

    THE CAPTURE HAS LANDED. See the commentary above
    `ORACLE_CAPTURED_PENNIES` for the probe program, the compiler and flags, and the
    verbatim output. The two figures asserted here - 148.94 and -148.94 - are what
    GnuCOBOL 3.2.0 printed, not what this file computed.

    The negative case is a separate capture for a separate reason: `ROUNDED` rounds half
    AWAY from zero, so the sign interacts with the rounding, and -148.94 rather than
    -148.93 is the measurement that pins the direction.

    THE RATCHET STILL OPERATES, in the other direction. `oracle_penny` raises
    `OracleCaptureUnavailable` for any identity not in the table, so a future parameter
    added here without a capture fails LOUDLY instead of silently asserting a derived
    figure.
    """
    # oracle: MEASURED on GnuCOBOL 3.2.0; see ORACLE_CAPTURED_PENNIES for
    # the probe and its verbatim output.  spec: [irs/irs030.cbl:L1562-L1564]
    expected = oracle_penny(capture_id)

    assert gross_vat(post_amount, rate, IRS_VAT_AMOUNT) == expected


# ---------------------------------------------------------------------------
#  SECTION 7  -  THE ROUNDED / UN-ROUNDED PAIR
#               [irs/irs030.cbl:L1562-L1563] then [irs/irs030.cbl:L1564]
# ---------------------------------------------------------------------------


def test_rounded_compute_and_unrounded_subtract_are_one_per_call_pair() -> None:
    """Both members of the pair, in sequence, in ONE test - because they conflict.

    [irs/irs030.cbl:L1562-L1563] is written `compute vat-amount rounded` and
    [irs/irs030.cbl:L1564] is written `subtract vat-amount from post-amount` with no
    ROUNDED. Two adjacent statements, opposite store directions. That is the whole
    argument for rounding being a per-call keyword argument rather than a mode, and
    this test makes it an asserted fact:

      1. `vat-amount` takes the HALF-AWAY-FROM-ZERO result;
      2. `post-amount` takes the TRUNCATED result of `post-amount - vat-amount`;
      3. flipping the ROUNDED flag on the first statement moves BOTH members, so a
         single module-wide direction cannot serve this pair and the cycle's other
         stores at the same time;
      4. the direction does not come from the decimal context either - the
         intermediate context truncates, yet member 1 rounds.

    The inputs are chosen so that every figure TERMINATES: `(20.00 + 100) / 100 =
    1.20` exactly and `99.99 / 1.20 = 83.325` exactly, an exact half penny. No
    intermediate precision at or above five significant digits can move any of it,
    so question Q-2 does not reach these figures and the only live question -
    which way an exact half goes - is already arbitrated.
    """
    post_amount = Decimal("99.99")

    # The same unquantized value reaches both directions, so the ONLY difference
    # between the two figures below is the store direction itself.
    unquantized = arithmetic.intermediate(
        gross_expression(post_amount, RATE_20_00)
    )
    # oracle: class (a) - 99.99 - 99.99/1.20 = 16.665 exactly, so this figure is
    # precision-independent.  spec: [irs/irs030.cbl:L1562-L1563]
    assert unquantized == Decimal("16.665")

    # MEMBER 1 - [irs/irs030.cbl:L1562-L1563], ROUNDED.
    # oracle: exact half penny, so precision-independent; the DIRECTION is settled by
    # the language and recorded at acas_posting/cobol/arithmetic.py ROUNDED_STORE -
    # COBOL ROUNDED is half AWAY FROM ZERO. Question Q-2's other half, the intermediate
    # PRECISION, is measured against GnuCOBOL 3.2.0 and cannot reach an exact half
    # penny in any case.
    # spec: [irs/irs030.cbl:L1562-L1563]
    vat_amount = gross_vat(post_amount, RATE_20_00, IRS_VAT_AMOUNT)
    assert vat_amount == Decimal("16.67")

    # MEMBER 2 - [irs/irs030.cbl:L1564], un-ROUNDED, destructive.
    # oracle: exact at two places - both operands are scale-two money items, so
    # their difference needs no rounding at all.
    # spec: [irs/irs030.cbl:L1564]
    net_amount = net_of_vat(vat_amount, post_amount, IRS_POST_AMOUNT)
    assert net_amount == Decimal("83.32")
    # Recovered through the module's own context rather than with a bare operator,
    # so that a narrowed ambient context elsewhere in the session cannot make this
    # assertion - or any other in this file - quietly inexact.
    assert arithmetic.intermediate(lambda: net_amount + vat_amount) == post_amount

    # 3. FLIPPING THE FIRST FLAG MOVES BOTH MEMBERS.
    # oracle: class (a) - the same exact 16.665, truncated toward zero instead of
    # rounded away from it.  spec: [irs/irs030.cbl:L1562-L1564], flags inverted.
    truncated_vat = arithmetic.store(unquantized, IRS_VAT_AMOUNT)
    assert truncated_vat == Decimal("16.66")
    assert net_of_vat(truncated_vat, post_amount, IRS_POST_AMOUNT) == Decimal(
        "83.33"
    )

    # A module-wide TRUNCATE mode would therefore store 16.66 where the frozen
    # program stores 16.67, and a module-wide ROUND mode would round the cycle's
    # every other store - the four hundred-odd un-ROUNDED ones - as well.
    assert truncated_vat != vat_amount

    # The un-ROUNDED direction of member 2 is live too, even though the frozen
    # statement cannot show it: its operands are both scale two, so their difference
    # is exact and the direction is invisible THERE. Feed the same verb a subtrahend
    # that carries sub-penny digits and the truncation appears.
    # oracle: class (a) - 99.99 - 16.665 = 83.325 exactly, truncated then rounded.
    # spec: [irs/irs030.cbl:L1564], with a subtrahend the frozen statement never
    # sees, so this pair is a property of the VERB and not of the frozen site.
    assert net_of_vat(unquantized, post_amount, IRS_POST_AMOUNT) == Decimal("83.32")
    assert net_of_vat(
        unquantized, post_amount, IRS_POST_AMOUNT, rounded=True
    ) == Decimal("83.33")

    # 4. THE DIRECTION IS NOT A CONTEXT SETTING. The intermediate context rounds
    # DOWN, yet member 1 rounded half up - so the direction travelled in the call,
    # not in the context.
    assert arithmetic.INTERMEDIATE_CONTEXT.rounding == decimal.ROUND_DOWN
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDING_DIRECTIONS[True] == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDING_DIRECTIONS[False] == decimal.ROUND_DOWN


def test_no_module_level_rounding_switch_exists() -> None:
    """There is no mode to set, and the two-member vocabulary cannot be edited.

    A guard against a future refactor rather than a statement about today's code: if
    someone introduces a settable rounding mode on `acas_posting.cobol.arithmetic`,
    this test fails and the reason is recorded right here. The names below are the
    plausible spellings such a switch would take.

    `ROUNDING_DIRECTIONS` is the one rounding-related mapping the module publishes,
    and it is a two-entry read-only view rather than a setting: it maps the COBOL
    keyword's presence to a `decimal` mode and is asserted immutable, so no caller
    can redirect every store in the cycle by assigning to it.
    """
    for plausible_switch in (
        "ROUNDING_MODE",
        "rounding_mode",
        "ROUNDING",
        "rounding",
        "ROUND_MODE",
        "DEFAULT_ROUNDING",
        "default_rounding",
        "set_rounding",
        "set_rounding_mode",
        "set_default_rounding",
        "use_rounding",
        "configure",
    ):
        assert not hasattr(arithmetic, plausible_switch), (
            f"acas_posting.cobol.arithmetic grew {plausible_switch!r}. Rounding "
            "must stay a per-call argument: [irs/irs030.cbl:L1562-L1563] needs "
            "half-away-from-zero and [irs/irs030.cbl:L1564], the very next "
            "statement, needs truncation, so no single mode can be correct."
        )

    assert isinstance(arithmetic.ROUNDING_DIRECTIONS, MappingProxyType)
    assert set(arithmetic.ROUNDING_DIRECTIONS) == {False, True}
    with pytest.raises(TypeError):
        arithmetic.ROUNDING_DIRECTIONS[True] = decimal.ROUND_DOWN  # type: ignore[index]


# ---------------------------------------------------------------------------
#  SECTION 8  -  THE DESTRUCTIVE SUBTRACT
#               [irs/irs030.cbl:L1564]
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("post_amount", "rate"),
    [
        (Decimal("99.99"), RATE_20_00),
        (Decimal("1000.00"), RATE_17_50),
        (Decimal("1234.56"), RATE_17_50),
        (Decimal("0.01"), RATE_20_00),
    ],
)
def test_l1564_subtract_reduces_post_amount_in_place(
    post_amount: Decimal, rate: Decimal
) -> None:
    """`post-amount` is both operand and receiver: gross becomes net in place.

    [irs/irs030.cbl:L1564] - and NOT L1565, which is a `*>` comment line, though the
    Technical Specification body cites it. The statement belongs to `Gross` alone:
    the `Net` section [irs/irs030.cbl:L1544-L1551] has no subtract at all, which is
    asserted by the sibling `test_irs_vat_from_net.py` rather than duplicated here.

    Two properties hold for every input, and both are structural rather than
    numeric, so no oracle figure is needed:

      * the receiver moves down by exactly the VAT and never up;
      * gross is recoverable as net plus VAT, because both operands are scale-two
        money items and their difference needs no rounding.

    The receiver is NOT asserted to move strictly, because for a one-penny gross it
    does not: `0.01` at 20 per cent yields a VAT of `0.001666...`, which the ROUNDED
    store takes to zero, and `post-amount` comes out unchanged.
    `test_a_sub_half_penny_vat_rounds_to_zero_and_leaves_post_amount_alone` records
    that case on its own. Asserting a strict decrease here would have been an
    invented rule of correct accounting rather than the observed behaviour, which
    rule R-4 forbids.
    """
    vat_amount = gross_vat(post_amount, rate, IRS_VAT_AMOUNT)
    net_amount = net_of_vat(vat_amount, post_amount, IRS_POST_AMOUNT)

    assert net_amount == arithmetic.intermediate(lambda: post_amount - vat_amount)
    assert net_amount.as_tuple().exponent == PENNY_EXPONENT
    # `arithmetic.compare` is the COBOL relation condition: algebraic, by value,
    # after aligning the decimal points - not a byte or digit-string comparison.
    assert arithmetic.compare(net_amount, post_amount) in (-1, 0)
    assert (
        arithmetic.compare(
            arithmetic.intermediate(lambda: net_amount + vat_amount), post_amount
        )
        == 0
    )


def test_l1564_is_applied_once_and_not_folded_into_the_compute() -> None:
    """The subtract is a separate statement, so it fires exactly once per posting.

    A reproduction that folded [irs/irs030.cbl:L1564] into the compute - returning
    the net figure directly from one expression - would leave `vat-amount` holding
    the wrong thing, and applying the subtract twice would post the VAT away twice
    over. Both mistakes are excluded here.
    """
    post_amount = Decimal("99.99")

    vat_amount = gross_vat(post_amount, RATE_20_00, IRS_VAT_AMOUNT)
    once = net_of_vat(vat_amount, post_amount, IRS_POST_AMOUNT)
    twice = net_of_vat(vat_amount, once, IRS_POST_AMOUNT)

    assert once != twice
    assert twice == arithmetic.intermediate(lambda: once - vat_amount)
    # The compute stores the VAT, not the net figure: the two differ, so a folded
    # implementation cannot pass by accident.
    assert vat_amount != once


def test_a_sub_half_penny_vat_rounds_to_zero_and_leaves_post_amount_alone() -> None:
    """A one-penny gross yields no VAT at all, and `post-amount` does not move.

    Recorded because it is the behaviour, not because it is desirable: at 20 per cent
    the VAT on `0.01` is `0.01 - 0.01/1.2 = 0.001666...`, which is below half a
    penny, so the ROUNDED store at [irs/irs030.cbl:L1562-L1563] takes it to zero and
    the un-ROUNDED subtract at [irs/irs030.cbl:L1564] subtracts nothing. The frozen
    program has no minimum-VAT rule and none is added here (rule R-3).

    The stored zero is not a precision judgement: the unquantized value is asserted
    to lie strictly between zero and half a penny, which is a distance of more than
    three times the boundary, so no intermediate precision can move it and question
    Q-2 does not reach it.
    """
    post_amount = Decimal("0.01")
    half_a_penny = Decimal("0.005")

    unquantized = arithmetic.intermediate(
        gross_expression(post_amount, RATE_20_00)
    )
    assert Decimal(0) < unquantized < half_a_penny

    # oracle: class (c) - the assertion above PROVES the stored zero from the
    # unquantized value's position rather than expecting a figure.
    # spec: [irs/irs030.cbl:L1562-L1563]
    vat_amount = gross_vat(post_amount, RATE_20_00, IRS_VAT_AMOUNT)
    assert vat_amount == Decimal("0.00")
    # Zero at scale two, not a bare zero: `pic s9(7)v99` always holds two places.
    assert vat_amount.as_tuple().exponent == PENNY_EXPONENT

    assert net_of_vat(vat_amount, post_amount, IRS_POST_AMOUNT) == post_amount


# ---------------------------------------------------------------------------
#  SECTION 9  -  THE GENERAL LEDGER MIRROR
#               [general/gl051.cbl:L796] then [general/gl051.cbl:L797]
# ---------------------------------------------------------------------------


def test_gl_receivers_are_ten_digit_trailing_sign_display_items() -> None:
    """`gl051`'s receivers are `pic s9(8)v99` - one integer digit wider than IRS.

    `gl051` copies `wspost.cob` at [general/gl051.cbl:L132], so the `vat-amount` and
    `post-amount` its `gross.` paragraph names are the GL posting record's:
    `post-amount` at [copybooks/wspost.cob:L23] and `vat-amount` at
    [copybooks/wspost.cob:L28]. (The Technical Specification names the two fields in
    the opposite order to the two locators; the checkout is as cited here.)

    Ten digits, eight before the point, and a TRAILING included sign rather than the
    IRS record's leading one - so the sign overpunches the LAST digit instead of the
    first. Ten bytes either way, since an included sign costs no byte of its own; the
    copybook's own running byte comment says 96 at that field
    [copybooks/wspost.cob:L28].
    """
    for descriptor, locator in (
        (GL_POST_AMOUNT, "copybooks/wspost.cob:L23"),
        (GL_VAT_AMOUNT, "copybooks/wspost.cob:L28"),
    ):
        assert descriptor.picture == "s9(8)v99"
        assert descriptor.usage is model.Usage.DISPLAY
        assert descriptor.signed is True
        assert descriptor.sign_position is model.SignPosition.TRAILING_INCLUDED
        # No sign clause is written: `pic s9(8)v99` alone, so the position is the
        # COBOL default and there is no clause text to preserve.
        assert descriptor.sign_clause_text is None
        assert descriptor.digits == 10
        assert descriptor.integer_digits == 8
        assert descriptor.scale == 2
        assert descriptor.byte_length == 10
        assert descriptor.source_locator == locator

    # One integer digit wider than the IRS pair, which is the whole point of
    # `test_irs_seven_integer_digits_overflow_where_gl_eight_do_not`.
    assert GL_POST_AMOUNT.integer_digits == IRS_POST_AMOUNT.integer_digits + 1
    assert GL_VAT_AMOUNT.digits == IRS_VAT_AMOUNT.digits + 1
    assert GL_VAT_AMOUNT.scale == IRS_VAT_AMOUNT.scale


@pytest.mark.parametrize(
    ("post_amount", "rate"),
    [
        (Decimal("99.99"), RATE_20_00),
        (Decimal("1000.00"), RATE_17_50),
        (Decimal("1234.56"), RATE_17_50),
        (Decimal("7.77"), RATE_20_00),
        (Decimal("123.45"), RATE_ZERO),
        (Decimal("-99.99"), RATE_20_00),
    ],
)
def test_gl_mirror_is_the_same_three_level_expression(
    post_amount: Decimal, rate: Decimal
) -> None:
    """One physical line in GL, two in IRS, and the same statement in both.

    [general/gl051.cbl:L796] writes the compute on a single physical line;
    [irs/irs030.cbl:L1562-L1563] breaks the same statement after the `=`. The
    difference is typographical, and the assertion here is that it is: for every
    amount that fits both receivers, the two reduce to the same expression and store
    the same figure.

    The rate items differ in name only - `ws-vat-rate` [general/gl051.cbl:L183]
    against `WS-Vat-Current` [irs/irs030.cbl:L277] - and share the `pic 99v99`
    picture, so one input serves both.
    """
    gl_vat = gross_vat(post_amount, rate, GL_VAT_AMOUNT)
    irs_vat = gross_vat(post_amount, rate, IRS_VAT_AMOUNT)
    assert gl_vat == irs_vat

    # And both are the SAME shared unquantized value put through the two stores, so
    # neither path can have smuggled a receiver-specific rounding into the expression
    # instead of into the store. This is what makes the equality above a statement
    # about one expression rather than a coincidence between two.
    unquantized = arithmetic.intermediate(gross_expression(post_amount, rate))
    assert arithmetic.store(unquantized, GL_VAT_AMOUNT, rounded=True) == gl_vat
    assert arithmetic.store(unquantized, IRS_VAT_AMOUNT, rounded=True) == irs_vat


def test_gl_pair_is_the_same_rounded_then_unrounded_pair() -> None:
    """[general/gl051.cbl:L796] rounds; [general/gl051.cbl:L797] truncates.

    The GL `gross.` paragraph carries the identical pair to the IRS `Gross` section:
    L796 is one of the cycle's five ROUNDED sites and L797 - `subtract vat-amount
    from post-amount` - is its un-ROUNDED successor, destructive in exactly the same
    way. `gl051`'s other ROUNDED site is its `net.` paragraph
    [general/gl051.cbl:L791], which has no subtract after it.
    """
    post_amount = Decimal("99.99")

    unquantized = arithmetic.intermediate(
        gross_expression(post_amount, RATE_20_00)
    )
    # oracle: exact half penny, precision-independent; direction arbitrated at
    # acas_posting/cobol/arithmetic.py ROUNDED_STORE.  spec: [general/gl051.cbl:L796]
    vat_amount = gross_vat(post_amount, RATE_20_00, GL_VAT_AMOUNT)
    assert vat_amount == Decimal("16.67")
    # oracle: class (a) again - the same exact 16.665, truncated as L797 would.
    assert arithmetic.store(unquantized, GL_VAT_AMOUNT) == Decimal("16.66")

    # spec: [general/gl051.cbl:L797]
    net_amount = net_of_vat(vat_amount, post_amount, GL_POST_AMOUNT)
    assert net_amount == Decimal("83.32")
    assert net_amount.as_tuple().exponent == PENNY_EXPONENT


# ---------------------------------------------------------------------------
#  SECTION 10  -  CAPACITY: SILENT MODULO, NO HANDLER
#
#  There are ZERO `ON SIZE ERROR` phrases and ZERO `REMAINDER` phrases across all
#  twelve in-scope programs, so there is NO overflow handler in the specification to
#  reproduce. A store past a field's capacity discards high-order DIGITS and keeps
#  the low-order ones; nothing is raised, nothing is clamped, nothing is warned.
#  That rule is the migrated store's own documented behaviour in
#  `acas_posting.cobol.usage`, and GnuCOBOL's default binary-size and
#  binary-truncate policy is recorded RESOLVED there as question Q-5.1 - so these
#  figures are not un-arbitrated and are asserted directly rather than deferred.
# ---------------------------------------------------------------------------


def test_irs_seven_integer_digits_overflow_where_gl_eight_do_not() -> None:
    """The same amount survives the GL receiver and is truncated by the IRS one.

    `12345678.99` needs eight integer digits. `pic s9(8)v99`
    [copybooks/wspost.cob:L23] has eight and stores it exactly; `pic s9(7)v99`
    [copybooks/irswspost.cob:L14] has seven and silently drops the leading `1`,
    keeping the low-order digits. No exception, no clamp, no warning - and the
    consequence is an accounting one, because the VAT computed from the truncated
    gross is a different figure from the VAT computed from the intact one.
    """
    gross_amount = Decimal("12345678.99")

    # The GL receiver has the room.
    assert arithmetic.store(gross_amount, GL_POST_AMOUNT) == gross_amount

    # The IRS receiver does not: high-order digits are discarded, modulo the
    # field's digit count, and the remaining digits are kept as they stand.
    # oracle: class (b) - a capacity fact, not an arithmetic result.
    # spec: [copybooks/irswspost.cob:L14] declares seven integer digits.
    truncated = arithmetic.store(gross_amount, IRS_POST_AMOUNT)
    assert truncated == Decimal("2345678.99")
    assert truncated.as_tuple().exponent == PENNY_EXPONENT
    # Stated as the rule rather than as a coincidence: units modulo ten to the
    # declared digit count.
    assert truncated == arithmetic.intermediate(
        lambda: gross_amount % (Decimal(10) ** IRS_POST_AMOUNT.integer_digits)
    )

    # The downstream effect. Both sides run the same statement; they disagree only
    # because the gross figure that reached the IRS record is not the one that
    # reached the GL record.
    assert gross_vat(truncated, RATE_20_00, IRS_VAT_AMOUNT) != gross_vat(
        gross_amount, RATE_20_00, GL_VAT_AMOUNT
    )


def test_overflow_preserves_the_sign_and_raises_nothing() -> None:
    """A negative amount past capacity keeps its sign along with its low digits.

    `pic s9(7)v99` [copybooks/irswspost.cob:L14] is signed, so the reduction acts on
    the magnitude and the sign of the truncated result is the sign of the value that
    was stored. Nothing is raised: the census finds no `ON SIZE ERROR` phrase in any
    in-scope program, so an exception here would be an invented behaviour.
    """
    # oracle: class (b) - the same capacity fact, with the sign of the value stored.
    # spec: [copybooks/irswspost.cob:L14]
    stored = arithmetic.store(Decimal("-12345678.99"), IRS_POST_AMOUNT)
    assert stored == Decimal("-2345678.99")
    assert stored < 0

    # And the same through the whole statement, so the capacity rule is not confined
    # to a bare store.
    over_capacity_vat = gross_vat(
        Decimal("-99999999.99"), RATE_20_00, IRS_VAT_AMOUNT
    )
    assert over_capacity_vat.as_tuple().exponent == PENNY_EXPONENT


def test_storing_a_negative_rate_into_the_unsigned_rate_item_drops_the_sign() -> None:
    """An unsigned receiver keeps the magnitude and discards the sign.

    `Vat-Rate-n pic 99v99` [copybooks/wssystem.cob:L56] has no `S`, so it is
    unsigned, and storing a negative value into it drops the sign rather than
    refusing it - the same silent reduction that discards high-order digits. Recorded
    here because the rate is an INPUT to the statement under test, so a caller that
    negated a rate would find the negation quietly gone rather than reported.

    Two integer digits, so `117.50` loses its leading `1` in exactly the same way.
    """
    # oracle: class (b) - a capacity and sign fact of an unsigned two-integer-digit
    # receiver.  spec: [copybooks/wssystem.cob:L56]
    assert arithmetic.store(Decimal("-17.50"), VAT_RATE) == Decimal("17.50")
    assert arithmetic.store(Decimal("117.50"), VAT_RATE) == Decimal("17.50")


# ---------------------------------------------------------------------------
#  SECTION 11  -  A ZERO RATE, AND A NEGATIVE GROSS
# ---------------------------------------------------------------------------


def test_a_zero_vat_rate_is_unguarded_and_arithmetically_benign() -> None:
    """No guard, and none needed on THIS path - which is an accident, not a design.

    The maintainer's own doubt sits over the `Net` computation, at
    [irs/irs030.cbl:L1547-L1548]: "Calculate vat from net - THIS MAY NEED A TEST FOR
    ONLY NON ZERO VAT RATES / before compute but look like comes to zero ?". No such
    test was ever added, on either path, and rule R-3 forbids adding one here.

    On the GROSS path a zero rate happens to be harmless: `(0 + 100) / 100` is
    exactly `1`, so `post-amount - post-amount / 1` is exactly zero and the
    subsequent subtract removes nothing. That is a property of the formula and NOT a
    guard: nothing tests the rate, nothing branches on it, and the divisor is never
    zero, so there is no divide-by-zero to guard against in the first place. A
    reproduction that added an `if rate == 0` short circuit would produce the same
    numbers today and a different program.
    """
    post_amount = Decimal("123.45")

    divisor = arithmetic.intermediate(lambda: (RATE_ZERO + ONE_HUNDRED) / ONE_HUNDRED)
    assert divisor == Decimal(1)

    # oracle: not required - the expression is exactly zero for any gross, at any
    # precision.  spec: [irs/irs030.cbl:L1562-L1563]
    vat_amount = gross_vat(post_amount, RATE_ZERO, IRS_VAT_AMOUNT)
    assert vat_amount == Decimal("0.00")
    assert vat_amount.as_tuple().exponent == PENNY_EXPONENT

    # spec: [irs/irs030.cbl:L1564] - the subtract still runs, and removes nothing.
    assert net_of_vat(vat_amount, post_amount, IRS_POST_AMOUNT) == post_amount

    # The GL mirror behaves identically at a zero rate, [general/gl051.cbl:L796-L797].
    # oracle: class (a) - exactly zero for any gross, at any precision.
    assert gross_vat(post_amount, RATE_ZERO, GL_VAT_AMOUNT) == Decimal("0.00")


@pytest.mark.parametrize(
    "receiving",
    [IRS_VAT_AMOUNT, GL_VAT_AMOUNT],
    ids=["irs-s9(7)v99", "gl-s9(8)v99"],
)
def test_a_negative_gross_rounds_away_from_zero(
    receiving: cobol_field.FieldDescriptor
) -> None:
    """COBOL ROUNDED is half AWAY FROM ZERO, so a negative half penny goes down.

    Both receivers are signed - `pic s9(7)v99 sign is leading`
    [copybooks/irswspost.cob:L18] and `pic s9(8)v99` [copybooks/wspost.cob:L28] - so
    a negative gross is representable and reaches the store with its sign. The
    inputs are the terminating pair again: `-99.99 / 1.20 = -83.325` exactly, so the
    intermediate is an exact half penny of the awkward sign and question Q-2 does not
    reach it. This is where half-away-from-zero and Python's built-in
    banker's-rounding part company: `ROUND_HALF_EVEN` would give `-16.66`.

    The non-terminating negative case is measured against the oracle by
    `test_the_non_terminating_quotient_penny_matches_the_compiled_oracle`.
    """
    post_amount = Decimal("-99.99")

    unquantized = arithmetic.intermediate(
        gross_expression(post_amount, RATE_20_00)
    )
    # oracle: class (a) - -99.99 - (-99.99/1.20) = -16.665 exactly.
    # spec: [irs/irs030.cbl:L1562-L1563]
    assert unquantized == Decimal("-16.665")

    # oracle: exact half penny, precision-independent; the DIRECTION is arbitrated at
    # acas_posting/cobol/arithmetic.py ROUNDED_STORE - half away from zero, measured
    # against GnuCOBOL 3.2.0.  spec: [irs/irs030.cbl:L1562-L1563]
    vat_amount = gross_vat(post_amount, RATE_20_00, receiving)
    assert vat_amount == Decimal("-16.67")

    # Away from zero, not toward it, and not to the even digit. The figure below is a
    # COUNTERFACTUAL, not an expectation: it is what Python's banker's rounding would
    # have stored, and it is asserted only to show that the two directions differ on
    # this value.
    assert vat_amount < unquantized
    # `Decimal.quantize` is a CONTEXT operation, and not merely in its rounding: it
    # raises `InvalidOperation` outright when the result would need more digits than
    # the ambient `prec` allows. A four-digit penny therefore cannot be formed at all
    # under a narrowed context, so the counterfactual is built inside the arithmetic
    # layer's own intermediate context - `INTERMEDIATE_CONTEXT`,
    # acas_posting/cobol/arithmetic.py INTERMEDIATE_CONTEXT - which is the same context every store in
    # the migrated cycle evaluates in. The explicit `rounding=` argument still governs
    # the direction, which is the property being contrasted (R-2).
    with decimal.localcontext(arithmetic.INTERMEDIATE_CONTEXT):
        bankers_rounded_penny = unquantized.quantize(
            Decimal("0.01"), rounding=decimal.ROUND_HALF_EVEN
        )
    assert bankers_rounded_penny == Decimal("-16.66")
    # Truncation, by contrast, moves TOWARD zero - which is what the un-ROUNDED
    # stores of the cycle do and what this site must not do.
    assert arithmetic.store(unquantized, receiving) == Decimal("-16.66")


def test_a_negative_gross_subtract_moves_post_amount_away_from_zero() -> None:
    """[irs/irs030.cbl:L1564] on a negative gross makes it more negative.

    `subtract vat-amount from post-amount` with both operands negative gives
    `-99.99 - (-16.67) = -83.32`, so the magnitude falls while the value rises. The
    statement is algebraic, not a magnitude operation, and there is no sign handling
    anywhere in the frozen section to reproduce.
    """
    post_amount = Decimal("-99.99")
    vat_amount = gross_vat(post_amount, RATE_20_00, IRS_VAT_AMOUNT)

    # oracle: class (a) - -99.99 - (-16.67) = -83.32 exactly, both operands at
    # scale two.  spec: [irs/irs030.cbl:L1564]
    net_amount = net_of_vat(vat_amount, post_amount, IRS_POST_AMOUNT)
    assert net_amount == Decimal("-83.32")
    assert arithmetic.compare(net_amount, post_amount) == 1
    assert arithmetic.intermediate(lambda: net_amount + vat_amount) == post_amount


# ---------------------------------------------------------------------------
#  SECTION 12  -  ANOMALY A-19  (rule R-4: reproduced or recorded, never fixed)
#
#  [irs/irs030.cbl:L1561], verbatim:
#
#       *>    compute  vat-amount rounded = post-amount - (post-amount / ( (vat + 100) / 100)).
#
#  A superseded, commented-out variant of the live compute, left in place beside it.
#  It is NOT implemented anywhere in this migration - a commented-out COBOL statement
#  has no behaviour to reproduce - and it must not be "restored" on the reasoning
#  that it is simpler. It names `vat`, which in this program is the FIRST IRS
#  parameter rate and nothing else, where the live statement names
#  `WS-Vat-Current`, the SELECTED rate. See the module docstring for the copy-and-
#  rename chain that establishes this.
#
#  The `Net` path carries its own superseded variant at [irs/irs030.cbl:L1550];
#  it is recorded by `test_irs_vat_from_net.py` and is not duplicated here.
# ---------------------------------------------------------------------------


def test_a19_superseded_variant_is_not_implemented() -> None:
    """The rate is SELECTED, so the superseded always-first-rate line is not benign.

    Reinstating [irs/irs030.cbl:L1561] would substitute the first rate for whichever
    rate the posting's VAT code chose, and this test proves that substitution is
    observable: the five rate slots are five distinct dictionary fields, and two
    different rates through the one statement give two different stored pennies. The
    anomaly is therefore recorded and LOCKED rather than merely commented, so a
    future "simplification" fails here.
    """
    post_amount = Decimal("1000.00")

    # Five distinct rate fields [copybooks/wssystem.cob:L56-L60], reachable as a
    # table through the OCCURS 5 redefinition [copybooks/wssystem.cob:L61] - which is
    # what makes `WS-Vat-Rate (WS-Vat-Number)` [irs/irs030.cbl:L721] a selection.
    assert len({entry_for(key).copybook.source for key in VAT_RATE_KEYS}) == 5

    # Three rates as INPUTS; no figure is expected from any of them, only that they
    # differ from one another - class (c), so the non-terminating 17.50 is safe here.
    at_standard_rate = gross_vat(post_amount, RATE_17_50, IRS_VAT_AMOUNT)
    at_reduced_rate = gross_vat(post_amount, Decimal("5.00"), IRS_VAT_AMOUNT)
    assert at_standard_rate != at_reduced_rate

    # The live statement takes the rate as an operand, so nothing in this file can
    # pin a rate silently: swapping the operand is the only way to change the rate,
    # and it changes the answer.
    assert gross_vat(post_amount, RATE_20_00, IRS_VAT_AMOUNT) not in (
        at_standard_rate,
        at_reduced_rate,
    )


# ---------------------------------------------------------------------------
#  SECTION 13  -  TRACEABILITY  (rule R-5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "copybook_locator", "sql_type"),
    [
        (IRS_POST_AMOUNT_KEY, "copybooks/irswspost.cob:L14", "decimal(9,2)"),
        (IRS_VAT_AMOUNT_KEY, "copybooks/irswspost.cob:L18", "decimal(9,2)"),
        (GL_POST_AMOUNT_KEY, "copybooks/wspost.cob:L23", "decimal(10,2)"),
        (GL_VAT_AMOUNT_KEY, "copybooks/wspost.cob:L28", "decimal(10,2)"),
    ],
)
def test_receiver_fields_are_signed_at_all_three_layers(
    key: str, copybook_locator: str, sql_type: str
) -> None:
    """Copybook, bridge host variable and column - the triple, and no sign drift.

    Rule R-5 requires every field to map to a data-dictionary entry, and the entry
    carries the authoritative triple: the copybook picture clause, the generated
    bridge's host variable, and the `CREATE TABLE` column. For these four money
    fields all three layers agree that the value is SIGNED and scaled to two places,
    so a negative VAT or a negative posting survives the write intact.

    That is worth asserting rather than assuming, because it is NOT universal in this
    codebase: the sales statistics fields are signed in the copybook and unsigned in
    both the host variable and the column, so their sign is lost at the bridge before
    any SQL runs - the anomaly recorded against
    [copybooks/wssl.cob:L46-L52] and [common/salesMT.cbl:L305-L312]. This path is
    clean, and if a dictionary regeneration ever makes it dirty, this test says so.
    """
    entry = entry_for(key)

    assert entry.copybook is not None
    assert entry.copybook.source == copybook_locator
    assert entry.copybook.signed is True
    assert entry.copybook.scale == 2

    assert entry.bridge_host_variable is not None
    assert entry.bridge_host_variable.signed is True
    assert entry.bridge_host_variable.scale == 2
    # The bridge holds the money fields as COMP host variables and loads them from
    # the record before every write, so a value that never reaches the host variable
    # would be written as the group's initialised zero rather than as SQL NULL.
    assert entry.bridge_host_variable.usage is model.Usage.COMP
    assert entry.bridge_host_variable.loaded_from_record is True

    assert entry.column is not None
    assert entry.column.sql_type == sql_type
    assert entry.column.base_type is model.SqlBaseType.DECIMAL
    assert entry.column.scale == 2
    assert entry.column.unsigned is False
    # Every column in the frozen schema is NOT NULL, which is why the bridge
    # initialises its host-variable group rather than omitting a field.
    assert entry.column.nullable is False

    # The descriptor a test or a record module builds from this key cites all three
    # layers, so a failure message names the frozen lines it disagrees with.
    citation = descriptor_for(key).cite()
    assert key in citation
    assert copybook_locator in citation


# ---------------------------------------------------------------------------
#  SECTION 13  -  THE SHIPPED `Gross` PARAGRAPH
#
#  Sections 1-12 pin the formula and the ROUNDED/un-ROUNDED pair against `gross_vat`
#  and `net_of_vat`, transcriptions written in this file. That establishes what
#  [irs/irs030.cbl:L1562-L1564] MEANS; it cannot establish that
#  `acas_posting/programs/irs030_posting.py::_gross_section` still does it. Deleting
#  L1564's counterpart from the shipped paragraph would leave every test above
#  green while every posting stored a gross figure where the net one belongs. This
#  section closes that gap.
#
#  WHY THE IMPORT IS DEFERRED (rule R-1). Agent Action Plan section 0.4.3 gives this
#  tier `cobol` and `records` and forbids `dal` and any database;
#  `acas_posting.programs.irs030_posting` imports `acas_posting.dal.facade`, which
#  pulls the MySQL driver in transitively. So the module is imported INSIDE the test
#  body, and the loader removes every tier-isolation-prefixed name it added from
#  `sys.modules` in a `finally`. It is NOT behind `pytest.importorskip`: a skip reads
#  as green, so a module that cannot be imported at all used to turn this section into
#  a pass, and the pinned driver is a hard `[project.dependencies]` entry and a hard
#  `requirements.txt` pin rather than an optional extra. Nor is it memoised - a cached
#  module is already resident, so the purge would remove nothing.
#  The three tier-isolation assertions this
#  suite carries - `test_comp3_packed_decimal.py test_the_packed_carrier_follows_the_scale_and_is_never_binary`,
#  `test_comp_binary.py test_q3_an_overflowing_negative_store_lands_on_its_magnitudes_byte`, `test_pic_field_descriptors.py test_no_single_winner_view_exists_on_drift_entry_or_descriptor` - therefore
#  keep passing UNCHANGED, and the tier still runs on a bare host. The pattern is
#  `tests/conftest.py _load_harness_module`'s, which loads the real harness modules while
#  keeping the forbidden name out of `sys.modules`.
#
#  NO DATABASE IS TOUCHED: `_gross_section(posting_record, ws_vat_current)` takes a
#  `PostingRecord` dataclass and a `Decimal`, opens no connection and needs no
#  MariaDB, no Docker and no GnuCOBOL.
#
#  NO NEW PENNY IS ASSERTED HERE. Rule R-6 and section 4.4 of this file's brief
#  forbid inventing a monetary constant, and 117.55 at 17.5 per cent has a
#  non-terminating quotient. So the shipped paragraph is compared against
#  `gross_vat` / `net_of_vat` - the audited path this file already pins - and against
#  structural relations that hold for every input. The one place a literal appears is
#  the sub-half-penny case, whose figures terminate.
# ---------------------------------------------------------------------------


#: The module-name prefixes the tier's own isolation assertions forbid.
TIER_ISOLATION_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
    "harness",
    "mysql",
    "numpy",
    "pandas",
    "sqlalchemy",
    "yaml",
)


IRS030_MODULE: Final[str] = "acas_posting.programs.irs030_posting"


def is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix the tier must not leave loaded?

    Matched as a package prefix - the exact name, or the name plus a dot - so a
    submodule cannot slip past and a merely similar name is not caught by accident.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def shipped_module(dotted_name: str) -> Iterator[types.ModuleType]:
    """Import a shipped module FOR REAL for one test, leaving `sys.modules` as found.

    THE IMPORT IS NOT OPTIONAL, AND IT IS NOT MEMOISED. Both of those are the point.

    NOT OPTIONAL. `pytest.importorskip` here would turn the one failure this section exists
    to catch into a PASS: a shipped module that cannot be imported at all - a syntax error,
    a circular import, a name it imports that no longer exists - would produce a SKIP, and
    a skipped test reads as green. The pinned MySQL driver the
    reason text blamed is a hard requirement of `requirements.txt`, so its absence is a
    broken environment and not a supported configuration; `importlib.import_module`
    lets the `ImportError` reach pytest as the FAILURE it is.

    NOT MEMOISED. A cached module is ALREADY RESIDENT in `sys.modules`, so the purge in
    the `finally` had nothing to remove and every "leaves no driver loaded" claim
    downstream was a statement about a module that had never left. Each entry therefore
    proves the import really happened: every tier-isolated name is EVICTED on the way in,
    so the module's top-level code re-executes and the purge on the way out has something
    real to remove, and the name is asserted RESIDENT while the body runs; on the way out
    every tier-isolated name the import added is removed and the residue is asserted
    empty.

    WHY EVICTION RATHER THAN A "MUST BE ABSENT" ASSERTION. Two remediations meet here
    and both are kept. One drives the SHIPPED sections from this file's own helpers -
    `gross_vat` and `net_of_vat` import `acas_posting.programs.irs030_posting` in
    function scope so the figures are production behaviour rather than a re-implementation
    - and the other refuses a vacuous isolation claim. An assertion that the name is
    absent on the way in would make the second forbid the first, because those helpers
    legitimately leave the module resident and dozens of earlier tests call them. Evicting
    first satisfies both: the import genuinely re-runs, the purge genuinely removes what
    it added, and no helper has to stop driving the shipped code to keep the claim true.

    A name that is NOT tier-isolated - `acas_posting.records.*`, `acas_posting.clock` -
    is imported and left alone. This tier is allowed `cobol` and `records` by Agent
    Action Plan section 0.4.3, so those are never purged and a freshness claim over
    them would be meaningless.

    Args:
        dotted_name: The importable name.

    Yields:
        The imported module.

    Raises:
        AssertionError: The name did not become resident after the eviction, or a
            tier-isolated name survived the purge.
        ImportError: The module could not be imported. NOT converted into a skip:
            `mysql-connector-python==26.7.0` is a HARD `[project.dependencies]`
            entry and a hard `requirements.txt` pin, so an installed package always has
            it, and the assertions this loader serves are anomaly locks rule R-4
            requires - a lock that can disappear into a skip line is not a lock.
    """
    #  EVICT FIRST, so the import below really runs the module's top-level code and the
    #  purge in the `finally` really removes what it added. Reverse-sorted so a package
    #  goes after its submodules, which is the order the sibling loader in
    #  `tests/arithmetic/test_compute_truncate_unrounded.py` uses.
    for resident in sorted(
        (name for name in sys.modules if is_tier_isolated_name(name)), reverse=True
    ):
        del sys.modules[resident]
    if is_tier_isolated_name(dotted_name):
        assert dotted_name not in sys.modules, (
            f"{dotted_name} survived the eviction above, so its top-level code will "
            f"NOT re-execute and the purge on the way out would remove nothing - which "
            f"is what the tier-isolation assertions in test_comp3_packed_decimal.py, "
            f"test_comp_binary.py and test_pic_field_descriptors.py rest on."
        )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(dotted_name)
        assert sys.modules.get(dotted_name) is module, (
            f"{dotted_name} did not become resident under its own name, so nothing "
            f"about a fresh import has been established."
        )
        yield module
        completed = True
    finally:
        added = set(sys.modules) - before
        for name in sorted(added, reverse=True):
            if is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name
            for name in set(sys.modules) - before
            if is_tier_isolated_name(name)
        )
        #  Only when the body itself succeeded, so a real failure is never masked by a
        #  second assertion about housekeeping.
        if completed:
            assert not residue, (
                f"importing {dotted_name} left {residue} resident after the purge, so "
                f"this tier no longer runs without a database driver and the three "
                f"isolation assertions above would fail depending only on file order."
            )


def stores_performed_by(function: object) -> tuple[tuple[str, str], ...]:
    """Every store the function's bytecode performs, its own and its lambdas'.

    Walks the function's code object and every code object nested inside it, and
    reports the attribute and closure stores in execution order. This is how "the
    paragraph stores the VAT and then the amount, in that order" becomes a property
    of the shipped code rather than of the inputs a test happened to pick.

    Args:
        function: A function object.

    Returns:
        A tuple of `(opname, target)` pairs, in bytecode order.
    """
    code = function.__code__  # type: ignore[attr-defined]

    def walk(target: types.CodeType) -> Iterator[types.CodeType]:
        yield target
        for constant in target.co_consts:
            if isinstance(constant, types.CodeType):
                yield from walk(constant)

    return tuple(
        (instruction.opname, str(instruction.argval))
        for block in walk(code)
        for instruction in dis.get_instructions(block)
        if instruction.opname in ("STORE_ATTR", "STORE_GLOBAL", "STORE_DEREF")
    )


#: Distinctive values for the eight `Posting-Record` fields
#: [copybooks/irswspost.cob:L8-L18] that `Gross` must not touch, at their frozen
#: widths - `pic xx`, `pic x(8)`, `pic x(32)` - so a store that re-padded one would
#: be caught.
SENTINEL_RECORD_FIELDS: Final[dict[str, object]] = {
    "post_key": 98765,
    "post_code": "PL",
    "post_date": "21/09/25",
    "post_dr": 22222,
    "post_cr": 33333,
    "post_legend": "sentinel legend, thirty-two wide ."[:32],
    "vat_ac_def": 32,
    "post_vat_side": "CR",
}

#: Gross figures with a strictly positive VAT, so the reduction at L1564 is
#: observable. The first three are the pairs section 8 already uses; the fourth is a
#: VAT-inclusive figure whose quotient does not terminate, which is the shape the
#: intermediate-precision question turns on.
SHIPPED_GROSS_CASES: Final[tuple[tuple[Decimal, Decimal], ...]] = (
    (Decimal("99.99"), RATE_20_00),
    (Decimal("1000.00"), RATE_17_50),
    (Decimal("1234.56"), RATE_17_50),
    (Decimal("117.55"), RATE_17_50),
)


def shipped_irs030() -> contextlib.AbstractContextManager[types.ModuleType]:
    """`acas_posting/programs/irs030_posting.py` - the module owning `Gross`."""
    return shipped_module(IRS030_MODULE)


def test_the_shipped_gross_paragraph_stores_the_vat_then_the_amount() -> None:
    """`_gross_section` performs EXACTLY TWO stores, in the written order.

        1562      compute  vat-amount rounded =
        1563          post-amount - (post-amount / ((WS-Vat-Current + 100) / 100)).
        1564      subtract vat-amount  from  post-amount.
        1566  Main-Exitb.

    L1562-L1563 stores `vat-amount`; L1564 stores `post-amount`. Two stores, in that
    sequence, and nothing after them but the exit paragraph.

    This is the structural lock, and it is what makes DELETING the subtract fail:
    the store census drops to one. A reproduction that folded L1564 into the compute
    would show one store too, and would additionally leave `vat-amount` holding the
    net figure rather than the VAT - which the behavioural test below rules out.
    Compare `Net`, which stores once and is pinned by
    `tests/arithmetic/test_irs_vat_from_net.py`.
    """
    with shipped_irs030() as irs030:
        assert stores_performed_by(irs030._gross_section) == (
            ("STORE_ATTR", "vat_amount"),
            ("STORE_ATTR", "post_amount"),
        )
        # The un-ROUNDED half of the pair is a `subtract_from`, per section 4.2 - a
        # separate verb from the ROUNDED `compute` above it, which is exactly why
        # rounding is per-call and can never be a module-level mode.
        reachable = {
            name
            for block in (
                irs030._gross_section.__code__,
                *(
                    constant
                    for constant in irs030._gross_section.__code__.co_consts
                    if isinstance(constant, types.CodeType)
                ),
            )
            for name in block.co_names
        }
        assert "compute" in reachable
        assert "subtract_from" in reachable

        # The receiving descriptors the module carries are the entries this file
        # mints from the generated dictionary, so both halves of the file compute
        # through the same field metadata (rule R-5).
        assert irs030._POST_AMOUNT == IRS_POST_AMOUNT
        assert irs030._VAT_AMOUNT == IRS_VAT_AMOUNT


@pytest.mark.parametrize(("post_amount", "rate"), SHIPPED_GROSS_CASES)
def test_the_shipped_gross_paragraph_reduces_post_amount_in_place(
    post_amount: Decimal, rate: Decimal
) -> None:
    """Drive the real `Gross` paragraph: gross becomes net, in place, once.

    [irs/irs030.cbl:L1564] - and not L1565, which is a `*>` line, though the
    specification body cites it. Four properties are asserted, none of them a new
    monetary constant:

      * `vat-amount` holds what the audited `gross_vat` path stores, so the ROUNDED
        compute is the one the file already pins;
      * `post-amount` holds what `net_of_vat` stores from that VAT, so the un-ROUNDED
        subtract is the one the file already pins;
      * the receiver moved strictly DOWN - every case here has a positive VAT, and
        the sub-half-penny case that does not move is asserted separately below;
      * the gross figure is recoverable as net plus VAT, so the amount was reduced
        exactly once rather than twice.

    The other eight fields of the record are asserted untouched, because `Gross`
    writes two money items and nothing else.
    """
    with shipped_irs030() as irs030:
        from acas_posting.records.irs_posting import PostingRecord

        record = PostingRecord(**SENTINEL_RECORD_FIELDS)  # type: ignore[arg-type]
        stored_gross = arithmetic.store(post_amount, IRS_POST_AMOUNT)
        assert isinstance(stored_gross, Decimal)
        record.post_amount = stored_gross
        current_rate = arithmetic.store(rate, VAT_RATE)
        assert isinstance(current_rate, Decimal)

        expected_vat = gross_vat(stored_gross, current_rate, IRS_VAT_AMOUNT)
        expected_net = net_of_vat(expected_vat, stored_gross, IRS_POST_AMOUNT)

        irs030._gross_section(record, current_rate)

        assert record.vat_amount == expected_vat
        assert record.post_amount == expected_net
        assert isinstance(record.post_amount, Decimal)
        assert record.post_amount.as_tuple().exponent == PENNY_EXPONENT

        # Strictly down, for these inputs.
        assert expected_vat > Decimal("0.00")
        assert arithmetic.compare(record.post_amount, stored_gross) == -1
        # Applied once: net + VAT is the gross figure again. Both operands are
        # scale-two money items, so their sum needs no rounding.
        assert (
            arithmetic.compare(
                arithmetic.intermediate(
                    lambda: record.post_amount + record.vat_amount
                ),
                stored_gross,
            )
            == 0
        )
        # And the compute stored the VAT, not the net figure, so a folded
        # implementation cannot pass by accident.
        assert record.vat_amount != record.post_amount

        for name, sentinel in SENTINEL_RECORD_FIELDS.items():
            assert getattr(record, name) == sentinel, name
        covered = {*SENTINEL_RECORD_FIELDS, "post_amount", "vat_amount"}
        assert {
            field.name for field in dataclasses.fields(record)
        } == covered, "a Posting-Record field is not covered by this assertion"


def test_the_shipped_gross_paragraph_leaves_a_sub_half_penny_amount_alone() -> None:
    """A one-penny gross at 20 per cent: no VAT, and the amount does not move.

    Recorded because it is the behaviour and not because it is desirable. The VAT on
    `0.01` is `0.01 - 0.01/1.2 = 0.001666...`, below half a penny, so the ROUNDED
    store at [irs/irs030.cbl:L1562-L1563] takes it to zero and [irs/irs030.cbl:L1564]
    subtracts nothing. These figures terminate, so the literals below need no oracle
    capture. No guard is added to make the amount move (rules R-3, R-4).

    AND THE SUBTRACT STILL RUNS. [irs/irs030.cbl:L1564] is unconditional - there is
    no `if vat-amount not = zero` above it - so the receiver is re-stored even when
    the subtrahend is zero. In Python that shows up as a NEW `Decimal` object with
    the same value, which is the observable difference from `Net`: `Net` never
    rebinds `post-amount` at all, and `tests/arithmetic/test_irs_vat_from_net.py`
    asserts object identity there for exactly that reason. Asserting `is not` here
    would fail if a well-meaning guard were ever added to skip a zero subtract.
    """
    with shipped_irs030() as irs030:
        from acas_posting.records.irs_posting import PostingRecord

        record = PostingRecord()
        penny = arithmetic.store(Decimal("0.01"), IRS_POST_AMOUNT)
        assert isinstance(penny, Decimal)
        record.post_amount = penny

        irs030._gross_section(record, RATE_20_00)

        assert record.vat_amount == Decimal("0.00")
        assert record.post_amount == Decimal("0.01")
        assert record.post_amount.as_tuple() == penny.as_tuple()
        # The store happened; only the value is unchanged.
        assert record.post_amount is not penny


def test_the_shipped_gross_paragraph_leaves_no_driver_loaded() -> None:
    """Rule R-1 holds even though this section reaches a program module.

    AND THE IMPORT REALLY HAPPENS, which is what makes the claim worth making. The
    loader MUST NOT memoise, or this guard would import nothing: the module would already
    be resident from an earlier test, the purge would remove nothing, and "leaves no driver
    loaded" would be a statement about a module that had never left. The loader does not
    cache, so each `with` below performs a genuine import - asserted INSIDE the block
    by reading live `sys.modules` - and the delta afterwards is a real measurement of
    what the purge removed.
    """
    before = frozenset(n for n in sys.modules if is_tier_isolated_name(n))

    assert IRS030_MODULE not in sys.modules, (
        f"{IRS030_MODULE} was resident BEFORE this guard imported it, so the import "
        f"below would be a no-op and the purge would remove nothing."
    )
    with shipped_irs030() as irs030:
        assert irs030.__name__ == IRS030_MODULE
        assert callable(irs030._gross_section)
        #  DURING: without this half, an import that silently did nothing would still
        #  satisfy the delta check below.
        assert sys.modules.get(IRS030_MODULE) is irs030
        assert any(
            is_tier_isolated_name(name) and name not in before
            for name in sys.modules
        ), (
            "importing the program added no tier-isolated name at all, so either it "
            "was already loaded or it does not reach the data-access layer."
        )
    assert IRS030_MODULE not in sys.modules, (
        "the program survived its loader's purge."
    )

    # Measured as the DELTA this guard's own action is responsible for, rather than
    # as absolute residency. The loader's contract - the one this docstring states -
    # is that it purges every tier-isolation-prefixed name IT added. Absolute
    # residency asserts something stronger that this tier does not own: another tier
    # in the same session legitimately loads the harness and its scenario parser
    # (Agent Action Plan section 0.4.3 puts PyYAML and harness/ on the harness side),
    # and that is not this loader leaking. The delta still fails loudly the moment
    # the loader leaves a name behind, in any run order.
    leaked = tuple(
        sorted(
            n
            for n in sys.modules
            if is_tier_isolated_name(n) and n not in before
        )
    )
    assert leaked == (), leaked
    # The prefix test recognises what it must and does not over-match.
    assert is_tier_isolated_name("acas_posting.dal") is True
    assert is_tier_isolated_name("acas_posting.programs.irs030_posting") is True
    assert is_tier_isolated_name("mysql.connector") is True
    assert is_tier_isolated_name("acas_posting.database") is False
    assert is_tier_isolated_name("acas_posting.records.irs_posting") is False


# ===========================================================================
#  THE CONFORMANCE LOCK - `net_of_vat` AGAINST THE SHIPPED SECTION'S SECOND STORE
#
#  WHY THIS IS A LOCK AND NOT A REDIRECTION. `gross_vat` above was redirected
#  outright: it takes the same inputs the shipped section takes, so it can simply call
#  it. `net_of_vat` cannot be, and the reason is a real difference rather than an
#  inconvenience - it takes an ALREADY-COMPUTED `vat_amount` as a parameter, which is
#  what lets thirteen assertions feed it values the statement above would never produce
#  (boundary pennies, sign combinations, an overflowing figure). The shipped section
#  computes its own VAT and would ignore any handed to it.
#
#  So the two are pinned together instead: for each case, the shipped `Gross` section
#  runs BOTH its stores, and `net_of_vat` is then handed the section's own VAT and
#  required to reach the same `post-amount`. If the section's subtraction ever changed -
#  operand order, receiving field, or a `ROUNDED` appearing where the frozen statement
#  has none - this fails, and the thirteen assertions above stop describing something
#  that is not there.
# ===========================================================================


@pytest.mark.parametrize(
    ("post_amount", "rate"),
    [
        pytest.param(Decimal("1200.00"), RATE_20_00, id="1200-at-20"),
        pytest.param(Decimal("1175.00"), Decimal("17.50"), id="1175-at-17.50"),
        pytest.param(Decimal("0.01"), RATE_20_00, id="one-penny"),
        pytest.param(Decimal("-1200.00"), RATE_20_00, id="negative-gross"),
        pytest.param(Decimal("1000.00"), Decimal("0.00"), id="zero-rate"),
    ],
)
def test_net_of_vat_agrees_with_the_shipped_sections_second_store(
    post_amount: Decimal, rate: Decimal
) -> None:
    """The shipped `Gross` section's two stores, and `net_of_vat`'s answer for them.

    [irs/irs030.cbl:L1562-L1565] verbatim, both statements:

        1562      compute  vat-amount rounded =
        1563               post-amount - (post-amount / ( (WS-Vat-Current + 100) / 100)).
        1564      subtract vat-amount  from  post-amount.

    TWO STORES, DIFFERENT ROUNDING. The compute is `ROUNDED` and the subtract is not,
    which is why `net_of_vat` defaults `rounded=False` - and why a `ROUNDED` appearing on
    the subtraction would be a defect this lock catches. The subtraction is also
    DESTRUCTIVE: `post-amount` is both an operand and the receiver.

    Args:
        post_amount: The gross figure before the statement.
        rate: `WS-Vat-Current`.
    """
    from acas_posting.programs import (  # noqa: PLC0415 - scoped; see the tier rule
        irs030_posting as irs030,
    )

    record = irs030.PostingRecord()
    record.post_amount = post_amount
    gross_before = record.post_amount

    irs030._gross_section(record, rate)

    #  The section's own VAT, fed back into this file's helper, which must then reach the
    #  same net figure the section left in `post-amount`.
    recomputed = net_of_vat(record.vat_amount, gross_before, irs030._POST_AMOUNT)
    assert recomputed == record.post_amount, (
        f"the shipped `Gross` section left post-amount = {record.post_amount} after "
        f"subtracting its own vat-amount = {record.vat_amount} from {gross_before}, and "
        f"`net_of_vat` reached {recomputed}. [irs/irs030.cbl:L1564] is an un-ROUNDED "
        f"SUBTRACT with post-amount as both operand and receiver; a disagreement means "
        f"the section's second store is no longer that statement."
    )

    #  AND THE VAT ITSELF, so the lock covers both stores rather than only the second.
    assert record.vat_amount == gross_vat(gross_before, rate, irs030._VAT_AMOUNT), (
        "the section's first store must be the same statement `gross_vat` drives; if "
        "these differ, one of the two entry points is reaching different code"
    )

    #  EXACTLY TWO STORES, in the frozen order: the VAT first, then the amount. A third
    #  store, or the pair reversed, would change what the posting record carries onward.
    stores = tuple(
        attribute
        for _, attribute in _stores_in(irs030._gross_section)
        if attribute in ("vat_amount", "post_amount")
    )
    assert stores == ("vat_amount", "post_amount"), (
        f"the shipped `Gross` section stores {stores}; [irs/irs030.cbl:L1562-L1564] "
        f"writes `vat-amount` and then `post-amount`, and the order is load-bearing "
        f"because the second statement reads what the first wrote"
    )


def _stores_in(function: object) -> tuple[tuple[str, str], ...]:
    """Every attribute store a function's bytecode performs, its own and its lambdas'.

    Walks the function's code object and every code object nested inside it - the
    `compute` lambda is one - and reports them in execution order, so a store hidden
    inside a lambda is not missed.

    Args:
        function: The function to inspect.

    Returns:
        `(opcode name, attribute name)` per store, in order.
    """
    import types  # noqa: PLC0415 - scoped, as everywhere in this tier

    def _walk(target: types.CodeType):
        yield target
        for constant in target.co_consts:
            if isinstance(constant, types.CodeType):
                yield from _walk(constant)

    import dis  # noqa: PLC0415

    found: list[tuple[str, str]] = []
    for code in _walk(function.__code__):
        for instruction in dis.get_instructions(code):
            if instruction.opname == "STORE_ATTR":
                found.append((instruction.opname, str(instruction.argval)))
    return tuple(found)
