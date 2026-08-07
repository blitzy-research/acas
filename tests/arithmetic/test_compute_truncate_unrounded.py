"""TRUNCATION IS THE DEFAULT for every un-`ROUNDED` store, and the three
moving-average idioms must never be unified.

This is the primary anomaly-locking file of the arithmetic tier. It proves two
things that no other file in the suite proves, and it exists because getting
either of them backwards would corrupt essentially every posted figure.

FIRST, that a store WITHOUT `ROUNDED` truncates toward zero. The migrated cycle
contains exactly FIVE `ROUNDED` sites - [general/gl080.cbl:L328],
[general/gl051.cbl:L791], [general/gl051.cbl:L796], [irs/irs030.cbl:L1551] and
[irs/irs030.cbl:L1562] - and every other store truncates. Agent Action Plan
section 0.1.1, verbatim: "Every other store truncates. Getting this backwards
would corrupt essentially every posted figure, so truncation is the default and
rounding is the annotated exception." The `ROUNDED` half of that pair is the
sibling file `test_compute_rounded_half_up.py`; this file owns the default.

SECOND, that the three moving-average idioms are irreconcilable. They are
locked here as anomalies A-8, A-9 and A-10:

* A-8  DOUBLE TRUNCATION of the moving average. `work-2` is
       `pic s9(14) comp-3` with ZERO decimal places [sales/sl060.cbl:L206]
       while `work-goods` carries two [sales/sl060.cbl:L218], so pence are
       discarded on every accumulation [sales/sl060.cbl:L826]; then
       `Sales-Average` is `binary-long` [copybooks/wssl.cob:L49], an INTEGER,
       so the divide discards the remainder [sales/sl060.cbl:L827].
* A-9  The credit-note path NEVER INCREMENTS its activity counter and wraps
       both the accumulate and the divide in an extra outer guard
       [sales/sl060.cbl:L832-L843], so a customer's FIRST credit note is
       silently dropped.
* A-10 THREE MUTUALLY INCONSISTENT GUARDS on one idiom - two conditions
       [sales/sl060.cbl:L819], the same two behind an extra outer test
       [sales/sl060.cbl:L835], and one condition with no ELSE at all
       [sales/sl100.cbl:L506] - and the variant carrying that third guard also
       writes its divide the other way round [sales/sl100.cbl:L511].

Agent Action Plan section 0.6.1, verbatim, is the sentence this file exists to
honour: "Normalising them into one helper would be the single easiest way to
fail this migration."
`test_a_unified_moving_average_helper_cannot_reproduce_all_three_idioms` makes
that normalisation FAIL, so a future well-intentioned correction breaks the suite
instead of passing unnoticed.

WHAT THIS FILE DELIBERATELY DOES NOT DUPLICATE. A-8 is caused by FIELD WIDTHS
rather than by arithmetic, and its two storage-class components are locked by
two sibling files: truncation #1, the packed-decimal accumulator with zero
decimal places, belongs to `test_comp3_packed_decimal.py`, and truncation #2,
the integer divide into a `binary-long`, belongs to `test_comp_binary.py`.
Neither is re-proved here. What IS proved here, and only here, is the two
truncations acting TOGETHER through the verbs, end to end, in the order the
frozen source writes them.

THE SIX RULES, as they bind this file. There is NO user rules document: the
`review_rules` facility reports "No user rules provided.", so the binding rules
are the six requirement-embedded rules restated in Agent Action Plan section
0.7.2, and enterprise-standard best practice applies wherever they are silent.

* R-1 No COBOL at runtime. This file imports no COBOL, spawns no process,
      reaches no database and never touches `harness/`. The compiled oracle is
      consumed only by `tests/scenarios/*` and `tests/determinism/*`.
* R-2 Zero binary floating point. Every value is `decimal.Decimal`, `int` or a
      numeric `str`. There is no tolerance, no `approx` and no float carrier -
      and `test_store_refuses_a_binary_float_carrier` proves the production
      tripwire that enforces it. The ambient `decimal` context is read or
      written in exactly one test, the deliberate sabotage of
      `test_ambient_decimal_context_cannot_change_a_store`, which restores it in
      a `finally`.
* R-3 No new validations. `ON SIZE ERROR` and `REMAINDER` occur ZERO times
      across the twelve in-scope programs, so there is NO overflow handler in
      the specification: an over-range store silently keeps the low-order
      digits and raises nothing. Nothing here is clamped, warned about or
      refused on the strength of a VALUE. Execution is strictly sequential; no
      parallel runner is used.
* R-4 Anomalies reproduced, never fixed. Agent Action Plan section 0.8.2,
      verbatim: "There is no test suite: compiled COBOL execution is the
      behavioral specification, defects included. A defect reproduced is
      correct; a defect fixed is a failure." Every anomaly-locking test below
      names its anomaly number and its `[path:Lnnn]` locator, per section 0.7.4
      C-3's requirement of "a comment at each reproduction site citing the COBOL
      locator". A test that asserted CORRECT ACCOUNTING rather than OBSERVED
      BEHAVIOUR would itself be a defect.
* R-5 Full traceability. Every descriptor cites a data-dictionary key or a
      `<path>:L<n>` source locator, and
      `test_every_locator_and_key_this_file_cites_is_well_formed` checks the
      citations mechanically. Coverage is evidence, never a gate: this file adds
      no coverage threshold of any kind.
* R-6 Compiled behaviour is the tie-breaker. Expected values come from behaviour
      recorded in the production modules against GnuCOBOL 3.2.0, never from reading
      the COBOL and reasoning about what it ought to produce - and where a value is
      NOT arbitrated, the question is named rather than the value guessed.

THE Q- REGISTER, and why this file carries NO `xfail`. Rule R-6 requires an
un-arbitrated value to be marked `pytest.mark.xfail(strict=True)` against a
named question. Every value this file asserts is ARBITRATED, so a strict
`xfail` would XPASS and fail the suite:

* Q-2  the intermediate precision and the truncation direction. ⭐ ITS TWO HALVES
       HAVE DIFFERENT STATUSES, and this file depends only on the settled one. The
       TRUNCATION DIRECTION on an un-`ROUNDED` store is settled - it is the language's,
       and `acas_posting/cobol/arithmetic.py` states it beside `TRUNCATING_STORE`. The
       NUMBER OF INTERMEDIATE DIGITS is a property of the compiler build and is
       PENDING in `docs/migration/ambiguity-resolutions.md`. Every figure below is
       reached by a single store from operands well inside the receiver's declared
       digits, so no assertion here would change whichever way the open half lands;
       the one figure that would is in `tests/arithmetic/test_irs_vat_from_gross.py`
       and is marked there.
* Q-7  a zero divisor. RESOLVED, and the resolution overturned the provisional
       answer: the compiled program stores NOTHING and carries on, which
       `arithmetic.SizeErrorNoStore` documents. No idiom below reaches it,
       because each frozen idiom guards its own divisor.
* Q-5.1 / Q-5.2 / Q-5.3  the binary width policy, the leading-sign width and
       the zoned overpunch bytes. All three recorded RESOLVED in
       `acas_posting/cobol/usage.py`.
* Q-3  the SIGNED-THROUGH-UNSIGNED question - and it is a BRIDGE-side question,
       not a field-side one. It asks what a `binary-long signed` value becomes
       through a `PIC 9(10) COMP` host variable and into an `int unsigned`
       column [copybooks/wssl.cob:L46-L52] -> [common/salesMT.cbl:L305-L312],
       which is anomaly A-11 and belongs to `acas_posting/dal/*`;
       `acas_posting/dal/acas007_gl_batch.py` records it as resolved against
       GnuCOBOL 3.2. What THIS file asserts is the different, field-side store
       into an item whose own PICTURE is unsigned - `pic 9(9)v99` under
       `03 Amounts comp-3.` [copybooks/wsbatch.cob:L40-L41] - which is
       language-level COBOL and settled: the sign is dropped and the magnitude
       is stored.

THE VERB CENSUSES over the twelve in-scope programs, recounted in this checkout
so the figures are this file's own rather than inherited. The convention is
non-comment lines on which the verb appears:

    MOVE      1250   (gl071 contributes ZERO - it is a pure sort)
    ADD        268   of which 32 are GIVING; the widest is FIVE sources, at
                     [sales/sl060.cbl:L523]
    SUBTRACT    82   of which 29 are GIVING. `SUBTRACT a FROM b GIVING c` is
                     `c = b - a` [general/gl051.cbl:L1105]
    MULTIPLY    50   of which 25 are GIVING
    DIVIDE      17   = 13 `BY ... GIVING` + 4 `INTO ... GIVING`, every one of
                     the seventeen written with GIVING
    COMPUTE      5   live, the two commented-out variants at
                     [irs/irs030.cbl:L1550] and [irs/irs030.cbl:L1561] excluded

The brief for this file quotes 1290 MOVEs and 269 ADDs, which is a different
counting convention rather than a disagreement about the source - counting
commented-out and continuation lines moves both figures. The other four counts
agree exactly, and the figures above are the ones this file stands behind.

The DIVIDE census is the one asserted rather than merely stated, because the two
spellings take their operands in opposite order and a reversal is silent. The
four `INTO ... GIVING` sites are exactly [sales/sl060.cbl:L827],
[sales/sl060.cbl:L843], [purchase/pl060.cbl:L751] and [purchase/pl060.cbl:L766];
the thirteen `BY ... GIVING` sites are enumerated in `_DIVIDE_BY_GIVING_SITES`.

TWO TRAPS worth naming, because both cost time to see. `compute-sales-pay.`
[sales/sl100.cbl:L497] and `compute-purch-pay.` [purchase/pl100.cbl:L488] are
PARAGRAPH NAMES, not `COMPUTE` verbs, and neither belongs in the COMPUTE census.
And the brief for this file cites the `sl100` `line-cnt` declaration at L179;
the declaration verified in the frozen source is at
[sales/sl100.cbl:L173] - L179 is `j-deduct pic s9(7)v99 comp-3` - so L173 is
cited throughout.

HOW TO RUN IT. From the repository root, with no Docker, no MariaDB and no
GnuCOBOL, and with `data_dictionary/acas_posting_dictionary.json` present:

    pytest tests/arithmetic/test_compute_truncate_unrounded.py
    pytest -m arithmetic
"""

from __future__ import annotations

import contextlib
import importlib
import decimal
import sys
import types
from collections.abc import Iterator
from decimal import Decimal
from typing import Final

import pytest

from acas_posting.cobol import arithmetic
from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
# Dictionary-key resolution, defensively, and local to this file
# ---------------------------------------------------------------------------
#
# `loader.DictionaryKeyError` is a `KeyError` subclass whose message already
# lists near misses, so a mistyped key reports itself clearly. What it cannot do
# is survive a key whose COLUMN segment is spelled as the copybook spells it
# rather than as the schema does - `SALES-AVERAGE` against `Sales-Average` - and
# that is the one slip a hand-written test makes. The resolver below therefore
# falls back to `loader.entries_for_table`, matching case-insensitively, and
# re-raises with the table's own column list when even that fails.
#
# It resolves a KEY and does nothing else. It encodes no part of any idiom, sets
# up no state and is shared by no two tests in the sense section 4.4 forbids.


class _KeyResolutionError(KeyError):
    """A dictionary key could not be resolved even by the table fallback.

    A subclass of `KeyError` for the same reason `loader.DictionaryKeyError` is
    one: a caller already catching `KeyError` keeps working.
    """


def _dictionary_descriptor(key: str) -> cobol_field.FieldDescriptor:
    """Build the descriptor the generated dictionary holds for one key.

    Args:
        key: A qualified entry key - `<TABLE-NAME>.<COLUMN-NAME>` or
            `<PROGRAM-RECORD>.<FIELD-NAME>#<line>`.

    Returns:
        The `FieldDescriptor` for that field, carrying its dictionary key and
            the locator of the declaration it was built from.

    Raises:
        _KeyResolutionError: Neither the key itself nor a case-insensitive match
            on its table resolved.
    """
    try:
        return cobol_field.FieldDescriptor.from_dictionary_key(key)
    except loader.DictionaryKeyError as unknown:
        table, _, column = key.partition(".")
        if not column:
            raise _KeyResolutionError(str(unknown)) from unknown
        try:
            entries = loader.entries_for_table(table)
        except loader.DictionaryLookupError as no_table:
            raise _KeyResolutionError(str(no_table)) from unknown
        wanted = column.casefold()
        for entry in entries:
            if entry.key.rpartition(".")[2].casefold() == wanted:
                return cobol_field.FieldDescriptor.from_dictionary_key(entry.key)
        raise _KeyResolutionError(
            f"{key!r} names no field of {table!r}. Its columns are: "
            + ", ".join(entry.key.rpartition(".")[2] for entry in entries)
        ) from unknown


def _working_storage(
    *,
    name: str,
    source_locator: str,
    usage: model.Usage,
    picture: str | None = None,
    signed: bool = False,
    sign_position: model.SignPosition = model.SignPosition.NONE,
    digits: int | None = None,
    integer_digits: int | None = None,
    scale: int | None = None,
    usage_declared_at: model.UsageDeclaredAt = model.UsageDeclaredAt.FIELD,
    parent_group: str | None = None,
    level: str = "03",
) -> cobol_field.FieldDescriptor:
    """Describe one WORKING-STORAGE item from its own declaration.

    The generated dictionary catalogues the fields that reach a table and the
    work-file records the General Ledger programs declare inline, but NOT a
    program's own WORKING-STORAGE - `work-2` never reaches a column. Such an item
    is therefore described from its declaration, with the `<path>:L<n>` locator
    that is the only traceability it will ever have (rule R-5).

    The carrier is DERIVED rather than passed, by `usage.python_storage_for`,
    because `FieldDescriptor.__post_init__` requires a key-less descriptor to
    name the carrier its own usage and scale imply - and deriving it is what
    makes `work-2` an `int` and `work-goods` a `Decimal` without either being
    asserted by hand here.

    Args:
        name: The field name, verbatim from the declaration.
        source_locator: `<path>:L<n>` for the declaring line.
        usage: The storage class the declaration carries.
        picture: The PICTURE clause as written, or None for a picture-less item.
        signed: Whether the declaration carries a sign.
        sign_position: Where the sign lives.
        digits: Total declared digits, or None for the binary family.
        integer_digits: Digits before the implied decimal point.
        scale: Digits after it.
        usage_declared_at: Whether USAGE sat on the item or the language default
            governed.
        parent_group: The group immediately above the item.
        level: The level number as written.

    Returns:
        The `FieldDescriptor` for that declaration.
    """
    del level  # Recorded in the calling comment; the descriptor has no member.
    return cobol_field.FieldDescriptor(
        name=name,
        usage=usage,
        usage_declared_at=usage_declared_at,
        picture=picture,
        signed=signed,
        sign_position=sign_position,
        digits=digits,
        integer_digits=integer_digits,
        scale=scale,
        python_storage=cobol_usage.python_storage_for(usage, scale),
        source_locator=source_locator,
        parent_group=parent_group,
    )


# ---------------------------------------------------------------------------
# The receiving fields the groups below store into
# ---------------------------------------------------------------------------
#
# Every one is a REAL declaration in the frozen source, reached by its dictionary
# key where the dictionary catalogues it and described from its own declaration
# where it does not. Nothing here is a picture invented to make a test convenient.
#
# THE THREE MOVING-AVERAGE TESTS USE NONE OF THESE. Each builds its own
# descriptors inline, which is deliberate duplication - see the comment above
# `test_a8_sl060_sales_comp_double_truncation_end_to_end`.

#: `03 Post-Amount pic s9(8)v99.` [copybooks/wspost.cob:L23] - signed, ten
#: digits, two decimal places, and the field the baseline table truncates into.
_POST_AMOUNT: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "GLPOSTING-REC.POST-AMOUNT"
)

#: `05 Input-Gross pic 9(9)v99.` under `03 Amounts comp-3.`
#: [copybooks/wsbatch.cob:L40-L41] - UNSIGNED, which is the whole point: a
#: negative value stored here loses its sign at the field, before any SQL.
_INPUT_GROSS: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "GLBATCH-REC.INPUT-GROSS"
)

#: `03 sih-deduct-amt pic 999v99 comp.` [copybooks/slwsinv.cob:L63] - FIVE
#: digits and unsigned, so it is the narrow receiver the overflow rows need.
_IH_DEDUCT_AMT: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "SAINVOICE-REC.IH-DEDUCT-AMT"
)

#: `03 OI-Deduct-Amt pic s999v99 comp.` [copybooks/slwsoi.cob:L51] - the same
#: five digits SIGNED, so the pair isolates signedness from width.
_OI3_DEDUCT_AMT: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "SAITM3-REC.OI3-DEDUCT-AMT"
)

#: `03 Ledger-Balance pic s9(8)v99 comp-3.` [copybooks/wsledger.cob:L28] - the
#: nominal-ledger accumulator `gl072` posts into.
_LEDGER_BALANCE: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

#: `03 pre-amount pic s9(8)v99.` [general/gl070.cbl:L115] - a work-file field,
#: which the dictionary DOES catalogue, and the receiver of both the two-source
#: `ADD ... GIVING` [general/gl070.cbl:L504] and the two sign flips
#: [general/gl070.cbl:L517], [general/gl070.cbl:L530].
_PRE_AMOUNT: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "pre-trans-record.pre-amount#115"
)

#: `05 Page-Lines binary-char unsigned.` [copybooks/wssystem.cob:L65] - the
#: right-hand operand of all six relation conditions, domain (0, 255).
_PAGE_LINES: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "SYSTEM-REC.PAGE-LINES"
)

#: `77 a pic 99 value zero.` [general/gl080.cbl:L183] - the quarter subscript the
#: only ROUNDED divide in the cycle lands in [general/gl080.cbl:L328]. Two digits,
#: unsigned, scale zero, so its carrier is `int`.
_QUARTER_SUBSCRIPT: Final[cobol_field.FieldDescriptor] = _working_storage(
    name="a",
    source_locator="general/gl080.cbl:L183",
    usage=model.Usage.DISPLAY,
    usage_declared_at=model.UsageDeclaredAt.DEFAULT,
    picture="99",
    digits=2,
    integer_digits=2,
    scale=0,
    level="77",
)

#: `03 line-cnt pic 99 comp value zero.` [sales/sl060.cbl:L223] - binary bounded
#: by a DECLARED DIGIT COUNT.
_LINE_CNT_SL060: Final[cobol_field.FieldDescriptor] = _working_storage(
    name="line-cnt",
    source_locator="sales/sl060.cbl:L223",
    usage=model.Usage.COMP,
    picture="99",
    digits=2,
    integer_digits=2,
    scale=0,
    parent_group="ws-data",
)

#: `03 line-cnt binary-char value zero.` [sales/sl100.cbl:L173] - THE SAME
#: FIELD NAME in a sibling program, declared in a DIFFERENT storage class whose
#: range comes from its WIDTH rather than from a picture. The divergence is
#: preserved, not normalised: `sl060`'s item saturates its two digits at 99 while
#: `sl100`'s is a signed byte spanning (-128, 127).
_LINE_CNT_SL100: Final[cobol_field.FieldDescriptor] = _working_storage(
    name="line-cnt",
    source_locator="sales/sl100.cbl:L173",
    usage=model.Usage.BINARY_CHAR,
    signed=True,
    sign_position=model.SignPosition.IMPLICIT_BINARY,
    parent_group="ws-data",
)

