"""VAT FROM NET: one `ROUNDED` multiply-and-divide that leaves `post-amount` ALONE.

File 8 of 14 in `tests/arithmetic/`. It locks the `Net section.` of the IRS posting
program - `[irs/irs030.cbl:L1544-L1554]` - and its GL twin, the `net.` paragraph of
`[general/gl051.cbl:L788-L791]`. Both are a single statement, and the whole point of
this file is what that statement does NOT do.

THE FROZEN SECTION, VERBATIM, exactly as `irs/irs030.cbl` carries it (retrieved from
the checkout, line numbers included so a reader can go and look):

    1544:  Net section.
    1545: *>----------
    1546: *>
    1547: *> Calculate vat from net  - THIS MAY NEED A TEST FOR ONLY NON ZERO VAT RATES
    1548: *>                           before compute but look like comes to zero ?
    1549: *>
    1550:  *>     compute  vat-amount rounded =  post-amount *  vat  /  100.
    1551:      compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.
    1552: *>
    1553:  Main-Exita.
    1554:      exit.

THE POST-CONDITION THIS FILE EXISTS TO PROVE: `post-amount` IS COMPLETELY UNCHANGED.
`Main-Exita.` at L1553 follows the compute at L1551 immediately; there is no second
statement, and in particular there is nothing that reduces `post-amount`. The VAT-
from-gross path is the opposite: `Gross section.` at `[irs/irs030.cbl:L1556]` computes
its VAT at L1562-L1563 and then DESTRUCTIVELY reduces the amount at
`[irs/irs030.cbl:L1564]` with `subtract vat-amount from post-amount.` - which is why
that path, and that statement, belong to the sibling file
`tests/arithmetic/test_irs_vat_from_gross.py` and are locked there, not here. The GL
pair has the same asymmetry in the same shape: `[general/gl051.cbl:L791]` has no
subtraction, `[general/gl051.cbl:L797]` has one. The asymmetry is a property of the
NET-versus-GROSS distinction, not of the IRS module.

A CITATION CORRECTION, recorded so nobody re-derives it. Agent Action Plan section
0.4.1.2 calls the destructive statement "the net-of-VAT subtraction
`[irs/irs030.cbl:L1565]`". MEASURED against the checkout, L1565 is a `*>` comment
line and the statement is at L1564. The plan's line is off by one; the statement's
OWNER - the `Gross` section, never `Net` - is what the plan gets right and what
matters. The word "subtract" appears in this file only in prose that cites L1564 and
L797; no statement in this file subtracts anything from any amount, and
`test_the_net_sequence_never_writes_post_amount` proves that structurally rather than
by inspection.

WHAT IS ASSERTED, in the order the tests appear:

    1  the five descriptors carry the declarations the frozen copybooks write
    2  the `Net` sequence leaves `post-amount` BYTE-IDENTICAL          <- the purpose
    3  the sequence has no path that could write `post-amount` at all
    4  the expression is quantized EXACTLY ONCE, at the `ROUNDED` store
    5  quantizing per sub-expression instead gives a DIFFERENT penny
    6  `ROUNDED` and un-`ROUNDED` differ, and `ROUNDED` is half AWAY FROM ZERO
    7  a zero VAT rate is not guarded
    8  a zero `post-amount` is not guarded either
    9  a rate too wide for `99v99` silently becomes a zero rate
   10  anomaly A-19 is recorded and deliberately NOT implemented
   11  the GL `net.` paragraph leaves ITS `post-amount` byte-identical too
   12  the IRS and GL receiving fields differ, and the difference is observable
   13  no in-range amount and rate can overflow `vat-amount`
   14  an overflow raises nothing and keeps the low-order digits

THE SIX BINDING RULES, THEIR PROVENANCE, AND HOW THIS FILE HONOURS EACH.

THE SIX BINDING RULES R-1 to R-6 live in Agent Action Plan section 0.7.2, and their
exact wording is retrievable from the requirements via `review_prompt`. Summarised in
this file's own words, each named at the site that honours it:

    R-1  No COBOL at runtime. Section 0.7.2, verbatim: "the compiled oracle exists
         only under `harness/` and is consumed only by `tests/scenarios/*` and
         `tests/determinism/*` as an out-of-process comparison; `tests/arithmetic/*`
         touch neither COBOL nor a database." This file spawns no process, opens no
         connection and imports nothing from the data-access layer under
         acas_posting/dal, nothing from the harness tree, and no driver. Its one
         file-system prerequisite is the generated
         `data_dictionary/acas_posting_dictionary.json`, which the descriptor factory
         reads. It runs on a bare host with no Docker, no MariaDB and no GnuCOBOL.
    R-2  Zero binary floating point. Every value here is `decimal.Decimal` or `int`.
         There is no binary floating-point literal, no approximate comparison, no
         tolerance, no epsilon, and neither numpy nor pandas. Equality is exact.
         The ambient decimal context is never read and never mutated: the semantics
         layer enters its own `INTERMEDIATE_CONTEXT` internally, and this file relies
         on that rather than configuring anything.
    R-3  No new validations, fields or schema changes; no concurrency. THE ZERO VAT
         RATE IS NOT GUARDED HERE BECAUSE IT IS NOT GUARDED THERE. The maintainer put
         his own doubt on the record immediately above the computation, verbatim
         `[irs/irs030.cbl:L1547-L1548]`, quoted at the bullet's own indent so the
         line fits, and otherwise character for character:

         *> Calculate vat from net  - THIS MAY NEED A TEST FOR ONLY NON ZERO VAT RATES
         *>                           before compute but look like comes to zero ?

         He considered the guard and did not add it. R-3 forbids us adding it, so
         tests 7, 8 and 9 assert the unguarded outcome - a zero product, silently -
         with no exception expected, no `pytest.raises`, no skip and no warning.
         Execution is strictly sequential and no parallel-distribution plugin is
         used.
    R-4  Legacy anomalies reproduced, never fixed. Section 0.8.2, verbatim: "There is
         no test suite: compiled COBOL execution is the behavioral specification,
         defects included. A defect reproduced is correct; a defect fixed is a
         failure." Section 0.7.4 C-3 requires "a comment at each reproduction site
         citing the COBOL locator", and every assertion below carries one. The
         corollary governs the test design: a test that asserted CORRECT ACCOUNTING
         rather than OBSERVED BEHAVIOUR would itself be the defect. That is why test
         9 asserts that an over-wide rate becomes zero rather than that it is
         rejected, and why test 14 asserts that an overflow is silent rather than
         that it is reported.
    R-5  Full traceability. Every test names the `[path:Lnnn]` it locks. Every
         descriptor is minted from a dictionary key, never hand-written, and test 1
         asserts each one's `source_locator` against the copybook line it was read
         from. Coverage is evidence, not a gate: this file sets no coverage
         threshold and no minimum.
    R-6  Compiled behavior is the tie-breaker. Section 0.3.2, verbatim: "the
         arithmetic suite captures expected values from the compiled oracle, never
         from reading the COBOL and reasoning about what it should produce."

R-6 AND THE MONETARY CONSTANTS IN THIS FILE - read this before adding another. Every
penny asserted below is EXACTLY DETERMINED by two things and nothing else: exact
decimal arithmetic, and the direction a `ROUNDED` store takes. Neither is a judgement
call. The rate and the amount both carry two declared decimal places, so their
product carries at most four and the divide by 100 is an exponent shift; the widest
in-range case, 9999999.99 at 99.99 per cent, needs 13 significant digits, which is
`digits` of the amount (9) plus `digits` of the rate (4). Test 4 asserts that bound.
Consequences, both of which this file states as assertions rather than as claims:

  * The intermediate precision is NOT load-bearing here. The semantics layer numbers
    that question Q-2 and records it MEASURED at 60 digits against GnuCOBOL 3.2.0
    `[acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION]`. Since 13 is far below 60 - and would be
    far below any plausible answer - no assertion in this file would change if Q-2's
    measured answer changed. There is therefore nothing here to mark `xfail` against
    Q-2, and marking one would be worse than useless: the assertion passes, so a
    strict `xfail` would turn a correct result into a reported failure.
  * `ROUNDED` means half AWAY FROM ZERO, which test 6 asserts on both signs so the
    direction cannot be quietly changed to half-to-even or to a floor.

THE Q- REGISTER FOR THIS FILE. `Q-` ids in this codebase are per-module registers,
and the id shape the generated dictionary validates is `Q-<n>`
(`model.AMBIGUITY_REF_PATTERN`). This file registers two, and states its scope each
time it names one:

    Q-1  (THIS FILE'S register) What the compiled program stores when a
         `COMPUTE ... ROUNDED` with no `ON SIZE ERROR` produces a result wider than
         `vat-amount`'s nine declared digits `[copybooks/irswspost.cob:L18]`. NOT
         arbitrated - and test 13 proves the question is unreachable from in-range
         data, because the widest in-range VAT (9998999.99) fits the field. Test 14
         therefore asserts only what does not depend on the answer: that nothing is
         raised, that what is stored is inside the field's declared domain, that the
         low-order digits are the ones kept, and that the discarded part is a whole
         multiple of the field's capacity. No monetary constant is asserted for it.
    Q-2  (the semantics layer's register, `[acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION]`)
         The default arithmetic precision, one of the five oracle-arbitration
         questions in Agent Action Plan section 0.6.8. MEASURED at 60. Shown above,
         and asserted in test 4, not to be load-bearing here.

ANOMALY A-19, RECORDED AND NOT IMPLEMENTED. `[irs/irs030.cbl:L1550]` carries a
superseded, commented-out variant of the live compute, verbatim:

     *>     compute  vat-amount rounded =  post-amount *  vat  /  100.

It references a differently named rate field, `vat`, where the live statement at
L1551 references `WS-Vat-Current`. The dead line is preserved here as a string
constant that nothing evaluates, so that a reader comparing the COBOL against the
Python does not conclude a variant was lost. Test 10 asserts that this file
implements exactly ONE variant of the formula. The `Gross` path has its own
superseded variant at `[irs/irs030.cbl:L1561]`, recorded in the sibling file.

WHAT THIS FILE NEEDS TO RUN: `data_dictionary/acas_posting_dictionary.json`, and
nothing else. Run it from the repository root.
"""

from __future__ import annotations

import contextlib
import importlib
import dataclasses
import decimal
import dis
import sys
import types
from collections.abc import Iterator
from decimal import Decimal
from typing import Final

import pytest

from acas_posting.cobol import arithmetic, field as cobol_field, usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  SECTION 1  -  DEFENSIVE DICTIONARY-KEY RESOLUTION
#
#  Every descriptor in this file is minted from the generated dictionary, because
#  rule R-5 makes the dictionary the only sanctioned source of a frozen field's
#  picture, scale, signedness and carrier - and because
#  `FieldDescriptor.for_working_storage`, which earlier drafts of this suite were
#  written against, NO LONGER EXISTS: `acas_posting/cobol/field.py _require_dictionary_provenance`
#  records its removal, leaving `from_dictionary_key` as the one door.
#
#  The keys are exact and case-sensitive. A near miss - `IRSPOSTING-REC.VAT-AMOUNT`
#  for `IRSPOSTING-REC.VAT-AMOUNT4`, say - raises `loader.DictionaryKeyError`, and a
#  bare `KeyError` traceback three frames inside a factory is a poor way to learn
#  that a key was mistyped. So each lookup states the COBOL field name it expects as
#  well as the key, and on a miss the fallback below asks the table for its entries
#  and reports which key actually carries that field.
#
#  This is a TEST-AUTHORING aid and NOT a validation of the kind rule R-3 forbids:
#  it can only fire on a key this file spells, never on an accounting value.
# ---------------------------------------------------------------------------


