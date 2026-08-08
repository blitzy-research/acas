"""`gl080`'s end-of-period gate: the one `ROUNDED` divide, and what it decides.

WHAT THIS FILE LOCKS. Two entries of the anomaly register, declared ONE LINE
APART in the frozen source, and one statement pair that looks like a rounding
nicety and is not:

  * ANOMALY A-2 - the quarter subscript is computed by a `ROUNDED` divide
    [general/gl080.cbl:L328] and used as a table subscript with NO BOUNDS TEST
    [general/gl080.cbl:L345] against `occurs 4` [copybooks/wsledger.cob:L36].
  * ANOMALY A-3 - `current-quarter` [general/gl080.cbl:L346] is a COMPLETELY
    DIFFERENT notion of "which quarter" from `a`, maintained by an independent
    rotating counter [general/gl080.cbl:L355-L357]. The two can disagree, and
    the frozen program never reconciles them.
  * THE SELF-CANCELLING ROUND-TRIP GATE - `a` is rounded at
    [general/gl080.cbl:L328], multiplied straight back at
    [general/gl080.cbl:L329] with NO `ROUNDED`, and the product compared against
    the original dividend at [general/gl080.cbl:L331-L332]. That comparison
    decides whether the ENTIRE end-of-period phase runs.

THE END-OF-PERIOD BLOCK, VERBATIM from the checkout::

     322:     perform  compress-post.
     324:     if       a = 9
     325:          or  scycle <  period
     326:              go to  main-end.
     328:     divide   scycle by period giving a rounded.
     329:     multiply a  by  period  giving  y.
     331:     if       scycle not = y
     332:              go to  main-end.
     334:     add      1  to scycle.
     337:     perform  GL-Nominal-Open.
     339: loop.
     342:     perform  GL-Nominal-Read-Next.
     343:     if       fs-reply = 10
     344:              go to  loop-end.
     345:     move     ledger-balance  to  ledger-q (a).
     346:     if       current-quarter = 4
     347:              move  ledger-balance  to  ledger-last.
     348:     perform  GL-Nominal-Rewrite.
     349:     go       to loop.
     351: loop-end.
     354:     perform  GL-Nominal-Close.
     355:     add      1  to  current-quarter.
     356:     if       current-quarter = 5
     357:              move  1  to  current-quarter.
     358:     if       period = 3
     359:        and   scycle > 12
     360:              move 1 to scycle.
     361:     if       period = 13
     362:        and   scycle > 52
     363:              move 1 to scycle.

and the two receivers the block stores into, verbatim::

     181: 77  prog-name           pic x(15)  value "gl080 (3.3.00)".
     182: 77  y                   pic 99     value zero.
     183: 77  a                   pic 99     value zero.

THE HEADLINE FINDING, AND IT IS NOT THE OBVIOUS ONE. Within a single call the
round trip at L328-L329 is EXACTLY SELF-CANCELLING, so the gate at L331 is an
exact-divisibility test whose outcome the rounding direction cannot change. The
mechanism: a rounding difference moves `a` by one and therefore `y` by `period`,
so for both spellings to land back on `scycle` the two-digit receiver would have
to wrap - and the census in `test_no_pair_flips_the_same_call_gate` walks the
WHOLE declared domain of the two signed operands and finds not one pair that
gets there, while 14132 pairs leave a DIFFERENT `a`. So the `ROUNDED` keyword is
load-bearing somewhere else - and where is settled by the next paragraph.

`a` IS READ BEFORE IT IS WRITTEN, SO IT IS LIVE STATE. L324 tests `a` BEFORE
L328 assigns it, and `a` is a `77` item with `value zero` [general/gl080.cbl:
L183] in a program that ends at `goback` [general/gl080.cbl:L366] rather than
`stop run`, so what L324 reads is whatever the PREVIOUS call left behind. That
is where the rounding direction lands: `scycle = 17, period = 2` gives `a = 9`
rounded and `a = 8` truncated, and `a = 9` ARMS L324, so the ROUNDED spelling
skips the whole end-of-period phase on the FOLLOWING call and the truncating
spelling does not. `scycle = 18, period = 2` is worse: the gate PASSES, the
phase runs to completion, and it still leaves `a = 9` behind, so every later
call is skipped. Getting truncation and rounding the wrong way round here would
therefore not shift a penny - it would silently switch an entire phase on or off
one invocation later. Agent Action Plan section 0.1.1, on why truncation is the
default and rounding the annotated exception: "Getting this backwards would
corrupt essentially every posted figure."

THREE STORAGE CLASSES MEET IN ONE STATEMENT PAIR. `Scycle` and `Period` are
signed `binary-char` [copybooks/wssystem.cob:L63], [copybooks/wssystem.cob:L64]
carried on `int`; `a` and `y` are two-digit unsigned zoned `DISPLAY`
[general/gl080.cbl:L182-L183], also on `int` but with a domain of 0 through 99;
and the value the subscript then stores is `pic s9(8)v99 comp-3`
[copybooks/wsledger.cob:L36] on `decimal.Decimal`. The mixture has teeth: a
signed dividend and a signed divisor can produce a negative quotient, and the
store into `a` DROPS THE SIGN and keeps only the low-order two digits.

THE DIVISION BY ZERO IS REACHABLE. The only guard on the divisor is
`scycle < period` [general/gl080.cbl:L325], which is FALSE for every
non-negative `scycle` when `period` is zero, so L328 is reached with a zero
divisor. Nothing here guards it, converts it to a sentinel or skips it.

RULES. There is NO user rules document for this project - `review_rules` reports
that none was provided - so the binding rules are the six the Technical
Specification carries in section 0.7.2, and this file honours them as follows.

  R-1  No COBOL at runtime. This file imports `acas_posting.cobol`,
       `acas_posting.dictionary`, `pytest` and the standard library, and nothing
       else. No subprocess, no foreign-function call, no `harness` import, no
       database, no Docker and no `cobc`. It runs on a bare host.
  R-2  Zero binary floating point. Every value is `int`, `decimal.Decimal` or a
       numeric `str`. No tolerance, no approximate comparison, no `float`. The
       ambient `decimal` context is read or written in exactly one test, the
       sabotage test at the end, which restores it in a `finally`.
  R-3  Nothing is validated, added or made concurrent. THE SUBSCRIPT STAYS
       UNBOUNDED and the two notions of quarter stay unreconciled; the
       zero-divisor outcome is asserted, not prevented. Execution is sequential.
  R-4  Anomalies are reproduced, never fixed. Every reproduction site below
       carries a comment naming A-2 or A-3 and its `[general/gl080.cbl:Lnnn]`
       locator, per section 0.7.4 C-3, so that a future well-meaning correction
       fails the suite instead of passing unnoticed. Section 0.8.2, verbatim: "A
       defect reproduced is correct; a defect fixed is a failure."
  R-5  Full traceability. Every descriptor arrives either through its data
       dictionary key or through a `<path>:L<n>` locator, and every test names
       the anomaly and the source line it locks. Coverage is evidence, never a
       gate.
  R-6  Compiled behaviour is the tie-breaker. Every expected value carries a
       provenance comment. NO question in this file is unanswered any more and
       there is no `xfail` in it: `Q-19`, the last one, was measured on GnuCOBOL
       3.2.0 and is asserted below against the reading the strict `xfail` used to
       assert against, so a reversal fails by name.

THE AMBIGUITY REGISTER IDS CITED HERE, none of them invented by this file:

  Q-2   the intermediate precision of a multi-term expression, and the direction
        of a `ROUNDED` store, both carried by `acas_posting/cobol/arithmetic.py`.
        THE TWO HALVES REACHED THEIR STATUS DIFFERENTLY and this file does not
        conflate them. The DIRECTION is settled by the language: COBOL `ROUNDED`
        rounds half away from zero, and the shipped layer does. The NUMBER OF
        INTERMEDIATE DIGITS is a property of the compiler build and was settled by
        a focused probe, so `Q-2` is `RESOLVED BY ORACLE` (2026-08-07) - extended
        precision throughout, quantized ONCE at the store. The register records
        that this entry was previously wrong in BOTH directions and keeps the
        rejected readings as evidence. No figure in this file turns on the digit
        count regardless: every quotient here lands in a two-digit receiver, so
        sixty working digits and the measured default agree.
  Q-3   a signed copybook item narrowed to an unsigned host variable and an
        unsigned column, so the sign is lost AT THE BRIDGE. Carried by
        `SYSTEM-REC.CYCLEA` and `SYSTEM-REC.PERIOD` together with anomaly A-11.
        MEASURED: the bridge stores the ABSOLUTE VALUE, then bounds it by the
        receiving digit count - `-1` arrives as 1, not as 255 - so `ambiguity_refs`
        is now empty on those entries while `A-11` stays, and this file asserts
        that rather than the former open state.
  Q-5   the zoned and binary store policy - the overpunch byte values, the
        default `binary-size` and `binary-truncate` settings - measured and
        recorded in `acas_posting/cobol/usage.py`.
  Q-7   the zero divisor. MEASURED: GnuCOBOL 3.2 raises the SIZE ERROR
        condition, performs NO STORE, and the program CONTINUES with the
        receiving field unchanged. Recorded on
        `acas_posting.cobol.arithmetic.SizeErrorNoStore`, and asserted here
        rather than deferred, because a strict `xfail` on an answered question
        would itself fail.
  Q-19  what the compiled program writes when the quarter subscript runs PAST
        THE RECORD'S END. MEASURED and no longer open: occurrence 13's six
        packed bytes land at offsets 125 through 130 of a 126-byte record - four
        of them past its end, in the storage that follows - every quarter field
        and `Ledger-Last` are left unchanged, no diagnostic is printed and the
        program exits 0. So an overrunning run moves NONE of the 22 compared
        tables. The reading is asserted in
        `test_a2_an_out_of_record_subscript_stores_past_the_record_and_moves_no_column`
        and recorded on
        `acas_posting.cobol.move.UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE`.

WHAT THIS FILE DOES NOT TOUCH. `MOVE` semantics belong to `acas_posting/cobol/
move.py` and to the `MOVE`-truncation test file, so the three `move` statements
in the block - L345, L347 and the two `move 1` resets - are modelled by
recording WHICH field is written and with what value, which is the observable
A-2 and A-3 are about. The frozen COBOL, the bridges, the copybooks and
`mysql/ACASDB.sql` are read-only here and are not modified by this or any other
test (section 0.8.1).
"""

from __future__ import annotations

import dataclasses
import decimal
from decimal import Decimal
from typing import Final

import pytest

from acas_posting.cobol import arithmetic, field as cobol_field, usage as cobol_usage
from acas_posting.dictionary import loader, model

# Imports carried in with the merged group below, which was
# test_gl080_shipped_end_of_cycle.py. Only the pieces the block above did not
# already provide are listed (Agent Action Plan section 0.3.1 inventory).
import ast
import contextlib
import importlib
import inspect
import logging
import sys
import types
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import GlBatchRecord
from acas_posting.records.gl_ledger import WsLedgerRecord
from acas_posting.records.gl_posting import WsPostingRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  THE PROVENANCE CONSTANTS
#
#  Written out in full rather than assembled from fragments, so that a grep for
#  a source line finds the test that locks it (R-5).
# ---------------------------------------------------------------------------

#: `77  y  pic 99  value zero.` - the un-ROUNDED product of L329.
_Y_LOCATOR: Final[str] = "general/gl080.cbl:L182"

#: `77  a  pic 99  value zero.` - the ROUNDED quotient of L328, the L345
#: subscript, and the value L324 reads BEFORE L328 writes it.
_A_LOCATOR: Final[str] = "general/gl080.cbl:L183"

#: `05  Cyclea  binary-char.  *> 99.` [copybooks/wssystem.cob:L62]. The
#: maintainer's trailing comment says `99`; the DECLARATION is what the compiler
#: obeys, so the descriptor is a signed one-byte binary item and the comment is
#: left standing beside it, unadjudicated.
_CYCLEA_KEY: Final[str] = "SYSTEM-REC.CYCLEA"

#: `05  Scycle Redefines cyclea  binary-char.` [copybooks/wssystem.cob:L63]. A
#: REDEFINES view has no column of its own, so the dictionary keys it by its
#: COPYBOOK RECORD rather than by a table - which is exactly why the key
#: resolver below has to be defensive about the two key forms.
_SCYCLE_KEY: Final[str] = "System-Record.Scycle"

#: `05  Period  binary-char.  *> 99.` [copybooks/wssystem.cob:L64].
_PERIOD_KEY: Final[str] = "SYSTEM-REC.PERIOD"

#: `05  Current-Quarter pic 9.` [copybooks/wssystem.cob:L110] - ANOMALY A-3's
#: rotating counter, tested at [general/gl080.cbl:L346] and advanced at
#: [general/gl080.cbl:L355-L357].
_CURRENT_QUARTER_KEY: Final[str] = "SYSTEM-REC.CURRENT-QUARTER"

#: `05  Ledger-Q  pic s9(8)v99  comp-3  occurs  4.`
#: [copybooks/wsledger.cob:L36] - ANOMALY A-2's four-element table.
_LEDGER_Q_KEY: Final[str] = "WS-Ledger-Record.Ledger-Q"

#: `03  Ledger-Last  pic s9(8)v99  comp-3.` [copybooks/wsledger.cob:L29]. It
#: sits IMMEDIATELY BEFORE `Quarters` [copybooks/wsledger.cob:L30] and is the
#: same width as one occurrence, which is what makes subscript zero land on it.
_LEDGER_LAST_KEY: Final[str] = "GLLEDGER-REC.LEDGER-LAST"

#: `03  filler  pic x(50).` [copybooks/wsledger.cob:L37] - the fifty bytes that
#: follow the table and absorb occurrences 5 through 12.
_LEDGER_FILLER_KEY: Final[str] = "WS-Ledger-Record.filler#37"

#: The two records the keys above are declared in, for the fallback search.
_SYSTEM_TABLE: Final[str] = "SYSTEM-REC"
_SYSTEM_RECORD: Final[str] = "System-Record"
_LEDGER_RECORD: Final[str] = "WS-Ledger-Record"

#: An incoming `a` that is NOT 9, so the L324 guard does not pre-empt the divide.
#: Nine is the only value that guard tests [general/gl080.cbl:L324].
_A_NOT_ARMED: Final[int] = 0

#: The value L324 tests for [general/gl080.cbl:L324].
_A_ARMED: Final[int] = 9


class _DictionaryKeyUnmatched(KeyError):
    """No dictionary entry could be reached for a key this file needs.

    A `KeyError` subclass so that it reads as the lookup failure it is, and local
    to this file because it exists only to make a near-miss legible: the artifact
    keys a field either by its table and column or by its copybook record and
    field name, and a redefines view has only the second form.
    """


def _entry(
    key: str, *, table: str | None = None, record: str | None = None
) -> model.DictionaryEntry:
    """Return the dictionary entry for `key`, searching by name if it moved.

    The exact key is tried first, because that is the key this file cites and the
    one a reader can grep for. If the artifact has since keyed the same field
    differently - the table-and-column form rather than the record-and-field
    form, or a different declaration-line suffix - the field name is matched
    against the entries of the table and of the copybook record, case-folded,
    so that a rename of the KEY cannot silently pass as a missing FIELD.

    Args:
        key: The qualified entry key this file cites.
        table: The table whose entries to search on a near miss, if any.
        record: The copybook record whose entries to search on a near miss.

    Returns:
        The dictionary entry.

    Raises:
        _DictionaryKeyUnmatched: Neither the exact key nor the field name reached
            an entry.
    """
    found = loader.find_entry(key)
    if found is not None:
        return found

    wanted = key.rsplit(".", 1)[-1].split("#", 1)[0].casefold()
    pool: list[model.DictionaryEntry] = []
    if table is not None:
        pool.extend(loader.entries_for_table(table))
    if record is not None:
        pool.extend(loader.entries_for_copybook_record(record))
    for candidate in pool:
        names = {candidate.key.rsplit(".", 1)[-1].split("#", 1)[0].casefold()}
        if candidate.copybook is not None:
            names.add(candidate.copybook.name.casefold())
        if wanted in names:
            return candidate

    raise _DictionaryKeyUnmatched(
        f"the data dictionary has no entry keyed {key!r} and no field named "
        f"{wanted!r} among the entries of table {table!r} or copybook record "
        f"{record!r}. This file cites the key in a comment beside every use, so "
        "check the artifact rather than the citation: regenerate it with "
        "`python -m acas_posting.dictionary.generate --check`."
    )


def _descriptor(
    key: str, *, table: str | None = None, record: str | None = None
) -> cobol_field.FieldDescriptor:
    """Build the descriptor the dictionary holds for one field (R-5).

    Args:
        key: The qualified entry key.
        table: The table to fall back to on a near miss.
        record: The copybook record to fall back to on a near miss.

    Returns:
        The descriptor, carrying its own `dictionary_key`.
    """
    return cobol_field.FieldDescriptor.from_dictionary_key(
        _entry(key, table=table, record=record).key
    )


def _pic_99(
    *, name: str, source_locator: str, unsigned: bool = False
) -> cobol_field.FieldDescriptor:
    """Describe one of `gl080`'s two `pic 99` WORKING-STORAGE receivers.

    THESE TWO FIELDS HAVE NO DICTIONARY ENTRY, and they are the only descriptors
    in this file that do not. The generated artifact catalogues what the frozen
    COBOL DECLARES as data - the copybook record layouts, the bridge-derived
    columns and the work-file records the General Ledger programs declare in
    their own FILE SECTIONs - and a `77` item in a program's WORKING-STORAGE is
    none of those. `acas_posting/cobol/field.py` withdrew its second factory,
    `for_working_storage`, for that reason, leaving `from_dictionary_key` as the
    only factory, so a program-local item is described by constructing the frozen
    value object directly WITH A `<path>:L<n>` LOCATOR. That locator is the
    provenance invariant rule R-5 puts on the layer: a descriptor with neither a
    key nor a locator is refused outright, which
    `test_a_descriptor_without_provenance_is_refused` exercises.

    `python_storage` is stated rather than omitted because the value object
    checks it against `usage.python_storage_for(usage, scale)` for a key-less
    descriptor, so a wrong carrier here cannot pass.

    Args:
        name: The COBOL field name, verbatim - `"y"` or `"a"`.
        source_locator: The declaration's `<path>:L<n>` locator.
        unsigned: Whether to set the explicit-UNSIGNED-keyword member. Defaults
            to False, which is what `pic 99` declares: the picture carries no S
            and no UNSIGNED keyword, exactly as
            `05 Current-Quarter pic 9.` [copybooks/wssystem.cob:L110] does, and
            the dictionary describes that declaration with `signed` false and
            `unsigned` false too - asserted in
            `test_y_and_a_are_two_digit_unsigned_zoned_display_receivers`. The
            parameter exists so that the same test can prove the member records
            the KEYWORD and cannot move a stored value.

    Returns:
        The descriptor for that receiver.
    """
    return cobol_field.FieldDescriptor(
        name=name,
        usage=model.Usage.DISPLAY,
        usage_declared_at=model.UsageDeclaredAt.DEFAULT,
        picture="99",
        signed=False,
        sign_position=model.SignPosition.NONE,
        digits=2,
        integer_digits=2,
        scale=0,
        unsigned=unsigned,
        python_storage=model.CobolPythonStorage.INT,
        source_locator=source_locator,
    )


#  The five fields the block computes with, and the three the loop stores into.
_CYCLEA: Final[cobol_field.FieldDescriptor] = _descriptor(
    _CYCLEA_KEY, table=_SYSTEM_TABLE, record=_SYSTEM_RECORD
)
_SCYCLE: Final[cobol_field.FieldDescriptor] = _descriptor(
    _SCYCLE_KEY, table=_SYSTEM_TABLE, record=_SYSTEM_RECORD
)
_PERIOD: Final[cobol_field.FieldDescriptor] = _descriptor(
    _PERIOD_KEY, table=_SYSTEM_TABLE, record=_SYSTEM_RECORD
)
_CURRENT_QUARTER: Final[cobol_field.FieldDescriptor] = _descriptor(
    _CURRENT_QUARTER_KEY, table=_SYSTEM_TABLE, record=_SYSTEM_RECORD
)
_LEDGER_Q: Final[cobol_field.FieldDescriptor] = _descriptor(
    _LEDGER_Q_KEY, record=_LEDGER_RECORD
)
_LEDGER_LAST: Final[cobol_field.FieldDescriptor] = _descriptor(
    _LEDGER_LAST_KEY, table="GLLEDGER-REC", record=_LEDGER_RECORD
)
_LEDGER_FILLER: Final[cobol_field.FieldDescriptor] = _descriptor(
    _LEDGER_FILLER_KEY, record=_LEDGER_RECORD
)
_A: Final[cobol_field.FieldDescriptor] = _pic_99(
    name="a", source_locator=_A_LOCATOR
)
_Y: Final[cobol_field.FieldDescriptor] = _pic_99(
    name="y", source_locator=_Y_LOCATOR
)


# ---------------------------------------------------------------------------
#  ANOMALY A-2's BYTE MAP, DERIVED FROM THE DESCRIPTORS AND NOT TRANSCRIBED
#
#  `move ledger-balance to ledger-q (a).` [general/gl080.cbl:L345] addresses
#  BYTES, because that is what a subscript compiles to and there is no bounds
#  test to stop it. Where an out-of-range occurrence lands therefore follows from
#  the widths the copybook declares, and every number below is read off a
#  descriptor rather than typed in.
# ---------------------------------------------------------------------------

#: Bytes per occurrence of `Ledger-Q` [copybooks/wsledger.cob:L36].
_STRIDE: Final[int] = _LEDGER_Q.byte_length

#: The declared bound - `occurs 4` [copybooks/wsledger.cob:L36]. The ONLY place
#: the number four appears in this file, and it is read, not written.
_OCCURRENCES: Final[int] = _LEDGER_Q.occurs or 0

#: The trailing `filler pic x(50)` [copybooks/wsledger.cob:L37].
_TRAILING_FILLER: Final[int] = _LEDGER_FILLER.byte_length

#: The highest occurrence that still lands WHOLLY inside the record: the four
#: declared ones plus as many whole strides as the trailing filler absorbs.
#: Occurrences 5 through this bound overwrite filler that carries no MySQL
#: column, so they are silent and have no table effect; occurrence zero lands on
#: `Ledger-Last`, which IS a column. All three bands are measured - see
#: `acas_posting/cobol/move.UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE` for the readings
#: and `acas_posting/programs/gl080_end_of_cycle.py` for the reproduction.
_LAST_IN_RECORD_OCCURRENCE: Final[int] = (
    _OCCURRENCES + _TRAILING_FILLER // _STRIDE
)


def _record_byte_length() -> int:
    """Sum `WS-Ledger-Record`'s own storage out of the dictionary (R-5).

    The oracle reading that settles question Q-19 is expressed in BYTE OFFSETS
    within the record, so the record's width has to come from the layout itself or
    the assertion would only be checking one typed-in number against another. A
    `redefines` subtree is skipped because it occupies no storage of its own -
    `WS-Ledger-Key9`, the `Ledger-n`/`Ledger-s` pair and the `Ledger-Q` `occurs`
    view are all alternative views of bytes already counted
    [copybooks/wsledger.cob:L12-L37] - and a group item is skipped because its
    children carry its width.

    A SUM is order-independent, which is why this function computes only the
    total: the dictionary lists a record's column-bound fields before its
    record-only fields, so its entry order is NOT declaration order and cannot be
    used to place an item inside the record. `_QUARTERS_FIRST_BYTE` is derived
    from the tail instead.

    Returns:
        The record's total byte length.
    """
    entries = loader.entries_for_copybook_record(_LEDGER_RECORD)
    entries += loader.entries_for_table("GLLEDGER-REC")

    #  Keep the FIRST appearance of each distinct copybook item so that the table
    #  view and the record view of one field are not counted twice. The ENTRY KEY
    #  is kept beside its copybook field, because two of this record's items are
    #  both named `filler` and only the key tells them apart.
    seen: set[str] = set()
    ordered: list[tuple[str, model.CopybookField]] = []
    for entry in entries:
        copybook = entry.copybook
        if copybook is None:
            continue
        marker = f"{copybook.source}|{copybook.name}|{copybook.level}"
        if marker in seen:
            continue
        seen.add(marker)
        ordered.append((entry.key, copybook))

    total = 0
    redefined: set[str] = set()
    for key, copybook in ordered:
        if copybook.level == "01":
            continue
        #  The `redefines` test comes FIRST, and deliberately: an alternative view
        #  is frequently a GROUP - `filler redefines WS-Ledger-Nos` and `filler
        #  redefines Quarters` both are - and skipping it as a group without
        #  remembering it would let its children be counted as storage of their
        #  own. Reversing these two tests inflates the record from 126 to 156.
        if copybook.redefines is not None:
            redefined.add(copybook.name)
            continue
        if copybook.parent_group is not None and copybook.parent_group in redefined:
            continue
        if copybook.is_group:
            continue
        width = cobol_field.FieldDescriptor.from_dictionary_key(key).byte_length
        total += width * (copybook.occurs or 1)
    return total


#: `WS-Ledger-Record`'s total width, derived. The oracle read `function length`
#: of the same record back as 126, and of one occurrence as 6, which is what makes
#: the derivation and the measurement comparable at all.
_RECORD_BYTES: Final[int] = _record_byte_length()

#: The 1-based offset of `Quarters`' first byte, derived FROM THE TAIL rather than
#: from a traversal: `Quarters` is followed by exactly one item, the trailing
#: `filler pic x(50)` [copybooks/wsledger.cob:L36-L37], so the four occurrences
#: end where the filler begins. The oracle's own byte census put `Quarters` at 53
#: through 76 of 126, which this reproduces without transcribing either number.
_QUARTERS_FIRST_BYTE: Final[int] = (
    _RECORD_BYTES - _TRAILING_FILLER - _OCCURRENCES * _STRIDE + 1
)


def _last_byte_of_occurrence_in_record(occurrence: int) -> int:
    """The 1-based offset, within the record, of an occurrence's LAST byte.

    Args:
        occurrence: The subscript `a` holds at [general/gl080.cbl:L345],
            unchecked - which is the whole of anomaly A-2.

    Returns:
        Where the six stored bytes end, counted from the record's first byte. A
            value greater than the record's width is the overrun the oracle
            measured landing in the storage that follows.
    """
    return _QUARTERS_FIRST_BYTE + _first_byte_of_occurrence(occurrence) + _STRIDE - 1


def _first_byte_of_occurrence(occurrence: int) -> int:
    """Where an occurrence starts, measured from the start of `Quarters`.

    Plain linear addressing, which is what a COBOL subscript compiles to and why
    an out-of-range one is a store rather than an error.

    Args:
        occurrence: The subscript `a` holds at [general/gl080.cbl:L345]. NOT
            checked against the bound - that is the whole point of anomaly A-2.

    Returns:
        The offset of the occurrence's first byte relative to the start of
            `Quarters` [copybooks/wsledger.cob:L30]. Negative for subscripts in
            front of the table.
    """
    return (occurrence - 1) * _STRIDE


def _bytes_past_the_table(occurrence: int) -> int:
    """How far past `Quarters` an occurrence's last byte reaches.

    Args:
        occurrence: The subscript, again unchecked.

    Returns:
        The offset of the occurrence's end, measured from the END of `Quarters`
            [copybooks/wsledger.cob:L30-L34]. Zero or less means the store lands
            inside the declared table or in front of it; a positive value means it
            lands in the trailing filler or beyond.
    """
    return _first_byte_of_occurrence(occurrence) + _STRIDE - _OCCURRENCES * _STRIDE


@dataclasses.dataclass(frozen=True, slots=True)
class _Phase:
    """What one pass through [general/gl080.cbl:L324-L363] did.

    Frozen and slotted so a test cannot mutate an outcome it is asserting, and so
    two identical passes compare equal (rule R-6).

    Attributes:
        divided: Whether control reached `divide scycle by period giving a
            rounded.` [general/gl080.cbl:L328]. False when the guard at
            [general/gl080.cbl:L324-L326] transferred to `main-end`.
        a: What `a` holds on exit. The INCOMING value when the guard fired,
            because nothing wrote it; the quotient otherwise. This is the value
            the NEXT call reads at [general/gl080.cbl:L324].
        y: The product from [general/gl080.cbl:L329], or None if the divide was
            never reached.
        gate_passed: Whether `scycle` still equalled `y` at
            [general/gl080.cbl:L331], i.e. whether phase 5 ran at all.
        subscripts: The subscript used at [general/gl080.cbl:L345], once per
            account the loop read. NOT filtered and NOT bounds-checked (A-2).
        ledger_last_writes: The balances [general/gl080.cbl:L347] copied into
            `Ledger-Last`, once per account for which
            [general/gl080.cbl:L346] held (A-3).
        scycle: What `scycle` holds on exit, after
            [general/gl080.cbl:L334] and the two resets at
            [general/gl080.cbl:L358-L363].
        current_quarter: What `current-quarter` holds on exit, after
            [general/gl080.cbl:L355-L357].
    """

    divided: bool
    a: int
    y: int | None
    gate_passed: bool
    subscripts: tuple[int, ...]
    ledger_last_writes: tuple[Decimal, ...]
    scycle: int
    current_quarter: int