#: `03 work-net pic s9(7)v99 comp-3.` [sales/sl060.cbl:L216] - the receiver of
#: the widest `ADD ... GIVING` in the cycle, five sources at
#: [sales/sl060.cbl:L523].
_WORK_NET: Final[cobol_field.FieldDescriptor] = _working_storage(
    name="work-net",
    source_locator="sales/sl060.cbl:L216",
    usage=model.Usage.COMP_3,
    picture="s9(7)v99",
    signed=True,
    sign_position=model.SignPosition.IMPLICIT_BINARY,
    digits=9,
    integer_digits=7,
    scale=2,
    parent_group="ws-data",
)


# ---------------------------------------------------------------------------
# The censuses, as data
# ---------------------------------------------------------------------------
#
# Written as tuples rather than as prose so that a test can count them, and so
# that a reader who doubts a figure has the locator to check rather than a number
# to trust.

#: Every `DIVIDE ... BY ... GIVING` in the twelve in-scope programs: the quotient
#: is the FIRST operand over the second. Nine are scalings by 100 or 10, one is
#: the leap-year test, and three are computations of substance.
_DIVIDE_BY_GIVING_SITES: Final[tuple[str, ...]] = (
    "general/gl051.cbl:L604",  # divide post-dr by 100 giving acc-ok
    "general/gl051.cbl:L607",  # divide post-cr by 100 giving acc-ok
    "general/gl051.cbl:L1035",  # divide post-dr by 100 giving l7-dr
    "general/gl051.cbl:L1037",  # divide post-cr by 100 giving l7-cr
    "general/gl051.cbl:L1044",  # divide vat-ac ... by 100 giving l7-vat-ac
    "general/gl072.cbl:L386",  # divide WS-Ledger-Nos by 100 giving l6-account
    "general/gl072.cbl:L413",  # divide WS-Ledger-Nos by 100 giving l6-account
    "general/gl080.cbl:L328",  # divide scycle by period giving a ROUNDED
    "sales/sl100.cbl:L511",  # divide work-b by sales-pay-activety giving ...
    "purchase/pl100.cbl:L502",  # divide work-b by purch-pay-activety giving ...
    "irs/irs030.cbl:L1074",  # divide ws-nstrg by 100 giving amt-ok
    "irs/irs030.cbl:L1077",  # divide ws-nstrg by 10 giving amt-ok
    "irs/irs030.cbl:L1333",  # divide u-year by 4 giving ws-work1
)

#: Every `DIVIDE ... INTO ... GIVING` in the twelve in-scope programs: the
#: quotient is the SECOND operand over the first. All four are the moving-average
#: idiom, two per program, and there are no others anywhere in the cycle.
_DIVIDE_INTO_GIVING_SITES: Final[tuple[str, ...]] = (
    "sales/sl060.cbl:L827",  # divide sales-activety into work-2 giving ...
    "sales/sl060.cbl:L843",  # divide sales-activety into work-2 giving ...
    "purchase/pl060.cbl:L751",  # divide purch-activety into work-2 giving ...
    "purchase/pl060.cbl:L766",  # divide purch-activety into work-2 giving ...
)

#: Every `ROUNDED` site in the cycle. Five, and no more - which is why
#: `rounded=False` is the default at every call in this file.
_ROUNDED_SITES: Final[tuple[str, ...]] = (
    "general/gl051.cbl:L791",  # compute vat-amount rounded = ... * rate / 100
    "general/gl051.cbl:L796",  # compute vat-amount rounded = ... VAT from gross
    "general/gl080.cbl:L328",  # divide scycle by period giving a rounded
    "irs/irs030.cbl:L1551",  # compute vat-amount rounded = ... * rate / 100
    "irs/irs030.cbl:L1562",  # compute vat-amount rounded = ... VAT from gross
)

#: The `multiply ... by -1` sign-flip census: twenty-seven entries across NINE
#: programs, every one un-`ROUNDED`, so every one truncates on store and every one
#: into an unsigned receiver would drop the sign it has just applied.
#:
#: TWO OF THE ENTRIES ARE SPANS rather than single lines -
#: [sales/sl055.cbl:L658-L666] is the nine-field credit-note negation block and
#: [purchase/pl055.cbl:L572-L575] is its four-field Purchase counterpart - so the
#: twenty-seven entries expand to thirty-eight statements. Counted directly in
#: this checkout there are THIRTY-NINE live `multiply ... -1` statements; the one
#: this census does not name is [irs/irs030.cbl:L1083]
#: `multiply -1 by amt-ok`, the no-GIVING spelling inside the IRS amount scaling.
#: Two further occurrences are commented out and correctly excluded,
#: [irs/irs030.cbl:L1006] and [irs/irs030.cbl:L1026].
_SIGN_FLIP_SITES: Final[tuple[str, ...]] = (
    "general/gl070.cbl:L517",
    "general/gl070.cbl:L530",
    "general/gl080.cbl:L493",
    "general/gl080.cbl:L506",
    "sales/sl055.cbl:L446",
    "sales/sl055.cbl:L457",
    "sales/sl055.cbl:L463",
    "sales/sl055.cbl:L658-L666",
    "sales/sl060.cbl:L571",
    "sales/sl060.cbl:L758",
    "sales/sl060.cbl:L861",
    "sales/sl100.cbl:L395",
    "purchase/pl055.cbl:L376",
    "purchase/pl055.cbl:L387",
    "purchase/pl055.cbl:L572-L575",
    "purchase/pl060.cbl:L507",
    "purchase/pl060.cbl:L683",
    "purchase/pl060.cbl:L783",
    "purchase/pl100.cbl:L387",
    "irs/irs030.cbl:L947",
    "irs/irs030.cbl:L963",
    "irs/irs030.cbl:L1096",
    "irs/irs030.cbl:L1125",
    "irs/irs030.cbl:L1127",
    "irs/irs030.cbl:L1139",
    "irs/irs030.cbl:L1141",
    "irs/irs030.cbl:L1179",
)

#: The six relation-condition sites, every one of the shape
#: `if line-cnt > Page-Lines - <n>`. There is no receiving field anywhere in that
#: expression, so there is nothing for COBOL to truncate to.
_RELATION_CONDITION_SITES: Final[tuple[str, ...]] = (
    "general/gl051.cbl:L1060",  # > Page-Lines - 6
    "general/gl051.cbl:L1111",  # > Page-Lines - 12
    "sales/sl060.cbl:L621",  # > Page-Lines - 7
    "sales/sl060.cbl:L691",  # > Page-Lines - 6 and ...
    "purchase/pl060.cbl:L556",  # > Page-Lines - 7
    "purchase/pl060.cbl:L619",  # > Page-Lines - 6 and ...
)


# ---------------------------------------------------------------------------
# 4.1  TRUNCATION IS THE DEFAULT - the baseline table
# ---------------------------------------------------------------------------

#: `(value, receiving field, expected, why)`, one row per baseline case. Each
#: expected value is what `usage.coerce` - the single audited store path - does
#: with the field's own digits, scale and signedness, all three read from the
#: frozen declaration rather than chosen here.
_BASELINE_TRUNCATION_TABLE: Final[tuple[tuple[str, object, object, str], ...]] = (
    (
        "1.999",
        _POST_AMOUNT,
        Decimal("1.99"),
        "two decimal places, TRUNCATED toward zero - not 2.00",
    ),
    (
        "-1.999",
        _POST_AMOUNT,
        Decimal("-1.99"),
        "truncation is toward ZERO, not toward minus infinity - not -2.00",
    ),
    (
        "2.50",
        _QUARTER_SUBSCRIPT,
        2,
        "scale zero, so the half is discarded and the carrier is int",
    ),
    (
        "-5.00",
        _INPUT_GROSS,
        Decimal("5.00"),
        "the receiver's PICTURE is unsigned, so the SIGN IS DROPPED",
    ),
    (
        "12345.67",
        _IH_DEDUCT_AMT,
        Decimal("345.67"),
        "five digits, so the high-order 12 is discarded SILENTLY",
    ),
    (
        "-12345.67",
        _OI3_DEDUCT_AMT,
        Decimal("-345.67"),
        "sign PRESERVED, high-order digits discarded",
    ),
)


@pytest.mark.parametrize(
    ("literal", "receiving", "expected", "why"),
    _BASELINE_TRUNCATION_TABLE,
    ids=[
        "1.999-into-s9(8)v99",
        "-1.999-into-s9(8)v99",
        "2.50-into-pic-99",
        "-5.00-into-unsigned-9(9)v99",
        "12345.67-into-999v99",
        "-12345.67-into-s999v99",
    ],
)
def test_an_unrounded_store_truncates(
    literal: str,
    receiving: cobol_field.FieldDescriptor,
    expected: object,
    why: str,
) -> None:
    """`store` truncates toward zero, because `rounded` defaults to False.

    The default is what the cycle needs at all but five sites `_ROUNDED_SITES`
    names, so it is asserted here row by row rather than left to be inferred from
    the rounded case. `rounded=False` is passed EXPLICITLY in the second
    assertion as well, so that the default and the explicit spelling are proved
    to be the same thing and neither can drift.
    """
    stored = arithmetic.store(Decimal(literal), receiving)

    assert stored == expected, (
        f"{literal} into {receiving.name} "
        f"({receiving.picture or receiving.usage.value}) at "
        f"{receiving.source_locator}: {why}"
    )
    # The carrier matters as much as the value: `Sales-Average` being an `int` is
    # half of anomaly A-8, so a Decimal that merely compares equal is not enough.
    assert type(stored) is type(expected), (
        f"{receiving.name} declares {receiving.python_storage.value} storage, so "
        f"a store must return {type(expected).__name__}, not {type(stored).__name__}"
    )
    assert arithmetic.store(Decimal(literal), receiving, rounded=False) == stored, (
        "rounded=False must mean exactly what the default means"
    )


def test_truncating_is_round_down_and_rounded_is_half_up() -> None:
    """The two-member rounding vocabulary, asserted against `decimal`'s modes.

    COBOL has exactly two store directions and `ROUNDING_DIRECTIONS` is the one
    place the correspondence is stated. Rounding half AWAY FROM ZERO is
    `ROUND_HALF_UP`, which is NOT the built-in `round`'s banker's rounding: a
    migration that reached for `ROUND_HALF_EVEN` would post a different penny at
    the five `ROUNDED` sites.
    """
    assert arithmetic.ROUNDING_DIRECTIONS[False] == decimal.ROUND_DOWN
    assert arithmetic.ROUNDING_DIRECTIONS[True] == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP
    assert len(arithmetic.ROUNDING_DIRECTIONS) == 2, (
        "COBOL has two store directions and no more"
    )
    # The pair that shows the two directions are genuinely different, at the one
    # value where they disagree, in both signs.
    assert arithmetic.store(Decimal("1.995"), _POST_AMOUNT) == Decimal("1.99")
    assert (
        arithmetic.store(Decimal("1.995"), _POST_AMOUNT, rounded=True)
        == Decimal("2.00")
    )
    assert arithmetic.store(Decimal("-1.995"), _POST_AMOUNT) == Decimal("-1.99")
    assert (
        arithmetic.store(Decimal("-1.995"), _POST_AMOUNT, rounded=True)
        == Decimal("-2.00")
    )
    assert len(_ROUNDED_SITES) == 5, (
        "the cycle has exactly five ROUNDED sites; a sixth would mean the "
        "census in this module's docstring is stale"
    )


# ---------------------------------------------------------------------------
# 4.1  The R-2 tripwire: a binary float is refused at the store
# ---------------------------------------------------------------------------


def test_store_refuses_a_binary_float_carrier() -> None:
    """A `float` operand raises `TypeError` rather than being converted.

    Rule R-2 forbids a binary floating-point accounting value outright, and the
    refusal has to live in the production code rather than in a reviewer's
    vigilance - so this test proves the tripwire exists. The carrier is obtained
    by dividing two ints rather than by writing a float literal or calling the
    float constructor, so that the only float in this file is the one the tripwire
    is pointed at.

    Converting instead of refusing would launder a loss that happened BEFORE this
    module was reached: 0.1 as a float is
    0.1000000000000000055511151231257827021181583404541015625, and no amount of
    care downstream can recover the missing exactness.
    """
    inexact = 199 / 100  # 1.99 as a binary float, built without a float literal
    assert not isinstance(inexact, (Decimal, int))

    with pytest.raises(TypeError, match="R-2"):
        arithmetic.store(inexact, _POST_AMOUNT)

    # The same refusal at the verbs, so no path routes around the store.
    with pytest.raises(TypeError, match="R-2"):
        arithmetic.add_giving(inexact, Decimal("1.00"), receiving=_POST_AMOUNT)
    with pytest.raises(TypeError, match="R-2"):
        arithmetic.multiply_by_giving(inexact, -1, _POST_AMOUNT)
    with pytest.raises(TypeError, match="R-2"):
        arithmetic.compare(inexact, Decimal("1.99"))

    # `complex` is refused for the same reason, and a numeric `str` is NOT: the
    # gate is on the CARRIER's exactness, never on the value (rule R-3).
    with pytest.raises(TypeError, match="R-2"):
        arithmetic.store(complex(1, 99), _POST_AMOUNT)
    assert arithmetic.store("1.999", _POST_AMOUNT) == Decimal("1.99")
    assert arithmetic.store(1, _POST_AMOUNT) == Decimal("1.00")


# ---------------------------------------------------------------------------
# 4.2  No overflow handler exists - silence IS the specification (R-3)
# ---------------------------------------------------------------------------
#
# `ON SIZE ERROR` and `REMAINDER` are ZERO-OCCURRENCE constructs across all
# twelve in-scope programs. There is therefore no overflow handler to reproduce:
# an over-range store keeps the low-order digits and carries on, and a diagnostic
# here would be a behaviour the compiled program cannot produce. Nothing is
# raised, nothing is clamped, nothing is warned about.
#
# `03 Sales-Limit binary-long.` [copybooks/wssl.cob:L45] supplies the signed
# binary-long case. It is deliberately NOT one of the five statistics fields the
# moving averages use, so that no overflow row can be mistaken for part of an
# idiom.
_SALES_LIMIT: Final[cobol_field.FieldDescriptor] = _dictionary_descriptor(
    "SALEDGER-REC.SALES-LIMIT"
)

#: `(value, receiving field, expected, storage class being exercised)`. One row
#: per storage class, positive and negative, so that no class can silently adopt
#: another's reduction rule.
_SILENT_OVERFLOW_TABLE: Final[tuple[tuple[object, object, object, str], ...]] = (
    # DISPLAY, ten digits: reduction is modulo 10**digits on the ALIGNED units.
    (Decimal("100000000.23"), _POST_AMOUNT, Decimal("0.23"), "DISPLAY s9(8)v99"),
    (Decimal("-100000000.23"), _POST_AMOUNT, Decimal("-0.23"), "DISPLAY s9(8)v99"),
    # COMP under the default `binary-truncate: yes`: the DECLARED DIGIT COUNT
    # governs, not the byte width, so two digits saturate at 99 and 123 becomes 23.
    (123, _LINE_CNT_SL060, 23, "COMP 99"),
    (Decimal("12345.67"), _IH_DEDUCT_AMT, Decimal("345.67"), "COMP 999v99"),
    (Decimal("-12345.67"), _OI3_DEDUCT_AMT, Decimal("-345.67"), "COMP s999v99"),
    # COMP-3 packed, signed and unsigned.
    (
        Decimal("-99999999999.99"),
        _LEDGER_BALANCE,
        Decimal("-99999999.99"),
        "COMP-3 s9(8)v99",
    ),
    (
        Decimal("999999999999.99"),
        _INPUT_GROSS,
        Decimal("999999999.99"),
        "COMP-3 9(9)v99 unsigned",
    ),
    # The BINARY FAMILY reduces into its WIDTH IN BITS instead, which is a
    # different rule and produces a different answer: a signed byte wraps
    # two's-complement and an unsigned one takes the magnitude modulo 256.
    (300, _LINE_CNT_SL100, 44, "BINARY-CHAR signed"),
    (300, _PAGE_LINES, 44, "BINARY-CHAR unsigned"),
    (-300, _PAGE_LINES, 44, "BINARY-CHAR unsigned, sign dropped"),
    (2**31, _SALES_LIMIT, -2147483648, "BINARY-LONG signed"),
)


def _units_of_last_digit(value: Decimal, scale: int) -> int:
    """`value` expressed as an exact integer number of its field's last digit.

    Written with integer arithmetic over the value's own digit tuple rather than with
    `Decimal.scaleb` or `Decimal.quantize`, because both of those are CONTEXT
    operations: under a reduced ambient `prec` they round, and an eleven-digit figure
    would then be reported as outside a field that in fact holds it. A digit tuple is
    a property of the value and of nothing else, so this reading cannot be perturbed.

    Args:
        value: A stored `Decimal`.
        scale: The receiving field's declared number of decimal places.

    Returns:
        The signed integer count of last-digit units.
    """
    sign, digits, exponent = value.as_tuple()
    assert isinstance(exponent, int), exponent
    magnitude = 0
    for digit in digits:
        magnitude = magnitude * 10 + digit
    shift = exponent + scale
    if shift >= 0:
        magnitude *= 10**shift
    else:
        # An exact division: a stored value never carries more decimal places than
        # its own field declares, so there is nothing to discard here.
        divisor = 10 ** (-shift)
        assert magnitude % divisor == 0, (value, scale)
        magnitude //= divisor
    return -magnitude if sign else magnitude


@pytest.mark.parametrize(
    ("value", "receiving", "expected", "storage_class"),
    _SILENT_OVERFLOW_TABLE,
    ids=[f"{row[3]}-{row[0]}" for row in _SILENT_OVERFLOW_TABLE],
)
def test_an_over_range_store_is_silent(
    value: object,
    receiving: cobol_field.FieldDescriptor,
    expected: object,
    storage_class: str,
) -> None:
    """An over-range store returns a value and raises NOTHING (rule R-3).

    The absence of a handler is the specification, so the assertion is on the
    value that comes back - the mere fact that this test does not error IS half of
    what it proves. Adding a raise, a clamp or a warning would be an added
    validation, which rule R-3 forbids and which the state diff would then fail on
    the first over-range figure a real batch carries.
    """
    stored = arithmetic.store(value, receiving)

    assert stored == expected, (
        f"{value} into {receiving.name} ({storage_class}) at "
        f"{receiving.source_locator}: an over-range store keeps the low-order "
        "part, silently"
    )
    assert type(stored) is type(expected)
    # And whatever came back is genuinely inside the field: the reduction is a
    # store, not an approximation of one.
    low, high = receiving.value_domain
    # Scaled to units of the field's last digit WITHOUT `Decimal.scaleb`, which is a
    # context operation and would round an eleven-digit figure under a reduced ambient
    # `prec`. The digit tuple is a property of the value alone, so this reading is
    # exact whatever the ambient context holds (R-2).
    units = stored if receiving.is_int else _units_of_last_digit(
        stored, receiving.scale or 0
    )
    assert low <= units <= high, (
        f"{receiving.name} spans {low}..{high} in units of its last digit; the "
        f"store returned {units}"
    )


