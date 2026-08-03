"""The batch-control gate of `gl051`'s `end-batch`, asserted exactly as written.

WHAT THIS FILE PROVES. Three things, and the first is the reason it exists.

  1. THE VAT ENTERS THE ACTUAL GROSS *BEFORE* THE EQUALITY TEST.
     [general/gl051.cbl:L1109] mutates `actual-gross` in place and only then does
     [general/gl051.cbl:L1117] compare it with `input-gross`. The entered gross is
     VAT-inclusive while the accumulated gross is VAT-exclusive, so Agent Action
     Plan section 0.6.4 says of swapping those two steps, verbatim: reversing them
     "would reject every batch that carries VAT." The central test below runs one
     batch through both orders and asserts the accept and the reject.

  2. THE TEST IS A TWO-PART CONJUNCTION, and all four combinations are asserted.

  3. THERE ARE **THREE** DISPOSITIONS, NOT TWO. One of them never assigns
     `batch-status` at all; another rejects *before* the VAT mutation, so
     `actual-gross` is left byte-for-byte as it stood.

THE PARAGRAPH, VERBATIM. `general/gl051.cbl`, the paragraph opening at L1096::

    1099:      if       z = 99
    1100:               go to  main-exit.
    1101:      if       not truet
    1102:               move 0 to batch-status
    1103:               go to  main-exit.
    1105:      subtract input-vat  from  input-gross  giving  l9-amount.
    1106:      move     input-vat    to  l9-vat.
    1107:      move     actual-gross to  l10-amount.
    1108:      move     actual-vat   to  l10-vat.
    1109:      add      actual-vat   to  actual-gross.
    1111:      if       line-cnt > Page-Lines - 12
    1112:      perform headings.
    1113:      write print-record from line-8 after 3
    1114:      write print-record from line-9 after 2
    1115:      write print-record from line-10 after 2
    1117:      if       input-gross = actual-gross
    1118:         and   input-vat   = actual-vat
    1119:               move  1  to  batch-status
    1120:      else
    1121:               move  0  to  batch-status.
    1123:      move     "*********************"  to  l11-status.
    1126:      if       batch-status = 1
    1127:               move  "* Batch Verified Ok *"  to  l11-status
    1128:      else
    1129:               move  "*  Batch In ERROR   *"  to  l11-status.
    1134:      go       to main-exit.

THE THREE DISPOSITIONS, AND THEY DIFFER IN THEIR DATABASE EFFECT.

  * [general/gl051.cbl:L1099-L1100] - `z = 99`, the all-batches proof mode.
    Control leaves the paragraph at once. `batch-status` IS NEVER ASSIGNED ON
    THIS PATH: it keeps whatever it already held. [general/gl051.cbl:L1109] is
    never reached either, so `actual-gross` is not mutated. Rule R-4 forbids
    "improving" this into an explicit status, so the test supplies `batch-status`
    as an INCOMING value and asserts that the value survives untouched.
  * [general/gl051.cbl:L1101-L1103] - `not truet`. Rejects with zero and leaves
    BEFORE COMPARING ANYTHING, which is the one path on which a batch whose
    figures agree perfectly is still rejected. `actual-gross` is again unmutated,
    and the test asserts that as BYTE IDENTITY - same value, same `as_tuple()`,
    same packed bytes - because that is the assertion a refactor which hoisted
    [general/gl051.cbl:L1109] above the `truet` test would break.
  * [general/gl051.cbl:L1109] then [general/gl051.cbl:L1117-L1121] - the gate
    proper. `actual-vat` is added into `actual-gross`, and the batch is accepted
    only if the mutated gross AND the VAT both agree.

L1099 PRECEDES L1101, so when both conditions hold the first disposition wins and
`batch-status` is still never assigned. That ordering is asserted too.

THE ACCUMULATION SITES THAT FEED THE GATE. From the same program::

    1063:      add      post-amount  to  actual-gross.
    1064:      add      vat-amount   to  actual-vat.

These are the only writers of the two `actual-*` fields before `end-batch` runs,
and both are UN-`ROUNDED` stores. Their receivers are UNSIGNED packed decimal
whose `comp-3` is inherited from a GROUP header [copybooks/wsbatch.cob:L40-L44]::

     40:  03  Amounts                         comp-3.
     41:      05  Input-Gross     pic 9(9)v99.
     42:      05  Input-Vat       pic 9(9)v99.
     43:      05  Actual-Gross    pic 9(9)v99.
     44:      05  Actual-Vat      pic 9(9)v99.

`post-amount` is `pic s9(8)v99` and SIGNED [copybooks/wspost.cob:L23], so a credit
posting arrives negative and lands in a receiver that cannot hold a sign. THE SIGN
IS DROPPED, silently, and the magnitude survives - reproduced here, never repaired
(R-3 forbids adding a rejection the COBOL does not have). A running total that
outgrows nine integer digits likewise keeps its LOW-ORDER digits in silence.

EQUALITY IS ALGEBRAIC. COBOL compares numeric operands by value after aligning
their decimal points, so `Decimal("100.00") == Decimal("100.0")` must be true and
the comparison must never be taken over a digit string or over encoded bytes.
Encoded bytes appear in exactly one place in this file - the byte-identity
assertion about NON-mutation - and that is a different question from equality.

RULES, AND WHERE THEY COME FROM. There is NO user rules document for this project:
`review_rules` reports that no user rules were provided. The six binding rules
below are the ones the Technical Specification carries in its own section 0.7.2,
and where the specification is silent this file holds to ordinary enterprise
practice and invents nothing.

  R-1 No COBOL at runtime. This file starts no process, loads no shared object and
      imports nothing from `harness`; it needs no database, no MariaDB, no Docker
      and no GnuCOBOL. Its one prerequisite is the generated data dictionary.
  R-2 Zero binary floating point. Every figure is `decimal.Decimal` or `int`.
      There is no tolerance anywhere, because a control total either agrees or does
      not. The ambient `decimal` context is neither read nor mutated.
  R-3 No new validation, no new field, no schema change, no concurrency. The gate
      gains no "within a penny" allowance, no rounding of either side before the
      comparison and no rejection reason beyond `batch-status`. The sign drop and
      the digit-width overflow raise nothing, clamp nothing and warn about nothing.
  R-4 Legacy anomalies reproduced, never repaired. Each reproduction site carries a
      comment citing its `[general/gl051.cbl:Lnnn]` locator, per section 0.7.4's
      conflict C-3. A test asserting *sound accounting* instead of *observed
      behaviour* would itself be the defect - which is why the never-assigned
      `batch-status` of the first disposition is asserted as an absence.
  R-5 Full traceability. Every test names the frozen line it is about, and every
      descriptor arrives through its data-dictionary key or carries a
      `<path>:L<n>` locator into the declaration it was built from.
  R-6 Compiled behaviour is the tie-breaker. Nothing here is expected because
      reading the COBOL suggests it; every figure is either transcribed from a
      frozen line or measured against the migrated semantics layer, which is in
      turn tied to GnuCOBOL 3.2.0.

THE OPEN QUESTIONS THAT BEAR ON THESE FIELDS. The generated dictionary attaches
`Q-4` to all four `Amounts` members and to `Batch-Status`: that is the batch
record's declared-length contradiction, anomaly `A-15`
[copybooks/wsbatch.cob:L7-L9], which this file RECORDS and does not settle - its
primary lock lives in `test_pic_field_descriptors.py`. Two further questions were
settled by MEASUREMENT rather than by reading, and are therefore asserted directly
rather than marked as expected failures:

  * the value a signed figure takes in an unsigned receiver. Measured on GnuCOBOL
    3.2.0 and recorded at `acas_posting/dal/acas029_otm5.py` - the magnitude
    survives and the sign is discarded, NOT a two's-complement reinterpretation.
    The same question at the bridge boundary is `Q-3`, anomaly `A-11`.
  * the direction of an un-`ROUNDED` store and the precision of the intermediate
    it truncates from - question `Q-2`, measured, and carried by
    `acas_posting/cobol/arithmetic.py`.

Because both were measured, neither may be written as a strict expected failure: a
strict `xfail` whose assertion passes is itself a failure, and asserting a value
this project has already measured as an expectation-to-fail would be a fiction.

TWO FIGURES WHERE THE SPECIFICATION AND THE COMMITTED CODE DIFFER, stated openly
because a reader comparing the two will notice, and because a test may only assert
what the code it imports actually does:

  * the size of the condition-name registry. The specification quotes ninety-eight;
    `acas_posting/cobol/condition_names.py` publishes ONE HUNDRED AND FIFTY-NINE
    rows, says so in its own comment, and its per-copybook counts sum to that. The
    committed figure is the one asserted, and the batch copybook's own share of it -
    eight, counted line by line from [copybooks/wsbatch.cob:L16-L18],
    [copybooks/wsbatch.cob:L26-L27] and [copybooks/wsbatch.cob:L30-L32] - is
    asserted beside it.
  * the `unsigned` member of the four `Amounts` descriptors. The specification reads
    it as true; the descriptor carries FALSE, because `unsigned` records the
    EXPLICIT `UNSIGNED` KEYWORD, which COBOL admits only on a binary item.
    `pic 9(9)v99` carries no `S` instead, so the absence of a sign is asserted
    through `signed` and through the domain floor of zero, which is what actually
    governs the store.

WHAT THIS FILE DOES NOT DO. It does not implement the four-link abort chain that a
rejection sets in motion - that is a scenario-tier concern - and it makes no timing
or performance assertion of any kind (section 0.8.4). It builds no gate helper:
section 0.4.1.2's census puts the control-total logic in one program module, so
each test below transcribes the frozen lines itself.
"""

from __future__ import annotations

import contextlib
import decimal
import sys
import types
from collections.abc import Iterator
from decimal import Decimal
from typing import Final

import pytest

from acas_posting.cobol import (
    arithmetic,
    condition_names,
    field as cobol_field,
    usage as cobol_usage,
)
from acas_posting.dictionary import loader, model

# Declared in pyproject.toml's `markers` list and applied here; nothing in this
# file registers a marker of its own.
pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  Dictionary-key lookup, defensively
#
#  Rule R-5 makes the generated dictionary the one door to a field's picture,
#  scale, signedness and carrier, so a mistyped key must fail with a message that
#  names the near misses rather than tempting a reader to hand-write the metadata.
#  `loader.DictionaryKeyError` already does that for an unknown key; this wrapper
#  adds the table's own key list when the table itself is known, because the
#  commonest slip is the COLUMN half of `<TABLE>.<COLUMN>` and not the table half.
# ---------------------------------------------------------------------------