def _end_of_period(
    *,
    incoming_a: int,
    scycle: int,
    period: int,
    current_quarter: int = 1,
    balances: tuple[Decimal, ...] = (),
    rounded: bool = True,
) -> _Phase:
    """Transcribe [general/gl080.cbl:L324-L363], in the source's own order.

    ONE FUNCTION PER STATEMENT-SEQUENCE, with the line number against every step,
    because the sequence IS the specification: the guard reads `a`, the divide
    writes it, the multiply reads it back, the comparison decides the phase, and
    the loop uses it as a subscript. Reorder any two of those and the program
    means something else.

    ⛔ `incoming_a` IS A PARAMETER AND IS NEVER INITIALISED HERE, because the slice
    this function transcribes begins at L324 and `a` is READ there before L328
    writes it. Setting `a` to zero inside this function would make
    [general/gl080.cbl:L324] dead code and would delete the only observable the
    `ROUNDED` keyword actually moves.

    THE JUSTIFICATION THIS PARAGRAPH USED TO GIVE WAS WRONG, and it is corrected
    rather than quietly rewritten because a reader who believed it would draw the
    wrong conclusion about a second invocation. It said `77 a pic 99 value zero.`
    [general/gl080.cbl:L183] "is initialised ONCE, when the module is loaded, and
    `gl080` leaves through `goback` [general/gl080.cbl:L366], so a second call sees
    what the first left". `move zero to a.` [general/gl080.cbl:L290] refutes that:
    `a` is zeroed on EVERY entry, so no value survives a `goback` into the next
    call. What survives of the point is narrower and still the reason for the
    parameter - within ONE run, `a` carries state from `gl080a`
    [general/gl080.cbl:L386] into the gate at L324.

    WHICH INCOMING VALUES THE SHIPPED PROGRAM CAN ACTUALLY PRESENT is therefore
    just one: ZERO. L290 zeroes it, the only other writer before the gate is
    `move 1 to a` inside `gl080a`, and a `1` there means batches are outstanding and
    leaves through `main-end` at [general/gl080.cbl:L307-L313] before the gate is
    reached at all. `a = 9` is UNREACHABLE at L324. The frozen program still tests
    for it, so the branch is reproduced (R-4) and this function is how it is
    exercised - as a source-level branch rather than a reachable state. The
    conformance section at the foot of this file pins this function against the
    shipped program for the state it CAN present, so the two cannot drift.

    The three `move` statements are recorded rather than performed, for the
    reason the module docstring gives: `MOVE` semantics are `acas_posting/cobol/
    move.py`'s subject, and what A-2 and A-3 are about is WHICH field a store
    reaches, not how a picture truncates. `move 1 to ...` is put on the
    receiver's own carrier with `store`, since 1 lies inside every one of these
    receivers' domains and so cannot differ between the two spellings.

    Args:
        incoming_a: What `a` holds when the block is entered - whatever the
            previous call left, per the note above.
        scycle: `Scycle` [copybooks/wssystem.cob:L63].
        period: `Period` [copybooks/wssystem.cob:L64].
        current_quarter: `Current-Quarter` [copybooks/wssystem.cob:L110].
        balances: One `Ledger-Balance` per account the loop at
            [general/gl080.cbl:L339-L349] reads, standing in for
            `GL-Nominal-Read-Next`; the empty default is the at-end-on-the-first-
            read case. No data-access layer is reachable from this tier (R-1).
        rounded: True transcribes [general/gl080.cbl:L328] as written. False is
            the counterfactual the parity tests need in order to show what the
            keyword decides; NO in-scope statement stores this quotient
            un-ROUNDED.

    Returns:
        What the pass did.

    Raises:
        arithmetic.SizeErrorNoStore: `period` was zero and the guard at
            [general/gl080.cbl:L324-L326] did not pre-empt the divide. Left to
            propagate deliberately (R-3); see
            `test_the_zero_divisor_is_reachable_and_stores_nothing`.
    """
    #  324  if       a = 9
    #  325       or  scycle <  period
    #  326           go to  main-end.
    #  GO TO class 3 - the transfer leaves the section, so it is a return. `a` is
    #  READ HERE, BEFORE L328 WRITES IT, which is what makes it live state.
    if arithmetic.compare(incoming_a, _A_ARMED) == 0 or (
        arithmetic.compare(scycle, period) < 0
    ):
        return _Phase(
            divided=False,
            a=incoming_a,
            y=None,
            gate_passed=False,
            subscripts=(),
            ledger_last_writes=(),
            scycle=scycle,
            current_quarter=current_quarter,
        )

    #  328  divide   scycle by period giving a rounded.
    #  THE ONLY `ROUNDED` SITE IN THIS PROGRAM, and one of exactly five in the
    #  whole migrated cycle. Two signed one-byte binary operands, one two-digit
    #  unsigned zoned receiver: the quotient's sign is dropped and only its
    #  low-order two digits survive.
    a = int(arithmetic.divide_by_giving(scycle, period, _A, rounded=rounded))

    #  329  multiply a  by  period  giving  y.
    #  NO `ROUNDED`. The default truncates, and the pairing of a rounded divide
    #  with a truncating multiply is what makes L331 an exact-divisibility test.
    y = int(arithmetic.multiply_by_giving(a, period, _Y))

    #  331  if       scycle not = y
    #  332           go to  main-end.
    #  THE GATE. A numeric relation condition, so the comparison is algebraic and
    #  crosses the two storage classes by value.
    if arithmetic.compare(scycle, y) != 0:
        return _Phase(
            divided=True,
            a=a,
            y=y,
            gate_passed=False,
            subscripts=(),
            ledger_last_writes=(),
            scycle=scycle,
            current_quarter=current_quarter,
        )

    #  334  add      1  to scycle.
    #  Un-ROUNDED, into the signed `binary-char`.
    scycle = int(arithmetic.add_to(1, receiver_value=scycle, receiving=_SCYCLE))

    subscripts: list[int] = []
    ledger_last_writes: list[Decimal] = []

    #  339 loop.  342 perform GL-Nominal-Read-Next.  343-344 at end -> loop-end.
    #  The class-2 forward transfer at L344 becomes exhaustion of `balances`, and
    #  the class-1 loop-back at L349 becomes the next iteration.
    for balance in balances:
        #  345  move     ledger-balance  to  ledger-q (a).
        #  ⭐ ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345] and
        #  `occurs 4` [copybooks/wsledger.cob:L36]. `a` is the ROUNDED quotient
        #  and is used here with NO BOUNDS TEST. The subscript is RECORDED
        #  EXACTLY AS COMPUTED - not clamped, not checked, not warned about, and
        #  emphatically not turned into a Python `a - 1` index, which would send
        #  subscript zero to the LAST occurrence and correspond to nothing the
        #  compiled program does. Reproduced per R-4; DO NOT FIX.
        subscripts.append(a)

        #  346  if       current-quarter = 4
        #  347           move  ledger-balance  to  ledger-last.
        #  ⭐ ANOMALY A-3 [general/gl080.cbl:L345-L357]. ONE LINE after the
        #  subscripted store, the program consults a COMPLETELY DIFFERENT notion
        #  of "which quarter": `Current-Quarter` [copybooks/wssystem.cob:L110],
        #  advanced by its own counter at [general/gl080.cbl:L355-L357] and never
        #  compared with `a`. The two are NOT reconciled here (R-3).
        if arithmetic.compare(current_quarter, 4) == 0:
            ledger_last_writes.append(balance)

        #  348 perform GL-Nominal-Rewrite.  349 go to loop.
        #  The rewrite is the data-access layer's, unreachable from this tier.
        continue

    #  351 loop-end.  354 perform GL-Nominal-Close.
    #  355  add      1  to  current-quarter.
    current_quarter = int(
        arithmetic.add_to(
            1, receiver_value=current_quarter, receiving=_CURRENT_QUARTER
        )
    )

    #  356  if       current-quarter = 5
    #  357           move  1  to  current-quarter.
    #  A-3's rotation, and the reason the counter never leaves 1..4 even though
    #  `pic 9` [copybooks/wssystem.cob:L110] would hold 0..9.
    if arithmetic.compare(current_quarter, 5) == 0:
        current_quarter = int(arithmetic.store(1, _CURRENT_QUARTER))

    #  358  if       period = 3
    #  359     and   scycle > 12
    #  360           move 1 to scycle.
    #  An independent statement, NOT the first arm of a choice: COBOL writes no
    #  `else` here and the period test below is a second `if`.
    if arithmetic.compare(period, 3) == 0 and arithmetic.compare(scycle, 12) > 0:
        scycle = int(arithmetic.store(1, _SCYCLE))

    #  361  if       period = 13
    #  362     and   scycle > 52
    #  363           move 1 to scycle.
    if arithmetic.compare(period, 13) == 0 and arithmetic.compare(scycle, 52) > 0:
        scycle = int(arithmetic.store(1, _SCYCLE))

    #  365 main-end.  366 goback.  `a` SURVIVES THE RETURN.
    return _Phase(
        divided=True,
        a=a,
        y=y,
        gate_passed=True,
        subscripts=tuple(subscripts),
        ledger_last_writes=tuple(ledger_last_writes),
        scycle=scycle,
        current_quarter=current_quarter,
    )


# ---------------------------------------------------------------------------
#  THE FOUR RECEIVERS, AND THE THREE STORAGE CLASSES THEY SPAN
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("descriptor", "locator"),
    (
        (_CYCLEA, "copybooks/wssystem.cob:L62"),
        (_SCYCLE, "copybooks/wssystem.cob:L63"),
        (_PERIOD, "copybooks/wssystem.cob:L64"),
    ),
)
def test_scycle_cyclea_and_period_are_signed_one_byte_binary_items(
    descriptor: cobol_field.FieldDescriptor, locator: str
) -> None:
    """The three operands of [general/gl080.cbl:L325] and L328 are signed bytes.

    ANOMALY A-2 depends on this: because `Period` is SIGNED, a negative period is
    inside its declared domain, and a negative period is the only way the L325
    guard lets a quotient below one through - which is how subscript ZERO becomes
    reachable at [general/gl080.cbl:L345].

    Provenance: `binary-char` [copybooks/wssystem.cob:L62-L64] with no UNSIGNED
    keyword, so the width is one byte and the domain is a signed byte's. The
    default `binary-size` and `binary-truncate` policy behind those two figures is
    the DOCUMENTED GnuCOBOL default, transcribed into
    `acas_posting/cobol/usage.py` rather than observed - the register keeps it
    pending as question Q-5.1 and names the provisional values so that the oracle
    can confirm or overturn a stated figure.
    """
    assert descriptor.dictionary_key is not None
    assert descriptor.source_locator == locator
    assert descriptor.usage is model.Usage.BINARY_CHAR
    assert descriptor.is_binary_family is True
    assert descriptor.is_zoned_display is False
    assert descriptor.is_packed is False
    assert descriptor.is_numeric is True

    #  A binary item carries its sign in its representation, so there is no
    #  overpunch and no separate sign byte.
    assert descriptor.signed is True
    assert descriptor.unsigned is False
    assert descriptor.sign_position is model.SignPosition.IMPLICIT_BINARY

    #  `binary-char` has no PICTURE at all, which is why the digit members are
    #  absent and the domain comes from the width instead.
    assert descriptor.picture is None
    assert descriptor.digits is None
    assert descriptor.scale is None
    assert descriptor.quantum is None

    assert descriptor.byte_length == 1
    assert descriptor.value_domain == (-128, 127)
    assert (descriptor.min_value, descriptor.max_value) == (-128, 127)

    #  `int`, NOT `Decimal`: an unscaled binary item truncates as an integer, and
    #  only an `int` carrier reproduces that (rule R-2 forbids the third option).
    assert descriptor.is_int is True
    assert descriptor.is_decimal is False
    assert descriptor.python_storage is model.CobolPythonStorage.INT

    #  The two figures above are the usage layer's, not the descriptor's own, so
    #  width and domain live in exactly one place.
    assert descriptor.byte_length == cobol_usage.byte_length(
        descriptor.usage,
        digits=descriptor.digits,
        scale=descriptor.scale,
        character_length=descriptor.character_length,
        sign_position=descriptor.sign_position,
        unsigned=descriptor.unsigned,
    )
    assert descriptor.value_domain == cobol_usage.value_domain(
        descriptor.usage,
        digits=descriptor.digits,
        signed=descriptor.signed,
        unsigned=descriptor.unsigned,
    )


def test_scycle_redefines_cyclea_and_the_relationship_is_exposed() -> None:
    """`Scycle Redefines cyclea` [copybooks/wssystem.cob:L63] is not flattened.

    The two names are ONE BYTE of storage under two spellings, and
    [general/gl080.cbl:L325] and L328 read it by the second spelling while the
    system record is written by the first. A migration that dropped the redefines
    would lose the fact that assigning either name changes the other.

    ANOMALY A-2 rests on this pair: `Scycle` is the dividend at
    [general/gl080.cbl:L328], so it is one of the two inputs that decide the
    subscript used at [general/gl080.cbl:L345], and it reaches the program under a
    name that owns no storage of its own.

    Provenance: the dictionary's own copybook view of L63, which records
    `redefines` verbatim - lower-case `cyclea`, exactly as the source writes it
    inside a declaration whose own name is capitalised.
    """
    assert _SCYCLE.redefines == "cyclea"
    assert _SCYCLE.redefines is not None
    assert _SCYCLE.redefines.casefold() == _CYCLEA.name.casefold()

    #  The base item is not itself a redefines, so the direction is unambiguous.
    assert _CYCLEA.redefines is None

    #  Same storage, therefore the same shape in every respect that matters to
    #  the arithmetic.
    assert _SCYCLE.usage is _CYCLEA.usage
    assert _SCYCLE.signed == _CYCLEA.signed
    assert _SCYCLE.byte_length == _CYCLEA.byte_length
    assert _SCYCLE.value_domain == _CYCLEA.value_domain
    assert _SCYCLE.python_storage is _CYCLEA.python_storage

    #  And they are DIFFERENT ENTRIES, keyed differently, because a redefines
    #  view has no column of its own: the base item reaches `SYSTEM-REC.CYCLEA`
    #  while the view is keyed by its copybook record. That asymmetry is why this
    #  file resolves keys defensively.
    scycle_entry = _entry(_SCYCLE_KEY, record=_SYSTEM_RECORD)
    cyclea_entry = _entry(_CYCLEA_KEY, table=_SYSTEM_TABLE)
    assert scycle_entry.presence.in_copybook is True
    assert scycle_entry.presence.in_bridge is False
    assert scycle_entry.presence.in_column is False
    assert scycle_entry.one_sided is True
    assert scycle_entry.column is None
    assert cyclea_entry.one_sided is False
    assert cyclea_entry.column is not None
    assert cyclea_entry.column.name == "CYCLEA"


def test_the_binary_char_declaration_governs_and_nothing_is_adjudicated() -> None:
    """`*> 99.` is a comment; `binary-char` is the declaration (R-4).

    `05 Cyclea binary-char.  *> 99.` [copybooks/wssystem.cob:L62] and
    `05 Period binary-char.  *> 99.` [copybooks/wssystem.cob:L64] carry the
    maintainer's own note that the field is "99", i.e. two unsigned decimal
    digits. The compiler obeys the DECLARATION, so the item is a signed byte with
    a domain of -128..127 rather than 0..99, and the note is simply left standing:
    there is no `picture` on these descriptors to hold it, and the disagreement it
    hints at is exposed through the drift channel instead of being settled.

    ANOMALY A-2 is downstream of this: because the declaration wins, `Period`
    [copybooks/wssystem.cob:L64] is a SIGNED divisor at [general/gl080.cbl:L328],
    and a negative divisor is what puts a subscript of zero within reach at
    [general/gl080.cbl:L345]. Had the comment governed, `Period` would have been
    0..99 and that band would have been unreachable.

    The bridge disagrees in the same direction, and THAT disagreement is a
    numbered register question rather than a matter of opinion: the copybook says
    signed, the host variable `HV-CYCLEA PIC 9(03) COMP` says unsigned, and the
    column `tinyint(2) unsigned` agrees with the host variable, so a negative
    value loses its sign AT THE BRIDGE, before any SQL runs. That is anomaly A-11
    and question Q-3.

    THE LAST TWO ASSERTIONS ARE THE POINT: the value object and its drift record
    expose EXACTLY the members their own docstrings describe and not one more, so
    no member can have appeared that quietly picks a winner between the three
    layers. Add such a member and this test fails.
    """
    for descriptor in (_CYCLEA, _PERIOD):
        assert descriptor.picture is None
        drift = descriptor.drift()
        assert drift is not None
        assert drift.signedness is True
        assert drift.usage is True
        assert any("Signedness disagrees" in detail for detail in drift.details)
        assert descriptor.anomaly_refs() == ("A-11",)
        # Q-3 RESOLVED (finding F-19), so the tuple is now empty: the measurement
        # is carried in the entry notes and A-11 remains in anomaly_refs.
        assert descriptor.ambiguity_refs() == ()
        assert any("MEASURED against GnuCOBOL" in note
                   for note in loader.get_entry(descriptor.dictionary_key).notes)

    #  The redefines view has no bridge and no column, so it cannot disagree with
    #  anything: its drift record exists but every flag is clear, and it carries
    #  no register reference of its own.
    scycle_drift = _SCYCLE.drift()
    assert scycle_drift is not None
    assert scycle_drift.signedness is False
    assert scycle_drift.usage is False
    assert scycle_drift.details == ()
    assert _SCYCLE.anomaly_refs() == ()
    assert _SCYCLE.ambiguity_refs() == ()

    assert {
        member.name for member in dataclasses.fields(cobol_field.FieldDescriptor)
    } == {
        "name",
        "usage",
        "usage_declared_at",
        "usage_inherited_from",
        "picture",
        "signed",
        "sign_position",
        "sign_clause_text",
        "digits",
        "integer_digits",
        "scale",
        "character_length",
        "unsigned",
        "is_edited",
        "occurs",
        "redefines",
        "is_filler",
        "is_group",
        "parent_group",
        "python_storage",
        "dictionary_key",
        "source_locator",
    }
    assert {member.name for member in dataclasses.fields(model.Drift)} == {
        "signedness",
        "usage",
        "digits",
        "scale",
        "character_length",
        "name",
        "details",
    }


def test_y_and_a_are_two_digit_unsigned_zoned_display_receivers() -> None:
    """`77 y pic 99` and `77 a pic 99` [general/gl080.cbl:L182-L183].

    These two receivers are what turn L328 and L329 from arithmetic into
    behaviour: two digits, no sign, and no size-error handler anywhere in the
    twelve in-scope programs, so a wider or a negative result is silently
    reshaped rather than reported.

    `a` is ANOMALY A-2's subscript. Its domain of 0 through 99 against a table
    bounded at four [copybooks/wsledger.cob:L36] IS the anomaly, so this test
    fixes the shape of the field the subscript at [general/gl080.cbl:L345] comes
    out of.

    `python_storage` is INT and not DECIMAL, which is what the usage layer reports
    for a zero-scale `DISPLAY` item; the assertion below states the layer's answer
    rather than a preference of this file's.

    ON THE UNSIGNEDNESS, and it is worth being exact. `signed` is false because
    the picture carries no S. `unsigned` is ALSO false, because that member
    records the explicit UNSIGNED KEYWORD - which `binary-char unsigned`
    [copybooks/wssystem.cob:L65] carries and `pic 99` does not. The item's
    unsignedness is stated by its DOMAIN, `(0, 99)`, and the dictionary describes
    the identical declaration `05 Current-Quarter pic 9.`
    [copybooks/wssystem.cob:L110] exactly the same way - asserted below against
    the real entry, so the claim is evidence rather than assertion. The final
    block proves the member cannot move a stored value either way.
    """
    for descriptor, locator, name in (
        (_A, _A_LOCATOR, "a"),
        (_Y, _Y_LOCATOR, "y"),
    ):
        assert descriptor.name == name

        #  No dictionary key: the artifact catalogues declared DATA, and a `77`
        #  item in a program's WORKING-STORAGE is not that. The locator is the
        #  provenance instead, and `cite` falls back to it.
        assert descriptor.dictionary_key is None
        assert descriptor.source_locator == locator
        assert descriptor.cite() == locator
        assert descriptor.drift() is None
        assert descriptor.anomaly_refs() == ()
        assert descriptor.ambiguity_refs() == ()

        assert descriptor.usage is model.Usage.DISPLAY
        assert descriptor.is_zoned_display is True
        assert descriptor.is_binary_family is False
        assert descriptor.is_packed is False
        assert descriptor.picture == "99"
        assert descriptor.digits == 2
        assert descriptor.integer_digits == 2
        assert descriptor.scale == 0
        assert descriptor.signed is False
        assert descriptor.unsigned is False
        assert descriptor.sign_position is model.SignPosition.NONE

        #  Two bytes, because a zoned digit is one byte and the sign is
        #  overpunched rather than separate.
        assert descriptor.byte_length == 2
        assert descriptor.value_domain == (0, 99)

        assert descriptor.is_int is True
        assert descriptor.is_decimal is False
        assert descriptor.python_storage is cobol_usage.python_storage_for(
            descriptor.usage, descriptor.scale
        )

    #  The dictionary's own description of the same kind of declaration.
    assert _CURRENT_QUARTER.picture == "9"
    assert _CURRENT_QUARTER.usage is model.Usage.DISPLAY
    assert _CURRENT_QUARTER.signed is False
    assert _CURRENT_QUARTER.unsigned is False
    assert _CURRENT_QUARTER.value_domain == (0, 9)

    #  A CONTROL PROBE, not a claim about the source: the same receiver spelled
    #  with the UNSIGNED keyword set behaves identically, so which way this file
    #  spells the member cannot change a single stored value.
    with_keyword = _pic_99(name="a", source_locator=_A_LOCATOR, unsigned=True)
    assert with_keyword.byte_length == _A.byte_length
    assert with_keyword.value_domain == _A.value_domain
    assert arithmetic.store(-3, with_keyword) == arithmetic.store(-3, _A)
    assert arithmetic.store(127, with_keyword) == arithmetic.store(127, _A)


def test_a_descriptor_without_provenance_is_refused() -> None:
    """Rule R-5's invariant, exercised rather than asserted.

    A descriptor for a field the frozen COBOL declares must arrive with either its
    dictionary key or a `<path>:L<n>` locator. `y` and `a` take the second route,
    so this test proves the route is a real gate and not a defaulted argument: the
    same construction with neither is refused, and a malformed locator is refused
    too.

    It matters here rather than in the abstract because ANOMALY A-2 is asserted
    THROUGH these two descriptors: `77 y pic 99` and `77 a pic 99`
    [general/gl080.cbl:L182-L183] have no dictionary entry, so if their provenance
    could be omitted, the subscript's declared domain would rest on nothing
    traceable.
    """
    with pytest.raises(cobol_field.MissingProvenanceError):
        cobol_field.FieldDescriptor(
            name="a",
            usage=model.Usage.DISPLAY,
            picture="99",
            digits=2,
            integer_digits=2,
            scale=0,
            python_storage=model.CobolPythonStorage.INT,
        )

    with pytest.raises(cobol_field.FieldDescriptorError):
        _pic_99(name="a", source_locator="gl080 line 183")


def test_one_statement_pair_spans_three_storage_classes() -> None:
    """L328, L329 and L345 touch BINARY-CHAR, zoned DISPLAY and COMP-3.

    `divide scycle by period giving a rounded.` [general/gl080.cbl:L328] reads two
    signed one-byte binary items and writes a two-byte unsigned zoned one;
    `move ledger-balance to ledger-q (a).` [general/gl080.cbl:L345] then uses that
    zoned value as a subscript into a packed-decimal table
    [copybooks/wsledger.cob:L36]. Three declarations, three widths, two carriers,
    one statement sequence - which is why the storage classes are modelled per
    field instead of collapsed into one numeric type.
    """
    classes = {
        _SCYCLE.usage,
        _PERIOD.usage,
        _A.usage,
        _Y.usage,
        _LEDGER_Q.usage,
    }
    assert classes == {
        model.Usage.BINARY_CHAR,
        model.Usage.DISPLAY,
        model.Usage.COMP_3,
    }

    #  The widths differ, so a byte-for-byte migration would have to know which
    #  is which.
    assert (_SCYCLE.byte_length, _A.byte_length, _LEDGER_Q.byte_length) == (1, 2, 6)

    #  And so do the carriers: the divide works in `int`, the table in `Decimal`.
    assert (_SCYCLE.is_int, _A.is_int, _LEDGER_Q.is_decimal) == (True, True, True)
    assert _LEDGER_Q.scale == 2
    assert _LEDGER_Q.quantum == Decimal("0.01")


# ---------------------------------------------------------------------------
#  THE SELF-CANCELLING ROUND-TRIP GATE
#
#      a = ROUND_HALF_UP(scycle / period)     L328,  rounded=True
#      y = a * period                         L329,  rounded=False
#      if scycle not = y: go to main-end      L331-L332   <-- THE GATE
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class _Census:
    """A walk of both spellings of L328 over the operands' whole domain.

    Attributes:
        flips: Every `(scycle, period)` whose SAME-CALL gate disposition differs
            between the rounded and the truncating spelling.
        a_differs: Every `(scycle, period)` for which the two spellings leave a
            different `a`.
        armed_by_rounding: Every `(scycle, period)` where rounding leaves the one
            value the guard at [general/gl080.cbl:L324] tests and truncation does
            not.
        passing: `(scycle, period, a)` for every pair whose gate LETS PHASE 5
            RUN, as written. `a` is then the subscript [general/gl080.cbl:L345]
            uses, so this is the set anomaly A-2 is about.
        pairs: How many pairs the walk reached.
    """

    flips: tuple[tuple[int, int], ...]
    a_differs: tuple[tuple[int, int], ...]
    armed_by_rounding: tuple[tuple[int, int], ...]
    passing: tuple[tuple[int, int, int], ...]
    pairs: int


@pytest.fixture(scope="module")
def census() -> _Census:
    """Walk every `(Scycle, Period)` the two declarations admit.

    EXHAUSTIVE over the operands' declared domain rather than sampled, because the
    claim being made is a universal one and a sample cannot support it. The two
    excluded bands are excluded for cause and are each covered by their own test:
    `period == 0` reaches the zero divisor of section 4.6, and
    `scycle < period` is turned back by [general/gl080.cbl:L325].

    Module-scoped because it is a pure function of the frozen declarations, so
    computing it once cannot leak state between tests.

    Returns:
        The census.
    """
    flips: list[tuple[int, int]] = []
    a_differs: list[tuple[int, int]] = []
    armed: list[tuple[int, int]] = []
    passing: list[tuple[int, int, int]] = []
    pairs = 0

    for scycle in range(_SCYCLE.min_value, _SCYCLE.max_value + 1):
        for period in range(_PERIOD.min_value, _PERIOD.max_value + 1):
            if period == 0:
                continue
            #  325  or  scycle <  period  ->  go to main-end.
            if arithmetic.compare(scycle, period) < 0:
                continue
            pairs += 1
            as_written = _end_of_period(
                incoming_a=_A_NOT_ARMED,
                scycle=scycle,
                period=period,
                rounded=True,
            )
            truncating = _end_of_period(
                incoming_a=_A_NOT_ARMED,
                scycle=scycle,
                period=period,
                rounded=False,
            )
            if as_written.gate_passed != truncating.gate_passed:
                flips.append((scycle, period))
            if as_written.a != truncating.a:
                a_differs.append((scycle, period))
                if as_written.a == _A_ARMED:
                    armed.append((scycle, period))
            if as_written.gate_passed:
                passing.append((scycle, period, as_written.a))

    return _Census(
        flips=tuple(flips),
        a_differs=tuple(a_differs),
        armed_by_rounding=tuple(armed),
        passing=tuple(passing),
        pairs=pairs,
    )


def test_the_round_trip_gate_is_an_exact_divisibility_test() -> None:
    """L328 rounds, L329 multiplies straight back, L331 compares (A-2's source).

    The pair of statements is a DIVISIBILITY TEST written as a round trip, and
    that is why the two halves must not share a rounding direction: the divide
    carries `ROUNDED` [general/gl080.cbl:L328] and the multiply does not
    [general/gl080.cbl:L329], so a module-level rounding mode covering both would
    be wrong for one of them whichever way it was set.

    Provenance for the two pairs. `scycle = 4, period = 2` divides exactly, so
    `a = 2`, `y = 4`, the gate passes and phase 5 runs - and note that `a = 2` is
    then the subscript at [general/gl080.cbl:L345], which is anomaly A-2's input.
    `scycle = 3, period = 2` does not divide exactly, so the gate turns the phase
    back. Both computed through the same two verbs the source writes.
    """
    exact = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=4, period=2)
    assert exact.divided is True
    assert exact.a == 2
    assert exact.y == 4
    assert exact.gate_passed is True

    inexact = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=3, period=2)
    assert inexact.divided is True
    assert inexact.a == 2
    assert inexact.y == 4
    assert inexact.gate_passed is False

    #  The gate is a comparison of `scycle` against `y` and of nothing else, so a
    #  passing pass leaves the two equal and a failing one does not.
    assert arithmetic.compare(4, exact.y) == 0
    assert arithmetic.compare(3, inexact.y) != 0


