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

WHERE THE RULES COME FROM. `review_rules` reports, verbatim, "No user rules
provided": this project has NO user rules document, so nothing below is verified
against one and none has been invented. The binding rules are the six the
Technical Specification carries at section 0.7.2, and this file honours them so:

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
  names have now been MEASURED on GnuCOBOL 3.2.0 (finding F-19), so there is no
  `xfail` here: each measurement is asserted, and where it refuted a reading the
  refutation is asserted too, so a change back fails by name.

THE TWO QUESTION IDS THIS FILE NAMES, both real, both citable, both MEASURED:

* Q-3 - what a negative COBOL value actually BECOMES once the bridge moves it
  into an unsigned host variable. The generated dictionary carries this as an
  OPEN ambiguity on all 91 affected entries (emitted by
  `acas_posting/dictionary/generate.py`), paired with anomaly A-11. Section
  0.6.8 is explicit that the stored value "must be measured rather than
  assumed", and IT HAS NOW BEEN MEASURED (finding F-19). GnuCOBOL 3.2.0 was
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
#: (finding F-20). It imports five pure-Python modules and prints `sys.modules`,
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
#: compiled measurement that SETTLED Q-3 (finding F-19). Matched rather than
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
#  `FieldDescriptor` once published a `for_working_storage` factory for this; it
#  has since been withdrawn - `acas_posting/cobol/field.py` records its removal -
#  and the picture parser that supersedes it is outside this tier's import set
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
#    copybooks/wssl.cob:L49   03  Sales-Average    binary-long. *> 9(8) comp
#                                                                    <-- SIGNED
#    common/salesMT.cbl:L308      05  HV-SALES-AVERAGE  PIC 9(10) COMP.
#                                                                  <-- UNSIGNED
#    mysql/ACASDB.sql:L969        `SALES-AVERAGE` int(8) unsigned NOT NULL
#                                                                  <-- UNSIGNED
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
    disagreement, and the entry carries both the anomaly and the open question.
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
    # Q-3 IS RESOLVED (finding F-19), so the entry no longer publishes it as an OPEN
    # ambiguity - it publishes the MEASUREMENT instead. The anomaly stays: the sign
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
    """A-11's value consequence, MEASURED and therefore asserted (finding F-19).

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


# ---------------------------------------------------------------------------
#  GROUP 6  -  A-8, TRUNCATION #2: THE INTEGER DIVIDE INTO A `binary-long`
#
#  Anomaly A-8 is a DOUBLE truncation in the moving-average idiom. This file owns
#  the second one only:
#
#      divide   sales-activety into work-2 giving sales-average.
#                                                  [sales/sl060.cbl:L827]
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
    rather than an open question, so it is asserted plainly - the sign question
    that IS open concerns an UNSIGNED receiving field, which the next test holds
    against Q-3.
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
    """The negative-into-unsigned OVERFLOW, MEASURED and therefore asserted (F-19).

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
#  ⚠️ CORRECTION, 2026-08-07. This header used to call those constants "the
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
    # FINITE, AND UNABLE TO WAIT ON A TERMINAL (finding F-20).
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
#    * An item with a PICTURE has a declared digit count, and the store reduces
#      MODULO 10**digits - so `pic 9(4) comp` turns 32767 into 2767 even though
#      two bytes could hold 32767 perfectly well. Digits win over capacity.
#    * An item declared by USAGE ALONE has no digit count for a policy to apply
#      to, so only the capacity is left, and the store WRAPS as signed two's
#      complement - `binary-short` turns 32768 into -32768.
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