class MissingDictionaryKeyError(KeyError):
    """A key this file asks for is absent from the generated dictionary.

    A `KeyError` subclass so that a caller which does not care about the
    distinction can catch `KeyError`, exactly as `loader.DictionaryKeyError` and
    `loader.DictionaryLookupError` are both `KeyError` subclasses.
    """


def _sibling_keys(key: str) -> tuple[str, ...]:
    """List the keys the dictionary does carry for this key's table.

    Args:
        key: The key that was not found, in `<TABLE-NAME>.<COLUMN-NAME>` form.

    Returns:
        Every entry key of that table in the dictionary's own order, or an empty
            tuple when the table half of the key is unknown too.
    """
    table = key.split(".", 1)[0]
    try:
        entries = loader.entries_for_table(table)
    except loader.DictionaryLookupError:
        return ()
    return tuple(entry.key for entry in entries)


def descriptor(key: str) -> cobol_field.FieldDescriptor:
    """Build one field's descriptor from its data-dictionary key.

    Args:
        key: A qualified entry key, exact and case-sensitive.

    Returns:
        The descriptor the generated dictionary holds for that key.

    Raises:
        MissingDictionaryKeyError: No entry carries the key. The message quotes the
            loader's own near-miss report and, where the table is known, the keys
            that table does carry.
    """
    try:
        return cobol_field.FieldDescriptor.from_dictionary_key(key)
    except loader.DictionaryKeyError as absent:
        siblings = _sibling_keys(key)
        offer = (
            f" Keys this table does carry: {siblings!r}." if siblings else ""
        )
        raise MissingDictionaryKeyError(
            f"{key!r} is not in the generated data dictionary, so no descriptor "
            f"for it can be built. Regenerate the artifact with "
            f"`python -m acas_posting.dictionary.generate` and correct the key; "
            f"rule R-5 forbids hand-writing the field's metadata instead.{offer} "
            f"Loader report: {absent}"
        ) from absent


def encoded(
    value: Decimal | int | str, receiving: cobol_field.FieldDescriptor
) -> bytes:
    """Lay out one stored value as the bytes its field holds.

    USED ONLY TO PROVE NON-MUTATION. The equality the gate performs is algebraic
    and never goes near these bytes; a byte comparison would be a different and
    stricter test than the COBOL relation condition performs.

    Args:
        value: The value the field holds.
        receiving: That field's descriptor.

    Returns:
        Exactly `receiving.byte_length` bytes.
    """
    return cobol_usage.encode(
        value,
        usage=receiving.usage,
        digits=receiving.digits,
        scale=receiving.scale,
        character_length=receiving.character_length,
        signed=receiving.signed,
        unsigned=receiving.unsigned,
        sign_position=receiving.sign_position,
    )


# ---------------------------------------------------------------------------
#  The fields the gate reads and writes
# ---------------------------------------------------------------------------

#: `05  Input-Gross     pic 9(9)v99.` [copybooks/wsbatch.cob:L41] - the gross the
#: operator entered, VAT-INCLUSIVE.
INPUT_GROSS = descriptor("GLBATCH-REC.INPUT-GROSS")

#: `05  Input-Vat       pic 9(9)v99.` [copybooks/wsbatch.cob:L42].
INPUT_VAT = descriptor("GLBATCH-REC.INPUT-VAT")

#: `05  Actual-Gross    pic 9(9)v99.` [copybooks/wsbatch.cob:L43] - accumulated at
#: [general/gl051.cbl:L1063], VAT-EXCLUSIVE until [general/gl051.cbl:L1109].
ACTUAL_GROSS = descriptor("GLBATCH-REC.ACTUAL-GROSS")

#: `05  Actual-Vat      pic 9(9)v99.` [copybooks/wsbatch.cob:L44] - accumulated at
#: [general/gl051.cbl:L1064].
ACTUAL_VAT = descriptor("GLBATCH-REC.ACTUAL-VAT")

#: `03  Batch-Status        pic 9.` [copybooks/wsbatch.cob:L25] - the gate's whole
#: observable outcome, and the field the four-link abort chain reads.
BATCH_STATUS = descriptor("GLBATCH-REC.BATCH-STATUS")

#: `03  Post-Amount     pic s9(8)v99.` [copybooks/wspost.cob:L23] - SIGNED, and the
#: sending field of [general/gl051.cbl:L1063].
POST_AMOUNT = descriptor("GLPOSTING-REC.POST-AMOUNT")

#: `03  Vat-Amount      pic s9(8)v99.` [copybooks/wspost.cob:L28] - SIGNED, and the
#: sending field of [general/gl051.cbl:L1064].
VAT_AMOUNT = descriptor("GLPOSTING-REC.VAT-AMOUNT")

#: `05  Page-Lines      binary-char  unsigned.` [copybooks/wssystem.cob:L65] - one
#: operand of the relation condition at [general/gl051.cbl:L1111].
PAGE_LINES = descriptor("SYSTEM-REC.PAGE-LINES")

#: The four members of the `Amounts` group [copybooks/wsbatch.cob:L40], in
#: declaration order.
AMOUNTS = (INPUT_GROSS, INPUT_VAT, ACTUAL_GROSS, ACTUAL_VAT)

#: `03  l9-amount           pic z(9)9.99bb.` [general/gl051.cbl:L331] - the
#: receiver of [general/gl051.cbl:L1105]. A PRINT-LINE field: it reaches no table,
#: so the generated dictionary does not catalogue it and its `source_locator` is
#: the only traceability it will ever have. The picture gives ten integer digit
#: positions - nine suppressed by `z(9)` plus one - and two decimal places; the
#: `.` and the two `b` are edit characters, and the character width they add is
#: not modelled here because nothing downstream reads this field's bytes. Agent
#: Action Plan section 0.1.1 excludes such representation-only declarations from
#: the migration while preserving the control flow around them.
L9_AMOUNT = cobol_field.FieldDescriptor(
    name="l9-amount",
    usage=model.Usage.DISPLAY,
    usage_declared_at=model.UsageDeclaredAt.DEFAULT,
    picture="z(9)9.99bb",
    signed=False,
    sign_position=model.SignPosition.NONE,
    digits=12,
    integer_digits=10,
    scale=2,
    is_edited=True,
    python_storage=model.CobolPythonStorage.DECIMAL,
    source_locator="general/gl051.cbl:L331",
)


# ---------------------------------------------------------------------------
#  The literals the frozen paragraph writes
# ---------------------------------------------------------------------------

#: `if z = 99` [general/gl051.cbl:L1099]. `03  z  pic 99.`
#: [general/gl051.cbl:L172].
Z_ALL_BATCHES = 99

#: `88  truet  value 1.` [general/gl051.cbl:L177], on `03  trutht  pic 9.`
#: [general/gl051.cbl:L175]. `88  falset  value zero.`
#: [general/gl051.cbl:L176] is declared and never tested.
TRUET = 1

#: `move  1  to  batch-status` [general/gl051.cbl:L1119] - which is
#: `88  Status-Closed  value 1.` [copybooks/wsbatch.cob:L27], so ACCEPTED means
#: CLOSED.
ACCEPTED = 1

#: `move  0  to  batch-status` [general/gl051.cbl:L1102] and
#: [general/gl051.cbl:L1121] - which is `88  Status-Open  value 0.`
#: [copybooks/wsbatch.cob:L26], so REJECTED means the batch is left OPEN.
REJECTED = 0

#: An arbitrary in-range `pic 9` value that is neither `ACCEPTED` nor `REJECTED`,
#: supplied as the INCOMING `batch-status` so that "never assigned" is visible
#: rather than indistinguishable from a rejection.
INCOMING_BATCH_STATUS = 7

#: `Page-Lines - 12` [general/gl051.cbl:L1111] - twelve, because three multi-line
#: total blocks are about to be written.
TOTALS_PAGE_MARGIN = 12

#: `Page-Lines - 6` [general/gl051.cbl:L1060] - the sibling site inside the `loop`
#: paragraph, which precedes `end-batch` and subtracts SIX for a single detail
#: line. The two margins differ, and both are reproduced as written.
DETAIL_PAGE_MARGIN = 6


# ---------------------------------------------------------------------------
#  The four `Amounts` members: packed decimal INHERITED FROM A GROUP, and UNSIGNED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("member", "cobol_name", "locator"),
    [
        (INPUT_GROSS, "Input-Gross", "copybooks/wsbatch.cob:L41"),
        (INPUT_VAT, "Input-Vat", "copybooks/wsbatch.cob:L42"),
        (ACTUAL_GROSS, "Actual-Gross", "copybooks/wsbatch.cob:L43"),
        (ACTUAL_VAT, "Actual-Vat", "copybooks/wsbatch.cob:L44"),
    ],
    ids=["input-gross", "input-vat", "actual-gross", "actual-vat"],
)
def test_each_amounts_member_inherits_comp_3_from_its_group_header(
    member: cobol_field.FieldDescriptor, cobol_name: str, locator: str
) -> None:
    """Every operand of the gate is GROUP-inherited packed decimal, 11 digits, 6 bytes.

    `03  Amounts  comp-3.` [copybooks/wsbatch.cob:L40] carries the USAGE and the four
    `pic 9(9)v99` members below it carry none of their own, so reading the picture
    line alone would class all four as zoned DISPLAY and give them nine bytes each
    instead of six. That is why the descriptor comes from the generated dictionary,
    which records WHERE the usage was declared as well as what it was.
    """
    assert member.name == cobol_name
    assert member.picture == "9(9)v99"

    # Packed, and inherited rather than declared on the item.
    assert member.usage is model.Usage.COMP_3
    assert member.is_packed is True
    assert member.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert member.usage_inherited_from == "Amounts"

    # `pic 9(9)v99` carries no `S`, so the item holds no sign. `unsigned` is the
    # EXPLICIT `UNSIGNED` KEYWORD, which COBOL admits only on a binary item -
    # `Page-Lines binary-char unsigned` [copybooks/wssystem.cob:L65] is the one in
    # this file that carries it - so it is false here and the absence of a sign is
    # read from `signed` and from the domain floor instead.
    assert member.signed is False
    assert member.unsigned is False
    assert member.sign_position is model.SignPosition.NONE
    assert member.min_value == 0
    assert member.value_domain == (0, 99_999_999_999)

    assert member.digits == 11
    assert member.integer_digits == 9
    assert member.scale == 2
    # `(digits + 2) // 2`: eleven digits plus the sign nibble, two nibbles a byte.
    assert member.byte_length == 6
    assert member.quantum == Decimal("0.01")

    assert member.python_storage is model.CobolPythonStorage.DECIMAL
    assert member.is_decimal is True
    assert member.is_int is False

    # Rule R-5: the descriptor leads a reader to the frozen declaration.
    assert member.source_locator == locator
    assert member.dictionary_key is not None
    assert locator in member.cite()