def test_the_two_over_range_reduction_rules_are_not_the_same_rule() -> None:
    """A declared digit count and a binary width reduce DIFFERENTLY.

    Worth its own assertion because collapsing the two is an easy and invisible
    mistake. A digit-count item keeps the SIGN OF THE ORIGINAL VALUE and discards
    high-order DIGITS; a signed binary item wraps two's-complement, which can flip
    the sign; and an unsigned item of either kind takes the magnitude. All three
    are settled behaviour - the digit-count and binary-width policies are
    questions Q-5.1 and Q-5.3, both recorded RESOLVED in
    `acas_posting/cobol/usage.py`, and the field-side unsigned drop is
    language-level COBOL, distinct from the bridge-side question Q-3 that anomaly
    A-11 raises in `acas_posting/dal/*`.
    """
    # Digit count: the sign SURVIVES, because the reduction is applied to the
    # magnitude and the original sign is put back.
    assert arithmetic.store(Decimal("-12345.67"), _OI3_DEDUCT_AMT) == Decimal("-345.67")

    # Binary width, signed: the sign can INVERT, because the reduction is a
    # two's-complement wrap.
    assert arithmetic.store(2**31, _SALES_LIMIT) == -2147483648
    assert arithmetic.store(-(2**31) - 1, _SALES_LIMIT) == 2147483647
    assert cobol_usage.is_binary_family(_SALES_LIMIT.usage)
    assert not cobol_usage.is_binary_family(_OI3_DEDUCT_AMT.usage)

    # Unsigned, either kind: the magnitude is stored and the sign is gone.
    assert arithmetic.store(Decimal("-5.00"), _INPUT_GROSS) == Decimal("5.00")
    assert arithmetic.store(-300, _PAGE_LINES) == 44
    assert _INPUT_GROSS.value_domain[0] == 0
    assert _PAGE_LINES.value_domain == (0, 255), (
        "Page-Lines is binary-char UNSIGNED [copybooks/wssystem.cob:L65]"
    )


# ---------------------------------------------------------------------------
# 4.3  Six relation conditions have NO receiving field, so NO truncation
# ---------------------------------------------------------------------------


def test_the_six_relation_condition_sites_have_no_receiving_field() -> None:
    """`if line-cnt > Page-Lines - <n>` evaluates at intermediate precision.

    All six live sites are the same shape, and none of them has a receiving item:
    the subtraction happens inside the relation, is compared, and is never stored.
    `intermediate` is the path for that, and it does not quantize. A single
    all-purpose function that always quantized would silently truncate where COBOL
    does not, which is why the two paths are separate functions.

    Because `Page-Lines` and the literal are both integers, the expression at
    these six sites happens to be integral, so the two paths agree HERE - and that
    agreement is asserted, because it is the reason the sites are safe. That the
    distinction is nonetheless observable is proved by the next test.
    """
    assert len(_RELATION_CONDITION_SITES) == 6
    assert len(set(_RELATION_CONDITION_SITES)) == 6

    page_lines = arithmetic.store(66, _PAGE_LINES)
    cases = ((6, 61, True), (6, 60, False), (12, 55, True))
    for margin, line_cnt, expected_over in cases:
        # The margin is bound as a default argument rather than captured, so the
        # expression a reader sees is unambiguously the one that is evaluated.
        threshold = arithmetic.intermediate(lambda n=margin: page_lines - n)
        assert threshold == 66 - margin
        assert threshold == threshold.to_integral_value(), (
            "Page-Lines and the literal are both integral, so the expression at "
            "these six sites carries no fraction to lose"
        )
        assert (arithmetic.compare(line_cnt, threshold) > 0) is expected_over


def test_an_intermediate_keeps_the_fraction_a_store_would_discard() -> None:
    """`intermediate` does not quantize; `store` does. The two differ.

    The constructed case is deliberately not one of the six sites, because none of
    them can produce a fraction. Its job is to prove that the distinction between
    the two paths is OBSERVABLE - that `intermediate` is not merely a stylistic
    alternative to `store` - so that a future simplification which routed relation
    conditions through the store path would change an answer here rather than
    somewhere in a scenario diff.
    """
    fractional = arithmetic.intermediate(lambda: Decimal(7) / Decimal(2))
    assert fractional == Decimal("3.5"), "no receiving field, so no truncation"

    # The SAME value truncates the moment it passes through a receiving field, and
    # both `line-cnt` declarations agree about that much.
    assert arithmetic.store(fractional, _LINE_CNT_SL060) == 3
    assert arithmetic.store(fractional, _LINE_CNT_SL100) == 3

    # And the relation's TRUTH VALUE flips between the two paths: 3.5 is greater
    # than 3, while the stored 3 is merely equal to it.
    assert arithmetic.compare(fractional, 3) > 0
    assert arithmetic.compare(arithmetic.store(fractional, _LINE_CNT_SL060), 3) == 0


def test_the_two_line_cnt_declarations_diverge_and_are_not_normalised() -> None:
    """`line-cnt` is `pic 99 comp` in `sl060` and `binary-char` in `sl100`.

    Two sibling programs, one field name, two storage classes - and the divergence
    is preserved rather than tidied away, because each program's own declaration
    governs its own arithmetic. `sl060`'s item is bounded by a DECLARED DIGIT
    COUNT, so it holds 0..99 and 123 becomes 23; `sl100`'s is a signed byte
    bounded by its WIDTH, so it holds -128..127 and 123 fits exactly.

    Locators: [sales/sl060.cbl:L223] and [sales/sl100.cbl:L173]. The brief for
    this file cites L179 for the second; the frozen source declares
    `j-deduct pic s9(7)v99 comp-3` there and `line-cnt binary-char value zero` at
    L173, so L173 is what is cited.
    """
    assert _LINE_CNT_SL060.usage is model.Usage.COMP
    assert _LINE_CNT_SL060.picture == "99"
    assert _LINE_CNT_SL060.value_domain == (0, 99)
    assert _LINE_CNT_SL060.source_locator == "sales/sl060.cbl:L223"

    assert _LINE_CNT_SL100.usage is model.Usage.BINARY_CHAR
    assert _LINE_CNT_SL100.picture is None, "the binary family carries no picture"
    assert _LINE_CNT_SL100.value_domain == (-128, 127)
    assert _LINE_CNT_SL100.source_locator == "sales/sl100.cbl:L173"

    # The same value, the same verb, two different stored results.
    assert arithmetic.store(123, _LINE_CNT_SL060) == 23
    assert arithmetic.store(123, _LINE_CNT_SL100) == 123
    assert arithmetic.store(123, _LINE_CNT_SL060) != arithmetic.store(
        123, _LINE_CNT_SL100
    ), "normalising the two declarations into one would change a stored value"


# ===========================================================================
# 4.4  THE THREE MOVING-AVERAGE IDIOMS - A-8, A-9, A-10
# ===========================================================================
#
# READ THIS BEFORE EDITING ANYTHING BELOW.
#
# The next three tests SHARE NO SETUP. Each builds its own descriptors inline and
# spells its own idiom out step by step, and the duplication is deliberate: a
# fixture or a helper shared across them would be exactly the normalisation the
# specification forbids, expressed in the test suite instead of in the production
# code. Agent Action Plan section 0.6.1, verbatim: "Normalising them into one
# helper would be the single easiest way to fail this migration."
#
# So if two of these three tests ever come to share a parametrized fixture, a
# setup function or a common accumulator descriptor, this file is wrong - however
# much duplication that removes.
#
# There is deliberately no `moving_average`, `average` or `round_to_pence` helper
# in `acas_posting.cobol.arithmetic` either, which is why each idiom is written
# here as an explicit sequence of verb calls in the order the frozen source writes
# them.
#
# `move zero to work-2` is reproduced as a store of zero rather than through
# `acas_posting.cobol.move`: that module is not among this file's permitted
# imports, and storing zero is the same operation on both paths. MOVE's own
# truncation rules are `test_move_truncation.py`'s subject.


def test_a8_sl060_sales_comp_double_truncation_end_to_end() -> None:
    """ANOMALY A-8 [sales/sl060.cbl:L816-L827] - the average truncates TWICE.

    `ba000-Sales-Comp section.` at L816, verbatim:

        L819       if       sales-activety not = zero
        L820           and  sales-average not = zero
        L821                multiply sales-activety by sales-average giving work-2
        L822       else
        L823                move zero to work-2
        L824       end-if
        L825       add      1 to sales-activety.
        L826       add      work-goods to work-2.
        L827       divide   sales-activety into work-2 giving sales-average.

    TRUNCATION #1 is at L826: `work-2` is `pic s9(14) comp-3` with ZERO decimal
    places [sales/sl060.cbl:L206] while `work-goods` carries two
    [sales/sl060.cbl:L218], so the pence of every accumulation are discarded.
    TRUNCATION #2 is at L827: `Sales-Average` is `binary-long`
    [copybooks/wssl.cob:L49], an INTEGER, so the remainder goes too.

    Both truncations arise from the DESCRIPTORS rather than from the arithmetic,
    which is why the two storage classes are locked separately by
    `test_comp3_packed_decimal.py` and `test_comp_binary.py`. What is proved here
    - and only here - is the two acting together through the verbs, in order.

    PROVENANCE of the expected values. Every step is the published behaviour of the
    single audited store path. Of that path's two governing decisions, TRUNCATION
    TOWARD ZERO on an un-`ROUNDED` store is settled and is what every figure here
    rests on; the INTERMEDIATE PRECISION is question Q-2's open half, recorded beside
    `arithmetic.INTERMEDIATE_PRECISION` and PENDING in the register. It cannot reach
    these figures: each is a single store from operands well inside the receiver's
    declared digits. The field widths are read from the frozen declarations cited
    above. No value here is a guess about what the COBOL ought to produce.

    The counter is incremented BEFORE the divide, at L825, so the divisor is the
    activity count INCLUDING this invoice. That is dimension three of the
    three-way divergence and idiom (c) does the opposite.
    """
    # --- this test's own setup, duplicated on purpose (see the block comment) ---
    #: `03 work-2 pic s9(14) comp-3.` [sales/sl060.cbl:L206] - FOURTEEN digits,
    #: ZERO decimal places. The carrier is `int` because the scale is zero, and
    #: that is truncation #1 made concrete.
    work_2 = cobol_field.FieldDescriptor(
        name="work-2",
        usage=model.Usage.COMP_3,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        picture="s9(14)",
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        digits=14,
        integer_digits=14,
        scale=0,
        python_storage=model.CobolPythonStorage.INT,
        source_locator="sales/sl060.cbl:L206",
        parent_group="ws-data",
    )
    #: `03 work-goods pic s9(7)v99 comp-3.` [sales/sl060.cbl:L218] - TWO decimal
    #: places, against `work-2`'s zero. The mismatch IS truncation #1.
    work_goods_field = cobol_field.FieldDescriptor(
        name="work-goods",
        usage=model.Usage.COMP_3,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        picture="s9(7)v99",
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        digits=9,
        integer_digits=7,
        scale=2,
        python_storage=model.CobolPythonStorage.DECIMAL,
        source_locator="sales/sl060.cbl:L218",
        parent_group="ws-data",
    )
    sales_activety_field = _dictionary_descriptor("SALEDGER-REC.SALES-ACTIVETY")
    sales_average_field = _dictionary_descriptor("SALEDGER-REC.SALES-AVERAGE")

    assert work_2.scale == 0 and work_goods_field.scale == 2, (
        "the two declarations must disagree about scale, or there is no A-8"
    )
    assert work_2.is_int and sales_average_field.is_int, (
        "an integer carrier at both ends is what makes the losses reproducible"
    )
    assert work_goods_field.is_decimal

    # --- the customer's state before this invoice, and the invoice's goods ---
    sales_activety = 2
    sales_average = 6
    work_goods = arithmetic.store(Decimal("12.99"), work_goods_field)
    assert work_goods == Decimal("12.99")

    # [:L819-L820] two conditions, both of which must hold.
    assert sales_activety != 0 and sales_average != 0
    # [:L821] multiply sales-activety by sales-average giving work-2
    work_2_value = arithmetic.multiply_by_giving(
        sales_activety, sales_average, work_2
    )
    assert work_2_value == 12, "2 x 6, into a scale-zero accumulator"

    # [:L825] add 1 to sales-activety.  THE COUNTER MOVES BEFORE THE DIVIDE.
    sales_activety = arithmetic.add_to(
        1, receiver_value=sales_activety, receiving=sales_activety_field
    )
    assert sales_activety == 3

    # [:L826] add work-goods to work-2.  TRUNCATION #1: 12 + 12.99 = 24.99, and
    # the receiver has no decimal places, so 24 is stored and the pence are gone.
    work_2_value = arithmetic.add_to(
        work_goods, receiver_value=work_2_value, receiving=work_2
    )
    assert work_2_value == 24, "the pence of 24.99 are discarded on accumulation"
    assert type(work_2_value) is int

    # [:L827] divide sales-activety into work-2 giving sales-average.  The INTO
    # spelling: the item written FIRST is the divisor. TRUNCATION #2: the quotient
    # 24 / 3 lands in a binary-long, so any remainder would be discarded too.
    sales_average = arithmetic.divide_into_giving(
        sales_activety, work_2_value, sales_average_field
    )
    assert sales_average == 8
    assert type(sales_average) is int, (
        "Sales-Average is binary-long [copybooks/wssl.cob:L49], so the average "
        "is an int and not a Decimal that happens to be whole"
    )

    # --- THE LOSS, MADE VISIBLE -------------------------------------------
    # What a naive full-precision implementation would have carried at each step.
    # These are NOT the specification; they are what the specification is being
    # protected from, and rule R-4 makes reproducing the loss the correct outcome.
    untruncated_accumulator = arithmetic.intermediate(lambda: Decimal(12) + work_goods)
    assert untruncated_accumulator == Decimal("24.99")
    assert work_2_value != untruncated_accumulator, (
        "truncation #1 must be observable: the frozen accumulator holds 24 where "
        "a two-decimal one would hold 24.99"
    )

    untruncated_average = arithmetic.intermediate(
        lambda: untruncated_accumulator / Decimal(sales_activety)
    )
    assert untruncated_average == Decimal("8.33")
    assert sales_average != untruncated_average, (
        "truncation #2 must be observable: the frozen average is 8 where a "
        "two-decimal one would be 8.33"
    )

    # And the loss compounds, because the truncated average is what the NEXT
    # invoice multiplies back up at L821. One more invoice is enough to show it.
    next_goods = arithmetic.store(Decimal("10.50"), work_goods_field)
    carried = arithmetic.multiply_by_giving(sales_activety, sales_average, work_2)
    sales_activety = arithmetic.add_to(
        1, receiver_value=sales_activety, receiving=sales_activety_field
    )
    carried = arithmetic.add_to(
        next_goods, receiver_value=carried, receiving=work_2
    )
    second_average = arithmetic.divide_into_giving(
        sales_activety, carried, sales_average_field
    )
    naive_second = arithmetic.intermediate(
        lambda: (untruncated_average * Decimal(3) + next_goods) / Decimal(4)
    )
    assert (sales_activety, carried, second_average) == (4, 34, 8)
    assert second_average != naive_second, (
        f"the divergence compounds: the frozen path reaches {second_average} "
        f"where an exact one reaches {naive_second}"
    )


def test_a9_sl060_credit_comp_never_increments_its_activity_counter() -> None:
    """ANOMALY A-9 [sales/sl060.cbl:L832-L843] - the first credit note is DROPPED.

    `ba000-Credit-Comp section.` at L832, verbatim:

        L835       if       sales-activety not = zero
        L836          and   sales-average not = zero
        L837                multiply sales-activety by sales-average giving work-2
        L838       else
        L839                move zero to work-2
        L840       end-if
        L841       if       work-2 not = zero
        L842                add   work-goods to work-2
        L843                divide sales-activety into work-2 giving sales-average.

    TWO DIFFERENCES FROM ITS SIBLING FORTY LINES ABOVE, and both are defects
    rather than choices. There is NO `add 1 to sales-activety` ANYWHERE in this
    section - verified against the frozen source, not inferred - so the counter
    never advances on a credit note. And the accumulate and the divide are wrapped
    in an EXTRA OUTER GUARD at L841, so when the L835-L836 guard has just set
    `work-2` to zero the average is not updated at all.

    Together those two mean a customer's FIRST credit note is silently dropped:
    zero activity fails the inner guard, the zeroed accumulator fails the outer
    guard, and `Sales-Average` is left exactly as it was.

    THE MISSING INCREMENT IS NOT ADDED HERE. Rule R-4: a defect reproduced is
    correct; a defect fixed is a failure. This test exists so that adding the
    increment - which any reviewer would call an obvious fix - fails the suite.

    PROVENANCE: as for A-8, every step is the published behaviour of the audited
    store path. Its truncation DIRECTION is settled by the language - an
    un-`ROUNDED` store truncates toward zero - and its intermediate PRECISION is
    question Q-2's open half, unmeasured and pending. Neither figure below can
    reach the open half: every operand and every receiver here is a two-place
    decimal or an integer.
    """
    # --- this test's own setup, duplicated on purpose (see the block comment) ---
    # Byte-for-byte the same declarations as the sibling test above, written out
    # again rather than shared: the two idioms must be able to diverge without one
    # test's setup constraining the other's.
    work_2 = cobol_field.FieldDescriptor(
        name="work-2",
        usage=model.Usage.COMP_3,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        picture="s9(14)",
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        digits=14,
        integer_digits=14,
        scale=0,
        python_storage=model.CobolPythonStorage.INT,
        source_locator="sales/sl060.cbl:L206",
        parent_group="ws-data",
    )
    work_goods_field = cobol_field.FieldDescriptor(
        name="work-goods",
        usage=model.Usage.COMP_3,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        picture="s9(7)v99",
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        digits=9,
        integer_digits=7,
        scale=2,
        python_storage=model.CobolPythonStorage.DECIMAL,
        source_locator="sales/sl060.cbl:L218",
        parent_group="ws-data",
    )
    sales_average_field = _dictionary_descriptor("SALEDGER-REC.SALES-AVERAGE")

    # ------------------------------------------------------------------
    # CASE 1 - a customer's FIRST credit note. Activity is zero.
    # ------------------------------------------------------------------
    sales_activety = 0
    sales_average = 7  # whatever the last invoice left behind
    average_before = sales_average
    work_goods = arithmetic.store(Decimal("12.99"), work_goods_field)

    # [:L835-L836] the inner guard fails, because activity is zero.
    if sales_activety != 0 and sales_average != 0:  # pragma: no cover - guard fails
        work_2_value = arithmetic.multiply_by_giving(
            sales_activety, sales_average, work_2
        )
    else:
        # [:L839] move zero to work-2
        work_2_value = arithmetic.store(0, work_2)
    assert work_2_value == 0

    # [:L841] the EXTRA OUTER GUARD then fails as well, so neither the accumulate
    # at L842 nor the divide at L843 happens.
    if work_2_value != 0:  # pragma: no cover - the outer guard fails
        work_2_value = arithmetic.add_to(
            work_goods, receiver_value=work_2_value, receiving=work_2
        )
        sales_average = arithmetic.divide_into_giving(
            sales_activety, work_2_value, sales_average_field
        )

    assert sales_average == average_before, (
        "ANOMALY A-9: the first credit note is SILENTLY DROPPED - the average is "
        "left exactly as the last invoice set it"
    )
    assert type(sales_average) is type(average_before)
    assert sales_activety == 0, (
        "and the counter did not move either: there is no `add 1 to "
        "sales-activety` anywhere in ba000-Credit-Comp"
    )
    # The credit note's own value never reached the average. Proving the negative
    # explicitly, because it is the whole anomaly.
    assert sales_average != arithmetic.store(work_goods, sales_average_field)

    # ------------------------------------------------------------------
    # CASE 2 - a LATER credit note. The average updates; the counter STILL does not.
    # ------------------------------------------------------------------
    sales_activety = 4
    sales_average = 25
    activety_before = sales_activety
    work_goods = arithmetic.store(Decimal("30.75"), work_goods_field)

    # [:L835-L837] both conditions hold this time.
    assert sales_activety != 0 and sales_average != 0
    work_2_value = arithmetic.multiply_by_giving(
        sales_activety, sales_average, work_2
    )
    assert work_2_value == 100

    # [:L841] the outer guard passes, so both statements run.
    assert work_2_value != 0
    # [:L842] add work-goods to work-2 - the same pence loss as A-8's truncation #1.
    work_2_value = arithmetic.add_to(
        work_goods, receiver_value=work_2_value, receiving=work_2
    )
    assert work_2_value == 130, "130.75 into a scale-zero accumulator"
    # [:L843] divide sales-activety into work-2 giving sales-average - and the
    # divisor is the UN-incremented counter, which is the anomaly's second face.
    sales_average = arithmetic.divide_into_giving(
        sales_activety, work_2_value, sales_average_field
    )
    assert sales_average == 32, "130 / 4, remainder discarded"

    assert sales_activety == activety_before == 4, (
        "ANOMALY A-9: the counter is NOT incremented, so this credit note "
        "divides by 4 where its sibling at [sales/sl060.cbl:L825] would have "
        "divided by 5"
    )
    # What the same figures would give if the missing increment were added - the
    # obvious fix, and the one this assertion exists to keep out.
    with_the_fix = arithmetic.divide_into_giving(
        sales_activety + 1, work_2_value, sales_average_field
    )
    assert with_the_fix == 26
    assert sales_average != with_the_fix, (
        "adding the missing increment changes the stored average, which is why "
        "rule R-4 makes reproducing the omission the correct outcome"
    )