class _UnresolvedFieldKey(KeyError):
    """A dictionary key this file names does not resolve, with the near misses named.

    A `KeyError` subclass so that it reads as what it is - a lookup that found
    nothing - and so that it cannot be confused with an assertion failure. It carries
    the table's real key for the field wherever the fallback can find one.
    """


def _resolved(key: str, *, table: str, cobol_name: str) -> cobol_field.FieldDescriptor:
    """Return the descriptor for `key`, or fail with the key that would have worked.

    Args:
        key: The qualified dictionary key, `<TABLE-NAME>.<COLUMN-NAME>`.
        table: The table the field belongs to, used only for the fallback search.
        cobol_name: The field name the frozen copybook declares, verbatim with its
            own casing - `"Post-Amount"`, `"Vat-Amount"`, `"Vat-Rate-1"`. Checked
            against the resolved entry so that a key which resolves to the WRONG
            field is caught as loudly as one that resolves to nothing.

    Returns:
        The descriptor the generated dictionary holds for that field.

    Raises:
        _UnresolvedFieldKey: Neither the key nor the table's own entries name that
            field.
    """
    try:
        descriptor = cobol_field.FieldDescriptor.from_dictionary_key(key)
    except loader.DictionaryKeyError:
        # The fallback: ask the table for its entries and find the one whose copybook
        # field name is the one this file means. `entries_for_table` yields them in
        # the frozen schema's column ordinal order and is the accessor the loader
        # publishes for exactly this purpose.
        candidates = tuple(
            entry
            for entry in loader.entries_for_table(table)
            if entry.copybook is not None and entry.copybook.name == cobol_name
        )
        if len(candidates) != 1:
            near = tuple(
                entry.key
                for entry in loader.entries_for_table(table)
                if entry.copybook is not None
                and cobol_name.split("-")[0].lower() in entry.key.lower()
            )
            raise _UnresolvedFieldKey(
                f"{key!r} names no entry, and {table!r} has "
                f"{len(candidates)} entries whose copybook field is "
                f"{cobol_name!r}; nearest keys: {near}"
            ) from None
        descriptor = cobol_field.FieldDescriptor.from_dictionary_key(
            candidates[0].key
        )

    if descriptor.name != cobol_name:
        raise _UnresolvedFieldKey(
            f"{key!r} resolves to the field {descriptor.name!r}, not the "
            f"{cobol_name!r} this file means"
        )
    return descriptor


# ---------------------------------------------------------------------------
#  SECTION 2  -  THE FIVE FIELDS
#
#  Three for the IRS statement at [irs/irs030.cbl:L1551] and two for the GL
#  statement at [general/gl051.cbl:L791]. Each carries its dictionary key, and test 1
#  asserts each one's `source_locator` against the copybook line it came from.
#
#  The five are left unannotated on purpose. `Final[FieldDescriptor]` would read
#  better and is what the program modules write, but it needs `typing.Final`, and the
#  import surface this tier is allowed is exactly `pytest`, `decimal`, three
#  `acas_posting.cobol` modules and two `acas_posting.dictionary` ones. Keeping to it
#  literally is worth more here than an annotation, and the SCREAMING_SNAKE names say
#  the same thing to a reader.
# ---------------------------------------------------------------------------

#: `03  Post-Amount     pic s9(7)v99  sign is leading.`
#: [copybooks/irswspost.cob:L14] - the amount the `Net` section reads and NEVER
#: writes. Zoned DISPLAY, nine digits, scale two, sign overpunched on the LEADING
#: digit.
_IRS_POST_AMOUNT = _resolved(
    "IRSPOSTING-REC.POST4-AMOUNT",
    table="IRSPOSTING-REC",
    cobol_name="Post-Amount",
)

#: `03  Vat-Amount      pic s9(7)v99   sign is leading.`
#: [copybooks/irswspost.cob:L18] - THE LOCATOR IS L18. L19 is a `*>` line, and the
#: Agent Action Plan's L19 citation points at that comment rather than at the
#: declaration. This is the ONLY field the `Net` section writes.
_IRS_VAT_AMOUNT = _resolved(
    "IRSPOSTING-REC.VAT-AMOUNT4",
    table="IRSPOSTING-REC",
    cobol_name="Vat-Amount",
)

#: `07 Vat-Rate-1   pic 99v99.` [copybooks/wssystem.cob:L56], under the group header
#: `05  Vat-Rates                    comp.` [copybooks/wssystem.cob:L55] from which
#: it INHERITS its COMP usage, and reachable by subscript through
#: `05  Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5.`
#: [copybooks/wssystem.cob:L61].
#:
#: This is the catalogued shape of the rate the statement multiplies by. The
#: statement itself names `WS-Vat-Current`, a program-local working-storage item
#: declared `03  WS-Vat-Current  pic 99v99       value zero.`
#: [irs/irs030.cbl:L277], which the program loads from `WS-Vat-Rate (n)`
#: [irs/irs030.cbl:L721], itself loaded from the IRS system record's percentages
#: [irs/irs030.cbl:L1472]. Same picture, same scale, same unsigned two-and-two
#: shape - so the catalogued field is the right descriptor for the rate's storage,
#: and it is the one the Agent Action Plan's own agent brief names.
_VAT_RATE = _resolved(
    "SYSTEM-REC.VAT-RATE-1",
    table="SYSTEM-REC",
    cobol_name="Vat-Rate-1",
)

#: `03  Post-Amount     pic s9(8)v99.  *> 46` [copybooks/wspost.cob:L23] - the GL
#: posting record's amount. TEN digits and a TRAILING sign, where the IRS field has
#: nine and a leading one.
_GL_POST_AMOUNT = _resolved(
    "GLPOSTING-REC.POST-AMOUNT",
    table="GLPOSTING-REC",
    cobol_name="Post-Amount",
)

#: `03  Vat-Amount      pic s9(8)v99.  *> 96` [copybooks/wspost.cob:L28] - the GL
#: posting record's VAT. The two GL locators the Agent Action Plan section 0.4.6
#: lists, L23 and L28, are in ascending line order and NOT in the order the sentence
#: names the fields: MEASURED against the checkout, L23 is `Post-Amount` and L28 is
#: `Vat-Amount`.
_GL_VAT_AMOUNT = _resolved(
    "GLPOSTING-REC.VAT-AMOUNT",
    table="GLPOSTING-REC",
    cobol_name="Vat-Amount",
)


# ---------------------------------------------------------------------------
#  SECTION 3  -  THE STATEMENT, TRANSCRIBED
#
#  There is deliberately NO `vat` helper, NO `percentage` helper and NO
#  `round_to_pence` helper in `acas_posting.cobol.arithmetic`, so the formula is
#  spelled out here exactly as the COBOL spells it. Two spellings appear below: the
#  faithful one, and a deliberately WRONG one that quantizes per sub-expression,
#  which exists only so that test 5 can show the difference is observable.
# ---------------------------------------------------------------------------

#: ANOMALY A-19 [irs/irs030.cbl:L1550] - the superseded, commented-out variant that
#: survives adjacent to the live statement, carried here verbatim so the record is
#: complete. NOTHING EVALUATES IT. It references a differently named rate field,
#: `vat`, where the live statement at L1551 references `WS-Vat-Current`; the `Gross`
#: path has its own dead variant at [irs/irs030.cbl:L1561], recorded in
#: `tests/arithmetic/test_irs_vat_from_gross.py`. Reproducing a dead line would be
#: implementing a variant the compiled program does not run, which is not what R-4
#: asks for: R-4 asks that the LIVE behaviour, defects included, be reproduced and
#: that the oddity be recorded. This constant is the record.
_A19_DEAD_VARIANT = (
    " *>     compute  vat-amount rounded =  post-amount *  vat  /  100."
)

#: The anomaly id, checked against the generated dictionary's own reference shape in
#: test 10 so that a typo in the register cannot pass unnoticed.
_A19_REF = "A-19"

#: This file's two ambiguity ids, in the shape the dictionary validates. See the
#: module docstring for what each question is and why neither is load-bearing.
_Q_UNSIZED_OVERFLOW = "Q-1"
_Q_INTERMEDIATE_PRECISION = "Q-2"


def _irs_net_vat(
    post_amount: Decimal,
    rate: Decimal,
    vat_field: cobol_field.FieldDescriptor,
    *,
    rounded: bool = True,
) -> Decimal | int:
    """`compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.`

    The whole of `Net` [irs/irs030.cbl:L1544-L1551], and the whole of the GL twin
    [general/gl051.cbl:L791], which differs only in the name of the rate item
    (`ws-vat-rate`) and in the receiving field. ONE statement, ONE store.

    NOTE WHAT IS ABSENT, because it is the point of this file: there is no second
    statement, and `post_amount` arrives as a VALUE, not as a field to be written.
    This function takes exactly one `FieldDescriptor`, the receiving VAT field, so
    there is no descriptor here that a store could target the amount through.
    `test_the_net_sequence_never_writes_post_amount` asserts that structurally.

    THE FORMULA IS NO LONGER WRITTEN HERE. This function used to evaluate
    `post_amount * rate / 100` itself, over the production primitive but as its own
    expression, which made this file a SECOND SOURCE for the statement it is about:
    nineteen assertions consumed it, and every one was checking a copy of the compute
    against the reasoning that produced the copy. If the shipped section were ever
    changed - the operand order altered, the `ROUNDED` dropped, the divisor moved - not
    one of them would have noticed.

    It now calls `_net_section` in `acas_posting/programs/irs030_posting.py`, which is
    the migration of `Net section.` [irs/irs030.cbl:L1544-L1551], and returns what that
    section stored. The nineteen call sites are unchanged and their fixed expectations
    became the independent side of the comparison rather than the only side.

    THE `rounded=False` PATH IS THE ONE EXCEPTION, and it is marked as such rather than
    hidden: no shipped code computes this expression un-`ROUNDED`, because the statement
    is written `ROUNDED` and there is nothing to drive. That path therefore still
    evaluates the expression directly, and it exists for exactly one caller - the test
    that computes the same inputs both ways to prove the direction is observable. It is
    a CONTRAST, not a claim about the migration, and it is the only place in this file
    where a formula is written test-side.

    THE TWIN IS DRIVEN TOO, BY THE RECEIVING FIELD. This file's subject is that the
    same statement appears twice in the frozen system with DIFFERENT receiving fields -
    the IRS `Vat-Amount pic s9(7)v99` [copybooks/irswspost.cob:L18] and the General
    Ledger `Vat-Amount pic s9(8)v99` [copybooks/wspost.cob:L28] - so several assertions
    ask for the GL field on purpose. Each field is answered by ITS OWN shipped section:
    the IRS one by `irs030_posting._net_section` and the GL one by
    `gl051_batch_control_check._net`, which is [general/gl051.cbl:L791]. A field that is
    neither is refused rather than answered from the wrong module.

    Args:
        post_amount: What `post-amount` holds, as the field holds it.
        rate: What the rate item holds, as the field holds it.
        vat_field: The receiving VAT field - the IRS `Vat-Amount`
            [copybooks/irswspost.cob:L18] or the GL one [copybooks/wspost.cob:L28].
        rounded: True, because the statement is written `ROUNDED`. Exposed as a
            parameter for one reason only: test 6 computes the same inputs both ways
            to prove the direction is observable. Nothing in the frozen program
            computes this expression un-`ROUNDED`.

    Returns:
        What the VAT field holds after the single store.
    """
    if not rounded:
        #  The CONTRAST path - see the docstring. No shipped code to drive.
        return arithmetic.compute(
            lambda: post_amount * rate / 100, vat_field, rounded=False
        )

    with _shipped_irs030_posting() as irs030:
        if vat_field == irs030._VAT_AMOUNT:
            record = irs030.PostingRecord()
            record.post_amount = post_amount
            irs030._net_section(record, rate)
            return record.vat_amount

    with _shipped_module(_GL051_MODULE) as gl051:
        if vat_field == gl051._VAT_AMOUNT:
            #  `_net` [general/gl051.cbl:L791] writes `vat-amount` on the GL posting
            #  record. Same one-statement shape, different receiving picture, which is
            #  the divergence several assertions in this file exist to show.
            posting = gl051.WsPostingRecord()
            posting.post_amount = post_amount
            gl051._net(posting, rate)
            return posting.vat_amount

    raise AssertionError(
        f"this helper answers for the two receiving fields the frozen system actually "
        f"uses - the IRS `Vat-Amount` [copybooks/irswspost.cob:L18] and the General "
        f"Ledger one [copybooks/wspost.cob:L28] - each from its own shipped section. It "
        f"was asked for {vat_field!r}, which is neither, and answering it from either "
        f"module would report a store into a field that module does not make."
    )


