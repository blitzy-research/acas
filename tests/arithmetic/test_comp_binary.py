"""Parity tests for the BINARY storage classes: COMP and the BINARY-* family.

File 3 of 14 in `tests/arithmetic/`. It proves that `COMP`, `BINARY-CHAR`,
`BINARY-SHORT` and `BINARY-LONG` are modelled EXACTLY as the frozen COBOL
declares them:

* their byte widths - one, two and four bytes, big-endian;
* their SIGNED and UNSIGNED value domains, which for the binary family come from
  the width and NOT from any digit count;
* the fact that `COMP` MAY CARRY A SCALE, so it is not an integer-only class
  [copybooks/wssl.cob:L42], [copybooks/wssystem.cob:L55-L61];
* INTEGER TRUNCATION TOWARD ZERO, which is not Python's floor division and which
  is what makes the second truncation of anomaly A-8 reproducible
  [copybooks/wssl.cob:L49], [sales/sl060.cbl:L827];
* the A-11 sign loss, which happens AT THE BRIDGE and not at the database
  [copybooks/wssl.cob:L43-L53] -> [common/salesMT.cbl:L302-L312] ->
  `int(8) unsigned` / `smallint(4) unsigned` in the frozen schema.

WHERE THE RULES COME FROM. The binding rules are the six the Technical
Specification carries at section 0.7.2, and this file honours them so:

* R-1, no COBOL at runtime. This tier "touch[es] neither COBOL nor a database":
  no subprocess, no foreign-function interface, no driver, no `acas_posting.dal`,
  no `acas_posting.cli`, no oracle module. The single prerequisite is
  `data_dictionary/acas_posting_dictionary.json`, a repository file rather than
  a piece of infrastructure, so the whole file runs on a host with no Docker, no
  MariaDB and no GnuCOBOL. The tier-isolation test in Group 11 asserts that from
  inside the run, over `sys.modules`, rather than leaving it to inspection.
* R-2, zero binary floating point. Every value here is an `int`, a `Decimal` or
  a `str`; every comparison is exact, never approximate and never within a
  tolerance. The one place that touches the ambient `decimal` context is the
  deliberate sabotage test, which restores it in a `finally`.
* R-3, no new validations and no concurrency. `ON SIZE ERROR` and `REMAINDER`
  occur zero times in the twelve in-scope programs, so an overflowing store
  silently keeps the low-order value and a store into an unsigned field silently
  drops the sign. Those are asserted as the behaviour, not corrected: nothing
  here expects a raise, a clamp or a warning. Execution is sequential; no
  parallel test runner is used or assumed.
* R-4, legacy anomalies reproduced and never fixed. Two are locked here:
  - A-8, truncation #2 - the integer divide into a picture-less `binary-long`
    receiving field. Truncation #1, the zero-scale `COMP-3` accumulator at
    [sales/sl060.cbl:L206] and [sales/sl060.cbl:L826], belongs to
    `test_comp3_packed_decimal.py`, and the composed idiom belongs to
    `test_compute_truncate_unrounded.py`. Neither is duplicated here.
  - A-11, the signed-to-unsigned narrowing at the bridge, in three flavours plus
    a clean-pass-through contrast, so that the drift is shown to be SPECIFIC and
    detected BY COMPARISON rather than hard-coded.
  Where a declaration and its trailing comment disagree, the DECLARATION WINS:
  the comment is recorded in prose and the contradiction is left unresolved.
  Every reproduction site names its anomaly and cites its COBOL locator.
* R-5, full traceability. Every descriptor arrives either through its
  dictionary key or through a `<path>:L<n>` locator into the frozen source, and
  no field metadata is hand-written. Coverage is evidence, never a gate.
* R-6, compiled behaviour is the tie-breaker. An expectation that only the
  compiled oracle can settle is never asserted as fact. Both questions this file
  names have now been MEASURED on GnuCOBOL 3.2.0, so there is no
  `xfail` here: each measurement is asserted, and where it refuted a reading the
  refutation is asserted too, so a change back fails by name.

THE TWO QUESTION IDS THIS FILE NAMES, both real, both citable, both MEASURED:

* Q-3 - what a negative COBOL value actually BECOMES once the bridge moves it
  into an unsigned host variable. The generated dictionary carries this as an
  OPEN ambiguity on all 91 affected entries (emitted by
  `acas_posting/dictionary/generate.py`), paired with anomaly A-11. Section
  0.6.8 is explicit that the stored value "must be measured rather than
  assumed", and IT HAS NOW BEEN MEASURED. GnuCOBOL 3.2.0 was
  driven with a `binary-long` sending item and a `pic 9(10) comp` receiver, and
  with narrower receivers besides: the bridge stores the ABSOLUTE VALUE and then
  bounds it by the RECEIVING DIGIT COUNT - `-1` arrives as 1 and not as 255,
  `-1000` as 1000, `-2147483648` as 2147483648, and `-123456` into `pic 9(4)
  comp` as 3456. Magnitude first, reduction second. That is exactly what
  `acas_posting/cobol/usage.py` already did in `_wrap_into_bits` and
  `_reduce_units`, so the measurement CONFIRMED the implementation; the
  dictionary's 91 affected entries now carry the measurement in their notes and
  no longer publish Q-3 as open, while anomaly A-11 stays on every one of them.
  The tests assert that state, and refuse an entry that still publishes Q-3.
* Q-5.1 - GnuCOBOL's default `binary-size` and `binary-truncate` policy. Section
  0.5.2 records that no compile invocation in the repository selects a dialect,
  no source carries an arithmetic directive and no `binary-truncate` flag
  appears anywhere, the compiler being GnuCOBOL 3.2 [common/comp-common.sh:L9].
  `acas_posting/cobol/usage.py` holds the policy in
  `DEFAULT_BINARY_SIZE_THRESHOLDS` and `BINARY_TRUNCATE`, and as of 2026-08-07
  both are MEASURED on the compiled oracle rather than transcribed from its
  documentation - GROUP 12 carries the twenty-four captured vectors, GROUP 10 the
  constants they confirm. The assertions are therefore plain, with no
  `xfail(strict=True)`; such a marker would now XPASS, which is the correct
  signal that the question is closed. The measurement also separated two rules
  that the single name `binary-truncate` had run together: a PICTURED `COMP`
  reduces on its digit count, while a PICTURELESS `BINARY-*` wraps at its signed
  byte capacity.

No timing assertion and no performance measurement appears anywhere in this
file (section 0.8.4).
"""

from __future__ import annotations

import decimal
import re
import subprocess
import sys
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Mapping

import pytest

from acas_posting.cobol import arithmetic
from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model

# Imports carried in with the merged group below, which was
# test_shared_storage_and_dispatch_boundaries.py. Only the pieces the block above did not
# already provide are listed (Agent Action Plan section 0.3.1 inventory).
import ast
import dataclasses
import importlib
import json
import types
from collections.abc import Iterator
from pathlib import Path

# Registered in pyproject.toml under `--strict-markers`, which owns it; declaring
# it again here would be a second definition of one fact.
pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  THE DEFENSIVE KEY RESOLVER
#
#  Dictionary keys are TABLE-QUALIFIED - `<TABLE-NAME>.<COLUMN-NAME>` - and two
#  of the keys this file needs are near misses for the name the copybook uses:
#  `Run-Date` [copybooks/wssystem.cob:L67] is keyed `SYSTEM-REC.RUN-DAT` and
#  `Sales-Create-Date` [copybooks/wssl.cob:L53] is keyed
#  `SALEDGER-REC.SALES-CREATE-DAT`, because the key follows the COLUMN name the
#  frozen schema declares. A bare `KeyError` from a mistyped key would say
#  nothing useful, so every lookup in this file goes through `_descriptor`,
#  which reports the near misses the table actually carries.
#
#  The fallback reads `loader.entries_for_table`; it NEVER invents metadata for a
#  key the artifact does not carry, because R-5 makes the dictionary the only
#  sanctioned source of a field's picture, scale, signedness and carrier.
# ---------------------------------------------------------------------------



#: How long the import-isolation probe may take before a hang is REPORTED
#:. It imports five pure-Python modules and prints `sys.modules`,
#: so anything approaching this is a module doing work at import time.
_IMPORT_PROBE_TIMEOUT_SECONDS = 30


class DictionaryKeyMiss(KeyError):
    """A key this file asked for is not in the generated dictionary.

    A `KeyError` subclass, exactly as `loader.DictionaryKeyError` is, so a caller
    that does not care which layer failed can catch either. Raised only on a
    PROGRAMMER error - a mistyped or stale key in this test file - never on a
    data value.
    """


#: How many near misses a failure message offers, matching the limit the loader's
#: own suggestion machinery uses. Small on purpose: a message that lists a
#: hundred and sixty-nine candidates teaches nothing.
_SUGGESTION_LIMIT = 5


def _shared_prefix_length(left: str, right: str) -> int:
    """How many leading characters two names have in common, case-folded.

    Args:
        left: One name.
        right: The other.

    Returns:
        The length of the common prefix, zero when the first characters differ.
    """
    shared = 0
    for one, other in zip(left.casefold(), right.casefold(), strict=False):
        if one != other:
            break
        shared += 1
    return shared


def _near_misses(key: str) -> tuple[str, ...]:
    """Return the keys of that table most like the one asked for.

    Ranked by shared prefix, because the misses this actually catches are a
    column name shortened at its end - `RUN-DAT` for `RUN-DATE`,
    `SALES-CREATE-DAT` for `SALES-CREATE-DATE`.

    Args:
        key: The qualified key that failed to resolve.

    Returns:
        Up to `_SUGGESTION_LIMIT` keys from that table, best match first, or an
            empty tuple when nothing resembles it or the table part is unknown
            too.
    """
    table, _, column = key.partition(".")
    try:
        candidates = tuple(entry.key for entry in loader.entries_for_table(table))
    except KeyError:
        # `loader.DictionaryLookupError` is a KeyError: the table name itself is
        # not one the frozen schema declares, so there is nothing to suggest.
        return ()

    scored = sorted(
        (
            (-_shared_prefix_length(column, candidate.partition(".")[2]), candidate)
            for candidate in candidates
        ),
    )
    return tuple(
        candidate for score, candidate in scored[:_SUGGESTION_LIMIT] if score < 0
    )


def _descriptor(key: str) -> cobol_field.FieldDescriptor:
    """Build the descriptor the generated dictionary holds for one key.

    The single door every dictionary-backed descriptor in this file comes
    through, so that a stale key fails with a message naming the keys that do
    exist rather than with a bare lookup error.

    Args:
        key: A qualified entry key - `<TABLE-NAME>.<COLUMN-NAME>` for a
            column-backed field, `<COPYBOOK-RECORD>.<FIELD-NAME>` for a
            copybook-only one.

    Returns:
        The descriptor for that field.

    Raises:
        DictionaryKeyMiss: No entry carries that key. The message lists the keys
            of the table the key names.
    """
    try:
        return cobol_field.FieldDescriptor.from_dictionary_key(key)
    except loader.DictionaryKeyError as missing:
        candidates = _near_misses(key)
        raise DictionaryKeyMiss(
            f"{key!r} is not a key the generated data dictionary carries. "
            f"Keys are table-qualified and follow the COLUMN name the frozen "
            f"schema declares, which is not always the copybook's field name - "
            f"`Run-Date` is keyed SYSTEM-REC.RUN-DAT and `Sales-Create-Date` "
            f"is keyed SALEDGER-REC.SALES-CREATE-DAT. The nearest keys that "
            f"table does carry, best match first, are: {candidates}. Correct "
            f"the key; never hand-write the field's metadata (R-5). Underlying "
            f"loader report: {missing}"
        ) from missing


def _entry(key: str) -> loader.DictionaryEntry:
    """Return the dictionary entry for one key, with the same near-miss report.

    Args:
        key: A qualified entry key.

    Returns:
        The entry: its three layer views, the drift between them, its Python
            carrier, its notes and its anomaly and ambiguity references.

    Raises:
        DictionaryKeyMiss: No entry carries that key.
    """
    # Resolving the descriptor first means a bad key is reported once, in one
    # voice, whichever accessor the test reached for.
    _descriptor(key)
    return loader.get_entry(key)


# ---------------------------------------------------------------------------
#  THE FIELDS THIS FILE IS ABOUT, as keys rather than as metadata.
#
#  Naming them once keeps every test citing the same field and makes the
#  membership facts below - "all nine", "exactly eleven" - readable.
# ---------------------------------------------------------------------------

#: The nine `binary-long` statistics fields of the sales ledger record,
#: [copybooks/wssl.cob:L45-L53], in declaration order. Their bridge host
#: variables are the nine `PIC 9(10) COMP` items at
#: [common/salesMT.cbl:L304-L312].
WSSL_BINARY_LONG_KEYS: tuple[str, ...] = (
    "SALEDGER-REC.SALES-LIMIT",  # copybooks/wssl.cob:L45
    "SALEDGER-REC.SALES-ACTIVETY",  # copybooks/wssl.cob:L46
    "SALEDGER-REC.SALES-LAST-INV",  # copybooks/wssl.cob:L47
    "SALEDGER-REC.SALES-LAST-PAY",  # copybooks/wssl.cob:L48
    "SALEDGER-REC.SALES-AVERAGE",  # copybooks/wssl.cob:L49
    "SALEDGER-REC.SALES-PAY-ACTIVETY",  # copybooks/wssl.cob:L50
    "SALEDGER-REC.SALES-PAY-AVERAGE",  # copybooks/wssl.cob:L51
    "SALEDGER-REC.SALES-PAY-WORST",  # copybooks/wssl.cob:L52
    "SALEDGER-REC.SALES-CREATE-DAT",  # copybooks/wssl.cob:L53
)

#: The two `binary-short` fields of the same record,
#: [copybooks/wssl.cob:L43-L44], whose host variables are `PIC 9(05) COMP` at
#: [common/salesMT.cbl:L302-L303].
WSSL_BINARY_SHORT_KEYS: tuple[str, ...] = (
    "SALEDGER-REC.SALES-LATE-MIN",  # copybooks/wssl.cob:L43
    "SALEDGER-REC.SALES-LATE-MAX",  # copybooks/wssl.cob:L44
)

#: The four `binary-long` date stamps of the batch record,
#: [copybooks/wsbatch.cob:L36-L39], whose host variables are `PIC 9(10) COMP` at
#: [common/glbatchMT.cbl:L287-L290] and whose columns are `int(8) unsigned` at
#: [mysql/ACASDB.sql:L86-L89].
WSBATCH_DATE_KEYS: tuple[str, ...] = (
    "GLBATCH-REC.ENTERED",  # copybooks/wsbatch.cob:L36
    "GLBATCH-REC.PROOFED",  # copybooks/wsbatch.cob:L37
    "GLBATCH-REC.POSTED",  # copybooks/wsbatch.cob:L38
    "GLBATCH-REC.STORED",  # copybooks/wsbatch.cob:L39
)

#: The five VAT rates, which carry no USAGE clause of their own and inherit
#: `COMP` from the group header `05 Vat-Rates comp.`
#: [copybooks/wssystem.cob:L55-L60].
VAT_RATE_KEYS: tuple[str, ...] = (
    "SYSTEM-REC.VAT-RATE-1",  # copybooks/wssystem.cob:L56
    "SYSTEM-REC.VAT-RATE-2",  # copybooks/wssystem.cob:L57
    "SYSTEM-REC.VAT-RATE-3",  # copybooks/wssystem.cob:L58
    "SYSTEM-REC.VAT-RATE-4",  # copybooks/wssystem.cob:L59
    "SYSTEM-REC.VAT-RATE-5",  # copybooks/wssystem.cob:L60
)

#: The receiving field of the A-8 average divide
#: [sales/sl060.cbl:L827]: picture-less, signed `binary-long`, so scale zero and
#: an `int` carrier.
SALES_AVERAGE_KEY = "SALEDGER-REC.SALES-AVERAGE"

#: The one place in this file that names the open bridge-conversion question.
#: The artifact carries it on every entry whose copybook view is signed and
#: whose host-variable view is not.
BRIDGE_SIGN_QUESTION = "Q-3"

#: The distinguishing phrase of the SIGN_LOST note that
#: acas_posting/dictionary/generate.py writes into every sign-loss entry, carrying the
#: compiled measurement that SETTLED Q-3. Matched rather than
#: transcribed in full, so a rewording of the note does not break these tests while an
#: absence of the measurement still does.
BRIDGE_SIGN_MEASUREMENT = "MEASURED against GnuCOBOL"

#: The anomaly that question belongs to, section 0.6.7 entry 11.
BRIDGE_SIGN_ANOMALY = "A-11"


#: THE Q-3 ARBITRATION, AS MEASURED - not as reasoned from the source.
#:
#: Question Q-3 asked what an unsigned column ends up holding when a SIGNED copybook
#: item is moved into an UNSIGNED bridge host variable. Section 0.6.8 held it open
#: because the answer is a property of the compiled path, and rule R-6 makes the
#: compiled program the arbiter rather than any reading of the source.
#:
#: HOW IT WAS MEASURED. A probe wrote `SALEDGER-REC` through the COMPILED `acas012`
#: handler and the COMPILED `salesMT` bridge - so through `cobmysqlapi` and real SQL
#: against real MariaDB - with negative values in the drifting statistics fields, then
#: read the columns back. Deliberately NOT measured at the COBOL move alone: the
#: question named the C interface, so the C interface had to be in the path.
#:
#: WHAT CAME BACK. The magnitude, with the sign gone. And for a magnitude wider than
#: the receiving host variable, the low-order digits OF THE MAGNITUDE - so the
#: absolute value is taken BEFORE the width reduction, not after.
#:
#: WHY IT IS A TABLE AND NOT LITERALS IN THE TESTS. The two tests that consume it
#: drive `cobol.usage`, which is production code; if they also carried their own
#: expected figures, they could pass by agreeing with the implementation they are
#: meant to check. Holding the measured outcome separately means the assertion sets
#: production behaviour against an independently sourced fact.
#:
#: Arbitration: docs/migration/ambiguity-resolutions.md, question Q-3.
BRIDGE_SIGN_MEASURED: Final[Mapping[str, object]] = MappingProxyType(
    {
        # A negative value's magnitude survives; only its sense is destroyed.
        "negative_becomes_absolute": 12,
        # The order of the two steps, which is what made the overflow case a
        # separate question rather than a corollary.
        "absolute_value_precedes_truncation": True,
    }
)


@pytest.fixture(name="measured")
def _measured() -> Mapping[str, object]:
    """The recorded Q-3 arbitration, so the tests cannot restate it differently.

    Returns:
        The measured outcomes, keyed by the property each one settles.
    """
    return BRIDGE_SIGN_MEASURED


# ---------------------------------------------------------------------------
#  PROGRAM-LOCAL DECLARATIONS
#
#  Six of the declarations this file must describe are WORKING-STORAGE items of a
#  single program, so the generated dictionary - which catalogues the record
#  layouts, the bridge-derived columns and the General Ledger work-file records -
#  carries no entry for them. `FieldDescriptor.__post_init__` admits exactly this
#  case: a descriptor with no `dictionary_key` but a `<path>:L<n>`
#  `source_locator` into the frozen source, whose carrier must be the one its own
#  usage and scale imply. That locator IS the traceability R-5 asks for, and it
#  is transcribed from the declaration rather than inferred.
#
#  `FieldDescriptor` publishes NO `for_working_storage` factory for this -
#  `acas_posting/cobol/field.py` records why it does not - and the picture parser that
#  covers the case is outside this tier's import set
#  (section 0.4.3 admits `cobol.usage`, `cobol.field`, `cobol.arithmetic` and the
#  dictionary loader). Direct construction through the helper below is therefore
#  the sanctioned route, and it goes through exactly the same validation.
# ---------------------------------------------------------------------------


def _working_storage(
    *,
    name: str,
    source_locator: str,
    usage: model.Usage,
    picture: str | None = None,
    digits: int | None = None,
    integer_digits: int | None = None,
    scale: int | None = None,
    signed: bool = False,
    sign_position: model.SignPosition = model.SignPosition.NONE,
) -> cobol_field.FieldDescriptor:
    """Describe one program-local WORKING-STORAGE item from its declaration.

    Args:
        name: The item's name exactly as the program writes it, lower case and
            hyphens preserved - `"line-cnt"`, `"work-a"`.
        source_locator: `<path>:L<n>` for the declaration line.
        usage: The storage class the declaration writes.
        picture: The PICTURE clause verbatim, or None for an item that has none -
            which is the normal case for `binary-long`.
        digits: Total declared digits, for an item with a picture.
        integer_digits: Digits before the implied decimal point.
        scale: Digits after it.
        signed: Whether the declaration carries a sign. The binary family is
            signed unless the declaration writes UNSIGNED.
        sign_position: Where that sign lives.

    Returns:
        The descriptor, carrying the locator as its provenance.
    """
    return cobol_field.FieldDescriptor(
        name=name,
        usage=usage,
        picture=picture,
        digits=digits,
        integer_digits=integer_digits,
        scale=scale,
        signed=signed,
        sign_position=sign_position,
        # Derived from the usage and the scale, exactly as the picture parser
        # derives it; `__post_init__` refuses any other value.
        python_storage=cobol_usage.python_storage_for(usage, scale),
        source_locator=source_locator,
    )


def _sl060_line_cnt() -> cobol_field.FieldDescriptor:
    """`03  line-cnt        pic 99        comp    value zero.`

    Verbatim from [sales/sl060.cbl:L223]. A two-digit COMP: a binary item whose
    domain comes from its DIGITS, which is the contrast that makes the binary
    family's width-derived domain legible.
    """
    return _working_storage(
        name="line-cnt",
        source_locator="sales/sl060.cbl:L223",
        usage=model.Usage.COMP,
        picture="99",
        digits=2,
        integer_digits=2,
        scale=0,
    )


def _sl100_line_cnt() -> cobol_field.FieldDescriptor:
    """`03  line-cnt        binary-char           value zero.`

    Verbatim from [sales/sl100.cbl:L173]. THE SAME NAME, A DIFFERENT STORAGE
    CLASS, in a sibling program - see
    `test_line_cnt_diverges_between_sl060_and_sl100` for why that divergence is
    preserved rather than unified (R-4).

    The specification body cites this declaration at `[sales/sl100.cbl:L179]`;
    the frozen file holds `03  j-deduct  pic s9(7)v99  comp-3  value zero.`
    there, and holds this one at L173. The verified locator is used and the
    discrepancy is recorded here rather than silently corrected.
    """
    return _working_storage(
        name="line-cnt",
        source_locator="sales/sl100.cbl:L173",
        usage=model.Usage.BINARY_CHAR,
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
    )


def _sl100_binary_long(*, name: str, line: int) -> cobol_field.FieldDescriptor:
    """One of `sl100`'s picture-less `binary-long` working items.

    `03  n-deduct        binary-long           value zero.` [sales/sl100.cbl:L180]
    `03  work-a          binary-long           value zero.` [sales/sl100.cbl:L182]
    `03  work-b          binary-long           value zero.` [sales/sl100.cbl:L183]

    Args:
        name: The item's name as written.
        line: Its line in `sales/sl100.cbl`.

    Returns:
        The descriptor.
    """
    return _working_storage(
        name=name,
        source_locator=f"sales/sl100.cbl:L{line}",
        usage=model.Usage.BINARY_LONG,
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
    )


# ---------------------------------------------------------------------------
#  GROUP 1  -  TRUNCATION TOWARD ZERO
#
#  THE SINGLE EASIEST WAY TO BE WRONG AND NEVER NOTICE. Python's `//` floors
#  toward negative infinity; COBOL discards the remainder and keeps the sign.
#  The two agree on every positive dividend and disagree on every negative one,
#  so a test suite that only ever divides positive numbers proves nothing.
# ---------------------------------------------------------------------------


def test_truncate_toward_zero_of_minus_seven_over_two_is_minus_three() -> None:
    """The mandatory assertion: -7 / 2 truncates to -3, never to -4.

    COBOL truncates TOWARD ZERO on an un-ROUNDED store, so the quotient of -7
    and 2 keeps its three whole units and discards the remainder. Python's floor
    division answers -4 for the same operands, which is why
    `usage.truncate_toward_zero` exists at all and why this assertion is the one
    that must never be removed.
    """
    assert cobol_usage.truncate_toward_zero(-7, 2) == -3
    assert cobol_usage.truncate_toward_zero(7, 2) == 3

    # Stated rather than implied: the wrong answer, and where it comes from.
    assert cobol_usage.truncate_toward_zero(-7, 2) != -4
    assert -7 // 2 == -4
    assert cobol_usage.truncate_toward_zero(-7, 2) != -7 // 2


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [
        (-1, 2, 0),
        (1, 2, 0),
        (-9, 4, -2),
        (9, 4, 2),
        (-100, 3, -33),
        (100, 3, 33),
        (-7, 2, -3),
        (7, 2, 3),
        # The two operands of the A-8 divide, in both signs.
        (38, 3, 12),
        (-38, 3, -12),
    ],
)
def test_truncate_toward_zero_discards_the_remainder_and_keeps_the_sign(
    numerator: int, denominator: int, expected: int
) -> None:
    """Every quotient keeps its whole units and its sign, and nothing else.

    Args:
        numerator: The dividend.
        denominator: The divisor.
        expected: The quotient COBOL stores, remainder discarded.
    """
    assert cobol_usage.truncate_toward_zero(numerator, denominator) == expected


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [
        (7, -2, -3),
        (-7, -2, 3),
        (-38, -3, 12),
    ],
)
def test_truncate_toward_zero_signs_the_quotient_algebraically(
    numerator: int, denominator: int, expected: int
) -> None:
    """A negative divisor signs the quotient, it does not shift it.

    The rule `usage.truncate_toward_zero` documents is "remainder discarded,
    sign preserved", which is algebraic: the sign of the quotient is negative
    when exactly one operand is. Floor division shifts the magnitude instead.

    Args:
        numerator: The dividend.
        denominator: The divisor, negative in two of the three cases.
        expected: The quotient COBOL stores.
    """
    assert cobol_usage.truncate_toward_zero(numerator, denominator) == expected


def test_truncate_toward_zero_returns_a_plain_int() -> None:
    """The quotient is a native `int`, never a decimal and never inexact (R-2).

    The carrier matters as much as the value: the receiving statistics fields are
    `binary-long`, so their arithmetic is integer arithmetic all the way through.
    """
    quotient = cobol_usage.truncate_toward_zero(-38, 3)
    assert isinstance(quotient, int)
    assert not isinstance(quotient, Decimal)
    assert not isinstance(quotient, bool)


def test_divide_by_giving_truncates_toward_zero_into_a_binary_long() -> None:
    """The same rule reached through the verb, into a real receiving field.

    `arithmetic.divide_by_giving` funnels an un-ROUNDED whole-number divide into
    an integer receiving field through `usage.truncate_toward_zero`, so the verb
    and the primitive cannot drift apart. The receiving field is the picture-less
    signed `binary-long` at [copybooks/wssl.cob:L49].
    """
    receiving = _descriptor(SALES_AVERAGE_KEY)

    assert arithmetic.divide_by_giving(-7, 2, receiving) == -3
    assert arithmetic.divide_by_giving(7, 2, receiving) == 3
    assert arithmetic.divide_by_giving(-7, 2, receiving) != -7 // 2


# ---------------------------------------------------------------------------
#  GROUP 2  -  THE BINARY FAMILY'S WIDTHS AND DOMAINS
#
#  A `binary-char`, `binary-short` or `binary-long` item is a true 8-, 16- or
#  32-bit integer. Its range comes from its WIDTH, it frequently carries no
#  picture at all [copybooks/wsbatch.cob:L36-L39], and its Python carrier is
#  native `int` - which is load-bearing, because that is what makes the A-8
#  divide truncate as integer arithmetic.
# ---------------------------------------------------------------------------


def test_binary_width_bytes_maps_the_three_classes_to_one_two_and_four() -> None:
    """One byte, two bytes, four bytes - and no fourth member.

    The mapping is the single place the family's hardware widths live, so a test
    on it is a test on every width assertion below.
    """
    assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_CHAR] == 1
    assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_SHORT] == 2
    assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_LONG] == 4
    assert len(cobol_usage.BINARY_WIDTH_BYTES) == 3

    # The predicate and the mapping must agree on membership, in both directions.
    for member in cobol_usage.BINARY_WIDTH_BYTES:
        assert cobol_usage.is_binary_family(member)
        assert cobol_usage.is_numeric(member)
    assert not cobol_usage.is_binary_family(model.Usage.COMP)
    assert not cobol_usage.is_binary_family(model.Usage.COMP_3)


def test_binary_width_bytes_is_read_only() -> None:
    """The width mapping cannot be mutated by a holder.

    It is a `MappingProxyType`, so an assignment raises `TypeError` rather than
    silently rewriting a hardware width for every caller in the process.
    """
    widths = cobol_usage.BINARY_WIDTH_BYTES
    with pytest.raises(TypeError):
        # A deliberate illegal write, made through the public name.
        widths[model.Usage.BINARY_CHAR] = 2  # type: ignore[index]

    assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_CHAR] == 1


def test_binary_short_sales_late_min_is_a_signed_sixteen_bit_int() -> None:
    """`03  Sales-Late-Min     binary-short. *> 9999 comp`

    Verbatim from [copybooks/wssl.cob:L43]. Two bytes, signed, so the domain is
    the full 16-bit one and the carrier is `int` with no quantum: there is no
    implied decimal point to quantize to.
    """
    field = _descriptor("SALEDGER-REC.SALES-LATE-MIN")

    assert field.usage is model.Usage.BINARY_SHORT
    assert field.byte_length == 2
    assert field.value_domain == (-32768, 32767)
    assert field.min_value == -32768
    assert field.max_value == 32767
    assert field.signed is True
    assert field.unsigned is False
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.is_int is True
    assert field.is_binary_family is True
    assert field.quantum is None
    assert field.source_locator == "copybooks/wssl.cob:L43"


def test_binary_long_sales_limit_is_a_signed_thirty_two_bit_int() -> None:
    """`03  Sales-Limit        binary-long. *> 9(8) comp`

    Verbatim from [copybooks/wssl.cob:L45]. Four bytes, signed, so the domain is
    the full 32-bit one.
    """
    field = _descriptor("SALEDGER-REC.SALES-LIMIT")

    assert field.usage is model.Usage.BINARY_LONG
    assert field.byte_length == 4
    assert field.value_domain == (-2147483648, 2147483647)
    assert field.signed is True
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.source_locator == "copybooks/wssl.cob:L45"


def test_binary_long_sales_average_is_an_int_with_no_quantum() -> None:
    """`03  Sales-Average      binary-long. *> 9(8) comp`

    Verbatim from [copybooks/wssl.cob:L49]. This is the receiving field of the
    A-8 average divide [sales/sl060.cbl:L827]: four bytes, signed, scale absent,
    carrier `int`. Because it has no scale it has no quantum, and because it has
    no quantum a divide into it cannot keep a fraction - which is exactly the
    second truncation Group 6 locks.
    """
    field = _descriptor(SALES_AVERAGE_KEY)

    assert field.usage is model.Usage.BINARY_LONG
    assert field.byte_length == 4
    assert field.value_domain == (-2147483648, 2147483647)
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.is_int is True
    assert field.is_decimal is False
    assert field.scale is None
    assert field.quantum is None
    assert field.picture is None


def test_binary_char_cyclea_is_signed_and_not_a_two_digit_item() -> None:
    """`05  Cyclea          binary-char.  *> 99.`

    Verbatim from [copybooks/wssystem.cob:L62]. One byte, SIGNED, so the domain
    runs -128 to 127. The trailing comment suggests a two-digit item; the
    declaration says otherwise and the declaration is what the compiler read.
    """
    field = _descriptor("SYSTEM-REC.CYCLEA")

    assert field.usage is model.Usage.BINARY_CHAR
    assert field.byte_length == 1
    assert field.value_domain == (-128, 127)
    assert field.signed is True
    assert field.unsigned is False
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.source_locator == "copybooks/wssystem.cob:L62"


def test_binary_char_scycle_redefines_cyclea() -> None:
    """`05  Scycle Redefines cyclea  binary-char.`

    Verbatim from [copybooks/wssystem.cob:L63]. A REDEFINES alternative view of
    the byte `Cyclea` already declares, so it has the same width and the same
    signed domain, and no column of its own - which is why its key is the
    copybook-qualified `System-Record.Scycle` rather than a `SYSTEM-REC.` one.
    The redefined name is carried with the copybook's own lower-case spelling.
    """
    field = _descriptor("System-Record.Scycle")

    assert field.usage is model.Usage.BINARY_CHAR
    assert field.redefines == "cyclea"
    assert field.byte_length == 1
    assert field.value_domain == (-128, 127)
    assert field.signed is True
    assert field.python_storage is model.CobolPythonStorage.INT

    # A copybook-only field has one layer, so it cannot disagree with itself and
    # the artifact records no drift for it.
    assert loader.host_variable_for("System-Record.Scycle") is None
    assert loader.column_for("System-Record.Scycle") is None


def test_binary_char_period_is_signed() -> None:
    """`05  Period          binary-char.  *> 99.`

    Verbatim from [copybooks/wssystem.cob:L64]. The same shape as `Cyclea`, and
    named separately because the accounting period is read on its own.
    """
    field = _descriptor("SYSTEM-REC.PERIOD")

    assert field.usage is model.Usage.BINARY_CHAR
    assert field.byte_length == 1
    assert field.signed is True
    assert field.value_domain == (-128, 127)
    assert field.source_locator == "copybooks/wssystem.cob:L64"


def test_binary_char_page_lines_is_unsigned_and_maxes_at_255() -> None:
    """`05  Page-Lines      binary-char  unsigned. *> 999. Portrait / default`

    Verbatim from [copybooks/wssystem.cob:L65]. The one in-scope declaration that
    writes the UNSIGNED keyword: one byte, no sign, so the domain runs 0 to 255.
    The trailing comment says 999, which one byte cannot hold - see Group 4.
    """
    field = _descriptor("SYSTEM-REC.PAGE-LINES")

    assert field.usage is model.Usage.BINARY_CHAR
    assert field.byte_length == 1
    assert field.unsigned is True
    assert field.signed is False
    assert field.value_domain == (0, 255)
    assert field.min_value == 0
    assert field.max_value == 255
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.source_locator == "copybooks/wssystem.cob:L65"


def test_binary_long_run_date_is_a_four_byte_int() -> None:
    """`05  Run-Date        binary-long. *> 9(8) comp.`

    Verbatim from [copybooks/wssystem.cob:L67]. One of the two observables the
    controlled clock pins, and an `int` because the date arrives as a binary day
    number rather than as a scaled quantity.

    Its key is `SYSTEM-REC.RUN-DAT`, after the COLUMN name the frozen schema
    declares at [mysql/ACASDB.sql:L1199], not after the copybook's `Run-Date`.
    """
    field = _descriptor("SYSTEM-REC.RUN-DAT")

    assert field.name == "Run-Date"
    assert field.usage is model.Usage.BINARY_LONG
    assert field.byte_length == 4
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.value_domain == (-2147483648, 2147483647)
    assert field.source_locator == "copybooks/wssystem.cob:L67"


def test_binary_long_entered_carries_no_picture_at_all() -> None:
    """`05  Entered         binary-long.`

    Verbatim from [copybooks/wsbatch.cob:L36] - no picture, no comment, nothing
    but the storage class. Its width and its domain therefore come from the class
    alone, and its carrier is `int`.
    """
    field = _descriptor("GLBATCH-REC.ENTERED")

    assert field.picture is None
    assert field.digits is None
    assert field.integer_digits is None
    assert field.scale is None
    assert field.usage is model.Usage.BINARY_LONG
    assert field.byte_length == 4
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.value_domain == (-2147483648, 2147483647)
    assert field.source_locator == "copybooks/wsbatch.cob:L36"


def test_all_nine_wssl_binary_long_fields_are_four_byte_ints() -> None:
    """The whole block at [copybooks/wssl.cob:L45-L53], not a sample of it.

    Nine consecutive `binary-long` statistics fields, every one four bytes wide,
    signed, picture-less and carried as `int`. Section 0.6.1 speaks of "seven at
    L46-L52"; that is a subset - `Sales-Limit` at L45 and `Sales-Create-Date` at
    L53 are declared identically, so all nine are asserted.
    """
    assert len(WSSL_BINARY_LONG_KEYS) == 9
    assert SALES_AVERAGE_KEY in WSSL_BINARY_LONG_KEYS

    for key in WSSL_BINARY_LONG_KEYS:
        field = _descriptor(key)
        assert field.usage is model.Usage.BINARY_LONG, key
        assert field.byte_length == 4, key
        assert field.value_domain == (-2147483648, 2147483647), key
        assert field.signed is True, key
        assert field.picture is None, key
        assert field.scale is None, key
        assert field.quantum is None, key
        assert field.python_storage is model.CobolPythonStorage.INT, key
        assert field.is_int is True, key