def test_no_pair_flips_the_same_call_gate(census: _Census) -> None:
    """THE ROUND TRIP IS EXACTLY SELF-CANCELLING WITHIN ONE CALL.

    Walking every `(Scycle, Period)` the two signed `binary-char` declarations
    admit [copybooks/wssystem.cob:L63-L64], there is NOT ONE pair whose gate
    disposition at [general/gl080.cbl:L331] differs between the rounded spelling
    and a truncating one - 32768 pairs, zero flips - while 14132 of them leave a
    DIFFERENT `a` and 98 of those are armings of the L324 guard. The three counts
    are a census of this layer over the frozen declarations, not measurements of
    the compiled program; the behaviour each pair exhibits is what carries oracle
    provenance, and the named pairs below cite theirs.

    The mechanism, so that the zero is not read as luck: a rounding difference
    moves `a` by one and therefore `y` by `period`, so for the product to come back
    to `scycle` anyway the two-digit receiver would have to wrap - the shortfall
    would have to reach 100, and the shortfall is smaller than the divisor, so only
    the far end of `Period`'s domain could even be in the running. `a` itself can
    exceed two digits only when the divisor's magnitude is 1, and there the
    quotient is exact and the two spellings agree. The census closes the remaining
    band by exhaustion rather than by argument.

    So the `ROUNDED` keyword at [general/gl080.cbl:L328] does not decide THIS
    call's disposition. What it decides is the value of `a`, which is anomaly
    A-2's subscript and, one call later, the guard at
    [general/gl080.cbl:L324] - see the next two tests.
    """
    assert census.pairs == 32768
    assert census.flips == ()
    assert len(census.a_differs) == 14132
    assert len(census.armed_by_rounding) == 98


def test_rounding_moves_a_even_where_it_cannot_move_the_gate(
    census: _Census,
) -> None:
    """A-2's subscript is the `ROUNDED` quotient, so rounding chooses the slot.

    Anomaly A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345] is a subscript
    computed by a rounding divide, so getting the rounding direction wrong changes
    WHICH element of `occurs 4` [copybooks/wsledger.cob:L36] the phase writes -
    and one of the two candidate slots may be inside the table while the other is
    not. The named pair is provenance for the direction: `scycle = 17, period = 2`
    has a quotient of exactly 8.5, which COBOL `ROUNDED` takes away from zero to 9
    while a plain store truncates it to 8.
    """
    assert (17, 2) in census.a_differs
    assert (17, 2) in census.armed_by_rounding

    as_written = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=17, period=2)
    truncating = _end_of_period(
        incoming_a=_A_NOT_ARMED, scycle=17, period=2, rounded=False
    )
    assert (as_written.a, truncating.a) == (9, 8)
    assert (as_written.y, truncating.y) == (18, 16)

    #  Neither reaches phase 5 on THIS call, which is the finding of the census
    #  above: the gate is blind to the rounding direction.
    assert as_written.gate_passed is False
    assert truncating.gate_passed is False

    #  The direction itself, stated once at the level of the store: half away
    #  from zero when ROUNDED, toward zero otherwise. Measured on GnuCOBOL 3.2.0
    #  and recorded as question Q-2 in `acas_posting/cobol/arithmetic.py`.
    assert arithmetic.store(Decimal("8.5"), _A, rounded=True) == 9
    assert arithmetic.store(Decimal("8.5"), _A) == 8
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDING_DIRECTIONS[False] == cobol_field.TRUNCATING_STORE


def test_the_rounding_direction_flips_the_next_invocation() -> None:
    """⭐ WHERE THE `ROUNDED` KEYWORD ACTUALLY DECIDES A PHASE.

    `a` is READ at [general/gl080.cbl:L324] and WRITTEN at
    [general/gl080.cbl:L328], in that order, and `77 a pic 99 value zero.`
    [general/gl080.cbl:L183] is initialised once at load in a program that returns
    with `goback` [general/gl080.cbl:L366]. So the quotient this call computes is
    the value the NEXT call's guard tests, and the guard tests for exactly one
    value: nine.

    `scycle = 17, period = 2` therefore splits the two spellings a call apart. As
    written, `a` becomes 9 and the following call is turned back at L324 without
    ever reaching the divide - the entire end-of-period phase, the whole
    `GL-Nominal` walk at [general/gl080.cbl:L339-L349] and both counters at
    [general/gl080.cbl:L355-L363], skipped. Truncating instead, `a` becomes 8, the
    guard is silent and the following call proceeds. Agent Action Plan section
    0.1.1: "Getting this backwards would corrupt essentially every posted figure."

    ANOMALY A-2 is on both sides of this: the value being carried forward is the
    same unbounded subscript [general/gl080.cbl:L328], [general/gl080.cbl:L345],
    and nine is outside the table's four elements either way - so the two
    spellings differ over whether the phase runs at all, not merely over which
    slot it would have written.

    ⛔ This is why `_end_of_period` takes `incoming_a` and never initialises it.
    """
    first_as_written = _end_of_period(
        incoming_a=_A_NOT_ARMED, scycle=17, period=2, rounded=True
    )
    first_truncating = _end_of_period(
        incoming_a=_A_NOT_ARMED, scycle=17, period=2, rounded=False
    )
    assert first_as_written.a == _A_ARMED
    assert first_truncating.a != _A_ARMED

    #  The second call, differing ONLY in what the first left in `a`. Its own
    #  operands are identical and are chosen to divide exactly, so nothing but the
    #  carried-over `a` can account for the difference.
    second_as_written = _end_of_period(
        incoming_a=first_as_written.a, scycle=8, period=2
    )
    second_truncating = _end_of_period(
        incoming_a=first_truncating.a, scycle=8, period=2
    )

    assert second_as_written.divided is False
    assert second_as_written.gate_passed is False
    assert second_as_written.subscripts == ()
    assert second_as_written.a == _A_ARMED

    assert second_truncating.divided is True
    assert second_truncating.gate_passed is True
    assert second_truncating.a == 4
    assert second_truncating.y == 8

    #  And with a ledger to walk, the two differ in table effect, not just in
    #  control flow: one writes nothing at all.
    balances = (Decimal("10.00"),)
    assert (
        _end_of_period(
            incoming_a=first_as_written.a, scycle=8, period=2, balances=balances
        ).subscripts
        == ()
    )
    assert _end_of_period(
        incoming_a=first_truncating.a, scycle=8, period=2, balances=balances
    ).subscripts == (4,)


def test_a_is_read_before_it_is_written() -> None:
    """[general/gl080.cbl:L324] reads `a`; [general/gl080.cbl:L328] writes it.

    The order matters three times over, and each is asserted here.

    First, an incoming nine turns the block back before the divide, so a `period`
    of zero that would otherwise have divided by zero is never reached on that
    path - which is why section 4.6's zero divisor is reachable only when `a` is
    not nine.

    Second, an incoming value other than nine lets the divide run, whatever it is.

    Third, the guard cannot police the value the divide is about to write: with
    `scycle = 9, period = 1` the quotient is nine, the gate passes, and NINE IS
    USED AS THE SUBSCRIPT at [general/gl080.cbl:L345] in the very same call. The
    guard is not a bound on `a` - it is a test of the previous call's leftovers.
    """
    #  Pre-empted, and note that `period` is zero: no exception, because the
    #  divide is never reached.
    armed = _end_of_period(incoming_a=_A_ARMED, scycle=5, period=0)
    assert armed.divided is False
    assert armed.a == _A_ARMED
    assert armed.y is None
    assert armed.gate_passed is False
    assert armed.scycle == 5

    #  Not pre-empted: the divide runs and overwrites whatever `a` held.
    for incoming in (0, 1, 8, 10, 99):
        ran = _end_of_period(incoming_a=incoming, scycle=8, period=2)
        assert ran.divided is True
        assert ran.a == 4
        assert ran.gate_passed is True

    #  The guard is not a bound: nine is written by L328 and then used by L345.
    #  ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345].
    reaches_nine = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=9,
        period=1,
        balances=(Decimal("1.00"), Decimal("2.00")),
    )
    assert reaches_nine.a == _A_ARMED
    assert reaches_nine.gate_passed is True
    assert reaches_nine.subscripts == (_A_ARMED, _A_ARMED)


def test_a_successful_phase_can_arm_the_guard_for_every_later_call() -> None:
    """A completed phase 5 can still poison every phase 5 after it.

    `scycle = 18, period = 2` divides exactly, so `y` comes back to 18, the gate
    at [general/gl080.cbl:L331] passes, the loop runs and both counters advance.
    The quotient it computed, though, is nine - and nine is what
    [general/gl080.cbl:L324] tests. So the call succeeds AND leaves the guard
    armed, and because nothing else in the block writes `a`, every later call is
    turned back at L324 with `a` still nine. Reproduced, not fixed (R-4).

    The successful pass is also an ANOMALY A-2 pass: nine is outside `occurs 4`
    [copybooks/wsledger.cob:L36], so the store at [general/gl080.cbl:L345] went
    past the table on the one run that did anything at all.
    """
    succeeded = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=18,
        period=2,
        current_quarter=1,
        balances=(Decimal("100.00"),),
    )
    assert succeeded.gate_passed is True
    assert succeeded.a == _A_ARMED
    assert succeeded.subscripts == (_A_ARMED,)
    assert succeeded.scycle == 19
    assert succeeded.current_quarter == 2

    #  Every subsequent call, fed the `a` its predecessor left, is turned back and
    #  leaves `a` untouched - so the state is stable and the phase never returns.
    carried = succeeded.a
    for _ in range(3):
        again = _end_of_period(
            incoming_a=carried,
            scycle=succeeded.scycle,
            period=2,
            balances=(Decimal("100.00"),),
        )
        assert again.divided is False
        assert again.subscripts == ()
        assert again.a == _A_ARMED
        carried = again.a


def test_the_half_way_quotient_rounds_away_from_zero() -> None:
    """COBOL `ROUNDED` is half AWAY FROM ZERO, on both signs.

    Provenance: `ROUNDED_STORE` in `acas_posting/cobol/arithmetic.py` is
    `ROUND_HALF_UP`, chosen because that is what GnuCOBOL 3.2.0 was measured to do
    - question Q-2 - and NOT Python's built-in banker's rounding, which would send
    8.5 to 8 and quietly change anomaly A-2's subscript.

    `scycle = 3, period = 2` gives exactly 1.5. Rounded it is 2, truncated it is
    1, and `y` follows to 4 and 2 respectively; neither equals 3, so the gate
    turns the phase back either way, as the census requires.

    The negative half-way case needs a negative `period`, which the signed
    declaration [copybooks/wssystem.cob:L64] admits: `scycle = 3, period = -2`
    gives -1.5, which goes to -2 away from zero and then LOSES ITS SIGN in the
    two-digit unsigned receiver, arriving as 2.
    """
    positive = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=3, period=2)
    assert positive.a == 2
    assert positive.y == 4
    assert positive.gate_passed is False

    truncating = _end_of_period(
        incoming_a=_A_NOT_ARMED, scycle=3, period=2, rounded=False
    )
    assert truncating.a == 1
    assert truncating.y == 2
    assert truncating.gate_passed is False

    negative = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=3, period=-2)
    assert negative.a == 2
    #  `y` is 2 * -2 = -4, and the sign is dropped again on the way into `y`.
    assert negative.y == 4
    assert negative.gate_passed is False

    negative_truncating = _end_of_period(
        incoming_a=_A_NOT_ARMED, scycle=3, period=-2, rounded=False
    )
    assert negative_truncating.a == 1
    assert negative_truncating.y == 2

    #  The direction at the level of the store, for both signs of the same
    #  magnitude, so neither can be read as an accident of the pair chosen.
    assert arithmetic.store(Decimal("1.5"), _A, rounded=True) == 2
    assert arithmetic.store(Decimal("-1.5"), _A, rounded=True) == 2
    assert arithmetic.store(Decimal("1.5"), _A) == 1
    assert arithmetic.store(Decimal("-1.5"), _A) == 1


# ---------------------------------------------------------------------------
#  ANOMALY A-2  -  THE UNBOUNDED QUARTER SUBSCRIPT
#      move     ledger-balance  to  ledger-q (a).      [general/gl080.cbl:L345]
#      05  Ledger-Q  pic s9(8)v99  comp-3  occurs  4.  [copybooks/wsledger.cob:L36]
#  ⛔ NOTHING BELOW BOUNDS-CHECKS `a`, AND NOTHING MAY (R-3, R-4).
# ---------------------------------------------------------------------------


def test_a2_the_quarter_table_is_bounded_at_four() -> None:
    """`occurs 4` [copybooks/wsledger.cob:L36] is the bound nobody enforces.

    ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345]. The table has
    four elements, `a` is a two-digit field holding 0 through 99, and the only
    tests standing between the two are the guard at
    [general/gl080.cbl:L324-L326], which excludes one value and one ordering, and
    the exact-multiple gate at [general/gl080.cbl:L331], which says nothing about
    magnitude. The bound is DECLARED but never CHECKED.

    The byte map that follows is derived from the descriptors, never transcribed:
    one occurrence is as wide as `Ledger-Last` [copybooks/wsledger.cob:L29], which
    is the field immediately before the table, and the trailing
    `filler pic x(50)` [copybooks/wsledger.cob:L37] absorbs eight whole
    occurrences after it. All three bands are measured - the two in-record ones
    and the overrun that was question Q-19 - see
    `acas_posting.cobol.move.UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE` for the readings
    and `acas_posting/programs/gl080_end_of_cycle.py` for the reproduction.
    """
    assert _LEDGER_Q.occurs == _OCCURRENCES == 4
    assert _STRIDE == 6
    assert _LEDGER_Q.digits == 10
    assert _LEDGER_Q.integer_digits == 8
    assert _LEDGER_Q.scale == 2
    assert _LEDGER_Q.signed is True

    #  `a`'s declared domain is twenty-five times the table's bound.
    assert _A.value_domain == (0, 99)
    assert _A.max_value > _OCCURRENCES

    #  Subscript one starts where the table starts, and subscript ZERO starts one
    #  whole occurrence in FRONT of it - which is exactly the width and the
    #  position of `Ledger-Last` [copybooks/wsledger.cob:L29]. That field IS a
    #  column, so a store there has a diff-visible effect on GLLEDGER-REC.
    assert _LEDGER_LAST.byte_length == _STRIDE
    assert _first_byte_of_occurrence(1) == 0
    assert _first_byte_of_occurrence(0) == -_LEDGER_LAST.byte_length
    assert _bytes_past_the_table(_OCCURRENCES) == 0

    #  The trailing filler carries no column, so subscripts 5 through 12 are
    #  silent: inside the record, outside every column.
    assert _TRAILING_FILLER == 50
    assert _LAST_IN_RECORD_OCCURRENCE == 12
    assert _first_byte_of_occurrence(5) == _OCCURRENCES * _STRIDE
    assert _bytes_past_the_table(5) == _STRIDE
    assert _bytes_past_the_table(_LAST_IN_RECORD_OCCURRENCE) <= _TRAILING_FILLER
    assert _bytes_past_the_table(_LAST_IN_RECORD_OCCURRENCE + 1) > _TRAILING_FILLER


def test_a2_the_out_of_range_band_is_reachable_on_a_passing_gate(
    census: _Census,
) -> None:
    """A-2 is reachable rather than theoretical, and on SUCCESSFUL runs.

    ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345],
    [copybooks/wsledger.cob:L36]. `Period = 1` is the case that matters: the guard
    at [general/gl080.cbl:L325] then passes for every `Scycle`,
    [general/gl080.cbl:L328] makes `a` equal to `Scycle`, and
    [general/gl080.cbl:L331] agrees because the multiply takes it straight back -
    so as the cycles advance, `a` WALKS OUT OF THE TABLE while the gate keeps
    letting phase 5 run. Nothing resets `Scycle` for `Period = 1` either: the two
    resets at [general/gl080.cbl:L358-L363] fire only for periods 3 and 13.

    Every subscript in 5 through 12 is therefore reached with the gate open, NINE
    INCLUDED - the guard at [general/gl080.cbl:L324] cannot exclude nine here,
    because it read `a` before the divide wrote it.

    ⛔ Nothing is clamped, nothing raises and nothing is logged as a warning. The
    subscripts come back exactly as computed.
    """
    balances = (Decimal("11.11"), Decimal("-22.22"))

    for subscript in range(5, _LAST_IN_RECORD_OCCURRENCE + 1):
        #  `Period = 1` and `Scycle = subscript` - the walk described above.
        walked = _end_of_period(
            incoming_a=_A_NOT_ARMED,
            scycle=subscript,
            period=1,
            balances=balances,
        )
        assert walked.gate_passed is True
        assert walked.a == subscript
        assert walked.subscripts == (subscript, subscript)
        assert walked.a > _OCCURRENCES
        assert _bytes_past_the_table(walked.a) > 0
        assert _bytes_past_the_table(walked.a) <= _TRAILING_FILLER

    #  Not a special case of one period, either: the census finds hundreds of
    #  passing pairs whose subscript is outside the declared bound.
    out_of_range = tuple(
        (scycle, period, a)
        for scycle, period, a in census.passing
        if not 1 <= a <= _OCCURRENCES
    )
    assert len(census.passing) == 1074
    assert len(out_of_range) == 664
    assert (5, 1, 5) in census.passing
    assert (20, 4, 5) in census.passing
    assert (12, 1, 12) in census.passing


def test_a2_subscript_zero_needs_a_negative_period(census: _Census) -> None:
    """Subscript ZERO reaches L345 only through a negative `Period`.

    ANOMALY A-2 [general/gl080.cbl:L345] together with the signedness the
    declaration gives `Period` [copybooks/wssystem.cob:L64]. For a positive
    `Period` the guard at [general/gl080.cbl:L325] forbids `scycle < period`, so
    the quotient is at least one and the store cannot fall in front of the table.
    A NEGATIVE `Period` is a different matter: the guard is then vacuous for any
    non-negative `Scycle`, the quotient is at or below zero, and the unsigned
    receiver drops the sign - so `Scycle = 0, Period = -5` sends the store to
    subscript zero with the gate WIDE OPEN, which is `Ledger-Last`, a real column.

    Whether a negative `Period` can arrive from the database is a separate
    question and its answer is no: the column is `tinyint(2) unsigned`. The
    copybook declares it signed all the same, the bridge narrows it, and the sign
    is lost there rather than at the database - anomaly A-11 and question Q-3,
    unadjudicated. What this test fixes is the CONSEQUENCE inside the program: the
    signed declaration is what makes subscript zero reachable at all.
    """
    zero_subscript = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=0,
        period=-5,
        balances=(Decimal("7.77"),),
    )
    assert zero_subscript.gate_passed is True
    assert zero_subscript.a == 0
    assert zero_subscript.y == 0
    assert zero_subscript.subscripts == (0,)

    #  Every passing pair whose subscript is zero has a negative period. Asserted
    #  over the whole census, so it is a property and not an example.
    zeroes = tuple(
        (scycle, period) for scycle, period, a in census.passing if a == 0
    )
    assert zeroes != ()
    assert all(period < 0 for _, period in zeroes)
    assert all(scycle == 0 for scycle, _ in zeroes)

    #  The narrowing that loses the sign one layer further out, asserted where the
    #  dictionary records it.
    period_entry = _entry(_PERIOD_KEY, table=_SYSTEM_TABLE)
    assert period_entry.copybook is not None
    assert period_entry.copybook.signed is True
    assert period_entry.bridge_host_variable is not None
    assert period_entry.bridge_host_variable.signed is False
    assert period_entry.column is not None
    assert period_entry.column.unsigned is True
    # Q-3 RESOLVED (finding F-19); the measurement is in the notes and the anomaly
    # reference is unchanged.
    assert period_entry.ambiguity_refs == ()
    assert any("MEASURED against GnuCOBOL" in note for note in period_entry.notes)


def test_a2_the_store_is_blind_to_the_subscript() -> None:
    """The layer cannot bounds-check `a`, because it never sees it (R-3).

    ANOMALY A-2 [general/gl080.cbl:L345]. A store takes a VALUE and a DESCRIPTOR,
    and a subscript is neither: `occurs` is carried on the descriptor as
    DESCRIPTION and is not consulted, so there is no place in the arithmetic or
    field layer where a bound could be applied even by accident. The value stored
    is therefore identical for an in-range and an out-of-range subscript, and no
    exception, clamp or warning appears for any of them.

    This is the assertion a future well-meaning correction breaks (R-4): add a
    bound and the loop stops early on the first out-of-range account, which
    changes the disposition of every account after it.
    """
    balance = Decimal("1234.56")
    stored = arithmetic.store(balance, _LEDGER_Q)
    assert stored == balance

    for subscript in (0, 1, 4, 5, 9, 12, 13, 27, 99):
        #  The same store, once per subscript, to make the independence explicit.
        assert arithmetic.store(balance, _LEDGER_Q) == stored
        assert _LEDGER_Q.store(balance) == stored
        #  And the descriptor keeps reporting the DECLARED bound, unchanged, while
        #  saying nothing whatever about this subscript.
        assert _LEDGER_Q.occurs == _OCCURRENCES
        #  The addressing is linear and UNCLAMPED: an out-of-range subscript
        #  addresses storage outside the table instead of being folded back into
        #  it, which is the difference between reproducing anomaly A-2 and
        #  quietly repairing it.
        inside_the_table = (
            0 <= _first_byte_of_occurrence(subscript) < _OCCURRENCES * _STRIDE
        )
        assert inside_the_table is (1 <= subscript <= _OCCURRENCES)

    #  A pass whose subscript is far outside the table completes normally and
    #  reports every account it walked - no truncation of the loop, no diagnostic.
    #  `Scycle = 27, Period = 1` gives `a = 27`.
    walked = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=27,
        period=1,
        balances=(Decimal("1.00"), Decimal("2.00"), Decimal("3.00")),
    )
    assert walked.gate_passed is True
    assert walked.subscripts == (27, 27, 27)


def test_a2_an_out_of_record_subscript_stores_past_the_record_and_moves_no_column() -> (
    None
):
    """Q-19 is SETTLED: the store runs past byte 126 and changes NO column.

    ANOMALY A-2 past the record's end - [general/gl080.cbl:L345]. Subscript 13 is
    reachable exactly as 5 through 12 are: `Period = 1` and `Scycle = 13` passes
    the guard at [general/gl080.cbl:L324-L326], passes the gate at
    [general/gl080.cbl:L331], and stores at an offset thirteen occurrences into a
    four-element table. The store is real. Where it lands is not describable from
    `copybooks/wsledger.cob`, which is why this was the file's one open question -
    and it is a question only the compiled program could answer.

    THREE THINGS ARE SETTLED BY THE LAYOUT ARITHMETIC ALONE, and no measurement can
    change them: the subscript is REACHED, it is not clamped, and its last byte falls
    PAST the record's trailing filler, so the destination is outside
    `WS-Ledger-Record` [copybooks/wsledger.cob:L12-L37] altogether. What the layout
    could NOT say is what the compiled program overwrites once it stores there, and
    no compile line in this repository enables bounds checking - so that half was
    measured on the oracle (rule R-6).

    THE MEASUREMENT (finding F-19). GnuCOBOL 3.2.0, `cobc -x -free`, default
    flags - no dialect selection, no `>>SET ARITHMETIC`, no bounds-checking flag,
    matching every compile line in this repository. `WS-Ledger-Record` was
    transcribed field for field with a `pic x(20)` sentinel declared IMMEDIATELY
    AFTER it inside one enclosing `01`, because that is the only arrangement in
    which the bytes beyond the record are observable at all; `function length` was
    read back as 126 for the record and 6 for one occurrence; and each byte of the
    area was read individually through `function ord` after the store:

        move 999.99 to ledger-q (13)
            -> the six packed bytes 00 00 00 99 99 9C landed at 1-based offsets
               125 through 130: TWO inside the trailing `filler pic x(50)` and
               FOUR past the record's last byte, in the sentinel that follows it
            -> Ledger-Q1, Ledger-Q2, Ledger-Q3, Ledger-Q4 UNCHANGED
            -> Ledger-Last UNCHANGED
            -> no runtime message of any kind, and the program exited 0
        move 888.88 to ledger-q (14)
            -> offsets 131 through 136, six further on, again silently: the
               addressing stays plainly LINEAR past the record rather than
               wrapping, clamping or faulting
        move 555.55 to ledger-q (5)
            -> the first six bytes of the trailing filler, and Q1..Q4 still
               unchanged - the in-record band, re-confirmed in the same run

    WHAT THAT SETTLES, and what it does not. It settles both facts the migration
    needs: control flow CONTINUES, and `GLLEDGER-REC` - eleven columns, none of
    them the trailing filler - is UNTOUCHED, so an overrunning run moves none of
    the 22 compared tables. What stays undecidable from the frozen source is only
    which `01` item receives the four overrun bytes in the real program, because
    that is the compiler's allocation rather than a declaration; no column binds
    them either way, so the answer cannot change a diff.
    `acas_posting/programs/gl080_end_of_cycle.py` therefore stores the in-record
    part, logs the overrun, and does NOT raise - and the log record is licensed by
    section 0.3.4's rule for a diagnostic with no database effect.

    ⛔ NO BOUND IS ADDED HERE OR ANYWHERE (rules R-3, R-4). The former
    `xfail(strict=True)` asserted the opposite of the reading below - that the
    store still lands inside the record - which the layout arithmetic refutes
    outright and which `test_a2_the_subscript_bands` already asserts the negation
    of unconditionally, so the marker could only ever fail and its promised
    "unexpected pass when the question is answered" could never happen. A change
    back in that direction now fails by name instead.

    Every offset asserted below is DERIVED: the record's width is summed from the
    dictionary and `Quarters`' position is computed from the tail, and both agree
    with the oracle's own `function length` and byte census.
    """
    subscript = _LAST_IN_RECORD_OCCURRENCE + 1
    assert subscript == 13

    #  The subscript is reached with the gate open, and the pass completes: no
    #  clamp, no truncated loop, no exception.
    reached = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=subscript,
        period=1,
        balances=(Decimal("5.00"),),
    )
    assert reached.gate_passed is True
    assert reached.subscripts == (subscript,)

    #  NOT CLAMPED - the reproduction stores where the subscript says, exactly as the
    #  frozen program does. A migration that folded the subscript back into the table
    #  would repair anomaly A-2, which rule R-4 forbids.
    assert reached.subscripts[0] > _OCCURRENCES

    #  THE DERIVED GEOMETRY, against the oracle's own readings.
    assert _RECORD_BYTES == 126
    assert _QUARTERS_FIRST_BYTE == 53
    assert _QUARTERS_FIRST_BYTE + _first_byte_of_occurrence(1) == 53
    assert _last_byte_of_occurrence_in_record(_OCCURRENCES) == 76

    #  THE MEASURED ANSWER: occurrence 13 occupies offsets 125 through 130, so it
    #  STRADDLES the record's end - two bytes in, four bytes out.
    first_byte = _QUARTERS_FIRST_BYTE + _first_byte_of_occurrence(subscript)
    last_byte = _last_byte_of_occurrence_in_record(subscript)
    assert (first_byte, last_byte) == (125, 130)
    assert first_byte <= _RECORD_BYTES < last_byte
    assert last_byte - _RECORD_BYTES == 4
    assert _STRIDE - (last_byte - _RECORD_BYTES) == 2

    #  This is the reading the strict xfail used to assert against, stated so the
    #  reversal is explicit rather than merely absent: the store does NOT stay
    #  inside the record.
    past = _bytes_past_the_table(subscript)
    assert past > _TRAILING_FILLER

    #  And the last IN-record occurrence is the boundary, not an approximation of it:
    #  one lower still fits, so 13 is exactly where the layout runs out.
    assert _bytes_past_the_table(_LAST_IN_RECORD_OCCURRENCE) <= _TRAILING_FILLER
    assert past - _bytes_past_the_table(_LAST_IN_RECORD_OCCURRENCE) == _STRIDE

    #  Occurrence 14 lands WHOLLY outside, six bytes further on. Linear, not
    #  wrapped: had it wrapped it would have re-entered the table.
    beyond = subscript + 1
    beyond_first = _QUARTERS_FIRST_BYTE + _first_byte_of_occurrence(beyond)
    assert (beyond_first, _last_byte_of_occurrence_in_record(beyond)) == (131, 136)
    assert beyond_first > _RECORD_BYTES
    assert beyond_first - first_byte == _STRIDE

    #  And the neighbouring band is unaffected by any of it: occurrence 5 through
    #  12 still land wholly inside the filler, which is what makes them silent.
    for inside in range(_OCCURRENCES + 1, _LAST_IN_RECORD_OCCURRENCE + 1):
        assert _last_byte_of_occurrence_in_record(inside) <= _RECORD_BYTES
        assert _bytes_past_the_table(inside) > 0