def test_the_amounts_group_is_twenty_four_bytes_of_the_batch_record() -> None:
    """The four members occupy six bytes each, and no total is claimed beyond them.

    Six bytes apiece is a property of each member's own declaration
    [copybooks/wsbatch.cob:L40-L44]. The RECORD's length is a different matter and
    an open one - see the anomaly test below - so nothing here adds the other
    members up.
    """
    assert [member.byte_length for member in AMOUNTS] == [6, 6, 6, 6]
    assert sum(member.byte_length for member in AMOUNTS) == 24


def test_the_batch_record_length_contradiction_is_recorded_and_left_open() -> None:
    """Anomaly A-15 is carried by the dictionary and settled nowhere in this file.

    [copybooks/wsbatch.cob:L7-L9] records three figures that cannot all hold::

          7: *> 96 bytes 26/03/09
          8: *> 98 bytes 20/12/11 (no, dont understand as I count 96)
          9: *>   but function length (Batch-record) says 98?

    The generated dictionary attaches anomaly `A-15` and open question `Q-4` to
    every field of the record, and the primary lock on the anomaly lives in
    `test_pic_field_descriptors.py`. This test only shows that the record-length
    question reaches the gate's own fields and that nothing here answers it: the
    descriptor vocabulary has no member in which an answer could be written.
    """
    for member in (*AMOUNTS, BATCH_STATUS):
        assert "A-15" in member.anomaly_refs()
        assert "Q-4" in member.ambiguity_refs()

    slots = set(cobol_field.FieldDescriptor.__slots__)
    assert "record_length" not in slots
    assert "declared_length" not in slots

    # A field's own width is a fact about its own declaration and says nothing about
    # the record total, which is what the frozen comment disagrees with itself over.
    assert BATCH_STATUS.byte_length == 1
    assert BATCH_STATUS.picture == "9"
    assert BATCH_STATUS.python_storage is model.CobolPythonStorage.INT


# ---------------------------------------------------------------------------
#  Disposition 1 - [general/gl051.cbl:L1099-L1100]
# ---------------------------------------------------------------------------


def test_first_disposition_z_99_never_assigns_batch_status() -> None:
    """`z = 99` leaves at once and writes NOTHING - not even a rejection.

    Reproduces [general/gl051.cbl:L1099-L1100]. `batch-status` IS NEVER ASSIGNED ON
    THIS PATH: the paragraph has no `move` before the `go to`, so the field keeps
    whatever the batch record already held. Rule R-4 forbids supplying a value here;
    an implementation that "tidied" this into an explicit rejection would change the
    batch record and therefore the database, so `batch-status` is supplied as an
    INCOMING value and the assertion is that the incoming value survives.
    """
    # The batch as `loop` [general/gl051.cbl:L1063-L1064] left it.
    actual_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
    actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
    # SUPPLIED, not initialised.
    batch_status = arithmetic.store(INCOMING_BATCH_STATUS, BATCH_STATUS)

    # `03  z  pic 99.` [general/gl051.cbl:L172], holding the all-batches sentinel.
    z = Z_ALL_BATCHES

    # 1099  if       z = 99
    # 1100           go to  main-exit.            GO TO class 3 - a section exit.
    assert arithmetic.compare(z, Z_ALL_BATCHES) == 0

    # Nothing from L1101 onwards runs, so `batch-status` is neither of the two
    # values the paragraph can write.
    assert batch_status == INCOMING_BATCH_STATUS
    assert batch_status != ACCEPTED
    assert batch_status != REJECTED

    # 1109  add      actual-vat   to  actual-gross.   NOT REACHED. The counterfactual
    # below is what L1109 would have produced; `actual-gross` is not it.
    would_have_mutated = arithmetic.add_to(
        actual_vat, receiver_value=actual_gross, receiving=ACTUAL_GROSS
    )
    as_it_arrived = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
    assert actual_gross == as_it_arrived
    assert actual_gross.as_tuple() == as_it_arrived.as_tuple()
    assert arithmetic.compare(actual_gross, would_have_mutated) != 0
    assert would_have_mutated == Decimal("1200.00")


def test_the_first_disposition_wins_when_both_guards_would_fire() -> None:
    """L1099 precedes L1101, so `z = 99` beats `not truet` and nothing is written.

    Reproduces the ORDER of [general/gl051.cbl:L1099] and
    [general/gl051.cbl:L1101]. Both conditions hold here. The first `go to` is taken,
    so `move 0 to batch-status` [general/gl051.cbl:L1102] never runs and
    `batch-status` is still never assigned - a different database outcome from the
    rejection the second disposition would have written.
    """
    batch_status = arithmetic.store(INCOMING_BATCH_STATUS, BATCH_STATUS)
    z = Z_ALL_BATCHES
    # `03  trutht  pic 9.` [general/gl051.cbl:L175] cleared by `get-description`.
    trutht = 0

    both_guards_hold = (
        arithmetic.compare(z, Z_ALL_BATCHES) == 0
        and arithmetic.compare(trutht, TRUET) != 0
    )
    assert both_guards_hold is True

    # 1099-1100 is written first, so it is the one that runs.
    exit_taken = (
        "L1100" if arithmetic.compare(z, Z_ALL_BATCHES) == 0 else "L1103"
    )
    assert exit_taken == "L1100"
    assert batch_status == INCOMING_BATCH_STATUS
    assert batch_status != REJECTED
    assert not condition_names.is_status_open(batch_status)
    assert not condition_names.is_status_closed(batch_status)


# ---------------------------------------------------------------------------
#  Disposition 2 - [general/gl051.cbl:L1101-L1103]
# ---------------------------------------------------------------------------


def test_second_disposition_rejects_before_the_vat_mutation() -> None:
    """`not truet` rejects with zero and leaves BEFORE anything is compared.

    Reproduces [general/gl051.cbl:L1101-L1103]. This is the only path on which a
    batch whose figures agree perfectly is still rejected: `get-description` cleared
    `trutht` because a posting named a nominal account that does not exist, and the
    rejection is decided without the comparison ever being reached.

    The figures used here DO agree, so the assertion is not merely that the status is
    zero but that `actual-gross` is BYTE-IDENTICAL to the total the accumulation left.
    That byte identity is the assertion a refactor which hoisted
    [general/gl051.cbl:L1109] above the `truet` test would break, and it is the only
    place in this file where encoded bytes are compared - the gate's own equality is
    algebraic and never touches them.
    """
    input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
    input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
    actual_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
    actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
    batch_status = arithmetic.store(INCOMING_BATCH_STATUS, BATCH_STATUS)
    as_it_arrived = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)

    z = 1
    trutht = 0

    # 1099  if       z = 99                       Not taken - a single batch.
    assert arithmetic.compare(z, Z_ALL_BATCHES) != 0
    # 1101  if       not truet
    # 1102           move  0  to  batch-status
    # 1103           go to  main-exit.
    assert arithmetic.compare(trutht, TRUET) != 0
    batch_status = arithmetic.store(REJECTED, BATCH_STATUS)

    assert batch_status == REJECTED
    assert condition_names.is_status_open(batch_status) is True

    # The batch WOULD have been accepted had control reached the gate: the VAT agrees
    # outright and the gross agrees once L1109 has run. Neither test happens.
    assert arithmetic.compare(input_vat, actual_vat) == 0
    assert (
        arithmetic.compare(
            input_gross,
            arithmetic.add_to(
                actual_vat, receiver_value=actual_gross, receiving=ACTUAL_GROSS
            ),
        )
        == 0
    )

    # BYTE IDENTITY - value, digit tuple and packed bytes.
    assert actual_gross == as_it_arrived
    assert actual_gross.as_tuple() == as_it_arrived.as_tuple()
    assert encoded(actual_gross, ACTUAL_GROSS) == encoded(
        as_it_arrived, ACTUAL_GROSS
    )
    # 1000.00 is 100000 hundredths, laid out as eleven packed digits and an `f`
    # sign nibble, because the item holds no sign.
    assert encoded(actual_gross, ACTUAL_GROSS) == bytes.fromhex("00000100000f")
    assert len(encoded(actual_gross, ACTUAL_GROSS)) == ACTUAL_GROSS.byte_length


# ---------------------------------------------------------------------------
#  Disposition 3 - [general/gl051.cbl:L1109] and [general/gl051.cbl:L1117-L1121]
# ---------------------------------------------------------------------------


def test_third_disposition_accepts_when_both_equalities_hold() -> None:
    """The gate proper: mutate, compare, then write one or zero.

    Reproduces [general/gl051.cbl:L1109] followed by
    [general/gl051.cbl:L1117-L1121], with both guards above it not taken.
    """
    input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
    input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
    actual_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
    actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
    batch_status = arithmetic.store(INCOMING_BATCH_STATUS, BATCH_STATUS)

    z = 1
    trutht = TRUET

    # 1099  if       z = 99                       Not taken.
    assert arithmetic.compare(z, Z_ALL_BATCHES) != 0
    # 1101  if       not truet                    Not taken.
    assert arithmetic.compare(trutht, TRUET) == 0
    # 1109  add      actual-vat   to  actual-gross.
    actual_gross = arithmetic.add_to(
        actual_vat, receiver_value=actual_gross, receiving=ACTUAL_GROSS
    )
    # 1117  if       input-gross = actual-gross
    # 1118     and   input-vat   = actual-vat
    both_agree = (
        arithmetic.compare(input_gross, actual_gross) == 0
        and arithmetic.compare(input_vat, actual_vat) == 0
    )
    # 1119           move  1  to  batch-status
    # 1121           move  0  to  batch-status.
    batch_status = arithmetic.store(
        ACCEPTED if both_agree else REJECTED, BATCH_STATUS
    )

    assert actual_gross == Decimal("1200.00")
    assert both_agree is True
    assert batch_status == ACCEPTED
    assert condition_names.is_status_closed(batch_status) is True


