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
      frozen line or read out of the migrated semantics layer. Where that layer's
      own answer rests on a compiled arbitration the question is named, and this
      file claims no measurement of its own.

THE COMPILED ARBITRATIONS THAT BEAR ON THESE FIELDS. The generated dictionary
attaches `Q-4` to all four `Amounts` members and to `Batch-Status`: that is the
batch record's declared-length contradiction, anomaly `A-15`
[copybooks/wsbatch.cob:L7-L9], which this file RECORDS and does not settle - its
primary lock lives in `test_pic_field_descriptors.py`. It IS settled in the
register: `Q-4` is `RESOLVED BY ORACLE` (2026-08-07) and the answer is NEITHER of
the two readings taken as a contest - both record copies measure 96 and `FUNCTION
LENGTH` agrees with the field sum - so the cross-reference these fields carry now
leads to a measurement rather than to a pending experiment. Two further questions
bear on the figures below, and this file claims NO measurement of either - what
makes them assertable is that the SHIPPED LAYER'S OWN ANSWER is what this file
imports and therefore what it may assert:

  * the value a signed figure takes in an unsigned WORKING-STORAGE receiver. The
    shipped layer keeps the magnitude and discards the sign - not a two's-complement
    reinterpretation - and `acas_posting/dal/acas029_otm5.py` carries the same
    treatment at the bridge. Whether the compiled bridge agrees is `Q-3`, anomaly
    `A-11`, and it too has been measured: `Q-3` is `RESOLVED BY ORACLE`
    (2026-08-07, finding F-19) - the magnitude is kept and the sign discarded, then
    bounded by the receiving digit count, which is what the shipped layer does.
    `test_comp_binary.py` asserts that measurement and carries NO strict expected
    failure for it, because a strict `xfail` against a resolved question would
    XPASS. Nothing here contradicts any of it, because the store asserted below is
    into working storage rather than through the bridge.
  * the direction of an un-`ROUNDED` store, settled BY THE LANGUAGE - truncation
    toward zero - and the precision of the intermediate it truncates from, which was
    question `Q-2` and is now `RESOLVED BY ORACLE` (2026-08-07): extended precision
    throughout, quantized ONCE at the store. Both are carried by
    `acas_posting/cobol/arithmetic.py`; no figure below could reach the
    intermediate-precision half in any case, because every operand and every
    receiver here is a two-place decimal.

Because the shipped behaviour of both is settled, neither may be written as a
strict expected failure: a strict `xfail` whose assertion passes is itself a
failure, and asserting what the imported layer demonstrably does as an
expectation-to-fail would be a fiction.

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
import importlib
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