def _net_vat_quantized_per_sub_expression(
    post_amount: Decimal,
    rate: Decimal,
    vat_field: cobol_field.FieldDescriptor,
    *,
    rounded: bool = True,
) -> Decimal | int:
    """The SAME formula, wrongly quantized at every step. NOT what COBOL does.

    Written in the operator order the statement writes - multiply, then divide - so
    that the only difference from `_irs_net_vat` is WHERE the quantize happens: here
    the product is stored into the receiving field first, and the quotient is stored
    into it again. COBOL truncates or rounds when it STORES, and a `COMPUTE` stores
    once, at the end.

    This exists solely as the contrast in test 5. No program module calls anything
    shaped like it.
    """
    product = arithmetic.multiply_by_giving(
        post_amount, rate, vat_field, rounded=rounded
    )
    return arithmetic.divide_by_giving(product, 100, vat_field, rounded=rounded)


def _encoded(value: Decimal | int, descriptor: cobol_field.FieldDescriptor) -> bytes:
    """Lay a value out as the bytes a field of this description would hold.

    The third and strictest of the three ways this file compares an amount before and
    after the computation. A `Decimal` can compare equal while carrying a different
    scale, and `as_tuple()` catches that; the bytes catch anything either of them
    would miss, including the sign's placement - which for the IRS field is an
    overpunch on the LEADING digit [copybooks/irswspost.cob:L14] and for the GL field
    is on the trailing one [copybooks/wspost.cob:L23].
    """
    return cobol_usage.encode(
        value,
        usage=descriptor.usage,
        digits=descriptor.digits,
        scale=descriptor.scale,
        character_length=descriptor.character_length,
        signed=descriptor.signed,
        unsigned=descriptor.unsigned,
        sign_position=descriptor.sign_position,
    )


def _significant_digits(value: Decimal) -> int:
    """How many significant digits an exact decimal carries.

    Used by test 4 to show that the widest expression this statement can evaluate
    stays far inside the semantics layer's intermediate precision, which is why
    question Q-2's measured answer is not load-bearing here.
    """
    return len(value.as_tuple().digits)


def _units(value: Decimal, descriptor: cobol_field.FieldDescriptor) -> int:
    """Express a value as whole units of a field's least significant digit.

    `FieldDescriptor.value_domain` states a field's bounds in units of its last digit
    - hundredths of a pound for these amounts - so a comparison against those bounds
    has to speak the same way. Scaling runs through `arithmetic.intermediate`, at the
    semantics layer's own precision, rather than through the ambient decimal context,
    which rule R-2 says is never to be read or reconfigured from here.
    """
    scale = descriptor.scale or 0
    scaled = arithmetic.intermediate(lambda: value * 10**scale)
    # A value at the field's own scale has no fraction left after the shift; asserting
    # it here means the callers below cannot silently compare a rounded-off integer.
    assert scaled == scaled.to_integral_value(
        rounding=arithmetic.ROUNDING_DIRECTIONS[False]
    )
    return int(scaled)


# ---------------------------------------------------------------------------
#  SECTION 4  -  THE ASSERTIONS
#
#  Numbers used below, and why each is the number it is:
#
#    100.00 at 20.00 per cent -> 20.0000 exactly. No rounding direction and no
#        intermediate precision can touch it; it is the shape case.
#     12.15 at 17.50 per cent -> 2.12625. Rounds to 2.13 and truncates to 2.12, so
#        it separates the two store directions by a penny.
#      1.50 at 17.00 per cent -> 0.2550 exactly - an EXACT half penny, which is the
#        only kind of value that can tell half-away-from-zero from half-to-even.
#     10.03 at 19.99 per cent -> 2.004997. Quantized once it is 2.00; quantized per
#        sub-expression it is 2.01. That penny is test 5.
#  9999999.99 at 99.99 per cent -> 9998999.990001, the widest in-range case, needing
#        13 significant digits and still fitting the nine-digit field.
# 12345678.90 is DELIBERATELY too wide for the IRS amount field and not for the GL
#        one, which is how test 12 makes the digit difference observable.
# 50000000.00 at 20.00 per cent -> 10000000.0000, one digit too wide for the IRS VAT
#        field, which is how test 14 reaches the silent-overflow path.
# ---------------------------------------------------------------------------


def test_the_five_descriptors_carry_the_declarations_the_copybooks_write() -> None:
    """Rule R-5: every field is traced to the frozen line that declares it.

    Locks [copybooks/irswspost.cob:L14], [copybooks/irswspost.cob:L18],
    [copybooks/wssystem.cob:L55-L56], [copybooks/wspost.cob:L23] and
    [copybooks/wspost.cob:L28]. If any of these five drifts, every penny below is
    computed against the wrong storage and the failure should say so here first.
    """
    # `03  Post-Amount     pic s9(7)v99  sign is leading.`
    assert _IRS_POST_AMOUNT.dictionary_key == "IRSPOSTING-REC.POST4-AMOUNT"
    assert _IRS_POST_AMOUNT.source_locator == "copybooks/irswspost.cob:L14"
    assert _IRS_POST_AMOUNT.picture == "s9(7)v99"
    assert _IRS_POST_AMOUNT.usage is model.Usage.DISPLAY
    assert _IRS_POST_AMOUNT.signed is True
    assert _IRS_POST_AMOUNT.sign_position is model.SignPosition.LEADING_INCLUDED
    assert _IRS_POST_AMOUNT.sign_clause_text == "sign is leading"
    assert (_IRS_POST_AMOUNT.digits, _IRS_POST_AMOUNT.integer_digits) == (9, 7)
    assert _IRS_POST_AMOUNT.scale == 2
    assert _IRS_POST_AMOUNT.byte_length == 9
    assert _IRS_POST_AMOUNT.python_storage is model.CobolPythonStorage.DECIMAL

    # `03  Vat-Amount      pic s9(7)v99   sign is leading.` - L18, NOT L19.
    assert _IRS_VAT_AMOUNT.dictionary_key == "IRSPOSTING-REC.VAT-AMOUNT4"
    assert _IRS_VAT_AMOUNT.source_locator == "copybooks/irswspost.cob:L18"
    # The receiving field has the SAME shape as the amount it is derived from, which
    # is what lets a VAT figure be as wide as the amount itself without overflowing.
    assert _IRS_VAT_AMOUNT.picture == _IRS_POST_AMOUNT.picture
    assert _IRS_VAT_AMOUNT.usage is _IRS_POST_AMOUNT.usage
    assert _IRS_VAT_AMOUNT.sign_position is _IRS_POST_AMOUNT.sign_position
    assert _IRS_VAT_AMOUNT.digits == _IRS_POST_AMOUNT.digits
    assert _IRS_VAT_AMOUNT.scale == _IRS_POST_AMOUNT.scale
    assert _IRS_VAT_AMOUNT.value_domain == _IRS_POST_AMOUNT.value_domain

    # `07 Vat-Rate-1   pic 99v99.` inheriting COMP from `05  Vat-Rates   comp.`
    assert _VAT_RATE.dictionary_key == "SYSTEM-REC.VAT-RATE-1"
    assert _VAT_RATE.source_locator == "copybooks/wssystem.cob:L56"
    assert _VAT_RATE.picture == "99v99"
    assert _VAT_RATE.usage is model.Usage.COMP
    # The USAGE is not on the item; it is inherited from the group header at
    # [copybooks/wssystem.cob:L55]. Reading the item alone would make it DISPLAY.
    assert _VAT_RATE.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert _VAT_RATE.usage_inherited_from == "Vat-Rates"
    assert (_VAT_RATE.digits, _VAT_RATE.integer_digits, _VAT_RATE.scale) == (4, 2, 2)
    assert _VAT_RATE.signed is False
    # A rate is a percentage held to two places: 0.00 through 99.99 and nothing else.
    assert _VAT_RATE.value_domain == (0, 9999)

    # `03  Post-Amount     pic s9(8)v99.` and `03  Vat-Amount      pic s9(8)v99.`
    assert _GL_POST_AMOUNT.dictionary_key == "GLPOSTING-REC.POST-AMOUNT"
    assert _GL_POST_AMOUNT.source_locator == "copybooks/wspost.cob:L23"
    assert _GL_VAT_AMOUNT.dictionary_key == "GLPOSTING-REC.VAT-AMOUNT"
    assert _GL_VAT_AMOUNT.source_locator == "copybooks/wspost.cob:L28"
    for gl_field in (_GL_POST_AMOUNT, _GL_VAT_AMOUNT):
        assert gl_field.picture == "s9(8)v99"
        assert gl_field.usage is model.Usage.DISPLAY
        assert gl_field.signed is True
        # No SIGN clause, so the sign overpunches the TRAILING digit by COBOL default.
        assert gl_field.sign_clause_text is None
        assert gl_field.sign_position is model.SignPosition.TRAILING_INCLUDED
        assert (gl_field.digits, gl_field.integer_digits, gl_field.scale) == (10, 8, 2)
        assert gl_field.byte_length == 10

    # Rule R-5 again: each descriptor can say where it came from, in one line, and the
    # citation names the dictionary key that vouches for it.
    for descriptor in (
        _IRS_POST_AMOUNT,
        _IRS_VAT_AMOUNT,
        _VAT_RATE,
        _GL_POST_AMOUNT,
        _GL_VAT_AMOUNT,
    ):
        citation = descriptor.cite()
        assert descriptor.dictionary_key is not None
        assert descriptor.dictionary_key in citation
        assert str(descriptor.source_locator) in citation