def test_third_disposition_mutates_the_gross_by_exactly_the_actual_vat() -> None:
    """L1109 adds `actual-vat` and nothing else, and the mutation is permanent.

    Reproduces [general/gl051.cbl:L1109]. The difference between the value the
    comparison sees and the value the accumulation left is exactly `actual-vat` - not
    `input-vat`, and not the two added together.
    """
    accumulated = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
    actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
    input_vat = arithmetic.store(Decimal("175.00"), INPUT_VAT)

    # 1109  add      actual-vat   to  actual-gross.
    mutated = arithmetic.add_to(
        actual_vat, receiver_value=accumulated, receiving=ACTUAL_GROSS
    )

    assert mutated == Decimal("1200.00")
    assert arithmetic.intermediate(lambda: mutated - accumulated) == actual_vat
    # It is `actual-vat` the statement names, not the entered figure.
    assert arithmetic.compare(
        arithmetic.intermediate(lambda: mutated - accumulated), input_vat
    ) != 0
    # And the mutation is to the SAME field the comparison then reads, so it is
    # visible to L1117 and to every later reader of the batch record. The result fits
    # the field, which a second store leaves untouched. Neither assertion reads the
    # ambient decimal context: the digit tuple is a property of the value, and the
    # arithmetic module works inside a context of its own (rule R-2).
    assert mutated.as_tuple().exponent == -2
    assert arithmetic.store(mutated, ACTUAL_GROSS) == mutated


# ---------------------------------------------------------------------------
#  THE CENTRAL TEST - the VAT enters the gross BEFORE the comparison
# ---------------------------------------------------------------------------


def test_the_vat_enters_the_gross_before_the_comparison() -> None:
    """As written the batch is accepted; with the two steps swapped it is rejected.

    THE REASON THIS FILE EXISTS. [general/gl051.cbl:L1109] `add actual-vat to
    actual-gross.` runs BEFORE [general/gl051.cbl:L1117-L1118] compares the gross,
    because the operator enters a VAT-INCLUSIVE gross while `loop`
    [general/gl051.cbl:L1063] accumulates a VAT-EXCLUSIVE one. Agent Action Plan
    section 0.6.4, verbatim: reversing these two steps "would reject every batch that
    carries VAT."

    The figures: entered gross 1200.00 and entered VAT 200.00; accumulated gross
    1000.00 and accumulated VAT 200.00. The VAT is NON-ZERO, which is what makes the
    two orders disagree - on a VAT-free batch they would agree and the defect would
    be invisible.
    """
    input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
    input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
    accumulated_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
    actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)

    # The batch carries VAT, and the entered gross is the net plus that VAT.
    assert arithmetic.compare(actual_vat, 0) != 0
    assert arithmetic.intermediate(
        lambda: accumulated_gross + actual_vat
    ) == input_gross

    # AS WRITTEN - 1109, then 1117-1118.
    mutated_gross = arithmetic.add_to(
        actual_vat, receiver_value=accumulated_gross, receiving=ACTUAL_GROSS
    )
    as_written = (
        ACCEPTED
        if (
            arithmetic.compare(input_gross, mutated_gross) == 0
            and arithmetic.compare(input_vat, actual_vat) == 0
        )
        else REJECTED
    )

    # SWAPPED - the comparison first, so it sees the VAT-exclusive total.
    swapped = (
        ACCEPTED
        if (
            arithmetic.compare(input_gross, accumulated_gross) == 0
            and arithmetic.compare(input_vat, actual_vat) == 0
        )
        else REJECTED
    )

    assert as_written == ACCEPTED
    assert swapped == REJECTED
    assert as_written != swapped
    assert condition_names.is_status_closed(as_written) is True
    # A rejected batch is left OPEN, which is what the next phase looks for.
    assert condition_names.is_status_open(swapped) is True


def test_the_vat_addition_is_an_unrounded_store() -> None:
    """L1109 carries no `ROUNDED`, so the store truncates toward zero.

    The whole in-scope cycle has exactly FIVE `ROUNDED` sites -
    [general/gl051.cbl:L791], [general/gl051.cbl:L796], [general/gl080.cbl:L328],
    [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562] - and
    [general/gl051.cbl:L1109] is not one of them, nor are the two accumulations at
    [general/gl051.cbl:L1063-L1064] that feed it. Truncation is therefore the
    default path and rounding the annotated exception; getting that the wrong way
    round would move a penny on essentially every posted figure.
    """
    assert arithmetic.ROUNDING_DIRECTIONS[False] == decimal.ROUND_DOWN
    assert arithmetic.ROUNDING_DIRECTIONS[True] == decimal.ROUND_HALF_UP
    assert cobol_field.TRUNCATING_STORE == decimal.ROUND_DOWN
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP

    # A third decimal place is the only way the two directions can be told apart,
    # and the receiving field has room for two.
    accumulated = arithmetic.store(Decimal("1200.00"), ACTUAL_GROSS)
    third_place = Decimal("0.005")

    # 1109  add      actual-vat   to  actual-gross.   No ROUNDED is written, and the
    # default of `add_to` is the un-ROUNDED store.
    as_written = arithmetic.add_to(
        third_place, receiver_value=accumulated, receiving=ACTUAL_GROSS
    )
    spelled_out = arithmetic.add_to(
        third_place,
        receiver_value=accumulated,
        receiving=ACTUAL_GROSS,
        rounded=False,
    )
    had_it_said_rounded = arithmetic.add_to(
        third_place,
        receiver_value=accumulated,
        receiving=ACTUAL_GROSS,
        rounded=True,
    )

    assert as_written == spelled_out
    assert as_written == Decimal("1200.00")
    assert had_it_said_rounded == Decimal("1200.01")
    assert as_written != had_it_said_rounded


# ---------------------------------------------------------------------------
#  The two-part conjunction - all four combinations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    (
        "accumulated_gross",
        "actual_vat",
        "gross_agrees",
        "vat_agrees",
        "expected_status",
    ),
    [
        # Entered gross 1200.00 and entered VAT 200.00 throughout.
        # Both agree: net 1000.00 plus VAT 200.00 is the entered gross exactly.
        (Decimal("1000.00"), Decimal("200.00"), True, True, ACCEPTED),
        # GROSS AGREES, VAT DOES NOT. Reachable precisely because the gross is
        # compared AFTER L1109 has folded the VAT in, so a COMPENSATING error in the
        # two components cancels in the total: the net is 50.00 too high (1050.00
        # instead of 1000.00) and the VAT is 50.00 too low (150.00 instead of
        # 200.00), so 1050.00 + 150.00 is still 1200.00 while the VAT disagrees.
        (Decimal("1050.00"), Decimal("150.00"), True, False, REJECTED),
        # VAT agrees, gross does not: one posting short by 1.00.
        (Decimal("999.00"), Decimal("200.00"), False, True, REJECTED),
        # Neither agrees.
        (Decimal("900.00"), Decimal("150.00"), False, False, REJECTED),
    ],
    ids=[
        "both-agree",
        "gross-agrees-vat-does-not",
        "vat-agrees-gross-does-not",
        "neither-agrees",
    ],
)
def test_the_gate_is_a_conjunction_of_both_equalities(
    accumulated_gross: Decimal,
    actual_vat: Decimal,
    gross_agrees: bool,
    vat_agrees: bool,
    expected_status: int,
) -> None:
    """Both equalities must hold; either one alone is not enough.

    Reproduces [general/gl051.cbl:L1117-L1121]::

        1117:      if       input-gross = actual-gross
        1118:         and   input-vat   = actual-vat
        1119:               move  1  to  batch-status
        1120:      else
        1121:               move  0  to  batch-status.

    One `and`, so three of the four combinations reject. Nothing widens the test:
    there is no tolerance, no allowance for a penny and no rounding of either side
    before the comparison (rule R-3).
    """
    input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
    input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
    running_gross = arithmetic.store(accumulated_gross, ACTUAL_GROSS)
    running_vat = arithmetic.store(actual_vat, ACTUAL_VAT)

    # 1109  add      actual-vat   to  actual-gross.
    running_gross = arithmetic.add_to(
        running_vat, receiver_value=running_gross, receiving=ACTUAL_GROSS
    )

    # 1117 / 1118, as two separate relations joined by one `and`.
    gross_matches = arithmetic.compare(input_gross, running_gross) == 0
    vat_matches = arithmetic.compare(input_vat, running_vat) == 0
    assert gross_matches is gross_agrees
    assert vat_matches is vat_agrees

    # 1119 / 1121.
    batch_status = arithmetic.store(
        ACCEPTED if (gross_matches and vat_matches) else REJECTED, BATCH_STATUS
    )
    assert batch_status == expected_status
    assert condition_names.is_status_closed(batch_status) is (
        expected_status == ACCEPTED
    )
    assert condition_names.is_status_open(batch_status) is (
        expected_status == REJECTED
    )



# ---------------------------------------------------------------------------
#  The equality is ALGEBRAIC - by value, never by representation
# ---------------------------------------------------------------------------


def test_the_equality_is_algebraic_across_differing_scales() -> None:
    """A two-place value equals a numerically equal value held at any other scale.

    COBOL aligns the decimal points of two numeric operands and compares what is
    left, so [general/gl051.cbl:L1117-L1118] is a comparison of VALUES. A digit-string
    comparison would give the opposite answer, and the counter-example below shows it
    doing so - it is there to be rejected, not used.
    """
    assert Decimal("100.00") == Decimal("100.0")
    assert arithmetic.compare(Decimal("100.00"), Decimal("100.0")) == 0

    # One side deliberately at a different scale before the comparison.
    entered_at_one_place = Decimal("1200.0")
    accumulated_at_two = arithmetic.store(Decimal("1200.00"), ACTUAL_GROSS)
    assert (
        entered_at_one_place.as_tuple().exponent
        != accumulated_at_two.as_tuple().exponent
    )
    assert entered_at_one_place == accumulated_at_two
    assert arithmetic.compare(entered_at_one_place, accumulated_at_two) == 0

    # THE COUNTER-EXAMPLE. Comparing the two as text disagrees with COBOL, which is
    # why no comparison in this file is taken over `str` or over encoded bytes.
    assert str(entered_at_one_place) != str(accumulated_at_two)

    # Whole numbers and trailing zeros compare equal too.
    assert arithmetic.compare(Decimal("1200"), accumulated_at_two) == 0
    assert arithmetic.compare(Decimal("1200.000"), accumulated_at_two) == 0