def test_a10_sl100_compute_sales_pay_single_guard_late_counter_and_by_divide() -> None:
    """ANOMALY A-10 [sales/sl100.cbl:L497-L514] - the third, divergent variant.

    `compute-sales-pay.` at L497 - a PARAGRAPH NAME, not a `COMPUTE` verb, and not
    part of the COMPUTE census. Verbatim:

        L500       if       oi-date-cleared = zero
        L501                go to csp-exit.
        L503       subtract oi-date from oi-date-cleared giving work-a.
        L504       move     zero to work-b.
        L506       if       sales-pay-activety not = zero
        L507                multiply sales-pay-activety by sales-pay-average
                                     giving work-b.
        L509       add      work-a to work-b.
        L510       add      1 to sales-pay-activety.
        L511       divide   work-b by sales-pay-activety giving sales-pay-average.
        L513       if       work-a > sales-pay-worst
        L514                move work-a to sales-pay-worst.

    FOUR DIVERGENCES from the two `sl060` variants, every one preserved:

    * ONE guard condition, not two - `sales-pay-average` is never tested.
    * NO `ELSE`. `work-b` is zeroed UNCONDITIONALLY at L504 instead, before the
      guard, which is a different mechanism reaching a similar place.
    * The counter is incremented AFTER the accumulate, at L510 - the opposite of
      [sales/sl060.cbl:L825], though still before the divide.
    * The divide is `work-b BY sales-pay-activety`, the REVERSED operand order
      relative to the `INTO` spelling its siblings use.

    And a fifth divergence in the storage: `work-a` and `work-b` are
    `binary-long value zero` [sales/sl100.cbl:L182-L183], a different accumulator
    mechanism from the `comp-3` `work-2` of the `sl060` pair, so this whole path
    is integer arithmetic from end to end.

    The Purchase mirror is `compute-purch-pay.` [purchase/pl100.cbl:L488-L505],
    identical in every one of those respects, including the `BY` divide at
    [purchase/pl100.cbl:L502].

    PROVENANCE: as for A-8 and A-9, each step is the audited store path's
    published behaviour. The direction of an un-`ROUNDED` store is settled by the
    language; the intermediate precision is question Q-2's open half and is
    unmeasured. The figures below are integer arithmetic from end to end, so the
    open half cannot reach them.
    """
    # --- this test's own setup, duplicated on purpose (see the block comment) ---
    #: `03 work-a binary-long value zero.` [sales/sl100.cbl:L182].
    work_a_field = cobol_field.FieldDescriptor(
        name="work-a",
        usage=model.Usage.BINARY_LONG,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        python_storage=model.CobolPythonStorage.INT,
        source_locator="sales/sl100.cbl:L182",
        parent_group="ws-data",
    )
    #: `03 work-b binary-long value zero.` [sales/sl100.cbl:L183].
    work_b_field = cobol_field.FieldDescriptor(
        name="work-b",
        usage=model.Usage.BINARY_LONG,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        python_storage=model.CobolPythonStorage.INT,
        source_locator="sales/sl100.cbl:L183",
        parent_group="ws-data",
    )
    pay_activety_field = _dictionary_descriptor("SALEDGER-REC.SALES-PAY-ACTIVETY")
    pay_average_field = _dictionary_descriptor("SALEDGER-REC.SALES-PAY-AVERAGE")
    pay_worst_field = _dictionary_descriptor("SALEDGER-REC.SALES-PAY-WORST")

    assert work_a_field.is_int and work_b_field.is_int
    assert work_a_field.usage is model.Usage.BINARY_LONG, (
        "dimension five: a DIFFERENT accumulator class from the comp-3 work-2 of "
        "[sales/sl060.cbl:L206]"
    )

    # --- the open item and the customer's payment history --------------------
    oi_date = 730000
    oi_date_cleared = 730045
    sales_pay_activety = 2
    sales_pay_average = 30
    sales_pay_worst = 45

    # [:L500-L501] the paragraph returns at once on an uncleared item.
    assert oi_date_cleared != 0

    # [:L503] subtract oi-date FROM oi-date-cleared GIVING work-a, which is
    # `work-a = oi-date-cleared - oi-date`. The two dates are deliberately
    # asymmetric, so a reversed transcription would be caught here rather than
    # cancelling out.
    work_a = arithmetic.subtract_giving(
        oi_date, minuend=oi_date_cleared, receiving=work_a_field
    )
    assert work_a == 45, "the item took 45 days to clear"
    assert (
        arithmetic.subtract_giving(
            oi_date_cleared, minuend=oi_date, receiving=work_a_field
        )
        == -45
    ), "reversing the operands would give -45, so the order is load-bearing"

    # [:L504] move zero to work-b - UNCONDITIONALLY, and before the guard.
    work_b = arithmetic.store(0, work_b_field)
    assert work_b == 0

    # [:L506-L507] ONE condition, and NO else.
    if sales_pay_activety != 0:
        work_b = arithmetic.multiply_by_giving(
            sales_pay_activety, sales_pay_average, work_b_field
        )
    assert work_b == 60

    # [:L509] add work-a to work-b.
    work_b = arithmetic.add_to(work_a, receiver_value=work_b, receiving=work_b_field)
    assert work_b == 105

    # [:L510] add 1 to sales-pay-activety - AFTER the accumulate, unlike
    # [sales/sl060.cbl:L825] which does it before.
    sales_pay_activety = arithmetic.add_to(
        1, receiver_value=sales_pay_activety, receiving=pay_activety_field
    )
    assert sales_pay_activety == 3

    # [:L511] divide work-b BY sales-pay-activety giving sales-pay-average - the
    # REVERSED spelling. The first operand is the dividend here, where in the
    # `INTO` form it is the divisor.
    sales_pay_average = arithmetic.divide_by_giving(
        work_b, sales_pay_activety, pay_average_field
    )
    assert sales_pay_average == 35, "105 / 3"
    assert type(sales_pay_average) is int

    # THE REVERSAL IS OBSERVABLE. Handing the same two operands, in the same
    # order, to the `INTO` spelling its siblings use computes 3 / 105 instead of
    # 105 / 3 - which truncates to nothing at all.
    the_wrong_spelling = arithmetic.divide_into_giving(
        work_b, sales_pay_activety, pay_average_field
    )
    assert the_wrong_spelling == 0
    assert the_wrong_spelling != sales_pay_average, (
        "transcribing [sales/sl100.cbl:L511] with the INTO helper would post a "
        "zero average and report nothing"
    )

    # [:L513-L514] the watermark comparison is STRICT. An equal value does not
    # update it, so the field keeps the FIRST occurrence of the worst delay.
    assert arithmetic.compare(work_a, sales_pay_worst) == 0
    if arithmetic.compare(work_a, sales_pay_worst) > 0:  # pragma: no cover - equal
        sales_pay_worst = arithmetic.store(work_a, pay_worst_field)
    assert sales_pay_worst == 45, "45 > 45 is false, so the watermark is unchanged"

    # One day worse, and it does move - so the strictness above is a real
    # boundary rather than an accident of the numbers chosen.
    worse = arithmetic.subtract_giving(
        oi_date, minuend=oi_date_cleared + 1, receiving=work_a_field
    )
    assert arithmetic.compare(worse, sales_pay_worst) > 0
    sales_pay_worst = arithmetic.store(worse, pay_worst_field)
    assert sales_pay_worst == 46

    # --- THE NO-ELSE MECHANISM, and why it is only safe by accident ----------
    # With zero activity the guard fails and there is no `else` to zero `work-b`.
    # It is nevertheless zero, because L504 zeroed it unconditionally. Drop that
    # one line - the mistranscription this assertion guards against - and a stale
    # value from the previous open item survives into this one's average.
    stale_work_b = 999
    faithful = arithmetic.store(0, work_b_field)  # [:L504], unconditional
    mistranscribed = stale_work_b  # L504 omitted, and no else to stand in for it
    first_payment_activety = 0
    if first_payment_activety != 0:  # pragma: no cover - the single guard fails
        faithful = arithmetic.multiply_by_giving(
            first_payment_activety, sales_pay_average, work_b_field
        )
        mistranscribed = faithful

    faithful = arithmetic.add_to(
        work_a, receiver_value=faithful, receiving=work_b_field
    )
    mistranscribed = arithmetic.add_to(
        work_a, receiver_value=mistranscribed, receiving=work_b_field
    )
    counted = arithmetic.add_to(
        1, receiver_value=first_payment_activety, receiving=pay_activety_field
    )
    assert counted == 1
    assert arithmetic.divide_by_giving(faithful, counted, pay_average_field) == 45
    assert (
        arithmetic.divide_by_giving(mistranscribed, counted, pay_average_field)
        == 1044
    )
    assert faithful != mistranscribed, (
        "the missing ELSE is harmless ONLY because L504 is unconditional; "
        "omitting L504 would leak the previous item's accumulator"
    )


def test_a_unified_moving_average_helper_cannot_reproduce_all_three_idioms() -> None:
    """The normalisation this whole file exists to prevent, made to FAIL.

    Agent Action Plan section 0.6.1, verbatim: "Normalising them into one helper
    would be the single easiest way to fail this migration."

    The three idioms look like one idiom written three times, and every instinct a
    good engineer has says to factor them. This test writes that factoring out -
    the helper a reviewer would ask for - applies it to all three sets of inputs,
    and shows that it CANNOT reproduce all three. It therefore fails the moment
    somebody acts on the instinct, which is the only reliable defence rule R-4
    has.

    The helper is defined INSIDE this function on purpose. It must never be
    importable, never be reachable from `acas_posting`, and never become the thing
    a program module calls.

    FIVE INDEPENDENT DIMENSIONS make the three irreconcilable, and no single
    signature spans them:

        dimension            (a) sl060 L816   (b) sl060 L832    (c) sl100 L497
        guard conditions     2                2 + 1 outer       1
        ELSE present         yes  L822        yes  L838         NO
        counter increment    BEFORE L825      ABSENT            AFTER L510
        divide spelling      INTO L827        INTO L843         BY, reversed L511
        accumulator class    comp-3 s9(14)    the same work-2   binary-long
                             L206                               L182-L183
    """

    # ------------------------------------------------------------------
    # The receiving fields the hypothetical helper would have to choose between.
    # ------------------------------------------------------------------
    packed_accumulator = cobol_field.FieldDescriptor(
        name="work-2",
        usage=model.Usage.COMP_3,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        picture="s9(14)",
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        digits=14,
        integer_digits=14,
        scale=0,
        python_storage=model.CobolPythonStorage.INT,
        source_locator="sales/sl060.cbl:L206",
        parent_group="ws-data",
    )
    binary_accumulator = cobol_field.FieldDescriptor(
        name="work-b",
        usage=model.Usage.BINARY_LONG,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        python_storage=model.CobolPythonStorage.INT,
        source_locator="sales/sl100.cbl:L183",
        parent_group="ws-data",
    )
    goods_field = cobol_field.FieldDescriptor(
        name="work-goods",
        usage=model.Usage.COMP_3,
        usage_declared_at=model.UsageDeclaredAt.FIELD,
        picture="s9(7)v99",
        signed=True,
        sign_position=model.SignPosition.IMPLICIT_BINARY,
        digits=9,
        integer_digits=7,
        scale=2,
        python_storage=model.CobolPythonStorage.DECIMAL,
        source_locator="sales/sl060.cbl:L218",
        parent_group="ws-data",
    )
    counter_field = _dictionary_descriptor("SALEDGER-REC.SALES-ACTIVETY")
    average_field = _dictionary_descriptor("SALEDGER-REC.SALES-AVERAGE")

    def moving_average(
        activity: int,
        average: int,
        addend: Decimal | int,
        *,
        increment_before: bool,
    ) -> tuple[int, int]:
        """THE HELPER THAT MUST NOT EXIST. Do not lift this out of this test.

        One guard shape, one ELSE, one counter policy behind a flag, one divide
        spelling and one accumulator class - which is precisely why it cannot be
        all three idioms at once.

        Args:
            activity: The customer's activity counter before this document.
            average: The customer's average before this document.
            addend: The document's value.
            increment_before: True for the [sales/sl060.cbl:L825] policy, False
                for the [sales/sl100.cbl:L510] one.

        Returns:
            The counter and the average the helper would leave behind.
        """
        if activity != 0 and average != 0:
            accumulated = arithmetic.multiply_by_giving(
                activity, average, packed_accumulator
            )
        else:
            accumulated = arithmetic.store(0, packed_accumulator)
        if increment_before:
            activity = arithmetic.add_to(
                1, receiver_value=activity, receiving=counter_field
            )
        accumulated = arithmetic.add_to(
            addend, receiver_value=accumulated, receiving=packed_accumulator
        )
        if not increment_before:
            activity = arithmetic.add_to(
                1, receiver_value=activity, receiving=counter_field
            )
        return activity, arithmetic.divide_into_giving(
            activity, accumulated, average_field
        )

    # ------------------------------------------------------------------
    # (a) [sales/sl060.cbl:L816-L827]. The helper DOES reproduce this one - it was
    # written from it, and that is exactly what makes it plausible.
    # ------------------------------------------------------------------
    goods = arithmetic.store(Decimal("12.99"), goods_field)
    assert moving_average(2, 6, goods, increment_before=True) == (3, 8)

    # ------------------------------------------------------------------
    # (b) [sales/sl060.cbl:L832-L843]. THE HELPER CANNOT REPRODUCE THIS ONE.
    # The frozen section has NO counter increment and an EXTRA OUTER GUARD, so a
    # customer's first credit note leaves both fields exactly as they were. The
    # helper increments and posts an average. Two fields, both wrong.
    # ------------------------------------------------------------------
    frozen_first_credit_note = (0, 7)  # counter untouched, average untouched
    assert moving_average(0, 7, goods, increment_before=True) == (1, 12)
    assert moving_average(0, 7, goods, increment_before=False) == (1, 12)
    assert moving_average(0, 7, goods, increment_before=True) != (
        frozen_first_credit_note
    ), (
        "ANOMALY A-9 is unreachable through any setting of increment_before: the "
        "frozen credit-note path increments NEVER, and its outer guard at "
        "[sales/sl060.cbl:L841] suppresses the divide as well"
    )
    assert moving_average(0, 7, goods, increment_before=False) != (
        frozen_first_credit_note
    )

    # ------------------------------------------------------------------
    # (c) [sales/sl100.cbl:L497-L514]. The helper matches the arithmetic while the
    # inputs stay small - which is the trap - and diverges on the two dimensions a
    # single signature cannot carry.
    # ------------------------------------------------------------------
    assert moving_average(2, 30, 45, increment_before=False) == (3, 35)

    # Dimension four. The helper takes the `INTO` operand order, so a caller
    # transcribing [sales/sl100.cbl:L511] literally - dividend first, as the `BY`
    # line writes it - gets the reciprocal and stores nothing of value.
    assert arithmetic.divide_by_giving(105, 3, average_field) == 35
    assert arithmetic.divide_into_giving(105, 3, average_field) == 0

    # Dimension five. The accumulator class is NOT interchangeable: the frozen
    # `sl100` path accumulates in a `binary-long`, which wraps two's-complement at
    # 2**31, while `work-2` carries fourteen digits and does not. The magnitude
    # below is past anything a day count reaches - the point is not that the cycle
    # produces it, but that the two receivers are different fields and a helper
    # must pick one.
    beyond_a_signed_word = 3_000_000_000
    in_the_binary_field = arithmetic.add_to(
        beyond_a_signed_word, receiver_value=60, receiving=binary_accumulator
    )
    in_the_packed_field = arithmetic.add_to(
        beyond_a_signed_word, receiver_value=60, receiving=packed_accumulator
    )
    assert in_the_binary_field == -1_294_967_236
    assert in_the_packed_field == 3_000_000_060
    assert in_the_binary_field != in_the_packed_field, (
        "dimension five: binary-long [sales/sl100.cbl:L183] and "
        "pic s9(14) comp-3 [sales/sl060.cbl:L206] reduce differently, so one "
        "accumulator descriptor cannot serve all three idioms"
    )

    # ------------------------------------------------------------------
    # (d), (e), (f) - THE PURCHASE MIRRORS. The idiom lives SIX times, not three:
    # `purch-comp` [purchase/pl060.cbl:L740-L751], `credit-comp`
    # [purchase/pl060.cbl:L755-L766] and `compute-purch-pay.`
    # [purchase/pl100.cbl:L488-L505] repeat (a), (b) and (c) field for field. The
    # helper fails on the Purchase trio for exactly the reasons it fails on the
    # Sales trio, which is the whole point: unifying "just the Purchase copies"
    # is the same mistake in a smaller disguise.
    #
    # The receiving descriptors are the Purchase statistics fields rather than the
    # Sales ones, and they are `binary-long` too - so the truncation is identical
    # and only the column names differ.
    # ------------------------------------------------------------------
    purch_counter_field = _dictionary_descriptor("PULEDGER-REC.PURCH-ACTIVETY")
    purch_average_field = _dictionary_descriptor("PULEDGER-REC.PURCH-AVERAGE")
    purch_pay_counter = _dictionary_descriptor("PULEDGER-REC.PURCH-PAY-ACTIVETY")
    purch_pay_average = _dictionary_descriptor("PULEDGER-REC.PURCH-PAY-AVERAGE")
    for purchase_field in (
        purch_counter_field,
        purch_average_field,
        purch_pay_counter,
        purch_pay_average,
    ):
        assert purchase_field.usage is model.Usage.BINARY_LONG
        assert purchase_field.is_int

    def purchase_moving_average(
        activity: int,
        average: int,
        addend: Decimal | int,
        *,
        increment_before: bool,
    ) -> tuple[int, int]:
        """The same helper, pointed at the Purchase receivers. Equally forbidden."""
        if activity != 0 and average != 0:
            accumulated = arithmetic.multiply_by_giving(
                activity, average, packed_accumulator
            )
        else:
            accumulated = arithmetic.store(0, packed_accumulator)
        if increment_before:
            activity = arithmetic.add_to(
                1, receiver_value=activity, receiving=purch_counter_field
            )
        accumulated = arithmetic.add_to(
            addend, receiver_value=accumulated, receiving=packed_accumulator
        )
        if not increment_before:
            activity = arithmetic.add_to(
                1, receiver_value=activity, receiving=purch_counter_field
            )
        return activity, arithmetic.divide_into_giving(
            activity, accumulated, purch_average_field
        )

    # (d) [purchase/pl060.cbl:L740-L751] - reproduced, as (a) was, and just as
    # misleadingly.
    assert purchase_moving_average(2, 6, goods, increment_before=True) == (3, 8)

    # (e) [purchase/pl060.cbl:L755-L766] - NOT reproducible. ANOMALY A-9 again:
    # there is no `add 1 to purch-activety` in that block, and the extra outer
    # guard at [purchase/pl060.cbl:L764] suppresses the divide as well, so a
    # supplier's first credit note leaves BOTH fields untouched.
    frozen_first_purchase_credit_note = (0, 7)
    assert purchase_moving_average(0, 7, goods, increment_before=True) == (1, 12)
    assert purchase_moving_average(0, 7, goods, increment_before=False) == (1, 12)
    assert (
        purchase_moving_average(0, 7, goods, increment_before=True)
        != frozen_first_purchase_credit_note
    ), (
        "ANOMALY A-9 on the Purchase side is unreachable through any setting of "
        "increment_before either: [purchase/pl060.cbl:L755-L766] increments NEVER"
    )

    # (f) [purchase/pl100.cbl:L488-L505] - the `BY` spelling again, and the same
    # reciprocal trap for a caller who transcribes the operands literally.
    assert arithmetic.divide_by_giving(105, 3, purch_pay_average) == 35
    assert arithmetic.divide_into_giving(105, 3, purch_pay_average) == 0
    assert purchase_moving_average(2, 30, 45, increment_before=False) == (3, 35)

    # ------------------------------------------------------------------
    # The five dimensions, as data, over ALL SIX SITES, so that a reader can check
    # the claim rather than take it on trust - and so that the counts themselves
    # are asserted. Order: (a) sl060 L816, (b) sl060 L832, (c) sl100 L497,
    # (d) pl060 L740, (e) pl060 L755, (f) pl100 L488.
    # ------------------------------------------------------------------
    sites = (
        "sales/sl060.cbl:L816",
        "sales/sl060.cbl:L832",
        "sales/sl100.cbl:L497",
        "purchase/pl060.cbl:L740",
        "purchase/pl060.cbl:L755",
        "purchase/pl100.cbl:L488",
    )
    dimensions = {
        "guard conditions": (2, 2 + 1, 1, 2, 2 + 1, 1),
        "ELSE present": (True, True, False, True, True, False),
        "counter increment": (
            "before",
            "absent",
            "after",
            "before",
            "absent",
            "after",
        ),
        "divide spelling": ("INTO", "INTO", "BY", "INTO", "INTO", "BY"),
        "accumulator class": (
            "COMP-3",
            "COMP-3",
            "BINARY-LONG",
            "COMP-3",
            "COMP-3",
            "BINARY-LONG",
        ),
    }
    assert len(dimensions) == 5
    assert len(sites) == 6
    assert all(len(values) == len(sites) for values in dimensions.values())
    differing = [name for name, values in dimensions.items() if len(set(values)) > 1]
    assert len(differing) == 5, (
        "all five dimensions must differ across the six sites; if one ever "
        f"agrees, re-derive it from the frozen source. Differing: {differing}"
    )
    assert dimensions["accumulator class"][2] == binary_accumulator.usage.value
    assert dimensions["accumulator class"][0] == packed_accumulator.usage.value
    # The Purchase trio repeats the Sales trio exactly, dimension for dimension -
    # which is why "just unify the mirrors" is the same error.
    for values in dimensions.values():
        assert values[:3] == values[3:], (
            "the Purchase mirrors must agree with their Sales originals on every "
            "dimension; a divergence here means one side was re-derived wrongly"
        )