@pytest.mark.parametrize(
    ("amount", "rate"),
    [
        # 20.0000 exactly - no rounding involved at all.
        (Decimal("100.00"), Decimal("20.00")),
        # 2.12625 - a rounding case, to prove the amount survives a rounded store.
        (Decimal("12.15"), Decimal("17.50")),
        # The same, negative: the sign lives in the amount's LEADING digit
        # [copybooks/irswspost.cob:L14], so a negative case is the one that would
        # expose an accidental re-encoding.
        (Decimal("-12.15"), Decimal("17.50")),
        # 0.2550 - an exact half penny.
        (Decimal("1.50"), Decimal("17.00")),
        # The widest in-range pair the two fields admit.
        (Decimal("9999999.99"), Decimal("99.99")),
        # A zero rate, which the frozen program does not guard - see test 7.
        (Decimal("250.00"), Decimal("0.00")),
    ],
)
def test_net_leaves_post_amount_byte_identical(
    amount: Decimal, rate: Decimal
) -> None:
    """THE PURPOSE OF THIS FILE. `Net` writes VAT and NOTHING ELSE.

    Reproduces [irs/irs030.cbl:L1544-L1551]: `Net section.` is one `compute`, and
    `Main-Exita.` at L1553 follows it immediately. THERE IS NO SUBTRACT IN `Net`. The
    VAT-from-gross path is the one that reduces the amount, at
    [irs/irs030.cbl:L1564], and that statement is locked by the sibling file
    `tests/arithmetic/test_irs_vat_from_gross.py`; it must never appear here.

    The amount is compared three ways - value, `as_tuple()` and encoded bytes - so
    that a change of scale, of sign placement or of representation would all fail,
    not just a change of magnitude.
    """
    post_amount = arithmetic.store(amount, _IRS_POST_AMOUNT)
    current_rate = arithmetic.store(rate, _VAT_RATE)
    # What the record holds before the statement runs. `Net` does not clear it, so the
    # zero is the record's own starting state rather than anything the section does.
    vat_before = arithmetic.store(Decimal("0.00"), _IRS_VAT_AMOUNT)

    # The amount is scaled - two declared decimal places - so its carrier is
    # `decimal.Decimal` and never `int`. The dictionary says so and the store honours
    # it, which is what makes the byte comparison below meaningful.
    assert isinstance(post_amount, Decimal)
    assert isinstance(current_rate, Decimal)

    before_value = post_amount
    before_tuple = post_amount.as_tuple()
    before_bytes = _encoded(post_amount, _IRS_POST_AMOUNT)

    vat_amount = _irs_net_vat(post_amount, current_rate, _IRS_VAT_AMOUNT)

    # 1551 compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.
    # 1553 Main-Exita.  <- nothing between them, so nothing else can have changed.
    assert post_amount == before_value
    assert post_amount.as_tuple() == before_tuple
    assert _encoded(post_amount, _IRS_POST_AMOUNT) == before_bytes
    # `Decimal` is immutable, so the object the caller still holds must be the object
    # it held before: the sequence rebinds nothing and hands back only the VAT.
    assert post_amount is before_value
    # And the amount still reads back as the amount the test put in.
    assert post_amount == arithmetic.store(amount, _IRS_POST_AMOUNT)

    # The VAT field is the one that took the store, and it holds exactly what a single
    # `ROUNDED` store of the expression puts there. Stated this way rather than as "the
    # VAT changed" because one pair here has a zero rate, whose VAT is the zero the
    # field already held - which is itself the behaviour test 7 locks.
    assert vat_before == Decimal("0.00")
    assert vat_amount == arithmetic.store(
        arithmetic.intermediate(lambda: post_amount * current_rate / 100),
        _IRS_VAT_AMOUNT,
        rounded=True,
    )
    # There is nothing else to have changed. The statement has exactly two observables
    # - the VAT it stores and the amount it reads - and
    # `test_the_net_sequence_never_writes_post_amount` proves no third one is
    # reachable from the transcription at all.


def test_the_net_sequence_never_writes_post_amount() -> None:
    """No code path in the SHIPPED `Net` section can reach `post-amount`.

    ASSERTED ABOUT THE SHIPPED SECTION, NOT ABOUT A HELPER IN THIS FILE. It used to
    inspect `_irs_net_vat.__code__`, which was this file's own transcription of the
    statement - so it proved that the TRANSCRIPTION had no path to the amount and said
    nothing at all about the migration. `_irs_net_vat` now drives
    `irs030_posting._net_section`, so the claim is made where it belongs: the global
    names the SHIPPED section's body references, and the stores its bytecode performs.

    Reproduces the absence at [irs/irs030.cbl:L1551-L1553]. The statement the `Gross`
    section adds at [irs/irs030.cbl:L1564] uses a SUBTRACT verb; no subtract verb is
    reachable from `Net`.
    """
    with _shipped_irs030_posting() as irs030:
        code = irs030._net_section.__code__

        # The section calls ONE arithmetic verb and no other. `compute` stores once, at
        # the end, which is the whole of [irs/irs030.cbl:L1551].
        assert "compute" in code.co_names
        for subtract_verb in ("subtract_from", "subtract_giving"):
            assert subtract_verb not in code.co_names, (
                f"the shipped `Net` section references {subtract_verb!r}; "
                f"[irs/irs030.cbl:L1544-L1551] has no SUBTRACT and the one at "
                f"[irs/irs030.cbl:L1564] belongs to `Gross`"
            )
            # Named in the module's public surface, so a typo here would go unnoticed.
            assert subtract_verb in arithmetic.__all__

        # AND IT WRITES ONLY `vat-amount`. `_stores_performed_by` walks the section's
        # bytecode and every code object nested in it - the `compute` lambda is one -
        # so a store into `post_amount` anywhere inside would appear here.
        stored = {attribute for _, attribute in _stores_performed_by(irs030._net_section)}
        assert "post_amount" not in stored, (
            f"the shipped `Net` section stores into {sorted(stored)}; "
            f"[irs/irs030.cbl:L1544-L1551] leaves `post-amount` alone and only `Gross` "
            f"[irs/irs030.cbl:L1564-L1565] writes it back"
        )

        # Annotations are strings here because of `from __future__ import
        # annotations`, which is why this reads as a name test.
        annotations = dict(irs030._net_section.__annotations__)
        annotations.pop("return", None)

        # NO `FieldDescriptor` REACHES THE SECTION AT ALL, which is a stronger form of
        # the old claim than the transcription could make. The receiving field is the
        # module's own `_VAT_AMOUNT` constant, so a caller cannot redirect the store by
        # passing a different descriptor - there is no parameter to pass one through.
        descriptor_parameters = tuple(
            name
            for name, annotation in annotations.items()
            if "FieldDescriptor" in annotation
        )
        assert descriptor_parameters == (), (
            f"the shipped `Net` section takes {descriptor_parameters} as descriptors; "
            f"it should take none and use its own `_VAT_AMOUNT`, so that the receiving "
            f"field is fixed by the module rather than chosen by a caller"
        )

        # And the parameter list is the section's linkage, in the statement's own
        # left-to-right order: the record that carries `post-amount`, then the rate.
        parameter_names = code.co_varnames[: code.co_argcount + code.co_kwonlyargcount]
        assert parameter_names == ("posting_record", "ws_vat_current"), (
            f"the shipped `Net` section's parameters are {parameter_names}; "
            f"[irs/irs030.cbl:L1544-L1551] reads `post-amount` off the posting record "
            f"and `WS-Vat-Current` from working storage, and nothing else"
        )


def test_net_quantizes_exactly_once_at_the_rounded_store() -> None:
    """One store, at the end, at intermediate precision until then.

    Reproduces [irs/irs030.cbl:L1551]. A COBOL `COMPUTE` evaluates its expression and
    stores once; it does not truncate or round at each operator. The store is written
    `ROUNDED`, one of the five such sites in the whole migrated cycle - the other four
    being [general/gl080.cbl:L328], [general/gl051.cbl:L791],
    [general/gl051.cbl:L796] and [irs/irs030.cbl:L1562].

    This test also settles question Q-2 for this file. Q-2 - the default arithmetic
    precision, one of the five oracle-arbitration questions of Agent Action Plan
    section 0.6.8 - is recorded MEASURED at 60 digits against GnuCOBOL 3.2.0
    [acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION]. The assertions below show that the widest
    expression this statement can evaluate needs 13 significant digits, so no penny in
    this file depends on Q-2's answer and nothing here is marked `xfail` against it.
    """
    # The semantics layer's own vocabulary, asserted so that `rounded=True` cannot
    # come to mean something else. COBOL ROUNDED is half AWAY FROM ZERO.
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDING_DIRECTIONS[True] == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDING_DIRECTIONS[False] == decimal.ROUND_DOWN
    assert arithmetic.INTERMEDIATE_PRECISION >= 60
    assert arithmetic.INTERMEDIATE_CONTEXT.prec == arithmetic.INTERMEDIATE_PRECISION

    post_amount = arithmetic.store(Decimal("12.15"), _IRS_POST_AMOUNT)
    current_rate = arithmetic.store(Decimal("17.50"), _VAT_RATE)

    # The expression, evaluated with NO receiving field: 12.15 * 17.50 / 100.
    exact = arithmetic.intermediate(lambda: post_amount * current_rate / 100)
    assert exact == Decimal("2.12625")
    # Unquantized - five decimal places, not two. The store is what scales it.
    assert exact.as_tuple().exponent == -5

    stored = _irs_net_vat(post_amount, current_rate, _IRS_VAT_AMOUNT)
    # 2.12625 rounded half away from zero at two places. Exactly determined by the
    # exact product above and the direction asserted at the top of this test.
    assert stored == Decimal("2.13")
    # Scaled TO THE RECEIVING FIELD, not left at intermediate scale.
    assert isinstance(stored, Decimal)
    assert stored.as_tuple().exponent == -2
    assert _IRS_VAT_AMOUNT.quantum == Decimal("0.01")

    # The single store is the ONLY quantize: computing the expression at intermediate
    # precision and then storing it once by hand gives the identical answer.
    assert stored == arithmetic.store(exact, _IRS_VAT_AMOUNT, rounded=True)

    # Q-2 is not load-bearing here. The amount carries nine declared digits and the
    # rate four, so the product carries at most thirteen, and dividing by 100 shifts
    # the exponent without adding a digit.
    widest = arithmetic.intermediate(
        lambda: Decimal("9999999.99") * Decimal("99.99") / 100
    )
    assert widest == Decimal("9998999.990001")
    assert _IRS_POST_AMOUNT.digits is not None and _VAT_RATE.digits is not None
    assert _significant_digits(widest) == _IRS_POST_AMOUNT.digits + _VAT_RATE.digits
    assert _significant_digits(widest) < arithmetic.INTERMEDIATE_PRECISION
    # So the widest case is exact before the store, and the store is the only place
    # precision is lost.
    assert arithmetic.store(widest, _IRS_VAT_AMOUNT, rounded=True) == Decimal(
        "9998999.99"
    )
    assert _Q_INTERMEDIATE_PRECISION == "Q-2"


