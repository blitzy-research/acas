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
        THE TWO HALVES HAVE DIFFERENT STANDING and this file does not conflate
        them. The DIRECTION is settled by the language: COBOL `ROUNDED` rounds half
        away from zero, and the shipped layer does. The NUMBER OF INTERMEDIATE
        DIGITS is a property of the compiler build, is UNMEASURED, and the register
        keeps Q-2 pending on it. No figure in this file depends on the open half:
        every quotient here lands in a two-digit receiver, so sixty working digits
        and any plausible compiler default agree.
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
    numbered open question rather than a matter of opinion: the copybook says
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

    Provenance: the zoned store policy, question Q-5.1, whose provisional values
    are transcribed from the documented GnuCOBOL default into
    `acas_posting/cobol/usage.py` and are pending measurement. Note this is the
    store into
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
    ambient context does. The sixty digits are a WORKING ASSUMPTION documented at
    `acas_posting/cobol/arithmetic.py`'s `INTERMEDIATE_PRECISION`, chosen to exceed
    every in-scope receiver; the compiler's own default is question Q-2 and is
    still pending, and it cannot reach these two figures, which need eight digits
    between them.

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