def test_a_negative_zero_equals_zero() -> None:
    """An empty batch compares equal whichever sign the zero carries.

    The gate at [general/gl051.cbl:L1117-L1118] runs on an empty batch as readily as
    on a full one, and a signed zero must not make it reject. The store into the
    unsigned receiver also lands a plain zero.
    """
    assert Decimal("0.00") == Decimal("-0.00")
    assert arithmetic.compare(Decimal("0.00"), Decimal("-0.00")) == 0
    # The two are DIFFERENT objects with different sign bits, and still equal.
    assert Decimal("0.00").as_tuple().sign != Decimal("-0.00").as_tuple().sign

    stored = arithmetic.store(Decimal("-0.00"), ACTUAL_GROSS)
    assert stored == Decimal("0.00")
    assert stored.as_tuple().sign == 0

    # An empty batch: every figure zero, so both equalities hold and the batch is
    # accepted. Reproduces the gate on the empty-batch scenario.
    both_agree = (
        arithmetic.compare(
            arithmetic.store(0, INPUT_GROSS),
            arithmetic.add_to(
                arithmetic.store(0, ACTUAL_VAT),
                receiver_value=arithmetic.store(0, ACTUAL_GROSS),
                receiving=ACTUAL_GROSS,
            ),
        )
        == 0
        and arithmetic.compare(
            arithmetic.store(0, INPUT_VAT), arithmetic.store(0, ACTUAL_VAT)
        )
        == 0
    )
    assert both_agree is True


@pytest.mark.parametrize(
    "incoming",
    [
        Decimal("1200"),
        Decimal("1200.0"),
        Decimal("1200.00"),
        Decimal("1200.005"),
        1200,
        "1200.00",
    ],
    ids=["whole", "one-place", "two-places", "three-places", "int", "text"],
)
def test_a_store_brings_both_sides_to_two_decimal_places(
    incoming: Decimal | int | str,
) -> None:
    """After its store every operand of the gate carries exponent minus two.

    Which is why the comparison at [general/gl051.cbl:L1117-L1118] is normally
    between two values of the same scale - and why the differing-scale case above is
    asserted separately rather than assumed away.
    """
    for member in AMOUNTS:
        stored = arithmetic.store(incoming, member)
        assert isinstance(stored, Decimal)
        assert stored.as_tuple().exponent == -2
        # The third place is discarded, not rounded: no `ROUNDED` is written at
        # [general/gl051.cbl:L1063], [general/gl051.cbl:L1064] or
        # [general/gl051.cbl:L1109].
        assert stored == Decimal("1200.00")


# ---------------------------------------------------------------------------
#  The accumulation sites that FEED the gate - [general/gl051.cbl:L1063-L1064]
# ---------------------------------------------------------------------------


def test_the_accumulation_sites_build_the_two_actual_totals() -> None:
    """`loop` totals the postings into the two `actual-*` fields, and nothing else does.

    Reproduces [general/gl051.cbl:L1063-L1064]::

        1063:      add      post-amount  to  actual-gross.
        1064:      add      vat-amount   to  actual-vat.

    Both are un-`ROUNDED`. The sending fields are the posting record's
    `Post-Amount` [copybooks/wspost.cob:L23] and `Vat-Amount`
    [copybooks/wspost.cob:L28]; the receiving fields are the batch record's
    `Actual-Gross` [copybooks/wsbatch.cob:L43] and `Actual-Vat`
    [copybooks/wsbatch.cob:L44].
    """
    postings = (
        (Decimal("352.75"), Decimal("58.79")),
        (Decimal("120.00"), Decimal("20.00")),
        (Decimal("1000.01"), Decimal("166.66")),
    )
    running_gross = arithmetic.store(0, ACTUAL_GROSS)
    running_vat = arithmetic.store(0, ACTUAL_VAT)

    for gross_figure, vat_figure in postings:
        post_amount = arithmetic.store(gross_figure, POST_AMOUNT)
        vat_amount = arithmetic.store(vat_figure, VAT_AMOUNT)
        # 1063  add      post-amount  to  actual-gross.
        running_gross = arithmetic.add_to(
            post_amount, receiver_value=running_gross, receiving=ACTUAL_GROSS
        )
        # 1064  add      vat-amount   to  actual-vat.
        running_vat = arithmetic.add_to(
            vat_amount, receiver_value=running_vat, receiving=ACTUAL_VAT
        )

    # 352.75 + 120.00 + 1000.01 and 58.79 + 20.00 + 166.66.
    assert running_gross == Decimal("1472.76")
    assert running_vat == Decimal("245.45")
    assert running_gross.as_tuple().exponent == -2
    assert running_vat.as_tuple().exponent == -2

    # And the gate then folds the VAT total into the gross total:
    # 1472.76 + 245.45.
    assert arithmetic.add_to(
        running_vat, receiver_value=running_gross, receiving=ACTUAL_GROSS
    ) == Decimal("1718.21")


def test_a_negative_post_amount_loses_its_sign_in_the_unsigned_receiver() -> None:
    """A credit posting arrives negative and lands as a magnitude, in silence.

    `03  Post-Amount     pic s9(8)v99.` [copybooks/wspost.cob:L23] is SIGNED, and
    `add post-amount to actual-gross.` [general/gl051.cbl:L1063] sends it into
    `05  Actual-Gross    pic 9(9)v99.` [copybooks/wsbatch.cob:L41-L44], which carries
    no `S` and so has no room for a sign. THE SIGN IS DISCARDED AND THE MAGNITUDE
    SURVIVES - measured on GnuCOBOL 3.2.0 and recorded in
    `acas_posting/dal/acas029_otm5.py`, where the same question at the bridge
    boundary is anomaly A-11's open question Q-3.

    Rule R-3 forbids turning this into a validation and rule R-4 forbids repairing
    it: nothing is raised, nothing is clamped and nothing is warned about. A batch
    of credit notes therefore accumulates a gross total of the WRONG SIGN, and the
    gate compares it as it stands.
    """
    credit = arithmetic.store(Decimal("-45.67"), POST_AMOUNT)
    # The sign survives at the source, which is what makes the loss attributable to
    # the receiver rather than to the posting.
    assert POST_AMOUNT.signed is True
    assert POST_AMOUNT.min_value < 0
    assert credit == Decimal("-45.67")
    assert credit.as_tuple().sign == 1

    # And is gone on arrival, because the receiver's domain has no negative half.
    assert ACTUAL_GROSS.signed is False
    assert ACTUAL_GROSS.min_value == 0
    landed = arithmetic.add_to(
        credit,
        receiver_value=arithmetic.store(0, ACTUAL_GROSS),
        receiving=ACTUAL_GROSS,
    )
    assert landed == Decimal("45.67")
    assert landed.as_tuple().sign == 0
    assert arithmetic.compare(landed, credit) != 0

    # A running total large enough to absorb the credit keeps an ordinary sum -
    # 100.00 - 45.67 - so the loss shows only where the total would have gone below
    # zero.
    assert arithmetic.add_to(
        credit, receiver_value=Decimal("100.00"), receiving=ACTUAL_GROSS
    ) == Decimal("54.33")


def test_a_running_total_past_nine_integer_digits_keeps_the_low_order_digits() -> None:
    """An over-wide total loses its HIGH-order digits, silently.

    `05  Actual-Gross    pic 9(9)v99.` [copybooks/wsbatch.cob:L43] holds nine integer
    digits, and a store of more than that discards the excess from the top rather
    than reporting a size condition - the frozen `add`
    [general/gl051.cbl:L1063] carries no `ON SIZE ERROR`. Reproduced, never repaired
    (rules R-3 and R-4).
    """
    assert ACTUAL_GROSS.integer_digits == 9
    assert ACTUAL_GROSS.max_value == 99_999_999_999

    # One penny over the field's capacity: the leading 1 goes and 0.99 remains.
    assert arithmetic.add_to(
        Decimal("1.00"),
        receiver_value=Decimal("999999999.99"),
        receiving=ACTUAL_GROSS,
    ) == Decimal("0.99")

    # And a single store of a ten-integer-digit figure keeps the low nine.
    assert arithmetic.store(Decimal("1234567890.99"), ACTUAL_GROSS) == Decimal(
        "234567890.99"
    )

    # The very largest figure the field can hold passes through untouched, which
    # shows the reduction is a capacity limit and not a modulus applied always.
    assert arithmetic.store(Decimal("999999999.99"), ACTUAL_GROSS) == Decimal(
        "999999999.99"
    )


# ---------------------------------------------------------------------------
#  `SUBTRACT a FROM b GIVING c` means `c = b - a` - [general/gl051.cbl:L1105]
# ---------------------------------------------------------------------------


def test_subtract_from_giving_subtracts_the_first_operand_from_the_minuend() -> None:
    """`subtract input-vat from input-gross giving l9-amount` is gross MINUS vat.

    Reproduces [general/gl051.cbl:L1105]. The receiver is the print field
    `03  l9-amount           pic z(9)9.99bb.` [general/gl051.cbl:L331], which reaches
    no table, so the same subtraction is asserted a second time into a receiver of
    the same shape as `input-gross` - the two must agree, because the operand order
    is a property of the verb and not of the receiver.
    """
    input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
    input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)

    # 1105  subtract input-vat  from  input-gross  giving  l9-amount.
    net_of_vat = arithmetic.subtract_giving(
        input_vat, minuend=input_gross, receiving=L9_AMOUNT
    )
    assert net_of_vat == Decimal("1000.00")
    assert L9_AMOUNT.source_locator == "general/gl051.cbl:L331"
    assert L9_AMOUNT.cite() == "general/gl051.cbl:L331"

    into_a_batch_field = arithmetic.subtract_giving(
        input_vat, minuend=input_gross, receiving=INPUT_GROSS
    )
    assert into_a_batch_field == net_of_vat
    assert into_a_batch_field == Decimal("1000.00")


def test_the_reversed_subtraction_is_a_different_number() -> None:
    """Read backwards the statement computes the negative of the net.

    `SUBTRACT a FROM b GIVING c` is the easiest COBOL verb to transcribe backwards,
    so the difference is asserted where it is visible: at intermediate precision,
    which has no receiving field and therefore keeps the sign.

    AND THE STORE CANNOT CATCH THE SLIP. Both candidate receivers of
    [general/gl051.cbl:L1105] - the print field at [general/gl051.cbl:L331] and any
    member of the `Amounts` group - are unsigned, so the reversed spelling stores the
    same magnitude as the written one. The operand order is therefore transcribed
    from the frozen line and never inferred from a stored value.
    """
    input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
    input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)

    as_written = arithmetic.intermediate(lambda: input_gross - input_vat)
    read_backwards = arithmetic.intermediate(lambda: input_vat - input_gross)

    assert as_written == Decimal("1000.00")
    assert read_backwards == Decimal("-1000.00")
    assert as_written != read_backwards
    assert arithmetic.compare(as_written, read_backwards) != 0
    assert read_backwards.as_tuple().sign == 1

    # The two stores agree, which is the point: only the unrounded intermediate shows
    # the difference.
    assert arithmetic.subtract_giving(
        input_gross, minuend=input_vat, receiving=L9_AMOUNT
    ) == arithmetic.subtract_giving(
        input_vat, minuend=input_gross, receiving=L9_AMOUNT
    )
    assert L9_AMOUNT.min_value == 0
    assert INPUT_GROSS.min_value == 0