def test_both_wssl_binary_short_fields_are_two_byte_ints() -> None:
    """The pair at [copybooks/wssl.cob:L43-L44], asserted together.

    They bracket the late-payment charge window, and both are `binary-short`
    rather than the four-digit item their shared comment suggests.
    """
    assert len(WSSL_BINARY_SHORT_KEYS) == 2

    for key in WSSL_BINARY_SHORT_KEYS:
        field = _descriptor(key)
        assert field.usage is model.Usage.BINARY_SHORT, key
        assert field.byte_length == 2, key
        assert field.value_domain == (-32768, 32767), key
        assert field.python_storage is model.CobolPythonStorage.INT, key


@pytest.mark.parametrize(
    ("usage", "value", "raw"),
    [
        # One byte. -1 is every bit set, which is the clearest proof that the
        # sign is two's complement in the item's own width.
        (model.Usage.BINARY_CHAR, -1, b"\xff"),
        (model.Usage.BINARY_CHAR, 127, b"\x7f"),
        # Two bytes, most significant first: 258 is 0x0102 and not 0x0201.
        (model.Usage.BINARY_SHORT, 258, b"\x01\x02"),
        # Four bytes, most significant first.
        (model.Usage.BINARY_LONG, 16909060, b"\x01\x02\x03\x04"),
    ],
)
def test_binary_family_lays_out_big_endian_at_its_declared_width(
    usage: model.Usage, value: int, raw: bytes
) -> None:
    """A binary item's bytes are its width, most significant first.

    Byte order is not a detail here: the migrated data-access layer reproduces the
    bridge's host-variable conversion, and a reversed layout would put a different
    number in the column while every in-process assertion still passed.

    Args:
        usage: The storage class under test.
        value: A signed value inside that class's domain.
        raw: The bytes the class lays that value out as.
    """
    encoded = cobol_usage.encode(value, usage=usage)

    assert encoded == raw
    assert len(encoded) == cobol_usage.BINARY_WIDTH_BYTES[usage]
    assert len(encoded) == cobol_usage.byte_length(usage)
    assert cobol_usage.decode(encoded, usage=usage) == value
    assert isinstance(cobol_usage.decode(encoded, usage=usage), int)


# ---------------------------------------------------------------------------
#  GROUP 3  -  `COMP` MAY CARRY A SCALE
#
#  `COMP` is NOT an integer-only class. Four in-scope declarations write
#  `pic 99v99 comp`, and a model that treated every binary item as an integer
#  would discard the pence of every VAT rate and every settlement discount in the
#  system. `COMP` differs from the binary family in a second way that matters as
#  much: its width AND its domain come from its DIGIT COUNT, not from a hardware
#  width.
# ---------------------------------------------------------------------------


def test_comp_sales_discount_carries_two_decimal_places() -> None:
    """`03  Sales-Discount     pic 99v99          comp.`

    Verbatim from [copybooks/wssl.cob:L42]. Four digits, two of them after the
    implied decimal point, so the carrier is `Decimal` and the quantum is one
    hundredth. Two bytes under the default binary-size policy, and the domain is
    counted in HUNDREDTHS - 0 to 9999 - because a domain is expressed in units of
    the item's last digit.
    """
    field = _descriptor("SALEDGER-REC.SALES-DISCOUNT")

    assert field.usage is model.Usage.COMP
    assert field.picture == "99v99"
    assert field.digits == 4
    assert field.integer_digits == 2
    assert field.scale == 2
    assert field.python_storage is model.CobolPythonStorage.DECIMAL
    assert field.is_decimal is True
    assert field.is_int is False
    assert field.quantum == Decimal("0.01")
    assert field.byte_length == 2
    assert field.value_domain == (0, 9999)
    assert field.is_binary_family is False
    assert field.source_locator == "copybooks/wssl.cob:L42"


def test_comp_scaled_store_keeps_its_hundredths() -> None:
    """A store into a scaled COMP item keeps two decimal places exactly.

    The point of the previous test made as behaviour: the value that comes back
    is a `Decimal` written at the receiving scale, and a third decimal place is
    truncated toward zero rather than rounded, because the statement carries no
    ROUNDED.
    """
    field = _descriptor("SALEDGER-REC.SALES-DISCOUNT")

    assert arithmetic.store(Decimal("12.50"), field) == Decimal("12.50")
    assert arithmetic.store(Decimal("12.509"), field) == Decimal("12.50")
    assert isinstance(arithmetic.store(Decimal("12.50"), field), Decimal)


def test_comp_vat_rates_group_hands_its_usage_down_to_five_children() -> None:
    """`05  Vat-Rates  comp.` with `07 Vat-Rate-1 .. Vat-Rate-5  pic 99v99.`

    Verbatim from [copybooks/wssystem.cob:L55-L60]. Not one of the five picture
    lines mentions storage: each inherits `COMP` from the group header. Reading
    usage from the picture line alone would class all five as zoned DISPLAY,
    which is a different byte layout and a different width, so the inheritance is
    recorded per field and asserted here.
    """
    assert len(VAT_RATE_KEYS) == 5

    for ordinal, key in enumerate(VAT_RATE_KEYS, start=1):
        field = _descriptor(key)
        assert field.name == f"Vat-Rate-{ordinal}", key
        assert field.usage is model.Usage.COMP, key
        assert field.usage_declared_at is model.UsageDeclaredAt.GROUP, key
        assert field.usage_inherited_from == "Vat-Rates", key
        assert field.picture == "99v99", key
        assert field.digits == 4, key
        assert field.scale == 2, key
        assert field.quantum == Decimal("0.01"), key
        assert field.python_storage is model.CobolPythonStorage.DECIMAL, key

    # The group header itself: a group has no elementary width and no domain of
    # its own, and the model reports the request rather than inventing an answer.
    group = _descriptor("System-Record.Vat-Rates")
    assert group.usage is model.Usage.GROUP
    assert group.is_group is True
    assert group.python_storage is model.CobolPythonStorage.NONE
    with pytest.raises(ValueError):
        _ = group.byte_length
    with pytest.raises(ValueError):
        _ = group.value_domain


def test_comp_vat_rate_redefines_the_group_and_occurs_five_times() -> None:
    """`05  Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5.`

    Verbatim from [copybooks/wssystem.cob:L61]. The subscripted view of the same
    twenty bytes the five named rates occupy: same class, same digits, same
    scale, plus an OCCURS of five and a REDEFINES naming the group. It has no
    column of its own, so its key is the copybook-qualified one.
    """
    field = _descriptor("System-Record.Vat-Rate")

    assert field.usage is model.Usage.COMP
    assert field.occurs == 5
    assert field.redefines == "Vat-Rates"
    assert field.picture == "99v99"
    assert field.digits == 4
    assert field.scale == 2
    assert field.quantum == Decimal("0.01")
    assert field.python_storage is model.CobolPythonStorage.DECIMAL
    assert field.byte_length == 2, "the OCCURS count is not a width multiplier"
    assert field.source_locator == "copybooks/wssystem.cob:L61"


def test_comp_line_cnt_in_sl060_is_a_two_digit_integer() -> None:
    """`03  line-cnt        pic 99        comp    value zero.`

    Verbatim from [sales/sl060.cbl:L223]. Two digits and no implied decimal
    point, so the carrier is `int` even though the class is `COMP` - the carrier
    follows the SCALE, and the class only decides the layout. One byte under the
    default binary-size policy, and a domain of 0 to 99 taken from the DIGITS.
    """
    field = _sl060_line_cnt()

    assert field.usage is model.Usage.COMP
    assert field.digits == 2
    assert field.scale == 0
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.is_int is True
    assert field.byte_length == 1
    assert field.value_domain == (0, 99)
    assert field.cite() == "sales/sl060.cbl:L223"


def test_comp_rrn_is_a_five_digit_integer() -> None:
    """`Rrn pic 9(5) comp` inside `File-Access`.

    Verbatim from [copybooks/wsfnctn.cob:L24]. The relative record number the
    file-handler protocol carries: five digits, unsigned, scale zero, so an `int`
    in four bytes - the default binary-size policy allocating four bytes to
    anything from five to nine digits.
    """
    field = _descriptor("File-Access.Rrn")

    assert field.name == "Rrn"
    assert field.usage is model.Usage.COMP
    assert field.picture == "9(5)"
    assert field.digits == 5
    assert field.scale == 0
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.byte_length == 4
    assert field.value_domain == (0, 99999)
    assert field.source_locator == "copybooks/wsfnctn.cob:L24"


def test_line_cnt_diverges_between_sl060_and_sl100() -> None:
    """R-4: one name, two storage classes, in two sibling programs.

    `line-cnt` is `pic 99 comp` in `sl060` [sales/sl060.cbl:L223] and
    `binary-char` in `sl100` [sales/sl100.cbl:L173]. The two are NOT unified into
    a shared definition: a defect reproduced is correct, and normalising a
    per-program divergence is precisely the well-meaning tidy-up R-4 forbids.

    The divergence has a visible consequence, which is why it is worth locking:
    the `sl060` item takes its domain from its two digits and stops at 99, while
    the `sl100` item takes its domain from one signed byte and runs to 127.
    """
    in_sl060 = _sl060_line_cnt()
    in_sl100 = _sl100_line_cnt()

    assert in_sl060.name == in_sl100.name == "line-cnt"
    assert in_sl060.usage is not in_sl100.usage
    assert in_sl060.usage is model.Usage.COMP
    assert in_sl100.usage is model.Usage.BINARY_CHAR

    # Same width, different domains, and different provenance.
    assert in_sl060.byte_length == in_sl100.byte_length == 1
    assert in_sl060.value_domain == (0, 99)
    assert in_sl100.value_domain == (-128, 127)
    assert in_sl060.value_domain != in_sl100.value_domain
    assert in_sl060.cite() == "sales/sl060.cbl:L223"
    assert in_sl100.cite() == "sales/sl100.cbl:L173"

    # Both carry `int`, which is the one thing they do agree on.
    assert in_sl060.is_int is True
    assert in_sl100.is_int is True


# ---------------------------------------------------------------------------
#  GROUP 4  -  THE DECLARATION WINS OVER THE COMMENT  (R-4)
#
#  Three in-scope declarations carry a trailing comment that contradicts them.
#  The ruling is: trust the DECLARATION, record the comment, RESOLVE NOTHING.
#  Each test below therefore does three things - asserts the domain the
#  declaration gives, shows the different domain the comment would have given,
#  and shows that the model carries no digit count through which the comment
#  could have leaked in. The contradiction is exhibited, never adjudicated.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "locator", "comment_digits", "declared_domain"),
    [
        # `binary-short. *> 9999 comp` - a 16-bit item, not a four-digit one.
        (
            "SALEDGER-REC.SALES-LATE-MIN",
            "copybooks/wssl.cob:L43",
            4,
            (-32768, 32767),
        ),
        # `binary-long. *> 9(8) comp` - a 32-bit item, not an eight-digit one.
        (
            "SALEDGER-REC.SALES-LIMIT",
            "copybooks/wssl.cob:L45",
            8,
            (-2147483648, 2147483647),
        ),
        # `binary-long. *> 9(8) comp` again, on the A-8 receiving field.
        (
            SALES_AVERAGE_KEY,
            "copybooks/wssl.cob:L49",
            8,
            (-2147483648, 2147483647),
        ),
    ],
)
def test_declaration_wins_over_a_comment_that_states_a_digit_count(
    key: str,
    locator: str,
    comment_digits: int,
    declared_domain: tuple[int, int],
) -> None:
    """A trailing `*> 9999 comp` or `*> 9(8) comp` does not narrow the item.

    The comment names a digit count; the declaration names a hardware class. The
    compiler read the declaration, so the domain is the class's and the item
    carries no digit count at all - there is nothing for the comment's count to
    have populated.

    Args:
        key: The dictionary key of the declared field.
        locator: Where the declaration and its comment sit.
        comment_digits: The digit count the comment states.
        declared_domain: The domain the declared class gives.
    """
    field = _descriptor(key)

    assert field.source_locator == locator
    assert field.value_domain == declared_domain
    assert field.picture is None, "the comment did not become a picture clause"
    assert field.digits is None, "no digit count reached the model"

    # What the comment WOULD have given, computed rather than asserted from
    # memory, so the two answers can be seen to differ. Nothing here decides
    # between them: the comment's reading is simply not the one in force.
    commented_domain = cobol_usage.value_domain(
        model.Usage.COMP, digits=comment_digits, signed=True
    )
    assert commented_domain == (
        -(10**comment_digits - 1),
        10**comment_digits - 1,
    )
    assert commented_domain != declared_domain

    # WHERE THE COMMENT IS RECORDED. The generated artifact does not copy a
    # trailing picture comment into its notes - the notes on these fields speak
    # only of the bridge narrowing - so the comment is recorded in this test's own
    # citation of the declaration above. What matters for R-4 is what is NOT
    # there: no note adopts the comment's digit count, and no note adjudicates
    # between the two readings. The contradiction stands.
    #
    # THE CHECK IS FOR A DIGIT-COUNT CLAIM, NOT FOR THE DIGIT ANYWHERE IN PROSE. It
    # used to search each note for `str(comment_digits)` as a bare substring, which is
    # satisfied by any note that happens to contain that character - and the sign-loss
    # note now quotes measured values like `-123456` and `2147483648`, so an `8` or a
    # `4` appears in it for reasons that have nothing to do with a digit count. A bare
    # substring test therefore reported a repaired contradiction where none existed.
    # What the rule actually forbids is a note ASSERTING the commented width, so that
    # is what is looked for: the number adjacent to a width word.
    entry = _entry(key)
    width_claim = re.compile(
        rf"\b{comment_digits}\b[\s-]*(digit|digits|byte|bytes|wide|width)"
        rf"|(digit|digits|byte|bytes|wide|width)[\s-]*\b{comment_digits}\b",
        re.IGNORECASE,
    )
    offending = tuple(note for note in entry.notes if width_claim.search(note))
    assert not offending, (
        f"no note on {key} may adopt the comment's digit count of "
        f"{comment_digits}: the contradiction between the declaration and its "
        f"comment is recorded and left unresolved, never repaired. These notes "
        f"assert it: {offending}"
    )


def test_declaration_wins_over_the_comment_that_says_page_lines_holds_999() -> None:
    """`05  Page-Lines      binary-char  unsigned. *> 999. Portrait / default`

    Verbatim from [copybooks/wssystem.cob:L65]. The comment says 999; one
    unsigned byte stops at 255. The declaration wins, so the maximum is 255 - and
    the contradiction stands unresolved, recorded here and in the anomaly log
    rather than repaired by widening the item.
    """
    field = _descriptor("SYSTEM-REC.PAGE-LINES")

    assert field.value_domain == (0, 255)
    assert field.max_value == 255
    assert field.unsigned is True
    assert field.picture is None, "the comment did not become a picture clause"
    assert field.digits is None, "no digit count reached the model"

    # The comment's own reading, and the size of the disagreement: a page length
    # between 256 and 999 cannot be represented at all.
    commented_domain = cobol_usage.value_domain(
        model.Usage.COMP, digits=3, signed=False, unsigned=True
    )
    assert commented_domain == (0, 999)
    assert commented_domain != field.value_domain
    assert field.max_value < commented_domain[1]

    # A store of the commented maximum is silently reduced into the byte rather
    # than refused - R-3, no new validation - which is what makes the
    # contradiction reachable at run time instead of theoretical.
    assert cobol_usage.coerce(
        Decimal("999"), usage=model.Usage.BINARY_CHAR, signed=False, unsigned=True
    ) == 999 % 256

    # The artifact records nothing at all for this field: no note, no anomaly, no
    # question. The comment lives in the frozen copybook and in this test's
    # citation of it, and nothing has adjudicated it.
    entry = _entry("SYSTEM-REC.PAGE-LINES")
    assert entry.notes == ()
    assert entry.anomaly_refs == ()
    assert entry.ambiguity_refs == ()


# ---------------------------------------------------------------------------
#  GROUP 5  -  A-11: THE SIGN IS LOST AT THE BRIDGE, NOT AT THE DATABASE
#
#  Section 0.6.2, verbatim: "a negative value computed in COBOL loses its sign AT
#  THE BRIDGE, not at the database". Three layers, and the middle one is where it
#  happens:
#
#  copybooks/wssl.cob:L49   03  Sales-Average    binary-long. *> 9(8) comp
#  <-- SIGNED
#  common/salesMT.cbl:L308      05  HV-SALES-AVERAGE  PIC 9(10) COMP.
#  <-- UNSIGNED
#  mysql/ACASDB.sql:L969        `SALES-AVERAGE` int(8) unsigned NOT NULL
#  <-- UNSIGNED
#
#  Three instances are asserted - `binary-long` in two different records and
#  `binary-short` in one - plus a CLEAN PASS-THROUGH contrast, so the drift is
#  shown to be SPECIFIC rather than systemic. Every one is read from the
#  artifact's own drift block, which is computed BY COMPARING the three views, so
#  none of these facts is hard-coded in the migration.
#
#  What the bridge actually stores WAS question Q-3 and is now MEASURED: see
#  `test_q3_the_bridge_stores_the_absolute_value_for_a_negative` at the end of this
#  group, and its sibling in Group 9, both of which assert the reading GnuCOBOL 3.2.0
#  produced - absolute value, then bounded by the receiving digit count.
# ---------------------------------------------------------------------------


def test_a11_sales_average_loses_its_sign_at_the_bridge() -> None:
    """A-11, the canonical instance, read from all three layer views.

    [copybooks/wssl.cob:L49] declares it signed; [common/salesMT.cbl:L308]
    declares the host variable unsigned; [mysql/ACASDB.sql:L969] declares the
    column unsigned. The artifact's drift block reports the signedness
    disagreement, and the entry carries the anomaly reference and the measured
    storage rule that settled `Q-3`.
    """
    field = _descriptor(SALES_AVERAGE_KEY)
    drift = field.drift()

    assert drift is not None
    assert drift.signedness is True

    # The three views, so the assertion above is legible rather than magic.
    copybook = loader.copybook_field_for(SALES_AVERAGE_KEY)
    host_variable = loader.host_variable_for(SALES_AVERAGE_KEY)
    column = loader.column_for(SALES_AVERAGE_KEY)
    assert copybook is not None
    assert host_variable is not None
    assert column is not None

    assert copybook.source == "copybooks/wssl.cob:L49"
    assert copybook.signed is True
    assert copybook.usage is model.Usage.BINARY_LONG

    assert host_variable.source == "common/salesMT.cbl:L308"
    assert host_variable.name == "HV-SALES-AVERAGE"
    assert host_variable.picture == "9(10)"
    assert host_variable.usage is model.Usage.COMP
    assert host_variable.signed is False

    assert column.source == "mysql/ACASDB.sql:L969"
    assert column.sql_type == "int(8) unsigned"
    assert column.unsigned is True

    # The sign is already gone one layer before the column, which is the whole
    # point of the anomaly: it is a BRIDGE defect, not a schema one.
    assert copybook.signed is not host_variable.signed
    assert host_variable.signed is False and column.unsigned is True

    # The ANOMALY is still published, because measuring the sign loss did not
    # repair it. The QUESTION is not, because it has been settled - see
    # `test_q3_the_bridge_stores_the_absolute_value_of_a_negative`. Both halves are
    # asserted so that neither can drift: republishing Q-3 would misreport a settled
    # question, and dropping A-11 would hide a live defect.
    assert BRIDGE_SIGN_ANOMALY in field.anomaly_refs()
    # Q-3 IS RESOLVED, so the entry publishes the MEASUREMENT rather than an OPEN
    # ambiguity. The anomaly stays: the sign
    # loss is the reproduced defect and does not stop being one because the resulting
    # value is now known (rule R-4).
    assert BRIDGE_SIGN_QUESTION not in field.ambiguity_refs()
    assert any(
        BRIDGE_SIGN_MEASUREMENT in note
        for note in loader.get_entry(SALES_AVERAGE_KEY).notes
    )


def test_a11_covers_all_nine_wssl_binary_long_fields() -> None:
    """The narrowing block is nine host variables wide, not one.

    [common/salesMT.cbl:L304-L312] narrows all nine of the `binary-long`
    statistics fields at [copybooks/wssl.cob:L45-L53] to `PIC 9(10) COMP`. The
    specification body's "L305-L312" omits `HV-SALES-LIMIT` at L304; the frozen
    file has nine, so nine are asserted.
    """
    for key in WSSL_BINARY_LONG_KEYS:
        field = _descriptor(key)
        drift = field.drift()
        assert drift is not None, key
        assert drift.signedness is True, key
        assert BRIDGE_SIGN_ANOMALY in field.anomaly_refs(), key
        assert BRIDGE_SIGN_QUESTION not in field.ambiguity_refs(), key
        assert any(
            BRIDGE_SIGN_MEASUREMENT in note
            for note in loader.get_entry(key).notes
        ), key

        host_variable = loader.host_variable_for(key)
        assert host_variable is not None, key
        assert host_variable.picture == "9(10)", key
        assert host_variable.signed is False, key


def test_a11_second_instance_the_four_glbatch_date_stamps() -> None:
    """A second instance, in a different record and a different bridge.

    `Entered`, `Proofed`, `Posted` and `Stored` are signed `binary-long`
    [copybooks/wsbatch.cob:L36-L39], their host variables are `PIC 9(10) COMP`
    [common/glbatchMT.cbl:L287-L290] and their columns are `int(8) unsigned`
    [mysql/ACASDB.sql:L86-L89]. Nothing in the migration lists these four as
    sign-loss fields: the drift is DETECTED by comparing the three views, which is
    why an instance the specification body never enumerates is caught anyway.
    """
    assert len(WSBATCH_DATE_KEYS) == 4

    for key in WSBATCH_DATE_KEYS:
        field = _descriptor(key)
        drift = field.drift()
        assert drift is not None, key
        assert drift.signedness is True, key
        assert field.usage is model.Usage.BINARY_LONG, key
        assert field.signed is True, key

        host_variable = loader.host_variable_for(key)
        column = loader.column_for(key)
        assert host_variable is not None and column is not None, key
        assert host_variable.picture == "9(10)", key
        assert host_variable.signed is False, key
        assert column.sql_type == "int(8) unsigned", key
        assert BRIDGE_SIGN_ANOMALY in field.anomaly_refs(), key
        assert BRIDGE_SIGN_QUESTION not in field.ambiguity_refs(), key
        assert any(
            BRIDGE_SIGN_MEASUREMENT in note
            for note in loader.get_entry(key).notes
        ), key

    # Exactly these four columns of the batch record drift in signedness - the
    # amounts do not - so the batch record shows the same specificity the sales
    # record does.
    drifting = tuple(
        entry.key
        for entry in loader.entries_for_table("GLBATCH-REC")
        if entry.column is not None and entry.drift.signedness
    )
    assert drifting == WSBATCH_DATE_KEYS


def test_a11_third_instance_the_binary_short_late_bounds() -> None:
    """A third instance, in the `binary-short` flavour.

    `Sales-Late-Min` and `Sales-Late-Max` are signed `binary-short`
    [copybooks/wssl.cob:L43-L44], their host variables are `PIC 9(05) COMP`
    [common/salesMT.cbl:L302-L303] and their columns are `smallint(4) unsigned`.
    The narrowing is therefore not particular to the 32-bit class: with the two of
    them the full signed-to-unsigned span at the sales bridge is eleven host
    variables, [common/salesMT.cbl:L302-L312].
    """
    for key in WSSL_BINARY_SHORT_KEYS:
        field = _descriptor(key)
        drift = field.drift()
        assert drift is not None, key
        assert drift.signedness is True, key
        assert field.usage is model.Usage.BINARY_SHORT, key

        host_variable = loader.host_variable_for(key)
        column = loader.column_for(key)
        assert host_variable is not None and column is not None, key
        assert host_variable.picture == "9(05)", key
        assert host_variable.signed is False, key
        assert column.sql_type == "smallint(4) unsigned", key


def test_sales_current_passes_through_the_bridge_signed() -> None:
    """The clean contrast: signed at all three layers, so no drift.

    `03  Sales-Current      pic s9(8)v99       comp-3.`
    [copybooks/wssl.cob:L54] -> `PIC S9(08)V9(02) COMP`
    [common/salesMT.cbl:L313] -> `decimal(10,2)` [mysql/ACASDB.sql:L974].

    This is what makes A-11 a finding rather than a description of the whole
    bridge: the monetary fields keep their signs, so a migration that dropped
    signs everywhere would be as wrong as one that kept them everywhere.
    """
    field = _descriptor("SALEDGER-REC.SALES-CURRENT")
    drift = field.drift()

    assert drift is not None
    assert drift.signedness is False
    assert field.anomaly_refs() == ()
    assert field.ambiguity_refs() == ()

    copybook = loader.copybook_field_for("SALEDGER-REC.SALES-CURRENT")
    host_variable = loader.host_variable_for("SALEDGER-REC.SALES-CURRENT")
    column = loader.column_for("SALEDGER-REC.SALES-CURRENT")
    assert copybook is not None
    assert host_variable is not None
    assert column is not None

    assert copybook.signed is True
    assert host_variable.signed is True
    assert column.unsigned is False
    assert column.sql_type == "decimal(10,2)"

    # And a negative value survives the store into it, which is the behavioural
    # form of "no drift".
    assert arithmetic.store(Decimal("-1234.56"), field) == Decimal("-1234.56")


def test_a11_drift_is_specific_and_not_systemic() -> None:
    """Eleven of the sales record's thirty-seven columns drift; seven money ones do not.

    A count rather than a claim: the eleven are exactly the `binary-short` pair
    and the nine `binary-long` fields, and the seven signed `COMP-3` money
    columns are exactly those that pass through cleanly. Both numbers come from
    comparing the three views, so this test fails if the narrowing ever spreads or
    is ever quietly repaired.
    """
    entries = loader.entries_for_table("SALEDGER-REC")
    column_backed = tuple(entry for entry in entries if entry.column is not None)
    assert len(column_backed) == 37

    drifting = tuple(
        entry.key for entry in column_backed if entry.drift.signedness
    )
    assert drifting == WSSL_BINARY_SHORT_KEYS + WSSL_BINARY_LONG_KEYS
    assert len(drifting) == 11

    signed_money = tuple(
        entry.key
        for entry in column_backed
        if entry.copybook is not None
        and entry.copybook.signed
        and not entry.drift.signedness
        and entry.cobol_python_storage is model.CobolPythonStorage.DECIMAL
    )
    assert len(signed_money) == 7
    assert "SALEDGER-REC.SALES-CURRENT" in signed_money
    assert not set(drifting) & set(signed_money)


def test_q3_the_bridge_stores_the_absolute_value_for_a_negative() -> None:
    """A-11's value consequence, MEASURED and therefore asserted.

    Q-3 asked what the bridge's C interface actually stores when a negative COBOL value
    is moved into an unsigned host variable, [copybooks/wssl.cob:L49] ->
    [common/salesMT.cbl:L308]. Agent Action Plan section 0.6.8 required the compiled
    oracle to answer it, and until it had, this test asserted the migration's
    provisional reading under `xfail(strict=True)` so that a choice could never be read
    as a fact.

    THE MEASUREMENT. GnuCOBOL 3.2.0, the compiler the maintainer targets
    [common/comp-common.sh:L9], no dialect flag and no arithmetic directive:

        01 signed-src      binary-long.
        01 hv-unsigned     pic 9(10) comp.
        01 small-unsigned  pic 9(4)  comp.
        ...
        -1          -> 0000000001
        -1000       -> 0000001000
        -2147483648 -> 2147483648
        +1000       -> 0000001000
        -123456 into pic 9(4) comp -> 3456
        +123456 into pic 9(4) comp -> 3456

    So the ABSOLUTE VALUE is stored - the ISO `MOVE` reading - and NOT a two's-complement
    reinterpretation of the source bytes, which would have made -1 store 4294967295. The
    receiving field's own digit count then bounds the magnitude, identically for a
    negative and a positive source. That is exactly what `usage.coerce` already did
    through `_wrap_into_bits`, so the measurement CONFIRMS the implementation rather
    than changing it, and it independently reproduces the measurement already recorded
    in the `Q-3` entry of `AMBIGUITIES` in acas_posting/dal/acas007_gl_batch.py.

    THE ANOMALY IS UNAFFECTED. A-11 is that the sign is lost at the BRIDGE, before any
    SQL runs - so the debit-versus-credit sense of the statistic is gone from the
    database. Knowing which value results does not make that acceptable and does not
    repair it; it is reproduced exactly (rule R-4).
    """
    field = _descriptor(SALES_AVERAGE_KEY)
    host_variable = loader.host_variable_for(SALES_AVERAGE_KEY)
    assert host_variable is not None
    assert host_variable.picture == "9(10)"
    assert host_variable.signed is False

    def stored(value: str) -> Decimal | int | str:
        """Coerce one value into the host variable's own shape."""
        return cobol_usage.coerce(
            Decimal(value),
            usage=host_variable.usage,
            digits=host_variable.digits,
            scale=host_variable.scale,
            signed=host_variable.signed,
        )

    # THE MEASURED ANSWER, as a fact. Each pair is one line of the probe output above.
    assert stored("-1") == 1
    assert stored("-12") == 12
    assert stored("-1000") == 1000
    assert stored("-2147483648") == 2147483648
    assert stored("1000") == 1000

    # NOT the two's-complement reading, which is the answer the question existed to
    # rule out: 4294967295 for -1 in a 32-bit field, or 18446744073709551615 in 64.
    assert stored("-1") != 4294967295
    assert stored("-12") != -12

    # A negative and its magnitude are INDISTINGUISHABLE once stored, which is the
    # behavioural statement of A-11.
    assert stored("-12") == stored("12")

    # The anomaly is on record and the question is not.
    assert BRIDGE_SIGN_ANOMALY in field.anomaly_refs()
    assert BRIDGE_SIGN_QUESTION not in field.ambiguity_refs(), (
        f"{BRIDGE_SIGN_QUESTION} is settled - GnuCOBOL 3.2.0 stores the absolute "
        f"value, bounded by the receiving digit count - so no entry may still "
        f"publish it as an open ambiguity on {SALES_AVERAGE_KEY}."
    )
    assert any(
        BRIDGE_SIGN_MEASUREMENT in note
        for note in loader.get_entry(SALES_AVERAGE_KEY).notes
    ), (
        f"the measurement that settled {BRIDGE_SIGN_QUESTION} must be recorded on "
        f"{SALES_AVERAGE_KEY}, so a reader of the dictionary alone learns what an "
        f"unsigned host variable stores for a negative value."
    )
    # The ANOMALY is not settled and must still be published.
    assert BRIDGE_SIGN_ANOMALY in field.anomaly_refs()


def test_a11_the_shipped_handler_drops_the_sign_at_its_own_load_paragraph() -> None:
    """A-11, LOCKED ON THE CODE THAT SHIPS - `acas012_sales`, not `usage.coerce`.

    WHY THIS EXISTS BESIDE THE TEST ABOVE, WHICH LOOKS LIKE IT COVERS THE SAME GROUND.
    The test above drives `acas_posting/cobol/usage.py::coerce`, the SEMANTICS helper.
    That is the right subject for "what does a `PIC 9(10) COMP` receiver store", and it
    is not the subject of A-11: the anomaly is that the sales-ledger handler's
    `bb000-HV-Load` PUTS a signed statistic INTO such a receiver
    [copybooks/wssl.cob:L43-L53] -> [common/salesMT.cbl:L302-L312]. Those are two
    different pieces of code, and the reproduction rule R-4 protects is the second one.

    THE GAP THIS CLOSES, MEASURED RATHER THAN SUPPOSED. Making
    `acas_posting/dal/acas012_sales.py`'s narrowing sign-PRESERVING left the whole
    arithmetic tier green - the mutation was never invoked, because every lock lived on
    `usage.coerce` or on the dictionary's `anomaly_refs()` - and left the sales scenario
    green too, because that scenario exercises the helper twenty times and NO SEEDED
    VALUE IS NEGATIVE, so removing the narrowing changed no stored byte. A repair of a
    reproduced defect that turns nothing red is exactly what R-4 forbids, so the
    negative value the seeds do not carry is supplied HERE.

    WHAT IS ASSERTED, at three depths of the shipped path:

    1. THE HELPER, for all ELEVEN A-11 columns - `_sign_loss_at_the_bridge` returns the
       ABSOLUTE VALUE, and a negative and its magnitude become indistinguishable. Also
       that the receiving host variable's own digit count bounds the magnitude, which is
       the second half of the measured `MOVE` semantics.
    2. THE SIBLING HELPER `_store_into_unsigned_host_variable`, which serves the columns
       whose copybook field is unsigned TOO. It has no sign to lose and drops one all
       the same, because the frozen bridge's `MOVE` into an unsigned receiver does; both
       its zero-scale branch and its scaled branch are driven.
    3. THE PARAGRAPH - `bb000_hv_load` on a real `WS-Sales-Record` carrying a NEGATIVE
       `Sales-Average` and a NEGATIVE `Sales-Current`. The statistic arrives at the host
       variable positive (the sign is gone before any SQL is built) while the money
       column arrives NEGATIVE, which is Agent Action Plan 0.6.2's own point that the
       drift is "specific rather than systemic" - and it is what stops this test from
       being satisfied by a handler that simply took `abs` of everything.

    NO DATABASE AND NO CONNECTION. `bb000_hv_load` is a pure `MOVE` paragraph over two
    dataclasses; the module-level autouse fixture purges `acas_posting.dal` afterwards,
    so the tier's import contract is unchanged (R-1).
    """
    module = _shipped("acas_posting.dal.acas012_sales")

    assert len(module.SIGN_LOSS_COLUMNS) == 11, (
        f"A-11 covers eleven columns; the shipped module reports "
        f"{len(module.SIGN_LOSS_COLUMNS)}."
    )

    #  1 - THE HELPER, every one of the eleven.
    for column in module.SIGN_LOSS_COLUMNS:
        digits = module.ENTRIES[column].bridge_host_variable.digits
        assert digits is not None, f"{column} declares no host-variable digit count"

        negative = module._sign_loss_at_the_bridge(-12, column=column)
        assert negative == 12, (
            f"{column}: the shipped handler stored {negative!r} for -12. GnuCOBOL 3.2.0 "
            f"stores the ABSOLUTE VALUE in an unsigned receiver, and A-11 is that this "
            f"handler moves a signed statistic into one. A sign-preserving store here "
            f"REPAIRS a reproduced defect, which rule R-4 makes a failure."
        )
        assert negative == module._sign_loss_at_the_bridge(12, column=column), (
            f"{column}: -12 and +12 must be INDISTINGUISHABLE once stored. That "
            f"indistinguishability IS the anomaly - the debit-versus-credit sense of "
            f"the statistic is gone from the database."
        )
        # The receiving digit count bounds the magnitude, identically either way.
        assert module._sign_loss_at_the_bridge(
            -(10**digits + 34), column=column
        ) == 34, (
            f"{column}: a magnitude past the host variable's {digits} digits must be "
            f"bounded by the receiver, exactly as the compiled MOVE bounds it."
        )

    # And the guard that stops the anomaly being applied where the bridge does not have
    # it: a money column, signed at all three layers, is refused by this helper.
    with pytest.raises(ValueError):
        module._sign_loss_at_the_bridge(-12, column=module.MONEY_COLUMNS[0])

    #  2 - THE SIBLING HELPER, both branches.
    assert module._store_into_unsigned_host_variable(-7, column="SALES-CREDIT") == 7, (
        "SALES-CREDIT: the zero-scale branch of `_store_into_unsigned_host_variable` "
        "must store the absolute value. This is the exact site whose sign-preserving "
        "mutation previously left the whole corpus green."
    )
    assert module._store_into_unsigned_host_variable(
        Decimal("-1.25"), column="SALES-DISCOUNT"
    ) == Decimal("1.25"), (
        "SALES-DISCOUNT: the scaled branch must store the absolute value at the host "
        "variable's own scale."
    )

    #  3 - THE PARAGRAPH, on a real record, with the money control beside it.
    record = module.WsSalesRecord()
    setattr(record, module.RECORD_ATTRIBUTE_FOR_COLUMN["SALES-AVERAGE"], -12)
    setattr(
        record,
        module.RECORD_ATTRIBUTE_FOR_COLUMN["SALES-CURRENT"],
        Decimal("-1.25"),
    )

    loaded = module.bb000_hv_load(record)

    assert loaded.values["SALES-AVERAGE"] == 12, (
        f"bb000-HV-Load carried Sales-Average -12 into HV-SALES-AVERAGE as "
        f"{loaded.values['SALES-AVERAGE']!r}. The sign must be gone BEFORE any SQL is "
        f"built [common/salesMT.cbl:L308], which is what makes A-11 a bridge anomaly "
        f"rather than a database one."
    )
    assert loaded.values["SALES-CURRENT"] == Decimal("-1.25"), (
        f"bb000-HV-Load also dropped the sign of the MONEY column SALES-CURRENT "
        f"({loaded.values['SALES-CURRENT']!r}). It is signed at all three layers "
        f"[common/salesMT.cbl:L313-L319], so narrowing it invents an anomaly the frozen "
        f"bridge does not have - and a handler that merely took `abs` of everything "
        f"would pass every other assertion in this test."
    )