# ---------------------------------------------------------------------------
#  ANOMALY A-3  -  TWO DISAGREEING NOTIONS OF "CURRENT QUARTER",
#  DECLARED ONE LINE APART
#      move     ledger-balance  to  ledger-q (a).   [general/gl080.cbl:L345]
#      if       current-quarter = 4                 [general/gl080.cbl:L346]
#  ⛔ THE TWO ARE NOT RECONCILED, AND MUST NOT BE (R-3, R-4).
# ---------------------------------------------------------------------------


def test_a3_current_quarter_rotates_independently_of_a() -> None:
    """`current-quarter` is its own counter [general/gl080.cbl:L355-L357].

    ANOMALY A-3 [general/gl080.cbl:L345], [general/gl080.cbl:L346],
    [general/gl080.cbl:L355-L357]. One line after the subscripted store, the
    program asks a question about a quarter - and it asks a DIFFERENT variable,
    advanced once per phase-5 run by `add 1` and wrapped by an equality test
    against five. `a` is a quotient of the cycle and the period; this is a
    revolving counter that knows nothing about either.

    The rotation is driven here through the field's own descriptor
    [copybooks/wssystem.cob:L110] rather than in plain Python, so the wrap is the
    one the COBOL writes: 1, 2, 3, 4 and back to 1. Note what does the capping -
    the equality test at [general/gl080.cbl:L356], not the field, whose `pic 9`
    domain would hold 5 quite happily.
    """
    quarter = 1
    seen = [quarter]
    for _ in range(8):
        #  355  add 1 to current-quarter.
        quarter = int(
            arithmetic.add_to(1, receiver_value=quarter, receiving=_CURRENT_QUARTER)
        )
        #  356-357  if current-quarter = 5 -> move 1 to current-quarter.
        if arithmetic.compare(quarter, 5) == 0:
            quarter = int(arithmetic.store(1, _CURRENT_QUARTER))
        seen.append(quarter)

    assert seen == [1, 2, 3, 4, 1, 2, 3, 4, 1]

    #  The field would hold five; only the test at L356 stops it.
    assert _CURRENT_QUARTER.value_domain == (0, 9)
    assert arithmetic.add_to(1, receiver_value=4, receiving=_CURRENT_QUARTER) == 5

    #  And it is a one-digit field, so an increment past its domain keeps the
    #  low-order digit silently rather than reporting anything - there is no
    #  size-error phrase anywhere in the twelve in-scope programs.
    assert arithmetic.add_to(1, receiver_value=9, receiving=_CURRENT_QUARTER) == 0

    #  Driven through the block itself, the counter advances once per run.
    run = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=8,
        period=2,
        current_quarter=3,
        balances=(Decimal("1.00"), Decimal("2.00")),
    )
    assert run.gate_passed is True
    assert run.current_quarter == 4
    wrapped = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=8,
        period=2,
        current_quarter=4,
        balances=(Decimal("1.00"),),
    )
    assert wrapped.current_quarter == 1


def test_a3_the_two_notions_of_quarter_can_disagree() -> None:
    """The subscript and the counter are free to point at different quarters.

    ANOMALY A-3 [general/gl080.cbl:L345], [general/gl080.cbl:L346],
    [general/gl080.cbl:L355-L357], sitting ONE LINE from anomaly A-2. Two states
    make the divergence concrete, and both are ordinary:

      * `a = 2` while `current-quarter = 4`. The balance goes into the SECOND
        quarter slot and, one line later, ALSO into `Ledger-Last`
        [copybooks/wsledger.cob:L29] - the year-end field - because the counter
        happens to say four.
      * `a = 4` while `current-quarter = 1`. The balance goes into the FOURTH
        quarter slot and `Ledger-Last` is NOT written, even though the fourth
        quarter is exactly what was just stored.

    ⛔ The two are NOT reconciled, not cross-checked and not warned about. A
    migration that made `current-quarter` follow `a` would post `Ledger-Last`
    on different rows from the compiled program, which is a table-visible
    difference (R-3, R-4).
    """
    balance = Decimal("500.00")

    #  `Scycle = 6, Period = 3` gives `a = 2`, and the gate passes because 2 * 3
    #  is exactly 6.
    second_slot_but_year_end = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=6,
        period=3,
        current_quarter=4,
        balances=(balance,),
    )
    assert second_slot_but_year_end.gate_passed is True
    assert second_slot_but_year_end.subscripts == (2,)
    assert second_slot_but_year_end.ledger_last_writes == (balance,)

    #  `Scycle = 12, Period = 3` gives `a = 4`, and the gate passes.
    fourth_slot_but_no_year_end = _end_of_period(
        incoming_a=_A_NOT_ARMED,
        scycle=12,
        period=3,
        current_quarter=1,
        balances=(balance,),
    )
    assert fourth_slot_but_no_year_end.gate_passed is True
    assert fourth_slot_but_no_year_end.subscripts == (4,)
    assert fourth_slot_but_no_year_end.ledger_last_writes == ()

    #  The counter is the ONLY thing L346 consults, so the same subscript writes
    #  `Ledger-Last` or not purely according to the counter's state.
    for quarter in (1, 2, 3, 4):
        pass_with_quarter = _end_of_period(
            incoming_a=_A_NOT_ARMED,
            scycle=12,
            period=3,
            current_quarter=quarter,
            balances=(balance,),
        )
        assert pass_with_quarter.subscripts == (4,)
        assert pass_with_quarter.ledger_last_writes == (
            (balance,) if quarter == 4 else ()
        )


# ---------------------------------------------------------------------------
#  THE REACHABLE DIVISION BY ZERO
#      if       a = 9  or  scycle <  period  ->  go to main-end. [L324-L326]
#      divide   scycle by period giving a rounded.               [L328]
#  ⛔ NO GUARD IS ADDED HERE. THE OUTCOME IS ASSERTED (R-3).
# ---------------------------------------------------------------------------


def test_the_zero_divisor_is_reachable_and_stores_nothing() -> None:
    """`period = 0` reaches L328, and the store does not happen (Q-7).

    THE GUARD DOES NOT COVER IT. [general/gl080.cbl:L325] turns the block back
    only when `scycle < period`, and no non-negative `scycle` is below zero, so a
    zero `period` walks straight into `divide scycle by period giving a rounded.`

    WHAT THE COMPILED PROGRAM DOES IS ANSWERED, and it is not what reading the
    statement suggests: GnuCOBOL 3.2 raises the SIZE ERROR condition, performs NO
    STORE, and CONTINUES - so the receiving field keeps whatever it held.
    Measured, and recorded as question Q-7 on
    `acas_posting.cobol.arithmetic.SizeErrorNoStore`. Because the question is
    answered, this test asserts the answer instead of deferring it; a strict
    `xfail` on an answered question would fail as an unexpected pass.

    BOTH ZERO-DIVISOR SHAPES ARE COVERED, because in `decimal` they are two
    different conditions - `n / 0` signals division by zero and `0 / 0` signals an
    undefined division, whose signal class is not a `ZeroDivisionError` at all -
    and the layer brings them to the SAME outcome, as COBOL does.

    ⛔ Nothing here guards, skips, or substitutes a sentinel. The one thing that is
    asserted unconditionally is that no value is silently produced.

    The connection to ANOMALY A-2: the statement that meets the zero divisor is
    the one that computes the unbounded subscript [general/gl080.cbl:L328],
    [general/gl080.cbl:L345], so a no-store leaves the PREVIOUS call's subscript
    in place - which is a second way for `a` to be carrying a value that has
    nothing to do with this cycle.
    """
    #  The guard at L325 is vacuous against a zero divisor.
    for scycle in (0, 1, 5, 127):
        assert arithmetic.compare(scycle, 0) >= 0

    #  Shape one: a non-zero dividend.
    with pytest.raises(arithmetic.SizeErrorNoStore) as non_zero:
        _end_of_period(incoming_a=_A_NOT_ARMED, scycle=5, period=0)
    assert non_zero.value.operation == "DIVIDE ... BY ... GIVING"

    #  Shape two: a zero dividend as well, which is the undefined division.
    with pytest.raises(arithmetic.SizeErrorNoStore) as both_zero:
        _end_of_period(incoming_a=_A_NOT_ARMED, scycle=0, period=0)
    assert both_zero.value.operation == "DIVIDE ... BY ... GIVING"

    #  Either spelling of the underlying condition is caught by the same clause a
    #  program module would write, so the assertion above is not brittle about
    #  which one the layer surfaces.
    assert issubclass(arithmetic.SizeErrorNoStore, ZeroDivisionError)
    assert issubclass(decimal.DivisionByZero, ZeroDivisionError)
    with pytest.raises(ZeroDivisionError):
        _end_of_period(incoming_a=_A_NOT_ARMED, scycle=5, period=0)

    #  The measured outcome, in the form a program module uses: hand the verb the
    #  receiving field's PREVIOUS value and it comes back unchanged - no store.
    for previous in (0, 7, 99):
        assert (
            arithmetic.divide_by_giving(
                5, 0, _A, rounded=True, receiver_value=previous
            )
            == previous
        )
        assert (
            arithmetic.divide_by_giving(
                0, 0, _A, rounded=True, receiver_value=previous
            )
            == previous
        )

    #  And with no previous value to return, the verb refuses rather than
    #  inventing one. A silent zero here would look like a working line and would
    #  mask a real divergence.
    with pytest.raises(arithmetic.SizeErrorNoStore):
        arithmetic.divide_by_giving(5, 0, _A, rounded=True)


def test_the_l324_guard_can_pre_empt_the_zero_divisor() -> None:
    """The zero divisor is reachable ONLY when `a` is not nine.

    [general/gl080.cbl:L324] is evaluated before [general/gl080.cbl:L328], so an
    incoming nine means the divide is never executed and a zero `period` never
    divides anything. Which of the two dispositions a run gets therefore depends
    on the value the PREVIOUS call left in `a` - the read-before-write order again,
    and a second reason the two must not be re-ordered.

    ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345]: the guard is
    the only test `a` is ever subjected to, and it is applied to the wrong
    value - the one on the way in rather than the one on the way to the subscript.
    """
    pre_empted = _end_of_period(incoming_a=_A_ARMED, scycle=5, period=0)
    assert pre_empted.divided is False
    assert pre_empted.a == _A_ARMED
    assert pre_empted.y is None

    with pytest.raises(arithmetic.SizeErrorNoStore):
        _end_of_period(incoming_a=_A_ARMED - 1, scycle=5, period=0)


# ---------------------------------------------------------------------------
#  SILENT OVERFLOW AND THE SIGN DROP
#
#  There is NO `ON SIZE ERROR` phrase and NO `REMAINDER` phrase anywhere in the
#  twelve in-scope programs, so an oversized or negative result into a two-digit
#  unsigned field is reshaped in silence. ⛔ Nothing raises, clamps or warns.
# ---------------------------------------------------------------------------


def test_silent_overflow_at_l328_changes_the_phase_disposition() -> None:
    """Two digits is not enough for `a`, and the gate feels it.

    `Scycle = 127, Period = 1` - the top of `Scycle`'s declared domain
    [copybooks/wssystem.cob:L63] - gives a quotient of 127, which does not fit
    `77 a pic 99` [general/gl080.cbl:L183]. The store keeps the LOW-ORDER TWO
    DIGITS, so `a` becomes 27, `y` becomes 27, and the gate at
    [general/gl080.cbl:L331] turns phase 5 back. Had the receiver been wide enough
    the same pair would have PASSED, which the counterfactual below shows using the
    unquantized intermediate: the overflow, not the arithmetic, decides the phase.

    `Scycle = 100, Period = 2` shows the same thing one statement later: the
    quotient 50 fits perfectly, but the product 100 does not fit `y`
    [general/gl080.cbl:L182], so `y` becomes 0 and an EXACTLY DIVISIBLE cycle is
    turned back.

    Provenance for the two stored values: the store policy for a zoned item -
    low-order digits kept, sign dropped, nothing reported - was measured on
    GnuCOBOL 3.2.0 and is recorded as question Q-5 in `acas_posting/cobol/
    usage.py`. Reproduced, not repaired (R-4).

    ANOMALY A-2 [general/gl080.cbl:L345] is present in the first case too: 27 is
    far outside `occurs 4` [copybooks/wsledger.cob:L36], so had the gate let this
    pair through, the store would have gone well past the table. Here the overflow
    closes the gate instead - which is the point, since the same overflow that
    would have produced a wild subscript is what stops the phase.
    """
    overflowing_quotient = _end_of_period(
        incoming_a=_A_NOT_ARMED, scycle=127, period=1
    )
    assert overflowing_quotient.divided is True
    assert overflowing_quotient.a == 27
    assert overflowing_quotient.y == 27
    assert overflowing_quotient.gate_passed is False

    #  THE COUNTERFACTUAL. Same operands, no receiving field, so no truncation:
    #  the quotient is 127 and the product comes back to 127, which equals
    #  `Scycle`. So the gate would have passed but for the two-digit receiver.
    #  Both counterfactual products are formed INSIDE `arithmetic.intermediate`. A
    #  bare `*` between two `Decimal`s is a CONTEXT operation and rounds its product
    #  to the ambient `prec`, so writing it outside the call would hand `compare` an
    #  operand the caller's context had already reshaped - and the assertion would
    #  then be about that context rather than about the receiver's width, which is
    #  the whole subject of this test. `intermediate` evaluates the expression at the
    #  layer's own precision and returns it exact (R-2).
    unquantized = arithmetic.intermediate(lambda: Decimal(127) / Decimal(1))
    assert unquantized == Decimal(127)
    assert (
        arithmetic.compare(
            127, arithmetic.intermediate(lambda: unquantized * Decimal(1))
        )
        == 0
    )

    overflowing_product = _end_of_period(
        incoming_a=_A_NOT_ARMED, scycle=100, period=2
    )
    assert overflowing_product.a == 50
    assert overflowing_product.y == 0
    assert overflowing_product.gate_passed is False
    assert (
        arithmetic.compare(
            100, arithmetic.intermediate(lambda: Decimal(50) * Decimal(2))
        )
        == 0
    )

    #  The two stores on their own, so the modulo is stated rather than implied.
    assert arithmetic.store(127, _A) == 127 % 100
    assert arithmetic.store(100, _Y) == 100 % 100
    assert arithmetic.store(104, _A) == 4


def test_the_signed_quotient_drops_its_sign_on_store_into_a() -> None:
    """Signed operands, unsigned receiver: the sign is simply gone.

    `Scycle` and `Period` are signed [copybooks/wssystem.cob:L63-L64] and `a` is
    not [general/gl080.cbl:L183], so a negative quotient is stored as its
    magnitude. `Scycle = 5, Period = -2` gives -2.5, which `ROUNDED` takes away
    from zero to -3, which arrives in `a` as 3. `y` is then computed from the
    SIGN-DROPPED value - 3 * -2 = -6 - and loses its own sign in turn, arriving as
    6, so the gate compares 5 against 6 and turns the phase back.

    Provenance: the zoned store policy, question Q-5.1, whose values were
    transcribed from the documented GnuCOBOL default into
    `acas_posting/cobol/usage.py` and have since been MEASURED: `Q-5.1` is
    `RESOLVED BY ORACLE` (2026-08-07) and the provisional constants turned out to be
    right, with a `COMP` item carrying a PICTURE reducing on its declared digit count
    while a `BINARY-*` item declared by USAGE ALONE wraps at its signed byte
    capacity. Note this is the store into
    WORKING STORAGE and is a separate matter from the sign lost at the bridge on
    the way to an unsigned column, which is anomaly A-11 and question Q-3. Q-3 has
    since been MEASURED - the unsigned column keeps the ABSOLUTE VALUE, magnitude
    first and then high-order truncation - so the two now agree on the rule and
    differ only in where it is applied. A-11 remains an anomaly regardless, because
    knowing what the column holds does not make holding it correct (R-4).

    ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345]: dropping the
    sign is what turns a negative quotient into a SMALL POSITIVE SUBSCRIPT rather
    than a negative one, so the out-of-range band reachable through a negative
    period is 0 and upwards rather than downwards - which is why subscript zero,
    and `Ledger-Last` with it, is the field a negative period can reach.
    """
    negative_divisor = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=5, period=-2)
    assert negative_divisor.a == 3
    assert negative_divisor.y == 6
    assert negative_divisor.gate_passed is False

    #  The two stores in isolation.
    assert arithmetic.store(-3, _A) == 3
    assert arithmetic.store(-6, _Y) == 6

    #  Sign drop and low-order truncation together, in that combination.
    assert arithmetic.store(-104, _A) == 4

    #  The operands really are signed, so the negative divisor is inside their
    #  declared domain rather than a contrived value.
    assert _PERIOD.min_value == -128
    assert _PERIOD.signed is True


def test_add_one_to_scycle_is_an_unrounded_store_that_wraps_silently() -> None:
    """`add 1 to scycle.` [general/gl080.cbl:L334], into a signed byte.

    No `ROUNDED`, and no `ON SIZE ERROR`: the receiver is
    `Scycle ... binary-char` [copybooks/wssystem.cob:L63], so the increment is an
    integer store into one signed byte and the top of the domain wraps to the
    bottom in silence. Provenance for the wrap: the default `binary-size` and
    `binary-truncate` policy, transcribed from the documented GnuCOBOL default into
    `acas_posting/cobol/usage.py` and pending measurement as question Q-5.1.

    Reproduced, not repaired: raising here would abort a phase the compiled program
    completes (R-3, R-4).
    """
    assert arithmetic.add_to(1, receiver_value=12, receiving=_SCYCLE) == 13
    at_the_top = arithmetic.add_to(
        1, receiver_value=_SCYCLE.max_value, receiving=_SCYCLE
    )
    assert at_the_top == _SCYCLE.min_value
    assert arithmetic.store(_SCYCLE.max_value + 1, _SCYCLE) == _SCYCLE.min_value

    #  Through the block, where the increment is the only thing that advances the
    #  cycle: `Period = 1`, so neither reset at [general/gl080.cbl:L358-L363]
    #  applies and the cycle simply climbs - which is what carries anomaly A-2's
    #  subscript out of the table.
    advanced = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=12, period=1)
    assert advanced.gate_passed is True
    assert advanced.scycle == 13
    assert advanced.a == 12


def test_the_two_cycle_reset_rules_are_independent_conjunctions() -> None:
    """[general/gl080.cbl:L358-L363] is two `if`s, not one choice.

    Verbatim, the two statements are `if period = 3 and scycle > 12 -> move 1 to
    scycle.` and `if period = 13 and scycle > 52 -> move 1 to scycle.` There is no
    `else` between them, both conditions are conjunctions, and both comparisons are
    STRICT - twelve does not reset a monthly cycle and fifty-two does not reset a
    weekly one. They are asserted separately and are not merged.

    Note that these resets fire AFTER the increment at [general/gl080.cbl:L334], so
    the value they test is the incremented one, and note which periods they leave
    alone: every period other than 3 and 13, `Period = 1` above all, has NOTHING
    resetting the cycle - which is precisely why anomaly A-2's subscript keeps
    climbing.
    """
    #  Period 3: `Scycle = 12` becomes 13 at L334, and 13 is above 12, so it
    #  resets. `a` is 4 here, the top of the declared table.
    monthly_reset = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=12, period=3)
    assert monthly_reset.gate_passed is True
    assert monthly_reset.a == 4
    assert monthly_reset.scycle == 1

    #  Period 3, one cycle earlier: 9 becomes 10, which is not above 12.
    monthly_no_reset = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=9, period=3)
    assert monthly_no_reset.a == 3
    assert monthly_no_reset.scycle == 10

    #  Period 13: 52 becomes 53, which is above 52, so the SECOND statement
    #  resets. The first cannot have fired - 13 is not 3 - which is what makes the
    #  two independent rather than alternatives.
    weekly_reset = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=52, period=13)
    assert weekly_reset.gate_passed is True
    assert weekly_reset.a == 4
    assert weekly_reset.scycle == 1

    #  Period 13, one cycle earlier: 39 becomes 40, not above 52.
    weekly_no_reset = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=39, period=13)
    assert weekly_no_reset.a == 3
    assert weekly_no_reset.scycle == 40

    #  Neither condition can hold at once, because a period cannot be both 3 and
    #  13, so at most one reset fires however the cycle stands.
    assert arithmetic.compare(3, 13) != 0

    #  Any other period is left to climb - the case anomaly A-2 rides on.
    for period in (1, 2, 4, 12, 14):
        climbing = _end_of_period(
            incoming_a=_A_NOT_ARMED, scycle=period * 4, period=period
        )
        assert climbing.gate_passed is True
        assert climbing.a == 4
        assert climbing.scycle == period * 4 + 1


# ---------------------------------------------------------------------------
#  THE AMBIENT-CONTEXT SABOTAGE TEST
# ---------------------------------------------------------------------------


def test_the_ambient_decimal_context_cannot_change_the_result() -> None:
    """Sabotage the process-wide `decimal` context; nothing moves (R-2, R-6).

    An accounting result that depended on the ambient `decimal` context would be a
    result that changed when some unrelated caller adjusted a global - the exact
    non-determinism rule R-6 exists to exclude. This test proves it cannot happen
    by breaking the ambient context on purpose: with the process precision cut to
    four significant digits, `12345678 / 7` would round to 1.764E+6 and arrive in
    `a` as 00 instead of 68.

    It comes back as 68, because every verb enters its own
    `INTERMEDIATE_CONTEXT` - sixty significant digits, and the direction of a store
    fixed by the descriptor rather than by the context. Both are the shipped
    layer's own, and what this test establishes is that neither moves when the
    ambient context does. The sixty digits are documented at
    `acas_posting/cobol/arithmetic.py`'s `INTERMEDIATE_PRECISION`, chosen to exceed
    every in-scope receiver; the compiler's own default was question Q-2 and is now
    `RESOLVED BY ORACLE` (2026-08-07), which is what promotes that constant from a
    working assumption to a confirmed reading. It cannot reach these two figures in
    any case, which need eight digits between them.

    THE AMBIENT CONTEXT IS THE ONLY GLOBAL THIS FILE TOUCHES, it is touched only
    here, and it is put back in a `finally` so that a failure inside the block
    cannot leak a broken context into another test.

    What is sabotaged is the whole block, so both ANOMALY A-2 and ANOMALY A-3 ride
    along: the subscript at [general/gl080.cbl:L345] and the counter at
    [general/gl080.cbl:L355-L357] come out of the sabotaged pass identical to the
    control, which is asserted by comparing the two outcomes whole rather than
    field by field.
    """
    assert arithmetic.INTERMEDIATE_PRECISION == 60
    assert arithmetic.INTERMEDIATE_CONTEXT.prec >= 60
    assert arithmetic.INTERMEDIATE_CONTEXT.rounding == cobol_field.TRUNCATING_STORE

    #  Computed BEFORE the sabotage, at whatever precision the process runs with,
    #  so the comparison afterwards is against a real control.
    control = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=17, period=2)

    context = decimal.getcontext()
    restore_to = context.prec
    try:
        context.prec = 4
        assert decimal.getcontext().prec == 4

        #  328, sabotaged. A wide dividend on purpose: four significant digits
        #  could not hold this quotient, so the ambient context would be visible.
        assert arithmetic.divide_by_giving(12345678, 7, _A, rounded=True) == 68
        #  329 and 331, sabotaged.
        assert arithmetic.multiply_by_giving(9, 2, _Y) == 18
        assert arithmetic.compare(1234567, 1234568) == -1
        #  And the whole block, which must be indistinguishable from the control.
        sabotaged = _end_of_period(incoming_a=_A_NOT_ARMED, scycle=17, period=2)
    finally:
        context.prec = restore_to

    assert decimal.getcontext().prec == restore_to
    assert sabotaged == control
    assert (sabotaged.a, sabotaged.y) == (9, 18)

    #  The same three verbs at the restored precision, as the other half of the
    #  control: identical, so the numbers above were not a coincidence.
    assert arithmetic.divide_by_giving(12345678, 7, _A, rounded=True) == 68
    assert arithmetic.multiply_by_giving(9, 2, _Y) == 18
    assert arithmetic.compare(1234567, 1234568) == -1


# ===========================================================================
# GROUP N - THE CONFORMANCE LOCK: `_end_of_period` AGAINST THE SHIPPED PROGRAM
#
# ⭐ WHY THIS SECTION EXISTS. Every assertion above consumes `_end_of_period`, which
# executes [general/gl080.cbl:L324-L363] as its own sequence over the production
# primitives. That is a SECOND SOURCE for the end-of-period logic: the shipped
# `acas_posting/programs/gl080_end_of_cycle.py` runs the same statements, and nothing
# above compares the two. They could drift apart in either direction - a fix applied to
# one and not the other, or a "tidy-up" of either - and all forty-seven assertions would
# stay green while the file's claim to describe the migration quietly became false.
#
# The sibling file test_double_entry_explosion.py had the same shape and was resolved by
# DELETING its transcription and driving the production paragraph instead. That is the
# better fix and it is not available here, for a reason worth stating rather than
# glossing: gl070's explosion is one paragraph reachable through one stubbed read, while
# gl080's end-of-period slice sits in the middle of `gl080-Main` behind the confirm gate,
# `gl080a`, the archiving branch, `gl080c` and `compress-post`. Reaching it means driving
# the whole program - which is exactly what this section does, ONCE per case, through the
# module's public `run` contract, and then requires the two to agree.
#
# WHAT THE PRODUCTION PATH CANNOT PRESENT, stated so the transcription's remaining role
# is honest rather than assumed:
#
#   - `a = 9` at the gate is UNREACHABLE. `move zero to a` [general/gl080.cbl:L290] runs
#     on every entry, and the only other writer before the gate is
#     `move 1 to a` [general/gl080.cbl:L386] inside `gl080a`. So `a` is 0 or 1 there and
#     never 9. The frozen program still tests `if a = 9` [general/gl080.cbl:L324], so the
#     branch is reproduced (R-4) and `_end_of_period` is how it is exercised - but it is
#     exercised as a SOURCE-LEVEL branch, not as a reachable state.
#   - `a = 1` at the gate ABORTS BEFORE IT. `gl080a` setting `a` to 1 means batches are
#     outstanding, and [general/gl080.cbl:L307-L313] leaves through `main-end` on that
#     alone. So the gate only ever sees `a = 0`.
#
# Those two facts also correct something this file used to assert. `_end_of_period`'s
# docstring said `a` "is initialised ONCE, when the module is loaded, and gl080 leaves
# through goback, so a second call sees what the first left". [general/gl080.cbl:L290]
# refutes that: `a` is zeroed on every entry. What survives of the point is narrower and
# still worth making - `a` is READ at L324 before L328 writes it, so within one run it
# carries state from `gl080a` into the gate.
#
# NO DATABASE. Every facade verb is replaced by a recorder; the nominal reader presents
# a fixed list of balances and then reports AT END, which is what the frozen loop's
# `at end go to loop-end` [general/gl080.cbl:L343-L344] responds to.
# ===========================================================================