# ---------------------------------------------------------------------------
# 4.4  The DIVIDE census, and the Purchase mirrors
# ---------------------------------------------------------------------------


def test_the_divide_census_is_thirteen_by_and_four_into() -> None:
    """Seventeen DIVIDEs, in two spellings that take their operands opposite ways.

    The census is asserted rather than merely documented because the two spellings
    are silently interchangeable at a call site and produce reciprocals. All four
    `INTO ... GIVING` sites are the moving-average idiom, two in `sl060` and two in
    `pl060`; every other divide in the cycle is `BY ... GIVING`, including the
    Purchase payment path at [purchase/pl100.cbl:L502], which mirrors
    [sales/sl100.cbl:L511].

    Exactly one of the seventeen is `ROUNDED`: [general/gl080.cbl:L328].
    """
    assert len(_DIVIDE_INTO_GIVING_SITES) == 4
    assert len(_DIVIDE_BY_GIVING_SITES) == 13
    assert len(_DIVIDE_BY_GIVING_SITES) + len(_DIVIDE_INTO_GIVING_SITES) == 17

    # The four INTO sites are the two Sales and the two Purchase average blocks,
    # and nothing else in the cycle divides that way round.
    assert _DIVIDE_INTO_GIVING_SITES == (
        "sales/sl060.cbl:L827",
        "sales/sl060.cbl:L843",
        "purchase/pl060.cbl:L751",
        "purchase/pl060.cbl:L766",
    )
    assert sum(site.startswith("sales/") for site in _DIVIDE_INTO_GIVING_SITES) == 2
    assert sum(site.startswith("purchase/") for site in _DIVIDE_INTO_GIVING_SITES) == 2

    # The single ROUNDED divide is a BY site, and it is the only overlap between
    # the divide census and the ROUNDED census.
    rounded_divides = tuple(
        site for site in _DIVIDE_BY_GIVING_SITES if site in _ROUNDED_SITES
    )
    assert rounded_divides == ("general/gl080.cbl:L328",)
    assert not any(site in _ROUNDED_SITES for site in _DIVIDE_INTO_GIVING_SITES)

    # No site is counted twice, and no site appears in both spellings.
    assert len(set(_DIVIDE_BY_GIVING_SITES)) == 13
    assert not set(_DIVIDE_BY_GIVING_SITES) & set(_DIVIDE_INTO_GIVING_SITES)


def test_the_purchase_mirrors_use_the_same_two_divide_forms_as_sales() -> None:
    """`pl060` divides `INTO` and `pl100` divides `BY`, exactly as Sales does.

    The Purchase family is a field-for-field mirror of the Sales family, and the
    mirror extends to the divergence: `purch-comp` [purchase/pl060.cbl:L740-L751]
    and `credit-comp` [purchase/pl060.cbl:L755-L766] use the `INTO` spelling with
    the counter incremented at [purchase/pl060.cbl:L749] and absent from the
    credit block, while `compute-purch-pay.` [purchase/pl100.cbl:L488-L505] uses
    the `BY` spelling with the counter incremented at
    [purchase/pl100.cbl:L501] - after the accumulate at
    [purchase/pl100.cbl:L500].

    So the same three anomalies live twice, and the migration must not normalise
    the Purchase copies either.
    """
    purch_activety = _dictionary_descriptor("PULEDGER-REC.PURCH-ACTIVETY")
    purch_average = _dictionary_descriptor("PULEDGER-REC.PURCH-AVERAGE")
    purch_pay_activety = _dictionary_descriptor("PULEDGER-REC.PURCH-PAY-ACTIVETY")
    purch_pay_average = _dictionary_descriptor("PULEDGER-REC.PURCH-PAY-AVERAGE")
    for descriptor in (
        purch_activety,
        purch_average,
        purch_pay_activety,
        purch_pay_average,
    ):
        assert descriptor.usage is model.Usage.BINARY_LONG
        assert descriptor.is_int, (
            "the Purchase statistics fields are binary-long like their Sales "
            "counterparts, so their averages truncate as integers too"
        )

    # [purchase/pl060.cbl:L751] divide purch-activety INTO work-2 giving
    # purch-average: the quotient is the SECOND operand over the first.
    assert arithmetic.divide_into_giving(3, 24, purch_average) == 8
    # [purchase/pl100.cbl:L502] divide work-b BY purch-pay-activety giving
    # purch-pay-average: the quotient is the FIRST over the second.
    assert arithmetic.divide_by_giving(105, 3, purch_pay_average) == 35
    # Handing either line's operands to the other spelling changes the answer.
    assert arithmetic.divide_by_giving(3, 24, purch_average) == 0
    assert arithmetic.divide_into_giving(105, 3, purch_pay_average) == 0


# ---------------------------------------------------------------------------
# 4.5  The sign-flip census - `multiply ... by -1`
# ---------------------------------------------------------------------------


def test_a_sign_flip_truncates_like_any_other_store() -> None:
    """`multiply <field> by -1 giving <field>` is an ordinary un-ROUNDED store.

    Nine of the twelve in-scope programs negate a value this way, and
    `_SIGN_FLIP_SITES` records the census - twenty-seven entries, two of them
    spans, expanding to thirty-eight of the thirty-nine live statements this
    checkout contains. None is `ROUNDED`, so every one truncates, and into an
    unsigned receiver every one drops the sign it has just applied.

    The receiver used here is the real one: `03 pre-amount pic s9(8)v99.`
    [general/gl070.cbl:L115], negated at [general/gl070.cbl:L517] to turn the
    credit leg of the double-entry explosion into a negative posting, and again at
    [general/gl070.cbl:L530] for the VAT leg.
    """
    # The signed receiver keeps the sign the multiply produced.
    assert (
        arithmetic.multiply_by_giving(Decimal("123.45"), -1, _PRE_AMOUNT)
        == Decimal("-123.45")
    )
    assert (
        arithmetic.multiply_by_giving(Decimal("-123.45"), -1, _PRE_AMOUNT)
        == Decimal("123.45")
    )
    # The same statement into an UNSIGNED receiver loses it again immediately -
    # `05 Input-Gross pic 9(9)v99.` under `03 Amounts comp-3.`
    # [copybooks/wsbatch.cob:L40-L41].
    assert (
        arithmetic.multiply_by_giving(Decimal("123.45"), -1, _INPUT_GROSS)
        == Decimal("123.45")
    )

    # It truncates, because it is un-ROUNDED like everything else: three decimal
    # places into a two-place field discard the third, in both signs.
    assert (
        arithmetic.multiply_by_giving(Decimal("1.999"), -1, _PRE_AMOUNT)
        == Decimal("-1.99")
    )
    assert (
        arithmetic.multiply_by_giving(Decimal("-1.999"), -1, _PRE_AMOUNT)
        == Decimal("1.99")
    )
    # And it rounds only where the statement says ROUNDED, which no sign flip does.
    assert (
        arithmetic.multiply_by_giving(Decimal("1.995"), -1, _PRE_AMOUNT, rounded=True)
        == Decimal("-2.00")
    )

    # The no-GIVING spelling is live too - `multiply -1 by work-1.`
    # [sales/sl060.cbl:L861] - and negates the RECEIVER rather than a third field.
    assert (
        arithmetic.multiply_by(-1, Decimal("123.45"), _PRE_AMOUNT)
        == Decimal("-123.45")
    )

    assert len(_SIGN_FLIP_SITES) == 27
    assert len(set(_SIGN_FLIP_SITES)) == 27
    assert not set(_SIGN_FLIP_SITES) & set(_ROUNDED_SITES), (
        "no sign flip anywhere in the cycle is written ROUNDED"
    )


# ---------------------------------------------------------------------------
# 4.6  Variadic `ADD ... GIVING` - summed at intermediate precision, stored ONCE
# ---------------------------------------------------------------------------


def test_add_giving_quantizes_once_however_many_sources_it_has() -> None:
    """The sum is taken at intermediate precision and stored ONCE.

    The two-source form is [general/gl070.cbl:L504]
    `add post-amount vat-amount giving pre-amount`, the statement that folds VAT
    into the leg of a double entry that carries it. The widest form in the cycle is
    five sources, at [sales/sl060.cbl:L523]
    `add oi-net oi-extra oi-carriage oi-discount oi-deduct-amt giving work-net`,
    whose receiver is `03 work-net pic s9(7)v99 comp-3.`
    [sales/sl060.cbl:L216].

    Five operands of four thousandths each total twenty thousandths, which lands as
    two hundredths in a two-place field. Truncating each operand on the way in
    would land NOTHING AT ALL - which is what a per-term quantize does, and what
    this test forbids.
    """
    # Two sources, the gl070 site, with figures that need no rounding at all.
    assert (
        arithmetic.add_giving(
            Decimal("100.00"), Decimal("17.50"), receiving=_PRE_AMOUNT
        )
        == Decimal("117.50")
    )

    # Five sources, the sl060 site, with figures that make the difference between
    # one quantize and five visible.
    thousandth_operands = (
        Decimal("0.004"),
        Decimal("0.004"),
        Decimal("0.004"),
        Decimal("0.004"),
        Decimal("0.004"),
    )
    once = arithmetic.add_giving(*thousandth_operands, receiving=_WORK_NET)
    assert once == Decimal("0.02"), "0.020 stored once into a two-place field"

    per_term_total = Decimal(0)
    for operand in thousandth_operands:
        per_term_total += arithmetic.store(operand, _WORK_NET)
    assert per_term_total == Decimal("0.00")
    assert once != per_term_total, (
        "quantizing per operand instead of once would discard every term; that is "
        "what INTERMEDIATE_CONTEXT exists to prevent"
    )

    # The sum is exact at intermediate precision before it is stored, so a
    # five-source total is the same whichever order the operands are written in -
    # addition being associative at that precision. Worth asserting, because it is
    # why a variadic signature is safe here at all.
    mixed = (
        Decimal("1.005"),
        Decimal("2.006"),
        Decimal("3.007"),
        Decimal("4.008"),
        Decimal("5.009"),
    )
    assert arithmetic.add_giving(*mixed, receiving=_WORK_NET) == Decimal("15.03")
    assert arithmetic.add_giving(
        *reversed(mixed), receiving=_WORK_NET
    ) == Decimal("15.03")
    assert arithmetic.intermediate(lambda: sum(mixed, Decimal(0))) == Decimal("15.035")

    # `ADD ... TO` folds the receiver in as an operand as well, and stores once for
    # the same reason - `add work-goods to work-2.` [sales/sl060.cbl:L826].
    assert (
        arithmetic.add_to(
            Decimal("0.004"),
            Decimal("0.004"),
            receiver_value=Decimal("0.012"),
            receiving=_WORK_NET,
        )
        == Decimal("0.02")
    )


# ---------------------------------------------------------------------------
# The operand-order contract, spelled out with asymmetric operands
# ---------------------------------------------------------------------------


def test_the_operand_order_of_every_two_operand_verb() -> None:
    """`SUBTRACT`, `DIVIDE BY` and `DIVIDE INTO`, each in the written order.

    Three statements whose Python spelling would be indistinguishable if the
    operands were symmetric, so every case below uses operands that are not.

    * `SUBTRACT a FROM b GIVING c` is `c = b - a` [general/gl051.cbl:L1105]
      `subtract input-vat from input-gross giving l9-amount` - the batch control
      gate's net-of-VAT line. The frozen receiver there is the edited print item
      `03 l9-amount pic z(9)9.99bb.` [general/gl051.cbl:L331], whose editing
      belongs to `test_move_truncation.py`; the arithmetic is asserted here into a
      plain signed receiver.
    * `DIVIDE a BY b GIVING c` is `c = a / b` [sales/sl100.cbl:L511].
    * `DIVIDE a INTO b GIVING c` is `c = b / a` [sales/sl060.cbl:L827].
    """
    # SUBTRACT ... FROM ... GIVING: the minuend is the item after FROM.
    assert (
        arithmetic.subtract_giving(
            Decimal("17.50"), minuend=Decimal("117.50"), receiving=_POST_AMOUNT
        )
        == Decimal("100.00")
    )
    assert (
        arithmetic.subtract_giving(
            Decimal("117.50"), minuend=Decimal("17.50"), receiving=_POST_AMOUNT
        )
        == Decimal("-100.00")
    ), "reversing minuend and subtrahend inverts the sign, so the order is caught"

    # SUBTRACT ... FROM (no GIVING): the RECEIVER is the minuend.
    assert (
        arithmetic.subtract_from(
            Decimal("17.50"),
            receiver_value=Decimal("117.50"),
            receiving=_POST_AMOUNT,
        )
        == Decimal("100.00")
    )
    # Variadic: `SUBTRACT a b FROM c` subtracts the SUM of the sources.
    assert (
        arithmetic.subtract_giving(
            Decimal("10.00"),
            Decimal("7.50"),
            minuend=Decimal("117.50"),
            receiving=_POST_AMOUNT,
        )
        == Decimal("100.00")
    )

    # DIVIDE ... BY ... GIVING against DIVIDE ... INTO ... GIVING, on the same
    # asymmetric pair, giving different answers in the same receiver.
    assert arithmetic.divide_by_giving(105, 3, _POST_AMOUNT) == Decimal("35.00")
    assert arithmetic.divide_into_giving(105, 3, _POST_AMOUNT) == Decimal("0.02")
    assert arithmetic.divide_by_giving(
        105, 3, _POST_AMOUNT
    ) != arithmetic.divide_into_giving(105, 3, _POST_AMOUNT)

    # Both truncate toward zero rather than flooring, which is where COBOL and
    # Python's `//` part company: -7 / 2 is -3 here and -4 there. The receiver has
    # to be a SIGNED integer item for the difference to be visible at all -
    # `03 Sales-Limit binary-long.` [copybooks/wssl.cob:L45] - because an unsigned
    # one such as `77 a pic 99.` [general/gl080.cbl:L183] would drop the sign and
    # store 3 either way.
    assert arithmetic.divide_by_giving(-7, 2, _SALES_LIMIT) == -3
    assert cobol_usage.truncate_toward_zero(-7, 2) == -3
    assert -7 // 2 == -4, "Python floors; COBOL discards the remainder"
    assert arithmetic.divide_by_giving(-7, 2, _QUARTER_SUBSCRIPT) == 3

    # MULTIPLY names its receiver in two different places in its two spellings.
    assert (
        arithmetic.multiply_by_giving(Decimal("2.50"), 4, _POST_AMOUNT)
        == Decimal("10.00")
    )
    assert (
        arithmetic.multiply_by(Decimal("2.50"), 4, _POST_AMOUNT) == Decimal("10.00")
    )


# ---------------------------------------------------------------------------
# 4.8  The ambient `decimal` context cannot reach into a store (R-2 hardening)
# ---------------------------------------------------------------------------