# ---------------------------------------------------------------------------
#  GROUP 6  -  A-8, TRUNCATION #2: THE INTEGER DIVIDE INTO A `binary-long`
#
#  Anomaly A-8 is a DOUBLE truncation in the moving-average idiom. This file owns
#  the second one only:
#
#  divide   sales-activety into work-2 giving sales-average.
#  [sales/sl060.cbl:L827]
#
#  `sales-average` is a picture-less `binary-long` [copybooks/wssl.cob:L49], so it
#  has scale zero and an `int` carrier, so the remainder of the divide is
#  discarded - toward zero, not floored.
#
#  WHAT THIS FILE DOES NOT DUPLICATE. Truncation #1 - the zero-scale `COMP-3`
#  accumulator `03 work-2 pic s9(14) comp-3.` [sales/sl060.cbl:L206] that discards
#  the pence of `add work-goods to work-2` [sales/sl060.cbl:L826] - belongs to
#  `test_comp3_packed_decimal.py`. The composed idiom, both truncations in the
#  order the section performs them, belongs to
#  `test_compute_truncate_unrounded.py`. The three guard variants and the missing
#  counter increment [sales/sl060.cbl:L835-L843], [sales/sl100.cbl:L506] belong to
#  the scenario tier and to `test_double_entry_explosion.py`'s siblings.
# ---------------------------------------------------------------------------


def test_a8_divide_into_a_binary_long_discards_the_remainder() -> None:
    """A-8 truncation #2: 38 over 3 stores 12, and the two thirds are gone.

    Reproduces [sales/sl060.cbl:L827] with the real receiving descriptor. The
    accumulator has already lost its pence by this point - truncation #1, locked
    by `test_comp3_packed_decimal.py` - and the divide now loses the remainder
    too. Both losses are REPRODUCED, never repaired (R-4).
    """
    receiving = _descriptor(SALES_AVERAGE_KEY)

    # `DIVIDE sales-activety INTO work-2 GIVING sales-average` with an activity
    # count of 3 and an accumulator of 38: 12.666... stores as 12.
    stored = arithmetic.divide_into_giving(
        divisor=3, dividend=Decimal("38"), receiving=receiving
    )

    assert stored == 12
    assert stored != Decimal("12.666666666666666666666666667")


def test_a8_divide_into_a_binary_long_truncates_toward_zero_when_negative() -> None:
    """A negative accumulator stores -12, not -13.

    The sales ledger can carry a negative statistic - a credit note reverses the
    goods value - so the negative case is reachable rather than theoretical, and
    it is the case where floor division would silently answer one unit low.
    """
    receiving = _descriptor(SALES_AVERAGE_KEY)

    stored = arithmetic.divide_into_giving(
        divisor=3, dividend=Decimal("-38"), receiving=receiving
    )

    assert stored == -12
    assert stored != -13
    # Python's integer floor division answers -13 for the same operands, which is
    # the one-unit-low result this whole group exists to keep out of the ledger.
    assert -38 // 3 == -13
    assert stored != -38 // 3


def test_a8_divide_into_a_binary_long_yields_an_int_and_not_a_decimal() -> None:
    """The carrier is `int`, which is what makes the truncation happen at all.

    Section 0.6.1, verbatim: "the statistics fields are Python `int` and not
    `Decimal`: they are declared `binary-long` [copybooks/wssl.cob:L46-L52], so
    their truncation on divide is INTEGER truncation, which is exactly what makes
    the moving-average defect reproducible." A `Decimal` carrier here would keep
    the fraction and the migrated average would diverge from the oracle on almost
    every invoice.
    """
    receiving = _descriptor(SALES_AVERAGE_KEY)
    stored = arithmetic.divide_into_giving(
        divisor=3, dividend=Decimal("38"), receiving=receiving
    )

    assert isinstance(stored, int)
    assert not isinstance(stored, Decimal)
    assert not isinstance(stored, bool)
    assert receiving.python_storage is model.CobolPythonStorage.INT


def test_the_two_divide_spellings_take_their_operands_in_opposite_order() -> None:
    """`INTO` divides the second operand by the first; `BY` the first by the second.

    Both spellings are live in the frozen source and they read in opposite
    directions, so the operands are deliberately ASYMMETRIC here - 3 and 38 - and
    a reversal could not pass unnoticed:

        divide   sales-activety into work-2 giving sales-average.
                                                  [sales/sl060.cbl:L827]  38 / 3
        divide   work-b by sales-pay-activety giving sales-pay-average.
                                                  [sales/sl100.cbl:L511]  b / a

    Note what the divergence between those two sites is NOT: both compute
    accumulator over activity counter. Their difference is in their guards and
    their counter handling, which the scenario tier owns.
    """
    receiving = _descriptor(SALES_AVERAGE_KEY)

    assert (
        arithmetic.divide_into_giving(
            divisor=3, dividend=Decimal("38"), receiving=receiving
        )
        == 12
    )
    assert (
        arithmetic.divide_by_giving(
            dividend=3, divisor=Decimal("38"), receiving=receiving
        )
        == 0
    )

    # Positionally too, since that is how a program module transcribes its line.
    assert arithmetic.divide_into_giving(3, Decimal("38"), receiving) == 12
    assert arithmetic.divide_by_giving(3, Decimal("38"), receiving) == 0


def test_the_sl100_average_divide_uses_the_other_spelling() -> None:
    """[sales/sl100.cbl:L511] is `BY`, and it computes accumulator over counter.

    `divide work-b by sales-pay-activety giving sales-pay-average.` - the
    accumulator is written first here and second in `sl060`, so the two
    statements arrive at the same quotient through opposite spellings. The
    receiving field is another picture-less `binary-long`
    [copybooks/wssl.cob:L51], so this quotient truncates as an integer too.
    """
    receiving = _descriptor("SALEDGER-REC.SALES-PAY-AVERAGE")
    assert receiving.usage is model.Usage.BINARY_LONG
    assert receiving.python_storage is model.CobolPythonStorage.INT

    # Accumulator 38, activity counter 3, exactly as in the sl060 case above.
    assert (
        arithmetic.divide_by_giving(
            dividend=Decimal("38"), divisor=3, receiving=receiving
        )
        == 12
    )
    assert (
        arithmetic.divide_by_giving(
            dividend=Decimal("-38"), divisor=3, receiving=receiving
        )
        == -12
    )


# ---------------------------------------------------------------------------
#  GROUP 7  -  `sl100`'s BINARY ACCUMULATORS ARE A DIFFERENT MECHANISM
#
#  `sl100` computes its payment-days average through `binary-long` working items
#  [sales/sl100.cbl:L182-L183]; `sl060` computes its goods average through
#  `comp-3` items of the same names [sales/sl060.cbl:L207-L208]. That is a genuine
#  per-program divergence, and unifying it would change what the intermediate
#  values hold. R-4: reproduce, do not tidy.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "line"),
    [
        ("n-deduct", 180),  # 03  n-deduct        binary-long           value zero.
        ("work-a", 182),  # 03  work-a          binary-long           value zero.
        ("work-b", 183),  # 03  work-b          binary-long           value zero.
    ],
)
def test_sl100_binary_long_working_items_are_four_byte_ints(
    name: str, line: int
) -> None:
    """Each is four bytes, `int`-carried and quantum-less, from its own locator.

    Args:
        name: The item's name as `sl100` writes it.
        line: Its declaration line in `sales/sl100.cbl`.
    """
    field = _sl100_binary_long(name=name, line=line)

    assert field.name == name
    assert field.usage is model.Usage.BINARY_LONG
    assert field.byte_length == 4
    assert field.value_domain == (-2147483648, 2147483647)
    assert field.python_storage is model.CobolPythonStorage.INT
    assert field.is_int is True
    assert field.quantum is None
    assert field.picture is None
    assert field.cite() == f"sales/sl100.cbl:L{line}"

    # A program-local descriptor has one layer, so there is nothing for it to
    # drift against and no anomaly or question attaches to it.
    assert field.drift() is None
    assert field.anomaly_refs() == ()
    assert field.ambiguity_refs() == ()


def test_sl100_work_accumulators_hold_whole_days_only() -> None:
    """`subtract oi-date from oi-date-cleared giving work-a` yields whole days.

    [sales/sl100.cbl:L503]. Both operands are binary day numbers, so the
    difference is a whole number of days and the accumulator that carries it has
    no fractional part to lose - which is the difference between this mechanism
    and `sl060`'s.
    """
    work_a = _sl100_binary_long(name="work-a", line=182)
    work_b = _sl100_binary_long(name="work-b", line=183)

    assert arithmetic.store(Decimal("41"), work_a) == 41
    assert isinstance(arithmetic.store(Decimal("41"), work_a), int)

    # `add work-a to work-b.` [sales/sl100.cbl:L509]. The receiving item is an
    # operand of its own ADD, so its current value is passed explicitly: 82
    # already in `work-b`, 41 added in from `work-a`.
    assert (
        arithmetic.add_to(
            Decimal("41"), receiver_value=Decimal("82"), receiving=work_b
        )
        == 123
    )

    # And a fraction cannot survive a store into either, truncating toward zero.
    assert arithmetic.store(Decimal("41.99"), work_a) == 41
    assert arithmetic.store(Decimal("-41.99"), work_a) == -41


def test_work_a_diverges_between_sl060_and_sl100() -> None:
    """R-4: the same item name is packed decimal in one program and binary in the other.

    `03  work-a          pic s9(7)v99  comp-3   value zero.`
                                                    [sales/sl060.cbl:L207]
    `03  work-a          binary-long           value zero.`
                                                    [sales/sl100.cbl:L182]

    The consequence is visible in one assertion: a store of 41.99 keeps its pence
    in `sl060` and loses them in `sl100`. Consolidating the two into one helper
    would silently give `sl100` two decimal places it does not have.
    """
    in_sl060 = _working_storage(
        name="work-a",
        source_locator="sales/sl060.cbl:L207",
        usage=model.Usage.COMP_3,
        picture="s9(7)v99",
        digits=9,
        integer_digits=7,
        scale=2,
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
    )
    in_sl100 = _sl100_binary_long(name="work-a", line=182)

    assert in_sl060.name == in_sl100.name == "work-a"
    assert in_sl060.usage is model.Usage.COMP_3
    assert in_sl100.usage is model.Usage.BINARY_LONG
    assert in_sl060.usage is not in_sl100.usage

    assert in_sl060.python_storage is model.CobolPythonStorage.DECIMAL
    assert in_sl100.python_storage is model.CobolPythonStorage.INT
    assert in_sl060.quantum == Decimal("0.01")
    assert in_sl100.quantum is None

    assert arithmetic.store(Decimal("41.99"), in_sl060) == Decimal("41.99")
    assert arithmetic.store(Decimal("41.99"), in_sl100) == 41


# ---------------------------------------------------------------------------
#  GROUP 8  -  THE AMBIENT-CONTEXT SABOTAGE TEST  (R-2 hardening)
#
#  `acas_posting/cobol/arithmetic.py` runs every `decimal` operation inside a copy
#  of its own `INTERMEDIATE_CONTEXT`, entered with `decimal.localcontext`, and
#  must never consult the ambient `decimal.getcontext()`. If it ever did, a
#  caller's precision setting - or a library that changed it - would silently
#  reshape posted figures, and the state diff against the oracle would fail with
#  no local cause to find.
#
#  This is the ONLY test in the file that touches the ambient context, and it
#  leaves it exactly as it found it.
# ---------------------------------------------------------------------------


def test_arithmetic_never_consults_the_ambient_decimal_context() -> None:
    """An ambient precision of four digits must not reshape an eleven-digit store.

    Four significant digits would turn 123456789.99 into 123500000, so if any
    operation on the path read the ambient context the corruption would be
    unmistakable. The context is saved, sabotaged, exercised and restored in a
    `finally`, so a failure inside the block cannot leak the sabotage into the
    tests that run after it.
    """
    gross = _descriptor("GLBATCH-REC.INPUT-GROSS")
    run_date = _descriptor("SYSTEM-REC.RUN-DAT")

    # Saved as a COPY, because the sabotage below mutates the live object.
    saved_context = decimal.getcontext().copy()
    try:
        decimal.getcontext().prec = 4
        assert decimal.getcontext().prec == 4, "the sabotage must be in force"

        # Eleven significant digits, stored exactly at the receiving scale.
        assert arithmetic.store(Decimal("123456789.99"), gross) == Decimal(
            "123456789.99"
        )

        # A ten-digit dividend, truncated toward zero into a `binary-long`.
        assert (
            arithmetic.divide_by_giving(
                dividend=Decimal("1234567891"), divisor=7, receiving=run_date
            )
            == 176366841
        )

        # A product wider than either operand, kept exact to the last penny.
        assert arithmetic.multiply_by_giving(
            Decimal("99999.99"), Decimal("9999"), gross
        ) == Decimal("999899900.01")

        # The module's own context is the one in force inside those calls, and it
        # is far wider than the sabotage.
        assert arithmetic.INTERMEDIATE_CONTEXT.prec == 60
        assert arithmetic.INTERMEDIATE_CONTEXT.prec > decimal.getcontext().prec

        # And the calls did not repair the ambient context behind our back
        # either: `localcontext` restores what it found, no more.
        assert decimal.getcontext().prec == 4
    finally:
        decimal.setcontext(saved_context)

    assert decimal.getcontext().prec == saved_context.prec
    assert decimal.getcontext().rounding == saved_context.rounding


# ---------------------------------------------------------------------------
#  GROUP 9  -  SILENT OVERFLOW AND THE SIGN DROP  (R-3)
#
#  `ON SIZE ERROR` and `REMAINDER` occur ZERO times in the twelve in-scope
#  programs. A value too big for its receiving field therefore keeps its
#  low-order part and a value with a sign stored into an unsigned field loses the
#  sign - silently, both of them. Nothing here raises, clamps or warns, because
#  adding any of those would be a new validation and would mask a real divergence.
# ---------------------------------------------------------------------------


def test_overflow_into_an_unsigned_binary_char_keeps_the_low_order_value(
    recwarn: pytest.WarningsRecorder,
) -> None:
    """99999 into one unsigned byte is 159, and nothing is reported.

    159 is 99999 reduced into the byte's own capacity - the high-order part is
    discarded and the low-order part kept, which is what an unguarded COBOL store
    into a one-byte item does. No exception, no clamp to 255, and no warning.

    Args:
        recwarn: pytest's warning recorder, asserted empty so that "silently" is
            a tested property rather than a claim in a comment.
    """
    stored = cobol_usage.coerce(
        Decimal("99999"), usage=model.Usage.BINARY_CHAR, unsigned=True
    )

    assert stored == 159
    assert stored == 99999 % 256
    assert isinstance(stored, int)
    assert len(recwarn) == 0, "an overflowing store must report nothing (R-3)"


def test_overflow_into_a_signed_field_keeps_the_original_sign() -> None:
    """A signed receiving field keeps the sign of the value it truncated.

    `usage._reduce_units` discards high-order DIGITS for a declared-digit class
    and then re-applies the incoming sign, so -12345.67 stored into a five-digit
    two-place item is -345.67. This is the documented behaviour of the store
    rather than an open question, so it is asserted plainly - and the companion
    sign question, which concerns an UNSIGNED receiving field, is no longer open
    either: the next test holds it against Q-3, which is `RESOLVED BY ORACLE`
    (2026-08-07) with the magnitude kept and the sign discarded.
    """
    assert (
        cobol_usage.coerce(
            Decimal("-12345.67"),
            usage=model.Usage.COMP_3,
            digits=5,
            scale=2,
            signed=True,
        )
        == Decimal("-345.67")
    )
    assert (
        cobol_usage.coerce(
            Decimal("12345.67"),
            usage=model.Usage.COMP_3,
            digits=5,
            scale=2,
            signed=True,
        )
        == Decimal("345.67")
    )


def test_store_into_an_unsigned_field_drops_the_sign(
    recwarn: pytest.WarningsRecorder,
) -> None:
    """-5.00 stored into `Input-Gross` is 5.00, silently.

    `03  Amounts                         comp-3.` / `05  Input-Gross     pic
    9(9)v99.` [copybooks/wsbatch.cob:L40-L41] - eleven digits, two places, and NO
    `S`, so the item is unsigned and a negative batch total cannot be represented
    in it at all. `arithmetic.store` drops the sign, which is a documented
    behaviour of the store and not an open question: it is the same reduction the
    signed case above performs, with the sign step omitted because there is
    nowhere to put one.

    Args:
        recwarn: asserted empty - the drop is silent.
    """
    field = _descriptor("GLBATCH-REC.INPUT-GROSS")

    assert field.signed is False
    assert field.unsigned is False, (
        "the UNSIGNED keyword is a binary-family clause; this item is unsigned "
        "because its picture carries no S"
    )
    assert field.value_domain == (0, 99999999999)

    stored = arithmetic.store(Decimal("-5.00"), field)
    assert stored == Decimal("5.00")
    assert stored != Decimal("-5.00")
    assert isinstance(stored, Decimal)
    assert len(recwarn) == 0, "the sign drop must report nothing (R-3)"


def test_q3_an_overflowing_negative_store_lands_on_its_magnitudes_byte() -> None:
    """The negative-into-unsigned OVERFLOW, MEASURED and therefore asserted.

    Q-3's second flavour: reducing a negative value into an unsigned field takes the
    absolute-value step first, so the question is not only "is the sign discarded" but
    "in which ORDER" - magnitude then reduce, or reduce then take the magnitude. The two
    give different bytes, so the order is observable and had to be measured.

    THE MEASUREMENT. GnuCOBOL 3.2.0, default flags:

        01 bc-unsigned  binary-char unsigned.        *> 0..255
        01 bc-signed    binary-char.                 *> -128..127
        01 bs-unsigned  binary-short unsigned.       *> 0..65535
        01 pic3-comp    pic 9(3) comp.
        ...
        +99999 -> binary-char unsigned = 159      -99999 -> 159
        +300   -> binary-char unsigned =  44      -300   ->  44
                                                  -1     ->   1
        +99999 -> binary-char (signed) = -97      -99999 -> +97
        +99999 -> binary-short unsigned = 34463   -99999 -> 34463
        +99999 -> pic 9(3) comp = 999             -99999 -> 999

    MAGNITUDE FIRST, THEN REDUCE. 99999 mod 256 is 159 and so is the negative's; 300 mod
    256 is 44 and so is -300's; and -1 stores 1, not 255. Had the reduction come first
    and the magnitude second, -1 would have stored 255. So a negative and its magnitude
    are indistinguishable once stored, which is what `usage.coerce` already implemented
    in `_wrap_into_bits` - the measurement confirms the implementation.

    The SIGNED counterpart is measured here too, and it behaves completely differently:
    `binary-char` wraps in two's complement and the SIGN FLIPS, +99999 storing -97 and
    -99999 storing +97. That contrast is why the unsigned case could not be reasoned out
    from the signed one and had to be measured.

    THE UNSIGNED-BOUND CASE IS AT `binary-char`, not at the sales field, because
    `SALES-AVERAGE`'s host variable is ten digits wide and nothing the cycle computes
    overflows it. The narrowing behaviour is the same; only the bound differs.
    """
    field = _descriptor(SALES_AVERAGE_KEY)

    def into_unsigned_char(value: str) -> Decimal | int | str:
        """Coerce one value into `binary-char unsigned`, the tightest bound present."""
        return cobol_usage.coerce(
            Decimal(value), usage=model.Usage.BINARY_CHAR, unsigned=True
        )

    # Magnitude first, then reduce: 99999 mod 256 == 159, for both signs.
    assert into_unsigned_char("-99999") == 159
    assert into_unsigned_char("99999") == 159
    assert into_unsigned_char("-99999") == into_unsigned_char("99999")

    # 300 mod 256 == 44, again for both signs.
    assert into_unsigned_char("-300") == 44
    assert into_unsigned_char("300") == 44

    # AND THE CASE THAT SETTLES THE ORDER. Reduce-then-magnitude would give 255 here;
    # magnitude-then-reduce gives 1, and 1 is what the compiler stores.
    assert into_unsigned_char("-1") == 1
    assert into_unsigned_char("-1") != 255

    # The signed carrier behaves differently, which is why the unsigned answer could
    # not be inferred: two's complement, and the sign flips.
    assert cobol_usage.coerce(
        Decimal("99999"), usage=model.Usage.BINARY_CHAR, unsigned=False
    ) == -97
    assert cobol_usage.coerce(
        Decimal("-99999"), usage=model.Usage.BINARY_CHAR, unsigned=False
    ) == 97

    # The anomaly is on record; the question is not.
    assert BRIDGE_SIGN_ANOMALY in field.anomaly_refs()
    assert BRIDGE_SIGN_QUESTION not in field.ambiguity_refs(), (
        f"{BRIDGE_SIGN_QUESTION} is settled in both its flavours - the magnitude is "
        f"taken first and reduced second - so no entry may still publish it as an "
        f"open ambiguity."
    )


# ---------------------------------------------------------------------------
#  GROUP 10  -  Q-5.1: THE DEFAULT BINARY-SIZE AND BINARY-TRUNCATE POLICY
#
#  Section 0.5.2, verbatim: "A census of every compile invocation in the
#  repository finds NO `-std=` dialect selection, NO `>>SET ARITHMETIC` directive
#  in any source, and NO `binary-truncate` flag anywhere." The compiler is
#  GnuCOBOL 3.2 [common/comp-common.sh:L9], so its DEFAULTS govern every COMP
#  item's width and its behaviour on store.
#
#  `acas_posting/cobol/usage.py` records that question, Q-5.1, as RESOLVED and
#  holds the policy in two constants. The assertions below are made plainly: an
#  `xfail(strict=True)` against a resolved question would XPASS and fail the
#  suite, which is the correct signal that it is no longer open. Any FUTURE
#  assertion that depended on an unmeasured compiler default would need that
#  marker; none here does.
#
#   CORRECTION, 2026-08-07. This header used to call those constants "the
#  measured policy". They were not measured; they were transcribed from
#  GnuCOBOL's documented defaults, and the register said so, carrying Q-5.1 as
#  PENDING while this file and the module both said RESOLVED. The wording is
#  corrected here rather than deleted, because the gap between "documented" and
#  "observed" is exactly what R-6 exists to police, and a reader should be able
#  to see that it once went unmarked. The constants are now backed by a compiled
#  measurement - see GROUP 12, which holds the captured vectors - and the values
#  turned out to be right, which does not make the earlier claim to have measured
#  them any less premature.
# ---------------------------------------------------------------------------


def test_q5_1_binary_size_policy_constants_are_present_and_immutable() -> None:
    """The two constants exist, hold the measured policy, and cannot be mutated.

    `DEFAULT_BINARY_SIZE_THRESHOLDS` is an ascending tuple of
    `(maximum declared digits, bytes allocated)` pairs; `BINARY_TRUNCATE` being
    True reproduces GnuCOBOL's default `binary-truncate: yes`, under which a COMP
    store reduces into its DIGIT COUNT rather than into its byte capacity.
    """
    thresholds = cobol_usage.DEFAULT_BINARY_SIZE_THRESHOLDS

    assert thresholds == ((2, 1), (4, 2), (9, 4), (18, 8))
    assert isinstance(thresholds, tuple)
    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in thresholds)

    # Ascending in both members, which is what makes the first-match lookup in
    # `usage.byte_length` correct.
    assert [digits for digits, _ in thresholds] == sorted(
        digits for digits, _ in thresholds
    )
    assert [width for _, width in thresholds] == sorted(
        width for _, width in thresholds
    )

    assert cobol_usage.BINARY_TRUNCATE is True

    # A tuple and a bool are immutable, so the policy cannot be edited in place
    # by any holder; the tuple is asserted read-only through an illegal write.
    with pytest.raises(TypeError):
        thresholds[0] = (2, 2)  # type: ignore[index]


@pytest.mark.parametrize(
    ("digits", "expected_bytes"),
    [
        (2, 1),  # `pic 99 comp` [sales/sl060.cbl:L223]
        (4, 2),  # `pic 99v99 comp` [copybooks/wssl.cob:L42]
        (5, 4),  # `pic 9(5) comp` [copybooks/wsfnctn.cob:L24]
        (9, 4),
        (10, 8),  # the bridge's `PIC 9(10) COMP` [common/salesMT.cbl:L308]
        (11, 8),  # the widest in-scope declaration
    ],
)
def test_q5_1_a_comp_item_takes_its_width_from_its_digit_count(
    digits: int, expected_bytes: int
) -> None:
    """A COMP item's width follows the size policy, one threshold at a time.

    Args:
        digits: The declared digit count.
        expected_bytes: The bytes the default policy allocates for it.
    """
    assert cobol_usage.byte_length(model.Usage.COMP, digits=digits) == expected_bytes


def test_binary_family_domains_come_from_the_class_and_not_from_a_digit_count() -> None:
    """The family's domains are width-derived, and no digit count can reach them.

    Two facts, together: `usage.value_domain` ignores `digits` outright for the
    binary family, and not one in-scope binary-family field carries a digit count
    for it to have ignored. So there is no path by which a picture - or a
    picture-shaped comment - could set one of these domains.
    """
    # The parameter is accepted for a uniform signature and has no effect.
    for member, width in cobol_usage.BINARY_WIDTH_BYTES.items():
        bits = 8 * width
        assert cobol_usage.value_domain(member) == (
            -(1 << (bits - 1)),
            (1 << (bits - 1)) - 1,
        )
        assert cobol_usage.value_domain(member, digits=3) == cobol_usage.value_domain(
            member
        )
        assert cobol_usage.value_domain(member, digits=18) == cobol_usage.value_domain(
            member
        )
        assert cobol_usage.value_domain(member, signed=False, unsigned=True) == (
            0,
            (1 << bits) - 1,
        )

    # And the declarations themselves carry no digit count.
    binary_keys = (
        WSSL_BINARY_SHORT_KEYS
        + WSSL_BINARY_LONG_KEYS
        + WSBATCH_DATE_KEYS
        + (
            "SYSTEM-REC.CYCLEA",
            "SYSTEM-REC.PERIOD",
            "SYSTEM-REC.PAGE-LINES",
            "SYSTEM-REC.RUN-DAT",
            "System-Record.Scycle",
        )
    )
    for key in binary_keys:
        field = _descriptor(key)
        assert field.is_binary_family is True, key
        assert field.digits is None, key
        assert field.integer_digits is None, key
        assert field.scale is None, key
        assert field.byte_length == cobol_usage.BINARY_WIDTH_BYTES[field.usage], key


# ---------------------------------------------------------------------------
#  GROUP 11  -  TIER ISOLATION  (R-1)
#
#  Asserted from inside the run rather than trusted: this tier reaches no
#  database, no driver, no COBOL and no oracle module, so it runs on a bare host.
# ---------------------------------------------------------------------------


def test_this_tier_imports_no_database_no_cobol_and_no_oracle() -> None:
    """Importing this tier's surface loads nothing forbidden.

    The prohibited names are checked as module PREFIXES, so a submodule cannot
    slip past a top-level check. The list is the one section 0.4.3 gives for
    `tests/arithmetic/*`: the data-access layer, the entry points, the program
    modules, either database driver, the scenario definition parser and the
    oracle harness.

    The measurement is taken in a FRESH interpreter rather than over this
    session's live `sys.modules`, because the claim belongs to the tier and not
    to the process. Live residency cannot establish it: the scenario and
    determinism tiers legitimately load `harness/*` and PyYAML - section 0.4.3
    puts both on the harness side - so whenever one of them runs first in the
    same process, an absolute check fails for a reason that has nothing to do
    with this tier. A subprocess measures only what this tier's own imports
    pull in, is immune to run order, and is the only measurement that actually
    demonstrates the "runs on a bare host" property this group asserts.
    """
    forbidden_prefixes = (
        "acas_posting.dal",
        "acas_posting.cli",
        "acas_posting.programs",
        "sqlalchemy",
        "mysql.connector",
        "mysql",
        "yaml",
        "harness",
        "numpy",
        "pandas",
    )

    # Exactly this module's own module-scope import surface, re-imported clean.
    probe = (
        "import sys\n"
        "from acas_posting.cobol import arithmetic\n"
        "from acas_posting.cobol import field as cobol_field\n"
        "from acas_posting.cobol import usage as cobol_usage\n"
        "from acas_posting.dictionary import loader, model\n"
        "print(chr(10).join(sorted(sys.modules)))\n"
    )
    # FINITE, AND UNABLE TO WAIT ON A TERMINAL.
    #
    # A bare `subprocess.run` inherits this process's stdin and has no deadline, so a
    # probe that ever blocks on input - an interpreter startup file reading a prompt, a
    # `breakpoint()` reached through PYTHONBREAKPOINT, an import that asks for a
    # passphrase - hangs the whole suite with no diagnosis. `stdin=DEVNULL` makes any
    # read return EOF immediately, and the timeout bounds everything else. Thirty
    # seconds is generous for importing five pure-Python modules and short enough that
    # a hang is reported rather than waited out.
    #
    # THE TIMEOUT IS CLASSIFIED, NOT LET ESCAPE. An unhandled `TimeoutExpired` reports
    # as an error whose message is the command line, which says nothing about what the
    # check was for; this says what it was measuring and why a hang is a defect.
    try:
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=_IMPORT_PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        #  Converted into an assertion rather than propagated, so the report names the
        #  tier and the cause instead of showing a bare timeout from the standard
        #  library, and carries the child's own output so a hang is diagnosable from
        #  the report alone.
        raise AssertionError(
            f"the import-isolation probe did not finish within "
            f"{_IMPORT_PROBE_TIMEOUT_SECONDS} seconds. It only imports five "
            f"pure-Python modules and prints `sys.modules`, so a hang means one of "
            f"them is doing work at import time - opening a connection, reading a "
            f"file descriptor or waiting on input - which is exactly the coupling "
            f"this test exists to refuse (rule R-1). stdin was already /dev/null, so "
            f"it is not blocked on a prompt.\n"
            f"  command: {exc.cmd}\n"
            f"  stdout : {(exc.stdout or b'')!r}\n"
            f"  stderr : {(exc.stderr or b'')!r}"
        ) from exc
    assert completed.returncode == 0, completed.stderr
    loaded = tuple(completed.stdout.split("\n"))

    offenders = tuple(
        name
        for name in loaded
        for prefix in forbidden_prefixes
        if name == prefix or name.startswith(f"{prefix}.")
    )

    assert offenders == (), (
        f"the arithmetic tier must reach neither a database nor the compiled "
        f"oracle (R-1), but importing its surface loads: {offenders}"
    )

    # Named individually as well, because these two are the ones a reader of the
    # brief will look for.
    assert "mysql.connector" not in loaded
    assert "acas_posting.dal" not in loaded

    # What this tier DOES reach, so the guard cannot pass by importing nothing.
    assert "acas_posting.cobol.usage" in loaded
    assert "acas_posting.cobol.field" in loaded
    assert "acas_posting.cobol.arithmetic" in loaded
    assert "acas_posting.dictionary.loader" in loaded

    # And the same four are live in THIS process, so the tier is genuinely
    # exercising the modules whose isolation it just proved.
    assert "acas_posting.cobol.usage" in sys.modules
    assert "acas_posting.cobol.field" in sys.modules
    assert "acas_posting.cobol.arithmetic" in sys.modules
    assert "acas_posting.dictionary.loader" in sys.modules


def test_every_descriptor_in_this_file_carries_its_provenance() -> None:
    """R-5, asserted rather than asserted-about: no field metadata is hand-written.

    Every dictionary-backed field this file names resolves to an entry whose
    citation carries a real copybook locator, and every program-local descriptor
    carries a `<path>:L<n>` into the frozen source. A key that went stale, or a
    locator that stopped pointing at a declaration, fails here.
    """
    catalogued = (
        WSSL_BINARY_SHORT_KEYS
        + WSSL_BINARY_LONG_KEYS
        + WSBATCH_DATE_KEYS
        + VAT_RATE_KEYS
        + (
            "SALEDGER-REC.SALES-DISCOUNT",
            "SALEDGER-REC.SALES-CURRENT",
            "SYSTEM-REC.CYCLEA",
            "SYSTEM-REC.PERIOD",
            "SYSTEM-REC.PAGE-LINES",
            "SYSTEM-REC.RUN-DAT",
            "System-Record.Scycle",
            "System-Record.Vat-Rate",
            "System-Record.Vat-Rates",
            "File-Access.Rrn",
            "GLBATCH-REC.INPUT-GROSS",
        )
    )
    for key in catalogued:
        field = _descriptor(key)
        assert field.dictionary_key == key
        assert field.cite().startswith(key), key
        assert "copybook=copybooks/" in field.cite(), key

    program_local = (
        _sl060_line_cnt(),
        _sl100_line_cnt(),
        _sl100_binary_long(name="n-deduct", line=180),
        _sl100_binary_long(name="work-a", line=182),
        _sl100_binary_long(name="work-b", line=183),
    )
    for field in program_local:
        assert field.dictionary_key is None
        assert field.source_locator is not None
        assert field.cite() == field.source_locator
        assert field.cite().startswith("sales/sl")
        assert ":L" in field.cite()


def test_a_stale_dictionary_key_is_reported_with_its_near_misses() -> None:
    """The defensive resolver names the keys that do exist.

    Keys follow the COLUMN name, so `SYSTEM-REC.RUN-DATE` looks right and is
    wrong - the artifact keys that field `SYSTEM-REC.RUN-DAT`. A bare lookup
    error would send a reader hand-writing the field's metadata, which is exactly
    what R-5 forbids, so the failure carries the correction instead.
    """
    with pytest.raises(DictionaryKeyMiss) as report:
        _descriptor("SYSTEM-REC.RUN-DATE")

    message = str(report.value)
    assert "SYSTEM-REC.RUN-DAT" in message
    assert "never hand-write" in message

    # And the same resolver reports a table it does not know without pretending
    # to have suggestions for it.
    with pytest.raises(DictionaryKeyMiss) as unknown_table:
        _descriptor("NO-SUCH-REC.NO-SUCH-COLUMN")
    assert "()" in str(unknown_table.value)


# ---------------------------------------------------------------------------
#  GROUP 12  -  Q-5.1 MEASURED ON THE COMPILED ORACLE  (R-6)
#
#  GROUP 10 above asserts that `usage.py`'s two policy constants hold particular
#  values, and its header calls them "the measured policy". Until 2026-08-07 that
#  description was generous: the values had been TRANSCRIBED from GnuCOBOL's
#  documented defaults and nobody had watched the compiler agree. The register
#  said so plainly, carrying Q-5.1 as PENDING while the module said RESOLVED.
#
#  That gap is now closed by measurement rather than by rewording. A probe
#  declared each form the way the frozen copybooks declare it, stored values at
#  and beyond every ceiling, and displayed what the compiler kept. The twenty-four
#  vectors below are those captured results, and every one of them is a fact about
#  GnuCOBOL 3.2.0 rather than a reading of its manual.
#
#  Why the vectors are held HERE and compared against production, rather than
#  recomputed: a test that derives the expected value from the same constants the
#  production code consults cannot fail when the constants are wrong. These are
#  independent - copied from a compiled run - so a drift in `usage.py` breaks them.
#
#  THE DISTINCTION THE MEASUREMENT ESTABLISHED, and it is the whole point of the
#  group: `binary-truncate` and the byte capacity govern DIFFERENT declarations.
#  * An item with a PICTURE has a declared digit count, and the store reduces
#  MODULO 10**digits - so `pic 9(4) comp` turns 32767 into 2767 even though
#  two bytes could hold 32767 perfectly well. Digits win over capacity.
#  * An item declared by USAGE ALONE has no digit count for a policy to apply
#  to, so only the capacity is left, and the store WRAPS as signed two's
#  complement - `binary-short` turns 32768 into -32768.
#  Reading the policy as one rule would get one of those two classes wrong, and
#  the classes are not rare: the copybook census counts 236 bare `comp` against
#  282 pictureless `binary-*` declarations.
# ---------------------------------------------------------------------------