def test_quantizing_per_sub_expression_gives_a_different_penny() -> None:
    """"Quantize once" is not a stylistic preference; it is worth a penny.

    Reproduces [irs/irs030.cbl:L1551] against a plausible mis-transcription of it. An
    implementation that stored the product into `vat-amount` and then divided that
    stored value by 100 - two stores, in the statement's own operator order - would
    disagree with the compiled program on 10.03 at 19.99 per cent.

    Both answers below are exactly determined: 10.03 * 19.99 = 200.4997, whose
    quotient by 100 is 2.004997 and rounds to 2.00, while the product itself rounds to
    200.50, whose quotient 2.0050 rounds half away from zero to 2.01.
    """
    post_amount = arithmetic.store(Decimal("10.03"), _IRS_POST_AMOUNT)
    current_rate = arithmetic.store(Decimal("19.99"), _VAT_RATE)

    faithful = _irs_net_vat(post_amount, current_rate, _IRS_VAT_AMOUNT)
    per_step = _net_vat_quantized_per_sub_expression(
        post_amount, current_rate, _IRS_VAT_AMOUNT
    )

    assert arithmetic.intermediate(
        lambda: post_amount * current_rate / 100
    ) == Decimal("2.004997")
    assert faithful == Decimal("2.00")
    assert per_step == Decimal("2.01")
    assert faithful != per_step
    # The divergence is a whole penny of the receiving field's own quantum, not a
    # representational difference.
    assert (
        arithmetic.intermediate(lambda: per_step - faithful)
        == _IRS_VAT_AMOUNT.quantum
    )

    # The intermediate product is where the two part company: stored, it is 200.50.
    assert arithmetic.multiply_by_giving(
        post_amount, current_rate, _IRS_VAT_AMOUNT, rounded=True
    ) == Decimal("200.50")
    assert arithmetic.intermediate(
        lambda: post_amount * current_rate
    ) == Decimal("200.4997")


@pytest.mark.parametrize(
    ("amount", "expected_rounded", "expected_truncated"),
    [
        # 0.2550 exactly - an exact half penny, positive.
        (Decimal("1.50"), Decimal("0.26"), Decimal("0.25")),
        # And negative. Half AWAY FROM ZERO takes this DOWN to -0.26; a floor, or
        # half-to-even, or Python's own round would not.
        (Decimal("-1.50"), Decimal("-0.26"), Decimal("-0.25")),
    ],
)
def test_rounded_and_truncated_stores_differ_and_rounded_is_away_from_zero(
    amount: Decimal, expected_rounded: Decimal, expected_truncated: Decimal
) -> None:
    """The statement is written `ROUNDED`, and the word changes the answer.

    Reproduces [irs/irs030.cbl:L1551], where `rounded` is written, against the default
    every other store in the cycle takes. Agent Action Plan section 0.6.1: exactly
    five `ROUNDED` sites exist in the whole in-scope cycle and every other store
    truncates toward zero, so the default and the exception must be separable by test.

    Both expected values are exactly determined: 1.50 * 17.00 / 100 is 0.2550 with no
    remainder, so the only question is which way an exact half goes, and COBOL takes
    it away from zero.
    """
    post_amount = arithmetic.store(amount, _IRS_POST_AMOUNT)
    current_rate = arithmetic.store(Decimal("17.00"), _VAT_RATE)
    assert isinstance(post_amount, Decimal)

    exact = arithmetic.intermediate(lambda: post_amount * current_rate / 100)
    # An EXACT half penny: the third decimal place is a five and there is nothing
    # after it. Only such a value can tell the two directions apart.
    assert exact.copy_abs() == Decimal("0.2550")

    rounded_store = _irs_net_vat(post_amount, current_rate, _IRS_VAT_AMOUNT)
    truncating_store = _irs_net_vat(
        post_amount, current_rate, _IRS_VAT_AMOUNT, rounded=False
    )
    assert isinstance(rounded_store, Decimal)
    assert isinstance(truncating_store, Decimal)

    assert rounded_store == expected_rounded
    assert truncating_store == expected_truncated
    assert rounded_store != truncating_store
    # Away from zero, in both directions: the magnitude grows, the sign is kept.
    assert rounded_store.copy_abs() > truncating_store.copy_abs()
    assert rounded_store.as_tuple().sign == post_amount.as_tuple().sign

    # And the amount is untouched either way - the `ROUNDED` keyword governs the
    # store, not what the statement reads.
    assert post_amount == arithmetic.store(amount, _IRS_POST_AMOUNT)


def test_a_zero_vat_rate_is_not_guarded() -> None:
    """The maintainer considered a guard and did not add one. Neither may we.

    His doubt is on the record immediately above the computation, verbatim
    `[irs/irs030.cbl:L1547-L1548]`:

        *> Calculate vat from net  - THIS MAY NEED A TEST FOR ONLY NON ZERO VAT RATES
        *>                           before compute but look like comes to zero ?

    He wrote "THIS MAY NEED A TEST", answered his own question with "look like comes
    to zero ?", and left the compute at L1551 unguarded. Rule R-3 forbids adding a
    validation the frozen program does not have, so this test asserts the unguarded
    outcome as it stands: a zero rate yields a zero VAT, quietly. THERE IS NO
    `pytest.raises` HERE, NO SKIP AND NO WARNING, and adding any of the three would be
    the "defect fixed" that rule R-4 counts as a failure.
    """
    post_amount = arithmetic.store(Decimal("250.00"), _IRS_POST_AMOUNT)
    zero_rate = arithmetic.store(Decimal("0.00"), _VAT_RATE)

    # `Vat-Rate-1 pic 99v99` is unsigned [copybooks/wssystem.cob:L56], so zero is a
    # perfectly ordinary value in its domain rather than an edge of it.
    assert zero_rate == Decimal("0.00")
    assert _VAT_RATE.min_value == 0

    before_bytes = _encoded(post_amount, _IRS_POST_AMOUNT)
    vat_amount = _irs_net_vat(post_amount, zero_rate, _IRS_VAT_AMOUNT)

    # Zero VAT, at the receiving field's own scale, and no complaint of any kind.
    assert isinstance(vat_amount, Decimal)
    assert vat_amount == Decimal("0.00")
    assert vat_amount.as_tuple().exponent == -2
    # The amount is still every penny of the 250.00 that went in: `Net` has no
    # subtraction, so a zero rate leaves a gross-looking amount and no VAT.
    assert post_amount == Decimal("250.00")
    assert _encoded(post_amount, _IRS_POST_AMOUNT) == before_bytes
    # The same reading through a COBOL relation condition, which compares
    # algebraically after aligning the decimal points.
    assert arithmetic.compare(vat_amount, 0) == 0


def test_a_zero_post_amount_with_a_non_zero_rate_is_not_guarded_either() -> None:
    """The other half of the unguarded case: nothing times something is nothing.

    Reproduces [irs/irs030.cbl:L1551] with a zero amount. The frozen statement does
    not test the amount any more than it tests the rate, and rule R-3 forbids us
    adding either test. A zero-amount posting therefore produces a zero-VAT posting
    and no diagnostic.
    """
    post_amount = arithmetic.store(Decimal("0.00"), _IRS_POST_AMOUNT)
    current_rate = arithmetic.store(Decimal("20.00"), _VAT_RATE)
    assert isinstance(post_amount, Decimal)

    vat_amount = _irs_net_vat(post_amount, current_rate, _IRS_VAT_AMOUNT)

    assert isinstance(vat_amount, Decimal)
    assert vat_amount == Decimal("0.00")
    assert vat_amount.as_tuple().exponent == -2
    assert post_amount == Decimal("0.00")
    assert post_amount.as_tuple() == Decimal("0.00").as_tuple()
    # Sign of zero: a zoned field with a leading overpunch stores a positive zero, and
    # the encoded bytes say so.
    assert _encoded(post_amount, _IRS_POST_AMOUNT) == _encoded(
        Decimal("0.00"), _IRS_POST_AMOUNT
    )


@pytest.mark.parametrize("offered_rate", [Decimal("100.00"), Decimal("200.00")])
def test_a_rate_too_wide_for_the_field_silently_becomes_a_zero_rate(
    offered_rate: Decimal,
) -> None:
    """`pic 99v99` holds four digits, and a fifth is discarded without a word.

    Reproduces the store semantics of [copybooks/wssystem.cob:L56] - and, through it,
    of the program-local `03  WS-Vat-Current  pic 99v99       value zero.`
    [irs/irs030.cbl:L277] that the statement actually reads. A rate of 100.00 per cent
    needs five digits; the field has four, so the high-order digit is dropped and what
    remains is 00.00.

    This is why the maintainer's note at [irs/irs030.cbl:L1547-L1548] matters more
    than it looks: a zero rate is not only an input the program does not check, it is
    also an outcome the storage itself can manufacture. Rule R-3 forbids a guard and
    rule R-4 forbids a fix, so the assertion below records the behaviour rather than
    objecting to it.
    """
    stored_rate = arithmetic.store(offered_rate, _VAT_RATE)

    # Four declared digits, so the domain stops at 99.99.
    assert _VAT_RATE.digits == 4
    assert _VAT_RATE.max_value == 9999
    # And the high-order digit of the offered rate is simply gone.
    assert stored_rate == Decimal("0.00")

    post_amount = arithmetic.store(Decimal("250.00"), _IRS_POST_AMOUNT)
    vat_amount = _irs_net_vat(post_amount, stored_rate, _IRS_VAT_AMOUNT)

    assert vat_amount == Decimal("0.00")
    assert post_amount == Decimal("250.00")