def _drive_shipped_gl080(
    *,
    scycle: int,
    period: int,
    current_quarter: int,
    balances: tuple[Decimal, ...],
) -> dict[str, object]:
    """Run the SHIPPED `gl080` end to end and report what its end-of-period pass did.

    Args:
        scycle: `Scycle` on the system record [copybooks/wssystem.cob:L63].
        period: `Period` [copybooks/wssystem.cob:L64].
        current_quarter: `Current-Quarter` [copybooks/wssystem.cob:L110].
        balances: The `Ledger-Balance` of each row the nominal reader presents.

    Returns:
        `a`, `y`, `scycle`, `current_quarter` as the run left them, plus the quarter
            subscript actually written per row and the `Ledger-Last` writes observed.
    """
    from acas_posting.dal import facade
    from acas_posting.programs import gl080_end_of_cycle as gl080
    from acas_posting.records.calling_data import WsCallingData
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    system_record = SystemRecord()
    system_record.system_data_block.scycle = scycle
    system_record.system_data_block.period = period
    system_record.system_data_block.current_quarter = current_quarter
    #  `88 Archiving value "Y"` [copybooks/wssystem.cob:L165]: anything else sends
    #  [general/gl080.cbl:L315-L320] down the deletion branch instead, which is the
    #  branch this case wants because archiving would open a sequential archive file.
    system_record.general_ledger_block.arch = "N"
    #  `88 FS-Cobol-Files-Used value zero` / `88 FS-MySql-Used value 1`
    #  [copybooks/wssystem.cob:L112-L114]. ONE is the RDB mode, and it is required
    #  rather than cosmetic: `compress-post` leaves immediately on
    #  `if not FS-Cobol-Files-Used` [general/gl080.cbl:L632-L635], and with the default
    #  zero it instead reaches the record-length check at [general/gl080.cbl:L643-L649]
    #  and stops the run - which is the frozen program's own behaviour for a COBOL
    #  indexed store the migration does not have.
    system_record.system_data_block.rdbms_flat_statuses.file_system_used = 1

    #  Every balance presented in turn, then AT END. `10` is FS-Reply's end-of-file.
    presented = {"index": 0}
    quarter_writes: list[int] = []
    ledger_last_writes: list[Decimal] = []

    def _nominal_read_next(ctx: object) -> None:
        index = presented["index"]
        if index >= len(balances):
            ctx.file_access.fs_reply = 10
            return
        presented["index"] = index + 1
        ctx.record.ledger_balance = balances[index]
        ctx.file_access.fs_reply = 0

    def _nominal_rewrite(ctx: object) -> None:
        #  WHICH occurrence the pass stored into, read back off the record rather than
        #  inferred: exactly one quarter differs from its seeded zero after the store.
        #  `05 Ledger-Q occurs 4` [copybooks/wsledger.cob:L36] is carried as a
        #  sequence, and it is read positionally with `start=1` because COBOL
        #  subscripts are ONE-based - turning them into Python indices here would be
        #  the very `a - 1` mistake ANOMALY A-2's reproduction exists to avoid.
        quarters = tuple(ctx.record.quarters_table.ledger_q)
        quarter_writes.extend(
            ordinal
            for ordinal, value in enumerate(quarters, start=1)
            if value != Decimal("0.00")
        )
        if ctx.record.ledger_last != Decimal("0.00"):
            ledger_last_writes.append(ctx.record.ledger_last)
        ctx.file_access.fs_reply = 0

    def _silent(ctx: object) -> None:
        ctx.file_access.fs_reply = 10 if _silent.at_end else 0

    _silent.at_end = True

    swapped: dict[str, object] = {}
    verbs = {
        "gl_nominal_read_next": _nominal_read_next,
        "gl_nominal_rewrite": _nominal_rewrite,
    }
    for name in (
        "gl_batch_open",
        "gl_batch_open_input",
        "gl_batch_read_next",
        "gl_batch_rewrite",
        "gl_batch_close",
        "gl_nominal_open",
        "gl_nominal_close",
        "gl_posting_open",
        "gl_posting_open_input",
        "gl_posting_open_output",
        "gl_posting_read_next",
        "gl_posting_write",
        "gl_posting_delete",
        "gl_posting_close",
    ):
        verbs.setdefault(name, _silent)

    try:
        for name, replacement in verbs.items():
            swapped[name] = getattr(facade, name)
            setattr(facade, name, replacement)
        gl080.run(
            WsCallingData(),
            system_record,
            "21/09/2025",
            FileDefs(),
            file_access=FileAccess(),
            dal_common=AcasDalCommonData(),
            run_confirmed=True,
        )
    finally:
        for name, original in swapped.items():
            setattr(facade, name, original)

    return {
        "scycle": int(system_record.system_data_block.scycle),
        "current_quarter": int(system_record.system_data_block.current_quarter),
        "quarter_writes": tuple(quarter_writes),
        "ledger_last_writes": tuple(ledger_last_writes),
        "rows_presented": presented["index"],
    }


@pytest.mark.parametrize(
    ("scycle", "period", "current_quarter", "balances"),
    [
        #  Exactly divisible, so the gate at L331 passes and the quarter pass runs.
        #  12 / 3 = 4 -> subscript 4, the last occurrence of `occurs 4`.
        pytest.param(12, 3, 4, (Decimal("4321.09"),), id="12-over-3-quarter-4"),
        #  3 / 3 = 1 -> subscript 1, and `current-quarter` is not 4 so `Ledger-Last`
        #  is left alone. The A-3 divergence in its visible form.
        pytest.param(3, 3, 1, (Decimal("117.53"),), id="3-over-3-quarter-1"),
        #  NOT exactly divisible: 7 / 3 rounds to 2, 2 * 3 = 6, 7 != 6, so L331 leaves
        #  and nothing is stored at all.
        pytest.param(7, 3, 2, (Decimal("777.01"),), id="7-over-3-gate-fails"),
        #  scycle < period, so the L324-L326 guard pre-empts the divide entirely.
        pytest.param(2, 3, 1, (Decimal("500.00"),), id="scycle-below-period"),
        #  More than one row, so the subscript is shown to be per-pass and not per-row.
        pytest.param(
            12,
            12,
            4,
            (Decimal("100.00"), Decimal("200.00")),
            id="two-rows-one-subscript",
        ),
    ],
)
def test_the_transcription_agrees_with_the_shipped_program(
    scycle: int, period: int, current_quarter: int, balances: tuple[Decimal, ...]
) -> None:
    """`_end_of_period` and the SHIPPED gl080 must agree, case by case.

    This is what stops the transcription above from being an independent second source.
    `incoming_a` is 0 because that is the only value the production path can present at
    the gate - see the section comment - so the two are compared on exactly the states
    the shipped program can actually be in.

    Args:
        scycle: The accounting cycle.
        period: The period length.
        current_quarter: The system record's own rotating counter.
        balances: The nominal balances the reader presents.
    """
    transcribed = _end_of_period(
        incoming_a=0,
        scycle=scycle,
        period=period,
        current_quarter=current_quarter,
        balances=balances,
    )
    shipped = _drive_shipped_gl080(
        scycle=scycle,
        period=period,
        current_quarter=current_quarter,
        balances=balances,
    )

    assert shipped["scycle"] == transcribed.scycle, (
        f"`add 1 to scycle` [general/gl080.cbl:L334] left {shipped['scycle']} in the "
        f"shipped program and {transcribed.scycle} in the transcription above"
    )
    assert shipped["current_quarter"] == transcribed.current_quarter, (
        f"the rotating counter [general/gl080.cbl:L355-L357] left "
        f"{shipped['current_quarter']} in the shipped program and "
        f"{transcribed.current_quarter} in the transcription above"
    )
    assert shipped["quarter_writes"] == transcribed.subscripts, (
        f"`move ledger-balance to ledger-q (a)` [general/gl080.cbl:L345] stored into "
        f"occurrence(s) {shipped['quarter_writes']} in the shipped program and "
        f"{transcribed.subscripts} in the transcription above. ANOMALY A-2 is that "
        f"this subscript is the ROUNDED quotient used with no bounds test; the two "
        f"sources must agree on it or one of them has been 'fixed' (R-4)."
    )
    assert shipped["ledger_last_writes"] == transcribed.ledger_last_writes, (
        f"`move ledger-balance to ledger-last` [general/gl080.cbl:L346-L347] fired for "
        f"{shipped['ledger_last_writes']} in the shipped program and "
        f"{transcribed.ledger_last_writes} in the transcription above. ANOMALY A-3 is "
        f"that this consults `Current-Quarter` and not `a`."
    )
    #  The reader is exhausted only on the paths that reach the loop, which is itself a
    #  claim about the gate: a pre-empted or failed gate must present NO rows.
    expected_rows = len(balances) if transcribed.gate_passed else 0
    assert shipped["rows_presented"] == expected_rows, (
        f"the shipped program presented {shipped['rows_presented']} nominal row(s) and "
        f"the transcription says the gate {'passed' if transcribed.gate_passed else 'did not pass'}, "
        f"which implies {expected_rows}"
    )


# ---------------------------------------------------------------------------
#  THE ZERO DIVISOR'S DATABASE CONSEQUENCE, MEASURED END TO END  (Q-7, R-6)
#
#  The section above establishes that the zero divisor is reachable and stores
#  nothing. That is where the analysis used to stop, and stopping there hides the
#  part that reaches a table. Measured on the compiled oracle 2026-08-07, the
#  chain runs on past the divide:
#
#    L290  move zero to a                     a is 0 on every entry
#    L324  if a = 9 or scycle < period        0 = 9 false; 0 < 0 false -> NOT taken
#    L328  divide scycle by period giving a   SIZE ERROR, NO STORE, a stays 0,
#          rounded                            and the RUN CONTINUES (exit 0)
#    L329  multiply a by period giving y      0 * 0 -> y = 0
#    L331  if scycle not = y go to main-end   0 not= 0 is FALSE -> NOT taken
#    L334  add 1 to scycle
#    L345  move ledger-balance to             subscript 0, on every ledger row
#          ledger-q (a)
#
#  So `period = 0` with `scycle = 0` does not merely fail to store a quotient - it
#  walks into phase 5 carrying subscript ZERO, and subscript zero is not harmless.
#  Measured against the frozen 126-byte `copybooks/wsledger.cob`: occurrence 0
#  occupies bytes 47-52, which is `Ledger-Last` - a REAL `GLLEDGER-REC` COLUMN.
#  Every row the loop touches therefore gets `LEDGER-LAST` overwritten with
#  `LEDGER-BALANCE`, gets NO quarter column updated at all, and is then persisted
#  by `GL-Nominal-Rewrite`.
#
#  ⭐ WHY IT IS PARTICULARLY HARD TO SPOT, and the reason it is worth a section of
#  its own: [general/gl080.cbl:L346-L347] contains a LEGITIMATE
#  `move ledger-balance to ledger-last`, taken when `current-quarter = 4`. The
#  corrupting store writes THE SAME VALUE INTO THE SAME COLUMN. On a quarter-4 run
#  it is invisible; on quarters 1 to 3 it produces a `LEDGER-LAST` that looks
#  entirely plausible and is a quarter early. No diagnostic, no status, no abort.
#
#  ⛔ NOTHING IS GUARDED. `scycle = 5` escapes through the L331 gate and
#  `scycle = 0` does not, and both outcomes are asserted rather than prevented.
# ---------------------------------------------------------------------------

#: What the compiled oracle kept, per subscript, starting from
#: balance 11.11 / last 22.22 / quarters 33.33, 44.44, 55.55, 66.66. Copied from
#: the probe output, NOT recomputed from the layout - so a drift in the offset
#: arithmetic breaks these rather than moving with it.
_MEASURED_SUBSCRIPT_LANDINGS: Final[
    tuple[tuple[int, str, tuple[str, str, str, str]], ...]
] = (
    (0, "11.11", ("33.33", "44.44", "55.55", "66.66")),
    (1, "22.22", ("11.11", "44.44", "55.55", "66.66")),
    (5, "22.22", ("33.33", "44.44", "55.55", "66.66")),
)


def test_the_zero_divisor_lets_control_reach_phase_five() -> None:
    """`scycle = 0` passes the L331 gate; `scycle = 5` does not.

    This is the fact the no-store assertion above does not reach. Once the divide
    has declined to store, `y` is computed from the UNCHANGED `a` - and when
    `period` is zero, `y` is zero whatever `a` holds. The gate then compares
    `scycle` against zero, so the phase turns back for every non-zero cycle and
    proceeds for a zero one. A run with `scycle = 0, period = 0` therefore enters
    the phase-5 ledger loop, which is where the table effect happens.

    The shipped primitives are driven directly, with the receiving field's
    previous value handed in the way `gl080` hands it
    [general/gl080.cbl:L328 -> the module's `receiver_value=st.a`], rather than the
    transcription being consulted - the point is what the production layer does.
    """
    #  L328 with the receiver armed, as the shipped module calls it: no store.
    for scycle, previous in ((0, 0), (5, 77), (0, 77)):
        kept = arithmetic.divide_by_giving(
            scycle, 0, _A, rounded=True, receiver_value=previous
        )
        assert kept == previous, (
            f"scycle={scycle} / period=0 must leave the receiver at {previous}; "
            f"the compiled oracle left it untouched"
        )

    #  L329, then the L331 gate, for the two cycles that decide the branch.
    for scycle, reaches_phase_five in ((0, True), (5, False), (1, False)):
        a_after = arithmetic.divide_by_giving(
            scycle, 0, _A, rounded=True, receiver_value=0
        )
        y_after = arithmetic.multiply_by_giving(a_after, 0, _Y, rounded=False)
        assert y_after == 0, "period = 0 forces y to zero whatever `a` holds"
        gate_passes = arithmetic.compare(scycle, y_after) == 0
        assert gate_passes is reaches_phase_five, (
            f"scycle={scycle}, period=0: the L331 gate "
            f"{'must pass' if reaches_phase_five else 'must turn the phase back'}"
        )

    #  And the subscript phase 5 would carry in the reachable case is ZERO - the
    #  value L290 put there, which L328 declined to replace.
    assert (
        arithmetic.divide_by_giving(0, 0, _A, rounded=True, receiver_value=0) == 0
    )


def test_subscript_zero_writes_a_real_ledger_column() -> None:
    """Subscript 0 lands on `Ledger-Last`, and no quarter column moves.

    Driven through the SHIPPED store primitive over the shipped record group, so
    the assertion is about `acas_posting` rather than about a layout recomputed
    here. The expected values are the compiled oracle's, captured against the
    frozen `copybooks/wsledger.cob` whose own header declares 126 bytes.

    Subscript 1 is included as the in-range control - it must move `Ledger-Q1` and
    leave `Ledger-Last` alone - and subscript 5 as the harmless out-of-range
    control, landing in the trailing `03 filler pic x(50)`
    [copybooks/wsledger.cob:L37], which carries no column.

    ⛔ A Python `[a - 1]` would make subscript 0 the LAST occurrence, which
    corresponds to nothing the compiled program does; `Ledger-Q4` staying at
    66.66 in the first row below is what rules that out.
    """
    from acas_posting.cobol import move
    from acas_posting.programs import gl080_end_of_cycle as gl080
    from acas_posting.records.gl_ledger import WsLedgerRecord

    for subscript, expected_last, expected_quarters in _MEASURED_SUBSCRIPT_LANDINGS:
        record = WsLedgerRecord()
        record.ledger_balance = Decimal("11.11")
        record.ledger_last = Decimal("22.22")
        for occurrence, seeded in enumerate(
            ("33.33", "44.44", "55.55", "66.66"), start=1
        ):
            setattr(record.quarters, f"ledger_q{occurrence}", Decimal(seeded))

        after = move.subscripted_store(
            gl080._LEDGER_RECORD_GROUP,
            gl080._ledger_record_values(record),
            member="Ledger-Q (1)",
            element_length=gl080._LEDGER_Q_ELEMENT_BYTES,
            subscript=subscript,
            value=move.move(
                record.ledger_balance, gl080._LEDGER_Q, sending_field=gl080._LEDGER_BALANCE
            ),
            statement="general/gl080.cbl:L345",
        )

        assert after["Ledger-Last"] == Decimal(expected_last), (
            f"subscript {subscript}: the compiled oracle left Ledger-Last at "
            f"{expected_last}"
        )
        for occurrence, expected in enumerate(expected_quarters, start=1):
            assert after[f"Ledger-Q ({occurrence})"] == Decimal(expected), (
                f"subscript {subscript}: the compiled oracle left "
                f"Ledger-Q ({occurrence}) at {expected}"
            )

    #  The two claims that make the finding a finding rather than an offset note:
    #  subscript 0 reaches a COLUMN, and it reaches it INSTEAD of any quarter.
    zero_case = dict(zip(("subscript", "last", "quarters"), _MEASURED_SUBSCRIPT_LANDINGS[0]))
    assert zero_case["last"] == "11.11", "subscript 0 must receive the balance"
    assert zero_case["quarters"] == ("33.33", "44.44", "55.55", "66.66"), (
        "subscript 0 must leave every quarter untouched"
    )


# ==========================================================================
#  MERGED GROUP - was tests/arithmetic/test_gl080_shipped_end_of_cycle.py
#
#  Relocated verbatim so that this directory holds exactly the fourteen test
#  modules the Agent Action Plan section 0.3.1 inventory names. Nothing was
#  rewritten: the group's own preamble follows, as its author wrote it, and
#  every test below is the test that ran under the old file name.
# ==========================================================================
#
#  The SHIPPED `gl080` end-of-cycle program, driven paragraph by paragraph.
#
#  WHY THIS FILE EXISTS, STATED AS THE GAP IT CLOSES. `test_gl080_cycle_divide_rounded.py`
#  locks the arithmetic of `general/gl080.cbl`'s end-of-period block against a MODEL of that
#  block written inside the test file - `_end_of_period` - and it locks it thoroughly: the
#  `ROUNDED` divide, the round-trip gate, the sign drop, the silent overflow, the two cycle
#  resets and the ambient-context sabotage. What it cannot do is prove that
#  `acas_posting/programs/gl080_end_of_cycle.py` - the module the CLI actually dispatches -
#  still does any of it. Its brief forbids it from importing `acas_posting.programs`:
#
#      Must NOT import: `acas_posting.dal.*`, `cli`, `programs`, `clock`, `dates`,
#      `workfiles`, `harness`, `sqlalchemy`, `mysql.connector`, `numpy`, `pandas` ...
#
#  So the model and the shipped module could drift apart in either direction and every test
#  in that file would stay green. Deleting `rounded=True` from
#  [general/gl080.cbl:L328]'s reproduction, clamping the unbounded subscript into 1..4,
#  reconciling the two notions of quarter, reversing the two cycle-reset conjunctions,
#  stamping the batch before archiving it rather than after - none of those would be caught.
#  THIS FILE DRIVES THE SHIPPED MODULE, and every assertion below is an observation of the
#  module's own behaviour rather than of a transcription of it.
#
#  The two files are therefore complementary and neither is redundant: that one proves what
#  the frozen COBOL MEANS, this one proves that the SHIPPED PROGRAM DOES IT. Where they
#  assert the same figure they are meant to, and a divergence between them is exactly the
#  signal both exist to raise.
#
#  ⭐ WHAT IS NOT CLOSED HERE, AND WHY. `gl080` is reached by no scenario in
#  `harness/scenarios/`, so no end-to-end diff covers it; that declination is recorded in
#  `docs/migration/ambiguity-resolutions.md` section 16.1 and it is bounded by the Agent
#  Action Plan rather than by preference. Section 0.3.1 fixes the scenario set at EIGHT
#  YAML definitions and eight test files, and section 0.8.5's mandated scenario set - clean
#  batch per ledger, mixed accepted-and-rejected, period-end totals, control-total mismatch
#  and empty batch - contains no end-of-cycle journey. Adding a ninth scenario would put
#  work outside the plan; driving the shipped program directly closes the coverage half of
#  the gap without doing that, and the state half stays recorded as a declination.
#
#  HOW THE MODULE IS DRIVEN. Two seams, both already in the shipped code and neither added
#  for the tests:
#
#    (1) `run(...)` [acas_posting/programs/gl080_end_of_cycle.py] takes the frozen
#        `PROCEDURE DIVISION USING` list - `ws-calling-data`, `system-record`, `to-day`,
#        `file-defs` [general/gl080.cbl:L269-L272] - plus the three promoted interactive
#        answers Agent Action Plan section 0.3.4 turns into parameters. Every test that
#        cares about the ROUTE enters here, because entering anywhere else would prove
#        the route by assuming it.
#    (2) `_Gl080Storage` is the program's working storage as one object, and the module
#        reaches every handler through the MODULE-GLOBAL name `facade`. A test that needs
#        to see `st.a`, `st.y` or the flat archive file after the run builds the storage
#        itself and calls the section function, exactly as the COBOL `perform` does.
#
#  ⛔ NO DATABASE, NO COBOL, NO SUBPROCESS (R-1). The handlers are replaced by
#  `_GlFacadeDouble`, which serves rows out of a list and records what it was asked to do.
#  The two flat files the program declares - `fd archive` [general/gl080.cbl:L156] and
#  `fd work-file` [general/gl080.cbl:L170] - are already in-process objects in the shipped
#  module (`_ArchiveFile`, `_WorkFile`), so nothing touches a filesystem either. The import
#  of `acas_posting.programs.gl080_end_of_cycle` pulls `acas_posting.dal.facade` and the
#  pinned MySQL driver in transitively; `_shipped_gl080` removes every tier-isolated name it
#  added, so the three isolation assertions this directory carries
#  (`test_comp3_packed_decimal.py`, `test_comp_binary.py`, `test_pic_field_descriptors.py`)
#  keep holding whatever order the files run in.
#
#  THE RULES, AS THEY BIND THIS FILE (Agent Action Plan section 0.7.2):
#
#    R-1  No COBOL at runtime. See above. No `harness` import, no subprocess, no FFI.
#    R-2  Zero binary floating point. Every money figure below is a `Decimal` built from a
#         string and every counter is an `int`. ⛔ no `float(`, no `pytest.approx`, no
#         `math.isclose`, no tolerance.
#    R-3  No new validations. ⭐⭐ THE QUARTER SUBSCRIPT STAYS UNBOUNDED and the two
#         notions of quarter stay unreconciled. A test that asserted an `IndexError`,
#         a clamp or a warning would be asserting a validation the frozen program does not
#         perform.
#    R-4  Anomalies reproduced, never fixed. This file locks ANOMALY A-2 (the unbounded
#         subscript at [general/gl080.cbl:L328] and [general/gl080.cbl:L345]) and
#         ANOMALY A-3 (two disagreeing notions of "current quarter",
#         [general/gl080.cbl:L346] against [general/gl080.cbl:L355-L357]) IN THE SHIPPED
#         MODULE, so that a future well-intentioned correction fails the suite.
#    R-5  Traceability. Every test names the `[general/gl080.cbl:Lnnn]` it drives and the
#         shipped function that reproduces it.
#    R-6  Compiled behaviour is the tie-breaker. Where the compiled disposition is not
#         settled the question is named - Q-19 for what an overrunning subscript writes
#         past the record, Q-23 for the record-length stop - and the test asserts the
#         SHIPPED behaviour without claiming the oracle has spoken.
#
#  Also binding - Agent Action Plan section 0.8.4: no timing assertion and no performance
#  measurement appears anywhere in this file. And section 0.8.1: the frozen COBOL, the
#  bridges, the copybooks and `mysql/ACASDB.sql` are read-only, and nothing here writes to
#  any of them.
#
#  THE FROZEN BLOCK THIS FILE DRIVES, verbatim from the checkout, so that a reader can
#  check every assertion below against the source without leaving the file::
#
#       283  display  prog-name  at 0101 ...
#       288  move     1  to  File-Key-No.
#       289  move     zero  to  a.
#       299  accept   keyed-reply  at 1065  with update auto.
#       302  goback.                                  *> run NOT confirmed
#       304  display  "Phase - 1.  Batch Check" ...
#       305  perform  gl080a.
#       308  if       a = 1
#       313           go to  main-end.                *> batches outstanding
#       315  if       archiving
#       317           perform  gl080b               *> Phase 2, Transaction Archiving
#       318  else
#       320           perform  gl080c.              *> Phase 3, Transaction Deletion
#       322  perform  compress-post.                *> Phase 4, Posting Contraction
#       324  if       a = 9
#       325      or   scycle <  period
#       326           go to  main-end.
#       328  divide   scycle by period giving a rounded.
#       329  multiply a  by  period  giving  y.
#       331  if       scycle not = y
#       332           go to  main-end.
#       334  add      1  to scycle.
#       337  perform  GL-Nominal-Open.
#       339  loop.
#       342  perform  GL-Nominal-Read-Next.
#       343  if       fs-reply = 10
#       344           go to  loop-end.
#       345  move     ledger-balance  to  ledger-q (a).
#       346  if       current-quarter = 4
#       347           move  ledger-balance  to  ledger-last.
#       348  perform  GL-Nominal-Rewrite.
#       349  go       to loop.
#       351  loop-end.
#       354  perform  GL-Nominal-Close.
#       355  add      1  to  current-quarter.
#       356  if       current-quarter = 5
#       357           move  1  to  current-quarter.
#       358  if       period = 3
#       359      and  scycle > 12
#       360           move 1 to scycle.
#       361  if       period = 13
#       362      and  scycle > 52
#       363           move 1 to scycle.
#       365  main-end.
#       366  goback.
#
#  ⚠ PROVENANCE OF RULES. There is no user rules document - `review_rules` returns exactly
#  `No user rules provided.` The six rules above are the Technical Specification's, section
#  0.7.2, and nothing has been invented to fill the gap.
#
# ==========================================================================


# ---------------------------------------------------------------------------
#  1.  THE IMPORT IS REAL, IT IS FRESH, AND IT LEAVES NOTHING RESIDENT
# ---------------------------------------------------------------------------

#: The shipped module under test. Named once so that a rename is a single edit and a
#: grep for the module finds this file.
_GL080: Final[str] = "acas_posting.programs.gl080_end_of_cycle"

#: The module-name prefixes this directory's own isolation assertions forbid. The same
#: list the sibling loaders carry, kept identical on purpose: a prefix that appears in
#: one list and not another is a hole.
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

#: `fs-reply` for a successful handler call, `88 fn-Ok` in the shared vocabulary
#: [copybooks/wsfnctn.cob:L25]. Both flat files in `gl080` declare the SAME field as
#: their FILE STATUS [general/gl080.cbl:L140], [general/gl080.cbl:L146].
_FS_OK: Final[int] = 0

#: `if fs-reply = 10` - the at-end every read loop in the program tests
#: [general/gl080.cbl:L343], [general/gl080.cbl:L379], [general/gl080.cbl:L422],
#: [general/gl080.cbl:L456], [general/gl080.cbl:L577], [general/gl080.cbl:L613].
_FS_AT_END: Final[int] = 10

#: `88 Archived value 2.` [copybooks/wsbatch.cob:L32] - what BOTH the archiving and the
#: deletion walk stamp into `Cleared-Status` [general/gl080.cbl:L430],
#: [general/gl080.cbl:L585].
_CLEARED_ARCHIVED: Final[int] = 2

#: The run date the tests hand in through `SYSTEM-REC`, and therefore the value both
#: walks stamp into `Stored` [general/gl080.cbl:L431], [general/gl080.cbl:L586]. A fixed
#: figure, never `date.today()`: rule R-6's determinism requirement is that every date
#: arrives through linkage, and this file is one of its witnesses.
_RUN_DATE: Final[int] = 20250921

#: `01 to-day pic x(10).` [general/gl080.cbl:L267] in the DD/MM/CCYY form the menu
#: shell supplies [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]. Pinned for the same
#: reason.
_TO_DAY: Final[str] = "21/09/2025"

#: `88 Archiving value "Y".` [copybooks/wssystem.cob:L165] over `Arch pic x`
#: [copybooks/wssystem.cob:L164] - the switch [general/gl080.cbl:L315] tests to choose
#: phase 2 over phase 3.
_ARCHIVING: Final[str] = "Y"

#: Anything that is not `"Y"`. The frozen condition name has one value, so one
#: counter-example is the whole of the else arm.
_NOT_ARCHIVING: Final[str] = " "

#: `88 FS-Cobol-Files-Used value zero.` over `File-System-Used`
#: [copybooks/wssystem.cob]. ZERO means Cobol files, so a NON-zero value is the RDBMS
#: configuration every scenario in this migration runs in, and it is the value that
#: makes `compress-post` [general/gl080.cbl:L633-L635] leave immediately.
_FILE_SYSTEM_RDBMS: Final[int] = 1