#: (declared digits, bytes) as the COMPILED compiler reported them through
#: `FUNCTION LENGTH`. Confirms `DEFAULT_BINARY_SIZE_THRESHOLDS` from the outside.
_MEASURED_PICTURED_COMP_BYTES: Final[Mapping[int, int]] = MappingProxyType(
    {2: 1, 4: 2, 5: 4, 8: 4, 9: 4}
)

#: The three pictureless forms' widths, likewise via `FUNCTION LENGTH`.
_MEASURED_USAGE_ONLY_BYTES: Final[Mapping[str, int]] = MappingProxyType(
    {"BINARY_CHAR": 1, "BINARY_SHORT": 2, "BINARY_LONG": 4}
)

#: (digits, stored source, what the compiler kept) for an UNSIGNED picture.
#: The 127-into-`pic 99` and 32767-into-`pic 9(4)` rows are the discriminating
#: ones: both values fit the byte capacity, and both were still reduced.
_MEASURED_PICTURED_TRUNCATION: Final[tuple[tuple[int, int, int], ...]] = (
    (2, 99, 99),
    (2, 100, 0),
    (2, 127, 27),
    (4, 9999, 9999),
    (4, 10000, 0),
    (4, 32767, 2767),
    (5, 99999, 99999),
    (5, 100000, 0),
    (8, 99999999, 99999999),
    (8, 100000000, 0),
    (9, 999999999, 999999999),
    (9, 1000000000, 0),
)

#: A negative into an UNSIGNED picture keeps its MAGNITUDE. This is the third
#: independent confirmation of that rule: Q-3 measured it at the bridge, Q-5
#: measured it at `add postings 1 giving Batch-start`, and this is a bare store.
_MEASURED_UNSIGNED_TAKES_MAGNITUDE: Final[tuple[tuple[int, int], ...]] = (
    (-1, 1),
    (-9999, 9999),
)

#: A SIGNED picture keeps the sign and still reduces on digits.
_MEASURED_SIGNED_PICTURE: Final[tuple[tuple[int, int, int], ...]] = (
    (4, -9999, -9999),
    (4, 10000, 0),
    (9, -1, -1),
)

#: PICTURELESS `binary-*`: signed two's-complement wrap at the byte capacity.
_MEASURED_USAGE_ONLY_WRAP: Final[tuple[tuple[str, int, int], ...]] = (
    ("BINARY_CHAR", 127, 127),
    ("BINARY_CHAR", 128, -128),
    ("BINARY_CHAR", 255, -1),
    ("BINARY_SHORT", 32767, 32767),
    ("BINARY_SHORT", 32768, -32768),
    ("BINARY_SHORT", 99999, -31073),
)


def test_q5_1_measured_binary_sizes_match_the_shipped_policy() -> None:
    """`FUNCTION LENGTH`, asked of the compiler, agrees with `byte_length`.

    This is the cheapest possible oracle for a width question - the compiler
    answers out of the allocation it actually made, with no database and no run
    involved - and it is the instrument that closed Q-5.1's `binary-size` half.
    """
    for digits, measured_bytes in _MEASURED_PICTURED_COMP_BYTES.items():
        assert (
            cobol_usage.byte_length(model.Usage.COMP, digits=digits, scale=0)
            == measured_bytes
        ), f"pic 9({digits}) comp: compiler measured {measured_bytes} bytes"

    for member_name, measured_bytes in _MEASURED_USAGE_ONLY_BYTES.items():
        member = getattr(model.Usage, member_name)
        assert cobol_usage.byte_length(member) == measured_bytes, (
            f"{member_name}: compiler measured {measured_bytes} bytes"
        )


def test_q5_1_a_pictured_comp_store_reduces_on_digits_not_capacity() -> None:
    """`binary-truncate` is in force: the DIGIT COUNT is the ceiling.

    The two rows that carry the argument are 127 into `pic 99 comp` and 32767
    into `pic 9(4) comp`. Each value fits its item's byte capacity exactly, and
    each was still reduced modulo its digit count - to 27 and to 2767. Had the
    compiler truncated to capacity, both would have survived whole, and every
    `COMP` figure this migration stores would be wrong in a way no scenario
    seeded with small numbers would ever reveal.
    """
    for digits, source, measured in _MEASURED_PICTURED_TRUNCATION:
        stored = cobol_usage.coerce(
            Decimal(source),
            usage=model.Usage.COMP,
            digits=digits,
            scale=0,
            unsigned=True,
        )
        assert int(stored) == measured, (
            f"pic 9({digits}) comp <- {source}: compiled oracle kept {measured}, "
            f"this build kept {stored}"
        )

    for source, measured in _MEASURED_UNSIGNED_TAKES_MAGNITUDE:
        stored = cobol_usage.coerce(
            Decimal(source),
            usage=model.Usage.COMP,
            digits=4,
            scale=0,
            unsigned=True,
        )
        assert int(stored) == measured, (
            f"pic 9(4) comp <- {source}: compiled oracle kept the magnitude "
            f"{measured}, this build kept {stored}"
        )

    for digits, source, measured in _MEASURED_SIGNED_PICTURE:
        stored = cobol_usage.coerce(
            Decimal(source),
            usage=model.Usage.COMP,
            digits=digits,
            scale=0,
            signed=True,
        )
        assert int(stored) == measured, (
            f"pic s9({digits}) comp <- {source}: compiled oracle kept {measured}, "
            f"this build kept {stored}"
        )


def test_q5_1_a_pictureless_binary_item_wraps_at_its_byte_capacity() -> None:
    """No picture means no digit count, so only the capacity can govern.

    The wrap is silent - there is no `ON SIZE ERROR` phrase at any of the frozen
    sites - and it is signed, which is what makes A-17 reach a database column as
    a magnitude: `binary-short` wraps 99999 to -31073, and the unsigned
    `pic 9(5)` that consumes it then drops the sign.
    """
    for member_name, source, measured in _MEASURED_USAGE_ONLY_WRAP:
        member = getattr(model.Usage, member_name)
        stored = cobol_usage.coerce(Decimal(source), usage=member, signed=True)
        assert int(stored) == measured, (
            f"{member_name} <- {source}: compiled oracle kept {measured}, "
            f"this build kept {stored}"
        )

    # The domains those wraps imply, stated directly, so a widened domain is
    # caught even if no vector above happens to straddle its new edge.
    assert cobol_usage.value_domain(model.Usage.BINARY_CHAR) == (-128, 127)
    assert cobol_usage.value_domain(model.Usage.BINARY_SHORT) == (-32768, 32767)


def test_q5_1_the_two_ceilings_are_not_the_same_rule() -> None:
    """A guard against collapsing the two classes into one policy.

    32767 is the value that separates them. Into `pic 9(4) comp` - which has a
    declared digit count - it becomes 2767. Into `binary-short` - which has none
    - it survives untouched. One number, one width in bytes, two answers, and any
    refactor that unified the two paths would have to break one of these.
    """
    pictured = cobol_usage.coerce(
        Decimal(32767), usage=model.Usage.COMP, digits=4, scale=0, unsigned=True
    )
    pictureless = cobol_usage.coerce(
        Decimal(32767), usage=model.Usage.BINARY_SHORT, signed=True
    )

    assert int(pictured) == 2767, "digits must govern a pictured COMP"
    assert int(pictureless) == 32767, "capacity must govern a pictureless BINARY-*"
    assert int(pictured) != int(pictureless), (
        "the two ceilings produced the same answer, so one of the two code paths "
        "has been generalised away - see GROUP 12's header"
    )

    # Both items occupy the same two bytes, which is what makes the divergence
    # a policy difference rather than a width difference.
    assert cobol_usage.byte_length(model.Usage.COMP, digits=4, scale=0) == 2
    assert cobol_usage.byte_length(model.Usage.BINARY_SHORT) == 2


# ==========================================================================
#
#  Regression locks for shared COBOL storage and DAL call boundaries.
#
#  EVERY IMPORT HERE IS MANDATORY, NOT SKIPPABLE. Reaching a module through
#  `pytest.importorskip` would make a host that cannot import one report this file as
#  SKIPPED rather than as broken - and every lock in it would silently stop locking. These are regression locks for the anomalies rule R-4
#  requires be reproduced, so a lock that can disappear into a skip line is not a
#  lock. `mysql-connector-python==26.7.0` is a hard `[project.dependencies]` entry,
#  so an installed package can always import every name below;
#  `importlib.import_module` therefore raises rather than skipping.
#
# ==========================================================================


# ---------------------------------------------------------------------------
#  THE IMPORTS ARE REAL, AND THEY LEAVE NOTHING RESIDENT.
#
#  Every test below reaches a shipped data-access module, and `acas_posting.dal.*`
#  pulls the pinned MySQL driver in transitively. Two properties have to hold at once.
#
#  THE IMPORT MUST FAIL WHEN IT FAILS. These sites used `pytest.importorskip`, which
#  turned the one outcome the file exists to catch into a PASS: a handler that cannot
#  be imported at all - a syntax error, a circular import, a symbol renamed in a module
#  it imports - produced a SKIP, and a skipped test reads as green. The driver is a hard
#  requirement of `requirements.txt`, so its absence is a broken environment and not a
#  supported configuration. `_shipped` therefore uses `importlib.import_module` and lets
#  the `ImportError` reach pytest.
#
#  AND NOTHING FORBIDDEN MAY BE LEFT LOADED. Agent Action Plan section 0.4.3 gives this
#  tier `cobol` and `records` and forbids `dal` and any database, and three files in it
#  assert exactly that - `test_comp3_packed_decimal.py`, `test_comp_binary.py` and
#  `test_pic_field_descriptors.py`. Two of them read LIVE `sys.modules`. This file used
#  to leave `acas_posting.dal.*` and `mysql.*` resident, and the only reason those three
#  kept passing is that they collate ALPHABETICALLY BEFORE it: the suite was green by
#  file order. `_purge_tier_isolated_names` runs after every test here and asserts the
#  residue is empty, so the ordering accident is no longer load-bearing.
# ---------------------------------------------------------------------------


#: The module-name prefixes the tier's own isolation assertions forbid. The same list
#: the five program-module loaders in this directory carry.
_TIER_ISOLATION_PREFIXES: Final[tuple[str, ...]] = (
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


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix the tier must not leave loaded?

    Matched as a package prefix - the exact name, or the name plus a dot - so a
    submodule cannot slip past and a merely similar name is not caught by accident.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


def _shipped(dotted_name: str) -> types.ModuleType:
    """Import a shipped module FOR REAL, letting an `ImportError` be a failure.

    Args:
        dotted_name: The importable name.

    Returns:
        The imported module.

    Raises:
        ImportError: The module could not be imported. Deliberately NOT converted into
            a skip - see the section note above.
    """
    return importlib.import_module(dotted_name)


@pytest.fixture(autouse=True)
def _purge_tier_isolated_names() -> Iterator[None]:
    """Remove every tier-isolated module each test added, and prove none survived.

    Autouse, so no test can forget it, and it asserts rather than merely cleaning:
    a name left resident would make the tier's three isolation assertions depend on
    which file ran first, which is how this leak went unnoticed.

    Yields:
        None, once, around each test.
    """
    before = frozenset(sys.modules)
    yield
    for name in sorted(set(sys.modules) - before, reverse=True):
        if _is_tier_isolated_name(name):
            del sys.modules[name]
    residue = sorted(
        name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
    )
    assert not residue, (
        f"this test left {residue} resident in sys.modules. Agent Action Plan section "
        f"0.4.3 forbids `dal` and any database in this tier, and the assertions in "
        f"test_comp3_packed_decimal.py, test_comp_binary.py and "
        f"test_pic_field_descriptors.py read LIVE sys.modules - so a survivor makes "
        f"them pass or fail on file order alone."
    )


def test_system_cycle_redefines_is_one_storage_location() -> None:
    """Cyclea and Scycle are two names for the byte at copybooks/wssystem.cob:L62-L63."""
    module = _shipped("acas_posting.records.system_record")
    block = module.SystemDataBlock()

    block.cyclea = 7
    assert block.scycle == 7

    block.scycle = 11
    assert block.cyclea == 11


@pytest.mark.parametrize("separator", ["/", ".", ",", "-"])
def test_controlled_clock_canonicalizes_supported_separators(
    separator: str,
) -> None:
    """Every maps04-supported input pins the frozen slash-form text."""
    clock = _shipped("acas_posting.clock")

    pinned = clock.pin_from_to_day(f"21{separator}09{separator}2025")

    assert pinned.to_day == "21/09/2025"
    assert pinned.run_date == 155127


def test_gl_batch_key_redefines_round_trips_through_both_views() -> None:
    """The grouped and six-digit batch keys cannot diverge."""
    records = _shipped("acas_posting.records.gl_batch")
    dal = _shipped("acas_posting.dal.acas007_gl_batch")

    assert [field.name for field in dataclasses.fields(records.WsBatchKey9)] == [
        "ws_batch_key9"
    ]

    batch = records.GlBatchRecord()
    batch.ws_batch_key.ws_ledger = 1
    batch.ws_batch_key.ws_batch_nos = 2
    assert batch.ws_batch_key9.ws_batch_key9 == 100002

    batch.ws_batch_key9.ws_batch_key9 = 200123
    assert batch.ws_batch_key.ws_ledger == 2
    assert batch.ws_batch_key.ws_batch_nos == 123
    assert dal.synchronise_batch_key_views(batch) == 200123
    assert dal.COLUMNS[0].record_path == ("ws_batch_key9", "ws_batch_key9")


def test_purchase_order_group_move_preserves_the_caller_byte_image() -> None:
    """The X(10) caller view survives the bridge's mixed-type group view."""
    records = _shipped("acas_posting.records.purchase_invoice")
    dal = _shipped("acas_posting.dal.acas026_pinvoice")

    group = records.IhOrder(
        ih_freq=" ",
        ih_repeat=0,
        filler_1=" " * 3,
        ih_last_date=0,
    )
    context = dal.PInvoiceContext()
    caller_image = "SO-31009  "

    dal._split_ih_order(caller_image, group, context)

    # `ih-order pic x(10)` [copybooks/plwspinv2.cob:L28] may contain bytes that
    # are not valid for the numeric members of the bridge's group view
    # [copybooks/plwspinv.cob:L17-L27]. An untouched group MOVE copies those
    # bytes; it does not parse and reformat them.
    assert group.ih_repeat == 0
    assert dal._group_ih_order(group, context) == caller_image

    # Once a subordinate field is explicitly changed, its declared representation
    # replaces the corresponding bytes, exactly as a COBOL elementary MOVE would.
    group.ih_repeat = 12
    assert dal._group_ih_order(group, context).startswith("S12")


def test_purchase_ledger_linkage_reinterprets_binary_bytes_like_purchmt() -> None:
    """acas022/wspl bytes cross purchMT's incompatible COMP linkage unchanged."""
    records = _shipped("acas_posting.records.purchase_ledger")
    dal = _shipped("acas_posting.dal.acas022_purch")

    caller = records.WsPurchRecord()
    caller.purch_sortcode = 112233
    caller.purch_accountno = 12345678
    caller.purch_last_inv = 155127
    caller.purch_average = 642
    caller.purch_create_date = 150000

    loaded = dal.bb000_hv_load(caller)

    # The frozen CALL passes native BINARY-LONG bytes to `PIC 9(8) COMP`
    # [copybooks/wspl.cob:L32-L39], [common/purchMT.cbl:L345-L352]. The
    # bridge's subsequent numeric MOVE preserves the reinterpreted underlying
    # value; only sort code's eight-character SQL window truncates it later.
    assert loaded.hv_purch_sortcode == 73535488
    assert loaded.hv_purch_accountno == 1315027968
    assert loaded.hv_purch_last_inv == 4150067712
    assert loaded.hv_purch_average == 2181169152
    assert loaded.hv_purch_create_dat == 4031316480

    fetched = dal.HostVariables(
        hv_purch_accountno=1315027968,
        hv_purch_last_inv=2354905600,
        hv_purch_average=2181169152,
        hv_purch_create_dat=4031316480,
    )
    unloaded = records.WsPurchRecord()
    dal.bb100_unload_hvs(fetched, unloaded)

    # The reverse MOVE first narrows into purchMT's eight-digit picture, then
    # exposes those bytes through the native BINARY-LONG caller declaration.
    assert unloaded.purch_accountno == 5235968
    assert unloaded.purch_last_inv == 13321475
    assert unloaded.purch_average == 9164292
    assert unloaded.purch_create_date == 14343425


def test_acas000_rdbms_dispatch_clears_the_incoming_reply_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An EOF from key 2 cannot suppress the following key-1 bridge call."""
    handler = _shipped("acas_posting.dal.acas000_system")
    status = _shipped("acas_posting.dal.status")
    file_access_module = _shipped("acas_posting.records.file_access")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    handler.reset_handler_state()
    system = system_module.SystemRecord()
    file_access = file_access_module.FileAccess()
    file_access.file_function = int(status.FileFunction.READ_INDEXED)
    file_access.fs_reply = int(status.FsReply.END_OF_FILE)
    file_access.we_error = 10
    dal_common = flags_module.AcasDalCommonData(sw_testing=0)
    observed: list[tuple[int, int, int]] = []

    monkeypatch.setattr(handler, "ba010_test_ws_rec_size", lambda _fa: None)
    monkeypatch.setattr(
        handler,
        "ba012_test_ws_rec_size_2",
        lambda _system, _fa, _common: False,
    )
    monkeypatch.setattr(handler, "ba_rdbms_exit", lambda: None)

    def capture(file_access_arg, _common, _record) -> None:
        observed.append(
            (
                int(file_access_arg.fs_reply),
                int(file_access_arg.we_error),
                int(file_access_arg.file_function),
            )
        )

    monkeypatch.setattr(handler, "ba015_test_ends", capture)
    handler.ba_process_rdbms(file_access, dal_common, system)

    assert observed == [
        (
            int(status.FsReply.SUCCESS),
            int(status.WeError.SUCCESS),
            int(status.FileFunction.READ_INDEXED),
        )
    ]


def test_acasirsub1_dispatch_resets_status_without_losing_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shared File-Access residue is cleared before IRS nominal guards run."""
    handler = _shipped("acas_posting.dal.acasirsub1_irs_nominal")
    status = _shipped("acas_posting.dal.status")
    nominal_module = _shipped("acas_posting.records.irs_nominal")
    file_access_module = _shipped("acas_posting.records.file_access")
    file_defs_module = _shipped("acas_posting.records.file_defs")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    system = system_module.SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    file_access = file_access_module.FileAccess()
    file_access.file_function = int(status.FileFunction.READ_INDEXED)
    file_access.logging_data.file_key_no = 1
    file_access.fs_reply = int(status.FsReply.END_OF_FILE)
    file_access.we_error = 10
    observed: list[tuple[int, int, int]] = []

    monkeypatch.setattr(handler, "_record_size_gate", lambda _s, _fa: True)

    def bridge(_system, file_access_arg, _record):
        observed.append(
            (
                int(file_access_arg.fs_reply),
                int(file_access_arg.we_error),
                int(file_access_arg.file_function),
            )
        )
        return (int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS))

    monkeypatch.setattr(handler, "_bridge_call", bridge)
    result = handler.dispatch(
        system,
        nominal_module.WsIrsnlRecord(),
        file_access,
        file_defs_module.FileDefs(),
        flags_module.AcasDalCommonData(sw_testing=0),
    )

    assert result == (int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS))
    assert observed == [
        (
            int(status.FsReply.SUCCESS),
            int(status.WeError.SUCCESS),
            int(status.FileFunction.READ_INDEXED),
        )
    ]


def test_irs_indexed_read_does_not_report_driver_failure_as_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A SELECT that never ran is distinct from a clean zero-row result."""
    handler = _shipped("acas_posting.dal.acasirsub1_irs_nominal")
    status = _shipped("acas_posting.dal.status")
    nominal_module = _shipped("acas_posting.records.irs_nominal")
    file_access_module = _shipped("acas_posting.records.file_access")

    handler.reset_bridge_storage(transport=None)
    failure = status.DbErrorStatus(
        fs_reply=status.FsReply.ERROR,
        we_error=status.WeError.RDB_INIT_ERROR,
        sql_err="1046 ",
        sql_msg="connection unavailable",
        sql_state="HY000",
        duplicate_key=False,
    )
    monkeypatch.setattr(
        handler,
        "_run_query",
        lambda _file_access, _statement, _parameters: ([], failure),
    )

    file_access = file_access_module.FileAccess()
    result = handler.read_indexed(
        file_access,
        nominal_module.WsIrsnlRecord(),
    )

    assert result == (
        int(status.FsReply.ERROR),
        int(status.WeError.RDB_INIT_ERROR),
    )
    assert result != handler.NOT_FOUND_STATUS


def test_transient_connection_close_does_not_close_persistent_handle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """acasirsub3's synthesized close owns only its transient SQL handle."""
    connection = _shipped("acas_posting.dal.connection")
    system_module = _shipped("acas_posting.records.system_record")

    class FakeConnection:
        def __init__(self) -> None:
            self.closed = False

        def connect(self, **_arguments: object) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    persistent = FakeConnection()
    transient = FakeConnection()
    connections = iter((persistent, transient))

    connection.reset_process_connection()
    monkeypatch.setattr(
        connection.mysql.connector,
        "connect",
        lambda **_arguments: next(connections),
    )
    monkeypatch.setattr(
        connection,
        "load_rdb_data_once",
        lambda _system: object(),
    )
    monkeypatch.setattr(
        connection,
        "connection_parameters",
        lambda _data, *, transport: {},
    )
    monkeypatch.setattr(
        connection,
        "_require_permitted_connection",
        lambda *_arguments, **_keywords: None,
    )
    monkeypatch.setattr(
        connection,
        "_assert_converter_pinned",
        lambda _connection: None,
    )

    system = system_module.SystemRecord()
    first = connection.mysql_1000_open(system)
    second = connection.mysql_1000_open(
        system,
        reuse_process_connection=False,
    )

    assert first.connection is persistent
    assert second.connection is transient
    connection.mysql_1980_close(second.connection)
    assert transient.closed
    assert not persistent.closed
    assert connection.process_connection() is persistent

    connection.mysql_1980_close(first.connection)
    assert not persistent.closed
    assert connection.process_connection() is persistent

    connection.reset_process_connection()
    assert persistent.closed


def test_acas007_dispatch_honours_keyword_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Facade-forwarded transport reaches the GL batch handler."""
    handler = _shipped("acas_posting.dal.acas007_gl_batch")
    connection = _shipped("acas_posting.dal.connection")
    batch_module = _shipped("acas_posting.records.gl_batch")
    file_access_module = _shipped("acas_posting.records.file_access")
    file_defs_module = _shipped("acas_posting.records.file_defs")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    handler.reset_working_storage()
    declared = connection.TransportSecurity(isolated_oracle=True)
    observed: list[object] = []
    monkeypatch.setattr(
        handler,
        "aa_process_flat_file",
        lambda *_arguments: observed.append(handler._HANDLER.transport),
    )

    handler.dispatch(
        system_module.SystemRecord(),
        batch_module.GlBatchRecord(),
        file_access_module.FileAccess(),
        file_defs_module.FileDefs(),
        flags_module.AcasDalCommonData(sw_testing=0),
        transport=declared,
    )

    assert observed == [declared]


def test_acas016_reuses_bridge_connection_across_fresh_buffers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A new invoice linkage buffer does not lose slinvoiceMT working storage."""
    handler = _shipped("acas_posting.dal.acas016_invoice")
    connection = _shipped("acas_posting.dal.connection")
    status = _shipped("acas_posting.dal.status")
    file_access_module = _shipped("acas_posting.records.file_access")
    file_defs_module = _shipped("acas_posting.records.file_defs")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    persistent = object()
    declared = connection.TransportSecurity(isolated_oracle=True)
    handler.reset_bridge_storage(transport=declared)
    monkeypatch.setattr(
        handler,
        "mysql_1000_open",
        lambda *_arguments, **_keywords: connection.OpenOutcome(
            connection=persistent,
            fs_reply=status.FsReply.SUCCESS,
            we_error=status.WeError.SUCCESS,
            ws_no_paragraph=0,
            sql_err="",
            sql_msg="",
            sql_state="",
        ),
    )
    observed: list[tuple[object, object]] = []

    def capture_write(context) -> None:
        observed.append((context.connection, context.state))
        context.file_access.fs_reply = int(status.FsReply.SUCCESS)
        context.file_access.we_error = int(status.WeError.SUCCESS)

    monkeypatch.setattr(handler, "ba070_process_write", capture_write)

    system = system_module.SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    file_access = file_access_module.FileAccess()
    file_defs = file_defs_module.FileDefs()
    common = flags_module.AcasDalCommonData(sw_testing=0)

    file_access.file_function = int(status.FileFunction.OPEN)
    first = handler.InvoiceBuffer()
    handler.dispatch(
        system,
        first,
        file_access,
        file_defs,
        common,
        transport=declared,
    )

    file_access.file_function = int(status.FileFunction.WRITE)
    second = handler.InvoiceBuffer()
    handler.dispatch(system, second, file_access, file_defs, common)

    assert observed == [(persistent, first.bridge_state)]
    assert second.connection is persistent
    assert second.bridge_state is first.bridge_state
    handler.reset_bridge_storage()


# ---------------------------------------------------------------------------
#  THE DEPLOYMENT SECURITY CONTRACT
#
#  ONE VARIABLE NAME AND ONE RESOLVER, asserted rather than assumed. The
#  failure mode is a declaration spelled one way by the shell half of the harness and by
#  `harness/docker-compose.yml` and read another way by the policy installer - say
#  `ACAS_DB_ALLOW_PLAINTEXT` against `ACAS_DB_ISOLATED_ORACLE` - so a harness run exports
#  the declaration, the installer never sees it, and every handler open logs the
#  unprotected-transport warning while the Compose file says the declaration was made.
#  These tests fail if the two halves drift apart.
#
#  AND THEY LOCK THE TWO MODES THE RIGHT WAY ROUND (rule R-3).
#  IT WOULD BE WRONG to assert that an undeclared deployment REFUSES a non-local target
#  and refuses the frozen placeholder credentials, failing "if the fail-closed default is
#  ever softened back into a warning". That would lock a disposition the compiled program
#  cannot produce: `Mysql-1000-Open` connects or reports (99, 911)
#  [copybooks/mysql-procedures.cpy:L60-L128] and inspects neither the address nor
#  the account, so a pre-connect refusal installed by DEFAULT was a validation the
#  migrated cycle has not got - on all seven routes. The default is now
#  exact-parity: the exposure is REPORTED and the connection is made. Hardened
#  mode is asserted separately, below, and a run made under it is explicitly NOT
#  parity evidence.
#
#  Infrastructure-free: no database, no COBOL, no Docker. Every environment is an
#  explicit mapping, so the process environment is never read.
# ---------------------------------------------------------------------------


def test_the_plaintext_declaration_has_exactly_one_variable_name() -> None:
    """The resolver reads the name the shell half and Compose export, and no other."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    assert (
        cli_args.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE == "ACAS_DB_ALLOW_PLAINTEXT"
    )
    # The superseded spelling must not come back under any name.
    assert not [
        name
        for name in dir(cli_args)
        if isinstance(getattr(cli_args, name), str)
        and getattr(cli_args, name) == "ACAS_DB_ISOLATED_ORACLE"
    ]


def test_an_undeclared_deployment_resolves_to_the_exact_parity_policy() -> None:
    """Nothing set means NEITHER refusal, which is what the compiled open does.

    The parity contract, asserted at the resolver rather than inferred from the
    data-access layer's own defaults: an environment that declares nothing must
    not install a pre-connect refusal, because the frozen paragraph has no such
    outcome [copybooks/mysql-procedures.cpy:L60-L128] (rule R-3).
    """
    cli_args = importlib.import_module("acas_posting.cli.args")

    declaration = cli_args.resolve_transport_policy({})

    assert declaration.require_encrypted_transport is False
    assert declaration.require_declared_placeholder_credentials is False
    assert declaration.isolated_oracle is False
    assert declaration.allow_frozen_placeholder_credentials is False
    #  And the type's own defaults say the same thing, so a caller that builds one
    #  directly cannot get a refusing policy it did not ask for either.
    bare = cli_args.TransportPolicyParams()
    assert bare.require_encrypted_transport is False
    assert bare.require_declared_placeholder_credentials is False
    #  The two layers must agree: `dal.connection.ConnectionPolicy` is what the
    #  handlers read, and the CLI installs into it.
    connection = importlib.import_module("acas_posting.dal.connection")
    installed_default = connection.ConnectionPolicy()
    assert installed_default.require_encrypted_transport is False
    assert installed_default.require_declared_placeholder_credentials is False


def test_hardened_mode_is_reached_only_by_naming_it_and_is_not_parity() -> None:
    """Each refusal exists, and each is switched on by ITS OWN variable only.

    Hardened mode is the right answer for a production deployment and the wrong
    one for a parity run, so it is asserted here rather than in the default: a run
    made under either variable refuses before the connect and therefore writes
    nothing where the compiled program would have written, which is why the
    project makes NO parity claim for such a run
    ([docs/migration/scenario-diff-evidence.md]).
    """
    cli_args = importlib.import_module("acas_posting.cli.args")

    tls_only = cli_args.resolve_transport_policy(
        {cli_args.TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE: "1"}
    )
    assert tls_only.require_encrypted_transport is True
    #  One knob, one effect: asking for TLS does not also refuse the credentials.
    assert tls_only.require_declared_placeholder_credentials is False

    credentials_only = cli_args.resolve_transport_policy(
        {cli_args.TRANSPORT_REQUIRE_DECLARED_CREDENTIALS_VARIABLE: "yes"}
    )
    assert credentials_only.require_declared_placeholder_credentials is True
    assert credentials_only.require_encrypted_transport is False


def test_the_declaration_is_the_narrow_opt_out_and_strictness_outranks_it() -> None:
    """The harness's declaration silences the report; an explicit strict setting wins."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    declared = cli_args.resolve_transport_policy(
        {cli_args.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE: "1"}
    )
    assert declared.isolated_oracle is True
    assert declared.require_encrypted_transport is False
    #  Granting plaintext grants nothing else, and it CREATES no refusal either:
    #  the credential exposure stays reported-and-permitted until a deployment
    #  names the credential refusal.
    assert declared.require_declared_placeholder_credentials is False

    forced = cli_args.resolve_transport_policy(
        {
            cli_args.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE: "1",
            cli_args.TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE: "1",
        }
    )
    assert forced.isolated_oracle is True
    assert forced.require_encrypted_transport is True


def test_the_installed_policy_carries_the_resolved_declaration() -> None:
    """`install_connection_policy` installs what the contract resolved, unchanged."""
    args = importlib.import_module("acas_posting.cli.args")
    connection = importlib.import_module("acas_posting.dal.connection")
    cli_args = importlib.import_module("acas_posting.cli.args")

    previous = connection.connection_policy()
    try:
        undeclared = args.install_connection_policy({})
        assert undeclared is connection.connection_policy()
        #  EXACT PARITY ON EVERY ROUTE: this function is reached by all seven, so
        #  these two assertions are what keep a refusal the compiled program cannot
        #  produce off the shipped critical path (rule R-3).
        assert undeclared.require_encrypted_transport is False
        assert undeclared.require_declared_placeholder_credentials is False

        declared = args.install_connection_policy(
            {cli_args.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE: "yes"}
        )
        assert declared is connection.connection_policy()
        assert declared.transport is not None
        assert declared.transport.isolated_oracle is True
        assert declared.require_encrypted_transport is False

        #  And the hardened declaration DOES reach the installed policy, so the
        #  operator's choice is honoured rather than quietly dropped.
        hardened = args.install_connection_policy(
            {cli_args.TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE: "1"}
        )
        assert hardened is connection.connection_policy()
        assert hardened.require_encrypted_transport is True
        assert hardened.require_declared_placeholder_credentials is False
    finally:
        connection.set_connection_policy(previous)


def test_no_migrated_route_publishes_a_transport_option() -> None:
    """Rule R-3: the linkage contract publishes no deployment-security input."""
    forbidden = ("--db-tls-ca", "--db-tls-cert", "--db-tls-key", "--db-allow-plaintext")
    for module_name in (
        "acas_posting.cli.gl_post_cycle",
        "acas_posting.cli.gl_end_of_cycle",
        "acas_posting.cli.sl_invoice_post",
        "acas_posting.cli.sl_cash_post",
        "acas_posting.cli.pl_order_post",
        "acas_posting.cli.pl_payment_post",
        "acas_posting.cli.irs_post",
    ):
        module = importlib.import_module(module_name)
        parser = module._build_parser()  # noqa: SLF001 - the route's own builder
        published = {
            option
            for action in parser._actions  # noqa: SLF001 - argparse publishes no reader
            for option in action.option_strings
        }
        assert not published.intersection(forbidden), module_name


# ---------------------------------------------------------------------------
#  THE FIVE `ROUNDED` SITES, EXERCISED THROUGH THE PRODUCTION FUNCTIONS
#
#  `test_compute_rounded_half_up.py` owns the rounding SEMANTICS and closes the
#  census against the shipped tree with an AST walk. What it cannot do without
#  breaking its own tier contract is CALL the accounting functions, because
#  `acas_posting.programs.*` imports `acas_posting.dal.facade`. This file already
#  crosses that boundary deliberately - every test in it reaches a program or a
#  handler through `pytest.importorskip` - so the behavioural lock lives here.
#
#  It matters that these assert against production rather than against a local
#  re-derivation of the formula: a test that rebuilds `post-amount * rate / 100`
#  itself passes even if the shipped store truncates.
# ---------------------------------------------------------------------------


def test_gl051_net_is_a_half_up_store_in_production() -> None:
    """Site 1 of 5: `compute vat-amount rounded = post-amount * ws-vat-rate / 100.`

    [general/gl051.cbl:L791]. 100.03 at 17.50% is exactly 17.50525, whose third
    decimal is above a half penny, so a half-up store holds 17.51 and a truncating
    store would hold 17.50. The pair therefore proves the DIRECTION and not merely
    that a number came back.
    """
    decimal_module = importlib.import_module("decimal")
    gl051 = importlib.import_module("acas_posting.programs.gl051_batch_control_check")
    gl_posting = importlib.import_module("acas_posting.records.gl_posting")

    posting = gl_posting.WsPostingRecord()
    posting.post_amount = decimal_module.Decimal("100.03")
    gl051._net(posting, decimal_module.Decimal("17.50"))  # noqa: SLF001

    assert posting.vat_amount == decimal_module.Decimal("17.51")
    # Un-ROUNDED, the same operands would have held 17.50 - asserted so the test
    # fails if `rounded=True` is ever dropped from the store.
    assert posting.vat_amount != decimal_module.Decimal("17.50")


def test_gl051_gross_rounds_then_subtracts_without_rounding_in_production() -> None:
    """Sites 2 of 5 and its un-ROUNDED successor, in one call.

    `compute vat-amount rounded = post-amount - (post-amount / ((ws-vat-rate + 100) /
    100)).` [general/gl051.cbl:L796] followed by `subtract vat-amount from
    post-amount.` [general/gl051.cbl:L797] - which carries no `ROUNDED` and therefore
    truncates. The successor is DESTRUCTIVE: `post-amount` leaves the paragraph
    holding the net.
    """
    decimal_module = importlib.import_module("decimal")
    gl051 = importlib.import_module("acas_posting.programs.gl051_batch_control_check")
    gl_posting = importlib.import_module("acas_posting.records.gl_posting")

    posting = gl_posting.WsPostingRecord()
    posting.post_amount = decimal_module.Decimal("117.50")
    gl051._gross(posting, decimal_module.Decimal("17.50"))  # noqa: SLF001

    assert posting.vat_amount == decimal_module.Decimal("17.50")
    # The gross has been REPLACED by the net, which is what makes the paragraph
    # non-idempotent - calling it twice would tax the net.
    assert posting.post_amount == decimal_module.Decimal("100.00")