def test_anomaly_a19_is_recorded_and_not_implemented() -> None:
    """A-19: a superseded variant survives next to the live statement.

    `[irs/irs030.cbl:L1550]`, verbatim, is a commented-out copy of the compute that
    references a differently named rate field, `vat`, where the live statement at
    L1551 references `WS-Vat-Current`. The `Gross` path carries its own dead variant
    at `[irs/irs030.cbl:L1561]`, recorded in
    `tests/arithmetic/test_irs_vat_from_gross.py`.

    IT IS NOT IMPLEMENTED HERE AND MUST NOT BE. Rule R-4 asks for the compiled
    behaviour to be reproduced and the oddity to be recorded; a dead line is not
    behaviour. This test asserts that the record exists, that its id is well formed in
    the vocabulary the generated dictionary validates, and that this file implements
    exactly ONE variant of the formula.
    """
    # The dead line, carried verbatim, as documentation and nothing else.
    assert _A19_DEAD_VARIANT == (
        " *>     compute  vat-amount rounded =  post-amount *  vat  /  100."
    )
    # It IS a comment in the frozen source - the `*>` marker is what makes it dead.
    assert _A19_DEAD_VARIANT.lstrip().startswith("*>")
    # It names `vat`, the superseded rate field, and NOT the live `WS-Vat-Current`.
    assert " vat  / " in _A19_DEAD_VARIANT
    assert "WS-Vat-Current" not in _A19_DEAD_VARIANT

    # The anomaly id is in the register's own shape, `A-1` through `A-22`, which the
    # generated dictionary enforces on every reference it carries.
    assert _A19_REF == "A-19"
    assert model.ANOMALY_REF_PATTERN.fullmatch(_A19_REF) is not None
    # And this file's two ambiguity ids are in theirs.
    for ambiguity_ref in (_Q_UNSIZED_OVERFLOW, _Q_INTERMEDIATE_PRECISION):
        assert model.AMBIGUITY_REF_PATTERN.fullmatch(ambiguity_ref) is not None

    # ONE variant is implemented: the live statement. Asserted about the SHIPPED
    # section rather than about a helper in this file, for the reason
    # `test_the_net_sequence_never_writes_post_amount` gives - the superseded variant
    # would have to be implemented in the MIGRATION to matter, and that is where it is
    # now shown not to be.
    with _shipped_irs030_posting() as irs030:
        assert "compute" in irs030._net_section.__code__.co_names
        # The live statement's rate reaches the section as a PARAMETER, which is how the
        # dead line's `vat` and the live line's `WS-Vat-Current` stay distinguishable:
        # the shipped section hard-codes neither field name.
        assert "ws_vat_current" in irs030._net_section.__code__.co_varnames
        # And exactly one store, into the VAT field. A second implemented variant would
        # need a second store or a branch, and there is neither.
        stores = _stores_performed_by(irs030._net_section)
        assert [attribute for _, attribute in stores] == ["vat_amount"], (
            f"the shipped `Net` section performs {stores}; A-19 is that the superseded "
            f"variant [irs/irs030.cbl:L1550] is a COMMENT, so the migration must "
            f"implement exactly one formula with exactly one store"
        )


def test_the_gl_net_paragraph_also_leaves_post_amount_byte_identical() -> None:
    """`general/gl051.cbl` has the same pair, and the same asymmetry.

    Verbatim, the two paragraphs:

        788:  net.
        791:      compute  vat-amount rounded = post-amount * ws-vat-rate / 100.
        793:  gross.
        796:      compute  vat-amount rounded = post-amount - (post-amount / ((ws-vat-rate + 100) / 100)).
        797:      subtract vat-amount  from  post-amount.

    THE GL `net.` PARAGRAPH HAS NO SUBTRACTION EITHER. The destructive statement is at
    L797 and belongs to `gross.` alone, exactly as [irs/irs030.cbl:L1564] belongs to
    `Gross` alone. The asymmetry is a property of the net-versus-gross distinction and
    not of the IRS module, which is what this test exists to establish.

    Scope note, so the citation is not misread: gl051's own migrated surface is the
    control-total gate at [general/gl051.cbl:L1096-L1134] - `batch-print` and its
    `end-batch` paragraph - and these two VAT paragraphs sit in the out-of-scope
    interactive amendment path. What is asserted here is the shared formula and the
    GL receiving fields' storage, per Agent Action Plan section 0.4.6.

    The rate is `03  ws-vat-rate         pic 99v99  comp   value zero.`
    [general/gl051.cbl:L183], loaded from the system record's rate table at
    [general/gl051.cbl:L522] - the same picture, usage and scale as the catalogued
    `SYSTEM-REC.VAT-RATE-1`, which is the descriptor used here.
    """
    post_amount = arithmetic.store(Decimal("12.15"), _GL_POST_AMOUNT)
    current_rate = arithmetic.store(Decimal("17.50"), _VAT_RATE)
    assert isinstance(post_amount, Decimal)

    before_value = post_amount
    before_tuple = post_amount.as_tuple()
    before_bytes = _encoded(post_amount, _GL_POST_AMOUNT)
    # Ten bytes, and the sign overpunches the TRAILING digit here.
    assert len(before_bytes) == 10

    vat_amount = _irs_net_vat(post_amount, current_rate, _GL_VAT_AMOUNT)

    # 791 compute vat-amount rounded = post-amount * ws-vat-rate / 100.
    # 12.15 * 17.50 / 100 is 2.12625, rounded half away from zero to 2.13.
    assert isinstance(vat_amount, Decimal)
    assert vat_amount == Decimal("2.13")
    assert vat_amount.as_tuple().exponent == -2

    # And the amount is byte-identical, the same three ways as the IRS case.
    assert post_amount == before_value
    assert post_amount.as_tuple() == before_tuple
    assert _encoded(post_amount, _GL_POST_AMOUNT) == before_bytes
    assert post_amount is before_value

    # The negative case, because the GL sign sits in a different byte from the IRS
    # one and an accidental re-encode would show up there.
    negative_amount = arithmetic.store(Decimal("-12.15"), _GL_POST_AMOUNT)
    negative_bytes = _encoded(negative_amount, _GL_POST_AMOUNT)
    assert negative_bytes != before_bytes
    assert _irs_net_vat(negative_amount, current_rate, _GL_VAT_AMOUNT) == Decimal(
        "-2.13"
    )
    assert _encoded(negative_amount, _GL_POST_AMOUNT) == negative_bytes


def test_the_irs_and_gl_receiving_fields_differ_observably() -> None:
    """Same formula, different receiving fields: nine digits, or ten.

    Agent Action Plan section 0.4.6 asks for this explicitly, because the same net
    formula can quantize to different results in the two modules. The IRS pair is
    `pic s9(7)v99 sign is leading` [copybooks/irswspost.cob:L14],
    [copybooks/irswspost.cob:L18]; the GL pair is `pic s9(8)v99` with the default
    trailing sign [copybooks/wspost.cob:L23], [copybooks/wspost.cob:L28].

    Two things are asserted. For any value both fields can hold, the two modules agree
    to the penny - so the formula is genuinely the same formula. For a value only the
    wider GL field can hold, they do not - so the digit difference is not decorative.
    """
    # The descriptors differ in exactly the ways that matter to a store.
    assert _IRS_POST_AMOUNT.digits == 9
    assert _GL_POST_AMOUNT.digits == 10
    assert _IRS_VAT_AMOUNT.digits != _GL_VAT_AMOUNT.digits
    assert _IRS_POST_AMOUNT.sign_position is model.SignPosition.LEADING_INCLUDED
    assert _GL_POST_AMOUNT.sign_position is model.SignPosition.TRAILING_INCLUDED
    assert _IRS_POST_AMOUNT.byte_length + 1 == _GL_POST_AMOUNT.byte_length
    # The scale is the one thing they share, which is why the two agree in range.
    assert _IRS_VAT_AMOUNT.scale == _GL_VAT_AMOUNT.scale == 2
    assert _IRS_VAT_AMOUNT.quantum == _GL_VAT_AMOUNT.quantum

    current_rate = arithmetic.store(Decimal("17.50"), _VAT_RATE)

    # IN RANGE FOR BOTH: identical to the penny. 12.15 and the widest amount the
    # narrower field admits.
    for shared_amount in (Decimal("12.15"), Decimal("9999999.99")):
        irs_amount = arithmetic.store(shared_amount, _IRS_POST_AMOUNT)
        gl_amount = arithmetic.store(shared_amount, _GL_POST_AMOUNT)
        assert irs_amount == gl_amount == shared_amount
        irs_vat = _irs_net_vat(irs_amount, current_rate, _IRS_VAT_AMOUNT)
        gl_vat = _irs_net_vat(gl_amount, current_rate, _GL_VAT_AMOUNT)
        assert irs_vat == gl_vat
        # The same reading through a COBOL relation condition.
        assert arithmetic.compare(irs_vat, gl_vat) == 0

    # TOO WIDE FOR THE IRS FIELD: 12345678.90 needs eight integer digits and the IRS
    # amount declares seven, so its leading digit is discarded on the store -
    # silently, per rule R-3 - while the GL amount, which declares eight, keeps it.
    # The VAT then differs by the whole of the discarded ten million.
    wide_amount = Decimal("12345678.90")
    irs_amount = arithmetic.store(wide_amount, _IRS_POST_AMOUNT)
    gl_amount = arithmetic.store(wide_amount, _GL_POST_AMOUNT)
    assert irs_amount == Decimal("2345678.90")
    assert gl_amount == wide_amount
    assert irs_amount != gl_amount

    irs_vat = _irs_net_vat(irs_amount, current_rate, _IRS_VAT_AMOUNT)
    gl_vat = _irs_net_vat(gl_amount, current_rate, _GL_VAT_AMOUNT)
    # 2345678.90 * 17.50 / 100 is 410493.8075, rounded to 410493.81.
    assert irs_vat == Decimal("410493.81")
    # 12345678.90 * 17.50 / 100 is 2160493.8075, rounded to 2160493.81.
    assert gl_vat == Decimal("2160493.81")
    assert irs_vat != gl_vat
    # The gap is 17.50 per cent of the ten million the IRS store dropped, exactly.
    assert arithmetic.intermediate(lambda: gl_vat - irs_vat) == Decimal(
        "1750000.00"
    )


def test_no_in_range_amount_and_rate_can_overflow_vat_amount() -> None:
    """The overflow question is unreachable from data the frozen fields can hold.

    Reproduces the arithmetic of [irs/irs030.cbl:L1551] against the declared domains
    of its three fields. The amount holds at most 9999999.99
    [copybooks/irswspost.cob:L14], the rate at most 99.99
    [copybooks/wssystem.cob:L56], and the receiving VAT field holds as much as the
    amount does [copybooks/irswspost.cob:L18]. Because a percentage of a number is
    smaller than the number whenever the rate is below one hundred - and the rate
    field cannot reach one hundred, as test 9 shows - the product can never need a
    tenth digit.

    THIS IS WHY THIS FILE ASSERTS NO CAPTURED CONSTANT FOR QUESTION Q-1, the
    un-arbitrated question of what the compiled program stores when a `COMPUTE`
    without `ON SIZE ERROR` overflows. The question cannot arise from valid data, so
    there is nothing for the oracle to arbitrate on the posting path. The proof comes
    twice: first as integer arithmetic on the declared domains alone, with no store and
    no rounding in it at all, and then through the statement itself at both extremes of
    the amount's range.
    """
    assert _IRS_POST_AMOUNT.scale == _VAT_RATE.scale == _IRS_VAT_AMOUNT.scale == 2

    # Both operands are held as whole units of their last digit: the amount in
    # hundredths of a pound, the rate in hundredths of a per cent.
    widest_amount_units = _IRS_POST_AMOUNT.max_value
    widest_rate_units = _VAT_RATE.max_value
    assert (widest_amount_units, widest_rate_units) == (999999999, 9999)

    # VAT in hundredths of a pound is amount_units * rate_units / 10 ** 4, and the
    # `ROUNDED` store can add at most half of that last place.
    product_units = widest_amount_units * widest_rate_units
    worst_case_units = (product_units + 5 * 10**3) // 10**4
    assert worst_case_units == 999899999
    assert worst_case_units <= _IRS_VAT_AMOUNT.max_value
    # Symmetrically on the negative side: the amount is signed, the rate is not.
    assert -worst_case_units >= _IRS_VAT_AMOUNT.min_value

    # And the same fact stated through the arithmetic itself rather than through the
    # domains, at the two extremes of the amount's range.
    widest_rate = arithmetic.store(Decimal("99.99"), _VAT_RATE)
    for extreme in (Decimal("9999999.99"), Decimal("-9999999.99")):
        amount = arithmetic.store(extreme, _IRS_POST_AMOUNT)
        vat_amount = _irs_net_vat(amount, widest_rate, _IRS_VAT_AMOUNT)
        assert isinstance(vat_amount, Decimal)
        assert vat_amount.copy_abs() == Decimal("9998999.99")
        # Inside the field, with a digit still to spare.
        assert vat_amount.copy_abs() < Decimal("9999999.99")

    # The register cross-reference, so that a reader who greps for the question id
    # lands on the test that closes it off rather than on the docstring alone.
    assert _Q_UNSIZED_OVERFLOW == "Q-1"