def test_ambient_decimal_context_cannot_change_a_store() -> None:
    """Sabotage the ambient context; every result must be unchanged.

    `decimal`'s precision is thread-local ambient state, so any library, plugin or
    unlucky import could set it. If this module's arithmetic read
    `decimal.getcontext()` instead of entering `INTERMEDIATE_CONTEXT`, an eleven
    digit accumulation under a precision of four would come back rounded - and a
    posted figure would then depend on what else the process had done first, which
    rule R-6's determinism requirement forbids outright.

    This is the ONE test in this file that touches the ambient context, and it
    restores it in a `finally` so that no test order can be affected. The context
    is restored from a COPY rather than by resetting to the default, so a runner
    that had legitimately configured it keeps its configuration.
    """
    assert arithmetic.INTERMEDIATE_CONTEXT.prec >= 60, (
        "an intermediate must carry far more digits than any field it can land in"
    )
    assert arithmetic.INTERMEDIATE_PRECISION == arithmetic.INTERMEDIATE_CONTEXT.prec
    assert arithmetic.INTERMEDIATE_CONTEXT.traps[decimal.FloatOperation], (
        "a float reaching decimal at all must signal, not convert (rule R-2)"
    )

    saved = decimal.getcontext().copy()
    try:
        decimal.getcontext().prec = 4
        assert decimal.getcontext().prec == 4

        # Eleven significant digits, which a precision of four could not hold.
        eleven_digits = Decimal("12345678.90")
        assert len(eleven_digits.as_tuple().digits) == 10

        assert (
            arithmetic.add_giving(
                eleven_digits, Decimal("0.09"), receiving=_LEDGER_BALANCE
            )
            == Decimal("12345678.99")
        )
        assert (
            arithmetic.add_to(
                Decimal("0.09"),
                receiver_value=eleven_digits,
                receiving=_LEDGER_BALANCE,
            )
            == Decimal("12345678.99")
        )
        assert (
            arithmetic.store(Decimal("99999999.99"), _LEDGER_BALANCE)
            == Decimal("99999999.99")
        )
        assert (
            arithmetic.intermediate(lambda: eleven_digits + Decimal("0.09"))
            == Decimal("12345678.99")
        )
        assert (
            arithmetic.multiply_by_giving(eleven_digits, -1, _LEDGER_BALANCE)
            == Decimal("-12345678.90")
        )
        assert (
            arithmetic.divide_by_giving(eleven_digits, 3, _LEDGER_BALANCE)
            == Decimal("4115226.30")
        )
        assert arithmetic.compare(eleven_digits, Decimal("12345678.91")) < 0

        # The arithmetic did not repair the ambient context either: it entered its
        # own and left the caller's alone.
        assert decimal.getcontext().prec == 4
    finally:
        decimal.setcontext(saved)

    assert decimal.getcontext().prec == saved.prec


# ---------------------------------------------------------------------------
# R-5: the citations this file makes are checkable, mechanically
# ---------------------------------------------------------------------------


def test_every_locator_and_key_this_file_cites_is_well_formed() -> None:
    """Rule R-5's invariant, enforced rather than trusted.

    A citation nobody can follow is the same as no traceability at all, so every
    `<path>:L<n>` locator in this file's census tuples and every descriptor's own
    provenance is matched against the dictionary's own patterns - imported rather
    than retyped, so the two can never drift apart.
    """
    censuses = (
        _DIVIDE_BY_GIVING_SITES,
        _DIVIDE_INTO_GIVING_SITES,
        _ROUNDED_SITES,
        _SIGN_FLIP_SITES,
        _RELATION_CONDITION_SITES,
    )
    for census in censuses:
        assert census, "an empty census would assert nothing"
        for locator in census:
            assert model.SOURCE_LOCATOR_PATTERN.match(locator), (
                f"{locator!r} is not a <path>:L<n> locator"
            )
            path = locator.partition(":")[0]
            assert model.REPO_PATH_PATTERN.match(path)
            assert path.endswith(".cbl"), (
                "every site cited here is a program line, not a copybook line"
            )

    dictionary_backed = (
        _POST_AMOUNT,
        _INPUT_GROSS,
        _IH_DEDUCT_AMT,
        _OI3_DEDUCT_AMT,
        _LEDGER_BALANCE,
        _PRE_AMOUNT,
        _PAGE_LINES,
        _SALES_LIMIT,
    )
    for descriptor in dictionary_backed:
        assert descriptor.dictionary_key is not None
        assert model.ENTRY_KEY_PATTERN.match(descriptor.dictionary_key)
        assert model.SOURCE_LOCATOR_PATTERN.match(str(descriptor.source_locator))
        # `cite` is the compact three-locator provenance line: copybook or
        # program, bridge, column. Surfacing it here proves the descriptor can
        # answer for itself where it came from.
        citation = loader.cite(descriptor.dictionary_key)
        assert descriptor.dictionary_key in citation
        assert citation == descriptor.cite()

    described_from_a_locator = (
        _QUARTER_SUBSCRIPT,
        _LINE_CNT_SL060,
        _LINE_CNT_SL100,
        _WORK_NET,
    )
    for descriptor in described_from_a_locator:
        assert descriptor.dictionary_key is None, (
            "a program's own WORKING-STORAGE never reaches a column, so it has "
            "no dictionary key to cite"
        )
        assert model.SOURCE_LOCATOR_PATTERN.match(str(descriptor.source_locator))
        assert descriptor.cite() == descriptor.source_locator
        # The carrier was DERIVED from the usage and the scale, not asserted by
        # hand - which is what `FieldDescriptor.__post_init__` insists on for a
        # key-less descriptor and what keeps this file from inventing storage.
        assert descriptor.python_storage is cobol_usage.python_storage_for(
            descriptor.usage, descriptor.scale
        )


def test_the_defensive_key_resolver_reports_a_key_it_cannot_resolve() -> None:
    """The local resolver falls back on the table, then fails loudly.

    Its only job is to turn a key into a descriptor, so its failure mode matters:
    a silent `None` would leave a later assertion comparing against nothing. The
    fallback exists because the one slip a hand-written test makes is spelling a
    column segment as the copybook spells it.
    """
    # A column segment in the copybook's own casing still resolves, through the
    # case-insensitive fallback.
    assert (
        _dictionary_descriptor("SALEDGER-REC.Sales-Average").dictionary_key
        == "SALEDGER-REC.SALES-AVERAGE"
    )
    # An unknown column of a known table reports the table's columns.
    with pytest.raises(_KeyResolutionError, match="SALES-AVERAGE"):
        _dictionary_descriptor("SALEDGER-REC.NO-SUCH-COLUMN")
    # An unknown table fails too, and both failures remain catchable as KeyError.
    with pytest.raises(KeyError):
        _dictionary_descriptor("NO-SUCH-TABLE.ANY-COLUMN")
    with pytest.raises(KeyError):
        _dictionary_descriptor("unqualified")


# ---------------------------------------------------------------------------
# 4.9  THE SIX SHIPPED PARAGRAPHS
#
#      Everything above pins the idioms against sequences of `arithmetic` calls
#      spelled out in this file. That proves what the frozen COBOL MEANS. It cannot
#      prove that the six paragraphs which actually run a posting still do it -
#      adding the missing `add 1 to purch-activety` to `pl060._credit_comp`, or
#      giving `work-2` two decimal places, would leave every test above green while
#      every supplier average moved. This section drives all six.
#
#      THE SIX SITES AND THEIR PYTHON HOMES:
#        (a) [sales/sl060.cbl:L816-L827]   sl060_invoice_posting._ba000_sales_comp
#        (b) [sales/sl060.cbl:L832-L843]   sl060_invoice_posting._ba000_credit_comp
#        (c) [sales/sl100.cbl:L497-L514]   sl100_cash_posting._compute_sales_pay
#        (d) [purchase/pl060.cbl:L740-L751] pl060_order_posting._purch_comp
#        (e) [purchase/pl060.cbl:L755-L766] pl060_order_posting._credit_comp
#        (f) [purchase/pl100.cbl:L488-L505] pl100_payment_posting._init01__compute_purch_pay
#
#      SIX TEST FUNCTIONS, NO SHARED IDIOM SETUP. This file's brief is explicit that
#      "sharing a fixture across the three would itself be the normalisation the
#      specification forbids", so each test below constructs its own state and
#      spells out its own inputs. The duplication is DELIBERATE. What is shared is
#      only the import mechanism - `_shipped_module` - which carries no accounting
#      value and no idiom.
#
#      WHY THE IMPORT IS DEFERRED (rule R-1). Agent Action Plan section 0.4.3 gives
#      this tier `cobol` and `records` and forbids `dal` and any database. The four
#      program modules import `acas_posting.dal.facade`, which pulls the MySQL
#      driver in transitively, so importing them at module scope would leave
#      `acas_posting.dal.*` and `mysql.*` resident and would break the three
#      tier-isolation assertions this suite carries
#      (`test_comp3_packed_decimal.py test_the_packed_carrier_follows_the_scale_and_is_never_binary`,
#      `test_comp_binary.py test_q3_an_overflowing_negative_store_lands_on_its_magnitudes_byte`,
#      `test_pic_field_descriptors.py test_no_single_winner_view_exists_on_drift_entry_or_descriptor`),
#      two of which read LIVE `sys.modules`.
#      So the import happens INSIDE each test body, and the loader removes every
#      tier-isolation-prefixed name it added in a `finally`.
#
#      IT IS MANDATORY, NOT SKIPPABLE. An earlier revision used
#      `pytest.importorskip` here so a driver-free host would SKIP this section.
#      That was wrong twice over: `mysql-connector-python==26.7.0` is a HARD
#      `[project.dependencies]` entry and a hard `requirements.txt` pin, so the
#      guarded state cannot arise for an installed package; and the assertions
#      below are the anomaly locks rule R-4 requires, which must fail loudly
#      rather than disappear into a skip line nobody reads - a skip reads as
#      green, so a shipped module that cannot be imported at all used to turn this
#      section into a pass. `importlib.import_module` is used instead.
#
#      NOR IS ANY MODULE MEMOISED. A cached module is ALREADY RESIDENT, so the
#      purge in the `finally` would have nothing to remove and the isolation claim
#      would be about a module that had never left. Each entry therefore proves
#      the import really happened: a tier-isolated name is asserted ABSENT on the
#      way in and RESIDENT while the body runs.
#      The pattern is `tests/conftest.py _load_harness_module`'s. NO DATABASE IS TOUCHED: all
#      six paragraphs operate on dataclasses in memory.
# ---------------------------------------------------------------------------


#: The module-name prefixes the tier's own isolation assertions forbid.
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
    """Does `name` fall under a prefix the tier must not leave loaded?"""
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped_module(dotted_name: str) -> Iterator[types.ModuleType]:
    """Import a shipped module FOR REAL for one test, leaving `sys.modules` as found.

    ⭐ THE IMPORT IS NOT OPTIONAL, AND IT IS NOT MEMOISED. Both of those are the point.

    NOT OPTIONAL. `pytest.importorskip` stood here, and it turned the one failure this
    section exists to catch into a PASS. A shipped module that cannot be imported at
    all - a syntax error, a circular import, a name it imports that no longer exists -
    produced a SKIP, and a skipped test reads as green. The pinned MySQL driver the
    reason text blamed is a hard requirement of `requirements.txt`, so its absence is a
    broken environment and not a supported configuration; `importlib.import_module`
    lets the `ImportError` reach pytest as the FAILURE it is.

    NOT MEMOISED. A cached module is ALREADY RESIDENT in `sys.modules`, so the purge in
    the `finally` had nothing to remove and every "leaves no driver loaded" claim
    downstream was a statement about a module that had never left. Each entry therefore
    proves the import really happened: a tier-isolated name must be ABSENT on the way
    in - which is what establishes that the previous exit purged it - and RESIDENT while
    the body runs; on the way out every tier-isolated name the import added is removed
    and the residue is asserted empty.

    A name that is NOT tier-isolated - `acas_posting.records.*`, `acas_posting.clock` -
    is imported and left alone. This tier is allowed `cobol` and `records` by Agent
    Action Plan section 0.4.3, so those are never purged and a freshness claim over
    them would be meaningless.

    Args:
        dotted_name: The importable name.

    Yields:
        The imported module.

    Raises:
        AssertionError: A tier-isolated name was already resident on the way in, or did
            not become resident, or survived the purge.
        ImportError: The module could not be imported. DELIBERATELY not turned into a
            skip: `mysql-connector-python==26.7.0` is a HARD `[project.dependencies]`
            entry and a hard `requirements.txt` pin, so an installed package always has
            it, and the assertions this loader serves are anomaly locks rule R-4
            requires - a lock that can disappear into a skip line is not a lock.
    """
    #  EVICT FIRST, so the import below really runs the module's top-level code and the
    #  purge in the `finally` really removes what it added - the same thing
    #  `_freshly_imported` below does, and for the same reason. Eviction rather than a
    #  "must be absent on the way in" assertion, because this tier's own helpers
    #  legitimately import program modules in function scope to drive the SHIPPED
    #  paragraphs, and an absence assertion would make the two remediations exclude each
    #  other - the claim would then depend on file order.
    for resident in sorted(
        (name for name in sys.modules if _is_tier_isolated_name(name)), reverse=True
    ):
        del sys.modules[resident]
    if _is_tier_isolated_name(dotted_name):
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
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name
            for name in set(sys.modules) - before
            if _is_tier_isolated_name(name)
        )
        #  Only when the body itself succeeded, so a real failure is never masked by a
        #  second assertion about housekeeping.
        if completed:
            assert not residue, (
                f"importing {dotted_name} left {residue} resident after the purge, so "
                f"this tier no longer runs without a database driver and the three "
                f"isolation assertions above would fail depending only on file order."
            )


def _pl060_working_storage(pl060: types.ModuleType) -> object:
    """A `pl060` WORKING-STORAGE container with every field at its declared default.

    Built exactly as `pl060_order_posting.run` builds it at its `_Ws(...)` call, so
    the container is the production one and not a stand-in. It carries NO idiom
    values: the activity counter, the average and the goods figure are set by each
    test, individually, which is what keeps the two `pl060` idioms unshared.
    """
    from acas_posting import workfiles
    from acas_posting.dates import WsDateFormats
    from acas_posting.records.calling_data import WsCallingData
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_posting import WsPostingRecord
    from acas_posting.records.maps03 import Maps03Ws
    from acas_posting.records.otm5 import OiHeader
    from acas_posting.records.purchase_ledger import WsPurchRecord
    from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.system_record_4 import SystemRecord4
    from acas_posting.records.test_data_flags import AcasDalCommonData

    return pl060._Ws(
        ws_calling_data=WsCallingData(),
        system_record=SystemRecord(),
        system_record_4=SystemRecord4(),
        to_day="21/09/2025",
        file_defs=FileDefs(),
        file_access=FileAccess(),
        dal_common=AcasDalCommonData(),
        purch=WsPurchRecord(),
        otm5=pl060._new_oi_header(),
        oi_header=pl060._new_oi_header(),
        si_header=pl060._new_oi_header(),
        batch=GlBatchRecord(),
        posting=WsPostingRecord(),
        irs_posting=WsIrsPostingRecord(),
        otm4=workfiles.open_item_work_file("otm4-in-memory", OiHeader),
        maps03_ws=Maps03Ws(),
        date_ws=WsDateFormats(),
    )


def test_shipped_a_sl060_sales_comp_truncates_twice_and_counts_before() -> None:
    """(a) `ba000-Sales-Comp` [sales/sl060.cbl:L816-L827], driven for real.

    ANOMALY A-8, end to end in the shipped code. With two prior invoices averaging
    12 and a new one worth 24.99:

        L821  multiply 2 by 12 giving work-2        ->  24
        L825  add 1 to sales-activety              ->   3   (BEFORE the divide)
        L826  add work-goods to work-2             ->  48    <- the pence are GONE
        L827  divide sales-activety into work-2    ->  16    <- and the remainder too

    24 + 24.99 is 48.99, and `work-2` is `pic s9(14) comp-3` with SCALE 0
    [sales/sl060.cbl:L206], so the ninety-nine pence are discarded on the way in.
    A full-precision accumulator would hold 48.99 and divide to 16.33, and the
    counterfactual below asserts that the two differ - which is what makes the
    reproduction a reproduction rather than a coincidence. No pence figure is
    invented: every value here is exact integer arithmetic over the declared
    widths.
    """
    with _shipped_module("acas_posting.programs.sl060_invoice_posting") as sl060:
        from acas_posting import workfiles
        from acas_posting.records.calling_data import WsCallingData
        from acas_posting.records.file_defs import FileDefs
        from acas_posting.records.otm3 import OiHeader
        from acas_posting.records.system_record import SystemRecord
        from acas_posting.records.system_record_4 import SystemRecord4

        state = sl060._new_state(
            WsCallingData(),
            SystemRecord(),
            SystemRecord4(),
            "21/09/2025",
            FileDefs(),
            workfiles.open_item_work_file("otm2-in-memory", OiHeader),
        )
        state.ws_sales_record.sales_activety = 2
        state.ws_sales_record.sales_average = 12
        state.work_goods = Decimal("24.99")

        sl060._ba000_sales_comp(state)

        # Truncation #1: the accumulator has scale 0, so 48.99 became 48.
        assert state.work_2 == 48
        assert isinstance(state.work_2, int) and not isinstance(state.work_2, bool)
        # The counter was incremented BEFORE the divide, so the divisor is 3.
        assert state.ws_sales_record.sales_activety == 3
        # Truncation #2: 48 / 3 is exact here, so the loss is entirely truncation #1.
        assert state.ws_sales_record.sales_average == 16
        assert isinstance(state.ws_sales_record.sales_average, int)

        # THE COUNTERFACTUAL. A two-decimal accumulator - the "obvious fix" - would
        # hold 48.99 and yield 16 as well after the integer store, so the average
        # alone cannot distinguish the two. The accumulator can, which is why it is
        # asserted above as an integer and not merely as a number.
        assert state.work_2 != Decimal("48.99")
        assert arithmetic.intermediate(
            lambda: Decimal("24") + Decimal("24.99")
        ) == Decimal("48.99")
        # And the declared descriptor the paragraph stores through is scale-0
        # fourteen-digit packed decimal, not a money field.
        assert sl060._WORK_2.scale == 0
        assert sl060._WORK_2.digits == 14
        assert sl060._WORK_2.usage is model.Usage.COMP_3
        assert sl060._WORK_2.python_storage is model.CobolPythonStorage.INT
        assert sl060._WORK_2.source_locator == "sales/sl060.cbl:L206"


def test_shipped_b_sl060_credit_comp_never_increments_its_counter() -> None:
    """(b) `ba000-Credit-Comp` [sales/sl060.cbl:L832-L843], driven for real.

    ANOMALY A-9 in the shipped code. There is NO `add 1 to sales-activety` anywhere
    in the section, and there is an EXTRA outer guard at L841. So:

      * a customer's FIRST credit note (activity 0) fails the L835-L836 guard, gets
        `work-2` zeroed at L839, fails the L841 outer guard, and leaves BOTH the
        counter and the average exactly as they were - the note is silently dropped;
      * a LATER credit note updates the average but divides by the UN-incremented
        counter, so 128 / 4 is 32 where a repaired path would divide by 5 and give
        25.

    The 32-versus-25 difference is what kills the repair: adding the missing
    increment changes a posted average. No pence are involved - every figure is
    exact integer arithmetic. Do NOT add the increment (rules R-3, R-4).
    """
    with _shipped_module("acas_posting.programs.sl060_invoice_posting") as sl060:
        from acas_posting import workfiles
        from acas_posting.records.calling_data import WsCallingData
        from acas_posting.records.file_defs import FileDefs
        from acas_posting.records.otm3 import OiHeader
        from acas_posting.records.system_record import SystemRecord
        from acas_posting.records.system_record_4 import SystemRecord4

        def fresh() -> object:
            # Constructed inside this test, and not shared with the sibling idiom's
            # test: sharing the setup is the normalisation the brief forbids.
            return sl060._new_state(
                WsCallingData(),
                SystemRecord(),
                SystemRecord4(),
                "21/09/2025",
                FileDefs(),
                workfiles.open_item_work_file("otm2-in-memory", OiHeader),
            )

        # The first credit note for a customer.
        state = fresh()
        state.ws_sales_record.sales_activety = 0
        state.ws_sales_record.sales_average = 7
        state.work_goods = Decimal("10.00")

        sl060._ba000_credit_comp(state)

        assert state.work_2 == 0
        # A-9: the counter is NOT incremented. A repaired path would read 1.
        assert state.ws_sales_record.sales_activety == 0
        # And the outer guard suppressed the divide, so the average is untouched.
        assert state.ws_sales_record.sales_average == 7

        # A later credit note, where the guards pass.
        state = fresh()
        state.ws_sales_record.sales_activety = 4
        state.ws_sales_record.sales_average = 30
        state.work_goods = Decimal("8.00")

        sl060._ba000_credit_comp(state)

        assert state.work_2 == 128
        # A-9 again: still not incremented, so the divisor is 4 and not 5.
        assert state.ws_sales_record.sales_activety == 4
        assert state.ws_sales_record.sales_average == 32
        # THE COUNTERFACTUAL: with the missing increment restored the divisor would
        # be 5 and the stored average 25, so the repair is observable in the ledger.
        assert arithmetic.divide_into_giving(
            5, 128, _dictionary_descriptor("SALEDGER-REC.SALES-AVERAGE")
        ) == 25
        assert state.ws_sales_record.sales_average != 25