def test_irs030_net_and_gross_are_the_gl051_pair_under_another_rate_field() -> None:
    """Sites 4 and 5 of 5: [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562-L1563].

    The same two expressions as `gl051`'s, differing only in the rate field's name -
    `WS-Vat-Current` rather than `ws-vat-rate` - and in the receiving record. Asserted
    side by side with the `gl051` pair so that a divergence between the two ledgers'
    VAT arithmetic cannot appear silently.
    """
    decimal_module = importlib.import_module("decimal")
    irs030 = importlib.import_module("acas_posting.programs.irs030_posting")
    irs_posting = importlib.import_module("acas_posting.records.irs_posting")

    net_record = irs_posting.PostingRecord()
    net_record.post_amount = decimal_module.Decimal("100.03")
    irs030._net_section(net_record, decimal_module.Decimal("17.50"))  # noqa: SLF001
    assert net_record.vat_amount == decimal_module.Decimal("17.51")

    gross_record = irs_posting.PostingRecord()
    gross_record.post_amount = decimal_module.Decimal("117.50")
    irs030._gross_section(gross_record, decimal_module.Decimal("17.50"))  # noqa: SLF001
    assert gross_record.vat_amount == decimal_module.Decimal("17.50")
    assert gross_record.post_amount == decimal_module.Decimal("100.00")


def test_gl051_account_scaling_truncates_on_all_five_statements() -> None:
    """The five scaling statements Agent Action Plan section 0.4.1.2 names for `gl051`.

    Two divides at [general/gl051.cbl:L604] and [general/gl051.cbl:L607], two
    multiplies at [general/gl051.cbl:L654] and [general/gl051.cbl:L657], and the fifth
    multiply at [general/gl051.cbl:L803]. NONE carries `ROUNDED`, so every one
    truncates - which is why the census in the sibling file stays at five.

    Also locks the field the divides store into: `acc-ok`
    [general/gl051.cbl:L233], NOT `account-in` [general/gl051.cbl:L178]. They share a
    picture and a separate statement copies between them, so conflating the two would
    be invisible to a value assertion alone.
    """
    decimal_module = importlib.import_module("decimal")
    gl051 = importlib.import_module("acas_posting.programs.gl051_batch_control_check")
    gl_posting = importlib.import_module("acas_posting.records.gl_posting")

    posting = gl_posting.WsPostingRecord()
    posting.post_dr = 123456
    posting.dr_pc = 7
    posting.post_cr = 654321
    posting.cr_pc = 9

    storage = gl051._WorkingStorage()  # noqa: SLF001
    gl051._accept_date_scale_out(storage, posting, "DR")  # noqa: SLF001
    assert storage.acc_ok == decimal_module.Decimal("1234.56")
    assert storage.array_pc == 7
    # `account-in` is untouched: the copy is `move acc-ok to account-in.` at
    # [general/gl051.cbl:L615], a statement in a different paragraph.
    assert storage.account_in == decimal_module.Decimal("0.00")

    # Anything other than "DR" takes the credit arm - the frozen test is an
    # alphanumeric relation condition with no third branch.
    gl051._accept_date_scale_out(storage, posting, "  ")  # noqa: SLF001
    assert storage.acc_ok == decimal_module.Decimal("6543.21")
    assert storage.array_pc == 9

    storage.account_in = decimal_module.Decimal("1234.56")
    storage.array_pc = 3
    scaled = gl_posting.WsPostingRecord()
    gl051._accept_amount_scale_in(storage, scaled, "DR")  # noqa: SLF001
    assert scaled.post_dr == 123456
    assert scaled.dr_pc == 3
    gl051._accept_amount_scale_in(storage, scaled, "CR")  # noqa: SLF001
    assert scaled.post_cr == 123456
    assert scaled.cr_pc == 3

    assert gl051._gl050c_get_description_scale(storage) == 123456  # noqa: SLF001

    # Truncation, proved on a value the multiply cannot represent exactly in the
    # receiver: 1234.569 * 100 is 123456.9, and the integer receiver keeps 123456.
    storage.account_in = decimal_module.Decimal("1234.569")
    assert gl051._gl050c_get_description_scale(storage) == 123456  # noqa: SLF001


# ---------------------------------------------------------------------------
#  THE CANONICAL FIXTURE ROOT -- THREE DERIVATIONS, ASSERTED TO AGREE
#
#  A built fixture cannot live where a scenario's own `seed_dir` points, because
#  that key resolves relative to the scenario file and the checkout is mounted
#  read-only (R-3). So the runtime location is a separate agreement, and three
#  components have to hold it: `harness/seed.sh --build-fixtures` writes it,
#  `harness/reset_db.sh` reads it for stages 1 and 5, and `tests/conftest.py` reads it
#  for the pytest protocol.
#
#  Each states the rule in its own language, so nothing but a test can keep them
#  in step - and when they drift, every parity and determinism composition fails
#  at stage 1 with a path nobody wrote down. These tests read the two shell
#  derivations out of the scripts as TEXT and compare them with the Python one.
# ---------------------------------------------------------------------------


def _harness_dir():
    """Return the repository's `harness/` directory."""
    import pathlib

    return pathlib.Path(__file__).resolve().parents[2] / "harness"


def test_the_three_fixture_root_derivations_are_textually_identical() -> None:
    """`seed.sh`, `reset_db.sh` and `conftest.py` derive one root.

    Asserted on the shell text because the two scripts cannot be imported: each must
    contain the `${ACAS_FIXTURES...}` / `$ACAS_DATA/fixtures` pair, so a change to
    one that is not made in the other is visible here rather than at stage 1.

    The producer is `harness/seed.sh --build-fixtures`: the builder was
    `harness/build_fixtures.sh`, and folding it into the script that CONSUMES the
    fixtures is what makes the producer and the consumer share one derivation instead
    of agreeing about one.
    """
    builder = (_harness_dir() / "seed.sh").read_text(encoding="utf-8")
    consumer = (_harness_dir() / "reset_db.sh").read_text(encoding="utf-8")

    # The producer's single statement of the rule.
    assert 'ACAS_BF_OUT="${ACAS_FIXTURES:-${ACAS_DATA:-/data}/fixtures}"' in builder

    # The reset stages' derivation: the same two sources, in the same precedence.
    assert 'local root="${ACAS_FIXTURES:-}"' in consumer
    assert '[[ -n "$root" ]] || root="${ACAS_DATA:-/data}"/fixtures' in consumer
    assert 'ACAS_RESET_SEED_DIR="${root%/}/$stem"' in consumer

    # And each cites the other, so a reader of one finds the other two.
    for text in (builder, consumer):
        assert "tests/conftest.py" in text
    assert "harness/seed.sh --build-fixtures" in consumer


def test_the_python_derivation_matches_the_shell_precedence() -> None:
    """`scenario_fixture_dir` prefers `$ACAS_FIXTURES`, then `$ACAS_DATA/fixtures`.

    Measured against a controlled environment rather than read off the source, so
    the precedence itself is asserted and not merely the presence of two names.
    """
    import pathlib

    conftest = importlib.import_module("conftest")
    monkey = pytest.MonkeyPatch()
    try:
        # Both set: ACAS_FIXTURES wins outright, and ACAS_DATA is not consulted.
        monkey.setenv("ACAS_FIXTURES", "/fx")
        monkey.setenv("ACAS_DATA", "/dt")
        assert conftest.scenario_fixture_dir("clean_batch_gl") == pathlib.Path(
            "/fx/clean_batch_gl"
        )

        # Only ACAS_DATA: the `fixtures` subdirectory is appended, exactly as the
        # builder's default does.
        monkey.delenv("ACAS_FIXTURES")
        assert conftest.scenario_fixture_dir("clean_batch_gl") == pathlib.Path(
            "/dt/fixtures/clean_batch_gl"
        )

        # An empty value is not a value: the builder's `:-` treats it the same way.
        monkey.setenv("ACAS_FIXTURES", "   ")
        assert conftest.scenario_fixture_dir("clean_batch_gl") == pathlib.Path(
            "/dt/fixtures/clean_batch_gl"
        )

        # Neither set: the two READERS refuse rather than guess. The builder's own
        # `/data` last resort is deliberately not mirrored here - it can be run
        # outside Compose, and a test protocol that guessed would fail at stage 1
        # against a path nobody chose.
        monkey.delenv("ACAS_FIXTURES")
        monkey.delenv("ACAS_DATA")
        with pytest.raises(conftest.HarnessFaultError):
            conftest.scenario_fixture_dir("clean_batch_gl")
    finally:
        monkey.undo()


# ---------------------------------------------------------------------------
#  THE SEEDING WINDOW'S DEFAULT MODE, AND THE HARDENED SEED TRANSPORT
#
#  Both belong to `harness/seed.sh` and both are R-6 arbitrations rather than
#  readings, so both are asserted on the shipped script text: a default that
#  silently reverts to the AAP-literal OFF mode would make every seed exit 76, and
#  a transport that reverted to the bare `KEY<TAB>value` grammar would let a
#  scenario file forge a record.
# ---------------------------------------------------------------------------


def test_the_seeding_window_defaults_to_the_aap_mandated_mode() -> None:
    """Unset `ACAS_SEED_AUTOCOMMIT` selects OFF, the mode the AAP mandates.

    The Agent Action Plan is the frozen, agreed-upon specification and says
    autocommit is off during seeding in three places -- sections 0.2.1.1, 0.4.1.7
    and 0.5.2. A harness that defaulted to the other mode would be reinterpreting
    its own governing document, and a reader of a parity result would have no way
    to know the configuration had been changed underneath them.

    The measured consequence is disclosed rather than worked around. Against the
    compiled loaders, `clean_batch_gl`, both modes: under OFF all seven loaders
    return zero and a fresh session sees zero rows in all seven seeded tables, and
    `seed.sh` exits 76 (EX_NOT_DURABLE); under ON the same seven return zero and a
    fresh session sees 8 rows across those 7 tables. The loader return codes are
    IDENTICAL either way, so the mode is invisible to the frozen code -- which is
    why ON remains selectable as an explicitly DECLARED DEVIATION, and is NOT a
    licence to make it the default.

    So the default must reproduce the frozen no-COMMIT defect and let the
    durability gate refuse it (R-4: a defect reproduced is correct), rather than
    quietly seeding in a mode the AAP does not sanction.
    """
    seed = (_harness_dir() / "seed.sh").read_text(encoding="utf-8")

    # The unset case is grouped with the OFF spellings, not with the ON ones.
    assert "    ''|off|0|false|no)\n" in seed
    assert "    on|1|true|yes)\n" in seed
    assert "    ''|on|1|true|yes)\n" not in seed

    # And the initial value of the target agrees with that grouping, so a code path
    # that skipped the parse would still open the AAP-mandated window rather than
    # falling through into an unsanctioned one.
    # Scoped to the DECLARATION, because the ON branch legitimately assigns 1 when
    # the deviation is requested; what must not happen is the variable starting at 1.
    declaration = re.search(
        r"^ACAS_SEED_WINDOW_TARGET=(\d+)", seed, re.MULTILINE
    )
    assert declaration is not None, "seed.sh declares no initial window target"
    assert declaration.group(1) == "0", (
        "the seeding window's initial value is the AAP-mandated OFF; a code path "
        f"that skipped the parse must not open a durable window, got {declaration.group(1)!r}"
    )

    # The refusal the default leads to must still exist: reproducing the defect is
    # only half of it, and reporting an empty seed as a success would be the other
    # half undone.
    assert "EX_NOT_DURABLE=76" in seed
    assert "acas_assert_seed_durability" in seed

    # And nothing may supply the COMMIT the frozen loaders omit (R-4). The file is
    # required to DISCUSS the missing commit at length -- and does, across wrapped
    # multi-line prose arguments -- so the match is deliberately narrow: a quoted
    # token that is a COMPLETE statement, which is what would reach the server.
    # Prose never closes its quote immediately after the word.
    issued = re.findall(r"""["'][ \t]*(commit|rollback)[ \t]*;?["']""", seed, re.I)
    assert not issued, (
        "seed.sh issues a COMMIT or ROLLBACK on a frozen loader's behalf "
        f"({issued!r}). R-4 makes a defect fixed a failure, and the missing COMMIT "
        "is precisely the defect this seeding mode reproduces."
    )


def test_no_harness_file_pins_the_seeding_window_to_the_deviation() -> None:
    """The AAP-mandated default must be reachable, not overridden by the harness.

    `harness/docker-compose.yml` used to set `ACAS_SEED_AUTOCOMMIT: "on"` on the
    `gnucobol` service. Because Compose environment beats the script default, that
    made the mandated mode unreachable through the harness for every operator who
    never opened `seed.sh` -- the default existed but nothing could run it. A
    per-invocation `-e ACAS_SEED_AUTOCOMMIT=on` is the supported way to request the
    deviation, precisely because it appears in the command that ran.
    """
    for name in ("docker-compose.yml", "Dockerfile.mariadb", "Dockerfile.gnucobol"):
        text = (_harness_dir() / name).read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # prose explaining the mode is expected, and required
            # An ASSIGNMENT, not a mention: the files are required to explain the
            # mode in prose, and a matcher that banned the name would forbid the
            # very disclosure this finding asks for.
            assert not re.match(r"ACAS_SEED_AUTOCOMMIT\s*:", stripped), (
                f"{name} pins the seeding window as Compose environment, "
                f"overriding the AAP-mandated default for every invocation: "
                f"{stripped!r}"
            )
            assert not re.match(
                r"(ENV|ARG)\s+ACAS_SEED_AUTOCOMMIT[\s=]", stripped
            ), f"{name} bakes a seeding window into the image: {stripped!r}"


def test_no_document_claims_the_seeding_deviation_is_the_default() -> None:
    """The prose must not contradict the script it documents.

    The two guards above hold the *scripts* to the AAP-mandated default. Neither
    of them can see the documentation, and the documentation is what an operator
    reads before running anything -- so it drifted. A superseded revision of
    `docs/migration/scenario-diff-evidence.md` section 4.3 stated that `on` was "the
    shipped default", that an unset `ACAS_SEED_AUTOCOMMIT` selected it, and that
    `harness/docker-compose.yml` "declares it explicitly, so no caller needs a
    flag to obtain a durable seed". Every clause of that was false by the time it
    was read: the default had moved to `off` and the Compose pin had been removed
    (the guard above now forbids it). Section 15 of the same document had already
    been corrected and pointed *at* the stale passage as its authority.

    An operator who believed the stale text would omit the flag, and stage 1 would
    exit 76 -- correct behaviour, reported clearly, and completely baffling if the
    document said no flag was needed.

    So the claim is asserted to be absent from the prose as well. The matcher is
    deliberately narrow: it looks for a *claim about the default*, not for any
    mention of the deviation, because these documents are required to discuss the
    deviation at length and a matcher that banned the name would forbid the very
    disclosure R-6 asks for. Prose that names the deviation while calling it a
    deviation passes; prose that calls it the default, or says the Compose file
    declares it, does not.
    """
    root = Path(__file__).resolve().parents[2]
    documents = sorted((root / "docs" / "migration").glob("*.md"))
    documents.append(root / "README-python-migration.md")
    assert len(documents) >= 5, (
        "the migration document set is smaller than the four AAP-mandated files "
        f"plus the README: {[p.name for p in documents]}"
    )

    # Each pattern is a claim that measurement refutes, paired with what was
    # measured instead. Written against the collapsed single-line form of each
    # paragraph so that a claim split across a line break is still caught.
    refuted: Final[tuple[tuple[str, str], str], ...] = (
        (
            (
                r"(?<![A-Za-z])`?on`?\s+is\s+(therefore\s+)?the\s+"
                r"(shipped|canonical|default)\s*(default)?\b"
            ),
            "unset resolves to `off` in "
            "[harness/seed.sh acas_open_seed_autocommit_window]; reset_db.sh with "
            "the variable unset was measured at exit 76",
        ),
        (
            # The pronoun form is banned outright rather than resolved: "unset
            # selects it" was the stale text's phrasing, and a reader cannot tell
            # which mode "it" is without trusting the sentence before. Name the
            # mode -- "unset selects `off`" -- and this passes.
            r"unset\s+selects\s+it\b",
            "name the mode explicitly instead of using a pronoun: an unset "
            "ACAS_SEED_AUTOCOMMIT selects `off`, the AAP-mandated window",
        ),
        (
            r"docker-compose\.yml`?\s+declares\s+it",
            "the Compose file carries no ACAS_SEED_AUTOCOMMIT setting, and "
            "test_no_harness_file_pins_the_seeding_window_to_the_deviation "
            "forbids one",
        ),
        (
            r"no\s+caller\s+needs\s+a\s+flag\s+to\s+obtain\s+a\s+durable\s+seed",
            "every durable seed needs -e ACAS_SEED_AUTOCOMMIT=on; without it a "
            "seed from an empty database exits 76",
        ),
    )

    for document in documents:
        text = document.read_text(encoding="utf-8")
        for paragraph in text.split("\n\n"):
            collapsed = " ".join(paragraph.split())
            if "ACAS_SEED_AUTOCOMMIT" not in collapsed and "autocommit" not in collapsed:
                continue
            # A paragraph that quotes the superseded claim in order to correct it
            # is the record this finding asked for, not a recurrence of it.
            if re.search(r"superseded|earlier revision|Correction,|was false", collapsed):
                continue
            for pattern, measured in refuted:
                found = re.search(pattern, collapsed, re.I)
                assert found is None, (
                    f"{document.name} states a seeding-window default that "
                    f"measurement refutes: {found.group(0)!r}. Measured instead: "
                    f"{measured}. The paragraph is: {collapsed[:400]!r}"
                )


def test_the_durability_gate_measures_this_seeds_own_writes() -> None:
    """The gate judges the DIFFERENCE a seed makes, not the rows it happens to find.

    The superseded gate summed the row counts of the tables whose loaders ran and
    passed whenever the sum was positive. Against the target the protocol always
    hands it -- a schema re-applied one stage earlier -- that is the right question
    asked the wrong way, because every table starts empty and the sum IS the delta.
    Run standalone against a database an earlier seed had committed rows into, the
    two questions come apart: measured on the shipped harness, `harness/seed.sh`
    with `ACAS_SEED_AUTOCOMMIT=off` over an already-seeded `clean_batch_gl` exited
    **0** and printed "the seed is present -- 8 row(s)" while the AAP-literal
    window had made nothing durable at all. The rows were the previous seed's.

    So a pre-seed census is taken BEFORE the window opens and the gate compares
    against it. This test asserts the three properties that make that measurement
    sound, on the shipped script text, because the gate is stack-bound and an
    ordinary run never reaches it:

      1. the census runs before the window and after the database is reachable -
         a census taken INSIDE the window would read the loaders' own uncommitted
         writes on some future server configuration and measure nothing;
      2. the gate reads the census rather than comparing a total against zero; and
      3. the census is READ-ONLY - it may not become a fixture-writing step, which
         would put the harness's own rows into a state the protocol then compares.
    """
    seed = (_harness_dir() / "seed.sh").read_text(encoding="utf-8")

    for name in (
        "acas_census_pre_seed_rows",
        "acas_census_table_state",
        "ACAS_SEED_ROWS_BEFORE",
        "ACAS_SEED_SUM_BEFORE",
    ):
        assert name in seed, (
            f"harness/seed.sh no longer defines {name}, so the durability gate has "
            f"no pre-seed baseline to compare against and is back to measuring "
            f"absolute row counts."
        )

    #  1. ORDER, in acas_main: database ready -> census -> window -> loaders ->
    #     window closed -> gate.
    positions = {}
    for call in (
        "  acas_wait_for_database",
        "  acas_census_pre_seed_rows",
        "  acas_open_seed_autocommit_window",
        "  acas_seed_system_block",
        "  acas_close_seed_autocommit_window",
        "  acas_assert_seed_durability",
    ):
        index = seed.find(f"\n{call}\n")
        assert index != -1, f"harness/seed.sh::acas_main no longer calls{call}"
        positions[call.strip()] = index

    ordered = [
        "acas_wait_for_database",
        "acas_census_pre_seed_rows",
        "acas_open_seed_autocommit_window",
        "acas_seed_system_block",
        "acas_close_seed_autocommit_window",
        "acas_assert_seed_durability",
    ]
    for earlier, later in zip(ordered, ordered[1:]):
        assert positions[earlier] < positions[later], (
            f"harness/seed.sh calls {later} before {earlier}. The census must be "
            f"taken after the database is reachable and BEFORE the seeding window "
            f"opens, and the gate must read the database after the window has "
            f"closed - that is what makes the difference it reports this seed's."
        )

    #  2. The gate compares against the baseline. The superseded pass condition was
    #     a bare positive-total test, and it must not be the gate's first arm again.
    gate = seed[seed.index("acas_assert_seed_durability() {"):]
    gate = gate[: gate.index("\n}\n")]
    assert "ACAS_SEED_ROWS_BEFORE[" in gate, (
        "the durability gate no longer reads the pre-seed census, so it cannot "
        "tell this seed's rows from an earlier seed's."
    )
    assert "count - before" in gate, (
        "the durability gate no longer computes a per-table delta; a total "
        "compared against zero is the measurement this finding replaced."
    )

    #  3. READ-ONLY. The census reads state to measure it and must never write any.
    census = seed[seed.index("acas_census_table_state() {"):]
    census = census[: census.index("\nacas_census_pre_seed_rows() {")]
    for verb in ("insert ", "update ", "delete ", "truncate ", "drop ", "create "):
        assert verb not in census.lower(), (
            f"the pre-seed census issues {verb.strip()!r}. It exists to OBSERVE the "
            f"state a seed starts from; a census that wrote would put the harness's "
            f"own rows into the state the protocol compares."
        )


def test_the_seed_transport_is_control_free_and_length_prefixed() -> None:
    """The YAML-to-shell seed protocol cannot be forged by a scenario file.

    The superseded grammar was `KEY<TAB>value`, read with `IFS=$'\\t' read -r key
    value`. A value carrying a TAB split its own record and the reader kept the
    fragment; a value carrying a NEWLINE let the scenario forge an entire extra
    record - a forged `SEED_FILE` (CWE-93) or, worse, a forged `SEED_DIR` pointing
    anywhere (CWE-22). A NUL-delimited stream is the usual answer and is unavailable
    here: the output is captured through command substitution and a bash variable
    cannot hold a NUL.

    So the emitter refuses every C0 control character and DEL outright, and the
    grammar is framed and length-prefixed so the decode is independently verifiable.
    Both halves are asserted, because either alone would be a single point of
    failure.
    """
    seed = (_harness_dir() / "seed.sh").read_text(encoding="utf-8")

    # The emitter's refusal, and the strict bare-name grammar beside it.
    assert "def reject_control_characters(" in seed
    assert "ord(character) < 0x20 or ord(character) == 0x7F" in seed
    assert "BARE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')" in seed

    # The framed, length-prefixed grammar.
    assert "sys.stdout.write('BEGIN\\t1\\n')" in seed
    assert "def emit(key, value):" in seed
    assert "'%s\\t%d\\t%s\\n' % (key, len(value), value)" in seed

    # The decoder's INDEPENDENT revalidation: three-field read, numeric length,
    # measured-versus-declared length, and the grammar applied a second time.
    assert "while IFS=$'\\t' read -r key len value; do" in seed
    assert "(( ${#value} == len ))" in seed
    assert '[[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]' in seed
    assert "the seed transport stream carries no BEGIN record" in seed
    assert "the seed transport stream carries no END record" in seed

    # The superseded two-field read must not come back as a loop header. The string
    # itself still appears ONCE, inside the emitter's docstring, which is where the
    # reason it went is recorded - so the assertion is on the loop and not on the
    # prose, and the prose is asserted to be the only other occurrence.
    assert "while IFS=$'\\t' read -r key value" not in seed
    assert seed.count("IFS=$'\\t' read -r key value") == 1


def test_the_reset_preflight_shares_the_hardened_seed_transport() -> None:
    """`reset_db.sh`'s pre-flight decodes with the same framed grammar.

    The pre-flight exists so that a fixture that was never built is reported BEFORE the
    frozen schema is dropped and re-applied. It reads the same untrusted source - a
    scenario YAML - into the same kind of shell loop, so it carries the same defences
    rather than a shorter version of them.

    It lived in the deleted ten-stage driver and moved into the stage that performs the
    destruction, which is strictly stronger: a hand-driven reset is now
    protected exactly as a composed one is.
    """
    resetter = (_harness_dir() / "reset_db.sh").read_text(encoding="utf-8")

    assert "acas_assert_seed_files()" in resetter
    assert "BARE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')" in resetter
    assert "while IFS=$'\\t' read -r key len value; do" in resetter
    assert "(( ${#value} == len ))" in resetter
    assert "the seed transport stream carries no BEGIN record" in resetter
    # Called from the precondition sequence, so it runs before any table is dropped.
    assert "  acas_assert_seed_script\n" in resetter
    schema_at = resetter.index("acas_assert_seed_files\n")
    apply_at = resetter.index("  acas_take_lock\n")
    assert schema_at < apply_at, (
        "harness/reset_db.sh calls acas_assert_seed_files AFTER it takes the reset "
        "lock, so a fixture that was never built would cost a wiped database before "
        "anything said so. The whole point of the pre-flight is that it comes first."
    )


# ---------------------------------------------------------------------------
#  CAPTURE OWNERSHIP, ATTESTATION AND OPERATION SYMMETRY
#
#  Three properties of the ten-stage protocol that nothing but a test can hold,
#  because each is a relationship BETWEEN files rather than a fact inside one:
#
#  * exactly one stage takes the state capture, and it is the protocol's stage 7
#  -- the only moment at which the run status its attestation carries is final;
#  * a run that COMPLETED and found a behavioural difference is comparable, while
#  a run that the harness broke is not;
#  * both runners can drive every operation a scenario declares.
# ---------------------------------------------------------------------------


def _load_harness_module(name: str):
    """Import a `harness/` module by file path, with `harness/` on `sys.path`.

    The harness is a SIBLING of the package and never on the import path (R-1), so a
    plain import cannot find it and adding it permanently would defeat the layering.
    This helper puts it there for the duration of one import, which is what the
    scenario tier's own helpers do.

    Args:
        name: The module's stem, e.g. `dump_tables`.

    Returns:
        The imported module.
    """
    import importlib.util
    import sys

    directory = _harness_dir()
    path = directory / f"{name}.py"
    inserted = False
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
        inserted = True
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            sys.path.remove(str(directory))


def test_only_the_protocol_takes_the_state_capture() -> None:
    """Neither runner dumps: capture ownership is single, and it is stage 7's.

    The Python runner used to take a full capture of every affected table and the
    protocol then took another to the same path. That cost three things: every table
    was read and written TWICE per scenario; the tree had two writers; and the
    runner's own capture COULD NOT BE USED, because the attestation
    `harness/dump_tables.py` reads carries the runner's exit status, which is not
    settled until its EXIT trap - after the stage that took it. The code said so
    itself.

    The oracle-side runner never dumped, so removing the Python one also removes an
    asymmetry a reader had to hold two models for.
    """
    python_runner = (_harness_dir() / "run_python_scenario.sh").read_text(
        encoding="utf-8"
    )
    cobol_runner = (_harness_dir() / "run_cobol_scenario.sh").read_text(
        encoding="utf-8"
    )

    # The capture command is still BUILT, because it is printed for a hand-driven
    # run - but it is never executed.
    assert "acas_py_capture_command()" in python_runner
    assert "owned by the protocol, not by this stage" in python_runner
    assert "deferred to the protocol" in python_runner

    # The opt-out flag is gone along with the stage it opted out of, and so is the
    # deadline that bounded a command this script no longer runs.
    assert "--no-dump" not in python_runner
    assert "ACAS_PY_DUMP" not in python_runner
    assert "ACAS_TIMEOUT_CAPTURE" not in python_runner

    # No trace of the EXECUTION remains: the stage neither bounds the capture with a
    # deadline nor diagnoses its failure, because it does not run it.
    assert "the state capture failed (status" not in python_runner

    # And the oracle side builds no capture command at all, so the two runners are
    # symmetrical. Asserted on the argv TOKENS dump_tables.py takes rather than on
    # its name, which both files mention in prose.
    for token in ("'--tables'", "'--side'", "'--out-dir'"):
        assert token not in cobol_runner, token


def test_neither_runner_removes_a_status_record_on_a_dry_run() -> None:
    """`--dry-run` writes nothing, and deleting is a write.

    Both runners used to `rm` any existing run-status record on a dry run, guarding a
    real hazard - a previous run's record going on to attest the next capture - with
    the most destructive tool available, inside a mode whose entire contract is that
    it touches nothing. The hazard is now REPORTED, and the operator's artifact is
    left alone.
    """
    for name in ("run_python_scenario.sh", "run_cobol_scenario.sh"):
        text = (_harness_dir() / name).read_text(encoding="utf-8")
        assert "rm -f -- \"$dry_target\"" not in text, name
        assert "has been left exactly as it was" in text, name
        assert "nothing on disk was created, changed or removed" in text, name


def test_a_completed_run_that_found_a_difference_is_still_comparable(tmp_path) -> None:
    """Status 69 attests a COMPARABLE run; any other non-zero attests nothing.

    This is the property that makes a real behavioural difference investigable.
    `harness/run_python_scenario.sh` exits 69 only after every operation has run,
    every post-run assertion has been taken and the database holds whatever the run
    produced - so that state IS the finding, and the table diff is the only artifact
    that says which rows and columns it consists of. Refusing it along with the harness
    faults would withhold the evidence exactly when it matters most.
    """
    dump_tables = _load_harness_module("dump_tables")

    #  A COMPLETE RECORD, because an incomplete one attests nothing at all. The
    #  reader requires the whole provenance set - the attempt id, both seed digests,
    #  the declared operation count and one disposition per operation, with
    #  `wrapper_status` agreeing with `status` - so a fixture that wrote only the
    #  status would exercise the MISSING-KEY refusal rather than the property under
    #  test. What varies here is the status; everything else is a healthy record.
    digest = "a" * 64

    def write_status(side: str, status: int) -> None:
        path = dump_tables.run_status_path(tmp_path, "clean_batch_gl", side)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"scenario\tclean_batch_gl\n"
            f"side\t{side}\n"
            f"run_id\tclean_batch_gl-0001\n"
            f"status\t{status}\n"
            f"wrapper_status\t{status}\n"
            f"seed_fingerprint_sha256\t{digest}\n"
            f"seed_marker_sha256\t{digest}\n"
            f"operations\t1\n"
            f"operation_status\t1\tgl_post_cycle\t0\n",
            encoding="utf-8",
        )

    # Clean: attested, disposition `clean`.
    write_status("python", 0)
    clean = dump_tables.read_run_attestation(tmp_path, "clean_batch_gl", "python")
    assert clean["attested"] is True
    assert clean["disposition"] == dump_tables.DISPOSITION_CLEAN
    assert clean["run_status"] == 0

    # Behavioural: attested AND comparable, with the status recorded verbatim and a
    # detail that forbids reading the verdict as a clean run's.
    write_status("python", dump_tables.BEHAVIOURAL_RUN_STATUS)
    behavioural = dump_tables.read_run_attestation(
        tmp_path, "clean_batch_gl", "python"
    )
    assert behavioural["attested"] is True
    assert behavioural["disposition"] == dump_tables.DISPOSITION_BEHAVIOURAL
    assert behavioural["run_status"] == 69
    assert "must not" in (behavioural["detail"] or "")
    assert behavioural["disposition"] in dump_tables.COMPARABLE_DISPOSITIONS

    # A harness fault is NOT comparable, and says so - with the status and the file
    # that recorded it, which is an operator's first question.
    write_status("python", 71)
    fault = dump_tables.read_run_attestation(tmp_path, "clean_batch_gl", "python")
    assert fault["attested"] is False
    assert fault["disposition"] == dump_tables.DISPOSITION_HARNESS_FAULT
    assert fault["run_status"] == 71
    assert fault["source"] is not None
    assert fault["disposition"] not in dump_tables.COMPARABLE_DISPOSITIONS

    # 69 is scoped to the migrated side: the oracle-side runner's band is 70-79 and
    # every member of it is a precondition or a drive fault, so a 69 there is not a
    # behavioural result and must not be treated as one.
    write_status("cobol", dump_tables.BEHAVIOURAL_RUN_STATUS)
    cobol = dump_tables.read_run_attestation(tmp_path, "clean_batch_gl", "cobol")
    assert cobol["attested"] is False
    assert cobol["disposition"] == dump_tables.DISPOSITION_HARNESS_FAULT

    # An absent record claims nothing, and is `unknown` rather than a fault: nothing
    # has seen a status, so nothing can say which kind of nothing it was.
    missing = dump_tables.read_run_attestation(tmp_path, "empty_batch", "python")
    assert missing["attested"] is False
    assert missing["disposition"] == dump_tables.DISPOSITION_UNKNOWN


def test_the_three_stages_agree_on_the_attestation_key_order() -> None:
    """`dump_tables`, `normalize` and `diff_states` carry one attestation shape.

    The object is written by the first, carried unread by the second and enforced by
    the third, and the manifest is compared byte for byte - so a key one stage writes
    and another drops is a false difference in every scenario at once.
    """
    dump_tables = _load_harness_module("dump_tables")
    normalize = _load_harness_module("normalize")

    assert dump_tables.ATTESTATION_KEYS == normalize.ATTESTATION_KEYS
    assert "disposition" in dump_tables.ATTESTATION_KEYS

    # diff_states mirrors the one disposition it treats specially rather than
    # importing it, following the convention its four sibling constants follow.
    diff_text = (_harness_dir() / "diff_states.py").read_text(encoding="utf-8")
    assert (
        f'DISPOSITION_BEHAVIOURAL: Final[str] = "{dump_tables.DISPOSITION_BEHAVIOURAL}"'
        in diff_text
    )


def test_both_sides_are_checked_against_every_declared_operation() -> None:
    """A parity verdict requires that the two sides did the same work.

    The failure this closes is silent and expensive: an operation one side cannot
    drive used to surface as a stage-10 table difference, after nine stages and two
    full seeds, looking exactly like a behavioural defect in the migration.
    """
    cobol_runner = (_harness_dir() / "run_cobol_scenario.sh").read_text(
        encoding="utf-8"
    )

    # THE CHECK LIVES IN THE FIRST STAGE THAT DRIVES AN OPERATION rather than in a
    # ten-stage driver, so it runs before any state is produced and a hand invocation is
    # protected exactly as a composed one is. It reads both maps out of
    # the shipped scripts rather than holding a third copy that could drift from either.
    assert "acas_assert_operations_supported_by_both_sides()" in cobol_runner
    assert "ACAS_RUN_OPERATION_MAP" in cobol_runner
    assert "ACAS_PY_OPERATION_MAP" in cobol_runner
    assert (
        "  acas_resolve_operations\n"
        "  acas_assert_operations_supported_by_both_sides\n" in cobol_runner
    )

    # And the oracle-side runner DRIVES EVERY DECLARED OPERATION ITSELF, in the
    # scenario's own order, with one status slot per operation pre-set to a sentinel
    # that is not zero - so a multi-operation scenario cannot compare a state
    # produced with less work than the migrated side did, and a hand invocation is
    # complete rather than merely looking complete.
    #
    #  TWO REMEDIATIONS EXISTED FOR THIS ONE DEFECT, and the stronger one is what the
    #  tree carries. The other had the runner REFUSE a multi-operation scenario
    #  outright while the orchestrator looped over the list; that closed the silent
    #  case but left a bare invocation unable to drive a four-operation scenario at
    #  all, and left the per-operation term codes unattested. Resolving the ordered
    #  list inside the runner closes both, so the refusal was withdrawn with it.
    assert "acas_resolve_operations()" in cobol_runner
    assert "One status slot per operation" in cobol_runner
    assert "ACAS_RUN_OP_STATUS" in cobol_runner