def test_an_overflow_is_silent_and_keeps_the_low_order_digits() -> None:
    """`ON SIZE ERROR` appears nowhere in the cycle, so an overflow is silent.

    Reproduces the store semantics behind [irs/irs030.cbl:L1551]. The statement is
    written `ROUNDED` and NOTHING ELSE - no `ON SIZE ERROR`, no `NOT ON SIZE ERROR` -
    so a result too wide for the receiving field loses its high-order digits and the
    program carries on. Rule R-3 forbids adding the check the frozen statement does
    not have, and rule R-4 forbids treating the silence as a bug.

    CONSTRUCTED, NOT OBSERVED: test 13 proves the posting path cannot reach this case,
    so the operand here is deliberately sourced from the WIDER GL amount field
    [copybooks/wspost.cob:L23], which can hold 50000000.00, and stored into the
    NARROWER IRS VAT field [copybooks/irswspost.cob:L18], which cannot hold its
    ten-million VAT.

    WHAT IS ASSERTED IS ONLY WHAT DOES NOT DEPEND ON QUESTION Q-1 - this file's
    un-arbitrated question of the exact value a compiled un-sized overflow leaves
    behind. Nothing is raised; the result sits inside the receiving field's declared
    domain; the digits kept are the LOW-ORDER ones, in the sense that what was
    discarded is a whole multiple of the field's capacity. No penny is guessed, and
    for the same reason nothing here is marked `xfail`: an `xfail` on an assertion
    this exact would be a passing test reported as a failure.
    """
    wide_amount = arithmetic.store(Decimal("50000000.00"), _GL_POST_AMOUNT)
    current_rate = arithmetic.store(Decimal("20.00"), _VAT_RATE)
    assert isinstance(wide_amount, Decimal)
    # The GL field holds it; the IRS field would not, which is the point of sourcing
    # it from the wider of the two.
    assert wide_amount == Decimal("50000000.00")

    exact = arithmetic.intermediate(lambda: wide_amount * current_rate / 100)
    assert exact == Decimal("10000000.0000")
    # Ten million needs eight integer digits; the IRS VAT field declares seven.
    assert _IRS_VAT_AMOUNT.integer_digits == 7

    # NO `pytest.raises`, because nothing is raised. The call either returns or the
    # test fails on the exception.
    stored = _irs_net_vat(wide_amount, current_rate, _IRS_VAT_AMOUNT)

    assert isinstance(stored, Decimal)
    assert stored.as_tuple().exponent == -2
    exact_units = _units(exact, _IRS_VAT_AMOUNT)
    stored_units = _units(stored, _IRS_VAT_AMOUNT)
    # Inside the declared domain: the store reduced the value rather than clamping it
    # or writing something the field could not hold.
    assert _IRS_VAT_AMOUNT.min_value <= stored_units <= _IRS_VAT_AMOUNT.max_value
    # The low-order digits are the ones kept: what went missing is a whole multiple of
    # the field's nine-digit capacity, so no low-order digit was disturbed.
    assert _IRS_VAT_AMOUNT.digits is not None
    capacity = 10**_IRS_VAT_AMOUNT.digits
    assert (exact_units - stored_units) % capacity == 0
    assert exact_units - stored_units == capacity
    # And the loss is real, not a representational difference.
    assert stored != exact

    # The identical expression into the GL VAT field, which has the tenth digit, keeps
    # the whole of it - so the loss is the FIELD's and not the formula's.
    assert _irs_net_vat(wide_amount, current_rate, _GL_VAT_AMOUNT) == Decimal(
        "10000000.00"
    )
    # The amount is still untouched, overflow or no overflow: `Net` writes VAT only.
    assert wide_amount == Decimal("50000000.00")


# ---------------------------------------------------------------------------
#  SECTION 3  -  THE SHIPPED PARAGRAPH ITSELF
#
#  Everything above proves the POST-CONDITION about a transcription of
#  [irs/irs030.cbl:L1544-L1553] written inside this file. That is necessary and it
#  is not sufficient: a transcription cannot notice a second statement appearing in
#  `acas_posting/programs/irs030_posting.py::_net_section`, which is the code that
#  actually runs a posting. This section closes that gap by driving the SHIPPED
#  paragraph.
#
#  WHY THE IMPORT IS DEFERRED, AND WHAT THAT PRESERVES (rule R-1).
#  Agent Action Plan section 0.4.3 gives this tier `cobol` and `records` to import
#  and forbids `dal` and any database; R-1 states it as "tests/arithmetic/* touch
#  neither COBOL nor a database". `acas_posting.programs.irs030_posting` imports
#  `acas_posting.dal.facade` at module scope, and that pulls the MySQL driver in
#  transitively - so importing it at module scope here would leave
#  `acas_posting.dal.*` and `mysql.*` resident in `sys.modules` and would break the
#  three tier-isolation assertions this suite already carries
#  (`tests/arithmetic/test_comp3_packed_decimal.py test_the_packed_carrier_follows_the_scale_and_is_never_binary`,
#  `tests/arithmetic/test_comp_binary.py test_q3_an_overflowing_negative_store_lands_on_its_magnitudes_byte`,
#  `tests/arithmetic/test_pic_field_descriptors.py test_no_single_winner_view_exists_on_drift_entry_or_descriptor`), two of which read LIVE
#  `sys.modules`.
#
#  So the module is imported INSIDE the test body through
#  `_shipped_irs030_posting()`, which
#    * uses `importlib.import_module`, MANDATORY rather than skippable: an earlier
#      revision used `pytest.importorskip`, and a skip reads as green, so a module
#      that cannot be imported at all turned this section into a pass.
#      `mysql-connector-python==26.7.0` is a HARD `[project.dependencies]` entry and a
#      hard `requirements.txt` pin, so the guarded state cannot arise for an installed
#      package, its absence is a broken environment rather than a configuration, and
#      an anomaly lock that can vanish into a skip line is not a lock (rule R-4);
#    * does NOT memoise it. A cached module is already resident, so the purge below
#      would remove nothing and the isolation claim would be about a module that had
#      never left. Each entry EVICTS every tier-isolated name first, which is what
#      makes the import re-execute, and asserts the name resident while the body runs;
#    * removes, in `finally`, exactly the newly-added `sys.modules` names that match
#      the tier-isolation prefixes, and asserts the residue is empty, so nothing
#      forbidden is left resident and all three assertions keep passing UNCHANGED and
#      unweakened - whatever order the files run in.
#  The pattern is the one `tests/conftest.py _load_harness_module` already uses for the harness
#  modules: load the real thing, keep the forbidden name out of `sys.modules`.
#
#  NO DATABASE IS TOUCHED. `_net_section(posting_record, ws_vat_current)` takes a
#  `PostingRecord` dataclass and a `Decimal`; it opens no connection, reads no
#  socket and needs no MariaDB, no Docker and no GnuCOBOL.
#
#  THE GENERAL LEDGER TWIN STAYS AT THE TRANSCRIPTION LEVEL, deliberately.
#  `general/gl051.cbl`'s `net.` and `gross.` paragraphs [general/gl051.cbl:L788-L797]
#  sit in the out-of-scope interactive amendment path - Agent Action Plan section
#  0.4.1.2 migrates only the control-total gate at [general/gl051.cbl:L1096-L1134] -
#  so `acas_posting/programs/gl051_batch_control_check.py` HAS no net or gross
#  paragraph to drive, and inventing one would be new behaviour (rule R-3).
#  `test_the_gl_net_paragraph_also_leaves_post_amount_byte_identical` above remains
#  the GL lock.
# ---------------------------------------------------------------------------


#: The module-name prefixes the tier's own isolation assertions forbid. Kept in one
#: place so the loader below and the guard test agree by construction.
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


_IRS030_MODULE: Final[str] = "acas_posting.programs.irs030_posting"