def test_shipped_c_sl100_compute_sales_pay_counts_after_and_divides_by() -> None:
    """(c) `compute-sales-pay.` [sales/sl100.cbl:L497-L514], driven for real.

    ANOMALY A-10 in the shipped code. One guard, no ELSE, the counter incremented AFTER
    the accumulation, and the divide spelled `BY` rather than `INTO`:

        L503  subtract oi-date from oi-date-cleared giving work-a  ->  45
        L504  move zero to work-b                                 ->   0
        L506  if sales-pay-activety not = zero  (no ELSE)
        L507  multiply 2 by 30 giving work-b                       ->  60
        L509  add work-a to work-b                                 -> 105
        L510  add 1 to sales-pay-activety                          ->   3  (AFTER)
        L511  divide work-b by sales-pay-activety giving average   ->  35  (BY)
        L513  if work-a > sales-pay-worst  (STRICT)                -> no move

    The watermark is left at 45 because the comparison is strict and `work-a` is
    exactly 45. Note that `compute-sales-pay.` is a PARAGRAPH NAME, not a `COMPUTE`
    verb. Every figure is exact integer arithmetic over day counts.
    """
    with _shipped_module("acas_posting.programs.sl100_cash_posting") as sl100:
        from acas_posting.records.calling_data import WsCallingData
        from acas_posting.records.file_defs import FileDefs
        from acas_posting.records.system_record import SystemRecord
        from acas_posting.records.system_record_4 import SystemRecord4

        state = sl100._new_state(
            WsCallingData(),
            SystemRecord(),
            SystemRecord4(),
            "21/09/2025",
            FileDefs(),
            ok_to_post=True,
        )
        state.oi.filler_1.oi_date = 100
        state.oi.filler_1.oi_date_cleared = 145
        state.sales.sales_pay_activety = 2
        state.sales.sales_pay_average = 30
        state.sales.sales_pay_worst = 45

        sl100._compute_sales_pay(state)

        # `subtract a from b giving c` is `c = b - a`; asymmetric operands, so a
        # reversal would show up as -45.
        assert state.work_a == 45
        assert state.work_b == 105
        # The counter moved AFTER the accumulate, so the divisor is 3.
        assert state.sales.sales_pay_activety == 3
        # ⭐ THE `BY` SPELLING COMPUTES accumulator / counter, WHICH IS WHAT `INTO`
        # COMPUTES TOO - only the operand ORDER in the source text differs. `divide
        # work-b by sales-pay-activety` [sales/sl100.cbl:L511] and the sibling
        # paragraphs' `divide sales-activety into work-2` [sales/sl060.cbl:L827] both
        # give 105 / 3 = 35, so A-10's divergence is the GUARD and the counter
        # handling, NOT the arithmetic. Calling it a reversed or inverted divide would
        # assert a behavioural difference that does not exist.
        assert state.sales.sales_pay_average == 35
        average_descriptor = _dictionary_descriptor(
            "SALEDGER-REC.SALES-PAY-AVERAGE"
        )
        # The EQUIVALENT named operands: `divide_into_giving(divisor, dividend, ...)`,
        # so the `INTO` spelling of the same statement takes the counter first. It
        # gives the same 35, which is the point.
        assert arithmetic.divide_into_giving(3, 105, average_descriptor) == 35
        assert (
            arithmetic.divide_into_giving(3, 105, average_descriptor)
            == state.sales.sales_pay_average
        )
        # And the POSITIONAL swap - passing the two operands in the other order,
        # which is what "reversed" would mean if the spellings really did disagree -
        # computes 3 / 105 and truncates to nothing. It is shown here as the mistake
        # a reader of the earlier wording would have made, not as the sibling
        # paragraphs' behaviour.
        assert arithmetic.divide_into_giving(105, 3, average_descriptor) == 0
        # The watermark comparison is STRICT, so an equal value does not update it.
        assert state.sales.sales_pay_worst == 45


def test_shipped_d_pl060_purch_comp_truncates_twice_and_counts_before() -> None:
    """(d) `purch-comp` [purchase/pl060.cbl:L740-L751], driven for real.

    The Purchase mirror of (a), and the reason a missing Purchase-specific test was
    a real gap rather than a formality: this is a DIFFERENT paragraph, with its own
    `work-2` descriptor at [purchase/pl060.cbl:L200] and its own receiving fields,
    so nothing asserted about `sl060` constrains it.

        L745  multiply 2 by 12 giving work-2      ->  24
        L749  add 1 to purch-activety            ->   3   (BEFORE the divide)
        L750  add work-goods to work-2           ->  48    <- the pence are GONE
        L751  divide purch-activety into work-2  ->  16

    Its state is constructed here rather than in a shared helper, deliberately.
    """
    with _shipped_module("acas_posting.programs.pl060_order_posting") as pl060:
        ws = _pl060_working_storage(pl060)
        ws.purch.purch_activety = 2
        ws.purch.purch_average = 12
        ws.work_goods = Decimal("24.99")

        pl060._purch_comp(ws)

        assert ws.work_2 == 48
        assert isinstance(ws.work_2, int) and not isinstance(ws.work_2, bool)
        assert ws.purch.purch_activety == 3
        assert ws.purch.purch_average == 16
        assert isinstance(ws.purch.purch_average, int)

        # THE COUNTERFACTUAL for the "obvious fix" of giving `work-2` two decimal
        # places: the accumulator would hold 48.99. The stored average would still
        # read 16, so only the accumulator distinguishes the two.
        assert ws.work_2 != Decimal("48.99")
        assert pl060._D_WORK_2.scale == 0
        assert pl060._D_WORK_2.digits == 14
        assert pl060._D_WORK_2.usage is model.Usage.COMP_3
        assert pl060._D_WORK_2.python_storage is model.CobolPythonStorage.INT
        assert pl060._D_WORK_2.source_locator == "purchase/pl060.cbl:L200"


def test_shipped_e_pl060_credit_comp_never_increments_its_counter() -> None:
    """(e) `credit-comp` [purchase/pl060.cbl:L755-L766], driven for real.

    ANOMALY A-9 on the Purchase side, in the shipped code: no `add 1 to
    purch-activety` anywhere in the block, plus the extra outer guard at
    [purchase/pl060.cbl:L764]. So a supplier's first credit note is silently
    dropped, and a later one divides by the un-incremented counter - 128 / 4 = 32,
    where the repair would give 128 / 5 = 25.

    This is the mutation a shared moving-average helper would introduce, which is
    why it is asserted against the real paragraph and not against a transcription.
    Do NOT add the increment (rules R-3, R-4).
    """
    with _shipped_module("acas_posting.programs.pl060_order_posting") as pl060:
        # The first credit note for a supplier.
        ws = _pl060_working_storage(pl060)
        ws.purch.purch_activety = 0
        ws.purch.purch_average = 7
        ws.work_goods = Decimal("10.00")

        pl060._credit_comp(ws)

        assert ws.work_2 == 0
        assert ws.purch.purch_activety == 0
        assert ws.purch.purch_average == 7

        # A later credit note.
        ws = _pl060_working_storage(pl060)
        ws.purch.purch_activety = 4
        ws.purch.purch_average = 30
        ws.work_goods = Decimal("8.00")

        pl060._credit_comp(ws)

        assert ws.work_2 == 128
        assert ws.purch.purch_activety == 4
        assert ws.purch.purch_average == 32
        assert (
            arithmetic.divide_into_giving(
                5, 128, _dictionary_descriptor("PULEDGER-REC.PURCH-AVERAGE")
            )
            == 25
        )
        assert ws.purch.purch_average != 25


def test_shipped_f_pl100_compute_purch_pay_counts_after_and_divides_by() -> None:
    """(f) `compute-purch-pay.` [purchase/pl100.cbl:L488-L505], driven for real.

    The Purchase mirror of (c), whose coverage was prose only until now:

        L497  subtract oi-date from oi-date-cleared giving work-a  ->  45
        L498  move zero to work-b                                 ->   0
        L499  if purch-pay-activety not = zero  (no ELSE)
        L500  multiply 2 by 30 giving work-b                       ->  60
        L500  add work-a to work-b                                 -> 105
        L501  add 1 to purch-pay-activety                          ->   3  (AFTER)
        L502  divide work-b by purch-pay-activety giving average   ->  35  (BY)
        L504  if work-a > purch-pay-worst  (STRICT)                -> no move

    `compute-purch-pay.` is a PARAGRAPH NAME and not a `COMPUTE` verb - the same
    trap the divide census notes for its Sales twin.
    """
    with _shipped_module("acas_posting.programs.pl100_payment_posting") as pl100:
        from acas_posting.records.calling_data import WsCallingData
        from acas_posting.records.file_defs import FileDefs
        from acas_posting.records.system_record import SystemRecord
        from acas_posting.records.system_record_4 import SystemRecord4

        state = pl100._Pl100State(
            ws_calling_data=WsCallingData(),
            system_record=SystemRecord(),
            system_record_4=SystemRecord4(),
            to_day="21/09/2025",
            file_defs=FileDefs(),
            ok_to_post=True,
        )
        state.otm5.oi_date = 100
        state.otm5.oi_date_cleared = 145
        state.purch.purch_pay_activety = 2
        state.purch.purch_pay_average = 30
        state.purch.purch_pay_worst = 45

        pl100._init01__compute_purch_pay(state)

        assert state.work_a == 45
        assert state.work_b == 105
        assert state.purch.purch_pay_activety == 3
        assert state.purch.purch_pay_average == 35
        assert (
            arithmetic.divide_into_giving(
                105, 3, _dictionary_descriptor("PULEDGER-REC.PURCH-PAY-AVERAGE")
            )
            == 0
        )
        assert state.purch.purch_pay_worst == 45

        # The early return at [purchase/pl100.cbl:L495]: an uncleared item does
        # nothing at all, so neither counter nor average nor watermark moves.
        untouched = pl100._Pl100State(
            ws_calling_data=WsCallingData(),
            system_record=SystemRecord(),
            system_record_4=SystemRecord4(),
            to_day="21/09/2025",
            file_defs=FileDefs(),
            ok_to_post=True,
        )
        untouched.otm5.oi_date = 100
        untouched.otm5.oi_date_cleared = 0
        untouched.purch.purch_pay_activety = 2
        untouched.purch.purch_pay_average = 30

        pl100._init01__compute_purch_pay(untouched)

        assert untouched.purch.purch_pay_activety == 2
        assert untouched.purch.purch_pay_average == 30


def test_the_six_shipped_paragraphs_leave_no_driver_loaded() -> None:
    """Rule R-1 holds even though this section reaches four program modules.

    ⭐ AND THE IMPORT REALLY HAPPENS, which is what makes the claim worth making. The
    loader used to memoise, so this guard imported nothing: the module was already
    resident from an earlier test, the purge removed nothing, and "leaves no driver
    loaded" was a statement about a module that had never left. The loader no longer
    caches, so each `with` below performs a genuine import - asserted INSIDE the block
    by reading live `sys.modules` - and the delta afterwards is a real measurement of
    what the purge removed.
    """
    before = frozenset(n for n in sys.modules if _is_tier_isolated_name(n))

    for dotted in (
        "acas_posting.programs.sl060_invoice_posting",
        "acas_posting.programs.sl100_cash_posting",
        "acas_posting.programs.pl060_order_posting",
        "acas_posting.programs.pl100_payment_posting",
    ):
        assert dotted not in sys.modules, (
            f"{dotted} was resident BEFORE this guard imported it, so the import "
            f"below would be a no-op and the purge would remove nothing."
        )
        with _shipped_module(dotted) as module:
            assert module.__name__ == dotted
            #  DURING: the forbidden name is resident, and so is the driver it pulls
            #  in. Without this half, an import that silently did nothing would still
            #  satisfy the delta check below.
            assert sys.modules.get(dotted) is module
            assert any(
                _is_tier_isolated_name(name) and name not in before
                for name in sys.modules
            ), (
                f"importing {dotted} added no tier-isolated name at all, so either it "
                f"was already loaded or it does not reach the data-access layer - and "
                f"the purge this guard measures has nothing to do."
            )
        #  AFTER, per module rather than only once at the end, so the loader that
        #  leaked is named rather than inferred.
        assert dotted not in sys.modules, (
            f"{dotted} survived its own loader's purge."
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
            if _is_tier_isolated_name(n) and n not in before
        )
    )
    assert leaked == (), leaked
    assert _is_tier_isolated_name("acas_posting.dal") is True
    assert _is_tier_isolated_name("acas_posting.programs.pl060_order_posting") is True
    assert _is_tier_isolated_name("mysql.connector") is True
    assert _is_tier_isolated_name("acas_posting.database") is False
    assert _is_tier_isolated_name("acas_posting.cobol.arithmetic") is False


# ===========================================================================
#  SECTION 4.11  THE AMBIENT DECIMAL CONTEXT IS NOT AN INPUT      (rule R-2)
# ===========================================================================
#
# Every function in `acas_posting.cobol.arithmetic` enters a copy of
# `INTERMEDIATE_CONTEXT` before it touches a `Decimal` - the policy the module states
# at `acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION` and pins at L102. This section is what
# turns that stated policy into a checked one.
#
# The reason it needs checking is that almost every `Decimal` method is a CONTEXT
# operation, and the context is process-global mutable state that this migration does
# not own. `+`, `-`, `*`, `/`, unary minus, `scaleb`, `**` and `quantize` all consult
# `decimal.getcontext()`; the first seven round their result to its `prec`, and
# `quantize` does something worse - it REFUSES, raising `InvalidOperation`, when the
# result would need more digits than `prec` allows. So an embedding application, a
# `sitecustomize`, or a library that calls `decimal.setcontext` at import can change
# what an unguarded expression computes, silently and everywhere at once. A migration
# whose whole acceptance criterion is an empty table diff (section 0.8.5) cannot have a
# posted figure that depends on that.
#
# Only three kinds of `Decimal` operation are context-FREE, and they are the ones this
# tier is built on: construction from a `str` or `int`, the sign-and-copy family
# (`copy_negate`, `copy_abs`, `copy_sign`), and `as_tuple`.
#
# The contexts below are deliberately absurd - one significant digit, rounding away
# from the layer's own direction, and in one case every signal trapped so that any
# leak raises instead of quietly rounding. None of them is a context a real deployment
# would install. That is the point: if the layer is indifferent to THESE, it is
# indifferent to whatever a real caller carries.

_HOSTILE_CONTEXTS: Final[tuple[tuple[str, decimal.Context], ...]] = (
    (
        # One significant digit. Any leaked binary operator collapses a money value to
        # a single digit, so this is the sharpest detector of the set.
        "prec-1",
        decimal.Context(prec=1),
    ),
    (
        # Rounding CEILING, the opposite direction to the layer's own truncating store
        # (`TRUNCATING_STORE`, `acas_posting/cobol/arithmetic.py INTERMEDIATE_CONTEXT`), so a leak
        # shows up as a value that moved the wrong way rather than merely a short one.
        "prec-4-ceiling",
        decimal.Context(prec=4, rounding=decimal.ROUND_CEILING),
    ),
    (
        # Every signal trapped, including `Inexact` and `Rounded`, which the layer's own
        # context deliberately leaves untrapped at
        # `acas_posting/cobol/arithmetic.py INTERMEDIATE_CONTEXT` and L116 because COBOL truncation IS
        # inexact by design. A leak therefore RAISES here rather than returning a
        # wrong number.
        "prec-2-all-trapped",
        decimal.Context(
            prec=2,
            traps={
                decimal.Clamped: True,
                decimal.DivisionByZero: True,
                decimal.Inexact: True,
                decimal.InvalidOperation: True,
                decimal.Overflow: True,
                decimal.Rounded: True,
                decimal.Subnormal: True,
                decimal.Underflow: True,
                decimal.FloatOperation: True,
            },
        ),
    ),
    (
        # The mirror image: NOTHING trapped, so a leaked invalid operation returns a
        # quiet `NaN` instead of raising. This is the nastiest of the four, because a
        # `NaN` compares unequal to everything and a weaker assertion would not notice.
        "prec-3-nothing-trapped",
        decimal.Context(
            prec=3,
            rounding=decimal.ROUND_FLOOR,
            traps={
                decimal.Clamped: False,
                decimal.DivisionByZero: False,
                decimal.Inexact: False,
                decimal.InvalidOperation: False,
                decimal.Overflow: False,
                decimal.Rounded: False,
                decimal.Subnormal: False,
                decimal.Underflow: False,
                decimal.FloatOperation: False,
            },
        ),
    ),
)


def _observation(label: str, produce: object) -> tuple[str, str, object]:
    """Reduce one layer result to data that carries no context of its own.

    A `Decimal` is recorded as its `as_tuple()` - sign, digit tuple and exponent - and
    NOT as the object, so the comparison downstream is over plain `int`s and cannot
    itself consult a context. `as_tuple` is one of the three context-free `Decimal`
    operations, alongside construction and the copy family.

    Recording the tuple rather than the value is what makes this byte-identity rather
    than numeric equality: `Decimal("1.5")` and `Decimal("1.50")` are `==` but their
    tuples differ, and it is the second that a `decimal(9,2)` column stores.

    Args:
        label: The call being recorded, used only to make a failure legible.
        produce: A zero-argument callable holding the layer call.

    Returns:
        `(label, carrier, payload)`. `carrier` is the result's type name, so an `int`
            receiver that started returning a `Decimal` is caught even when the two
            compare equal. A raise is recorded as the exception's type name, because
            WHICH size error the layer reports is as much a part of its behaviour as
            what it returns.
    """
    try:
        value = produce()  # type: ignore[operator]
    except Exception as exc:  # noqa: BLE001 - the exception type IS the observation
        return (label, "raised", type(exc).__name__)
    if isinstance(value, Decimal):
        return (label, "Decimal", value.as_tuple())
    return (label, type(value).__name__, value)