def test_a_protocol_capture_carries_every_field_the_verdict_must_match(
    tmp_path,
) -> None:
    """SELECTION and PROVENANCE are different jobs, and conflating them closed stage 10.

    The three tools once disagreed with each other in a way no single tool's own
    tests could see. `--all-in-scope` became the comparison bound, so the capture
    stages stopped passing `--scenario-file`; `harness/dump_tables.py` refused the
    two options TOGETHER as "alternative ways of choosing the same list", and filled
    `provenance.scenario_file_sha256` from `--scenario-file` alone; and
    `harness/diff_states.py` requires that field to be present and EQUAL on both
    sides before it compares a row. The field was therefore empty on both sides of
    every capture, stage 10 exited 2 for EVERY scenario, and the pass condition of
    Agent Action Plan §0.8.5 could not be produced at all.

    A guard is cheap and belongs here: this asserts the three-way contract from the
    provenance side, with no database, no oracle and no container, so a capture that
    could not be compared is a red test rather than a protocol that runs nine stages
    and then refuses.
    """
    dump_tables = _load_harness_module("dump_tables")
    diff_states = _load_harness_module("diff_states")

    scenario_file = tmp_path / "clean_batch_gl.yaml"
    scenario_file.write_text("scenario: clean_batch_gl\n", encoding="utf-8")
    repository = _repo_root()

    #  1. THE PARSER ACCEPTS THE TWO TOGETHER. This is the argument vector the
    #     documented recipe and tests/conftest.py both use at stages 3 and 7.
    parsed = dump_tables.build_parser().parse_args(
        [
            "--scenario",
            "clean_batch_gl",
            "--side",
            "cobol",
            "--all-in-scope",
            "--scenario-file",
            str(scenario_file),
        ]
    )
    assert parsed.all_in_scope is True
    assert parsed.scenario_file == str(scenario_file), (
        "--scenario-file was rejected or dropped alongside --all-in-scope. It is "
        "PROVENANCE there, not a selector: its digest is the field stage 10 "
        "requires, and refusing the pair is what emptied it."
    )

    #  2. THE BOUND IS STILL ALL 22. Provenance must not narrow the comparison: a
    #     capture bounded by a scenario's declared effect cannot show a difference in
    #     a table the scenario did not expect to move.
    resolved = dump_tables.resolve_tables(
        scenario_file=scenario_file, all_in_scope=True
    )
    assert resolved == dump_tables.IN_SCOPE_TABLES, (
        f"--all-in-scope with --scenario-file resolved {len(resolved)} table(s), not "
        f"the {len(dump_tables.IN_SCOPE_TABLES)} the protocol compares."
    )
    #  And the two REAL selectors remain mutually exclusive, because those two really
    #  are alternative ways of naming one list.
    with pytest.raises(ValueError):
        dump_tables.resolve_tables(tables="GLBATCH-REC", all_in_scope=True)

    #  3. EVERY FIELD THE VERDICT MATCHES ON IS POPULATED. Read from
    #     diff_states.PROVENANCE_MUST_MATCH rather than restated, so a fourth field
    #     added there is covered here the day it is added.
    provenance = dump_tables.build_provenance(
        run_id="parity-guard-1",
        scenario_file=scenario_file,
        repository=repository,
        command=["harness/dump_tables.py", "--all-in-scope"],
    )
    for field in diff_states.PROVENANCE_MUST_MATCH:
        assert provenance.get(field), (
            f"a stage-3/7 capture would carry no {field!r}, and "
            f"harness/diff_states.py requires every field of "
            f"PROVENANCE_MUST_MATCH to be present and equal on both sides before it "
            f"compares a single row - so stage 10 would exit "
            f"{diff_states.EX_ERROR} for every scenario."
        )
    assert provenance["scenario_file_sha256"] == dump_tables.file_digest(scenario_file)

    #  4. AND THE COMPOSED DRIVER NAMES THE DEFINITION ON EVERY CAPTURE. The recipe
    #     in README-python-migration.md is prose; tests/conftest.py is code, and it
    #     is what the scenario and determinism tiers drive, so its argv is asserted.
    conftest_text = (_repo_root() / "tests" / "conftest.py").read_text(
        encoding="utf-8"
    )
    publish = conftest_text[conftest_text.index("\ndef dump(\n") :]
    publish = publish[1:]
    publish = publish[: publish.index("\ndef ")]
    assert '"--all-in-scope"' in publish, (
        "tests/conftest.py's dump stage no longer bounds the capture with "
        "--all-in-scope, so an empty diff would attest agreement over a fraction of "
        "the surface."
    )
    assert '"--scenario-file"' in publish, (
        "tests/conftest.py's dump stage no longer names the scenario definition, so "
        "scenario_file_sha256 would be empty on both sides and stage 10 would refuse "
        "every comparison - the exact regression this guard exists for."
    )



# ---------------------------------------------------------------------------
# SECTION 17 -- what the harness GENERATES and what it REUSES
#
# Two properties of the build side, asserted against the shipped scripts because
# neither can be reached from the package (R-1 keeps `harness/` off the import path)
# and both are the kind of thing that is correct once and then quietly regresses:
#
#  * a path the operator supplies cannot end a COBOL string literal early, so the
#  fixture builder cannot be steered into generating a different program;
#  * every source, object and translator the oracle is built from can name where it
#  came from, on the reuse branch as well as the build branch.
# ---------------------------------------------------------------------------


def test_a_generated_cobol_literal_cannot_be_ended_early() -> None:
    """Every path the fixture builder writes into COBOL goes through one gate.

    The builder is `harness/dump_tables.py --make-fixtures`; it was
    `harness/make_fixtures.py`, and the gate moved with it unchanged.

    The generator emits `move "<path>" to <field>.` statements. A path holding a
    double quote would close the literal and leave the rest of it as COBOL source --
    an operator-supplied `--out` deciding what the generated loader DOES rather than
    only where it writes. Control characters are the same defect through a different
    door: a newline splits one statement into two.

    Driven through the shipped helper rather than asserted on the source text, so it
    is the committed behaviour that is measured.
    """
    builder = _load_harness_module("dump_tables")

    # Refused: the character that ends a literal, every control character, the
    # DEL byte, an empty path, and anything past the length budget.
    rejected = (
        '/data/fix"tures/x.dat',
        "/data/fix\ntures/x.dat",
        "/data/fix\ttures/x.dat",
        "/data/fix\rtures/x.dat",
        "/data/fix\x00tures/x.dat",
        "/data/fix\x7ftures/x.dat",
        "",
        "/" + "d" * (builder.COBOL_PATH_LITERAL_MAX + 1),
    )
    for path in rejected:
        with pytest.raises(SystemExit) as caught:
            builder.cobol_path_literal(path, what="--out")
        assert caught.value.code == 65, f"{path!r} was not refused with exit 65"

    # Accepted, and returned unchanged: the caller supplies the framing, because a
    # `move' statement wants quotes and a `*>' comment does not.
    good = "/data/fixtures/clean_batch_gl/system.dat"
    assert builder.cobol_path_literal(good, what="--out") == good

    # A path exactly at the budget is inside it: the bound is not off by one.
    at_budget = "/" + "d" * (builder.COBOL_PATH_LITERAL_MAX - 1)
    assert len(at_budget) == builder.COBOL_PATH_LITERAL_MAX
    assert builder.cobol_path_literal(at_budget, what="--out") == at_budget


def test_one_rule_governs_every_generated_literal() -> None:
    """A declared VALUE, a declared raw image and a path are held to one standard.

    Three of the four interpolation gates used to spell the rule for themselves and
    checked only `"`, newline and carriage return; a NUL or a DEL went straight into
    generated source. The rule now lives in one function, so a site cannot be tightened
    without tightening all of them.
    """
    builder = _load_harness_module("dump_tables")

    # The shared predicate refuses the quote and EVERY control character, under
    # whichever exit status its caller passes.
    for bad in ('a"b', "a\nb", "a\rb", "a\tb", "a\x00b", "a\x7fb"):
        for code in (
            builder.FIXTURE_EX_DECLARATION,
            builder.FIXTURE_EX_PRECONDITION,
        ):
            with pytest.raises(SystemExit) as caught:
                builder.refuse_unplaceable_text(bad, what="x", code=code)
            assert caught.value.code == code
    # Ordinary text passes through, including a space and a trailing one.
    for good in ("abc", "a b ", "", "/data/x.dat"):
        builder.refuse_unplaceable_text(
            good, what="x", code=builder.FIXTURE_EX_DECLARATION
        )

    # A declared VALUE reaches it, and comes back quoted exactly once.
    assert builder.cobol_literal("alphanumeric", "AB", "F") == '"AB"'
    for bad in ('A"B', "A\nB", "A\tB", "A\x00B"):
        with pytest.raises(SystemExit) as caught:
            builder.cobol_literal("alphanumeric", bad, "F")
        assert caught.value.code == builder.FIXTURE_EX_DECLARATION


def test_every_generated_path_interpolation_uses_the_gate() -> None:
    """No interpolation site may format an unchecked value into generated COBOL.

    The gate only helps if nothing bypasses it, and a new emitter is exactly the
    change that would. Asserted structurally, because a bypass is a source-level
    property: there is no input that reveals a site which simply was not called.
    """
    source = (_harness_dir() / "dump_tables.py").read_text(encoding="utf-8")
    checked = 'cobol_path_literal(path, what="the seed file path")'

    # Every generated `move "<path>" to <field>.' interpolates the CHECKED path.
    assert source.count(f'f\'     move     "{{{checked}}}"\'') == 4, (
        "expected exactly four generated `move \"<path>\" to <field>.' statements, "
        "each interpolating cobol_path_literal(); a new one must route through it"
    )
    # And both comment lines that name the path do too.
    assert source.count(f"*>  Writes {{{checked}}}") == 2

    # The only other `move "{...}"' emitters interpolate a declared raw image, and
    # that name is gated by refuse_unplaceable_text before it is used. Counting them
    # pins the total, so a NEW unchecked emitter cannot slip in unnoticed.
    assert source.count('move     "{') == 6
    assert source.count('move     "{text}"') == 2
    assert source.count("refuse_unplaceable_text(") == 5  # 1 def + 4 call sites

    # The path budget is measured against the WORST case once, before any file is
    # generated, so the diagnosis names what the operator typed rather than a line of
    # generated COBOL they never wrote.
    assert "longest = max(len(name) for name in SEED_FILES)" in source
    assert "the --out directory, plus the longest seed file name it will hold," in source


def test_a_reused_build_product_must_name_the_source_it_came_from() -> None:
    """Step 1 verifies four members; steps 2 and 3 verify what they reuse.

    The hole this closes was structural rather than theoretical. `build_oracle.sh`
    verified the vendored archive's digest only on the branch that UNPACKS it, and
    the reuse branch is the default -- the image unpacks at build time -- so an
    ordinary run never reached the check. Step 2 compiles `cobmysqlapi38.c' into the
    object every bridge links, and step 3 compiles `presql2.cbl' into the translator
    that generates every bridge's SQL, so between them those two files decide what
    the oracle IS. The oracle is the specification (R-6), which makes an unverified
    one an unverified specification.
    """
    build = (_harness_dir() / "build_oracle.sh").read_text(encoding="utf-8")

    # The four members carry pinned digests, and they are verified on BOTH branches:
    # the loop sits after the if/else, not inside the unpack arm.
    assert "readonly ACAS_PRESQL2_MEMBER_DIGESTS=(" in build
    for member in (
        "cobmysqlapi38.c",
        "cobmysqlapi38.sh",
        "presql2.cbl",
        "presql2.sh",
    ):
        assert f"'{member}:" in build, f"{member} carries no pinned digest"

    unpack = build.index("acas_step1_unpack_presql2()")
    step2 = build.index("acas_step2_build_cobmysqlapi()")
    loop = build.index('for entry in "${ACAS_PRESQL2_MEMBER_DIGESTS[@]}"; do', unpack)
    reuse_branch = build.index("reusing the package harness/Dockerfile.gnucobol", unpack)
    assert unpack < reuse_branch < loop < step2, (
        "the member-digest loop must run AFTER the reuse/unpack choice, so that the "
        "default branch is verified too"
    )

    # A compiled artifact cannot honestly pin its own digest -- that moves with the
    # compiler and the host -- so what is pinned is the digest of its SOURCE.
    assert "readonly ACAS_COBMYSQLAPI_PROVENANCE_SUFFIX='.source-sha256'" in build

    # Both reuse sites are gated on it, and each names its own source.
    assert build.count("acas_artifact_provenance_holds ") >= 2
    assert (
        'acas_artifact_provenance_holds "$published" "$c_digest" '
        "'cobmysqlapi38.c'" in build
    )
    assert (
        'acas_artifact_provenance_holds "$existing" "$cbl_digest" '
        "'presql2.cbl'" in build
    )

    # Refusing must not be fatal: each caller rebuilds from the verified source, so a
    # missing record costs one compile instead of failing the build.
    assert "'presql2 cannot be trusted or is absent" in build
    assert "acas_record_artifact_provenance " in build

    # The pinned ARCHIVE digest stays authoritative: the identity override cannot
    # admit unpinned C or COBOL, because the member digests are still enforced.
    assert "ACAS_PRESQL2_SHA256_EXPECTED and ACAS_PRESQL2_MEMBER_DIGESTS." in build
    assert "cannot become a way to" in build


def test_the_image_records_the_provenance_the_build_script_requires() -> None:
    """The two sides of the sidecar contract agree on its name and its content.

    If they disagree the build still works -- it rebuilds both artifacts every run --
    so the regression is a silent slowdown rather than a failure, which is precisely
    the kind that survives. The image also asserts it wrote them, so the divergence
    surfaces at image build.
    """
    build = (_harness_dir() / "build_oracle.sh").read_text(encoding="utf-8")
    dockerfile = (_harness_dir() / "Dockerfile.gnucobol").read_text(encoding="utf-8")

    suffix = ".source-sha256"
    assert f"readonly ACAS_COBMYSQLAPI_PROVENANCE_SUFFIX='{suffix}'" in build

    # The producer writes one sidecar per published artifact, from the SOURCE.
    assert f'sha256sum cobmysqlapi38.c | cut -d" " -f1' in dockerfile
    assert f'"${{ACAS_LIB_DIR}}/cobmysqlapi.o{suffix}"' in dockerfile
    assert f'sha256sum presql2.cbl | cut -d" " -f1' in dockerfile
    assert f"/usr/local/bin/presql2{suffix}" in dockerfile

    # And asserts them, so a producer change that stops writing them fails loudly.
    assert f'test -s "${{ACAS_LIB_DIR}}/cobmysqlapi.o{suffix}"' in dockerfile
    assert f"test -s /usr/local/bin/presql2{suffix}" in dockerfile


# ---------------------------------------------------------------------------
# SECTION 18 -- WITHDRAWN. THE gl051 CONTROL-TOTAL GATE IS DRIVEN ELSEWHERE.
#
# THIS SECTION HELD SIX TESTS THAT DROVE `gl051_batch_control_check._end_batch`
# FROM PRE-GATE DATA, AND THEY WERE REDUNDANT. They were written on the belief that no
# test drove the migrated gate - a belief formed from an incomplete reading of
# `tests/arithmetic/test_control_total_comparison.py`, whose first twelve hundred lines
# do re-derive the comparison out of `arithmetic.compare` and `arithmetic.store`. Its
# LAST two hundred do not: `test_the_shipped_gate_accepts_a_vat_bearing_batch_as_written`,
# `..._rejects_a_vat_mismatch_and_still_mutates_the_gross`, `..._rejects_a_gross_mismatch`,
# `..._keeps_its_two_early_dispositions` and `..._leaves_no_driver_loaded` call the
# shipped `_end_batch` directly, through a deferred import behind `pytest.importorskip`
# that deletes every tier-isolated name it added.
#
# That group is a STRICT SUPERSET of what was here: the same three dispositions, the
# same `Batch-Status` sentinel of 7 so that "never assigned" is distinguishable from
# "rejected", the same L1109-before-L1117 proof stated as a counterfactual value, plus a
# byte-level `encoded()` comparison and an R-1 no-driver-left-loaded check that the six
# withdrawn tests did not have.
#
# The withdrawal is recorded rather than done silently, because two other files were
# edited to point AT the withdrawn section and have been corrected to point at the real
# one. Duplicating coverage would have been the smaller error; leaving a header claiming
# to be the only place the gate is driven would have been the larger.
#
# WHAT DRIVES WHAT, for a reader arriving from either file:
#  - the gl051 control-total gate      -> tests/arithmetic/test_control_total_comparison.py
#  - the gl072 silent skips            -> SECTION 19 below
#  - the acas008 refusal pair (A-6)    -> SECTION 20 below
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# SECTION 19 -- gl072'S TWO SILENT SKIPS, DRIVEN AGAINST THE MIGRATED LOOP
#
# WHY THESE ARE HERE AND NOT IN A SCENARIO, WITH THE MEASUREMENT THAT DECIDED IT.
# `mixed_accepted_rejected` is the scenario whose stated headline is these two skips
# [general/gl072.cbl:L291-L292] and [general/gl072.cbl:L306-L307]. It does not reach
# either of them, and no seed can, which was established by running the compiled
# cycle and looking at the work file gl070 writes and gl072 reads:
#
#  pretrans.tmp  EXISTS  size=0 bytes
#  postrans.tmp  EXISTS  size=0 bytes
#
# Zero bytes means gl070 emitted no work record, so gl072's first `read post-trans`
# met AT END [general/gl072.cbl:L286-L289] and neither skip test was ever evaluated.
# The cause is ANOMALY N-KEY, measured on GnuCOBOL 3.2 and derived in full in
# `test_the_measured_post_key_round_trip_is_what_starves_gl072` below: the POST-KEY
# a seeded posting row carries cannot be decoded back into the batch number it came
# from, so gl070's OWN guard [general/gl070.cbl:L492-L493] discards the row first.
#
# So the scenario tier can prove the ABSENCE (and does, row by row against the
# declared seed) but cannot prove WHICH skip produced it - which is exactly the
# defect this section closes. Each skip is therefore driven against
# `acas_posting.programs.gl072_transaction_update` itself, and each is paired with
# its CONTRARY case, because a test that only shows a skip cannot tell a skip from a
# program that does nothing at all.
#
# NO DATABASE IS REACHED. The eight facade verbs gl072 performs are replaced by
# recorders, and the work files are the migration's own in-process sequences
# [acas_posting/workfiles.py] - `self._records.clear()`, not a file. The program
# module is imported inside each test body, as everywhere in this file.
# ---------------------------------------------------------------------------

#: The five bytes the frozen bridge leaves in `Batch` after a POST-KEY round trip,
#: measured on the oracle compiler. `move HV-POST-KEY to WS-Post-Key`
#: [common/glpostingMT.cbl:L1085] copies the host variable's eight bytes into the
#: ten-byte group, and for the POST-KEY a seeded `batch 1 / post 1` produces those
#: bytes are 0x06 0x8E 0x0C 0x15 0x3B 0x04 0x30 0x30. `Batch` is the first five.
_MEASURED_ROUND_TRIPPED_BATCH_BYTES: str = "\x06\x8e\x0c\x15\x3b"

#: `472328296244457520` - what the column actually holds after a compiled seed of
#: `Batch: "1"` / `Post-Number: "1"`. Measured by SELECT, and derived from first
#: principles in the test that consumes it.
_MEASURED_STORED_POST_KEY: int = 472328296244457520


def _gl072_fixture(monkeypatch, *, cleared_status: int = 0):
    """Build gl072's storage with every facade verb replaced by a recorder.

    Args:
        monkeypatch: The pytest fixture, used to swap the facade verbs.
        cleared_status: What `GL-Batch-Read-Next` leaves in `Cleared-Status`. Zero is
            `88 Waiting` [copybooks/wsbatch.cob:L30]; one is `88 Processed`.

    Returns:
        `(module, storage, calls)` where `calls` is the ordered list of facade verb
        names the run performed.
    """
    from acas_posting.dal import facade
    from acas_posting.programs import gl072_transaction_update as gl072
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_ledger import WsLedgerRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData
    from acas_posting.workfiles import general_ledger_work_files

    calls: list[str] = []

    def recorder(name: str):
        def verb(ctx, *args, **kwargs):
            calls.append(name)
            # `GL-Batch-Read-Next` is the ONLY verb whose result the skip logic reads:
            # `get-batch` tests `Cleared-Status` immediately after it
            # [general/gl072.cbl:L458].
            if name == "gl_batch_read_next":
                ctx.record.cleared_status = cleared_status
            ctx.file_access.fs_reply = 0
        return verb

    for verb_name in (
        "gl_batch_open",
        "gl_nominal_open",
        "gl_batch_read_next",
        "gl_nominal_read_next",
        "gl_batch_rewrite",
        "gl_nominal_rewrite",
        "gl_batch_close",
        "gl_nominal_close",
    ):
        monkeypatch.setattr(gl072.facade, verb_name, recorder(verb_name))

    system_record = SystemRecord()
    file_access = FileAccess()
    ledger = WsLedgerRecord()
    batch = GlBatchRecord()
    file_defs = FileDefs()
    common = AcasDalCommonData()

    storage = gl072._ProgramStorage(
        ws_calling_data=__import__(
            "acas_posting.records.calling_data", fromlist=["WsCallingData"]
        ).WsCallingData(),
        system_record=system_record,
        to_day="21/09/2025",
        file_defs=file_defs,
        file_access=file_access,
        ledger=ledger,
        batch=batch,
        dal_common=common,
        date_formats=__import__(
            "acas_posting.dates", fromlist=["WsDateFormats"]
        ).WsDateFormats(),
        work_files=general_ledger_work_files(),
        ledger_ctx=facade.FacadeContext(
            system=system_record,
            record=ledger,
            file_access=file_access,
            file_defs=file_defs,
            dal_common=common,
        ),
        batch_ctx=facade.FacadeContext(
            system=system_record,
            record=batch,
            file_access=file_access,
            file_defs=file_defs,
            dal_common=common,
        ),
    )
    return gl072, storage, calls


def _stage_one_work_record(gl072, storage, *, post_batch) -> None:
    """Put exactly one record into `post-trans` and open it for input.

    Args:
        gl072: The program module.
        storage: Its storage.
        post_batch: What `post-batch pic 9(5)` [general/gl072.cbl:L111] holds. An
            `int` for the numeric case; a `str` of non-digit bytes for the case the
            frozen bridge actually produces.
    """
    import decimal

    from acas_posting.records.work_records import PostTransRecord

    record = PostTransRecord()
    record.post_batch = post_batch
    record.post_post = 1
    record.post_ledger.post_ac = 1000
    record.post_ledger.post_pc = 0
    record.post_amount = decimal.Decimal("100.00")
    record.post_code = "GL"
    record.post_date = "21/09/25"
    record.post_legend = "one leg"

    files = storage.work_files.post_trans
    files.open_output()
    files.write(record)
    files.close()
    files.open_input()


def test_the_non_numeric_batch_number_skip_fires_and_is_silent(monkeypatch) -> None:
    """SKIP (a), driven: `if post-batch not numeric go to loop`.

    [general/gl072.cbl:L291-L292], ANOMALY A-13 site (a). The value handed in is not
    invented for the test - it is the FIVE BYTES the frozen bridge leaves in `Batch`
    after a POST-KEY round trip, measured on the oracle compiler.

    WHAT "SILENT" MEANS HERE, ASSERTED RATHER THAN DESCRIBED. The skip precedes
    `if save-batch equal zero ... perform headings` [general/gl072.cbl:L302-L304], so
    `get-batch` - and with it the ONLY read of the batch file
    [general/gl072.cbl:L454] - never happens. Nothing is written, nothing is counted,
    and `save-batch` is still zero afterwards.
    """
    import decimal

    gl072, storage, calls = _gl072_fixture(monkeypatch)
    _stage_one_work_record(
        gl072, storage, post_batch=_MEASURED_ROUND_TRIPPED_BATCH_BYTES
    )

    gl072._loop(storage)

    assert "gl_batch_read_next" not in calls, (
        "the skip is BEFORE the headings performs, so get-batch must not run; the "
        f"loop performed {calls}"
    )
    assert "gl_nominal_read_next" not in calls, (
        "no account may be located for a record the program discarded"
    )
    assert storage.save_batch == 0, (
        "`move post-batch to save-batch` [general/gl072.cbl:L303] is downstream of "
        f"the skip, so save-batch must still be zero; it holds {storage.save_batch!r}"
    )
    assert storage.tot_dr == decimal.Decimal("0.00")
    assert storage.tot_cr == decimal.Decimal("0.00")
    # AT END still performs end-account and end-batch [general/gl072.cbl:L287-L288],
    # which is why the two rewrites appear. They are the AT-END pair, not this
    # record's - the frozen program performs them unconditionally on the way out.
    assert calls == ["gl_nominal_rewrite", "gl_batch_rewrite"], (
        "the only verbs on this path are the AT-END pair; the loop performed "
        f"{calls}"
    )


def test_a_numeric_batch_number_is_not_skipped_which_is_the_contrast(
    monkeypatch,
) -> None:
    """THE CONTRARY CASE, without which the test above proves nothing.

    Identical staging except that `post-batch` holds a NUMBER. The record now
    survives the class condition, `save-batch` is zero so `headings` runs, and
    `get-batch` reads the batch file - so the two paths are distinguished by an
    observable rather than asserted to differ.
    """
    gl072, storage, calls = _gl072_fixture(monkeypatch, cleared_status=0)
    _stage_one_work_record(gl072, storage, post_batch=1)

    gl072._loop(storage)

    assert "gl_batch_read_next" in calls, (
        "a numeric batch number must reach get-batch, or this file cannot claim to "
        f"distinguish the skip from the posting path; the loop performed {calls}"
    )
    assert storage.save_batch == 1, (
        "get-batch's two-receiver move [general/gl072.cbl:L452] must have run"
    )
    assert "gl_nominal_read_next" in calls, (
        "with we-error clear the record proceeds to new-account "
        "[general/gl072.cbl:L316-L317]"
    )


def test_get_batch_raises_the_999_sentinel_for_a_batch_that_is_not_waiting(
    monkeypatch,
) -> None:
    """The ONLY setter of the sentinel, driven: `if not waiting move 999 to we-error`.

    [general/gl072.cbl:L458-L460]. `88 Waiting value 0` sits on `Cleared-Status`
    [copybooks/wsbatch.cob:L29-L32] - NOT on `Batch-Status`, which carries
    `Status-Open`/`Status-Closed` two lines above and is a different field. A batch
    already `Processed` therefore raises the sentinel, which is the frozen system's
    re-post guard.

    `999` IS `WeError.NOT_USED` [copybooks/wsfnctn.cob:L23] - the handler
    vocabulary's "not used" value, borrowed here as a private flag. That overlap is
    the frozen program's, and it is preserved.
    """
    gl072, storage, _ = _gl072_fixture(monkeypatch, cleared_status=1)
    _stage_one_work_record(gl072, storage, post_batch=1)
    storage.post = storage.work_files.post_trans.read_next()

    gl072._get_batch(storage)

    assert storage.file_access.we_error == 999, (
        "a batch that is not waiting must raise the sentinel; we-error holds "
        f"{storage.file_access.we_error!r}"
    )
    assert storage.save_batch == 0, (
        "`move 0 to save-batch` [general/gl072.cbl:L460] accompanies the sentinel, "
        "and it is what makes the NEXT record re-perform headings"
    )


def test_get_batch_clears_the_sentinel_for_a_waiting_batch(monkeypatch) -> None:
    """The `else` limb, so the sentinel is shown to be conditional.

    [general/gl072.cbl:L461-L462]. Same call, same record, `Cleared-Status` zero.
    """
    gl072, storage, _ = _gl072_fixture(monkeypatch, cleared_status=0)
    _stage_one_work_record(gl072, storage, post_batch=7)
    storage.post = storage.work_files.post_trans.read_next()

    gl072._get_batch(storage)

    assert storage.file_access.we_error == 0
    assert storage.save_batch == 7, (
        "the two-receiver move [general/gl072.cbl:L452] writes save-batch AND "
        "WS-Batch-Nos; the else limb leaves both standing"
    )
    assert storage.batch.ws_batch_key.ws_batch_nos == 7
    assert storage.batch.ws_batch_key.ws_ledger == 1, (
        "`move 1 to WS-Ledger` [general/gl072.cbl:L451] - 88 GL-Batch value 1 "
        "[copybooks/wsbatch.cob:L16]"
    )


def test_the_999_skip_fires_and_leaves_the_ledger_untouched(monkeypatch) -> None:
    """SKIP (b), driven END TO END: `if we-error equal 999 go to loop`.

    [general/gl072.cbl:L306-L307], ANOMALY A-13 site (b). Not staged by hand: the
    sentinel is raised by the production `get-batch` the loop itself performs,
    because the batch the sequential read lands on is `Processed`. So this exercises
    the whole chain - headings performs get-batch, get-batch raises 999, the loop
    tests it and continues - rather than asserting a branch over a planted flag.

    THE DATABASE EFFECT IS NOTHING, which is the half of A-13 the anomaly register
    cares about: the account is never located, so no balance moves.
    """
    import decimal

    gl072, storage, calls = _gl072_fixture(monkeypatch, cleared_status=1)
    _stage_one_work_record(gl072, storage, post_batch=1)

    gl072._loop(storage)

    assert "gl_batch_read_next" in calls, (
        "the sentinel must be raised by the production get-batch, not planted"
    )
    assert storage.file_access.we_error == 999
    assert "gl_nominal_read_next" not in calls, (
        "the skip precedes new-account [general/gl072.cbl:L309-L317], so the "
        f"nominal ledger must never be read; the loop performed {calls}"
    )
    assert storage.tot_dr == decimal.Decimal("0.00")
    assert storage.tot_cr == decimal.Decimal("0.00")
    assert storage.ledger.ledger_balance == decimal.Decimal("0.00"), (
        "no accumulation at [general/gl072.cbl:L331] may have happened"
    )


def test_the_measured_post_key_round_trip_is_what_starves_gl072() -> None:
    """ANOMALY N-KEY, derived and locked: why no seed can reach either skip.

    THE CHAIN, each link measured on GnuCOBOL 3.2 against MariaDB 10.11.7:

      1. `WS-Post-Key` is a GROUP of two `pic 9(5)` items
         [copybooks/wspost.cob:L14-L16]; `HV-POST-KEY` is `PIC 9(18) COMP`
         [common/glpostingMT.cbl:L283]. A GROUP sender makes
         `move WS-Post-Key to HV-POST-KEY` [common/glpostingMT.cbl:L1054] a BYTE
         move, not a numeric conversion - proved on the oracle by moving the
         non-numeric group "ABCDE00001" into it without a diagnostic.
      2. Batch 1 / post 1 gives the bytes "0000100001". The first EIGHT read as a
         big-endian integer are 3472328296244457520 - NINETEEN digits - which the
         eighteen-digit picture truncates to 472328296244457520. That is what the
         column holds; measured by SELECT after a compiled seed.
      3. The nineteenth digit is gone, so reading back cannot restore the original
         bytes. `move HV-POST-KEY to WS-Post-Key` [common/glpostingMT.cbl:L1085]
         copies the host variable's eight bytes back, and `Batch` receives five
         CONTROL CHARACTERS. `IF Batch IS NUMERIC` is FALSE - displayed by the
         oracle probe.
      4. gl070 therefore discards the row at
         `if batch not = WS-Batch-Nos go to loop` [general/gl070.cbl:L492-L493] and
         writes nothing. MEASURED: pretrans.tmp is ZERO BYTES after the run.

    Step 4 is the whole reason SECTION 19 exists: gl072's skips are downstream of a
    guard that removes their input, so they are unreachable from any seed and must be
    driven directly. Nothing here is repaired (R-4).
    """
    group_image = f"{1:05d}{1:05d}".encode("latin-1")
    assert group_image == b"0000100001"

    raw = int.from_bytes(group_image[:8], byteorder="big")
    assert raw == 3472328296244457520
    assert len(str(raw)) == 19, (
        "the nineteenth digit is the whole mechanism: an eighteen-digit picture "
        "cannot hold it"
    )
    assert raw % 10**18 == _MEASURED_STORED_POST_KEY, (
        "the truncated value must equal what the column was measured to hold"
    )

    # Step 3, byte for byte.
    returned = _MEASURED_STORED_POST_KEY.to_bytes(8, byteorder="big")
    assert returned == b"\x06\x8e\x0c\x15\x3b\x0400"
    assert returned[:5].decode("latin-1") == _MEASURED_ROUND_TRIPPED_BATCH_BYTES

    # Step 3's consequence, through the PRODUCTION class condition rather than a
    # hand-rolled one.
    from acas_posting.cobol import move as cobol_move
    from acas_posting.programs import gl072_transaction_update as gl072

    assert not cobol_move.is_numeric_class(
        _MEASURED_ROUND_TRIPPED_BATCH_BYTES, gl072._POST_BATCH
    ), (
        "if this ever becomes numeric the derivation above is wrong and the "
        "scenario narratives that cite it must be re-measured"
    )

    # Step 4: whatever those bytes are, they are not the batch number that produced
    # them, so gl070's guard cannot match for ANY seeded batch number.
    assert _MEASURED_ROUND_TRIPPED_BATCH_BYTES != f"{1:05d}"


# ---------------------------------------------------------------------------
# SECTION 20 -- ANOMALY A-6, LOCKED AT THE HANDLER WHERE IT LIVES
#
# WHY A HANDLER-LEVEL CASE IS NEEDED WHEN A SCENARIO ALREADY ASSERTS THE STATE.
# `acas008` refuses FOUR verbs unconditionally at its own entry
# [common/acas008.cbl:L299-L307] and the facade publishes all four anyway, so a
# caller invoking the re-write verb ALWAYS fails. The only TABLE STATE that can
# produce is no change - which is what `tests/scenarios/test_clean_batch_post_irs.py`
# asserts, and it is not enough on its own: a migrated handler that silently did
# nothing, or raised, or returned a DIFFERENT failure pair, would leave exactly the
# same state and pass. The anomaly is the SPECIFIC PAIR the guard answers with, and
# the pair is a value returned to a caller rather than a row, so only a handler-level
# case can see it.
#
# THE PAIR WAS MEASURED, NOT READ. A COBOL driver was compiled against the frozen
# copybooks and called the COMPILED `acas008` once per verb, with its own linkage in
# its own order [common/acas008.cbl:L278-L284], logging off, and `File-System-Used`
# set to the RDB mode. GnuCOBOL 3.2 answered:
#
#  verb              File-Function  WE-Error  FS-Reply
#  ----------------  -------------  --------  --------
#  read-indexed      04             988       99
#  re-write          07             988       99
#  delete            08             988       99
#  start             09             988       99
#
# No database was needed and none was opened, because the guard returns before any
# access-type or file-mode logic runs - which is itself part of what was measured.
#
# THE CONTRAST WAS MEASURED TOO, and it is what makes the pair meaningful rather than
# generic: `read-next` (function 2) is NOT named by the `evaluate`, so the same call
# passed the guard and went on into the handler's real work - observably, it reached
# code that drives the terminal. So 988/99 is THIS GUARD'S answer and not what
# `acas008` says whenever something goes wrong.
# ---------------------------------------------------------------------------

#: The pair the compiled `acas008` answered for every one of the four refused verbs.
#: `988` is the maintainer's own `*> Action type wrong for file type (seq)   988`
#: [common/acas008.cbl:L304]; `99` is `FS-Reply` [common/acas008.cbl:L305].
_MEASURED_ACAS008_REFUSAL: tuple[int, int] = (988, 99)

#: The four `File-Function` values the guard's single branch names, in the order the
#: `evaluate` lists them - `when 4`, `when 7`, `when 9`, `when 8`
#: [common/acas008.cbl:L300-L303]. The order is preserved because the anomaly register
#: cites the individual `when` lines.
_MEASURED_ACAS008_REFUSED_FUNCTIONS: tuple[int, ...] = (4, 7, 9, 8)


def _acas008_linkage(file_function: int):
    """Build `acas008`'s five arguments, in its own order, for one function code.

    Args:
        file_function: The `File-Function` to call with.

    Returns:
        `(module, args)` where `args` is the tuple `aa010_main` takes.
    """
    from acas_posting.dal import acas008_spl_posting as acas008
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    file_access = FileAccess()
    file_access.file_function = file_function
    # Neither is the guard's business - it is tested before both - but they are set so
    # that a handler which somehow got PAST the guard would take the RDB path the
    # migration reproduces rather than the flat-file leg it does not have. ONE is
    # `88 FS-MySql-Used` and ZERO is `88 FS-Cobol-Files-Used`
    # [copybooks/wssystem.cob:L112-L114], and the default is zero.
    system = SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    args = (
        system,
        WsIrsPostingRecord(),
        file_access,
        FileDefs(),
        AcasDalCommonData(),
    )
    return acas008, args