# Imports carried in with the merged group below, which was
# test_cli_seams_and_failure_paths.py. Only the pieces the block above did not
# already provide are listed (Agent Action Plan section 0.3.1 inventory).
import argparse
import logging
from pathlib import Path
from typing import Any

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

    The generated dictionary attaches anomaly `A-15` and the ambiguity
    cross-reference `Q-4` to every field of the record, and the primary lock on the
    anomaly lives in `test_pic_field_descriptors.py`. This test only shows that the
    record-length question reaches the gate's own fields and that nothing HERE
    answers it: the descriptor vocabulary has no member in which an answer could be
    written. The answer lives where it belongs - `Q-4` is `RESOLVED BY ORACLE`
    (2026-08-07), NEITHER declared length wins and both copies measure 96 - and the
    reference is retained as the route from a field to that record.
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
    SURVIVES - the shipped store path's own behaviour, and the same treatment
    `acas_posting/dal/acas029_otm5.py` applies at the bridge. Whether the COMPILED
    bridge agrees was anomaly A-11's question Q-3, and it agrees: Q-3 is `RESOLVED
    BY ORACLE` (2026-08-07, finding F-19) - the bridge stores the absolute value,
    bounded by the receiving digit count. The store asserted here is into working
    storage either way, so it does not turn on that answer.

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
#  (`test_comp3_packed_decimal.py test_the_packed_carrier_follows_the_scale_and_is_never_binary`,
#  `test_comp_binary.py test_q3_an_overflowing_negative_store_lands_on_its_magnitudes_byte`,
#  `test_pic_field_descriptors.py test_no_single_winner_view_exists_on_drift_entry_or_descriptor`),
#  two of which read LIVE `sys.modules`. So
#  the import happens INSIDE the test bodies -- MANDATORY, never behind
#  `pytest.importorskip`, because a skipped anomaly lock is indistinguishable from an
#  absent one and the driver is a hard dependency -- and the loader deletes every
#  tier-isolation-prefixed name it added in a `finally`. The pattern is the one
#  `tests/conftest.py _load_harness_module` already uses for the harness modules.
#
#  THE IMPORT IS MANDATORY, NOT SKIPPABLE. An earlier revision used
#  `pytest.importorskip`, so a driver-free host skipped this section silently. That
#  was wrong twice over: `mysql-connector-python==26.7.0` is a HARD
#  `[project.dependencies]` entry and a hard `requirements.txt` pin, so the guarded
#  state cannot arise for an installed package; and the control-total ordering
#  asserted below is the gate the Agent Action Plan section 0.6.4 calls load-bearing,
#  which must fail loudly rather than vanish into a skip line.
#  `importlib.import_module` is used instead, and nothing is memoised: a cached module
#  is already resident, so the purge would remove nothing and the isolation claim
#  would be about a module that had never left.
#
#  IT IS NOT BEHIND `pytest.importorskip`, and that is deliberate. A skip reads as
#  green, so a gl051 that cannot be imported at all - a syntax error, a circular
#  import, a renamed symbol in a module it imports - used to turn this whole section
#  into a pass. The pinned MySQL driver is a hard requirement of `requirements.txt`,
#  so its absence is a broken environment and not a supported configuration; the
#  `ImportError` is allowed to reach pytest as the failure it is. Nor is the module
#  MEMOISED: a cached module is already resident, so the purge would remove nothing
#  and the isolation guarantee would be a statement about a module that never left.
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

    ⭐ THE IMPORT IS NOT OPTIONAL, AND IT IS NOT MEMOISED. Both of those are the point.

    NOT OPTIONAL. `pytest.importorskip` stood here, and it turned the one failure this
    section exists to catch into a PASS. A shipped module that cannot be imported at
    all - a syntax error, a circular import, a name it imports that no longer exists -
    produced a SKIP, and a skipped test reads as green. The pinned MySQL driver the
    reason text blamed is a hard requirement of `requirements.txt`, so its absence is a
    broken environment and not a supported configuration.

    NOT MEMOISED. A cached module is ALREADY RESIDENT in `sys.modules`, so the purge in
    the `finally` had nothing to remove and every "leaves no driver loaded" claim
    downstream was a statement about a module that had never left. So this asserts the
    name is ABSENT on the way in - which is what establishes that the previous exit
    purged it - and RESIDENT while the body runs, and on the way out removes every
    tier-isolated name the import added and asserts the residue is empty.

    Yields:
        The shipped module.

    Raises:
        AssertionError: The name was already resident on the way in, or did not become
            resident, or survived the purge.
        ImportError: The module could not be imported. NOT converted into a skip:
            `mysql-connector-python==26.7.0` is a HARD `[project.dependencies]`
            entry and a hard `requirements.txt` pin, so an installed package always has
            it, and the assertions this loader serves are anomaly locks rule R-4
            requires - a lock that can disappear into a skip line is not a lock.
    """
    #  EVICT FIRST, so the import below really runs the module's top-level code and the
    #  purge in the `finally` really removes what it added. Eviction rather than a "must
    #  be absent on the way in" assertion, because this tier's own helpers legitimately
    #  import program modules in function scope to drive the SHIPPED paragraphs, and an
    #  absence assertion would make the two remediations exclude each other - the claim
    #  would then depend on file order, which is the fragility it exists to remove.
    for resident in sorted(
        (name for name in sys.modules if _is_tier_isolated_name(name)), reverse=True
    ):
        del sys.modules[resident]
    assert _GL051_MODULE not in sys.modules, (
        f"{_GL051_MODULE} survived the eviction above, so its top-level code will NOT "
        f"re-execute and the purge on the way out would remove nothing - which is what "
        f"the tier-isolation assertions in test_comp3_packed_decimal.py, "
        f"test_comp_binary.py and test_pic_field_descriptors.py rest on."
    )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(_GL051_MODULE)
        assert sys.modules.get(_GL051_MODULE) is module, (
            f"{_GL051_MODULE} did not become resident under its own name, so nothing about "
            f"a fresh import has been established."
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
                f"importing {_GL051_MODULE} left {residue} resident after the purge, so "
                f"this tier no longer runs without a database driver and the three "
                f"isolation assertions would fail depending only on file order."
            )


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

    ⭐ AND THE IMPORT REALLY HAPPENS, which is what makes the claim worth making. The
    loader used to memoise, so this guard imported nothing: the module was already
    resident from an earlier test, the purge removed nothing, and "leaves no driver
    loaded" was a statement about a module that had never left. The loader no longer
    caches, so each `with` below performs a genuine import - asserted INSIDE the block
    by reading live `sys.modules` - and the delta afterwards is a real measurement of
    what the purge removed.
    """
    before = frozenset(n for n in sys.modules if _is_tier_isolated_name(n))

    assert _GL051_MODULE not in sys.modules, (
        f"{_GL051_MODULE} was resident BEFORE this guard imported it, so the import "
        f"below would be a no-op and the purge would remove nothing."
    )
    with _shipped_gl051() as gl051:
        assert gl051.__name__ == _GL051_MODULE
        assert callable(gl051._end_batch)
        #  DURING: without this half, an import that silently did nothing would still
        #  satisfy the delta check below.
        assert sys.modules.get(_GL051_MODULE) is gl051
        assert any(
            _is_tier_isolated_name(name) and name not in before
            for name in sys.modules
        ), (
            "importing the gate added no tier-isolated name at all, so either it was "
            "already loaded or it does not reach the data-access layer."
        )
    assert _GL051_MODULE not in sys.modules, "the gate survived its loader's purge."

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
    assert _is_tier_isolated_name("mysql.connector") is True
    assert _is_tier_isolated_name("acas_posting.database") is False
    assert _is_tier_isolated_name("acas_posting.cobol.condition_names") is False


# ==========================================================================
#  MERGED GROUP - was tests/arithmetic/test_cli_seams_and_failure_paths.py
#
#  Relocated verbatim so that this directory holds exactly the fourteen test
#  modules the Agent Action Plan section 0.3.1 inventory names. Nothing was
#  rewritten: the group's own preamble follows, as its author wrote it, and
#  every test below is the test that ran under the old file name.
# ==========================================================================
#
#  The CLI boundary's failure paths, driven for real.
#
#  WHY THIS FILE EXISTS. The migration's command-line layer carries decisions that change
#  what runs and what a caller is told, and until now NO TEST IMPORTED `acas_posting.cli` at
#  all: the arithmetic tier reaches `cobol` and `records`, and the scenario tier reaches the
#  CLI only through the harness's runner script, which drives the SUCCESS path with a live
#  database. So every refusal, every short-circuit and every status code at the boundary was
#  unexercised - and each of them is a place where a wrong answer is silent rather than loud.
#
#  FIVE SEAMS, and each is one an operator or a scenario depends on:
#
#    1. THE KEY-1 SYSTEM READ [acas_posting/cli/args.py, `aa010_get_system_recs`]. The menu
#       shell reads `SYSTEM-REC` under `File-Key-No` 1 before it dispatches anything
#       [general/general.cbl:L398-L418]. If that read fails, the migrated boundary logs, then
#       CLOSES, then raises - and the pair it reports has to be THE READ'S, not the close's,
#       because a close overwrites `Fs-Reply` on the same shared block
#       [copybooks/wsfnctn.cob:L25]. Getting the order wrong turns a diagnosable failure into
#       "FS-Reply 0".
#
#    2. THE VERB VOCABULARY THE MENU STATE SELECTS. `irs/irs.cbl` copies the handler-named
#       facade [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob] and drives `acas000` by its HANDLER
#       name [irs/irs.cbl:L499, L512], while the General, Sales and Purchase menus copy the
#       entity-named one [copybooks/Proc-ACAS-FH-Calls.cob]. The two are NOT interchangeable:
#       the handler-named open family carries its own error check and can end the menu
#       program outright. The selection is a one-field decision on the menu state, and this
#       file asserts which state picks which.
#
#    3. THE POSTING CYCLE'S TWO SHORT-CIRCUITS [acas_posting/cli/gl_post_cycle.py, `load08`].
#       `gl070` raising term code 5 stops the cycle before `gl071` and `gl072`
#       [general/general.cbl:L810-L811]; a SERIOUS error - above 7
#       [general/general.cbl:L720-L721] - stops it wherever it happens. A cycle that ran
#       `gl072` after `gl071` had failed would post from a work file that was never sorted,
#       and `gl072` finds its accounts by SEQUENTIAL read [general/gl072.cbl:L410-L412], so
#       the postings would go to the WRONG ACCOUNTS with no error at all.
#
#    4. THE REQUIRED OPTIONS. Two routes refuse to run without an explicit answer: the
#       General route needs `--run-date`, because rule R-6 forbids taking a date from the
#       clock, and the IRS route needs `--clear-posting-file` or `--no-clear-posting-file`,
#       because one of those answers DELETES EVERY ROW of the transfer table
#       [irs/irs030.cbl:L1715-L1724]. An implied default for either would be an invented
#       behaviour.
#
#    5. THE CONFIGURATION CONTRACT'S STATUS CODES [acas_posting/cli/args.py SECTION 0]. The
#       frozen parameter reader publishes 8 for "no source" and 1 for "malformed"
#       [common/acas-get-params.cbl:L37-L42], and the boundary surfaces the error's own code
#       so a caller can tell "not configured" from "misconfigured" without parsing text.
#
#  ⛔ NO DATABASE, NO COBOL, NO SUBPROCESS (R-1). Every test replaces the seam it is not
#  about: the system verbs are a triple of callables, the three General Ledger programs are
#  doubles, and no test resolves a real connection. The imports of `acas_posting.cli` pull
#  `acas_posting.dal.facade` and the pinned driver in transitively, so every loader purges
#  what it added and the tier's three isolation assertions keep holding whatever order the
#  files run in.
#
#  THE RULES, as they bind this file (Agent Action Plan section 0.7.2):
#
#    R-1  No COBOL at runtime, no database.
#    R-2  Zero binary floating point. Nothing here computes money; the one numeric family in
#         play is exit statuses, which are `int`.
#    R-3  ⛔ No added validation. The two required options are not a validation this
#         migration invented - each replaces a frozen prompt that cannot be left
#         unanswered - and the tests say so at the site.
#    R-4  Reproduced, not repaired: the IRS route ABSORBS the facade copybook's `goback`
#         [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] as a normal return, because that is
#         what the frozen menu program does with it.
#    R-5  Every test names the frozen line and the shipped function it drives.
#    R-6  ⭐ The run date arrives through linkage and never from a clock, which is why
#         `--run-date` is required rather than defaulted. Asserted here as a refusal.
#
#  ⚠ PROVENANCE OF RULES. There is no user rules document - `review_rules` returns exactly
#  `No user rules provided.` The rules above are the Technical Specification's, section
#  0.7.2, and nothing has been invented to fill the gap.
#
# ==========================================================================


#: `move 1 to File-Key-No` - the system parameter record [general/general.cbl:L399].
_KEY_PARAMS: Final[int] = 1

#: The defaults record, key 2 [general/general.cbl:L406].
_KEY_DEFAULTS: Final[int] = 2

#: The period-totals record, key 4 [general/general.cbl:L402].
_KEY_TOTALS: Final[int] = 4

#: `if ws-term-code = 5` - the abort gate [general/general.cbl:L810].
_ABORT_TERM_CODE: Final[int] = 5

#: `if ws-term-code > 7` - the serious-error threshold [general/general.cbl:L720].
_SERIOUS_THRESHOLD: Final[int] = 7

#: A run date in the DD/MM/CCYY form the menu shell supplies, pinned so that nothing
#: reads a clock (R-6).
_RUN_DATE_TEXT: Final[str] = "21/09/2025"

#: The six-variable deployment contract, complete, so that the SUCCESS path of
#: `aa010_get_system_recs` can run to its end: after the key-1 read the boundary binds the
#: connection parameters onto `SYSTEM-REC` [copybooks/wssystem.cob:L137-L144], and an
#: absent contract raises there rather than at the read. Supplied as a MAPPING rather than
#: exported, so the tests do not depend on the host's own environment and cannot leak one
#: of its values. Nothing here opens a connection.
_CONTRACT: Final[dict[str, str]] = {
    "ACAS_DB_HOST": "db.internal",
    "ACAS_DB_USER": "acas",
    #: A literal that is obviously not a credential, and is never asserted by value.
    "ACAS_DB_PASSWORD": "test-only",
    "ACAS_DB_NAME": "ACASDB",
    "ACAS_DB_PORT": "3306",
    "ACAS_DB_SOCKET": "",
}

#: `argparse`'s own status for a usage error. Not this project's choice, but it IS the
#: status an operator and a shell script see, so it is asserted rather than assumed.
_USAGE_ERROR_STATUS: Final[int] = 2


@contextlib.contextmanager
def _shipped(*dotted_names: str) -> Iterator[tuple[types.ModuleType, ...]]:
    """Import shipped modules for one test, leaving `sys.modules` as found.

    Not optional and not memoised, for the reasons every loader in this directory
    records: `pytest.importorskip` turns a broken shipped module into a PASS, and a
    memoised module is already resident so the purge would remove nothing.

    Args:
        dotted_names: The importable names, in the order they are wanted.

    Yields:
        The imported modules, in the same order.

    Raises:
        AssertionError: A name was already resident on the way in, or survived the purge.
        ImportError: A module could not be imported. Deliberately NOT a skip.
    """
    #  EVICT FIRST, so the import below really runs the module's top-level code and the
    #  purge on the way out really removes what it added. Eviction rather than a "must be
    #  absent on the way in" assertion, because this tier's own helpers legitimately
    #  import program modules in function scope to drive the SHIPPED paragraphs, and an
    #  absence assertion makes the claim depend on which file ran first - the very
    #  fragility it exists to remove.
    for _resident in sorted(
        (_name for _name in sys.modules if _is_tier_isolated_name(_name)), reverse=True
    ):
        del sys.modules[_resident]
    for name in dotted_names:
        assert name not in sys.modules, (
            f"{name} survived the eviction above, so this would not be a fresh "
            f"import and the purge on the way out would remove nothing."
        )
    before = frozenset(sys.modules)
    completed = False
    try:
        modules = tuple(importlib.import_module(name) for name in dotted_names)
        yield modules
        completed = True
    finally:
        for name in sorted(set(sys.modules) - before, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
        )
        if completed:
            assert not residue, f"{dotted_names} left {residue} resident after the purge."


class _SystemVerbDouble:
    """The three `acas000` verbs the menu shell drives, recording the keys it asked for.

    ⭐ THE KEY IS READ OFF THE SHARED BLOCK AT CALL TIME, which is the whole mechanism
    being tested: `_select_key` writes `File-Key-No` [copybooks/wsfnctn.cob:L44-L56] and
    the verb is then expected to act on THAT key. A double that took the key as an
    argument would test a different design.

    Attributes:
        opened: The `File-Key-No` at each `open_input`.
        read: The `File-Key-No` at each `read_indexed`.
        closed: The `File-Key-No` at each `close`.
        order: Every call in order, as `(verb, key)`.
    """

    def __init__(
        self,
        status_module: types.ModuleType,
        facade_module: types.ModuleType,
        *,
        read_replies: dict[int, tuple[int, int]] | None = None,
        close_reply: tuple[int, int] = (0, 0),
    ) -> None:
        self._status = status_module
        self._facade = facade_module
        self._read_replies = dict(read_replies or {})
        self._close_reply = close_reply
        self.opened: list[int] = []
        self.read: list[int] = []
        self.closed: list[int] = []
        self.order: list[tuple[str, int]] = []

    def _pair(self, ctx: Any, fs_reply: int, we_error: int) -> Any:
        ctx.file_access.fs_reply = fs_reply
        ctx.file_access.we_error = we_error
        return self._facade.StatusPair(fs_reply, we_error)

    def open_input(self, ctx: Any) -> Any:
        key = ctx.file_access.logging_data.file_key_no
        self.opened.append(key)
        self.order.append(("open_input", key))
        return self._pair(ctx, 0, 0)

    def read_indexed(self, ctx: Any) -> Any:
        key = ctx.file_access.logging_data.file_key_no
        self.read.append(key)
        self.order.append(("read_indexed", key))
        fs_reply, we_error = self._read_replies.get(key, (0, 0))
        return self._pair(ctx, fs_reply, we_error)

    def close(self, ctx: Any) -> Any:
        key = ctx.file_access.logging_data.file_key_no
        self.closed.append(key)
        self.order.append(("close", key))
        return self._pair(ctx, *self._close_reply)


def _install_verbs(args_module: types.ModuleType, double: _SystemVerbDouble) -> None:
    """Put `double` behind BOTH published vocabularies for the duration of a test.

    Both, because `_system_verbs` selects between two module-level triples and a test
    about the key sequence should not also depend on which vocabulary was chosen - the
    selection has its own test.

    Args:
        args_module: The shipped `cli.args`.
        double: The stand-in.
    """
    replacement = args_module._SystemVerbs(
        double.open_input,
        double.read_indexed,
        double.close,
        "double",
        "double",
    )
    args_module._ENTITY_NAMED_SYSTEM_VERBS = replacement
    args_module._HANDLER_NAMED_SYSTEM_VERBS = replacement


def _namespace(args_module: types.ModuleType) -> argparse.Namespace:
    """The parsed namespace `aa010_get_system_recs` reads its pins from.

    ⭐ BUILT BY THE SHIPPED ARGUMENT HELPERS, not hand-assembled. `_apply_cli_pins` reads
    `ns.date_form` and moves it into `pic 9` [copybooks/wssystem.cob:L127], so a
    hand-made namespace with `None` in that attribute fails inside the semantics layer
    rather than testing anything - and building the namespace the way the routes build it
    exercises `add_calling_data_arguments` and `add_gl_linkage_arguments` at the same
    time. The two helpers are exactly the pair `gl_post_cycle._build_parser` uses.

    Args:
        args_module: The shipped `cli.args`.

    Returns:
        The namespace, with the parser's own defaults in every attribute the boundary
        reads.
    """
    parser = argparse.ArgumentParser()
    args_module.add_calling_data_arguments(
        parser, default_caller=args_module.WS_CALLER_GENERAL
    )
    args_module.add_gl_linkage_arguments(parser)
    return parser.parse_args(["--run-date", _RUN_DATE_TEXT])


# ---------------------------------------------------------------------------
#  1.  THE KEY-1 SYSTEM READ - STATUS BEFORE CLOSE
# ---------------------------------------------------------------------------


def test_the_key_one_failure_reports_the_reads_pair_and_not_the_closes() -> None:
    """⭐ THE READ'S STATUS SURVIVES THE CLOSE THAT FOLLOWS IT.

    `Fs-Reply` and `We-Error` live on ONE shared `File-Access` block
    [copybooks/wsfnctn.cob:L22-L38] that every verb writes, so the close issued after a
    failed read OVERWRITES both. The shipped boundary captures the read's pair into a
    local and reports THAT [acas_posting/cli/args.py, `aa010_get_system_recs`], which is
    the only way an operator learns why the record could not be read.

    THE DOUBLE MAKES THE TWO PAIRS DIFFERENT ON PURPOSE: the read answers
    `FS-Reply 23 / WE-Error 121` - 23 being the ISAM "record not found" every handler
    reports for an absent key - and the close answers `0 / 0`, which is what a successful
    close reports. A boundary that read the block after closing would report `0 / 0`, and
    the message would say the record could not be read and that nothing was wrong.

    THE CLOSE STILL HAPPENS, and that is asserted too: the frozen menu closes the file on
    the failure path [general/general.cbl:L412-L418], and leaving it open would strand a
    handle for the rest of the process.
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(
            status, facade, read_replies={_KEY_PARAMS: (23, 121)}, close_reply=(0, 0)
        )
        _install_verbs(args, double)
        state = args.irs_menu_state()
        system_record = args._declared_system_record()

        with pytest.raises(args.SystemRecordUnavailableError) as unavailable:
            args.aa010_get_system_recs(
                system_record,
                state,
                args.FileDefs(),
                _namespace(args),
                args.resolve_clock(_RUN_DATE_TEXT),
                env={},
            )

        #  THE READ'S PAIR, carried on the exception.
        assert unavailable.value.fs_reply == 23
        assert unavailable.value.we_error == 121
        #  Both figures also appear in the message, because that is what an operator
        #  reads; and the key is named, because there are four of them.
        message = str(unavailable.value)
        assert "FS-Reply=23" in message
        assert "WE-Error=121" in message
        assert f"File-Key-No {_KEY_PARAMS}" in message

        #  The close happened, on key 1, AFTER the read.
        assert double.closed == [_KEY_PARAMS]
        assert double.order[-1] == ("close", _KEY_PARAMS)
        assert double.order[-2] == ("read_indexed", _KEY_PARAMS)
        #  And the shared block now holds the CLOSE's pair - which is precisely why the
        #  exception could not have been built from it.
        assert state.file_access.fs_reply == 0
        assert state.file_access.we_error == 0


def test_a_successful_key_one_read_closes_and_returns_without_raising() -> None:
    """The control: the same route with a read that succeeds.

    Without this, the test above would pass just as well if the boundary raised
    unconditionally - and a boundary that always raised would make every route unusable
    while the failure test stayed green. The success path is therefore asserted whole: no
    exception, the file closed exactly once, and the run date pinned onto the record from
    the controlled clock rather than from anywhere else (R-6).
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.irs_menu_state()
        system_record = args._declared_system_record()
        pinned = args.resolve_clock(_RUN_DATE_TEXT)

        args.aa010_get_system_recs(
            system_record, state, args.FileDefs(), _namespace(args), pinned, env=_CONTRACT
        )

        assert double.closed == [_KEY_PARAMS]
        assert system_record.system_data_block.run_date == pinned.run_date
        #  A non-zero binary run date, so the assertion above is not comparing two zeroes.
        assert pinned.run_date > 0

        #  ⭐ AND THE SUCCESS PATH CONTINUES PAST THE READ. `_apply_cli_pins` binds the
        #  six connection parameters onto the record it has just read
        #  [copybooks/wssystem.cob:L137-L144], which is why an absent contract fails HERE
        #  rather than at the read - the status-code tests in section 4 drive that half.
        #  Four of the six are asserted by value; the password is not, because a test
        #  that printed one would be a test that could leak one.
        assert system_record.system_data_block.rdbms_host.rstrip() == "db.internal"
        assert system_record.system_data_block.rdbms_user.rstrip() == "acas"
        assert system_record.system_data_block.rdbms_db_name.rstrip() == "ACASDB"
        assert system_record.system_data_block.rdbms_port.rstrip() == "3306"


def test_the_irs_menu_state_reads_key_one_and_nothing_else() -> None:
    """`irs/irs.cbl` reads ONE system record; the General menu reads three.

    The IRS menu state carries neither a totals record nor a defaults record
    [acas_posting/cli/args.py, `irs_menu_state`], and the two reads at keys 4 and 2 are
    guarded on their presence - so the IRS route touches key 1 only. A route that read
    keys 2 and 4 anyway would issue two reads against records the IRS subsystem does not
    have, and the extra traffic would appear in the handler's own log.

    ASSERTED AS THE ORDERED KEY SEQUENCE, not as a count, because the ORDER is the frozen
    menu's: open on key 1, then the other records, then BACK to key 1 for the read that
    matters, then close.
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.irs_menu_state()
        assert state.system_record_4 is None
        assert state.default_record is None

        args.aa010_get_system_recs(
            args._declared_system_record(),
            state,
            args.FileDefs(),
            _namespace(args),
            args.resolve_clock(_RUN_DATE_TEXT),
            env=_CONTRACT,
        )

        assert double.order == [
            ("open_input", _KEY_PARAMS),
            ("read_indexed", _KEY_PARAMS),
            ("close", _KEY_PARAMS),
        ]


def test_the_general_menu_state_reads_the_totals_and_defaults_records_first() -> None:
    """Keys 4 and 2 are read BEFORE the key-1 read the dispatch depends on.

    `general/general.cbl` reads the period totals and the defaults as well
    [general/general.cbl:L398-L410], and the order matters for one concrete reason: the
    handler has ONE record buffer that four bridges reinterpret
    [common/acas000.cbl:L311], so the key-1 read has to come LAST or the parameter record
    would be overwritten by whichever record was read after it.

    THE SALES AND PURCHASE STATE reads the totals but not the defaults, which is the
    third shape and is asserted in the same test so the three cannot drift apart.
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.general_menu_state()
        assert state.system_record_4 is not None
        assert state.default_record is not None

        args.aa010_get_system_recs(
            args._declared_system_record(),
            state,
            args.FileDefs(),
            _namespace(args),
            args.resolve_clock(_RUN_DATE_TEXT),
            env=_CONTRACT,
        )

        assert double.order == [
            ("open_input", _KEY_PARAMS),
            ("read_indexed", _KEY_TOTALS),
            ("read_indexed", _KEY_DEFAULTS),
            ("read_indexed", _KEY_PARAMS),
            ("close", _KEY_PARAMS),
        ]

    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.slpl_menu_state()
        assert state.system_record_4 is not None
        assert state.default_record is None

        args.aa010_get_system_recs(
            args._declared_system_record(),
            state,
            args.FileDefs(),
            _namespace(args),
            args.resolve_clock(_RUN_DATE_TEXT),
            env=_CONTRACT,
        )

        assert double.order == [
            ("open_input", _KEY_PARAMS),
            ("read_indexed", _KEY_TOTALS),
            ("read_indexed", _KEY_PARAMS),
            ("close", _KEY_PARAMS),
        ]


def test_the_menu_state_selects_the_vocabulary_its_frozen_menu_copies() -> None:
    """⭐ ONE FIELD DECIDES WHICH FACADE PARAGRAPHS RUN, and it is not cosmetic.

    `irs/irs.cbl` copies [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob] and performs
    `acas000-open-Input` [irs/irs.cbl:L499]; the General, Sales and Purchase menus copy
    [copybooks/Proc-ACAS-FH-Calls.cob] and perform `System-Open-Input`. The IRS
    convention's open family carries a per-handler error check that can end the menu
    program outright, and the entity-named one has no such paragraph at all - so the two
    vocabularies differ in DISPOSITION and not only in name.

    Asserted through the shipped selector rather than by inspecting the constants, and
    with the copybook each triple names, because that name is the traceability claim
    (R-5).
    """
    with _shipped("acas_posting.cli.args") as (args,):
        irs = args._system_verbs(args.irs_menu_state())
        general = args._system_verbs(args.general_menu_state())
        slpl = args._system_verbs(args.slpl_menu_state())

        assert irs.copybook == "copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob"
        assert irs.paragraphs.startswith("acas000-")
        assert general.copybook == "copybooks/Proc-ACAS-FH-Calls.cob"
        assert general.paragraphs.startswith("System-")
        #  Sales and Purchase use the same vocabulary as General - the same triple
        #  object, so they cannot diverge.
        assert slpl == general
        assert irs != general
        #  And the flag that selects it is the menu state's own.
        assert args.irs_menu_state().handler_named_verbs is True
        assert args.general_menu_state().handler_named_verbs is False
        assert args.slpl_menu_state().handler_named_verbs is False


# ---------------------------------------------------------------------------
#  2.  THE POSTING CYCLE'S TWO SHORT-CIRCUITS
# ---------------------------------------------------------------------------


class _ProgramDouble:
    """One of the three General Ledger programs, recording that it was dispatched.

    Attributes:
        dispatched: Appended to on every `run`.
    """

    def __init__(
        self, name: str, log: list[str], *, term_code: int | None = None
    ) -> None:
        self._name = name
        self._log = log
        self._term_code = term_code

    def run(
        self,
        ws_calling_data: Any,
        system_record: Any,
        to_day: str,
        file_defs: Any,
        /,
        *,
        work_files: Any = None,
    ) -> Any:
        self._log.append(self._name)
        if self._term_code is not None:
            #  `move <n> to ws-term-code` - what a program does to report a
            #  disposition to the menu [copybooks/wscall.cob:L10].
            ws_calling_data.ws_term_code = self._term_code
        return work_files


@contextlib.contextmanager
def _programs(
    cycle: types.ModuleType, log: list[str], *, term_codes: dict[str, int]
) -> Iterator[None]:
    """Replace the three program modules `load08` dispatches, then restore them.

    The module-global names are the seam, exactly as they are for the program modules'
    `facade`: `load08` names `gl070_transaction_pre_process` and its two siblings, and a
    `CALL` in the frozen menu resolves by name at run time too.

    Args:
        cycle: The shipped `cli.gl_post_cycle`.
        log: The list every dispatch appends its program id to.
        term_codes: Program id to the term code that program reports, if any.

    Yields:
        None, for the duration.
    """
    originals = {
        "gl070_transaction_pre_process": cycle.gl070_transaction_pre_process,
        "gl071_batch_sort": cycle.gl071_batch_sort,
        "gl072_transaction_update": cycle.gl072_transaction_update,
    }
    identifiers = {
        "gl070_transaction_pre_process": "gl070",
        "gl071_batch_sort": "gl071",
        "gl072_transaction_update": "gl072",
    }
    try:
        for attribute, program_id in identifiers.items():
            setattr(
                cycle,
                attribute,
                _ProgramDouble(program_id, log, term_code=term_codes.get(program_id)),
            )
        yield
    finally:
        for attribute, original in originals.items():
            setattr(cycle, attribute, original)


def _gl_linkage(args: types.ModuleType) -> Any:
    """The four-parameter General Ledger linkage, built without a database.

    `bind_gl_linkage` resolves a connection contract, so it is not used here: what these
    tests are about is the dispatch sequence, and the linkage is a named tuple of four
    records.

    Args:
        args: The shipped `cli.args`.

    Returns:
        The linkage.
    """
    return args.GlLinkage(
        args._declared_calling_data(),
        args._declared_system_record(),
        _RUN_DATE_TEXT,
        args.FileDefs(),
    )


def test_all_three_phases_run_when_no_program_reports_a_disposition() -> None:
    """`load08` dispatches gl070, gl071 and gl072 in that order.

    THE CONTROL for the two short-circuit tests, and a claim in its own right: the order
    is load-bearing because `gl072` locates each posting's nominal account by SEQUENTIAL
    read [general/gl072.cbl:L410-L412] and therefore depends on `gl071` having emitted
    the stream in nominal-key order.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        linkage = _gl_linkage(args)
        with _programs(cycle, dispatched, term_codes={}):
            cycle.load08(linkage, menu_state=args.general_menu_state())

        assert dispatched == ["gl070", "gl071", "gl072"]
        assert linkage.calling_data.ws_term_code == 0


def test_the_abort_term_code_stops_the_cycle_before_gl071_and_gl072() -> None:
    """`if ws-term-code = 5 ... go to menu` [general/general.cbl:L810-L811].

    `gl070` raises 5 when it finds a batch left open [general/gl070.cbl:L289], and the
    frozen menu then returns WITHOUT dispatching the sort or the update. The database
    effect of the abort is therefore THE ABSENCE of everything those two would have
    written, which is Agent Action Plan section 0.6.5's second rejection class - and it
    only holds if the gate is a hard stop rather than a warning.

    ⭐ FIVE IS NOT A SERIOUS ERROR. `is_serious_error` tests ABOVE seven
    [general/general.cbl:L720], so the abort takes its own arm and not the error arm -
    asserted here by the term code surviving as 5 rather than being escalated.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        linkage = _gl_linkage(args)
        with _programs(cycle, dispatched, term_codes={"gl070": _ABORT_TERM_CODE}):
            cycle.load08(linkage, menu_state=args.general_menu_state())

        assert dispatched == ["gl070"]
        assert linkage.calling_data.ws_term_code == _ABORT_TERM_CODE
        assert args.is_serious_error(_ABORT_TERM_CODE) is False
        #  And the process status is the term code itself, so a shell script can tell an
        #  abort from a clean run [copybooks/wscall.cob:L10].
        assert args.exit_status_for(_ABORT_TERM_CODE) == _ABORT_TERM_CODE


def test_a_serious_error_from_gl071_stops_the_cycle_before_gl072() -> None:
    """⭐⭐ THE SHORT-CIRCUIT THAT PREVENTS SILENT MISPOSTING.

    `load00` tests `if ws-term-code > 7` after every dispatch
    [general/general.cbl:L720-L721], and `load08` returns as soon as one reports it. The
    consequence of getting this wrong is the worst kind in this codebase: `gl072` finds
    each posting's account with a SEQUENTIAL read [general/gl072.cbl:L410-L412], so
    running it after a FAILED sort posts to whatever account the unsorted stream happens
    to reach - with no error, no diagnostic and no way to tell from the tables that
    anything went wrong.

    THE SYSTEM RECORDS ARE STILL PERSISTED on the way out, because `load00`'s error arm
    performs the same `overrewrite` the menu's quit key does - so a failed cycle does not
    lose the parameter record. Asserted through a recorder rather than by writing to a
    database.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        persisted: list[object] = []
        original_overrewrite = args.overrewrite
        args.overrewrite = lambda *arguments, **keywords: persisted.append(arguments)
        try:
            linkage = _gl_linkage(args)
            with _programs(
                cycle, dispatched, term_codes={"gl071": _SERIOUS_THRESHOLD + 1}
            ):
                cycle.load08(linkage, menu_state=args.general_menu_state())
        finally:
            args.overrewrite = original_overrewrite

        assert dispatched == ["gl070", "gl071"]
        assert "gl072" not in dispatched
        assert linkage.calling_data.ws_term_code == _SERIOUS_THRESHOLD + 1
        assert args.is_serious_error(linkage.calling_data.ws_term_code) is True
        #  Exactly one persist, from `load00`'s error arm.
        assert len(persisted) == 1


def test_a_serious_error_from_gl070_stops_the_cycle_before_gl071() -> None:
    """The same gate at the FIRST dispatch, so the sort never runs either.

    `load08` checks the disposition after each of its two guarded dispatches, and a
    migration that checked only after the second would run `gl071` over a work file
    `gl070` had abandoned. Asserted separately because the two call sites are separate
    statements.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        persisted: list[object] = []
        original_overrewrite = args.overrewrite
        args.overrewrite = lambda *arguments, **keywords: persisted.append(arguments)
        try:
            linkage = _gl_linkage(args)
            with _programs(cycle, dispatched, term_codes={"gl070": 99}):
                cycle.load08(linkage, menu_state=args.general_menu_state())
        finally:
            args.overrewrite = original_overrewrite

        assert dispatched == ["gl070"]
        assert len(persisted) == 1
        assert args.exit_status_for(99) == 99


# ---------------------------------------------------------------------------
#  3.  THE REQUIRED OPTIONS - AN OMISSION IS A USAGE ERROR, NOT A DEFAULT
# ---------------------------------------------------------------------------


def test_the_general_route_refuses_to_run_without_a_run_date() -> None:
    """⭐ THERE IS NO DEFAULT RUN DATE, and that is rule R-6 made operational.

    Every date the migrated cycle uses arrives through linkage
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80 is the ONE clock read in the whole call
    chain, and it lives in the menu shell]. If the CLI defaulted the run date to today,
    two runs of the same scenario would write different rows and the determinism
    requirement would be unenforceable - so `--run-date` is required and its omission is
    a usage error.

    ⛔ NOT AN ADDED VALIDATION (R-3). The frozen menu obtains the date before it
    dispatches anything [general/general.cbl:L371]; requiring it at the boundary is where
    that acquisition went, not a new rule.

    NOTHING IS DISPATCHED: the three program doubles record every call, and the list is
    empty, so the refusal happens during parsing and before any program is entered.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        with _programs(cycle, dispatched, term_codes={}):
            with pytest.raises(SystemExit) as exited:
                cycle.main([])

        assert exited.value.code == _USAGE_ERROR_STATUS
        assert dispatched == []

        #  And the option IS declared required on the parser, which is what makes the
        #  status a usage error rather than a later failure.
        required = [
            action.option_strings
            for action in cycle._build_parser()._actions
            if action.required
        ]
        assert ["--run-date"] in required


def test_the_irs_route_requires_an_explicit_clear_posting_file_answer() -> None:
    """⭐⭐ ONE ANSWER DELETES EVERY ROW OF THE TRANSFER TABLE, so neither is defaulted.

    `irs030`'s end-of-job question [irs/irs030.cbl:L1715-L1724] decides whether the
    transfer file is cleared, and answering yes performs an open-output which for this
    handler is a MASS DELETE [common/acas008.cbl:L313-L319]. Agent Action Plan section
    0.3.4 promotes exactly this kind of prompt to a parameter *"with the COBOL default
    preserved"* - and the frozen program HAS NO DEFAULT: the `[Y]` in the prompt is
    display text, the accept carries no `WITH UPDATE`, and any reply that is neither Y nor
    N re-prompts, so a bare Enter cannot leave the loop.

    So the migrated route requires one of the two switches, and omitting both is a usage
    error rather than an implied yes. A defaulted yes would empty one of the compared
    tables on every run that forgot to say otherwise.
    """
    with _shipped("acas_posting.cli.irs_post", "acas_posting.cli.args") as (
        route,
        args,
    ):
        with pytest.raises(SystemExit) as exited:
            route.main(["--run-date", _RUN_DATE_TEXT])

        assert exited.value.code == _USAGE_ERROR_STATUS

        required = [
            action.option_strings
            for action in route._build_parser()._actions
            if action.required
        ]
        #  Both the run date and the destructive answer are required, and the switch is
        #  a paired boolean so that saying no is as explicit as saying yes.
        assert ["--run-date"] in required
        assert any("--clear-posting-file" in options for options in required)


def test_the_help_text_names_the_deletion_rather_than_burying_it() -> None:
    """The destructive answer says so, in the help an operator reads.

    Not a style assertion: the switch's help is the only place a run's most destructive
    input is explained, and the table it empties is named there by its own identifier so
    that an operator can check the scenario definition against it.
    """
    with _shipped("acas_posting.cli.irs_post") as (route,):
        help_text = route._build_parser().format_help()

        assert "PSIRSPOST-REC" in help_text
        assert "irs/irs030.cbl:L1716" in help_text
        assert "--no-clear-posting-file" in help_text


# ---------------------------------------------------------------------------
#  4.  THE CONFIGURATION CONTRACT'S STATUS CODES
# ---------------------------------------------------------------------------


def test_an_absent_contract_raises_the_frozen_no_source_code() -> None:
    """`move 8 to LK-Return` [common/acas-get-params.cbl:L174-L178].

    The frozen parameter reader answers 8 when there is no source to read, and the
    migrated resolver answers 8 when not one of the six `ACAS_DB_*` variables is set - the
    same refusal over the transport this migration uses. The environment is passed in as
    an empty mapping rather than manipulated, so the test does not depend on the host's own
    variables and cannot leak one.

    ⭐ THE MESSAGE NAMES THE SIX VARIABLES, because the operator's next action is to set
    them; and it carries NO VALUE, because a value could be a password.
    """
    with _shipped("acas_posting.cli.args") as (cli_args,):
        assert cli_args.RDB_RETURN_NO_SOURCE == 8
        assert cli_args.RDB_RETURN_OK == 0

        with pytest.raises(cli_args.RdbmsParamError) as raised:
            cli_args.resolve_rdbms_params({})

        assert raised.value.return_code == cli_args.RDB_RETURN_NO_SOURCE
        message = str(raised.value)
        for variable in (
            "ACAS_DB_HOST",
            "ACAS_DB_USER",
            "ACAS_DB_PASSWORD",
            "ACAS_DB_NAME",
            "ACAS_DB_PORT",
            "ACAS_DB_SOCKET",
        ):
            assert variable in message


def test_a_present_contract_resolves_as_the_frozen_reader_would() -> None:
    """The control, and the frozen transformation with it.

    `UNSTRING ... delimited by "=" or ":" or space`
    [common/acas-get-params.cbl:L193-L199] means a value is CUT AT THE FIRST DELIMITER,
    and every bridge then extracts its own item `delimited by space`. So a value with a
    space in it does not fail - it is truncated, exactly as the frozen reader truncates
    it. Reproduced rather than rejected (R-3, R-4): a validation here would refuse a
    deployment the compiled system accepts.
    """
    with _shipped("acas_posting.cli.args") as (cli_args,):
        resolved = cli_args.resolve_rdbms_params(
            {
                "ACAS_DB_HOST": "db.internal",
                "ACAS_DB_USER": "acas",
                "ACAS_DB_PASSWORD": "unused-by-this-test",
                "ACAS_DB_NAME": "ACASDB",
                "ACAS_DB_PORT": "3306",
                "ACAS_DB_SOCKET": "",
            }
        )

        assert resolved.host == "db.internal"
        assert resolved.user == "acas"
        assert resolved.database == "ACASDB"
        assert resolved.port == "3306"
        #  Only the socket may be empty - it means connect over TCP.
        assert resolved.socket == ""

        #  The frozen cut, asserted on the host rather than on the credential.
        cut = cli_args.resolve_rdbms_params(
            {"ACAS_DB_HOST": "db.internal extra words"}
        )
        assert cut.host == "db.internal"


def test_the_malformed_code_is_published_and_surfaced_by_the_boundary() -> None:
    """⚠ 1 IS PART OF THE FROZEN SET, AND THE SIX-FIELD RESOLVER NEVER RAISES IT.

    [common/acas-get-params.cbl:L37-L42] publishes four codes, of which
    `resolve_rdbms_params` can express one: 8, "no source". The malformed code, 1,
    belongs to the frozen reader's `if WS-RDB-Equal not = "="` test
    [common/acas-get-params.cbl:L200-L203] - a keyword terminator that is neither `=`
    nor `:` - and an environment variable HAS no keyword terminator, so the condition
    cannot arise over this transport for the six CONNECTION parameters.

    IT IS RAISED BY THE DEPLOYMENT SETTINGS BESIDE THEM, which have no frozen
    counterpart at all: an unrecognised transport flag [`read_declared_flag`] and a
    malformed driver deadline [`_optional_seconds`] both refuse with 1 rather than
    guessing. Those paths have their own tests in section 8 below.

    WHAT THIS TEST STATES: the constant is 1, and the boundary surfaces whatever code
    an error carries, so each refusal reaches a caller as its own status without
    another change.
    """
    with _shipped("acas_posting.cli.args") as (args,):
        assert args.RDB_RETURN_MALFORMED == 1

        #  The boundary surfaces the code the error carries, whichever it is.
        malformed = args.RdbmsParamError(
            args.RDB_RETURN_MALFORMED,
            "a keyword terminator that is neither = nor : - the frozen L200-L203 case",
        )
        absent = args.RdbmsParamError(args.RDB_RETURN_NO_SOURCE, "no source")
        assert args.boundary_exit_status(malformed) == 1
        assert args.boundary_exit_status(absent) == 8
        #  An error with no code at all falls back to the smallest status the frozen menu
        #  treats as serious, DERIVED rather than typed [general/general.cbl:L720].
        assert args.boundary_exit_status(RuntimeError("no code")) == (
            args.SERIOUS_ERROR_THRESHOLD + 1
        )


def test_a_configuration_failure_is_reported_as_its_own_status_and_runs_nothing() -> None:
    """`report_configuration_failure` returns the code, and the route returns it too.

    THE ROUTE IS DRIVEN, not the helper alone: `gl_post_cycle.main` catches the binder's
    error and returns the status, so an operator's shell sees 8 for "not configured". The
    binder is replaced with one that raises, which is deterministic - the alternative,
    emptying the process environment, would make the test depend on the host.

    NOTHING WAS RUN: the three program doubles record every dispatch and the list is
    empty. The error is raised while the six connection fields are still being resolved,
    before any database is contacted or any program entered, so a run that reports this
    has changed no table.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        original_bind = args.bind_gl_linkage

        def refuse(*_arguments: object, **_keywords: object) -> object:
            raise args.RdbmsParamError(
                args.RDB_RETURN_NO_SOURCE,
                "no database connection contract is present in the environment",
            )

        args.bind_gl_linkage = refuse
        try:
            with _programs(cycle, dispatched, term_codes={}):
                status = cycle.main(["--run-date", _RUN_DATE_TEXT])
        finally:
            args.bind_gl_linkage = original_bind

        assert status == args.RDB_RETURN_NO_SOURCE
        assert dispatched == []


# ---------------------------------------------------------------------------
#  5.  THE FACADE'S `goback`, ABSORBED AT THE IRS BOUNDARY
# ---------------------------------------------------------------------------


def test_the_irs_route_absorbs_the_facade_goback_as_a_normal_return() -> None:
    """`goback` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] ends the MENU program.

    ⭐ WHY THIS IS REPRODUCED RATHER THAN CAUGHT DEFENSIVELY (R-4). The IRS facade
    convention wraps each handler call in a per-handler error check, and on an
    unrecoverable open failure that check RETURNS FROM THE PROGRAM outright. `irs/irs.cbl`
    copies that same copybook [irs/irs.cbl:L1035], so the `goback` is a disposition of the
    menu program - and the migrated route reproduces it by absorbing `FacadeGoback` and
    returning zero, which is what a `goback` from a menu program yields.

    The General, Sales and Purchase convention has NO such paragraph
    [copybooks/Proc-ACAS-FH-Calls.cob contains none], so their routes do not absorb it -
    a behavioural difference between the two vocabularies rather than a naming one.

    THE NAME PATCHED HERE IS `bind_irs_route`, AND THAT MATTERS. The route binds ONCE,
    through `args.bind_irs_route`, which returns the linkage AND the snapshot its single
    `zz090` pass captured; `args.bind_irs_linkage` is the thin caller that keeps the
    three-operand shape available and delegates to it. Patching the delegate would leave
    the real binder in the route's path, so the run would fail resolving the deployment
    contract and this test would be measuring the wrong boundary.
    """
    with _shipped(
        "acas_posting.cli.irs_post", "acas_posting.cli.args", "acas_posting.dal.facade"
    ) as (route, args, facade):
        original_bind = args.bind_irs_route

        def goback(*_arguments: object, **_keywords: object) -> object:
            raise facade.FacadeGoback(
                "acas000 reported an unrecoverable open failure"
            )

        args.bind_irs_route = goback
        try:
            status = route.main(
                ["--run-date", _RUN_DATE_TEXT, "--no-clear-posting-file"]
            )
        finally:
            args.bind_irs_route = original_bind

        assert status == 0


def test_an_unexpected_failure_at_the_irs_boundary_is_not_absorbed() -> None:
    """Only the two frozen dispositions are handled; everything else propagates.

    Without this, the test above would be indistinguishable from a bare `except
    Exception` - and a boundary that swallowed every failure would report success for a
    run that did nothing. The route handles `FacadeGoback` because it has a frozen
    counterpart and `RdbmsParamError` because it carries a frozen return code; a
    `RuntimeError` has neither, so it reaches the caller.
    """
    with _shipped("acas_posting.cli.irs_post", "acas_posting.cli.args") as (
        route,
        args,
    ):
        original_bind = args.bind_irs_route
        marker = RuntimeError("not a frozen disposition")

        def explode(*_arguments: object, **_keywords: object) -> object:
            raise marker

        args.bind_irs_route = explode
        try:
            with pytest.raises(RuntimeError) as raised:
                route.main(
                    ["--run-date", _RUN_DATE_TEXT, "--no-clear-posting-file"]
                )
        finally:
            args.bind_irs_route = original_bind

        assert raised.value is marker


# ---------------------------------------------------------------------------
#  6.  THE END-OF-CYCLE ROUTE - `load09`, AND ITS THREE PROMOTED ANSWERS
#
#      `general/general.cbl` dispatches `gl080` from `load09.`
#      [general/general.cbl:L817-L820] through the same shared `load00.` block
#      [general/general.cbl:L711-L722]. The route carries the three interactive
#      answers Agent Action Plan section 0.3.4 promotes to parameters, and TWO OF THEM
#      DECIDE WHETHER THE DATABASE IS WRITTEN AT ALL - which is why the route refuses
#      to run until both have been stated.
# ---------------------------------------------------------------------------


class _Gl080Double:
    """`gl080`, recording the linkage and the three promoted answers it received.

    Attributes:
        calls: One entry per dispatch, as the keyword answers it was handed.
    """

    def __init__(self, log: list[dict[str, object]], *, term_code: int = 0) -> None:
        self._log = log
        self._term_code = term_code

    def run(
        self,
        ws_calling_data: Any,
        system_record: Any,
        to_day: str,
        file_defs: Any,
        /,
        *,
        run_confirmed: bool = True,
        disk_change_option: int = 0,
        archive_path_override: str | None = None,
        dal_options: Any = None,
    ) -> None:
        self._log.append(
            {
                "called": ws_calling_data.ws_called.strip(),
                "to_day": to_day,
                "run_confirmed": run_confirmed,
                "disk_change_option": disk_change_option,
                "archive_path_override": archive_path_override,
            }
        )
        ws_calling_data.ws_term_code = self._term_code


def test_the_end_of_cycle_route_hands_gl080_the_three_promoted_answers() -> None:
    """`load09` -> `load00` -> `gl080.run` [general/general.cbl:L817-L820].

    THE ROUTE IS DRIVEN, and what it forwards is asserted item by item, because each of
    the three answers changes what the program writes:

      `run_confirmed`          False returns before a single write
                               [general/gl080.cbl:L299-L302]
      `disk_change_option`     9 suppresses archiving AND end-of-period through the
                               shared `a` [general/gl080.cbl:L545], [general/gl080.cbl:L324]
      `archive_path_override`  moves where the flat archive rows are written
                               [general/gl080.cbl:L555]

    The program id and the run date are asserted with them: `set_called` moves the
    program name into `WS-Called` [copybooks/wscall.cob:L7] before the dispatch, and the
    run date is the text date the CLI pinned - never a clock (R-6).
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        original = route.gl080
        route.gl080 = _Gl080Double(dispatched)
        try:
            linkage = _gl_linkage(args)
            term_code = route.load09(
                linkage,
                menu_state=args.general_menu_state(),
                run_confirmed=False,
                disk_change_option=9,
                archive_path_override="/var/spool/acas-archive.dat",
            )
        finally:
            route.gl080 = original

        assert term_code == 0
        assert dispatched == [
            {
                "called": "gl080",
                "to_day": _RUN_DATE_TEXT,
                "run_confirmed": False,
                "disk_change_option": 9,
                "archive_path_override": "/var/spool/acas-archive.dat",
            }
        ]


def test_a_serious_error_from_gl080_is_returned_and_persists_the_records() -> None:
    """`if ws-term-code > 7` [general/general.cbl:L720-L721], on the end-of-cycle route.

    `gl080` NEVER SETS A TERM CODE of its own - it returns [general/gl080.cbl:L366] where
    `gl070` raises 5 - so this arm is reached only when something below it does. It is
    asserted anyway, because `load00` is shared with the posting-cycle route and a change
    to the shared block would otherwise be caught on one route only.
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        persisted: list[object] = []
        original_program = route.gl080
        original_overrewrite = args.overrewrite
        route.gl080 = _Gl080Double(dispatched, term_code=_SERIOUS_THRESHOLD + 1)
        args.overrewrite = lambda *arguments, **keywords: persisted.append(arguments)
        try:
            linkage = _gl_linkage(args)
            term_code = route.load09(
                linkage,
                menu_state=args.general_menu_state(),
                run_confirmed=True,
                disk_change_option=0,
                archive_path_override=None,
            )
        finally:
            route.gl080 = original_program
            args.overrewrite = original_overrewrite

        assert term_code == _SERIOUS_THRESHOLD + 1
        assert args.exit_status_for(term_code) == term_code
        assert len(persisted) == 1


@pytest.mark.parametrize(
    "argv",
    [
        #  Neither destructive answer stated.
        ["--run-date", _RUN_DATE_TEXT],
        #  The confirm stated, the disk-change option not.
        ["--run-date", _RUN_DATE_TEXT, "--run-confirmed"],
        #  The disk-change option stated, the confirm not.
        ["--run-date", _RUN_DATE_TEXT, "--disk-change-option", "0"],
    ],
)
def test_the_end_of_cycle_route_refuses_until_both_answers_are_stated(
    argv: list[str],
) -> None:
    """⭐⭐ TWO ANSWERS DECIDE WHETHER POSTED TRANSACTIONS ARE DELETED.

    `--disk-change-option 0` proceeds, which deletes posted transactions, stamps every
    batch, rolls the ledger quarters over and increments the accounting cycle; 9 aborts
    and leaves the three tables as the seed left them. `--run-confirmed` decides whether
    the run happens at all. So the route requires BOTH to be stated explicitly, and an
    omission of either is argparse's usage error - status 2, indistinguishable from an
    omitted `--run-date`.

    ⛔ NOT A VALIDATION OF THE ANSWER (R-3). Both values are equally acceptable and
    neither is rejected; what is refused is SILENCE. Rejecting one of them would be a
    check the frozen program has not got, and defaulting either would answer a
    destructive question on the operator's behalf.

    NOTHING IS DISPATCHED: the double records every call and the list is empty, because
    `require_stated` runs after parsing and before anything is bound, connected or
    dispatched.
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        original = route.gl080
        route.gl080 = _Gl080Double(dispatched)
        try:
            with pytest.raises(SystemExit) as exited:
                route.main(argv)
        finally:
            route.gl080 = original

        assert exited.value.code == _USAGE_ERROR_STATUS
        assert dispatched == []


def test_the_end_of_cycle_refusal_names_what_each_answer_decides(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The refusal quotes the consequence, so an operator is told what they are choosing.

    `require_stated` puts each requirement's sentence into the message verbatim
    [acas_posting/cli/args.py], and the two sentences name the frozen lines and the three
    tables the destructive answer reaches. Asserted on the message rather than on the
    status, because the status alone tells an operator nothing about which answer is
    missing.
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        original = route.gl080
        route.gl080 = _Gl080Double(dispatched)
        try:
            with pytest.raises(SystemExit):
                route.main(["--run-date", _RUN_DATE_TEXT])
        finally:
            route.gl080 = original

        message = capsys.readouterr().err
        assert "--run-confirmed" in message
        assert "--disk-change-option" in message
        #  The frozen locators, so the operator can read the statement being answered.
        assert "general/gl080.cbl:L295-L302" in message
        assert "general/gl080.cbl:L542-L549" in message
        #  And the three tables the proceeding answer reaches.
        for table in ("GLPOSTING-REC", "GLBATCH-REC", "GLLEDGER-REC"):
            assert table in message
        assert dispatched == []


# ---------------------------------------------------------------------------
#  MN-08 - THE PUBLIC CONTRACT HOLDS EACH NAME EXACTLY ONCE
#
#  `acas_posting.cli.args.__all__` is grouped by theme with explanatory comments, and
#  several of the menu paragraphs it publishes belong to more than one theme. A tuple is
#  not a set, so re-listing one under a second heading is a genuine duplicate in the
#  module's public contract - and an invisible one, because a duplicate in `__all__`
#  raises nothing, simply binding the name twice under `import *`. Seven names were
#  duplicated: `len(__all__)` read 72 against 65 distinct.
#
#  The module asserts this at import too. This test exists because that assert is
#  stripped under `python -O`, and because a test states the property where a reviewer
#  looks for properties.
def test_cli_args_publishes_each_public_name_once() -> None:
    """`args.__all__` holds no repeated entry, and exports nothing it lacks."""
    from acas_posting.cli import args

    names = list(args.__all__)
    repeated = sorted({name for name in names if names.count(name) > 1})
    assert not repeated, (
        f"acas_posting.cli.args.__all__ lists {len(names)} entries with only "
        f"{len(set(names))} distinct names. Repeated: {', '.join(repeated)}. "
        "A duplicate binds the name twice under `import *` and makes any count of the "
        "public surface wrong (MN-08)."
    )

    # A deduplication that dropped a name would be a silent narrowing of the public
    # surface, so every listed name must still resolve on the module.
    absent = sorted(name for name in names if not hasattr(args, name))
    assert not absent, (
        "acas_posting.cli.args.__all__ names attributes the module does not define, so "
        f"`from acas_posting.cli.args import *` would fail: {', '.join(absent)}"
    )

    # The seven names the duplication involved must still be exported - removing one
    # rather than deduplicating it would also make the count agree.
    formerly_duplicated = (
        "RDBMS_STORE_SELECTOR_DIGIT",
        "SYSTEM_FILE_KEY_DEFAULTS",
        "SYSTEM_FILE_KEY_PARAMS",
        "SYSTEM_FILE_KEY_TOTALS",
        "aa010_get_system_recs",
        "overrewrite",
        "zz095_restore_irs_system_data",
    )
    lost = sorted(name for name in formerly_duplicated if name not in names)
    assert not lost, (
        "these names were published twice and are now published zero times, which "
        f"narrows the public surface rather than tidying it: {', '.join(lost)}"
    )


def test_cli_args_import_star_binds_every_published_name() -> None:
    """`import *` succeeds and binds exactly the published set (MN-08).

    Exercises the contract the way a consumer would, so a `__all__` entry that names
    something unimportable is caught as the ImportError it would really be.
    """
    namespace: dict[str, Any] = {}
    exec("from acas_posting.cli.args import *", namespace)  # noqa: S102

    from acas_posting.cli import args

    bound = {name for name in namespace if not name.startswith("__")}
    assert bound == set(args.__all__), (
        "the names `import *` bound differ from `__all__`:\n"
        f"  only bound    : {sorted(bound - set(args.__all__))}\n"
        f"  only in __all__: {sorted(set(args.__all__) - bound)}"
    )


# ---------------------------------------------------------------------------
#  MN-05 - THE CLEAR ANSWER HAS NO DEFAULT, AND NOTHING SAYS IT DOES
#
#  `EOJ-q1` displays "Can I clear the Ledgers Posting file? [Y]"
#  [irs/irs030.cbl:L1716] and that `[Y]` looks like a default. It is not one: the accept
#  on the next line carries no `WITH UPDATE`, so the literal never reaches the field;
#  `WS-Reply pic x` is never set to "Y" anywhere in the program; and L1718-L1719 send
#  anything that is neither `Y` nor `N` back to the prompt, so a bare Enter RE-PROMPTS.
#
#  Answering `Y` reaches `acas008-Open-Output`, which for that handler DELETES EVERY ROW
#  of `PSIRSPOST-REC` [common/acas008.cbl:L313-L319]. So a default would not merely be
#  wrong, it would be the destructive answer applied to an operator who said nothing -
#  which is why the seam requires the answer, and why prose claiming otherwise is worth
#  a test rather than a correction alone. Three comment sites still claimed a `True`
#  default after the seam had stopped having one.
def test_the_clear_answer_is_required_at_both_layers() -> None:
    """Neither the program module nor the CLI can be driven without the answer."""
    import inspect

    from acas_posting.programs.irs030_posting import run

    parameter = inspect.signature(run).parameters["clear_posting_file"]
    assert parameter.default is inspect.Parameter.empty, (
        "irs030_posting.run gives clear_posting_file the default "
        f"{parameter.default!r}. The frozen prompt has no default -- the [Y] at "
        "[irs/irs030.cbl:L1716] is prompt text, the accept carries no WITH UPDATE, and "
        "L1718-L1719 re-prompt on anything but Y or N -- so a default here invents one, "
        "and answering Y deletes every row of PSIRSPOST-REC (MN-05, finding CLI-05)."
    )
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
        "clear_posting_file must stay keyword-only so a caller cannot supply the "
        "destructive answer positionally by accident."
    )


def test_no_module_claims_the_clear_answer_defaults_on() -> None:
    """No comment or docstring says clearing is on by default (MN-05).

    Read as text on purpose: the defect was prose disagreeing with the code, so the
    code assertion above cannot catch it and did not.
    """
    root = Path(__file__).resolve().parents[2]
    # Phrases that assert a live default. A sentence EXPLAINING that an earlier draft
    # had one, or that the file brief specifies one the module declines, is the
    # historical record and is not a claim about the seam - so those are exempted by
    # requiring the phrase to appear without a disclaiming neighbour on the same line.
    claims = (
        "on by default",
        "does default to `True`",
        "default is [Y]",
        "frozen default is [Y]",
        "defaults to clearing",
    )
    exempt = ("previous default", "was wrong", "invented", "brief gives", "brief also gives")

    offenders: list[str] = []
    for relative in (
        "acas_posting/cli/irs_post.py",
        "acas_posting/cli/args.py",
        "acas_posting/programs/irs030_posting.py",
    ):
        path = root / relative
        assert path.is_file(), f"a declared consumer is absent: {path}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            lowered = line.lower()
            if any(word in lowered for word in exempt):
                continue
            for claim in claims:
                if claim.lower() in lowered:
                    offenders.append(f"{relative}:{number}: {line.strip()[:92]}")
    assert not offenders, (
        "these lines claim the transfer-file clear defaults on, while the seam requires "
        "an explicit Y or N and the frozen prompt has no default at all (MN-05):\n  "
        + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------
#  8.  SEC-01 - THE CONFIGURATION-FAILURE STATUS IS AN INTEGER ON BOTH ROUTES
#
#  ⭐ THE DEFECT THIS SECTION CLOSES. `RdbmsParamError.__init__` takes
#  `(return_code: int, message: str)`. Two raise sites inside `_optional_seconds`
#  passed them the other way round, so for a malformed `ACAS_DB_CONNECT_TIMEOUT`,
#  `ACAS_DB_READ_TIMEOUT` or `ACAS_DB_WRITE_TIMEOUT` the exception carried the
#  FORMATTED MESSAGE in `return_code` and the integer code in `str(error)`. Nothing
#  raised at the point of the mistake. What happened instead:
#
#    * `report_configuration_failure` returned `error.return_code` - the string -
#      as the route's status. Run directly, `python -m acas_posting.cli.<route>`
#      handed that string to `SystemExit`, which prints it verbatim, so the
#      "status" became a sentence and the shell saw 1 (CWE-704).
#    * Run through the router, `__main__` applied `args.is_serious_error(term_code)`
#      - `term_code > 7` - to a `str` and raised `TypeError`, whose traceback
#      discloses installation paths and internals (CWE-209).
#    * Both messages interpolated the raw value with `{raw!r}`, and these three
#      variables are read from the same transport as `ACAS_DB_PASSWORD`, so a value
#      pasted into the wrong variable reached the log (CWE-532).
#
#  ⛔ NO ACCOUNTING BEHAVIOUR IS IN SCOPE HERE. Every assertion below is about the
#  DEPLOYMENT boundary - the three driver deadlines and the transport flags have no
#  frozen counterpart at all, and are read before any statement with a COBOL
#  counterpart runs (rules R-3, R-6).
# ---------------------------------------------------------------------------


_TIMEOUT_VARIABLES: Final[tuple[str, ...]] = (
    "ACAS_DB_CONNECT_TIMEOUT",
    "ACAS_DB_READ_TIMEOUT",
    "ACAS_DB_WRITE_TIMEOUT",
)

#: Malformed values, each chosen to be recognisable if it is ever echoed. The two
#: numeric ones are out of range rather than unparseable, so both refusal branches
#: of `_optional_seconds` are covered.
_MALFORMED_TIMEOUTS: Final[tuple[str, ...]] = (
    "abc-XYZ",
    "s3cr3t-Passw0rd",
    "1 2",
    "-77771",
    "918273645",
)


def test_every_rdbms_param_error_carries_an_integer_return_code() -> None:
    """The exception's fields are `(int, str)` at every raise site in the module.

    Driven rather than read: each of the three refusal paths the module can reach
    over this transport is provoked, and the constructed exception is inspected. A
    reversed argument pair puts a `str` in `return_code`, which is exactly what
    `boundary_exit_status` and the router then mishandle.
    """
    with _shipped("acas_posting.cli.args") as (cli_args,):
        provoked: list[cli_args.RdbmsParamError] = []

        #  1. no source at all - the frozen reader's code 8.
        with pytest.raises(cli_args.RdbmsParamError) as absent:
            cli_args.resolve_rdbms_params({})
        provoked.append(absent.value)

        #  2. an unrecognised transport flag - code 1.
        with pytest.raises(cli_args.RdbmsParamError) as flag:
            cli_args.read_declared_flag(
                {"ACAS_DB_ALLOW_PLAINTEXT": "perhaps"}, "ACAS_DB_ALLOW_PLAINTEXT"
            )
        provoked.append(flag.value)

        #  3. a malformed driver deadline - code 1, and the SEC-01 site.
        for variable in _TIMEOUT_VARIABLES:
            for value in _MALFORMED_TIMEOUTS:
                with pytest.raises(cli_args.RdbmsParamError) as deadline:
                    cli_args.resolve_transport_policy(
                        {variable: value, "ACAS_DB_ALLOW_PLAINTEXT": "1"}
                    )
                provoked.append(deadline.value)

        for error in provoked:
            assert type(error.return_code) is int, (
                f"return_code is {type(error.return_code).__name__} carrying "
                f"{error.return_code!r}. RdbmsParamError takes "
                f"(return_code, message) in that order (SEC-01)."
            )
            assert error.return_code in {
                cli_args.RDB_RETURN_NO_SOURCE,
                cli_args.RDB_RETURN_MALFORMED,
            }, f"{error.return_code} is not one of the frozen codes 8 and 1."
            assert str(error) and not str(error).isdigit(), (
                f"str(error) is {str(error)!r}, which is the shape a reversed "
                f"argument pair produces: the integer code where the message "
                f"belongs (SEC-01)."
            )


def test_a_malformed_deadline_names_its_variable_and_never_its_value() -> None:
    """The refusal is diagnosable without echoing what was typed.

    These three variables arrive over the same transport as `ACAS_DB_PASSWORD`, so a
    value pasted into the wrong one must not reach a log or a traceback (CWE-532).
    The message therefore names the VARIABLE and the accepted range, which is all an
    operator needs in order to correct it.
    """
    with _shipped("acas_posting.cli.args") as (cli_args,):
        for variable in _TIMEOUT_VARIABLES:
            for value in _MALFORMED_TIMEOUTS:
                with pytest.raises(cli_args.RdbmsParamError) as raised:
                    cli_args.resolve_transport_policy(
                        {variable: value, "ACAS_DB_ALLOW_PLAINTEXT": "1"}
                    )
                message = str(raised.value)
                assert variable in message, (
                    f"the refusal for {variable}={value!r} does not name the "
                    f"variable, so an operator cannot tell which one to correct."
                )
                assert value not in message and repr(value) not in message, (
                    f"the refusal for {variable} echoes the value {value!r}: "
                    f"{message!r}. This transport also carries the password."
                )


def test_the_error_refuses_a_reversed_argument_pair() -> None:
    """A transposition fails at the raise site instead of at the process boundary.

    The annotations cannot catch it at run time, and the consequence was three
    distinct downstream failures none of which pointed at the raise. So the
    constructor refuses the pair, and the diagnosis names the order it wants.
    """
    with _shipped("acas_posting.cli.args") as (cli_args,):
        #  The declared order is accepted.
        good = cli_args.RdbmsParamError(
            cli_args.RDB_RETURN_MALFORMED, "a value-free diagnosis"
        )
        assert good.return_code == cli_args.RDB_RETURN_MALFORMED
        assert str(good) == "a value-free diagnosis"

        #  The reversed one is not, and the refusal echoes neither argument.
        with pytest.raises(TypeError) as raised:
            cli_args.RdbmsParamError(
                "a value-free diagnosis", cli_args.RDB_RETURN_MALFORMED
            )
        assert "(return_code: int, message: str)" in str(raised.value)
        assert "a value-free diagnosis" not in str(raised.value)


def test_the_configuration_boundary_cannot_return_a_non_integer_status() -> None:
    """`report_configuration_failure` resolves through the one guarded helper.

    The regression is expressed as the condition itself rather than as the shape of
    the code: an error whose `return_code` is NOT an integer must still produce an
    integer status, and it must be the same integer `boundary_exit_status` produces,
    because the router and a direct invocation read the route's value through
    different machinery and must not be able to disagree.
    """
    with _shipped("acas_posting.cli.args") as (args,):

        class _MisconstructedError(args.RdbmsParamError):
            """An error carrying a string where the frozen code belongs.

            Built by bypassing the constructor's guard, so that the BOUNDARY's own
            robustness is what this test measures rather than the guard's.
            """

            def __init__(self) -> None:
                ValueError.__init__(self, "1")
                self.return_code = "ACAS_DB_READ_TIMEOUT must be a whole number"

        broken = _MisconstructedError()
        status = args.report_configuration_failure(
            broken, logger=logging.getLogger(__name__), subject="General Ledger"
        )
        assert type(status) is int, (
            f"the boundary returned {status!r}, a "
            f"{type(status).__name__}. A route returns this value as its process "
            f"exit status and the router compares it with `> 7` (SEC-01)."
        )
        assert status == args.boundary_exit_status(broken)
        #  And the router's own predicate accepts it, which is the comparison that
        #  raised `TypeError` before.
        assert args.is_serious_error(status) in {True, False}

        #  A well-formed error still surfaces its own frozen code unchanged.
        for code in (
            args.RDB_RETURN_NO_SOURCE,
            args.RDB_RETURN_MALFORMED,
        ):
            sound = args.RdbmsParamError(code, "a value-free diagnosis")
            assert (
                args.report_configuration_failure(
                    sound, logger=logging.getLogger(__name__), subject="Sales"
                )
                == code
            )


def test_a_malformed_deadline_reaches_a_route_as_an_integer_status() -> None:
    """Direct and routed execution agree, and neither runs a program.

    The route is driven for real with a malformed `ACAS_DB_READ_TIMEOUT` in the
    environment it resolves from, TWICE: once as a direct call, the way
    `python -m acas_posting.cli.gl_post_cycle` reaches it, and once through
    `run_entry_point`, which is the single boundary both that guard and the package
    router pass through. The two statuses must be equal and both must be integers -
    the divergence SEC-01 produced was exactly here, one route printing a sentence
    as its status while the other raised `TypeError` comparing it with 7.

    The three General Ledger program modules are doubles that record every dispatch,
    and the list must stay empty on both passes: the refusal happens while the
    deployment contract is still being read, before any database is contacted or any
    program entered, so a run that reports it has changed no table.
    """
    with _shipped(
        "acas_posting.cli.gl_post_cycle",
        "acas_posting.cli.args",
    ) as (cycle, args):
        #  The router is reached with `importlib` rather than through `_shipped`,
        #  because `acas_posting.__main__` is resident for the whole session - the
        #  tier's isolation vocabulary deliberately does not evict it - so asking
        #  `_shipped` for a fresh import of it would fail its own precondition.
        package_main = importlib.import_module("acas_posting.__main__")
        dispatched: list[str] = []
        original_bind = args.bind_gl_linkage

        def refuse(*_arguments: object, **_keywords: object) -> object:
            #  Raised the way `resolve_transport_policy` raises it, from the real
            #  reader, so the test cannot drift from the module it is about.
            return args.resolve_transport_policy(
                {
                    "ACAS_DB_READ_TIMEOUT": "s3cr3t-Passw0rd",
                    "ACAS_DB_ALLOW_PLAINTEXT": "1",
                }
            )

        args.bind_gl_linkage = refuse
        try:
            with _programs(cycle, dispatched, term_codes={}):
                direct = cycle.main(["--run-date", _RUN_DATE_TEXT])
                routed = package_main.run_entry_point(
                    cycle.main,
                    ["--run-date", _RUN_DATE_TEXT],
                    command="post-cycle",
                )
        finally:
            args.bind_gl_linkage = original_bind

        for status in (direct, routed):
            assert type(status) is int
            assert status == args.RDB_RETURN_MALFORMED
            #  The router's own predicate, which raised on a `str` before.
            assert args.is_serious_error(status) is False
        assert direct == routed
        assert dispatched == []