def test_the_print_line_moves_precede_the_vat_mutation() -> None:
    """L1105-L1108 read the totals BEFORE L1109 changes one of them.

    Reproduces the ORDER of [general/gl051.cbl:L1105-L1108] against
    [general/gl051.cbl:L1109]. `move actual-gross to l10-amount`
    [general/gl051.cbl:L1107] copies the VAT-EXCLUSIVE total, so the proof report
    shows a different figure from the one the comparison at
    [general/gl051.cbl:L1117] tests.

    None of the four statements has a database effect - Agent Action Plan section
    0.1.1 excludes "screen output that has no database effect" from the migration -
    so this test asserts their POSITION and nothing about a table. The control flow
    around them is preserved; only the rendering is left out.
    """
    input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
    input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
    accumulated_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
    actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)

    # 1105  subtract input-vat  from  input-gross  giving  l9-amount.
    l9_amount = arithmetic.subtract_giving(
        input_vat, minuend=input_gross, receiving=L9_AMOUNT
    )
    # 1106  move     input-vat    to  l9-vat.
    l9_vat = input_vat
    # 1107  move     actual-gross to  l10-amount.
    l10_amount = accumulated_gross
    # 1108  move     actual-vat   to  l10-vat.
    l10_vat = actual_vat
    # 1109  add      actual-vat   to  actual-gross.
    mutated_gross = arithmetic.add_to(
        actual_vat, receiver_value=accumulated_gross, receiving=ACTUAL_GROSS
    )

    # The report's own two lines: entered net over VAT, then accumulated net over VAT.
    assert l9_amount == Decimal("1000.00")
    assert l9_vat == Decimal("200.00")
    assert l10_amount == Decimal("1000.00")
    assert l10_vat == Decimal("200.00")

    # `l10-amount` took the total as it stood, so it differs from what L1117 sees.
    assert arithmetic.compare(l10_amount, mutated_gross) != 0
    assert mutated_gross == Decimal("1200.00")
    assert arithmetic.compare(l10_amount, accumulated_gross) == 0


# ---------------------------------------------------------------------------
#  A relation condition has NO receiving field - [general/gl051.cbl:L1111]
# ---------------------------------------------------------------------------


def test_the_relation_condition_arithmetic_is_not_quantized_to_any_field() -> None:
    """`Page-Lines - 12` has no receiver, so nothing truncates it.

    Reproduces [general/gl051.cbl:L1111] `if line-cnt > Page-Lines - 12`. This is one
    of the six relation-condition arithmetic sites across the twelve in-scope
    programs - [general/gl051.cbl:L1060], [general/gl051.cbl:L1111],
    [sales/sl060.cbl:L621], [sales/sl060.cbl:L691], [purchase/pl060.cbl:L556] and
    [purchase/pl060.cbl:L619] - and not one of them has a receiving item. A single
    all-purpose evaluator that always quantized would silently truncate where COBOL
    does not, so the intermediate path and the store path are kept apart.

    `line-cnt` is `03  line-cnt            binary-char      value zero.`
    [general/gl051.cbl:L166], program-local WORKING-STORAGE that reaches no table.
    """
    page_lines = arithmetic.store(66, PAGE_LINES)
    assert isinstance(page_lines, int)

    # A sixty-six-line page less the twelve-line margin: 66 - 12.
    margin = arithmetic.intermediate(lambda: page_lines - TOTALS_PAGE_MARGIN)
    assert isinstance(margin, Decimal)
    assert margin == Decimal("54")
    assert margin.as_tuple().exponent == 0

    # A FRACTIONAL intermediate survives whole and truncates only at a store.
    fractional = arithmetic.intermediate(lambda: Decimal(7) / Decimal(2))
    assert fractional == Decimal("3.5")
    assert fractional.as_tuple().exponent == -1
    assert arithmetic.store(fractional, PAGE_LINES) == 3
    # `Page-Lines` has no scale at all, so it names no quantum to truncate to.
    assert PAGE_LINES.quantum is None
    assert PAGE_LINES.scale is None

    # 1111 compares `line-cnt` with that intermediate. The margin here is twelve; the
    # sibling site at [general/gl051.cbl:L1060] subtracts six instead, and both are
    # reproduced as written.
    assert TOTALS_PAGE_MARGIN == 12
    assert DETAIL_PAGE_MARGIN == 6
    assert TOTALS_PAGE_MARGIN != DETAIL_PAGE_MARGIN
    assert arithmetic.compare(60, margin) > 0
    assert arithmetic.compare(54, margin) == 0
    assert arithmetic.compare(6, margin) < 0


def test_page_lines_is_a_single_unsigned_byte() -> None:
    """`Page-Lines binary-char unsigned` holds 0 through 255, and the declaration wins.

    `05  Page-Lines      binary-char  unsigned. *> 999. Portrait / default`
    [copybooks/wssystem.cob:L65]. The maintainer's trailing `*> 999.` is a COMMENT
    and the declaration is the code: a single unsigned byte reaches 255 and not 999.
    The comment is evidence about the source and is recorded as such; nothing here
    reconciles the two.
    """
    assert PAGE_LINES.usage is model.Usage.BINARY_CHAR
    assert PAGE_LINES.is_binary_family is True
    assert PAGE_LINES.usage_declared_at is model.UsageDeclaredAt.FIELD
    assert PAGE_LINES.usage_inherited_from is None
    # The EXPLICIT keyword, which the binary family is the only class to admit.
    assert PAGE_LINES.unsigned is True
    assert PAGE_LINES.signed is False
    # A binary item's range comes from its width, so it declares no picture.
    assert PAGE_LINES.picture is None
    assert PAGE_LINES.digits is None
    assert PAGE_LINES.byte_length == 1
    assert PAGE_LINES.value_domain == (0, 255)
    assert PAGE_LINES.min_value == 0
    assert PAGE_LINES.max_value == 255
    assert PAGE_LINES.python_storage is model.CobolPythonStorage.INT
    assert PAGE_LINES.is_int is True
    assert PAGE_LINES.source_locator == "copybooks/wssystem.cob:L65"


def test_the_page_margin_goes_negative_on_a_small_page_and_nothing_guards_it() -> None:
    """A page shorter than twelve lines makes the margin negative, unguarded.

    [general/gl051.cbl:L1111] subtracts twelve from `Page-Lines` and compares the
    result with `line-cnt`, with no test that the difference is positive. For a page
    of six lines the margin is minus six, which every possible `line-cnt` exceeds, so
    `headings` [general/gl051.cbl:L1074] fires on every pass. Reproduced as written;
    adding a floor would be a validation the COBOL does not have (rule R-3).
    """
    # A six-line page less the twelve-line margin: 6 - 12.
    small_page = arithmetic.store(6, PAGE_LINES)
    margin = arithmetic.intermediate(lambda: small_page - TOTALS_PAGE_MARGIN)

    assert margin == Decimal("-6")
    assert margin.as_tuple().sign == 1
    # Outside the receiving field's own domain, which is exactly why there is no
    # receiving field: an intermediate is not bound by one.
    assert margin < PAGE_LINES.min_value

    # `line-cnt` starts at zero [general/gl051.cbl:L166], and zero already exceeds it.
    line_cnt = 0
    assert arithmetic.compare(line_cnt, margin) > 0

    # A page of exactly twelve lines gives a margin of zero, and the first line
    # already exceeds that too.
    twelve_line_page = arithmetic.store(TOTALS_PAGE_MARGIN, PAGE_LINES)
    assert arithmetic.intermediate(
        lambda: twelve_line_page - TOTALS_PAGE_MARGIN
    ) == Decimal("0")


# ---------------------------------------------------------------------------
#  The `88`-level condition names on the batch record
# ---------------------------------------------------------------------------


def test_the_batch_status_condition_names() -> None:
    """`Status-Open` is zero and `Status-Closed` is one, as the copybook declares.

    `03  Batch-Status        pic 9.` [copybooks/wsbatch.cob:L25] with
    `88  Status-Open   value 0.` [copybooks/wsbatch.cob:L26] and
    `88  Status-Closed value 1.` [copybooks/wsbatch.cob:L27].
    """
    assert condition_names.is_status_open(0) is True
    assert condition_names.is_status_open(1) is False
    assert condition_names.is_status_closed(1) is True
    assert condition_names.is_status_closed(0) is False

    assert condition_names.evaluate("Status-Closed", 1) is True
    assert condition_names.evaluate("Status-Closed", 0) is False
    assert condition_names.evaluate("Status-Open", 0) is True

    assert condition_names.values_for("Status-Open") == ("0",)
    assert condition_names.values_for("Status-Closed") == ("1",)

    open_spec = condition_names.lookup("Status-Open")
    closed_spec = condition_names.lookup("Status-Closed")
    assert open_spec.locator == "copybooks/wsbatch.cob:L26"
    assert closed_spec.locator == "copybooks/wsbatch.cob:L27"
    assert open_spec.conditional_variable == "Batch-Status"
    assert closed_spec.conditional_variable == "Batch-Status"
    assert open_spec.copybook == "copybooks/wsbatch.cob"

    # COBOL is case-insensitive about names, and `gl070` reads the condition in lower
    # case - `if status-open` [general/gl070.cbl:L314].
    assert condition_names.lookup("status-open") is open_spec