#: The Cobol-files configuration. Reachable, and phase 4 runs in it - see the
#: record-length stop, question Q-23.
_FILE_SYSTEM_COBOL: Final[int] = 0


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix this tier must not leave loaded?

    Matched as a package prefix - the exact name, or the name plus a dot - so a
    submodule cannot slip past and a merely similar name is not caught by accident.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped_gl080() -> Iterator[types.ModuleType]:
    """Import the shipped `gl080` module for one test, leaving `sys.modules` as found.

    ⭐ THE IMPORT IS NOT OPTIONAL AND IT IS NOT MEMOISED, for the reasons the sibling
    loaders in this directory record: `pytest.importorskip` turns the one failure this
    file exists to catch - a shipped module that cannot be imported at all - into a
    PASS, and a memoised module is already resident, so the purge on the way out would
    remove nothing and every freshness claim would be about a module that had never
    left. The pinned MySQL driver the skip reason used to blame is a hard requirement of
    `requirements.txt`, so its absence is a broken environment rather than a supported
    configuration.

    Yields:
        The imported module.

    Raises:
        AssertionError: The module was already resident on the way in, did not become
            resident, or a tier-isolated name survived the purge.
        ImportError: The module could not be imported. Deliberately NOT a skip.
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
    assert _GL080 not in sys.modules, (
        f"{_GL080} survived the eviction above, so its top-level code will "
        f"NOT re-execute and the purge on the way out would remove nothing."
    )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(_GL080)
        assert sys.modules.get(_GL080) is module, (
            f"{_GL080} did not become resident under its own name, so nothing about a "
            f"fresh import has been established."
        )
        #  The transitive pull is the point of the purge: a program module reaches its
        #  handlers through `acas_posting.dal.facade`, which imports the driver.
        assert any(
            _is_tier_isolated_name(name) for name in set(sys.modules) - before
        ), (
            "importing the shipped program added no tier-isolated name at all, which "
            "would mean the module no longer reaches the data-access layer - the seam "
            "every test in this file drives."
        )
        yield module
        completed = True
    finally:
        added = set(sys.modules) - before
        for name in sorted(added, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
        )
        #  Only when the body itself succeeded, so a real failure is never masked by a
        #  second assertion about housekeeping.
        if completed:
            assert not residue, (
                f"importing {_GL080} left {residue} resident after the purge, so the "
                f"tier-isolation assertions in test_comp3_packed_decimal.py, "
                f"test_comp_binary.py and test_pic_field_descriptors.py would depend on "
                f"file order rather than on this loader."
            )


# ---------------------------------------------------------------------------
#  2.  THE HANDLER DOUBLE
#
#      The program reaches sixteen facade verbs across three entities, and every one
#      of them goes through the module-global name `facade`. Replacing that name is
#      the whole of the substitution: nothing is patched inside the program, no
#      function is wrapped, and the program cannot tell the difference because the
#      COBOL cannot either - a `CALL "acas005"` resolves at run time.
#
#      WHY THE VERBS ARE SPELLED OUT ONE BY ONE rather than answered by a catch-all.
#      A catch-all would keep working after a verb was renamed or dropped in the
#      shipped module, which is precisely a change this file should fail on. Defining
#      the sixteen explicitly makes the verb vocabulary a CHECKED FACT: an unexpected
#      attribute raises `AttributeError` out of the double and the test fails.
#
#      WHAT A REAL HANDLER DOES, and therefore what the double does. It MUTATES THE
#      CALLER'S RECORD IN PLACE - the bridge's unload paragraph moves host variables
#      into the `01` the caller passed [common/glpostingMT.cbl:L992-L998] - and it
#      writes its status into `Fs-Reply` on the shared `File-Access` block
#      [copybooks/wsfnctn.cob:L25]. It does NOT hand the record back as a return
#      value, and the shipped program reads no return value either, so the double
#      returns None: a program that started depending on a returned status would fail
#      here rather than pass quietly.
# ---------------------------------------------------------------------------


def _apply(record: object, values: Mapping[str, object]) -> None:
    """Move `values` into `record`, keyed by dotted attribute path.

    A dotted path because the record layouts are nested groups - `WS-Post-Key` inside
    `WS-Posting-Record` [copybooks/wspost.cob:L11-L14] - and the group names are part of
    the field's identity in the COBOL.

    Args:
        record: The `01` the handler was handed.
        values: Dotted attribute path to value, as a seeded row.
    """
    for dotted, value in values.items():
        target = record
        parts = dotted.split(".")
        for part in parts[:-1]:
            target = getattr(target, part)
        assert hasattr(target, parts[-1]), (
            f"the seeded row names {dotted!r}, which is not a field of "
            f"{type(record).__name__} - the record layer and this file disagree about "
            f"the layout, which is a real failure rather than a typo to route around."
        )
        setattr(target, parts[-1], value)


class _GlFacadeDouble:
    """The three General Ledger entity facades, in memory, with a call log.

    Attributes:
        calls: Every verb name in invocation order. THE ORDER IS AN ASSERTED FACT in
            several tests below, because the frozen program's phase order is one of
            the four things Agent Action Plan section 0.8.1 requires be preserved.
        ledger_rewrites: One snapshot per `GL-Nominal-Rewrite`, taken at the moment of
            the call. Snapshots rather than references, because the program reuses the
            same `01` for every row and a reference would show only the last one.
        batch_rewrites: One snapshot per `GL-Batch-Rewrite`.
        posting_deletes: The `(batch, post-number)` of every `GL-Posting-Delete`.
        posting_writes: The `(batch, post-number)` of every `GL-Posting-Write`.
    """

    def __init__(
        self,
        facade_module: types.ModuleType,
        *,
        batches: Sequence[Mapping[str, object]] = (),
        postings: Sequence[Mapping[str, object]] = (),
        ledgers: Sequence[Mapping[str, object]] = (),
    ) -> None:
        #  The real context class, not a stand-in: `_Gl080Storage.nominal_ctx()` and its
        #  two siblings build one per verb, and the parameter list they fill is the
        #  handler's five-argument `CALL` block [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57].
        #  Keeping the real class means those three methods are exercised for real.
        self.FacadeContext = facade_module.FacadeContext
        self.calls: list[str] = []
        self._rows: dict[str, list[Mapping[str, object]]] = {
            "batch": list(batches),
            "posting": list(postings),
            "ledger": list(ledgers),
        }
        self._cursor: dict[str, int] = {"batch": 0, "posting": 0, "ledger": 0}
        self.ledger_rewrites: list[dict[str, Any]] = []
        self.batch_rewrites: list[dict[str, Any]] = []
        self.posting_deletes: list[tuple[int, int]] = []
        self.posting_writes: list[tuple[int, int]] = []

    # -- the shared mechanics -------------------------------------------------

    def _log(self, verb: str, ctx: Any) -> None:
        self.calls.append(verb)
        ctx.file_access.fs_reply = _FS_OK

    def _open(self, verb: str, ctx: Any, entity: str) -> None:
        """An OPEN positions at the first record, which is why the cursor resets.

        `START`-less sequential access is what both walks use, and a real
        `GL-Batch-Open` followed by `GL-Batch-Read-Next` reads the FIRST row however
        many times the file has been opened. Phase 1 and phase 2 or 3 each open the
        batch file in turn [general/gl080.cbl:L376], [general/gl080.cbl:L419],
        [general/gl080.cbl:L574], so without the reset the second walk would see an
        exhausted file and every archiving and deletion test would pass by seeing
        nothing at all.
        """
        self._cursor[entity] = 0
        self._log(verb, ctx)

    def _read_next(self, verb: str, ctx: Any, entity: str) -> None:
        rows = self._rows[entity]
        position = self._cursor[entity]
        if position >= len(rows):
            self.calls.append(verb)
            ctx.file_access.fs_reply = _FS_AT_END
            return
        self._cursor[entity] = position + 1
        _apply(ctx.record, rows[position])
        self._log(verb, ctx)

    # -- GL-Nominal, handler acas005 -----------------------------------------

    def gl_nominal_open(self, ctx: Any) -> None:
        self._open("gl_nominal_open", ctx, "ledger")

    def gl_nominal_read_next(self, ctx: Any) -> None:
        self._read_next("gl_nominal_read_next", ctx, "ledger")

    def gl_nominal_rewrite(self, ctx: Any) -> None:
        ledger = ctx.record
        self.ledger_rewrites.append(
            {
                "key": ledger.ws_ledger_key.ws_ledger_nos,
                "balance": ledger.ledger_balance,
                "last": ledger.ledger_last,
                "quarters": (
                    ledger.quarters.ledger_q1,
                    ledger.quarters.ledger_q2,
                    ledger.quarters.ledger_q3,
                    ledger.quarters.ledger_q4,
                ),
                "occurs_view": tuple(ledger.quarters_table.ledger_q),
                "filler": ledger.filler_l37,
            }
        )
        self._log("gl_nominal_rewrite", ctx)

    def gl_nominal_close(self, ctx: Any) -> None:
        self._log("gl_nominal_close", ctx)

    # -- GL-Batch, handler acas007 -------------------------------------------

    def gl_batch_open(self, ctx: Any) -> None:
        self._open("gl_batch_open", ctx, "batch")

    def gl_batch_open_input(self, ctx: Any) -> None:
        self._open("gl_batch_open_input", ctx, "batch")

    def gl_batch_read_next(self, ctx: Any) -> None:
        self._read_next("gl_batch_read_next", ctx, "batch")

    def gl_batch_rewrite(self, ctx: Any) -> None:
        batch = ctx.record
        self.batch_rewrites.append(
            {
                "key": batch.ws_batch_key.ws_batch_nos,
                "cleared_status": batch.cleared_status,
                "batch_status": batch.batch_status,
                "stored": batch.dates.stored,
                "batch_start": batch.batch_start,
                "items": batch.items,
            }
        )
        self._log("gl_batch_rewrite", ctx)

    def gl_batch_close(self, ctx: Any) -> None:
        self._log("gl_batch_close", ctx)

    # -- GL-Posting, handler acas006 -----------------------------------------

    def gl_posting_open(self, ctx: Any) -> None:
        self._open("gl_posting_open", ctx, "posting")

    def gl_posting_open_input(self, ctx: Any) -> None:
        self._open("gl_posting_open_input", ctx, "posting")

    def gl_posting_open_output(self, ctx: Any) -> None:
        """`Open` plus `Output` EMPTIES the store, and the double empties it too.

        [copybooks/Proc-ACAS-FH-Calls.cob] publishes the verb and `acas006` honours it;
        the handler that turns it into a delete-every-row is `acas008`
        [common/acas008.cbl:L313-L319], and the same meaning applies here. Reached only
        by `compress-post` after `loop1` [general/gl080.cbl:L671], which the record-length
        stop at [general/gl080.cbl:L643-L649] currently pre-empts - so this arm is
        implemented for fidelity rather than exercised, and a test that reached it would
        see an emptied store rather than a surprise.
        """
        self._rows["posting"].clear()
        self._open("gl_posting_open_output", ctx, "posting")

    def gl_posting_read_next(self, ctx: Any) -> None:
        self._read_next("gl_posting_read_next", ctx, "posting")

    def gl_posting_write(self, ctx: Any) -> None:
        posting = ctx.record
        self.posting_writes.append(
            (posting.ws_post_key.batch, posting.ws_post_key.post_number)
        )
        self._log("gl_posting_write", ctx)

    def gl_posting_delete(self, ctx: Any) -> None:
        posting = ctx.record
        self.posting_deletes.append(
            (posting.ws_post_key.batch, posting.ws_post_key.post_number)
        )
        self._log("gl_posting_delete", ctx)

    def gl_posting_close(self, ctx: Any) -> None:
        self._log("gl_posting_close", ctx)

    # -- what the double DOES NOT publish ------------------------------------

    def verbs(self) -> tuple[str, ...]:
        """Every verb this double answers, sorted. Asserted as a set in section 3."""
        return tuple(
            sorted(
                name
                for name in dir(self)
                if name.startswith(("gl_nominal_", "gl_batch_", "gl_posting_"))
            )
        )


@contextlib.contextmanager
def _driving(
    gl080: types.ModuleType, double: _GlFacadeDouble
) -> Iterator[_GlFacadeDouble]:
    """Put `double` in the module's `facade` slot for the duration, then put it back.

    Done with an explicit try/finally rather than with `monkeypatch` so that the
    restoration happens INSIDE the `_shipped_gl080` block, before the module is purged,
    rather than after it in pytest's fixture teardown. The two orderings are both
    harmless today; this one cannot become harmful.

    Args:
        gl080: The shipped module.
        double: The stand-in.

    Yields:
        The same double, so a caller can write `with _driving(...) as calls:`.
    """
    real = gl080.facade
    assert hasattr(real, "FacadeContext"), (
        "the shipped module's `facade` global is not the data-access facade, so the "
        "seam this file drives has moved and every substitution below is meaningless."
    )
    gl080.facade = double
    try:
        yield double
    finally:
        gl080.facade = real


def _system(
    *,
    scycle: int,
    period: int,
    current_quarter: int = 1,
    arch: str = _NOT_ARCHIVING,
    file_system_used: int = _FILE_SYSTEM_RDBMS,
    date_form: int | None = None,
) -> SystemRecord:
    """`01 System-Record` [copybooks/wssystem.cob] with the seven fields `gl080` reads.

    Everything else keeps the record layer's own default, because a value this program
    never reads has no business being set by a test that claims to be about this program.

    Args:
        scycle: `05 Scycle Redefines Cyclea binary-char.` [copybooks/wssystem.cob:L63].
        period: `05 Period binary-char.` [copybooks/wssystem.cob:L64].
        current_quarter: `05 Current-Quarter pic 9.` [copybooks/wssystem.cob:L110] -
            ANOMALY A-3's rotating counter.
        arch: `05 Arch pic x.` [copybooks/wssystem.cob:L164].
        file_system_used: `File-System-Used`, which decides whether phase 4 runs.
        date_form: `05 Date-Form pic 9.` [copybooks/wssystem.cob:L127]. Left at the
            record layer's default when omitted, which is what makes the mutation at
            [general/gl080.cbl:L729-L730] observable.

    Returns:
        The record, ready to hand to `run`.
    """
    system = SystemRecord()
    system.system_data_block.scycle = scycle
    system.system_data_block.period = period
    system.system_data_block.current_quarter = current_quarter
    system.system_data_block.run_date = _RUN_DATE
    system.system_data_block.rdbms_flat_statuses.file_system_used = file_system_used
    system.general_ledger_block.arch = arch
    if date_form is not None:
        system.system_data_block.date_form = date_form
    return system


def _storage(
    gl080: types.ModuleType,
    system: SystemRecord,
    *,
    file_access: FileAccess | None = None,
    file_defs: FileDefs | None = None,
    a: int = 0,
    y: int = 0,
    run_confirmed: bool = True,
    disk_change_option: int = 0,
    archive_path_override: str | None = None,
) -> Any:
    """Build `_Gl080Storage` the way `run` builds it, so a test can watch the fields.

    ⭐ `a` AND `y` ARE PARAMETERS, not initialised constants. `[general/gl080.cbl:L324]`
    reads `a` BEFORE `[general/gl080.cbl:L328]` writes it, and `77 a pic 99 value zero.`
    [general/gl080.cbl:L183] means its incoming value is whatever the program left there -
    so a test unit that initialised it internally could not express the read-before-write
    at all. `run` itself passes zero, which is the `value zero` clause; a test that wants
    the guard pre-armed passes nine.

    Every record and both flat files come from the module's OWN classes, looked up as
    attributes rather than imported at file scope, which keeps this file's module-level
    imports inside the tier's `records`-only allowance.

    Args:
        gl080: The shipped module.
        system: The system record, from `_system`.
        file_access: The shared status block. A fresh one when omitted; pass your own to
            read `Fs-Reply` afterwards.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13]. A fresh one when omitted;
            pass your own to watch `disk-change` compose the archive path.
        a: `77 a pic 99.` on entry [general/gl080.cbl:L183].
        y: `77 y pic 99.` on entry [general/gl080.cbl:L182].
        run_confirmed: The promoted answer at [general/gl080.cbl:L299-L302].
        disk_change_option: The promoted option at [general/gl080.cbl:L545-L547].
        archive_path_override: The promoted path edit at [general/gl080.cbl:L555].

    Returns:
        The storage object.
    """
    access = file_access if file_access is not None else FileAccess()
    return gl080._Gl080Storage(
        ws_calling_data=WsCallingData(),
        system=system,
        to_day=_TO_DAY,
        file_defs=file_defs if file_defs is not None else FileDefs(),
        file_access=access,
        dal_common=AcasDalCommonData(),
        ledger=WsLedgerRecord(),
        batch=GlBatchRecord(),
        posting=WsPostingRecord(),
        a=a,
        y=y,
        ws_eval_msg=" " * 25,
        ws_date_formats=gl080.WsDateFormats(),
        archive=gl080._ArchiveFile(access),
        work_file=gl080._WorkFile(access),
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
        dal_options={},
    )


def _ledger_row(
    key: int, balance: str, *, last: str = "0.00"
) -> dict[str, object]:
    """One `GLLEDGER-REC` row for the double to serve.

    Args:
        key: `WS-Ledger-Nos` [copybooks/wsledger.cob:L15].
        balance: `Ledger-Balance pic s9(8)v99 comp-3` [copybooks/wsledger.cob:L28], as a
            STRING so that no binary float can be constructed on the way in (R-2).
        last: `Ledger-Last`, the field subscript zero lands on.

    Returns:
        The row, keyed by dotted attribute path.
    """
    return {
        "ws_ledger_key.ws_ledger_nos": key,
        "ledger_balance": Decimal(balance),
        "ledger_last": Decimal(last),
    }


def _batch_row(
    number: int,
    cycle: int,
    *,
    batch_status: int = 1,
    cleared_status: int = 1,
    items: int = 1,
) -> dict[str, object]:
    """One `GLBATCH-REC` row for the double to serve.

    The two status defaults are the ones that get PAST phase 1: `88 Status-Closed value
    1.` [copybooks/wsbatch.cob:L27] and `88 Processed value 1.`
    [copybooks/wsbatch.cob:L31] are both satisfied, so
    [general/gl080.cbl:L384-L386] does not set `a` to one. A test about the phase-1 gate
    passes something else deliberately.

    Args:
        number: `WS-Batch-Nos` [copybooks/wsbatch.cob:L14].
        cycle: `Bcycle`, compared against `Scycle` at [general/gl080.cbl:L380-L382].
        batch_status: `Batch-Status` [copybooks/wsbatch.cob:L25].
        cleared_status: `Cleared-Status` [copybooks/wsbatch.cob:L29].
        items: `Items` [copybooks/wsbatch.cob:L23].

    Returns:
        The row, keyed by dotted attribute path.
    """
    return {
        "ws_batch_key.ws_batch_nos": number,
        "bcycle": cycle,
        "batch_status": batch_status,
        "cleared_status": cleared_status,
        "items": items,
    }


def _posting_row(
    batch: int,
    number: int,
    *,
    amount: str = "100.00",
    dr: int = 1010,
    dr_pc: int = 11,
    cr: int = 2020,
    cr_pc: int = 22,
    vat_ac: int = 0,
    vat_pc: int = 0,
    vat_amount: str = "0.00",
    vat_side: str = "  ",
    code: str = "GL",
    date: str = "21/09/25",
    legend: str = "END OF CYCLE TEST",
) -> dict[str, object]:
    """One `GLPOSTING-REC` row for the double to serve.

    Args:
        batch: `Batch` inside `WS-Post-Key` [copybooks/wspost.cob:L13].
        number: `Post-Number` inside `WS-Post-Key` [copybooks/wspost.cob:L14].
        amount: `Post-Amount pic s9(8)v99` [copybooks/wspost.cob:L23], as a STRING (R-2).
        dr: `Post-DR` [copybooks/wspost.cob:L19].
        dr_pc: `DR-PC` [copybooks/wspost.cob:L20].
        cr: `Post-CR` [copybooks/wspost.cob:L21].
        cr_pc: `CR-PC` [copybooks/wspost.cob:L22].
        vat_ac: `VAT-AC` [copybooks/wspost.cob], zero suppresses the VAT leg at
            [general/gl080.cbl:L497-L499].
        vat_pc: `VAT-PC`.
        vat_amount: `VAT-Amount`, as a STRING (R-2). Zero also suppresses the VAT leg.
        vat_side: `Post-VAT-Side`, `"DR"` or `"CR"`, which decides which leg the VAT is
            added into [general/gl080.cbl:L475-L477], [general/gl080.cbl:L489-L491] and
            whether the VAT leg is negated [general/gl080.cbl:L505-L506].
        code: `Post-Code`.
        date: `Post-Date`.
        legend: `Post-Legend`.

    Returns:
        The row, keyed by dotted attribute path.
    """
    return {
        "ws_post_key.batch": batch,
        "ws_post_key.post_number": number,
        "post_code": code,
        "post_date": date,
        "post_legend": legend,
        "post_dr": dr,
        "dr_pc": dr_pc,
        "post_cr": cr,
        "cr_pc": cr_pc,
        "post_amount": Decimal(amount),
        "vat_ac": vat_ac,
        "vat_pc": vat_pc,
        "post_vat_side": vat_side,
        "vat_amount": Decimal(vat_amount),
    }


def _facade_verbs_the_module_calls(module: types.ModuleType) -> frozenset[str]:
    """Every `facade.<verb>` the shipped module names, read out of its own source.

    Read with `ast` rather than by importing and introspecting, because an attribute
    that is only reached down one branch would never show up in a trace of a single run,
    and the verb VOCABULARY is what this is about rather than the verbs one path happens
    to use.

    Args:
        module: The shipped module.

    Returns:
        The verb names, without `FacadeContext` and without anything private.
    """
    tree = ast.parse(inspect.getsource(module))
    return frozenset(
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "facade"
        and node.attr.startswith(("gl_nominal_", "gl_batch_", "gl_posting_"))
    )


@contextlib.contextmanager
def caplog_free() -> Iterator[list[logging.LogRecord]]:
    """Collect `acas_posting.cobol.move` records for the block, with no level games.

    A handler attached to the one logger rather than `caplog`, because `caplog` sets the
    ROOT level and this control test has to be sure it is not the level that made the
    list empty. The handler is removed in a `finally` so no test leaks a handler into
    another.

    Yields:
        The list the handler appends to, live.
    """
    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("acas_posting.cobol.move")
    handler = _Collector(level=logging.NOTSET)
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


# ---------------------------------------------------------------------------
#  3.  THE SEAM ITSELF
#
#      Before any behaviour is asserted, the substitution has to be shown to be the
#      real one. If the program reached its handlers some other way, every test below
#      would be observing a double nobody consulted.
# ---------------------------------------------------------------------------


def test_the_program_reaches_every_handler_through_one_module_global() -> None:
    """`facade` is a module attribute, and replacing it replaces the whole call chain.

    The COBOL equivalent is that `CALL "acas005"` resolves at RUN TIME, by name, to
    whatever module the loader finds - which is why the migration can substitute the
    data-access layer without touching the program, and why this file can drive the
    shipped program with no database (R-1).

    Two facts, both checked rather than assumed: the name exists and carries the
    facade's own `FacadeContext`, and the module holds NO OTHER bound reference to a
    handler that a substitution would miss - every verb it names is spelled
    `facade.<verb>`, so there is exactly one seam.
    """
    with _shipped_gl080() as gl080:
        assert hasattr(gl080, "facade")
        assert hasattr(gl080.facade, "FacadeContext")

        #  A direct `from acas_posting.dal.facade import gl_batch_read_next` would bind
        #  the verb into the module's own namespace and slip past the substitution. None
        #  exists: the module names the verbs only through the `facade` attribute.
        module_level_verbs = sorted(
            name
            for name in vars(gl080)
            if name.startswith(("gl_nominal_", "gl_batch_", "gl_posting_"))
        )
        assert module_level_verbs == [], (
            f"{module_level_verbs} are bound directly into the program's namespace, so "
            f"replacing `facade` would not replace them and the handler substitution "
            f"this file rests on would be partial."
        )


def test_the_double_answers_exactly_the_verbs_the_program_names() -> None:
    """The double's verb set and the program's verb set are the same set.

    A double that answered MORE verbs than the program calls would be harmless but
    misleading; one that answered FEWER would make the first test to reach the missing
    verb fail with `AttributeError` far from the cause. Asserting set equality turns the
    vocabulary into a checked fact, so adding a seventeenth verb to the shipped program
    fails HERE, with a message that says which one.

    THE SIXTEEN, by entity: four on `GL-Nominal` (`acas005`), five on `GL-Batch`
    (`acas007`) and seven on `GL-Posting` (`acas006`)
    [copybooks/Proc-ACAS-FH-Calls.cob].
    """
    with _shipped_gl080() as gl080:
        double = _GlFacadeDouble(gl080.facade)
        named = _facade_verbs_the_module_calls(gl080)

        assert named, (
            "no `facade.<verb>` call was found in the shipped module's source, which "
            "would mean the program no longer reaches the data-access layer at all."
        )
        assert set(double.verbs()) == set(named), (
            f"the double answers {sorted(set(double.verbs()) - set(named))} the program "
            f"does not call, and does not answer "
            f"{sorted(set(named) - set(double.verbs()))} that it does."
        )
        assert len(named) == 16
        assert sum(1 for verb in named if verb.startswith("gl_nominal_")) == 4
        assert sum(1 for verb in named if verb.startswith("gl_batch_")) == 5
        assert sum(1 for verb in named if verb.startswith("gl_posting_")) == 7


# ---------------------------------------------------------------------------
#  4.  THE ROUTE - THE PHASE ORDER, DRIVEN THROUGH `run`
#
#      Agent Action Plan section 0.8.1 requires posting order and batch sequencing be
#      preserved exactly, and section 0.6.4 records that `gl080` labels its own phases
#      on screen in an order that is NOT the order of the numbers: deletion is
#      "Phase - 3" but runs after "Phase - 4"'s neighbour and before "Phase - 5". The
#      only way to lock a route is to assert the ordered call log of a real run.
# ---------------------------------------------------------------------------


def test_the_phases_run_in_the_frozen_order_on_the_deletion_route() -> None:
    """`run` drives phase 1, phase 3, phase 4's gate and phase 5, in that order.

    ENTERED THROUGH `run`, with the frozen four-parameter list
    [general/gl080.cbl:L269-L272], so the route is observed rather than assumed. The
    system record says NOT archiving [copybooks/wssystem.cob:L164-L165], so
    [general/gl080.cbl:L315-L320] takes the `else` arm and phase 3 runs.

    THE ASSERTED SEQUENCE, and what each entry is:

        gl_batch_open_input   376  phase 1 opens the batch file for input only
        gl_batch_read_next    378  the one seeded batch
        gl_batch_read_next    378  at end
        gl_batch_close        391  phase 1's post-loop block
        gl_batch_open         574  phase 3 opens it again, for update this time
        gl_batch_read_next    576
        gl_posting_open       604  del-process, per batch
        gl_posting_read_next  611
        gl_posting_delete     620  the batch's own posting
        gl_posting_read_next  611  at end
        gl_posting_close      582  back in gl080c, AFTER del-process returns
        gl_batch_rewrite      588  the stamp: archived, stored, batch-start zero
        gl_batch_read_next    576  at end
        gl_batch_close        593  phase 3's post-loop block
        gl_nominal_open       337  phase 5, only because the gate at 331 passed
        gl_nominal_read_next  342
        gl_nominal_rewrite    348
        gl_nominal_read_next  342  at end
        gl_nominal_close      354  loop-end

    ⭐ THE TWO OPENS OF THE BATCH FILE ARE BOTH REQUIRED AND ARE NOT THE SAME VERB.
    Phase 1 opens INPUT [general/gl080.cbl:L376] and phase 3 opens I-O
    [general/gl080.cbl:L574]; collapsing them into one open would let phase 1 rewrite,
    and dropping phase 1's close [general/gl080.cbl:L391] would leave the file open
    across a walk that reopens it.

    ⭐ `gl_posting_close` COMES AFTER THE DELETE WALK AND BEFORE THE BATCH REWRITE
    [general/gl080.cbl:L580-L588], which is the account-before-batch ordering Agent
    Action Plan section 0.6.4 names: the batch is stamped only once its postings are
    dealt with.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "123.45")],
        )
        access = FileAccess()
        with _driving(gl080, double):
            gl080.run(
                WsCallingData(),
                system,
                _TO_DAY,
                FileDefs(),
                file_access=access,
            )

        assert double.calls == [
            "gl_batch_open_input",
            "gl_batch_read_next",
            "gl_batch_read_next",
            "gl_batch_close",
            "gl_batch_open",
            "gl_batch_read_next",
            "gl_posting_open",
            "gl_posting_read_next",
            "gl_posting_delete",
            "gl_posting_read_next",
            "gl_posting_close",
            "gl_batch_rewrite",
            "gl_batch_read_next",
            "gl_batch_close",
            "gl_nominal_open",
            "gl_nominal_read_next",
            "gl_nominal_rewrite",
            "gl_nominal_read_next",
            "gl_nominal_close",
        ]
        #  Phase 4 did not run: `File-System-Used` is non-zero, so `not
        #  FS-Cobol-Files-Used` is true and [general/gl080.cbl:L633-L635] leaves at once.
        #  It has no verb of its own in the log, so the absence is asserted through the
        #  one verb it would have used first.
        assert "gl_posting_open_input" not in double.calls