#: The module that owns the General Ledger TWIN of the same statement,
#: [general/gl051.cbl:L791]. Named here because `_irs_net_vat` answers for the GL
#: receiving field from this module rather than from the IRS one - the two sections
#: differ only in the rate item's name and in the receiving picture, and reporting a
#: GL store from the IRS section would misattribute the divergence this file exists
#: to show.
_GL051_MODULE: Final[str] = "acas_posting.programs.gl051_batch_control_check"


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under one of the prefixes the tier must not leave loaded?

    Matched as a package prefix - exact name or name plus a dot - so a submodule
    cannot slip past and a same-prefixed unrelated name cannot be caught by accident.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped_module(dotted_name: str) -> Iterator[types.ModuleType]:
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
        AssertionError: The name did not become resident after the eviction, or a
            tier-isolated name survived the purge.
        ImportError: The module could not be imported. NOT converted into a skip:
            `mysql-connector-python==26.7.0` is a HARD `[project.dependencies]`
            entry and a hard `requirements.txt` pin, so an installed package always has
            it, and the assertions this loader serves are anomaly locks rule R-4
            requires - a lock that can disappear into a skip line is not a lock.
    """
    #  EVICT FIRST, so the import below really runs the module's top-level code and the
    #  purge in the `finally` really removes what it added. Nothing is memoised: a
    #  cached module is ALREADY RESIDENT, so the purge would remove nothing and the
    #  isolation claim would be about a module that had never left. Eviction rather than
    #  a "must be absent on the way in" assertion, because this tier's own helpers
    #  legitimately import program modules in function scope to drive the SHIPPED
    #  paragraphs, and an absence assertion would make the two remediations exclude each
    #  other. Reverse-sorted so a package goes after its submodules.
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


def _shipped_irs030_posting() -> contextlib.AbstractContextManager[types.ModuleType]:
    """`acas_posting/programs/irs030_posting.py`, the module that owns `Net`."""
    return _shipped_module(_IRS030_MODULE)


def _stores_performed_by(function: object) -> tuple[tuple[str, str], ...]:
    """Every store this function's bytecode performs, its own and its lambdas'.

    Walks the function's code object and every code object nested inside it - the
    `compute` lambda is one - and reports the attribute and local stores in
    execution order. This is how "the paragraph writes `vat-amount` and nothing
    else" becomes a property of the SHIPPED CODE rather than of the inputs a test
    happened to choose: a second statement cannot be added to the paragraph without
    adding a store, and a store cannot be added without appearing here.

    Args:
        function: A function object.

    Returns:
        A tuple of `(opname, target)` pairs.
    """
    code = function.__code__  # type: ignore[attr-defined]

    def _walk(target: types.CodeType) -> Iterator[types.CodeType]:
        yield target
        for constant in target.co_consts:
            if isinstance(constant, types.CodeType):
                yield from _walk(constant)

    return tuple(
        (instruction.opname, str(instruction.argval))
        for block in _walk(code)
        for instruction in dis.get_instructions(block)
        if instruction.opname in ("STORE_ATTR", "STORE_GLOBAL", "STORE_DEREF")
    )


#: A distinctive value for each of the ten `Posting-Record` fields
#: [copybooks/irswspost.cob:L8-L18], so that "nothing else moved" is asserted over
#: the WHOLE record and not just over the two money items. The strings are declared
#: at their frozen widths - `pic xx`, `pic x(8)`, `pic x(32)` - because a store that
#: re-padded one would be a change this test must catch.
_SENTINEL_RECORD_FIELDS: Final[dict[str, object]] = {
    "post_key": 12345,
    "post_code": "SL",
    "post_date": "21/09/25",
    "post_dr": 54321,
    "post_cr": 11111,
    "post_legend": "sentinel legend, thirty-two wide ."[:32],
    "vat_ac_def": 31,
    "post_vat_side": "DR",
}

#: The same six (amount, rate) pairs `test_net_leaves_post_amount_byte_identical`
#: uses, so the shipped paragraph is exercised over exactly the inputs the
#: transcription is exercised over and the two can be compared pair for pair.
_SHIPPED_NET_CASES: Final[tuple[tuple[Decimal, Decimal], ...]] = (
    (Decimal("100.00"), Decimal("20.00")),
    (Decimal("12.15"), Decimal("17.50")),
    (Decimal("-12.15"), Decimal("17.50")),
    (Decimal("1.50"), Decimal("17.00")),
    (Decimal("9999999.99"), Decimal("99.99")),
    (Decimal("250.00"), Decimal("0.00")),
)


def test_the_shipped_net_paragraph_stores_vat_amount_and_only_vat_amount() -> None:
    """`_net_section` performs EXACTLY ONE store, and its target is `vat_amount`.

    This is the structural half of the post-condition, asserted against the shipped
    bytecode rather than against a transcription. Reproduces the absence at
    [irs/irs030.cbl:L1551-L1553]: one `compute`, then `Main-Exita.`, and nothing in
    between. The destructive statement is [irs/irs030.cbl:L1564] and belongs to
    `Gross` alone.

    Adding a second statement to `Net` - a subtract from `post-amount`, say - cannot
    avoid adding a store, so it cannot avoid failing here. That is the point: the
    assertion is on the code, so it holds for every input and not only for the six
    pairs the sibling test runs.
    """
    with _shipped_irs030_posting() as irs030:
        stores = _stores_performed_by(irs030._net_section)

        assert stores == (("STORE_ATTR", "vat_amount"),)
        # Stated separately as well, because this is the sentence a reader is looking
        # for: no store anywhere in the paragraph targets the amount.
        assert ("STORE_ATTR", "post_amount") not in stores

        # And no subtract verb is reachable from the paragraph at all - not from its
        # own body and not from the `compute` lambda nested inside it.
        reachable_names = {
            name
            for block in (
                irs030._net_section.__code__,
                *(
                    constant
                    for constant in irs030._net_section.__code__.co_consts
                    if isinstance(constant, types.CodeType)
                ),
            )
            for name in block.co_names
        }
        for subtract_verb in ("subtract_from", "subtract_giving"):
            assert subtract_verb not in reachable_names
            # Named in the public surface, so a typo above would go unnoticed.
            assert subtract_verb in arithmetic.__all__

        # The two receiving descriptors the module carries are the very entries this
        # file mints from the generated dictionary (rule R-5), so the numbers below
        # and the numbers above are computed through the same field metadata.
        assert irs030._VAT_AMOUNT == _IRS_VAT_AMOUNT
        assert irs030._POST_AMOUNT == _IRS_POST_AMOUNT


@pytest.mark.parametrize(("amount", "rate"), _SHIPPED_NET_CASES)
def test_the_shipped_net_paragraph_leaves_the_whole_posting_record_alone(
    amount: Decimal, rate: Decimal
) -> None:
    """Drive the real `Net` paragraph: VAT moves, and the other nine fields do not.

    The behavioural half of the post-condition. `_net_section` is handed a real
    `Posting-Record` [copybooks/irswspost.cob:L8-L18] whose ten fields all carry
    distinctive values, and afterwards every field except `vat_amount` is asserted
    unchanged - `post_amount` four ways over, by value, by `as_tuple()`, by encoded
    bytes and by object identity, because a change of scale, of sign placement, of
    representation or of binding would each escape a bare equality.
    """
    with _shipped_irs030_posting() as irs030:
        from acas_posting.records.irs_posting import PostingRecord

        record = PostingRecord(**_SENTINEL_RECORD_FIELDS)  # type: ignore[arg-type]
        record.post_amount = arithmetic.store(amount, _IRS_POST_AMOUNT)
        record.vat_amount = arithmetic.store(Decimal("0.00"), _IRS_VAT_AMOUNT)
        current_rate = arithmetic.store(rate, _VAT_RATE)
        assert isinstance(record.post_amount, Decimal)
        assert isinstance(current_rate, Decimal)

        before_value = record.post_amount
        before_tuple = before_value.as_tuple()
        before_bytes = _encoded(before_value, _IRS_POST_AMOUNT)

        irs030._net_section(record, current_rate)

        # 1551 compute vat-amount rounded = post-amount * WS-Vat-Current / 100.
        assert record.vat_amount == arithmetic.store(
            arithmetic.intermediate(lambda: before_value * current_rate / 100),
            _IRS_VAT_AMOUNT,
            rounded=True,
        )

        # 1553 Main-Exita.  <- nothing between them, so nothing else can have moved.
        assert record.post_amount == before_value
        assert record.post_amount.as_tuple() == before_tuple
        assert _encoded(record.post_amount, _IRS_POST_AMOUNT) == before_bytes
        # `Decimal` is immutable, so an untouched attribute must still be the very
        # object that was put there: the paragraph rebinds it not at all.
        assert record.post_amount is before_value

        # The remaining eight fields, each still exactly as the record was built.
        for name, sentinel in _SENTINEL_RECORD_FIELDS.items():
            assert getattr(record, name) == sentinel, name
        # Asserted over the dataclass's own field list too, so a field added to the
        # record later cannot quietly escape this check.
        checked = {*_SENTINEL_RECORD_FIELDS, "post_amount", "vat_amount"}
        assert {
            field.name for field in dataclasses.fields(record)
        } == checked, "a Posting-Record field is not covered by this assertion"


@pytest.mark.parametrize(("amount", "rate"), _SHIPPED_NET_CASES)
def test_the_shipped_net_paragraph_agrees_with_this_files_transcription(
    amount: Decimal, rate: Decimal
) -> None:
    """`_irs_net_vat` and `_net_section` produce the same penny, pair for pair.

    The transcription above exists so the formula can be reasoned about without a
    program module in the way; this test is what stops the two drifting apart. If the
    shipped paragraph ever computes something else - a different rounding direction, a
    quantize per sub-expression, a different receiving field - the two stop agreeing
    here, and the reader is told which of the two moved rather than being left to
    guess.
    """
    with _shipped_irs030_posting() as irs030:
        from acas_posting.records.irs_posting import PostingRecord

        post_amount = arithmetic.store(amount, _IRS_POST_AMOUNT)
        current_rate = arithmetic.store(rate, _VAT_RATE)
        assert isinstance(post_amount, Decimal)
        assert isinstance(current_rate, Decimal)

        record = PostingRecord()
        record.post_amount = post_amount
        irs030._net_section(record, current_rate)

        transcribed = _irs_net_vat(post_amount, current_rate, _IRS_VAT_AMOUNT)
        assert record.vat_amount == transcribed
        assert isinstance(record.vat_amount, Decimal)
        assert isinstance(transcribed, Decimal)
        assert record.vat_amount.as_tuple() == transcribed.as_tuple()


def test_the_shipped_gross_paragraph_is_the_one_that_reduces_post_amount() -> None:
    """The asymmetry is a property of the shipped module, not of this file's prose.

    Verbatim, the two sections' stores:

        1551      compute  vat-amount rounded =  post-amount * WS-Vat-Current / 100.
        1553  Main-Exita.

        1562      compute  vat-amount rounded =
        1563          post-amount - (post-amount / ((WS-Vat-Current + 100) / 100)).
        1564      subtract vat-amount  from  post-amount.
        1566  Main-Exitb.

    So `Gross` stores twice - the VAT first, then the amount - and `Net` stores once.
    Asserted here over both paragraphs at once, in one place, so that REMOVING the
    subtract from `Gross` fails just as loudly as ADDING one to `Net`. The
    behavioural lock on the subtract itself lives in the sibling file
    `tests/arithmetic/test_irs_vat_from_gross.py`; what is established here is only
    that the two paragraphs differ in the way the frozen source says they differ.
    """
    with _shipped_irs030_posting() as irs030:
        assert _stores_performed_by(irs030._net_section) == (
            ("STORE_ATTR", "vat_amount"),
        )
        # In this order: L1562 stores the VAT, then L1564 stores the amount. A
        # reproduction that folded the subtract into the compute would show one store.
        assert _stores_performed_by(irs030._gross_section) == (
            ("STORE_ATTR", "vat_amount"),
            ("STORE_ATTR", "post_amount"),
        )


def test_the_shipped_net_paragraph_is_driven_without_leaving_a_driver_loaded() -> None:
    """Rule R-1 holds even though this section reaches a program module.

    The loader purges every tier-isolation-prefixed name it added, so by the time any
    later test in the tier inspects `sys.modules` there is nothing forbidden in it.
    This test says so at the point of use, rather than leaving the property to be
    discovered by whichever file happens to sort last.
    """
    before = frozenset(name for name in sys.modules if _is_tier_isolated_name(name))

    with _shipped_irs030_posting() as irs030:
        assert irs030.__name__ == _IRS030_MODULE
        # While the context manager is open the module object is live and usable.
        assert callable(irs030._net_section)

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
            name
            for name in sys.modules
            if _is_tier_isolated_name(name) and name not in before
        )
    )
    assert leaked == (), leaked
    # The prefix test is a real test and not a tautology: it recognises the names it
    # is meant to recognise, and does not over-match a merely similar one.
    assert _is_tier_isolated_name("acas_posting.dal") is True
    assert _is_tier_isolated_name("acas_posting.dal.acas006_gl_posting") is True
    assert _is_tier_isolated_name("mysql.connector") is True
    assert _is_tier_isolated_name("acas_posting.database") is False
    assert _is_tier_isolated_name("acas_posting.cobol.arithmetic") is False