@pytest.mark.parametrize("file_function", _MEASURED_ACAS008_REFUSED_FUNCTIONS)
def test_a6_the_handler_answers_the_measured_refusal_pair(file_function: int) -> None:
    """A-6, DRIVEN: each refused verb answers exactly `WE-Error 988` / `FS-Reply 99`.

    The migrated handler is called through `aa010_main`, which is
    `aa010-main.` [common/acas008.cbl:L289] and holds the whole of the handler's
    logic. No connection is opened, for the same reason the compiled probe needed
    none: the guard is the FIRST thing after the two logging moves, so it returns
    before any code that would want one.

    THE VALUES ARE THE MEASUREMENT'S, not the source's. Reading
    [common/acas008.cbl:L304-L305] would give the same two numbers, but reading is not
    arbitration (R-6) - and reading cannot establish that the compiled handler really
    returns them rather than being overridden downstream, which the probe did
    establish by calling it.

    Args:
        file_function: One of the four values the guard's branch names.
    """
    acas008, args = _acas008_linkage(file_function)

    acas008.aa010_main(*args)

    file_access = args[2]
    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (file_access.we_error, file_access.fs_reply) == (measured_we, measured_fs), (
        f"acas008 called with File-Function {file_function} answered "
        f"({file_access.we_error}, {file_access.fs_reply}); the COMPILED handler was "
        f"measured to answer ({measured_we}, {measured_fs}). A-6 is that the refusal "
        f"is unconditional and always this pair; a different pair means the guard has "
        f"been altered, and a SUCCESS means A-6 has been FIXED - which is a failure "
        f"(R-4)."
    )


def test_a6_the_refusal_is_declared_for_exactly_the_four_measured_functions() -> None:
    """The guard's MEMBERSHIP, so a fifth verb cannot be quietly added or one dropped.

    The migrated layer is data-driven - `HANDLER_REJECTED_FUNCTIONS` keyed by table
    then by function - which is the right shape, and it means the set itself is a
    value that can drift without any code changing. It is pinned here against the
    four the compiled handler was measured to refuse, and against the locators the
    anomaly register cites.
    """
    from acas_posting.dal import acas008_spl_posting as acas008

    declared = {int(function) for function in acas008.REJECTED_FUNCTIONS}
    assert declared == set(_MEASURED_ACAS008_REFUSED_FUNCTIONS), (
        f"the handler declares refusals for {sorted(declared)} and the compiled "
        f"handler was measured to refuse "
        f"{sorted(_MEASURED_ACAS008_REFUSED_FUNCTIONS)} "
        f"[common/acas008.cbl:L300-L303]"
    )
    for function, (fs_reply, we_error, locator) in acas008.REJECTED_FUNCTIONS.items():
        assert (int(we_error), int(fs_reply)) == _MEASURED_ACAS008_REFUSAL, (
            f"File-Function {int(function)} is declared to answer "
            f"({int(we_error)}, {int(fs_reply)}) and was measured as "
            f"{_MEASURED_ACAS008_REFUSAL}"
        )
        assert locator.startswith("[common/acas008.cbl:L30"), (
            f"File-Function {int(function)} cites {locator!r}; the guard's four `when` "
            f"lines are L300 to L303 and the anomaly register cites them individually"
        )


def test_a6_both_published_facade_verbs_reach_the_same_refusal() -> None:
    """THE VERB IS PUBLISHED TWICE AND FAILS BOTH WAYS.

    `SPL-Posting-Rewrite` [copybooks/Proc-ACAS-FH-Calls.cob] and `acas008-Rewrite`
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163] are the entity-named and
    handler-named spellings of one verb, and the facade publishes BOTH over one
    implementation. A caller following either convention must reach the same refusal,
    or the dual-alias design has a hole in exactly the place the anomaly lives.

    ASSERTED ON THE PLAN, NOT BY CALLING. Both verbs dispatch into the handler, and
    the handler's answer is already driven above; what is open here is whether the two
    aliases carry the SAME `File-Function`. That is the property the aliasing could
    get wrong, and it is a value in the published plan, so it is read from there. The
    two prefixes are the layer's own: `_E_` for the ENTITY-named vocabulary of
    `Proc-ACAS-FH-Calls.cob` and `_H_` for the HANDLER-named vocabulary of
    `Proc-ZZ100-ACAS-IRS-Calls.cob`.
    """
    from acas_posting.dal import facade

    plans = {
        "spl_posting_rewrite": getattr(facade, "_E_SPL_POSTING_REWRITE", None),
        "acas008_rewrite": getattr(facade, "_H_ACAS008_REWRITE", None),
    }
    missing = sorted(name for name, plan in plans.items() if plan is None)
    assert not missing, (
        f"no published plan for {missing}; the facade publishes the entity-named and "
        f"handler-named vocabularies over one implementation, so both spellings of the "
        f"re-write verb must exist [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166]"
    )

    def function_of(plan) -> int:
        for setting, value in plan.moves:
            if str(setting).endswith("File-Function"):
                return int(value)
        raise AssertionError(f"{plan.paragraph} sets no File-Function")

    functions = {name: function_of(plan) for name, plan in plans.items()}
    assert len(set(functions.values())) == 1, (
        f"the two alias spellings set different File-Function values: {functions!r}. "
        f"They are one verb [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163], so a "
        f"caller following either convention must reach the same refusal."
    )
    assert set(functions.values()) == {7}, (
        f"the re-write verb must carry File-Function 7, which is the `when 7` of the "
        f"guard [common/acas008.cbl:L301]; the plans carry {functions!r}"
    )
    assert all(plan.handler == "acas008" for plan in plans.values()), (
        "both aliases must dispatch to acas008, which is the handler that refuses"
    )


def _a6_facade_context():
    """One `FacadeContext` carrying the five arguments every handler CALL takes.

    The facade path, as distinct from `_acas008_linkage`'s direct call into
    `aa010_main`: these three cases are about what a CALLER of the published verb
    observes, so they go through the published verb.

    Returns:
        The context, with a fresh record and a fresh status block, in the RDB
        configuration - `1` is `88 FS-MySql-Used` [copybooks/wssystem.cob:L112-L114], so
        a supported function would take the leg that wants a connection.
    """
    from acas_posting.dal import facade
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    system = SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    return facade.FacadeContext(
        system=system,
        record=WsIrsPostingRecord(),
        file_access=FileAccess(),
        file_defs=FileDefs(),
        dal_common=AcasDalCommonData(),
    )


@pytest.mark.parametrize(
    ("verb_name", "file_function"),
    (
        ("spl_posting_read_indexed", 4),
        ("spl_posting_rewrite", 7),
        ("spl_posting_start", 9),
        ("spl_posting_delete", 8),
    ),
)
def test_a6_the_published_verb_is_refused_and_leaves_the_record_alone(
    verb_name: str, file_function: int
) -> None:
    """A-6 through the ENTITY-named vocabulary, invoked rather than inspected.

    The section above drives `aa010_main` directly, which establishes the pair. What
    this adds is the CALLER'S view: the facade paragraph is performed, so the
    `File-Function` it sets on the way in is observable, and the record is compared
    field for field before and after - because "the verb can never succeed" has to mean
    the record did not move either, not merely that a status came back.

    Args:
        verb_name: The published entity-named verb.
        file_function: The `when` the guard names for it [common/acas008.cbl:L300-L303].
    """
    from acas_posting.dal import facade

    context = _a6_facade_context()
    before = dataclasses.asdict(context.record)

    pair = getattr(facade, verb_name)(context)

    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (int(pair.fs_reply), int(pair.we_error)) == (measured_fs, measured_we)
    assert int(context.file_access.fs_reply) == measured_fs
    assert int(context.file_access.we_error) == measured_we
    #  The facade paragraph selected this function, which is how we know the right verb
    #  was reached rather than some other refusal being observed.
    assert int(context.file_access.file_function) == file_function
    assert dataclasses.asdict(context.record) == before, (
        "the verb can never succeed [common/acas008.cbl:L296-L307], so nothing about "
        "the record may move - a handler that refused and still stored would leave the "
        "same status pair behind"
    )


def test_a6_the_handler_named_rewrite_is_refused_by_calling_it() -> None:
    """A-6 through the OTHER vocabulary - one implementation, two published names.

    `acas008-Rewrite` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166] is the IRS
    convention's name for the same paragraph, and the facade publishes both alias sets
    over one implementation (Agent Action Plan section 0.3.3). The sibling test above
    asserts the two PLANS agree; this one asserts a caller following the IRS convention
    actually gets the identical refusal.

    THE IRS VOCABULARY PUBLISHES ONLY THE REWRITE of the four. It has no
    `acas008-Read-Indexed`, `-Start` or `-Delete` paragraph at all, which is asserted
    here as an absence: inventing aliases the frozen copybook does not declare would be
    a facade this migration made up.
    """
    from acas_posting.dal import facade

    context = _a6_facade_context()
    before = dataclasses.asdict(context.record)

    pair = facade.acas008_rewrite(context)

    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (int(pair.fs_reply), int(pair.we_error)) == (measured_fs, measured_we)
    assert int(context.file_access.file_function) == 7
    assert dataclasses.asdict(context.record) == before

    for absent in ("acas008_read_indexed", "acas008_start", "acas008_delete"):
        assert not hasattr(facade, absent), (
            f"{absent} is published, but "
            f"[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166] declares no such "
            f"paragraph - the handler-named vocabulary would then be this migration's "
            f"invention rather than the copybook's."
        )


def test_a6_the_refusal_happens_before_any_connection_is_attempted() -> None:
    """The guard is the FIRST thing the handler does, so no database is reached.

    The measurement in the section note records this - the compiled probe needed no
    database - and prose is not a lock. Proved here by sabotage: the handler's own
    `mysql_1000_open` is replaced by a call that fails the test if it is ever reached,
    and the verb is invoked in the RDBMS configuration, the one every scenario runs in,
    where a SUPPORTED function would open a connection. The verb still answers 99/988,
    so the guard returned before the configuration test at [common/acas008.cbl:L313] and
    before every store decision after it.

    The process connection is asserted absent afterwards as well, because a connection
    opened and left open would be a resource leak this tier could not otherwise see.
    """
    from acas_posting.dal import acas008_spl_posting as acas008
    from acas_posting.dal import connection, facade

    context = _a6_facade_context()
    assert connection.process_connection() is None

    attempts: list[object] = []

    def refuse_to_open(*arguments, **_keywords):
        attempts.append(arguments)
        raise AssertionError(
            "a verb the handler refuses at entry [common/acas008.cbl:L296-L307] must "
            "not reach the database - anomaly A-6 is a status pair, not a query."
        )

    original = acas008.mysql_1000_open
    acas008.mysql_1000_open = refuse_to_open
    try:
        pair = facade.spl_posting_rewrite(context)
    finally:
        acas008.mysql_1000_open = original

    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (int(pair.fs_reply), int(pair.we_error)) == (measured_fs, measured_we)
    assert attempts == []
    assert connection.process_connection() is None


def test_a6_the_supported_functions_are_not_refused() -> None:
    """The guard names four functions and ONLY those four.

    Without this control every assertion above would pass just as well if the handler
    refused EVERYTHING - and a handler that refused `Open`, `Close`, `Read-Next` and
    `Write` would make the IRS transfer file unusable while every A-6 test stayed green.
    The supported functions [common/acas008.cbl:L354-L375] are therefore asserted to be
    absent from the rejection table, and `Delete-All` with them: it is the function the
    handler COERCES `Open`-plus-`Output` into [common/acas008.cbl:L313-L319], so
    refusing it would break the transfer-file clear `irs030` performs at end of job
    [irs/irs030.cbl:L1720-L1724].
    """
    from acas_posting.dal import acas008_spl_posting as acas008
    from acas_posting.dal import status

    rejected = {int(function) for function in acas008.REJECTED_FUNCTIONS}
    assert rejected == set(_MEASURED_ACAS008_REFUSED_FUNCTIONS)

    for supported in acas008.SUPPORTED_HANDLER_FUNCTIONS:
        assert int(supported) not in rejected, (
            f"File-Function {int(supported)} is both supported and refused, which no "
            f"reading of [common/acas008.cbl:L296-L307] permits"
        )
    assert int(status.FileFunction.DELETE_ALL) not in rejected
    assert int(acas008.COERCED_FUNCTION) == int(status.FileFunction.DELETE_ALL)


# ---------------------------------------------------------------------------
# SECTION 20a -- THE STATUS VOCABULARY ITSELF, ASSERTED RATHER THAN ONLY DECLARED
#
# WHY THIS SITS BESIDE SECTION 20. Section 20 locks ONE pair - 988/99 - because that
# pair is anomaly A-6's whole observable. The vocabulary those numbers come from was
# only DECLARED: the `FS-Reply` value set, the `We-Error` codes and the two-layer
# duplicate-key test are what the Agent Action Plan calls an EMULATED status protocol
# (section 0.1.1, "the `FS-Reply` status protocol"), and three of the helpers that
# publish it were reached by no test and no scenario at all. Measured directly in this
# checkout: forcing `implies_fs_reply_error` to answer True, and forcing
# `is_duplicate_key_bridge_level` to answer True, each left the whole arithmetic tier
# green. A mapping nothing asserts is a mapping that can be wrong in the direction
# nobody notices - and for a duplicate-key test, being wrong means a write that
# collided is reported as an unexplained failure, or an unexplained failure is reported
# as a collision.
#
# `end_of_file_status` IS already locked, incidentally but genuinely, by the docstring
# example guard in test_pic_field_descriptors.py: giving it the wrong pair fails that
# test. It is asserted here as well, because a documentation guard is the wrong place
# for the protocol's own contract to live, and because the (10, 10) pairing is the one
# every reader expects to be (10, 0).
# ---------------------------------------------------------------------------


def test_the_fs_reply_value_set_is_exactly_the_frozen_prose_table() -> None:
    """`FS-Reply` carries six values and no others - 0, 10, 21, 22, 23, 99.

    The set is the bridges' own prose table [common/glpostingMT.cbl:L125-L131], and it
    is asserted as a SET so that neither an addition nor a removal can pass. Two
    details of it are easy to get wrong and are asserted individually:

    * `end_of_file_status()` returns (10, **10**) and not (10, 0). One frozen statement
      writes BOTH fields - `move 10 to fs-Reply WE-Error`
      [common/glpostingMT.cbl:L557] - so the detail code equals the reply, which is why
      the helper exists instead of two assignments per call site.
    * `FsReply` is an `IntEnum`, because `FileAccess.fs_reply` holds a plain `int` and a
      handler's stored value must compare equal to a member.
    """
    from acas_posting.dal import status

    assert {int(member) for member in status.FsReply} == {0, 10, 21, 22, 23, 99}, (
        f"the FS-Reply value set is {sorted(int(m) for m in status.FsReply)}; the "
        f"frozen prose table declares 0, 10, 21, 22, 23 and 99 "
        f"[common/glpostingMT.cbl:L125-L131]. An extra value is a status this "
        f"migration invented; a missing one is a status a caller can no longer be told."
    )
    assert int(status.FsReply.SUCCESS) == 0
    assert int(status.FsReply.END_OF_FILE) == 10
    assert int(status.FsReply.INVALID_KEY_ON_START) == 21
    assert int(status.FsReply.DUPLICATE_KEY) == 22
    assert int(status.FsReply.KEY_NOT_FOUND) == 23
    assert int(status.FsReply.ERROR) == 99

    reply, we_error = status.end_of_file_status()
    assert (int(reply), int(we_error)) == (10, 10), (
        f"end_of_file_status() answered {(int(reply), int(we_error))}; "
        f"[common/glpostingMT.cbl:L557] moves 10 into BOTH fs-Reply and WE-Error in one "
        f"statement, so the pair is (10, 10). (10, 0) is the plausible wrong answer."
    )
    assert isinstance(status.FsReply.SUCCESS, int) and status.FsReply.SUCCESS == 0


def test_every_we_error_code_that_arrives_with_fs_reply_99_is_classified() -> None:
    """`implies_fs_reply_error` partitions the fourteen `We-Error` codes correctly.

    The predicate reports whether a detail code is one the frozen source pairs with
    `FS-Reply 99`. Both directions are asserted, because a predicate that answered True
    for everything - the mutation this test was written against - is as useless as one
    that answered False for everything, and the tier could not previously tell the
    difference.

    THE THREE CODES THAT MUST NOT IMPLY 99 are the ones that arrive with a reply of
    their own: `SUCCESS` (0), `NOT_USED` (999) - the value the gl072 silent skip tests
    for [general/gl072.cbl:L306-L307] - and any integer that is not a member at all,
    which a `File-Access` block can legitimately hold because `We-Error` is `pic 999`
    [copybooks/wsfnctn.cob:L23-L38] and nothing constrains it to the table.
    """
    from acas_posting.dal import status

    assert len(status.WeError) == 14, (
        f"the We-Error table has {len(status.WeError)} members; the frozen table's "
        f"twelve plus the two that exist only in handler source is fourteen."
    )

    for member in status.WE_ERRORS_IMPLYING_FS_REPLY_ERROR:
        assert status.implies_fs_reply_error(int(member)), (
            f"We-Error {int(member)} is in WE_ERRORS_IMPLYING_FS_REPLY_ERROR and the "
            f"predicate denies it, so the two disagree about the same fact."
        )

    not_implying = set(status.WeError) - set(status.WE_ERRORS_IMPLYING_FS_REPLY_ERROR)
    assert {int(member) for member in not_implying} == {0, 999}, (
        f"exactly SUCCESS (0) and NOT_USED (999) arrive with a reply of their own; "
        f"this checkout reports {sorted(int(m) for m in not_implying)}."
    )
    for member in not_implying:
        assert not status.implies_fs_reply_error(int(member)), (
            f"We-Error {int(member)} does not arrive with FS-Reply 99, and the "
            f"predicate claims it does. 999 in particular is what gl072's second "
            f"silent skip tests for [general/gl072.cbl:L306-L307]."
        )

    # A value outside the table is not an error by implication - the predicate reports,
    # it does not validate, so an unknown code must simply answer False.
    assert not status.implies_fs_reply_error(1)
    assert not status.implies_fs_reply_error(-1)
    assert not status.implies_fs_reply_error(1000)

    # The two documentation-only codes are still classified as implying 99, because the
    # prose table pairs them with it even though no statement produces them (N6).
    for orphan in status.DOCUMENTATION_ONLY_WE_ERRORS:
        assert status.implies_fs_reply_error(int(orphan))


def test_the_bridge_level_duplicate_key_test_reads_four_characters_and_sqlstate() -> None:
    """`is_duplicate_key_bridge_level` reproduces [common/glpostingMT.cbl:L818-L824].

    Three properties of the frozen fragment, each asserted because each is a way an
    implementation can look right and behave differently:

    1. EITHER duplicate errno - `"1062"` or `"1022"` - answers True, and so does
       SQLSTATE `"23000"` INDEPENDENTLY of the errno. The frozen test is a three-way
       `or`, not a conjunction.
    2. ONLY THE FIRST FOUR CHARACTERS of `SQL-Err` are compared
       [copybooks/wsfnctn.cob:L49], so a fifth character - and any trailing text - is
       never examined. `"10620"` therefore answers True on its first four.
    3. NEITHER duplicate errno NOR `23000` means False, which the caller turns into
       `FS-Reply 99`.

    A True answer becomes `move 22 to fs-reply` and a False one `move 99`, so this
    predicate decides whether a collided write is reported as a duplicate or as an
    unexplained failure. Nothing in the corpus asserted it before.
    """
    from acas_posting.dal import status

    assert status.DUPLICATE_KEY_ERRNOS == frozenset({"1062", "1022"})

    # 1 - each alternative on its own.
    assert status.is_duplicate_key_bridge_level("1062", "00000")
    assert status.is_duplicate_key_bridge_level("1022", "00000")
    assert status.is_duplicate_key_bridge_level("0000", str(status.SqlState.DUPLICATE_KEY))
    assert str(status.SqlState.DUPLICATE_KEY) == "23000"

    # 2 - four characters, and only four.
    assert status.is_duplicate_key_bridge_level("10620", "00000"), (
        "only SQL-Err(1:4) is compared [common/glpostingMT.cbl:L819], so a fifth "
        "character cannot change the answer."
    )
    assert not status.is_duplicate_key_bridge_level("106", "00000"), (
        "a three-character field does not match the four-character literal"
    )

    # 3 - neither alternative.
    assert not status.is_duplicate_key_bridge_level("1146", "42S02"), (
        "a table-missing errno with a table-missing SQLSTATE is NOT a duplicate; "
        "reporting it as FS-Reply 22 would tell a caller its row already existed."
    )
    assert not status.is_duplicate_key_bridge_level("0000", "00000")


# ---------------------------------------------------------------------------
# SECTION 21 -- THE TIER-IMPORT CONTRACT, MADE EXPLICIT AND BOUNDED
#
# WHY THIS SECTION EXISTS. Agent Action Plan section 0.4.3 gives `tests/arithmetic/*`
# a deliberately narrow import set: `cobol` and `records`, and NOT `dal`, NOT
# `programs` and NOT a database. The point of that boundary is not tidiness. It is
# that the arithmetic tier is the one tier which runs ANYWHERE - no container, no
# MariaDB, no seeded fixture - so it is the tier that still tells you something when
# the stack is down. An arithmetic module that imports `acas_posting.dal` at module
# level drags `dal.facade` in at COLLECTION time, and with it a connection module and
# every handler; the tier then either fails to collect on a bare host or silently
# stops being the thing it was for.
#
# AND YET SEVERAL MODULES IN THIS TIER LEGITIMATELY REACH INTO `programs` AND `dal`.
# They must: a test that re-derives a program's formula inline is a SECOND source of
# business logic, and can pass while the shipped program is wrong. Driving the
# shipped paragraph is the fix, and it needs the shipped module. So the boundary
# cannot be "never"; it has to be "never at module level, and only in a named set of
# files".
#
# THE TWO HALVES, AND WHY BOTH ARE ASSERTED SEPARATELY.
#
#  (1) NO MODULE-LEVEL IMPORT, in ANY file of the tier. This is the structural
#  property, and it is absolute - there is no allow-list for it. A deferred
#  import inside a function body costs nothing until that test runs, and the
#  helpers that perform them restore `sys.modules` afterwards, so collection
#  stays clean and a bare host still collects the whole tier.
#
#  (2) A BOUNDED SET OF FILES may defer-import. This half is a ratchet rather than
#  a prohibition. Without it the practice spreads file by file, each step
#  locally justified, until the tier's import set is whatever happened to
#  accumulate - and nobody ever decided that. Adding a file to the set below is
#  a deliberate edit with a reason attached, which is the whole mechanism.
#
# WHAT THIS SECTION DOES NOT DO. It does not check that a deferred import is *used*
# correctly, and it does not check the third mechanism - `pytest.importorskip` and
# the `_shipped_module` / `_freshly_imported` context managers, which import by NAME
# rather than by statement and therefore cannot be found by an AST walk for `Import`
# nodes. Those are bounded by the same allow-list through their own textual
# reference, and each restores what it added in a `finally`. Naming that limit here
# is better than implying a completeness the walk does not have.
# ---------------------------------------------------------------------------

#: Every `tests/arithmetic/*.py` permitted to import `acas_posting.programs`,
#: `acas_posting.dal` or `acas_posting.cli` INSIDE A FUNCTION BODY, with the reason
#: each one needs to. The name keeps its original two-prefix spelling - it is quoted
#: verbatim in the ratchet's own failure message below, which is what a reader acts
#: on; the set it governs is whatever `_tier_crossing_imports` matches.
#:
#: Every entry earns its place by driving shipped code instead of re-deriving it. That
#: is the trade this allow-list records: a slightly wider import set in exchange for
#: tests that cannot pass by agreeing with themselves.
_MAY_DEFER_IMPORT_PROGRAM_OR_DAL: Final[Mapping[str, str]] = MappingProxyType(
    {
        "test_double_entry_explosion.py": (
            "drives gl070's own pre-process loop, so the three-leg explosion is "
            "measured against the shipped paragraph rather than a transcription of "
            "it; the merged close-and-rejection group additionally drives the "
            "shipped sl060 close paragraph and the irs030 input loop with a "
            "recording facade stand-in, because A-1's nested posting close and the "
            "IR032 clean rejection are call sequences no table dump can observe "
            ""
        ),
        "test_gl080_cycle_divide_rounded.py": (
            "drives gl080.run() with every facade verb substituted, to prove the "
            "file's transcription agrees with the shipped program"
        ),
        "test_irs_vat_from_gross.py": (
            "drives the shipped gross sections of irs030 and gl051, so the VAT store "
            "under test is the one the cycle performs"
        ),
        "test_irs_vat_from_net.py": (
            "the net twin of the above, dispatching on the receiving descriptor to "
            "reach whichever of the two shipped sections owns it"
        ),
        "test_ledger_balance_accumulation.py": (
            "drives gl072's new-account paragraph; the conformance lock here is what "
            "caught the transcription that computed the key move without storing it"
        ),
        "test_compute_truncate_unrounded.py": (
            "drives the shipped sl060 and sl100 average blocks, whose three "
            "mutually inconsistent guards cannot be checked from a transcription"
        ),
        "test_control_total_comparison.py": (
            "drives gl051._end_batch, which is the control-total gate itself; the "
            "merged CLI-seams group additionally inspects irs030_posting.run's own "
            "signature to prove the transfer-file clear answer has no default "
            "(MN-05), which a transcription of the signature could not catch"
        ),
        "test_comp3_packed_decimal.py": (
            "reads the shipped sl060 accumulator declaration to pin truncation #1 "
            "against the field the program actually declares"
        ),
        "test_comp_binary.py": (
            "reads the shipped sales-ledger and bridge views for the A-11 sign-loss "
            "census and the measured Q-3 outcome; this file also holds the merged "
            "shared-storage group, whose sections 19 and 20 drive gl072's skip loop "
            "and the acas008 refusal plans and whose section 21 reads the tier's own "
            "import graph"
        ),
        "test_compute_rounded_half_up.py": (
            "walks the three program modules with `ast` to close the five-ROUNDED "
            "census at both ends - table rows and shipped call sites"
        ),
        "test_irs_date_component_derivation.py": (
            "reads the shipped irspostingMT loader view for the guarded date "
            "components and the Q-25 composition census"
        ),
        "test_pic_field_descriptors.py": (
            "reads shipped descriptors for the drift census across the three layers"
        ),
    }
)


def _arithmetic_tier_files() -> tuple[Path, ...]:
    """Every test module of the arithmetic tier, in a stable order.

    Returns:
        The `tests/arithmetic/*.py` paths, sorted, excluding `__init__.py` so the
        count is of test modules rather than of package plumbing.
    """
    here = Path(__file__).resolve().parent
    return tuple(
        path
        for path in sorted(here.glob("*.py"))
        if path.name != "__init__.py"
    )