def test_an_accepted_batch_is_closed_and_a_rejected_batch_is_left_open() -> None:
    """The literals the gate writes are the two condition names, and they read inverted.

    `move  1  to  batch-status` [general/gl051.cbl:L1119] satisfies `Status-Closed`,
    so ACCEPTED means closed; `move  0` [general/gl051.cbl:L1121] and
    [general/gl051.cbl:L1102] satisfy `Status-Open`, so REJECTED LEAVES THE BATCH
    OPEN.

    That open status is what the rest of the cycle reads: `gl070`'s batch check finds
    it, raises its terminate code, the menu tests that code and returns, and `gl071`
    and `gl072` never run at all - so the database effect of a control-total mismatch
    is the ABSENCE of everything the later phases would have written. Implementing
    that chain belongs to the scenario tier; only the condition-name semantics are
    asserted here.
    """
    accepted = arithmetic.store(ACCEPTED, BATCH_STATUS)
    rejected = arithmetic.store(REJECTED, BATCH_STATUS)

    assert accepted == 1
    assert rejected == 0
    assert condition_names.is_status_closed(accepted) is True
    assert condition_names.is_status_open(accepted) is False
    assert condition_names.is_status_open(rejected) is True
    assert condition_names.is_status_closed(rejected) is False

    # The two literals the paragraph writes are exactly the two declared values, so
    # the gate can leave the field in no third state.
    assert {str(accepted), str(rejected)} == {
        condition_names.values_for("Status-Closed")[0],
        condition_names.values_for("Status-Open")[0],
    }

    # `Cleared-Status` [copybooks/wsbatch.cob:L29] is a DIFFERENT field with its own
    # three names, and `end-batch` writes none of them.
    assert condition_names.values_for("Waiting") == ("0",)
    assert condition_names.values_for("Processed") == ("1",)
    assert condition_names.values_for("Archived") == ("2",)
    assert condition_names.lookup("Waiting").conditional_variable == "Cleared-Status"


def test_the_ledger_condition_names_of_the_batch_key() -> None:
    """`GL-Batch` is one, and the other two ledgers are not it.

    `05  WS-Ledger          pic 9.` [copybooks/wsbatch.cob:L15] with
    [copybooks/wsbatch.cob:L16-L18]::

         16:          88  GL-Batch                   value 1.
         17:          88  PL-Batch                   value 2.
         18:          88  SL-Batch                   value 3.
    """
    assert condition_names.is_gl_batch(1) is True
    assert condition_names.is_gl_batch(2) is False
    assert condition_names.is_gl_batch(3) is False

    assert condition_names.values_for("GL-Batch") == ("1",)
    assert condition_names.values_for("PL-Batch") == ("2",)
    assert condition_names.values_for("SL-Batch") == ("3",)

    gl_spec = condition_names.lookup("GL-Batch")
    assert gl_spec.conditional_variable == "WS-Ledger"
    assert gl_spec.locator == "copybooks/wsbatch.cob:L16"
    assert gl_spec.copybook == "copybooks/wsbatch.cob"
    assert gl_spec.kind is condition_names.ConditionKind.SINGLE


def test_the_batch_copybook_declares_eight_condition_names() -> None:
    """Eight `88` levels in `copybooks/wsbatch.cob`, counted line by line.

    Three on `WS-Ledger` [copybooks/wsbatch.cob:L16-L18], two on `Batch-Status`
    [copybooks/wsbatch.cob:L26-L27] and three on `Cleared-Status`
    [copybooks/wsbatch.cob:L30-L32].

    The registry's committed extent is also asserted. It is read from the module as
    committed - 159 rows, which the module states in its own comment and which the
    per-copybook counts sum to - rather than from any figure quoted elsewhere, and
    the registry's own cross-check against the generated dictionary reports no
    disagreement.
    """
    declared = {
        spec.cobol_name: spec.locator
        for spec in condition_names.specs_for_copybook("copybooks/wsbatch.cob")
    }
    assert declared == {
        "GL-Batch": "copybooks/wsbatch.cob:L16",
        "PL-Batch": "copybooks/wsbatch.cob:L17",
        "SL-Batch": "copybooks/wsbatch.cob:L18",
        "Status-Open": "copybooks/wsbatch.cob:L26",
        "Status-Closed": "copybooks/wsbatch.cob:L27",
        "Waiting": "copybooks/wsbatch.cob:L30",
        "Processed": "copybooks/wsbatch.cob:L31",
        "Archived": "copybooks/wsbatch.cob:L32",
    }
    assert condition_names.COUNTS_BY_COPYBOOK["copybooks/wsbatch.cob"] == 8
    assert len(declared) == 8

    assert len(condition_names.CONDITION_NAMES) == 159
    assert sum(condition_names.COUNTS_BY_COPYBOOK.values()) == len(
        condition_names.CONDITION_NAMES
    )
    assert condition_names.cross_check_against_dictionary() == ()


def test_fs_reply_declares_no_condition_name() -> None:
    """`Fs-Reply pic 99` carries no `88` level at all.

    `03  Fs-Reply            pic 99.` [copybooks/wsfnctn.cob:L25] declares none, so
    its value set is not a condition-name question and no row of the registry belongs
    to it. The `FsReply` vocabulary lives in `acas_posting/dal/status.py`, which this
    tier must not import and does not: an arithmetic-tier test reaches no database and
    no data-access module.
    """
    assert condition_names.FS_REPLY_CONDITION_NAME_COUNT == 0
    assert condition_names.specs_for_variable("Fs-Reply") == ()
    assert "Fs-Reply" not in condition_names.conditional_variables()
    assert not [
        spec
        for spec in condition_names.CONDITION_NAMES
        if spec.conditional_variable.casefold() == "fs-reply"
    ]
    # Nor under the copybook that declares it, whose thirty rows are all elsewhere.
    assert "Fs-Reply" not in {
        spec.conditional_variable
        for spec in condition_names.specs_for_copybook("copybooks/wsfnctn.cob")
    }


# ---------------------------------------------------------------------------
#  The lookup this file resolves its own descriptors through
# ---------------------------------------------------------------------------


def test_an_unknown_dictionary_key_fails_with_its_near_misses() -> None:
    """A mistyped key must report the keys the dictionary does carry.

    Rule R-5 makes the generated dictionary the one door to a field's picture, scale,
    signedness and carrier, so the failure has to point a reader back to the artifact
    rather than tempt them to hand-write the metadata. The key mistyped below is the
    one for `05  Actual-Gross    pic 9(9)v99.` [copybooks/wsbatch.cob:L43], the field
    [general/gl051.cbl:L1109] mutates.
    """
    with pytest.raises(MissingDictionaryKeyError) as raised:
        descriptor("GLBATCH-REC.ACTUAL-GROSSS")

    reported = str(raised.value)
    assert "GLBATCH-REC.ACTUAL-GROSSS" in reported
    # The table half is right, so the sibling keys of that table are offered.
    assert "GLBATCH-REC.ACTUAL-GROSS" in reported
    assert "acas_posting.dictionary.generate" in reported
    # A `KeyError`, exactly as the loader's own two lookup failures are.
    assert isinstance(raised.value, KeyError)

    # An unknown TABLE half has no siblings to offer, and still fails cleanly.
    with pytest.raises(MissingDictionaryKeyError):
        descriptor("NO-SUCH-REC.NO-SUCH-COLUMN")


def test_every_field_the_gate_touches_carries_dictionary_provenance() -> None:
    """Each descriptor names its entry key and its frozen declaration line (R-5)."""
    catalogued = {
        INPUT_GROSS: "copybooks/wsbatch.cob:L41",
        INPUT_VAT: "copybooks/wsbatch.cob:L42",
        ACTUAL_GROSS: "copybooks/wsbatch.cob:L43",
        ACTUAL_VAT: "copybooks/wsbatch.cob:L44",
        BATCH_STATUS: "copybooks/wsbatch.cob:L25",
        POST_AMOUNT: "copybooks/wspost.cob:L23",
        VAT_AMOUNT: "copybooks/wspost.cob:L28",
        PAGE_LINES: "copybooks/wssystem.cob:L65",
    }
    for member, locator in catalogued.items():
        assert member.dictionary_key is not None
        assert member.source_locator == locator
        assert locator in member.cite()

    # The one field with no entry, because it reaches no table: the print receiver of
    # [general/gl051.cbl:L1105]. It carries a locator instead, which is the whole of
    # the traceability such a field can have.
    assert L9_AMOUNT.dictionary_key is None
    assert L9_AMOUNT.source_locator == "general/gl051.cbl:L331"
    assert L9_AMOUNT.drift() is None
    assert L9_AMOUNT.anomaly_refs() == ()
    assert L9_AMOUNT.ambiguity_refs() == ()


# ---------------------------------------------------------------------------
#  THE SHIPPED GATE
#
#  Every test above builds the gate out of `arithmetic` calls written in this file.
#  That establishes what [general/gl051.cbl:L1096-L1133] MEANS, and it is the reason
#  `test_the_vat_enters_the_gross_before_the_comparison` can show the two orders
#  disagreeing. What it cannot establish is that
#  `acas_posting/programs/gl051_batch_control_check.py::_end_batch` still runs them
#  in that order. Hoisting the comparison above [general/gl051.cbl:L1109] inside the
#  shipped paragraph would leave every test above green while - in the Agent Action
#  Plan's own words, section 0.6.4 - the cycle "would reject every batch that
#  carries VAT". This section drives the shipped paragraph and closes that gap.
#
#  WHY THE IMPORT IS DEFERRED (rule R-1). Agent Action Plan section 0.4.3 gives this
#  tier `cobol` and `records` and forbids `dal` and any database.
#  `acas_posting.programs.gl051_batch_control_check` imports `acas_posting.dal.facade`,
#  which pulls the MySQL driver in transitively, so a module-scope import would
#  leave `acas_posting.dal.*` and `mysql.*` resident and break the three
#  tier-isolation assertions this suite carries
#  (`test_comp3_packed_decimal.py:L1536`, `test_comp_binary.py:L2036`,
#  `test_pic_field_descriptors.py:L2134`), two of which read LIVE `sys.modules`. So
#  the import happens INSIDE the test bodies, behind `pytest.importorskip` so a
#  driver-free host SKIPS this section rather than failing, and the loader deletes
#  every tier-isolation-prefixed name it added in a `finally`. The pattern is the one
#  `tests/conftest.py:L423-L483` already uses for the harness modules.
#
#  NO DATABASE IS TOUCHED. `_end_batch(storage, linkage)` reads and writes seven
#  in-memory record dataclasses; it opens no connection and issues no verb. The
#  page-break branch at [general/gl051.cbl:L1111] does fire with the default
#  `page-lines`, so `_headings` runs - and that is faithful, since headings are a
#  print-line concern with no database effect.
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

#: The shipped module once imported. A plain dict, so it is inspectable and a failed
#: import is never memoised.
_SHIPPED_MODULE_CACHE: dict[str, types.ModuleType] = {}