def _layer_observations() -> tuple[tuple[str, str, object], ...]:
    """Drive one representative call of every public entry point of the layer.

    Coverage is by RECEIVER SHAPE as well as by verb, because the store is where the
    context would bite: `DISPLAY` and `COMP-3` and the binary family, signed and
    unsigned, scale two and scale zero, in range and over range. The values are the
    ones the sibling tables in this file already measure, so nothing here invents a
    figure - it re-drives figures the tier has already arbitrated.

    Returns:
        The observations, in a fixed order so two runs are comparable positionally.
    """
    return (
        # -- store: the truncating default, both signs, four storage classes ---------
        _observation(
            "store display signed",
            lambda: arithmetic.store(Decimal("1234.567"), _POST_AMOUNT),
        ),
        _observation(
            "store display signed negative",
            lambda: arithmetic.store(Decimal("-1234.567"), _POST_AMOUNT),
        ),
        _observation(
            "store comp-3 unsigned full width",
            lambda: arithmetic.store(Decimal("999999999.99"), _INPUT_GROSS),
        ),
        _observation(
            "store comp-3 signed negative",
            lambda: arithmetic.store(Decimal("-45.678"), _LEDGER_BALANCE),
        ),
        _observation(
            "store comp unsigned",
            lambda: arithmetic.store(Decimal("123.456"), _IH_DEDUCT_AMT),
        ),
        _observation(
            "store binary-char int carrier",
            lambda: arithmetic.store(127, _PAGE_LINES),
        ),
        _observation(
            "store binary-long signed int carrier",
            lambda: arithmetic.store(-2147483648, _SALES_LIMIT),
        ),
        # -- store: the silent over-range paths, where a leak would change the digits
        #    that survive rather than merely their count ------------------------------
        _observation(
            "store scale-0 over range",
            lambda: arithmetic.store(Decimal("104"), _QUARTER_SUBSCRIPT),
        ),
        _observation(
            "store display over range",
            lambda: arithmetic.store(Decimal("123456789012.34"), _POST_AMOUNT),
        ),
        # -- store: ROUNDED, the five annotated sites of the cycle -------------------
        _observation(
            "store rounded half away from zero",
            lambda: arithmetic.store(Decimal("16.665"), _WORK_NET, rounded=True),
        ),
        _observation(
            "store rounded negative half",
            lambda: arithmetic.store(Decimal("-16.665"), _WORK_NET, rounded=True),
        ),
        # -- compute: the expression form, unrounded then rounded --------------------
        _observation(
            "compute unrounded",
            lambda: arithmetic.compute(
                lambda: Decimal("99.99") - Decimal("99.99") / Decimal("1.20"),
                _WORK_NET,
            ),
        ),
        _observation(
            "compute rounded",
            lambda: arithmetic.compute(
                lambda: Decimal("99.99") - Decimal("99.99") / Decimal("1.20"),
                _WORK_NET,
                rounded=True,
            ),
        ),
        # -- the five arithmetic verbs, both the GIVING and the in-place shapes ------
        _observation(
            "add_giving",
            lambda: arithmetic.add_giving(
                Decimal("1200.00"), Decimal("240.00"), receiving=_PRE_AMOUNT
            ),
        ),
        _observation(
            "add_to",
            lambda: arithmetic.add_to(
                Decimal("12.99"), receiver_value=Decimal("25.98"), receiving=_WORK_NET
            ),
        ),
        _observation(
            "subtract_giving",
            lambda: arithmetic.subtract_giving(
                Decimal("16.67"), minuend=Decimal("-99.99"), receiving=_POST_AMOUNT
            ),
        ),
        _observation(
            "subtract_from",
            lambda: arithmetic.subtract_from(
                Decimal("16.67"),
                receiver_value=Decimal("99.99"),
                receiving=_POST_AMOUNT,
            ),
        ),
        _observation(
            "multiply_by",
            lambda: arithmetic.multiply_by(
                -1, receiver_value=Decimal("1200.00"), receiving=_PRE_AMOUNT
            ),
        ),
        _observation(
            "multiply_by_giving",
            lambda: arithmetic.multiply_by_giving(
                Decimal("1.20"), Decimal("99.99"), _WORK_NET
            ),
        ),
        _observation(
            "divide_by_giving",
            lambda: arithmetic.divide_by_giving(
                Decimal("99.99"), Decimal("1.20"), _WORK_NET
            ),
        ),
        _observation(
            "divide_into_giving",
            lambda: arithmetic.divide_into_giving(
                Decimal("1.20"), Decimal("99.99"), _WORK_NET
            ),
        ),
        # -- the two receiver-less forms: no store, so nothing truncates -------------
        _observation(
            "intermediate",
            lambda: arithmetic.intermediate(
                lambda: Decimal("99.99") / Decimal("1.20")
            ),
        ),
        _observation(
            "compare equal after alignment",
            lambda: arithmetic.compare(Decimal("1.50"), Decimal("1.5")),
        ),
        _observation(
            "compare unequal",
            lambda: arithmetic.compare(Decimal("1.50"), Decimal("1.51")),
        ),
    )


@contextlib.contextmanager
def _ambient_context(context: decimal.Context) -> Iterator[None]:
    """Install `context` process-wide, and put the caller's back afterwards.

    `decimal.localcontext` is deliberately NOT used: it is the very mechanism under
    test, so borrowing it here would make the test agree with the layer by
    construction. `setcontext` with an explicit restore reproduces what a hostile
    caller actually does - it replaces the thread's context outright.

    The restore is in a `finally`, so a failing assertion inside the block cannot
    leave the reduced precision installed for the rest of the session.

    Args:
        context: The context to install.

    Yields:
        Nothing; the block runs with `context` current.
    """
    previous = decimal.getcontext()
    decimal.setcontext(context.copy())
    try:
        yield
    finally:
        decimal.setcontext(previous)


@pytest.mark.parametrize(
    ("label", "hostile"),
    _HOSTILE_CONTEXTS,
    ids=[label for label, _ in _HOSTILE_CONTEXTS],
)
def test_every_layer_call_is_byte_identical_under_a_hostile_ambient_context(
    label: str, hostile: decimal.Context
) -> None:
    """The layer's answers do not move when the caller's context does (R-2).

    Every public entry point and every receiver storage class, driven once under
    whatever context this session is running in and again under `label`. The two runs
    must agree on the SIGN, the DIGIT TUPLE, the EXPONENT and the CARRIER of every
    result - and on which exception is raised where one is - not merely on numeric
    value.

    This is the property that makes a posted figure reproducible: two processes
    running the same scenario must write the same bytes, and one of them cannot be
    allowed to differ because it happened to import a library that narrowed the
    ambient precision. Section 0.8.5's determinism criterion depends on it.
    """
    baseline = _layer_observations()

    with _ambient_context(hostile):
        under_hostile = _layer_observations()

    # Every label distinct, so a call quietly dropped from the table cannot hide
    # behind a shorter comparison, and the two runs the same length. The COVERAGE of
    # the table - that it reaches all twelve entry points - is asserted separately by
    # `test_the_hostile_context_table_reaches_every_public_entry_point`, which is a
    # statement about the layer's surface rather than about a count.
    labels = tuple(label for label, _, _ in baseline)
    assert len(labels) == len(set(labels)), labels
    assert len(under_hostile) == len(baseline)
    assert under_hostile == baseline, [
        (b, h) for b, h in zip(baseline, under_hostile, strict=True) if b != h
    ]

    # No result silently became a NaN, which is the failure mode of the context that
    # traps nothing: a NaN would compare unequal above, but only if the tuples were
    # reached - and a NaN's `as_tuple()` exponent is the string "n", so it is named
    # here explicitly rather than left to inference.
    assert all(
        payload[2] != "n"
        for _, carrier, payload in under_hostile
        if carrier == "Decimal"
    )


@pytest.mark.parametrize(
    ("label", "hostile"),
    _HOSTILE_CONTEXTS,
    ids=[label for label, _ in _HOSTILE_CONTEXTS],
)
def test_each_hostile_context_really_is_hostile(
    label: str, hostile: decimal.Context
) -> None:
    """The detector detects: each context above genuinely corrupts naive arithmetic.

    A test that pins a context which turns out to be harmless proves nothing, and the
    sibling test above would pass just as happily against `decimal.Context()`. So each
    context is required to change - or refuse - the SAME expression when it is written
    the naive way, outside the layer.

    The expression is `1234.56 + 1234.56`, whose exact answer needs SIX significant
    digits - more than the widest context above carries - so every one of them is too
    narrow for it. Three return a shortened figure, each in its own rounding
    direction, and the all-trapped one raises `Inexact` outright. Both outcomes count
    as hostile; agreement with 2469.12 does not.
    """
    exact = Decimal("2469.12")

    with _ambient_context(hostile):
        try:
            naive = Decimal("1234.56") + Decimal("1234.56")
        except decimal.DecimalException:
            naive = None

    # Either it refused, or it answered - but it must not have answered correctly,
    # because a context that computes this correctly is not narrow enough to detect a
    # leak in the layer.
    assert naive is None or naive != exact, (label, naive)


def test_the_layer_leaves_the_callers_context_exactly_as_it_found_it() -> None:
    """`localcontext` is entered and exited, so the caller's context is not collateral.

    The complement of the two tests above. Those establish that the caller cannot
    change the layer; this one establishes that the layer does not change the caller -
    neither its precision and rounding, nor, less obviously, its accumulated signal
    FLAGS. A layer that truncated inside the caller's context would raise `Inexact`
    and `Rounded` in the caller's flags, and an application that inspects those flags
    to decide whether ITS OWN computation was exact would then be misled by a
    completely unrelated ledger posting.
    """
    caller = decimal.Context(prec=5, rounding=decimal.ROUND_UP)
    caller.clear_flags()

    previous = decimal.getcontext()
    decimal.setcontext(caller)
    try:
        current = decimal.getcontext()
        flags_before = dict(current.flags)

        _layer_observations()

        assert current.prec == 5
        assert current.rounding == decimal.ROUND_UP
        assert dict(current.flags) == flags_before
        # Specifically: the truncating stores above are inexact by design, and not one
        # of them reported that fact into the caller's flags.
        assert current.flags[decimal.Inexact] is False
        assert current.flags[decimal.Rounded] is False
        assert decimal.getcontext() is current
    finally:
        decimal.setcontext(previous)


# The twelve public callables of `acas_posting.cobol.arithmetic`, named so that the
# table above is measured against the layer's surface rather than against a count. Any
# verb added to the layer later fails the test below until it is exercised under a
# hostile context too, which is the point of writing the set down.
_LAYER_ENTRY_POINTS_COVERED: Final[frozenset[str]] = frozenset(
    {
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
    }
)


def test_the_hostile_context_table_reaches_every_public_entry_point() -> None:
    """No verb of the arithmetic layer escapes the ambient-context check.

    Derived from `arithmetic.__all__` rather than from a hand-kept list, so the day a
    thirteenth verb is exported this fails and the table above has to grow with it.
    The upper-case exports are excluded because they are the layer's constants and its
    exception class, not entry points: `INTERMEDIATE_CONTEXT`,
    `INTERMEDIATE_PRECISION`, `ROUNDED_STORE`, `ROUNDING_DIRECTIONS` and
    `SizeErrorNoStore`.
    """
    exported_callables = frozenset(
        name
        for name in arithmetic.__all__
        if not name[0].isupper() and callable(getattr(arithmetic, name))
    )
    assert exported_callables == _LAYER_ENTRY_POINTS_COVERED

    # And each of the twelve is actually named by the driven table, matched on the
    # first word of the label so the mapping is legible in a failure message.
    driven = tuple(label for label, _, _ in _layer_observations())
    for entry_point in sorted(_LAYER_ENTRY_POINTS_COVERED):
        assert any(
            label == entry_point or label.startswith(entry_point + " ")
            for label in driven
        ), (entry_point, driven)


# The migration's own layers whose modules must be re-executed, not reused, to observe
# a constant they fold at import time. Third-party names are deliberately absent: a C
# extension does not need re-importing to be measured, and repeatedly evicting one is
# needless risk.
_MIGRATION_LAYER_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
)


@contextlib.contextmanager
def _freshly_imported(dotted_name: str) -> Iterator[types.ModuleType]:
    """Import `dotted_name` so that its top-level code RUNS inside the block.

    Distinct from `_shipped_module` above in ONE respect only: this one evicts the
    migration's whole lower stack first, not just what its own import added, because the
    two constants this section measures are folded once at import and a module carried
    over from any earlier import would answer with THAT import's context and the test
    would be vacuous. Neither loader memoises, and neither skips.

    On the way out, every tier-isolated name the import added is removed, so rule R-1's
    guards - which read LIVE `sys.modules` in two later files - are unaffected.

    Args:
        dotted_name: The importable name.

    Yields:
        The freshly executed module.

    Raises:
        ImportError: The module could not be imported. DELIBERATELY not turned into a
            skip: `pytest.importorskip` stood here and reported a shipped module that
            cannot be imported at all as a PASS. `mysql-connector-python==26.7.0` is a
            HARD `[project.dependencies]` entry and a hard `requirements.txt` pin, so
            an installed package always has it and its absence is a broken environment
            rather than a supported configuration. The assertions this loader serves
            are anomaly locks rule R-4 requires, and a lock that can disappear into a
            skip line is not a lock.
    """
    for name in sorted(
        (
            name
            for name in sys.modules
            if any(
                name == prefix or name.startswith(f"{prefix}.")
                for prefix in _MIGRATION_LAYER_PREFIXES
            )
        ),
        reverse=True,
    ):
        del sys.modules[name]

    before = frozenset(sys.modules)
    assert dotted_name not in sys.modules, (
        f"{dotted_name} survived the eviction above, so its top-level code will NOT "
        f"re-execute and the folded constants this section measures would be read from "
        f"an earlier import's context."
    )
    completed = False
    try:
        module = importlib.import_module(dotted_name)
        assert sys.modules.get(dotted_name) is module, (
            f"{dotted_name} did not become resident under its own name, so its "
            f"top-level code cannot be shown to have run in this block."
        )
        yield module
        completed = True
    finally:
        added = set(sys.modules) - before
        for name in sorted(added, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name
            for name in set(sys.modules) - before
            if _is_tier_isolated_name(name)
        )
        if completed:
            assert not residue, (
                f"importing {dotted_name} left {residue} resident after the purge, so "
                f"this tier no longer runs without a database driver."
            )


def _bridge_renderer_observations() -> tuple[tuple[str, str, object], ...]:
    """Measure the two bridge-side sites that fold or render exact decimals.

    Both are outside `acas_posting.cobol`, so the section above does not reach them,
    and both were MEASURED to answer to the ambient context before being corrected:

    * `acas_posting/dal/acas029_otm5.py` rendered ``WS-MYSQL-EDIT``
      [common/otm5MT.cbl:L227] with `quantize`, unary minus and `*` in the ambient
      context. At an ambient precision of nine digits `mysql_edit` RAISED
      `decimal.InvalidOperation` instead of rendering a ``decimal(9,2)`` column, and
      its two derived constants drifted (``1000000000`` became ``1.000E+9``).
    * `acas_posting/dal/acas012_sales.py` folded `SPACE_FILLED_RECORD` at import with
      `scaleb`, a constant whose own docstring promises two processes agree on it byte
      for byte.

    Returns:
        The observations, in a fixed order, reduced to context-free data by
            `_observation`.
    """
    with _freshly_imported("acas_posting.dal.acas029_otm5") as otm5:
        rendered: tuple[tuple[str, str, object], ...] = (
            _observation(
                "otm5 edit fraction quantum", lambda m=otm5: m._EDIT_FRACTION_QUANTUM
            ),
            _observation(
                "otm5 edit ten power", lambda m=otm5: m._EDIT_TEN_POWER_FRACTION
            ),
            _observation("otm5 edit context prec", lambda m=otm5: m._EDIT_CONTEXT.prec),
            _observation(
                "otm5 render integer", lambda m=otm5: m.render_integer_column(1234567)
            ),
            _observation(
                "otm5 render tinyint", lambda m=otm5: m.render_tinyint_column(99999999)
            ),
        )
        for money in ("1234.56", "-99.99", "0", "999999999.99", "-0.01"):
            rendered += (
                _observation(
                    f"otm5 mysql_edit {money}",
                    lambda v=money, m=otm5: m.mysql_edit(Decimal(v)),
                ),
                _observation(
                    f"otm5 render money {money}",
                    lambda v=money, m=otm5: m.render_money_column(Decimal(v)),
                ),
            )

    with _freshly_imported("acas_posting.dal.acas012_sales") as sales:
        space_filled = tuple(
            _observation(
                f"sales space-filled {column}",
                lambda c=column, m=sales: m.SPACE_FILLED_RECORD[c],
            )
            for column in sorted(sales.SPACE_FILLED_RECORD)
        )
        # The table is all thirty-seven columns of `SALEDGER-REC`, and eight of them are
        # the scaled ones the `scaleb` fold produces - so the measurement is not
        # dominated by character columns that no context could have touched.
        assert len(space_filled) == 37
        scaled = tuple(
            label for label, carrier, _ in space_filled if carrier == "Decimal"
        )
        assert len(scaled) == 8, scaled

    return rendered + space_filled


def test_the_two_bridge_renderers_do_not_answer_to_the_ambient_context() -> None:
    """The same indifference, for the two data-access sites that lacked it (R-2).

    Fifty-two observations - two folded constants, twelve renderings and all
    thirty-seven columns of `SPACE_FILLED_RECORD` - taken once under this session's
    context and again under each of the four hostile contexts, with the module
    RE-EXECUTED every time so an import-time fold is genuinely re-run.

    This is the regression lock for the correction described in
    `_bridge_renderer_observations`. Removing either guard puts a `quantize`, a
    `scaleb`, a `**` or a unary minus back into the caller's context, and this test
    then reports either a drifted constant or the `InvalidOperation` the renderer
    raises instead of rendering.
    """
    baseline = _bridge_renderer_observations()

    labels = tuple(label for label, _, _ in baseline)
    assert len(labels) == len(set(labels)), labels
    # Two folded constants plus the edit context's precision, two integer renderings,
    # ten money renderings, and all thirty-seven columns of `SPACE_FILLED_RECORD`.
    assert len(baseline) == 3 + 2 + 10 + 37
    # Nothing raised under this session's own context, so a `raised` observation below
    # can only be the hostile context leaking into the renderer.
    assert all(carrier != "raised" for _, carrier, _ in baseline), baseline

    for label, hostile in _HOSTILE_CONTEXTS:
        with _ambient_context(hostile):
            under_hostile = _bridge_renderer_observations()
        assert under_hostile == baseline, (
            label,
            [
                (b, h)
                for b, h in zip(baseline, under_hostile, strict=True)
                if b != h
            ][:8],
        )


def test_the_bridge_renderer_measurement_leaves_no_driver_loaded() -> None:
    """Rule R-1 still holds after two fresh data-access imports.

    `_freshly_imported` evicts every tier-isolated name its import added, so by the
    time the two later files that read LIVE `sys.modules` run their guards, nothing
    forbidden is resident.
    """
    before = frozenset(n for n in sys.modules if _is_tier_isolated_name(n))

    with _freshly_imported("acas_posting.dal.acas029_otm5") as otm5:
        assert otm5.__name__ == "acas_posting.dal.acas029_otm5"
        #  DURING, read from live `sys.modules`: the forbidden name really is resident
        #  inside the block. Without this half an import that silently did nothing -
        #  which is what a memoising loader gave - would still satisfy the delta below.
        assert sys.modules.get("acas_posting.dal.acas029_otm5") is otm5
        assert any(
            _is_tier_isolated_name(name) and name not in before
            for name in sys.modules
        ), (
            "the fresh import added no tier-isolated name at all, so it did not "
            "re-execute and there is nothing for the purge to remove."
        )
    assert "acas_posting.dal.acas029_otm5" not in sys.modules, (
        "the handler survived its loader's purge."
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
            if _is_tier_isolated_name(n) and n not in before
        )
    )
    assert leaked == (), leaked