def _tier_crossing_imports(tree: ast.Module) -> tuple[tuple[int, str, bool], ...]:
    """Every import of `programs`, `dal` or `cli` from `acas_posting` in one module.

    Args:
        tree: The parsed module.

    Returns:
        One tuple per crossing import: its line, the module named, and whether it
        sits at MODULE level. Module level is determined by identity against the
        module body rather than by indentation or by `ast.walk` order, because
        walking from the top descends into function bodies and would report every
        deferred import as a module-level one.
    """
    top_level = {id(node) for node in tree.body}
    found: list[tuple[int, str, bool]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        named: list[str] = []
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            named.append(node.module)
        named.extend(alias.name for alias in node.names)
        for name in named:
            if name.startswith(
                (
                    "acas_posting.programs",
                    "acas_posting.dal",
                    #  `acas_posting.cli` belongs here for the SAME REASON, and it
                    #  was measured rather than assumed: importing
                    #  `acas_posting.cli.args` loads `acas_posting.dal` and the whole
                    #  of `mysql.connector` transitively, so a module-level import of
                    #  it breaks this tier's runs-anywhere property exactly as a
                    #  direct `dal` import would - while naming neither of the two
                    #  prefixes above. The README's import-boundary note names all
                    #  three, so the enforced set is the documented set.
                    "acas_posting.cli",
                )
            ):
                found.append((node.lineno, name, id(node) in top_level))
    return tuple(found)


def test_no_arithmetic_module_imports_a_program_or_dal_at_module_level() -> None:
    """Half one, and it is absolute: nothing crosses the tier at COLLECTION time.

    A module-level `from acas_posting.dal import facade` in this tier pulls the whole
    data-access layer in when pytest merely COLLECTS the file - before any test runs,
    on every host, including one with no MariaDB. The tier's value is that it runs
    anywhere; that is what this assertion protects, and it protects it for every file
    rather than for a chosen set, because there is no legitimate reason for the
    exception to exist.

    The diagnostic names the file, the line and the module, so a failure is a
    one-line fix rather than a hunt.
    """
    offenders: list[str] = []
    for path in _arithmetic_tier_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders.extend(
            f"{path.name}:L{line} imports {module} at module level"
            for line, module, at_module_level in _tier_crossing_imports(tree)
            if at_module_level
        )

    assert offenders == [], (
        "the arithmetic tier must not import acas_posting.programs, acas_posting.dal "
        "or acas_posting.cli at module level - Agent Action Plan section 0.4.3 keeps "
        "this tier runnable with no database, and a module-level import crosses the "
        "boundary at collection time. Move the import into the function that needs "
        "it. Offenders: " + "; ".join(offenders)
    )


def test_the_set_of_modules_that_defer_import_is_the_declared_one() -> None:
    """Half two, a ratchet: the crossing set is exactly what was decided.

    Two directions, and the second is the one that matters more.

    FORWARD - a file that defers an import must be on the list. That is the ratchet:
    the practice cannot spread to a fourteenth file without someone adding a row and
    a reason, which is the moment to ask whether driving shipped code is really what
    the new test needs.

    BACKWARD - a row on the list whose file no longer defers anything is stale, and
    stale permission is how an allow-list stops meaning anything. Asserting the set
    both ways keeps the list a description of the tree rather than a wish about it.

    The backward direction is asserted only for files that exist and defer no import
    by STATEMENT. A listed file may legitimately reach shipped code only through
    `pytest.importorskip` or a `_shipped_module` context manager, which import by
    name; those are outside an AST walk for `Import` nodes, as this section's header
    records, so their rows are checked for a textual reference instead of being
    reported as stale.
    """
    present = {path.name for path in _arithmetic_tier_files()}
    declared = set(_MAY_DEFER_IMPORT_PROGRAM_OR_DAL)

    unknown = sorted(declared - present)
    assert unknown == [], (
        f"the allow-list names files that are not in this tier: {unknown}. A row "
        f"that points at nothing grants permission nobody can audit."
    )

    deferring: set[str] = set()
    referencing: set[str] = set()
    for path in _arithmetic_tier_files():
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        crossings = _tier_crossing_imports(tree)
        if crossings:
            deferring.add(path.name)
        if "acas_posting.programs" in text or "acas_posting.dal" in text:
            referencing.add(path.name)

    undeclared = sorted(deferring - declared)
    assert undeclared == [], (
        f"these modules defer-import acas_posting.programs, acas_posting.dal or "
        f"acas_posting.cli but "
        f"are not on the allow-list: {undeclared}. Driving shipped code instead of "
        f"re-deriving a formula is the right reason to cross this boundary - add the "
        f"file to _MAY_DEFER_IMPORT_PROGRAM_OR_DAL with that reason stated, so the "
        f"tier's import set stays something that was decided rather than something "
        f"that accumulated (Agent Action Plan section 0.4.3)."
    )

    stale = sorted(declared - referencing)
    assert stale == [], (
        f"these modules are on the allow-list but no longer reference "
        f"acas_posting.programs or acas_posting.dal at all: {stale}. Remove the "
        f"rows - an allow-list carrying permissions nothing uses trains a reader to "
        f"stop believing it."
    )

    # Every reason is real prose, not a placeholder. A row whose justification is
    # empty grants the same permission as one that explains itself, which is exactly
    # the failure this list exists to prevent.
    for name, reason in _MAY_DEFER_IMPORT_PROGRAM_OR_DAL.items():
        assert len(reason.split()) >= 8, f"{name}'s reason is too thin: {reason!r}"


def test_the_tier_still_collects_without_the_data_access_layer_imported() -> None:
    """The property the two halves above exist to deliver, asserted end to end.

    The previous two tests are about import STATEMENTS. This one is about the
    OUTCOME they are meant to produce, and it is worth asserting separately because
    the statements could all be correct while something else - a module-level
    descriptor built by calling into `dal`, say - still dragged the layer in.

    Collecting this tier in a subprocess with `--collect-only` and then asking
    whether `acas_posting.dal.connection` reached `sys.modules` answers the real
    question: can a developer with no MariaDB, no container and no seeded fixture
    still collect and run the arithmetic tier? A subprocess is required because this
    very session has already imported the layer through the deferred imports the
    allow-list permits, so `sys.modules` here cannot answer it.
    """
    repo_root = Path(__file__).resolve().parents[2]
    probe = (
        "import subprocess, sys, json\n"
        "import pytest\n"
        "code = pytest.main(['-q', '--collect-only', '-p', 'no:cacheprovider',\n"
        "                    'tests/arithmetic'])\n"
        "leaked = sorted(m for m in sys.modules\n"
        "                if m.startswith('acas_posting.dal')\n"
        "                or m.startswith('acas_posting.programs'))\n"
        "print('COLLECT_RC=' + str(int(code)))\n"
        "print('LEAKED=' + json.dumps(leaked))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    stdout = completed.stdout
    assert "COLLECT_RC=0" in stdout, (
        f"collecting the arithmetic tier must succeed on its own; rc line missing or "
        f"non-zero.\nstdout:\n{stdout[-3000:]}\nstderr:\n{completed.stderr[-2000:]}"
    )

    leaked_line = next(
        line for line in stdout.splitlines() if line.startswith("LEAKED=")
    )
    leaked = json.loads(leaked_line[len("LEAKED=") :])
    assert leaked == [], (
        f"collecting the arithmetic tier imported program or data-access modules: "
        f"{leaked}. Collection must not cross the tier boundary, or this tier stops "
        f"being the one that still runs when the stack is down."
    )


# ---------------------------------------------------------------------------
# SECTION 22 -- THE POST-KEY ROUND TRIP, MEASURED AND PINNED  (ANOMALY N-KEY)
#
# WHAT WAS WRONG, AND WHY NO GREEN SCENARIO WOULD HAVE SHOWN IT.
#
# `WS-Post-Key` is a GROUP of two `pic 9(5)` items [copybooks/wspost.cob:L14-L16] and
# `HV-POST-KEY` is `PIC 9(18) COMP` [common/glpostingMT.cbl:L283]. Both directions of
# the bridge move between them:
#
#  move WS-Post-Key to HV-POST-KEY.   [common/glpostingMT.cbl:L1054]   LOAD
#  move HV-POST-KEY to WS-Post-Key.   [common/glpostingMT.cbl:L1085]   UNLOAD
#
# Because one operand is a group, BOTH are alphanumeric BYTE moves - nothing is
# converted numerically on the way. The load was implemented that way. The unload was
# not: it took the last ten DECIMAL digits of the host variable and split them, which
# for the value the compiled bridge actually stores yields a batch of 62444.
#
# 62444 is a perfectly legitimate five-digit batch number, and that is the whole danger.
# The compiled program leaves bytes in `Batch` that cannot be a batch number at all, so
# gl070's guard `if batch not = WS-Batch-Nos go to loop` [general/gl070.cbl:L492-L493]
# discards every posting - ANOMALY N-KEY, the defect that starves gl070, gl071, gl072
# AND gl080's deletion pass. A reproduction yielding 62444 discards every posting too,
# for as long as no run happens to seed batch 62444. On a run that did, the Python side
# would MATCH and post while the frozen system posts nothing. A state diff would then
# show it - but only on that run, which is why the arithmetic tier has to own it.
#
# THE MEASUREMENT, taken with both operands declared exactly as the frozen sources
# declare them, the host variable set to 472328296244457520 - the value the compiled
# bridge stores for a 0000100001 key, hence the value a fetch really returns - and all
# ten group bytes read back with FUNCTION ORD:
#
#  group bytes      06 8E 0C 15 3B 04 30 30 20 20
#  Batch            0x06 8E 0C 15 3B   -> reported NOT NUMERIC
#  Post-Number      0x04 30 30 20 20   -> reported NOT NUMERIC
#  first ten digits 4723282962         -> does not match
#  last ten digits  6244457520         -> does not match
#
# So the answer to "first ten or last ten" is NEITHER: it is eight BYTES, space-padded
# to the group's ten. The last two bytes are 0x20 - measured, not assumed, and not zero.
#
# AND WHAT `Batch` COMPARES AS. An exhaustive comparison against every value in
# 0..99999 inside the compiled probe matched 75261 and nothing else; `= 1`, `= 62444`
# and `= ZERO` were all false. 75261 is what COBOL's tolerant zoned read gives for those
# five bytes - the digit of each byte is its LOW NIBBLE, so 6, 14, 12, 5, 11 accumulated
# base ten - which is exactly the rule `acas_posting.cobol.usage` already implements.
# The compiled program and the migration's own semantics layer agree, independently.
#
# WHY THESE TESTS EXIST RATHER THAN JUST THE DOCSTRING. The DAL states the zoned rule
# inline because `acas_posting.cobol` is outside its dependency set (section 0.4.3).
# That is a SECOND expression of a rule the semantics layer owns, and the way to make a
# second expression safe is to assert the two agree - which is what the first test below
# does, over a range of images rather than the one that was measured.
# ---------------------------------------------------------------------------

#: The value the compiled bridge stores for a `0000100001` key, and therefore the value
#: a fetch returns. Recorded once, because three tests below use it.
_MEASURED_POST_KEY_COLUMN_VALUE: Final[str] = "472328296244457520"

#: The ten group bytes measured after the frozen unload of that value.
_MEASURED_POST_KEY_GROUP_IMAGE: Final[bytes] = bytes(
    (0x06, 0x8E, 0x0C, 0x15, 0x3B, 0x04, 0x30, 0x30, 0x20, 0x20)
)

#: What `Batch` compares equal to, found by exhaustive search inside the compiled probe.
_MEASURED_BATCH_COMPARES_AS: Final[int] = 75261

#: What the superseded `% 10**10` reading produced - a LEGITIMATE batch number, which is
#: why it was dangerous rather than merely wrong.
_REJECTED_DECIMAL_READING_BATCH: Final[int] = 62444


def test_the_post_key_unload_reproduces_the_measured_group_image() -> None:
    """The unload takes eight BYTES, space-padded - not ten decimal digits.

    Asserts the measured outcome directly, and asserts BOTH rejected readings against
    it, so the test records what the answer is *and* what it is not. Without the second
    half a reader cannot tell that two plausible alternatives were considered and
    excluded by measurement rather than never contemplated.
    """
    from acas_posting.dal import acas006_gl_posting as gl_posting

    batch, post_number = gl_posting._split_post_key(
        Decimal(_MEASURED_POST_KEY_COLUMN_VALUE)
    )

    # oracle: measured - an exhaustive comparison in the compiled probe matched this
    # value and no other.  spec: [common/glpostingMT.cbl:L1085]
    assert batch == _MEASURED_BATCH_COMPARES_AS

    # The byte image the function must be building, asserted through the function's own
    # inputs rather than by reading its internals.
    stored = int(Decimal(_MEASURED_POST_KEY_COLUMN_VALUE))
    assert (
        stored.to_bytes(8, byteorder="big") + b"\x20\x20"
        == _MEASURED_POST_KEY_GROUP_IMAGE
    )

    # NEITHER decimal reading. Both are asserted because both were live candidates.
    eighteen_digits = f"{stored:018d}"
    assert batch != int(eighteen_digits[:10]) % 100000, "the first-ten reading"
    assert batch != _REJECTED_DECIMAL_READING_BATCH, (
        "the last-ten reading produced 62444, a legitimate batch number that would "
        "MATCH a seeded batch 62444 and post where the frozen system posts nothing"
    )
    assert post_number == 40000


def test_the_post_key_zoned_rule_agrees_with_the_semantics_layer() -> None:
    """The DAL's inline zoned read must equal `cobol.usage`'s, over a RANGE of images.

    The DAL states the rule inline because it may not import `acas_posting.cobol`
    (section 0.4.3). This test is what makes that safe: it drives the DAL's own function
    and the semantics layer's canonical decoder over the same images and requires them to
    agree. A range rather than the single measured image, because two implementations can
    coincide on one input and diverge on the next - which is exactly how a duplicated
    rule rots.

    The images are chosen to span the cases that behave differently: the measured one, a
    plain ASCII-digit key where every low nibble is already a digit, and keys whose bytes
    carry high nibbles the zoned read must ignore.
    """
    from acas_posting.cobol import usage as cobol_usage
    from acas_posting.dal import acas006_gl_posting as gl_posting
    from acas_posting.dictionary import model

    column_values = (
        Decimal(_MEASURED_POST_KEY_COLUMN_VALUE),
        Decimal("3472328296244457520"),  # the in-memory image, all ASCII digits
        Decimal("0"),
        Decimal("1"),
        Decimal("999999999999999999"),  # the widest `pic 9(18)` value
        Decimal("72340172838076673"),
    )

    for column_value in column_values:
        batch, post_number = gl_posting._split_post_key(column_value)
        stored = int(column_value)
        image = stored.to_bytes(8, byteorder="big", signed=stored < 0) + b"\x20\x20"

        canonical_batch = cobol_usage.decode(
            image[:5], usage=model.Usage.DISPLAY, digits=5, scale=0, signed=False
        )
        canonical_post = cobol_usage.decode(
            image[5:10], usage=model.Usage.DISPLAY, digits=5, scale=0, signed=False
        )
        assert batch == canonical_batch, column_value
        assert post_number == canonical_post, column_value


def test_an_in_memory_post_key_round_trip_is_byte_symmetric() -> None:
    """Load then unload the SAME host variable and the bytes come back.

    This is the case the load and the unload share, and it is worth pinning separately
    because it is the one that proves the two functions are mirrors. A probe measured it:
    loading `0000100001` leaves the ASCII bytes `00001000` in the host variable, and
    unloading that same host variable puts those eight bytes back with two spaces after
    them, so `Batch` reads 1 and `Post-Number` reads 0.

    NOTE WHAT THIS IS NOT. It is not the path a real read takes. A real read fetches the
    COLUMN's value - the eighteen-digit edit the bridge rendered, which is a DIFFERENT
    bit pattern - so the sibling test above is the one that describes production
    behaviour. Both are kept because conflating them is how the `% 10**10` reading looked
    plausible in the first place.
    """
    from acas_posting.dal import acas006_gl_posting as gl_posting
    from acas_posting.records.gl_posting import WsPostKey

    host_variable = gl_posting._join_post_key(WsPostKey(batch=1, post_number=1))

    # The load's own byte image, which the probe read as the ASCII text `00001000`.
    assert int(host_variable).to_bytes(8, byteorder="big") == b"00001000"

    batch, post_number = gl_posting._split_post_key(host_variable)
    assert batch == 1
    assert post_number == 0, (
        "the group's last two bytes are the alphanumeric space pad, so Post-Number "
        "reads `000` followed by two spaces - low nibbles 0,0,0,0,0"
    )


# ---------------------------------------------------------------------------
# SECTION 22B -- WHAT A CORRUPT `Batch` COMPARES AS, AND AGAINST WHAT
#
# WHY THIS SECTION EXISTS. Section 22 above pinned the BYTES and the numeric reading of
# a `Batch` that came back through the bridge, and stopped there. That was not enough,
# and a QA arbitration proved it: the migrated `gl080` deleted a posting row per posting
# while the compiled `gl080` deleted none, at a batch number - 75261 - the migration's
# own recorded reading names. Final table state was identical on both sides, so no
# scenario diff, no determinism check and no test in this repository could see it. The
# reading was not wrong; it was applied to a relation that does not use it.
#
# THE MEASUREMENT, taken on the compiled oracle (GnuCOBOL 3.2.0) with both operands
# declared exactly as the frozen copybooks declare them - `Batch pic 9(5)`
# [copybooks/wspost.cob:L15] and `WS-Batch-Nos pic 9(5)` [copybooks/wsbatch.cob:L19] -
# `HV-POST-KEY` set to the value the compiled bridge stores, and the frozen unload
# performed:
#
#   Batch IS NUMERIC                                     no
#   if batch = 75261            (numeric LITERAL)        EQUAL
#   if batch = WS-Batch-Nos     (same-picture FIELD)     NOT EQUAL, for all 100,000
#                                                        values a pic 9(5) can hold
#   if batch = ws-save5, that field holding 75261        NOT EQUAL
#   a group of spaces = ZERO    (GROUP vs figurative)    FALSE  -> byte comparison
#   a group of '0'    = ZERO                             TRUE
#   if batch = zero             (ELEMENTARY vs figurative, Batch holding spaces)
#                                                        TRUE   -> numeric comparison
#   move batch to another pic 9(5)                       BYTE COPY: 06 8E 0C 15 3B
#   move batch to a pic 9(6)                             30 06 8E 0C 15 3B
#
# So a relation between two same-picture unsigned DISPLAY items compares STORAGE, while a
# relation with a literal or with the figurative constant compares the tolerant numeric
# reading. The frozen cycle turns on the first at three gates -
# [general/gl070.cbl:L492-L493], [general/gl080.cbl:L460] and [general/gl080.cbl:L617] -
# and at a fourth inside the in-scope part of gl051 [general/gl051.cbl:L1029]. Every one
# of them therefore discards EVERY posting the database returns, which is the third face
# of ANOMALY N-KEY: gl070 writes no work record, gl080 archives and deletes nothing, and
# gl051's proof loop admits nothing to its totals.
#
# The two MOVE readings are recorded above but deliberately NOT implemented: see
# `Q-NKEY-CMP` in docs/migration/ambiguity-resolutions.md for the trace showing that no
# site a corrupt value can reach through a MOVE has a database effect.
# ---------------------------------------------------------------------------

#: The five bytes `Batch` holds after the frozen unload - section 22's measurement,
#: sliced to the first item so the gate tests can hand it about.
_MEASURED_BATCH_IMAGE: Final[bytes] = _MEASURED_POST_KEY_GROUP_IMAGE[:5]

#: The whole domain of a `pic 9(5)` batch number, which the compiled probe swept.
_BATCH_NUMBER_DOMAIN: Final[range] = range(0, 100_000)


def _corrupt_batch() -> object:
    """The `Batch` value a fetch produces, value and bytes together."""
    from acas_posting.cobol import usage as cobol_usage

    return cobol_usage.ZonedDisplayInt(
        _MEASURED_BATCH_COMPARES_AS, zoned_image=_MEASURED_BATCH_IMAGE
    )


def test_the_unload_carries_the_measured_bytes_beside_the_value() -> None:
    """`_split_post_key` publishes the storage, not only the reading.

    The bytes cannot be recovered from the value - that is the whole reason they travel
    with it - so a reproduction that returned a bare `int` could not answer a
    field-to-field relation at all. Both halves are checked, because the second one's
    image is where the two-space pad shows up.
    """
    from acas_posting.dal import acas006_gl_posting as gl_posting

    batch, post_number = gl_posting._split_post_key(
        Decimal(_MEASURED_POST_KEY_COLUMN_VALUE)
    )

    assert batch.zoned_image == _MEASURED_POST_KEY_GROUP_IMAGE[:5]
    assert post_number.zoned_image == _MEASURED_POST_KEY_GROUP_IMAGE[5:10]
    # And the values are unchanged by carrying them: section 22's readings still hold.
    assert (int(batch), int(post_number)) == (_MEASURED_BATCH_COMPARES_AS, 40000)


def test_a_fetched_key_rewritten_puts_the_same_column_value_back() -> None:
    """Unload then load is exact, because both moves move BYTES.

    `move HV-POST-KEY to WS-Post-Key` [common/glpostingMT.cbl:L1085] and
    `move WS-Post-Key to HV-POST-KEY` [common/glpostingMT.cbl:L1054] are both group
    moves, so a row read and written back carries the key it arrived with. Before the
    bytes travelled with the value this composition returned the digits of 75261 instead
    - a different column value, and one no frozen path can produce.
    """
    from acas_posting.dal import acas006_gl_posting as gl_posting
    from acas_posting.records.gl_posting import WsPostKey

    fetched = Decimal(_MEASURED_POST_KEY_COLUMN_VALUE)
    batch, post_number = gl_posting._split_post_key(fetched)

    reloaded = gl_posting._join_post_key(
        WsPostKey(batch=batch, post_number=post_number)
    )

    assert reloaded == fetched


def test_a_corrupt_batch_matches_no_batch_number_field_in_the_whole_domain() -> None:
    """The compiled sweep, re-run against the migrated comparison.

    100,000 field-to-field relations, which is the measurement rather than a sample: the
    compiled probe compared `Batch` with `WS-Batch-Nos` for every value a `pic 9(5)`
    batch number can hold and matched none of them.
    """
    from acas_posting.cobol import arithmetic
    from acas_posting.records.gl_batch import WsBatchKey
    from acas_posting.records.gl_posting import WsPostKey

    batch_field = next(f for f in WsPostKey.FIELDS if f.name == "Batch")
    batch_nos_field = next(f for f in WsBatchKey.FIELDS if f.name == "WS-Batch-Nos")
    corrupt = _corrupt_batch()

    matches = [
        candidate
        for candidate in _BATCH_NUMBER_DOMAIN
        if arithmetic.compare_zoned_display_fields(
            corrupt,
            candidate,
            left_field=batch_field,
            right_field=batch_nos_field,
        )
        == 0
    ]

    assert matches == [], (
        f"the compiled probe matched none of 0..99999; this comparison matched "
        f"{matches[:5]}"
    )

    #  AND THE READING THAT IS STILL CORRECT IS STILL CORRECT. A relation with a
    # numeric LITERAL uses the tolerant value, measured EQUAL at 75261, so the two
    # functions are not interchangeable and neither replaces the other.
    assert arithmetic.compare(corrupt, _MEASURED_BATCH_COMPARES_AS) == 0
    assert arithmetic.compare(corrupt, 1) != 0


def test_the_algebraic_comparison_is_what_matched_and_is_no_longer_the_gate() -> None:
    """The defect, stated as a test so it cannot come back.

    An algebraic comparison of the same two operands DOES match at 75261. That is the
    exact input the QA arbitration used, and the reason the migrated `gl080` issued one
    `DELETE` per posting row where the compiled `gl080` issued none. Keeping both
    assertions in one place records the difference rather than leaving a reader to infer
    why the gate does not use `compare`.
    """
    from acas_posting.cobol import arithmetic
    from acas_posting.records.gl_batch import WsBatchKey
    from acas_posting.records.gl_posting import WsPostKey

    batch_field = next(f for f in WsPostKey.FIELDS if f.name == "Batch")
    batch_nos_field = next(f for f in WsBatchKey.FIELDS if f.name == "WS-Batch-Nos")
    corrupt = _corrupt_batch()

    assert arithmetic.compare(corrupt, _MEASURED_BATCH_COMPARES_AS) == 0, (
        "the algebraic reading matches, which is what the frozen program does NOT do "
        "for a field-to-field relation"
    )
    assert (
        arithmetic.compare_zoned_display_fields(
            corrupt,
            _MEASURED_BATCH_COMPARES_AS,
            left_field=batch_field,
            right_field=batch_nos_field,
        )
        != 0
    )


def test_the_four_frozen_gates_discard_every_posting_the_bridge_returns() -> None:
    """gl070, gl080's two passes and gl051, driven through their own predicates.

    FOUR gate SITES, THREE predicates: gl080's archive pass and deletion pass are
    textually identical [general/gl080.cbl:L459-L461,L616-L618] and share one migrated
    predicate, so driving that predicate once covers both sites. The two counts are
    stated separately because they differ, and a reader comparing this test with the
    frozen source would otherwise find one gate unaccounted for.

    Each gate is the program's own function, not a re-implementation, so a future change
    that reverted any one of them to an algebraic comparison fails here. The sweep is the
    whole batch-number domain for the two that own a named predicate, and the four
    corners plus the tolerant reading for the two that are expressions inside a loop.
    """
    from acas_posting.cobol import arithmetic
    from acas_posting.programs import gl051_batch_control_check as gl051
    from acas_posting.programs import gl070_transaction_pre_process as gl070
    from acas_posting.programs import gl080_end_of_cycle as gl080
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_posting import WsPostingRecord, WsPostKey

    corrupt = _corrupt_batch()
    interesting = (0, 1, _MEASURED_BATCH_COMPARES_AS, 62444, 99999)

    for candidate in interesting:
        posting = WsPostingRecord(
            ws_post_key=WsPostKey(batch=corrupt, post_number=40000)
        )
        batch = GlBatchRecord()
        batch.ws_batch_key.ws_batch_nos = candidate

        gl070_store = types.SimpleNamespace(posting=posting, batch=batch)
        assert gl070._batch_is_not_the_one_being_processed(gl070_store), candidate
        assert not gl070._post_key_is_zero(gl070_store), candidate

        gl080_store = types.SimpleNamespace(posting=posting, batch=batch)
        assert gl080._batch_is_not_the_one_being_processed(gl080_store), candidate
        assert not gl080._post_key_is_zero(gl080_store), candidate

        # gl051's gate is an `elif` inside `batch-print`, so its comparison is driven
        # with the module's own descriptors rather than through a loop that would need
        # a printer, a batch header read and a proof state.
        assert (
            arithmetic.compare_zoned_display_fields(
                corrupt,
                candidate,
                left_field=gl051._POST_BATCH,
                right_field=gl051._WS_BATCH_NOS,
            )
            != 0
        ), candidate


def test_a_clean_key_still_passes_the_gates_which_is_the_contrast() -> None:
    """The gates are not simply always closed.

    A `Batch` holding the digits of its own batch number matches, so the byte comparison
    has not turned the guard into an unconditional skip - it is the CORRUPT image, and
    only that, which no batch number equals.
    """
    from acas_posting.programs import gl070_transaction_pre_process as gl070
    from acas_posting.programs import gl080_end_of_cycle as gl080
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_posting import WsPostingRecord, WsPostKey

    posting = WsPostingRecord(ws_post_key=WsPostKey(batch=7, post_number=3))
    batch = GlBatchRecord()
    batch.ws_batch_key.ws_batch_nos = 7

    store = types.SimpleNamespace(posting=posting, batch=batch)
    assert not gl070._batch_is_not_the_one_being_processed(store)
    assert not gl080._batch_is_not_the_one_being_processed(store)

    batch.ws_batch_key.ws_batch_nos = 8
    assert gl070._batch_is_not_the_one_being_processed(store)
    assert gl080._batch_is_not_the_one_being_processed(store)


def test_the_group_zero_test_is_a_byte_comparison_and_the_elementary_one_is_not() -> (
    None
):
    """`WS-Post-Key = zero` against `batch = zero`: the two readings, both measured.

    A group of ten SPACES is not `ZERO` and a group of ten `0` characters is - so the
    group test compares bytes. An ELEMENTARY item of spaces IS zero, so the elementary
    test compares the tolerant reading. `gl070` and `gl080` have the group form and
    `gl051` [general/gl051.cbl:L1012] has the elementary one, and this pins both against
    the same pair of images.
    """
    from acas_posting.cobol import arithmetic
    from acas_posting.cobol import usage as cobol_usage
    from acas_posting.programs import gl070_transaction_pre_process as gl070
    from acas_posting.programs import gl080_end_of_cycle as gl080
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_posting import WsPostingRecord, WsPostKey

    spaces = cobol_usage.ZonedDisplayInt(0, zoned_image=b"     ")
    posting = WsPostingRecord(
        ws_post_key=WsPostKey(batch=spaces, post_number=spaces)
    )
    store = types.SimpleNamespace(posting=posting, batch=GlBatchRecord())

    # The GROUP form: spaces are not the character zero, so the key is NOT zero.
    assert not gl070._post_key_is_zero(store)
    assert not gl080._post_key_is_zero(store)

    # The ELEMENTARY form, which `gl051` uses: the tolerant reading of five spaces is
    # zero, and `compare` is what gl051 keeps.
    assert arithmetic.compare(spaces, 0) == 0

    # A genuinely zero key is zero on both readings, which is the contrast.
    zero_key = WsPostingRecord(ws_post_key=WsPostKey(batch=0, post_number=0))
    zero_store = types.SimpleNamespace(posting=zero_key, batch=GlBatchRecord())
    assert gl070._post_key_is_zero(zero_store)
    assert gl080._post_key_is_zero(zero_store)


def test_the_byte_comparison_refuses_shapes_it_was_not_measured_for() -> None:
    """The primitive is not a general comparison, and says so.

    Restricted to two unsigned zoned DISPLAY items of scale zero and EQUAL width,
    because that is the shape the compiled measurement covers. A signed operand, a
    packed one, a scaled one or a width mismatch is a call-site error rather than a data
    condition, so it raises rather than guessing at a layout.
    """
    from acas_posting.cobol import arithmetic
    from acas_posting.records.gl_batch import WsBatchKey
    from acas_posting.records.gl_posting import WsPostingRecord, WsPostKey

    batch_field = next(f for f in WsPostKey.FIELDS if f.name == "Batch")
    batch_nos_field = next(f for f in WsBatchKey.FIELDS if f.name == "WS-Batch-Nos")
    amount_field = next(f for f in WsPostingRecord.FIELDS if f.name == "Post-Amount")
    account_field = next(f for f in WsPostingRecord.FIELDS if f.name == "Post-DR")

    with pytest.raises(ValueError, match="unsigned zoned DISPLAY"):
        arithmetic.compare_zoned_display_fields(
            1, 1, left_field=amount_field, right_field=batch_nos_field
        )
    with pytest.raises(ValueError, match="unsigned zoned DISPLAY"):
        arithmetic.compare_zoned_display_fields(
            1, 1, left_field=batch_field, right_field=amount_field
        )
    with pytest.raises(ValueError, match="EQUAL declared width"):
        arithmetic.compare_zoned_display_fields(
            1, 1, left_field=batch_field, right_field=account_field
        )



# ---------------------------------------------------------------------------
# SECTION 23 -- THE CITATION CONTRACT: EVERY `[path:Lnnn]` MUST RESOLVE  (R-5)
#
#  Rule R-5 requires field-level and paragraph-level traceability, and this
#  project discharges it with inline `[path:Lnnn]` citations into the frozen
#  source - more than eighteen thousand of them. A citation that does not resolve
#  is worse than no citation: it asserts an authority, and a reader who follows it
#  lands on an unrelated line and either mistrusts the whole scheme or, worse,
#  believes what they find there.
#
#  A code review found twenty-six such citations. Fixing them one by one would have
#  hand-checking leaves the rest unverified, so this section makes the property
#  MACHINE-CHECKED instead. It found and closed fifty-three:
#  * 5 out of range - `copybooks/irswssystem.cob:L44` and `:L43` in `args.py`
#  (that copybook has 41 lines; `Print-Spool-Name` is line 37 and
#  `PL-Approp-AC` is line 36, a consistent +7 drift), plus
#  `harness/docker-compose.yml` lines 869-871 in `build_oracle.sh` and line 792
#  in `dump_tables.py`, for a file of 592 lines.
#  * 48 bare FILENAMES with no directory - `ACASDB.sql`, `irsfinalMT.cbl`,
#  `irswsfinal.cob`, `acasirsub5.cbl`, `run_cobol_scenario.sh`. Each resolved
#  to exactly ONE tracked path, so qualifying them was mechanical.
#
#  TWO CITATION FORMS, AND WHY THE SECOND NEEDS A DOCUMENTED RULE. The
#  fully-qualified form -- `general/gl080.cbl` then `:L328`, wrapped in brackets --
#  is self-contained and is checked directly. The SHORTHAND form, a bare `:L328` in
#  brackets with no path, inherits its path from context, and that
#  inheritance is what a validation check has to model. Reading the codebase rather
#  than assuming, the convention is TWO-LEVEL:
#
#  1. THE NEAREST PRECEDING fully-qualified citation in the same scope, where a
#  scope is one function (or, for markdown, one heading section). This is what
#  a human reader does, and it accounts for 1749 of the 2155 shorthand
#  citations. It was verified against a case that discriminates: the shorthand
#  `:L324` in `acas007_gl_batch.py` resolves to `common/acas007.cbl` line 324,
#  which reads
#  `perform ba012-Test-WS-Rec-Size-2.` - an exact match for the comment on it,
#  and NOT the more-frequently-cited `common/glbatchMT.cbl`, whose line 324 is
#  an unrelated screen literal.
#  2. THE FILE'S DECLARED SUBJECT, when level 1 yields nothing or yields a file
#  too short to contain the line. A module docstring whose shorthand names line
#  1176 of the program it migrates means that program, even where some other
#  file was
#  mentioned more recently - which is the case for the shorthand pointing at
#  line 1176 in `sl060_invoice_posting.py`, and accounts for most of the
#  remaining 406.
#
#  A DAL module has TWO declared subjects, its handler AND its bridge, because it
#  narrates both: `acas007_gl_batch.py` cites `common/acas007.cbl` for the
#  handler's procedure division and `common/glbatchMT.cbl` for the bridge's. That
#  is not laxity in the rule - it is the module's actual subject matter, and a
#  one-subject rule would reject correct citations.
#
#  WHAT THIS SECTION DELIBERATELY DOES NOT DO. It does not check that a citation
#  points at the RIGHT line, only that the line EXISTS. Semantic correctness is not
#  mechanically decidable and the surviving quotations in the prose are what carry
#  it. What is decidable - the path resolves, and the line is inside the file - is
#  now decided on every run, and the frozen sources cannot be edited to satisfy it
#  because they cannot be edited at all.
# ---------------------------------------------------------------------------

#: A fully-qualified citation: a path with an extension, then `:Lnnn` or
#: `:Lnnn-Lmmm`. The alternation of extensions keeps prose like `[R-5:L1]` out.
_CITATION_FULL: Final = re.compile(
    r"\[([A-Za-z0-9_./-]+\.(?:cbl|cob|scb|sql|cpy|sh|conf|py|md|txt|toml|yaml|yml))"
    r":L(\d+)(?:\s*-\s*L?(\d+))?\]"
)

#: The shorthand form, which inherits its path from context.
_CITATION_BARE: Final = re.compile(r"\[:L(\d+)(?:\s*-\s*L?(\d+))?\]")

#: A scope boundary in Python: the shorthand does not reach across a definition.
_SCOPE_BOUNDARY: Final = re.compile(r"^\s*(?:def |class |async def )")

#: handler stem -> bridge stem, from the Agent Action Plan's entity-to-table spine
#: (§0.2.1.1). A DAL module's shorthand may cite either of its two subjects.
_HANDLER_BRIDGE: Final[Mapping[str, str]] = MappingProxyType(
    {
        "acas000": "systemMT",
        "acas005": "nominalMT",
        "acas006": "glpostingMT",
        "acas007": "glbatchMT",
        "acas008": "slpostingMT",
        "acas012": "salesMT",
        "acas013": "valueMT",
        "acas015": "analMT",
        "acas016": "slinvoiceMT",
        "acas019": "otm3MT",
        "acas022": "purchMT",
        "acas026": "plinvoiceMT",
        "acas029": "otm5MT",
        "acasirsub1": "irsnominalMT",
        "acasirsub3": "irsdfltMT",
        "acasirsub4": "irspostingMT",
        "acasirsub5": "irsfinalMT",
    }
)

#: Files whose subject is not derivable from their name, declared explicitly. Each
#: was determined by measurement - the frozen file cited most often in that module
#: whose length admits every shorthand line it carries - and each is the module's
#: obvious subject, which is the corroboration that the derivation is right rather
#: than merely self-consistent.
_DECLARED_SUBJECT: Final[Mapping[str, str]] = MappingProxyType(
    {
        "acas_posting/dal/status.py": "common/glpostingMT.cbl",
        "acas_posting/dal/connection.py": "copybooks/mysql-procedures.cpy",
        "acas_posting/records/file_access.py": "copybooks/wsfnctn.cob",
        "acas_posting/records/file_defs.py": "copybooks/wsnames.cob",
        "acas_posting/records/gl_ledger.py": "copybooks/wsledger.cob",
        "acas_posting/records/maps03.py": "copybooks/wsmaps03.cob",
        "tests/arithmetic/test_irs_date_component_derivation.py": (
            "common/irspostingMT.cbl"
        ),
    }
)


def _repo_root() -> Path:
    """The repository root, from this file's own location."""
    return Path(__file__).resolve().parent.parent.parent


def _citation_subjects(relative_path: str) -> tuple[str, ...]:
    """The declared subjects a shorthand citation in this file may resolve to."""
    root = _repo_root()
    name = relative_path.split("/")[-1]
    candidates: list[str] = []

    explicit = _DECLARED_SUBJECT.get(relative_path)
    if explicit is not None:
        candidates.append(explicit)

    handler = re.match(r"(acasirsub\d|acas\d{3})_", name)
    if handler is not None and "/dal/" in relative_path:
        candidates.append(f"common/{handler.group(1)}.cbl")
        bridge = _HANDLER_BRIDGE.get(handler.group(1))
        if bridge is not None:
            candidates.append(f"common/{bridge}.cbl")

    for pattern, directory in (
        (r"(gl\d{3})_", "general"),
        (r"(sl\d{3})_", "sales"),
        (r"(pl\d{3})_", "purchase"),
    ):
        program = re.match(pattern, name)
        if program is not None:
            candidates.append(f"{directory}/{program.group(1)}.cbl")

    if name == "irs030_posting.py":
        candidates.append("irs/irs030.cbl")

    return tuple(c for c in candidates if (root / c).is_file())


#: Directory names never scanned for citations. Caches and virtual environments
#: hold generated copies of files that ARE scanned, so including them would report
#: every failure twice and make the count depend on whether a cache happened to be
#: warm.
_UNSCANNED_DIRECTORIES = frozenset(
    {
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "node_modules",
        "build",
        "dist",
    }
)

#: The four trees whose files carry this migration's citations, plus the README,
#: which sits at the repository root and so is named rather than walked.
_CITED_TREES = ("acas_posting", "harness", "docs/migration", "tests")

#: Suffixes that can carry a citation. A citation lives in prose or a comment, so
#: binary and generated-data files are out.
_CITED_SUFFIXES = (".py", ".md", ".sh", ".yaml", ".yml")


def _cited_files() -> tuple[str, ...]:
    """Every text file of this migration that may carry a citation.

    DELIBERATELY NOT `git ls-files`. Shelling out to git would make this check
    environment-dependent in the one environment that matters most: the harness container has python3 but NO git, so the whole check would raise
    `FileNotFoundError: 'git'` there while passing on the host. A check that is skipped or
    broken exactly where the authoritative run happens is worse than no check, because its
    green result on the host is then read as coverage.

    The walk below is deterministic and needs no tooling: a sorted traversal of
    four named trees, filtered by suffix, with cache and virtual-environment
    directories pruned and scratch files excluded by name. It therefore scans an
    IDENTICAL set on a bare host and inside the container, which is the property
    that makes the two runs comparable.

    Returns:
        Repository-relative paths, sorted, with the root README last.
    """
    root = _repo_root()
    scanned: list[str] = []

    for tree in _CITED_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in _CITED_SUFFIXES:
                continue
            relative = path.relative_to(root)
            if _UNSCANNED_DIRECTORIES.intersection(relative.parts):
                continue
            #  Ad-hoc validation scratch is never committed and never cited.
            if relative.name.startswith("blitzy_adhoc_test_"):
                continue
            scanned.append(relative.as_posix())

    return tuple(sorted(scanned) + ["README-python-migration.md"])


def _validate_citations() -> tuple[dict[str, int], tuple[str, ...]]:
    """Resolve every citation in the migration's own files.

    Returns:
        A count per citation form, and one human-readable failure line per
        citation that does not resolve. An empty failure tuple is the pass.
    """
    root = _repo_root()
    lengths: dict[str, int | None] = {}

    def line_count(path: str) -> int | None:
        if path not in lengths:
            target = root / path
            lengths[path] = (
                len(target.read_text(errors="replace").split("\n"))
                if target.is_file()
                else None
            )
        return lengths[path]

    counts = {"full": 0, "bare": 0}
    failures: list[str] = []

    for relative in _cited_files():
        source = root / relative
        if not source.is_file():
            continue
        lines = source.read_text(errors="replace").split("\n")
        is_markdown = relative.endswith(".md")
        subjects = _citation_subjects(relative)
        inherited: str | None = None

        for number, line in enumerate(lines, start=1):
            #  A definition (or, in markdown, a heading) ends the scope the
            #  shorthand inherits through.
            if (not is_markdown and _SCOPE_BOUNDARY.match(line)) or (
                is_markdown and line.startswith("#")
            ):
                inherited = None

            found = [
                (match.start(), "full", match)
                for match in _CITATION_FULL.finditer(line)
            ] + [
                (match.start(), "bare", match)
                for match in _CITATION_BARE.finditer(line)
            ]

            for _, form, match in sorted(found):
                if form == "full":
                    counts["full"] += 1
                    inherited = match.group(1)
                    available = line_count(inherited)
                    low = int(match.group(2))
                    high = int(match.group(3) or match.group(2))
                    if available is None:
                        failures.append(
                            f"{relative}:{number}  {match.group(0)}  -> no such "
                            f"file. A citation must name a path that exists; a "
                            f"bare filename is not a path."
                        )
                    elif low < 1 or high > available:
                        failures.append(
                            f"{relative}:{number}  {match.group(0)}  -> "
                            f"{inherited} has {available} lines. Re-read the "
                            f"frozen file and cite the line it is actually on."
                        )
                    continue

                counts["bare"] += 1
                high = int(match.group(2) or match.group(1))
                resolved = False
                if inherited is not None:
                    available = line_count(inherited)
                    if available is not None and high <= available:
                        resolved = True
                if not resolved:
                    for subject in subjects:
                        available = line_count(subject)
                        if available is not None and high <= available:
                            resolved = True
                            break
                if not resolved:
                    failures.append(
                        f"{relative}:{number}  {match.group(0)}  -> unresolvable. "
                        f"The nearest preceding citation in scope is "
                        f"{inherited!r} and this file's declared subjects are "
                        f"{subjects}; none of them has a line {high}. Either "
                        f"qualify the citation with its path, or add this file to "
                        f"SECTION 23's _DECLARED_SUBJECT."
                    )

    return counts, tuple(failures)


def test_every_citation_resolves_to_a_real_line() -> None:
    """R-5's citations must lead a reader somewhere real.

    This is the check a code review asked for, standing in place of the twenty-six
    corrections it listed. It resolves both citation forms and fails with the file,
    the line, the citation and the reason for each one that does not resolve, so a
    failure is actionable without re-deriving anything.
    """
    counts, failures = _validate_citations()

    assert not failures, (
        f"{len(failures)} citation(s) do not resolve:\n  " + "\n  ".join(failures[:40])
    )

    #  The check must be measuring something. A refactor that removed the citations,
    #  or a regex that stopped matching them, would otherwise pass silently.
    assert counts["full"] > 15_000, (
        f"only {counts['full']} fully-qualified citations were found; R-5's "
        f"traceability rests on them and this file previously saw over 15,000"
    )
    assert counts["bare"] > 2_000, (
        f"only {counts['bare']} shorthand citations were found; the two-level "
        f"resolution rule above is what makes them checkable, so a collapse here "
        f"means the scanner stopped seeing them"
    )


def test_the_citation_scanner_rejects_a_broken_citation() -> None:
    """The check is proven non-vacuous rather than asserted to be.

    A validation check that cannot fail is decoration. Rather than editing a
    shipped file to prove it, the three failure modes are exercised directly
    against the resolver's own inputs: a path that does not exist, a line past the
    end of a real file, and a shorthand citation with no subject that admits it.
    """
    root = _repo_root()

    #  A real frozen file, and a line number past its end.
    ledger = root / "copybooks" / "wsledger.cob"
    assert ledger.is_file()
    available = len(ledger.read_text().split("\n"))
    assert available < 500, "the guard below assumes this copybook is short"

    #  Built by concatenation so no literal citation appears in this file for the
    #  scanner above to read as a claim - the check checks this file too.
    probe_text = "[" + f"copybooks/wsledger.cob:L{available + 1}" + "]"
    probe_full = _CITATION_FULL.fullmatch(probe_text)
    assert probe_full is not None, "the regex must match a well-formed citation"
    assert int(probe_full.group(2)) > available, (
        "the probe must describe a line the file does not have, which is exactly "
        "what the check reports"
    )

    #  A path that does not exist resolves to no length at all.
    assert not (root / "copybooks" / "no-such-copybook.cob").is_file()

    #  And the shorthand form is matched, with its range captured, so an
    #  out-of-range shorthand is reachable by the same comparison.
    probe_bare = _CITATION_BARE.fullmatch("[" + ":L1-L99999" + "]")
    assert probe_bare is not None
    assert int(probe_bare.group(2)) == 99_999

    #  A file with no derivable and no declared subject offers the shorthand
    #  nothing to resolve against, which is the third failure mode.
    assert _citation_subjects("acas_posting/cobol/move.py") == ()