def test_the_archiving_route_replaces_the_deletion_route() -> None:
    """`if archiving` takes phase 2 INSTEAD of phase 3, never as well.

    [general/gl080.cbl:L315-L320] is one `if`/`else`, so exactly one of `gl080b` and
    `gl080c` runs. The observable difference is the archive file: phase 2 writes flat
    rows before deleting the posting [general/gl080.cbl:L468-L508], phase 3 deletes
    without writing anything [general/gl080.cbl:L620].

    Both arms end the same way - the same three stamps and the same rewrite
    [general/gl080.cbl:L428-L433] against [general/gl080.cbl:L583-L588] - which is why
    the batch effect alone cannot tell them apart and the archive is what is asserted.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
        )
        storage = _storage(gl080, system)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  Phase 2's own verb, absent from phase 3's route: `gl080b` opens the archive
        #  and then the batch file for update [general/gl080.cbl:L411-L419].
        assert storage.archive.rows, (
            "the archiving arm wrote no flat archive row, so either the route took the "
            "deletion arm or arc-process stopped before its first write."
        )
        assert "gl_posting_delete" in double.calls
        assert double.batch_rewrites == [
            {
                "key": 7,
                "cleared_status": _CLEARED_ARCHIVED,
                "batch_status": 1,
                "stored": _RUN_DATE,
                "batch_start": 0,
                "items": 1,
            }
        ]


# ---------------------------------------------------------------------------
#  5.  THE ONE `ROUNDED` SITE, IN THE SHIPPED MODULE
#
#      [general/gl080.cbl:L328] is one of only FIVE `ROUNDED` sites in the whole
#      in-scope cycle (Agent Action Plan section 0.6.1), and the sibling file proves
#      what the statement means. What follows proves the shipped module still spells it
#      that way, by reading `a` out of the program's own storage after the call.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("scycle", "period", "expected_a", "truncated_a"),
    [
        #  2.5 -> 3 away from zero. Truncation would leave 2.
        (5, 2, 3, 2),
        #  3.5 -> 4. Truncation would leave 3.
        (7, 2, 4, 3),
        #  1.333... -> 1 either way: rounding DOWN is still rounding, and a case where
        #  the two agree belongs in the table so the discriminating cases are not the
        #  only ones exercised.
        (4, 3, 1, 1),
        #  50.5 -> 51, which still fits `pic 99`. Truncation would leave 50.
        (101, 2, 51, 50),
    ],
)
def test_the_shipped_divide_stores_the_rounded_quotient_into_a(
    scycle: int, period: int, expected_a: int, truncated_a: int
) -> None:
    """`divide scycle by period giving a rounded.` [general/gl080.cbl:L328], observed.

    ⭐ WHY `a` IS READ OUT OF THE STORAGE RATHER THAN INFERRED FROM THE ROUTE. On every
    row in the table the round-trip gate at [general/gl080.cbl:L331-L332] REJECTS, and
    it would reject under truncation too - the gate is an exact-divisibility test, so no
    inexact quotient can pass it whichever way it was rounded. The DISPOSITION therefore
    cannot distinguish the two rounding modes, and the sibling file's census says so.
    The stored value CAN: `st.a` is the program's own `77 a pic 99` and it holds 3 where
    truncation would have left 2. Driving `_gl080_main` with a storage the test owns is
    the only way to see it.

    Rule R-4's stake, from Agent Action Plan section 0.1.1: *"Every other store
    truncates. Getting this backwards would corrupt essentially every posted figure."*
    Here the direction is the annotated exception, and this is the assertion that keeps
    it annotated.
    """
    assert expected_a != truncated_a or scycle % period == 0 or scycle == 4, (
        "the table row claims nothing: rounding and truncation give the same answer and "
        "the quotient is not exact either, so state which case it covers."
    )
    with _shipped_gl080() as gl080:
        system = _system(scycle=scycle, period=period)
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1, "1.00")])
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == expected_a
        #  The product of the un-ROUNDED multiply at [general/gl080.cbl:L329], computed
        #  from the value above and stored into `77 y pic 99` - which is why 51 * 2 = 102
        #  arrives as 2 rather than as 102.
        assert storage.y == (expected_a * period) % 100
        #  The gate rejected, so the cycle was NOT advanced [general/gl080.cbl:L334] and
        #  phase 5 never opened the ledger [general/gl080.cbl:L337].
        assert system.system_data_block.scycle == scycle
        assert "gl_nominal_open" not in double.calls
        assert double.ledger_rewrites == []


@pytest.mark.parametrize(
    ("scycle", "period", "expected_a", "expected_scycle_after"),
    [
        #  12 / 3 = 4 exactly. `add 1 to scycle` gives 13, and then
        #  [general/gl080.cbl:L358-L360] resets a monthly cycle above twelve to one.
        (12, 3, 4, 1),
        #  9 / 3 = 3 exactly, and 10 is not above twelve, so no reset.
        (9, 3, 3, 10),
        #  6 / 2 = 3 exactly. Period two resets at neither three nor thirteen, so the
        #  cycle simply climbs - which is how `a` reaches the out-of-range band.
        (6, 2, 3, 7),
    ],
)
def test_the_round_trip_gate_admits_only_an_exact_multiple(
    scycle: int, period: int, expected_a: int, expected_scycle_after: int
) -> None:
    """The gate passes, so phase 5 runs and the cycle advances.

    `multiply a by period giving y` [general/gl080.cbl:L329] then `if scycle not = y`
    [general/gl080.cbl:L331] is exact divisibility expressed as a round trip. When it
    holds, four things follow in order and all four are asserted: the cycle is
    incremented [general/gl080.cbl:L334], the ledger is opened
    [general/gl080.cbl:L337], every row is rewritten [general/gl080.cbl:L348], and the
    trailing reset rules are applied [general/gl080.cbl:L358-L363].
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=scycle, period=period, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            ledgers=[_ledger_row(1010, "10.00"), _ledger_row(2020, "20.00")],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == expected_a
        assert storage.y == scycle
        assert system.system_data_block.scycle == expected_scycle_after
        assert double.calls.count("gl_nominal_open") == 1
        assert double.calls.count("gl_nominal_close") == 1
        assert [rewrite["key"] for rewrite in double.ledger_rewrites] == [1010, 2020]


def test_the_zero_divisor_reaches_the_shipped_divide_and_stores_nothing() -> None:
    """`period = 0` walks into [general/gl080.cbl:L328], and `a` does not move (Q-7).

    THE GUARD DOES NOT COVER IT. [general/gl080.cbl:L325] turns the block back only when
    `scycle < period`, and no non-negative cycle is below zero, so a zero period reaches
    the divide. What the compiled program then does is ANSWERED and is not what reading
    the statement suggests: GnuCOBOL 3.2 raises the SIZE ERROR condition, performs NO
    STORE and CONTINUES, so the receiving field keeps whatever it held. That is question
    Q-7, and the sibling file locks the semantics layer's half of it against
    `arithmetic.SizeErrorNoStore`.

    ⭐ WHAT THIS TEST ADDS is the half that file cannot reach: THE SHIPPED PROGRAM
    SURVIVES IT. `gl080_end_of_cycle` hands the verb the receiving field's previous value
    - `receiver_value=st.a` - which is what turns the condition into a no-store rather
    than into an exception, so the run continues to `main-end` and returns normally. A
    module that had called the verb WITHOUT `receiver_value` would abort the program
    here, and an operator would see a traceback where the compiled program prints
    nothing.

    ⛔ NOTHING IS GUARDED, CLAMPED OR SUBSTITUTED (R-3): the zero period is not
    validated on the way in, and the no-store leaves `a` holding the value the program
    itself put there at [general/gl080.cbl:L289].
    """
    with _shipped_gl080() as gl080:
        #  The guard at L325 is vacuous against a zero divisor, for every cycle a
        #  signed byte can hold on the non-negative side.
        for cycle in (0, 1, 5, 127):
            assert arithmetic.compare(cycle, 0) >= 0

        system = _system(scycle=4, period=0)
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1, "1.00")])
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            #  No `pytest.raises`: the point is that this RETURNS.
            gl080._gl080_main(storage)

        #  No store happened, so `a` still holds [general/gl080.cbl:L289]'s zero...
        assert storage.a == 0
        #  ... and [general/gl080.cbl:L329] then multiplied that zero by the zero
        #  period, which is a perfectly ordinary store of zero into `y`.
        assert storage.y == 0
        #  The gate compared 4 against 0 and turned the phase back, so the cycle was
        #  not advanced and the ledger was never opened.
        assert system.system_data_block.scycle == 4
        assert "gl_nominal_open" not in double.calls
        assert double.ledger_rewrites == []


# ---------------------------------------------------------------------------
#  6.  ANOMALY A-2 - THE UNBOUNDED QUARTER SUBSCRIPT, IN THE SHIPPED MODULE
#
#      `move ledger-balance to ledger-q (a).` [general/gl080.cbl:L345] against
#      `05 Ledger-Q pic s9(8)v99 comp-3 occurs 4.` [copybooks/wsledger.cob:L36].
#      `a` is the ROUNDED quotient and is NEVER bounds-checked, so an accounting cycle
#      that is not a small multiple of the period length indexes past a four-element
#      table.
#
#      ⛔⛔ DO NOT BOUNDS-CHECK, DO NOT CLAMP, DO NOT WARN (R-3, R-4). Every test in
#      this section asserts that the store HAPPENED and that the walk CONTINUED. The
#      shipped module resolves the subscript to a byte offset and stores into whichever
#      declared item those bytes belong to, which is what the compiled program does; a
#      Python `[a - 1]` would make `a = 0` write the LAST occurrence, a third behaviour
#      belonging to neither language.
#
#      THE DESTINATIONS, from [copybooks/wsledger.cob:L28-L37], and every one of them
#      is exercised below by a `(scycle, period)` pair that reaches it through the real
#      gate rather than by setting `a` directly:
#
#        a = 0        Ledger-Last, A REAL COLUMN      scycle 0, period -1
#        a = 1..4     the four quarters               scycle 12, period 3  -> 4
#        a = 5..12    the trailing filler, no column  scycle 5,  period 1  -> 5
#        a = 13..99   past the 126-byte record        scycle 99, period 1  -> 99
# ---------------------------------------------------------------------------


def test_an_in_range_subscript_writes_both_views_of_the_same_bytes() -> None:
    """`ledger-q (4)` and `Ledger-Q4` are one storage location, and both are written.

    In COBOL `Ledger-Q (a)` and `Ledger-Q1` through `Ledger-Q4` ARE THE SAME BYTES
    [copybooks/wsledger.cob:L30-L36]; in Python they are two dataclass views that do not
    alias, and the record layer deliberately declines to synchronise them because
    keeping a redefines in step would be behaviour in a record layout (R-3).

    ⭐ WHY THIS MATTERS RATHER THAN BEING A CURIOSITY. The `acas005` handler binds its
    columns from the FOUR NAMED FIELDS. A value written into the `occurs` view alone
    would never reach `GLLEDGER-REC` - phase 5's entire table effect would vanish with no
    error and no diagnostic. So the assertion is not "both views agree" for tidiness; it
    is "the view the handler reads was written".

    The subscript here is four, reached honestly: 12 / 3 = 4 exactly, so the gate at
    [general/gl080.cbl:L331] passes and phase 5 runs.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "123.45", last="9.99")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 4
        rewritten = double.ledger_rewrites
        assert len(rewritten) == 1
        #  The named view - what `acas005` binds `LEDGER-Q4` from.
        assert rewritten[0]["quarters"] == (
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("123.45"),
        )
        #  The `occurs` view - the one [general/gl080.cbl:L345] names.
        assert rewritten[0]["occurs_view"] == rewritten[0]["quarters"]
        #  `current-quarter` is one, so [general/gl080.cbl:L346-L347] did NOT fire and
        #  `Ledger-Last` still holds the seeded figure. ANOMALY A-3's independence, from
        #  the other side.
        assert rewritten[0]["last"] == Decimal("9.99")
        #  The balance itself is untouched by the statement: it is the SENDING field.
        assert rewritten[0]["balance"] == Decimal("123.45")


def test_subscript_five_lands_in_the_trailing_filler_and_moves_no_column() -> None:
    """`a = 5` writes past the table, into `filler pic x(50)`, and nothing complains.

    ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345],
    [copybooks/wsledger.cob:L36-L37]. Reached with cycle 5 and period 1: 5 / 1 = 5
    exactly, so the round-trip gate PASSES and phase 5 runs with a subscript one past
    the end of a four-element table. Period one is the ordinary reason this happens -
    nothing resets the cycle for it [general/gl080.cbl:L358-L363], so the quotient
    climbs through the whole `pic 99` domain.

    ⭐ THE STORE IS DATABASE-INVISIBLE, WHICH IS WHY IT IS SILENT. `mysql/ACASDB.sql`
    gives `GLLEDGER-REC` eleven columns and none of them is that filler, so an
    out-of-range quarter store changes the record in memory, is rewritten, and moves NO
    COLUMN. That is exactly the shape of defect a state diff cannot see and a test must.

    ⛔ No `IndexError`, no clamp into 1..4, no warning, and the walk goes on to the next
    account - all four asserted.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=5, period=1, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            ledgers=[
                _ledger_row(1010, "50.00", last="9.99"),
                _ledger_row(2020, "60.00", last="8.88"),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 5
        first, second = double.ledger_rewrites
        #  Not one of the four quarters moved, in either view.
        assert first["quarters"] == (Decimal("0.00"),) * 4
        assert first["occurs_view"] == (Decimal("0.00"),) * 4
        #  Nor `Ledger-Last`, which is where subscript ZERO would have gone.
        assert first["last"] == Decimal("9.99")
        #  The six bytes of the packed value landed at the head of the fifty-byte
        #  filler, because occurrence five begins exactly where the table ends. The
        #  bytes are asserted as a length and a difference rather than as a literal
        #  image: the image is `move`'s business and is locked in its own file.
        default_filler = WsLedgerRecord().filler_l37
        assert len(first["filler"]) == len(default_filler)
        assert first["filler"] != default_filler
        assert first["filler"][6:] == default_filler[6:]
        #  THE WALK CONTINUED: the second account was read, stored into and rewritten
        #  with the same out-of-range subscript.
        assert [rewrite["key"] for rewrite in double.ledger_rewrites] == [1010, 2020]
        assert second["filler"] != default_filler
        assert second["quarters"] == (Decimal("0.00"),) * 4


def test_subscript_zero_overwrites_ledger_last_which_is_a_real_column() -> None:
    """`a = 0` writes `Ledger-Last` - the ONE out-of-range case with a table effect.

    ANOMALY A-2, its most consequential shape. `Ledger-Last`
    [copybooks/wsledger.cob:L29] sits IMMEDIATELY BEFORE `Quarters`
    [copybooks/wsledger.cob:L30] and is the same width as one occurrence, so occurrence
    zero lands squarely on it - and unlike the trailing filler, `LEDGER-LAST` IS A COLUMN
    of `GLLEDGER-REC`. An out-of-range subscript therefore CAN move the database, in
    silence, and this is the case that does it.

    HOW ZERO IS REACHED, and it needs a negative period. [general/gl080.cbl:L324-L325]
    only turns the block back when `a` is nine or `scycle < period`, so a zero quotient
    needs a cycle below one with a period below it - and `Period` is a SIGNED
    `binary-char` [copybooks/wssystem.cob:L64], so a negative value is inside its
    declared domain. Cycle zero with period minus one gives a quotient of zero, `y` of
    zero after the sign drop into `77 y pic 99`, and a gate that PASSES because zero
    equals zero.

    ⭐ THE DISCRIMINATOR: `current-quarter` is ONE here, so [general/gl080.cbl:L346-L347]
    did not fire. `Ledger-Last` therefore holds the balance for one reason only - the
    subscript-zero store. Were the shipped module to clamp the subscript into 1..4, the
    seeded 9.99 would survive and this test would fail, which is the point.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=0, period=-1, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "42.00", last="9.99")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 0
        assert storage.y == 0
        #  The gate passed, so the cycle was advanced - from zero to one.
        assert system.system_data_block.scycle == 1
        rewritten = double.ledger_rewrites
        assert len(rewritten) == 1
        #  THE COLUMN MOVED, and the four quarters did not.
        assert rewritten[0]["last"] == Decimal("42.00")
        assert rewritten[0]["quarters"] == (Decimal("0.00"),) * 4
        assert rewritten[0]["occurs_view"] == (Decimal("0.00"),) * 4
        #  And the filler - the OTHER out-of-range destination - was not touched either,
        #  so the store went to exactly one place.
        assert rewritten[0]["filler"] == WsLedgerRecord().filler_l37


def test_an_out_of_record_subscript_records_the_overrun_and_keeps_walking(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`a = 99` writes wholly past the 126-byte record, and the phase runs to the end.

    ANOMALY A-2 at its far end, and ⚠ AMBIGUITY Q-19: from occurrence thirteen the store
    runs beyond the record into WORKING-STORAGE that belongs to no table, and what the
    compiled program overwrites there is not defined by the record layout. GnuCOBOL
    compiled without bounds checking - and no compile line in this repository passes any
    such flag - stores into whatever follows and CONTINUES.

    THE SHIPPED MODULE'S CHOICE, which this test locks: reproduce the part of the store
    that lands inside the record - here, none of it - and record the overrun as a log
    line rather than raising. Both halves are asserted, because both are load-bearing:
    an exception would end phase 5 at the first oversized cycle and change the
    disposition of every account after it, and a silent no-op would hide the reproduced
    anomaly from the operator entirely.

    HOW 99 IS REACHED: cycle 99 with period 1 divides exactly, so the gate passes.
    `77 a pic 99` [general/gl080.cbl:L183] holds it without overflow.

    ⚠ WHAT IS NOT CLAIMED. This test does not say the compiled program leaves the record
    unchanged; it says the SHIPPED module does, and names Q-19 as the question that
    settles whether an overrunning run moves any of the twenty-two compared tables
    (R-6).
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=99, period=1, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            ledgers=[
                _ledger_row(1010, "3.00", last="1.11"),
                _ledger_row(2020, "4.00", last="2.22"),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with caplog.at_level(logging.ERROR, logger="acas_posting.cobol.move"):
            with _driving(gl080, double):
                gl080._gl080_main(storage)

        assert storage.a == 99
        #  BOTH accounts were rewritten: the walk did not stop at the first overrun.
        assert [rewrite["key"] for rewrite in double.ledger_rewrites] == [1010, 2020]
        #  And the cycle still advanced, so `loop-end` ran too.
        assert system.system_data_block.scycle == 100
        #  Nothing inside the record moved, because none of the six bytes fell inside it.
        blank = WsLedgerRecord()
        for rewrite in double.ledger_rewrites:
            assert rewrite["quarters"] == (Decimal("0.00"),) * 4
            assert rewrite["filler"] == blank.filler_l37
        assert [rewrite["last"] for rewrite in double.ledger_rewrites] == [
            Decimal("1.11"),
            Decimal("2.22"),
        ]

        #  THE OVERRUN WAS RECORDED, once per account, naming the statement and the
        #  subscript. A reproduction that could not be seen would be indistinguishable
        #  from a missing statement.
        overruns = [
            record
            for record in caplog.records
            if record.name == "acas_posting.cobol.move"
        ]
        assert len(overruns) == 2
        for record in overruns:
            message = record.getMessage()
            assert "general/gl080.cbl:L345" in message
            assert "99" in message
            #  The anomaly is named in the message, so an operator reading a log finds
            #  the register entry rather than a mystery.
            assert "A-2" in message


def test_the_in_range_store_records_nothing() -> None:
    """The overrun log line is a REPORT OF AN ANOMALY, not the statement's own trace.

    Without this, the previous test's log assertion would pass just as well if the
    shipped module logged on every store - and a log line on every account of every
    end-of-period run would be noise that hid the one case that matters. So the control
    is asserted: subscript four writes quarter four and says nothing.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1010, "5.00")])
        storage = _storage(gl080, system, a=0)
        with caplog_free() as records:
            with _driving(gl080, double):
                gl080._gl080_main(storage)

        assert storage.a == 4
        assert double.ledger_rewrites[0]["quarters"][3] == Decimal("5.00")
        assert records == []


# ---------------------------------------------------------------------------
#  7.  ANOMALY A-3 - TWO DISAGREEING NOTIONS OF "CURRENT QUARTER"
#
#      [general/gl080.cbl:L345] indexes the quarter table with `a`, the computed
#      quotient. THE VERY NEXT LINE [general/gl080.cbl:L346] tests `current-quarter`,
#      a completely different value maintained by an independent rotating counter at
#      [general/gl080.cbl:L355-L357]. Nothing keeps them in step.
#
#      ⛔ DO NOT RECONCILE THEM (R-3, R-4).
# ---------------------------------------------------------------------------


def test_the_rotating_counter_advances_independently_of_the_subscript() -> None:
    """`add 1 to current-quarter` [general/gl080.cbl:L355] ignores `a` entirely.

    The counter is advanced ONCE PER RUN in `loop-end`, after the walk, while `a` is
    computed once per run from the cycle and the period. They are two unrelated numbers
    that happen to be called the same thing, and this test drives a run where they
    differ by two.

    ANOMALY A-3 [general/gl080.cbl:L345], [general/gl080.cbl:L346],
    [general/gl080.cbl:L355-L357].
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=2)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "77.00", last="1.11")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  The subscript says quarter FOUR.
        assert storage.a == 4
        assert double.ledger_rewrites[0]["quarters"][3] == Decimal("77.00")
        #  The counter said TWO while the row was written, so
        #  [general/gl080.cbl:L346-L347] did not fire...
        assert double.ledger_rewrites[0]["last"] == Decimal("1.11")
        #  ... and afterwards the counter went to THREE, not to five and not to `a`.
        assert system.system_data_block.current_quarter == 3


def test_the_two_notions_of_quarter_can_disagree_in_both_directions() -> None:
    """Quarter one written while `Ledger-Last` is stamped as if it were year end.

    THE SHARPEST FORM OF A-3. `a` is one - the FIRST quarter - so
    [general/gl080.cbl:L345] writes `ledger-q (1)`, while `current-quarter` is four, so
    [general/gl080.cbl:L346-L347] ALSO writes `Ledger-Last`, the field that means "the
    closing balance of the year". The row therefore says both "this is the first quarter"
    and "this is the end of the year" at once, and the compiled program writes it exactly
    that way.

    Reached with cycle 3 and period 3: 3 / 3 = 1 exactly, so the gate passes with a
    subscript of one.

    ⛔ NOT RECONCILED (R-4): no test here asserts that the two agree, and no code is
    changed to make them.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=3, period=3, current_quarter=4)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "88.00", last="1.11")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 1
        rewritten = double.ledger_rewrites[0]
        #  Quarter ONE received the balance.
        assert rewritten["quarters"] == (
            Decimal("88.00"),
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.00"),
        )
        #  And `Ledger-Last` received it too, from the OTHER notion of quarter.
        assert rewritten["last"] == Decimal("88.00")
        #  The counter was four, so `loop-end` rolled it back to one
        #  [general/gl080.cbl:L356-L357] - while the cycle went 3 -> 4, nowhere near a
        #  reset.
        assert system.system_data_block.current_quarter == 1
        assert system.system_data_block.scycle == 4


@pytest.mark.parametrize(
    (
        "period",
        "scycle",
        "current_quarter",
        "expected_quarter_after",
        "expected_scycle_after",
    ),
    [
        #  Monthly accounting, cycle 12: the counter rolls 4 -> 1 and the cycle is reset
        #  from 13 to 1 by [general/gl080.cbl:L358-L360].
        (3, 12, 4, 1, 1),
        #  Monthly accounting, cycle 9: the counter climbs, and 10 is not above twelve so
        #  no cycle reset.
        (3, 9, 2, 3, 10),
        #  Weekly accounting at the year end: 52 / 13 = 4 exactly, the increment gives
        #  53, and 53 IS above 52, so [general/gl080.cbl:L361-L363] resets it.
        (13, 52, 4, 1, 1),
        #  Weekly accounting mid-year: 39 / 13 = 3, the increment gives 40, which is not
        #  above 52.
        (13, 39, 1, 2, 40),
        #  ⭐ ANY OTHER PERIOD NEVER RESETS. Period 1, cycle 6: the cycle climbs to 7 and
        #  keeps climbing on later runs, which is how `a` reaches the out-of-range band
        #  at all. THE TWO RESET RULES ARE THE ONLY TWO, and they are conjunctions.
        (1, 6, 3, 4, 7),
        #  Period 2, cycle 12: 12 is above twelve, but the period is not three, so the
        #  first conjunction fails and there is no reset. The conjunction is asserted by
        #  the absence.
        (2, 12, 4, 1, 13),
    ],
)
def test_the_counter_and_the_cycle_wrap_by_their_own_separate_rules(
    period: int,
    scycle: int,
    current_quarter: int,
    expected_quarter_after: int,
    expected_scycle_after: int,
) -> None:
    """`loop-end` [general/gl080.cbl:L354-L363], driven through the shipped module.

    FOUR STATEMENTS, THREE INDEPENDENT RULES, no `else` between them: the counter is
    incremented and wrapped at five, and the cycle is reset by two conjunctions that can
    never both hold because a period cannot be both three and thirteen. Merging them,
    turning either into an `else`, or inferring a reset for a period the source does not
    name would all be caught here.

    ANOMALY A-3 rides along in every row: `expected_quarter_after` is computed from
    `current_quarter` alone and never from `a`.
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=scycle, period=period, current_quarter=current_quarter
        )
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1010, "1.00")])
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  Every row divides exactly, so the gate passed and `loop-end` was reached.
        assert storage.y == scycle
        assert system.system_data_block.current_quarter == expected_quarter_after
        assert system.system_data_block.scycle == expected_scycle_after
        #  A period cannot satisfy both reset conditions, whatever the cycle.
        assert arithmetic.compare(3, 13) != 0


# ---------------------------------------------------------------------------
#  8.  PHASE 1 - THE OUTSTANDING-BATCH GATE
#
#      `gl080a` [general/gl080.cbl:L368-L395] walks the batch file and sets `a` to one
#      if it finds a batch in this cycle that is neither closed nor processed;
#      [general/gl080.cbl:L308-L313] then stops the whole run. THE DETECTOR PREDICATE
#      IS NOT `gl070`'S: `gl070` tests one condition name [general/gl070.cbl:L314],
#      this program tests the conjunction of two negations
#      [general/gl080.cbl:L384-L386].
# ---------------------------------------------------------------------------


def test_an_outstanding_batch_stops_the_run_before_any_write() -> None:
    """`if a = 1 ... go to main-end` [general/gl080.cbl:L308-L313].

    An outstanding batch means the cycle is not ready to close, and the compiled program
    responds by returning - not by aborting, not by setting a term code, and not by
    writing anything. `gl080` never sets a term code at all, which is why its caller's
    `load00.` block has no `= 5` gate the way `load08` does
    [general/general.cbl:L711-L722].

    ⭐ EVERY LATER PHASE IS ABSENT, and that is the whole assertion: no batch rewrite,
    no posting delete, no archive row, no ledger verb and no cycle increment. A run that
    stopped later - after phase 3 had already deleted the postings, say - would leave the
    database in a state the compiled program never produces.

    THE BATCH SEEDED HERE fails BOTH negations: status zero is not
    `88 Status-Closed value 1` [copybooks/wsbatch.cob:L27] and cleared status zero is not
    `88 Processed value 1` [copybooks/wsbatch.cob:L31], so [general/gl080.cbl:L386] sets
    `a` to one.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12, batch_status=0, cleared_status=0)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, system, a=0)
        before = dataclasses.asdict(storage.ledger)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 1
        #  Phase 1 and nothing else.
        assert double.calls == [
            "gl_batch_open_input",
            "gl_batch_read_next",
            "gl_batch_read_next",
            "gl_batch_close",
        ]
        assert double.batch_rewrites == []
        assert double.posting_deletes == []
        assert double.ledger_rewrites == []
        assert storage.archive.rows == ()
        #  The cycle did not move, so a later run sees the same cycle and can try again.
        assert system.system_data_block.scycle == 12
        #  And the ledger record the program carries was never touched.
        assert dataclasses.asdict(storage.ledger) == before


@pytest.mark.parametrize(
    ("batch_status", "cleared_status", "expected_a"),
    [
        #  Neither negation satisfied -> outstanding.
        (0, 0, 1),
        #  Closed but not processed -> the first negation fails, so the conjunction
        #  fails and `a` stays zero.
        (1, 0, 0),
        #  Processed but not closed -> the second negation fails.
        (0, 1, 0),
        #  Both -> the batch is finished with, and the run proceeds.
        (1, 1, 0),
    ],
)
def test_the_detector_needs_both_negations_at_once(
    batch_status: int, cleared_status: int, expected_a: int
) -> None:
    """`if not status-closed and not processed` [general/gl080.cbl:L384-L386].

    A CONJUNCTION OF TWO NEGATIONS, which is not the same as either negation alone and
    not the same as `gl070`'s single `if status-open` [general/gl070.cbl:L314]. The truth
    table is asserted whole, because three of its four rows let the run PROCEED and only
    one stops it - so a fix that turned the conjunction into a disjunction would stop
    runs the compiled program allows, and the failure would look like a business rule
    rather than like a defect.

    The section is driven directly rather than through `run`, because what is asserted is
    the detector's own output - `a` - and `_gl080_main` would then consume it.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[
                _batch_row(
                    7, 12, batch_status=batch_status, cleared_status=cleared_status
                )
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080a(storage)

        assert storage.a == expected_a
        #  The file was opened for INPUT and closed again, whichever way the test went.
        assert double.calls[0] == "gl_batch_open_input"
        assert double.calls[-1] == "gl_batch_close"


def test_the_detector_ignores_a_batch_from_another_cycle() -> None:
    """`if bcycle not = scycle go to loop` [general/gl080.cbl:L380-L382].

    The cycle filter comes FIRST, so a batch left open in a previous cycle does not block
    this cycle's close - and the status test is never reached for it. Asserted with a
    batch that WOULD be outstanding if it were examined: were the filter dropped, `a`
    would come back as one.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(9, 11, batch_status=0, cleared_status=0)],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080a(storage)

        assert storage.a == 0
        #  The row WAS read - the filter is inside the loop, not in the read.
        assert double.calls.count("gl_batch_read_next") == 2


# ---------------------------------------------------------------------------
#  9.  PHASE 2 - THE ARCHIVING WALK
#
#      `arc-process` [general/gl080.cbl:L445-L516] explodes every posting of the batch
#      into TWO OR THREE flat archive rows and then deletes the posting. The three legs
#      and their signs are the frozen source's, verbatim:
#
#        leg 1  DR side  arc-ac <- post-dr, arc-c-ac <- post-cr, amount POSITIVE,
#                        plus the VAT when `post-vat-side = "CR"`
#                        [general/gl080.cbl:L468-L479]
#        leg 2  CR side  the two accounts SWAPPED, plus the VAT when the side is "DR",
#                        then `multiply arc-amount by -1` [general/gl080.cbl:L481-L493]
#        leg 3  VAT      only when both `vat-ac` and `vat-amount` are non-zero, negated
#                        when the side is "CR" [general/gl080.cbl:L497-L508]
# ---------------------------------------------------------------------------