_GL051_MODULE: Final[str] = "acas_posting.programs.gl051_batch_control_check"


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix the tier must not leave loaded?"""
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped_gl051() -> Iterator[types.ModuleType]:
    """Import `gl051_batch_control_check` for one test, leaving no trace.

    Yields:
        The shipped module.

    Raises:
        Skipped: Through `pytest.importorskip`, when the pinned MySQL driver is
            absent - which is what keeps the rest of the tier runnable on a bare
            host (rule R-1).
    """
    cached = _SHIPPED_MODULE_CACHE.get(_GL051_MODULE)
    if cached is not None:
        yield cached
        return

    before = frozenset(sys.modules)
    try:
        module = pytest.importorskip(
            _GL051_MODULE,
            reason=(
                f"{_GL051_MODULE} could not be imported - without the pinned MySQL "
                f"driver this section skips and the rest of the tier still runs"
            ),
        )
        _SHIPPED_MODULE_CACHE[_GL051_MODULE] = module
        yield module
    finally:
        for name in sorted(set(sys.modules) - before, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]


def _shipped_linkage(gl051: types.ModuleType) -> object:
    """A `_HandlerLinkage` whose seven records are all at their declared defaults.

    The batch amounts a test cares about are set by the test itself, so this carries
    no control total of its own. Built from the record modules `gl051` itself uses,
    which is what makes it the production linkage rather than a stand-in.
    """
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_ledger import WsLedgerRecord
    from acas_posting.records.gl_posting import WsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    return gl051._HandlerLinkage(
        system_record=SystemRecord(),
        posting=WsPostingRecord(),
        batch=GlBatchRecord(),
        ledger=WsLedgerRecord(),
        file_access=FileAccess(),
        file_defs=FileDefs(),
        dal_common=AcasDalCommonData(),
    )


def test_the_shipped_gate_accepts_a_vat_bearing_batch_as_written() -> None:
    """THE MUTATION THIS TEST EXISTS TO KILL: comparing before adding the VAT.

    Driven against the shipped `_end_batch`. The figures are the ones
    `test_the_vat_enters_the_gross_before_the_comparison` uses, because they are the
    ones on which the two orders disagree: entered gross 1200.00 with entered VAT
    200.00, against an accumulated VAT-EXCLUSIVE gross of 1000.00 and an accumulated
    VAT of 200.00.

        1109      add      actual-vat   to  actual-gross.
        1117      if       input-gross  =   actual-gross
        1118        and    input-vat    =   actual-vat

    As written the batch is ACCEPTED and `actual-gross` is left holding 1200.00 -
    the mutation at L1109 is permanent and visible to every later reader of the
    batch record. Evaluate the two-part equality before L1109 and the same batch is
    REJECTED, which Agent Action Plan section 0.6.4 describes as rejecting "every
    batch that carries VAT".
    """
    with _shipped_gl051() as gl051:
        storage = gl051._WorkingStorage()
        linkage = _shipped_linkage(gl051)
        amounts = linkage.batch.amounts
        amounts.input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
        amounts.input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
        amounts.actual_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
        amounts.actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
        linkage.batch.batch_status = INCOMING_BATCH_STATUS

        # The two guards the paragraph tests first are at their pass-through values,
        # so the gate is actually reached: `z` is not the all-batches marker
        # [general/gl051.cbl:L1098] and `trutht` is set [general/gl051.cbl:L1101].
        assert storage.z != gl051._Z_ALL_BATCHES
        assert storage.trutht == gl051._TRUET_VALUE
        # The batch carries VAT - a VAT-free batch would make the two orders agree
        # and the defect invisible.
        assert arithmetic.compare(amounts.actual_vat, 0) != 0

        gl051._end_batch(storage, linkage)

        assert linkage.batch.batch_status == ACCEPTED
        assert condition_names.is_status_closed(linkage.batch.batch_status) is True
        # L1109's mutation happened, in place, and by exactly the ACTUAL VAT.
        assert amounts.actual_gross == Decimal("1200.00")
        assert arithmetic.intermediate(
            lambda: amounts.actual_gross - Decimal("1000.00")
        ) == amounts.actual_vat
        # THE COUNTERFACTUAL, stated as a value rather than as prose: the gross the
        # accumulation left, 1000.00, does NOT equal the entered gross - so a gate
        # that read it before L1109 would have rejected this batch.
        assert arithmetic.compare(amounts.input_gross, Decimal("1000.00")) != 0


def test_the_shipped_gate_rejects_a_vat_mismatch_and_still_mutates_the_gross() -> None:
    """A VAT disagreement rejects, and L1109 has already run when it does.

    [general/gl051.cbl:L1117-L1118] is a CONJUNCTION, so the gross agreeing is not
    enough. Here the entered VAT is 150.00 against an accumulated 200.00: the gross
    matches after L1109 and the VAT does not, so the batch is left OPEN - which is
    the state `gl070`'s Phase 1 looks for [general/gl070.cbl:L312-L313].

    The gross is asserted to be 1200.00 even on the rejecting path, because L1109
    runs before the comparison and is not undone. A reproduction that rolled the
    mutation back on rejection would be new behaviour (rules R-3, R-4).
    """
    with _shipped_gl051() as gl051:
        storage = gl051._WorkingStorage()
        linkage = _shipped_linkage(gl051)
        amounts = linkage.batch.amounts
        amounts.input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
        amounts.input_vat = arithmetic.store(Decimal("150.00"), INPUT_VAT)
        amounts.actual_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
        amounts.actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
        linkage.batch.batch_status = INCOMING_BATCH_STATUS

        gl051._end_batch(storage, linkage)

        assert linkage.batch.batch_status == REJECTED
        assert condition_names.is_status_open(linkage.batch.batch_status) is True
        # The gross half of the conjunction DID agree once L1109 had run, so the
        # rejection is attributable to the VAT half alone.
        assert amounts.actual_gross == Decimal("1200.00")
        assert arithmetic.compare(amounts.input_gross, amounts.actual_gross) == 0
        assert arithmetic.compare(amounts.input_vat, amounts.actual_vat) != 0


def test_the_shipped_gate_rejects_a_gross_mismatch() -> None:
    """The other half of the conjunction, so neither equality is redundant.

    Entered gross 1300.00 against 1000.00 accumulated plus 200.00 VAT: after L1109
    the gross is 1200.00 and still disagrees, while the VAT halves match exactly.
    """
    with _shipped_gl051() as gl051:
        storage = gl051._WorkingStorage()
        linkage = _shipped_linkage(gl051)
        amounts = linkage.batch.amounts
        amounts.input_gross = arithmetic.store(Decimal("1300.00"), INPUT_GROSS)
        amounts.input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
        amounts.actual_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
        amounts.actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
        linkage.batch.batch_status = INCOMING_BATCH_STATUS

        gl051._end_batch(storage, linkage)

        assert linkage.batch.batch_status == REJECTED
        assert amounts.actual_gross == Decimal("1200.00")
        assert arithmetic.compare(amounts.input_vat, amounts.actual_vat) == 0
        assert arithmetic.compare(amounts.input_gross, amounts.actual_gross) != 0


def test_the_shipped_gate_keeps_its_two_early_dispositions() -> None:
    """The all-batches marker and the `not truet` path, driven for real.

    First disposition [general/gl051.cbl:L1098]: `z = 99` returns without assigning
    any status at all, so a status already on the record survives untouched AND
    L1109 never runs - the gross is left exactly as the accumulation left it.

    Second disposition [general/gl051.cbl:L1101-L1103]: `not truet` sets the status
    OPEN and returns, again before L1109. The figures used here AGREE perfectly, so
    the assertion is not merely that the batch is rejected but that a batch whose
    totals balance is still rejected - and that its gross was never mutated. That
    byte-level non-mutation is what a refactor hoisting L1109 above the `truet` test
    would break.
    """
    with _shipped_gl051() as gl051:
        # First disposition.
        storage = gl051._WorkingStorage()
        storage.z = gl051._Z_ALL_BATCHES
        linkage = _shipped_linkage(gl051)
        amounts = linkage.batch.amounts
        amounts.input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
        amounts.input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
        amounts.actual_gross = arithmetic.store(Decimal("1000.00"), ACTUAL_GROSS)
        amounts.actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
        linkage.batch.batch_status = INCOMING_BATCH_STATUS

        gl051._end_batch(storage, linkage)

        assert linkage.batch.batch_status == INCOMING_BATCH_STATUS
        assert linkage.batch.batch_status not in (ACCEPTED, REJECTED)
        assert amounts.actual_gross == Decimal("1000.00")

        # Second disposition, with figures that balance.
        storage = gl051._WorkingStorage()
        storage.trutht = 0
        linkage = _shipped_linkage(gl051)
        amounts = linkage.batch.amounts
        amounts.input_gross = arithmetic.store(Decimal("1200.00"), INPUT_GROSS)
        amounts.input_vat = arithmetic.store(Decimal("200.00"), INPUT_VAT)
        amounts.actual_gross = arithmetic.store(Decimal("1200.00"), ACTUAL_GROSS)
        amounts.actual_vat = arithmetic.store(Decimal("200.00"), ACTUAL_VAT)
        linkage.batch.batch_status = INCOMING_BATCH_STATUS

        assert storage.trutht != gl051._TRUET_VALUE
        gl051._end_batch(storage, linkage)

        assert linkage.batch.batch_status == REJECTED
        # Balanced, and rejected anyway - and the gross was NOT mutated.
        assert amounts.actual_gross == Decimal("1200.00")
        assert (
            encoded(amounts.actual_gross, ACTUAL_GROSS)
            == encoded(Decimal("1200.00"), ACTUAL_GROSS)
        )


def test_the_shipped_gate_leaves_no_driver_loaded() -> None:
    """Rule R-1 holds even though this section reaches a program module.

    The loader purges every tier-isolation-prefixed name it added, so nothing
    forbidden is resident by the time a later test in the tier inspects
    `sys.modules`.
    """
    with _shipped_gl051() as gl051:
        assert gl051.__name__ == _GL051_MODULE
        assert callable(gl051._end_batch)

    resident = tuple(sorted(n for n in sys.modules if _is_tier_isolated_name(n)))
    assert resident == (), resident
    assert _is_tier_isolated_name("acas_posting.dal") is True
    assert _is_tier_isolated_name("mysql.connector") is True
    assert _is_tier_isolated_name("acas_posting.database") is False
    assert _is_tier_isolated_name("acas_posting.cobol.condition_names") is False

