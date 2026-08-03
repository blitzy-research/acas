"""`COMP-3` packed decimal, proved byte-exact - and anomaly A-8's first truncation.

File 2 of 14 in the arithmetic parity tier. What it locks:

  * the packed WIDTH rule, `ceil((digits + 1) / 2)` bytes, on the seven in-scope
    packed descriptions;
  * the SIGN NIBBLE - `0xC` positive, `0xD` negative, `0xF` unsigned - which is the
    last nibble of the last byte and is spent whether or not the item is signed;
  * the `encode` / `decode` ROUND TRIP, exactly, with no tolerance of any kind;
  * `COMP-3` INHERITED FROM A GROUP header, which the copybooks use for 24 in-scope
    fields and which no picture clause on the field itself reveals;
  * ⭐ ANOMALY A-8, TRUNCATION #1: the ZERO-SCALE packed accumulator `work-2`
    [sales/sl060.cbl:L206] that discards the pence of every `work-goods`
    [sales/sl060.cbl:L218] added into it [sales/sl060.cbl:L826];
  * SILENT high-order overflow and SILENT sign loss, because the frozen sources
    contain no `ON SIZE ERROR` to reproduce.

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none
was provided, so there is no on-disk rules file to consult and no reader should look
for one. The six binding rules live in the Agent Action Plan itself, section 0.7.2,
and bind this file as follows.

R-1, no COBOL at runtime. `tests/arithmetic/*` touch neither COBOL nor a database.
    Nothing here spawns a process, opens a connection, loads a shared library or
    imports the oracle harness, the data-access layer, the CLI or a driver. The one
    file-system prerequisite is the generated dictionary, read through
    `acas_posting.dictionary.loader`. The guard test at the foot of the file asserts
    that, from a snapshot taken while this module was being imported and from this
    module's own global namespace.

R-2, zero binary floating point. Every value below is `decimal.Decimal`, `int` or
    `bytes`. There is no binary-floating-point literal anywhere, no conversion into
    that type, no approximate-comparison helper, no closeness predicate and no
    tolerance of any size: equality is exact or the test fails. The ambient
    `decimal` context is never read and never mutated - the exact `Decimal`s here
    are built from digit tuples, which is context-free, and every store is
    performed by `acas_posting.cobol.usage`, which installs its own context for the
    duration.

R-3, no new validations. `coerce` and `encode` truncate high-order digits silently
    and never raise on a data value, because `ON SIZE ERROR` occurs ZERO times
    across the twelve in-scope programs. No test below asserts an exception on a
    value, clamps a value, or expects a warning. Execution is strictly sequential:
    nothing below depends on ordering across tests, and the manifest admits no
    parallel-runner plugin.

R-4, legacy anomalies reproduced and never fixed. A defect reproduced is correct; a
    defect fixed is a failure. A-8's first truncation has its own named test, and
    that test carries the reproduction comment rule R-4 requires, citing every
    COBOL line involved. These tests exist so that a future well-intentioned
    correction fails the suite rather than passing unnoticed.

R-5, full traceability. Every catalogued field arrives through its TABLE-QUALIFIED
    dictionary key, `<TABLE-NAME>.<COLUMN-NAME>`, resolved by `_resolve_entry_key`
    below rather than hard-coded on faith; every program-local field arrives through
    a `<path>:L<n>` locator and the verbatim declaration text. Where the three layer
    views of a field disagree, the disagreement is REPORTED AND NOT ADJUDICATED:
    `test_the_batch_amount_digit_drift_is_reported_and_not_adjudicated` asserts the
    drift flag and names no winner among the three views.

R-6, compiled behaviour is the tie-breaker. Every expected value carries a
    provenance comment. The three exact byte strings below are the layout of
    ambiguity-register question Q-5.3, which `acas_posting/cobol/usage.py:L94`
    records as RESOLVED and whose arbitrated constants that module owns
    (`PACKED_SIGN_POSITIVE`, `PACKED_SIGN_NEGATIVE`, `PACKED_SIGN_UNSIGNED`, and the
    two-digits-per-byte nibble placement). The ambiguity register itself,
    `docs/migration/ambiguity-resolutions.md`, is not present in this checkout and so
    carries no separate id for the packed byte values; Q-5.3 is therefore the id
    cited, being the one the owning module names, and NO NEW ID HAS BEEN INVENTED.
    Structural facts that follow from that module's own published contract - the
    total width, which nibble carries the sign, and `decode(encode(v)) == v` - are
    asserted outright.

Also binding, Agent Action Plan section 0.8.4: no timing assertion and no
performance measurement appears anywhere below.

THE STORAGE CENSUS this tier exists for, as the specification records it: across the
copybook tree `comp-3` 182, bare `comp` 410, `binary-long` 166, `binary-short` 31,
`binary-char` 84, `sign leading` 4, `sign is leading` 2, `occurs` 107 and
`redefines` 60. Six numeric storage classes must be modelled because collapsing any
of them changes stored values; this file owns one of the six. The following have
ZERO occurrences and are therefore neither implemented nor asserted anywhere:
`binary-double`, `comp-5` as a copybook field, `sign trailing`, `separate`,
`justified`, `blank when zero` in a copybook, `PIC A`, a trailing `V` with no
following `9`, and `P` scaling.

A NOTE ON CARRIERS, because it decides half the assertions below. A packed field's
Python carrier follows its SCALE, not its usage: `python_storage_for(COMP-3, 2)` is
`DECIMAL` and `python_storage_for(COMP-3, 0)` is `INT`. So `Ledger-Balance` comes
back as `Decimal('1234.56')` while `work-2` comes back as `int`. Every carrier
assertion below is driven from `python_storage_for` or from the descriptor's own
`python_storage` rather than assuming one or the other, and each also asserts the
value is not a binary float (R-2).

WHAT THIS FILE DELIBERATELY DOES NOT ASSERT. A-8's truncation #2 - the integer
divide into `Sales-Average binary-long` [copybooks/wssl.cob:L49] at
[sales/sl060.cbl:L827] - belongs to `test_comp_binary.py`, and the composed
two-truncation idiom belongs to `test_compute_truncate_unrounded.py`. Zoned
`DISPLAY` and `SIGN LEADING` belong to `test_sign_leading_display.py`. Nothing here
duplicates them.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import picture as cobol_picture
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic

# A snapshot of the import graph as it stood the instant this module finished
# importing, taken at module scope precisely because it must be taken THEN and not
# later. Rule R-1's claim is about what THIS TIER pulls in; a scenario module
# collected afterwards imports a driver quite legitimately, and asserting on live
# `sys.modules` inside a test body would therefore be asserting something R-1 never
# said. See the guard test at the foot of the file.
_MODULES_PRESENT_AT_IMPORT: Final[frozenset[str]] = frozenset(sys.modules)

# Top-level module names that would mean this tier had reached for a database, the
# compiled oracle, or a library that computes in binary floating point.
_FORBIDDEN_TOP_LEVEL_MODULES: Final[frozenset[str]] = frozenset(
    {"harness", "mysql", "numpy", "pandas", "sqlalchemy"}
)

# Package prefixes inside the migrated cycle that sit BELOW this tier - the
# data-access layer, the CLI and the program modules, the first of which reaches a
# database and the other two of which reach it transitively.
# `acas_posting.clock`, `acas_posting.dates` and
# `acas_posting.workfiles` are deliberately ABSENT from this list even though this
# tier does not import them: `tests/conftest.py` imports the first two for the
# pinned-clock fixture the other two tiers need, they are pure computation with no
# infrastructure of their own, and their presence in a shared session therefore says
# nothing about this file. What this file itself imports is asserted exactly, by
# `_ACAS_MODULES_THIS_FILE_IMPORTS` below.
_FORBIDDEN_PACKAGE_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
)

# The complete set of migration modules this file is allowed to bind, from the tier
# contract: the storage-semantics layer and the dictionary the descriptors come from.
# Asserted against this module's own global namespace, which is exact and cannot be
# perturbed by whatever else the session collected.
_ACAS_MODULES_THIS_FILE_IMPORTS: Final[frozenset[str]] = frozenset(
    {
        "acas_posting.cobol.field",
        "acas_posting.cobol.picture",
        "acas_posting.cobol.usage",
        "acas_posting.dictionary.loader",
        "acas_posting.dictionary.model",
    }
)


#  THE AMBIGUITY THIS FILE'S BYTE LITERALS BELONG TO  (rule R-6)

# Named once so that every citation below leads to the same register entry and none
# is retyped. `acas_posting/cobol/usage.py:L94` records this id as RESOLVED and owns
# the arbitrated constants; `acas_posting/cobol/sortverb.py:L75` cites the same id.
PACKED_LAYOUT_QUESTION: Final[str] = "Q-5.3"

# The width rule - a digit count rounded up to whole bytes at two digits per byte -
# expressed the way the implementation expresses it: INTEGER arithmetic,
# `(digits + 2) // 2`. Never a ceiling function over a real quotient, which would
# route a digit count through binary floating point (R-2).
PACKED_WIDTH_CASES: Final[tuple[tuple[int, int], ...]] = (
    # digits, bytes.  9 -> 5 is `work-goods` [sales/sl060.cbl:L218];
    # 10 -> 6 is `Ledger-Balance` [copybooks/wsledger.cob:L28] - ten digit nibbles
    #           plus a sign nibble is eleven, padded to twelve;
    # 11 -> 6 is `Input-Gross` [copybooks/wsbatch.cob:L41] - eleven digit nibbles
    #           plus a sign nibble is twelve exactly, which is how one more digit
    #           costs no more bytes;
    # 14 -> 8 is `work-2` [sales/sl060.cbl:L206].
    (9, 5),
    (10, 6),
    (11, 6),
    (14, 8),
)


#  THE CATALOGUED PACKED FIELDS  (rule R-5)

# One row per field this file binds to, carrying the facts the FROZEN COPYBOOK
# declares. The dictionary is the source of truth at run time; these literals are
# what the copybook line says, so a disagreement between the two fails a test rather
# than passing silently. Nothing here is a guess: each row was read off the cited
# line.
#
# Row layout, in order: table, column, cobol_name, copybook_locator, digits, scale,
# signed, byte_length.
CATALOGUED_PACKED_FIELDS: Final[
    tuple[tuple[str, str, str, str, int, int, bool, int], ...]
] = (
    # `03  Ledger-Balance    pic s9(8)v99   comp-3.`
    (
        "GLLEDGER-REC",
        "LEDGER-BALANCE",
        "Ledger-Balance",
        "copybooks/wsledger.cob:L28",
        10,
        2,
        True,
        6,
    ),
    # `03  Ledger-Last       pic s9(8)v99   comp-3.`
    (
        "GLLEDGER-REC",
        "LEDGER-LAST",
        "Ledger-Last",
        "copybooks/wsledger.cob:L29",
        10,
        2,
        True,
        6,
    ),
    # `05  Input-Gross     pic 9(9)v99.` under `03  Amounts  comp-3.`
    # [copybooks/wsbatch.cob:L40]. UNSIGNED - the picture carries no `S`.
    (
        "GLBATCH-REC",
        "INPUT-GROSS",
        "Input-Gross",
        "copybooks/wsbatch.cob:L41",
        11,
        2,
        False,
        6,
    ),
    # `03  Sales-Current      pic s9(8)v99       comp-3.`
    (
        "SALEDGER-REC",
        "SALES-CURRENT",
        "Sales-Current",
        "copybooks/wssl.cob:L54",
        10,
        2,
        True,
        6,
    ),
    # `05  sl-os-bal-last-month  pic s9(8)v99.` under
    # `03  Sales-Ledger-Data  comp-3.` [copybooks/wssys4.cob:L9].
    (
        "SYSTOT-REC",
        "SL-OS-BAL-LAST-MONTH",
        "sl-os-bal-last-month",
        "copybooks/wssys4.cob:L10",
        10,
        2,
        True,
        6,
    ),
)

# The four amount fields that inherit `COMP-3` from one group header, in the source
# order of [copybooks/wsbatch.cob:L41-L44].
GLBATCH_AMOUNT_COLUMNS: Final[tuple[str, ...]] = (
    "INPUT-GROSS",
    "INPUT-VAT",
    "ACTUAL-GROSS",
    "ACTUAL-VAT",
)

# The group header those four inherit from, verbatim from [copybooks/wsbatch.cob:L40].
GLBATCH_AMOUNT_GROUP: Final[str] = "Amounts"

# The ten fields under `03  Sales-Ledger-Data  comp-3.`, in the source order of
# [copybooks/wssys4.cob:L10-L19].
SYSTOT_SALES_COLUMNS: Final[tuple[str, ...]] = (
    "SL-OS-BAL-LAST-MONTH",
    "SL-OS-BAL-THIS-MONTH",
    "SL-INVOICES-THIS-MONTH",
    "SL-CREDIT-NOTES-THIS-MONTH",
    "SL-VARIANCE",
    "SL-CREDIT-DEDUCTIONS",
    "SL-CN-UNAPPL-THIS-MONTH",
    "SL-PAYMENTS",
    "SL4-SPARE1",
    "SL4-SPARE2",
)

# The ten under `03  Purchase-Ledger-Data  comp-3.`
# [copybooks/wssys4.cob:L21-L30]. ANOMALY A-20 lives in the last two names: the two
# spare fields carry the SALES prefix inside the PURCHASE group. Reproduced, not
# renamed.
SYSTOT_PURCHASE_COLUMNS: Final[tuple[str, ...]] = (
    "PL-OS-BAL-LAST-MONTH",
    "PL-OS-BAL-THIS-MONTH",
    "PL-INVOICES-THIS-MONTH",
    "PL-CREDIT-NOTES-THIS-MONTH",
    "PL-VARIANCE",
    "PL-CREDIT-DEDUCTIONS",
    "PL-CN-UNAPPL-THIS-MONTH",
    "PL-PAYMENTS",
    "SL4-SPARE3",
    "SL4-SPARE4",
)

SYSTOT_SALES_GROUP: Final[str] = "Sales-Ledger-Data"
SYSTOT_PURCHASE_GROUP: Final[str] = "Purchase-Ledger-Data"


#  THE PROGRAM-LOCAL PACKED FIELDS  (rule R-5: a locator is their only traceability)

# These three never reach a table, so the generated dictionary does not catalogue
# them and `FieldDescriptor.from_dictionary_key` cannot reach them. They arrive
# instead through the picture parser, handed the declaration VERBATIM together with
# its `<path>:L<n>` locator - which is what `acas_posting.cobol.picture` exists for.
# Retyping the components by hand instead would be exactly the transcription error
# the data-dictionary-first directive exists to prevent.

# `03  work-2          pic s9(14)    comp-3.`  <- SCALE 0, and NO `value` clause,
# unlike `work-1` on the line above it [sales/sl060.cbl:L205], which is
# `pic s9(7)v99  comp-3   value zero.`
WORK_2_CLAUSES: Final[str] = "s9(14)    comp-3"
WORK_2_NAME: Final[str] = "work-2"
WORK_2_LOCATOR: Final[str] = "sales/sl060.cbl:L206"

# The same line VERBATIM, indentation and all, for the assertions that are about the
# declaration itself rather than about the storage it describes.
WORK_2_DECLARATION: Final[str] = "     03  work-2          pic s9(14)    comp-3.\n"

# `03  work-goods      pic s9(7)v99  comp-3.`  <- scale 2: the source of the pence
# that the store into `work-2` throws away.
WORK_GOODS_CLAUSES: Final[str] = "s9(7)v99  comp-3"
WORK_GOODS_NAME: Final[str] = "work-goods"
WORK_GOODS_LOCATOR: Final[str] = "sales/sl060.cbl:L218"

# [sales/sl060.cbl:L219-L221] verbatim, comments and indentation included, so the
# parser sees what the compiler sees. `total-group` declares `comp-3` on a group
# that also carries `OCCURS 3`, and neither child's picture mentions storage at all.
SL060_TOTAL_GROUP_SOURCE: Final[str] = (
    "     03  total-group    occurs 3       comp-3.\n"
    "         05 total-net    pic s9(7)v99.\n"
    "         05 total-vat    pic s9(7)v99.\n"
)
SL060_TOTAL_GROUP_FIRST_LINE: Final[int] = 219
SL060_TOTAL_GROUP_OCCURS: Final[int] = 3
SL060_TOTAL_GROUP_NAME: Final[str] = "total-group"


#  THE ORACLE-ARBITRATED BYTE STRINGS  (rule R-6, question Q-5.3)

# Written as byte tuples rather than escape sequences so the NIBBLES are legible: a
# packed item stores two digits per byte and spends its last nibble on the sign, so
# ten digits of `pic s9(8)v99` become eleven digit nibbles zero-filled to twelve,
# and the twelfth is the sign.
#
#   1234.56 at scale 2 is 123456 units -> digits 00000123456 -> 0x00 0x00 0x01 0x23
#   0x45 0x6? where `?` is the sign nibble.
#
# Q-5.3 fixes `?`: 0xC for a signed positive value, 0xD for a signed negative one,
# 0xF for an unsigned item, which spends the nibble regardless.

# `Ledger-Balance` [copybooks/wsledger.cob:L28] holding +1234.56.
LEDGER_BALANCE_BYTES_POSITIVE: Final[bytes] = bytes(
    (0x00, 0x00, 0x01, 0x23, 0x45, 0x6C)
)

# The same field holding -1234.56. Only the sign nibble differs.
LEDGER_BALANCE_BYTES_NEGATIVE: Final[bytes] = bytes(
    (0x00, 0x00, 0x01, 0x23, 0x45, 0x6D)
)

# `Input-Gross` [copybooks/wsbatch.cob:L41] holding 1234.56. Eleven digits rather
# than ten, so the digit nibbles shift by one and the leading nibble is zero - yet
# the total is still six bytes.
INPUT_GROSS_BYTES_UNSIGNED: Final[bytes] = bytes(
    (0x00, 0x00, 0x01, 0x23, 0x45, 0x6F)
)

# The one value every byte string above encodes, kept as a name so the three cannot
# drift apart from each other.
BYTE_LITERAL_VALUE: Final[Decimal] = Decimal("1234.56")


#  ROUND-TRIP VALUE SELECTION  (rule R-2: exact, and built without a context)

# The four magnitudes each field is round-tripped at, named rather than numbered so
# a failure says WHICH one broke. Resolved against the descriptor inside the test,
# because a field's maximum is a property of its digit count.
ROUND_TRIP_MAGNITUDES: Final[tuple[str, ...]] = (
    "zero",
    "quantum",
    "mid",
    "maximum",
)

# A value comfortably inside every in-scope packed domain - the narrowest is
# `work-goods` at nine digits - so "mid" is a real interior point for all of them.
MID_UNITS: Final[int] = 123456


#  HELPERS, ALL LOCAL TO THIS FILE
#
# Deliberately not a shared module: the tier contract forbids a helper module or a
# nested conftest inside `tests/arithmetic/`, and `tests/conftest.py` exists for the
# comparison protocol rather than for storage-class plumbing.


def _resolve_entry_key(table: str, column: str) -> str:
    """Resolve one field to the dictionary key that actually carries it.

    Keys are TABLE-QUALIFIED, `<TABLE-NAME>.<COLUMN-NAME>`, and never a bare field
    name. The obvious composition is tried first; if the document does not carry it,
    the table's own entries are walked - `entries_for_table` yields them in the
    column-ordinal order the frozen schema dump fixes - and the failure names the
    columns the table really has. Nothing is guessed and nothing is hand-written:
    `loader.find_entry` returns None rather than raising, so the fallback is reached
    without swallowing an exception, and an unresolvable field fails the test loudly
    (rule R-5).

    Args:
        table: A table name as the frozen schema declares it, upper case with
            hyphens.
        column: A column name as the frozen schema declares it.

    Returns:
        The exact key the generated dictionary carries for that field.
    """
    composed = f"{table}.{column}"
    if loader.find_entry(composed) is not None:
        return composed

    try:
        candidates = loader.entries_for_table(table)
    except KeyError as exc:  # DictionaryLookupError - the table name itself is wrong
        pytest.fail(
            f"the generated dictionary carries no table {table!r}, so "
            f"{composed!r} cannot be resolved. The loader reports: {exc}"
        )

    for candidate in candidates:
        _, _, tail = candidate.key.partition(".")
        if tail == column:
            return candidate.key

    pytest.fail(
        f"no entry of table {table!r} is keyed for column {column!r}. The "
        f"{len(candidates)} columns it does carry, in ordinal order, are: "
        + ", ".join(entry.key.partition(".")[2] for entry in candidates)
    )


def _descriptor_for(table: str, column: str) -> cobol_field.FieldDescriptor:
    """Build the descriptor the generated dictionary holds for one catalogued field.

    Args:
        table: The table name.
        column: The column name.

    Returns:
        The descriptor, carrying its dictionary key as provenance.
    """
    return cobol_field.FieldDescriptor.from_dictionary_key(
        _resolve_entry_key(table, column)
    )


def _storage_components(
    descriptor: cobol_field.FieldDescriptor,
) -> dict[str, object]:
    """Spread a descriptor into the keyword components `usage` takes.

    `usage.encode` and `usage.decode` take a description rather than a descriptor,
    by design - the storage layer knows nothing of the dictionary. This is the one
    place the two are bridged, so no test below retypes a component and no test can
    accidentally encode with a description its descriptor does not have.

    Args:
        descriptor: The field to describe.

    Returns:
        The keyword arguments for `usage.encode`, `usage.decode` and `usage.coerce`.
    """
    return {
        "usage": descriptor.usage,
        "digits": descriptor.digits,
        "scale": descriptor.scale,
        "signed": descriptor.signed,
        "unsigned": descriptor.unsigned,
        "sign_position": descriptor.sign_position,
    }


def _encode(descriptor: cobol_field.FieldDescriptor, value: Decimal | int) -> bytes:
    """Lay out one value in the bytes the given field would hold it in.

    Args:
        descriptor: The receiving field.
        value: An exact value - `Decimal` or `int`, never a binary float (R-2).

    Returns:
        Exactly `descriptor.byte_length` bytes.
    """
    return cobol_usage.encode(value, **_storage_components(descriptor))


def _decode(
    descriptor: cobol_field.FieldDescriptor, raw: bytes
) -> Decimal | int | str:
    """Read a field's bytes back into the carrier its storage class calls for.

    Args:
        descriptor: The field the bytes came from.
        raw: Exactly `descriptor.byte_length` bytes.

    Returns:
        The value, on the carrier `python_storage` names for the field.
    """
    return cobol_usage.decode(raw, **_storage_components(descriptor))


def _exact_value(units: int, scale: int) -> Decimal:
    """Build the exact `Decimal` that `units` scaled units represent.

    Constructed from a digit tuple rather than by scaling or dividing, so it is
    exact, carries exactly `scale` decimal places, and DOES NOT CONSULT THE AMBIENT
    DECIMAL CONTEXT (R-2). `Decimal(units).scaleb(-scale)` would be context
    sensitive, and `Decimal(units) / 10 ** scale` would be too.

    Args:
        units: The value in whole units of the field's last digit.
        scale: How many of those digits are fractional.

    Returns:
        The value, at exactly that scale.
    """
    magnitude = abs(units)
    return Decimal(
        (
            1 if units < 0 else 0,
            tuple(int(character) for character in str(magnitude)),
            -scale,
        )
    )


def _magnitude_units(
    descriptor: cobol_field.FieldDescriptor, magnitude: str
) -> int:
    """Resolve one named round-trip magnitude against a field's own domain.

    Args:
        descriptor: The field, whose digit count fixes its maximum.
        magnitude: One of `ROUND_TRIP_MAGNITUDES`.

    Returns:
        The magnitude in whole units of the field's last digit.
    """
    match magnitude:
        case "zero":
            return 0
        case "quantum":
            # The smallest positive value the field can distinguish: one unit of its
            # last digit - a penny for a scale-2 money field, 1 for `work-2`.
            return 1
        case "mid":
            return MID_UNITS
        case "maximum":
            # `value_domain` reports bounds in SCALED UNITS, so this is 9999999999
            # for `pic s9(8)v99` rather than 99999999.99.
            return descriptor.max_value
        case _:
            pytest.fail(f"{magnitude!r} is not one of {ROUND_TRIP_MAGNITUDES}")


def _work_2_descriptor() -> cobol_field.FieldDescriptor:
    """The zero-scale packed accumulator of anomaly A-8, from its own declaration.

    Returns:
        The descriptor for `work-2` [sales/sl060.cbl:L206].
    """
    return cobol_picture.descriptor_for(
        WORK_2_CLAUSES,
        name=WORK_2_NAME,
        source_locator=WORK_2_LOCATOR,
    )


def _work_goods_descriptor() -> cobol_field.FieldDescriptor:
    """The two-decimal source field of anomaly A-8, from its own declaration.

    Returns:
        The descriptor for `work-goods` [sales/sl060.cbl:L218].
    """
    return cobol_picture.descriptor_for(
        WORK_GOODS_CLAUSES,
        name=WORK_GOODS_NAME,
        source_locator=WORK_GOODS_LOCATOR,
    )


#  GROUP 1  -  THE PACKED WIDTH RULE


@pytest.mark.parametrize(("digits", "expected_bytes"), PACKED_WIDTH_CASES)
def test_packed_width_is_ceil_of_digits_plus_one_over_two(
    digits: int, expected_bytes: int
) -> None:
    """A `COMP-3` item is `ceil((digits + 1) / 2)` bytes wide.

    One digit per nibble, and the LAST nibble is the sign - so eleven digits and ten
    digits both take six bytes, which is the fact that makes `Input-Gross`
    [copybooks/wsbatch.cob:L41] the same width as `Ledger-Balance`
    [copybooks/wsledger.cob:L28] despite carrying one more digit.

    Provenance: the rule is `acas_posting/cobol/usage.py:L424`, which computes it as
    integer arithmetic. This test recomputes it the same way rather than by rounding
    a real quotient up, because a digit count must never travel through binary
    floating point (R-2).
    """
    assert (digits + 2) // 2 == expected_bytes
    assert cobol_usage.byte_length(model.Usage.COMP_3, digits=digits) == expected_bytes


@pytest.mark.parametrize(("digits", "expected_bytes"), PACKED_WIDTH_CASES)
def test_packed_width_ignores_scale_and_signedness(
    digits: int, expected_bytes: int
) -> None:
    """Neither the implied decimal point nor the sign changes a packed width.

    A `V` occupies no byte, so `pic s9(14)` [sales/sl060.cbl:L206] at scale 0 and a
    fourteen-digit scaled item are the same eight bytes. And signedness never changes
    a width in COBOL, because the sign nibble is spent either way - `0xF` when the
    item is unsigned, as `pic 9(9)v99` under a packed group is
    [copybooks/wsbatch.cob:L40-L41].

    Provenance: `acas_posting/cobol/usage.py:L369-L370` states the rule - an implied
    decimal point occupies no byte, so scale does not enter the width arithmetic -
    and `acas_posting/cobol/usage.py:L380-L381` states that signedness never changes
    a width. This test holds both to it across all four in-scope digit counts (R-5).
    """
    for scale in (0, 2):
        assert (
            cobol_usage.byte_length(
                model.Usage.COMP_3, digits=digits, scale=scale
            )
            == expected_bytes
        )
    assert (
        cobol_usage.byte_length(model.Usage.COMP_3, digits=digits, unsigned=True)
        == expected_bytes
    )
    assert (
        cobol_usage.byte_length(
            model.Usage.COMP_3,
            digits=digits,
            sign_position=model.SignPosition.IMPLICIT_BINARY,
        )
        == expected_bytes
    )


@pytest.mark.parametrize(
    (
        "table",
        "column",
        "cobol_name",
        "locator",
        "digits",
        "scale",
        "signed",
        "expected_bytes",
    ),
    CATALOGUED_PACKED_FIELDS,
    ids=[f"{row[0]}.{row[1]}" for row in CATALOGUED_PACKED_FIELDS],
)
def test_catalogued_packed_field_matches_its_copybook_declaration(
    table: str,
    column: str,
    cobol_name: str,
    locator: str,
    digits: int,
    scale: int,
    signed: bool,
    expected_bytes: int,
) -> None:
    """Each catalogued packed field is the field its copybook line declares.

    Provenance: the expected components are read off the cited copybook line, and
    the descriptor is built from the generated dictionary, so this test compares two
    independent readings of the same frozen declaration (rule R-5). The `cite()`
    string is asserted to lead back to that line, because a citation nobody can
    follow is the same as no traceability at all.
    """
    key = _resolve_entry_key(table, column)
    descriptor = cobol_field.FieldDescriptor.from_dictionary_key(key)

    assert descriptor.dictionary_key == key
    assert descriptor.name == cobol_name
    assert descriptor.source_locator == locator
    assert locator in descriptor.cite()

    assert descriptor.usage is model.Usage.COMP_3
    assert descriptor.is_packed is True
    assert cobol_usage.is_packed(descriptor.usage) is True

    assert descriptor.digits == digits
    assert descriptor.scale == scale
    assert descriptor.signed is signed
    assert descriptor.byte_length == expected_bytes
    assert descriptor.byte_length == (digits + 2) // 2

    # The quantum is the unit of the last place - a penny for every scale-2 field
    # here. Compared with `==` on `Decimal`, which is exact.
    assert descriptor.quantum == _exact_value(1, scale)

    # `value_domain` counts SCALED UNITS, so a ten-digit money field runs to
    # 9999999999 hundredths rather than to 99999999.99 pounds.
    minimum, maximum = descriptor.value_domain
    assert maximum == 10**digits - 1
    assert minimum == (-maximum if signed else 0)


#  GROUP 2  -  THE SIGN NIBBLE:  0xC POSITIVE, 0xD NEGATIVE, 0xF UNSIGNED


def test_the_three_packed_sign_nibbles_are_c_d_and_f() -> None:
    """The three sign nibbles are `0xC`, `0xD` and `0xF`, and they are distinct.

    Provenance: `acas_posting/cobol/usage.py:L89-L91`, the arbitrated constants of
    ambiguity-register question Q-5.3, which that module's line 94 records as
    RESOLVED. A nibble is four bits, so each must fit in one.
    """
    assert cobol_usage.PACKED_SIGN_POSITIVE == 0xC
    assert cobol_usage.PACKED_SIGN_NEGATIVE == 0xD
    assert cobol_usage.PACKED_SIGN_UNSIGNED == 0xF

    nibbles = (
        cobol_usage.PACKED_SIGN_POSITIVE,
        cobol_usage.PACKED_SIGN_NEGATIVE,
        cobol_usage.PACKED_SIGN_UNSIGNED,
    )
    assert len(set(nibbles)) == len(nibbles)
    for nibble in nibbles:
        assert 0x0 <= nibble <= 0xF


def test_signed_positive_packed_value_carries_the_c_sign_nibble() -> None:
    """A positive signed packed value ends in `0xC`, and reads back exactly.

    Provenance: the byte string is the layout of question Q-5.3, cited above and
    recorded RESOLVED by the module that owns the constants
    (`acas_posting/cobol/usage.py:L94`). The structural facts - six bytes, and the
    sign in the LOW nibble of the LAST byte - follow from that module's published
    contract and are asserted outright.
    """
    descriptor = _descriptor_for("GLLEDGER-REC", "LEDGER-BALANCE")
    raw = _encode(descriptor, BYTE_LITERAL_VALUE)

    assert len(raw) == descriptor.byte_length == 6
    assert raw[-1] & 0x0F == cobol_usage.PACKED_SIGN_POSITIVE
    # Q-5.3: 123456 units -> 0x00 0x00 0x01 0x23 0x45 0x6C.
    assert raw == LEDGER_BALANCE_BYTES_POSITIVE, (
        f"the packed layout of {PACKED_LAYOUT_QUESTION} puts "
        f"{LEDGER_BALANCE_BYTES_POSITIVE.hex(' ')} here, and {descriptor!r} "
        f"produced {raw.hex(' ')}"
    )

    recovered = _decode(descriptor, raw)
    assert recovered == BYTE_LITERAL_VALUE
    assert isinstance(recovered, Decimal)
    # The scale survives the round trip, so the value is `1234.56` and not `1234.5600`
    # or `1234.6`. `as_tuple().exponent` is the only exact way to say so.
    assert recovered.as_tuple().exponent == -descriptor.scale
    assert recovered.as_tuple().exponent == -2


def test_signed_negative_packed_value_carries_the_d_sign_nibble() -> None:
    """A negative signed packed value ends in `0xD` and differs only in that nibble.

    Provenance: question Q-5.3 as above. The magnitude nibbles are asserted
    IDENTICAL to the positive case, because in packed decimal the sign is not a
    separate byte and does not disturb the digits - a fact worth locking, since a
    representation that stored a negative by complementing the digits would still
    round-trip and would still be wrong on the wire.
    """
    descriptor = _descriptor_for("GLLEDGER-REC", "LEDGER-BALANCE")
    raw = _encode(descriptor, -BYTE_LITERAL_VALUE)

    assert len(raw) == 6
    assert raw[-1] & 0x0F == cobol_usage.PACKED_SIGN_NEGATIVE
    # Q-5.3: the same digit nibbles, 0xD in place of 0xC.
    assert raw == LEDGER_BALANCE_BYTES_NEGATIVE, (
        f"the packed layout of {PACKED_LAYOUT_QUESTION} puts "
        f"{LEDGER_BALANCE_BYTES_NEGATIVE.hex(' ')} here, and {descriptor!r} "
        f"produced {raw.hex(' ')}"
    )
    assert raw[:-1] == LEDGER_BALANCE_BYTES_POSITIVE[:-1]
    assert raw[-1] >> 4 == LEDGER_BALANCE_BYTES_POSITIVE[-1] >> 4

    recovered = _decode(descriptor, raw)
    assert recovered == -BYTE_LITERAL_VALUE
    assert recovered == Decimal("-1234.56")
    assert isinstance(recovered, Decimal)
    assert recovered.as_tuple().exponent == -2


def test_unsigned_packed_value_carries_the_f_sign_nibble() -> None:
    """An unsigned packed field still spends a nibble, and it holds `0xF`.

    `Input-Gross` is `pic 9(9)v99` under `03 Amounts comp-3.`
    [copybooks/wsbatch.cob:L40-L41] - eleven digits, no `S`. It occupies the same
    six bytes as the ten-digit signed fields precisely BECAUSE the sign nibble is
    spent either way.

    Provenance: question Q-5.3, as above.
    """
    descriptor = _descriptor_for("GLBATCH-REC", "INPUT-GROSS")
    assert descriptor.signed is False
    assert descriptor.digits == 11

    raw = _encode(descriptor, BYTE_LITERAL_VALUE)
    assert len(raw) == descriptor.byte_length == 6
    assert raw[-1] & 0x0F == cobol_usage.PACKED_SIGN_UNSIGNED
    # Q-5.3: eleven digit nibbles zero-filled to eleven, then 0xF.
    assert raw == INPUT_GROSS_BYTES_UNSIGNED, (
        f"the packed layout of {PACKED_LAYOUT_QUESTION} puts "
        f"{INPUT_GROSS_BYTES_UNSIGNED.hex(' ')} here, and {descriptor!r} "
        f"produced {raw.hex(' ')}"
    )

    recovered = _decode(descriptor, raw)
    assert recovered == BYTE_LITERAL_VALUE
    assert isinstance(recovered, Decimal)
    assert recovered.as_tuple().exponent == -2


#  GROUP 3  -  THE ENCODE / DECODE ROUND TRIP


@pytest.mark.parametrize("magnitude", ROUND_TRIP_MAGNITUDES)
@pytest.mark.parametrize(
    ("table", "column"),
    [(row[0], row[1]) for row in CATALOGUED_PACKED_FIELDS],
    ids=[f"{row[0]}.{row[1]}" for row in CATALOGUED_PACKED_FIELDS],
)
def test_catalogued_packed_field_round_trips_exactly(
    table: str, column: str, magnitude: str
) -> None:
    """`decode(encode(v)) == v`, exactly, at zero, one unit, mid range and maximum.

    Every signed field is tested at the negation of each magnitude too. An unsigned
    field is not: storing a negative into it DROPS THE SIGN, which is real behaviour
    and is locked by its own test rather than smuggled in here as a round-trip
    failure.

    Provenance: the round trip is `acas_posting/cobol/usage.py` guaranteeing
    `encode`/`decode` are inverses; this test binds that guarantee to the seven
    in-scope packed descriptions. Comparison is `==` on `Decimal` or `int` - exact.
    There is no tolerance anywhere (R-2).
    """
    descriptor = _descriptor_for(table, column)
    scale = descriptor.scale or 0
    units = _magnitude_units(descriptor, magnitude)

    candidates = [units]
    if descriptor.signed and units != 0:
        candidates.append(-units)

    for candidate_units in candidates:
        value = _exact_value(candidate_units, scale)
        raw = _encode(descriptor, value)

        assert len(raw) == descriptor.byte_length, (
            f"{descriptor!r} laid {value} out in {len(raw)} bytes, not "
            f"{descriptor.byte_length}"
        )

        recovered = _decode(descriptor, raw)
        assert recovered == value, f"{descriptor!r} lost {value} - got {recovered}"

        # R-2: whatever the carrier is, it is never a binary float.
        assert not isinstance(recovered, float)

        # The carrier is decided by the SCALE, so it is read from the module rather
        # than assumed: DECIMAL where there is a fractional part, INT where there is
        # not.
        expected_carrier = cobol_usage.python_storage_for(descriptor.usage, scale)
        assert expected_carrier is descriptor.python_storage
        if expected_carrier is model.CobolPythonStorage.DECIMAL:
            assert isinstance(recovered, Decimal)
            assert recovered.as_tuple().exponent == -scale
        else:
            assert isinstance(recovered, int)


@pytest.mark.parametrize("magnitude", ROUND_TRIP_MAGNITUDES)
def test_program_local_packed_fields_round_trip_exactly(magnitude: str) -> None:
    """The two program-local packed fields of anomaly A-8 round-trip exactly too.

    They carry no dictionary key - they never reach a table - so they arrive through
    the picture parser from their verbatim declarations at
    [sales/sl060.cbl:L206] and [sales/sl060.cbl:L218], which is the only
    traceability such a field will ever have (R-5).

    `work-2` is scale 0, so its carrier is `int`; `work-goods` is scale 2, so its
    carrier is `Decimal`. Both are asserted from `python_storage`, neither assumed.
    """
    for descriptor in (_work_2_descriptor(), _work_goods_descriptor()):
        scale = descriptor.scale or 0
        units = _magnitude_units(descriptor, magnitude)

        candidates = [units]
        if descriptor.signed and units != 0:
            candidates.append(-units)

        for candidate_units in candidates:
            value = _exact_value(candidate_units, scale)
            raw = _encode(descriptor, value)

            assert len(raw) == descriptor.byte_length
            recovered = _decode(descriptor, raw)
            assert recovered == value
            assert not isinstance(recovered, float)

            # The sign nibble again, on fields the dictionary does not catalogue.
            if candidate_units < 0:
                assert raw[-1] & 0x0F == cobol_usage.PACKED_SIGN_NEGATIVE
            else:
                assert raw[-1] & 0x0F == cobol_usage.PACKED_SIGN_POSITIVE


def test_every_in_scope_packed_width_is_exercised_by_the_round_trip() -> None:
    """The four widths of `PACKED_WIDTH_CASES` are all reached by real fields.

    A completeness check on this file rather than on the migration: it fails if a
    width is claimed in the table above but no field below ever encodes at it, which
    is how a parity suite quietly stops covering a storage shape (R-5).

    The three distinct widths and the declarations that produce them: 5 bytes from
    `pic s9(7)v99` [sales/sl060.cbl:L218], 6 bytes from `pic s9(8)v99`
    [copybooks/wsledger.cob:L28] and from `pic 9(9)v99`
    [copybooks/wsbatch.cob:L41] alike, and 8 bytes from `pic s9(14)`
    [sales/sl060.cbl:L206].
    """
    catalogued = {
        _descriptor_for(row[0], row[1]).byte_length
        for row in CATALOGUED_PACKED_FIELDS
    }
    program_local = {
        _work_2_descriptor().byte_length,
        _work_goods_descriptor().byte_length,
    }
    exercised = catalogued | program_local

    assert exercised == {expected for _, expected in PACKED_WIDTH_CASES}
    assert exercised == {5, 6, 8}


#  GROUP 4  -  `COMP-3` INHERITED FROM A GROUP HEADER


@pytest.mark.parametrize("column", GLBATCH_AMOUNT_COLUMNS)
def test_batch_amount_inherits_comp3_from_the_amounts_group(column: str) -> None:
    """The four batch amounts are packed because their GROUP says so.

    `03  Amounts                         comp-3.` [copybooks/wsbatch.cob:L40] is the
    only place storage is declared; the four fields below it
    [copybooks/wsbatch.cob:L41-L44] write `pic 9(9)v99.` and nothing else. A reader
    of the field line alone would call them zoned `DISPLAY`, eleven bytes each, and
    would be wrong by five bytes per field.

    Provenance: the dictionary records the inheritance explicitly, at
    `usage_declared_at` and `usage_inherited_from`, so this test asserts both rather
    than inferring the storage class from the width.
    """
    descriptor = _descriptor_for("GLBATCH-REC", column)

    assert descriptor.usage is model.Usage.COMP_3
    assert descriptor.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert descriptor.usage_inherited_from == GLBATCH_AMOUNT_GROUP

    # No `S` on the picture, so the field is unsigned and its domain starts at zero.
    assert descriptor.signed is False
    assert descriptor.digits == 11
    assert descriptor.scale == 2
    assert descriptor.byte_length == 6
    assert descriptor.value_domain == (0, 99999999999)

    # And the inherited class really does govern storage, not merely metadata.
    assert _encode(descriptor, BYTE_LITERAL_VALUE)[-1] & 0x0F == (
        cobol_usage.PACKED_SIGN_UNSIGNED
    )


def test_the_batch_amounts_are_exactly_the_four_packed_columns_of_the_batch() -> None:
    """`GLBATCH-REC` carries those four packed columns and no others.

    Locks the boundary of the group: `Dates` above it holds four `binary-long` items
    [copybooks/wsbatch.cob:L36-L39] and `Description` below it is alphanumeric
    [copybooks/wsbatch.cob:L45], so a group header understood to reach one item
    further in either direction would change the record's shape, and this is where
    that would be caught.
    """
    packed = tuple(
        entry.key.partition(".")[2]
        for entry in loader.entries_for_table("GLBATCH-REC")
        if entry.copybook is not None
        and entry.copybook.usage is model.Usage.COMP_3
    )
    assert packed == GLBATCH_AMOUNT_COLUMNS


@pytest.mark.parametrize(
    ("column", "group"),
    [(column, SYSTOT_SALES_GROUP) for column in SYSTOT_SALES_COLUMNS]
    + [(column, SYSTOT_PURCHASE_GROUP) for column in SYSTOT_PURCHASE_COLUMNS],
)
def test_period_total_inherits_comp3_from_its_ledger_group(
    column: str, group: str
) -> None:
    """All twenty period totals are packed by group inheritance, ten from each group.

    `03  Sales-Ledger-Data  comp-3.` [copybooks/wssys4.cob:L9] carries the class down
    to ten fields [copybooks/wssys4.cob:L10-L19], and
    `03  Purchase-Ledger-Data  comp-3.` [copybooks/wssys4.cob:L20] to ten more
    [copybooks/wssys4.cob:L21-L30]. The nine period-total write sites of the Sales
    and Purchase programs are the sole writers of this record, so its storage shape
    decides whether the period-end-totals scenario can diff at all.

    ANOMALY A-20 is preserved in the parameter list, not renamed: `SL4-SPARE3` and
    `SL4-SPARE4` carry the SALES prefix while sitting inside the PURCHASE group.
    """
    descriptor = _descriptor_for("SYSTOT-REC", column)

    assert descriptor.usage is model.Usage.COMP_3
    assert descriptor.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert descriptor.usage_inherited_from == group

    assert descriptor.signed is True
    assert descriptor.digits == 10
    assert descriptor.scale == 2
    assert descriptor.byte_length == 6
    assert descriptor.quantum == Decimal("0.01")


def test_the_period_totals_are_twenty_packed_columns_split_ten_and_ten() -> None:
    """Exactly twenty of `SYSTOT-REC`'s columns are packed, in a ten-ten split.

    `System-Record-4` declares exactly two packed groups of ten
    [copybooks/wssys4.cob:L9-L30] and then a filler [copybooks/wssys4.cob:L31], so
    twenty is the whole of it. The record's twenty-first dictionary entry is its key,
    which the bridge and the schema know about and no copybook declares - so it has
    no COBOL-side storage class and is excluded here rather than counted as a
    twenty-first total (R-5: the entry is reported as it is, not reshaped to fit).
    """
    entries = loader.entries_for_table("SYSTOT-REC")
    packed = tuple(
        entry
        for entry in entries
        if entry.copybook is not None
        and entry.copybook.usage is model.Usage.COMP_3
    )

    assert len(packed) == 20
    assert tuple(entry.key.partition(".")[2] for entry in packed) == (
        SYSTOT_SALES_COLUMNS + SYSTOT_PURCHASE_COLUMNS
    )

    inherited_from = [entry.copybook.usage_inherited_from for entry in packed]
    assert inherited_from.count(SYSTOT_SALES_GROUP) == 10
    assert inherited_from.count(SYSTOT_PURCHASE_GROUP) == 10
    # The ten Sales fields come first, in the copybook's own order.
    assert inherited_from == (
        [SYSTOT_SALES_GROUP] * 10 + [SYSTOT_PURCHASE_GROUP] * 10
    )


def test_total_group_carries_comp3_down_to_its_two_subordinates() -> None:
    """`03 total-group occurs 3 comp-3.` gives both children packed storage.

    Parsed from [sales/sl060.cbl:L219-L221] VERBATIM, so the assertion is against
    the declaration the compiler sees rather than against components retyped by
    hand. This is a working-storage table, not a record, so the generated dictionary
    does not catalogue it and its locator is its only traceability (R-5).

    Two facts are load-bearing. The group carries `OCCURS 3` AND `COMP-3` on the same
    line, so a parser that treated `occurs` as terminating the clause list would lose
    the storage class. And each child writes only `pic s9(7)v99.`, so the class can
    come from nowhere but the group.
    """
    parsed = cobol_picture.parse_entries(
        SL060_TOTAL_GROUP_SOURCE,
        source_path="sales/sl060.cbl",
        first_line=SL060_TOTAL_GROUP_FIRST_LINE,
    )
    assert len(parsed) == 3

    group, total_net, total_vat = parsed

    assert group.name == SL060_TOTAL_GROUP_NAME
    assert group.source_locator == "sales/sl060.cbl:L219"
    assert group.is_group is True
    assert group.occurs == SL060_TOTAL_GROUP_OCCURS
    # A group's OWN usage is GROUP; the class it hands down is kept separately.
    assert group.usage is model.Usage.GROUP
    assert group.carried_usage is model.Usage.COMP_3

    for child, expected_name, expected_locator in (
        (total_net, "total-net", "sales/sl060.cbl:L220"),
        (total_vat, "total-vat", "sales/sl060.cbl:L221"),
    ):
        assert child.name == expected_name
        assert child.source_locator == expected_locator
        assert child.parent_group == SL060_TOTAL_GROUP_NAME
        assert child.usage is model.Usage.COMP_3
        assert child.usage_declared_at is model.UsageDeclaredAt.GROUP
        assert child.usage_inherited_from == SL060_TOTAL_GROUP_NAME

        descriptor = child.descriptor
        assert descriptor is not None
        assert descriptor.source_locator == expected_locator
        assert descriptor.digits == 9
        assert descriptor.scale == 2
        assert descriptor.signed is True
        assert descriptor.byte_length == 5
        assert descriptor.is_packed is True
        assert descriptor.quantum == Decimal("0.01")


#  GROUP 5  -  ⭐ ANOMALY A-8, TRUNCATION #1:  THE ZERO-SCALE PACKED ACCUMULATOR
#
#  REPRODUCTION SITE (rule R-4, and Agent Action Plan section 0.7.4 C-3, which
#  requires a comment at each reproduction site citing the COBOL locator).
#
#  ANOMALY A-8 - "double truncation of the moving average: pence discarded into a
#  zero-decimal accumulator, then the remainder discarded by an integer divide."
#  This file owns the FIRST of those two truncations. Its three locators:
#
#    [sales/sl060.cbl:L206]  `03  work-2          pic s9(14)    comp-3.`
#                            The accumulator. Fourteen digits and SCALE ZERO - it
#                            has no room for a penny. It also carries no `value`
#                            clause, where `work-1` on the line immediately above
#                            it [sales/sl060.cbl:L205] and `work-a` and `work-b`
#                            immediately below it [sales/sl060.cbl:L207-L208] all
#                            write `value zero`.
#
#    [sales/sl060.cbl:L218]  `03  work-goods      pic s9(7)v99  comp-3.`
#                            The value added in. Nine digits, SCALE TWO.
#
#    [sales/sl060.cbl:L826]  `add      work-goods to work-2.`
#                            The discarding add, inside section `ba000-Sales-Comp`
#                            [sales/sl060.cbl:L816]. COBOL aligns the operands on
#                            their decimal points and stores into the receiving
#                            field, so the two pence digits fall off the low-order
#                            end on EVERY accumulation - not once at the end.
#
#  IT IS REPRODUCED, NOT FIXED. A defect reproduced is correct; a defect fixed is a
#  failure. The whole value of this migration is that the Python cycle can replace
#  the COBOL cycle without changing a single posted figure, and an implementation
#  that carried the pence through would diverge from the oracle on very nearly every
#  invoice. These assertions exist so that a future well-intentioned correction fails
#  the suite rather than passing unnoticed.
#
#  WHAT LIVES ELSEWHERE, and must not be duplicated here:
#    * TRUNCATION #2 - `divide sales-activety into work-2 giving sales-average.`
#      [sales/sl060.cbl:L827], which discards the remainder because
#      `Sales-Average` is `binary-long` [copybooks/wssl.cob:L49] and therefore an
#      integer - is locked by `test_comp_binary.py`.
#    * The COMPOSED two-truncation idiom, accumulate-then-divide end to end, is
#      locked by `test_compute_truncate_unrounded.py`.
#
#  AND A DIVERGENCE WORTH RECORDING, in a comment only. The same-looking idiom in
#  [sales/sl100.cbl:L497-L511] runs on `work-a` and `work-b`, which
#  [sales/sl100.cbl:L182-L183] declares as `binary-long value zero` - a DIFFERENT
#  storage mechanism reaching a similar-looking result, and with the divide operands
#  the other way round at [sales/sl100.cbl:L511]. NEITHER IS "THE DEFAULT." The
#  binary path is asserted in `test_comp_binary.py`, never here.


def test_a8_truncation_one_zero_scale_packed_accumulator_discards_the_pence() -> None:
    """A-8 #1: storing a two-decimal value into `work-2` throws the pence away.

    See the reproduction comment above for the anomaly, its three COBOL locators and
    the division of labour with the other two arithmetic files.

    Provenance: the two field descriptions are parsed from their verbatim
    declarations at [sales/sl060.cbl:L206] and [sales/sl060.cbl:L218]. The store is
    `usage.coerce` at its default rounding, `ROUND_DOWN`, because COBOL truncates
    toward zero on store unless the statement is written `ROUNDED` - and
    [sales/sl060.cbl:L826] is not.
    """
    work_2 = _work_2_descriptor()
    work_goods = _work_goods_descriptor()

    # The two declarations, as declared. The scale difference IS the anomaly.
    assert work_2.digits == 14
    assert work_2.scale == 0
    assert work_2.signed is True
    assert work_2.byte_length == 8
    assert work_2.quantum == Decimal(1)

    assert work_goods.digits == 9
    assert work_goods.scale == 2
    assert work_goods.signed is True
    assert work_goods.byte_length == 5
    assert work_goods.quantum == Decimal("0.01")

    # `work-goods` can hold the pence...
    assert work_goods.store(Decimal("12.99")) == Decimal("12.99")

    # ...and `work-2` cannot. 12.99 becomes 12: NOT 13, and NOT 12.99.
    stored = work_2.store(Decimal("12.99"))
    assert stored == Decimal(12)
    assert stored != 13
    assert stored != Decimal("12.99")

    # Truncation is TOWARD ZERO, not floor. Flooring the scaled units the way
    # Python's integer division does - `-1299 // 100` - would give -13; COBOL
    # discards the remainder and keeps the sign, giving -12.
    negative = work_2.store(Decimal("-12.99"))
    assert negative == Decimal(-12)
    assert negative != -13
    assert -1299 // 100 == -13
    assert cobol_usage.truncate_toward_zero(-1299, 100) == -12

    # The same store spelled through `usage.coerce` directly, to bind that entry
    # point too and to show the default rounding is the truncating one.
    assert (
        cobol_usage.coerce(
            Decimal("12.99"),
            usage=model.Usage.COMP_3,
            digits=14,
            scale=0,
            signed=True,
        )
        == Decimal(12)
    )


def test_a8_truncation_one_compounds_across_a_running_accumulation() -> None:
    """A-8 #1: the pence are lost on EVERY add, so the loss compounds.

    Three invoices of 12.99 accumulated one at a time through the scale-0 receiver
    total 36. The same three summed at full scale and stored once total 38. The
    difference is two whole pounds on three invoices, and it grows with the number of
    accumulations - which is why the divergence is asserted in BOTH directions here,
    so that neither figure can be quietly replaced by the other.

    See the reproduction comment above: A-8, [sales/sl060.cbl:L206],
    [sales/sl060.cbl:L218], [sales/sl060.cbl:L826]. The COBOL performs the first
    form, so 36 is what this migration must produce. 38 is what an implementation
    that "tidied up" the accumulator would produce, and it is therefore the failure
    this test exists to catch rather than an answer to prefer.
    """
    work_2 = _work_2_descriptor()
    work_goods = _work_goods_descriptor()

    invoice_goods = work_goods.store(Decimal("12.99"))
    assert invoice_goods == Decimal("12.99")

    # `add work-goods to work-2.` performed three times, exactly as
    # [sales/sl060.cbl:L826] performs it once per invoice. The receiver's carrier is
    # `int`, because its scale is zero, and it is asserted on every pass rather than
    # assumed - a `Decimal` carrier here would mean the pence had survived.
    through_the_receiver = Decimal(0)
    for _ in range(3):
        stored = work_2.store(through_the_receiver + invoice_goods)
        assert isinstance(stored, int)
        through_the_receiver = Decimal(stored)
    assert through_the_receiver == Decimal(36)

    # The same three values summed at full scale and stored once. This is what an
    # implementation that "cleaned up" the accumulator would produce.
    full_scale_total = invoice_goods + invoice_goods + invoice_goods
    assert full_scale_total == Decimal("38.97")
    stored_once = work_2.store(full_scale_total)
    assert stored_once == Decimal(38)

    # Locked in both directions: the two must NOT agree.
    assert through_the_receiver != stored_once


def test_a8_accumulator_declaration_carries_no_value_clause() -> None:
    """`work-2` is declared with no `value` clause, and that is left as it is.

    [sales/sl060.cbl:L206] verbatim, between neighbours that do initialise -
    `work-1` at [sales/sl060.cbl:L205] is `pic s9(7)v99  comp-3   value zero.` and
    `work-a` and `work-b` at [sales/sl060.cbl:L207-L208] are the same. The
    program assigns `work-2` before reading it in both consuming sections
    [sales/sl060.cbl:L821] and [sales/sl060.cbl:L823], so the omission is recorded
    here rather than compensated for: adding an initialiser would be a new behaviour
    (R-3), and asserting one exists would be a fiction.
    """
    parsed = cobol_picture.parse_entries(
        WORK_2_DECLARATION,
        source_path="sales/sl060.cbl",
        first_line=206,
    )
    assert len(parsed) == 1
    entry = parsed[0]

    assert entry.name == WORK_2_NAME
    assert entry.source_locator == WORK_2_LOCATOR
    assert entry.level == "03"
    assert entry.usage is model.Usage.COMP_3
    # Declared ON THE FIELD here, unlike the group-inherited cases above.
    assert entry.usage_declared_at is model.UsageDeclaredAt.FIELD
    assert entry.usage_inherited_from is None

    assert entry.value_keyword is None
    assert entry.value_text is None
    assert entry.value_number is None

    descriptor = entry.descriptor
    assert descriptor is not None
    assert descriptor.digits == 14
    assert descriptor.scale == 0
    assert descriptor.byte_length == 8


#  GROUP 6  -  SILENT OVERFLOW AND SILENT SIGN LOSS
#
#  `ON SIZE ERROR` occurs ZERO times across all twelve in-scope programs, and so does
#  `REMAINDER`. There is therefore no diagnostic to reproduce, and rule R-3 forbids
#  inventing one: no test below expects an exception on a value, and none expects a
#  clamp or a warning. Adding any of the three would be a new validation the COBOL
#  does not have.


def test_high_order_digits_are_discarded_silently_on_overflow() -> None:
    """A value too wide for a packed field loses its HIGH-order digits, quietly.

    A fifteen-digit value stored into `work-2` [sales/sl060.cbl:L206] keeps the
    low-order fourteen. Nothing is raised, nothing is clamped, nothing is logged -
    which is exactly what the COBOL does, there being no `ON SIZE ERROR` anywhere in
    the in-scope set to reproduce (R-3).

    Provenance: the reduction is `acas_posting/cobol/usage.py:L621-L624`, which takes
    the magnitude modulo ten to the declared digit count and reapplies the sign.
    """
    work_2 = _work_2_descriptor()
    assert work_2.digits == 14

    # 123456789012345.67 -> truncate the pence -> 123456789012345 -> fifteen digits
    # into fourteen -> the leading 1 falls off.
    assert work_2.store(Decimal("123456789012345.67")) == 23456789012345
    assert 23456789012345 == 123456789012345 % 10**14

    # The sign of the TRUNCATED result is preserved: the digits are lost, the sign is
    # not.
    assert work_2.store(Decimal("-123456789012345.67")) == -23456789012345

    # And the field still lays out in its declared width afterwards, because the
    # value was reduced INTO the field rather than overflowing it.
    raw = _encode(work_2, Decimal("123456789012345.67"))
    assert len(raw) == 8
    assert _decode(work_2, raw) == 23456789012345


def test_signed_value_stored_into_an_unsigned_packed_field_loses_its_sign() -> None:
    """Storing a negative into an unsigned packed field drops the sign, silently.

    `Input-Gross` is `pic 9(9)v99` under `03 Amounts comp-3.`
    [copybooks/wsbatch.cob:L40-L41] - no `S`, so no sign. -5.00 becomes 5.00 and the
    sign nibble is `0xF` rather than `0xD`. Nothing is raised (R-3).

    This is the same class of loss that anomaly A-11 records at the bridge boundary
    for `Sales-Average` - a signed value narrowed into an unsigned host variable and
    an unsigned column - but reached here through the COPYBOOK's own declaration
    rather than through the bridge. A-11's own site is the data-access layer and is
    not asserted here.
    """
    descriptor = _descriptor_for("GLBATCH-REC", "INPUT-GROSS")
    assert descriptor.signed is False

    assert descriptor.store(Decimal("-5.00")) == Decimal("5.00")
    assert (
        cobol_usage.coerce(
            Decimal("-5.00"),
            usage=model.Usage.COMP_3,
            digits=11,
            scale=2,
            signed=False,
        )
        == Decimal("5.00")
    )

    negative_bytes = _encode(descriptor, Decimal("-1234.56"))
    positive_bytes = _encode(descriptor, Decimal("1234.56"))
    assert negative_bytes[-1] & 0x0F == cobol_usage.PACKED_SIGN_UNSIGNED
    # The two are INDISTINGUISHABLE once stored, which is the whole point.
    assert negative_bytes == positive_bytes == INPUT_GROSS_BYTES_UNSIGNED
    assert _decode(descriptor, negative_bytes) == Decimal("1234.56")


def test_the_batch_amount_digit_drift_is_reported_and_not_adjudicated() -> None:
    """The batch amounts' three layer views disagree, and the disagreement stands.

    `Input-Gross` is eleven digits in [copybooks/wsbatch.cob:L41] and fourteen in
    both the bridge host variable and the column. The generated dictionary carries
    ALL THREE views and flags the disagreement; it names no winner, and neither does
    this test (R-5). The entry also carries anomaly A-15 - the batch record's declared
    length contradicting the sum of its fields - and ambiguity Q-4, the question of
    which of the two governs the record actually read, which only the compiled
    program can settle (R-6).

    What IS asserted is that the copybook view is what drives storage in this tier,
    because the copybook is the declaration the COBOL program compiles against; the
    bridge's own conversion belongs to the data-access layer and is out of scope
    here.
    """
    descriptor = _descriptor_for("GLBATCH-REC", "INPUT-GROSS")
    drift = descriptor.drift()

    assert drift is not None
    # The disagreement is reported, per axis.
    assert drift.digits is True
    assert drift.usage is True
    assert drift.scale is False
    assert drift.signedness is False
    # And it is described rather than resolved: the detail names all three views.
    assert any("11 digits" in detail for detail in drift.details)
    assert any("14 digits" in detail for detail in drift.details)

    # The register references travel with the field, so a reader of a failing test
    # reaches the anomaly log and the ambiguity log without leaving the file.
    assert "A-15" in descriptor.anomaly_refs()
    assert "Q-4" in descriptor.ambiguity_refs()

    # Storage in this tier follows the COPYBOOK view, unadjudicated: eleven digits.
    assert descriptor.digits == 11
    assert descriptor.byte_length == 6


def test_every_packed_field_reports_the_bridge_storage_class_change() -> None:
    """Every in-scope packed field's storage class changes at the bridge, reportedly.

    A copybook `COMP-3` becomes a `COMP` host variable and then a `DECIMAL` column.
    The dictionary flags that on the `usage` axis for all of them. It is recorded
    here so the flag cannot be mistaken for a per-field oddity, and no view is
    declared to win (R-5).
    """
    for table, column, *_ in CATALOGUED_PACKED_FIELDS:
        descriptor = _descriptor_for(table, column)
        drift = descriptor.drift()
        assert drift is not None, f"{descriptor!r} carries no drift record"
        assert drift.usage is True, f"{descriptor!r} reports no storage-class change"
        assert any(
            "COMP-3" in detail for detail in drift.details
        ), f"{descriptor!r} does not name its copybook class in its drift detail"


#  GROUP 7  -  CARRIER GUARANTEES AND TIER HYGIENE


def test_the_packed_carrier_follows_the_scale_and_is_never_binary() -> None:
    """A packed field's Python carrier is `Decimal` when scaled and `int` when not.

    The rule is `python_storage_for`: a fractional part means `DECIMAL`, none means
    `INT`. It is not cosmetic. `work-2` being an `int` is half of why A-8 is
    reproducible at all, and no value on either branch is ever carried in binary
    floating point (R-2).
    """
    assert (
        cobol_usage.python_storage_for(model.Usage.COMP_3, 2)
        is model.CobolPythonStorage.DECIMAL
    )
    assert (
        cobol_usage.python_storage_for(model.Usage.COMP_3, 0)
        is model.CobolPythonStorage.INT
    )

    scaled = _descriptor_for("GLLEDGER-REC", "LEDGER-BALANCE")
    assert scaled.scale == 2
    assert scaled.python_storage is model.CobolPythonStorage.DECIMAL
    assert scaled.is_decimal is True
    assert scaled.is_int is False
    scaled_value = scaled.store(Decimal("1234.56"))
    assert isinstance(scaled_value, Decimal)
    assert not isinstance(scaled_value, float)
    assert not isinstance(scaled_value, str)

    unscaled = _work_2_descriptor()
    assert unscaled.scale == 0
    assert unscaled.python_storage is model.CobolPythonStorage.INT
    assert unscaled.is_int is True
    assert unscaled.is_decimal is False
    unscaled_value = unscaled.store(Decimal("12.99"))
    assert isinstance(unscaled_value, int)
    assert not isinstance(unscaled_value, float)
    assert not isinstance(unscaled_value, str)

    # Both carriers compare exactly against an exact literal, which is the property
    # R-2 exists to protect.
    assert scaled_value == Decimal("1234.56")
    assert unscaled_value == Decimal(12)


def test_packed_is_distinguished_from_every_other_storage_class() -> None:
    """`COMP-3` is recognised as packed, and nothing else is.

    Six numeric storage classes must be modelled because collapsing any of them
    changes stored values (R-2). This file owns one; the predicate that separates it
    from the other five is asserted here so that no other file has to. The five it is
    separated from are all live in the frozen copybooks: zoned `DISPLAY`
    [copybooks/wsledger.cob:L14], `COMP` [copybooks/wssl.cob:L42], `DISPLAY` with
    `SIGN LEADING` [copybooks/wspost-irs.cob:L21], and the
    `BINARY-CHAR`/`BINARY-SHORT`/`BINARY-LONG` family
    [copybooks/wssystem.cob:L65], [copybooks/wssl.cob:L43], [copybooks/wssl.cob:L49].
    """
    assert cobol_usage.is_packed(model.Usage.COMP_3) is True
    # Both spellings the dictionary and the raw artifact use reach the same member.
    assert cobol_usage.is_packed("COMP-3") is True

    for other in (
        model.Usage.DISPLAY,
        model.Usage.COMP,
        model.Usage.COMP_5,
        model.Usage.BINARY_CHAR,
        model.Usage.BINARY_SHORT,
        model.Usage.BINARY_LONG,
        model.Usage.ALPHANUMERIC,
        model.Usage.GROUP,
    ):
        assert cobol_usage.is_packed(other) is False, f"{other.value} read as packed"

    # A packed item is numeric and is not a member of the native binary family, whose
    # width comes from the hardware rather than from a picture.
    assert cobol_usage.is_numeric(model.Usage.COMP_3) is True
    assert cobol_usage.is_binary_family(model.Usage.COMP_3) is False
    assert cobol_usage.is_zoned_display(model.Usage.COMP_3) is False
    assert cobol_usage.is_alphanumeric(model.Usage.COMP_3) is False
    assert cobol_usage.is_group(model.Usage.COMP_3) is False


def test_the_arithmetic_tier_imported_no_driver_no_database_and_no_oracle() -> None:
    """R-1: importing this module pulled in no COBOL, no database and no float library.

    Asserted against `_MODULES_PRESENT_AT_IMPORT`, the snapshot taken as this module
    finished importing, rather than against live `sys.modules`. The distinction
    matters: a scenario module collected later in the same session imports a driver
    quite legitimately, and rule R-1's claim is about what THIS TIER reaches for.

    The claim being locked is that the infrastructure-free tier really is
    infrastructure-free - it runs on a host with no Docker, no MariaDB and no
    GnuCOBOL, its only file-system prerequisite being the generated data dictionary.
    """
    assert "mysql.connector" not in _MODULES_PRESENT_AT_IMPORT

    imported_top_level = {name.partition(".")[0] for name in _MODULES_PRESENT_AT_IMPORT}
    trespassers = sorted(imported_top_level & _FORBIDDEN_TOP_LEVEL_MODULES)
    assert not trespassers, (
        "the arithmetic tier imported "
        + ", ".join(trespassers)
        + " - it must touch neither COBOL nor a database (R-1) and must compute in "
        "no binary float (R-2)"
    )

    reached = sorted(
        name
        for name in _MODULES_PRESENT_AT_IMPORT
        if name.startswith(_FORBIDDEN_PACKAGE_PREFIXES)
    )
    assert not reached, (
        "the arithmetic tier reached into "
        + ", ".join(reached)
        + " - the data-access layer, the CLI and the program modules all sit below "
        "it and none may be imported from here (R-1)"
    )

    # And exactly which migration modules THIS FILE binds, read off its own global
    # namespace rather than off a session-wide snapshot. This is the precise form of
    # the tier contract: the storage-semantics layer and the dictionary, and nothing
    # else. It also means the test cannot pass by having imported nothing at all.
    bound = frozenset(
        value.__name__
        for value in globals().values()
        if isinstance(value, ModuleType)
        and value.__name__.startswith("acas_posting")
    )
    assert bound == _ACAS_MODULES_THIS_FILE_IMPORTS


def test_the_generated_dictionary_is_this_tier_s_only_prerequisite(
    data_dictionary_path: Path,
) -> None:
    """The one file this tier needs is present, and it is a FILE and not a service.

    Every assertion above that names a `<TABLE-NAME>.<COLUMN-NAME>` key reads the
    generated artifact through `acas_posting.dictionary.loader`, so its absence would
    fail this whole file - which is a file-system dependency and not an
    infrastructure one. That distinction is what lets this tier run on a host with no
    Docker, no MariaDB and no GnuCOBOL (R-1).

    The path arrives through `tests/conftest.py`'s session fixture rather than being
    composed here, so there is exactly one definition of where the artifact lives.
    """
    assert data_dictionary_path.is_file()
    assert data_dictionary_path.name == "acas_posting_dictionary.json"

    # And the loader really is reading THAT document: a key asserted above resolves
    # against the same path when it is passed explicitly.
    key = _resolve_entry_key("GLLEDGER-REC", "LEDGER-BALANCE")
    entry = loader.get_entry(key, path=data_dictionary_path)
    assert entry.key == key
    assert entry.copybook is not None
    assert entry.copybook.usage is model.Usage.COMP_3