def test_the_archive_walk_writes_the_double_entry_and_the_vat_leg() -> None:
    """Three rows, three signs, one delete - `arc-process` in full.

    THE FIGURES, and every one of them is a consequence of a cited line rather than a
    choice: a posting of 100.00 with 17.50 of VAT on the CR side gives

        leg 1  arc-ac 1010 / 11   arc-c-ac 2020 / 22   amount  117.50
        leg 2  arc-ac 2020 / 22   arc-c-ac 1010 / 11   amount -100.00
        leg 3  arc-ac 3030 / 33   arc-c-ac 1010 / 11   amount  -17.50

    Leg 1 carries the VAT because the side is "CR" [general/gl080.cbl:L475-L477]; leg 2
    does NOT, because the same test at [general/gl080.cbl:L489-L491] asks for "DR", and it
    is then negated unconditionally [general/gl080.cbl:L493]; leg 3 is negated for the
    same "CR" reason [general/gl080.cbl:L505-L506].

    ⭐ LEG 3'S CONTRA ACCOUNT IS LEG 2'S, AND THAT IS NOT AN OVERSIGHT IN THIS TEST.
    [general/gl080.cbl:L501-L503] moves only `arc-ac`, `arc-pc` and `arc-amount` before
    the third `write`, so `arc-c-ac` and `arc-c-pc` still hold what leg 2 put there. The
    compiled program writes the record it has, fields and all, and so does the shipped
    module (R-4). Asserting the leftover is how a future "tidy-up" that cleared the
    contra fields gets caught.

    All four money figures are `Decimal` built from strings; nothing here goes near a
    binary float (R-2).
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                _posting_row(
                    7,
                    3,
                    amount="100.00",
                    vat_ac=3030,
                    vat_pc=33,
                    vat_amount="17.50",
                    vat_side="CR",
                )
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        rows = storage.archive.rows
        assert len(rows) == 3

        assert (rows[0].arc_batch, rows[0].arc_post) == (7, 3)
        assert (rows[0].arc_ac, rows[0].arc_pc) == (1010, 11)
        assert (rows[0].arc_c_ac, rows[0].arc_c_pc) == (2020, 22)
        assert rows[0].arc_amount == Decimal("117.50")

        assert (rows[1].arc_ac, rows[1].arc_pc) == (2020, 22)
        assert (rows[1].arc_c_ac, rows[1].arc_c_pc) == (1010, 11)
        assert rows[1].arc_amount == Decimal("-100.00")

        assert (rows[2].arc_ac, rows[2].arc_pc) == (3030, 33)
        #  The leftover contra, per the docstring.
        assert (rows[2].arc_c_ac, rows[2].arc_c_pc) == (1010, 11)
        assert rows[2].arc_amount == Decimal("-17.50")

        #  The posting's own fields are carried into all three rows unchanged
        #  [general/gl080.cbl:L464-L466].
        for row in rows:
            assert row.arc_code == "GL"
            assert row.arc_date == "21/09/25"
            assert row.arc_legend.rstrip() == "END OF CYCLE TEST"

        #  And then the posting is deleted, once, AFTER the last write
        #  [general/gl080.cbl:L510-L512].
        assert double.posting_deletes == [(7, 3)]
        assert double.calls.index("gl_posting_delete") > double.calls.index(
            "gl_posting_read_next"
        )


@pytest.mark.parametrize(
    ("vat_ac", "vat_amount"),
    [
        #  `if vat-ac equal zero` - the first disjunct [general/gl080.cbl:L497].
        (0, "17.50"),
        #  `or vat-amount = zero` - the second [general/gl080.cbl:L498].
        (3030, "0.00"),
        #  Both, which is the ordinary case for a posting that carries no VAT.
        (0, "0.00"),
    ],
)
def test_the_archive_walk_omits_the_vat_leg_when_either_vat_field_is_zero(
    vat_ac: int, vat_amount: str
) -> None:
    """`go to by-pass` [general/gl080.cbl:L497-L499] - two rows, not three.

    A DISJUNCTION, so either field alone suppresses the leg. The delete at
    [general/gl080.cbl:L511] still happens, because `by-pass` is where the jump lands
    and the delete is its only statement - so a posting with no VAT is archived as a
    plain double entry and removed exactly like one with VAT.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                _posting_row(
                    7,
                    1,
                    amount="60.00",
                    vat_ac=vat_ac,
                    vat_pc=33,
                    vat_amount=vat_amount,
                    vat_side="DR",
                )
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        rows = storage.archive.rows
        assert len(rows) == 2
        #  The side is "DR" here, so the VAT - where there is any - belongs to leg 2,
        #  which is also the negated one [general/gl080.cbl:L489-L493].
        expected_second = -(Decimal("60.00") + Decimal(vat_amount))
        assert rows[0].arc_amount == Decimal("60.00")
        assert rows[1].arc_amount == expected_second
        assert double.posting_deletes == [(7, 1)]


def test_the_archive_walk_skips_the_zero_key_and_a_foreign_batch() -> None:
    """`if WS-Post-Key = zero or batch not = WS-Batch-Nos go to loop`
    [general/gl080.cbl:L458-L460].

    Two filters in one condition, and the consequence of dropping either is a posting
    archived under the wrong batch or a placeholder row archived as if it were real.
    Asserted with three seeded postings of which exactly ONE belongs to the batch: the
    archive gets that one's rows and the deletes name that one only.

    ⭐ THE ZERO KEY IS THE WHOLE GROUP, not the batch alone: `WS-Post-Key` spans both
    `Batch` and `Post-Number` [copybooks/wspost.cob:L12-L14], so a row with batch zero
    and a NON-zero post number does not match the first disjunct - it is caught by the
    second instead, because zero is not this batch. Both shapes are seeded so that the
    group test cannot be mistaken for a test of `batch` alone.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                #  The whole key is zero - the first disjunct.
                _posting_row(0, 0, amount="1.00"),
                #  Another batch - the second disjunct.
                _posting_row(8, 1, amount="2.00"),
                #  Batch zero with a real post number: not the zero GROUP, but still not
                #  this batch.
                _posting_row(0, 5, amount="3.00"),
                #  The only one that belongs here.
                _posting_row(7, 9, amount="4.00"),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert double.posting_deletes == [(7, 9)]
        rows = storage.archive.rows
        assert len(rows) == 2
        assert rows[0].arc_amount == Decimal("4.00")
        assert rows[1].arc_amount == Decimal("-4.00")
        assert {row.arc_post for row in rows} == {9}


def test_the_extend_then_output_fallback_creates_the_archive_and_appends_to_it() -> None:
    """`open extend` then, on a non-zero status, `close` and `open output`
    [general/gl080.cbl:L411-L414].

    THE MAINTAINER'S OWN IDIOM, and his comment explains it: try to append, and if that
    fails create the file. Both arms are exercised, because they differ in exactly one
    observable - whether what was already in the file survives.

    ARM ONE, the fallback. A fresh archive does not exist, so `open extend` answers a
    non-zero file status; the shipped `_ArchiveFile` reports 35, the ISAM "file not
    found". The walk then writes its rows anyway, which is the whole point of the
    fallback: without it, `gl080b` would append to a file it never opened.

    ARM TWO, the append. An archive that already holds a row opens for extend
    successfully, and the pre-existing row is STILL THERE afterwards, followed by this
    run's. An `open output` that ran unconditionally would have truncated it - losing
    every previously archived cycle - and this assertion is what stands between the two.
    """
    with _shipped_gl080() as gl080:
        #  The premise of arm one, asserted rather than assumed: a file that has never
        #  been created answers `open extend` with a non-zero status.
        access = FileAccess()
        fresh = gl080._ArchiveFile(access)
        fresh.open_extend()
        assert access.fs_reply != _FS_OK

        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[_posting_row(7, 1, amount="5.00")],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)
        #  ARM ONE: the rows were written despite the failed extend.
        assert [row.arc_amount for row in storage.archive.rows] == [
            Decimal("5.00"),
            Decimal("-5.00"),
        ]

    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[_posting_row(7, 1, amount="5.00")],
        )
        storage = _storage(gl080, system, a=0)
        #  A previous cycle's archive: created, written and closed, so the file EXISTS.
        storage.archive.open_output()
        storage.archive.record.arc_batch = 999
        storage.archive.record.arc_amount = Decimal("11.11")
        storage.archive.write()
        storage.archive.close()

        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  ARM TWO: the earlier row survived and this run's two follow it.
        rows = storage.archive.rows
        assert len(rows) == 3
        assert (rows[0].arc_batch, rows[0].arc_amount) == (999, Decimal("11.11"))
        assert [row.arc_amount for row in rows[1:]] == [
            Decimal("5.00"),
            Decimal("-5.00"),
        ]


# ---------------------------------------------------------------------------
#  10.  PHASE 3 - THE DELETION WALK
# ---------------------------------------------------------------------------


def test_the_deletion_walk_deletes_the_batchs_postings_and_writes_no_archive_row() -> None:
    """`del-process` [general/gl080.cbl:L600-L625] - the same walk, without the archive.

    The two walks share their filters [general/gl080.cbl:L615-L617] and their stamps
    [general/gl080.cbl:L583-L588], and differ in that this one has no `write`. So the
    assertion that separates them is the EMPTY ARCHIVE, and the assertion that they
    share is the identical batch stamp - both are made here.

    THE POSTINGS ARE DELETED IN THE ORDER THEY ARE READ, which for a sequential walk is
    the order of the store. Asserted as a list rather than as a set: order is a
    behavioural fact here, not an incidental one.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_NOT_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                _posting_row(7, 1),
                _posting_row(8, 1),
                _posting_row(7, 2),
                _posting_row(0, 0),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert double.posting_deletes == [(7, 1), (7, 2)]
        assert storage.archive.rows == ()
        assert double.batch_rewrites == [
            {
                "key": 7,
                "cleared_status": _CLEARED_ARCHIVED,
                "batch_status": 1,
                "stored": _RUN_DATE,
                "batch_start": 0,
                "items": 1,
            }
        ]


def test_both_walks_stamp_the_batch_the_same_way() -> None:
    """[general/gl080.cbl:L428-L433] and [general/gl080.cbl:L583-L588], side by side.

    ⭐ `Cleared-Status` BECOMES 2, WHICH IS `88 Archived`
    [copybooks/wsbatch.cob:L32] - EVEN ON THE DELETION ROUTE, where nothing was archived
    at all. The name is wrong for what the deletion walk did, and the value is what the
    compiled program stores; both routes are asserted to store it so that a "fix" giving
    the deletion route a different status fails here (R-4).

    `Stored` receives `Run-Date` off the system record [copybooks/wssystem.cob:L67],
    which is the determinism requirement in miniature: the date arrives through linkage
    and no clock is read (R-6). `Batch-Start` is zeroed
    [general/gl080.cbl:L432], [general/gl080.cbl:L587].
    """
    stamps = []
    for arch in (_ARCHIVING, _NOT_ARCHIVING):
        with _shipped_gl080() as gl080:
            system = _system(scycle=4, period=3, arch=arch)
            double = _GlFacadeDouble(
                gl080.facade,
                batches=[_batch_row(7, 4)],
                postings=[_posting_row(7, 1)],
            )
            storage = _storage(gl080, system, a=0)
            with _driving(gl080, double):
                gl080._gl080_main(storage)
            stamps.append(double.batch_rewrites)

    archiving, deleting = stamps
    assert archiving == deleting
    assert archiving[0]["cleared_status"] == _CLEARED_ARCHIVED
    assert archiving[0]["stored"] == _RUN_DATE
    assert archiving[0]["batch_start"] == 0


# ---------------------------------------------------------------------------
#  11.  `disk-change` - THE PROMOTED OPTION, AND `a`'S SECOND ROLE
#
#      [general/gl080.cbl:L519-L559]. Agent Action Plan section 0.3.4 makes the accept
#      at [general/gl080.cbl:L545-L547] a parameter because its answer decides whether
#      the database is written: nine suppresses the archiving walk AND, through the
#      shared `a`, the whole of end-of-period processing.
# ---------------------------------------------------------------------------


def test_the_disk_change_abort_suppresses_archiving_and_end_of_period() -> None:
    """⭐ `a` CARRIES THE ABORT CODE ACROSS TWO PHASES - one field, two purposes.

    `accept-option` stores the answer into `a` [general/gl080.cbl:L545]. `gl080b` tests
    it immediately and leaves [general/gl080.cbl:L408-L409]; then
    [general/gl080.cbl:L324] tests THE SAME FIELD and turns end-of-period back too. So
    one operator answer stops two unrelated phases, through a field whose third use is
    the quarter subscript.

    THE DISCRIMINATING PAIR. Both runs below are identical except for the option, and
    the cycle and period are chosen so that end-of-period WOULD run: 12 / 3 = 4 exactly.
    With the option at zero the ledger is walked and the cycle advances; with it at nine
    neither happens. A module that had used a local variable for the `disk-change`
    answer - the obvious tidy-up - would archive nothing and then still run
    end-of-period, and the difference between the two runs would collapse.
    """
    with _shipped_gl080() as gl080:
        proceeding = _system(scycle=12, period=3, current_quarter=1, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, proceeding, a=0, disk_change_option=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.archive.rows != ()
        assert double.ledger_rewrites != []
        #  13, then reset to 1 by the monthly rule.
        assert proceeding.system_data_block.scycle == 1

    with _shipped_gl080() as gl080:
        aborting = _system(scycle=12, period=3, current_quarter=1, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, aborting, a=0, disk_change_option=9)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  Nothing archived, nothing deleted, no batch stamped...
        assert storage.archive.rows == ()
        assert double.posting_deletes == []
        assert double.batch_rewrites == []
        #  ... and end-of-period did not run either, because `a` still holds the nine.
        assert storage.a == 9
        assert double.ledger_rewrites == []
        assert "gl_nominal_open" not in double.calls
        assert aborting.system_data_block.scycle == 12
        assert aborting.system_data_block.current_quarter == 1


@pytest.mark.parametrize("option", [1, 2, 5, 8, 10, 99])
def test_a_disk_change_option_outside_zero_and_nine_is_refused_before_any_write(
    option: int,
) -> None:
    """`if a not = zero go to accept-option` [general/gl080.cbl:L548-L549].

    THE DOMAIN IS EXACTLY {0, 9}, because every other value is sent back to the prompt
    and the prompt is not a parameter - so no third value can reach the statements below
    it. The shipped module refuses rather than proceeding, which is the CLI-boundary
    finding its own docstring records: a caller that passed 5 would otherwise silently
    get the "proceed" arm, which is the one answer the compiled program certainly does
    not give.

    ⛔ THIS IS NOT AN ADDED VALIDATION (R-3). The refusal replaces an unreachable state
    with an error at the boundary; it does not reject an input the compiled program
    accepts, because the compiled program never accepts one - it loops.

    NOTHING IS WRITTEN when it fires: the exception comes out of `disk-change`, which
    runs BEFORE the archive is opened [general/gl080.cbl:L411] and before the batch file
    is opened for update [general/gl080.cbl:L419].
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, system, a=0, disk_change_option=option)
        with _driving(gl080, double):
            with pytest.raises(gl080.DiskChangeOptionNotAcceptable) as refused:
                gl080._gl080_main(storage)

        assert str(option) in str(refused.value)
        assert storage.archive.rows == ()
        assert double.batch_rewrites == []
        assert double.posting_deletes == []
        assert double.ledger_rewrites == []
        #  Phase 1 ran, because it comes first; phase 2 got as far as `disk-change`.
        assert "gl_batch_open_input" in double.calls
        assert "gl_batch_open" not in double.calls


def test_the_archive_path_is_composed_and_a_blank_override_is_ignored() -> None:
    """`string ... into arg-test` then `move arg-test to file-2`
    [general/gl080.cbl:L530-L539].

    FOUR SOURCES, TWO DELIMITER FORMS. `file-24` and `file-2` are `delimited by space`,
    so each contributes up to its first space; the literal `"archives"` and the operating
    system's separator are `delimited by size`, so they contribute in full. With a base
    of `/opt/acas/` and a separator of `/` the result is
    `/opt/acas/archives/archive.dat`, and that string is then moved back over `file-2` -
    which is why the composition is observable at all.

    THE OVERRIDE, and its guard. [general/gl080.cbl:L550-L557] accepts an edited path and
    keeps it only `if file-2 (1:1) not = space`; a leading space means the operator
    pressed Enter and the composed path stands. Both arms asserted, because a module that
    dropped the guard would replace a working path with a blank one.

    ⭐ THE OVERRIDE OVERWRITES IN PLACE, WHICH IS MEASURED AND NOT ASSUMED. `accept
    file-2 ... with update` [general/gl080.cbl:L555] presents the field holding the
    composed path, and question `Q-GL084-ACCEPT-SEMANTICS` asked whether typed text
    replaces that content or is inserted into it. MEASURED (2026-08-08) on the harness
    image's own `cobc (GnuCOBOL) 3.2.0` over a real 24x80 pty, against the frozen
    declaration `pic x(532)` [copybooks/file02.cob:L1] and the frozen statement form:
    NEITHER. Typed characters overwrite from position 1 and everything beyond them
    stands, so `XY` over `archives/archive.dat` came back as `XYchives/archive.dat`,
    and a bare Return came back unchanged. This assertion therefore requires the
    composed path's TAIL to survive an override shorter than it - a whole-field
    replacement, which this test used to assert, is a reading no probe could make the
    compiled accept produce (rules R-6 and R-3).

    ⛔ NO TABLE EFFECT EITHER WAY. The archive is a flat file, not a schema table, so
    nothing here reaches the comparison - which is precisely why it needs a test of its
    own.
    """
    base = "/opt/acas/"
    with _shipped_gl080() as gl080:
        file_defs = FileDefs()
        file_defs.file_defs_os_delimiter = "/"
        file_defs.file_defs_a.file_24 = base.ljust(len(file_defs.file_defs_a.file_24))
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(gl080, system, file_defs=file_defs, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert (
            storage.file_defs.file_defs_a.file_2.rstrip()
            == "/opt/acas/archives/archive.dat"
        )

    with _shipped_gl080() as gl080:
        file_defs = FileDefs()
        file_defs.file_defs_os_delimiter = "/"
        file_defs.file_defs_a.file_24 = base.ljust(len(file_defs.file_defs_a.file_24))
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(
            gl080,
            system,
            file_defs=file_defs,
            a=0,
            archive_path_override="/var/spool/acas-archive.dat",
        )
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  The composed path is 30 characters and the override is 27, so the
        #  override overwrites positions 1 to 27 and the composed path's last three
        #  characters - `dat`, positions 28 to 30 of `archive.dat` - are still there.
        #  That trailing `dat` is the whole discrimination: it is present under the
        #  measured overwrite-in-place semantics and absent under a whole-field move.
        assert (
            storage.file_defs.file_defs_a.file_2.rstrip()
            == "/var/spool/acas-archive.datdat"
        )

    with _shipped_gl080() as gl080:
        file_defs = FileDefs()
        file_defs.file_defs_os_delimiter = "/"
        file_defs.file_defs_a.file_24 = base.ljust(len(file_defs.file_defs_a.file_24))
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(
            gl080,
            system,
            file_defs=file_defs,
            a=0,
            #  A leading space: the operator accepted the composed path.
            archive_path_override=" /var/spool/ignored.dat",
        )
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert (
            storage.file_defs.file_defs_a.file_2.rstrip()
            == "/opt/acas/archives/archive.dat"
        )


# ---------------------------------------------------------------------------
#  12.  PHASE 4 - POSTING CONTRACTION, AND THE RECORD-LENGTH STOP
#
#      `compress-post` [general/gl080.cbl:L628-L708] copies every posting out to a work
#      file, re-creates the posting store and copies them back - a physical compaction
#      that only makes sense for indexed files. Its first statement is a configuration
#      test, and its second is a length comparison that STOPS THE RUN.
# ---------------------------------------------------------------------------


def test_phase_four_does_not_run_in_the_rdbms_configuration() -> None:
    """`if not FS-Cobol-Files-Used go to main-exit` [general/gl080.cbl:L633-L635].

    `88 FS-Cobol-Files-Used value zero` over `File-System-Used`, so a NON-zero value
    means an RDBMS - which is the configuration every scenario in this migration runs in.
    Phase 4 therefore leaves before it opens anything, and the whole of the compaction is
    dead code for a database run.

    ASSERTED BY ABSENCE, with the two verbs only phase 4 uses
    [general/gl080.cbl:L651-L652], [general/gl080.cbl:L671-L672] - and by the work file
    staying empty.
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=4, period=3, file_system_used=_FILE_SYSTEM_RDBMS
        )
        double = _GlFacadeDouble(
            gl080.facade, postings=[_posting_row(5, 1), _posting_row(5, 2)]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._compress_post(storage)

        assert double.calls == []
        assert storage.work_file.rows == ()
        assert double.posting_writes == []


def test_phase_four_stops_the_run_on_the_record_length_disagreement() -> None:
    """`stop run.` [general/gl080.cbl:L643-L649] - and it fires on EVERY Cobol-files run.

    ⚠ AMBIGUITY Q-23, and this test is what makes it visible rather than theoretical.
    The frozen guard is

        if function length (WS-Posting-Record) not =
           function length (work-file-record)   ... stop run.

    and the two are NOT equal: the posting record is 103 bytes and
    `work-file-record pic x(101)` [general/gl080.cbl:L173] is 101. So in the Cobol-files
    configuration `compress-post` reaches the comparison, finds a mismatch and ENDS THE
    RUN UNIT - phase 4 cannot complete, and neither can anything after it.

    ⛔ THE MISMATCH IS NOT REPAIRED (R-4). Padding the work record to 103, or comparing
    something else, would make a stop the compiled program performs disappear. What the
    shipped module does instead is raise its own `_StopRun`, whose message carries both
    lengths and the locator, so an operator sees the same halt with a reason attached.

    ⭐ WHY THE TWO FIGURES ARE ASSERTED. Q-23 asks when this can happen; the answer this
    test records is "whenever the run uses Cobol files", and it can only record that by
    naming the lengths. Were either declaration to change, this test would fail and the
    register entry would need revisiting - which is the correct outcome, not a nuisance.

    NOTHING IS WRITTEN BEFORE THE STOP: the guard precedes the posting open
    [general/gl080.cbl:L651] and the work-file open [general/gl080.cbl:L652].
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=4, period=3, file_system_used=_FILE_SYSTEM_COBOL
        )
        double = _GlFacadeDouble(
            gl080.facade, postings=[_posting_row(5, 1), _posting_row(5, 2)]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            with pytest.raises(gl080._StopRun) as stopped:
                gl080._compress_post(storage)

        message = str(stopped.value)
        assert "103" in message
        assert "101" in message
        assert "general/gl080.cbl:L643-L649" in message
        #  Nothing was opened, nothing was copied and nothing was written back.
        assert double.calls == []
        assert storage.work_file.rows == ()
        assert double.posting_writes == []


def test_the_record_length_stop_propagates_out_of_the_whole_program() -> None:
    """`stop run` ends the RUN UNIT, so it is not caught on the way out either.

    [general/gl080.cbl:L322] performs `compress-post` from the middle of
    `gl080-Main`, between phase 3 and the end-of-period gate. A `stop run` there means
    the phases after it never execute - so the assertion is both that the exception
    reaches the caller of `run` and that end-of-period left no trace.

    This is the ONE place where the shipped program's disposition depends on the flat-file
    configuration, and a scenario cannot reach it: every scenario runs with an RDBMS. The
    test is therefore the only witness (R-6).
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=12,
            period=3,
            current_quarter=1,
            file_system_used=_FILE_SYSTEM_COBOL,
        )
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        with _driving(gl080, double):
            with pytest.raises(gl080._StopRun):
                gl080.run(
                    WsCallingData(),
                    system,
                    _TO_DAY,
                    FileDefs(),
                    file_access=FileAccess(),
                )

        #  Phase 3 had already run and stamped the batch - that state is real and is
        #  what the compiled program leaves behind too.
        assert double.batch_rewrites != []
        #  End-of-period never started.
        assert double.ledger_rewrites == []
        assert system.system_data_block.scycle == 12


# ---------------------------------------------------------------------------
#  13.  THE PROMOTED CONFIRM, THE DATE-FORM MUTATION, AND DETERMINISM
# ---------------------------------------------------------------------------


def test_an_unconfirmed_run_writes_nothing_at_all() -> None:
    """`accept keyed-reply` then `goback` [general/gl080.cbl:L299-L304].

    THE BACKUP QUESTION IS A GATE, not a courtesy: Escape or "A" returns before a single
    handler is called. Agent Action Plan section 0.3.4 promotes it to a parameter because
    its answer changes table state - here by preventing every change - and the default is
    the answer that proceeds.

    ZERO VERBS, which is a stronger claim than "no writes": phase 1 does not even open
    the batch file.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        with _driving(gl080, double):
            gl080.run(
                WsCallingData(),
                system,
                _TO_DAY,
                FileDefs(),
                file_access=FileAccess(),
                run_confirmed=False,
            )

        assert double.calls == []
        assert double.batch_rewrites == []
        assert double.ledger_rewrites == []
        assert system.system_data_block.scycle == 12


def test_the_run_fills_date_form_when_it_is_zero_and_leaves_a_set_value_alone() -> None:
    """`zz070-Convert-Date` [general/gl080.cbl:L719-L747] MUTATES the system record.

    ⭐ THE DISPLAY IS DROPPED AND THE STATEMENT IS NOT. [general/gl080.cbl:L285] performs
    the date conversion only so that [general/gl080.cbl:L286] can display the result, and
    presentation is out of scope (Agent Action Plan section 0.3.4) - but the section also
    writes `Date-Form` when that field is zero [general/gl080.cbl:L729-L730], and
    `Date-Form` IS A COLUMN of `SYSTEM-REC` [copybooks/wssystem.cob:L127]. Dropping the
    performed section with the display it fed would have removed a database effect.

    ⭐⭐ AND THIS IS WHY `SYSTEM-REC` IS FINGERPRINTED RATHER THAN LEFT UNWATCHED. The
    scenario harness records a digest of `SYSTEM-REC` on both sides precisely because
    routes like this one move it without meaning to; `tests/conftest.py`'s
    `PARAMETER_TABLE` carries the reasoning.

    Both arms: zero is filled with the UK form, and a value already set is left as it is
    - which is the `if` at [general/gl080.cbl:L729] rather than an unconditional move.
    """
    with _shipped_gl080() as gl080:
        unset = _system(scycle=4, period=3)
        assert unset.system_data_block.date_form == 0
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(gl080, unset, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  `1` is the UK form [copybooks/wssystem.cob], the default the section supplies.
        assert unset.system_data_block.date_form == 1
        #  And the converted text is the date that arrived through linkage, which is the
        #  determinism claim in one line (R-6).
        assert storage.ws_date_formats.ws_date == _TO_DAY

    with _shipped_gl080() as gl080:
        preset = _system(scycle=4, period=3, date_form=2)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(gl080, preset, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert preset.system_data_block.date_form == 2


def test_two_runs_with_the_same_arguments_write_the_same_rows() -> None:
    """Determinism, at the program level (R-6).

    Every date this program uses arrives through linkage - the text date in `to_day` and
    the binary run date on the system record - and the module imports no clock. So two
    runs of the same scenario write the same rows, and the assertion is a whole-object
    comparison of everything the two runs produced: the ordered verb log, both rewrite
    lists, the deletes, the flat archive rows and the mutated system record.

    A comparison of SUMMARIES would let a difference hide; this compares the observations
    themselves, and the archive rows are compared as dataclasses so that every field of
    every row takes part.
    """
    outcomes = []
    for _ in range(2):
        with _shipped_gl080() as gl080:
            system = _system(scycle=12, period=3, current_quarter=4, arch=_ARCHIVING)
            double = _GlFacadeDouble(
                gl080.facade,
                batches=[_batch_row(7, 12), _batch_row(8, 11)],
                postings=[
                    _posting_row(
                        7, 1, amount="10.00", vat_ac=3030, vat_amount="1.75",
                        vat_side="CR",
                    ),
                    _posting_row(7, 2, amount="20.00"),
                ],
                ledgers=[_ledger_row(1010, "5.00"), _ledger_row(2020, "-6.00")],
            )
            storage = _storage(gl080, system, a=0)
            with _driving(gl080, double):
                gl080._gl080_main(storage)

            outcomes.append(
                {
                    "calls": list(double.calls),
                    "ledger_rewrites": list(double.ledger_rewrites),
                    "batch_rewrites": list(double.batch_rewrites),
                    "posting_deletes": list(double.posting_deletes),
                    "archive": [
                        dataclasses.asdict(row) for row in storage.archive.rows
                    ],
                    "system": dataclasses.asdict(system),
                    "a": storage.a,
                    "y": storage.y,
                }
            )

    first, second = outcomes
    assert first == second
    #  And the run was not vacuous: it archived, deleted, stamped and posted.
    assert first["archive"]
    assert first["posting_deletes"]
    assert first["batch_rewrites"]
    assert first["ledger_rewrites"]
